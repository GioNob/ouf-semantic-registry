import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('repair', Path(__file__).parents[1] / 'scripts' / 'repair_search_owner_binding.py')
repair = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repair)


def fixture():
    return {'id': repair.ROUTE, 'uri': repair.URI, 'methods': ['POST'],
            'create_time': 1, 'update_time': 2,
            'plugins': {'openid-connect': {'scope': 'unchanged'}, 'serverless-post-function': {'functions': [
                'return function(conf, ctx)\nlocal DELEGATION_KEY_ENV = "EXISTING_DELEGATION_KEY"\n'
                "local capability = 'urban.object.search'\nlocal purpose = 'udp-object-search-owner'\n"
                "local receipt = 'X-OUF-UDP-Search-Receipt'\nlocal owner_key = os.getenv(OWNER_KEY_ENV)\nend"]}},
            'upstream': {'nodes': {'ouf-udp-object-resolution:8080': 1}}}


class MemoryAdmin:
    def __init__(self, route, fail_after_put=False):
        self.current = copy.deepcopy(route)
        self.puts = []
        self.fail_after_put = fail_after_put

    def call(self, method, route=None):
        if method == 'GET':
            return copy.deepcopy(self.current)
        self.current = copy.deepcopy(route)
        self.puts.append(copy.deepcopy(route))
        if self.fail_after_put:
            self.fail_after_put = False
            raise OSError('ambiguous transport failure after committed write')
        return copy.deepcopy(route)


class BindingRepairTest(unittest.TestCase):
    def test_only_missing_declaration_changes(self):
        old = fixture()
        new = repair.proposed(old)
        self.assertNotEqual(new, old)
        source = new['plugins']['serverless-post-function']['functions'][0]
        self.assertEqual(source.count(repair.MARKER), 1)
        new['plugins']['serverless-post-function']['functions'][0] = source.replace(repair.MARKER, '', 1)
        self.assertEqual(new, old)

    def test_existing_and_foreign_binding_never_overwritten(self):
        new = repair.proposed(fixture())
        self.assertIsNone(repair.proposed(new))
        new['plugins']['serverless-post-function']['functions'][0] = new['plugins']['serverless-post-function']['functions'][0].replace('OUF_UDP_SEARCH_OWNER_KEY', 'FOREIGN_KEY')
        with self.assertRaises(ValueError):
            repair.proposed(new)

    def test_wrong_route_denied(self):
        old = fixture()
        old['uri'] = '/unrelated'
        with self.assertRaises(ValueError):
            repair.proposed(old)

    def test_success_readback_and_ambiguous_write_rollback(self):
        old = fixture()
        new = repair.proposed(old)
        admin = MemoryAdmin(old)
        self.assertEqual(repair.transaction(admin, old, new), 'REPAIRED_AND_READBACK_VERIFIED')
        self.assertEqual(admin.current, repair.canonical(new))
        admin = MemoryAdmin(old, fail_after_put=True)
        self.assertEqual(repair.transaction(admin, old, new), 'BLOCKED_ORIGINAL_RESTORED')
        self.assertEqual(admin.current, repair.canonical(old))

    def test_concurrent_drift_denied_before_write(self):
        old = fixture()
        admin = MemoryAdmin(old)
        admin.current['plugins']['openid-connect']['scope'] = 'concurrent-value'
        with self.assertRaises(ValueError):
            repair.transaction(admin, old, repair.proposed(old))
        self.assertEqual(admin.puts, [])


if __name__ == '__main__':
    unittest.main()
