#!/usr/bin/env python3
"""Confirm and publish the reviewed Ingestion publication grant once, with readback."""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import r4a_service_grant_lifecycle as lifecycle

ROOT = Path('/etc/ouf/deploy-snapshots')
STATE = ROOT / 'ingestion-runtime-publication-grant-draft.json'
RECEIPT = ROOT / 'ingestion-runtime-publication-grant-publication.json'
DRAFT = 'c957ad91-95f3-43fe-8a43-808e0566f977'
BASE = 'ouf-lab-authorization:32'
TARGET = 'ouf-lab-authorization:33'
GRANT = 'grant-onboarding-runtime-publication-read-ingestion'
MANIFEST = Path(__file__).with_name('r4a-ingestion-runtime-publication-grant.json')
MANIFEST_SHA = 'df04f4d925d76b9ba3bb59d5b60543073049a4c2d71f36f239bcfe4d4962337d'


def record(fd, value):
    os.lseek(fd, 0, os.SEEK_SET)
    payload = (json.dumps(value, sort_keys=True) + '\n').encode()
    offset = 0
    while offset < len(payload):
        offset += os.write(fd, payload[offset:])
    os.ftruncate(fd, len(payload))
    os.fsync(fd)


def validate_state(state, desired):
    if (state.get('draftId') != DRAFT or state.get('revision') != 0 or
        state.get('targetPolicyRef') != TARGET or state.get('addedGrantIds') != [GRANT] or
        state.get('desiredGrants') != {GRANT: desired[0]}):
        raise RuntimeError('REVIEWED_DRAFT_STATE_MISMATCH')


def main():
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    os.umask(0o077)
    meta = ROOT.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o700:
        raise RuntimeError('PRIVATE_ROOT_UNSAFE')
    if RECEIPT.exists() or RECEIPT.is_symlink():
        raise RuntimeError('PUBLICATION_RECEIPT_EXISTS_RECONCILE_DO_NOT_REPOST')
    raw = MANIFEST.read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA:
        raise RuntimeError('GRANT_MANIFEST_HASH_MISMATCH')
    desired = lifecycle.manifest(MANIFEST)
    state = lifecycle.read_state(STATE)
    validate_state(state, desired)
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise RuntimeError('HUMAN_CONFIRMATION_TERMINAL_REQUIRED')
    token = lifecycle.device_login()
    active = lifecycle.active(lifecycle.DEFAULT_BASE, token)
    policy = active['policy']
    if (active.get('policyRef') != BASE or len(policy['capabilities']) != 36 or len(policy['grants']) != 76 or
        lifecycle.digest(policy['capabilities']) != state['capabilitiesHash'] or
        lifecycle.digest(policy['grants']) != state['baselineGrantsHash']):
        raise RuntimeError('ACTIVE_POLICY_BASELINE_DRIFT')
    lifecycle.preview(lifecycle.DEFAULT_BASE, token, state)
    print('R4A_PUBLICATION_GRANT_REVIEW=PASS BASE=' + BASE + ' TARGET=' + TARGET)
    print('ADD_GRANT=' + GRANT + ' SERVICE_PRINCIPAL=ouf-ingestion TENANT=ouf-lab')
    print('RESOURCE_TYPE=published-configuration MODULE=ONBOARDING')
    print('VALID_UNTIL=2036-09-15T07:13:50.968730Z CAPABILITY_CHANGES=0 EXISTING_GRANTS_PRESERVED=true')
    phrase = 'PUBBLICO ' + TARGET
    if input('Per pubblicare digita ' + phrase + ': ').strip() != phrase:
        raise RuntimeError('HUMAN_PUBLICATION_NOT_CONFIRMED')
    # Recheck after the terminal prompt; never silently publish against a new base.
    current = lifecycle.active(lifecycle.DEFAULT_BASE, token)
    if current.get('policyRef') != BASE or current.get('policy') != policy or lifecycle.read_state(STATE) != state:
        raise RuntimeError('POLICY_OR_DRAFT_DRIFT_AFTER_CONFIRMATION')
    lifecycle.preview(lifecycle.DEFAULT_BASE, token, state)
    fd = os.open(RECEIPT, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    receipt = dict(status='UNVERIFIED_DO_NOT_REPOST', draftId=DRAFT, targetPolicyRef=TARGET,
                   sourceActivation=False, addedGrantIds=[GRANT])
    try:
        record(fd, receipt)
        folder_fd = os.open(ROOT, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(folder_fd)
        finally:
            os.close(folder_fd)
        status, value, _ = lifecycle.request(lifecycle.DEFAULT_BASE, token,
            '/policies/' + DRAFT + ':publish', 'POST', etag=state['revision'])
        if status != 200 or value.get('state') != 'PUBLISHED':
            raise RuntimeError('POLICY_PUBLICATION_RESPONSE_UNVERIFIED')
        current = lifecycle.active(lifecycle.DEFAULT_BASE, token)
        lifecycle.verify(current, state)
        receipt.update(status='PASS', activePolicyRef=current['policyRef'],
                       activeCapabilities=len(current['policy']['capabilities']),
                       activeGrants=len(current['policy']['grants']))
        record(fd, receipt)
    finally:
        os.close(fd)
    print('R4A_PUBLICATION_GRANT_PUBLISH=PASS POLICY_REF=' + TARGET)
    print('R4A_PUBLICATION_GRANT_READBACK=PASS ACTIVE_CAPABILITIES=36 ACTIVE_GRANTS=77 EXISTING_GRANTS_PRESERVED=true')
    print('R4A_PUBLICATION_GRANT_RECEIPT=' + str(RECEIPT) + ' PRIVATE=true')
    print('R4A_PUBLICATION_GRANT_COMPLETE=PASS SOURCE_ACTIVATION=false WORKER_UNCHANGED=true TOKEN_UNCHANGED=true SECRETS_NOT_PRINTED=true')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_PUBLICATION_GRANT_PUBLISH=BLOCKED CODE=' + code + ' SOURCE_ACTIVATION=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
