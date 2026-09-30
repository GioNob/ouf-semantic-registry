#!/usr/bin/env python3
"""Create one hash-bound approval challenge and read its card. Never confirm/activate."""
import argparse
import json
import io
from contextlib import redirect_stdout
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import time
import types
import uuid
from datetime import datetime
from urllib.request import HTTPRedirectHandler, build_opener
import r4a_approval_route_inventory as inventory

ROOT = Path('/etc/ouf/deploy-snapshots')
STATE = ROOT / 'cinema-approval-challenge.json'
API = 'https://api.ouf-lab.it'


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def save(value):
    fd, path = tempfile.mkstemp(prefix='.cinema-approval-', dir=ROOT)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(path, STATE)
    finally:
        if os.path.exists(path):
            os.unlink(path)


def human_token(revision):
    git = ['git', '-c', 'safe.directory=/opt/ouf/semantic', '-C', '/opt/ouf/semantic']
    resolved = subprocess.check_output([*git, 'rev-parse', revision + '^{commit}'], stderr=subprocess.DEVNULL).decode().strip()
    if resolved != revision:
        raise RuntimeError('PINNED_REVISION_MISMATCH')
    source = subprocess.check_output([*git, 'show', revision + ':scripts/r4a_cinema_semantic_draft.py'], stderr=subprocess.DEVNULL)
    module = types.ModuleType('cinema_human_login')
    exec(compile(source, 'r4a_cinema_semantic_draft.py', 'exec'), module.__dict__)
    module.SCOPES = {'ouf.onboarding.configuration.write'}
    module.urlopen = build_opener(NoRedirect()).open
    return module.human_token()[0]


def request(method, path, token):
    if method not in {'GET', 'POST'} or path not in {
        inventory.TARGETS['CREATE'][1],
        '/api/trusted-human/v1/approval-challenges/' + path.rsplit('/', 1)[-1]
    }:
        raise RuntimeError('APPROVAL_REQUEST_PATH_INVALID')
    if method == 'POST' and path != inventory.TARGETS['CREATE'][1]:
        raise RuntimeError('APPROVAL_CONFIRM_OR_ACTIVATE_FORBIDDEN')
    if method == 'GET':
        uuid.UUID(path.rsplit('/', 1)[-1])
    if not re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', token):
        raise RuntimeError('HUMAN_TOKEN_FORMAT_INVALID')
    config = ('silent\nshow-error\nmax-time = 20\nmax-filesize = 1048576\n'
              'request = "' + method + '"\nheader = "Accept: application/json"\n'
              'header = "Authorization: Bearer ' + token + '"\n'
              'header = "X-Correlation-ID: r4a-cinema-approval-' + inventory.VERSION + '"\n'
              'url = "' + API + path + '"\nwrite-out = "\\n%{http_code}"\n')
    if method == 'POST':
        config += 'header = "Content-Type: application/json"\ndata = "{}"\n'
    raw = inventory.routes.helper.run(['docker', 'run', '--rm', '-i', '--read-only',
        '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
        '--network', 'ouf-backend', 'curlimages/curl:8.16.0', '--config', '-'],
        input=config, timeout=30)
    body, code = raw.rsplit('\n', 1)
    if code != ('201' if method == 'POST' else '200'):
        raise RuntimeError('APPROVAL_' + method + '_HTTP_' + (code if re.fullmatch(r'\d{3}', code) else 'INVALID'))
    return json.loads(body)


def check_card(card, challenge, configuration=None):
    if (str(card.get('challenge_id')) != challenge or
            card.get('source_id') != inventory.SOURCE or
            str(card.get('onboarding_version_id')) != inventory.VERSION or
            card.get('configuration_hash') != inventory.HASH or
            card.get('status') != 'CREATED' or
            card.get('trustedApprovalRef') != 'ths://approval-challenges/' + challenge):
        raise RuntimeError('APPROVAL_CARD_CONTEXT_MISMATCH')
    expiry = datetime.fromisoformat(str(card.get('expires_at')).replace('Z', '+00:00'))
    if expiry.tzinfo is None or expiry.timestamp() <= time.time() + 30:
        raise RuntimeError('APPROVAL_CHALLENGE_EXPIRED_OR_TOO_SHORT')
    if configuration is not None and card.get('configuration') != configuration:
        raise RuntimeError('APPROVAL_CARD_CONFIGURATION_DRIFT')


def existing_count():
    query = ("begin read only; select count(*) from ouf_onboarding.approval_challenge "
             "where onboarding_version_id='" + inventory.VERSION + "'; rollback;")
    return int(inventory.routes.helper.run(['docker', 'exec', 'ouf-postgres', 'psql', '-X', '-qAt',
        '-v', 'ON_ERROR_STOP=1', '-U', 'ouf_onboarding', '-d', 'ouf_onboarding', '-c', query]))


def verify_routes():
    captured = io.StringIO()
    with redirect_stdout(captured):
        inventory.main()
    output = captured.getvalue()
    print(output, end='', flush=True)
    facts = dict(line.split('=', 1) for line in output.splitlines() if '=' in line)
    for name in ('CREATE', 'CARD', 'CONFIRM', 'ACTIVATE'):
        prefix = 'APPROVAL_' + name + '_1_'
        required = {'ENABLED': 'true', 'UPSTREAM_ONBOARDING': 'true',
                    'UPSTREAM_REFERENCE': 'false', 'SERVICE_REFERENCE': 'false',
                    'PLUGIN_CONFIG_REFERENCE': 'false', 'OIDC_ENABLED': 'true',
                    'OWNER_PATH_PRESERVED': 'true', 'REWRITE_PRESENT': 'false',
                    'EXTRA_MATCH_CONDITIONS': 'false',
                    'PUBLIC_HOST_UNRESTRICTED_OR_EXACT': 'true',
                    'REQUIRED_SCOPES': 'ouf.onboarding.configuration.write'}
        if (facts.get('APPROVAL_' + name + '_ROUTE_COUNT') != '1' or
                any(facts.get(prefix + key) != value for key, value in required.items())):
            raise RuntimeError('APPROVAL_' + name + '_ROUTE_DRIFT')


def main(revision):
    if os.geteuid() != 0 or not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise RuntimeError('ROOT_AND_PINNED_REVISION_REQUIRED')
    meta = ROOT.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o700:
        raise RuntimeError('SNAPSHOT_DIRECTORY_UNSAFE')
    verify_routes()
    live = inventory.routes.helper.inspect('ouf-onboarding')
    before = inventory.routes.helper.candidate_row(inventory.SOURCE, inventory.VERSION, inventory.HASH)
    if before['state'] != 'IN_REVIEW':
        raise RuntimeError('APPROVAL_VERSION_NOT_IN_REVIEW')
    state = None
    if STATE.exists() or STATE.is_symlink():
        meta = STATE.lstat()
        if not stat.S_ISREG(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o600:
            raise RuntimeError('APPROVAL_RECEIPT_UNSAFE')
        state = json.loads(STATE.read_text())
        if (state.get('status') != 'PASS' or state.get('sourceId') != inventory.SOURCE or
                state.get('versionId') != inventory.VERSION or state.get('configurationHash') != inventory.HASH):
            raise RuntimeError('APPROVAL_RECEIPT_RECONCILIATION_REQUIRED_DO_NOT_REPOST')
    elif existing_count() != 0:
        raise RuntimeError('APPROVAL_EXISTING_CHALLENGE_RECONCILIATION_REQUIRED')
    token = human_token(revision)
    verify_routes()
    current_live = inventory.routes.helper.inspect('ouf-onboarding')
    if current_live['Id'] != live['Id'] or current_live['Image'] != live['Image']:
        raise RuntimeError('APPROVAL_OWNER_DRIFT_DURING_LOGIN')
    if inventory.routes.helper.candidate_row(inventory.SOURCE, inventory.VERSION, inventory.HASH) != before:
        raise RuntimeError('APPROVAL_VERSION_DRIFT_BEFORE_POST')
    if state is None:
        if existing_count() != 0:
            raise RuntimeError('APPROVAL_CHALLENGE_CREATED_DURING_LOGIN')
        state = {'status': 'UNVERIFIED_DO_NOT_REPOST', 'sourceId': inventory.SOURCE,
                 'versionId': inventory.VERSION, 'configurationHash': inventory.HASH}
        fd = os.open(STATE, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump(state, stream)
            stream.flush()
            os.fsync(stream.fileno())
        response = request('POST', inventory.TARGETS['CREATE'][1], token)
        challenge = str(uuid.UUID(str(response.get('challenge_id'))))
        state['challengeId'] = challenge
        state['response'] = response
        save(state)
        check_card(response, challenge)
    else:
        challenge = str(uuid.UUID(state['challengeId']))
    card = request('GET', '/api/trusted-human/v1/approval-challenges/' + challenge, token)
    check_card(card, challenge, before['configuration'])
    current_live = inventory.routes.helper.inspect('ouf-onboarding')
    if current_live['Id'] != live['Id'] or current_live['Image'] != live['Image']:
        raise RuntimeError('APPROVAL_OWNER_DRIFT_AFTER_CARD')
    if inventory.routes.helper.candidate_row(inventory.SOURCE, inventory.VERSION, inventory.HASH) != before:
        raise RuntimeError('APPROVAL_VERSION_DRIFT_AFTER_CARD')
    state.update(status='PASS', card=card, sourceApproval=False, sourceActivation=False)
    save(state)
    print('R4A_APPROVAL_CHALLENGE=PASS CHALLENGE_ID=' + challenge)
    print('R4A_APPROVAL_CARD=PASS FROZEN_CONFIGURATION_MATCH=true')
    print('R4A_APPROVAL_EXPIRES_AT=' + str(card['expires_at']))
    print('R4A_APPROVAL_REF=ths://approval-challenges/' + challenge)
    print('R4A_APPROVAL_RECEIPT=' + str(STATE) + ' PRIVATE=true')
    print('R4A_APPROVAL_PREPARE=PASS SOURCE_APPROVAL=false SOURCE_ACTIVATION=false SECRETS_NOT_PRINTED=true')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', required=True)
    try:
        main(parser.parse_args().revision)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_APPROVAL_PREPARE=BLOCKED CODE=' + code + ' SOURCE_APPROVAL=false SOURCE_ACTIVATION=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
