#!/usr/bin/env python3
"""Read queue exposure and real runtime-publications access before enabling the worker."""
import json
import os
from pathlib import Path
import re
import r4a_prepare_frozen_compatibility_probe as helper


def db(user, query):
    return helper.run(['docker', 'exec', 'ouf-postgres', 'psql', '-X', '-qAt',
        '-v', 'ON_ERROR_STOP=1', '-U', user, '-d', user, '-c', 'begin read only; ' + query + '; rollback;'])


def main():
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    print('R4A_WORKER_ENABLEMENT_PREFLIGHT=READ_ONLY', flush=True)
    row = helper.candidate_row('managed-cinema-8ec8ae90', '68394f42-5c82-4127-a1f3-126516665749',
        'sha256:2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891')
    if row['state'] != 'APPROVED':
        raise RuntimeError('SOURCE_NOT_APPROVED')
    print('WORKER_CATALOG_ACTIVE_PUBLICATIONS=' + db('ouf_onboarding', 'select count(*) from ouf_onboarding.published_configuration where active'))
    print('WORKER_EXISTING_CINEMA_ACTIVE_PUBLICATIONS=' + db('ouf_onboarding', "select count(*) from ouf_onboarding.published_configuration where active and source_id='managed-cinema-8ec8ae90'"))
    print('WORKER_EXISTING_ACTIVE_SCHEDULES=' + db('ouf_ingestion', "select count(*) from ouf_ingestion.ing_schedule where state='ACTIVE' and publication_enabled and not activation_blocked"))
    print('WORKER_EXISTING_UNFINISHED_RUNS=' + db('ouf_ingestion', "select count(*) from ouf_ingestion.ing_run where state in ('READY','PREFLIGHT','RUNNING','DRAINING')"))
    live = helper.inspect('ouf-ingestion')
    settings = helper.transport_settings(live, 'ouf-lab')
    mounts = {m['Destination']: m for m in live['Mounts']}
    properties = Path(mounts[helper.PROPERTIES]['Source']).read_text()
    if any(helper.literal_property(properties, key) != value for key, value in settings.items()):
        raise RuntimeError('WORKER_ACTIVATION_TRANSPORT_DRIFT')
    relative = Path(settings['ouf.ingestion.activation.token-file']).relative_to(helper.AUTH)
    token = (Path(mounts[helper.AUTH]['Source']) / relative).read_text().strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', token):
        raise RuntimeError('WORKER_TOKEN_FORMAT_INVALID')
    endpoint = settings['ouf.ingestion.activation.gateway-url'].rstrip('/') + '/api/onboarding/v1/runtime/publications?limit=20&after='
    config = ('silent\nshow-error\nmax-time = 5\nmax-filesize = 2097152\n'
              'header = "Authorization: Bearer ' + token + '"\nurl = "' + endpoint + '"\n'
              'write-out = "\\n%{http_code}"\n')
    raw = helper.run(['docker', 'run', '--rm', '-i', '--read-only', '--cap-drop', 'ALL',
        '--security-opt', 'no-new-privileges', '--network', 'ouf-backend',
        'curlimages/curl:8.16.0', '--config', '-'], input=config, timeout=15)
    body, code = raw.rsplit('\n', 1)
    print('WORKER_PUBLICATION_DISCOVERY_HTTP=' + (code if re.fullmatch(r'\d{3}', code) else 'INVALID'))
    if code == '200':
        page = json.loads(body)
        if not isinstance(page.get('items'), list) or len(page['items']) > 20 or not isinstance(page.get('nextAfter'), str):
            raise RuntimeError('WORKER_PUBLICATION_PAGE_INVALID')
        print('WORKER_PUBLICATION_DISCOVERY_FIRST_PAGE_COUNT=' + str(len(page['items'])))
        print('WORKER_PUBLICATION_DISCOVERY_MORE_PAGES=' + str(bool(page['nextAfter'])).lower())
    else:
        print('WORKER_PUBLICATION_DISCOVERY_AUTHORIZED=false')
    after = helper.inspect('ouf-ingestion')
    if after['Id'] != live['Id'] or after['Image'] != live['Image'] or helper.candidate_row(
            row['sourceId'], row['onboardingVersionId'], row['configurationHash']) != row:
        raise RuntimeError('WORKER_ENABLEMENT_CONTEXT_DRIFT')
    print('R4A_WORKER_ENABLEMENT_PREFLIGHT=COMPLETE LIVE_UNCHANGED=true WORKER_ENABLED=false SOURCE_ACTIVATION=false SECRETS_NOT_PRINTED=true')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_WORKER_ENABLEMENT_PREFLIGHT=BLOCKED CODE=' + code + ' SOURCE_ACTIVATION=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
