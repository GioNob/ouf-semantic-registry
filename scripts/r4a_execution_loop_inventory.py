#!/usr/bin/env python3
"""Read the execution-loop switch before any HUMAN source activation."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import r4a_prepare_frozen_compatibility_probe as helper
import r4a_managed_identity_release_inventory as owner

ROOT = Path('/etc/ouf/deploy-snapshots')
REVISION = '0dfab1e7b2253fd939088259ea61754d6e56706c'


def private(path):
    meta = path.lstat()
    if not stat.S_ISREG(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o600:
        raise RuntimeError('WORKER_PRIVATE_STATE_UNSAFE')
    return json.loads(path.read_text())


def boolean(value):
    if value is None:
        return 'ABSENT'
    value = str(value).strip().lower()
    return value.upper() if value in {'true', 'false'} else 'UNSUPPORTED'


def facts(live, properties):
    env = owner.environment(live)
    command = ' '.join((live['Config'].get('Entrypoint') or []) + (live['Config'].get('Cmd') or []))
    command += ' ' + ' '.join(env.get(k, '') for k in ('JAVA_TOOL_OPTIONS', 'JDK_JAVA_OPTIONS', '_JAVA_OPTIONS'))
    result = {}
    for loop in ('activation', 'execution'):
        key = 'ouf.ingestion.' + loop + '.enabled'
        values = re.findall(r'^\s*' + re.escape(key) + r'\s*[=:]\s*(.*?)\s*$', properties, re.MULTILINE)
        prefix = 'ING_' + loop.upper() + '_LOOP_'
        result[prefix + 'PROPERTY_COUNT'] = str(len(values))
        result[prefix + 'PROPERTY'] = boolean(values[0] if len(values) == 1 else None)
        value = env.get('OUF_INGESTION_' + loop.upper() + '_ENABLED')
        result[prefix + 'ENV'] = boolean(value)
        override = key in command
        result[prefix + 'COMMAND_OVERRIDE_PRESENT'] = str(override).lower()
        effective = ('UNSUPPORTED' if len(values) > 1 or override or env.get('SPRING_APPLICATION_JSON')
                     else boolean(value) if value is not None else boolean(values[0]) if values else 'FALSE')
        result[prefix + 'EFFECTIVE_DIAGNOSTIC'] = effective
    result['ING_SPRING_APPLICATION_JSON_PRESENT'] = str(bool(env.get('SPRING_APPLICATION_JSON'))).lower()
    return result


def main():
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    print('R4A_EXECUTION_LOOP_INVENTORY=READ_ONLY', flush=True)
    state = private(ROOT / 'ingestion-activation-worker-prepare.json')
    receipt = private(ROOT / 'ingestion-activation-worker-switch.json')
    row = helper.candidate_row('managed-cinema-8ec8ae90', '68394f42-5c82-4127-a1f3-126516665749',
        'sha256:2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891')
    live = helper.inspect('ouf-ingestion')
    image = helper.inspect(live['Image'], 'image')
    if (receipt.get('status') != 'PASS' or receipt.get('workerEnabled') is not True or
        live['Id'] != state.get('candidateId') or live['Image'] != state.get('imageId') or
        not live['State']['Running'] or row['state'] != 'APPROVED' or
        image['Config'].get('Labels', {}).get('org.opencontainers.image.revision') != REVISION):
        raise RuntimeError('WORKER_OR_SOURCE_BASELINE_DRIFT')
    mounts = [m for m in live['Mounts'] if m['Destination'] == helper.PROPERTIES]
    if len(mounts) != 1 or mounts[0]['Type'] != 'bind' or mounts[0]['RW'] or mounts[0]['Source'] != state.get('properties'):
        raise RuntimeError('WORKER_PROPERTIES_MOUNT_DRIFT')
    raw = Path(mounts[0]['Source']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != state.get('propertiesSha256'):
        raise RuntimeError('WORKER_PROPERTIES_HASH_DRIFT')
    values = facts(live, raw.decode('utf-8'))
    print('ONBOARDING_STATE=' + row['state'])
    for key, value in values.items():
        print(key + '=' + value)
    if owner.environment(live) != owner.environment(state['old']):
        raise RuntimeError('WORKER_ENV_DRIFT')
    if (helper.inspect('ouf-ingestion')['Id'] != live['Id'] or
        helper.candidate_row(row['sourceId'], row['onboardingVersionId'], row['configurationHash']) != row or
        Path(mounts[0]['Source']).read_bytes() != raw):
        raise RuntimeError('EXECUTION_INVENTORY_CONTEXT_DRIFT')
    both = all(values['ING_' + name + '_LOOP_EFFECTIVE_DIAGNOSTIC'] == 'TRUE' for name in ('ACTIVATION', 'EXECUTION'))
    print('R4A_EXECUTION_LOOP_SWITCHES_READY=' + str(both).lower() + ' LIVE_BEAN_PRESENCE_NOT_INSPECTED=true')
    print('R4A_EXECUTION_LOOP_INVENTORY=COMPLETE LIVE_UNCHANGED=true SOURCE_ACTIVATION=false SECRETS_NOT_PRINTED=true')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_EXECUTION_LOOP_INVENTORY=BLOCKED CODE=' + code + ' SOURCE_ACTIVATION=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
