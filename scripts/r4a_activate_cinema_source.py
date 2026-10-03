#!/usr/bin/env python3
"""One direct HUMAN activation of the already approved frozen cinema source."""
import argparse
import base64
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import time
import uuid
from types import SimpleNamespace
from urllib.request import build_opener
import r4a_prepare_cinema_approval as approval
import r4a_cinema_semantic_draft as human
import r4a_execution_loop_inventory as switches
import r4a_current_udp_activation_gate as gate
import r4a_enable_activation_worker as worker

ROOT = approval.ROOT
STATE = ROOT / 'cinema-source-activation.json'
SOURCE, VERSION, HASH = approval.inventory.SOURCE, approval.inventory.VERSION, approval.inventory.HASH


def sql(query):
    return approval.inventory.routes.helper.run(['docker', 'exec', 'ouf-postgres', 'psql', '-X', '-qAt',
        '-v', 'ON_ERROR_STOP=1', '-U', 'ouf_onboarding', '-d', 'ouf_onboarding',
        '-c', 'begin read only; ' + query + '; rollback;'])


def check_card(card, challenge, configuration):
    if (str(card.get('challenge_id')) != challenge or card.get('source_id') != SOURCE or
        str(card.get('onboarding_version_id')) != VERSION or card.get('configuration_hash') != HASH or
        card.get('status') != 'CONFIRMED' or card.get('configuration') != configuration or
        card.get('trustedApprovalRef') != 'ths://approval-challenges/' + challenge):
        raise RuntimeError('CONFIRMED_APPROVAL_CARD_MISMATCH')
    # expires_at governs confirmation of CREATED challenges, not activation
    # of a version already approved through a CONFIRMED challenge.


def empty():
    worker.queues_empty()
    count = worker.rollout.sql("select count(*) from ouf_ingestion.handoff_outbox where state in ('READY','DELIVERING','FAILED_RETRYABLE')")
    if count != '0':
        raise RuntimeError('PENDING_HANDOFFS_REVIEW_REQUIRED')


def context():
    confirmation = switches.private(ROOT / 'cinema-approval-confirmation.json')
    state = switches.private(ROOT / 'ingestion-execution-loop-prepare.json')
    receipt = switches.private(ROOT / 'ingestion-execution-loop-switch.json')
    challenge = str(uuid.UUID(confirmation['challengeId']))
    if (confirmation.get('status') != 'PASS' or confirmation.get('sourceApproval') is not True or
        confirmation.get('sourceId') != SOURCE or confirmation.get('versionId') != VERSION or
        confirmation.get('configurationHash') != HASH or state.get('status') != 'PASS' or
        receipt.get('status') != 'PASS' or receipt.get('executionEnabled') is not True or
        receipt.get('activationEnabled') is not True or receipt.get('configurationHash') != HASH):
        raise RuntimeError('APPROVAL_OR_EXECUTION_RECEIPT_NOT_PASS')
    live = worker.prepare.probe.inspect('ouf-ingestion')
    image = worker.prepare.probe.inspect(live['Image'], 'image')
    if (live['Id'] != state.get('candidateId') or receipt.get('candidateId') != live['Id'] or
        live['Image'] != state.get('imageId') or not live['State']['Running'] or
        image['Config'].get('Labels', {}).get('org.opencontainers.image.revision') != worker.prepare.REVISION):
        raise RuntimeError('EXECUTION_RUNTIME_DRIFT')
    worker.prepare.guard(live, image)
    path = Path(next(m['Source'] for m in live['Mounts'] if m['Destination'] == worker.prepare.probe.PROPERTIES))
    raw = path.read_bytes()
    if str(path) != state.get('properties') or hashlib.sha256(raw).hexdigest() != state.get('propertiesSha256'):
        raise RuntimeError('EXECUTION_PROPERTIES_DRIFT')
    facts = switches.facts(live, raw.decode())
    if (any(facts['ING_' + name + '_LOOP_EFFECTIVE_DIAGNOSTIC'] != 'TRUE' for name in ('ACTIVATION', 'EXECUTION')) or
        worker.prepare.environment(live) != worker.prepare.environment(state['old'])):
        raise RuntimeError('BOTH_RUNTIME_SWITCHES_NOT_PROVEN')
    settings = worker.rollout.tokens_fresh(live, 'ouf-lab')
    auth = Path(next(m['Source'] for m in live['Mounts'] if m['Destination'] == worker.prepare.probe.AUTH))
    token_path = auth / Path(settings['ouf.ingestion.activation.token-file']).relative_to(worker.prepare.probe.AUTH)
    token, claims = worker.access.token_claims(token_path)
    if worker.access.prepare.CAP not in str(claims.get('scope', '')).split():
        raise RuntimeError('CONFIG_READ_SCOPE_MISSING')
    worker.access.discovery(settings, token)
    empty()
    worker.rollout.ready(1)
    row = worker.prepare.probe.candidate_row(SOURCE, VERSION, HASH)
    if row['state'] != 'APPROVED':
        raise RuntimeError('SOURCE_NOT_APPROVED')
    if sql("select count(*) from ouf_onboarding.published_configuration where source_id='" + SOURCE + "'") != '0':
        raise RuntimeError('SOURCE_HAS_PUBLICATION_RECONCILE')
    compatible = sql("select compatible from ouf_onboarding.consumer_compatibility_attestation where onboarding_version_id='" + VERSION + "' and consumer='INGESTION_RUNTIME' and configuration_hash='" + HASH + "' order by created_at desc,attestation_id desc limit 1")
    if compatible != 't':
        raise RuntimeError('CURRENT_INGESTION_ATTESTATION_NOT_COMPATIBLE')
    if sql("select count(*) from ouf_onboarding.approval_decision where challenge_id='" + challenge + "' and onboarding_version_id='" + VERSION + "' and decision='APPROVE' and target_hash='" + HASH + "' and actor_subject='" + human.SUBJECT + "'") != '1':
        raise RuntimeError('APPROVAL_DECISION_MISMATCH')
    return challenge, row, live['Id'], live['Image']


def udp_gate():
    gate.main(SimpleNamespace(source=SOURCE, version=VERSION, expected_hash=HASH, tenant_id='ouf-lab'))


def save(value, exclusive=False):
    if exclusive:
        fd = os.open(STATE, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream)
            stream.flush()
            os.fsync(stream.fileno())
    else:
        previous = approval.STATE
        try:
            approval.STATE = STATE
            approval.save(value)
        finally:
            approval.STATE = previous
    worker.access.sync_directory(ROOT)


def post_activate(challenge, token):
    challenge = str(uuid.UUID(challenge))
    if not re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', token):
        raise RuntimeError('HUMAN_TOKEN_FORMAT_INVALID')
    config = ('silent\nshow-error\nmax-time = 30\nmax-filesize = 1048576\nrequest = "POST"\n'
        'header = "Authorization: Bearer ' + token + '"\nheader = "Content-Type: application/json"\ndata = "{}"\n'
        'header = "X-Correlation-ID: r4a-cinema-activate-' + challenge + '"\n'
        'url = "' + approval.API + '/api/trusted-human/v1/approval-challenges/' + challenge + '/activate"\n'
        'write-out = "\\n%{http_code}"\n')
    raw = worker.prepare.probe.run(['docker', 'run', '--rm', '-i', '--read-only', '--cap-drop', 'ALL',
        '--security-opt', 'no-new-privileges', '--network', 'ouf-backend', 'curlimages/curl:8.16.0', '--config', '-'], input=config, timeout=40)
    body, code = raw.rsplit('\n', 1)
    if code != '200':
        raise RuntimeError('ACTIVATION_HTTP_' + (code if re.fullmatch(r'\d{3}', code) else 'INVALID') + '_DO_NOT_REPOST')
    return json.loads(body)


def readback(response, configuration):
    rows = json.loads(sql("select coalesce(json_agg(t),'[]'::json) from (select publication_id,source_id,onboarding_version_id,bundle_version,bundle,checksum,active from ouf_onboarding.published_configuration where source_id='" + SOURCE + "') t"))
    version = json.loads(sql("select row_to_json(t) from (select state,configuration_hash,configuration from ouf_onboarding.onboarding_version where onboarding_version_id='" + VERSION + "') t"))
    if len(rows) != 1:
        raise RuntimeError('ACTIVATION_PUBLICATION_COUNT_MISMATCH_DO_NOT_REPOST')
    item = rows[0]
    if (not item['active'] or version['state'] != 'ACTIVE' or version['configuration_hash'] != HASH or
        version['configuration'] != configuration or item['onboarding_version_id'] != VERSION or
        item['source_id'] != SOURCE or any(str(item[k]) != str(response.get(k)) for k in
        ('publication_id', 'source_id', 'onboarding_version_id', 'bundle_version', 'checksum')) or
        item['bundle'] != response.get('bundle') or item['bundle'].get('configurationHash') != HASH or
        item['bundle'].get('status') != 'ACTIVE'):
        raise RuntimeError('ACTIVATION_OWNER_READBACK_MISMATCH_DO_NOT_REPOST')
    return item


def main(mode):
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    meta = ROOT.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o700:
        raise RuntimeError('PRIVATE_SNAPSHOT_DIRECTORY_UNSAFE')
    if STATE.exists() or STATE.is_symlink():
        raise RuntimeError('ACTIVATION_RECEIPT_EXISTS_RECONCILE_DO_NOT_REPOST')
    before = context()
    approval.verify_routes()
    udp_gate()
    print('R4A_SOURCE_ACTIVATION_PREFLIGHT=PASS SOURCE_STATE=APPROVED BOTH_LOOPS_ENABLED=true SOURCE_ACTIVATION=false')
    if mode == 'preflight':
        return
    human.SCOPES = {'ouf.onboarding.configuration.write'}
    human.urlopen = build_opener(approval.NoRedirect()).open
    token, _ = human.human_token()
    challenge, row, _, _ = before
    card = approval.request('GET', '/api/trusted-human/v1/approval-challenges/' + challenge, token)
    check_card(card, challenge, row['configuration'])
    print('SOURCE=' + SOURCE + '\nVERSION=' + VERSION + '\nCONFIGURATION_HASH=' + HASH, flush=True)
    print('Attivazione della fonte: i worker potranno avviare ingestion e consegna a UDP.', flush=True)
    expected = 'ATTIVO ' + SOURCE
    if input('Per attivare digita ' + expected + '\n> ').strip() != expected:
        print('R4A_SOURCE_ACTIVATION=CANCELLED SOURCE_ACTIVATION=false')
        return
    part = token.split('.')[1]
    claims = json.loads(base64.urlsafe_b64decode(part + '=' * (-len(part) % 4)))
    if claims['exp'] < time.time() + 60:
        raise RuntimeError('HUMAN_TOKEN_TOO_SHORT_RELOGIN')
    if context() != before:
        raise RuntimeError('ACTIVATION_CONTEXT_DRIFT_BEFORE_POST')
    approval.verify_routes()
    udp_gate()
    check_card(approval.request('GET', '/api/trusted-human/v1/approval-challenges/' + challenge, token), challenge, row['configuration'])
    receipt = dict(status='UNVERIFIED_DO_NOT_REPOST', sourceId=SOURCE, versionId=VERSION,
        challengeId=challenge, configurationHash=HASH, activationAttempted=True)
    save(receipt, exclusive=True)
    response = post_activate(challenge, token)
    receipt['response'] = response
    save(receipt)
    publication = readback(response, row['configuration'])
    receipt.update(status='PASS', sourceState='ACTIVE', sourceActivation=True,
        publicationId=publication['publication_id'], checksum=publication['checksum'])
    save(receipt)
    print('R4A_SOURCE_ACTIVATION=PASS STATE=ACTIVE FROZEN_HASH_UNCHANGED=true')
    print('R4A_SOURCE_PUBLICATION_ID=' + str(publication['publication_id']))
    print('R4A_SOURCE_ACTIVATION_RECEIPT=' + str(STATE) + ' PRIVATE=true')
    print('R4A_SOURCE_ACTIVATION_COMPLETE=PASS INGESTION_RESULT_NOT_YET_VERIFIED=true SECRETS_NOT_PRINTED=true')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('preflight', 'activate'))
    try:
        main(parser.parse_args().mode)
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_SOURCE_ACTIVATION=BLOCKED CODE=' + code + ' DO_NOT_REPOST_IF_RECEIPT_EXISTS=true SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
