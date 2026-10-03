import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import r4a_enable_activation_worker as worker


class WorkerRolloutTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        root = Path(self.folder.name)
        self.receipt = root / 'receipt.json'
        self.original_path = root / 'original.properties'
        self.original = b'other.property=value\n'
        self.original_path.write_bytes(self.original)
        self.properties = root / 'candidate.properties'
        self.properties.write_bytes(worker.content(self.original))
        self.old = dict(Id='old-id', Image='image-id', Config={'Env': []}, HostConfig={}, Mounts=[])
        self.candidate = dict(Id='candidate-id')
        self.image = dict(Id='image-id')
        self.state = dict(status='PASS', old=worker.prepare.stable(self.old), candidateId='candidate-id',
            candidateName=worker.NAME, imageId='image-id', revision=worker.prepare.REVISION,
            properties=str(self.properties), propertiesSha256=worker.hashlib.sha256(self.properties.read_bytes()).hexdigest(),
            sourceId=worker.access.prepare.SOURCE, versionId=worker.access.prepare.VERSION,
            configurationHash=worker.access.prepare.HASH)
        self.history = [{'version': '14', 'success': True}]
        self.row = {'state': 'APPROVED'}
        def inspect(name):
            return self.old if name == 'ouf-ingestion' else self.candidate
        patches = [patch.object(worker, 'ROOT', root), patch.object(worker, 'RECEIPT', self.receipt),
            patch.object(worker, 'context', return_value=(self.old, self.image, self.original_path, self.original, self.row, self.history, ('0','0'))),
            patch.object(worker.rollout, 'private_json', return_value=self.state),
            patch.object(worker.prepare, 'private'), patch.object(worker.prepare, 'matches', return_value=True),
            patch.object(worker.prepare, 'optional', return_value=None),
            patch.object(worker.prepare.probe, 'inspect', side_effect=inspect),
            patch.object(worker.rollout, 'docker'),
            patch.object(worker.rollout, 'backup_restore', side_effect=RuntimeError('BACKUP_FAILURE'))]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self.folder.cleanup)

    def test_backup_failure_restores_disabled_runtime_and_blocks_retry(self):
        with patch.object(worker.rollout, 'recover') as recover:
            with self.assertRaisesRegex(RuntimeError, 'BACKUP_FAILURE'):
                worker.main('apply')
            recover.assert_called_once()
            self.assertEqual(recover.call_args.args[0], {'old': self.state['old'], 'candidate_id': 'candidate-id'})
            self.assertEqual(json.loads(self.receipt.read_text())['status'], 'ROLLED_BACK')
            with self.assertRaisesRegex(RuntimeError, 'RECEIPT_EXISTS'):
                worker.main('apply')
            self.assertEqual(recover.call_count, 1)

    def test_recovery_failure_remains_reviewable(self):
        with patch.object(worker.rollout, 'recover', side_effect=RuntimeError('RECOVERY_FAILURE')):
            with self.assertRaisesRegex(RuntimeError, 'BACKUP_FAILURE'):
                worker.main('apply')
            self.assertEqual(json.loads(self.receipt.read_text())['status'], 'MANUAL_RECOVERY_REQUIRED')

    def test_legacy_active_schedule_is_not_hidden_by_publication_filter(self):
        with patch.object(worker.access, 'queues_empty'), \
             patch.object(worker.access.preflight, 'db', return_value='1'):
            with self.assertRaisesRegex(RuntimeError, 'LEGACY_ACTIVE_SCHEDULE'):
                worker.queues_empty()


if __name__ == '__main__':
    unittest.main()
