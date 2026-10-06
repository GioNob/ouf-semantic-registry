import copy
import hashlib
import json
from pathlib import Path
import unittest
from tools.reconcile_semantic_luajit_findings import IMAGE, PROBES, SOURCE_PREFIX, reconcile


class ReconciliationRejectionTests(unittest.TestCase):
    def setUp(self):
        self.lock = json.loads(Path('tests/semantic-luajit-reconciliation-lock.json').read_bytes())
        self.files = {p: '\n'.join(v).encode() for p, v in PROBES.items()}
        self.sources = {'sourceFiles': {'compiledSourceFiles': {
            SOURCE_PREFIX+p: hashlib.sha256(data).hexdigest() for p,data in self.files.items()}}}
        self.facts = {'imageId': IMAGE, 'scannerSeverityThresholdMet': False,
                      'severityCounts': dict(Critical=2, High=1, Medium=0, Low=0, Negligible=0, Unknown=0)}
        self.report = {'matches': [
            {'vulnerability': {'id': f['id'], 'severity': f['severity'], 'namespace': 'nvd:cpe'},
             'artifact': {'name':'luajit','version':'2.1-20260824','purl':'pkg:generic/luajit@2.1-20260824'},
             'matchDetails': [{'type':'cpe-match','found':{'versionConstraint':'<= 2.1 (unknown)'},
                 'searchedBy':{'cpes':['cpe:2.3:a:luajit:luajit:2.1-20260824:*:*:*:*:*:*:*']}}]}
            for f in self.lock['findings']]}

    def evaluate(self):
        return reconcile(self.report,self.facts,self.sources,self.files,self.lock)

    def test_valid_source_proof_keeps_raw_gate_and_reports_unchanged(self):
        before=copy.deepcopy(self.report)
        out=self.evaluate()
        self.assertFalse(out['scannerSeverityThresholdMet'])
        self.assertFalse(out['acceptanceGranted'])
        self.assertFalse(out['suppressionApplied'])
        self.assertEqual(self.report,before)

    def test_tampered_compiled_source_rejected(self):
        self.files['src/lj_state.c'] += b'changed'
        with self.assertRaisesRegex(ValueError,'signed compiled manifest'): self.evaluate()

    def test_missing_fix_even_with_matching_hash_rejected(self):
        p='src/lj_snap.c'; self.files[p]=b'old source without fix'
        self.sources['sourceFiles']['compiledSourceFiles'][SOURCE_PREFIX+p]=hashlib.sha256(self.files[p]).hexdigest()
        with self.assertRaisesRegex(ValueError,'fix missing'): self.evaluate()

    def test_unexpected_cve_not_adjudicated(self):
        self.report['matches'][0]['vulnerability']['id']='CVE-2099-12345'
        with self.assertRaisesRegex(ValueError,'unexpected blocker'): self.evaluate()

    def test_changed_match_constraint_rejected(self):
        self.report['matches'][0]['matchDetails'][0]['found']['versionConstraint']='< 9.0'
        with self.assertRaisesRegex(ValueError,'unexpected range'): self.evaluate()

    def test_changed_counts_rejected(self):
        self.facts['severityCounts']['High']=0
        with self.assertRaisesRegex(ValueError,'count mismatch'): self.evaluate()

    def test_missing_or_duplicate_blocker_rejected(self):
        self.report['matches'].pop()
        with self.assertRaisesRegex(ValueError,'missing or duplicate'): self.evaluate()

    def test_changed_image_or_gate_rejected(self):
        self.facts['scannerSeverityThresholdMet']=True
        with self.assertRaisesRegex(ValueError,'image or gate'): self.evaluate()


if __name__ == '__main__':
    unittest.main()
