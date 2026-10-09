import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import r4a_switch_udp as switch


class SwitchOrderTest(unittest.TestCase):
    def test_stop_then_verified_backup_then_swap_and_health(self):
        with tempfile.TemporaryDirectory() as root:
            stage = Path(root)
            (stage / "identity-images.json").write_text(json.dumps({"modules": {"udp": {
                "commit": switch.EXPECTED, "live_image_id": "old", "image_id": "new"}}}))
            events = []
            def inspected(name):
                if name == switch.LIVE:
                    return {"Image": "old", "Id": "a" * 64, "State": {"Running": True},
                            "HostConfig": {"NetworkMode": "ouf-backend"}}
                if name == switch.CANDIDATE:
                    return {"Image": "new", "Id": "b" * 64, "State": {"Running": False}}
                raise subprocess.CalledProcessError(1, ["docker", "inspect"])
            versions = iter(("26", "34"))
            def docker(*args):
                events.append(("docker", args[:2]))
                return next(versions) if args[0] == "exec" else ""
            def backup():
                events.append(("backup", None))
                return stage / "backup.dump"
            with patch.object(switch, "STAGE", stage), patch.object(switch.os, "geteuid", return_value=0), \
                 patch.object(switch, "inspect", side_effect=inspected), \
                 patch.object(switch, "health", return_value=True), \
                 patch.object(switch, "gateway_reachability", return_value=True), \
                 patch.object(switch, "docker", side_effect=docker), \
                 patch.object(switch, "backup", side_effect=backup):
                switch.main()
            self.assertLess(events.index(("docker", ("stop", "--time"))),
                            events.index(("backup", None)))
            self.assertLess(events.index(("backup", None)),
                            events.index(("docker", ("rename", switch.LIVE))))
            self.assertIn(("docker", ("start", switch.LIVE)), events)

    def test_backup_failure_restarts_old_without_rename(self):
        with tempfile.TemporaryDirectory() as root:
            stage = Path(root)
            (stage / "identity-images.json").write_text(json.dumps({"modules": {"udp": {
                "commit": switch.EXPECTED, "live_image_id": "old", "image_id": "new"}}}))
            calls = []
            stopped = [False]
            def inspected(name):
                if name == switch.LIVE:
                    return {"Image": "old", "Id": "a" * 64,
                            "State": {"Running": not stopped[0]},
                            "HostConfig": {"NetworkMode": "ouf-backend"}}
                if name == switch.CANDIDATE:
                    return {"Image": "new", "Id": "b" * 64, "State": {"Running": False}}
                raise subprocess.CalledProcessError(1, ["docker", "inspect"])
            def docker(*args):
                calls.append(args)
                if args[0] == "stop": stopped[0] = True
                if args[0] == "start": stopped[0] = False
                return "26" if args[0] == "exec" else ""
            with patch.object(switch, "STAGE", stage), patch.object(switch.os, "geteuid", return_value=0), \
                 patch.object(switch, "inspect", side_effect=inspected), \
                 patch.object(switch, "health", return_value=True), \
                 patch.object(switch, "docker", side_effect=docker), \
                 patch.object(switch, "backup", side_effect=RuntimeError("BACKUP_FAILED")):
                with self.assertRaisesRegex(RuntimeError, "BACKUP_FAILED"):
                    switch.main()
            self.assertIn(("start", switch.LIVE), calls)
            self.assertFalse(any(call[0] == "rename" for call in calls))


if __name__ == "__main__":
    unittest.main()
