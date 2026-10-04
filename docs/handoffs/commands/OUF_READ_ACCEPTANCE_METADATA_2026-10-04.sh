#!/usr/bin/env bash
# Section 39: NOT EXECUTED. Historical metadata readback only; no replay of 34/36/38.
# One complete wrapper. No target installation, helper download, package or rollback mutation.
set -euo pipefail
exec sudo /usr/bin/python3 -I -B - \
  --manifest-root /etc/ouf/deploy-snapshots/semantic-provider-candidate-manifest-20261003-130410/prepared \
  --creation-root /etc/ouf/deploy-snapshots/semantic-provider-stopped-create-20261003-135106/prepared \
  --dossier-root /etc/ouf/deploy-snapshots/semantic-target-acceptance-inventory-20261004-151023/prepared \
  --tls-root /etc/ouf/deploy-snapshots/semantic-provider-tls-runtime-20261002-230418 \
  --trust-root /etc/ouf/deploy-snapshots/semantic-provider-trust-20261002-212033 \
  --manifest-hash 052b46a56ea666971f135c75af48b3342dbeb68e2f17f1f16263a99351df88bd \
  --creation-hash a1c2acd9924fc0f924ded7c2d59f128ef2d8b8dd11c62484a901f628022aaae7 \
  --dossier-hash a37f22635035ab8543a4654def5cd6a6f4fe45fd1affc0ff10ccc3c19f03085c \
  --installation ouf-lab-netcup-01 <<'OUF_PYTHON'
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
if __name__ == '__main__':
    import sys
    raise SystemExit(main())
OUF_PYTHON
