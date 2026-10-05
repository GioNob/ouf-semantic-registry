"""Mandatory real created runc PID/mount/source-inode evidence; no app start."""
import copy,errno,json,os,shutil,subprocess,sys,tempfile,unittest,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import observe_semantic_mount_view as m
from tools.review_semantic_oci_policy import Denied

class Native(unittest.TestCase):
    def exercise(self,variant=None):
        self.assertEqual(os.geteuid(),0);runc=Path('/usr/bin/runc');self.assertTrue(runc.is_file())
        cid='ouf-ci-mount-'+uuid.uuid4().hex
        with tempfile.TemporaryDirectory(dir=os.environ['OUF_TEST_ROOT']) as dirname:
            root=Path(dirname);root.chmod(0o700);fs=root/'rootfs';fs.mkdir(mode=0o755)
            for name in ('bin','proc','dev','proofdir'):(fs/name).mkdir(mode=0o755)
            os.chown(fs/'proofdir',10006,10006)
            shutil.copyfile('/usr/bin/busybox',fs/'bin/busybox');(fs/'bin/busybox').chmod(0o755)
            source=root/'source';source.write_bytes(b'CI_PRIVATE_BIND_CONTENT');source.chmod(0o600);os.chown(source,10006,10006)
            target='/proof';marker=fs/'proofdir/APP_STARTED';bundle=root/'bundle';bundle.mkdir(mode=0o700)
            doc={'ociVersion':'1.0.2','root':{'path':str(fs),'readonly':False},
                'process':{'terminal':False,'user':{'uid':10006,'gid':10006},'cwd':'/',
                    'args':['/bin/busybox','sh','-c','echo CI_APP > /proofdir/APP_STARTED'],'env':['PATH=/bin'],
                    'noNewPrivileges':True,'capabilities':{k:[] for k in ('bounding','effective','inheritable','permitted','ambient')}},
                'mounts':[{'destination':'/proc','type':'proc','source':'proc','options':['nosuid','noexec','nodev']},
                    {'destination':'/dev','type':'tmpfs','source':'tmpfs','options':['nosuid','strictatime','mode=755']},
                    {'destination':target,'type':'bind','source':str(source),'options':['rbind','rprivate','rw' if variant=='rw' else 'ro']}],
                'linux':{'cgroupsPath':'/'+cid,'namespaces':[{'type':k} for k in ('mount','pid','ipc','uts','network','cgroup')]}}
            config=bundle/'config.json';config.write_text(json.dumps(doc));config.chmod(0o600)
            args=[str(runc),'--root',str(root/'runtime')]
            def run(*tail):
                p=subprocess.run([*args,*map(str,tail)],capture_output=True,timeout=20)
                self.assertEqual(p.returncode,0,'CI_RUNC_OPERATION_FAILED');return p.stdout
            created=False
            try:
                run('create','--bundle',bundle,cid);created=True
                state=json.loads(run('state',cid));self.assertEqual(state['status'],'created');pid=state['pid']
                expected=m.generation(pid,m.Budget());bindings=[{'source':str(source),'target':target,'readOnly':True}]
                attrs=[m.attributes(source.lstat())];before=source.read_bytes()
                if variant=='generation':expected['startTicks']+=1
                if variant=='source':
                    replaced=root/'replacement';replaced.write_bytes(before);replaced.chmod(0o600);os.chown(replaced,10006,10006)
                    os.replace(replaced,source);attrs=[m.attributes(source.lstat())]
                if variant:
                    with self.assertRaises(Denied):m.observe(pid,expected,doc,bindings,attrs)
                else:
                    result=m.observe(pid,expected,doc,bindings,attrs)
                    self.assertTrue(result['effectiveReadOnlyFileBindingsObserved']);self.assertTrue(result['stableAcrossReads'])
                    self.assertTrue(result['allMountPointsExplained']);self.assertFalse(result['fullMountViewAccepted'])
                    self.assertEqual(result['privateFileContentsRead'],0);self.assertFalse(result['acceptanceGranted'])
                    self.assertNotIn('CI_PRIVATE',json.dumps(result));self.assertNotIn(str(root),json.dumps(result))
                    fd=None
                    try:
                        fd=os.open('/proc/'+str(pid)+'/root'+target,os.O_WRONLY)
                    except OSError as error:self.assertEqual(error.errno,errno.EROFS)
                    else:self.fail('ACTUAL_FILE_BIND_MUST_BE_KERNEL_READONLY')
                    finally:
                        if fd is not None:os.close(fd)
                self.assertEqual(source.read_bytes(),before);self.assertFalse(marker.exists())
                self.assertEqual(json.loads(run('state',cid))['status'],'created')
            finally:
                if created:run('delete','--force',cid)

    def test_actual_mountinfo_pid_generation_inode_and_kernel_readonly_without_app_start(self):self.exercise()
    def test_actual_rw_bind_denied(self):self.exercise('rw')
    def test_replaced_source_inode_denied_even_when_bytes_equal(self):self.exercise('source')
    def test_wrong_created_generation_denied(self):self.exercise('generation')

if __name__=='__main__':unittest.main()
