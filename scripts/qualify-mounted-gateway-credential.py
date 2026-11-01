#!/usr/bin/env python3
"""Actual UID10001 Java client vs exact disposable credential ownership/modes.

Native Java process, files, HTTP and caching. Additional cases use the retained
Keycloak26.7.4 digest and actual IAM decoder/converter. Loopback HTTP/realm are
fixtures: no production TLS, APISIX, target grant or E2E acceptance is proved.
"""
import json, os, pathlib, shutil, subprocess, time, unittest, urllib.request, uuid

KEYCLOAK='quay.io/keycloak/keycloak@sha256:82a77884f3af238beab1e7afd63b5f530e1b5c0590bd7aa60b40a40463e29b2c'

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
        cls.prepare_iam()
    @classmethod
    def prepare_iam(cls):
        docker=shutil.which('docker')
        if not docker:raise AssertionError('NATIVE_KEYCLOAK_DOCKER_FIXTURE_REQUIRED')
        def command(args):
            return subprocess.run([docker,*args],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,check=True,timeout=120).stdout
        def claim(name,value):
            return {'name':name,'protocol':'openid-connect','protocolMapper':'oidc-hardcoded-claim-mapper',
                'config':{'claim.name':name,'claim.value':value,'jsonType.label':'String','access.token.claim':'true'}}
        realm={'realm':'ouf-native-provider','enabled':True,'sslRequired':'none',
            'clientScopes':[{'name':'gateway.invoke','protocol':'openid-connect','attributes':{'include.in.token.scope':'true'}}],
            'clients':[{'clientId':'native-workload','enabled':True,'protocol':'openid-connect',
                'publicClient':False,'clientAuthenticatorType':'client-secret','secret':'native-contract-fixture-only-secret',
                'serviceAccountsEnabled':True,'standardFlowEnabled':False,'directAccessGrantsEnabled':False,
                'defaultClientScopes':[],'optionalClientScopes':['gateway.invoke'],
                'protocolMappers':[claim('tenant_id','native-fixture-tenant'),claim('ouf_actor_type','SERVICE'),claim('acr','1'),
                    {'name':'subject','protocol':'openid-connect','protocolMapper':'oidc-sub-mapper','config':{'access.token.claim':'true'}},
                    {'name':'audience','protocol':'openid-connect','protocolMapper':'oidc-audience-mapper',
                        'config':{'included.custom.audience':'ouf-native-gateway','access.token.claim':'true'}}]}]}
        path=cls.root/'iam-realm.json';path.write_text(json.dumps(realm));path.chmod(0o644)
        cid=command(['run','-d','--name','ouf-native-provider-'+uuid.uuid4().hex[:12],
            '--memory','1g','--memory-swap','1g','--cpus','2','--pids-limit','512',
            '--cap-drop','ALL','--security-opt','no-new-privileges','-p','127.0.0.1::8080',
            '-v',str(path)+':/opt/keycloak/data/import/realm.json:ro',
            '-e','JAVA_OPTS_KC_HEAP=-Xms128m -Xmx512m',KEYCLOAK,'start-dev','--hostname-strict=false','--import-realm']).decode().strip()
        cls.addClassCleanup(lambda:command(['rm','-f',cid]))
        published=command(['port',cid,'8080/tcp']).decode().strip()
        if not published.startswith('127.0.0.1:') or not published.rsplit(':',1)[1].isdigit():
            raise AssertionError('EXACT_LOOPBACK_IAM_PUBLISHED_FIXTURE_REQUIRED')
        cls.issuer='http://'+published+'/realms/ouf-native-provider';deadline=time.monotonic()+120
        while True:
            try:
                with urllib.request.urlopen(cls.issuer+'/.well-known/openid-configuration',timeout=3)as response:
                    body=response.read(131073)
                if len(body)<=131072 and json.loads(body)['issuer']==cls.issuer:break
            except (OSError,ValueError,KeyError):pass
            if time.monotonic()>=deadline:raise AssertionError('NATIVE_KEYCLOAK_READINESS_EXHAUSTED')
            time.sleep(.5)
        version=command(['exec',cid,'/opt/keycloak/bin/kc.sh','--version']).decode()
        if '26.7.4'not in version:raise AssertionError('EXACT_NATIVE_KEYCLOAK_VERSION_REQUIRED')
    def probe(self,name):
        result=subprocess.run([self.setpriv,'--reuid=10001','--regid=10001','--clear-groups',
            '--no-new-privs','--bounding-set=-all','--inh-caps=-all','--ambient-caps=-all','--',
            self.java,'-Douf.native.iamIssuer='+self.issuer,'-cp',self.classpath,
            'it.comune.trieste.ouf.semantic.adapters.discovery.MountedGatewayCredentialNativeProbe',
            str(self.credentials),name],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            timeout=15,env={'PATH':'/usr/bin:/bin','LC_ALL':'C'},cwd='/')
        self.assertEqual(result.returncode,0,result.stderr.decode(errors='replace'))
        self.assertEqual(result.stdout,b'NATIVE_GATEWAY_CREDENTIAL_CONTRACT=PASS\n')

for name in ('root-service-readonly','owner-private-readonly','owner-private-writable','wrong-owner','wrong-group',
             'group-write','world-readable','group-executable','special-mode','hardlink','symlink',
             'real-iam','real-iam-wrong-audience','real-iam-invalid-signature'):
    setattr(NativeCredentialContract,'test_'+name.replace('-','_'),lambda self,name=name:self.probe(name))

if __name__=='__main__':unittest.main(verbosity=2)
