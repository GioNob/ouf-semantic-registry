#!/usr/bin/env python3
"""Read owner tenant bindings, installed token refresher and policy diagnostic counts."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import r4a_prepare_frozen_compatibility_probe as helper
import r4a_managed_identity_release_inventory as owner_helper

CAP = 'ouf.onboarding.configuration.read'


def flatten(value, prefix=''):
    out = {}
    if isinstance(value, dict):
        for key, child in value.items():
            out.update(flatten(child, prefix + ('.' if prefix else '') + key))
    else:
        out[prefix] = value
    return out


def tenant_values(values):
    return [value for key, value in values.items()
            if re.sub(r'[^a-z0-9]', '', key.lower()) == 'oufruntimepublicationstenantid']


def objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from objects(child)


def flag(name, value):
    print(name + '=' + str(bool(value)).lower())


def main():
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    print('R4A_PUBLICATION_BINDINGS_INVENTORY=READ_ONLY', flush=True)
    owner = helper.inspect('ouf-onboarding')
    env = owner_helper.environment(owner)
    raw = env.get('SPRING_APPLICATION_JSON')
    json_values = flatten(json.loads(raw)) if raw else {}
    tenants = tenant_values(json_values)
    print('OWNER_TENANT_JSON_RELAXED_MATCH_COUNT=' + str(len(tenants)))
    flag('OWNER_TENANT_JSON_RELAXED_MATCH_OUF_LAB', len(tenants) == 1 and tenants[0] == 'ouf-lab')
    imports = env.get('SPRING_CONFIG_IMPORT', json_values.get('spring.config.import', ''))
    if not isinstance(imports, str):
        raise RuntimeError('OWNER_CONFIG_IMPORT_LAYOUT_UNSUPPORTED')
    imported_tenants = []
    unsupported = 0
    for item in imports.split(','):
        item = item.strip().removeprefix('optional:')
        if not item:
            continue
        if not item.startswith('file:') or not item.endswith('.properties'):
            unsupported += 1
            continue
        path = owner_helper.host_file(owner, item[5:])
        if path is None or not path.is_file() or path.stat().st_size > 1048576:
            unsupported += 1
            continue
        matches = re.findall(r'^\s*ouf\.runtime-publications\.tenant-id\s*[=:]\s*(.*?)\s*$', path.read_text(), re.MULTILINE)
        imported_tenants.extend(matches)
    print('OWNER_TENANT_IMPORTED_PROPERTY_COUNT=' + str(len(imported_tenants)))
    flag('OWNER_TENANT_IMPORTED_PROPERTY_MATCH', len(imported_tenants) == 1 and imported_tenants[0] == 'ouf-lab')
    print('OWNER_CONFIG_IMPORT_UNSUPPORTED_COUNT=' + str(unsupported))
    command = ' '.join(owner['Config'].get('Entrypoint') or []) + ' ' + ' '.join(owner['Config'].get('Cmd') or [])
    command += ' ' + ' '.join(env.get(k, '') for k in ('JAVA_TOOL_OPTIONS', 'JDK_JAVA_OPTIONS', '_JAVA_OPTIONS'))
    flag('OWNER_TENANT_COMMAND_OVERRIDE_PRESENT', 'ouf.runtime-publications.tenant-id' in command)
    live = helper.inspect('ouf-ingestion')
    settings = helper.transport_settings(live, 'ouf-lab')
    mounts = {m['Destination']: m for m in live['Mounts']}
    properties = Path(mounts[helper.PROPERTIES]['Source']).read_text()
    registry = helper.literal_property(properties, 'ouf.authorization.registry-url')
    token_host = Path(mounts[helper.AUTH]['Source']) / Path(settings['ouf.ingestion.activation.token-file']).relative_to(helper.AUTH)
    token = token_host.read_text().strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', token):
        raise RuntimeError('ING_WORKLOAD_TOKEN_FORMAT_INVALID')
    part = token.split('.')[1]
    claims = json.loads(base64.urlsafe_b64decode(part + '=' * (-len(part) % 4)))
    flag('ING_TOKEN_CONFIG_READ_SCOPE_PRESENT', CAP in str(claims.get('scope', '')).split())
    # Existing authenticated bundle binding; do not invent or bypass an owner URL.
    config = ('silent\nshow-error\nmax-time = 5\nmax-filesize = 2097152\n'
        'header = "Authorization: Bearer ' + token + '"\nurl = ' + json.dumps(registry) + '\nwrite-out = "\\n%{http_code}"\n')
    raw = helper.run(['docker', 'run', '--rm', '-i', '--read-only', '--cap-drop', 'ALL',
        '--security-opt', 'no-new-privileges', '--network', 'ouf-backend', 'curlimages/curl:8.16.0', '--config', '-'], input=config, timeout=15)
    body, code = raw.rsplit('\n', 1)
    print('PUBLICATION_POLICY_BUNDLE_HTTP=' + (code if re.fullmatch(r'\d{3}', code) else 'INVALID'))
    if code == '200':
        bundle = json.loads(body)
        relevant = [item for item in objects(bundle) if item.get('capabilityId') == CAP]
        descriptors = [item for item in relevant if 'riskClass' in item and 'effect' not in item]
        grants = [item for item in relevant if item.get('effect') in {'ALLOW', 'DENY'}]
        service = [item for item in grants if set(item.get('actorTypes') or []) & {'SERVICE', 'SERVICE_IDENTITY'}]
        print('PUBLICATION_POLICY_CONFIG_READ_DESCRIPTOR_COUNT=' + str(len(descriptors)))
        print('PUBLICATION_POLICY_CONFIG_READ_GRANT_COUNT=' + str(len(grants)))
        print('PUBLICATION_POLICY_CONFIG_READ_SERVICE_GRANT_COUNT=' + str(len(service)))
        principals = {claims.get(k) for k in ('sub', 'service_principal_id', 'servicePrincipalId', 'client_id', 'azp')} - {None, ''}
        matching = [item for item in service if isinstance(item.get('subject'), dict)
                    and item['subject'].get('principalRef') in principals]
        print('PUBLICATION_POLICY_CONFIG_READ_SERVICE_PRINCIPAL_DIAGNOSTIC_MATCH_COUNT=' + str(len(matching)))
        flag('PUBLICATION_POLICY_CONFIG_READ_SERVICE_RESOURCE_CONDITIONS_PRESENT', any(item.get('resourceConditions') for item in service))
    units = helper.run(['systemctl', 'list-unit-files', '--type=service', '--no-legend', '--no-pager'])
    names = [line.split()[0] for line in units.splitlines() if line.strip() and re.fullmatch(r'ouf[-._A-Za-z0-9]*\.service', line.split()[0])
             and 'ingestion' in line.split()[0] and 'token' in line.split()[0]]
    print('ING_TOKEN_REFRESH_SERVICE_COUNT=' + str(len(names)))
    if len(names) > 6:
        raise RuntimeError('ING_TOKEN_REFRESH_SERVICE_AMBIGUOUS')
    for index, name in enumerate(names, 1):
        prefix = 'ING_TOKEN_REFRESH_' + str(index) + '_'
        print(prefix + 'SERVICE=' + name)
        start = helper.run(['systemctl', 'show', name, '-p', 'ExecStart', '--value'])
        paths = set(re.findall(r'(/[A-Za-z0-9_./-]+\.py)(?:\s|;|$)', start))
        print(prefix + 'PYTHON_SCRIPT_COUNT=' + str(len(paths)))
        if len(paths) == 1:
            path = Path(next(iter(paths)))
            source = path.read_bytes()
            print(prefix + 'SCRIPT_PATH=' + str(path))
            print(prefix + 'SCRIPT_SHA256=' + hashlib.sha256(source).hexdigest())
            flag(prefix + 'CONFIG_READ_SCOPE_IN_SOURCE', CAP.encode() in source)
            flag(prefix + 'TOKEN_HOST_PATH_IN_SOURCE', str(token_host).encode() in source)
    after = helper.inspect('ouf-onboarding')
    if after['Id'] != owner['Id'] or after['Image'] != owner['Image']:
        raise RuntimeError('OWNER_RUNTIME_DRIFT')
    print('R4A_PUBLICATION_BINDINGS_INVENTORY=COMPLETE LIVE_UNCHANGED=true IAM_UNCHANGED=true SOURCE_ACTIVATION=false SECRETS_NOT_PRINTED=true')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_PUBLICATION_BINDINGS_INVENTORY=BLOCKED CODE=' + code + ' SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
