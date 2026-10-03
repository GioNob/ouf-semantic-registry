import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import r4a_publish_publication_grant as publish


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        original = Path(__file__).parents[1] / 'catalogue/r4a-ingestion-runtime-publication-grant.json'
        self.manifest = self.root / 'manifest.json'
        self.manifest.write_bytes(original.read_bytes())
        self.desired = json.loads(original.read_text())[0]
        self.policy = dict(capabilities=[{'capabilityId': str(i)} for i in range(36)],
                           grants=[{'grantId': str(i)} for i in range(76)])
        self.active = dict(policyRef=publish.BASE, policy=self.policy)
        self.state = dict(draftId=publish.DRAFT, revision=0, targetPolicyRef=publish.TARGET,
                          addedGrantIds=[publish.GRANT], desiredGrants={publish.GRANT: self.desired},
                          capabilitiesHash=publish.lifecycle.digest(self.policy['capabilities']),
                          baselineGrantsHash=publish.lifecycle.digest(self.policy['grants']))
        self.state_path = self.root / 'state.json'
        self.state_path.write_text(json.dumps(self.state))
        self.state_path.chmod(0o600)
        self.receipt = self.root / 'receipt.json'
        patches = [patch.object(publish, 'ROOT', self.root), patch.object(publish, 'STATE', self.state_path),
                   patch.object(publish, 'RECEIPT', self.receipt), patch.object(publish, 'MANIFEST', self.manifest),
                   patch.object(publish, 'MANIFEST_SHA', hashlib.sha256(original.read_bytes()).hexdigest()),
                   patch.object(publish.sys.stdin, 'isatty', return_value=True),
                   patch.object(publish.sys.stdout, 'isatty', return_value=True),
                   patch.object(publish.lifecycle, 'device_login', return_value='not-a-real-token'),
                   patch.object(publish.lifecycle, 'preview', return_value={}),
                   patch('builtins.input', return_value='PUBBLICO ' + publish.TARGET)]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self.folder.cleanup)

    def test_timeout_retains_receipt_and_blocks_repost(self):
        with patch.object(publish.lifecycle, 'active', return_value=self.active), \
             patch.object(publish.lifecycle, 'request', side_effect=TimeoutError) as request:
            with self.assertRaises(TimeoutError):
                publish.main()
            self.assertEqual(json.loads(self.receipt.read_text())['status'], 'UNVERIFIED_DO_NOT_REPOST')
            with self.assertRaisesRegex(RuntimeError, 'RECEIPT_EXISTS'):
                publish.main()
            self.assertEqual(request.call_count, 1)

    def test_baseline_drift_prevents_publish(self):
        changed = dict(self.active, policyRef='ouf-lab-authorization:34')
        with patch.object(publish.lifecycle, 'active', return_value=changed), \
             patch.object(publish.lifecycle, 'request') as request:
            with self.assertRaisesRegex(RuntimeError, 'BASELINE_DRIFT'):
                publish.main()
            request.assert_not_called()
            self.assertFalse(self.receipt.exists())

    def test_success_verifies_full_preserved_baseline(self):
        after = dict(policyRef=publish.TARGET, policy=dict(self.policy, grants=self.policy['grants'] + [self.desired]))
        with patch.object(publish.lifecycle, 'active', side_effect=[self.active, self.active, after]), \
             patch.object(publish.lifecycle, 'request', return_value=(200, {'state': 'PUBLISHED'}, {})) as request:
            publish.main()
            self.assertEqual(request.call_count, 1)
            receipt = json.loads(self.receipt.read_text())
            self.assertEqual(receipt['status'], 'PASS')
            self.assertEqual(receipt['activeGrants'], 77)


if __name__ == '__main__':
    unittest.main()
