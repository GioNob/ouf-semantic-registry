#!/usr/bin/env python3
"""HUMAN review and publish of the exact confirmed cinema RDF draft via Gateway.

Pins both the source RDF and the imported revision; checks the full trusted
approval card before the HUMAN decision. No Onboarding configuration is made.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import types
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

REPO = Path('/opt/ouf/semantic')
ROOT = Path('/etc/ouf/deploy-snapshots')
STATE = ROOT / 'r4a-cinema-semantic-draft.json'
EXPECTED_ID = 'https://api.ouf-lab.it/semantic/cinema'
EXPECTED_ASSET = '8ec8ae90-808a-4d9e-907c-d56de119e376'
EXPECTED_PROFILE = '4462692b-9c85-446b-b6fd-779f01eab64d'
EXPECTED_REVISION = '51706bed-81e4-4306-aca1-70119821727d'
EXPECTED_RDF_HASH = '4340986102db6e47345dd8157734d9db83b928edd94485f1b9a5b9e81c497a2e'


class Blocked(RuntimeError):
    pass


def git(safe, object_name):
    return subprocess.check_output([*safe, 'show', object_name], stderr=subprocess.DEVNULL)


def update(state):
    fd, temporary = tempfile.mkstemp(prefix='r4a-cinema-state-', dir=ROOT)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(state, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, STATE)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def call(url, token, method='GET', payload=None, headers=None):
    request_headers = {'Accept': 'application/json', 'Authorization': 'Bearer ' + token}
    if payload is not None:
        request_headers['Content-Type'] = 'application/json'
    request_headers.update(headers or {})
    request = Request(url, method=method, data=payload, headers=request_headers)
    try:
        with urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read(1048576))
    except HTTPError as error:
        error.read(1048576)
        return error.code, {}


def checked(status, body, expected, label):
    if status != expected or not isinstance(body, dict):
        raise Blocked(label + '_HTTP_' + str(status))
    return body


def card_exact(card, state, turtle):
    snap = card.get('interchangeSnapshot') or {}
    if (str(card.get('revision_id')) != EXPECTED_REVISION
            or card.get('artifact_id') != state['artifactId']
            or card.get('semantic_id') != EXPECTED_ID
            or card.get('artifact_type') != 'ONTOLOGY'
            or card.get('semantic_version') != '1.0.0'
            or card.get('owner_ref') != 'b93d8cf6-cd14-4ee6-91d7-84cd76c4f500'
            or card.get('authority_ref') != 'ouf-lab-netcup-01'
            or card.get('revision_no') != 1
            or snap.get('mediaType') != 'text/turtle'
            or snap.get('contentHash') != EXPECTED_RDF_HASH
            or snap.get('content') != turtle.decode('utf-8')
            or not isinstance(snap.get('statementCount'), int)
            or snap['statementCount'] < 10):
        raise Blocked('HUMAN_REVIEW_CARD_MISMATCH')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', required=True)
    args = parser.parse_args()
    if os.geteuid() != 0 or not re.fullmatch('[0-9a-f]{40}', args.revision):
        raise Blocked('ROOT_AND_PINNED_REVISION_REQUIRED')
    meta = STATE.lstat()
    if not stat.S_ISREG(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o600:
        raise Blocked('DRAFT_STATE_UNSAFE')
    state = json.loads(STATE.read_text())
    if (state.get('semanticId') != EXPECTED_ID or state.get('assetId') != EXPECTED_ASSET
            or state.get('profileId') != EXPECTED_PROFILE
            or state.get('revisionId') != EXPECTED_REVISION
            or state.get('rdfSha256') != EXPECTED_RDF_HASH
            or not re.fullmatch('[0-9a-f-]{36}', str(state.get('artifactId')))):
        raise Blocked('DRAFT_STATE_MISMATCH')
    safe = ['git', '-c', 'safe.directory=' + str(REPO), '-C', str(REPO)]
    if subprocess.check_output([*safe, 'rev-parse', args.revision + '^{commit}'],
                               stderr=subprocess.DEVNULL).decode().strip() != args.revision:
        raise Blocked('PINNED_SOURCE_UNAVAILABLE')
    turtle = git(safe, args.revision + ':docs/r4a_cinema_draft.ttl')
    if hashlib.sha256(turtle).hexdigest() != EXPECTED_RDF_HASH:
        raise Blocked('REVIEWED_RDF_SOURCE_CHANGED')
    helper = types.ModuleType('r4a_cinema_semantic_draft')
    exec(compile(git(safe, args.revision + ':scripts/r4a_cinema_semantic_draft.py'),
                 'r4a_cinema_semantic_draft.py', 'exec'), helper.__dict__)
    helper.SCOPES = {'ouf.semantic.review.prepare', 'ouf.semantic.approval.request',
                     'ouf.semantic.review', 'ouf.semantic.approve',
                     'ouf.semantic.publish', 'ouf.semantic.search'}
    token, _ = helper.human_token()
    api = helper.API
    revision = EXPECTED_REVISION
    if not state.get('challengeId') and not state.get('publicationSetId'):
        status, validation = call(api + '/api/semantic/v1/revisions/' + revision + ':validate',
                                  token, 'POST', b'')
        validation = checked(status, validation, 200, 'VALIDATION')
        content_hash = validation.get('validated_content_hash')
        if (validation.get('status') != 'PASS' or validation.get('error_count') != 0
                or not isinstance(content_hash, str)
                or not re.fullmatch('[0-9a-f]{64}', content_hash)):
            raise Blocked('SEMANTIC_VALIDATION_NOT_GREEN')
        status, challenge = call(api + '/api/semantic/v1/approval-challenges', token, 'POST',
            json.dumps({'revisionId': revision, 'contentHash': content_hash}).encode())
        challenge = checked(status, challenge, 201, 'CHALLENGE')
        if (challenge.get('status') != 'OPEN' or challenge.get('targetContentHash') != content_hash
                or not re.fullmatch('[0-9a-f-]{36}', str(challenge.get('challengeId')))):
            raise Blocked('APPROVAL_CHALLENGE_MISMATCH')
        state['challengeId'] = challenge['challengeId']
        state['targetContentHash'] = content_hash
        update(state)
        card_exact(challenge, state, turtle)
    if not state.get('publicationSetId'):
        challenge_id = state['challengeId']
        status, card = call(api + '/api/trusted-human/v1/semantic-approval-challenges/' +
                            challenge_id, token)
        card = checked(status, card, 200, 'HUMAN_CARD')
        card_exact(card, state, turtle)
        if card.get('target_content_hash') != state['targetContentHash']:
            raise Blocked('HUMAN_CARD_HASH_MISMATCH')
        if not state.get('decisionId'):
            if card.get('status') != 'OPEN':
                raise Blocked('HUMAN_CHALLENGE_NOT_OPEN')
            print('EXACT_HUMAN_CARD_VERIFIED=true RDF_SHA256=' + EXPECTED_RDF_HASH,
                  flush=True)
            status, decision = call(api + '/api/trusted-human/v1/semantic-approval-challenges/' +
                challenge_id + '/decision', token, 'POST', b'{"decision":"APPROVED"}')
            decision = checked(status, decision, 200, 'HUMAN_DECISION')
            if decision.get('decision') != 'APPROVED' or not decision.get('decisionId'):
                raise Blocked('HUMAN_DECISION_MISMATCH')
            state['decisionId'] = decision['decisionId']
            update(state)
        status, published = call(api + '/api/trusted-human/v1/semantic-approval-challenges/' +
            challenge_id + '/publish', token, 'POST',
            json.dumps({'approvalDecisionId': state['decisionId'],
                        'contentHash': state['targetContentHash']}).encode(),
            {'Idempotency-Key': 'r4a-cinema-' + revision})
        published = checked(status, published, 200, 'HUMAN_PUBLICATION')
        if (published.get('status') != 'PUBLISHED'
                or not re.fullmatch('[0-9a-f-]{36}', str(published.get('publicationSetId')))
                or not re.fullmatch('[0-9a-f]{64}', str(published.get('manifestHash')))):
            raise Blocked('HUMAN_PUBLICATION_MISMATCH')
        state['publicationSetId'] = published['publicationSetId']
        state['manifestHash'] = published['manifestHash']
        update(state)
    status, found = call(api + '/api/semantic/v1/search?' +
                         urlencode({'q': EXPECTED_ID, 'status': 'ACTIVE', 'limit': 20}), token)
    if status != 200 or not isinstance(found, list) or not any(
            r.get('semantic_id') == EXPECTED_ID and
            str(r.get('revision_id')) == EXPECTED_REVISION and
            str(r.get('artifact_id')) == state['artifactId'] for r in found):
        raise Blocked('ACTIVE_SEARCH_EXACT_REVISION_NOT_FOUND')
    print('SEMANTIC_HUMAN_PUBLICATION=PASS')
    print('SEMANTIC_ID=' + EXPECTED_ID)
    print('REVISION_ID=' + revision)
    print('PUBLICATION_SET_ID=' + state['publicationSetId'])
    print('MANIFEST_HASH=' + state['manifestHash'])
    print('RDF_SHA256=' + EXPECTED_RDF_HASH)
    print('ONBOARDING_CONFIGURATION_UNCHANGED=true TOKEN_NOT_PRINTED=true')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError, TypeError, IndexError,
            subprocess.CalledProcessError) as exc:
        code = str(exc) if isinstance(exc, Blocked) else type(exc).__name__
        print('CINEMA_SEMANTIC_PUBLICATION_BLOCKED=' + code, file=sys.stderr)
        raise SystemExit(1)
