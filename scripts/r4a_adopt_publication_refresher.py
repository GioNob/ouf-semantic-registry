#!/usr/bin/env python3
"""Adopt the prepared scope refresher; renew the workload token and prove discovery."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import time
import r4a_prepare_publication_bindings as prepare
import r4a_switch_managed_identity_candidate as owner_rollout
import r4a_worker_enablement_preflight as preflight

ROOT = prepare.ROOT
RECEIPT = ROOT / 'publication-refresher-adoption.json'
SERVICE = 'ouf-ingestion-policy-token.service'


def system(*args):
    return prepare.frozen.run(['systemctl', *args], timeout=60)


def save(receipt):
    fd, name = tempfile.mkstemp(prefix='publication-refresher-receipt-', dir=ROOT)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(receipt, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, RECEIPT)
        sync_directory(ROOT)
    finally:
        Path(name).unlink(missing_ok=True)


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def install(data, metadata):
    target = prepare.REFRESHER
    fd, name = tempfile.mkstemp(prefix='.r4a-refresher-', dir=target.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            os.fchown(stream.fileno(), metadata.st_uid, metadata.st_gid)
            os.fchmod(stream.fileno(), stat.S_IMODE(metadata.st_mode))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, target)
        sync_directory(target.parent)
    finally:
        Path(name).unlink(missing_ok=True)


def worker_disabled(live, properties):
    env = prepare.owner.inventory.environment(live)
    command = ' '.join((live['Config'].get('Entrypoint') or []) + (live['Config'].get('Cmd') or []))
    command += ' ' + ' '.join(env.get(k, '') for k in ('JAVA_TOOL_OPTIONS', 'JDK_JAVA_OPTIONS', '_JAVA_OPTIONS'))
    if (env.get('SPRING_APPLICATION_JSON') or 'ouf.ingestion.activation.enabled' in command or
        env.get('OUF_INGESTION_ACTIVATION_ENABLED', 'false').strip().lower() != 'false'):
        raise RuntimeError('WORKER_DISABLED_BINDING_NOT_PROVEN')
    values = re.findall(r'^\s*ouf\.ingestion\.activation\.enabled\s*[=:]\s*(.*?)\s*$', properties, re.MULTILINE)
    if len(values) > 1 or any(x.strip().lower() != 'false' for x in values):
        raise RuntimeError('WORKER_DISABLED_PROPERTY_NOT_PROVEN')


def queues_empty():
    counts = {
        'ACTIVE_PUBLICATIONS': preflight.db('ouf_onboarding', 'select count(*) from ouf_onboarding.published_configuration where active'),
        'ACTIVE_SCHEDULES': preflight.db('ouf_ingestion', "select count(*) from ouf_ingestion.ing_schedule where state='ACTIVE' and publication_enabled and not activation_blocked"),
        'UNFINISHED_RUNS': preflight.db('ouf_ingestion', "select count(*) from ouf_ingestion.ing_run where state in ('READY','PREFLIGHT','RUNNING','DRAINING')"),
    }
    for name, count in counts.items():
        print('PUBLICATION_REFRESHER_' + name + '=' + count)
    if any(count != '0' for count in counts.values()):
        raise RuntimeError('PUBLICATION_REFRESHER_QUEUE_NOT_EMPTY')


def token_claims(path):
    token = path.read_text().strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', token):
        raise RuntimeError('ING_TOKEN_FORMAT_INVALID')
    part = token.split('.')[1]
    return token, json.loads(base64.urlsafe_b64decode(part + '=' * (-len(part) % 4)))


def discovery(settings, token):
    endpoint = settings['ouf.ingestion.activation.gateway-url'].rstrip('/') + '/api/onboarding/v1/runtime/publications?limit=20&after='
    config = ('silent\nshow-error\nmax-time = 5\nmax-filesize = 2097152\n'
        'header = "Authorization: Bearer ' + token + '"\nurl = ' + json.dumps(endpoint) + '\nwrite-out = "\\n%{http_code}"\n')
    raw = prepare.frozen.run(['docker', 'run', '--rm', '-i', '--read-only', '--cap-drop', 'ALL',
        '--security-opt', 'no-new-privileges', '--network', 'ouf-backend', 'curlimages/curl:8.16.0',
        '--config', '-'], input=config, timeout=15)
    body, code = raw.rsplit('\n', 1)
    print('PUBLICATION_REFRESHER_DISCOVERY_HTTP=' + (code if re.fullmatch(r'\d{3}', code) else 'INVALID'))
    if code != '200':
        raise RuntimeError('PUBLICATION_DISCOVERY_NOT_AUTHORIZED')
    page = json.loads(body)
    if not isinstance(page, dict) or page.get('items') != [] or page.get('nextAfter') != '':
        raise RuntimeError('PUBLICATION_DISCOVERY_EXPECTED_EMPTY_CATALOG')
    print('PUBLICATION_REFRESHER_DISCOVERY=PASS EMPTY_CATALOG=true OWNER_AUTHORIZATION_PROVEN=true')


def refresh():
    system('reset-failed', SERVICE)
    system('start', SERVICE)
    if system('show', SERVICE, '-p', 'ExecMainStatus', '--value') != '0':
        raise RuntimeError('TOKEN_REFRESH_SERVICE_FAILED')


def restore(original, script_meta, timers, installed, live):
    recovered = True
    try:
        for name in timers:
            system('stop', name)
        system('stop', SERVICE)
        if installed:
            install(original, script_meta)
            refresh()
            prepare.frozen.transport_settings(live, 'ouf-lab')
        for name in timers:
            system('start', name)
        recovered = prepare.REFRESHER.read_bytes() == original and all(
            system('show', name, '-p', 'ActiveState', '--value') == 'active' for name in timers)
    except BaseException:
        recovered = False
        # Best effort keeps periodic token refresh from being silently lost.
        for name in timers:
            try:
                system('start', name)
            except BaseException:
                pass
    return recovered


def main(mode):
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    os.umask(0o077)
    meta = ROOT.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o700:
        raise RuntimeError('PRIVATE_ROOT_UNSAFE')
    if RECEIPT.exists() or RECEIPT.is_symlink():
        raise RuntimeError('REFRESHER_RECEIPT_EXISTS_RECONCILE')
    state = owner_rollout.private_json(prepare.STATE)
    owner_receipt = owner_rollout.private_json(ROOT / 'publication-owner-switch.json')
    grant_receipt = owner_rollout.private_json(ROOT / 'ingestion-runtime-publication-grant-publication.json')
    owner = prepare.owner.inventory.inspect('ouf-onboarding')
    if (state.get('status') != 'PASS' or owner_receipt.get('status') != 'PASS' or
        owner['Id'] != state.get('candidateId') or owner['Image'] != state.get('imageId') or
        prepare.owner.inventory.environment(owner).get('OUF_RUNTIME_PUBLICATIONS_TENANT_ID') != 'ouf-lab' or
        grant_receipt.get('status') != 'PASS' or grant_receipt.get('activePolicyRef') != 'ouf-lab-authorization:33'):
        raise RuntimeError('OWNER_OR_GRANT_ADOPTION_NOT_PASS')
    before = prepare.frozen.candidate_row(prepare.SOURCE, prepare.VERSION, prepare.HASH)
    if before['state'] != 'APPROVED':
        raise RuntimeError('SOURCE_NOT_APPROVED')
    script_meta = prepare.REFRESHER.lstat()
    if not stat.S_ISREG(script_meta.st_mode) or script_meta.st_uid != 0 or script_meta.st_mode & 0o022:
        raise RuntimeError('INSTALLED_SCRIPT_METADATA_UNSAFE')
    original = prepare.REFRESHER.read_bytes()
    candidate_path = Path(state['refresherCandidate'])
    candidate_meta = candidate_path.lstat()
    if (not stat.S_ISREG(candidate_meta.st_mode) or candidate_meta.st_uid != 0 or
        stat.S_IMODE(candidate_meta.st_mode) != 0o600 or not candidate_path.resolve().is_relative_to(ROOT.resolve())):
        raise RuntimeError('REFRESHER_CANDIDATE_UNSAFE')
    candidate = candidate_path.read_bytes()
    if (hashlib.sha256(original).hexdigest() != prepare.EXPECTED_SCRIPT or
        state.get('refresherBeforeSha256') != prepare.EXPECTED_SCRIPT or
        hashlib.sha256(candidate).hexdigest() != state.get('refresherCandidateSha256') or
        candidate != prepare.scope_patch(original.decode('utf-8'))):
        raise RuntimeError('REFRESHER_OR_CANDIDATE_HASH_DRIFT')
    live = prepare.frozen.inspect('ouf-ingestion')
    image = prepare.frozen.inspect(live['Image'], 'image')
    if image['Config'].get('Labels', {}).get('org.opencontainers.image.revision') != '0dfab1e7b2253fd939088259ea61754d6e56706c':
        raise RuntimeError('INGESTION_WORKER_DEFAULT_REVISION_DRIFT')
    settings = prepare.frozen.transport_settings(live, 'ouf-lab')
    mounts = {m['Destination']: m for m in live['Mounts']}
    properties = Path(mounts[prepare.frozen.PROPERTIES]['Source']).read_text()
    release = owner_rollout.private_json(ROOT / 'ingestion-compatibility-release.json')
    if hashlib.sha256(properties.encode()).hexdigest() != release.get('properties_sha256'):
        raise RuntimeError('INGESTION_PROPERTIES_RELEASE_DRIFT')
    worker_disabled(live, properties)
    if any(prepare.frozen.literal_property(properties, key) != value for key, value in settings.items()):
        raise RuntimeError('ACTIVATION_TRANSPORT_DRIFT')
    token_path = Path(mounts[prepare.frozen.AUTH]['Source']) / Path(settings['ouf.ingestion.activation.token-file']).relative_to(prepare.frozen.AUTH)
    token_before, _ = token_claims(token_path)
    owner_rollout.ready(1)
    queues_empty()
    start = system('show', SERVICE, '-p', 'ExecStart', '--value')
    scripts = set(re.findall(r'(/[A-Za-z0-9_./-]+\.py)(?:\s|;|$)', start))
    if scripts != {str(prepare.REFRESHER)} or system('show', SERVICE, '-p', 'Type', '--value') != 'oneshot':
        raise RuntimeError('TOKEN_REFRESH_SERVICE_CONTRACT_UNSUPPORTED')
    names = system('show', SERVICE, '-p', 'TriggeredBy', '--value').split()
    if not names or any(not re.fullmatch(r'ouf[-._A-Za-z0-9]*\.timer', name) for name in names):
        raise RuntimeError('TOKEN_REFRESH_TIMER_CONTRACT_UNSUPPORTED')
    timers = {name: system('show', name, '-p', 'ActiveState', '--value') for name in names}
    if any(value != 'active' for value in timers.values()):
        raise RuntimeError('TOKEN_REFRESH_TIMER_NOT_ACTIVE')
    print('R4A_PUBLICATION_REFRESHER_PLAN=PASS MODE=' + mode + ' TIMER_COUNT=' + str(len(timers)) + ' WORKER_ENABLED=false', flush=True)
    if mode == 'plan':
        print('R4A_PUBLICATION_REFRESHER=PLANNED SCRIPT_UNCHANGED=true TOKEN_UNCHANGED=true SOURCE_ACTIVATION=false')
        return
    folder = Path(tempfile.mkdtemp(prefix='publication-refresher-', dir=ROOT))
    backup = folder / 'refresh-ingestion-policy-token.before.py'
    with backup.open('xb') as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(original)
        stream.flush()
        os.fsync(stream.fileno())
    sync_directory(folder)
    receipt = dict(status='STARTING', backupScript=str(backup), beforeSha256=prepare.EXPECTED_SCRIPT,
        candidateSha256=state['refresherCandidateSha256'], service=SERVICE, timers=timers,
        ingestionId=live['Id'], ownerId=owner['Id'], sourceActivation=False)
    fd = os.open(RECEIPT, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(receipt, stream)
        stream.flush()
        os.fsync(stream.fileno())
    sync_directory(ROOT)
    installed = False
    try:
        for name in timers:
            system('stop', name)
        system('stop', SERVICE)
        if prepare.REFRESHER.read_bytes() != original or candidate_path.read_bytes() != candidate:
            raise RuntimeError('REFRESHER_CHANGED_BEFORE_INSTALL')
        # Mark before replace so any failure after replacement enters restoration.
        installed = True
        install(candidate, script_meta)
        if prepare.REFRESHER.read_bytes() != candidate:
            raise RuntimeError('REFRESHER_INSTALL_READBACK_MISMATCH')
        refresh()
        # Reuses all transport checks: retained object-store scope, identity,
        # audience, expiry and mounted bearer target; no token values printed.
        if prepare.frozen.transport_settings(live, 'ouf-lab') != settings:
            raise RuntimeError('REFRESHED_TRANSPORT_DRIFT')
        token, claims = token_claims(token_path)
        if token == token_before or prepare.CAP not in str(claims.get('scope', '')).split():
            raise RuntimeError('REFRESHED_TOKEN_CONFIG_READ_SCOPE_MISSING')
        print('PUBLICATION_REFRESHER_TOKEN_READBACK=PASS TOKEN_CHANGED=true CONFIG_READ_SCOPE_PRESENT=true', flush=True)
        discovery(settings, token)
        queues_empty()
        current = prepare.frozen.inspect('ouf-ingestion')
        current_owner = prepare.owner.inventory.inspect('ouf-onboarding')
        current_properties = Path(mounts[prepare.frozen.PROPERTIES]['Source']).read_text()
        worker_disabled(current, current_properties)
        if (prepare.owner.stable(current) != prepare.owner.stable(live) or current_properties != properties or
            prepare.owner.stable(current_owner) != prepare.owner.stable(owner) or
            prepare.frozen.candidate_row(prepare.SOURCE, prepare.VERSION, prepare.HASH) != before):
            raise RuntimeError('REFRESHER_RUNTIME_OR_SOURCE_DRIFT')
        for name in timers:
            system('start', name)
        if any(system('show', name, '-p', 'ActiveState', '--value') != 'active' for name in timers):
            raise RuntimeError('TOKEN_REFRESH_TIMER_RESTART_FAILED')
        receipt.update(status='PASS', discoveryHttp=200, configReadScopePresent=True, sourceState='APPROVED')
        save(receipt)
    except BaseException:
        recovered = restore(original, script_meta, timers, installed, live)
        receipt['status'] = 'ROLLED_BACK' if recovered else 'MANUAL_RECOVERY_REQUIRED'
        save(receipt)
        print('R4A_PUBLICATION_REFRESHER_ROLLBACK=' + ('PASS' if recovered else 'MANUAL_RECOVERY_REQUIRED'), flush=True)
        raise
    print('R4A_PUBLICATION_REFRESHER=PASS TIMER_RESTORED=true WORKER_ENABLED=false SOURCE_STATE=APPROVED')
    print('R4A_PUBLICATION_REFRESHER_RECEIPT=' + str(RECEIPT) + ' PRIVATE=true')
    print('R4A_PUBLICATION_REFRESHER_COMPLETE=PASS DISCOVERY_HTTP=200 SOURCE_ACTIVATION=false SECRETS_NOT_PRINTED=true')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('plan', 'apply'))
    try:
        main(parser.parse_args().mode)
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_PUBLICATION_REFRESHER=BLOCKED CODE=' + code + ' SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
