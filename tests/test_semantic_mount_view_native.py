"""Mandatory real created runc PID/mount/source-inode evidence; no app start."""
import copy,errno,hashlib,json,os,shutil,subprocess,sys,tempfile,unittest,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import observe_semantic_mount_view as m
from tools import observe_semantic_creation_frame as frame
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
                'linux':{'cgroupsPath':'/'+cid,'namespaces':[{'type':k} for k in ('mount','pid','ipc','uts','network','cgroup')],
                    'maskedPaths':['/proc/kcore'],'readonlyPaths':['/proc/sys'],
                    'resources':{'memory':{'limit':201326592,'swap':201326592},'pids':{'limit':32}},
                    'seccomp':{'defaultAction':'SCMP_ACT_ERRNO','defaultErrnoRet':1,'architectures':['SCMP_ARCH_X86_64'],
                        'syscalls':[{'names':["read","write","close","exit","exit_group","rt_sigreturn","rt_sigprocmask","prctl","futex","open","openat","readlink","readlinkat","fstat","newfstatat","statx","fcntl","close_range","getpid","gettid","getppid","getuid","geteuid","getgid","getegid","setgroups","setgid","setuid","getcwd","chdir","fchdir","rt_sigaction","sigaltstack","sched_yield","sched_getaffinity","clock_gettime","nanosleep","mmap","mprotect","munmap","brk","arch_prctl","set_tid_address","set_robust_list","rseq","dup","dup2","dup3","pipe","pipe2","poll","ppoll","readv","writev","pread64","pwrite64","lseek"],
                            'action':'SCMP_ACT_ALLOW'}]}}}
            config=bundle/'config.json';config.write_text(json.dumps(doc));config.chmod(0o600)
            args=[str(runc),'--root',str(root/'runtime')]
            def run(*tail):
                # A created init retains its stdio until start/delete. PIPE
                # makes communicate wait for that init after runc has exited.
                # These files hold synthetic CI diagnostics only.
                with tempfile.TemporaryFile() as output:
                    p=subprocess.run([*args,*map(str,tail)],stdin=subprocess.DEVNULL,
                        stdout=output,stderr=output,timeout=20)
                    self.assertEqual(p.returncode,0,'CI_RUNC_OPERATION_FAILED')
                    output.seek(0);data=output.read(16385)
                    self.assertLessEqual(len(data),16384,'CI_RUNC_OUTPUT_UNBOUNDED');return data
            created=False
            try:
                # Cleanup also applies if create succeeds but its caller fails.
                created=True;run('create','--bundle',bundle,cid)
                state=json.loads(run('state',cid));self.assertEqual(state['status'],'created');pid=state['pid']
                expected=m.generation(pid,m.Budget());bindings=[{'source':str(source),'target':target,'readOnly':True}]
                attrs=[m.attributes(source.lstat())];before=source.read_bytes()
                source_policy={'source':str(source),'target':target,'readOnly':True,'uid':10006,'gid':10006,
                    'mode':0o600,'sha256':hashlib.sha256(before).hexdigest(),'maxBytes':131072}
                if variant=='generation':expected['startTicks']+=1
                if variant=='source':
                    replaced=root/'replacement';replaced.write_bytes(before);replaced.chmod(0o600);os.chown(replaced,10006,10006)
                    os.replace(replaced,source);attrs=[m.attributes(source.lstat())]
                if variant:
                    with self.assertRaises(Denied):m.observe(pid,expected,doc,bindings,attrs)
                    with self.assertRaises(Denied):frame.source_mount_frame(pid,expected,doc,[source_policy])
                else:
                    result=m.observe(pid,expected,doc,bindings,attrs)
                    self.assertTrue(result['effectiveReadOnlyFileBindingsObserved']);self.assertTrue(result['stableAcrossReads'])
                    self.assertTrue(result['allMountPointsExplained']);self.assertFalse(result['fullMountViewAccepted'])
                    self.assertEqual(result['privateFileContentsRead'],0);self.assertFalse(result['acceptanceGranted'])
                    self.assertNotIn('CI_PRIVATE',json.dumps(result));self.assertNotIn(str(root),json.dumps(result))
                    joined=frame.source_mount_frame(pid,expected,doc,[source_policy])
                    self.assertTrue(joined['sourceByteHashesMatchExpected']);self.assertTrue(joined['stableAcrossReads'])
                    self.assertEqual(joined['sourceBytesRead'],len(before)*2)
                    self.assertFalse(joined['atomicSnapshotProven']);self.assertFalse(joined['acceptanceGranted'])
                    self.assertNotIn('CI_PRIVATE',json.dumps(joined));self.assertNotIn(str(root),json.dumps(joined))
                    incorrect=dict(source_policy);incorrect['sha256']='0'*64
                    with self.assertRaisesRegex(Denied,'SOURCE_FRAME_BYTE_HASH_DRIFT'):
                        frame.source_mount_frame(pid,expected,doc,[incorrect])
                    policy={'schema':'ouf.semantic-configured-creation-frame-policy.v1','expectedOci':doc,
                        'manifest':{'user':'10006:10006','readOnlyRoot':False,'memoryBytes':201326592,'pidsLimit':32,
                            'mounts':bindings},'startup':{'uid':10006,'gid':10006,'umask':None,'cwd':'/',
                            'args':doc['process']['args'],'env':doc['process']['env']},'approvedHooks':{},'sources':[source_policy]}
                    policy_path=root/'policy.json';policy_path.write_text(json.dumps(policy));policy_path.chmod(0o600)
                    request={'pid':pid,'generation':{'pid':pid,'startTicks':expected['startTicks'],
                        'namespaceInode':expected['networkNamespaceInode']},'bundlePath':str(config),
                        'applicationHash':hashlib.sha256(frame.canonical(doc)).hexdigest(),
                        'policyHash':hashlib.sha256(policy_path.read_bytes()).hexdigest()}
                    helper=Path(__file__).resolve().parents[1]/'tools/semantic_creation_frame_observer.py'
                    command=['/usr/bin/python3','-I','-B',str(helper),'--configuration',str(policy_path)]
                    reply=subprocess.run(command,input=frame.canonical(request),capture_output=True,timeout=6)
                    self.assertEqual(reply.returncode,0,'CI_SOURCE_SEALED_FRAME_OBSERVER_FAILED')
                    combined=json.loads(reply.stdout);self.assertTrue(combined['configuredPolicy']['configuredPolicyConforms'])
                    self.assertTrue(combined['sourceMountFrame']['sourceByteHashesMatchExpected'])
                    self.assertFalse(combined['acceptanceGranted']);self.assertEqual(reply.stderr,b'')
                    self.assertNotIn(b'CI_PRIVATE',reply.stdout);self.assertNotIn(str(root).encode(),reply.stdout)
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
                if created:
                    subprocess.run([*args,'delete','--force',cid],stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20,check=True)

    def test_actual_mountinfo_pid_generation_inode_and_kernel_readonly_without_app_start(self):self.exercise()
    def test_actual_rw_bind_denied(self):self.exercise('rw')
    def test_replaced_source_inode_denied_even_when_bytes_equal(self):self.exercise('source')
    def test_wrong_created_generation_denied(self):self.exercise('generation')

if __name__=='__main__':unittest.main()
