import copy
from datetime import datetime, timezone
import unittest
import r4a_prepare_recovery_policy as recovery

class RecoveryPolicyTest(unittest.TestCase):
    def setUp(self):
        self.caps=recovery.descriptors()
        self.grants=recovery.grant_rows('tenant-other','00000000-0000-0000-0000-000000000001','2027-09-30T00:00:00Z',datetime(2026,9,30,tzinfo=timezone.utc))
        self.current={'policy':{'bundleId':'other','version':7,'publishedAt':'2026-09-01T00:00:00Z','capabilities':[{'capabilityId':'existing','operation':'READ','requiredScope':'existing','allowedActors':['SERVICE']}], 'grants':[{'grantId':'existing-grant','capabilityId':'existing','opaque':'preserve'}]}}
    def test_source_independent_human_grants(self):
        self.assertEqual(len(self.grants),4)
        for grant in self.grants:
            self.assertEqual(grant['tenantId'],'tenant-other')
            self.assertIsNone(grant['constraints'])
            self.assertIsNone(grant['servicePrincipalId'])
        self.assertTrue(all(c['allowedActors']==['HUMAN'] for c in self.caps))
    def test_add_only_preserves_arbitrary_existing_entries(self):
        original=copy.deepcopy(self.current)
        result=recovery.build(self.current,self.caps,self.grants)
        self.assertEqual(result['version'],8)
        self.assertEqual(result['grants'],self.current['policy']['grants']+self.grants)
        self.assertEqual(result['capabilities'],self.current['policy']['capabilities']+self.caps)
        self.assertEqual(self.current,original)
    def test_existing_recovery_requires_reconciliation(self):
        self.current['policy']['capabilities'].append(self.caps[0])
        with self.assertRaisesRegex(RuntimeError,'ALREADY_ACTIVE'):recovery.build(self.current,self.caps,self.grants)
    def test_preview_rejects_prior_grant_mutation(self):
        preview={'addedCapabilities':self.caps,'removedCapabilities':[], 'grantChanges':[{'grantId':g['grantId'],'before':None,'after':g} for g in self.grants]}
        recovery.preview_check(preview,self.caps,self.grants)
        preview['grantChanges'][0]['before']={'grantId':'existing'}
        with self.assertRaisesRegex(RuntimeError,'GRANT_DIFF'):recovery.preview_check(preview,self.caps,self.grants)
    def test_preview_rejects_additional_change(self):
        preview={'addedCapabilities':self.caps,'removedCapabilities':['existing'],'grantChanges':[]}
        with self.assertRaisesRegex(RuntimeError,'CAPABILITY_DIFF'):recovery.preview_check(preview,self.caps,self.grants)
    def test_validity_requires_future_timezone(self):
        for invalid in ('2020-01-01T00:00:00Z','2027-09-30T00:00:00'):
            with self.assertRaises(RuntimeError):recovery.grant_rows('tenant','00000000-0000-0000-0000-000000000001',invalid)

if __name__=='__main__':unittest.main()
