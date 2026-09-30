import contextlib
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
import r4a_attest_ingestion_compatibility as attest


class AttestationTests(unittest.TestCase):
    def args(self, mode="apply"):
        return SimpleNamespace(mode=mode, source="source", version="68394f42-5c82-4127-a1f3-126516665749", expected_hash="sha256:hash", tenant_id="tenant")

    def proof(self):
        args = self.args()
        return {"schema": "ouf.ingestion.compatibility-probe.v1", "status": "PASS",
                "onboardingVersionId": args.version, "configurationHash": args.expected_hash,
                "attestationSubmitted": False, "candidateDeployed": True,
                "candidateCommit": attest.prepare.REVISION, "sourceId": args.source,
                "tenantId": args.tenant_id, "validatedRows": 8,
                "executionMode": "SEPARATE_JVM_DEPLOYED_IMAGE_AND_LIVE_MOUNTS",
                "liveContainerId": "live-id", "liveImageId": "image-id", "contentHash": "asset-hash",
                "adapterId": "managed-tabular-v1", "adapterRuntimeVersion": "1",
                "semanticBindingCount": 1, "propertiesSha256": "props-hash", "verifiedAtEpochSeconds": 1}

    def route(self):
        return {"uri": "/internal/onboarding/compatibility/ingestion-runtime", "methods": ["POST"],
                "upstream": {"nodes": {"ouf-onboarding:8080": 1}},
                "plugins": {"proxy-rewrite": {"uri": attest.TARGET},
                            "openid-connect": {"required_scopes": ["ouf.ingestion.configuration.attest"]}}}

    def test_route_checks_unique_scope_owner_and_enabled(self):
        route = self.route()
        self.assertEqual(attest.route_path([route], "https://gateway"), route["uri"])
        for changed in ({**route, "status": 0}, {**route, "upstream_id": "extra"},
                        {**route, "hosts": ["other"]}, {**route, "plugins": {}}):
            with self.assertRaises(RuntimeError): attest.route_path([changed], "https://gateway")
        with self.assertRaises(RuntimeError): attest.route_path([route, route], "https://gateway")

    def test_body_binds_exact_production_evidence_and_rejects_wrong_context(self):
        proof = self.proof()
        body = attest.body_for(proof, self.args())
        evidence = json.loads(body["detail"])
        self.assertEqual(evidence["liveImageId"], "image-id")
        self.assertEqual(evidence["configurationHash"], self.args().expected_hash)
        for key, value in (("candidateDeployed", False), ("validatedRows", 7),
                           ("tenantId", "wrong"), ("candidateCommit", "wrong")):
            with self.assertRaises(RuntimeError): attest.body_for({**proof, key: value}, self.args())

    def exercise(self, root, mode="apply", failed=False):
        args, proof = self.args(mode), self.proof()
        body = attest.body_for(proof, args)
        response = {"attestation_id": "57499699-dbc5-419d-a14b-27cd3604ec6f", "onboarding_version_id": args.version,
                    "configuration_hash": args.expected_hash, "consumer": "INGESTION_RUNTIME", "compatible": True,
                    "detail": body["detail"]}
        live = {"Id": "live-id", "Image": "image-id", "Config": {}, "HostConfig": {},
                "Mounts": [{"Destination": attest.inventory.PROPERTIES, "Source": "/private/props"}]}
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(attest.prepare, "ROOT", root))
            stack.enter_context(patch.object(attest, "RECEIPT", root / "receipt.json"))
            refresh = stack.enter_context(patch.object(attest.deployed, "main"))
            stack.enter_context(patch.object(attest.switch, "private_json", return_value=proof))
            stack.enter_context(patch.object(attest.inventory, "inspect", return_value=live))
            stack.enter_context(patch.object(attest.switch, "tokens_fresh", return_value={"ouf.ingestion.activation.gateway-url": "https://gateway"}))
            stack.enter_context(patch.object(attest, "resolve_route", return_value="/public/attest"))
            stack.enter_context(patch.object(attest.switch, "frozen", return_value={"state": "IN_REVIEW", "configurationHash": args.expected_hash}))
            stack.enter_context(patch.object(attest.deployed, "digest", return_value="props-hash"))
            stack.enter_context(patch.object(attest, "existing_count", return_value=0))
            post = stack.enter_context(patch.object(attest, "post", side_effect=RuntimeError("TEST_TIMEOUT") if failed else None, return_value=response))
            readback = stack.enter_context(patch.object(attest, "readback", return_value=response))
            with contextlib.redirect_stdout(io.StringIO()):
                if failed:
                    with self.assertRaisesRegex(RuntimeError, "TEST_TIMEOUT"): attest.main(args)
                else: attest.main(args)
            refresh.assert_called_once_with(args)
            if mode == "plan":
                post.assert_not_called()
                readback.assert_not_called()
                self.assertFalse(attest.RECEIPT.exists())
            else:
                post.assert_called_once()
                receipt = json.loads(attest.RECEIPT.read_text())
                self.assertTrue(receipt["post_attempted"])
                self.assertEqual(receipt["status"], "UNVERIFIED_DO_NOT_REPOST" if failed else "PASS")
                self.assertEqual(attest.RECEIPT.stat().st_mode & 0o777, 0o600)
                with self.assertRaisesRegex(RuntimeError, "NO_REPOST"): attest.main(args)
                self.assertEqual(post.call_count, 1)

    def test_plan_refreshes_proof_without_post_or_receipt(self):
        with tempfile.TemporaryDirectory() as folder: self.exercise(Path(folder), mode="plan")

    def test_apply_posts_once_and_verifies_owner_readback(self):
        with tempfile.TemporaryDirectory() as folder: self.exercise(Path(folder))

    def test_timeout_retains_receipt_and_blocks_repost(self):
        with tempfile.TemporaryDirectory() as folder: self.exercise(Path(folder), failed=True)

    def test_post_keeps_token_and_body_on_stdin_without_automatic_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "token").write_text("header.payload.signature")
            live = {"Mounts": [{"Destination": attest.inventory.AUTH, "Source": str(root)}]}
            settings = {"ouf.ingestion.activation.gateway-url": "https://gateway",
                        "ouf.ingestion.activation.token-file": attest.inventory.AUTH + "/token"}
            with patch.object(attest.inventory, "run", return_value='{"ok":true}\n201') as run:
                self.assertEqual(attest.post({"detail": 'a "quoted" detail'}, live, settings, "/public/attest", "correlation"), {"ok": True})
            argv = run.call_args.args[0]
            self.assertNotIn("header.payload.signature", " ".join(argv))
            self.assertNotIn("--retry", argv)
            config = run.call_args.kwargs["input"]
            self.assertIn("Authorization: Bearer header.payload.signature", config)
            self.assertIn('request = "POST"', config)

    def test_reserve_does_not_overwrite_existing_receipt(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(attest, "RECEIPT", Path(folder) / "receipt.json"):
            attest.reserve({"correlation_id": "first"})
            with self.assertRaises(FileExistsError): attest.reserve({"correlation_id": "second"})
            self.assertEqual(json.loads(attest.RECEIPT.read_text())["correlation_id"], "first")


if __name__ == "__main__":
    unittest.main()
