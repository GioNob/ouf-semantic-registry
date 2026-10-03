import contextlib
import base64
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import r4a_switch_ingestion_candidate as switch


class SwitchTests(unittest.TestCase):
    def execute(self, root, mode="apply", backup_fail=False, start_fail=False, properties_drift=False):
        settings = {"ouf.ingestion.activation.gateway-url": "https://gateway"}
        original = root / "original.properties"
        original.write_text("existing=preserved\n")
        properties = root / "candidate.properties"
        properties.write_bytes(original.read_bytes() + b"\n" + b"ouf.ingestion.activation.gateway-url=https://gateway\n")
        properties.chmod(0o440)
        config = {"User": "10002:10002", "Env": ["SECRET=private-value"],
                  "Entrypoint": ["java", "-jar", "/app/app.jar"], "Cmd": None,
                  "WorkingDir": "/app", "ExposedPorts": None}
        old = {"Id": "old-id", "Image": "old-image", "Config": config,
               "State": {"Running": True, "Status": "running"},
               "HostConfig": {"NetworkMode": "ouf-backend", "Memory": 1024, "MemorySwap": 2048,
                              "RestartPolicy": {"Name": "unless-stopped"},
                              "LogConfig": {"Type": "json-file", "Config": {}}},
               "NetworkSettings": {"Networks": {"ouf-backend": {"Aliases": ["ouf-ingestion"]}}},
               "Mounts": [{"Type": "bind", "Source": str(original), "Destination": switch.inventory.PROPERTIES, "RW": False},
                          {"Type": "bind", "Source": str(root), "Destination": switch.inventory.AUTH, "RW": False}]}
        candidate = copy.deepcopy(old)
        candidate.update(Id="new-id", Image="new-image", State={"Running": False, "Status": "created"})
        candidate["HostConfig"]["RestartPolicy"]["Name"] = "no"
        candidate["Mounts"][0]["Source"] = str(properties)
        image = {"Id": "new-image", "Config": {**config, "Labels": {"org.opencontainers.image.revision": switch.prepare.REVISION}}}
        row = {"onboardingVersionId": "version", "configurationHash": "hash"}
        proof = {"schema": "ouf.ingestion.compatibility-probe.v1", "status": "PASS", **row,
                 "attestationSubmitted": False, "validatedRows": 8, "candidateCommit": switch.prepare.REVISION,
                 "candidateImageId": "new-image"}
        state = {"revision": switch.prepare.REVISION, "candidate_name": switch.prepare.NAME,
                 "old": old, "candidate_id": "new-id", "image_id": "new-image", "proof": proof,
                 "properties": str(properties), "properties_sha256": hashlib.sha256(properties.read_bytes()).hexdigest(),
                 "source": "source", "version": "version", "expected_hash": "hash", "tenant_id": "tenant"}
        state_path = root / "state.json"
        state_path.write_text(json.dumps(state))
        state_path.chmod(0o600)
        containers = {switch.LIVE: copy.deepcopy(old), switch.prepare.NAME: candidate}
        events = []
        def inspect(name, kind="container"):
            return copy.deepcopy(image if kind == "image" else containers[name])
        def optional(name=switch.prepare.NAME):
            return copy.deepcopy(containers.get(name))
        def docker(*args):
            events.append(args)
            if args[0] == "update": containers[args[-1]]["HostConfig"]["RestartPolicy"]["Name"] = args[2]
            if args[0] == "stop": containers[args[-1]]["State"]["Running"] = False
            if args[0] == "rename": containers[args[2]] = containers.pop(args[1])
            if args[0] == "start": containers[args[1]]["State"] = {"Running": True, "Status": "running"}
            return ""
        def backup(before):
            events.append(("backup",))
            if backup_fail: raise RuntimeError("TEST_BACKUP_FAILED")
            if properties_drift:
                properties.chmod(0o600)
                properties.write_text("drift")
                properties.chmod(0o440)
            return root / "backup.dump"
        ready_replies = [None, RuntimeError("TEST_START_FAILED"), None] if start_fail else [None, None]
        with contextlib.ExitStack() as stack:
            for obj, key, value in ((switch.prepare, "ROOT", root), (switch.prepare, "STATE", state_path),
                                    (switch, "RECEIPT", root / "receipt.json")):
                stack.enter_context(patch.object(obj, key, value))
            stack.enter_context(patch.object(switch.inventory, "inspect", side_effect=inspect))
            stack.enter_context(patch.object(switch.prepare, "optional", side_effect=optional))
            stack.enter_context(patch.object(switch, "tokens_fresh", return_value=settings))
            stack.enter_context(patch.object(switch, "history", return_value=[{"version": str(n), "success": True} for n in range(1, 15)]))
            stack.enter_context(patch.object(switch, "frozen", return_value=row))
            stack.enter_context(patch.object(switch, "ready", side_effect=ready_replies))
            stack.enter_context(patch.object(switch, "backup_restore", side_effect=backup))
            stack.enter_context(patch.object(switch, "docker", side_effect=docker))
            stack.enter_context(patch.object(switch.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)))
            args = SimpleNamespace(mode=mode, source="source", version="version", expected_hash="hash", tenant_id="tenant")
            with contextlib.redirect_stdout(io.StringIO()) as output:
                if backup_fail or start_fail or properties_drift:
                    with self.assertRaises(RuntimeError): switch.main(args)
                else: switch.main(args)
            self.assertNotIn("private-value", output.getvalue())
        return events, containers, root / "receipt.json", original

    def test_plan_has_no_writes_or_runtime_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            events, containers, receipt, original = self.execute(Path(folder), mode="plan")
            self.assertEqual(events, [])
            self.assertFalse(receipt.exists())
            self.assertTrue(containers[switch.LIVE]["State"]["Running"])

    def test_apply_stops_before_backup_and_swaps_after_restore(self):
        with tempfile.TemporaryDirectory() as folder:
            events, containers, receipt, original = self.execute(Path(folder))
            self.assertLess(events.index(("stop", "--time", "60", switch.LIVE)), events.index(("backup",)))
            self.assertLess(events.index(("backup",)), events.index(("rename", switch.prepare.NAME, switch.LIVE)))
            self.assertEqual(json.loads(receipt.read_text())["status"], "PASS")
            self.assertEqual(receipt.stat().st_mode & 0o777, 0o600)
            self.assertEqual(containers[switch.LIVE]["Id"], "new-id")
            self.assertEqual(containers[switch.LIVE]["HostConfig"]["MemorySwap"], 2048)
            self.assertEqual(original.read_text(), "existing=preserved\n")

    def test_backup_failure_restarts_old_without_swapping(self):
        with tempfile.TemporaryDirectory() as folder:
            events, containers, receipt, _ = self.execute(Path(folder), backup_fail=True)
            self.assertFalse(any(e[0] == "rename" for e in events))
            self.assertEqual(containers[switch.LIVE]["Id"], "old-id")
            self.assertTrue(containers[switch.LIVE]["State"]["Running"])
            self.assertEqual(json.loads(receipt.read_text())["status"], "ROLLED_BACK")

    def test_start_failure_retains_failed_and_restores_old(self):
        with tempfile.TemporaryDirectory() as folder:
            _, containers, receipt, _ = self.execute(Path(folder), start_fail=True)
            self.assertEqual(containers[switch.LIVE]["Id"], "old-id")
            self.assertEqual(containers["ouf-ingestion-compatibility-failed-new-id"]["Id"], "new-id")
            self.assertIsNotNone(json.loads(receipt.read_text())["db_dump"])

    def test_properties_drift_after_backup_blocks_swap_and_recovers(self):
        with tempfile.TemporaryDirectory() as folder:
            events, containers, receipt, _ = self.execute(Path(folder), properties_drift=True)
            self.assertFalse(any(e[0] == "rename" for e in events))
            self.assertEqual(containers[switch.LIVE]["Id"], "old-id")

    def test_recovery_refuses_foreign_live_id(self):
        with patch.object(switch.prepare, "optional", return_value={"Id": "foreign"}), patch.object(switch, "docker") as docker:
            with self.assertRaisesRegex(RuntimeError, "ROLLBACK_LIVE_ID_MISMATCH"):
                switch.recover({"old": {"Id": "old"}, "candidate_id": "new"}, "previous", "failed")
            docker.assert_not_called()

    def test_failed_scratch_restore_drops_scratch_and_retains_dump(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def command(args, **kwargs):
                if "pg_dump" in args:
                    kwargs["stdout"].write(b"private" * 300)
                    return subprocess.CompletedProcess(args, 0)
                raise subprocess.CalledProcessError(1, args, stderr="private")
            with patch.object(switch.prepare, "ROOT", root), patch.object(switch.inventory, "inspect", return_value={"Config": {"Env": ["POSTGRES_USER=admin"]}}), patch.object(switch.subprocess, "run", side_effect=command), patch.object(switch, "docker") as docker, contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(subprocess.CalledProcessError): switch.backup_restore([])
            self.assertIn("dropdb", docker.call_args_list[-1].args)
            self.assertTrue(docker.call_args_list[-1].args[-1].startswith("ouf_ingestion_restore_"))
            self.assertEqual(next(root.glob("*.dump")).stat().st_mode & 0o777, 0o600)

    def test_workload_token_requires_semantic_scope_issuer_audience_and_freshness(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            token = root / "token"
            owner = {"Mounts": [{"Destination": switch.inventory.AUTH, "Source": str(root)}]}
            settings = {"ouf.ingestion.activation.token-file": switch.inventory.AUTH + "/token"}
            claims = {"iss": "https://auth.ouf-lab.it/realms/ouf", "aud": ["ouf-api-gateway"],
                      "exp": 1300, "scope": "ouf.semantic.read ouf.internal.object-storage.read ouf.ingestion.configuration.attest"}
            for override in ({}, {"iss": "wrong"}, {"aud": ["other"]},
                             {"exp": 1050}, {"scope": "ouf.internal.object-storage.read"}):
                payload = base64.urlsafe_b64encode(json.dumps({**claims, **override}).encode()).decode().rstrip("=")
                token.write_text("header." + payload + ".signature")
                os.utime(token, (1000, 1000))
                with patch.object(switch.inventory, "transport_settings", return_value=settings), patch.object(switch.time, "time", return_value=1000):
                    if override:
                        with self.assertRaisesRegex(RuntimeError, "TOKEN_NOT_FRESH_OR_CLAIMS_INVALID"):
                            switch.tokens_fresh(owner, "tenant")
                    else:
                        self.assertEqual(switch.tokens_fresh(owner, "tenant"), settings)


if __name__ == "__main__":
    unittest.main()
