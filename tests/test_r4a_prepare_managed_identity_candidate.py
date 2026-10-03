import contextlib
import copy
import io
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import r4a_prepare_managed_identity_candidate as prepare


def live():
    return {"Id": "old-id", "Image": "old-image", "State": {"Running": True},
            "Config": {"User": "10003:10003", "Env": ["PRIVATE_PASSWORD=private-value"],
                       "Entrypoint": ["java"], "Cmd": ["app.jar"], "WorkingDir": "/app"},
            "HostConfig": {"NetworkMode": "ouf-backend", "RestartPolicy": {"Name": "unless-stopped"},
                           "LogConfig": {"Type": "json-file", "Config": {}}},
            "NetworkSettings": {"Networks": {"ouf-backend": {"Aliases": ["ouf-onboarding"]}}},
            "Mounts": [{"Type": "bind", "Source": "/private/token-dir", "Destination": "/run/auth", "RW": False}]}


def image():
    config = copy.deepcopy(live()["Config"])
    config["Labels"] = {"org.opencontainers.image.revision": prepare.REVISION}
    return {"Id": "new-image", "Config": config}


def candidate():
    doc = live()
    doc.update(Id="new-id", Image="new-image", State={"Running": False, "Status": "created"})
    doc["HostConfig"]["RestartPolicy"]["Name"] = "no"
    return doc


class PrepareManagedIdentityCandidateTests(unittest.TestCase):
    def test_optional_lookup_uses_exact_names_and_rejects_daemon_failure(self):
        for names in ("", "candidate-old\nother\n"):
            with patch.object(prepare.inventory, "run", return_value=names) as run, \
                 patch.object(prepare.inventory, "inspect") as inspect:
                self.assertIsNone(prepare.optional("candidate"))
                self.assertEqual(run.call_args.args[0], ["docker", "container", "ls", "--all", "--format", "{{.Names}}"])
                inspect.assert_not_called()
        with patch.object(prepare.inventory, "run", return_value="other\ncandidate\n"), \
             patch.object(prepare.inventory, "inspect", return_value={"Id": "existing"}) as inspect:
            self.assertEqual(prepare.optional("candidate"), {"Id": "existing"})
            inspect.assert_called_once_with("candidate")
        error = subprocess.CalledProcessError(1, ["docker"], stderr="private-detail")
        with patch.object(prepare.inventory, "run", side_effect=error):
            with self.assertRaisesRegex(RuntimeError, "^OWNER_DOCKER_INSPECT_FAILED$"):
                prepare.optional("candidate")

    def test_unsafe_root_blocks_before_inventory_build_or_container_operations(self):
        for mode, owner in ((stat.S_IFDIR | 0o755, 0), (stat.S_IFDIR | 0o700, 1000),
                            (stat.S_IFLNK | 0o700, 0)):
            with patch.object(Path, "lstat", return_value=SimpleNamespace(st_mode=mode, st_uid=owner)), \
                 patch.object(prepare.os, "geteuid", return_value=0), \
                 patch.object(prepare.inventory, "inspect") as inspect, \
                 patch.object(prepare, "build") as build:
                with self.assertRaisesRegex(RuntimeError, "OWNER_STAGE_DIRECTORY_UNSAFE"):
                    prepare.main(SimpleNamespace(repo=Path("/unused")))
                inspect.assert_not_called()
                build.assert_not_called()

    def test_complete_prepare_keeps_env_in_private_file_and_never_starts_runtime(self):
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def create(args):
                self.assertEqual(args[:2], ["docker", "create"])
                env_path = Path(args[args.index("--env-file") + 1])
                self.assertEqual(env_path.read_text(), "PRIVATE_PASSWORD=private-value\n")
                self.assertEqual(env_path.stat().st_mode & 0o777, 0o600)
                self.assertNotIn("private-value", " ".join(args))
                return "new-id\n"
            with patch.object(prepare, "ROOT", root), patch.object(prepare, "STATE", root / "state.json"), \
                 patch.object(prepare.inventory, "inspect", side_effect=[live(), live(), image(), live(), candidate(), live()]), \
                 patch.object(prepare.inventory, "main", return_value=True) as preflight, \
                 patch.object(prepare, "optional", return_value=None), \
                 patch.object(prepare, "build"), \
                 patch.object(prepare.inventory, "run", side_effect=create) as run, \
                 contextlib.redirect_stdout(output):
                prepare.main(SimpleNamespace(repo=root))
            self.assertEqual(preflight.call_count, 2)
            self.assertEqual(run.call_count, 1)
            state = json.loads((root / "state.json").read_text())
            self.assertEqual(state["candidate_id"], "new-id")
            self.assertEqual(state["old"]["Id"], "old-id")
            self.assertEqual((root / "state.json").stat().st_mode & 0o777, 0o600)
            self.assertEqual(list(root.glob("*/candidate.env")), [])
        self.assertIn("STOPPED=true ENV_AND_MOUNTS_PRESERVED=true", output.getvalue())
        self.assertNotIn("private-value", output.getvalue())

    def test_live_drift_after_build_blocks_before_creating_candidate(self):
        changed = live()
        changed["Config"]["Env"] = ["PRIVATE_PASSWORD=changed-private-value"]
        with tempfile.TemporaryDirectory() as folder, patch.object(prepare, "ROOT", Path(folder)), \
             patch.object(prepare.inventory, "inspect", side_effect=[live(), live(), image(), changed]), \
             patch.object(prepare.inventory, "main", return_value=True), patch.object(prepare, "build"), \
             patch.object(prepare.inventory, "run") as run, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, "OWNER_LIVE_CHANGED_DURING_BUILD"):
                prepare.main(SimpleNamespace(repo=Path(folder)))
            run.assert_not_called()

    def test_failed_readback_removes_only_its_own_stopped_container(self):
        wrong = candidate()
        wrong["Config"]["Env"] = []
        replacement = candidate()
        replacement["Id"] = "unrelated-id"
        for cleanup_doc, expected_calls in ((candidate(), 2), (replacement, 1)):
            with tempfile.TemporaryDirectory() as folder, patch.object(prepare, "ROOT", Path(folder)), \
                 patch.object(prepare, "STATE", Path(folder) / "state.json"), \
                 patch.object(prepare.inventory, "inspect", side_effect=[live(), live(), image(), live(), wrong]), \
                 patch.object(prepare.inventory, "main", return_value=True), patch.object(prepare, "build"), \
                 patch.object(prepare, "optional", side_effect=[None, cleanup_doc]), \
                 patch.object(prepare.inventory, "run", return_value="new-id\n") as run, \
                 contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(RuntimeError, "OWNER_CANDIDATE_READBACK_MISMATCH"):
                    prepare.main(SimpleNamespace(repo=Path(folder)))
                self.assertEqual(run.call_count, expected_calls)
                if expected_calls == 2:
                    self.assertEqual(run.call_args.args[0], ["docker", "rm", prepare.NAME])

    def test_existing_drift_is_rejected_and_never_removed(self):
        wrong = candidate()
        wrong["State"]["Running"] = True
        self.assertFalse(prepare.candidate_matches(wrong, live(), image()))
        wrong = candidate()
        wrong["Mounts"][0]["RW"] = True
        self.assertFalse(prepare.candidate_matches(wrong, live(), image()))
        self.assertTrue(prepare.candidate_matches(candidate(), live(), image()))


if __name__ == "__main__":
    unittest.main()
