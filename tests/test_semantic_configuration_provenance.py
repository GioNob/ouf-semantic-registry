import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('provenance',ROOT/'tools/verify_semantic_configuration_provenance.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def encode(v):return json.dumps(v,sort_keys=True).encode()
def fixture():
    adapter={'admission':{'installation':'fixture'},'secretReference':'DO_NOT_PRINT_SENTINEL'}
    routes=[{'private':'DO_NOT_PRINT_SENTINEL'}]
    v={'adapter.json':adapter,'config.yaml':{'private':'DO_NOT_PRINT_SENTINEL'},
        'apisix.yaml':{'routes':routes,'ssls':[{'key':'INLINE_PRIVATE_KEY_SENTINEL'}]},
        'binding':{'adapter':adapter,'tlsIdentities':{'adapterHostname':'adapter','southboundHostname':'south'}},
        'plan':{'schema':'ouf.semantic-provider-runtime-plan.v1','adapterConfiguration':adapter,
            'southboundRoutes':{'routes':routes},'installed':False,'notReleaseAcceptance':True,'providerCalls':0},
        'trust':{'intent':{'gateway':{'uid':0,'gid':0},'adapterImage':{'id':'sha256:'+'a'*64},
            'adapterUid':0,'adapterGid':0,'installation':'fixture','adapterHostname':'adapter','southboundHostname':'south'},
            'verified':True,'mountsInstalled':False,'notReleaseAcceptance':True}}
    raw={k:encode(x)+(b'\n#END\n' if k=='apisix.yaml' else b'') for k,x in v.items()}
    raw['stage']=encode({'bindingHash':m.sha(raw['binding']),'planHash':m.sha(raw['plan']),
        'notReleaseAcceptance':True,'runtimeFilesMounted':False})
    raw['tls']=encode({'intent':dict(v['trust']['intent'],trustReceiptHash=m.sha(raw['trust']),stageReceiptHash=m.sha(raw['stage'])),
        'outputHashes':{k:m.sha(raw[k]) for k in m.NAMES[7:]},'notReleaseAcceptance':True,'mountsInstalled':False,
        'containersCreated':0,'providerCalls':0})
    raw['launch']=encode({'schema':'ouf.semantic-provider-launch-inputs.v1',
        'trustReceiptHash':m.sha(raw['trust']),'tlsReceiptHash':m.sha(raw['tls']),'bindingHash':m.sha(raw['binding']),
        'privateArtifactHashes':{k:m.sha(raw[k]) for k in ('config.yaml','apisix.yaml')},'mountsInstalled':False,
        'notReleaseAcceptance':True,'containersCreated':0,'providerCalls':0})
    raw['manifest']=encode({'schema':'ouf.semantic-provider-stopped-manifest.v1','installation':'fixture',
        'startAuthorized':False,'launchReceiptHash':m.sha(raw['launch'])})
    return raw
class Tests(unittest.TestCase):
    def test_success_redaction_limits(self):
        raw=fixture();result=m.project(raw,m.sha(raw['manifest']),'fixture');out=encode(result)
        self.assertNotIn(b'SENTINEL',out);self.assertTrue(result['inlineTlsPrivateKeyFileRead'])
        self.assertFalse(result['acceptanceGranted']);self.assertFalse(result['independentCompilerReplay'])
    def test_every_input_drift_blocked(self):
        for name in m.NAMES:
            raw=fixture();pin=m.sha(raw['manifest']);raw[name]+=b' '
            with self.subTest(name=name),self.assertRaises((m.Blocked,ValueError)):m.project(raw,pin,'fixture')
    def test_resealed_invalid_contracts_rejected(self):
        # A coherent hash chain cannot legitimize inconsistent role/route bindings.
        for target,key,value in (('adapter.json','admission',{'installation':'other'}),
                ('apisix.yaml','routes',[]),('plan','installed',True),('trust','verified',False),
                ('launch','mountsInstalled',True)):
            raw=fixture();obj=m.decode(raw[target],end=target=='apisix.yaml');obj[key]=value
            raw[target]=encode(obj)+(b'\n#END\n' if target=='apisix.yaml' else b'')
            stage=m.decode(raw['stage']);stage.update(bindingHash=m.sha(raw['binding']),planHash=m.sha(raw['plan']));raw['stage']=encode(stage)
            tls=m.decode(raw['tls']);tls['intent'].update(trustReceiptHash=m.sha(raw['trust']),stageReceiptHash=m.sha(raw['stage']))
            tls['outputHashes']={k:m.sha(raw[k]) for k in m.NAMES[7:]};raw['tls']=encode(tls)
            launch=m.decode(raw['launch']);launch.update(trustReceiptHash=m.sha(raw['trust']),tlsReceiptHash=m.sha(raw['tls']),bindingHash=m.sha(raw['binding']))
            launch['privateArtifactHashes']={k:m.sha(raw[k]) for k in ('config.yaml','apisix.yaml')};raw['launch']=encode(launch)
            manifest=m.decode(raw['manifest']);manifest['launchReceiptHash']=m.sha(raw['launch']);raw['manifest']=encode(manifest)
            with self.subTest(target=target),self.assertRaises(m.Blocked):m.project(raw,m.sha(raw['manifest']),'fixture')
    def test_duplicate_nonfinite_end_missing_and_limit(self):
        for raw,end in ((b'{"x":1,"x":2}',False),(b'{"x":NaN}',False),(b'{}',True),(b'x'*(m.LIMIT+1),False)):
            with self.assertRaises((m.Blocked,ValueError)):m.decode(raw,end)
    def test_stable_bytes_and_metadata_required(self):
        raw=fixture();paths={k:Path('/FIXED/'+k) for k in m.NAMES};owners={k:(0,0) for k in m.NAMES};seen=[]
        def reader(p,*owner):
            seen.append(p);return raw[p.name],(1,)
        m.verify(paths,owners,m.sha(raw['manifest']),'fixture',reader)
        self.assertEqual(seen,list(paths.values())*2)
        seen=[]
        def drift(p,*owner):
            seen.append(p);return raw[p.name],(1 if len(seen)<=len(paths) else 2,)
        with self.assertRaises(m.Blocked):m.verify(paths,owners,m.sha(raw['manifest']),'fixture',drift)
    def test_real_cli_no_writes_redaction_and_failure(self):
        self.assertEqual(os.geteuid(),0)
        raw=fixture()
        with tempfile.TemporaryDirectory(dir=os.environ.get('OUF_TEST_ROOT',str(ROOT.parent))) as d:
            root=Path(d);root.chmod(0o700)
            filenames={'manifest':'stopped-manifest.json','launch':'launch-input-receipt.json','tls':'tls-runtime-receipt.json',
                'trust':'trust-receipt.json','stage':'stage-receipt.json','binding':'binding.json','plan':'runtime-plan.json'}
            for k,data in raw.items():
                p=root/filenames.get(k,k);p.write_bytes(data);p.chmod(0o600)
            args=[os.sys.executable,'-I','-B',str(ROOT/'tools/verify_semantic_configuration_provenance.py')]
            for k in ('manifest','launch','tls','trust','stage'):args+=['--'+k+'-root',d]
            args+=['--adapter-uid','0','--adapter-gid','0','--gateway-uid','0','--gateway-gid','0']
            args+=['--manifest-hash',m.sha(raw['manifest']),'--installation','fixture']
            before={p.name:(p.read_bytes(),m.attrs(p.stat())) for p in root.iterdir()}
            proc=subprocess.run(args,capture_output=True);self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
            self.assertNotIn(b'SENTINEL',proc.stdout+proc.stderr)
            self.assertEqual(before,{p.name:(p.read_bytes(),m.attrs(p.stat())) for p in root.iterdir()})
            (root/'apisix.yaml').write_bytes(b'{"secret":"FAILURE_SENTINEL"}\n#END\n')
            proc=subprocess.run(args,capture_output=True);self.assertEqual(proc.returncode,1)
            self.assertNotIn(b'SENTINEL',proc.stdout+proc.stderr);self.assertNotIn(d.encode(),proc.stdout+proc.stderr)
    def test_symlink_hardlink_fifo_wrong_owner_and_modes(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('OUF_TEST_ROOT',str(ROOT.parent))) as d:
            root=Path(d);root.chmod(0o700);p=root/'file';p.write_bytes(b'{}');p.chmod(0o600)
            link=root/'link';link.symlink_to(p)
            with self.assertRaises(OSError):m.read(link)
            link.unlink();os.link(p,link)
            with self.assertRaises(m.Blocked):m.read(p)
            link.unlink();p.chmod(0o644)
            with self.assertRaises(m.Blocked):m.read(p)
            p.chmod(0o600)
            with self.assertRaises(m.Blocked):m.read(p,636,636)
            p.unlink();os.mkfifo(p,0o600)
            with self.assertRaises(m.Blocked):m.read(p)
if __name__=='__main__':unittest.main()
