#!/usr/bin/env python3
"""Stage an existing Semantic workload secret after TLS token/introspection acceptance.

No secret rotation, IAM configuration writes, container/route switch or provider call.
"""
import argparse
import base64
import contextlib
import hmac
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import ssl
import stat
import subprocess
import tempfile
import time
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, HTTPRedirectHandler, HTTPSHandler, build_opener


class Blocked(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Blocked('IAM_REDIRECT_FORBIDDEN')


@contextlib.contextmanager
def deadline(seconds):
    previous = signal.getsignal(signal.SIGALRM)
    def expired(signum, frame):
        raise Blocked('IAM_REQUEST_TIMEOUT')
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def unique_object(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise Blocked('IAM_JSON_INVALID')
        result[name] = value
    return result


def https_url(value):
    try:
        parsed = urlsplit(value)
        if (parsed.scheme != 'https' or not parsed.hostname or parsed.username is not None
                or parsed.password is not None or parsed.query or parsed.fragment
                or not parsed.path or parsed.path == '/' or '\\' in value
                or any(c.isspace() or ord(c) < 32 for c in value)
                or (parsed.port is not None and not 1 <= parsed.port <= 65535)):
            raise ValueError()
    except (ValueError, TypeError):
        raise Blocked('IAM_ENDPOINT_INVALID') from None
    return value


def http_json(args, url, form=None):
    https_url(url)
    context = ssl.create_default_context(cafile=args.ca_file)
    opener = build_opener(NoRedirect(), HTTPSHandler(context=context))
    request = Request(url, data=None if form is None else urlencode(form).encode(),
                      headers={'Accept': 'application/json',
                               'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        with deadline(args.timeout), opener.open(request, timeout=args.timeout) as response:
            if response.status != 200:
                raise Blocked('IAM_HTTP_REJECTED')
            if response.headers.get_content_type() != 'application/json':
                raise Blocked('IAM_MEDIA_TYPE_REJECTED')
            raw = response.read(65537)
            if len(raw) > 65536:
                raise Blocked('IAM_RESPONSE_TOO_LARGE')
            value = json.loads(raw, object_pairs_hook=unique_object)
            if not isinstance(value, dict):
                raise Blocked('IAM_JSON_INVALID')
            return value
    except Blocked:
        raise
    except Exception:
        raise Blocked('IAM_REQUEST_FAILED') from None


def workload_module(args):
    path = Path(__file__).resolve().parent / 'provision-keycloak-workload.py'
    spec = importlib.util.spec_from_file_location('proven_workload', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    def run(*values, input_text=None):
        if not values or values[0] != 'get' or input_text is not None:
            raise Blocked('IAM_MUTATION_FORBIDDEN')
        result = subprocess.run(['docker', 'exec', '-i', args.iam_container, args.kcadm_path, *values],
                                capture_output=True, text=True, timeout=20)
        if result.returncode:
            error = (result.stdout + result.stderr).lower()
            raise Blocked('KCADM_SESSION_EXPIRED' if 'session has expired' in error or 'invalid_grant' in error else 'KCADM_READ_FAILED')
        return result.stdout
    module.run = run
    def exact(realm, client):
        rows = module.get_json('get', 'clients', '-r', realm, '-q', 'clientId=' + client, '--fields', 'id,clientId')
        matches = [r for r in rows if r.get('clientId') == client]
        if len(matches) > 1:
            raise Blocked('CLIENT_NOT_UNIQUE')
        return matches[0] if matches else None
    module.exact_client = exact
    return module


def profile(args, workload):
    state = workload.inspect_state(args.realm, args.client_id, args.provider_scope, args.audience, args.tenant)
    ignored = {'BASE_DEFAULT_SCOPES_MISSING', 'BASE_OPTIONAL_SCOPES_MISSING'}
    if not state.get('exists') or any(d not in ignored for d in state['drift']):
        raise Blocked('WORKLOAD_PROFILE_OR_SCOPE_DRIFT')
    return state


def semantic_binding(args):
    result = subprocess.run(['docker', 'inspect', args.semantic_container], capture_output=True, text=True, timeout=20)
    if result.returncode:
        raise Blocked('SEMANTIC_INSPECTION_FAILED')
    rows = json.loads(result.stdout)
    if len(rows) != 1:
        raise Blocked('SEMANTIC_INSPECTION_AMBIGUOUS')
    row = rows[0]
    if row.get('Id') != args.expected_semantic_id or not row.get('State', {}).get('Running'):
        raise Blocked('SEMANTIC_ID_OR_RUNNING_STATE_CHANGED')
    user = row.get('Config', {}).get('User', '')
    if not re.fullmatch(r'[0-9]+:[0-9]+', user):
        raise Blocked('NUMERIC_SEMANTIC_USER_REQUIRED')
    uid, gid = map(int, user.split(':'))
    if uid == 0 or gid == 0:
        raise Blocked('NON_ROOT_SEMANTIC_USER_REQUIRED')
    env = {}
    for item in row.get('Config', {}).get('Env', []):
        name, separator, value = item.partition('=')
        if not separator or name in env:
            raise Blocked('SEMANTIC_ENVIRONMENT_AMBIGUOUS')
        env[name] = value
    if env.get('OUF_IAM_ISSUER') != args.issuer:
        raise Blocked('SEMANTIC_ISSUER_BINDING_CHANGED')
    return {'id': row['Id'], 'uid': uid, 'gid': gid, 'issuer': args.issuer,
            'image': row.get('Image'), 'config': row.get('Config'), 'mounts': row.get('Mounts')}


def trusted_ancestors(parent):
    for ancestor in reversed(parent.parents):
        metadata = ancestor.lstat()
        if not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != 0 or stat.S_IMODE(metadata.st_mode) & 0o022:
            raise Blocked('CREDENTIAL_ANCESTOR_UNSAFE')


def private_target(path, uid, gid):
    if not path.is_absolute() or '..' in path.parts or path.name in ('', '.', '..'):
        raise Blocked('CREDENTIAL_PATH_INVALID')
    parent = path.parent
    trusted_ancestors(parent)
    if parent.exists() or parent.is_symlink():
        metadata = parent.lstat()
        if not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != 0 or stat.S_IMODE(metadata.st_mode) != 0o700:
            raise Blocked('CREDENTIAL_DIRECTORY_UNSAFE')
    elif not parent.parent.is_dir():
        raise Blocked('CREDENTIAL_PARENT_MISSING')
    if path.exists() or path.is_symlink():
        metadata = path.lstat()
        if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != uid or metadata.st_gid != gid
                or stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_nlink != 1 or metadata.st_size > 4096):
            raise Blocked('CREDENTIAL_FILE_UNSAFE')
        return True
    return False


def credential(value):
    if not isinstance(value, str) or not value or len(value.encode()) > 4095 or any(c.isspace() or ord(c) < 32 for c in value):
        raise Blocked('CREDENTIAL_VALUE_INVALID')
    return value


def local_secret(path, uid, gid):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, 'rb') as stream:
        metadata = os.fstat(stream.fileno())
        if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != uid or metadata.st_gid != gid
                or stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_nlink != 1):
            raise Blocked('CREDENTIAL_FILE_UNSAFE')
        raw = stream.read(4097)
    if len(raw) > 4096:
        raise Blocked('CREDENTIAL_VALUE_INVALID')
    return credential(raw.decode().strip())


def claims(args, value, now):
    if not isinstance(value, dict):
        raise Blocked('TOKEN_CLAIMS_INVALID')
    audiences = value.get('aud')
    if isinstance(audiences, str):
        audiences = [audiences]
    expires, issued = value.get('exp'), value.get('iat')
    scope = value.get('scope')
    if (value.get('iss') != args.issuer or not isinstance(audiences, list)
            or args.audience not in audiences or not isinstance(scope, str)
            or args.provider_scope not in scope.split()
            or value.get(args.actor_claim) != 'SERVICE' or value.get(args.tenant_claim) != args.tenant
            or (value.get('client_id') or value.get('azp')) != args.client_id
            or not isinstance(value.get('sub'), str) or not value['sub']
            or value.get('acr') is None or str(value['acr']) == ''
            or type(expires) is not int or not 60 <= expires - now <= 86400
            or type(issued) is not int or not now - 60 <= issued <= now + 30
            or ('nbf' in value and (type(value['nbf']) is not int or value['nbf'] > now + 30))):
        raise Blocked('TOKEN_CLAIMS_INVALID')
    return int(expires - now)


def token_acceptance(args, secret):
    payload = http_json(args, args.token_endpoint, {'grant_type': 'client_credentials',
        'client_id': args.client_id, 'client_secret': secret, 'scope': args.provider_scope})
    token = payload.get('access_token')
    if (payload.get('token_type', '').lower() != 'bearer' or not isinstance(token, str)
            or len(token) > 16384 or not re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', token)
            or type(payload.get('expires_in')) is not int or not 60 <= payload['expires_in'] <= 86400
            or not isinstance(payload.get('scope'), str) or args.provider_scope not in payload['scope'].split()):
        raise Blocked('TOKEN_RESPONSE_INVALID')
    try:
        parts = token.split('.')
        header = json.loads(base64.urlsafe_b64decode(parts[0] + '=' * (-len(parts[0]) % 4)), object_pairs_hook=unique_object)
        decoded = json.loads(base64.urlsafe_b64decode(parts[1] + '=' * (-len(parts[1]) % 4)), object_pairs_hook=unique_object)
        if not isinstance(header, dict) or header.get('alg') != 'RS256' or header.get('crit'):
            raise ValueError()
    except Exception:
        raise Blocked('TOKEN_RESPONSE_INVALID') from None
    ttl = claims(args, decoded, time.time())
    authority = http_json(args, args.introspection_endpoint, {'token': token, 'token_type_hint': 'access_token',
        'client_id': args.client_id, 'client_secret': secret})
    if authority.get('active') is not True:
        raise Blocked('TOKEN_INTROSPECTION_INACTIVE')
    authority_ttl = claims(args, authority, time.time())
    for name in ('iss', 'sub', 'exp', 'iat', args.actor_claim, args.tenant_claim):
        if authority.get(name) != decoded.get(name):
            raise Blocked('TOKEN_INTROSPECTION_CONTEXT_MISMATCH')
    return min(ttl, authority_ttl)


def install_secret(args, secret, binding):
    target = args.credential_file
    existing = private_target(target, binding['uid'], binding['gid'])
    if existing:
        if not hmac.compare_digest(local_secret(target, binding['uid'], binding['gid']), secret):
            raise Blocked('EXISTING_CREDENTIAL_DRIFT')
        return False
    if not target.parent.exists():
        target.parent.mkdir(mode=0o700)
    private_target(target, binding['uid'], binding['gid'])
    descriptor, temporary = tempfile.mkstemp(prefix='.provider-credential-', dir=target.parent)
    try:
        with os.fdopen(descriptor, 'w') as stream:
            os.fchmod(stream.fileno(), 0o600)
            os.fchown(stream.fileno(), binding['uid'], binding['gid'])
            stream.write(secret + '\n'); stream.flush(); os.fsync(stream.fileno())
        # Atomic creation; never replace a concurrently created or different credential.
        os.link(temporary, target, follow_symlinks=False)
    finally:
        Path(temporary).unlink(missing_ok=True)
    private_target(target, binding['uid'], binding['gid'])
    return True


def prepare(args, workload):
    before = profile(args, workload)
    binding = semantic_binding(args)
    existed = private_target(args.credential_file, binding['uid'], binding['gid'])
    metadata = http_json(args, args.issuer.rstrip('/') + '/.well-known/openid-configuration')
    if (metadata.get('issuer') != args.issuer or metadata.get('token_endpoint') != args.token_endpoint
            or metadata.get('introspection_endpoint') != args.introspection_endpoint):
        raise Blocked('OIDC_ENDPOINT_BINDING_MISMATCH')
    if args.mode == 'plan':
        print('SEMANTIC_PROVIDER_CREDENTIAL_PLAN=' + json.dumps({'mode': 'plan', 'existingCredential': existed,
              'fileAction': 'VERIFY_EXISTING' if existed else 'CREATE_PRIVATE_COPY',
              'uid': binding['uid'], 'gid': binding['gid'], 'secretReadRequested': False,
              'tokenRequested': False, 'iamConfigurationWrites': False, 'containerSwitchRequested': False}, sort_keys=True))
        print('SEMANTIC_PROVIDER_CREDENTIAL_PLAN=PASS READ_ONLY=true IAM_TLS_METADATA_PROVEN=true NO_SECRETS_PRINTED=true')
        return
    if args.mode == 'verify' and not existed:
        raise Blocked('CREDENTIAL_FILE_MISSING')
    secret = credential(workload.get_json('get', 'clients/' + before['internalId'] + '/client-secret', '-r', args.realm).get('value'))
    if existed and not hmac.compare_digest(local_secret(args.credential_file, binding['uid'], binding['gid']), secret):
        raise Blocked('EXISTING_CREDENTIAL_DRIFT')
    ttl = token_acceptance(args, secret)
    # Detect configuration/container/credential rotation races before any persistent write.
    if profile(args, workload) != before or semantic_binding(args) != binding:
        raise Blocked('RUNTIME_CHANGED_DURING_PREPARATION')
    current = credential(workload.get_json('get', 'clients/' + before['internalId'] + '/client-secret', '-r', args.realm).get('value'))
    if not hmac.compare_digest(current, secret):
        raise Blocked('IAM_CREDENTIAL_CHANGED_DURING_PREPARATION')
    created = install_secret(args, secret, binding) if args.mode == 'apply' else False
    print('SEMANTIC_PROVIDER_TOKEN_CONTEXT=PASS AUTHORITY_INTROSPECTION_ACTIVE=true TTL_SECONDS=' + str(ttl)
          + ' ACTOR=SERVICE NO_SECRETS_PRINTED=true GATEWAY_ADMISSION_NOT_PROVEN=true')
    print('SEMANTIC_PROVIDER_CREDENTIAL_PREPARE=PASS MODE=' + args.mode + ' PRIVATE_COPY_CREATED=' + str(created).lower()
          + ' SECRET_ROTATED=false IAM_CONFIGURATION_UNCHANGED=true CONTAINERS_UNCHANGED=true ROUTES_UNCHANGED=true'
          + ' NO_POLICY_PUBLICATION=true NO_PROVIDER_CALL=true MOUNT_NOT_INSTALLED=true NO_SECRETS_PRINTED=true')


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('plan', 'apply', 'verify'))
    for option in ('iam-container', 'kcadm-path', 'realm', 'client-id', 'audience', 'tenant',
                   'provider-scope', 'semantic-container', 'expected-semantic-id', 'issuer',
                   'token-endpoint', 'introspection-endpoint'):
        parser.add_argument('--' + option, required=True)
    parser.add_argument('--credential-file', type=Path, required=True)
    parser.add_argument('--actor-claim', default='ouf_actor_type')
    parser.add_argument('--tenant-claim', default='tenant_id')
    parser.add_argument('--ca-file', default=None)
    parser.add_argument('--timeout', type=int, default=15)
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise Blocked('ROOT_REQUIRED')
    for name in ('iam_container', 'realm', 'client_id', 'audience', 'tenant', 'provider_scope', 'semantic_container', 'actor_claim', 'tenant_claim'):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', getattr(args, name)):
            raise Blocked('INSTALLATION_BINDING_INVALID')
    if not re.fullmatch(r'[a-f0-9]{64}', args.expected_semantic_id) or not 1 <= args.timeout <= 30:
        raise Blocked('INSTALLATION_BINDING_INVALID')
    if not args.kcadm_path.startswith('/') or '..' in Path(args.kcadm_path).parts:
        raise Blocked('KCADM_PATH_INVALID')
    for url in (args.issuer, args.token_endpoint, args.introspection_endpoint):
        https_url(url)
    return args


if __name__ == '__main__':
    try:
        arguments = parse_args()
        prepare(arguments, workload_module(arguments))
    except Exception as error:
        code = str(error) if isinstance(error, Blocked) and re.fullmatch(r'[A-Z_]{1,80}', str(error)) else 'UNCLASSIFIED_PREPARATION_FAILURE'
        print('SEMANTIC_PROVIDER_CREDENTIAL_PREPARE=BLOCKED CODE=' + code + ' NO_SECRETS_PRINTED=true DO_NOT_RERUN_BLINDLY=true')
        raise SystemExit(1) from None
