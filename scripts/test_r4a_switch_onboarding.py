import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import r4a_switch_onboarding as switch


class OnboardingSwitchTest(unittest.TestCase):
    def fixtures(self, root, events, failure=False):
        stage = Path(root)
        (stage / "identity-images.json").write_text(json.dumps({"modules": {
            "onboarding": {"commit": switch.EXPECTED, "live_image_id": "old",
                           "image_id": "new"}}}))
        stopped = [False]

        def inspected(name):
            if name == switch.LIVE:
                return {"Image": "old", "Id": "a" * 64,
                        "State": {"Running": not stopped[0]},
                        "HostConfig": {"NetworkMode": "ouf-backend"}}
            if name == switch.CANDIDATE:
                return {"Image": "new", "Id": "b" * 64, "State": {"Running": False},
                        "HostConfig": {"NetworkMode": "ouf-backend"},
                        "Mounts": [{"Destination": "/run/ouf-onboarding-identity",
                                    "RW": False}]}
            raise subprocess.CalledProcessError(1, ["docker", "inspect"])

        def docker(*args):
            events.append(args)
            if args[0] == "stop":
                stopped[0] = True
            if args[0] == "start":
                stopped[0] = False
            return ""

        def backup():
            events.append(("backup",))
            if failure:
                raise RuntimeError("BACKUP_FAILED")
            return stage / "snapshot.dump"

        return stage, inspected, docker, backup

    def test_stop_backup_swap_and_verify(self):
        with tempfile.TemporaryDirectory() as root:
            events = []
            stage, inspected, docker, backup = self.fixtures(root, events)
            with patch.object(switch, "STAGE", stage), \
                 patch.object(switch.os, "geteuid", return_value=0), \
                 patch.object(switch, "token_fresh", return_value=True), \
                 patch.object(switch, "inspect", side_effect=inspected), \
                 patch.object(switch, "docker", side_effect=docker), \
                 patch.object(switch, "health", return_value=True), \
                 patch.object(switch, "flyway", return_value="31"), \
                 patch.object(switch, "backup", side_effect=backup), \
                 patch.object(switch.subprocess, "run",
                              return_value=type("Result", (), {"returncode": 0})()):
                switch.main("31")
            self.assertLess(events.index(("stop", "--time", "60", switch.LIVE)),
                            events.index(("backup",)))
            self.assertLess(events.index(("backup",)),
                            events.index(("rename", switch.LIVE,
                                          "ouf-onboarding-rollback-" + "a" * 12)))
            self.assertIn(("start", switch.LIVE), events)

    def test_backup_failure_recovers_old_container(self):
        with tempfile.TemporaryDirectory() as root:
            events = []
            stage, inspected, docker, backup = self.fixtures(root, events, failure=True)
            with patch.object(switch, "STAGE", stage), \
                 patch.object(switch.os, "geteuid", return_value=0), \
                 patch.object(switch, "token_fresh", return_value=True), \
                 patch.object(switch, "inspect", side_effect=inspected), \
                 patch.object(switch, "docker", side_effect=docker), \
                 patch.object(switch, "health", return_value=True), \
                 patch.object(switch, "flyway", return_value="31"), \
                 patch.object(switch, "backup", side_effect=backup), \
                 patch.object(switch.subprocess, "run",
                              return_value=type("Result", (), {"returncode": 0})()):
                with self.assertRaisesRegex(RuntimeError, "BACKUP_FAILED"):
                    switch.main("31")
            self.assertIn(("start", switch.LIVE), events)
            self.assertFalse(any(event[0] == "rename" for event in events))

    def test_stale_token_blocks_before_stop(self):
        with tempfile.TemporaryDirectory() as root:
            events = []
            stage, inspected, docker, backup = self.fixtures(root, events)
            with patch.object(switch, "STAGE", stage), \
                 patch.object(switch.os, "geteuid", return_value=0), \
                 patch.object(switch, "token_fresh", return_value=False), \
                 patch.object(switch, "inspect", side_effect=inspected), \
                 patch.object(switch, "docker", side_effect=docker), \
                 patch.object(switch, "backup", side_effect=backup):
                with self.assertRaisesRegex(RuntimeError, "PINNED_PREFLIGHT_CHANGED"):
                    switch.main("31")
            self.assertFalse(events)


if __name__ == "__main__":
    unittest.main()
