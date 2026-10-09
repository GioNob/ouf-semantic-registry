import contextlib
import io
import json
import unittest
from unittest.mock import patch

import r4a_semantic_inventory as inventory


class SemanticInventoryTest(unittest.TestCase):
    def test_empty_publication_stays_explicit_and_read_only(self):
        response = {'published_sets': 0, 'active_artifacts': 0,
                    'latest_set_id': None, 'latest_set_no': None,
                    'member_count': 0, 'members': []}
        with patch.object(inventory.subprocess, 'run') as run:
            run.return_value.returncode = 0
            run.return_value.stdout = json.dumps(response)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                inventory.main()
        args = run.call_args.args[0]
        self.assertIn('default_transaction_read_only=on', args[3])
        self.assertIn('SEMANTIC_LATEST_SET=NONE', output.getvalue())
        self.assertIn('NO_WRITES=true', output.getvalue())

    def test_published_member_is_pinned_to_version_and_revision(self):
        response = {'published_sets': 1, 'active_artifacts': 1,
                    'latest_set_id': 'set-1', 'latest_set_no': 1,
                    'member_count': 1, 'members': [{'semantic_id': 'https://example.org/Cinema',
                    'artifact_type': 'CLASS', 'semantic_version': '1.0.0',
                    'revision_id': 'rev-1', 'namespace': 'https://example.org/',
                    'local_name': 'Cinema'}]}
        with patch.object(inventory.subprocess, 'run') as run:
            run.return_value.returncode = 0
            run.return_value.stdout = json.dumps(response)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                inventory.main()
        self.assertIn('SEMANTIC_PUBLISHED_MEMBER_COUNT=1', output.getvalue())
        self.assertIn('"semantic_version": "1.0.0"', output.getvalue())


if __name__ == '__main__':
    unittest.main()
