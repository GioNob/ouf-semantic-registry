import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from tools.verify_semantic_extended_evidence import SUBJECTS, ORIGINAL_SHA, read_sidecar, review, fresh_database_pin

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
    def test_fresh_pin_rejects_stale_future_and_report_database_swap(self):
        import datetime
        pin={'status':'active','schemaVersion':'v6.1.10',
             'built':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'path':'vulnerability-db_v6.1.10_2026-10-07T00:34:45Z_1791354708.tar.zst',
             'checksum':'sha256:'+'0'*64}
        built=datetime.datetime.fromisoformat(pin['built']).timestamp()
        with self.assertRaises(ValueError):fresh_database_pin(pin,built-1)
        with self.assertRaises(ValueError):fresh_database_pin(pin,built+172801)
        files,receipt,inventory=self.fixture()
        inventory['databasePin']=pin
        for role in ('adapter','southbound'):
            raw=json.dumps({'matches':[],'descriptor':{'db':{'status':{
                'built':pin['built'],'schemaVersion':pin['schemaVersion'],'valid':True}}}}).encode()
            files[role+'.extended.grype.json']=raw
            next(s for s in inventory['scans'] if s['role']==role)['reportSha256']=hashlib.sha256(raw).hexdigest()
        files['inventory.json']=json.dumps(inventory).encode()
        self.assertFalse(review(files,receipt,database_pin=pin)['acceptanceGranted'])
        wrong=dict(pin,checksum='sha256:'+'1'*64)
        with self.assertRaises(ValueError):review(files,receipt,database_pin=wrong)
        report=json.loads(files['adapter.extended.grype.json'])
        report['descriptor']['db']['status']['built']='2020-01-01T00:00:00Z'
        raw=json.dumps(report).encode();files['adapter.extended.grype.json']=raw
        inventory['scans'][0]['reportSha256']=hashlib.sha256(raw).hexdigest()
        files['inventory.json']=json.dumps(inventory).encode()
        with self.assertRaises(ValueError):review(files,receipt,database_pin=pin)

    def test_accepts_bound_evidence_without_granting_acceptance(self):
        files,receipt,_=self.fixture()
        self.assertFalse(review(files,receipt)['acceptanceGranted'])
    def test_required_generated_proof_and_dossier_cannot_be_omitted(self):
        files,receipt,_=self.fixture()
        with self.assertRaises((ValueError,KeyError)):review(files,receipt,require_generated=True)
        with self.assertRaises((ValueError,KeyError)):review(files,receipt,require_dossier=True)
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
