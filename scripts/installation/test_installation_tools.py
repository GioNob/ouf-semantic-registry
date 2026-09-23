"""Offline regression tests: no Keycloak, Docker, or network dependency."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


def module(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + ".py"))
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


scopes = module("keycloak_scopes")
preflight = module("source_preflight")


class FakeAdmin:
    def __init__(self):
        self.calls = []
        # Intentionally unordered: Keycloak ?name= filtering must not be trusted.
        self.scopes = [{"id": "id-other", "name": "other", "protocol": "openid-connect"},
                       {"id": "id-existing", "name": "mcp.connect", "protocol": "openid-connect"}]
        self.bound = []

    def request(self, method, path, body=None):
        self.calls.append((method, path))
        if method == "GET" and path == "/clients":
            return [{"id": "uuid-real", "clientId": "ouf-chatgpt"},
                    {"id": "uuid-wrong", "clientId": "ouf-chatgpt-other"}], {}
        if method == "GET" and path == "/client-scopes":
            return self.scopes, {}
        if method == "POST" and path == "/client-scopes":
            self.scopes.append({"id": "00000000-0000-0000-0000-000000000001",
                                "name": body["name"], "protocol": body["protocol"]})
            return None, {"Location": "https://auth.example/admin/realms/ouf/client-scopes/00000000-0000-0000-0000-000000000001"}
        if method == "GET" and path.startswith("/client-scopes/"):
            return next(s for s in self.scopes if s["id"] == path.rsplit("/", 1)[-1]), {}
        if method == "GET" and path == "/clients/uuid-real/default-client-scopes":
            return [{"id": i} for i in self.bound], {}
        if method == "PUT" and path.startswith("/clients/uuid-real/default-client-scopes/"):
            self.bound.append(path.rsplit("/", 1)[-1])
            return None, {}
        raise AssertionError((method, path))


class InstallationToolsTest(unittest.TestCase):
    def test_keycloak_offline_plan_rejects_non_https_and_duplicate_scopes(self):
        desired = {"issuer": "http://auth.example/realms/ouf",
                   "clients": {"ouf-chatgpt": ["mcp.connect"]}}
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            scopes.validate(desired)
        desired["issuer"] = "https://auth.example/realms/ouf"
        desired["clients"]["ouf-chatgpt"].append("mcp.connect")
        with self.assertRaisesRegex(ValueError, "unique"):
            scopes.validate(desired)

    def test_keycloak_exact_existing_id_then_created_id_and_idempotence(self):
        desired = {"clients": {"ouf-chatgpt": ["mcp.connect", "operations.status.read"]}}
        fake = FakeAdmin()
        self.assertTrue(scopes.reconcile(fake, desired, sorted(desired["clients"]["ouf-chatgpt"]), False))
        self.assertFalse(any(method != "GET" for method, _ in fake.calls))
        scopes.reconcile(fake, desired, sorted(desired["clients"]["ouf-chatgpt"]), True)
        self.assertEqual(fake.bound, ["id-existing", "00000000-0000-0000-0000-000000000001"])
        fake.calls.clear()
        self.assertFalse(scopes.reconcile(fake, desired, sorted(desired["clients"]["ouf-chatgpt"]), True))
        self.assertFalse(any(method != "GET" for method, _ in fake.calls))

    def test_keycloak_ambiguous_exact_client_fails_before_writes(self):
        fake = FakeAdmin()
        original = fake.request
        def duplicates(method, path, body=None):
            data, headers = original(method, path, body)
            if path == "/clients":
                data.append({"id": "duplicate", "clientId": "ouf-chatgpt"})
            return data, headers
        fake.request = duplicates
        with self.assertRaisesRegex(RuntimeError, "ambiguous"):
            scopes.reconcile(fake, {"clients": {"ouf-chatgpt": ["mcp.connect"]}},
                             ["mcp.connect"], True)
        self.assertFalse(any(method != "GET" for method, _ in fake.calls))

    def test_preflight_refuses_incomplete_lock_without_git_access(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "six OUF"):
                preflight.check(Path(temp), {"repositories": {"ouf-mcp-server": "0" * 40}})


if __name__ == "__main__":
    unittest.main()
