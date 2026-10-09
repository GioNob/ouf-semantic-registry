import copy
import importlib.util
from pathlib import Path
import unittest
import stat
import json
from types import SimpleNamespace
from unittest.mock import patch

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
    def test_upstream_repair_preserves_full_route_and_weight(self):
        old=fixture()
        new=repair.proposed_upstream(old)
        self.assertEqual(new['upstream']['nodes'],{'ouf-udp:8080':1})
        new['upstream']['nodes']=copy.deepcopy(old['upstream']['nodes'])
        self.assertEqual(new,old)
        self.assertIsNone(repair.proposed_upstream(repair.proposed_upstream(old)))
        old['upstream']['nodes']={'foreign:8080':1}
        with self.assertRaises(ValueError): repair.proposed_upstream(old)

    def test_upstream_repair_requires_missing_old_name_and_verified_owner(self):
        old={'result':'NAME_NOT_RESOLVED'}
        new={'udpRunning':True,'resolvedAddressesMatchUdp':True,'unsignedOwnerProbe':{'httpStatus':403}}
        repair.qualify_upstream_repair(old,new)
        for bad_old,bad_new in [({},new),(old,{**new,'resolvedAddressesMatchUdp':False}),(old,{**new,'unsignedOwnerProbe':{'httpStatus':200}}),(old,{**new,'udpRunning':False})]:
            with self.assertRaises(ValueError): repair.qualify_upstream_repair(bad_old,bad_new)
        route=fixture();candidate=repair.proposed_upstream(route)
        admin=MemoryAdmin(route,fail_after_put=True)
        self.assertEqual(repair.transaction(admin,route,candidate),'BLOCKED_ORIGINAL_RESTORED')
        self.assertEqual(admin.current,repair.canonical(route))

    def test_upstream_alias_and_foreign_targets(self):
        gateway={'NetworkSettings':{'Networks':{'shared':{}}}}
        udp={'Name':'/ouf-udp','State':{'Running':True},'NetworkSettings':{'Networks':{'shared':{'IPAddress':'172.20.0.4','Aliases':['ouf-udp']}}}}
        route=fixture()
        r,host,addresses=repair.upstream_summary(route,gateway,udp)
        self.assertEqual(host,'ouf-udp-object-resolution')
        self.assertFalse(r['upstreamMatchesUdpAliasOrAddress'])
        self.assertEqual(addresses,{'172.20.0.4'})
        udp['NetworkSettings']['Networks']['shared']['Aliases'].append(host)
        self.assertTrue(repair.upstream_summary(route,gateway,udp)[0]['upstreamMatchesUdpAliasOrAddress'])
        route['upstream']['nodes']={'foreign.example:8080':1}
        self.assertIsNone(repair.upstream_summary(route,gateway,udp)[1])

    def test_generated_env_quotes_assignments_and_name_boundaries(self):
        name = 'OUF_UDP_SEARCH_OWNER_KEY'
        for line in ('env '+name+';', 'env "'+name+'";', "env '"+name+"';", 'env "'+name+'=secret"; # retained'):
            self.assertTrue(repair.env_directive_present(line, name))
        for line in ('# env '+name+';', 'env '+name+'_OTHER;', 'env OTHER='+name+';', 'env '+name):
            self.assertFalse(repair.env_directive_present(line, name))

    def test_diagnosis_only_reports_format_and_presence(self):
        route = repair.proposed(fixture())
        report = repair.diagnose_bindings(route, {'EXISTING_DELEGATION_KEY': 'a'*64, 'OUF_UDP_SEARCH_OWNER_KEY': 'b'*64}, 'env "OUF_UDP_SEARCH_OWNER_KEY";')
        self.assertFalse(report['routeChanged'])
        self.assertTrue(report['bindings']['OWNER_KEY_ENV']['generatedEnvDirectivePresent'])
        self.assertFalse(report['bindings']['DELEGATION_KEY_ENV']['generatedEnvDirectivePresent'])
        self.assertNotIn('a'*64, json.dumps(report))
        self.assertNotIn('b'*64, json.dumps(report))

    def test_observed_private_operator_owned_file_accepted(self):
        repair.validate_admin_metadata(SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_uid=1000), 1000)
        for mode, uid in ((stat.S_IFREG | 0o644, 1000), (stat.S_IFREG | 0o600, 1001), (stat.S_IFLNK | 0o777, 1000)):
            with self.assertRaises(ValueError):
                repair.validate_admin_metadata(SimpleNamespace(st_mode=mode, st_uid=uid), 1000)

    def test_admin_secret_only_in_stdin_and_namespace_fd_preserved(self):
        with patch.object(repair.os, 'open', return_value=17), patch.object(repair.subprocess, 'run') as run:
            run.return_value = SimpleNamespace(returncode=0, stdout=json.dumps(fixture()), stderr='')
            admin = repair.Admin(123, 'secret-not-an-argument', '/usr/bin/nsenter', '/usr/bin/python3')
            self.assertEqual(admin.call('GET'), fixture())
            args, kwargs = run.call_args
            self.assertNotIn('secret-not-an-argument', ' '.join(args[0]))
            self.assertEqual(kwargs['pass_fds'], (17,))
            self.assertEqual(json.loads(kwargs['input'])['key'], 'secret-not-an-argument')

    def test_admin_failure_never_exposes_raw_stderr(self):
        with patch.object(repair.os, 'open', return_value=17), patch.object(repair.subprocess, 'run') as run:
            run.return_value = SimpleNamespace(returncode=1, stdout='', stderr='private key and raw response')
            admin = repair.Admin(123, 'secret', '/usr/bin/nsenter', '/usr/bin/python3')
            with self.assertRaisesRegex(ValueError, '^ADMIN_WORKER_FAILED$'):
                admin.call('GET')

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
