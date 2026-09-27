"""Regression checks for the read-only R4a runtime inventory."""
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
from types import SimpleNamespace

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "r4a_handoff_snapshot.py"
spec = importlib.util.spec_from_file_location("r4a_handoff_snapshot", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SnapshotTest(unittest.TestCase):
    def test_missing_is_distinct_from_daemon_failure_and_secrets_are_omitted(self):
        item = {
            "Config": {"Labels": {"org.opencontainers.image.revision": "abc"},
                       "Env": ["SECRET=never-print"]},
            "State": {"Running": True, "Status": "running"},
            "HostConfig": {"RestartPolicy": {"Name": "unless-stopped"}},
            "Image": "sha256:test",
            "NetworkSettings": {"Networks": {"backend": {}}},
            "Mounts": [{"Source": "never-print"}],
        }
        def run(cmd, **kwargs):
            self.assertEqual(kwargs["timeout"], 10)
            if cmd[1] == "container":
                return SimpleNamespace(returncode=0, stdout="present\n")
            return SimpleNamespace(returncode=0, stdout=json.dumps([item]))
        with patch.object(module.subprocess, "run", side_effect=run):
            result = module.snapshot(("present", "missing"))
        self.assertEqual(result["containers"][1], {"name": "missing", "present": False})
        self.assertNotIn("never-print", json.dumps(result))
        with patch.object(module.subprocess, "run",
                          return_value=SimpleNamespace(returncode=1, stdout="")):
            with self.assertRaises(RuntimeError):
                module.snapshot(("present",))

    def test_inspect_failure_and_timeout_fail_closed(self):
        with patch.object(module.subprocess, "run",
                          side_effect=[SimpleNamespace(returncode=0, stdout="present\n"),
                                       SimpleNamespace(returncode=1, stdout="")]):
            with self.assertRaises(RuntimeError):
                module.snapshot(("present",))
        with patch.object(module.subprocess, "run",
                          side_effect=subprocess.TimeoutExpired(["docker"], 10)):
            with self.assertRaises(subprocess.TimeoutExpired):
                module.snapshot(("present",))


if __name__ == "__main__":
    unittest.main()
