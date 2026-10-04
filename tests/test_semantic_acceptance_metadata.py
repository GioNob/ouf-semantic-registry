import copy
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('readback',ROOT/'tools/read_semantic_acceptance_metadata.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def fixture():
    tls='/private/tls';trust='/private/trust'
    roles=[('adapter',True,[('adapter.json',tls),('adapter/server.crt',trust),
        ('adapter/server.key',trust),('adapter/provider-receipt.key',trust),('trust-bundle.pem',trust)]),
        ('southbound',False,[('config.yaml',tls),('apisix.yaml',tls),('trust-bundle.pem',trust)])]
    specs=[];rows=[];ids={}
    for i,(role,ro,slots) in enumerate(roles,1):
        cid=str(i)*64;image='sha256:'+str(i+2)*64;ids[role]=cid
        mounts=[{'source':root+'/'+suffix,'target':'/run/SECRET_SENTINEL/'+suffix,'readOnly':True} for suffix,root in slots]
        specs.append({'name':role,'image':image,'readOnlyRoot':ro,'mounts':mounts})
        observed=[dict(v,metadata={'kind':'file','contentsRead':False,'contentsAccepted':False,
            'attributes':[1,2,stat.S_IFREG|0o600,10006,10006,1,128,3,4]}) for v in mounts]
        rows.append({'containerId':cid,'name':role,'environmentRead':False,'fullCreationAcceptanceProven':False,
            'image':{'id':image,'rootfs':{'Type':'layers','Layers':['sha256:'+'a'*64]}},'mountMetadata':observed,
            'selectedConfiguration':{'command':['DO_NOT_PRINT_SECRET'],'extra':'DO_NOT_PRINT_SECRET'}})
    manifest={'schema':'ouf.semantic-provider-stopped-manifest.v1','installation':'fixture',
        'startAuthorized':False,'containers':specs}
    raw_manifest=m.encoded(manifest)
    journal={'schema':'ouf.semantic-provider-stopped-create.v1','state':'CREATED_STOPPED',
        'startAuthorized':False,'manifestHash':m.sha(raw_manifest),'transaction':'f'*32,'candidateIds':ids}
    dossier={'installationRef':'fixture','candidates':rows};raw_dossier=m.encoded(dossier)
    receipt={'schema':'ouf.semantic-target-acceptance-inventory.v1','dossierHash':m.sha(raw_dossier),'candidateCount':2,'mountCount':8}
    for k in ('sourceCustodyVerified','candidatesNeverStarted','stableAcrossReads','readOnlyTarget',
        'privateEvidenceOnly','notReleaseAcceptance','noSecretsPrinted'):receipt[k]=True
    for k in ('atomicSnapshotProven','fullCreationAcceptanceProven','mountContentsRead','environmentRead',
        'deploymentAuthorityProven','runtimeRegistrationAuthorized','startAuthorized','rulesChanged','unitsChanged','containersChanged'):receipt[k]=False
    for k in ('keysGenerated','privateKeysRead','signaturesIssued','providerCalls','dnsCalls','iamCalls'):receipt[k]=0
    return [manifest,journal,dossier,receipt],tls,trust

class ReadbackTests(unittest.TestCase):
    def run_projection(self,values=None):
        original,tls,trust=fixture();values=values or original
        # Tests schema rejection independently from the already tested byte pin.
        raws=list(map(m.encoded,values));values[1]['manifestHash']=m.sha(raws[0]);values[3]['dossierHash']=m.sha(raws[2])
        raws=list(map(m.encoded,values))
        return m.project(raws,[m.sha(v) for v in raws[:3]],'fixture',tls,trust)
    def test_exact_eight_slots_and_redaction(self):
        result=self.run_projection();raw=m.encoded(result)
        self.assertEqual(sum(len(r['mounts']) for r in result['candidates']),8)
        for secret in (b'SECRET_SENTINEL',b'DO_NOT_PRINT_SECRET',b'/private/',b'"generation"'):
            self.assertNotIn(secret,raw)
        self.assertFalse(result['acceptanceGranted']);self.assertFalse(result['currentTargetInspected'])
    def test_hash_mismatch(self):
        values,tls,trust=fixture();raws=list(map(m.encoded,values))
        with self.assertRaises(m.Blocked):m.project(raws,['0'*64]*3,'fixture',tls,trust)
    def test_duplicate_nonfinite_and_oversize(self):
        for raw in (b'{"x":1,"x":2}',b'{"x":NaN}',b'['+b'0'*(m.LIMIT)+b']',b'[]'):
            with self.assertRaises((m.Blocked,ValueError)):m.decode(raw)
    def test_unknown_mount_and_duplicate_destination(self):
        for operation in ('source','target'):
            values,_,_=fixture();mounts=values[2]['candidates'][0]['mountMetadata']
            mounts[0][operation]=mounts[1][operation]
            with self.assertRaises(m.Blocked):self.run_projection(values)
    def test_false_receipt_or_accepted_content(self):
        for key in ('startAuthorized','fullCreationAcceptanceProven','mountContentsRead','environmentRead'):
            values,_,_=fixture();values[3][key]=True
            with self.assertRaises(m.Blocked):self.run_projection(values)
        values,_,_=fixture();values[2]['candidates'][0]['mountMetadata'][0]['metadata']['contentsAccepted']=True
        with self.assertRaises(m.Blocked):self.run_projection(values)
    def test_bad_metadata(self):
        for index,value in ((2,stat.S_IFIFO|0o600),(2,stat.S_IFREG|0o666),(5,2),(6,-1),(3,True)):
            values,_,_=fixture();values[2]['candidates'][0]['mountMetadata'][0]['metadata']['attributes'][index]=value
            with self.assertRaises(m.Blocked):self.run_projection(values)
    def test_reader_only_fixed_inputs_and_drift(self):
        values,tls,trust=fixture();raws=list(map(m.encoded,values));paths=[Path('/fixed/'+str(i)) for i in range(4)]
        seen=[]
        def reader(path):seen.append(path);return raws[paths.index(path)]
        m.readback(paths,[m.sha(v) for v in raws[:3]],'fixture',tls,trust,reader)
        self.assertEqual(seen,paths*2)
        n=0
        def changed(path):
            nonlocal n
            n+=1;return raws[paths.index(path)] if n<=4 else b'changed'
        with self.assertRaises(m.Blocked):m.readback(paths,[m.sha(v) for v in raws[:3]],'fixture',tls,trust,changed)
    def test_cli_failure_redacts(self):
        p=subprocess.run([os.sys.executable,'-I','-B',str(ROOT/'tools/read_semantic_acceptance_metadata.py'),
            *sum((['--'+v,'/DO_NOT_PRINT_SECRET'] for v in ('manifest-root','creation-root','dossier-root','tls-root','trust-root')),[]),
            '--manifest-hash','0'*64,'--creation-hash','0'*64,'--dossier-hash','0'*64,'--installation','fixture'],capture_output=True)
        self.assertEqual(p.returncode,1);self.assertNotIn(b'DO_NOT_PRINT_SECRET',p.stdout+p.stderr)
    def test_successful_isolated_cli_no_writes(self):
        values,tls,trust=fixture();raws=list(map(m.encoded,values))
        with tempfile.TemporaryDirectory(dir=os.environ.get('OUF_TEST_ROOT',str(ROOT.parent))) as directory:
            root=Path(directory);root.chmod(0o700)
            for name,raw in zip(('stopped-manifest.json','creation-journal.json','target-dossier.json','inventory-receipt.json'),raws):
                path=root/name;path.write_bytes(raw);path.chmod(0o600)
            before={p.name:(p.read_bytes(),p.stat().st_mode,p.stat().st_mtime_ns) for p in root.iterdir()}
            p=subprocess.run([os.sys.executable,'-I','-B',str(ROOT/'tools/read_semantic_acceptance_metadata.py'),
                '--manifest-root',directory,'--creation-root',directory,'--dossier-root',directory,
                '--tls-root',tls,'--trust-root',trust,'--manifest-hash',m.sha(raws[0]),
                '--creation-hash',m.sha(raws[1]),'--dossier-hash',m.sha(raws[2]),'--installation','fixture'],capture_output=True)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            self.assertIn(b'HISTORICAL_ONLY=true',p.stdout);self.assertNotIn(b'SECRET_SENTINEL',p.stdout+p.stderr)
            after={p.name:(p.read_bytes(),p.stat().st_mode,p.stat().st_mtime_ns) for p in root.iterdir()}
            self.assertEqual(before,after)
    def test_real_file_nofollow_links_and_permissions(self):
        self.assertEqual(os.geteuid(),0,'Run this IO fixture as root; no skip replaces it')
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'file';p.write_bytes(b'{}');p.chmod(0o600)
            # /tmp is intentionally untrusted; isolate IO checks here. Ancestors tested separately.
            with patch.object(m,'ancestors'):
                self.assertEqual(m.private(p),b'{}')
                link=Path(directory)/'link';link.symlink_to(p)
                with self.assertRaises(OSError):m.private(link)
                link.unlink();os.link(p,link)
                with self.assertRaises(m.Blocked):m.private(p)
                link.unlink();p.chmod(0o644)
                with self.assertRaises(m.Blocked):m.private(p)
                p.unlink();os.mkfifo(p,0o600)
                with self.assertRaises(m.Blocked):m.private(p)
    def test_untrusted_ancestor(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory).chmod(0o777)
            with self.assertRaises(m.Blocked):m.ancestors(Path(directory)/'file')
        with self.assertRaises(m.Blocked):m.ancestors(Path('/private/../other/file'))

if __name__=='__main__':unittest.main()
