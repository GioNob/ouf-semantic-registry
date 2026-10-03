#!/usr/bin/env python3
"""Inspect the real cinema Onboarding DRAFT through the HUMAN Gateway route.

This records a validation run, but never submits, approves, or activates a bundle.
"""
import argparse
import json
import re
import subprocess
import sys
import types

SOURCE = 'managed-cinema-8ec8ae90'
VERSION = '68394f42-5c82-4127-a1f3-126516665749'
ASSET = '8ec8ae90-808a-4d9e-907c-d56de119e376'
PROFILE = '4462692b-9c85-446b-b6fd-779f01eab64d'
SEMANTIC = 'https://api.ouf-lab.it/semantic/cinema@1.0.0'
BASE = 'https://api.ouf-lab.it/api/onboarding/v1/sources/' + SOURCE + '/onboarding-versions/' + VERSION


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[0-9a-f]{40}', args.revision):
        raise RuntimeError('PINNED_REVISION_REQUIRED')
    git = ['git', '-c', 'safe.directory=/opt/ouf/semantic', '-C', '/opt/ouf/semantic']
    pinned = subprocess.check_output([*git, 'rev-parse', args.revision + '^{commit}'],
                                     stderr=subprocess.DEVNULL).decode().strip()
    if pinned != args.revision:
        raise RuntimeError('PINNED_REVISION_MISMATCH')
    source = subprocess.check_output([*git, 'show', args.revision +
                                      ':scripts/r4a_cinema_semantic_draft.py'],
                                     stderr=subprocess.DEVNULL)
    helper = types.ModuleType('r4a_cinema_semantic_draft')
    exec(compile(source, 'r4a_cinema_semantic_draft.py', 'exec'), helper.__dict__)
    helper.SCOPES = {'ouf.onboarding.configuration.write'}
    token, _ = helper.human_token()

    def call(method, suffix=''):
        status, raw = helper.request(BASE + suffix, method=method, data=b'' if method == 'POST' else None,
                                     token=token)
        if status != 200:
            raise RuntimeError(method + '_HTTP_' + str(status))
        return json.loads(raw)

    version = call('GET')
    config = version.get('configuration') or {}
    extraction = config.get('extractionProfile') or {}
    runtime = extraction.get('runtime') or {}
    identity = config.get('sourceObjectIdentityPolicy') or {}
    mapping = config.get('semanticMapping') or {}
    fields = {d.get('target'): d.get('label') for d in config.get('dataAccessPolicies', [])}
    expected_fields = {
        'https://api.ouf-lab.it/semantic/cinema#nome': 'OPEN',
        'https://api.ouf-lab.it/semantic/cinema#indirizzo': 'OPEN',
    }
    if (version.get('source_id') != SOURCE or version.get('onboarding_version_id') != VERSION
            or version.get('state') != 'DRAFT'
            or extraction.get('selection') != {'assetId': ASSET, 'fileProfileId': PROFILE}
            or mapping.get('semanticRefs') != [SEMANTIC]
            or identity.get('strategy') != 'MANAGED_DETERMINISTIC'
            or identity.get('sourceFields') != ['$managedRowOrdinal']
            or fields != expected_fields):
        raise RuntimeError('REVIEWED_DRAFT_MISMATCH')
    print('REVIEWED_DRAFT_MATCH=true', flush=True)
    print('UDP_RESOLUTION_CONFIGURED=' + str(bool((runtime.get('udp') or {}).get('resolution'))).lower(),
          flush=True)
    validation = call('POST', '/validate')
    if validation.get('onboardingVersionId') != VERSION:
        raise RuntimeError('VALIDATION_VERSION_MISMATCH')
    print('ONBOARDING_VALIDATION=' + str(validation.get('result')) +
          ' ERRORS=' + str(validation.get('errorCount')) +
          ' WARNINGS=' + str(validation.get('warningCount')), flush=True)
    for item in validation.get('findings', []):
        if item.get('severity') in ('ERROR', 'WARNING'):
            print('FINDING=' + str(item.get('code')) + ' PATH=' + str(item.get('path')),
                  flush=True)
    print('DRAFT_UNCHANGED=true NO_SUBMIT_OR_ACTIVATION=true TOKEN_NOT_PRINTED=true')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('ONBOARDING_PREFLIGHT_BLOCKED=' + str(error), file=sys.stderr)
        sys.exit(1)
