#!/usr/bin/env python3
"""Inspect the actual flat policy and Keycloak scope bindings without changing IAM."""
import argparse
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import r4a_prepare_frozen_compatibility_probe as helper
import r4a_publication_bindings_inventory as bindings

CAP = bindings.CAP


def flag(name, value):
    print(name + '=' + str(bool(value)).lower())


def valid_now(grant, now):
    def instant(value):
        if not isinstance(value, str):
            raise ValueError('unsupported timestamp')
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None:
            raise ValueError('timezone required')
        return result
    try:
        start, end = grant.get('validFrom'), grant.get('validUntil')
        return instant(start) <= now < instant(end)
    except (ValueError, TypeError):
        return False


def policy_counts(bundle, claims, now):
    relevant = [x for x in bindings.objects(bundle) if x.get('capabilityId') == CAP]
    descriptors = [x for x in relevant if 'allowedActors' in x and 'requiredScope' in x]
    grants = [x for x in relevant if 'grantId' in x and 'servicePrincipalId' in x]
    # Pinned owner IamSecurityConfiguration: text/trim, client_id then azp,
    # ouf_subject then sub. No arbitrary service_principal_id alias.
    def text(value):
        return str(value).strip() if value is not None and str(value).strip() else None
    principal = text(claims.get('client_id')) or text(claims.get('azp'))
    subject_id = text(claims.get('ouf_subject')) or text(claims.get('sub'))
    actor = text(claims.get('ouf_actor_type'))
    matching = [x for x in grants if actor == 'SERVICE' and principal and
                text(x.get('servicePrincipalId')) == principal]
    subject = [x for x in matching if not text(x.get('subjectId')) or x.get('subjectId') == subject_id]
    tenant = [x for x in subject if x.get('tenantId') == claims.get('tenant_id') == 'ouf-lab']
    return {
        'FLAT_DESCRIPTOR_COUNT': len(descriptors),
        'FLAT_DESCRIPTOR_SERVICE_SCOPE_COUNT': sum(isinstance(x['allowedActors'], list) and
            'SERVICE' in x['allowedActors'] and x['requiredScope'] == CAP for x in descriptors),
        'FLAT_GRANT_COUNT': len(grants),
        'SUBJECT_ONLY_GRANT_COUNT': sum(bool(x.get('subjectId')) and not x.get('servicePrincipalId') for x in grants),
        'SERVICE_PRINCIPAL_BOUND_GRANT_COUNT': sum(bool(x.get('servicePrincipalId')) for x in grants),
        'ORGANIZATION_BOUND_GRANT_COUNT': sum(bool(x.get('organizationId')) for x in grants),
        'SERVICE_PRINCIPAL_CLAIM_DIAGNOSTIC_MATCH_COUNT': len(matching),
        'SUBJECT_CLAIM_DIAGNOSTIC_MATCH_COUNT': len(subject),
        'TENANT_DIAGNOSTIC_MATCH_COUNT': len(tenant),
        'CURRENT_VALIDITY_DIAGNOSTIC_MATCH_COUNT': sum(valid_now(x, now) for x in tenant),
    }


def kc(container, realm, resource, extra=()):
    raw = helper.run(['docker', 'exec', container, '/opt/keycloak/bin/kcadm.sh',
                      'get', resource, '-r', realm, *extra], timeout=20)
    return json.loads(raw)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--keycloak-container', default='ouf-keycloak')
    parser.add_argument('--login-keycloak', action='store_true', help='Renew admin session interactively only if the read fails')
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', args.keycloak_container):
        raise RuntimeError('KEYCLOAK_CONTAINER_INVALID')
    print('R4A_PUBLICATION_ACCESS_INVENTORY=READ_ONLY', flush=True)
    live = helper.inspect('ouf-ingestion')
    settings = helper.transport_settings(live, 'ouf-lab')
    mounts = {m['Destination']: m for m in live['Mounts']}
    properties = Path(mounts[helper.PROPERTIES]['Source']).read_text()
    registry = helper.literal_property(properties, 'ouf.authorization.registry-url')
    token_path = Path(mounts[helper.AUTH]['Source']) / Path(settings['ouf.ingestion.activation.token-file']).relative_to(helper.AUTH)
    token = token_path.read_text().strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', token):
        raise RuntimeError('TOKEN_FORMAT_INVALID')
    part = token.split('.')[1]
    claims = json.loads(base64.urlsafe_b64decode(part + '=' * (-len(part) % 4)))
    flag('PUBLICATION_TOKEN_CONFIG_READ_SCOPE_PRESENT', CAP in str(claims.get('scope', '')).split())
    config = ('silent\nshow-error\nmax-time = 5\nmax-filesize = 2097152\n'
              'header = "Authorization: Bearer ' + token + '"\nurl = ' + json.dumps(registry) + '\nwrite-out = "\\n%{http_code}"\n')
    raw = helper.run(['docker', 'run', '--rm', '-i', '--read-only', '--cap-drop', 'ALL',
                     '--security-opt', 'no-new-privileges', '--network', 'ouf-backend',
                     'curlimages/curl:8.16.0', '--config', '-'], input=config, timeout=15)
    body, code = raw.rsplit('\n', 1)
    if code != '200':
        raise RuntimeError('POLICY_BUNDLE_HTTP_NOT_200')
    for name, value in policy_counts(json.loads(body), claims, datetime.now(timezone.utc)).items():
        print('PUBLICATION_POLICY_' + name + '=' + str(value))
    print('PUBLICATION_POLICY_COUNTS_ARE_DIAGNOSTIC=true OWNER_AUTHORIZATION_NOT_PROVEN=true')
    issuer = claims.get('iss', '')
    match = re.search(r'/realms/([A-Za-z0-9_.-]+)$', issuer) if isinstance(issuer, str) else None
    if not match:
        raise RuntimeError('TOKEN_REALM_UNSUPPORTED')
    try:
        try:
            container = helper.inspect(args.keycloak_container)
        except subprocess.SubprocessError:
            raise RuntimeError('KEYCLOAK_CONTAINER_NOT_FOUND')
        if not container['State']['Running']:
            raise RuntimeError('KEYCLOAK_CONTAINER_NOT_RUNNING')
        try:
            helper.run(['docker', 'exec', args.keycloak_container, 'test', '-x', '/opt/keycloak/bin/kcadm.sh'])
        except subprocess.SubprocessError:
            raise RuntimeError('KEYCLOAK_KCADM_NOT_EXECUTABLE')
        try:
            scopes = kc(args.keycloak_container, match[1], 'client-scopes', ('--fields', 'id,name'))
        except subprocess.CalledProcessError as error:
            diagnostic = (error.stderr or '').lower()
            auth_missing = any(x in diagnostic for x in ('no server specified', 'session has expired',
                               'invalid_grant', 'unauthorized', '401', 'failed to refresh token'))
            if not args.login_keycloak or not auth_missing:
                print('PUBLICATION_KEYCLOAK_SESSION_RENEWAL_INDICATED=' + str(auth_missing).lower())
                raise
            if not sys.stdin.isatty() or not sys.stdout.isatty():
                raise RuntimeError('KEYCLOAK_LOGIN_TERMINAL_REQUIRED')
            username = input('Account amministratore Keycloak (realm master): ').strip()
            if not username or username.startswith('-') or any(ord(c) < 32 for c in username):
                raise RuntimeError('KEYCLOAK_ADMIN_USERNAME_INVALID')
            # Password is prompted by kcadm on the terminal, never passed on argv
            # or read/captured by Python. No environment credentials are read.
            result = subprocess.run(['docker', 'exec', '-it', args.keycloak_container,
                '/opt/keycloak/bin/kcadm.sh', 'config', 'credentials',
                '--server', 'http://localhost:8080', '--realm', 'master', '--user', username], timeout=120)
            if result.returncode:
                raise RuntimeError('KEYCLOAK_INTERACTIVE_LOGIN_FAILED')
            scopes = kc(args.keycloak_container, match[1], 'client-scopes', ('--fields', 'id,name'))
        clients = kc(args.keycloak_container, match[1], 'clients', ('-q', 'clientId=ouf-ingestion', '--fields', 'id,clientId'))
        if not isinstance(scopes, list) or not isinstance(clients, list):
            raise RuntimeError('KEYCLOAK_RESPONSE_LAYOUT_UNSUPPORTED')
        selected = [s for s in scopes if s.get('name') == CAP]
        client = [c for c in clients if c.get('clientId') == 'ouf-ingestion']
        print('PUBLICATION_KEYCLOAK_SCOPE_COUNT=' + str(len(selected)))
        print('PUBLICATION_KEYCLOAK_ING_CLIENT_COUNT=' + str(len(client)))
        if len(client) != 1 or not re.fullmatch(r'[A-Za-z0-9-]+', client[0].get('id', '')):
            raise RuntimeError('KEYCLOAK_ING_CLIENT_NOT_UNIQUE')
        prefix = 'clients/' + client[0]['id']
        for kind in ('default', 'optional'):
            values = kc(args.keycloak_container, match[1], prefix + '/' + kind + '-client-scopes', ('--fields', 'id,name'))
            if not isinstance(values, list):
                raise RuntimeError('KEYCLOAK_BINDING_LAYOUT_UNSUPPORTED')
            print('PUBLICATION_KEYCLOAK_' + kind.upper() + '_SCOPE_MATCH_COUNT=' + str(sum(x.get('name') == CAP for x in values)))
        print('PUBLICATION_KEYCLOAK_READ=PASS')
    except subprocess.SubprocessError:
        print('PUBLICATION_KEYCLOAK_READ=UNAVAILABLE KCADM_GET_FAILED=true')
    except RuntimeError as error:
        print('PUBLICATION_KEYCLOAK_READ=UNAVAILABLE CODE=' + str(error))
    if helper.inspect('ouf-ingestion')['Id'] != live['Id']:
        raise RuntimeError('ING_RUNTIME_DRIFT')
    print('R4A_PUBLICATION_ACCESS_INVENTORY=COMPLETE LIVE_UNCHANGED=true IAM_UNCHANGED=true SOURCE_ACTIVATION=false SECRETS_NOT_PRINTED=true')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_PUBLICATION_ACCESS_INVENTORY=BLOCKED CODE=' + code + ' SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
