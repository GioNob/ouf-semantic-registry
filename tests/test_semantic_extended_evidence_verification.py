import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from tools.verify_semantic_extended_evidence import SUBJECTS, ORIGINAL_SHA, read_sidecar, review

class ExtendedEvidenceVerificationTests(unittest.TestCase):
    def fixture(self):
        files={};images=[];scans=[];archives=[]
        for role in ('adapter','southbound'):
            sbom=b'{"artifacts":[]}'
            report=json.dumps({'matches':[]}).encode()
            files[role+'.extended.syft.json']=sbom
            files[role+'.extended.grype.json']=report
            images.append(dict(role=role,imageId='sha256:'+role,imageArchiveSha256=role,
                               extendedSyftSha256=hashlib.sha256(sbom).hexdigest()))
            archives.append(dict(role=role,imageId='sha256:'+role,sha256=role))
            scans.append(dict(role=role,reportSha256=hashlib.sha256(report).hexdigest(),
                              severityCounts={k:0 for k in ('Critical','High','Medium','Low','Negligible','Unknown')},
                              scannerSeverityThresholdMet=True))
        inventory=dict(schema='ouf.semantic-extended-dependency-inventory.v1',sourceArtifactSha256=ORIGINAL_SHA,
            imagesModified=False,originalSyftDocumentsPreserved=True,containerOperations=0,
            scannerInvoked=True,networkIsolatedScanner=True,images=images,scans=scans,
            allScannerSeverityThresholdsMet=True,dependencyCoverageAccepted=False,publisherTrustAccepted=False,
            acceptanceGranted=False,runtimeRegistered=False,startAuthorized=False)
        files['inventory.json']=json.dumps(inventory).encode()
        return files,{'candidateArchives':archives},inventory
    def test_accepts_bound_evidence_without_granting_acceptance(self):
        files,receipt,_=self.fixture()
        self.assertFalse(review(files,receipt)['acceptanceGranted'])
    def test_rejects_changed_report_and_incorrect_image(self):
        files,receipt,_=self.fixture();files['adapter.extended.grype.json']=b'{"matches":[],"changed":true}'
        with self.assertRaises(ValueError):review(files,receipt)
        files,receipt,_=self.fixture();receipt['candidateArchives'][0]['imageId']='different'
        with self.assertRaises(ValueError):review(files,receipt)
    def test_rejects_acceptance_or_hidden_threshold_override(self):
        files,receipt,inventory=self.fixture();inventory['acceptanceGranted']=True
        files['inventory.json']=json.dumps(inventory).encode()
        with self.assertRaises(ValueError):review(files,receipt)
        files,receipt,inventory=self.fixture();inventory['scans'][0]['severityCounts']['High']=1
        files['inventory.json']=json.dumps(inventory).encode()
        with self.assertRaises(ValueError):review(files,receipt)
    def test_rejects_zip_path_traversal_even_with_matching_whole_zip_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'sidecar.zip'
            with zipfile.ZipFile(path,'w') as archive:archive.writestr('../payload',b'untrusted')
            with self.assertRaises(ValueError):read_sidecar(path,hashlib.sha256(path.read_bytes()).hexdigest())

if __name__ == '__main__':unittest.main()
