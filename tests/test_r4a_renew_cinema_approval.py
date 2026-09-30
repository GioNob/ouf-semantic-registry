import io
import json
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import r4a_renew_cinema_approval as subject

OLD = 'd56c8e00-de2b-4f47-a940-38b453facf2f'
NEW = '187ba4cf-dc61-4596-a187-1e83d6e019ee'


class Renewal(unittest.TestCase):
    def facts(self):
        return {'sourceId': subject.prepare.inventory.SOURCE, 'versionId': subject.prepare.inventory.VERSION,
                'hash': subject.prepare.inventory.HASH, 'status': 'CREATED', 'expired': True,
                'decisions': 0, 'unexpiredChallenges': 0}

    def test_unexpired_decided_or_other_live_challenge_block(self):
        subject.validate_expired(self.facts())
        for key, value in [('expired', False), ('decisions', 1), ('unexpiredChallenges', 1), ('hash', 'wrong'), ('status', 'CONFIRMED')]:
            with self.assertRaises(RuntimeError):
                subject.validate_expired(dict(self.facts(), **{key: value}))

    def setup_flow(self, stack, root):
        state = root / 'challenge.json'
        old = {'status': 'PASS', 'challengeId': OLD, 'sourceId': subject.prepare.inventory.SOURCE,
               'versionId': subject.prepare.inventory.VERSION, 'configurationHash': subject.prepare.inventory.HASH,
               'card': {'configuration': {}}}
        state.write_text(json.dumps(old))
        state.chmod(0o600)
        stack.enter_context(patch.object(subject.prepare, 'ROOT', root))
        stack.enter_context(patch.object(subject.prepare, 'STATE', state))
        stack.enter_context(patch.object(subject.prepare, 'verify_routes'))
        stack.enter_context(patch.object(subject.prepare, 'human_token', return_value='a.b.c'))
        stack.enter_context(patch.object(subject.prepare, 'check_card'))
        stack.enter_context(patch.object(subject, 'owner_facts', return_value=self.facts()))
        stack.enter_context(patch.object(subject.prepare.inventory.routes.helper, 'candidate_row', return_value={'state': 'IN_REVIEW', 'configuration': {}}))
        stack.enter_context(patch.object(subject.prepare.inventory.routes.helper, 'inspect', return_value={'Id': 'live', 'Image': 'image'}))
        stack.enter_context(patch('sys.stdout', io.StringIO()))
        return stack.enter_context(patch.object(subject.prepare, 'request', side_effect=[{'challenge_id': NEW}, {'expires_at': 'future', 'configuration': {}}]))

    def test_old_receipt_archived_and_only_new_challenge_created(self):
        with tempfile.TemporaryDirectory() as d, ExitStack() as stack:
            root = Path(d)
            request = self.setup_flow(stack, root)
            token, challenge = subject.renew('a' * 40, OLD)
            self.assertEqual(challenge, NEW)
            self.assertEqual([c.args[0] for c in request.call_args_list], ['POST', 'GET'])
            archive = root / ('cinema-approval-challenge-expired-' + OLD + '.json')
            self.assertEqual(json.loads(archive.read_text())['challengeId'], OLD)
            self.assertEqual(json.loads(subject.prepare.STATE.read_text())['challengeId'], NEW)
            self.assertNotIn(token, subject.prepare.STATE.read_text())

    def test_timeout_retains_archive_and_blocks_retry(self):
        with tempfile.TemporaryDirectory() as d, ExitStack() as stack:
            request = self.setup_flow(stack, Path(d))
            request.side_effect = RuntimeError('TIMEOUT')
            with self.assertRaisesRegex(RuntimeError, 'TIMEOUT'):
                subject.renew('a' * 40, OLD)
            with self.assertRaises(RuntimeError):
                subject.renew('a' * 40, OLD)
            self.assertEqual(request.call_count, 1)
            self.assertEqual(json.loads(subject.prepare.STATE.read_text())['status'], 'UNVERIFIED_DO_NOT_REPOST')

    def test_followup_uses_same_session_but_human_confirmation_function(self):
        import r4a_confirm_cinema_approval as human
        with patch.object(subject, 'renew', return_value=('a.b.c', NEW)), patch.object(human, 'main') as confirm:
            original = subject.prepare.human_token
            subject.main('a' * 40, OLD, True)
            confirm.assert_called_once_with('a' * 40, NEW)
            self.assertIs(subject.prepare.human_token, original)


if __name__ == '__main__':
    unittest.main()
