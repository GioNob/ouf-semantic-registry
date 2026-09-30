import copy
from contextlib import ExitStack, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("prep_ing", ROOT / "scripts/r4a_prepare_ingestion_candidate.py")
prep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prep)


class PreparationTests(unittest.TestCase):
    def exercise(self, drift=False, repeat=False, memory_drift=False):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            root.chmod(0o700)
            props = root / "live.properties"
            props.write_text("existing.setting=preserved\n")
            config = {"User": "10002:10002", "Env": ["SECRET=hidden"],
                      "Entrypoint": ["java", "-jar", "/app/app.jar"], "Cmd": None,
                      "WorkingDir": "/app", "ExposedPorts": None}
            old = {"Id": "old", "Image": "old-image", "Config": config,
                   "State": {"Running": True},
                   "HostConfig": {"NetworkMode": "ouf-backend", "RestartPolicy": {"Name": "unless-stopped"},
                                  "Binds": [str(props) + ":" + prep.probe.PROPERTIES + ":ro"],
                                  "Memory": 1073741824, "MemorySwap": 2147483648,
                                  "LogConfig": {"Type": "json-file", "Config": {}}},
                   "NetworkSettings": {"Networks": {"ouf-backend": {}}},
                   "Mounts": [{"Type": "bind", "Source": str(props), "Destination": prep.probe.PROPERTIES, "RW": False},
                              {"Type": "bind", "Source": str(root), "Destination": prep.probe.AUTH, "RW": False}]}
            image = {"Id": "new-image", "Config": {**config, "Labels": {"org.opencontainers.image.revision": prep.REVISION}}}
            row = {"onboardingVersionId": "version", "configurationHash": "hash"}
            proof = {"schema": "ouf.ingestion.compatibility-probe.v1", "status": "PASS", **row,
                     "attestationSubmitted": False, "validatedRows": 8, "candidateCommit": prep.REVISION,
                     "candidateDeployed": False, "liveImageId": old["Image"], "candidateImageId": image["Id"]}
            proof_path = root / "proof.json"
            proof_path.write_text(json.dumps(proof))
            candidate = None
            events = []
            def inspect(name, kind="container"):
                if kind == "image": return image
                return candidate if name == prep.NAME else old
            def run(cmd):
                nonlocal candidate
                events.append(cmd[:2])
                if cmd[:2] == ["docker", "exec"]: return "14"
                if cmd[:3] == ["docker", "container", "ls"]:
                    return prep.NAME if candidate is not None else ""
                if cmd[:2] == ["docker", "create"]:
                    self.assertNotIn("hidden", " ".join(cmd))
                    self.assertEqual(cmd[cmd.index("--memory") + 1], "1073741824")
                    self.assertEqual(cmd[cmd.index("--memory-swap") + 1], "2147483648")
                    candidate = copy.deepcopy(old)
                    candidate.update(Id="created", Image="new-image", State={"Running": False, "Status": "created"})
                    candidate["HostConfig"]["RestartPolicy"]["Name"] = "no"
                    candidate["NetworkSettings"]["Networks"]["ouf-backend"]["Aliases"] = ["ouf-ingestion"]
                    for m in candidate["Mounts"]:
                        if m["Destination"] == prep.probe.PROPERTIES:
                            m["Source"] = next(root.glob("ingestion-compatibility-*/ingestion-summary.properties")).as_posix()
                    if drift: candidate["Config"]["Env"] = ["WRONG=value"]
                    if memory_drift: candidate["HostConfig"]["MemorySwap"] = -1
                    return "created"
                if cmd[:2] == ["docker", "rm"]:
                    self.assertEqual(cmd[-1], "created")
                    candidate = None
                    return ""
                self.fail(str(cmd))
            for name, value in {"ROOT": root, "STATE": root / "state.json", "PROOF": proof_path}.items():
                stack.enter_context(patch.object(prep, name, value))
            stack.enter_context(patch.object(prep.probe, "inspect", side_effect=inspect))
            stack.enter_context(patch.object(prep.probe, "run", side_effect=run))
            stack.enter_context(patch.object(prep.probe, "candidate_row", return_value=row))
            stack.enter_context(patch.object(prep.probe, "transport_settings", return_value={"ouf.ingestion.activation.gateway-url": "https://gateway"}))
            stack.enter_context(patch.object(prep.os, "geteuid", return_value=0))
            stack.enter_context(patch.object(prep.os, "chown"))
            args = SimpleNamespace(source="source", version="version", expected_hash="hash", tenant_id="tenant")
            with redirect_stdout(io.StringIO()):
                if drift or memory_drift:
                    with self.assertRaisesRegex(RuntimeError, "READBACK_MISMATCH"):
                        prep.main(args)
                    self.assertIsNone(candidate)
                    self.assertFalse(prep.STATE.exists())
                else:
                    prep.main(args)
                    if repeat: prep.main(args)
                    state = json.loads(prep.STATE.read_text())
                    self.assertEqual(state["candidate_id"], "created")
                    self.assertEqual(prep.STATE.stat().st_mode & 0o777, 0o600)
                    transport = Path(state["properties"])
                    self.assertEqual(transport.stat().st_mode & 0o777, 0o440)
                    self.assertIn("existing.setting=preserved", transport.read_text())
                    self.assertIn("ouf.ingestion.activation.gateway-url=https://gateway", transport.read_text())
                    self.assertEqual(events.count(["docker", "create"]), 1)
            self.assertEqual(props.read_text(), "existing.setting=preserved\n")
            self.assertFalse(list(root.glob("ingestion-compatibility-*/candidate.env")))
            self.assertNotIn(["docker", "start"], events)

    def test_preparation_preserves_original_and_never_starts(self):
        self.exercise()

    def test_readback_drift_removes_only_created_container(self):
        self.exercise(drift=True)

    def test_repeat_reuses_valid_owned_candidate(self):
        self.exercise(repeat=True)

    def test_duplicate_or_multiline_env_is_rejected(self):
        for values in (["A=x", "A=y"], ["A=x\nB=y"]):
            with self.assertRaises(RuntimeError):
                prep.environment({"Config": {"Env": values}})

    def test_state_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target"
            target.write_text("private")
            target.chmod(0o600)
            link = root / "link"
            link.symlink_to(target)
            with self.assertRaisesRegex(RuntimeError, "PRIVATE_FILE_UNSAFE"):
                prep.private(link, 0o600)

    def test_memory_flags_preserve_limits_and_unlimited_swap(self):
        self.assertEqual(prep.memory_flags({"Memory": 1024, "MemorySwap": -1}),
                         ["--memory", "1024", "--memory-swap", "-1"])
        self.assertEqual(prep.memory_flags({}), [])
        for memory, swap in ((True, 0), (-1, 0), (0, 1024), (1024, 512), (1024, -2)):
            with self.assertRaisesRegex(RuntimeError, "MEMORY_SETTINGS_UNSUPPORTED"):
                prep.memory_flags({"Memory": memory, "MemorySwap": swap})

    def test_binds_reject_unresolved_rw_and_extra_options(self):
        live = {"HostConfig": {"Binds": ["/host:/container:ro"]},
                "Mounts": [{"Type": "bind", "Source": "/host", "Destination": "/container", "RW": False}]}
        prep.validate_binds(live)
        for value in ("/other:/container:ro", "/host:/container:rw", "/host:/container:ro,z"):
            changed = copy.deepcopy(live)
            changed["HostConfig"]["Binds"] = [value]
            with self.assertRaises(RuntimeError):
                prep.validate_binds(changed)
        live["Mounts"][0]["Propagation"] = "rshared"
        with self.assertRaisesRegex(RuntimeError, "PROPAGATION_UNSUPPORTED"):
            prep.validate_binds(live)

    def test_candidate_memory_drift_is_rejected(self):
        self.exercise(memory_drift=True)


if __name__ == "__main__":
    unittest.main()
