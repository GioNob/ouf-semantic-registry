#!/usr/bin/env python3
"""Publish a reviewed generic HUMAN recovery draft once, with terminal confirmation."""
import argparse
from datetime import datetime
import json
import os
import stat
import sys
import uuid
import r4a_prepare_recovery_policy as prepare

ROOT = prepare.ROOT
RECEIPT = ROOT / 'ingestion-recovery-policy-publication.json'


def validate(state, args):
    if (state.get('status')!='PASS' or state.get('draftId')!=str(uuid.UUID(args.draft))
            or state.get('revision')!=args.revision or state.get('baseActiveRef')!=args.expected_base
            or state.get('targetPolicyRef')!=args.target or state.get('tenant')!=args.tenant
            or state.get('subject')!=str(uuid.UUID(args.subject))):
        raise RuntimeError('RECOVERY_REVIEWED_DRAFT_STATE_MISMATCH')
    desired = prepare.descriptors()
    additions = state['addedGrants']
    if len(additions)!=4:
        raise RuntimeError('RECOVERY_GRANT_SET_MISMATCH')
    when = datetime.fromisoformat(additions[0]['validFrom'].replace('Z','+00:00'))
    expected = prepare.grant_rows(args.tenant, args.subject, args.valid_until, when)
    if additions!=expected or state.get('addedDescriptors')!=desired:
        raise RuntimeError('RECOVERY_REVIEWED_PERMISSION_DIFF_MISMATCH')
    baseline = state['baselinePolicy']; candidate = state['candidate']
    if (args.expected_base!=baseline['bundleId']+':'+str(baseline['version'])
            or args.target!=candidate['bundleId']+':'+str(candidate['version'])
            or candidate['bundleId']!=baseline['bundleId']
            or candidate['version']!=baseline['version']+1
            or candidate['capabilities']!=baseline['capabilities']+desired
            or candidate['grants']!=baseline['grants']+expected
            or prepare.policy.digest(baseline['capabilities'])!=state['baselineCapabilitiesHash']
            or prepare.policy.digest(baseline['grants'])!=state['baselineGrantsHash']):
        raise RuntimeError('RECOVERY_ADD_ONLY_CANDIDATE_MISMATCH')
    # Detect duplicates/conflicts in baseline as well as accidental removals.
    rebuilt = prepare.build({'policy':baseline}, desired, expected)
    if rebuilt['capabilities']!=candidate['capabilities'] or rebuilt['grants']!=candidate['grants']:
        raise RuntimeError('RECOVERY_CANDIDATE_RECONSTRUCTION_MISMATCH')
    return desired, expected


def preview(token, state, desired, additions):
    _, value, _ = prepare.policy.request(prepare.policy.DEFAULT_BASE, token,
        '/policies/'+state['draftId']+':preview', 'POST', etag=state['revision'])
    prepare.preview_check(value, desired, additions)


def verify(active, state):
    actual = active['policy']; wanted = state['candidate']
    if (active.get('policyRef')!=state['targetPolicyRef']
            or actual.get('bundleId')!=wanted['bundleId'] or actual.get('version')!=wanted['version']
            or actual.get('capabilities')!=wanted['capabilities']
            or [prepare.normalize_grant(g) for g in actual.get('grants',[])]!=
               [prepare.normalize_grant(g) for g in wanted['grants']]):
        raise RuntimeError('RECOVERY_ACTIVE_READBACK_MISMATCH_DO_NOT_REPOST')


def record(fd, value):
    os.lseek(fd, 0, os.SEEK_SET)
    data = (json.dumps(value, sort_keys=True)+'\n').encode()
    offset = 0
    while offset<len(data):
        n = os.write(fd, data[offset:])
        if n<=0: raise RuntimeError('RECOVERY_RECEIPT_WRITE_FAILED')
        offset+=n
    os.ftruncate(fd,len(data)); os.fsync(fd)


def main(args):
    if os.geteuid()!=0: raise RuntimeError('ROOT_REQUIRED')
    os.umask(0o077)
    meta = ROOT.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid!=0 or stat.S_IMODE(meta.st_mode)!=0o700:
        raise RuntimeError('PRIVATE_ROOT_UNSAFE')
    if RECEIPT.exists() or RECEIPT.is_symlink():
        raise RuntimeError('RECOVERY_PUBLICATION_RECEIPT_EXISTS_RECONCILE_DO_NOT_REPOST')
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise RuntimeError('HUMAN_TERMINAL_REQUIRED')
    state = prepare.policy.read_state(prepare.STATE)
    desired, additions = validate(state,args)
    # A fresh login is only for policy administration, never for workload execution.
    token = prepare.login(args.tenant,args.subject)
    current = prepare.policy.active(prepare.policy.DEFAULT_BASE,token)
    if current.get('policyRef')!=args.expected_base or current.get('policy')!=state['baselinePolicy']:
        raise RuntimeError('RECOVERY_POLICY_BASELINE_DRIFT')
    preview(token,state,desired,additions)
    print('R4A_RECOVERY_POLICY_REVIEW=PASS BASE='+args.expected_base+' TARGET='+args.target,flush=True)
    print('ADD_CAPABILITIES='+','.join(prepare.CAPABILITIES)+' ADD_GRANTS=4 EXISTING_ENTRIES_PRESERVED=true',flush=True)
    print('ACTOR=HUMAN TENANT='+args.tenant+' SOURCE_SCOPE=ALL_TENANT_SOURCES SERVICE_GRANTS=0',flush=True)
    print('VALID_UNTIL='+additions[0]['validUntil'],flush=True)
    phrase = 'PUBBLICO '+args.target
    if input('Per pubblicare digita '+phrase+': ').strip()!=phrase:
        print('R4A_RECOVERY_POLICY_PUBLICATION=CANCELLED POLICY_NOT_PUBLISHED=true')
        return
    if prepare.policy.read_state(prepare.STATE)!=state or prepare.policy.active(prepare.policy.DEFAULT_BASE,token)!=current:
        raise RuntimeError('RECOVERY_POLICY_OR_STATE_DRIFT_AFTER_CONFIRMATION')
    preview(token,state,desired,additions)
    fd = os.open(RECEIPT,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    receipt = dict(status='UNVERIFIED_DO_NOT_REPOST',draftId=state['draftId'],
                   targetPolicyRef=args.target,addedCapabilityIds=list(prepare.CAPABILITIES),
                   addedGrantIds=[g['grantId'] for g in additions])
    try:
        record(fd,receipt)
        folder = os.open(ROOT,os.O_RDONLY|os.O_DIRECTORY)
        try: os.fsync(folder)
        finally: os.close(folder)
        status, response, _ = prepare.policy.request(prepare.policy.DEFAULT_BASE,token,
            '/policies/'+state['draftId']+':publish','POST',etag=state['revision'])
        if status!=200 or response.get('state')!='PUBLISHED':
            raise RuntimeError('RECOVERY_PUBLICATION_RESPONSE_UNVERIFIED_DO_NOT_REPOST')
        active = prepare.policy.active(prepare.policy.DEFAULT_BASE,token)
        verify(active,state)
        receipt.update(status='PASS',activePolicyRef=args.target,
            activeCapabilities=len(active['policy']['capabilities']),activeGrants=len(active['policy']['grants']))
        record(fd,receipt)
    finally: os.close(fd)
    print('R4A_RECOVERY_POLICY_PUBLICATION=PASS POLICY_REF='+args.target)
    print('R4A_RECOVERY_POLICY_READBACK=PASS ACTIVE_CAPABILITIES='+str(receipt['activeCapabilities'])+
          ' ACTIVE_GRANTS='+str(receipt['activeGrants'])+' EXISTING_ENTRIES_PRESERVED=true')
    print('R4A_RECOVERY_POLICY_RECEIPT='+str(RECEIPT)+' PRIVATE=true')
    print('R4A_RECOVERY_POLICY_COMPLETE=PASS IAM_UNCHANGED=true ROUTES_UNCHANGED=true WORKLOAD_TOKEN_UNCHANGED=true RETRY=false RUN_RESUME=false SECRETS_NOT_PRINTED=true')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--draft',required=True)
    p.add_argument('--revision',required=True,type=int)
    p.add_argument('--expected-base',required=True)
    p.add_argument('--target',required=True)
    p.add_argument('--tenant',required=True)
    p.add_argument('--subject',required=True)
    p.add_argument('--valid-until',required=True)
    try: main(p.parse_args())
    except Exception as error:
        code = str(error) if isinstance(error,RuntimeError) else type(error).__name__
        print('R4A_RECOVERY_POLICY_PUBLICATION=BLOCKED CODE='+code+' DO_NOT_REPOST_IF_RECEIPT_EXISTS=true RETRY=false RUN_RESUME=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
