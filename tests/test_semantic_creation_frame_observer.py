import hashlib,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.build_semantic_creation_frame_observer import build
from test_semantic_oci_policy import fixture

class Observer(unittest.TestCase):
    def test_generated_artifact_matches_reviewed_closure_exactly(self):
        root=Path(__file__).resolve().parents[1]/'tools'
        self.assertEqual((root/'semantic_creation_frame_observer.py').read_text(),build(root))

    def test_isolated_cli_denies_missing_invalid_private_inputs_without_content_or_path_output(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('OUF_TEST_ROOT')) as dirname:
            root=Path(dirname);root.chmod(0o700)
            doc,expected,spec,startup,hooks,schema=fixture()
            policy={'schema':'ouf.semantic-configured-creation-frame-policy.v1','expectedOci':doc,
                'manifest':spec,'startup':startup,'approvedHooks':hooks,'sources':[]}
            filename=root/'CI_PRIVATE_POLICY.json';filename.write_text(json.dumps(policy));filename.chmod(0o600)
            helper=Path(__file__).resolve().parents[1]/'tools/semantic_creation_frame_observer.py'
            command=['/usr/bin/python3','-I','-B',str(helper),'--configuration',str(filename)]
            request={'pid':0,'generation':{},'bundlePath':str(root/'CI_PRIVATE_MISSING.json'),
                'applicationHash':'a'*64,'policyHash':hashlib.sha256(filename.read_bytes()).hexdigest()}
            variants=[json.dumps(request).encode(),b'{"CI_PRIVATE":1,"CI_PRIVATE":2}',b'x'*4097]
            for raw in variants:
                reply=subprocess.run(command,input=raw,capture_output=True,timeout=6)
                self.assertEqual(reply.returncode,1);self.assertEqual(reply.stdout,b'')
                self.assertEqual(reply.stderr,b'SEMANTIC_CREATION_FRAME=DENIED NO_SECRETS_PRINTED=true\n')
            self.assertEqual(list(root.iterdir()),[filename])

if __name__=='__main__':unittest.main()
