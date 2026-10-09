import base64
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import r4a_activate_cinema_source as activation

class ActivationTests(unittest.TestCase):
    challenge = '4f7a8248-ef40-4dc4-8a64-8a6101c98511'

    def card(self):
        return dict(challenge_id=self.challenge, source_id=activation.SOURCE,
            onboarding_version_id=activation.VERSION, configuration_hash=activation.HASH,
            status='CONFIRMED', configuration={'frozen': True},
            trustedApprovalRef='ths://approval-challenges/' + self.challenge,
            expires_at='2000-01-01T00:00:00Z')

    def test_confirmed_card_survives_creation_expiry(self):
        activation.check_card(self.card(), self.challenge, {'frozen': True})

    def test_drifted_confirmed_card_blocks_activation(self):
        card = self.card()
        card['configuration_hash'] = 'different'
        with self.assertRaisesRegex(RuntimeError, 'CARD_MISMATCH'):
            activation.check_card(card, self.challenge, {'frozen': True})

    def test_uncertain_post_retains_receipt_and_blocks_second_post(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            root.chmod(0o700)
            state = root / 'receipt.json'
            payload = base64.urlsafe_b64encode(json.dumps({'exp': int(time.time()) + 600}).encode()).decode().rstrip('=')
            token = 'header.' + payload + '.signature'
            before = (self.challenge, {'configuration': {'frozen': True}}, 'id', 'image')
            with patch.object(activation, 'ROOT', root), patch.object(activation, 'STATE', state), \
                patch.object(activation.os, 'geteuid', return_value=0), \
                patch.object(activation, 'context', return_value=before), \
                patch.object(activation.approval, 'verify_routes'), patch.object(activation, 'udp_gate'), \
                patch.object(activation.human, 'human_token', return_value=(token, 'subject')), \
                patch.object(activation.approval, 'request', return_value=self.card()), \
                patch('builtins.input', return_value='ATTIVO ' + activation.SOURCE), \
                patch.object(activation.worker.access, 'sync_directory'), \
                patch.object(activation, 'post_activate', side_effect=TimeoutError) as post:
                with self.assertRaises(TimeoutError):
                    activation.main('activate')
                receipt = json.loads(state.read_text())
                self.assertEqual(receipt['status'], 'UNVERIFIED_DO_NOT_REPOST')
                self.assertTrue(receipt['activationAttempted'])
                self.assertEqual(state.stat().st_mode & 0o777, 0o600)
                with self.assertRaisesRegex(RuntimeError, 'DO_NOT_REPOST'):
                    activation.main('activate')
                post.assert_called_once()

    def test_active_publication_with_drifted_hash_cannot_pass(self):
        response = dict(publication_id='p', source_id=activation.SOURCE,
            onboarding_version_id=activation.VERSION, bundle_version=1, checksum='checksum',
            bundle={'configurationHash': activation.HASH, 'status': 'ACTIVE'})
        item = dict(response, active=True)
        version = dict(state='ACTIVE', configuration_hash='drift', configuration={'frozen': True})
        with patch.object(activation, 'sql', side_effect=[json.dumps([item]), json.dumps(version)]):
            with self.assertRaisesRegex(RuntimeError, 'READBACK_MISMATCH'):
                activation.readback(response, {'frozen': True})

if __name__ == '__main__':
    unittest.main()
