import io
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from scripts import r4a_service_token_smoke as smoke


class GatewaySmokeTest(unittest.TestCase):
    def test_requires_anonymous_401_and_authenticated_owner_binding_400(self):
        def reply(request, timeout):
            bearer = request.get_header("Authorization")
            code = 400 if bearer == "Bearer test-token" else 401
            raise HTTPError(request.full_url, code, "test", None, io.BytesIO())
        with patch.object(smoke.HTTP, "open", side_effect=reply):
            smoke.gateway("test-token")

    def test_owner_route_missing_is_not_accepted(self):
        def reply(request, timeout):
            code = 404 if request.get_header("Authorization") else 401
            raise HTTPError(request.full_url, code, "test", None, io.BytesIO())
        with patch.object(smoke.HTTP, "open", side_effect=reply):
            with self.assertRaisesRegex(ValueError, "AUTH_PATH_UNVERIFIED"):
                smoke.gateway("test-token")


if __name__ == "__main__":
    unittest.main()
