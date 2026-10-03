#!/usr/bin/env python3
"""Read source-independent UDP lake/IAM bindings; never perform storage/intake writes."""
import argparse
import json
import os
import re
from urllib.parse import urlsplit
import r4a_prepare_frozen_compatibility_probe as runtime

REVISION = 'edaba2bff18a2aaf52d1180f21f0e68984cc3437'
RETENTIONS = {'OPERATIONAL', 'AUDIT', 'ARCHIVAL', 'LEGAL_HOLD', 'DERIVED_REBUILDABLE'}
LABELS = {'OPEN', 'ANONYMOUS', 'PERSONAL', 'SENSITIVE', 'RESTRICTED'}


def flag(name, value):
    print(name + '=' + str(bool(value)).lower())


def environment(live):
    pairs = [x.split('=', 1) for x in live['Config'].get('Env', []) if '=' in x]
    names = [x[0] for x in pairs]
    if len(set(names)) != len(names):
        raise RuntimeError('DUPLICATE_ENV_BINDING')
    return dict(pairs)


def supported_url(value):
    try:
        uri = urlsplit(value)
        return uri.scheme in {'http', 'https'} and bool(uri.hostname) and not any(c.isspace() for c in value) and uri.username is None and uri.password is None and not uri.query and not uri.fragment
    except ValueError:
        return False


def facts(live, tenant):
    env = environment(live)
    command = ' '.join((live['Config'].get('Entrypoint') or []) + (live['Config'].get('Cmd') or []))
    command += ' ' + ' '.join(env.get(k, '') for k in ('JAVA_TOOL_OPTIONS', 'JDK_JAVA_OPTIONS', '_JAVA_OPTIONS'))
    # Exact release application.yml binds the profile variables below. Other
    # config sources must be resolved before these diagnostics imply effective values.
    overrides = {
        'SPRING_JSON_PRESENT': bool(env.get('SPRING_APPLICATION_JSON')),
        'SPRING_EXTERNAL_CONFIG_ENV_PRESENT': any(env.get(k) for k in ('SPRING_CONFIG_IMPORT', 'SPRING_CONFIG_LOCATION', 'SPRING_CONFIG_ADDITIONAL_LOCATION', 'SPRING_PROFILES_ACTIVE', 'SPRING_PROFILES_INCLUDE')),
        'COMMAND_CONFIG_OVERRIDE_PRESENT': any(x in command for x in ('ouf.', 'spring.config', 'spring.profiles', 'spring.application.json')),
        'EXTERNAL_CONFIG_MOUNT_PRESENT': any(re.search(r'\.(?:properties|ya?ml)$', m['Destination']) or m['Destination'].rstrip('/').endswith('/config') for m in live.get('Mounts', [])),
        'DIRECT_RELAXED_PROPERTY_ENV_PRESENT': any(k.startswith(('OUF_UDP_LAKE_', 'OUF_UDP_LAKE_S3_')) and k not in {'OUF_UDP_LAKE_REQUIRED', 'OUF_UDP_LAKE_MAINTENANCE_WORKER_ID', 'OUF_UDP_LAKE_MAINTENANCE_POLL_MS', 'OUF_UDP_LAKE_MAINTENANCE_INITIAL_DELAY_MS', 'OUF_UDP_LAKE_MAINTENANCE_LEASE_SECONDS', 'OUF_UDP_LAKE_SHADOW_WORKER_ID', 'OUF_UDP_LAKE_SHADOW_POLL_MS', 'OUF_UDP_LAKE_SHADOW_INITIAL_DELAY_MS', 'OUF_UDP_LAKE_SHADOW_LEASE_SECONDS'} for k in env),
    }
    days = env.get('OUF_UDP_RAW_RETENTION_DAYS', '0').strip()
    endpoint = env.get('OUF_UDP_S3_ENDPOINT', '').strip()
    bucket = env.get('OUF_UDP_S3_BUCKET', '').strip()
    checks = {
        'TENANT_MATCH': env.get('OUF_UDP_TENANT_ID', '').strip() == tenant,
        'RAW_RETENTION_DAYS_VALID': bool(re.fullmatch(r'[0-9]{1,5}', days)) and 1 <= int(days) <= 36500,
        'RAW_RETENTION_CLASS_VALID': env.get('OUF_UDP_RAW_RETENTION_CLASS', '').strip() in RETENTIONS,
        'RAW_ACCESS_LABEL_VALID': env.get('OUF_UDP_RAW_ACCESS_LABEL', '').strip() in LABELS,
        'S3_BUCKET_PRESENT': bool(bucket) and '${' not in bucket,
        'S3_ENDPOINT_SUPPORTED_OR_AWS_DEFAULT': not endpoint or supported_url(endpoint),
        'S3_REGION_PRESENT_OR_DEFAULT': bool(env.get('OUF_UDP_S3_REGION', 'us-east-1').strip()),
        'S3_PATH_STYLE_BOOLEAN_VALID': env.get('OUF_UDP_S3_PATH_STYLE', 'false').strip().lower() in {'true', 'false'},
        'IAM_ENABLED': env.get('OUF_UDP_IAM_ENABLED', 'false').strip().lower() == 'true',
        'IAM_ISSUER_SUPPORTED': supported_url(env.get('OUF_UDP_IAM_ISSUER', '')),
        'IAM_AUDIENCE_PRESENT': bool(env.get('OUF_UDP_IAM_AUDIENCE', '').strip()),
    }
    credentials = bool(env.get('AWS_ACCESS_KEY_ID')) and bool(env.get('AWS_SECRET_ACCESS_KEY'))
    return overrides, checks, credentials


def main(tenant):
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    if not re.fullmatch(r'[A-Za-z0-9._-]{1,160}', tenant):
        raise RuntimeError('TENANT_INVALID')
    print('R4A_RUNTIME_LAKE_PREREQUISITES=READ_ONLY', flush=True)
    live = runtime.inspect('ouf-udp')
    image = runtime.inspect(live['Image'], 'image')
    if not live['State']['Running'] or image['Config'].get('Labels', {}).get('org.opencontainers.image.revision') != REVISION:
        raise RuntimeError('UDP_RUNTIME_REVISION_DRIFT')
    overrides, checks, credentials = facts(live, tenant)
    for name, value in overrides.items():
        flag('LAKE_' + name, value)
    for name, value in checks.items():
        flag('LAKE_ENV_' + name, value)
    flag('LAKE_AWS_CREDENTIAL_PAIR_ENV_PRESENT', credentials)
    # Environment presence never proves SDK credential resolution or S3 permissions.
    flag('LAKE_BINDINGS_READY_DIAGNOSTIC', not any(overrides.values()) and all(checks.values()))
    print('LAKE_INVALID_ENV_CHECKS=' + (','.join(k for k, v in checks.items() if not v) or 'NONE'))
    after = runtime.inspect('ouf-udp')
    if any(after[k] != live[k] for k in ('Id', 'Image', 'Config', 'HostConfig', 'Mounts')):
        raise RuntimeError('UDP_CONTEXT_CHANGED_DURING_READ')
    print('R4A_RUNTIME_LAKE_PREREQUISITES=COMPLETE READ_ONLY=true LIVE_UNCHANGED=true S3_AUTHORIZATION_NOT_PROVEN=true INTAKE_OWNER_AUTHORIZATION_NOT_PROVEN=true INTAKE_POST=false RUN_RESUME=false SECRETS_NOT_PRINTED=true')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tenant', required=True)
    try:
        main(parser.parse_args().tenant)
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_RUNTIME_LAKE_PREREQUISITES=BLOCKED CODE=' + code + ' READ_ONLY=true RUN_RESUME=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
