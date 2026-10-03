#!/usr/bin/env python3
"""Prepare and adopt the same-image activation worker against an empty catalog."""
import argparse
import contextlib
import io
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import time
import r4a_prepare_ingestion_candidate as prepare
import r4a_switch_ingestion_candidate as rollout
import r4a_adopt_publication_refresher as access

ROOT = prepare.ROOT
NAME = 'ouf-ingestion-r4a-activation-worker-candidate'
STATE = ROOT / 'ingestion-activation-worker-prepare.json'
RECEIPT = ROOT / 'ingestion-activation-worker-switch.json'
KEY = 'ouf.ingestion.activation.enabled'
STAGE_PREFIX = 'activation-worker-'
ROLLBACK_PREFIX = 'ouf-ingestion-activation-worker-rollback-'
FAILED_PREFIX = 'ouf-ingestion-activation-worker-failed-'
FAILURE_MARKERS = ('ING_ACTIVATION_DISCOVERY_UNAVAILABLE', 'ING_ACTIVATION_PUBLICATION_REJECTED', 'ING_ACTIVATION_DISPATCH_FAILED')


def save(value):
    fd, name = tempfile.mkstemp(prefix=STAGE_PREFIX + 'receipt-', dir=ROOT)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, RECEIPT)
        access.sync_directory(ROOT)
    finally:
        Path(name).unlink(missing_ok=True)


def content(original):
    if KEY in original.decode('utf-8'):
        raise RuntimeError('WORKER_ENABLED_PROPERTY_ALREADY_PRESENT')
    return original + b'\n' + KEY.encode() + b'=true\n'


def queues_empty(quiet=False):
    if quiet:
        with contextlib.redirect_stdout(io.StringIO()):
            access.queues_empty()
    else:
        access.queues_empty()
    # claimDue can also select legacy ACTIVE schedules without a publication.
    if access.preflight.db('ouf_ingestion', "select count(*) from ouf_ingestion.ing_schedule where state='ACTIVE'") != '0':
        raise RuntimeError('WORKER_LEGACY_ACTIVE_SCHEDULE_PRESENT')


def totals():
    return (rollout.sql('select count(*) from ouf_ingestion.ing_run'),
            rollout.sql('select count(*) from ouf_ingestion.ing_schedule'))


def logs_safe():
    result = subprocess.run(['docker', 'logs', '--tail', '250', 'ouf-ingestion'],
                            capture_output=True, text=True, timeout=15, check=True)
    return result.stdout + result.stderr


def context():
    receipt = rollout.private_json(ROOT / 'publication-refresher-adoption.json')
    if receipt.get('status') != 'PASS' or receipt.get('discoveryHttp') != 200 or receipt.get('configReadScopePresent') is not True:
        raise RuntimeError('REFRESHER_DISCOVERY_RECEIPT_NOT_PASS')
    row = prepare.probe.candidate_row(access.prepare.SOURCE, access.prepare.VERSION, access.prepare.HASH)
    if row['state'] != 'APPROVED':
        raise RuntimeError('SOURCE_NOT_APPROVED')
    live = prepare.probe.inspect('ouf-ingestion')
    image = prepare.probe.inspect(live['Image'], 'image')
    if image['Config'].get('Labels', {}).get('org.opencontainers.image.revision') != prepare.REVISION:
        raise RuntimeError('INGESTION_IMAGE_REVISION_DRIFT')
    prepare.guard(live, image)
    settings = rollout.tokens_fresh(live, 'ouf-lab')
    path = Path(next(m['Source'] for m in live['Mounts'] if m['Destination'] == prepare.probe.PROPERTIES))
    original = path.read_bytes()
    baseline = rollout.private_json(prepare.STATE)
    if hashlib.sha256(original).hexdigest() != baseline.get('properties_sha256'):
        raise RuntimeError('INGESTION_PROPERTIES_BASELINE_DRIFT')
    access.worker_disabled(live, original.decode('utf-8'))
    if any(prepare.probe.literal_property(original.decode(), key) != value for key, value in settings.items()):
        raise RuntimeError('WORKER_TRANSPORT_DRIFT')
    token_path = Path(next(m['Source'] for m in live['Mounts'] if m['Destination'] == prepare.probe.AUTH)) / Path(settings['ouf.ingestion.activation.token-file']).relative_to(prepare.probe.AUTH)
    token, claims = access.token_claims(token_path)
    if access.prepare.CAP not in str(claims.get('scope', '')).split():
        raise RuntimeError('WORKER_TOKEN_CONFIG_READ_SCOPE_MISSING')
    access.discovery(settings, token)
    queues_empty()
    history = rollout.history()
    if len([x for x in history if x['version'] is not None]) != 14 or not all(x['success'] for x in history) or history[-1]['version'] != '14':
        raise RuntimeError('INGESTION_FLYWAY14_DRIFT')
    rollout.ready(1)
    return live, image, path, original, row, history, totals()


def prepare_candidate(live, image, original):
    existing = prepare.optional(NAME)
    desired = content(original)
    if STATE.exists() or STATE.is_symlink():
        state = rollout.private_json(STATE)
        properties = Path(state['properties'])
        prepare.private(properties, 0o440)
        if (state.get('status') != 'PASS' or state.get('old') != prepare.stable(live) or
            state.get('candidateName') != NAME or state.get('imageId') != image['Id'] or
            state.get('revision') != prepare.REVISION or state.get('propertiesSha256') != hashlib.sha256(desired).hexdigest() or
            state.get('sourceId') != access.prepare.SOURCE or state.get('versionId') != access.prepare.VERSION or
            state.get('configurationHash') != access.prepare.HASH or properties.read_bytes() != desired or
            existing is None or existing['Id'] != state.get('candidateId') or
            not prepare.matches(existing, live, image, properties)):
            raise RuntimeError('WORKER_PREPARATION_STATE_DRIFT')
        return state
    if existing is not None:
        raise RuntimeError('WORKER_UNOWNED_CANDIDATE')
    folder = Path(tempfile.mkdtemp(prefix=STAGE_PREFIX, dir=ROOT))
    properties = folder / 'ingestion-summary.properties'
    properties.write_bytes(desired)
    os.chown(properties, 0, 10002)
    properties.chmod(0o440)
    with properties.open('rb') as stream:
        os.fsync(stream.fileno())
    access.sync_directory(folder)
    env_path = folder / 'candidate.env'
    created = None
    try:
        env_path.write_text('\n'.join(live['Config']['Env']) + '\n')
        command = ['docker', 'create', '--name', NAME, '--network', 'ouf-backend', '--network-alias', 'ouf-ingestion',
            '--restart', 'no', '--user', '10002:10002', '--log-driver', 'json-file', '--env-file', str(env_path)]
        command.extend(prepare.memory_flags(live['HostConfig']))
        for key, value in live['HostConfig']['LogConfig'].get('Config', {}).items():
            command.extend(['--log-opt', key + '=' + value])
        for _, source, target, _ in prepare.mounts(live, properties):
            command.extend(['--mount', 'type=bind,src=' + source + ',dst=' + target + ',readonly'])
        command.append(image['Id'])
        created = prepare.probe.run(command)
        candidate = prepare.probe.inspect(NAME)
        if candidate['Id'] != created or not prepare.matches(candidate, live, image, properties):
            raise RuntimeError('WORKER_CANDIDATE_READBACK_MISMATCH')
        if prepare.stable(prepare.probe.inspect('ouf-ingestion')) != prepare.stable(live):
            raise RuntimeError('WORKER_LIVE_CHANGED_DURING_PREPARE')
        state = dict(status='PASS', old=prepare.stable(live), candidateId=created, candidateName=NAME,
            imageId=image['Id'], revision=prepare.REVISION, properties=str(properties),
            propertiesSha256=hashlib.sha256(desired).hexdigest(), sourceId=access.prepare.SOURCE,
            versionId=access.prepare.VERSION, configurationHash=access.prepare.HASH)
        temporary = folder / 'state.json'
        temporary.write_text(json.dumps(state, sort_keys=True))
        with temporary.open('rb') as stream:
            os.fsync(stream.fileno())
        os.link(temporary, STATE)
        access.sync_directory(ROOT)
        return state
    except BaseException:
        if created:
            current = prepare.optional(NAME)
            if current is not None and current['Id'] == created and not current['State']['Running']:
                prepare.probe.run(['docker', 'rm', created])
        raise
    finally:
        env_path.unlink(missing_ok=True)


def main(mode):
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    os.umask(0o077)
    meta = ROOT.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o700:
        raise RuntimeError('PRIVATE_ROOT_UNSAFE')
    if RECEIPT.exists() or RECEIPT.is_symlink():
        raise RuntimeError('WORKER_SWITCH_RECEIPT_EXISTS_RECONCILE')
    live, image, original_path, original, row, history, counts = context()
    if mode == 'prepare':
        state = prepare_candidate(live, image, original)
        if (original_path.read_bytes() != original or rollout.history() != history or
            prepare.probe.candidate_row(access.prepare.SOURCE, access.prepare.VERSION, access.prepare.HASH) != row):
            raise RuntimeError('WORKER_CONTEXT_CHANGED_DURING_PREPARE')
        print('R4A_ACTIVATION_WORKER_PREPARE=PASS STOPPED=true SAME_IMAGE=true LIVE_UNCHANGED=true SOURCE_ACTIVATION=false')
        print('R4A_ACTIVATION_WORKER_STATE=' + str(STATE) + ' PRIVATE=true')
        return
    state = rollout.private_json(STATE)
    properties = Path(state['properties'])
    prepare.private(properties, 0o440)
    candidate = prepare.probe.inspect(NAME)
    if (state.get('status') != 'PASS' or state.get('old') != prepare.stable(live) or
        state.get('candidateName') != NAME or state.get('candidateId') != candidate['Id'] or
        state.get('imageId') != image['Id'] or state.get('revision') != prepare.REVISION or
        state.get('sourceId') != access.prepare.SOURCE or state.get('versionId') != access.prepare.VERSION or
        state.get('configurationHash') != access.prepare.HASH or properties.read_bytes() != content(original) or
        hashlib.sha256(properties.read_bytes()).hexdigest() != state.get('propertiesSha256') or
        not prepare.matches(candidate, live, image, properties)):
        raise RuntimeError('WORKER_PINNED_CANDIDATE_DRIFT')
    previous = ROLLBACK_PREFIX + live['Id'][:12]
    failed = FAILED_PREFIX + candidate['Id'][:12]
    if prepare.optional(previous) is not None or prepare.optional(failed) is not None:
        raise RuntimeError('WORKER_RETENTION_NAME_OCCUPIED')
    print('R4A_ACTIVATION_WORKER_SWITCH_PLAN=PASS MODE=' + mode + ' SAME_IMAGE=true FLYWAY=14 EMPTY_CATALOG=true', flush=True)
    if mode == 'plan':
        print('R4A_ACTIVATION_WORKER_SWITCH=PLANNED LIVE_UNCHANGED=true SOURCE_ACTIVATION=false')
        return
    receipt = dict(status='STARTING', oldId=live['Id'], candidateId=candidate['Id'], rollbackContainer=previous,
                   failedContainer=failed, propertiesSha256=state['propertiesSha256'], dbDump=None)
    fd = os.open(RECEIPT, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(receipt, stream)
        stream.flush()
        os.fsync(stream.fileno())
    access.sync_directory(ROOT)
    try:
        if prepare.stable(prepare.probe.inspect('ouf-ingestion')) != state['old'] or original_path.read_bytes() != original:
            raise RuntimeError('WORKER_LIVE_CHANGED_BEFORE_STOP')
        print('R4A_ACTIVATION_WORKER_SWITCH=STOPPING_LIVE SOURCE_ACTIVATION=false', flush=True)
        rollout.docker('update', '--restart', 'no', 'ouf-ingestion')
        rollout.docker('stop', '--time', '60', 'ouf-ingestion')
        receipt['dbDump'] = str(rollout.backup_restore(history))
        save(receipt)
        queues_empty()
        if (rollout.history() != history or properties.read_bytes() != content(original) or
            prepare.probe.candidate_row(access.prepare.SOURCE, access.prepare.VERSION, access.prepare.HASH) != row or
            not prepare.matches(prepare.probe.inspect(NAME), live, image, properties)):
            raise RuntimeError('WORKER_CONTEXT_CHANGED_DURING_BACKUP')
        rollout.docker('rename', 'ouf-ingestion', previous)
        rollout.docker('rename', NAME, 'ouf-ingestion')
        rollout.docker('start', 'ouf-ingestion')
        rollout.ready()
        current = prepare.probe.inspect('ouf-ingestion')
        if (current['Id'] != candidate['Id'] or current['Image'] != image['Id'] or
            prepare.environment(current) != prepare.environment(live) or
            prepare.mounts(current) != prepare.mounts(live, properties) or
            any(current['HostConfig'].get(k, 0) != live['HostConfig'].get(k, 0) for k in ('Memory', 'MemorySwap')) or
            any(current['Config'].get(k) != live['Config'].get(k) for k in ('User', 'Entrypoint', 'Cmd', 'WorkingDir', 'ExposedPorts')) or
            properties.read_bytes() != content(original) or original_path.read_bytes() != original or rollout.history() != history):
            raise RuntimeError('WORKER_POST_SWITCH_RUNTIME_DRIFT')
        rollout.tokens_fresh(current, 'ouf-lab')
        # Observe beyond the default initial delay and poll interval. No log
        # values leave this process; absence of markers is not a poll counter.
        for number in range(8):
            time.sleep(2)
            rollout.ready(1)
            queues_empty(quiet=True)
            if totals() != counts:
                raise RuntimeError('WORKER_RUN_OR_SCHEDULE_CREATED_BEFORE_ACTIVATION')
            if number in (3, 7):
                print('R4A_ACTIVATION_WORKER_OBSERVATION_WAIT_SECONDS=' + str((number + 1) * 2), flush=True)
            logs = logs_safe()
            if any(marker in logs for marker in FAILURE_MARKERS):
                raise RuntimeError('WORKER_ACTIVATION_FAILURE_MARKER_OBSERVED')
        if prepare.probe.candidate_row(access.prepare.SOURCE, access.prepare.VERSION, access.prepare.HASH) != row:
            raise RuntimeError('SOURCE_CHANGED_DURING_WORKER_OBSERVATION')
        rollout.docker('update', '--restart', 'unless-stopped', 'ouf-ingestion')
        prepare.guard(prepare.probe.inspect('ouf-ingestion'), image)
        receipt.update(status='PASS', runCount=counts[0], scheduleCount=counts[1], workerEnabled=True, sourceState='APPROVED', observationSeconds=16,
                       revision=prepare.REVISION, configurationHash=access.prepare.HASH)
        save(receipt)
    except BaseException:
        try:
            rollback_state = dict(old=state['old'], candidate_id=state['candidateId'])
            rollout.recover(rollback_state, previous, failed)
            receipt['status'] = 'ROLLED_BACK'
            print('R4A_ACTIVATION_WORKER_ROLLBACK=PASS WORKER_DISABLED_RESTORED=true', flush=True)
        except Exception:
            receipt['status'] = 'MANUAL_RECOVERY_REQUIRED'
            print('R4A_ACTIVATION_WORKER_ROLLBACK=MANUAL_RECOVERY_REQUIRED', flush=True)
        save(receipt)
        raise
    print('R4A_ACTIVATION_WORKER_SWITCH=PASS WORKER_ENABLED=true SAME_IMAGE=true FLYWAY_UNCHANGED=true NO_NEW_RUNS=true')
    print('R4A_ACTIVATION_WORKER_OBSERVATION=PASS SECONDS=16 FAILURE_MARKERS_ABSENT=true POLL_COUNT_NOT_MEASURED=true')
    print('R4A_ACTIVATION_WORKER_ROLLBACK_CONTAINER=' + previous)
    print('R4A_ACTIVATION_WORKER_RECEIPT=' + str(RECEIPT) + ' PRIVATE=true')
    print('R4A_ACTIVATION_WORKER_COMPLETE=PASS SOURCE_STATE=APPROVED SOURCE_ACTIVATION=false SECRETS_NOT_PRINTED=true')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'plan', 'apply'))
    try:
        main(parser.parse_args().mode)
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_ACTIVATION_WORKER=BLOCKED CODE=' + code + ' SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
