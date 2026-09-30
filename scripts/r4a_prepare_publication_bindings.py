#!/usr/bin/env python3
"""Prepare inert owner tenant candidate and private scope-refresher patch; inspect policy layout."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import r4a_prepare_managed_identity_candidate as owner
import r4a_prepare_frozen_compatibility_probe as frozen
import r4a_publication_bindings_inventory as bindings

ROOT = Path('/etc/ouf/deploy-snapshots')
STATE = ROOT / 'publication-bindings-prepare.json'
NAME = 'ouf-onboarding-r4a-runtime-tenant-candidate'
REFRESHER = Path('/opt/ouf/ops/refresh-ingestion-policy-token.py')
EXPECTED_SCRIPT = 'af4275509ab66841e77a04e1cf04605228d12e627de51e1c043588eb151f50d0'
CAP = bindings.CAP
SOURCE = 'managed-cinema-8ec8ae90'
VERSION = '68394f42-5c82-4127-a1f3-126516665749'
HASH = 'sha256:2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891'


def scope_patch(source):
    tree = ast.parse(source)
    selected = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        pairs = {key.value: value for key, value in zip(node.keys, node.values)
                 if isinstance(key, ast.Constant) and isinstance(key.value, str)}
        grant = pairs.get('grant_type')
        if isinstance(grant, ast.Constant) and grant.value == 'client_credentials':
            if any(key is None for key in node.keys):
                raise RuntimeError('REFRESHER_GRANT_DICT_UNPACK_UNSUPPORTED')
            selected.append(node)
    if len(selected) != 1:
        raise RuntimeError('REFRESHER_GRANT_DICT_LAYOUT_UNSUPPORTED')
    node = selected[0]
    # AST column offsets are UTF-8 bytes; preserve all source bytes outside the dict.
    raw = source.encode('utf-8')
    lines = raw.splitlines(keepends=True)
    end = sum(map(len, lines[:node.end_lineno - 1])) + node.end_col_offset
    begin = sum(map(len, lines[:node.lineno - 1])) + node.col_offset
    fragment = raw[begin:end]
    if not fragment.endswith(b'}'):
        raise RuntimeError('REFRESHER_GRANT_DICT_BOUNDARY_UNSUPPORTED')
    keys, values = list(node.keys), list(node.values)
    existing_scope = next((index for index, key in enumerate(keys)
                           if isinstance(key, ast.Constant) and key.value == 'scope'), None)
    if existing_scope is None:
        keys.append(ast.Constant(value='scope'))
        values.append(ast.Constant(value=CAP))
    else:
        # Keep the existing scope expression and its evaluation, adding one scope.
        values[existing_scope] = ast.BinOp(left=values[existing_scope], op=ast.Add(), right=ast.Constant(value=' ' + CAP))
    changed = ast.unparse(ast.Dict(keys=keys, values=values)).encode('utf-8')
    output = raw[:begin] + changed + raw[end:]
    ast.parse(output.decode('utf-8'))
    return output


def candidate_matches(candidate, live):
    expected = owner.inventory.environment(live)
    expected['OUF_RUNTIME_PUBLICATIONS_TENANT_ID'] = 'ouf-lab'
    return (candidate['Image'] == live['Image'] and candidate['State']['Status'] == 'created' and
        not candidate['State']['Running'] and owner.inventory.environment(candidate) == expected and
        owner.mounts(candidate) == owner.mounts(live) and candidate['HostConfig'].get('NetworkMode') == 'ouf-backend' and
        set(candidate['NetworkSettings']['Networks']) == {'ouf-backend'} and
        'ouf-onboarding' in candidate['NetworkSettings']['Networks']['ouf-backend'].get('Aliases', []) and
        candidate['HostConfig'].get('RestartPolicy', {}).get('Name') == 'no' and
        candidate['HostConfig'].get('LogConfig') == live['HostConfig'].get('LogConfig') and
        all(candidate['Config'].get(k) == live['Config'].get(k) for k in ('User', 'Entrypoint', 'Cmd', 'WorkingDir', 'ExposedPorts')))


def policy_layout():
    live = frozen.inspect('ouf-ingestion')
    settings = frozen.transport_settings(live, 'ouf-lab')
    mounts = {m['Destination']: m for m in live['Mounts']}
    properties = Path(mounts[frozen.PROPERTIES]['Source']).read_text()
    registry = frozen.literal_property(properties, 'ouf.authorization.registry-url')
    relative = Path(settings['ouf.ingestion.activation.token-file']).relative_to(frozen.AUTH)
    token = (Path(mounts[frozen.AUTH]['Source']) / relative).read_text().strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', token):
        raise RuntimeError('ING_TOKEN_FORMAT_INVALID')
    config = ('silent\nshow-error\nfail\nmax-time = 5\nmax-filesize = 2097152\n'
        'header = "Authorization: Bearer ' + token + '"\nurl = ' + json.dumps(registry) + '\n')
    raw = frozen.run(['docker', 'run', '--rm', '-i', '--read-only', '--cap-drop', 'ALL',
        '--security-opt', 'no-new-privileges', '--network', 'ouf-backend', 'curlimages/curl:8.16.0', '--config', '-'], input=config, timeout=15)
    bundle = json.loads(raw)
    if not isinstance(bundle, dict):
        raise RuntimeError('POLICY_BUNDLE_ROOT_UNSUPPORTED')
    safe = lambda keys: ','.join(sorted(k for k in keys if re.fullmatch(r'[A-Za-z0-9_.-]{1,80}', k)))
    print('PUBLICATION_POLICY_ROOT_FIELDS=' + safe(bundle.keys()))
    matches = [item for item in bindings.objects(bundle) if any(value == CAP for value in item.values())]
    print('PUBLICATION_POLICY_CAPABILITY_STRING_PARENT_COUNT=' + str(len(matches)))
    for index, item in enumerate(matches[:8], 1):
        print('PUBLICATION_POLICY_CAPABILITY_PARENT_' + str(index) + '_FIELDS=' + safe(item.keys()))
    print('PUBLICATION_POLICY_CAPABILITY_LAYOUT_DIAGNOSTIC=true')


def main():
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    os.umask(0o077)
    meta = ROOT.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o700:
        raise RuntimeError('BINDINGS_PRIVATE_ROOT_UNSAFE')
    before = frozen.candidate_row(SOURCE, VERSION, HASH)
    if before['state'] != 'APPROVED':
        raise RuntimeError('SOURCE_NOT_APPROVED')
    live = owner.inventory.inspect('ouf-onboarding')
    image = owner.inventory.inspect(live['Image'])
    owner.runtime_guard(live, image)
    if image['Config'].get('Labels', {}).get('org.opencontainers.image.revision') != owner.REVISION:
        raise RuntimeError('OWNER_IMAGE_REVISION_DRIFT')
    env = owner.inventory.environment(live)
    if 'OUF_RUNTIME_PUBLICATIONS_TENANT_ID' in env:
        raise RuntimeError('OWNER_TENANT_ENV_ALREADY_PRESENT_RECONCILE')
    existing = bindings.tenant_values(bindings.flatten(json.loads(env.get('SPRING_APPLICATION_JSON', '{}'))))
    if existing:
        raise RuntimeError('OWNER_TENANT_JSON_ALREADY_PRESENT_RECONCILE')
    source = REFRESHER.read_bytes()
    if hashlib.sha256(source).hexdigest() != EXPECTED_SCRIPT:
        raise RuntimeError('INSTALLED_REFRESHER_HASH_DRIFT')
    patched = scope_patch(source.decode('utf-8'))
    policy_layout()
    candidate = owner.optional(NAME)
    if STATE.exists() or STATE.is_symlink():
        meta = STATE.lstat()
        if not stat.S_ISREG(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o600:
            raise RuntimeError('BINDINGS_STATE_UNSAFE')
        state = json.loads(STATE.read_text())
        path = Path(state['refresherCandidate'])
        if (state.get('status') != 'PASS' or state.get('old') != owner.stable(live) or candidate is None or
                state.get('sourceId') != SOURCE or state.get('versionId') != VERSION or state.get('configurationHash') != HASH or
                candidate['Id'] != state.get('candidateId') or not candidate_matches(candidate, live) or path.read_bytes() != patched):
            raise RuntimeError('BINDINGS_EXISTING_STATE_DRIFT')
    else:
        if candidate is not None:
            raise RuntimeError('BINDINGS_UNOWNED_CANDIDATE')
        folder = Path(tempfile.mkdtemp(prefix='publication-bindings-', dir=ROOT))
        script = folder / 'refresh-ingestion-policy-token.py'
        script.write_bytes(patched)
        script.chmod(0o600)
        env_path = folder / 'candidate.env'
        created = None
        try:
            env_path.write_text('\n'.join(live['Config']['Env']) + '\nOUF_RUNTIME_PUBLICATIONS_TENANT_ID=ouf-lab\n')
            command = ['docker', 'create', '--name', NAME, '--network', 'ouf-backend', '--network-alias', 'ouf-onboarding',
                '--restart', 'no', '--user', '10003:10003', '--log-driver', 'json-file', '--env-file', str(env_path)]
            for key, value in live['HostConfig']['LogConfig'].get('Config', {}).items():
                command.extend(['--log-opt', key + '=' + value])
            for _, source_path, target, _ in owner.mounts(live):
                command.extend(['--mount', 'type=bind,src=' + source_path + ',dst=' + target + ',readonly'])
            command.append(live['Image'])
            created = owner.inventory.run(command).strip()
            candidate = owner.inventory.inspect(NAME)
            if candidate['Id'] != created or not candidate_matches(candidate, live):
                raise RuntimeError('BINDINGS_CANDIDATE_READBACK_MISMATCH')
            if owner.stable(owner.inventory.inspect('ouf-onboarding')) != owner.stable(live) or frozen.candidate_row(SOURCE, VERSION, HASH) != before:
                raise RuntimeError('BINDINGS_LIVE_OR_SOURCE_DRIFT')
            state = {'status': 'PASS', 'old': owner.stable(live), 'candidateId': created, 'candidateName': NAME,
                'imageId': live['Image'], 'revision': owner.REVISION, 'sourceId': SOURCE, 'versionId': VERSION,
                'configurationHash': HASH, 'refresherCandidate': str(script), 'refresherBeforeSha256': EXPECTED_SCRIPT,
                'refresherCandidateSha256': hashlib.sha256(patched).hexdigest()}
            temporary = folder / 'state.json'
            temporary.write_text(json.dumps(state))
            os.link(temporary, STATE)
        except BaseException:
            if created:
                current = owner.optional(NAME)
                if current is not None and current['Id'] == created and not current['State']['Running']:
                    owner.inventory.run(['docker', 'rm', created])
            raise
        finally:
            env_path.unlink(missing_ok=True)
    if owner.stable(owner.inventory.inspect('ouf-onboarding')) != owner.stable(live) or frozen.candidate_row(SOURCE, VERSION, HASH) != before:
        raise RuntimeError('BINDINGS_FINAL_LIVE_OR_SOURCE_DRIFT')
    print('R4A_PUBLICATION_OWNER_CANDIDATE=PASS STOPPED=true SAME_IMAGE=true TENANT_ENV_PREPARED=true')
    print('R4A_PUBLICATION_TOKEN_REFRESHER_CANDIDATE=PASS INSTALLED_SCRIPT_UNCHANGED=true TOKEN_UNCHANGED=true')
    print('R4A_PUBLICATION_BINDINGS_STATE=' + str(STATE) + ' PRIVATE=true')
    print('R4A_PUBLICATION_BINDINGS_PREPARE=PASS LIVE_UNCHANGED=true IAM_UNCHANGED=true DB_UNCHANGED=true SOURCE_ACTIVATION=false SECRETS_NOT_PRINTED=true')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_PUBLICATION_BINDINGS_PREPARE=BLOCKED CODE=' + code + ' SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
