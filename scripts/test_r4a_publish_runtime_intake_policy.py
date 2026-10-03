import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import r4a_publish_runtime_intake_policy as publish

class PublicationTests(unittest.TestCase):
    def setUp(self):
        root=Path(__file__).resolve().parents[1]/'catalogue'
        self.desired=[x['descriptor'] for x in json.loads((root/'r4a-ingestion-runtime-intake-capabilities.json').read_text())]
        self.grants=json.loads((root/'r4a-ingestion-runtime-intake-grants.json').read_text())
        baseline=dict(bundleId='ouf-lab-authorization',version=33,capabilities=[dict(capabilityId='old'+str(i),operation='READ',requiredScope='old'+str(i),allowedActors=['SERVICE']) for i in range(36)],grants=[{'grantId':'old'+str(i)} for i in range(77)])
        candidate=dict(baseline,version=34,capabilities=baseline['capabilities']+self.desired,grants=baseline['grants']+self.grants)
        self.state=dict(status='PASS',draftId=publish.DRAFT,revision=0,baseActiveRef=publish.BASE,targetPolicyRef=publish.TARGET,manifestHashes=publish.prepare.MANIFEST_HASHES,addedDescriptors=self.desired,addedGrants=self.grants,baselinePolicy=baseline,candidate=candidate,baselineCapabilitiesHash=publish.prepare.policy.digest(baseline['capabilities']),baselineGrantsHash=publish.prepare.policy.digest(baseline['grants']))

    def test_baseline_grant_change_cannot_be_published(self):
        publish.validate(self.state,self.desired,self.grants)
        state=copy.deepcopy(self.state)
        state['candidate']['grants'][0]['grantId']='changed'
        with self.assertRaisesRegex(RuntimeError,'ADD_ONLY_CANDIDATE'):
            publish.validate(state,self.desired,self.grants)

    def test_readback_requires_full_candidate_not_only_counts(self):
        active=dict(policyRef=publish.TARGET,policy=copy.deepcopy(self.state['candidate']))
        publish.verify(active,self.state)
        active['policy']['grants'][0]['grantId']='changed'
        with self.assertRaisesRegex(RuntimeError,'READBACK_MISMATCH'):
            publish.verify(active,self.state)

    def test_uncertain_post_retains_receipt_and_blocks_second_publish(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);root.chmod(0o700)
            receipt=root/'receipt.json'
            active=dict(policyRef=publish.BASE,policy=self.state['baselinePolicy'])
            with patch.object(publish,'ROOT',root),patch.object(publish,'RECEIPT',receipt), \
                patch.object(publish.os,'geteuid',return_value=0),patch.object(publish.sys.stdin,'isatty',return_value=True), \
                patch.object(publish.sys.stdout,'isatty',return_value=True),patch.object(publish.prepare,'manifests',return_value=([],self.desired,self.grants)), \
                patch.object(publish.prepare.policy,'read_state',return_value=self.state),patch.object(publish.prepare.human,'human_token',return_value=('token','subject')), \
                patch.object(publish.prepare.policy,'active',return_value=active),patch.object(publish,'preview'), \
                patch('builtins.input',return_value='PUBBLICO '+publish.TARGET),patch.object(publish.prepare.policy,'request',side_effect=TimeoutError) as post:
                with self.assertRaises(TimeoutError):publish.main()
                self.assertEqual(json.loads(receipt.read_text())['status'],'UNVERIFIED_DO_NOT_REPOST')
                self.assertEqual(receipt.stat().st_mode&0o777,0o600)
                with self.assertRaisesRegex(RuntimeError,'DO_NOT_REPOST'):publish.main()
                post.assert_called_once()

if __name__=='__main__':unittest.main()
