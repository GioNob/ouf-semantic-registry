"""Plan-only dossier from signed original image config bytes; no Docker or secrets."""
import argparse
import gzip
import hashlib
import json
import tarfile
import zipfile
from pathlib import Path

ORIGINAL='2cdd7a73c1fc2a710f1e6604eb6cab2988492e4c45b5252defffa9832b91d9d0'

def require(value):
    if not value:raise ValueError('ISOLATED_V2_DOSSIER_UNPROVEN')

def config_from_archive(incoming, image_id):
    expected=image_id.removeprefix('sha256:');found=[];manifests=[]
    paths={expected+'.json','blobs/sha256/'+expected}
    with gzip.GzipFile(fileobj=incoming) as plain,tarfile.open(fileobj=plain,mode='r|') as archive:
        for member in archive:
            path=member.name.removeprefix('./')
            if path=='manifest.json':
                require(member.isfile() and 0<member.size<=131072)
                manifests.append(json.loads(archive.extractfile(member).read()))
            if path not in paths:continue
            require(member.isfile() and 0<member.size<=131072)
            raw=archive.extractfile(member).read()
            require(hashlib.sha256(raw).hexdigest()==expected)
            found.append(json.loads(raw))
    require(len(found)==1)
    require(len(manifests)==1 and len(manifests[0])==1 and manifests[0][0]['Config'].removeprefix('./') in paths)
    return found[0]

def role_plan(role, image_id, config):
    require(config['os']=='linux' and config['architecture']=='amd64')
    packaged=config['config']
    require(isinstance(packaged,dict))
    env=packaged.get('Env') or []
    require(all(isinstance(v,str) and '=' in v for v in env))
    startup={k:packaged.get(k) for k in ('Entrypoint','Cmd','WorkingDir','User')}
    return dict(role=role,localImageId=image_id,configSha256=image_id[7:],
        operatingSystem='linux',architecture='amd64',packagedStartup=startup,
        startupFingerprint=hashlib.sha256(json.dumps(startup,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        packagedEnvironmentNames=sorted({v.split('=',1)[0] for v in env}),
        packagedExposedPorts=sorted((packaged.get('ExposedPorts') or {}).keys()),
        hostPublishedPorts=[],pullOrTagFallbackAllowed=False,plannedState='CREATED_STOPPED',
        needsExplicitRuntimeUidGid=True,needsFreshPrivateMountAndNetworkReceipts=True,
        restartPolicy='no',privileged=False,capDrop=['ALL'],startAuthorized=False)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--inventory-directory',type=Path,required=True);args=parser.parse_args()
    with args.bundle.open('rb') as stream:require(hashlib.file_digest(stream,'sha256').hexdigest()==ORIGINAL)
    root=args.inventory_directory;inventory=json.loads((root/'inventory.json').read_bytes())
    require(inventory['sourceArtifactSha256']==ORIGINAL)
    roles=[]
    with zipfile.ZipFile(args.bundle) as archive:
        receipt=json.loads(archive.read('receipt.json'))
        for role in ('adapter','southbound'):
            image=next(r for r in receipt['candidateArchives'] if r['role']==role)
            current=next(r for r in inventory['images'] if r['role']==role)
            require(current['imageId']==image['imageId'] and current['imageArchiveSha256']==image['sha256'])
            with archive.open(role+'.image.tar.gz') as incoming:config=config_from_archive(incoming,image['imageId'])
            roles.append(role_plan(role,image['imageId'],config))
    dossier=dict(schema='ouf.semantic-v2-isolated-dossier.v1',sourceArtifactSha256=ORIGINAL,
        roles=roles,liveGatewayRetainsItsExistingImage=True,existingCandidatesPreserved=True,
        legacyGatewayBoundStagerUsed=False,targetIdentityAndConfigurationVerified=False,
        privateReceiptsRefreshed=False,dockerInvoked=False,imageImportPerformed=False,containerOperations=0,
        publisherTrustAccepted=False,dependencyCoverageAccepted=False,acceptanceGranted=False,startAuthorized=False,
        requiredTargetChecks=['Explicit runtime UID/GID and packaged startup compatibility',
            'Fresh private TLS/trust/launch bindings for the new role-specific image IDs',
            'Fresh private source/config hashes and authority/environment bindings',
            'Distinct owned empty networks, current deny-guard and IPAM reservations',
            'Explicit new TLS container identities without reusing existing candidate names',
            'Complete creation manifest and independent stopped-container readback',
            'Fresh vulnerability database and custom/publisher/Wasm review before acceptance'])
    inventory['isolatedDossier']=dossier
    (root/'inventory.json').write_text(json.dumps(inventory,indent=2,sort_keys=True)+'\n')
    print('OUF_ISOLATED_V2_DOSSIER='+json.dumps(dossier,sort_keys=True))

if __name__=='__main__':main()
