import io
import json
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import r4a_confirm_cinema_approval as subject

CHALLENGE = 'd56c8e00-de2b-4f47-a940-38b453facf2f'


class Confirm(unittest.TestCase):
    def setup_flow(self, stack, root, answer):
        receipt = root / 'challenge.json'
        receipt.write_text(json.dumps({'challengeId': CHALLENGE}))
        stack.enter_context(patch.object(subject, 'STATE', root / 'confirm.json'))
        stack.enter_context(patch.object(subject.prepare, 'ROOT', root))
        stack.enter_context(patch.object(subject.prepare, 'STATE', receipt))
        stack.enter_context(patch.object(subject.review, 'main'))
        stack.enter_context(patch.object(subject.review, 'review_sections', return_value={'review': 'content'}))
        stack.enter_context(patch.object(subject.prepare, 'check_card'))
        stack.enter_context(patch.object(subject.prepare, 'verify_routes'))
        stack.enter_context(patch.object(subject.prepare, 'human_token', return_value='a.b.c'))
        stack.enter_context(patch.object(subject.prepare, 'request', return_value={'configuration': {}}))
        stack.enter_context(patch.object(subject.prepare.inventory.routes.helper, 'inspect', return_value={'Id': 'live', 'Image': 'image'}))
        stack.enter_context(patch.object(subject.prepare.inventory.routes.helper, 'candidate_row', side_effect=[{'state': 'IN_REVIEW', 'configuration': {}}, {'state': 'IN_REVIEW', 'configuration': {}}, {'state': 'APPROVED', 'configuration': {}}]))
        stack.enter_context(patch.object(subject.prepare.inventory.routes.helper, 'run', return_value='1'))
        stack.enter_context(patch('builtins.input', return_value=answer))
        stack.enter_context(patch('sys.stdout', io.StringIO()))
        response = {'state': 'APPROVED', 'source_id': subject.prepare.inventory.SOURCE,
                    'onboarding_version_id': subject.prepare.inventory.VERSION,
                    'configuration_hash': subject.prepare.inventory.HASH, 'configuration': {}}
        return stack.enter_context(patch.object(subject, 'post_confirm', return_value=response))

    def test_cancel_does_not_post_or_reserve_receipt(self):
        with tempfile.TemporaryDirectory() as d, ExitStack() as stack:
            root = Path(d)
            post = self.setup_flow(stack, root, 'NO')
            subject.main('a' * 40, CHALLENGE)
            post.assert_not_called()
            self.assertFalse(subject.STATE.exists())

    def test_explicit_human_confirm_and_owner_readback(self):
        with tempfile.TemporaryDirectory() as d, ExitStack() as stack:
            post = self.setup_flow(stack, Path(d), 'APPROVO ' + CHALLENGE)
            subject.main('a' * 40, CHALLENGE)
            post.assert_called_once()
            receipt = json.loads(subject.STATE.read_text())
            self.assertEqual(receipt['status'], 'PASS')
            self.assertFalse(receipt['sourceActivation'])

    def test_timeout_blocks_a_second_confirmation(self):
        with tempfile.TemporaryDirectory() as d, ExitStack() as stack:
            post = self.setup_flow(stack, Path(d), 'APPROVO ' + CHALLENGE)
            post.side_effect = RuntimeError('TIMEOUT')
            with self.assertRaisesRegex(RuntimeError, 'TIMEOUT'):
                subject.main('a' * 40, CHALLENGE)
            with self.assertRaisesRegex(RuntimeError, 'DO_NOT_REPOST'):
                subject.main('a' * 40, CHALLENGE)
            self.assertEqual(post.call_count, 1)

    def test_bearer_private_and_only_confirm_path(self):
        with patch.object(subject.prepare.inventory.routes.helper, 'run', return_value='{}\n200') as run:
            subject.post_confirm(CHALLENGE, 'private.token.value')
        self.assertNotIn('private.token.value', ' '.join(run.call_args.args[0]))
        config = run.call_args.kwargs['input']
        self.assertIn('/' + CHALLENGE + '/confirm', config)
        self.assertNotIn('/activate', config)
        self.assertNotIn('location', config)


if __name__ == '__main__':
    unittest.main()
