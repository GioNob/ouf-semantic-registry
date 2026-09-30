import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import r4a_prepare_cinema_approval as subject


class PrepareApproval(unittest.TestCase):
    def card(self):
        return {'challenge_id': 'b6b42f1a-73fc-44e1-98ca-cd44492817de',
                'source_id': subject.inventory.SOURCE,
                'onboarding_version_id': subject.inventory.VERSION,
                'configuration_hash': subject.inventory.HASH, 'status': 'CREATED',
                'expires_at': (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
                'trustedApprovalRef': 'ths://approval-challenges/b6b42f1a-73fc-44e1-98ca-cd44492817de',
                'configuration': {'review': 'frozen'}}

    def test_card_wrong_hash_configuration_and_expiry_block(self):
        card = self.card()
        subject.check_card(card, card['challenge_id'], card['configuration'])
        for field, value in [('configuration_hash', 'wrong'), ('configuration', {}),
                             ('expires_at', '2000-01-01T00:00:00Z')]:
            bad = dict(card, **{field: value})
            with self.assertRaises((RuntimeError, ValueError)):
                subject.check_card(bad, card['challenge_id'], card['configuration'])

    def test_confirm_and_activate_are_not_requestable(self):
        for verb in ('confirm', 'activate'):
            with self.assertRaises(RuntimeError):
                subject.request('POST', '/api/trusted-human/v1/approval-challenges/' +
                                self.card()['challenge_id'] + '/' + verb, 'a.b.c')

    def test_route_drift_blocks_preparation(self):
        with patch.object(subject.inventory, 'main', side_effect=lambda: print('APPROVAL_CREATE_ROUTE_COUNT=2')):
            with patch('sys.stdout', io.StringIO()), self.assertRaisesRegex(RuntimeError, 'CREATE_ROUTE_DRIFT'):
                subject.verify_routes()

    def test_gateway_bearer_stays_off_argv_and_stdout(self):
        with patch.object(subject.inventory.routes.helper, 'run', return_value='{}\n201') as run:
            subject.request('POST', subject.inventory.TARGETS['CREATE'][1], 'private.token.value')
        self.assertNotIn('private.token.value', ' '.join(run.call_args.args[0]))
        self.assertIn('private.token.value', run.call_args.kwargs['input'])
        self.assertNotIn('--location', run.call_args.args[0])

    def exercise(self, stack, root, response=None):
        stack.enter_context(patch.object(subject, 'ROOT', root))
        stack.enter_context(patch.object(subject, 'STATE', root / 'state.json'))
        stack.enter_context(patch.object(subject, 'verify_routes'))
        stack.enter_context(patch.object(subject, 'human_token', return_value='a.b.c'))
        stack.enter_context(patch.object(subject, 'existing_count', return_value=0))
        stack.enter_context(patch.object(subject.inventory.routes.helper, 'inspect', return_value={'Id': 'live', 'Image': 'image'}))
        stack.enter_context(patch.object(subject.inventory.routes.helper, 'candidate_row', return_value={'state': 'IN_REVIEW', 'configuration': {'review': 'frozen'}}))
        return stack.enter_context(patch.object(subject, 'request', side_effect=response))

    def test_create_readback_then_resume_without_second_post(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            root.chmod(0o700)
            card = self.card()
            request = self.exercise(stack, root, [card, card, card])
            stack.enter_context(patch('sys.stdout', io.StringIO()))
            subject.main('a' * 40)
            self.assertEqual([c.args[0] for c in request.call_args_list], ['POST', 'GET'])
            state = json.loads(subject.STATE.read_text())
            self.assertEqual(state['status'], 'PASS')
            self.assertFalse(state['sourceApproval'])
            self.assertEqual(subject.STATE.stat().st_mode & 0o777, 0o600)
            subject.main('a' * 40)
            self.assertEqual([c.args[0] for c in request.call_args_list], ['POST', 'GET', 'GET'])

    def test_timeout_retains_receipt_and_blocks_second_post(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            root.chmod(0o700)
            request = self.exercise(stack, root, RuntimeError('TIMEOUT'))
            with self.assertRaises(RuntimeError):
                subject.main('a' * 40)
            self.assertEqual(json.loads(subject.STATE.read_text())['status'], 'UNVERIFIED_DO_NOT_REPOST')
            with self.assertRaisesRegex(RuntimeError, 'DO_NOT_REPOST'):
                subject.main('a' * 40)
            self.assertEqual(request.call_count, 1)


if __name__ == '__main__':
    unittest.main()
