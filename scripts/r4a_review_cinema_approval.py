#!/usr/bin/env python3
"""Show authoritative decision sections of a verified card; no confirmation or activation."""
import json
import os
import stat
import subprocess
import uuid
import r4a_prepare_cinema_approval as prepare


def review_sections(configuration):
    runtime = configuration['extractionProfile']['runtime']
    return {
        'semanticMapping': configuration['semanticMapping'],
        'semanticReferenceBindings': configuration['semanticReferenceBindings'],
        'sourceObjectIdentityPolicy': configuration['sourceObjectIdentityPolicy'],
        'dataAccessPolicies': configuration['dataAccessPolicies'],
        'recordModel': runtime['recordModel'],
        'rowIdentityBasis': runtime['rowIdentityBasis'],
        'execution': runtime['execution'],
        'udpResolution': runtime['udp']['resolution'],
        'udpMaterialization': runtime['udp']['materialization'],
    }


def main():
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    meta = prepare.STATE.lstat()
    if not stat.S_ISREG(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o600:
        raise RuntimeError('APPROVAL_RECEIPT_UNSAFE')
    state = json.loads(prepare.STATE.read_text())
    if (state.get('status') != 'PASS' or state.get('sourceId') != prepare.inventory.SOURCE or
            state.get('versionId') != prepare.inventory.VERSION or state.get('configurationHash') != prepare.inventory.HASH):
        raise RuntimeError('APPROVAL_RECEIPT_CONTEXT_MISMATCH')
    challenge = str(uuid.UUID(state['challengeId']))
    before = prepare.inventory.routes.helper.candidate_row(prepare.inventory.SOURCE, prepare.inventory.VERSION, prepare.inventory.HASH)
    if before['state'] != 'IN_REVIEW':
        raise RuntimeError('APPROVAL_VERSION_NOT_IN_REVIEW')
    prepare.check_card(state['card'], challenge, before['configuration'])
    query = ("begin read only; select json_build_object('challengeId',challenge_id,"
             "'sourceId',source_id,'versionId',onboarding_version_id,'hash',configuration_hash,"
             "'status',status,'notExpired',expires_at>transaction_timestamp())::text "
             "from ouf_onboarding.approval_challenge where challenge_id='" + challenge + "'; rollback;")
    row = json.loads(prepare.inventory.routes.helper.run(['docker', 'exec', 'ouf-postgres', 'psql', '-X', '-qAt',
        '-v', 'ON_ERROR_STOP=1', '-U', 'ouf_onboarding', '-d', 'ouf_onboarding', '-c', query]))
    if (row.get('sourceId') != prepare.inventory.SOURCE or row.get('versionId') != prepare.inventory.VERSION or
            row.get('hash') != prepare.inventory.HASH or row.get('status') != 'CREATED' or row.get('notExpired') is not True):
        raise RuntimeError('APPROVAL_OWNER_CHALLENGE_STALE_OR_MISMATCH')
    sections = review_sections(before['configuration'])
    if prepare.inventory.routes.helper.candidate_row(prepare.inventory.SOURCE, prepare.inventory.VERSION, prepare.inventory.HASH) != before:
        raise RuntimeError('APPROVAL_VERSION_DRIFT')
    print('R4A_APPROVAL_REVIEW=READ_ONLY CHALLENGE_ID=' + challenge)
    print('CONFIGURATION_HASH=' + prepare.inventory.HASH)
    print('CHALLENGE_EXPIRES_AT=' + str(state['card']['expires_at']))
    print(json.dumps(sections, ensure_ascii=False, indent=2, sort_keys=True))
    print('R4A_APPROVAL_REVIEW=PASS CARD_AND_OWNER_MATCH=true SOURCE_APPROVAL=false SOURCE_ACTIVATION=false')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_APPROVAL_REVIEW=BLOCKED CODE=' + code + ' SOURCE_APPROVAL=false SOURCE_ACTIVATION=false')
        raise SystemExit(1)
