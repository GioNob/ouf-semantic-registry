import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import r4a_reconcile_intake_service_guards as fix


class ServiceGuardTests(unittest.TestCase):
    def route(self):
        return {'id':'id','uri':'/api/internal/v1/lake/objects','methods':['POST'],'upstream':{'nodes':{'ouf-udp:8080':1}},'plugins':{'openid-connect':{'bearer_only':True,'required_scopes':['datalake.write'],'client_secret':'PRIVATE'},'limit-count':{'count':10},'serverless-pre-function':{'functions':['OLD_PREFLIGHT_SCOPE']},'serverless-post-function':{'functions':['OLD_OWNER_GUARD']}}}

    def test_legacy_lua_replaced_preserving_oidc_limits_and_source(self):
        route=self.route();result=fix.patch_route(route,'datalake.write')
        self.assertEqual(route['plugins']['serverless-pre-function']['functions'],['OLD_PREFLIGHT_SCOPE'])
        self.assertEqual(result['plugins']['openid-connect'],route['plugins']['openid-connect'])
        self.assertEqual(result['plugins']['limit-count'],route['plugins']['limit-count'])
        lua=json.dumps([result['plugins']['serverless-pre-function'],result['plugins']['serverless-post-function']])
        self.assertNotIn('OLD_',lua);self.assertIn('SERVICE',lua)
        self.assertNotIn('clear_header(\'Authorization\')',lua)
        self.assertEqual(result['plugins']['serverless-post-function']['phase'],'access')

    def test_unknown_security_plugin_and_rewrite_are_refused(self):
        for key in ('unreviewed-plugin','proxy-rewrite'):
            route=self.route();route['plugins'][key]={'value':'unknown'}
            with self.assertRaises(RuntimeError):fix.patch_route(route,'datalake.write')

    def test_probe_body_cannot_enter_pinned_lake_storage(self):
        args=SimpleNamespace(run='86809c17-3354-45ca-a7e6-57e903944b24',source='source-test')
        for direct in (True,False):
            with patch.object(fix.helper,'run',return_value='{}\n400') as tool:
                self.assertEqual(fix.negative_probe(args,'hidden',direct),'400')
                config=tool.call_args.kwargs['input']
                self.assertNotIn('contentBase64',config)
                self.assertIn('source-test',config)
                self.assertNotIn('hidden',' '.join(tool.call_args.args[0]))


if __name__=='__main__':unittest.main()
