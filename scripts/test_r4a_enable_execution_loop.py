import unittest
from unittest.mock import patch
import r4a_enable_execution_loop as execution
from test_r4a_enable_activation_worker import WorkerRolloutTests

class ExecutionRecoveryTests(WorkerRolloutTests):
    def setUp(self):
        super().setUp()
        self.original = b'other.property=value\nouf.ingestion.activation.enabled=true\n'
        self.original_path.write_bytes(self.original)
        execution.worker.context.return_value = (self.old, self.image, self.original_path, self.original, self.row, self.history, ('0', '0', '0'))
        self.properties.write_bytes(execution.worker.content(self.original))
        self.state['propertiesSha256'] = execution.worker.hashlib.sha256(self.properties.read_bytes()).hexdigest()

    def test_legacy_active_schedule_is_not_hidden_by_publication_filter(self):
        with patch.object(execution.worker.access, 'queues_empty'), patch.object(execution.worker.access.preflight, 'db', return_value='1'):
            with self.assertRaisesRegex(RuntimeError, 'LEGACY_ACTIVE_SCHEDULE'):
                execution.original_queues()

class ExecutionOutboxTests(unittest.TestCase):
    def test_pending_handoff_blocks_switch_without_mutation(self):
        with patch.object(execution, 'original_queues'), patch.object(execution.worker.rollout, 'sql', return_value='1'), patch.object(execution.worker.rollout, 'docker') as docker:
            with self.assertRaisesRegex(RuntimeError, 'EXISTING_HANDOFFS_REVIEW_REQUIRED'):
                execution.queues_empty()
            docker.assert_not_called()

    def test_completed_receipt_records_execution_and_preserves_activation(self):
        with patch.object(execution, 'original_save') as saved:
            execution.save(dict(status='PASS', workerEnabled=True))
            value = saved.call_args.args[0]
            self.assertTrue(value['executionEnabled'])
            self.assertTrue(value['activationEnabled'])
            self.assertNotIn('workerEnabled', value)
            self.assertEqual(value['enabledProperty'], 'ouf.ingestion.execution.enabled')

if __name__ == '__main__':
    unittest.main()
