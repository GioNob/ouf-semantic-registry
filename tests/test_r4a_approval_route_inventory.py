import sys
from pathlib import Path
import unittest
from unittest.mock import patch
import io

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import r4a_approval_route_inventory as subject


class ApprovalRoutes(unittest.TestCase):
    def test_static_wildcard_and_named_parameters(self):
        path = subject.TARGETS["CREATE"][1]
        self.assertTrue(subject.uri_matches(path, path))
        self.assertTrue(subject.uri_matches("/api/onboarding/v1/*", path))
        self.assertTrue(subject.uri_matches("/api/onboarding/v1/sources/:source/onboarding-versions/:version/approval-challenges", path))
        self.assertFalse(subject.uri_matches("/api/trusted-human/v1/*", path))

    def test_card_route_does_not_cover_confirm(self):
        self.assertTrue(subject.uri_matches("/api/trusted-human/v1/approval-challenges/:id", subject.CARD))
        self.assertFalse(subject.uri_matches("/api/trusted-human/v1/approval-challenges/:id", subject.CARD + "/confirm"))

    def test_method_and_overlapping_routes(self):
        path = subject.TARGETS["CREATE"][1]
        values = [{"uri": path, "methods": ["GET"]},
                  {"uri": path, "methods": ["POST"]},
                  {"uri": "/api/onboarding/v1/*"}]
        self.assertEqual(len(subject.candidates(values, "POST", path)), 2)

    def test_read_only_main_and_private_admin_key(self):
        live = {"Id": "live", "Image": "image", "State": {"Running": True}}
        image = {"Config": {"Labels": {"org.opencontainers.image.revision": subject.OWNER}}}
        apisix = {"State": {"Running": True}}
        def inspect(name, kind="container"):
            return image if kind == "image" else (apisix if name == "ouf-apisix" else live)
        captured = io.StringIO()
        with patch.object(subject.os, "geteuid", return_value=0), \
             patch.object(subject.routes.helper, "inspect", side_effect=inspect), \
             patch.object(subject.routes.helper, "candidate_row", return_value={"state": "IN_REVIEW"}), \
             patch.object(subject.routes, "mounted_config") as config, \
             patch.object(subject.routes, "admin_key", return_value="private-example-key"), \
             patch.object(subject.routes.helper, "run", return_value='{"list": []}') as run, \
             patch("sys.stdout", captured):
            config.return_value.read_text.return_value = "private config"
            subject.main()
        argv = run.call_args.args[0]
        self.assertNotIn("private-example-key", " ".join(argv))
        self.assertIn("private-example-key", run.call_args.kwargs["input"])
        self.assertNotIn("private-example-key", captured.getvalue())
        self.assertIn("CHALLENGE_POST=false", captured.getvalue())
        self.assertEqual(run.call_count, 1)
        self.assertNotIn("--request", argv)


if __name__ == "__main__":
    unittest.main()
