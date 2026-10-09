#!/usr/bin/env python3
"""Publish the reviewed source-independent intake policy once with HUMAN terminal confirmation."""
import json
import os
import stat
import sys
import r4a_prepare_runtime_intake_policy as prepare

ROOT=prepare.ROOT
RECEIPT=ROOT/'ingestion-runtime-intake-policy-publication.json'
DRAFT='34a9b8f5-50e2-4c6a-86b1-6d869d053a95'
BASE='ouf-lab-authorization:33'
TARGET='ouf-lab-authorization:34'


def validate(state,desired,desired_grants):
    if (state.get('status')!='PASS' or state.get('draftId')!=DRAFT or state.get('revision')!=0 or
        state.get('baseActiveRef')!=BASE or state.get('targetPolicyRef')!=TARGET or
        state.get('manifestHashes')!=prepare.MANIFEST_HASHES or state.get('addedDescriptors')!=desired or
        state.get('addedGrants')!=desired_grants):
        raise RuntimeError('REVIEWED_INTAKE_DRAFT_STATE_MISMATCH')
    baseline=state['baselinePolicy'];candidate=state['candidate']
    if (len(baseline['capabilities'])!=36 or len(baseline['grants'])!=77 or
        candidate['bundleId']!=baseline['bundleId'] or candidate['version']!=baseline['version']+1 or
        candidate['capabilities']!=baseline['capabilities']+desired or
        candidate['grants']!=baseline['grants']+desired_grants or
        prepare.policy.digest(baseline['capabilities'])!=state['baselineCapabilitiesHash'] or
        prepare.policy.digest(baseline['grants'])!=state['baselineGrantsHash']):
        raise RuntimeError('INTAKE_ADD_ONLY_CANDIDATE_MISMATCH')


def preview(token,state,desired,desired_grants):
    _,value,_=prepare.policy.request(prepare.policy.DEFAULT_BASE,token,'/policies/'+DRAFT+':preview','POST',etag=state['revision'])
    prepare.preview_check(value,desired,desired_grants)


def verify(active,state):
    policy=active['policy'];candidate=state['candidate']
    if (active.get('policyRef')!=TARGET or policy.get('bundleId')!=candidate['bundleId'] or
        policy.get('version')!=candidate['version'] or policy.get('capabilities')!=candidate['capabilities'] or
        policy.get('grants')!=candidate['grants']):
        raise RuntimeError('INTAKE_ACTIVE_READBACK_MISMATCH_DO_NOT_REPOST')


def record(fd,value):
    os.lseek(fd,0,os.SEEK_SET)
    payload=(json.dumps(value,sort_keys=True)+'\n').encode()
    offset=0
    while offset<len(payload):offset+=os.write(fd,payload[offset:])
    os.ftruncate(fd,len(payload));os.fsync(fd)


def main():
    if os.geteuid()!=0:
        raise RuntimeError('ROOT_REQUIRED')
    os.umask(0o077)
    meta=ROOT.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid!=0 or stat.S_IMODE(meta.st_mode)!=0o700:
        raise RuntimeError('PRIVATE_ROOT_UNSAFE')
    if RECEIPT.exists() or RECEIPT.is_symlink():
        raise RuntimeError('INTAKE_PUBLICATION_RECEIPT_EXISTS_RECONCILE_DO_NOT_REPOST')
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise RuntimeError('HUMAN_TERMINAL_REQUIRED')
    _,desired,desired_grants=prepare.manifests()
    state=prepare.policy.read_state(prepare.STATE)
    validate(state,desired,desired_grants)
    prepare.human.SCOPES={'authorization.policy.admin'}
    prepare.human.urlopen=prepare.build_opener(prepare.NoRedirect()).open
    token,_=prepare.human.human_token()
    prepare.policy.urllib.request.urlopen=prepare.build_opener(prepare.NoRedirect()).open
    current=prepare.policy.active(prepare.policy.DEFAULT_BASE,token)
    if current.get('policyRef')!=BASE or current.get('policy')!=state['baselinePolicy']:
        raise RuntimeError('INTAKE_POLICY_BASELINE_DRIFT')
    preview(token,state,desired,desired_grants)
    print('R4A_INTAKE_POLICY_REVIEW=PASS BASE='+BASE+' TARGET='+TARGET,flush=True)
    print('ADD_CAPABILITIES=datalake.write,udp.candidate.write ADD_GRANTS=2 EXISTING_ENTRIES_PRESERVED=true',flush=True)
    print('SERVICE_PRINCIPAL=ouf-ingestion TENANT=ouf-lab RESOURCE_TYPE=ingestion-intake MODULE=UDP SOURCE_SCOPE=ALL_TENANT_SOURCES',flush=True)
    print('VALID_UNTIL=2036-09-15T07:13:50.968730Z TOKEN_UNCHANGED=true ROUTES_UNCHANGED=true RUN_RESUME=false',flush=True)
    phrase='PUBBLICO '+TARGET
    if input('Per pubblicare digita '+phrase+': ').strip()!=phrase:
        print('R4A_INTAKE_POLICY_PUBLICATION=CANCELLED POLICY_NOT_PUBLISHED=true')
        return
    if prepare.policy.read_state(prepare.STATE)!=state or prepare.policy.active(prepare.policy.DEFAULT_BASE,token)!=current:
        raise RuntimeError('INTAKE_POLICY_OR_DRAFT_DRIFT_AFTER_CONFIRMATION')
    preview(token,state,desired,desired_grants)
    fd=os.open(RECEIPT,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
    receipt=dict(status='UNVERIFIED_DO_NOT_REPOST',draftId=DRAFT,targetPolicyRef=TARGET,
        addedCapabilityIds=[x['capabilityId'] for x in desired],addedGrantIds=[x['grantId'] for x in desired_grants])
    try:
        record(fd,receipt)
        folder=os.open(ROOT,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(folder)
        finally:os.close(folder)
        status,response,_=prepare.policy.request(prepare.policy.DEFAULT_BASE,token,'/policies/'+DRAFT+':publish','POST',etag=state['revision'])
        if status!=200 or response.get('state')!='PUBLISHED':
            raise RuntimeError('INTAKE_PUBLICATION_RESPONSE_UNVERIFIED_DO_NOT_REPOST')
        active=prepare.policy.active(prepare.policy.DEFAULT_BASE,token)
        verify(active,state)
        receipt.update(status='PASS',activePolicyRef=TARGET,activeCapabilities=len(active['policy']['capabilities']),activeGrants=len(active['policy']['grants']))
        record(fd,receipt)
    finally:os.close(fd)
    print('R4A_INTAKE_POLICY_PUBLICATION=PASS POLICY_REF='+TARGET)
    print('R4A_INTAKE_POLICY_READBACK=PASS ACTIVE_CAPABILITIES=38 ACTIVE_GRANTS=79 EXISTING_ENTRIES_PRESERVED=true')
    print('R4A_INTAKE_POLICY_RECEIPT='+str(RECEIPT)+' PRIVATE=true')
    print('R4A_INTAKE_POLICY_COMPLETE=PASS TOKEN_UNCHANGED=true ROUTES_UNCHANGED=true RUN_RESUME=false SECRETS_NOT_PRINTED=true')


if __name__=='__main__':
    try:main()
    except Exception as error:
        code=str(error) if isinstance(error,RuntimeError) else type(error).__name__
        print('R4A_INTAKE_POLICY_PUBLICATION=BLOCKED CODE='+code+' DO_NOT_REPOST_IF_RECEIPT_EXISTS=true RUN_RESUME=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
