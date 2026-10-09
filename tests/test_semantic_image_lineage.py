import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import verify_semantic_image_lineage as m

def encode(v): return json.dumps(v, sort_keys=True).encode()

def fixture():
    payload = {'Dockerfile.semantic-provider': m.sha(b'FROM pinned'), 'tools/adapter.py': m.sha(b'code')}
    expected = dict(installation='fixture', adapterImage='sha256:'+'a'*64,
        southboundImage='sha256:'+'b'*64, sourceCommit='c'*40,
        sourceURLBase='https://raw.githubusercontent.com/fixture/repo',
        baseImage='python@sha256:'+'d'*64, runtimeUser='10006:10006',
        gatewayVersion='3.18.0', payloadHashes=payload)
    intent = {k: v for k, v in expected.items() if k not in
        ('installation', 'adapterImage', 'southboundImage', 'gatewayVersion')}
    intent.update(schema='ouf.semantic-provider-image-stage.v1', payloadHash=m.sha(m.encoded(payload)),
        gateway={'id':'e'*64, 'image':expected['southboundImage'],
                 'version':'3.18.0', 'configurationHash':'f'*64, 'private':'DO_NOT_PRINT_SENTINEL'})
    stage = dict(intent=intent, imageId=expected['adapterImage'], baseImageId='sha256:'+'1'*64,
        noRuntimeContainersCreated=True, noRouteWrites=True, noIAMWrites=True,
        noPolicyPublication=True, providerCalls=0, notReleaseAcceptance=True)
    trust = dict(verified=True, notReleaseAcceptance=True, intent={'installation':'fixture',
        'adapterImage':dict(id=expected['adapterImage'], sourceCommit=expected['sourceCommit'],
            runtimeUser=expected['runtimeUser'], payloadHash=intent['payloadHash']),
        'gateway':intent['gateway']})
    manifest = dict(schema='ouf.semantic-provider-stopped-manifest.v1', installation='fixture',
        startAuthorized=False, containers=[{'image':expected['adapterImage'], 'readOnlyRoot':True},
        {'image':expected['southboundImage'], 'readOnlyRoot':False}])
    raw = {'manifest':encode(manifest), 'trust':encode(trust), 'image-stage':encode(stage),
           'build-intent':encode(intent), 'Dockerfile.semantic-provider':b'FROM pinned', 'tools/adapter.py':b'code'}
    pins = {k:m.sha(raw[k]) for k in ('manifest','trust')}
    return raw, pins, expected

class Tests(unittest.TestCase):
    def test_success_precise_claims_and_redaction(self):
        raw,pins,e=fixture(); r=m.project(raw,pins,e)
        self.assertTrue(r['buildContextMatchesPinnedSource'])
        for k in ('acceptanceGranted','imageBytesVerified','imagePublisherProvenanceVerified',
                  'buildReproduced','generationObserved','rootfsSealProven','startAuthorized'):
            self.assertIs(r[k],False)
        self.assertNotIn(b'SENTINEL',m.encoded(r))

    def test_every_input_drift(self):
        for name in fixture()[0]:
            raw,pins,e=fixture(); raw[name]+=b'x'
            with self.subTest(name=name),self.assertRaises((ValueError,KeyError)):m.project(raw,pins,e)

    def test_resealed_binding_mismatch(self):
        changes=[('image-stage','imageId','sha256:'+'9'*64),
                 ('image-stage','providerCalls',True),('image-stage','noIAMWrites',False),
                 ('manifest','startAuthorized',True),('trust','verified',False)]
        for name,key,val in changes:
            raw,pins,e=fixture();obj=json.loads(raw[name]);obj[key]=val;raw[name]=encode(obj)
            pins={k:m.sha(raw[k]) for k in pins}
            with self.subTest(name=name,key=key),self.assertRaises(ValueError):m.project(raw,pins,e)

    def test_source_or_base_change_with_coherent_intent(self):
        for key,val in [('sourceCommit','9'*40),('baseImage','python@sha256:'+'9'*64),
                        ('runtimeUser','0:0'),('sourceURLBase','https://untrusted.invalid')]:
            raw,pins,e=fixture();intent=json.loads(raw['build-intent']);intent[key]=val
            raw['build-intent']=encode(intent);stage=json.loads(raw['image-stage']);stage['intent']=intent
            raw['image-stage']=encode(stage)
            with self.subTest(key=key),self.assertRaises(ValueError):m.project(raw,pins,e)

    def test_context_substitution_even_if_receipt_resealed(self):
        raw,pins,e=fixture();raw['tools/adapter.py']=b'evil'
        intent=json.loads(raw['build-intent']);intent['payloadHashes']['tools/adapter.py']=m.sha(b'evil')
        intent['payloadHash']=m.sha(m.encoded(intent['payloadHashes']))
        raw['build-intent']=encode(intent);stage=json.loads(raw['image-stage']);stage['intent']=intent
        raw['image-stage']=encode(stage)
        with self.assertRaises(ValueError):m.project(raw,pins,e)

    def test_wrong_southbound_or_root_role(self):
        for key,val in [('image','sha256:'+'9'*64),('readOnlyRoot',True)]:
            raw,pins,e=fixture();obj=json.loads(raw['manifest']);obj['containers'][1][key]=val
            raw['manifest']=encode(obj);pins['manifest']=m.sha(raw['manifest'])
            with self.subTest(key=key),self.assertRaises(ValueError):m.project(raw,pins,e)

    def test_double_read_metadata_drift(self):
        raw,pins,e=fixture();paths={k:Path('/fixed')/k for k in raw};calls=[]
        def reader(p):
            calls.append(p);return raw[str(p.relative_to('/fixed'))],(1,)
        m.verify(paths,pins,e,reader);self.assertEqual(calls,list(paths.values())*2)
        calls=[]
        def drift(p):
            calls.append(p);return raw[str(p.relative_to('/fixed'))],(len(calls)>len(paths),)
        with self.assertRaises(ValueError):m.verify(paths,pins,e,drift)

    def test_real_standalone_cli_and_error_redaction(self):
        raw,pins,e=fixture()
        helper=(ROOT/'tools/verify_semantic_configuration_provenance.py').read_text()
        helper=helper.split("if __name__=='__main__':")[0].rstrip()
        code=(ROOT/'tools/verify_semantic_image_lineage.py').read_text().replace(
            'from tools.verify_semantic_configuration_provenance import read, decode, require, sha',helper)
        with tempfile.TemporaryDirectory(dir=os.environ.get('OUF_TEST_ROOT',str(ROOT.parent))) as d:
            root=Path(d);root.chmod(0o700);ctx=root/'context';ctx.mkdir(mode=0o700)
            (ctx/'tools').mkdir(mode=0o700)
            names={'manifest':'stopped-manifest.json','trust':'trust-receipt.json',
                   'image-stage':'stage-receipt.json','build-intent':'build-intent.json'}
            for k,v in raw.items():
                p=root/names[k] if k in names else ctx/k;p.write_bytes(v);p.chmod(0o600)
            program=root/'verify.py';program.write_text(code);program.chmod(0o600)
            args=[sys.executable,'-I','-B',str(program)]
            for k in ('manifest','trust','image-stage'):args+=['--'+k+'-root',d]
            for k,v in e.items():
                option={'adapterImage':'adapter-image','southboundImage':'southbound-image',
                  'sourceCommit':'source-commit','sourceURLBase':'source-url-base','baseImage':'base-image',
                  'runtimeUser':'runtime-user','gatewayVersion':'gateway-version','payloadHashes':'payload-hashes'}.get(k,k)
                args+=['--'+option,json.dumps(v) if isinstance(v,dict) else v]
            for k,v in pins.items():args+=['--'+k+'-hash',v]
            before={str(p):p.read_bytes() for p in root.rglob('*') if p.is_file()}
            proc=subprocess.run(args,capture_output=True);self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
            self.assertNotIn(b'SENTINEL',proc.stdout+proc.stderr)
            self.assertEqual(before,{str(p):p.read_bytes() for p in root.rglob('*') if p.is_file()})
            (ctx/'tools/adapter.py').write_bytes(b'SECRET_FAILURE_SENTINEL')
            proc=subprocess.run(args,capture_output=True);self.assertEqual(proc.returncode,1)
            self.assertNotIn(b'SENTINEL',proc.stdout+proc.stderr);self.assertNotIn(d.encode(),proc.stdout+proc.stderr)

if __name__=='__main__':unittest.main()
