#!/usr/bin/env python3
"""Register the two exact owner capabilities and prepare one add-only HUMAN policy draft; never publish."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import uuid
from urllib.request import HTTPRedirectHandler, build_opener
import r4a_authorization_lifecycle as policy
import r4a_service_grant_lifecycle as grants
import r4a_register_capabilities as registry
import r4a_cinema_semantic_draft as human

ROOT = Path('/etc/ouf/deploy-snapshots')
STATE = ROOT/'ingestion-runtime-intake-policy-draft.json'
MANIFEST_HASHES = {'r4a-ingestion-runtime-intake-capabilities.json': '3b8d31d9bbde9a021575409b12003c781c3b6b6f28b3b9b78d010b1f2926ba4d', 'r4a-ingestion-runtime-intake-grants.json': '89425209cee3d05d511a69c1e087d0cd0e845c33dc2157c8afd4cfd4a44c5ba1'}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None


def manifests():
    paths={name:Path(__file__).with_name(name) for name in MANIFEST_HASHES}
    for name,path in paths.items():
        if hashlib.sha256(path.read_bytes()).hexdigest()!=MANIFEST_HASHES[name]:
            raise RuntimeError('INTAKE_MANIFEST_HASH_MISMATCH')
    caps=json.loads(paths['r4a-ingestion-runtime-intake-capabilities.json'].read_text())
    desired=policy.manifest_descriptors(paths['r4a-ingestion-runtime-intake-capabilities.json'])
    desired_grants=grants.manifest(paths['r4a-ingestion-runtime-intake-grants.json'])
    return caps,desired,desired_grants


def preview_check(value,desired,desired_grants):
    added=[policy.normalize_descriptor(x) for x in value.get('addedCapabilities',[])]
    if sorted(added,key=lambda x:x['capabilityId'])!=sorted(desired,key=lambda x:x['capabilityId']) or value.get('removedCapabilities'):
        raise RuntimeError('INTAKE_PREVIEW_CAPABILITY_DIFF_MISMATCH')
    changes=value.get('grantChanges') or []
    actual={x.get('grantId'):grants.normalize_grant(x.get('after')) for x in changes}
    expected={x['grantId']:grants.normalize_grant(x) for x in desired_grants}
    if len(changes)!=len(expected) or actual!=expected or any(x.get('before') is not None for x in changes):
        raise RuntimeError('INTAKE_PREVIEW_GRANT_DIFF_MISMATCH')


def build(current,desired,desired_grants):
    candidate,missing=policy.build_candidate(current,desired)
    if missing!=desired:
        raise RuntimeError('INTAKE_CAPABILITIES_ALREADY_ACTIVE_RECONCILE')
    oldids={x['grantId'] for x in current['policy']['grants']}
    if oldids & {x['grantId'] for x in desired_grants}:
        raise RuntimeError('INTAKE_GRANT_IDS_ALREADY_PRESENT_RECONCILE')
    candidate['grants']=[*current['policy']['grants'],*desired_grants]
    return candidate


def write(value,exclusive=False):
    if exclusive:
        fd=os.open(STATE,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
        temporary=None
    else:
        fd,name=tempfile.mkstemp(prefix='.intake-policy-',dir=ROOT)
        temporary=Path(name)
    with os.fdopen(fd,'w') as stream:
        json.dump(value,stream,sort_keys=True)
        stream.flush();os.fsync(stream.fileno())
    if temporary:
        os.replace(temporary,STATE)
    fd=os.open(ROOT,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def catalogue(token):
    rows={}
    for offset in range(0,100001,200):
        _,raw=registry.request(policy.DEFAULT_BASE+'/capabilities?limit=200&offset='+str(offset),token)
        page=json.loads(raw)
        if not isinstance(page,list) or len(page)>200:
            raise RuntimeError('CATALOGUE_PAGE_UNSUPPORTED')
        for item in page:
            ident=item.get('capability_id')
            if not isinstance(ident,str) or ident in rows:
                raise RuntimeError('CATALOGUE_DUPLICATE_OR_INVALID_ID')
            rows[ident]=item
        if len(page)<200:
            return rows
    raise RuntimeError('CATALOGUE_PAGINATION_LIMIT')


def check_registered(row,wanted):
    descriptor=row.get('descriptor')
    if isinstance(descriptor,dict) and descriptor.get('type')=='jsonb':
        descriptor=descriptor.get('value')
    if isinstance(descriptor,str):descriptor=json.loads(descriptor)
    if row.get('owner_ref')!=wanted['ownerRef'] or policy.normalize_descriptor(descriptor)!=policy.normalize_descriptor(wanted['descriptor']):
        raise RuntimeError('REGISTERED_CAPABILITY_SEMANTIC_CONFLICT')


def main(expected_base):
    if os.geteuid()!=0:
        raise RuntimeError('ROOT_REQUIRED')
    os.umask(0o077)
    meta=ROOT.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid!=0 or stat.S_IMODE(meta.st_mode)!=0o700:
        raise RuntimeError('PRIVATE_ROOT_UNSAFE')
    if STATE.exists() or STATE.is_symlink():
        raise RuntimeError('INTAKE_POLICY_STATE_EXISTS_RECONCILE_DO_NOT_REPOST')
    rows,desired,desired_grants=manifests()
    human.SCOPES={'authorization.policy.admin'}
    human.urlopen=build_opener(NoRedirect()).open
    token,_=human.human_token()
    policy.urllib.request.urlopen=build_opener(NoRedirect()).open
    current=policy.active(policy.DEFAULT_BASE,token)
    if current.get('policyRef')!=expected_base:
        raise RuntimeError('EXPECTED_POLICY_BASELINE_DRIFT')
    candidate=build(current,desired,desired_grants)
    target=candidate['bundleId']+':'+str(candidate['version'])
    registered=catalogue(token)
    missing=[]
    for row in rows:
        ident=row['descriptor']['capabilityId']
        if ident in registered:check_registered(registered[ident],row)
        else:missing.append(row)
    state=dict(status='STARTING',baseActiveRef=expected_base,targetPolicyRef=target,baselinePolicy=current['policy'],candidate=candidate,
        manifestHashes=MANIFEST_HASHES,registeredCapabilities=[],addedDescriptors=desired,addedGrants=desired_grants)
    write(state,exclusive=True)
    for row in missing:
        status,_=registry.request(policy.DEFAULT_BASE+'/capabilities',token,'POST',row)
        if status!=201:raise RuntimeError('CAPABILITY_REGISTRATION_NOT_201')
        state['registeredCapabilities'].append(row['descriptor']['capabilityId']);write(state)
    registered=catalogue(token)
    for row in rows:check_registered(registered[row['descriptor']['capabilityId']],row)
    if policy.active(policy.DEFAULT_BASE,token)!=current:
        raise RuntimeError('POLICY_BASE_DRIFT_AFTER_REGISTRATION')
    state['status']='DRAFT_POST_UNVERIFIED_DO_NOT_REPOST';write(state)
    status,draft,headers=policy.request(policy.DEFAULT_BASE,token,'/policies','POST',candidate)
    etag=headers.get('ETag','').strip('"')
    if status!=200 or not etag.isdigit():raise RuntimeError('INTAKE_DRAFT_RESPONSE_UNVERIFIED')
    state.update(draftId=str(uuid.UUID(draft['id'])),revision=int(etag),status='DRAFT_PREVIEW_PENDING');write(state)
    _,preview,_=policy.request(policy.DEFAULT_BASE,token,'/policies/'+state['draftId']+':preview','POST',etag=state['revision'])
    preview_check(preview,desired,desired_grants)
    if policy.active(policy.DEFAULT_BASE,token)!=current:
        raise RuntimeError('POLICY_BASE_DRIFT_AFTER_PREVIEW')
    state.update(status='PASS',preview=preview,baselineCapabilitiesHash=policy.digest(current['policy']['capabilities']),baselineGrantsHash=policy.digest(current['policy']['grants']));write(state)
    print('R4A_INTAKE_CAPABILITY_REGISTRATION=PASS COUNT=2 POLICY_UNPUBLISHED=true')
    print('R4A_INTAKE_POLICY_DRAFT=PASS BASE='+expected_base+' TARGET='+target+' DRAFT_ID='+state['draftId']+' REVISION='+str(state['revision']))
    print('ADD_CAPABILITIES=datalake.write,udp.candidate.write ADD_GRANTS=2 EXISTING_CAPABILITIES_PRESERVED=true EXISTING_GRANTS_PRESERVED=true')
    print('SERVICE_PRINCIPAL=ouf-ingestion TENANT=ouf-lab RESOURCE_TYPE=ingestion-intake MODULE=UDP SOURCE_SCOPE=ALL_TENANT_SOURCES')
    print('R4A_INTAKE_POLICY_STATE='+str(STATE)+' PRIVATE=true')
    print('R4A_INTAKE_POLICY_PREPARE=PASS POLICY_NOT_PUBLISHED=true TOKEN_UNCHANGED=true ROUTES_UNCHANGED=true RUN_RESUME=false SECRETS_NOT_PRINTED=true')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-base',required=True)
    try:main(parser.parse_args().expected_base)
    except Exception as error:
        code=str(error) if isinstance(error,RuntimeError) else type(error).__name__
        print('R4A_INTAKE_POLICY_PREPARE=BLOCKED CODE='+code+' RECONCILE_IF_STATE_EXISTS=true POLICY_NOT_PUBLISHED=true RUN_RESUME=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
