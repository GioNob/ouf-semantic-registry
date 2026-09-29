#!/usr/bin/env python3
"""Safety gates for the live UDP principal correction."""

import importlib.util
from pathlib import Path
import time
from unittest import TestCase, main, mock


spec = importlib.util.spec_from_file_location("switch", Path(__file__).with_name(
    "r4a_switch_udp_principal_fix.py"))
switch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(switch)


class SwitchSafetyTest(TestCase):
    def setUp(self):
        self.live = {"Id": "a" * 64, "Image": "sha256:old", "State": {"Running": True}}
        self.new = {"Id": "b" * 64}
        self.manifest = {"commit": switch.TARGET}

    def run_case(self, preflight_error=None, token_error=None, backup_error=None):
        events = []
        self.events = events

        def docker(*args, **_):
            events.append(("docker", args))
            return ""

        def token():
            events.append(("token",))
            if token_error:
                raise token_error
            return "in-memory-test-token", time.time() + 300

        def preflight(*_):
            events.append(("preflight",))
            if preflight_error:
                raise preflight_error

        with (mock.patch.object(switch.os, "geteuid", return_value=0),
              mock.patch.object(Path, "is_file", return_value=True),
              mock.patch.object(Path, "read_text", return_value='{"commit":"x"}'),
              mock.patch.object(switch, "inspect", side_effect=lambda name: self.live if name == switch.LIVE else
                                {"State": {"Running": False}} if name == switch.CANDIDATE else
                                (_ for _ in ()).throw(switch.subprocess.CalledProcessError(1, "inspect"))),
              mock.patch.object(switch, "health", return_value=True),
              mock.patch.object(switch, "flyway", return_value="34"),
              mock.patch.object(switch, "human_token", side_effect=token),
              mock.patch.object(switch, "frozen_configuration", return_value={"test": True}),
              mock.patch.object(switch, "candidate", return_value=self.new),
              mock.patch.object(switch, "docker", side_effect=docker),
              mock.patch.object(switch, "backup", side_effect=backup_error if backup_error else
                                lambda: Path("/opt/ouf/r4a-stage/test.dump")),
              mock.patch.object(switch, "preflight", side_effect=preflight),
              mock.patch.object(switch, "rollback", side_effect=lambda *_: events.append(("rollback",)))):
            switch.main()
        return events

    def test_authentication_failure_cannot_stop_udp(self):
        with self.assertRaisesRegex(RuntimeError, "TOKEN_FAILED"):
            self.run_case(token_error=RuntimeError("TOKEN_FAILED"))
        self.assertFalse(any(event[0] == "docker" for event in self.events))

    def test_failed_authenticated_preflight_rolls_back_runtime(self):
        with self.assertRaisesRegex(RuntimeError, "HTTP_403"):
            self.run_case(preflight_error=RuntimeError("AUTHENTICATED_PREFLIGHT_HTTP_403"))
        self.assertIn(("rollback",), self.events)
        self.assertNotIn(("docker", ("rm", switch.CANDIDATE)), self.events)

    def test_backup_failure_recovers_before_swap_and_removes_candidate(self):
        with self.assertRaisesRegex(RuntimeError, "BACKUP_FAILED"):
            self.run_case(backup_error=RuntimeError("BACKUP_FAILED"))
        self.assertIn(("docker", ("rm", switch.CANDIDATE)), self.events)
        self.assertNotIn(("rollback",), self.events)

    def test_success_only_after_authenticated_preflight(self):
        events = self.run_case()
        self.assertLess(events.index(("preflight",)), len(events))
        self.assertNotIn(("rollback",), events)
        self.assertIn(("docker", ("stop", "--time", "60", switch.LIVE)), events)


if __name__ == "__main__":
    main()
