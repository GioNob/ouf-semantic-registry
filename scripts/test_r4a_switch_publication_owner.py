import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import r4a_switch_publication_owner as switch


class RollbackTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        root = Path(self.folder.name)
        self.receipt = root / 'receipt.json'
        self.old = dict(Id='old-container-id', Image='same-image')
        self.candidate = dict(Id='candidate-container-id', Image='same-image')
        self.state = dict(old=self.old, candidateId=self.candidate['Id'])
        def inspect(name):
            return self.old if name == 'ouf-onboarding' else self.candidate if name == switch.bindings.NAME else {}
        def private(path):
            return self.state if path == switch.bindings.STATE else dict(status='PASS', activePolicyRef='ouf-lab-authorization:33')
        patches = [patch.object(switch, 'ROOT', root), patch.object(switch, 'RECEIPT', self.receipt),
            patch.object(switch, 'check_prepared'),
            patch.object(switch.bindings.owner.inventory, 'inspect', side_effect=inspect),
            patch.object(switch.bindings.owner, 'runtime_guard'),
            patch.object(switch.bindings.owner, 'stable', side_effect=lambda x: x),
            patch.object(switch.bindings.owner, 'optional', return_value=None),
            patch.object(switch.rollout, 'private_json', side_effect=private),
            patch.object(switch.rollout, 'tokens_fresh'), patch.object(switch.rollout, 'ready'),
            patch.object(switch.rollout, 'history', return_value=[dict(version=str(i), success=True) for i in range(31)]),
            patch.object(switch.bindings.frozen, 'candidate_row', return_value={'state': 'APPROVED'}),
            patch.object(switch.rollout, 'docker'),
            patch.object(switch.rollout, 'backup_restore', side_effect=RuntimeError('BACKUP_FAILED'))]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self.folder.cleanup)

    def test_backup_failure_recovers_and_prevents_second_switch(self):
        with patch.object(switch.rollout, 'recover') as recover:
            with self.assertRaisesRegex(RuntimeError, 'BACKUP_FAILED'):
                switch.main('apply')
            recover.assert_called_once()
            self.assertEqual(recover.call_args.args[0]['candidate_id'], self.candidate['Id'])
            self.assertEqual(json.loads(self.receipt.read_text())['status'], 'ROLLED_BACK')
            with self.assertRaisesRegex(RuntimeError, 'RECEIPT_EXISTS'):
                switch.main('apply')
            self.assertEqual(recover.call_count, 1)

    def test_recovery_failure_is_retained_for_manual_reconciliation(self):
        with patch.object(switch.rollout, 'recover', side_effect=RuntimeError('RECOVERY_FAILED')):
            with self.assertRaisesRegex(RuntimeError, 'BACKUP_FAILED'):
                switch.main('apply')
            self.assertEqual(json.loads(self.receipt.read_text())['status'], 'MANUAL_RECOVERY_REQUIRED')


if __name__ == '__main__':
    unittest.main()
