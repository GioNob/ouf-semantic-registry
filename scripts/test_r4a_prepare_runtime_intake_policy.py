import copy
import json
from pathlib import Path
import unittest
import r4a_prepare_runtime_intake_policy as prepare

class IntakePolicyTests(unittest.TestCase):
    def setUp(self):
        root=Path(__file__).resolve().parents[1]/'catalogue'
        self.desired=[x['descriptor'] for x in json.loads((root/'r4a-ingestion-runtime-intake-capabilities.json').read_text())]
        self.grants=json.loads((root/'r4a-ingestion-runtime-intake-grants.json').read_text())
        self.current={'policy':dict(bundleId='installation-policy',version=5,publishedAt='2026-01-01T00:00:00Z',capabilities=[dict(capabilityId='existing',operation='READ',requiredScope='existing',allowedActors=['SERVICE'])],grants=[{'grantId':'existing'}])}

    def test_one_candidate_preserves_every_baseline_entry(self):
        old=copy.deepcopy(self.current)
        candidate=prepare.build(self.current,self.desired,self.grants)
        self.assertEqual(self.current,old)
        self.assertEqual(candidate['capabilities'][:-2],old['policy']['capabilities'])
        self.assertEqual(candidate['grants'][:-2],old['policy']['grants'])
        self.assertEqual(candidate['version'],6)

    def test_grants_are_service_and_tenant_scoped_for_all_sources(self):
        for grant in self.grants:
            self.assertEqual(grant['constraints']['resourceAttributes'],{'module':'UDP'})
            self.assertEqual(grant['constraints']['resourceType'],'ingestion-intake')
            self.assertEqual(grant['servicePrincipalId'],'ouf-ingestion')
            self.assertEqual(grant['tenantId'],'ouf-lab')
            self.assertIsNone(grant['subjectId'])
        self.assertNotIn('cinema',json.dumps(self.grants))

    def test_preview_requires_exact_add_only_capabilities_and_grants(self):
        preview=dict(addedCapabilities=self.desired,removedCapabilities=[],grantChanges=[dict(grantId=x['grantId'],before=None,after=x) for x in self.grants])
        prepare.preview_check(preview,self.desired,self.grants)
        preview['grantChanges'][0]['before']={'grantId':'existing'}
        with self.assertRaisesRegex(RuntimeError,'GRANT_DIFF_MISMATCH'):
            prepare.preview_check(preview,self.desired,self.grants)

    def test_active_capability_conflict_blocks_draft(self):
        self.current['policy']['capabilities'].append(dict(self.desired[0],requiredScope='other'))
        with self.assertRaisesRegex(ValueError,'SEMANTIC_CONFLICT'):
            prepare.build(self.current,self.desired,self.grants)

if __name__=='__main__':
    unittest.main()
