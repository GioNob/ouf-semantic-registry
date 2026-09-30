import unittest
from unittest.mock import patch
import r4a_install_runtime_intake_routes as install

class IntakeRoutesTests(unittest.TestCase):
    def template(self):
        return dict(id='existing',uri=install.TEMPLATE,methods=['GET'],upstream={'nodes':{'ouf-udp:8080':1}},plugins={'openid-connect':{'required_scopes':['ouf.udp.identity.attestation.read'],'bearer_only':True}})

    def test_clones_security_without_changing_existing_route(self):
        template = self.template()
        desired = install.desired_routes([template],{'datalake.write':'lake.scope','udp.candidate.write':'handoff.scope'})
        self.assertEqual(template['plugins']['openid-connect']['required_scopes'],['ouf.udp.identity.attestation.read'])
        self.assertEqual(len(desired),2)
        for value in desired.values():
            self.assertEqual(value['methods'],['POST'])
            self.assertTrue(value['plugins']['openid-connect']['bearer_only'])
            self.assertEqual(value['upstream']['nodes'],{'ouf-udp:8080':1})

    def test_duplicate_template_blocks_mutation(self):
        with self.assertRaisesRegex(RuntimeError,'NOT_UNIQUE'):
            install.desired_routes([self.template(),self.template()],{})

    def test_non_service_descriptor_is_rejected(self):
        descriptor=dict(capabilityId='datalake.write',allowedActors=['HUMAN_USER'],requiredScope='lake.scope',operation='WRITE')
        with self.assertRaisesRegex(RuntimeError,'UNSUPPORTED'):
            install.scope_for(descriptor,'datalake.write')

    def test_partial_install_rollback_removes_only_owned_matching_route(self):
        desired={'new':{'uri':'/new','methods':['POST']}}
        with patch.object(install.admin,'api',side_effect=[({'value':dict(id='new',**desired['new'])},'200'),({},'200'),({},'404')]) as api:
            install.rollback('key',desired,['new'])
            self.assertEqual([c.args[1] for c in api.call_args_list],['GET','DELETE','GET'])
            self.assertTrue(all(c.args[2]=='routes/new' for c in api.call_args_list))

    def test_concurrently_changed_route_is_not_deleted(self):
        with patch.object(install.admin,'api',return_value=({'value':{'id':'new','uri':'/changed'}},'200')) as api:
            with self.assertRaisesRegex(RuntimeError,'DRIFT_MANUAL_REVIEW'):
                install.rollback('key',{'new':{'uri':'/new'}},['new'])
            api.assert_called_once()

if __name__=='__main__':
    unittest.main()
