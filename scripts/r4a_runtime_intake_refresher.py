#!/usr/bin/env python3
"""Prepare/adopt shared intake scopes; no source, route, policy or run mutation."""
import argparse
import ast
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import time
import r4a_prepare_frozen_compatibility_probe as runtime

ROOT = Path('/etc/ouf/deploy-snapshots')
SCRIPT = Path('/opt/ouf/ops/refresh-ingestion-policy-token.py')
SERVICE = 'ouf-ingestion-policy-token.service'
STATE = ROOT / 'ingestion-runtime-intake-refresher-prepare.json'
RECEIPT = ROOT / 'ingestion-runtime-intake-refresher-adoption.json'
SCOPES = ('datalake.write', 'udp.candidate.write')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def private(path):
    meta = path.lstat()
    if not stat.S_ISREG(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o600:
        raise RuntimeError('PRIVATE_FILE_UNSAFE')
    return json.loads(path.read_text())


def scope_patch(source):
    tree = ast.parse(source)
    nodes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict) and any(isinstance(k, ast.Constant) and k.value == 'grant_type'
                and isinstance(v, ast.Constant) and v.value == 'client_credentials'
                for k, v in zip(node.keys, node.values)):
            nodes.append(node)
    if len(nodes) != 1:
        raise RuntimeError('REFRESHER_GRANT_DICT_LAYOUT_UNSUPPORTED')
    node = nodes[0]
    if any(not isinstance(k, ast.Constant) or not isinstance(k.value, str) for k in node.keys):
        raise RuntimeError('REFRESHER_DYNAMIC_KEYS_UNSUPPORTED')
    keys = [k.value for k in node.keys]
    if len(set(keys)) != len(keys):
        raise RuntimeError('REFRESHER_DUPLICATE_KEYS')
    values = list(node.values)
    if 'scope' in keys:
        i = keys.index('scope')
        values[i] = ast.BinOp(left=values[i], op=ast.Add(), right=ast.Constant(' ' + ' '.join(SCOPES)))
        changed = ast.Dict(keys=node.keys, values=values)
    else:
        changed = ast.Dict(keys=node.keys + [ast.Constant('scope')], values=values + [ast.Constant(' '.join(SCOPES))])
    raw = source.encode('utf-8')
    lines = raw.splitlines(keepends=True)
    start = sum(map(len, lines[:node.lineno - 1])) + node.col_offset
    end = sum(map(len, lines[:node.end_lineno - 1])) + node.end_col_offset
    result = raw[:start] + ast.unparse(changed).encode('utf-8') + raw[end:]
    ast.parse(result)
    return result


def write(path, data, exclusive=False):
    if exclusive:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
    else:
        fd, name = tempfile.mkstemp(dir=path.parent, prefix='.r4a-intake-')
        try:
            with os.fdopen(fd, 'wb') as output:
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
            os.replace(name, path)
        finally:
            Path(name).unlink(missing_ok=True)
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def save(path, data, exclusive=False):
    write(path, json.dumps(data, sort_keys=True).encode(), exclusive)


def install(data, meta):
    fd, name = tempfile.mkstemp(dir=SCRIPT.parent, prefix='.r4a-intake-')
    try:
        with os.fdopen(fd, 'wb') as output:
            output.write(data)
            os.fchown(output.fileno(), meta.st_uid, meta.st_gid)
            os.fchmod(output.fileno(), stat.S_IMODE(meta.st_mode))
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, SCRIPT)
        fd = os.open(SCRIPT.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        Path(name).unlink(missing_ok=True)


def system(*args):
    return runtime.run(['systemctl', *args], timeout=60)


def refresh():
    system('reset-failed', SERVICE)
    system('start', SERVICE)
    if system('show', SERVICE, '-p', 'ExecMainStatus', '--value') != '0':
        raise RuntimeError('TOKEN_REFRESH_FAILED')


def snapshot():
    query = """select json_build_object(
      'busyRuns',(select count(*) from ouf_ingestion.ing_run where state in ('READY','PREFLIGHT','RUNNING','DRAINING')),
      'activeSchedules',(select count(*) from ouf_ingestion.ing_schedule where state='ACTIVE' and publication_enabled and not activation_blocked),
      'busyReplays',(select count(*) from ouf_ingestion.replay_execution where state in ('QUEUED','RUNNING','RETRY_WAIT')),
      'deliverable',(select count(*) from ouf_ingestion.handoff_outbox where state in ('READY','DELIVERING','FAILED_RETRYABLE')),
      'runs',coalesce((select json_agg(x order by run_id) from (select run_id,state,failure_code from ouf_ingestion.ing_run) x),'[]'::json),
      'schedules',coalesce((select json_agg(x order by schedule_id) from (select schedule_id,state,publication_enabled,activation_blocked,consumed_publication_id from ouf_ingestion.ing_schedule) x),'[]'::json),
      'handoffs',coalesce((select json_agg(x order by handoff_id) from (select handoff_id,state,attempts from ouf_ingestion.handoff_outbox) x),'[]'::json),
      'quarantine',coalesce((select json_agg(x order by quarantine_id) from (select quarantine_id,state,lifecycle_state,lifecycle_version from ouf_ingestion.ing_quarantine) x),'[]'::json))::text"""
    data = json.loads(runtime.run(['docker', 'exec', 'ouf-postgres', 'psql', '-X', '-qAt', '-v', 'ON_ERROR_STOP=1',
        '-U', 'ouf_ingestion', '-d', 'ouf_ingestion', '-c', 'begin read only; set local statement_timeout=15000; ' + query + '; rollback;']))
    if any(data[k] != 0 for k in ('busyRuns', 'activeSchedules', 'deliverable', 'busyReplays')):
        raise RuntimeError('INTAKE_REFRESHER_REQUIRES_QUIESCENT_QUEUES')
    data['publications'] = json.loads(runtime.run(['docker', 'exec', 'ouf-postgres', 'psql', '-X', '-qAt', '-v', 'ON_ERROR_STOP=1', '-U', 'ouf_onboarding', '-d', 'ouf_onboarding', '-c', "begin read only; set local statement_timeout=15000; select coalesce(json_agg(x order by publication_id),'[]'::json)::text from (select publication_id,source_id,onboarding_version_id,checksum,active from ouf_onboarding.published_configuration where active) x; rollback;"]))
    return data


def context(tenant):
    live = runtime.inspect('ouf-ingestion')
    if not live['State']['Running']:
        raise RuntimeError('INGESTION_NOT_RUNNING')
    settings = runtime.transport_settings(live, tenant)
    mounts = {m['Destination']: m for m in live['Mounts']}
    props = Path(mounts[runtime.PROPERTIES]['Source']).read_bytes()
    if any(runtime.literal_property(props.decode(), k) != v for k, v in settings.items()):
        raise RuntimeError('TRANSPORT_PROPERTIES_DRIFT')
    token_path = Path(mounts[runtime.AUTH]['Source']) / Path(settings['ouf.ingestion.activation.token-file']).relative_to(runtime.AUTH)
    token = token_path.read_text().strip()
    part = token.split('.')[1]
    claims = json.loads(base64.urlsafe_b64decode(part + '=' * (-len(part) % 4)))
    scopes = set(claims.get('scope', '').split())
    if 'ouf.onboarding.configuration.read' not in scopes or claims.get('exp', 0) - time.time() < 90:
        raise RuntimeError('TOKEN_BASELINE_SCOPE_OR_VALIDITY_INVALID')
    stable = {k: live[k] for k in ('Id', 'Image', 'Config', 'HostConfig', 'Mounts')}
    stable['propertiesSha256'] = digest(props)
    return stable, settings, token, scopes


def discovery(settings, token):
    endpoint = settings['ouf.ingestion.activation.gateway-url'].rstrip('/') + '/api/onboarding/v1/runtime/publications?limit=20&after='
    config = 'silent\nshow-error\nmax-time = 5\nmax-filesize = 2097152\nheader = "Authorization: Bearer ' + token + '"\nurl = ' + json.dumps(endpoint) + '\nwrite-out = "\\n%{http_code}"\n'
    raw = runtime.run(['docker', 'run', '--rm', '-i', '--read-only', '--cap-drop', 'ALL', '--security-opt',
        'no-new-privileges', '--network', 'ouf-backend', 'curlimages/curl:8.16.0', '--config', '-'], input=config, timeout=15)
    body, code = raw.rsplit('\n', 1)
    print('INTAKE_REFRESHER_DISCOVERY_HTTP=' + code)
    if code != '200':
        raise RuntimeError('DISCOVERY_NOT_AUTHORIZED')
    page = json.loads(body)
    if not isinstance(page.get('items'), list) or len(page['items']) > 20 or not isinstance(page.get('nextAfter'), str):
        raise RuntimeError('DISCOVERY_PAGE_INVALID')


def main(args):
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    os.umask(0o077)
    meta = ROOT.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o700:
        raise RuntimeError('PRIVATE_ROOT_UNSAFE')
    if RECEIPT.exists() or RECEIPT.is_symlink():
        raise RuntimeError('ADOPTION_RECEIPT_EXISTS_RECONCILE')
    meta = SCRIPT.lstat()
    if not stat.S_ISREG(meta.st_mode) or meta.st_uid != 0 or meta.st_mode & 0o022:
        raise RuntimeError('REFRESHER_METADATA_UNSAFE')
    original = SCRIPT.read_bytes()
    stable, settings, token_before, old_scopes = context(args.tenant)
    before = snapshot()
    if args.mode == 'prepare':
        baseline = private(Path(args.baseline_receipt))
        if baseline.get('status') != 'PASS' or baseline.get('candidateSha256') != digest(original):
            raise RuntimeError('BASELINE_REFRESHER_RECEIPT_MISMATCH')
        if set(SCOPES) & old_scopes:
            raise RuntimeError('INTAKE_SCOPES_ALREADY_PRESENT_RECONCILE')
        candidate = scope_patch(original.decode())
        folder = Path(tempfile.mkdtemp(prefix='intake-refresher-', dir=ROOT))
        path = folder / 'candidate.py'
        write(path, candidate, True)
        save(STATE, dict(status='PASS', tenant=args.tenant, beforeSha256=digest(original), candidateSha256=digest(candidate),
            candidatePath=str(path), runtime=stable, queues=before), True)
        print('R4A_INTAKE_REFRESHER_PREPARE=PASS SCRIPT_UNCHANGED=true TOKEN_UNCHANGED=true RUN_RESUME=false')
        return
    state = private(STATE)
    path = Path(state['candidatePath'])
    if not path.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError('CANDIDATE_PATH_UNSAFE')
    cm = path.lstat()
    if not stat.S_ISREG(cm.st_mode) or cm.st_uid != 0 or stat.S_IMODE(cm.st_mode) != 0o600:
        raise RuntimeError('CANDIDATE_METADATA_UNSAFE')
    candidate = path.read_bytes()
    if (state.get('status') != 'PASS' or state.get('tenant') != args.tenant or state['runtime'] != stable or
            state['queues'] != before or state['beforeSha256'] != digest(original) or
            state['candidateSha256'] != digest(candidate) or candidate != scope_patch(original.decode())):
        raise RuntimeError('PREPARED_CONTEXT_DRIFT')
    start = system('show', SERVICE, '-p', 'ExecStart', '--value')
    if set(re.findall(r'(/[A-Za-z0-9_./-]+\.py)(?:\s|;|$)', start)) != {str(SCRIPT)} or system('show', SERVICE, '-p', 'Type', '--value') != 'oneshot':
        raise RuntimeError('REFRESHER_SERVICE_UNSUPPORTED')
    timers = system('show', SERVICE, '-p', 'TriggeredBy', '--value').split()
    if len(timers) != 1 or not re.fullmatch(r'ouf[-._A-Za-z0-9]*\.timer', timers[0]) or system('show', timers[0], '-p', 'ActiveState', '--value') != 'active':
        raise RuntimeError('REFRESHER_TIMER_UNSUPPORTED')
    print('R4A_INTAKE_REFRESHER_PLAN=PASS MODE=' + args.mode)
    if args.mode == 'plan':
        print('R4A_INTAKE_REFRESHER=PLANNED SCRIPT_UNCHANGED=true TOKEN_UNCHANGED=true RUN_RESUME=false')
        return
    backup = path.parent / 'before.py'
    write(backup, original, True)
    receipt = dict(status='STARTING', backupScript=str(backup), beforeSha256=digest(original), candidateSha256=digest(candidate),
        service=SERVICE, timers=timers, tenant=args.tenant, runResume=False)
    save(RECEIPT, receipt, True)
    installed = False
    try:
        system('stop', timers[0])
        system('stop', SERVICE)
        if SCRIPT.read_bytes() != original or snapshot() != before or context(args.tenant)[0] != stable:
            raise RuntimeError('CONTEXT_CHANGED_BEFORE_INSTALL')
        installed = True
        install(candidate, meta)
        refresh()
        after, settings_after, token_after, new_scopes = context(args.tenant)
        if after != stable or settings_after != settings or token_after == token_before or not old_scopes <= new_scopes or not set(SCOPES) <= new_scopes or SCRIPT.read_bytes() != candidate:
            raise RuntimeError('TOKEN_OR_RUNTIME_READBACK_MISMATCH')
        discovery(settings_after, token_after)
        if snapshot() != before:
            raise RuntimeError('QUEUES_CHANGED_DURING_REFRESH')
        system('start', timers[0])
        if system('show', timers[0], '-p', 'ActiveState', '--value') != 'active':
            raise RuntimeError('TIMER_RESTORE_FAILED')
        receipt['status'] = 'PASS'
        save(RECEIPT, receipt)
        print('R4A_INTAKE_REFRESHER=PASS TOKEN_CHANGED=true OLD_SCOPES_PRESERVED=true INTAKE_SCOPES_PRESENT=true TIMER_RESTORED=true')
        print('R4A_INTAKE_REFRESHER_COMPLETE=PASS RUNTIME_UNCHANGED=true QUEUES_UNCHANGED=true RUN_RESUME=false INTAKE_OWNER_AUTHORIZATION_NOT_YET_PROVEN=true SECRETS_NOT_PRINTED=true')
    except BaseException:
        recovered = True
        try:
            system('stop', timers[0])
            system('stop', SERVICE)
            if installed:
                install(original, meta)
                refresh()
                _, _, _, scopes = context(args.tenant)
                if scopes != old_scopes:
                    raise RuntimeError('ROLLBACK_SCOPES_MISMATCH')
        except BaseException:
            recovered = False
        finally:
            try:
                system('start', timers[0])
                recovered = recovered and SCRIPT.read_bytes() == original and system('show', timers[0], '-p', 'ActiveState', '--value') == 'active'
            except BaseException:
                recovered = False
        receipt['status'] = 'ROLLED_BACK' if recovered else 'MANUAL_RECOVERY_REQUIRED'
        save(RECEIPT, receipt)
        print('R4A_INTAKE_REFRESHER_RECOVERY=' + receipt['status'])
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('prepare', 'plan', 'apply'), required=True)
    parser.add_argument('--tenant', required=True)
    parser.add_argument('--baseline-receipt', default=str(ROOT / 'publication-refresher-adoption.json'))
    try:
        main(parser.parse_args())
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_INTAKE_REFRESHER=BLOCKED CODE=' + code + ' RUN_RESUME=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
