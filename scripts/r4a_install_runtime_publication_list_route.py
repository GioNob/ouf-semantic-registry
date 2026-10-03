#!/usr/bin/env python3
"""Plan/add the missing exact GET discovery route, preserving existing route security."""
import argparse
import copy
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import r4a_approval_route_inventory as inventory

ROOT = Path('/etc/ouf/deploy-snapshots')
RECEIPT = ROOT / 'runtime-publication-list-route.json'
ID = 'r4a-onboarding-runtime-publications-list'
PATH = '/api/onboarding/v1/runtime/publications'
ACTIVE = PATH + '/managed-cinema-8ec8ae90/active'


def api(key, method, path, payload=None, accepted=('200',)):
    config = ('silent\nshow-error\nmax-time = 15\nmax-filesize = 10485760\n'
              'header = "X-API-KEY: ' + key + '"\nrequest = "' + method + '"\n'
              'url = "http://127.0.0.1:9180/apisix/admin/' + path + '"\n'
              'write-out = "\\n%{http_code}"\n')
    if payload is not None:
        data = json.dumps(payload, separators=(',', ':'))
        config += 'header = "Content-Type: application/json"\ndata = ' + json.dumps(data) + '\n'
    raw = inventory.routes.helper.run(['docker', 'run', '--rm', '-i', '--read-only',
        '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
        '--network', 'container:ouf-apisix', 'curlimages/curl:8.16.0', '--config', '-'], input=config, timeout=30)
    body, code = raw.rsplit('\n', 1)
    if code not in accepted:
        raise RuntimeError('PUBLICATION_ROUTE_ADMIN_HTTP_' + (code if re.fullmatch(r'\d{3}', code) else 'INVALID'))
    return json.loads(body), code


def template(values):
    selected = inventory.candidates(values, 'GET', ACTIVE)
    if len(selected) != 1:
        raise RuntimeError('PUBLICATION_ACTIVE_TEMPLATE_NOT_UNIQUE')
    route = selected[0]
    oidc = route.get('plugins', {}).get('openid-connect', {})
    if (route.get('status', 1) != 1 or route.get('upstream', {}).get('nodes') != {'ouf-onboarding:8080': 1} or
            any(route.get(k) for k in ('upstream_id', 'service_id', 'plugin_config_id', 'vars', 'filter_func', 'remote_addr', 'remote_addrs')) or
            route.get('plugins', {}).get('proxy-rewrite') or not oidc or oidc.get('_meta', {}).get('disable', False) or
            oidc.get('required_scopes') != ['ouf.onboarding.configuration.read']):
        raise RuntimeError('PUBLICATION_ACTIVE_TEMPLATE_UNSUPPORTED')
    new = copy.deepcopy(route)
    for name in ('id', 'create_time', 'update_time', 'uri', 'uris', 'name', 'desc'):
        new.pop(name, None)
    new.update(uri=PATH, methods=['GET'], name=ID, desc='Exact runtime-publication discovery; SERVICE owner authorization retained')
    return new


def comparable(route):
    result = copy.deepcopy(route)
    for name in ('id', 'create_time', 'update_time'):
        result.pop(name, None)
    return result


def tenant_from_json(environment):
    flattened = {}
    def flatten(value, prefix=''):
        if isinstance(value, dict):
            for k, child in value.items():
                flatten(child, prefix + ('.' if prefix else '') + k)
        else:
            if prefix in flattened:
                raise RuntimeError('OWNER_SPRING_JSON_AMBIGUOUS')
            flattened[prefix] = value
    text = environment.get('SPRING_APPLICATION_JSON')
    if text:
        flatten(json.loads(text))
    return flattened.get('ouf.runtime-publications.tenant-id')


def main(mode):
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    meta = ROOT.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o700:
        raise RuntimeError('PUBLICATION_ROUTE_SNAPSHOT_DIRECTORY_UNSAFE')
    row = inventory.routes.helper.candidate_row(inventory.SOURCE, inventory.VERSION, inventory.HASH)
    if row['state'] != 'APPROVED':
        raise RuntimeError('PUBLICATION_SOURCE_NOT_APPROVED')
    owner = inventory.routes.helper.inspect('ouf-onboarding')
    image = inventory.routes.helper.inspect(owner['Image'], 'image')
    if not owner['State']['Running'] or image['Config'].get('Labels', {}).get('org.opencontainers.image.revision') != inventory.OWNER:
        raise RuntimeError('PUBLICATION_OWNER_REVISION_DRIFT')
    env = dict(v.split('=', 1) for v in owner['Config'].get('Env', []) if '=' in v)
    tenant = tenant_from_json(env)
    inventory.flag('PUBLICATION_OWNER_TENANT_SPRING_JSON_PRESENT', tenant is not None)
    inventory.flag('PUBLICATION_OWNER_TENANT_SPRING_JSON_MATCH', tenant == 'ouf-lab')
    apisix = inventory.routes.helper.inspect('ouf-apisix')
    if not apisix['State']['Running']:
        raise RuntimeError('APISIX_NOT_RUNNING')
    key = inventory.routes.admin_key(inventory.routes.mounted_config(apisix).read_text())
    raw, _ = api(key, 'GET', 'routes')
    values = inventory.routes.route_values(raw)
    desired = template(values)
    if RECEIPT.exists() or RECEIPT.is_symlink():
        raise RuntimeError('PUBLICATION_ROUTE_RECEIPT_PRESENT_RECONCILE_DO_NOT_REPUT')
    if inventory.candidates(values, 'GET', PATH):
        raise RuntimeError('PUBLICATION_LIST_ROUTE_ALREADY_PRESENT_RECONCILE')
    _, status = api(key, 'GET', 'routes/' + ID, accepted=('200', '404'))
    if status != '404':
        raise RuntimeError('PUBLICATION_LIST_ROUTE_ID_ALREADY_OWNED')
    print('R4A_PUBLICATION_LIST_ROUTE_PLAN=PASS MODE=' + mode + ' REQUIRED_SCOPE=ouf.onboarding.configuration.read', flush=True)
    if mode == 'plan':
        print('R4A_PUBLICATION_LIST_ROUTE=PLANNED LIVE_UNCHANGED=true SOURCE_ACTIVATION=false')
        return
    snapshot = Path(tempfile.mkdtemp(prefix='publication-list-route-', dir=ROOT)) / 'routes-before.json'
    snapshot.write_text(json.dumps(raw))
    snapshot.chmod(0o600)
    receipt = {'status': 'UNVERIFIED_DO_NOT_REPUT', 'routeId': ID, 'beforeSnapshot': str(snapshot), 'desired': desired}
    fd = os.open(RECEIPT, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(receipt, stream)
        stream.flush()
        os.fsync(stream.fileno())
    api(key, 'PUT', 'routes/' + ID, desired, accepted=('200', '201'))
    after, _ = api(key, 'GET', 'routes')
    matches = inventory.candidates(inventory.routes.route_values(after), 'GET', PATH)
    if len(matches) != 1 or comparable(matches[0]) != desired:
        raise RuntimeError('PUBLICATION_LIST_ROUTE_READBACK_MISMATCH')
    if inventory.routes.helper.candidate_row(inventory.SOURCE, inventory.VERSION, inventory.HASH) != row:
        raise RuntimeError('PUBLICATION_SOURCE_DRIFT_AFTER_ROUTE')
    receipt['status'] = 'PASS'
    fd, temporary = tempfile.mkstemp(prefix='.publication-list-route-', dir=ROOT)
    with os.fdopen(fd, 'w') as stream:
        json.dump(receipt, stream)
    os.replace(temporary, RECEIPT)
    print('R4A_PUBLICATION_LIST_ROUTE=PASS ROUTE_ID=' + ID)
    print('R4A_PUBLICATION_LIST_ROUTE_SNAPSHOT=' + str(snapshot) + ' PRIVATE=true')
    print('R4A_PUBLICATION_LIST_ROUTE_COMPLETE=PASS IAM_UNCHANGED=true WORKER_ENABLED=false SOURCE_ACTIVATION=false SECRETS_NOT_PRINTED=true')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('plan', 'apply'))
    try:
        main(parser.parse_args().mode)
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_PUBLICATION_LIST_ROUTE=BLOCKED CODE=' + code + ' SOURCE_ACTIVATION=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
