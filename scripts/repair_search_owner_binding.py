"""Check/repair only an omitted OWNER_KEY_ENV declaration in the live search route.

Uses the existing private Admin key for the exact route GET/PUT, never prints it.
Preserves a private route snapshot and restores on failed write/readback.
"""
import argparse
import copy
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import urllib.error
import urllib.request

ROUTE = 'execute-urban-object-search'
URI = '/internal/capabilities/v1/execute/urban.object.search'
MARKER = 'local OWNER_KEY_ENV = "OUF_UDP_SEARCH_OWNER_KEY"\n'


def canonical(route):
    return {k: v for k, v in route.items() if k not in ('create_time', 'update_time')}


def proposed(route):
    if route.get('id') != ROUTE or route.get('uri') != URI or route.get('methods') != ['POST']:
        raise ValueError('SEARCH_ROUTE_IDENTITY_MISMATCH')
    functions = route.get('plugins', {}).get('serverless-post-function', {}).get('functions')
    if not isinstance(functions, list) or len(functions) != 1 or not isinstance(functions[0], str):
        raise ValueError('ONE_SEARCH_FUNCTION_REQUIRED')
    source = functions[0]
    if re.search(r'\blocal\s+OWNER_KEY_ENV\b', source):
        if source.count(MARKER.strip()) == 1:
            return None
        raise ValueError('EXISTING_OWNER_BINDING_REQUIRES_REVIEW')
    if not source.startswith('return function(conf, ctx)\n'):
        raise ValueError('FUNCTION_HEADER_REQUIRES_REVIEW')
    if source.count('local owner_key = os.getenv(OWNER_KEY_ENV)') != 1:
        raise ValueError('EXPECTED_OWNER_LOOKUP_REQUIRED')
    if not re.search(r'^local DELEGATION_KEY_ENV = "[A-Z][A-Z0-9_]*"$', source, re.M):
        raise ValueError('DELEGATION_BINDING_REQUIRED')
    for fragment in ("'urban.object.search'", "'udp-object-search-owner'", "'X-OUF-UDP-Search-Receipt'"):
        if fragment not in source:
            raise ValueError('EXPECTED_SEARCH_CONTRACT_REQUIRED')
    new = copy.deepcopy(route)
    header = 'return function(conf, ctx)\n'
    new['plugins']['serverless-post-function']['functions'][0] = header + MARKER + source[len(header):]
    check = copy.deepcopy(new)
    check['plugins']['serverless-post-function']['functions'][0] = check['plugins']['serverless-post-function']['functions'][0].replace(MARKER, '', 1)
    if check != route:
        raise ValueError('UNRELATED_ROUTE_CHANGE_DENIED')
    return new


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Admin:
    def __init__(self, address, key):
        ip = ipaddress.ip_address(address)
        if ip.version != 4 or not ip.is_private or ip.is_loopback or ip.is_unspecified:
            raise ValueError('PRIVATE_CONTAINER_IPV4_REQUIRED')
        self.url = 'http://' + str(ip) + ':9180/apisix/admin/routes/' + ROUTE
        self.key = key
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def call(self, method, route=None):
        data = None if route is None else json.dumps(route, separators=(',', ':')).encode()
        request = urllib.request.Request(self.url, method=method, data=data,
                                        headers={'X-API-KEY': self.key, 'Content-Type': 'application/json'})
        with self.opener.open(request, timeout=5) as response:
            body = response.read(2 * 1024 * 1024 + 1)
            if len(body) > 2 * 1024 * 1024:
                raise ValueError('ADMIN_RESPONSE_TOO_LARGE')
            doc = json.loads(body)
            value = doc.get('value') or (doc.get('node') or {}).get('value')
            if not isinstance(value, dict):
                raise ValueError('ADMIN_ROUTE_RESPONSE_REQUIRED')
            return value


def transaction(admin, old, new):
    if canonical(admin.call('GET')) != canonical(old):
        raise ValueError('LIVE_ROUTE_CHANGED_BEFORE_WRITE')
    try:
        admin.call('PUT', canonical(new))
        if canonical(admin.call('GET')) != canonical(new):
            raise ValueError('REPAIR_READBACK_MISMATCH')
    except Exception:
        # Restore only our exact new state. Do not overwrite concurrent changes.
        try:
            current = canonical(admin.call('GET'))
            if current == canonical(old):
                return 'BLOCKED_ORIGINAL_PRESENT'
            if current != canonical(new):
                return 'BLOCKED_CONCURRENT_OR_UNKNOWN_STATE_REVIEW_REQUIRED'
            admin.call('PUT', canonical(old))
            if canonical(admin.call('GET')) == canonical(old):
                return 'BLOCKED_ORIGINAL_RESTORED'
        except Exception:
            pass
        return 'BLOCKED_ROLLBACK_UNVERIFIED_REVIEW_REQUIRED'
    return 'REPAIRED_AND_READBACK_VERIFIED'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--docker', required=True)
    parser.add_argument('--gateway', required=True)
    parser.add_argument('--network', required=True)
    parser.add_argument('--admin-key-file', type=Path, required=True)
    parser.add_argument('--backup-root', type=Path, required=True)
    args = parser.parse_args()
    if os.geteuid() != 0 or not args.docker.startswith('/') or any(not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', x) for x in (args.gateway, args.network)):
        raise SystemExit('SEARCH_OWNER_BINDING=ROOT_AND_EXPLICIT_BINDINGS_REQUIRED')
    stage = 'CONTAINER_BINDING_READ'
    try:
        result = subprocess.run([args.docker, 'inspect', '--type', 'container', args.gateway], capture_output=True, timeout=10, check=True)
        gateway = json.loads(result.stdout)[0]
        if gateway.get('State', {}).get('Running') is not True:
            raise ValueError('GATEWAY_NOT_RUNNING')
        env = dict(item.split('=', 1) for item in gateway['Config']['Env'])
        if not re.fullmatch(r'[a-fA-F0-9]{64}', env.get('OUF_UDP_SEARCH_OWNER_KEY', '')):
            raise ValueError('EXISTING_SEARCH_KEY_REQUIRED')
        address = gateway['NetworkSettings']['Networks'][args.network]['IPAddress']
        stage = 'GENERATED_ENV_DIRECTIVE_READ'
        generated = subprocess.run([args.docker, 'exec', args.gateway, 'cat', '/usr/local/apisix/conf/nginx.conf'], capture_output=True, timeout=10, check=True).stdout.decode('utf-8')
        inherited = bool(re.search(r'^\s*env\s+OUF_UDP_SEARCH_OWNER_KEY(?:\s*=\s*[^;\n]+)?\s*;', generated, re.M))
        stage = 'EXISTING_ADMIN_KEY_READ'
        metadata = args.admin_key_file.lstat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != 0 or stat.S_IMODE(metadata.st_mode) & 0o077:
            raise ValueError('PRIVATE_ROOT_ADMIN_KEY_REQUIRED')
        key = args.admin_key_file.read_text().strip()
        if not key or any(c.isspace() for c in key) or len(key) > 4096:
            raise ValueError('ADMIN_KEY_FORMAT_INVALID')
        admin = Admin(address, key)
        stage = 'SEARCH_ROUTE_GET_AND_EXACT_DELTA_REVIEW'
        old = admin.call('GET')
        new = proposed(old)
        if new is None:
            print('SEARCH_OWNER_BINDING=' + json.dumps({'status': 'ALREADY_DECLARED', 'generatedSearchEnvDirectivePresent': inherited, 'routeChanged': False, 'positiveSearchProven': False}))
            return
        if not inherited:
            print('SEARCH_OWNER_BINDING=MISSING_DECLARATION GENERATED_SEARCH_ENV_DIRECTIVE_ABSENT=true NO_ROUTE_CHANGED=true')
            return
        if not args.apply:
            print('SEARCH_OWNER_BINDING=MISSING_DECLARATION_EXACT_REPAIR_READY NO_ROUTE_CHANGED=true')
            return
        stage = 'PRIVATE_SNAPSHOT'
        root = args.backup_root.lstat()
        if not stat.S_ISDIR(root.st_mode) or root.st_uid != 0 or stat.S_IMODE(root.st_mode) & 0o022:
            raise ValueError('ROOT_BACKUP_DIRECTORY_NOT_WRITABLE_BY_OTHERS_REQUIRED')
        os.umask(0o077)
        folder = Path(tempfile.mkdtemp(prefix='search-owner-binding-', dir=args.backup_root))
        previous = folder / 'previous-route.json'
        with previous.open('x') as output:
            json.dump(old, output)
            output.flush()
            os.fsync(output.fileno())
        stage = 'EXACT_ROUTE_REPAIR_AND_READBACK'
        status = transaction(admin, old, new)
        report = {'status': status, 'snapshotDirectory': str(folder), 'routeId': ROUTE,
                  'onlyAddedOwnerKeyDeclaration': True, 'secretValuesPrinted': False,
                  'configurationSnapshotModified': False, 'containerRestarted': False,
                  'positiveSearchProven': False}
        print('SEARCH_OWNER_BINDING=' + json.dumps(report, sort_keys=True))
        if status != 'REPAIRED_AND_READBACK_VERIFIED':
            raise SystemExit(1)
    except Exception:
        raise SystemExit('SEARCH_OWNER_BINDING=BLOCKED STAGE=' + stage + ' NO_RAW_OUTPUT=true')


if __name__ == '__main__':
    main()
