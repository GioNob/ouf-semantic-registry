import base64,copy,hashlib,json,os,re,subprocess,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import prepare_semantic_image_sbom as m
from tools import build_semantic_image_sbom_preparer as builder
class Sbom(unittest.TestCase):
    def fixture(self):
        cfg=b'{"CI_PRIVATE_IMAGE":"NOT_PRINTED"}'
        verified={'imageId':'sha256:'+'1'*64,'configByteSha256':hashlib.sha256(cfg).hexdigest(),
            'archiveSha256':'2'*64,'archiveBytes':100,'rootfsDescriptorsHash':'3'*64}
        syft={'source':{'type':'image','metadata':{'imageID':'sha256:'+verified['configByteSha256'],
            'os':'linux','architecture':'amd64','config':base64.b64encode(cfg).decode()}},
            'descriptor':{'name':'syft','version':'1.54.0'},'artifacts':[{'id':'CI_PRIVATE_ID','name':'CI_PRIVATE_PACKAGE','version':'1'}]}
        spdx={'spdxVersion':'SPDX-2.3','SPDXID':'SPDXRef-DOCUMENT','packages':[{'name':'CI_PRIVATE_PACKAGE'}],
            'creationInfo':{'creators':['Tool: syft-1.54.0']}}
        return syft,spdx,verified
    def result(self,syft,spdx,verified):return m.summarize(json.dumps(syft).encode(),json.dumps(spdx).encode(),verified)
    def test_artifact_is_bound_to_config_identity_and_redacted_not_acceptance(self):
        result=self.result(*self.fixture());self.assertTrue(result['sbomImageIdentityBound'])
        self.assertNotIn('CI_PRIVATE',json.dumps(result))
        for field in ('dependencySbomAccepted','vulnerabilityReviewProven','imagePublisherProvenanceVerified','completeCreationAccepted','acceptanceGranted','startAuthorized'):self.assertFalse(result[field])
    def test_other_source_platform_config_or_scanner_is_denied(self):
        for path,value in [(['source','type'],'directory'),(['source','metadata','imageID'],'sha256:'+'9'*64),
            (['source','metadata','os'],'windows'),(['source','metadata','architecture'],'arm64'),
            (['source','metadata','config'],base64.b64encode(b'other').decode()),(['descriptor','version'],'other')]:
            syft,spdx,verified=self.fixture();target=syft
            for k in path[:-1]:target=target[k]
            target[path[-1]]=value
            with self.subTest(path=path),self.assertRaises(m.Denied):self.result(syft,spdx,verified)
    def test_empty_duplicate_or_incompatible_sbom_is_denied(self):
        for kind in ('empty','duplicate','other-format','missing-creator','omitted-packages'):
            syft,spdx,verified=self.fixture()
            if kind=='empty':syft['artifacts']=[]
            elif kind=='duplicate':syft['artifacts']*=2
            elif kind=='other-format':spdx['spdxVersion']='SPDX-UNKNOWN'
            elif kind=='missing-creator':spdx['creationInfo']['creators']=[]
            else:spdx['packages']=[]
            with self.subTest(kind=kind),self.assertRaises(m.Denied):self.result(syft,spdx,verified)
    def test_duplicate_json_keys_cannot_replace_identity(self):
        with self.assertRaises(m.Denied):m.decode(b'{"id":1,"id":2}')
    def test_generated_closure_is_byte_identical(self):
        root=Path(__file__).resolve().parents[1]/'tools'
        self.assertEqual((root/'semantic_image_sbom_preparer.py').read_text(),builder.build(root))
    def test_operator_wrapper_pins_exact_tested_closure_scanner_and_target_images(self):
        root=Path(__file__).resolve().parents[1]
        wrapper=root/'docs/handoffs/commands/OUF_PREPARE_IMAGE_SBOM_2026-10-05.sh';raw=wrapper.read_text()
        expected=hashlib.sha256((root/'tools/semantic_image_sbom_preparer.py').read_bytes()).hexdigest()
        self.assertEqual(re.search(r'^SOURCE_SHA256=([0-9a-f]{64})$',raw,re.M)[1],expected)
        self.assertIn(m.SCANNER_ARCHIVE_SHA256,raw)
        self.assertIn('PREPARED_SCOPE_NOT_GRANTED',raw)
        self.assertIn('a697bf75bf7d51afadadfaccd3d80537e9a5fb2a08f0d194c6dfd9462e812468',raw)
        self.assertIn('84e6b5e787e9f889ebff88161cb9a16599bafcffa236c6b54c7f779a0655940d',raw)
        subprocess.run(['/usr/bin/bash','-n',str(wrapper)],check=True,capture_output=True)
if __name__=='__main__':unittest.main()
