#!/bin/bash
# Section47 READY_SAME_READ_SCOPE_45_46: complete field rules; no acceptance/sign/start.
set -euo pipefail
exec sudo /usr/bin/python3 -I -B - \
 --manifest-root /etc/ouf/deploy-snapshots/semantic-provider-candidate-manifest-20261003-130410/prepared \
 --creation-root /etc/ouf/deploy-snapshots/semantic-provider-stopped-create-20261003-135106/prepared \
 --launch-root /etc/ouf/deploy-snapshots/semantic-provider-launch-inputs-20261003-124906/prepared \
 --credential-root /etc/ouf/deploy-snapshots/semantic-southbound-validator-20261003-114001/prepared \
 --runtime-root /etc/ouf/deploy-snapshots/semantic-provider-runtime-20261002-222530 \
 --trust-root /etc/ouf/deploy-snapshots/semantic-provider-trust-20261002-212033 \
 --manifest-hash 052b46a56ea666971f135c75af48b3342dbeb68e2f17f1f16263a99351df88bd \
 --creation-hash a1c2acd9924fc0f924ded7c2d59f128ef2d8b8dd11c62484a901f628022aaae7 \
 --launch-hash 715ad05237a26f9f63324f2bee87296659420d081ae3598414f798dc74f319cc \
 --installation ouf-lab-netcup-01 --credential-uid 636 --credential-gid 636 \
 --docker-path /usr/bin/docker --docker-host unix:///var/run/docker.sock \
 --docker-hash 7f5b38163f9c5367f4b42d905c0505877eafa4c20abe49430c85a770aefacf40 \
 --public-scratch-root /tmp --expected-section45 '{"adapter":{"configHash":"17a6d053f4edd9e714ccbfd4373e6e39480578161af97b22b1f3cd57d6035e54","hostConfigHash":"06768922cdaf3ab73744c9ee1bf805c62687a38f25ffbb1d9ac028eb6cae5822","environmentHash":"97c911ee90364f2f4e907af7d6d4e617ad51d065dce2755826dea58d1713b9c4","fullInspectHash":"25aaba6b09a205f9dd2e29f29c9ab6bba89309374e7600d0f984cbc3403ed4ef","imageInspectHash":"5e24aaff3746e452977f5047226c7dc6406b337df9835859c781a6c19ce6d0be"},"southbound":{"configHash":"2f206dd24295e3792cc21919e91bf558684a2f842b9a958b94fcb31934f0d5d6","hostConfigHash":"a815610fd7f164eb65e8b447ad2560b002f62c0f4440db8fc193590c917e0964","environmentHash":"2bd856400c11aeda1bd3171c5e9b44e2ea21e4392f4a17ac355522a10ed770e5","fullInspectHash":"d6914b8cfe1c6d2ed8408a1fc488cc6164907c96a5215e7cfcdfe6128b344214","imageInspectHash":"4c5e48e985f857380163cbafb98aa8d714c64de2b81e485e1ac00a8e3acd4046"}}' --expected-section46 '{"binding":"a486c01d486023f960945c71737d151eacfe91b341ffdb5b7aa0cc03c316b7d3","creation":"a1c2acd9924fc0f924ded7c2d59f128ef2d8b8dd11c62484a901f628022aaae7","credential":"661c6853548fa7282442c61447c6bcc53105e4cac8e23a4158dd63dfd5790cc6","env":"34c981245c4d49193b45afa26d5e386763f7f05ad519583e643773d01c2bed32","launch":"715ad05237a26f9f63324f2bee87296659420d081ae3598414f798dc74f319cc","manifest":"052b46a56ea666971f135c75af48b3342dbeb68e2f17f1f16263a99351df88bd","secret":"b9ef5dd3904b4a8fad719c0ca76e4356d977b1a8b86c7bf404d006700b1f00c8","trust":"8a108a3c4b47f86ef58589c7322572db88991672f4c328a200711a9fd5576776"}' <<'OUF_PYTHON'
"""Read-only complete Config/HostConfig rules with exact §45/§46 binding."""
"""Exact sealed launch Env/OIDC/MAC binding; no IAM grant, signature or start."""
import argparse
import hmac
import os
from pathlib import Path
import re
import stat
import sys
"""Fixed never-started candidate Config/HostConfig review; no OCI acceptance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import stat
import subprocess
import sys
import tempfile
import time
"""Project sealed historical candidate metadata; no Docker or mount-content IO."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

LIMIT = 131072
class Blocked(ValueError):
    pass
def require(ok):
    if not ok:
        raise Blocked('SEALED_METADATA_UNPROVEN')
def sha(raw):
    return hashlib.sha256(raw).hexdigest()
def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
def decode(raw):
    require(type(raw) is bytes and 0 < len(raw) <= LIMIT)
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out); out[key] = value
        return out
    value = json.loads(raw, object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(Blocked()))
    require(type(value) is dict)
    return value
def attrs(s):
    return tuple(getattr(s, k) for k in ('st_dev','st_ino','st_mode','st_uid','st_gid',
        'st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
def ancestors(path):
    require(path.is_absolute() and '..' not in path.parts)
    for parent in (path.parent, *path.parent.parents):
        info = parent.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022)
    parent = path.parent.lstat()
    require(parent.st_gid == 0 and stat.S_IMODE(parent.st_mode) == 0o700)
def private(path):
    ancestors(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_uid == before.st_gid == 0
            and before.st_nlink == 1 and stat.S_IMODE(before.st_mode) == 0o600
            and 0 < before.st_size <= LIMIT)
        raw = os.read(fd, LIMIT+1)
        require(len(raw) == before.st_size and attrs(before) == attrs(os.fstat(fd))
            and attrs(before) == attrs(path.lstat()))
        return raw
    finally:
        os.close(fd)
def project(raws, expected, installation, tls_root, trust_root):
    require(len(raws) == 4 and len(expected) == 3)
    require(all(re.fullmatch('[0-9a-f]{64}', x) for x in expected))
    require([sha(raw) for raw in raws[:3]] == expected)
    manifest, journal, dossier, receipt = map(decode, raws)
    require(manifest['schema'] == 'ouf.semantic-provider-stopped-manifest.v1'
        and manifest['installation'] == dossier['installationRef'] == installation
        and manifest['startAuthorized'] is False
        and journal['schema'] == 'ouf.semantic-provider-stopped-create.v1'
        and journal['state'] == 'CREATED_STOPPED' and journal['startAuthorized'] is False
        and journal['manifestHash'] == expected[0]
        and re.fullmatch('[0-9a-f]{32}', journal['transaction'])
        and receipt['schema'] == 'ouf.semantic-target-acceptance-inventory.v1'
        and receipt['dossierHash'] == expected[2]
        and receipt['candidateCount'] == 2 and receipt['mountCount'] == 8)
    for k in ('sourceCustodyVerified','candidatesNeverStarted','stableAcrossReads',
              'readOnlyTarget','privateEvidenceOnly','notReleaseAcceptance','noSecretsPrinted'):
        require(receipt[k] is True)
    for k in ('atomicSnapshotProven','fullCreationAcceptanceProven','mountContentsRead',
              'environmentRead','deploymentAuthorityProven','runtimeRegistrationAuthorized',
              'startAuthorized','rulesChanged','unitsChanged','containersChanged'):
        require(receipt[k] is False)
    for k in ('keysGenerated','privateKeysRead','signaturesIssued','providerCalls','dnsCalls','iamCalls'):
        require(type(receipt[k]) is int and receipt[k] == 0)
    specs = manifest['containers']; candidates = dossier['candidates']
    require(type(specs) is list and type(candidates) is list and len(specs) == len(candidates) == 2)
    ids = journal['candidateIds']
    require(type(ids) is dict and len(ids) == 2 and len(set(ids.values())) == 2
        and set(ids) == {s['name'] for s in specs}
        and all(type(x) is str and re.fullmatch('[0-9a-f]{64}', x) for x in ids.values())
        and {r['containerId'] for r in candidates} == set(ids.values()))
    mapping = {
        'adapter': [('adapter.json',tls_root,'CONFIG'), ('adapter/server.crt',trust_root,'PUBLIC_CERT'),
            ('adapter/server.key',trust_root,'TLS_SECRET'), ('adapter/provider-receipt.key',trust_root,'PURPOSE_MAC_SECRET'),
            ('trust-bundle.pem',trust_root,'PUBLIC_TRUST')],
        'southbound': [('config.yaml',tls_root,'CONFIG'), ('apisix.yaml',tls_root,'CONFIG_WITH_TLS_SECRET'),
            ('trust-bundle.pem',trust_root,'PUBLIC_TRUST')]}
    rows = []; roles = set()
    for spec in specs:
        role = 'adapter' if spec['readOnlyRoot'] is True else 'southbound'
        require(role not in roles); roles.add(role)
        row = next(r for r in candidates if r['containerId'] == ids[spec['name']])
        require(row['name'] == spec['name'] and row['environmentRead'] is False
            and row['fullCreationAcceptanceProven'] is False
            and re.fullmatch('sha256:[0-9a-f]{64}', spec['image'])
            and row['image']['id'] == spec['image'])
        observed = row['mountMetadata']; mounts = spec['mounts']; expected_mounts = mapping[role]
        require(len(observed) == len(mounts) == len(expected_mounts)
            and len({m['source'] for m in observed}) == len(observed)
            and len({m['target'] for m in observed}) == len(observed))
        projected = []
        for suffix, root, category in expected_mounts:
            source = str(Path(root)/suffix)
            matches = [m for m in observed if m['source'] == source]
            require(len(matches) == 1); m = matches[0]
            matching = [v for v in mounts if v['source'] == source and v['target'] == m['target']]
            require(len(matching) == 1 and matching[0]['readOnly'] is True and m['readOnly'] is True)
            target = m['target']; require(type(target) is str and len(target) <= 4096
                and target.startswith('/') and '..' not in Path(target).parts)
            metadata = m['metadata']; a = metadata['attributes']
            require(metadata['kind'] == 'file' and metadata['contentsRead'] is False
                and metadata['contentsAccepted'] is False and type(a) is list and len(a) == 9
                and all(type(v) is int and v >= 0 for v in a)
                and stat.S_ISREG(a[2]) and not a[2] & 0o022 and a[5] == 1)
            projected.append({'slot': suffix, 'category': category, 'sourceBindingHash':sha(source.encode()),
                'destinationBindingHash':sha(target.encode()),'uid':a[3],'gid':a[4],
                'mode':format(stat.S_IMODE(a[2]), '04o'),'size':a[6],
                'readOnly':True,'contentsRead':False,'contentsAccepted':False})
        layers = row['image']['rootfs']
        require(layers['Type'] == 'layers' and type(layers['Layers']) is list
            and 1 <= len(layers['Layers']) <= 256
            and all(type(x) is str and re.fullmatch('sha256:[0-9a-f]{64}', x) for x in layers['Layers']))
        rows.append({'role':role,'containerIdHash':sha(ids[spec['name']].encode()),
            'imageId':spec['image'],'layerDescriptorCount':len(layers['Layers']),
            'layerDescriptorsHash':sha(encoded(layers)),'readOnlyRoot':spec['readOnlyRoot'],'mounts':projected})
    return {'schema':'ouf.semantic-acceptance-metadata-readback.v1',
        'inputHashes':[sha(raw) for raw in raws], 'candidates':sorted(rows,key=lambda r:r['role']),
        'historicalEvidenceOnly':True,'currentTargetInspected':False,'atomicSnapshotProven':False,
        'acceptanceGranted':False,'fullCreationAcceptanceProven':False,
        'generationObserved':False,'mountContentsRead':False,'environmentRead':False,
        'privateKeysRead':0,'signaturesIssued':0,'providerCalls':0,
        'targetFilesWritten':0,'containersChanged':False,'runtimeRegistered':False,'startAuthorized':False}
def readback(paths, expected, installation, tls_root, trust_root, reader=private):
    # Fixed file list; no path from private JSON is ever opened.
    raws = [reader(p) for p in paths]
    result = project(raws, expected, installation, tls_root, trust_root)
    require(raws == [reader(p) for p in paths])
    return result
def main():
    try:
        p = argparse.ArgumentParser(description=__doc__)
        for name in ('manifest-root','creation-root','dossier-root','tls-root','trust-root'):
            p.add_argument('--'+name,required=True,type=Path)
        for name in ('manifest-hash','creation-hash','dossier-hash','installation'):
            p.add_argument('--'+name,required=True)
        a = p.parse_args()
        require(os.geteuid() == 0 and sys.flags.isolated and sys.dont_write_bytecode)
        paths = [a.manifest_root/'stopped-manifest.json',a.creation_root/'creation-journal.json',
            a.dossier_root/'target-dossier.json',a.dossier_root/'inventory-receipt.json']
        for root in (a.tls_root,a.trust_root):
            require(root.is_absolute() and '..' not in root.parts)
        result = readback(paths,[a.manifest_hash,a.creation_hash,a.dossier_hash],a.installation,a.tls_root,a.trust_root)
        print('SEMANTIC_ACCEPTANCE_METADATA='+encoded(result).decode())
        print('SEMANTIC_ACCEPTANCE_METADATA=PASS HISTORICAL_ONLY=true ACCEPTANCE_GRANTED=false START_AUTHORIZED=false')
        return 0
    except Exception:
        print('SEMANTIC_ACCEPTANCE_METADATA=BLOCKED REASON=SEALED_METADATA_UNPROVEN NO_SECRETS_PRINTED=true')
        return 1


class Blocked(ValueError):pass
def require(ok):
    if not ok:raise Blocked('CREATION_CONFIGURATION_UNPROVEN')
class Budget:
    def __init__(self):self.deadline=time.monotonic()+60
    def remaining(self):
        value=self.deadline-time.monotonic();require(value>0);return min(value,10)
def binary(path,budget):
    require(path.is_absolute() and '..' not in path.parts)
    for p in path.parents:
        s=p.lstat();require(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and not s.st_mode&0o022)
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        before=os.fstat(fd);require(stat.S_ISREG(before.st_mode) and before.st_uid==0
            and before.st_mode&0o111 and not before.st_mode&0o022 and 0<before.st_size<=64000000)
        h=hashlib.sha256();size=0
        while True:
            budget.remaining();raw=os.read(fd,65536)
            if not raw:break
            size+=len(raw);require(size<=64000000);h.update(raw)
        require(size==before.st_size and attrs(before)==attrs(os.fstat(fd))==attrs(path.lstat()))
        return h.hexdigest()
    finally:os.close(fd)
class Query:
    def __init__(self,path,pin,scratch,host):
        self.budget=Budget();self.path=path;self.pin=pin;self.scratch=scratch;self.host=host
        require(re.fullmatch('[0-9a-f]{64}',pin) and host.startswith('unix:///') and '..' not in Path(host[7:]).parts)
        info=scratch.lstat();require(scratch.is_absolute() and '..' not in scratch.parts and stat.S_ISDIR(info.st_mode) and info.st_uid==0
            and (not info.st_mode&0o022 or info.st_mode&stat.S_ISVTX))
        for p in scratch.parents:
            info=p.lstat();require(stat.S_ISDIR(info.st_mode) and info.st_uid==0 and not info.st_mode&0o022)
        require(binary(path,self.budget)==pin)
    def __call__(self,kind,identifier):
        require(kind in ('container','image') and re.fullmatch('[0-9a-f]{64}' if kind=='container' else 'sha256:[0-9a-f]{64}',identifier))
        require(binary(self.path,self.budget)==self.pin)
        # Empty CLI directory only. Full private inspect stdout stays in memory.
        with tempfile.TemporaryDirectory(prefix='ouf-empty-docker-',dir=self.scratch) as config:
            p=subprocess.Popen([str(self.path),'--config',config,'--host',self.host,'inspect','--type',kind,
                '--format','{{json .}}',identifier],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                env={'PATH':'/usr/bin:/bin','LC_ALL':'C'})
            try:
                raw=bytearray();deadline=time.monotonic()+self.budget.remaining()
                with selectors.DefaultSelector() as sel:
                    sel.register(p.stdout,selectors.EVENT_READ)
                    while True:
                        left=min(deadline-time.monotonic(),self.budget.remaining());require(left>0)
                        require(sel.select(left))
                        part=os.read(p.stdout.fileno(),65536)
                        if not part:break
                        raw.extend(part);require(len(raw)<=131072)
                require(p.wait(timeout=max(0.001,deadline-time.monotonic()))==0)
            finally:
                if p.poll() is None:p.kill();p.wait()
                p.stdout.close()
        require(binary(self.path,self.budget)==self.pin);return decode(bytes(raw))
def environment(cfg):
    rows=cfg.get('Env') or [];require(type(rows) is list and len(rows)<=256);out={}
    for item in rows:
        require(type(item) is str and '=' in item);name,value=item.split('=',1)
        require(re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',name) and name not in out and len(item)<=16384);out[name]=value
    return out
def review(manifest,journal,query):
    require(manifest['schema']=='ouf.semantic-provider-stopped-manifest.v1' and manifest['startAuthorized'] is False
        and journal['schema']=='ouf.semantic-provider-stopped-create.v1' and journal['state']=='CREATED_STOPPED'
        and journal['startAuthorized'] is False)
    specs=manifest['containers'];ids=journal['candidateIds'];require(type(specs) is list and len(specs)==len(ids)==2
        and set(ids)=={s['name'] for s in specs} and len(set(ids.values()))==2)
    rows=[];captured=[]
    for spec in specs:
        cid=ids[spec['name']];row=query('container',cid);image=query('image',spec['image']);captured.extend((row,image))
        require(row['Id']==cid and row['Image']==image['Id']==spec['image'] and row['Name']=='/'+spec['name'])
        state=row['State'];require(state['Status']=='created' and state['Running'] is False and state['Restarting'] is False
            and state['Pid']==0 and state['StartedAt'].startswith('0001-01-01T') and row['RestartCount']==0)
        cfg,base,host=row['Config'],image['Config'],row['HostConfig']
        labels=cfg.get('Labels') or {}
        require(labels.get('ouf.semantic.candidate.transaction')==journal['transaction']
            and labels.get('ouf.semantic.candidate.manifest')==journal['manifestHash'])
        require(cfg['User']==spec['user'] and cfg.get('Entrypoint')==base.get('Entrypoint')
            and cfg.get('Cmd')==(spec['command'] or base.get('Cmd')) and cfg.get('WorkingDir')==base.get('WorkingDir')
            and not base.get('Volumes') and cfg['Healthcheck']['Test']==['NONE'])
        require(host['Privileged'] is False and host['ReadonlyRootfs'] is spec['readOnlyRoot']
            and host['RestartPolicy']['Name']=='no' and set(host['CapDrop'] or [])=={'ALL'}
            and not any(host.get(k) for k in ('CapAdd','Devices','DeviceRequests','PortBindings'))
            and host['Memory']==host['MemorySwap']==spec['memoryBytes'] and host['PidsLimit']==spec['pidsLimit']
            and host['Dns']==spec['dnsServers'])
        expected={(m['source'],m['target']) for m in spec['mounts']};mounts=row['Mounts']
        require(len(expected)==len(mounts)==len(spec['mounts']) and expected=={(m['Source'],m['Destination']) for m in mounts}
            and all(m['readOnly'] is True for m in spec['mounts'])
            and all(m['Type']=='bind' and m['RW'] is False and m['Propagation']=='rprivate' for m in mounts))
        env,baseenv=environment(cfg),environment(base)
        require(all(env.get(k)==v for k,v in baseenv.items()) and (spec.get('envFile') or env==baseenv))
        # Complete objects are sealed, including unclassified or future fields.
        # Their hashes do not confer semantic acceptance of those fields.
        rows.append({'role':'adapter' if spec['readOnlyRoot'] else 'southbound','containerIdHash':sha(cid.encode()),
            'imageId':image['Id'],'fullInspectHash':sha(encoded(row)),'imageInspectHash':sha(encoded(image)),
            'configHash':sha(encoded(cfg)),'hostConfigHash':sha(encoded(host)),
            'environmentHash':sha(encoded(env)),'imageEnvironmentHash':sha(encoded(baseenv)),
            'environmentEntryCount':len(env),'additionalEnvironmentEntryCount':len(set(env)-set(baseenv)),
            'packagedStartupMatches':True,'declaredHostRestrictionsMatch':True,'manifestMountBindingsMatch':True,
            'allConfigurationFieldsSemanticallyAccepted':False})
    return sorted(rows,key=lambda r:r['role']),captured
def collect(raws,pins,installation,query):
    require([sha(raw) for raw in raws]==pins);manifest,journal=map(decode,raws)
    require(manifest['installation']==installation and journal['manifestHash']==pins[0])
    rows,first=review(manifest,journal,query);other,second=review(manifest,journal,query)
    require(first==second and rows==other)
    return {'schema':'ouf.semantic-creation-configuration-readback.v1','inputHashes':pins,'candidates':rows,
        'environmentRead':True,'environmentFilesRead':False,'fullInspectRead':True,'currentTargetInspected':True,
        'stableAcrossReads':True,'atomicSnapshotProven':False,'fullOciAcceptanceProven':False,'generationObserved':False,
        'mountViewInspected':False,'privateKeysRead':0,'privateMaterialSpooled':False,'providerCalls':0,
        'signaturesIssued':0,'targetFilesWritten':0,'containersChanged':False,'acceptanceGranted':False,
        'runtimeRegistered':False,'startAuthorized':False}
def main():
    try:
        p=argparse.ArgumentParser(description=__doc__)
        for k in ('manifest-root','creation-root','docker-path','public-scratch-root'):p.add_argument('--'+k,type=Path,required=True)
        for k in ('manifest-hash','creation-hash','installation','docker-hash','docker-host'):p.add_argument('--'+k,required=True)
        a=p.parse_args();require(os.geteuid()==0 and sys.flags.isolated and sys.dont_write_bytecode)
        paths=[a.manifest_root/'stopped-manifest.json',a.creation_root/'creation-journal.json']
        raw=[private(x) for x in paths];query=Query(a.docker_path,a.docker_hash,a.public_scratch_root,a.docker_host)
        result=collect(raw,[a.manifest_hash,a.creation_hash],a.installation,query);require(raw==[private(x) for x in paths])
        result['dockerBinarySha256']=a.docker_hash
        print('SEMANTIC_CREATION_CONFIGURATION='+encoded(result).decode())
        print('SEMANTIC_CREATION_CONFIGURATION=PASS ACCEPTANCE_GRANTED=false START_AUTHORIZED=false');return 0
    except Exception:
        print('SEMANTIC_CREATION_CONFIGURATION=BLOCKED REASON=CREATION_CONFIGURATION_UNPROVEN NO_SECRETS_PRINTED=true');return 1


def role_secret(path,uid,gid):
    require(path.is_absolute() and '..' not in path.parts)
    for p in path.parents:
        s=p.lstat();require(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and not s.st_mode&0o022)
    s=path.parent.lstat();require(s.st_gid==0 and stat.S_IMODE(s.st_mode)==0o700)
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        before=os.fstat(fd);require(stat.S_ISREG(before.st_mode) and before.st_uid==uid and before.st_gid==gid
            and before.st_nlink==1 and stat.S_IMODE(before.st_mode)==0o600 and 16<=before.st_size<=1024)
        raw=os.read(fd,1025);require(len(raw)==before.st_size and attrs(before)==attrs(os.fstat(fd))==attrs(path.lstat()))
        require(re.fullmatch(rb'[!-~]{16,1024}',raw));return raw
    finally:os.close(fd)
def pairing(raws,launch_pin,uid,gid):
    require(sha(raws['launch'])==launch_pin)
    launch,binding,trust,credential=(decode(raws[k]) for k in ('launch','binding','trust','credential'))
    require(launch['schema']=='ouf.semantic-provider-launch-inputs.v1' and launch['notReleaseAcceptance'] is True
        and launch['containersCreated']==0 and launch['mountsInstalled'] is False and launch['providerCalls']==0
        and launch['bindingHash']==sha(raws['binding']) and launch['trustReceiptHash']==sha(raws['trust'])
        and launch['credentialReceiptHash']==sha(raws['credential']) and launch['environmentHash']==sha(raws['env']))
    intent=credential['intent'];routes=binding['routes']
    require(intent['schema']=='ouf.semantic-southbound-validator-credential.v1' and intent['purpose']=='OIDC_BEARER_TOKEN_VALIDATOR_ONLY'
        and intent['uid']==uid and intent['gid']==gid and uid>0 and gid>0
        and intent['trustReceiptHash']==sha(raws['trust']) and intent['tlsReceiptHash']==launch['tlsReceiptHash']
        and intent['clientProfile']['clientId']==routes['audience'] and intent['providerCalls']==0
        and all(intent[k] is False for k in ('clientCredentialsGrantRequested','iamConfigurationChanged','secretRotated'))
        and intent['notReleaseAcceptance'] is True and credential['credentialHash']==sha(raws['secret']))
    match=re.fullmatch(r'\$ENV://([A-Z][A-Z0-9_]{0,127})',routes['oidcSecretRef']);require(match)
    names=[match[1],routes['receiptKeyEnvironment']]
    require(names==launch['environmentNames'] and len(set(names))==2
        and all(re.fullmatch('[A-Z][A-Z0-9_]{0,127}',n) and n not in ('PATH','HOME','LD_PRELOAD','PYTHONPATH') for n in names))
    raw=raws['env'];require(type(raw) is bytes and 0<len(raw)<=4096 and raw.endswith(b'\n') and raw.count(b'\n')==2)
    lines=raw[:-1].decode('ascii').split('\n');values=[]
    for name,line in zip(names,lines):
        require(line.startswith(name+'='));values.append(line[len(name)+1:])
    oidc,mac=values;require(re.fullmatch('[!-~]{16,1024}',oidc) and re.fullmatch('[0-9a-f]{64}',mac))
    require(hmac.compare_digest(oidc.encode(),raws['secret']) and sha(mac.encode())==trust['artifactHashes']['southbound/provider-receipt.key'])
    require(trust['artifactHashes']['adapter/provider-receipt.key']==trust['artifactHashes']['southbound/provider-receipt.key'])
    return dict(zip(names,values))
def verify(raws,pins,installation,uid,gid,query,expected):
    extras=pairing(raws,pins['launch'],uid,gid);seen={}
    def capture(kind,identifier):
        value=query(kind,identifier);seen[kind,identifier]=value;return value
    result=collect([raws['manifest'],raws['creation']],[pins['manifest'],pins['creation']],installation,capture)
    rows=result['candidates'];require(len(expected)==2 and set(expected)=={'adapter','southbound'})
    for row in rows:
        require(all(row[k]==expected[row['role']][k] for k in ('configHash','hostConfigHash','environmentHash','fullInspectHash','imageInspectHash')))
    manifest,journal=decode(raws['manifest']),decode(raws['creation'])
    for spec in manifest['containers']:
        actual=environment(seen['container',journal['candidateIds'][spec['name']]]['Config'])
        base=environment(seen['image',spec['image']]['Config'])
        require(not set(extras)&set(base))
        if spec['readOnlyRoot']:
            require(spec['envFile'] is None and hmac.compare_digest(encoded(actual),encoded(base)))
        else:
            require(type(spec['envFile']) is str and spec['envFile']==pins['envPath'])
            require(hmac.compare_digest(encoded(actual),encoded({**base,**extras})))
    return {'schema':'ouf.semantic-sealed-environment-binding-review.v1','inputHashes':{k:sha(v) for k,v in raws.items()},
        'exactExtraEnvironmentEntryCount':2,'environmentNameBindingsHash':sha(encoded(sorted(extras))),
        'oidcCredentialPairConsistent':True,'purposeMacReceiptBindingConsistent':True,'containerEnvironmentMatchesSealedLaunch':True,
        'creationConfigurationUnchangedSinceSection45':True,'environmentFilesRead':True,'oidcPrivateCredentialFilesRead':1,
        'macSeparatePrivateKeyFilesRead':0,'tlsPrivateKeyFilesRead':0,'deploymentSigningKeysRead':False,'caPrivateKeyRead':False,
        'iamCurrentCredentialValidityProven':False,'providerCalls':0,'iamCalls':0,'signaturesIssued':0,'targetFilesWritten':0,
        'privateMaterialSpooled':False,'containersChanged':False,'fullOciAcceptanceProven':False,'generationObserved':False,
        'mountViewInspected':False,'atomicSnapshotProven':False,'allConfigurationFieldsSemanticallyAccepted':False,
        'acceptanceGranted':False,'runtimeRegistered':False,'startAuthorized':False}
def main():
    try:
        p=argparse.ArgumentParser(description=__doc__)
        for k in ('manifest-root','creation-root','launch-root','credential-root','runtime-root','trust-root','docker-path','public-scratch-root'):
            p.add_argument('--'+k,type=Path,required=True)
        for k in ('manifest-hash','creation-hash','launch-hash','installation','docker-hash','docker-host','expected-section45'):
            p.add_argument('--'+k,required=True)
        for k in ('credential-uid','credential-gid'):p.add_argument('--'+k,type=int,required=True)
        a=p.parse_args();require(os.geteuid()==0 and sys.flags.isolated and sys.dont_write_bytecode)
        paths={'manifest':a.manifest_root/'stopped-manifest.json','creation':a.creation_root/'creation-journal.json',
            'launch':a.launch_root/'launch-input-receipt.json','env':a.launch_root/'southbound.env',
            'credential':a.credential_root/'credential-receipt.json','secret':a.credential_root/'client-secret',
            'binding':a.runtime_root/'binding.json','trust':a.trust_root/'trust-receipt.json'}
        def readall():
            values={k:role_secret(path,a.credential_uid,a.credential_gid) if k=='secret' else private(path) for k,path in paths.items()}
            require(len(values['env'])<=4096);return values
        query=Query(a.docker_path,a.docker_hash,a.public_scratch_root,a.docker_host)
        raw=readall();result=verify(raw,{'manifest':a.manifest_hash,'creation':a.creation_hash,'launch':a.launch_hash,
            'envPath':str(paths['env'])},a.installation,a.credential_uid,a.credential_gid,query,decode(a.expected_section45.encode()))
        require(raw==readall());query.budget.remaining();result['dockerBinarySha256']=a.docker_hash
        print('SEMANTIC_ENVIRONMENT_BINDING='+encoded(result).decode())
        print('SEMANTIC_ENVIRONMENT_BINDING=PASS ACCEPTANCE_GRANTED=false START_AUTHORIZED=false');return 0
    except Exception:
        print('SEMANTIC_ENVIRONMENT_BINDING=BLOCKED REASON=SEALED_ENVIRONMENT_BINDING_UNPROVEN NO_SECRETS_PRINTED=true');return 1

"""Exhaustive Docker creation-field review, never an OCI acceptance issuer.

Schema: Moby 464cd50c3d9e92877d56940ea160de6fca7bea23 (Docker 29.8.1).
Rules intentionally distinguish a declared creation request from the effective
OCI security policy. No daemon default, inherited image metadata or checksum
can confer effective-runtime or supply-chain acceptance.
"""
import hashlib
import json
import re

CONFIG_REQUIRED = frozenset('Hostname Domainname User AttachStdin AttachStdout AttachStderr Tty OpenStdin StdinOnce Env Cmd Image Volumes WorkingDir Entrypoint Labels'.split())
CONFIG_OPTIONAL = frozenset('ExposedPorts Healthcheck ArgsEscaped NetworkDisabled OnBuild StopSignal StopTimeout Shell'.split())
HOST_OPTIONAL = frozenset('Annotations StorageOpt Tmpfs Sysctls Runtime Umask Mounts Init'.split())
HOST_REQUIRED = frozenset('Binds ContainerIDFile LogConfig NetworkMode PortBindings RestartPolicy AutoRemove VolumeDriver VolumesFrom ConsoleSize CapAdd CapDrop CgroupnsMode Dns DnsOptions DnsSearch ExtraHosts GroupAdd IpcMode Cgroup Links OomScoreAdj PidMode Privileged PublishAllPorts ReadonlyRootfs SecurityOpt UTSMode UsernsMode ShmSize Isolation CpuShares Memory NanoCpus CgroupParent BlkioWeight BlkioWeightDevice BlkioDeviceReadBps BlkioDeviceWriteBps BlkioDeviceReadIOps BlkioDeviceWriteIOps CpuPeriod CpuQuota CpuRealtimePeriod CpuRealtimeRuntime CpusetCpus CpusetMems Devices DeviceCgroupRules DeviceRequests MemoryReservation MemorySwap MemorySwappiness OomKillDisable PidsLimit Ulimits CpuCount CpuPercent IOMaximumIOps IOMaximumBandwidth MaskedPaths ReadonlyPaths'.split())

def same(a, b):
    # JSON bool and number equality in Python is not semantic type equality.
    return type(a) is type(b) and (a == b if type(a) not in (dict, list) else
        (set(a) == set(b) and all(same(a[k], b[k]) for k in a) if type(a) is dict else
         len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))))

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def no_request(value, kind):
    return value is None or type(value) is kind and len(value) == 0

def environment_map(rows):
    if type(rows) is not list or len(rows) > 256:
        return None
    result = {}
    for row in rows:
        if type(row) is not str or '=' not in row or len(row) > 16384:
            return None
        key, value = row.split('=', 1)
        if not re.fullmatch('[A-Za-z_][A-Za-z0-9_]*', key) or key in result:
            return None
        result[key] = value
    return result

class Fields:
    def __init__(self, obj, required, optional):
        if type(obj) is not dict:
            raise ValueError('CONFIGURATION_OBJECT_REQUIRED')
        self.obj, self.known = obj, required | optional
        self.results = {k: 'UNCLASSIFIED' for k in sorted(set(obj) & self.known)}
        self.missing = sorted(required - set(obj))
        self.unknown = len(set(obj) - self.known)

    def rule(self, key, ok, status='REQUEST_CONFORMS'):
        if key in self.obj:
            if key in self.results and self.results[key] != 'UNCLASSIFIED':
                raise ValueError('DUPLICATE_FIELD_RULE')
            self.results[key] = status if ok else 'REJECTED'

    def exact(self, key, value):
        self.rule(key, same(self.obj.get(key), value))

    def empty(self, key, kind):
        self.rule(key, no_request(self.obj.get(key), kind))

    def report(self):
        # Only schema-defined names and finite reason codes are public. Unknown
        # field names and ALL values, including paths and labels, stay private.
        statuses = set(self.results.values())
        rejected = bool(self.missing or self.unknown or {'REJECTED', 'UNCLASSIFIED'} & statuses)
        return {'fieldCount': len(self.obj), 'unknownFieldCount': self.unknown,
                'missingRequiredFields': self.missing, 'fields': self.results,
                'declaredRequestConforms': not rejected,
                'effectivePolicyEvidenceRequired': 'EFFECTIVE_POLICY_REQUIRED' in statuses,
                'imageProvenanceEvidenceRequired': 'IMAGE_PROVENANCE_REQUIRED' in statuses,
                'configurationHash': digest(self.obj)}

def mounts_match(actual, intended):
    if type(actual) is not list or type(intended) is not list or len(actual) != len(intended):
        return False
    expected = {(v['source'], v['target']) for v in intended}
    if len(expected) != len(intended) or not all(v['readOnly'] is True for v in intended):
        return False
    seen = set()
    for value in actual:
        if type(value) is not dict or not {'Type', 'Source', 'Target', 'ReadOnly'} <= set(value):
            return False
        if set(value) - {'Type', 'Source', 'Target', 'ReadOnly', 'Consistency', 'BindOptions'}:
            return False
        if value['Type'] != 'bind' or value['ReadOnly'] is not True or value.get('Consistency', '') != '':
            return False
        pair = (value['Source'], value['Target'])
        if pair in seen or pair not in expected:
            return False
        seen.add(pair)
        options = value.get('BindOptions')
        if options is not None:
            if type(options) is not dict or set(options) - {'Propagation', 'NonRecursive', 'CreateMountpoint', 'ReadOnlyNonRecursive', 'ReadOnlyForceRecursive'}:
                return False
            if options.get('Propagation', '') not in ('', 'rprivate'):
                return False
            if any(options.get(k, False) is not False for k in ('NonRecursive', 'CreateMountpoint', 'ReadOnlyNonRecursive', 'ReadOnlyForceRecursive')):
                return False
    return seen == expected

def review_fields(config, host, base, spec, journal, container_id, sealed_environment):
    """Review complete objects using already authenticated in-memory inputs.

    Caller must prove identity, stopped state, byte/source/receipt binding and
    exact sealed_environment pairing. This function cannot authenticate inputs,
    inspect effective mounts/namespaces, sign or authorize a start.
    """
    c = Fields(config, CONFIG_REQUIRED, CONFIG_OPTIONAL)
    h = Fields(host, HOST_REQUIRED, HOST_OPTIONAL)
    for key in ('AttachStdin', 'Tty', 'OpenStdin', 'StdinOnce', 'ArgsEscaped', 'NetworkDisabled'):
        c.exact(key, False)
    # docker create CLI, without -a or -i, requests stdout/stderr attachment.
    # This is not OpenStdin/interactive execution or permission to start.
    c.exact('AttachStdout', True); c.exact('AttachStderr', True)
    c.exact('Hostname', container_id[:12]); c.exact('Domainname', '')
    c.exact('User', spec['user']); c.exact('Image', spec['image'])
    actual_env, expected_env = environment_map(config.get('Env')), environment_map(sealed_environment)
    c.rule('Env', actual_env is not None and expected_env is not None and same(actual_env, expected_env))
    c.exact('Cmd', spec['command'] or base.get('Cmd'))
    c.exact('Entrypoint', base.get('Entrypoint'))
    c.exact('WorkingDir', base.get('WorkingDir', ''))
    c.empty('Volumes', dict)
    labels = {**(base.get('Labels') or {}), 'ouf.semantic.candidate.transaction': journal['transaction'],
              'ouf.semantic.candidate.manifest': journal['manifestHash']}
    c.exact('Labels', labels)
    health = config.get('Healthcheck')
    c.rule('Healthcheck', type(health) is dict and health.get('Test') == ['NONE']
           and not set(health) - {'Test', 'Interval', 'Timeout', 'StartPeriod', 'StartInterval', 'Retries'}
           and all(type(v) is int and v == 0 for k, v in health.items() if k != 'Test'))
    if 'Healthcheck' not in config:
        c.missing.append('Healthcheck')
    # Image metadata can be inherited without being trusted publisher evidence.
    for key in ('ExposedPorts', 'OnBuild', 'StopSignal', 'Shell'):
        c.rule(key, same(config.get(key), base.get(key)), 'IMAGE_PROVENANCE_REQUIRED')
    c.exact('StopTimeout', None)
    for key in ('AutoRemove', 'Privileged', 'PublishAllPorts'):
        h.exact(key, False)
    h.exact('ReadonlyRootfs', spec['readOnlyRoot'])
    h.exact('RestartPolicy', {'Name': 'no', 'MaximumRetryCount': 0})
    h.exact('CapDrop', ['ALL'])
    h.exact('Memory', spec['memoryBytes']); h.exact('MemorySwap', spec['memoryBytes'])
    h.exact('PidsLimit', spec['pidsLimit']); h.exact('Dns', spec['dnsServers'])
    for key in ('Binds', 'VolumesFrom', 'CapAdd', 'DnsOptions', 'DnsSearch', 'ExtraHosts', 'GroupAdd', 'Links',
                'BlkioWeightDevice', 'BlkioDeviceReadBps', 'BlkioDeviceWriteBps', 'BlkioDeviceReadIOps',
                'BlkioDeviceWriteIOps', 'Devices', 'DeviceCgroupRules', 'DeviceRequests'):
        h.empty(key, list)
    for key in ('PortBindings', 'Annotations', 'StorageOpt', 'Tmpfs', 'Sysctls'):
        h.empty(key, dict)
    for key in ('ContainerIDFile', 'VolumeDriver', 'Cgroup', 'PidMode', 'UTSMode', 'Isolation', 'CgroupParent', 'CpusetCpus', 'CpusetMems'):
        h.exact(key, '')
    for key in ('OomScoreAdj', 'CpuShares', 'NanoCpus', 'BlkioWeight', 'CpuPeriod', 'CpuQuota', 'CpuRealtimePeriod',
                'CpuRealtimeRuntime', 'MemoryReservation', 'CpuCount', 'CpuPercent', 'IOMaximumIOps', 'IOMaximumBandwidth'):
        h.exact(key, 0)
    h.exact('ConsoleSize', [0, 0]); h.exact('MemorySwappiness', None)
    h.rule('OomKillDisable', host.get('OomKillDisable') is None or host.get('OomKillDisable') is False)
    networks = spec.get('networks')
    h.rule('NetworkMode', type(networks) is list and bool(networks)
           and host.get('NetworkMode') in (networks[0]['id'], networks[0]['name']))
    h.rule('Mounts', mounts_match(host.get('Mounts'), spec['mounts']))
    if spec['mounts'] and 'Mounts' not in host:
        h.missing.append('Mounts')
    # These defaults depend on daemon/host and the generated OCI process,
    # namespaces, seccomp/LSM, mounts and cgroup resources. They never become
    # accepted solely because they were not overridden in docker create.
    h.rule('CgroupnsMode', host.get('CgroupnsMode') == 'private', 'EFFECTIVE_POLICY_REQUIRED')
    h.rule('IpcMode', host.get('IpcMode') == 'private', 'EFFECTIVE_POLICY_REQUIRED')
    h.rule('UsernsMode', host.get('UsernsMode') == '', 'EFFECTIVE_POLICY_REQUIRED')
    h.rule('Runtime', type(host.get('Runtime')) is str and bool(host.get('Runtime')), 'EFFECTIVE_POLICY_REQUIRED')
    h.rule('SecurityOpt', no_request(host.get('SecurityOpt'), list), 'EFFECTIVE_POLICY_REQUIRED')
    h.rule('ShmSize', type(host.get('ShmSize')) is int and host['ShmSize'] == 64 * 1024 * 1024, 'EFFECTIVE_POLICY_REQUIRED')
    h.rule('Init', host.get('Init') is None or host.get('Init') is False, 'EFFECTIVE_POLICY_REQUIRED')
    h.rule('Umask', host.get('Umask') is None, 'EFFECTIVE_POLICY_REQUIRED')
    h.rule('Ulimits', no_request(host.get('Ulimits'), list), 'EFFECTIVE_POLICY_REQUIRED')
    for key in ('MaskedPaths', 'ReadonlyPaths'):
        value = host.get(key)
        h.rule(key, type(value) is list and bool(value) and all(type(v) is str for v in value)
               and len(set(value)) == len(value), 'EFFECTIVE_POLICY_REQUIRED')
    log = host.get('LogConfig')
    h.rule('LogConfig', type(log) is dict and set(log) == {'Type', 'Config'}
           and log['Type'] in ('json-file', 'local') and no_request(log['Config'], dict), 'EFFECTIVE_POLICY_REQUIRED')
    cr, hr = c.report(), h.report()
    return {'schema': 'ouf.semantic-creation-field-review.v1', 'config': cr, 'hostConfig': hr,
            'declaredRequestConforms': cr['declaredRequestConforms'] and hr['declaredRequestConforms'],
            'allConfigurationFieldsSemanticallyAccepted': False, 'fullOciAcceptanceProven': False,
            'acceptanceGranted': False, 'signaturesIssued': 0, 'startAuthorized': False}

import argparse
import os
from pathlib import Path
import sys

def verify_all(raws,pins,installation,uid,gid,query,expected45,expected46):
    require(type(expected46) is dict and set(expected46)==set(raws)
            and {k:sha(v) for k,v in raws.items()}==expected46)
    seen={}
    def capture(kind,identifier):
        value=query(kind,identifier);seen[kind,identifier]=value;return value
    binding=verify(raws,pins,installation,uid,gid,capture,expected45)
    extras=pairing(raws,pins['launch'],uid,gid)
    manifest,journal=decode(raws['manifest']),decode(raws['creation'])
    rows=[]
    for spec in manifest['containers']:
        cid=journal['candidateIds'][spec['name']]
        current,image=seen['container',cid],seen['image',spec['image']]
        require(image['Os']=='linux' and image['Architecture']=='amd64')
        base=image['Config'];sealed=list(base.get('Env') or [])
        if not spec['readOnlyRoot']:
            sealed.extend(k+'='+v for k,v in extras.items())
        row=review_fields(current['Config'],current['HostConfig'],base,spec,journal,cid,sealed)
        row['role']='adapter' if spec['readOnlyRoot'] else 'southbound'
        rows.append(row)
    return {'schema':'ouf.semantic-complete-creation-fields-readback.v1',
        'inputHashes':binding['inputHashes'],'candidates':sorted(rows,key=lambda r:r['role']),
        'creationConfigurationUnchangedSinceSection45':True,'environmentBindingsUnchangedSinceSection46':True,
        'declaredRequestConforms':all(r['declaredRequestConforms'] for r in rows),
        'allConfigurationFieldsSemanticallyAccepted':False,'effectiveOciPolicyReviewed':False,
        'imagePublisherProvenanceVerified':False,'fullOciAcceptanceProven':False,'mountViewInspected':False,
        'generationObserved':False,'atomicSnapshotProven':False,'privateMaterialSpooled':False,
        'oidcPrivateCredentialFilesRead':1,'tlsPrivateKeyFilesRead':0,'deploymentSigningKeysRead':False,
        'caPrivateKeyRead':False,'providerCalls':0,'iamCalls':0,'targetFilesWritten':0,'signaturesIssued':0,
        'containersChanged':False,'runtimeRegistered':False,'acceptanceGranted':False,'startAuthorized':False}

def main():
    try:
        p=argparse.ArgumentParser(description=__doc__)
        for k in ('manifest-root','creation-root','launch-root','credential-root','runtime-root','trust-root','docker-path','public-scratch-root'):
            p.add_argument('--'+k,type=Path,required=True)
        for k in ('manifest-hash','creation-hash','launch-hash','installation','docker-hash','docker-host','expected-section45','expected-section46'):
            p.add_argument('--'+k,required=True)
        for k in ('credential-uid','credential-gid'):p.add_argument('--'+k,type=int,required=True)
        a=p.parse_args();require(os.geteuid()==0 and sys.flags.isolated and sys.dont_write_bytecode)
        paths={'manifest':a.manifest_root/'stopped-manifest.json','creation':a.creation_root/'creation-journal.json',
            'launch':a.launch_root/'launch-input-receipt.json','env':a.launch_root/'southbound.env',
            'credential':a.credential_root/'credential-receipt.json','secret':a.credential_root/'client-secret',
            'binding':a.runtime_root/'binding.json','trust':a.trust_root/'trust-receipt.json'}
        def readall():
            values={k:role_secret(path,a.credential_uid,a.credential_gid) if k=='secret' else private(path) for k,path in paths.items()}
            require(len(values['env'])<=4096);return values
        query=Query(a.docker_path,a.docker_hash,a.public_scratch_root,a.docker_host)
        raw=readall();result=verify_all(raw,{'manifest':a.manifest_hash,'creation':a.creation_hash,'launch':a.launch_hash,
            'envPath':str(paths['env'])},a.installation,a.credential_uid,a.credential_gid,query,
            decode(a.expected_section45.encode()),decode(a.expected_section46.encode()))
        require(raw==readall());query.budget.remaining();result['dockerBinarySha256']=a.docker_hash
        print('SEMANTIC_CREATION_FIELDS='+encoded(result).decode())
        if not result['declaredRequestConforms']:
            print('SEMANTIC_CREATION_FIELDS=BLOCKED REASON=CREATION_FIELDS_REJECTED NO_SECRETS_PRINTED=true');return 1
        print('SEMANTIC_CREATION_FIELDS=PASS ACCEPTANCE_GRANTED=false START_AUTHORIZED=false');return 0
    except Exception:
        print('SEMANTIC_CREATION_FIELDS=BLOCKED REASON=CREATION_FIELD_BINDING_UNPROVEN NO_SECRETS_PRINTED=true');return 1
if __name__=='__main__':raise SystemExit(main())
OUF_PYTHON
