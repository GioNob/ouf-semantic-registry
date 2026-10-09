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
import r4a_switch_managed_identity_candidate as switch
from test_r4a_prepare_managed_identity_candidate import live, candidate, image


class SwitchManagedIdentityCandidateTests(unittest.TestCase):
    def fixture(self, root):
        state = {"revision": switch.prepare.REVISION, "candidate_name": switch.prepare.NAME,
                 "image_id": "new-image", "candidate_id": "new-id", "old": live()}
        path = root / "state.json"
        path.write_text(json.dumps(state))
        path.chmod(0o600)
        current = candidate()
        current["State"] = {"Running": True, "Status": "running"}
        final = copy.deepcopy(current)
        final["HostConfig"]["RestartPolicy"]["Name"] = "unless-stopped"
        args = SimpleNamespace(mode="apply", repo=root, source="test", version="unused", expected_hash="unused")
        return state, path, current, final, args

    def execute(self, root, *, mode="apply", fail_backup=False, fail_start=False):
        state, path, current, final, args = self.fixture(root)
        args.mode = mode
        output, events = io.StringIO(), []
        def command(*args):
            events.append(args)
            return "401" if args[0] == "unused" else ""
        def backup():
            events.append(("backup",))
            if fail_backup:
                raise RuntimeError("TEST_BACKUP_FAILED")
            return root / "backup.dump"
        ready_replies = [None, RuntimeError("TEST_START_FAILED")] if fail_start else [None, None]
        with patch.object(switch.prepare, "ROOT", root), patch.object(switch.prepare, "STATE", path), \
             patch.object(switch, "RECEIPT", root / "receipt.json"), \
             patch.object(switch.inventory, "inspect", side_effect=[live(), candidate(), image(), live(), current, final]), \
             patch.object(switch.inventory, "main", return_value=True), \
             patch.object(switch.prepare, "optional", return_value=None), \
             patch.object(switch, "tokens_fresh"), patch.object(switch, "ready", side_effect=ready_replies), \
             patch.object(switch, "history", return_value=[{"version": "31"}]), \
             patch.object(switch, "frozen", return_value={"hash": "pinned", "state": "IN_REVIEW"}), \
             patch.object(switch, "backup_restore", side_effect=backup), \
             patch.object(switch, "http_code", return_value="403"), \
             patch.object(switch, "docker", side_effect=command), \
             patch.object(switch, "recover") as recover, contextlib.redirect_stdout(output):
            if fail_backup or fail_start:
                with self.assertRaisesRegex(RuntimeError, "TEST_"):
                    switch.main(args)
            else:
                switch.main(args)
            return events, output.getvalue(), recover.call_args_list

    def test_apply_backs_up_after_stop_and_swaps_only_verified_candidate(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            events, output, recovery = self.execute(root)
            self.assertLess(events.index(("stop", "--time", "60", switch.LIVE)), events.index(("backup",)))
            self.assertLess(events.index(("backup",)), events.index(("rename", switch.prepare.NAME, switch.LIVE)))
            receipt = json.loads((root / "receipt.json").read_text())
            self.assertEqual(receipt["status"], "PASS")
            self.assertEqual((root / "receipt.json").stat().st_mode & 0o777, 0o600)
            self.assertEqual(recovery, [])
            self.assertIn("ATTESTATION_POST=false COMPATIBILITY_PROBE_PENDING=true", output)
            self.assertNotIn("private-value", output)

    def test_plan_does_not_write_stop_backup_or_start(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            events, output, recovery = self.execute(root, mode="plan")
            self.assertEqual(events, [])
            self.assertEqual(recovery, [])
            self.assertFalse((root / "receipt.json").exists())
            self.assertIn("LIVE_UNCHANGED=true", output)

    def test_backup_failure_recovers_without_renaming_candidate(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            events, output, recovery = self.execute(root, fail_backup=True)
            self.assertFalse(any(event[0] == "rename" for event in events))
            self.assertEqual(len(recovery), 1)
            self.assertEqual(json.loads((root / "receipt.json").read_text())["status"], "ROLLED_BACK")
            self.assertIn("DB_NOT_AUTOMATICALLY_RESTORED=true", output)

    def test_start_failure_recovers_after_swap_and_preserves_backup_reference(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            events, output, recovery = self.execute(root, fail_start=True)
            self.assertIn(("start", switch.LIVE), events)
            self.assertEqual(len(recovery), 1)
            receipt = json.loads((root / "receipt.json").read_text())
            self.assertEqual(receipt["db_dump"], str(root / "backup.dump"))
            self.assertEqual(receipt["status"], "ROLLED_BACK")

    def test_recovery_refuses_to_touch_an_unrelated_live_id(self):
        doc = live()
        doc["Id"] = "unrelated-id"
        with patch.object(switch.prepare, "optional", return_value=doc), patch.object(switch, "docker") as docker:
            with self.assertRaisesRegex(RuntimeError, "OWNER_ROLLBACK_LIVE_ID_MISMATCH"):
                switch.recover({"old": {"Id": "old-id"}, "candidate_id": "new-id"}, "previous", "failed")
            docker.assert_not_called()

    def test_scratch_restore_failure_drops_only_scratch_and_keeps_private_dump(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def command(args, **kwargs):
                if "pg_dump" in args:
                    kwargs["stdout"].write(b"private-dump" * 200)
                    return subprocess.CompletedProcess(args, 0)
                raise subprocess.CalledProcessError(1, args, stderr="private-error")
            output = io.StringIO()
            with patch.object(switch.prepare, "ROOT", root), \
                 patch.object(switch.inventory, "inspect", return_value={"Config": {"Env": ["POSTGRES_USER=ouf_admin"]}}), \
                 patch.object(switch.subprocess, "run", side_effect=command), \
                 patch.object(switch, "docker") as docker, contextlib.redirect_stdout(output):
                with self.assertRaises(subprocess.CalledProcessError):
                    switch.backup_restore()
            self.assertIn("createdb", docker.call_args_list[0].args)
            self.assertIn("dropdb", docker.call_args_list[-1].args)
            self.assertTrue(docker.call_args_list[-1].args[-1].startswith("ouf_managed_restore_"))
            self.assertEqual(len(list(root.glob("*.dump"))), 1)
            self.assertEqual(next(root.glob("*.dump")).stat().st_mode & 0o777, 0o600)
            self.assertNotIn("private-dump", output.getvalue())
            self.assertNotIn("private-error", output.getvalue())


if __name__ == "__main__":
    unittest.main()
