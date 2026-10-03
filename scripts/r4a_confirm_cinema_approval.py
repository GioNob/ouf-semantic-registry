#!/usr/bin/env python3
"""Direct HUMAN confirmation after terminal card review. Never activate the source."""
import argparse
import json
import os
import stat
import uuid
import r4a_prepare_cinema_approval as prepare
import r4a_review_cinema_approval as review

STATE = prepare.ROOT / 'cinema-approval-confirmation.json'


def post_confirm(challenge, token):
    challenge = str(uuid.UUID(challenge))
    # Reuse the token-format guard without allowing arbitrary URLs or redirects.
    if not prepare.re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', token):
        raise RuntimeError('HUMAN_TOKEN_FORMAT_INVALID')
    config = ('silent\nshow-error\nmax-time = 20\nmax-filesize = 1048576\nrequest = "POST"\n'
              'header = "Authorization: Bearer ' + token + '"\n'
              'header = "Content-Type: application/json"\ndata = "{}"\n'
              'header = "X-Correlation-ID: r4a-cinema-confirm-' + challenge + '"\n'
              'url = "' + prepare.API + '/api/trusted-human/v1/approval-challenges/' + challenge + '/confirm"\n'
              'write-out = "\\n%{http_code}"\n')
    raw = prepare.inventory.routes.helper.run(['docker', 'run', '--rm', '-i', '--read-only',
        '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges', '--network', 'ouf-backend',
        'curlimages/curl:8.16.0', '--config', '-'], input=config, timeout=30)
    body, code = raw.rsplit('\n', 1)
    if code != '200':
        raise RuntimeError('APPROVAL_CONFIRM_HTTP_' + (code if prepare.re.fullmatch(r'\d{3}', code) else 'INVALID'))
    return json.loads(body)


def write_receipt(value, exclusive=False):
    if exclusive:
        fd = os.open(STATE, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream)
            stream.flush()
            os.fsync(stream.fileno())
    else:
        previous = prepare.STATE
        try:
            prepare.STATE = STATE
            prepare.save(value)
        finally:
            prepare.STATE = previous


def main(revision, challenge):
    challenge = str(uuid.UUID(challenge))
    if os.geteuid() != 0 or not prepare.re.fullmatch(r'[0-9a-f]{40}', revision):
        raise RuntimeError('ROOT_AND_PINNED_REVISION_REQUIRED')
    meta = prepare.ROOT.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o700:
        raise RuntimeError('SNAPSHOT_DIRECTORY_UNSAFE')
    if STATE.exists() or STATE.is_symlink():
        raise RuntimeError('CONFIRMATION_RECEIPT_EXISTS_RECONCILE_DO_NOT_REPOST')
    review.main()
    recorded = json.loads(prepare.STATE.read_text())
    if recorded.get('challengeId') != challenge:
        raise RuntimeError('REVIEW_CHALLENGE_MISMATCH')
    prepare.verify_routes()
    live = prepare.inventory.routes.helper.inspect('ouf-onboarding')
    before = prepare.inventory.routes.helper.candidate_row(prepare.inventory.SOURCE, prepare.inventory.VERSION, prepare.inventory.HASH)
    token = prepare.human_token(revision)
    card = prepare.request('GET', '/api/trusted-human/v1/approval-challenges/' + challenge, token)
    prepare.check_card(card, challenge, before['configuration'])
    print('REVIEW_DIRECT_HUMAN_CARD=' + challenge, flush=True)
    print(json.dumps(review.review_sections(card['configuration']), ensure_ascii=False, sort_keys=True, indent=2), flush=True)
    print('HASH=' + prepare.inventory.HASH, flush=True)
    print('Questa azione approva la configurazione; non attiva la fonte.', flush=True)
    expected = 'APPROVO ' + challenge
    answer = input('Per confermare digita esattamente: ' + expected + '\n> ')
    if answer.strip() != expected:
        print('R4A_HUMAN_APPROVAL=CANCELLED SOURCE_APPROVAL=false SOURCE_ACTIVATION=false')
        return
    prepare.check_card(card, challenge, before['configuration'])
    prepare.verify_routes()
    current = prepare.inventory.routes.helper.inspect('ouf-onboarding')
    if current['Id'] != live['Id'] or current['Image'] != live['Image'] or prepare.inventory.routes.helper.candidate_row(prepare.inventory.SOURCE, prepare.inventory.VERSION, prepare.inventory.HASH) != before:
        raise RuntimeError('APPROVAL_CONTEXT_DRIFT_BEFORE_CONFIRM')
    receipt = {'status': 'UNVERIFIED_DO_NOT_REPOST', 'challengeId': challenge,
               'sourceId': prepare.inventory.SOURCE, 'versionId': prepare.inventory.VERSION,
               'configurationHash': prepare.inventory.HASH, 'sourceActivation': False}
    write_receipt(receipt, exclusive=True)
    response = post_confirm(challenge, token)
    if (response.get('state') != 'APPROVED' or response.get('configuration_hash') != prepare.inventory.HASH or
            str(response.get('onboarding_version_id')) != prepare.inventory.VERSION or
            response.get('source_id') != prepare.inventory.SOURCE or response.get('configuration') != before['configuration']):
        raise RuntimeError('APPROVAL_CONFIRM_RESPONSE_MISMATCH_DO_NOT_REPOST')
    after = prepare.inventory.routes.helper.candidate_row(prepare.inventory.SOURCE, prepare.inventory.VERSION, prepare.inventory.HASH)
    if after['state'] != 'APPROVED' or after['configuration'] != before['configuration']:
        raise RuntimeError('APPROVAL_CONFIRM_OWNER_READBACK_MISMATCH')
    query = ("begin read only; select count(*) from ouf_onboarding.approval_decision "
             "where challenge_id='" + challenge + "' and onboarding_version_id='" + prepare.inventory.VERSION +
             "' and decision='APPROVE' and target_hash='" + prepare.inventory.HASH + "'; rollback;")
    count = int(prepare.inventory.routes.helper.run(['docker', 'exec', 'ouf-postgres', 'psql', '-X', '-qAt',
        '-v', 'ON_ERROR_STOP=1', '-U', 'ouf_onboarding', '-d', 'ouf_onboarding', '-c', query]))
    if count != 1:
        raise RuntimeError('APPROVAL_DECISION_READBACK_MISMATCH')
    receipt.update(status='PASS', sourceApproval=True)
    write_receipt(receipt)
    print('R4A_HUMAN_APPROVAL=PASS CHALLENGE_ID=' + challenge)
    print('R4A_HUMAN_APPROVAL_READBACK=PASS STATE=APPROVED FROZEN_HASH_UNCHANGED=true')
    print('R4A_HUMAN_APPROVAL_RECEIPT=' + str(STATE) + ' PRIVATE=true')
    print('R4A_HUMAN_APPROVAL_COMPLETE=PASS SOURCE_ACTIVATION=false SECRETS_NOT_PRINTED=true')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--challenge', required=True)
    try:
        args = parser.parse_args()
        main(args.revision, args.challenge)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, EOFError, prepare.subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_HUMAN_APPROVAL=BLOCKED CODE=' + code + ' SOURCE_ACTIVATION=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
