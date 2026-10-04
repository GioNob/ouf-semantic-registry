#!/usr/bin/env bash
# PREPARED ONLY — §41 PRIVATE IMAGE LINEAGE READ SCOPE NOT GRANTED.
# Four evidence files plus six frozen source files; no secrets/config/Env/Docker reads.
# Historical bindings only; no image-byte verification, acceptance, writes, signing or start.
set -euo pipefail
exec sudo /usr/bin/python3 -I -B - '--manifest-root' '/etc/ouf/deploy-snapshots/semantic-provider-candidate-manifest-20261003-130410/prepared' '--trust-root' '/etc/ouf/deploy-snapshots/semantic-provider-trust-20261002-212033' '--image-stage-root' '/etc/ouf/deploy-snapshots/semantic-provider-adapter-20261002-173408' '--manifest-hash' '052b46a56ea666971f135c75af48b3342dbeb68e2f17f1f16263a99351df88bd' '--trust-hash' '8a108a3c4b47f86ef58589c7322572db88991672f4c328a200711a9fd5576776' '--installation' 'ouf-lab-netcup-01' '--adapter-image' 'sha256:a697bf75bf7d51afadadfaccd3d80537e9a5fb2a08f0d194c6dfd9462e812468' '--southbound-image' 'sha256:84e6b5e787e9f889ebff88161cb9a16599bafcffa236c6b54c7f779a0655940d' '--source-commit' '52c0dcf11654a4d3d0f17a6902ed095975466fb9' '--source-url-base' 'https://raw.githubusercontent.com/GioNob/ouf-api-gateway' '--base-image' 'python@sha256:bb2988715db2cf7ace7b53f38f3cffbef7c7046a656bee66245eb0ed386e2e81' '--runtime-user' '10006:10006' '--gateway-version' '3.18.0' '--payload-hashes' '{"Dockerfile.semantic-provider":"b2cc4828a2cc9424c2a3b31793d9094dbade41d8d7485ca43b32d2dcd80873e7","tools/semantic_provider_adapter.py":"718f031cd4116d233c3075ee74da2f28170b5ed4efcac1a77deef154f7fd320c","tools/semantic_provider_admission.py":"dca670d1f0ced678db6af9810199da07419901a21523385e0ebea623b608bbfc","tools/semantic_provider_boundary.py":"cae2b1d5970349ce1ebc95fb44ca4dd1bd67d93e43900ad4cbeabb3d5fbd6e69","tools/semantic_provider_relay.py":"04b33da9b3d599872c19ea20d3775141ef99c5989c7fb7175be6926b74cc7f6f","tools/southbound_security.py":"5953e6143fb7141b62a2d5cc26d8cf85ee74147d9eefaa923460f8e1706eb0ec"}' <<'OUF_PYTHON'
"""Read frozen build evidence and context; grants no image acceptance."""
import argparse
import json
import os
from pathlib import Path
import re
import sys

"""Verify sealed receipt/configuration consistency privately; grants no acceptance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

LIMIT = 131072
NAMES = ('manifest','launch','tls','trust','stage','binding','plan','adapter.json','config.yaml','apisix.yaml')
class Blocked(ValueError): pass
def require(ok):
    if not ok: raise Blocked('CONFIGURATION_PROVENANCE_UNPROVEN')
def sha(raw): return hashlib.sha256(raw).hexdigest()
def decode(raw, end=False):
    require(type(raw) is bytes and 0 < len(raw) <= LIMIT)
    if end:
        require(raw.endswith(b'\n#END\n')); raw=raw[:-6]
    def unique(items):
        out={}
        for key,value in items:
            require(key not in out);out[key]=value
        return out
    value=json.loads(raw,object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(Blocked()))
    require(type(value) is dict);return value
def attrs(s):
    return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
def read(path,uid=0,gid=0):
    require(path.is_absolute() and '..' not in path.parts)
    for parent in path.parents:
        s=parent.lstat()
        require(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and not s.st_mode & 0o022)
    s=path.parent.lstat();require(s.st_gid==0 and stat.S_IMODE(s.st_mode)==0o700)
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        s=os.fstat(fd)
        require(stat.S_ISREG(s.st_mode) and s.st_uid==uid and s.st_gid==gid
            and stat.S_IMODE(s.st_mode)==0o600 and s.st_nlink==1 and 0<s.st_size<=LIMIT)
        raw=os.read(fd,LIMIT+1)
        require(len(raw)==s.st_size and attrs(s)==attrs(os.fstat(fd))==attrs(path.lstat()))
        return raw,attrs(s)
    finally: os.close(fd)
def project(raws,manifest_hash,installation):
    require(set(raws)==set(NAMES) and sha(raws['manifest'])==manifest_hash)
    v={k:decode(raw,end=k=='apisix.yaml') for k,raw in raws.items()}
    m,l,t,tr,s,b,p=(v[k] for k in NAMES[:7])
    require(m['schema']=='ouf.semantic-provider-stopped-manifest.v1'
        and m['installation']==installation and m['startAuthorized'] is False)
    require(l['schema']=='ouf.semantic-provider-launch-inputs.v1' and m['launchReceiptHash']==sha(raws['launch']))
    for key,name in (('tlsReceiptHash','tls'),('trustReceiptHash','trust'),('bindingHash','binding')):
        require(l[key]==sha(raws[name]))
    require(t['intent']['trustReceiptHash']==sha(raws['trust']) and t['intent']['stageReceiptHash']==sha(raws['stage'])
        and s['bindingHash']==sha(raws['binding']) and s['planHash']==sha(raws['plan']))
    for receipt in (l,t,tr,s): require(receipt['notReleaseAcceptance'] is True)
    require(l['mountsInstalled'] is False and t['mountsInstalled'] is False and tr['mountsInstalled'] is False
        and s['runtimeFilesMounted'] is False and tr['verified'] is True)
    for receipt in (l,t): require(type(receipt['containersCreated']) is int and receipt['containersCreated']==0
        and type(receipt['providerCalls']) is int and receipt['providerCalls']==0)
    require(p['schema']=='ouf.semantic-provider-runtime-plan.v1' and p['installed'] is False
        and p['notReleaseAcceptance'] is True and p['providerCalls']==0)
    intent=tr['intent']
    require(t['intent']['gateway']==intent['gateway'] and t['intent']['adapterImage']==intent['adapterImage']
        and t['intent']['adapterUid']==intent['adapterUid'] and t['intent']['adapterGid']==intent['adapterGid']
        and b['adapter']['admission']['installation']==intent['installation']==installation
        and b['tlsIdentities']['adapterHostname']==intent['adapterHostname']
        and b['tlsIdentities']['southboundHostname']==intent['southboundHostname'])
    require(v['adapter.json']==b['adapter']==p['adapterConfiguration'])
    for name in NAMES[7:]:
        require(t['outputHashes'][name]==sha(raws[name]))
    for name in ('config.yaml','apisix.yaml'):
        require(l['privateArtifactHashes'][name]==sha(raws[name]))
    # Compare routes to the sealed plan. This is NOT independent recompilation.
    require(v['apisix.yaml']['routes']==p['southboundRoutes']['routes'])
    return {'schema':'ouf.semantic-configuration-provenance-readback.v1',
        'receiptChainConsistent':True,'sealedConfigurationBytesConsistent':True,
        'adapterBindingConsistent':True,'routesMatchSealedPlan':True,
        'inputHashes':{k:sha(raws[k]) for k in NAMES},'configurationFilesRead':3,
        'inlineTlsPrivateKeyFileRead':True,'separatePrivateKeyFilesRead':0,
        'independentCompilerReplay':False,'cryptographicKeyValidation':False,
        'imagePublisherProvenanceVerified':False,'currentTargetInspected':False,
        'atomicSnapshotProven':False,'acceptanceGranted':False,'environmentRead':False,
        'signaturesIssued':0,'providerCalls':0,'targetFilesWritten':0,
        'runtimeRegistered':False,'startAuthorized':False}
def verify(paths,owners,manifest_hash,installation,reader=read):
    require(set(paths)==set(NAMES) and set(owners)==set(NAMES))
    first={k:reader(paths[k],*owners[k]) for k in NAMES}
    result=project({k:first[k][0] for k in NAMES},manifest_hash,installation)
    intent=decode(first['trust'][0])['intent']
    require(owners['adapter.json']==(intent['adapterUid'],intent['adapterGid'])
        and owners['config.yaml']==owners['apisix.yaml']==(intent['gateway']['uid'],intent['gateway']['gid']))
    require(first=={k:reader(paths[k],*owners[k]) for k in NAMES})
    return result

def main():
    try:
        parser=argparse.ArgumentParser(description=__doc__)
        for name in ('manifest','launch','tls','trust','stage'):
            parser.add_argument('--'+name+'-root',type=Path,required=True)
        parser.add_argument('--manifest-hash',required=True)
        parser.add_argument('--installation',required=True)
        for name in ('adapter-uid','adapter-gid','gateway-uid','gateway-gid'):
            parser.add_argument('--'+name,type=int,required=True)
        a=parser.parse_args();require(os.geteuid()==0 and sys.flags.isolated and sys.dont_write_bytecode)
        paths={'manifest':a.manifest_root/'stopped-manifest.json','launch':a.launch_root/'launch-input-receipt.json',
            'tls':a.tls_root/'tls-runtime-receipt.json','trust':a.trust_root/'trust-receipt.json',
            'stage':a.stage_root/'stage-receipt.json','binding':a.stage_root/'binding.json','plan':a.stage_root/'runtime-plan.json'}
        paths.update({k:a.tls_root/k for k in NAMES[7:]})
        require(all(0<=v<=2147483647 for v in (a.adapter_uid,a.adapter_gid,a.gateway_uid,a.gateway_gid)))
        owners={k:(0,0) for k in NAMES};owners.update({'adapter.json':(a.adapter_uid,a.adapter_gid),
            'config.yaml':(a.gateway_uid,a.gateway_gid),'apisix.yaml':(a.gateway_uid,a.gateway_gid)})
        result=verify(paths,owners,a.manifest_hash,a.installation)
        print('SEMANTIC_CONFIGURATION_PROVENANCE='+json.dumps(result,sort_keys=True,allow_nan=False))
        print('SEMANTIC_CONFIGURATION_PROVENANCE=PASS ACCEPTANCE_GRANTED=false START_AUTHORIZED=false')
        return 0
    except Exception:
        print('SEMANTIC_CONFIGURATION_PROVENANCE=BLOCKED REASON=CONFIGURATION_PROVENANCE_UNPROVEN NO_SECRETS_PRINTED=true')
        return 1


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def project(raws, pins, expected):
    payload = expected['payloadHashes']
    require(set(raws) == {'manifest', 'trust', 'image-stage', 'build-intent'} | set(payload))
    require(set(pins) == {'manifest', 'trust'})
    require(all(re.fullmatch('[0-9a-f]{64}', h) and sha(raws[k]) == h for k, h in pins.items()))
    m, t, s, intent = (decode(raws[k]) for k in ('manifest', 'trust', 'image-stage', 'build-intent'))
    require(m['schema'] == 'ouf.semantic-provider-stopped-manifest.v1'
            and m['installation'] == expected['installation'] and m['startAuthorized'] is False)
    require(t['verified'] is True and t['notReleaseAcceptance'] is True)
    require(s['intent'] == intent and intent['schema'] == 'ouf.semantic-provider-image-stage.v1')
    for key in ('sourceCommit', 'sourceURLBase', 'baseImage', 'runtimeUser', 'payloadHashes'):
        require(intent[key] == expected[key])
    require(intent['payloadHash'] == sha(encoded(payload)))
    require(all(sha(raws[k]) == h for k, h in payload.items()))
    require(re.fullmatch('sha256:[0-9a-f]{64}', s['baseImageId']))
    require(s['imageId'] == expected['adapterImage'])
    for key in ('noRuntimeContainersCreated', 'noRouteWrites', 'noIAMWrites',
                'noPolicyPublication', 'notReleaseAcceptance'):
        require(s[key] is True)
    require(type(s['providerCalls']) is int and s['providerCalls'] == 0)
    adapter = t['intent']['adapterImage']; gateway = t['intent']['gateway']
    require(adapter['id'] == s['imageId'] and adapter['sourceCommit'] == intent['sourceCommit']
            and adapter['runtimeUser'] == intent['runtimeUser'] and adapter['payloadHash'] == intent['payloadHash'])
    require(t['intent']['installation'] == expected['installation'])
    require(gateway['id'] == intent['gateway']['id']
            and gateway['image'] == intent['gateway']['image'] == expected['southboundImage']
            and intent['gateway']['version'] == expected['gatewayVersion'])
    require(re.fullmatch('[0-9a-f]{64}', intent['gateway']['configurationHash']))
    candidates = m['containers']
    require(type(candidates) is list and len(candidates) == 2)
    require(sorted(c['image'] for c in candidates) == sorted([s['imageId'], gateway['image']]))
    require(sum(c['image'] == s['imageId'] and c['readOnlyRoot'] is True for c in candidates) == 1
            and sum(c['image'] == gateway['image'] and c['readOnlyRoot'] is False for c in candidates) == 1)
    return {'schema': 'ouf.semantic-image-lineage-readback.v1',
            'inputHashes': {k: sha(raws[k]) for k in sorted(raws)},
            'buildContextFileCount': len(payload), 'buildContextMatchesPinnedSource': True,
            'adapterReceiptBindingsConsistent': True, 'southboundSelectionConsistent': True,
            'historicalEvidenceOnly': True, 'currentTargetInspected': False,
            'imageBytesVerified': False, 'imagePublisherProvenanceVerified': False,
            'dependencySbomVerified': False, 'buildReproduced': False,
            'rootfsSealProven': False, 'generationObserved': False, 'atomicSnapshotProven': False,
            'acceptanceGranted': False, 'startAuthorized': False, 'runtimeRegistered': False,
            'configurationFilesRead': 0, 'privateKeyFilesRead': 0, 'environmentRead': False,
            'providerCalls': 0, 'signaturesIssued': 0, 'targetFilesWritten': 0}


def verify(paths, pins, expected, reader=read):
    require(set(paths) == {'manifest', 'trust', 'image-stage', 'build-intent'} | set(expected['payloadHashes']))
    first = {k: reader(p) for k, p in paths.items()}
    result = project({k: first[k][0] for k in paths}, pins, expected)
    require(first == {k: reader(p) for k, p in paths.items()})
    return result


def main():
    try:
        parser = argparse.ArgumentParser(description=__doc__)
        for name in ('manifest-root', 'trust-root', 'image-stage-root'):
            parser.add_argument('--' + name, type=Path, required=True)
        for name in ('manifest-hash', 'trust-hash', 'installation', 'adapter-image',
                     'southbound-image', 'source-commit', 'source-url-base', 'base-image',
                     'runtime-user', 'gateway-version', 'payload-hashes'):
            parser.add_argument('--' + name, required=True)
        a = parser.parse_args()
        require(os.geteuid() == 0 and sys.flags.isolated and sys.dont_write_bytecode)
        payload = decode(a.payload_hashes.encode())
        require(1 <= len(payload) <= 32 and all(type(k) is str and type(v) is str
                and re.fullmatch('[0-9a-f]{64}', v) and not Path(k).is_absolute()
                and '..' not in Path(k).parts and len(k) <= 256 for k, v in payload.items()))
        paths = {'manifest': a.manifest_root / 'stopped-manifest.json',
                 'trust': a.trust_root / 'trust-receipt.json',
                 'image-stage': a.image_stage_root / 'stage-receipt.json',
                 'build-intent': a.image_stage_root / 'build-intent.json'}
        paths.update({k: a.image_stage_root / 'context' / k for k in payload})
        require(len(set(paths.values())) == len(paths))
        expected = dict(installation=a.installation, adapterImage=a.adapter_image,
                        southboundImage=a.southbound_image, sourceCommit=a.source_commit,
                        sourceURLBase=a.source_url_base, baseImage=a.base_image,
                        runtimeUser=a.runtime_user, gatewayVersion=a.gateway_version, payloadHashes=payload)
        result = verify(paths, {'manifest': a.manifest_hash, 'trust': a.trust_hash}, expected)
        print('SEMANTIC_IMAGE_LINEAGE=' + encoded(result).decode())
        print('SEMANTIC_IMAGE_LINEAGE=PASS HISTORICAL_ONLY=true ACCEPTANCE_GRANTED=false START_AUTHORIZED=false')
        return 0
    except Exception:
        print('SEMANTIC_IMAGE_LINEAGE=BLOCKED REASON=IMAGE_LINEAGE_UNPROVEN NO_SECRETS_PRINTED=true')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
OUF_PYTHON

