import copy
import contextlib
import io
import re
import unittest
import r4a_install_recovery_routes as routes

class RecoveryRoutesTest(unittest.TestCase):
    def setUp(self):
        self.template={'id':'existing','uri':routes.TEMPLATE,'methods':['GET'],'status':1,'upstream':{'nodes':{'ouf-onboarding:8080':1}},'plugins':{'openid-connect':{'bearer_only':True,'required_scopes':['ouf.onboarding.configuration.read'],'discovery':'https://example.invalid/oidc'},'proxy-rewrite':{'uri':'/irrelevant','headers':{'X-Fake':'ignored'}}}}
        self.scopes={t[4]:t[4] for t in routes.TARGETS}
    def test_clone_preserves_oidc_and_owner_path(self):
        original=copy.deepcopy(self.template)
        desired=routes.desired_routes([self.template],self.scopes)
        self.assertEqual(self.template,original)
        for value in desired.values():
            self.assertNotIn('proxy-rewrite',value['plugins'])
            self.assertEqual(value['upstream']['nodes'],{'ouf-ingestion:8080':1})
            self.assertEqual(value['plugins']['openid-connect']['discovery'],'https://example.invalid/oidc')
            self.assertNotIn('service_id',value)
    def test_exact_uuid_actions(self):
        desired=routes.desired_routes([self.template],self.scopes)
        ids=['00000000-0000-0000-0000-000000000001','AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE']
        for ident,method,resource,action,cap in routes.TARGETS:
            rule=desired[ident]['vars'][0]
            self.assertEqual(rule[:2],['uri','~~'])
            self.assertEqual(desired[ident]['plugins']['openid-connect']['required_scopes'],[cap])
            for object_id in ids:
                self.assertIsNotNone(re.search(rule[2],routes.BASE+resource+'/'+object_id+action))
            for invalid in ['not-uuid','00000000-0000-0000-0000-000000000001/abort','00000000-0000-0000-0000-000000000001/reprocess']:
                self.assertIsNone(re.search(rule[2],routes.BASE+resource+'/'+invalid))
    def test_unknown_transforming_plugin_blocks(self):
        self.template['plugins']['body-transformer']={}
        with self.assertRaisesRegex(RuntimeError,'TEMPLATE_UNSUPPORTED'):routes.desired_routes([self.template],self.scopes)
    def test_reference_template_blocks(self):
        self.template['plugin_config_id']='reference'
        with self.assertRaises(RuntimeError):routes.desired_routes([self.template],self.scopes)
    def test_existing_prefix_collision_blocks(self):
        desired=routes.desired_routes([self.template],self.scopes)
        with self.assertRaises(RuntimeError):routes.collision([{'uri':routes.BASE+'runs/*','methods':['POST']}],desired)
        routes.collision([self.template],desired)
    def test_human_descriptor_required(self):
        document={'bundle':{'capabilities':[dict(capabilityId=cap,operation='READ' if method=='GET' else 'WRITE',requiredScope=cap,allowedActors=['HUMAN']) for _,method,_,_,cap in routes.TARGETS]}}
        self.assertEqual(routes.scopes(document),self.scopes)
        document['bundle']['capabilities'][0]['allowedActors']=['SERVICE']
        with self.assertRaises(RuntimeError):routes.scopes(document)
    def test_duplicate_template_blocks(self):
        with self.assertRaises(RuntimeError):routes.desired_routes([self.template,self.template],self.scopes)

    def test_diagnostic_reports_failure_without_credentials(self):
        self.template['plugins']['openid-connect']['client_secret']='DO_NOT_PRINT_TEST_SECRET'
        self.template['plugins']['openid-connect']['bearer_only']=False
        self.template['plugins']['serverless-pre-function']={'functions':['DO_NOT_PRINT_TEST_CODE']}
        output=io.StringIO()
        with contextlib.redirect_stdout(output):routes.template_report([self.template])
        text=output.getvalue()
        self.assertIn('BEARER_ONLY_LAYOUT=BOOLEAN_FALSE',text)
        self.assertIn('FAILED_CHECKS=OIDC_BEARER_ONLY_TRUE',text)
        self.assertNotIn('DO_NOT_PRINT_TEST_SECRET',text)
        self.assertNotIn('DO_NOT_PRINT_TEST_CODE',text)

    def test_template_functions_replaced_rate_limit_preserved(self):
        self.template['plugins']['limit-count']={'count':20,'time_window':60}
        self.template['plugins']['serverless-pre-function']={'phase':'rewrite','functions':['DO_NOT_COPY_OTHER_OWNER']}
        self.template['plugins']['serverless-post-function']={'phase':'access','functions':['DO_NOT_COPY_SERVICE_GUARD']}
        desired=routes.desired_routes([self.template],self.scopes)
        for route in desired.values():
            self.assertEqual(route['plugins']['limit-count'],{'count':20,'time_window':60})
            pre=route['plugins']['serverless-pre-function']['functions'][0]
            post=route['plugins']['serverless-post-function']['functions'][0]
            self.assertNotIn('DO_NOT_COPY',pre+post)
            self.assertIn("'x-ouf-'",pre)
            self.assertIn("actor~='HUMAN'",post)
            self.assertNotIn("clear_header('Authorization')",pre+post)

if __name__=='__main__':unittest.main()
