import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import refresh_discovery_sbom as refresh

class EvidenceBoundaryTests(unittest.TestCase):
    def test_real_retained_mcp_artifact_and_config_binding(self):
        raw = Path('mcp-original.zip').read_bytes()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            names = refresh.extract_subjects(raw, refresh.SPECS['mcp'], 'mcp', root)
            self.assertEqual(len(names), 4)
            document = refresh.binding(root, refresh.SPECS['mcp'], 'mcp')
            self.assertTrue(document['artifacts'])
            inventory = json.loads((root/'inventory.json').read_bytes())
            inventory['sourceCommit'] = '0'*40
            (root/'inventory.json').write_text(json.dumps(inventory))
            with self.assertRaisesRegex(ValueError, 'SOURCE_IMAGE_MISMATCH'):
                refresh.binding(root, refresh.SPECS['mcp'], 'mcp')

    def test_archive_hash_duplicate_and_path_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaisesRegex(ValueError, 'ZIP_HASH_MISMATCH'):
                refresh.extract_subjects(b'wrong', refresh.SPECS['mcp'], 'mcp', root)
            for names, reason in [(['inventory.json','inventory.json'], 'DUPLICATE'), (['../inventory.json'], 'FLAT_ARTIFACT')]:
                buffer = io.BytesIO()
                with zipfile.ZipFile(buffer,'w') as archive:
                    for name in names:
                        archive.writestr(name, '{}')
                raw = buffer.getvalue()
                with self.assertRaisesRegex(ValueError, reason):
                    refresh.extract_subjects(raw, dict(zipSha=refresh.sha(raw)), 'mcp', root)

    def test_real_original_report_and_new_denial_conditions(self):
        with zipfile.ZipFile('mcp-original.zip') as archive:
            report = json.loads(archive.read('mcp.grype.json'))
        pin = report['descriptor']['db']['status']
        self.assertTrue(refresh.scan_summary(refresh.canonical(report), pin)['thresholdMet'])
        report['matches'][0]['vulnerability']['severity'] = 'High'
        result = refresh.scan_summary(refresh.canonical(report), pin)
        self.assertFalse(result['thresholdMet'])
        self.assertEqual(result['severityCounts']['High'], 1)
        report['ignoredMatches'] = [{}]
        with self.assertRaisesRegex(ValueError, 'IGNORED_MATCHES'):
            refresh.scan_summary(refresh.canonical(report), pin)
        report['ignoredMatches'] = []
        with self.assertRaisesRegex(ValueError, 'DATABASE_REPORT_MISMATCH'):
            refresh.scan_summary(refresh.canonical(report), dict(built='old',schemaVersion=pin['schemaVersion']))

if __name__ == '__main__':
    unittest.main()
