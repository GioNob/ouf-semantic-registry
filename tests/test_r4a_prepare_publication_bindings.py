import ast
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import r4a_prepare_publication_bindings as subject


class PrepareBindings(unittest.TestCase):
    def test_missing_scope_added_and_other_payload_preserved(self):
        source = 'before = "unchanged"\nrequest = {"grant_type": "client_credentials", "client_secret": secret}\nafter = "unchanged"\n'
        patched = subject.scope_patch(source).decode()
        self.assertIn(subject.CAP, patched)
        self.assertTrue(patched.startswith('before = "unchanged"\n'))
        self.assertTrue(patched.endswith('\nafter = "unchanged"\n'))
        request = ast.parse(patched).body[1].value
        values = {k.value: v for k, v in zip(request.keys, request.values)}
        self.assertEqual(values['client_secret'].id, 'secret')

    def test_existing_scope_expression_kept_and_appended(self):
        patched = ast.parse(subject.scope_patch('request={"grant_type":"client_credentials", "scope": scopes}').decode())
        request = patched.body[0].value
        values = {k.value: v for k, v in zip(request.keys, request.values)}
        self.assertIsInstance(values['scope'], ast.BinOp)
        self.assertEqual(values['scope'].left.id, 'scopes')
        self.assertEqual(values['scope'].right.value, ' ' + subject.CAP)

    def test_comments_and_utf8_offsets_do_not_corrupt_source(self):
        source = 'prefix="città"; payload={\n "grant_type": "client_credentials", # comment\n}\n'
        patched = subject.scope_patch(source).decode()
        ast.parse(patched)
        self.assertTrue(patched.startswith('prefix="città"; payload='))
        self.assertIn(subject.CAP, patched)

    def test_ambiguous_or_unpack_payload_blocks(self):
        for source in ['a={"grant_type":"client_credentials"}; b={"grant_type":"client_credentials"}',
                       'a={"grant_type":"client_credentials", **other}', 'a={}']:
            with self.assertRaises(RuntimeError):
                subject.scope_patch(source)


if __name__ == '__main__':
    unittest.main()
