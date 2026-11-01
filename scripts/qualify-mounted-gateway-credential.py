#!/usr/bin/env python3
"""Actual UID10001 Java client vs exact disposable credential ownership/modes.

Native Java process, files, HTTP and caching. Loopback OAuth response is a
fixture: this is not real IAM, a signed bearer, a target grant or E2E acceptance.
"""
import os, pathlib, shutil, subprocess, sys, unittest

class NativeCredentialContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.geteuid()!=0 or os.environ.get('GITHUB_ACTIONS')!='true':
            raise AssertionError('HOSTED_ROOT_NATIVE_CREDENTIAL_FIXTURE_REQUIRED')
        cls.root=pathlib.Path(os.environ['OUF_NATIVE_CREDENTIAL_FIXTURE'])
        cls.java=str(pathlib.Path(os.environ['OUF_NATIVE_JAVA']).resolve())
        cls.setpriv=shutil.which('setpriv')
        if not cls.setpriv or cls.root.exists():raise AssertionError('NEW_NATIVE_CREDENTIAL_SCOPE_REQUIRED')
        cls.root.mkdir(mode=0o755)
        cls.addClassCleanup(shutil.rmtree,cls.root)
        credentials=cls.root/'credentials';credentials.mkdir(mode=0o750);os.chown(credentials,0,10001)
        cls.credentials=credentials
        cases={'root-service-readonly':(0,10001,0o440),
            'owner-private-readonly':(10001,10001,0o400),'owner-private-writable':(10001,10001,0o600),
            'wrong-owner':(10002,10001,0o440),'wrong-group':(0,10002,0o440),
            'group-write':(0,10001,0o460),'world-readable':(0,10001,0o444),
            'group-executable':(0,10001,0o450),'special-mode':(0,10001,0o4440),
            'hardlink':(0,10001,0o440)}
        for name,(uid,gid,mode) in cases.items():
            path=credentials/name;path.write_bytes(b'native-contract-fixture-only-secret')
            os.chown(path,uid,gid);path.chmod(mode)
        os.link(credentials/'hardlink',credentials/'hardlink-alias')
        (credentials/'symlink').symlink_to(credentials/'root-service-readonly')
        libs=cls.root/'libraries';libs.mkdir(mode=0o755);classpath=[]
        repo=pathlib.Path(__file__).resolve().parents[1]
        for index,path in enumerate((repo/'target/native-classpath.txt').read_text().strip().split(':')):
            source=pathlib.Path(path);target=libs/(str(index)+'-'+source.name)
            shutil.copyfile(source,target);target.chmod(0o444);classpath.append(str(target))
        for name in ('classes','test-classes'):
            target=cls.root/name;shutil.copytree(repo/'target'/name,target)
            for path in [target,*target.rglob('*')]:path.chmod(0o555 if path.is_dir() else 0o444)
            classpath.append(str(target))
        cls.classpath=':'.join(classpath)
    def probe(self,name):
        result=subprocess.run([self.setpriv,'--reuid=10001','--regid=10001','--clear-groups',
            '--no-new-privs','--bounding-set=-all','--inh-caps=-all','--ambient-caps=-all','--',
            self.java,'-cp',self.classpath,
            'it.comune.trieste.ouf.semantic.adapters.discovery.MountedGatewayCredentialNativeProbe',
            str(self.credentials),name],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            timeout=15,env={'PATH':'/usr/bin:/bin','LC_ALL':'C'},cwd='/')
        self.assertEqual(result.returncode,0,result.stderr.decode(errors='replace'))
        self.assertEqual(result.stdout,b'NATIVE_GATEWAY_CREDENTIAL_CONTRACT=PASS\n')

for name in ('root-service-readonly','owner-private-readonly','owner-private-writable','wrong-owner','wrong-group',
             'group-write','world-readable','group-executable','special-mode','hardlink','symlink'):
    setattr(NativeCredentialContract,'test_'+name.replace('-','_'),lambda self,name=name:self.probe(name))

if __name__=='__main__':unittest.main(verbosity=2)
