#!/usr/bin/env python3
"""Adopt the prepared same-image owner tenant binding with backup and runtime rollback."""
import argparse
import json
import os
from pathlib import Path
import stat
import tempfile
import r4a_prepare_publication_bindings as bindings
import r4a_switch_managed_identity_candidate as rollout

ROOT = bindings.ROOT
RECEIPT = ROOT / 'publication-owner-switch.json'


def sync_root():
    fd = os.open(ROOT, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def save(value):
    fd, name = tempfile.mkstemp(prefix='publication-owner-receipt-', dir=ROOT)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, RECEIPT)
        sync_root()
    finally:
        Path(name).unlink(missing_ok=True)


def check_prepared(state, old, candidate, image):
    if (state.get('status') != 'PASS' or state.get('old') != bindings.owner.stable(old) or
        state.get('candidateName') != bindings.NAME or state.get('candidateId') != candidate['Id'] or
        state.get('imageId') != old['Image'] or state.get('revision') != bindings.owner.REVISION or
        state.get('sourceId') != bindings.SOURCE or state.get('versionId') != bindings.VERSION or
        state.get('configurationHash') != bindings.HASH or
        image['Config'].get('Labels', {}).get('org.opencontainers.image.revision') != bindings.owner.REVISION or
        not bindings.candidate_matches(candidate, old)):
        raise RuntimeError('PREPARED_OWNER_OR_CANDIDATE_DRIFT')


def main(mode):
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    os.umask(0o077)
    meta = ROOT.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o700:
        raise RuntimeError('PRIVATE_ROOT_UNSAFE')
    if RECEIPT.exists() or RECEIPT.is_symlink():
        raise RuntimeError('OWNER_SWITCH_RECEIPT_EXISTS_RECONCILE')
    grant_receipt = rollout.private_json(ROOT / 'ingestion-runtime-publication-grant-publication.json')
    if grant_receipt.get('status') != 'PASS' or grant_receipt.get('activePolicyRef') != 'ouf-lab-authorization:33':
        raise RuntimeError('PUBLICATION_GRANT_RECEIPT_NOT_PASS')
    state = rollout.private_json(bindings.STATE)
    old = bindings.owner.inventory.inspect('ouf-onboarding')
    candidate = bindings.owner.inventory.inspect(bindings.NAME)
    image = bindings.owner.inventory.inspect(old['Image'])
    check_prepared(state, old, candidate, image)
    bindings.owner.runtime_guard(old, image)
    rollout.tokens_fresh(old)
    before = bindings.frozen.candidate_row(bindings.SOURCE, bindings.VERSION, bindings.HASH)
    if before['state'] != 'APPROVED':
        raise RuntimeError('SOURCE_NOT_APPROVED')
    history = rollout.history()
    if len([x for x in history if x['version'] is not None and x['success']]) != 31 or any(not x['success'] for x in history):
        raise RuntimeError('OWNER_FLYWAY_BASELINE_NOT_31')
    rollout.ready(1)
    previous = 'ouf-onboarding-runtime-tenant-rollback-' + old['Id'][:12]
    failed = 'ouf-onboarding-runtime-tenant-failed-' + candidate['Id'][:12]
    if bindings.owner.optional(previous) is not None or bindings.owner.optional(failed) is not None:
        raise RuntimeError('OWNER_RETENTION_NAME_OCCUPIED')
    print('R4A_PUBLICATION_OWNER_SWITCH_PLAN=PASS MODE=' + mode + ' SAME_IMAGE=true FLYWAY=31 SOURCE_STATE=APPROVED', flush=True)
    if mode == 'plan':
        print('R4A_PUBLICATION_OWNER_SWITCH=PLANNED LIVE_UNCHANGED=true SOURCE_ACTIVATION=false')
        return
    receipt = dict(status='STARTING', oldId=old['Id'], candidateId=candidate['Id'],
                   rollbackContainer=previous, failedContainer=failed, dbDump=None)
    # Reserve before any live mutation; receipt prevents blind re-entry.
    fd = os.open(RECEIPT, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(receipt, stream)
        stream.flush()
        os.fsync(stream.fileno())
    sync_root()
    try:
        if bindings.owner.stable(bindings.owner.inventory.inspect('ouf-onboarding')) != state['old']:
            raise RuntimeError('OWNER_LIVE_CHANGED_BEFORE_STOP')
        print('R4A_PUBLICATION_OWNER_SWITCH=STOPPING_LIVE SOURCE_ACTIVATION=false', flush=True)
        rollout.docker('update', '--restart', 'no', 'ouf-onboarding')
        rollout.docker('stop', '--time', '60', 'ouf-onboarding')
        receipt['dbDump'] = str(rollout.backup_restore())
        save(receipt)
        if rollout.history() != history or bindings.frozen.candidate_row(bindings.SOURCE, bindings.VERSION, bindings.HASH) != before:
            raise RuntimeError('OWNER_DB_CHANGED_DURING_BACKUP')
        if not bindings.candidate_matches(bindings.owner.inventory.inspect(bindings.NAME), old):
            raise RuntimeError('OWNER_CANDIDATE_CHANGED_DURING_BACKUP')
        rollout.docker('rename', 'ouf-onboarding', previous)
        rollout.docker('rename', bindings.NAME, 'ouf-onboarding')
        rollout.docker('start', 'ouf-onboarding')
        rollout.ready()
        current = bindings.owner.inventory.inspect('ouf-onboarding')
        expected_env = bindings.owner.inventory.environment(old)
        expected_env['OUF_RUNTIME_PUBLICATIONS_TENANT_ID'] = 'ouf-lab'
        if (current['Id'] != candidate['Id'] or current['Image'] != old['Image'] or
            bindings.owner.inventory.environment(current) != expected_env or
            bindings.owner.mounts(current) != bindings.owner.mounts(old) or
            any(current['Config'].get(k) != old['Config'].get(k) for k in ('User', 'Entrypoint', 'Cmd', 'WorkingDir', 'ExposedPorts')) or
            rollout.history() != history or bindings.frozen.candidate_row(bindings.SOURCE, bindings.VERSION, bindings.HASH) != before):
            raise RuntimeError('OWNER_POST_SWITCH_DRIFT')
        denied = rollout.http_code('/api/internal/v1/onboarding/managed-files/content?ref=object://managed-files/11111111-1111-1111-1111-111111111111')
        if denied not in ('401', '403'):
            raise RuntimeError('OWNER_ANONYMOUS_MANAGED_READ_NOT_DENIED')
        rollout.tokens_fresh(current)
        rollout.docker('update', '--restart', 'unless-stopped', 'ouf-onboarding')
        bindings.owner.runtime_guard(bindings.owner.inventory.inspect('ouf-onboarding'), image)
        receipt.update(status='PASS', imageId=old['Image'], revision=bindings.owner.REVISION,
                       sourceState='APPROVED', configurationHash=bindings.HASH, anonymousManagedReadHttp=denied)
        save(receipt)
    except BaseException:
        try:
            rollback_state = dict(old=state['old'], candidate_id=state['candidateId'])
            rollout.recover(rollback_state, previous, failed)
            receipt['status'] = 'ROLLED_BACK'
            print('R4A_PUBLICATION_OWNER_ROLLBACK=PASS DB_NOT_AUTOMATICALLY_RESTORED=true', flush=True)
        except Exception:
            receipt['status'] = 'MANUAL_RECOVERY_REQUIRED'
            print('R4A_PUBLICATION_OWNER_ROLLBACK=MANUAL_RECOVERY_REQUIRED', flush=True)
        save(receipt)
        raise
    print('R4A_PUBLICATION_OWNER_SWITCH=PASS TENANT_ENV_MATCH=true SAME_IMAGE=true FLYWAY_UNCHANGED=true')
    print('R4A_PUBLICATION_OWNER_ROLLBACK_CONTAINER=' + previous)
    print('R4A_PUBLICATION_OWNER_RECEIPT=' + str(RECEIPT) + ' PRIVATE=true')
    print('R4A_PUBLICATION_OWNER_COMPLETE=PASS SOURCE_STATE=APPROVED SOURCE_ACTIVATION=false WORKER_UNCHANGED=true REFRESHER_UNCHANGED=true SECRETS_NOT_PRINTED=true')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('plan', 'apply'))
    try:
        main(parser.parse_args().mode)
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_PUBLICATION_OWNER_SWITCH=BLOCKED CODE=' + code + ' SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
