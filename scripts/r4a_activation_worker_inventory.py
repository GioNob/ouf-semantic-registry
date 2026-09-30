#!/usr/bin/env python3
"""Inspect explicit activation-worker settings; never activate or modify configuration."""
import hashlib
import json
import os
from pathlib import Path
import re
import r4a_prepare_frozen_compatibility_probe as helper


def boolean(value):
    if value is None:
        return 'ABSENT'
    if str(value).strip().lower() in {'true', 'false'}:
        return str(value).strip().upper()
    return 'UNSUPPORTED'


def main():
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    print('R4A_ACTIVATION_WORKER_INVENTORY=READ_ONLY', flush=True)
    row = helper.candidate_row('managed-cinema-8ec8ae90', '68394f42-5c82-4127-a1f3-126516665749',
        'sha256:2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891')
    print('ONBOARDING_STATE=' + row['state'])
    if row['state'] != 'APPROVED':
        raise RuntimeError('VERSION_NOT_APPROVED')
    live = helper.inspect('ouf-ingestion')
    image = helper.inspect(live['Image'], 'image')
    print('ING_WORKER_LIVE_RUNNING=' + str(bool(live['State']['Running'])).lower())
    print('ING_WORKER_REVISION_MATCH=' + str(image['Config'].get('Labels', {}).get('org.opencontainers.image.revision') ==
        '0dfab1e7b2253fd939088259ea61754d6e56706c').lower())
    mounts = [m for m in live['Mounts'] if m['Destination'] == '/run/secrets/ingestion-summary.properties']
    if len(mounts) != 1 or mounts[0]['Type'] != 'bind' or mounts[0]['RW']:
        raise RuntimeError('ING_WORKER_PROPERTIES_MOUNT_UNSUPPORTED')
    text = Path(mounts[0]['Source']).read_text()
    env = dict(v.split('=', 1) for v in live['Config'].get('Env', []) if '=' in v)
    matches = re.findall(r'^\s*ouf\.ingestion\.activation\.enabled\s*[=:]\s*(.*?)\s*$', text, re.MULTILINE)
    print('ING_WORKER_ENABLED_PROPERTY_COUNT=' + str(len(matches)))
    print('ING_WORKER_ENABLED_PROPERTY=' + boolean(matches[0] if len(matches) == 1 else None))
    print('ING_WORKER_ENABLED_ENV=' + boolean(env.get('OUF_INGESTION_ACTIVATION_ENABLED')))
    print('ING_WORKER_SPRING_APPLICATION_JSON_PRESENT=' + str(bool(env.get('SPRING_APPLICATION_JSON'))).lower())
    command = ' '.join(live['Config'].get('Entrypoint') or []) + ' ' + ' '.join(live['Config'].get('Cmd') or [])
    options = ' '.join(env.get(k, '') for k in ('JAVA_TOOL_OPTIONS', 'JDK_JAVA_OPTIONS', '_JAVA_OPTIONS'))
    print('ING_WORKER_ENABLED_COMMAND_OVERRIDE_PRESENT=' + str('ouf.ingestion.activation.enabled' in command + options).lower())
    state = json.loads(Path('/etc/ouf/deploy-snapshots/ingestion-compatibility-release.json').read_text())
    print('ING_WORKER_PROPERTIES_MATCH_RELEASE=' + str(hashlib.sha256(text.encode()).hexdigest() == state.get('properties_sha256')).lower())
    after = helper.inspect('ouf-ingestion')
    if after['Id'] != live['Id'] or after['Image'] != live['Image']:
        raise RuntimeError('ING_WORKER_RUNTIME_DRIFT')
    print('R4A_ACTIVATION_WORKER_INVENTORY=COMPLETE LIVE_UNCHANGED=true SOURCE_ACTIVATION=false SECRETS_NOT_PRINTED=true')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_ACTIVATION_WORKER_INVENTORY=BLOCKED CODE=' + code + ' SOURCE_ACTIVATION=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
