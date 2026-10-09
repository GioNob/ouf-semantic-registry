#!/usr/bin/env python3
"""Import and validate the real cinema asset's reviewable RDF DRAFT via Gateway.

No approval challenge, HUMAN decision, Semantic publication, or Onboarding
configuration is created here. The OIDC device flow keeps tokens in memory.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

REPO = Path('/opt/ouf/semantic')
ROOT = Path('/etc/ouf/deploy-snapshots')
STATE = ROOT / 'r4a-cinema-semantic-draft.json'
ISSUER = 'https://auth.ouf-lab.it/realms/ouf'
API = 'https://api.ouf-lab.it'
CLIENT = 'ouf-human-admin'
SUBJECT = 'b93d8cf6-cd14-4ee6-91d7-84cd76c4f500'
SCOPES = {'ouf.semantic.propose', 'ouf.semantic.review.prepare'}
SEMANTIC_ID = 'https://api.ouf-lab.it/semantic/cinema'
ASSET_ID = '8ec8ae90-808a-4d9e-907c-d56de119e376'
PROFILE_ID = '4462692b-9c85-446b-b6fd-779f01eab64d'


class Blocked(RuntimeError):
    pass


def request(url, method='GET', data=None, token=None, content_type=None):
    headers = {'Accept': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if content_type:
        headers['Content-Type'] = content_type
    try:
        with urlopen(Request(url, method=method, data=data, headers=headers), timeout=30) as response:
            return response.status, response.read(1048576)
    except HTTPError as error:
        return error.code, error.read(1048576)


def form(url, values):
    status, body = request(url, 'POST', urlencode(values).encode(),
                           content_type='application/x-www-form-urlencoded')
    try:
        return status, json.loads(body)
    except ValueError:
        return status, {}


def human_token():
    status, raw = request(ISSUER + '/.well-known/openid-configuration')
    if status != 200:
        raise Blocked('OIDC_DISCOVERY_UNAVAILABLE')
    doc = json.loads(raw)
    device = doc.get('device_authorization_endpoint', '')
    endpoint = doc.get('token_endpoint', '')
    if (doc.get('issuer') != ISSUER or
            not device.startswith(ISSUER + '/protocol/openid-connect/') or
            not endpoint.startswith(ISSUER + '/protocol/openid-connect/')):
        raise Blocked('OIDC_DISCOVERY_MISMATCH')
    status, auth = form(device, {'client_id': CLIENT,
                                 'scope': 'openid ' + ' '.join(sorted(SCOPES))})
    if status != 200 or not all(auth.get(k) for k in
                                 ('device_code', 'user_code', 'verification_uri', 'expires_in')):
        raise Blocked('DEVICE_AUTHORIZATION_FAILED')
    if not auth['verification_uri'].startswith('https://auth.ouf-lab.it/'):
        raise Blocked('VERIFICATION_URI_UNEXPECTED')
    print('OPEN_IN_BROWSER=' + auth['verification_uri'], flush=True)
    print('ENTER_DEVICE_CODE=' + auth['user_code'], flush=True)
    delay = max(5, min(30, int(auth.get('interval', 5))))
    deadline = time.monotonic() + min(600, int(auth['expires_in']))
    while time.monotonic() < deadline:
        time.sleep(delay)
        status, result = form(endpoint, {'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
                                         'client_id': CLIENT, 'device_code': auth['device_code']})
        if status == 200:
            token = result.get('access_token')
            break
        if result.get('error') == 'slow_down':
            delay = min(30, delay + 5)
        elif result.get('error') != 'authorization_pending':
            raise Blocked('DEVICE_LOGIN_FAILED')
    else:
        raise Blocked('DEVICE_LOGIN_EXPIRED')
    if not isinstance(token, str) or len(token) > 16384 or token.count('.') != 2:
        raise Blocked('HUMAN_TOKEN_INVALID')
    part = token.split('.')[1]
    claims = json.loads(base64.urlsafe_b64decode(part + '=' * (-len(part) % 4)))
    audience = claims.get('aud', [])
    if isinstance(audience, str):
        audience = [audience]
    if not (claims.get('iss') == ISSUER and claims.get('azp') == CLIENT
            and claims.get('sub') == SUBJECT and claims.get('preferred_username') == 'ouf-admin'
            and claims.get('ouf_actor_type') in ('HUMAN', 'HUMAN_USER')
            and claims.get('tenant_id') == 'ouf-lab' and 'ouf-api-gateway' in audience
            and SCOPES <= set(str(claims.get('scope', '')).split())
            and isinstance(claims.get('exp'), int) and claims['exp'] > time.time() + 60):
        raise Blocked('HUMAN_TOKEN_SCOPE_OR_IDENTITY_MISMATCH')
    return token, claims['sub']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', required=True)
    args = parser.parse_args()
    if os.geteuid() != 0 or not re.fullmatch('[0-9a-f]{40}', args.revision):
        raise Blocked('ROOT_AND_PINNED_REVISION_REQUIRED')
    meta = ROOT.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o700:
        raise Blocked('SNAPSHOT_DIRECTORY_UNSAFE')
    safe = ['git', '-c', 'safe.directory=' + str(REPO), '-C', str(REPO)]
    if subprocess.check_output([*safe, 'rev-parse', args.revision + '^{commit}'],
                               stderr=subprocess.DEVNULL).decode().strip() != args.revision:
        raise Blocked('PINNED_SOURCE_UNAVAILABLE')
    turtle = subprocess.check_output([*safe, 'show',
        args.revision + ':docs/r4a_cinema_draft.ttl'], stderr=subprocess.DEVNULL)
    source = b'profile://managed-files/' + ASSET_ID.encode() + b'/profiles/' + PROFILE_ID.encode()
    if (not 0 < len(turtle) <= 65536 or source not in turtle
            or SEMANTIC_ID.encode() not in turtle
            or turtle.count(b'owl:Ontology') != 1
            or b'cinema:Cinema' not in turtle or b'cinema:nome' not in turtle
            or b'cinema:indirizzo' not in turtle):
        raise Blocked('REVIEW_SOURCE_UNEXPECTED')
    rdf_hash = hashlib.sha256(turtle).hexdigest()
    if STATE.exists():
        state = json.loads(STATE.read_text())
        if state.get('semanticId') != SEMANTIC_ID or state.get('rdfSha256') != rdf_hash:
            raise Blocked('EXISTING_DRAFT_STATE_MISMATCH')
        revision_id = state['revisionId']
        print('SEMANTIC_DRAFT_ALREADY_RECORDED=true')
    else:
        token, subject = human_token()
        query = urlencode({'semanticId': SEMANTIC_ID, 'artifactType': 'ONTOLOGY',
                           'namespace': SEMANTIC_ID + '#', 'localName': 'CinemaOntology',
                           'ownerRef': subject, 'authorityRef': 'ouf-lab-netcup-01',
                           'semanticVersion': '1.0.0'})
        status, raw = request(API + '/api/semantic/v1/imports?' + query, 'POST', turtle,
                              token, 'text/turtle')
        if status != 200:
            raise Blocked('RDF_IMPORT_HTTP_' + str(status))
        imported = json.loads(raw)
        if (imported.get('semanticId') != SEMANTIC_ID or imported.get('status') != 'DRAFT'
                or imported.get('contentHash') != rdf_hash
                or not imported.get('artifactId') or not imported.get('revisionId')):
            raise Blocked('RDF_IMPORT_RESPONSE_MISMATCH')
        state = {'semanticId': SEMANTIC_ID, 'assetId': ASSET_ID, 'profileId': PROFILE_ID,
                 'rdfSha256': rdf_hash, 'artifactId': str(imported['artifactId']),
                 'revisionId': str(imported['revisionId'])}
        os.umask(0o077)
        fd = os.open(STATE, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump(state, stream)
        revision_id = state['revisionId']
        print('SEMANTIC_DRAFT_IMPORTED=true')
    # A fresh device login is only necessary when resuming a previous import.
    if 'token' not in locals():
        token, _ = human_token()
    status, raw = request(API + '/api/semantic/v1/revisions/' + revision_id + ':validate',
                          'POST', b'', token)
    if status != 200:
        raise Blocked('SEMANTIC_VALIDATION_HTTP_' + str(status))
    validation = json.loads(raw)
    print('ASSET_ID=' + ASSET_ID)
    print('PROFILE_ID=' + PROFILE_ID)
    print('SEMANTIC_ID=' + SEMANTIC_ID)
    print('ARTIFACT_ID=' + state['artifactId'])
    print('REVISION_ID=' + revision_id)
    print('RDF_SHA256=' + rdf_hash)
    print('VALIDATION=' + str(validation.get('status')) + ' ERRORS=' +
          str(validation.get('error_count')) + ' WARNINGS=' + str(validation.get('warning_count')))
    print('DRAFT_STATE=' + str(STATE))
    print('NO_APPROVAL_OR_PUBLICATION=true TOKEN_NOT_PRINTED=true')
    if validation.get('status') != 'PASS' or validation.get('error_count') != 0:
        raise Blocked('SEMANTIC_DRAFT_VALIDATION_FAILED')


if __name__ == '__main__':
    try:
        main()
    except (Blocked, OSError, ValueError, KeyError, TypeError, IndexError,
            subprocess.CalledProcessError) as exc:
        code = str(exc) if isinstance(exc, Blocked) else type(exc).__name__
        print('CINEMA_SEMANTIC_DRAFT_BLOCKED=' + code, file=sys.stderr)
        raise SystemExit(1)
