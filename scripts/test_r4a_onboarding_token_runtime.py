import base64
import json
import time
import unittest

from scripts import r4a_onboarding_token_runtime as runtime


def bearer(expiry, scope=runtime.SCOPE):
    body = {"iss": runtime.ISSUER, "aud": ["ouf-api-gateway"],
            "scope": scope, "ouf_actor_type": "SERVICE", "tenant_id": "ouf-lab",
            "client_id": runtime.CLIENT, "sub": "service-subject", "acr": "1", "exp": expiry}
    encoded = base64.urlsafe_b64encode(json.dumps(body).encode()).decode().rstrip("=")
    return "header." + encoded + ".signature"


class TokenRuntimeTest(unittest.TestCase):
    def test_valid_service_claims_have_refresh_margin(self):
        self.assertGreaterEqual(runtime.claims(bearer(int(time.time()) + 300)), 290)

    def test_wrong_scope_and_short_lifetime_are_rejected(self):
        for value in (bearer(int(time.time()) + 300, "other.scope"),
                      bearer(int(time.time()) + 90)):
            with self.assertRaisesRegex(RuntimeError, "TOKEN_CLAIMS_OR_LIFETIME_INVALID"):
                runtime.claims(value)


if __name__ == "__main__":
    unittest.main()
