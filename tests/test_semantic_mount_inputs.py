import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import verify_semantic_mount_inputs as m

def encode(value):return json.dumps(value,sort_keys=True).encode()

class Fixture:
    def __init__(self, root):
        self.root=root;root.chmod(0o700)
        self.tls=root/'tls';self.trust=root/'trust';self.stage=root/'stage'
        for p in (self.tls,self.trust,self.stage):p.mkdir(mode=0o700)
        for role in ('adapter','southbound'):(self.trust/role).mkdir(mode=0o700)
        self.binding=json.loads((ROOT/'tests/fixtures/semantic_provider_runtime_review.json').read_bytes())
        for target in (self.binding['routes'],self.binding['adapter']['admission']):target['installation']='fixture'
        self.binding['tlsIdentities']={'adapterHostname':'adapter.fixture.invalid','southboundHostname':'southbound.fixture.invalid'}
        self.binding['routes']['upstream'].update(upstream_host='adapter.fixture.invalid',nodes={'adapter.fixture.invalid:9443':1})
        self.crypto=m.Crypto(Path('/usr/bin/openssl'),m.Budget(),root)
        self.command(['req','-x509','-newkey','ec','-pkeyopt','ec_paramgen_curve:P-256','-nodes',
            '-keyout',str(root/'ci-ca.key'),'-out',str(self.trust/'ca.crt'),'-days','2','-subj','/CN=ci-only-ca',
            '-addext','basicConstraints=critical,CA:TRUE','-addext','keyUsage=critical,keyCertSign,cRLSign'])
        for role in ('adapter','southbound'):
            directory=self.trust/role;host=self.binding['tlsIdentities'][role+'Hostname']
            self.command(['req','-new','-newkey','ec','-pkeyopt','ec_paramgen_curve:P-256','-nodes',
                '-keyout',str(directory/'server.key'),'-out',str(root/(role+'.csr')),'-subj','/CN='+host])
            ext=root/(role+'.ext');ext.write_text('basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature\nextendedKeyUsage=serverAuth\nsubjectAltName=DNS:'+host+'\n')
            self.command(['x509','-req','-in',str(root/(role+'.csr')),'-CA',str(self.trust/'ca.crt'),'-CAkey',str(root/'ci-ca.key'),
                '-CAcreateserial','-out',str(directory/'server.crt'),'-days','1','-extfile',str(ext)])
            for name in ('server.crt','server.key'):(directory/name).chmod(0o600)
            (directory/'provider-receipt.key').write_bytes(b'a'*64);(directory/'provider-receipt.key').chmod(0o600)
        (self.trust/'trust-bundle.pem').write_bytes((self.trust/'ca.crt').read_bytes())
        for name in ('ca.crt','trust-bundle.pem'):(self.trust/name).chmod(0o644)
        self.trust_raw={k:(self.trust/k).read_bytes() for k in m.TRUST_NAMES}
        compile_plan,materialize=m.compiler();self.plan=compile_plan(copy.deepcopy(self.binding))
        self.listener={'address':'0.0.0.0','port':10443,'hostname':'southbound.fixture.invalid','sslResourceId':'fixture'}
        bootstrap=materialize(self.binding['routes'],{'listenAddress':'0.0.0.0','listenPort':10443,
            'serverHostname':'southbound.fixture.invalid','sslResourceId':'fixture'},
            certificate_pem=self.trust_raw['southbound/server.crt'].decode(),private_key_pem=self.trust_raw['southbound/server.key'].decode())
        values={'adapter.json':self.binding['adapter'],'config.yaml':bootstrap['runtimeConfiguration'],
                'apisix.yaml':bootstrap['resources'],'binding':self.binding,'plan':self.plan,
            'trust':{'verified':True,'mountsInstalled':False,'notReleaseAcceptance':True,
                'intent':{'installation':'fixture','gateway':{'uid':0,'gid':0},'adapterImage':{'id':'sha256:'+'b'*64},
                'adapterUid':0,'adapterGid':0,**self.binding['tlsIdentities']},
                'artifactHashes':{k:m.sha(v) for k,v in self.trust_raw.items()}}}
        self.raw={k:encode(v)+(b'\n#END\n' if k=='apisix.yaml' else b'\n' if k in ('adapter.json','config.yaml') else b'') for k,v in values.items()}
        self.raw['stage']=encode({'bindingHash':m.sha(self.raw['binding']),'planHash':m.sha(self.raw['plan']),
            'sourceHashes':{k:m.sha(m.GATEWAY_SOURCES[k].encode()) for k in m.SOURCE_NAMES},'notReleaseAcceptance':True,'runtimeFilesMounted':False})
        intent={**values['trust']['intent'],'trustReceiptHash':m.sha(self.raw['trust']),'stageReceiptHash':m.sha(self.raw['stage']),
                'runtimeTrustHashes':{k:m.sha(v) for k,v in self.trust_raw.items()},'listener':self.listener}
        self.raw['tls']=encode({'intent':intent,'outputHashes':{k:m.sha(self.raw[k]) for k in ('adapter.json','config.yaml','apisix.yaml')},
            'notReleaseAcceptance':True,'mountsInstalled':False,'containersCreated':0,'providerCalls':0})
        self.raw['launch']=encode({'schema':'ouf.semantic-provider-launch-inputs.v1','trustReceiptHash':m.sha(self.raw['trust']),
            'tlsReceiptHash':m.sha(self.raw['tls']),'bindingHash':m.sha(self.raw['binding']),
            'privateArtifactHashes':{k:m.sha(self.raw[k]) for k in ('config.yaml','apisix.yaml')},
            'mountsInstalled':False,'notReleaseAcceptance':True,'containersCreated':0,'providerCalls':0})
        targets={'adapter/server.crt':self.binding['adapter']['tlsCertificateFile'],
            'adapter/server.key':self.binding['adapter']['tlsPrivateKeyFile'],
            'adapter/provider-receipt.key':self.binding['adapter']['receiptKeyFile'],
            'trust-bundle.pem':self.binding['adapter']['provider']['ca_file']}
        adapter=[{'source':str(self.tls/'adapter.json'),'target':'/run/config/adapter.json','readOnly':True}]+[
            {'source':str(self.trust/k),'target':v,'readOnly':True} for k,v in targets.items()]
        south=[{'source':str(self.tls/k),'target':'/run/config/'+k,'readOnly':True} for k in ('config.yaml','apisix.yaml')]+[
            {'source':str(self.trust/'trust-bundle.pem'),'target':targets['trust-bundle.pem'],'readOnly':True}]
        self.raw['manifest']=encode({'schema':'ouf.semantic-provider-stopped-manifest.v1','installation':'fixture',
            'startAuthorized':False,'launchReceiptHash':m.sha(self.raw['launch']),
            'containers':[{'readOnlyRoot':True,'mounts':adapter},{'readOnlyRoot':False,'mounts':south}]})
        self.pin=m.sha(self.raw['manifest']);self.write()
    def command(self, args):
        subprocess.run(['/usr/bin/openssl',*args],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=3)
    def write(self):
        names={'manifest':'stopped-manifest.json','launch':'launch-input-receipt.json','tls':'tls-runtime-receipt.json',
            'trust':'trust-receipt.json','stage':'stage-receipt.json','binding':'binding.json','plan':'runtime-plan.json'}
        self.paths={}
        for name,raw in self.raw.items():
            directory=self.tls if name in ('adapter.json','config.yaml','apisix.yaml','tls') else self.trust if name=='trust' else self.stage
            p=directory/names.get(name,name);p.write_bytes(raw);p.chmod(0o600);self.paths[name]=p
        self.paths.update({'trust:'+k:self.trust/k for k in m.TRUST_NAMES})
        self.meta={k:(0,0,0o600,131072) for k in self.paths}
        for k in m.TRUST_NAMES:self.meta['trust:'+k]=(0,0,0o600,65536) if '/' in k else (0,0,0o644,1048576)
    def review(self):return m.review(self.raw,self.trust_raw,self.pin,'fixture',self.tls,self.trust,self.crypto)
    def verify(self,reader=m.read):
        return m.verify(self.paths,self.meta,self.pin,'fixture',self.tls,self.trust,self.crypto,m.Budget(),reader)

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.geteuid()!=0:raise AssertionError('Root native mount review tests must run; no skip')
        cls.tmp=tempfile.TemporaryDirectory(dir=os.environ.get('OUF_TEST_ROOT',str(ROOT.parent)))
        cls.fixture=Fixture(Path(cls.tmp.name))
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_native_crypto_compiler_mapping_and_private_read_stability(self):
        f=self.fixture;before={p:(p.read_bytes(),m.attrs(p.stat())) for p in f.paths.values()}
        result=f.verify();out=encode(result)
        self.assertEqual(result['manifestMountCount'],8);self.assertTrue(result['independentCompilerReplay'])
        self.assertTrue(result['cryptographicKeyValidation']);self.assertFalse(result['acceptanceGranted'])
        for raw in (f.trust_raw['adapter/server.key'],f.trust_raw['southbound/server.key'],b'a'*64):self.assertNotIn(raw,out)
        self.assertNotIn(str(f.root).encode(),out)
        self.assertEqual(before,{p:(p.read_bytes(),m.attrs(p.stat())) for p in f.paths.values()})
    def test_mismatched_leaf_key_wrong_hostname_and_expired_time_fail_closed(self):
        f=self.fixture
        with self.assertRaisesRegex(m.Blocked,'TLS_KEY_PAIR_MISMATCH'):
            f.crypto.validate_pair(f.trust_raw['adapter/server.crt'],f.trust_raw['southbound/server.key'],f.trust_raw['ca.crt'],'adapter.fixture.invalid')
        with self.assertRaises(m.Blocked):
            f.crypto.validate_pair(f.trust_raw['adapter/server.crt'],f.trust_raw['adapter/server.key'],f.trust_raw['ca.crt'],'wrong.fixture.invalid')
        # Actual native verification at a distant future time proves expiry;
        # this is a fixture test, never a production ignore-time option.
        original=f.crypto.run
        def future(args,*rest,**kwargs):
            if args[0]=='verify':args=args+['-attime','4102444800']
            return original(args,*rest,**kwargs)
        with patch.object(f.crypto,'run',side_effect=future),self.assertRaises(m.Blocked):
            f.crypto.validate_pair(f.trust_raw['adapter/server.crt'],f.trust_raw['adapter/server.key'],f.trust_raw['ca.crt'],'adapter.fixture.invalid')
    def test_mac_key_artifact_and_resealed_compiler_source_drift(self):
        f=self.fixture
        for role in ('adapter','southbound'):
            values=copy.deepcopy(f.trust_raw);values[role+'/provider-receipt.key']=b'b'*64
            with self.assertRaises(m.Blocked):m.review(f.raw,values,f.pin,'fixture',f.tls,f.trust,f.crypto)
        raw=copy.deepcopy(f.raw);stage=m.decode(raw['stage']);stage['sourceHashes']['tools/materialize_semantic_provider.py']='f'*64
        raw['stage']=encode(stage);tls=m.decode(raw['tls']);tls['intent']['stageReceiptHash']=m.sha(raw['stage']);raw['tls']=encode(tls)
        launch=m.decode(raw['launch']);launch['tlsReceiptHash']=m.sha(raw['tls']);raw['launch']=encode(launch)
        manifest=m.decode(raw['manifest']);manifest['launchReceiptHash']=m.sha(raw['launch']);raw['manifest']=encode(manifest)
        with self.assertRaisesRegex(m.Blocked,'STAGED_COMPILER_SOURCE_DRIFT'):
            m.review(raw,f.trust_raw,m.sha(raw['manifest']),'fixture',f.tls,f.trust,f.crypto)
    def test_manifest_extra_missing_rw_and_wrong_destination(self):
        f=self.fixture
        for kind in ('extra','missing','rw','destination'):
            raw=copy.deepcopy(f.raw);manifest=m.decode(raw['manifest']);rows=manifest['containers'][0]['mounts']
            if kind=='extra':rows.append({'source':'/unreviewed','target':'/extra','readOnly':True})
            elif kind=='missing':rows.pop()
            elif kind=='rw':rows[0]['readOnly']=False
            else:rows[1]['target']='/wrong'
            raw['manifest']=encode(manifest)
            with self.subTest(kind=kind),self.assertRaises(m.Blocked):
                m.review(raw,f.trust_raw,m.sha(raw['manifest']),'fixture',f.tls,f.trust,f.crypto)
    def test_inode_bytes_and_metadata_drift_and_no_extra_private_paths(self):
        f=self.fixture;calls=[]
        def reader(path,*args):
            calls.append(path);return m.read(path,*args)
        f.verify(reader);self.assertEqual(calls,list(f.paths.values())*2)
        self.assertNotIn(f.root/'ci-ca.key',calls)
        self.assertFalse(any(p.name.endswith('.env') for p in calls))
        calls=[]
        def changed(path,*args):
            calls.append(path);raw,meta=m.read(path,*args)
            if len(calls)>len(f.paths):meta=(*meta[:-1],meta[-1]+1)
            return raw,meta
        with self.assertRaisesRegex(m.Blocked,'INPUTS_CHANGED_DURING_REVIEW'):f.verify(changed)
    def test_actual_isolated_cli_redaction_no_private_file_writes(self):
        f=self.fixture;args=['/usr/bin/python3','-I','-B',str(ROOT/'tools/verify_semantic_mount_inputs.py')]
        # Isolated CLI normally uses the complete embedded closure. Tests build
        # exactly that closure, avoiding dependence on a checkout sys.path.
        embedded=build_embedded()
        cli=f.root/'public-reader.py';cli.write_text(embedded);cli.chmod(0o600);args[3]=str(cli)
        for k,path in (('manifest',f.stage),('launch',f.stage),('tls',f.tls),('trust',f.trust),('stage',f.stage)):
            args+=['--'+k+'-root',str(path)]
        args+=['--public-scratch-root',str(f.root),'--openssl-path','/usr/bin/openssl','--manifest-hash',f.pin,'--installation','fixture',
               '--adapter-uid','0','--adapter-gid','0','--gateway-uid','0','--gateway-gid','0']
        before={p:(p.read_bytes(),m.attrs(p.stat())) for p in f.paths.values()}
        proc=subprocess.run(args,capture_output=True,timeout=10);self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
        self.assertIn(b'SEMANTIC_MOUNT_INPUTS=PASS',proc.stdout)
        self.assertNotIn(str(f.root).encode(),proc.stdout+proc.stderr)
        self.assertNotIn(f.trust_raw['adapter/server.key'],proc.stdout+proc.stderr)
        self.assertEqual(before,{p:(p.read_bytes(),m.attrs(p.stat())) for p in f.paths.values()})
        args[args.index('--manifest-hash')+1]='f'*64
        proc=subprocess.run(args,capture_output=True,timeout=10);self.assertEqual(proc.returncode,1)
        self.assertIn(b'NO_SECRETS_PRINTED=true',proc.stdout);self.assertNotIn(str(f.root).encode(),proc.stdout+proc.stderr)
    def test_symlink_hardlink_fifo_wrong_mode_owner_and_limits(self):
        with tempfile.TemporaryDirectory(dir=self.fixture.root) as d:
            root=Path(d);root.chmod(0o700);p=root/'file';p.write_bytes(b'x');p.chmod(0o600)
            link=root/'link';link.symlink_to(p)
            with self.assertRaises(OSError):m.read(link,0,0,0o600,10,m.Budget())
            link.unlink();os.link(p,link)
            with self.assertRaises(m.Blocked):m.read(p,0,0,0o600,10,m.Budget())
            link.unlink();p.chmod(0o644)
            with self.assertRaises(m.Blocked):m.read(p,0,0,0o600,10,m.Budget())
            p.chmod(0o600)
            with self.assertRaises(m.Blocked):m.read(p,1,1,0o600,10,m.Budget())
            p.write_bytes(b'x'*11)
            with self.assertRaises(m.Blocked):m.read(p,0,0,0o600,10,m.Budget())
            fifo=root/'fifo';os.mkfifo(fifo,0o600)
            with self.assertRaises(m.Blocked):m.read(fifo,0,0,0o600,10,m.Budget())
    def test_budget_exhaustion_and_unknown_json_cannot_be_executed(self):
        budget=m.Budget();budget.deadline=0
        with self.assertRaises(m.Blocked):m.read(self.fixture.paths['manifest'],0,0,0o600,131072,budget)
        raw=copy.deepcopy(self.fixture.raw);raw['adapter.json']=b'{"secret":"PRIVATE_SENTINEL"}'
        with self.assertRaises(Exception):m.review(raw,self.fixture.trust_raw,self.fixture.pin,'fixture',self.fixture.tls,self.fixture.trust,self.fixture.crypto)

    def test_resealed_config_bytes_and_runtime_plan_still_require_independent_replay(self):
        f=self.fixture
        for name in ('config.yaml','plan'):
            raw=copy.deepcopy(f.raw)
            if name=='config.yaml':raw[name]+=b' '
            else:
                value=m.decode(raw[name]);value['unexpected']='PRIVATE_PLAN_SENTINEL';raw[name]=encode(value)
                stage=m.decode(raw['stage']);stage['planHash']=m.sha(raw[name]);raw['stage']=encode(stage)
            tls=m.decode(raw['tls']);tls['outputHashes']['config.yaml']=m.sha(raw['config.yaml'])
            tls['intent']['stageReceiptHash']=m.sha(raw['stage']);raw['tls']=encode(tls)
            launch=m.decode(raw['launch']);launch['tlsReceiptHash']=m.sha(raw['tls'])
            launch['privateArtifactHashes']['config.yaml']=m.sha(raw['config.yaml']);raw['launch']=encode(launch)
            manifest=m.decode(raw['manifest']);manifest['launchReceiptHash']=m.sha(raw['launch']);raw['manifest']=encode(manifest)
            with self.subTest(name=name),self.assertRaisesRegex(m.Blocked,'INDEPENDENT_(TLS_COMPILER|RUNTIME_PLAN)_DRIFT'):
                m.review(raw,f.trust_raw,m.sha(raw['manifest']),'fixture',f.tls,f.trust,f.crypto)

    def test_crypto_does_not_use_default_ca_network_or_ignore_time_options(self):
        f=self.fixture;calls=[];native=f.crypto.run
        def track(args,*rest,**kwargs):
            calls.append(args);return native(args,*rest,**kwargs)
        with patch.object(f.crypto,'run',side_effect=track):
            f.crypto.validate_pair(f.trust_raw['adapter/server.crt'],f.trust_raw['adapter/server.key'],f.trust_raw['ca.crt'],'adapter.fixture.invalid')
        verify=[args for args in calls if args[0]=='verify'];self.assertEqual(len(verify),2)
        for args in verify:
            for option in ('-no-CAfile','-no-CApath','-no-CAstore','-purpose','-verify_hostname'):self.assertIn(option,args)
            for option in ('-no_check_time','-crl_download','-partial_chain'):self.assertNotIn(option,args)
        self.assertFalse(any('pkeyutl' in args or '-sign' in args or '-newkey' in args for args in calls))

    def test_embedded_public_closure_does_not_read_lua_or_call_network(self):
        f=self.fixture
        with patch('socket.getaddrinfo',side_effect=AssertionError('NETWORK_NOT_ALLOWED')),\
             patch.object(Path,'read_text',side_effect=AssertionError('EXTERNAL_SOURCE_READ_NOT_ALLOWED')):
            compile_plan,_=m.compiler();self.assertEqual(compile_plan(copy.deepcopy(f.binding)),f.plan)

def build_embedded():
    helper=(ROOT/'tools/verify_semantic_configuration_provenance.py').read_text().split("if __name__=='__main__':")[0]
    sources=(ROOT/'tools/semantic_mount_review_sources.py').read_text()
    reader=(ROOT/'tools/verify_semantic_mount_inputs.py').read_text()
    reader=reader.replace('from tools.verify_semantic_configuration_provenance import NAMES, project, decode, attrs, sha',helper)
    reader=reader.replace('from tools.semantic_mount_review_sources import GATEWAY_SOURCES, GATEWAY_SOURCE_COMMIT',sources)
    return reader

if __name__=='__main__':unittest.main()
