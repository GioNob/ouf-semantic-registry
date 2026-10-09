"""Read-only complete Config/HostConfig rules with exact §45/§46 binding."""
from tools.verify_semantic_environment_binding import Query,verify,pairing,role_secret,require,private,decode,sha,encoded
from tools.review_semantic_creation_fields import review_fields
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
