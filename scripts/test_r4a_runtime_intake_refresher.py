import ast
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import r4a_runtime_intake_refresher as target


class ScopePatchTest(unittest.TestCase):
    def test_preserves_existing_scope_expression_once_and_surrounding_unicode(self):
        source = "# città\ncalls=[]\ndef old():\n calls.append(1)\n return 'old.read another.write'\nrequest={'grant_type':'client_credentials', 'scope':old(), 'client_secret':'private'}\n# untouched\n"
        result = target.scope_patch(source)
        self.assertTrue(result.startswith(b'# citt\xc3\xa0\n'))
        self.assertTrue(result.endswith(b'\n# untouched\n'))
        namespace = {}
        exec(result, namespace)
        self.assertEqual(namespace['calls'], [1])
        self.assertEqual(set(namespace['request']['scope'].split()), {'old.read', 'another.write', *target.SCOPES})
        self.assertEqual(namespace['request']['client_secret'], 'private')

    def test_rejects_ambiguous_unpacked_and_duplicate_dictionaries(self):
        for source in ("a={'grant_type':'client_credentials'}; b={'grant_type':'client_credentials'}",
                       "a={'grant_type':'client_credentials', **other}",
                       "a={'grant_type':'client_credentials','scope':'a','scope':'b'}"):
            with self.subTest(source=source), self.assertRaises(RuntimeError):
                target.scope_patch(source)

    def test_absent_scope_supported(self):
        namespace = {}
        exec(target.scope_patch("a={'grant_type':'client_credentials'}"), namespace)
        self.assertEqual(set(namespace['a']['scope'].split()), set(target.SCOPES))


class AdoptionTest(unittest.TestCase):
    def exercise(self, failure=False):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / 'refresh.py'
            original = b"request={'grant_type':'client_credentials','scope':'old.read'}\n"
            script.write_bytes(original)
            script.chmod(0o600)
            candidate = target.scope_patch(original.decode())
            path = root / 'candidate.py'
            path.write_bytes(candidate)
            path.chmod(0o600)
            state = root / 'state.json'
            receipt = root / 'receipt.json'
            stable = {'Id':'unchanged', 'propertiesSha256':'same'}
            queues = {'runs':['paused']}
            target.save(state, dict(status='PASS', tenant='test', candidatePath=str(path),
                beforeSha256=target.digest(original), candidateSha256=target.digest(candidate), runtime=stable, queues=queues))
            def system(*args):
                if 'ExecStart' in args:
                    return str(script) + ' ;'
                if 'Type' in args:
                    return 'oneshot'
                if 'TriggeredBy' in args:
                    return 'ouf-refresh.timer'
                if 'ActiveState' in args:
                    return 'active'
                return '0'
            def context(_):
                adopted = script.read_bytes() == candidate
                scopes = {'old.read'} | (set(target.SCOPES) if adopted else set())
                return stable, {}, 'new' if adopted else 'old', scopes
            with patch.multiple(target, ROOT=root, SCRIPT=script, STATE=state, RECEIPT=receipt), \
                 patch.object(target, 'private', side_effect=lambda p: __import__('json').loads(p.read_text())), \
                 patch.object(target, 'system', side_effect=system), patch.object(target, 'context', side_effect=context), \
                 patch.object(target, 'snapshot', return_value=queues), \
                 patch.object(target, 'discovery', side_effect=RuntimeError('DISCOVERY_NOT_AUTHORIZED') if failure else None):
                root.chmod(0o700)
                if failure:
                    with self.assertRaises(RuntimeError):
                        target.main(SimpleNamespace(mode='apply', tenant='test'))
                    self.assertEqual(script.read_bytes(), original)
                    self.assertEqual(__import__('json').loads(receipt.read_text())['status'], 'ROLLED_BACK')
                else:
                    target.main(SimpleNamespace(mode='apply', tenant='test'))
                    self.assertEqual(script.read_bytes(), candidate)
                    self.assertEqual(__import__('json').loads(receipt.read_text())['status'], 'PASS')
                with self.assertRaisesRegex(RuntimeError, 'RECEIPT_EXISTS'):
                    target.main(SimpleNamespace(mode='apply', tenant='test'))

    def test_adoption_preserves_runtime_and_old_scopes(self):
        self.exercise()

    def test_failed_owner_discovery_restores_script_and_refresh_timer(self):
        self.exercise(True)


if __name__ == '__main__':
    unittest.main()
