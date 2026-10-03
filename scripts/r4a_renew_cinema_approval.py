#!/usr/bin/env python3
"""Explicit expired-challenge renewal, optionally followed by direct HUMAN review/confirmation."""
import argparse
import json
import os
import stat
import uuid
import r4a_prepare_cinema_approval as prepare


def owner_facts(challenge):
    query = ("begin read only; select json_build_object('sourceId',c.source_id,"
        "'versionId',c.onboarding_version_id,'hash',c.configuration_hash,'status',c.status,"
        "'expired',c.expires_at<=transaction_timestamp(),"
        "'decisions',(select count(*) from ouf_onboarding.approval_decision d where d.onboarding_version_id=c.onboarding_version_id),"
        "'unexpiredChallenges',(select count(*) from ouf_onboarding.approval_challenge x where x.onboarding_version_id=c.onboarding_version_id and x.status='CREATED' and x.expires_at>transaction_timestamp()))::text "
        "from ouf_onboarding.approval_challenge c where c.challenge_id='" + str(uuid.UUID(challenge)) + "'; rollback;")
    return json.loads(prepare.inventory.routes.helper.run(['docker', 'exec', 'ouf-postgres', 'psql', '-X', '-qAt',
        '-v', 'ON_ERROR_STOP=1', '-U', 'ouf_onboarding', '-d', 'ouf_onboarding', '-c', query]))


def validate_expired(facts):
    if (facts.get('sourceId') != prepare.inventory.SOURCE or facts.get('versionId') != prepare.inventory.VERSION or
            facts.get('hash') != prepare.inventory.HASH or facts.get('status') not in {'CREATED', 'EXPIRED'} or
            facts.get('expired') is not True or facts.get('decisions') != 0 or facts.get('unexpiredChallenges') != 0):
        raise RuntimeError('RENEWAL_OWNER_NOT_EXPIRED_UNDECIDED_OR_OTHER_CHALLENGE_PRESENT')


def write_exclusive(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(value, stream)
        stream.flush()
        os.fsync(stream.fileno())


def renew(revision, expired):
    expired = str(uuid.UUID(expired))
    if os.geteuid() != 0 or not prepare.re.fullmatch(r'[0-9a-f]{40}', revision):
        raise RuntimeError('ROOT_AND_PINNED_REVISION_REQUIRED')
    for path, kind, mode in [(prepare.ROOT, stat.S_ISDIR, 0o700), (prepare.STATE, stat.S_ISREG, 0o600)]:
        meta = path.lstat()
        if not kind(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != mode:
            raise RuntimeError('RENEWAL_PRIVATE_PATH_UNSAFE')
    confirmation = prepare.ROOT / 'cinema-approval-confirmation.json'
    if confirmation.exists() or confirmation.is_symlink():
        raise RuntimeError('RENEWAL_CONFIRMATION_RECEIPT_PRESENT_RECONCILE')
    old = json.loads(prepare.STATE.read_text())
    if (old.get('status') != 'PASS' or old.get('challengeId') != expired or
            old.get('sourceId') != prepare.inventory.SOURCE or old.get('versionId') != prepare.inventory.VERSION or
            old.get('configurationHash') != prepare.inventory.HASH):
        raise RuntimeError('RENEWAL_RECEIPT_CONTEXT_MISMATCH')
    before = prepare.inventory.routes.helper.candidate_row(prepare.inventory.SOURCE, prepare.inventory.VERSION, prepare.inventory.HASH)
    if before['state'] != 'IN_REVIEW' or old.get('card', {}).get('configuration') != before['configuration']:
        raise RuntimeError('RENEWAL_VERSION_OR_CARD_DRIFT')
    validate_expired(owner_facts(expired))
    lock = prepare.ROOT / ('cinema-approval-renewal-' + expired + '.json')
    if lock.exists() or lock.is_symlink():
        raise RuntimeError('RENEWAL_ALREADY_RESERVED_RECONCILE_DO_NOT_REPOST')
    prepare.verify_routes()
    live = prepare.inventory.routes.helper.inspect('ouf-onboarding')
    token = prepare.human_token(revision)
    prepare.verify_routes()
    validate_expired(owner_facts(expired))
    current = prepare.inventory.routes.helper.inspect('ouf-onboarding')
    if current['Id'] != live['Id'] or current['Image'] != live['Image'] or prepare.inventory.routes.helper.candidate_row(prepare.inventory.SOURCE, prepare.inventory.VERSION, prepare.inventory.HASH) != before:
        raise RuntimeError('RENEWAL_CONTEXT_DRIFT_BEFORE_POST')
    state = {'status': 'UNVERIFIED_DO_NOT_REPOST', 'sourceId': prepare.inventory.SOURCE,
             'versionId': prepare.inventory.VERSION, 'configurationHash': prepare.inventory.HASH,
             'supersedesLocalReceiptForChallenge': expired, 'sourceApproval': False, 'sourceActivation': False}
    write_exclusive(lock, state)
    archive = prepare.ROOT / ('cinema-approval-challenge-expired-' + expired + '.json')
    write_exclusive(archive, old)
    prepare.save(state)
    response = prepare.request('POST', prepare.inventory.TARGETS['CREATE'][1], token)
    challenge = str(uuid.UUID(str(response.get('challenge_id'))))
    if challenge == expired:
        raise RuntimeError('RENEWAL_OWNER_REUSED_EXPIRED_ID')
    state.update(challengeId=challenge, response=response)
    prepare.save(state)
    prepare.check_card(response, challenge)
    card = prepare.request('GET', '/api/trusted-human/v1/approval-challenges/' + challenge, token)
    prepare.check_card(card, challenge, before['configuration'])
    current = prepare.inventory.routes.helper.inspect('ouf-onboarding')
    if current['Id'] != live['Id'] or current['Image'] != live['Image'] or prepare.inventory.routes.helper.candidate_row(prepare.inventory.SOURCE, prepare.inventory.VERSION, prepare.inventory.HASH) != before:
        raise RuntimeError('RENEWAL_CONTEXT_DRIFT_AFTER_CARD')
    state.update(status='PASS', card=card)
    prepare.save(state)
    canonical_state = prepare.STATE
    try:
        prepare.STATE = lock
        prepare.save({'status': 'PASS', 'expiredChallengeId': expired, 'newChallengeId': challenge})
    finally:
        prepare.STATE = canonical_state
    print('R4A_APPROVAL_RENEWAL=PASS NEW_CHALLENGE_ID=' + challenge, flush=True)
    print('R4A_APPROVAL_EXPIRES_AT=' + str(card['expires_at']), flush=True)
    print('R4A_APPROVAL_EXPIRED_RECEIPT=' + str(archive) + ' PRIVATE=true', flush=True)
    print('R4A_APPROVAL_RENEWAL_COMPLETE=PASS SOURCE_APPROVAL=false SOURCE_ACTIVATION=false', flush=True)
    return token, challenge


def main(revision, expired, confirm):
    token, challenge = renew(revision, expired)
    if confirm:
        import r4a_confirm_cinema_approval as human
        login = prepare.human_token
        try:
            # Same fresh human session; confirmation still requires explicit terminal input.
            prepare.human_token = lambda requested_revision: token
            human.main(revision, challenge)
        finally:
            prepare.human_token = login


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--expired-challenge', required=True)
    parser.add_argument('--review-and-confirm', action='store_true')
    try:
        args = parser.parse_args()
        main(args.revision, args.expired_challenge, args.review_and_confirm)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, EOFError, prepare.subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_APPROVAL_RENEWAL_OR_CONFIRM=BLOCKED CODE=' + code + ' SOURCE_ACTIVATION=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
