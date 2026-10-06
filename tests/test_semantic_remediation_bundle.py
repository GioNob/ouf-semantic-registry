"""Reject ambiguous or corrupted handoff input before any target work."""
import io,tempfile,unittest,zipfile,hashlib
from pathlib import Path
from tools import qualify_semantic_remediation_bundle as q
class Bundle(unittest.TestCase):
    def test_duplicate_or_escaping_zip_names_are_rejected(self):
        for names in (('receipt.json','receipt.json'),('../receipt.json',),('/receipt.json',),('evil\\receipt.json',)):
            raw=io.BytesIO()
            with zipfile.ZipFile(raw,'w') as z:
                for name in names:z.writestr(name,b'owned fixture')
            raw.seek(0)
            with zipfile.ZipFile(raw) as z,self.assertRaises(ValueError):q.inventory(z)
    def test_wrong_whole_artifact_hash_prevents_any_output(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'must-remain-absent'
            with self.assertRaises(ValueError):q.qualify(io.BytesIO(b'corrupt zip'),root,'0'*64,'0'*40)
            self.assertFalse(root.exists())
    def test_native_report_missing_or_failed_prevents_archive_read(self):
        for failed in (False,True):
            raw=io.BytesIO()
            facts={'scannerSeverityThresholdMet':False}
            with zipfile.ZipFile(raw,'w') as z:
                if failed:z.writestr('native/native-coverage.json',b'{"scannerSeverityThresholdMet":false}')
                else:z.writestr('unrelated.txt',b'fixture')
            raw.seek(0)
            with zipfile.ZipFile(raw) as z,self.assertRaises(ValueError):
                q.native_evidence(z,q.inventory(z),{'includeOwnedNativeBinariesRequested':True,'nativeScan':facts},
                    {},{},b'',Path('/must-not-read-image'))
    def test_high_finding_receipt_cannot_qualify(self):
        raw=io.BytesIO()
        with zipfile.ZipFile(raw,'w') as z:z.writestr('receipt.json',b'{"schema":"ouf.semantic-image-remediation-experiment.v1","candidate":"alpine-ubuntu-source-fixed","semanticBuildCommit":"0000000000000000000000000000000000000000","allScannerSeverityThresholdsMet":false}')
        raw.seek(0);expected=hashlib.sha256(raw.getvalue()).hexdigest()
        with tempfile.TemporaryDirectory() as d,self.assertRaises(ValueError):q.qualify(raw,Path(d),expected,'0'*40)
if __name__=='__main__':unittest.main()

