"""Real target Docker OCI generation, deliberately stopped before runc create.

This proves generated-document shape/profile only, NOT kernel enforcement,
live generation, mount view, rootfs or acceptance. Synthetic CI inputs only.
"""
import copy,json,os,subprocess,sys,tempfile,unittest,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import review_semantic_oci_policy as m

class DockerOCI(unittest.TestCase):
    def test_real_generated_oci_shape_and_configured_policy_without_application_process(self):
        self.assertEqual(os.geteuid(),0)
        docker=Path(os.environ['OUF_CREATION_DOCKER_PATH']);host=os.environ['OUF_CREATION_DOCKER_HOST']
        token=uuid.uuid4().hex;tag='ouf-ci-oci-'+token;cid=None
        def run(*args):
            p=subprocess.run([str(docker),'--host',host,*map(str,args)],capture_output=True,timeout=45)
            self.assertEqual(p.returncode,0,'CI_DOCKER_SETUP_FAILED');return p.stdout.decode().strip()
        with tempfile.TemporaryDirectory(dir=os.environ['OUF_TEST_ROOT']) as dirname:
            root=Path(dirname);root.chmod(0o700)
            (root/'proof').write_text('CI_PRIVATE_FILE');(root/'proof').chmod(0o600)
            (root/'Dockerfile').write_text('FROM scratch\nCOPY proof /proof\nUSER 10006:10006\nCMD ["ci-never-start"]\n')
            try:
                run('build','--network=none','--pull=false','--tag',tag,root)
                image=run('image','inspect','--format','{{.Id}}',tag)
                cid=run('create','--runtime','ouf-ci-oci-observe','--name',tag,'--user','10006:10006',
                    '--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',
                    '--memory','201326592','--memory-swap','201326592','--pids-limit','32',
                    '--env','CI_PRIVATE_SECRET=CI_PRIVATE_VALUE','--mount','type=bind,source='+str(root/'proof')+',target=/proof,readonly',image)
                attempt=subprocess.run([str(docker),'--host',host,'start',cid],capture_output=True,timeout=45)
                self.assertNotEqual(attempt.returncode,0,'CAPTURE_RUNTIME_MUST_DENY_APPLICATION_EXECUTION')
                observed=Path('/root/ouf-ci-runtime/observed-oci')/(cid+'.json')
                self.assertTrue(observed.is_file(),'REAL_GENERATED_OCI_NOT_CAPTURED')
                doc=json.loads(observed.read_bytes());schema=m.schema_from_source_closure()
                m.shape(doc,'Spec',schema)
                # Independent launch/image fixture inputs; never copied from OCI.
                startup={'args':['ci-never-start'],'cwd':'/','uid':10006,'gid':10006,'umask':None,
                    'env':['PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
                        'HOSTNAME='+cid[:12],'HOME=/','CI_PRIVATE_SECRET=CI_PRIVATE_VALUE']}
                spec={'user':'10006:10006','readOnlyRoot':True,'memoryBytes':201326592,'pidsLimit':32,
                    'mounts':[{'source':str(root/'proof'),'target':'/proof','readOnly':True}]}
                # The observed exact document is only a proposed template; this
                # fixture does not authenticate it or claim issuer authority.
                result=m.configured_profile(doc,copy.deepcopy(doc),spec,startup,{},schema)
                self.assertTrue(result['configuredPolicyConforms']);self.assertFalse(result['policyAuthenticationProven'])
                self.assertFalse(result['kernelEnforcementObserved']);self.assertFalse(result['acceptanceGranted'])
                self.assertNotIn('CI_PRIVATE',json.dumps(result));self.assertNotIn(str(root),json.dumps(result))
                state=json.loads(run('inspect','--format','{{json .State}}',cid))
                self.assertFalse(state['Running']);self.assertEqual(state['Pid'],0)
                altered=copy.deepcopy(doc);altered['process']['noNewPrivileges']=False
                with self.assertRaises(m.Denied):m.configured_profile(altered,copy.deepcopy(altered),spec,startup,{},schema)
            finally:
                if cid:
                    run('rm','--force',cid)
                    (Path('/root/ouf-ci-runtime/observed-oci')/(cid+'.json')).unlink(missing_ok=True)
                run('image','rm',tag)

if __name__=='__main__':unittest.main()
