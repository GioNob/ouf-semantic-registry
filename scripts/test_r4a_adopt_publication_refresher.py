from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import r4a_adopt_publication_refresher as adopt


class AdoptionTests(unittest.TestCase):
    def test_atomic_install_preserves_owner_mode_and_restores_original(self):
        with tempfile.TemporaryDirectory() as folder:
            script = Path(folder) / 'script.py'
            script.write_bytes(b'original')
            script.chmod(0o750)
            metadata = script.stat()
            with patch.object(adopt.prepare, 'REFRESHER', script):
                adopt.install(b'candidate', metadata)
                self.assertEqual(script.read_bytes(), b'candidate')
                self.assertEqual(script.stat().st_mode & 0o777, 0o750)
                self.assertEqual(script.stat().st_uid, metadata.st_uid)
                adopt.install(b'original', metadata)
                self.assertEqual(script.read_bytes(), b'original')

    def test_restore_installed_script_and_timer_after_validation_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            script = Path(folder) / 'script.py'
            script.write_bytes(b'original')
            with patch.object(adopt.prepare, 'REFRESHER', script), \
                 patch.object(adopt, 'system', return_value='active') as system, \
                 patch.object(adopt, 'install') as install, \
                 patch.object(adopt, 'refresh') as refresh, \
                 patch.object(adopt.prepare.frozen, 'transport_settings') as transport:
                self.assertTrue(adopt.restore(b'original', script.stat(), {'ouf-token.timer': 'active'}, True, {}))
                install.assert_called_once()
                refresh.assert_called_once()
                transport.assert_called_once()
                self.assertIn(('start', 'ouf-token.timer'), [x.args for x in system.call_args_list])

    def test_restore_failure_reports_manual_recovery_and_attempts_timer_start(self):
        with patch.object(adopt, 'system', return_value='active') as system, \
             patch.object(adopt, 'install', side_effect=OSError('disk failure')):
            self.assertFalse(adopt.restore(b'original', None, {'ouf-token.timer': 'active'}, True, {}))
            self.assertIn(('start', 'ouf-token.timer'), [x.args for x in system.call_args_list])

    def test_discovery_must_be_200_and_empty(self):
        settings = {'ouf.ingestion.activation.gateway-url': 'https://api.ouf-lab.it'}
        for response in ['{}\n403', '{"items": [{}], "nextAfter": ""}\n200']:
            with patch.object(adopt.prepare.frozen, 'run', return_value=response):
                with self.assertRaises(RuntimeError):
                    adopt.discovery(settings, 'not-a-real-token')
        with patch.object(adopt.prepare.frozen, 'run', return_value='{"items": [], "nextAfter": ""}\n200'):
            adopt.discovery(settings, 'not-a-real-token')


if __name__ == '__main__':
    unittest.main()
