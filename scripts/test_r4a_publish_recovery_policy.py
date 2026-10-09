import argparse
import copy
from datetime import datetime,timezone
import unittest
import r4a_publish_recovery_policy as publish

class RecoveryPublicationTest(unittest.TestCase):
    def setUp(self):
        self.args=argparse.Namespace(draft='00000000-0000-0000-0000-000000000010',revision=0,expected_base='other:8',target='other:9',tenant='other-tenant',subject='00000000-0000-0000-0000-000000000001',valid_until='2036-09-15T07:13:50.968730Z')
        p=publish.prepare
        caps=p.descriptors()
        grants=p.grant_rows(self.args.tenant,self.args.subject,self.args.valid_until,datetime(2026,9,30,tzinfo=timezone.utc))
        baseline={'bundleId':'other','version':8,'publishedAt':'2026-09-01T00:00:00Z','capabilities':[],'grants':[]}
        candidate=p.build({'policy':baseline},caps,grants)
        self.state=dict(status='PASS',draftId=self.args.draft,revision=0,baseActiveRef=self.args.expected_base,targetPolicyRef=self.args.target,tenant=self.args.tenant,subject=self.args.subject,addedGrants=grants,addedDescriptors=caps,baselinePolicy=baseline,candidate=candidate,baselineCapabilitiesHash=p.policy.digest([]),baselineGrantsHash=p.policy.digest([]))
    def test_generic_draft_validates(self):
        caps,grants=publish.validate(self.state,self.args)
        self.assertEqual(len(caps),4);self.assertEqual(len(grants),4)
    def test_rejects_other_draft_or_target(self):
        for key,value in [('draftId','00000000-0000-0000-0000-000000000011'),('targetPolicyRef','other:10'),('revision',1)]:
            state=copy.deepcopy(self.state);state[key]=value
            with self.assertRaises(RuntimeError):publish.validate(state,self.args)
    def test_rejects_service_or_different_tenant_grant(self):
        for key,value in [('servicePrincipalId','workload'),('tenantId','wrong')]:
            state=copy.deepcopy(self.state);state['addedGrants'][0][key]=value
            with self.assertRaises(RuntimeError):publish.validate(state,self.args)
    def test_rejects_unreviewed_existing_entry_changes(self):
        state=copy.deepcopy(self.state);state['candidate']['grants'].pop()
        with self.assertRaises(RuntimeError):publish.validate(state,self.args)
    def test_active_exact_readback_and_null_serialization(self):
        active={'policyRef':self.args.target,'policy':copy.deepcopy(self.state['candidate'])}
        for grant in active['policy']['grants']:grant.pop('constraints')
        publish.verify(active,self.state)
        active['policy']['grants'].pop()
        with self.assertRaises(RuntimeError):publish.verify(active,self.state)

if __name__=='__main__':unittest.main()
