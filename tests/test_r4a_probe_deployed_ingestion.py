import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import r4a_probe_deployed_ingestion as probe
import test_r4a_switch_ingestion_candidate as switch_tests


class DeployedProbeTests(unittest.TestCase):
    def exercise(self, failure=None, drift=False):
        with tempfile.TemporaryDirectory() as directory, contextlib.ExitStack() as stack:
            root = Path(directory)
            _, containers, receipt, _ = switch_tests.SwitchTests().execute(root)
            state_path = root / "state.json"
            state = json.loads(state_path.read_text())
            fields = {"contentHash": "sha256:asset", "adapterId": "managed-tabular-v1",
                      "adapterRuntimeVersion": "1", "semanticBindingCount": 1}
            state["proof"].update(fields)
            state_path.write_text(json.dumps(state))
            live = containers[probe.switch.LIVE]
            image = {"Id": live["Image"], "Config": {**live["Config"], "Labels": {"org.opencontainers.image.revision": probe.prepare.REVISION}}}
            row = {"onboardingVersionId": "version", "configurationHash": "hash"}
            result_proof = {"schema": "ouf.ingestion.compatibility-probe.v1", "status": "PASS",
                            **row, **fields, "validatedRows": 8, "attestationSubmitted": False}
            if failure == "denied": result_proof = {"code": "ING_EXECUTION_GATEWAY_403"}
            events = []
            def external(command, **kwargs):
                events.append(command)
                if command[:2] == ["docker", "run"]:
                    self.assertIn(live["Image"], command)
                    self.assertIn("type=bind,src=" + state["properties"] + ",dst=" + probe.inventory.PROPERTIES + ",readonly", command)
                    self.assertNotIn("private-value", " ".join(command))
                    self.assertNotIn("OUF_ING_DB", " ".join(command))
                    self.assertEqual(json.loads(kwargs["input"]), row)
                    if failure == "timeout": raise subprocess.TimeoutExpired(command, 120)
                    return SimpleNamespace(stdout=json.dumps(result_proof), returncode=int(failure == "denied"))
                return SimpleNamespace(returncode=0)
            calls = 0
            def inspect(name, kind="container"):
                nonlocal calls
                if kind == "image": return image
                calls += 1
                doc = copy.deepcopy(live)
                if drift and calls > 1: doc["Id"] = "foreign"
                return doc
            for obj, name, value in ((probe.prepare, "ROOT", root), (probe.prepare, "STATE", state_path),
                                     (probe.switch, "RECEIPT", receipt), (probe, "PROOF", root / "deployed-proof.json")):
                stack.enter_context(patch.object(obj, name, value))
            stack.enter_context(patch.object(probe.inventory, "inspect", side_effect=inspect))
            stack.enter_context(patch.object(probe.switch, "tokens_fresh", return_value={"ouf.ingestion.activation.gateway-url": "https://gateway"}))
            stack.enter_context(patch.object(probe.switch, "history", return_value=json.loads(receipt.read_text())["history"]))
            stack.enter_context(patch.object(probe.switch, "frozen", return_value=row))
            stack.enter_context(patch.object(probe.switch, "ready"))
            stack.enter_context(patch.object(probe.subprocess, "run", side_effect=external))
            args = SimpleNamespace(source="source", version="version", expected_hash="hash", tenant_id="tenant")
            with contextlib.redirect_stdout(io.StringIO()) as output:
                if failure or drift:
                    with self.assertRaises((RuntimeError, subprocess.TimeoutExpired)): probe.main(args)
                    self.assertFalse(probe.PROOF.exists())
                else:
                    probe.main(args)
                    saved = json.loads(probe.PROOF.read_text())
                    self.assertTrue(saved["candidateDeployed"])
                    self.assertFalse(saved["attestationSubmitted"])
                    self.assertEqual(saved["executionMode"], "SEPARATE_JVM_DEPLOYED_IMAGE_AND_LIVE_MOUNTS")
                    self.assertEqual(probe.PROOF.stat().st_mode & 0o777, 0o600)
            self.assertNotIn("private-value", output.getvalue())
            self.assertEqual(len(events), 2)
            self.assertEqual(events[1][:3], ["docker", "rm", "--force"])
            self.assertEqual(events[1][-1], events[0][events[0].index("--name") + 1])

    def test_pass_uses_exact_deployed_image_and_live_properties(self):
        self.exercise()

    def test_gateway_denial_cleans_probe_and_does_not_write_proof(self):
        self.exercise(failure="denied")

    def test_timeout_cleans_only_own_probe(self):
        self.exercise(failure="timeout")

    def test_live_drift_after_validation_blocks_proof(self):
        self.exercise(drift=True)


if __name__ == "__main__":
    unittest.main()
