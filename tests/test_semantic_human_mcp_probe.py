import contextlib
import io
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import r4a_probe_semantic_human_mcp as probe


class ProbeTests(unittest.TestCase):
    def test_policy_login_requests_only_policy_scope_and_validates_human_context(self):
        a=SimpleNamespace(issuer='https://issuer/realms/ouf',subject='admin',client='ouf-human-admin',tenant='tenant-a',audience='gateway')
        scopes={'authorization.policy.admin'}
        claims={'iss':a.issuer,'sub':a.subject,'azp':a.client,'tenant_id':a.tenant,'ouf_actor_type':'HUMAN',
            'aud':a.audience,'scope':'openid authorization.policy.admin','acr':'1','exp':probe.client.time.time()+300}
        original=probe.client.validate_admin_claims
        def login():
            probe.client.oidc_post(a.issuer+'/device',{'client_id':'default','scope':'default'})
            self.assertTrue(probe.client.validate_admin_claims(claims))
            for altered in ({**claims,'sub':'other'},{**claims,'ouf_actor_type':'SERVICE'},{**claims,'scope':'mcp.connect'}):
                with self.assertRaisesRegex(ValueError,'CONTEXT_MISMATCH'):probe.client.validate_admin_claims(altered)
            return 'memory-token'
        with patch.object(probe.client,'oidc_post',return_value=(200,{})) as post,patch.object(probe.client,'device_login',side_effect=login),patch.object(probe.client,'validate_admin_claims',original),patch.object(probe.client,'ISSUER',probe.client.ISSUER),patch.object(probe.client,'ADMIN_SUB',probe.client.ADMIN_SUB),patch.object(probe.client,'REQUIRED_SCOPES',probe.client.REQUIRED_SCOPES):
            self.assertEqual(probe.human_login(a,scopes),'memory-token')
        self.assertEqual(post.call_args.args[1],{'client_id':a.client,'scope':'openid authorization.policy.admin'})

    def result(self, value):
        return {'content': [{'type': 'text', 'text': probe.json.dumps(value)}]}

    def test_exact_get_uses_authorized_search_triple(self):
        row = {'semantic_id': 'urn:test:cinema', 'revision_id': 'revision',
               'publication_set_id': 'publication'}
        replies = [{'tools': [{'name': n} for n in ('semantic.search', 'semantic.get')]},
                   self.result([row]), self.result(row)]
        with patch.object(probe.client, 'rpc', side_effect=replies) as rpc, contextlib.redirect_stdout(io.StringIO()):
            probe.probe('test-token', 'Cinema')
        call = rpc.call_args_list[2].args
        self.assertEqual(call[1], 'tools/call')
        self.assertEqual(call[2]['arguments'], {'semanticId': row['semantic_id'],
            'revisionId': row['revision_id'], 'publicationSetId': row['publication_set_id']})
        self.assertEqual([c.args[2].get('name') for c in rpc.call_args_list[1:]],
                         ['semantic.search', 'semantic.get'])

    def test_missing_discovery_stops_before_any_tool_call(self):
        with patch.object(probe.client, 'rpc', return_value={'tools': []}) as rpc, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, 'MISSING_FROM_SERVER_DISCOVERY'):
                probe.probe('test-token', 'Cinema')
        self.assertEqual(rpc.call_count, 1)

    def test_changed_reference_cannot_pass(self):
        row = {'semantic_id': 'urn:test:cinema', 'revision_id': 'revision',
               'publication_set_id': 'publication'}
        replies = [{'tools': [{'name': n} for n in ('semantic.search', 'semantic.get')]},
                   self.result([row]), self.result({**row, 'revision_id': 'other'})]
        with patch.object(probe.client, 'rpc', side_effect=replies), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, 'EXACT_REFERENCE_MISMATCH'):
                probe.probe('test-token', 'Cinema')


if __name__ == '__main__':
    unittest.main()
