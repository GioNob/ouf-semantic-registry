import contextlib
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import r4a_probe_semantic_human_mcp as probe


class ProbeTests(unittest.TestCase):
    def result(self, value):
        return {'content': [{'type': 'text', 'text': probe.json.dumps(value)}]}

    def test_exact_get_uses_authorized_search_triple(self):
        row = {'semantic_id': 'urn:test:cinema', 'revision_id': 'revision',
               'publication_set_id': 'publication'}
        replies = [{'tools': [{'name': n} for n in ('semantic.search', 'semantic.get')]},
                   self.result([row]), self.result(row)]
        with patch.object(probe.client, 'rpc', side_effect=replies) as rpc, contextlib.redirect_stdout(io.StringIO()):
            probe.probe('test-token', 'Cinema')
        call = rpc.call_args_list[2].args
        self.assertEqual(call[1], 'tools/call')
        self.assertEqual(call[2]['arguments'], {'semanticId': row['semantic_id'],
            'revisionId': row['revision_id'], 'publicationSetId': row['publication_set_id']})
        self.assertEqual([c.args[2].get('name') for c in rpc.call_args_list[1:]],
                         ['semantic.search', 'semantic.get'])

    def test_missing_discovery_stops_before_any_tool_call(self):
        with patch.object(probe.client, 'rpc', return_value={'tools': []}) as rpc, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, 'MISSING_FROM_SERVER_DISCOVERY'):
                probe.probe('test-token', 'Cinema')
        self.assertEqual(rpc.call_count, 1)

    def test_changed_reference_cannot_pass(self):
        row = {'semantic_id': 'urn:test:cinema', 'revision_id': 'revision',
               'publication_set_id': 'publication'}
        replies = [{'tools': [{'name': n} for n in ('semantic.search', 'semantic.get')]},
                   self.result([row]), self.result({**row, 'revision_id': 'other'})]
        with patch.object(probe.client, 'rpc', side_effect=replies), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, 'EXACT_REFERENCE_MISMATCH'):
                probe.probe('test-token', 'Cinema')


if __name__ == '__main__':
    unittest.main()
