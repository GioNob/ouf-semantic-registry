#!/usr/bin/env python3
"""Read-only source/publication-scoped snapshot of real Ingestion and UDP execution."""
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import uuid
from datetime import datetime

ROOT = Path('/etc/ouf/deploy-snapshots')
SOURCE = 'managed-cinema-8ec8ae90'
VERSION = '68394f42-5c82-4127-a1f3-126516665749'
HASH = 'sha256:2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891'
PUBLICATION = '82a8a210-32fd-4ca3-adeb-ff0ec7872bf6'
EXPECTED_ROWS = 8


def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=30).stdout.strip()


def private(path):
    meta = path.lstat()
    if not stat.S_ISREG(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o600:
        raise RuntimeError('ACTIVATION_RECEIPT_UNSAFE')
    return json.loads(path.read_text())


def sql(database, query):
    return json.loads(run(['docker', 'exec', 'ouf-postgres', 'psql', '-X', '-qAt', '-v', 'ON_ERROR_STOP=1',
        '-U', database, '-d', database, '-c', "begin read only; set local statement_timeout='15s'; set local lock_timeout='2s'; " + query + '; rollback;']))


def counts(items):
    result = {}
    for item in items:
        state = item.get('state', 'UNKNOWN')
        state = state if re.fullmatch(r'[A-Z_]{1,80}', str(state)) else 'REDACTED'
        result[state] = result.get(state, 0) + 1
    return result


def codes(items, field):
    return sorted({str(x[field]) if re.fullmatch(r'[A-Z0-9_]{1,120}', str(x[field])) else 'NON_SYMBOLIC_REDACTED'
                   for x in items if x.get(field) is not None})


def classify(ingestion, udp):
    runs, handoffs = ingestion['runs'], ingestion['handoffs']
    ids_match = {x['handoff_id'] for x in handoffs} == {x['handoff_id'] for x in udp['intakes']}
    delivered = (len(runs) == 1 and runs[0]['state'] == 'SUCCEEDED' and len(handoffs) == EXPECTED_ROWS and
                 all(x['state'] == 'ACKED' and x['receipt_present'] for x in handoffs) and ids_match and ingestion['quarantine'] == 0)
    materialized = (delivered and len(udp['intakes']) == EXPECTED_ROWS and
        all(x['state'] == 'PROCESSED' for x in udp['intakes']) and len(udp['jobs']) == EXPECTED_ROWS and
        all(x['state'] == 'SUCCEEDED' for x in udp['jobs']) and
        udp['observations'] == EXPECTED_ROWS and udp['open_issues'] == 0 and udp['bindings'] == EXPECTED_ROWS and udp['active_objects'] > 0)
    return ids_match, delivered, materialized


def main():
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    receipt_path = ROOT / 'cinema-source-activation.json'
    receipt = private(receipt_path)
    if (receipt.get('status') != 'PASS' or receipt.get('sourceActivation') is not True or
        receipt.get('sourceId') != SOURCE or receipt.get('versionId') != VERSION or
        receipt.get('configurationHash') != HASH or receipt.get('publicationId') != PUBLICATION):
        raise RuntimeError('ACTIVATION_RECEIPT_NOT_PASS_OR_MISMATCH')
    response = receipt['response']
    checksum = receipt['checksum']
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', checksum):
        raise RuntimeError('PUBLICATION_CHECKSUM_INVALID')
    print('R4A_CINEMA_EXECUTION_READBACK=READ_ONLY SOURCE=' + SOURCE, flush=True)
    owner = sql('ouf_onboarding', "select json_build_object('state',v.state,'hash',v.configuration_hash,'publicationId',p.publication_id,'active',p.active,'checksum',p.checksum,'bundle',p.bundle) from ouf_onboarding.onboarding_version v join ouf_onboarding.published_configuration p on p.onboarding_version_id=v.onboarding_version_id where v.source_id='" + SOURCE + "' and v.onboarding_version_id='" + VERSION + "' and p.publication_id='" + PUBLICATION + "'")
    if (owner.get('state') != 'ACTIVE' or owner.get('hash') != HASH or owner.get('active') is not True or
        owner.get('checksum') != checksum or owner.get('bundle') != response.get('bundle')):
        raise RuntimeError('ACTIVE_PUBLICATION_DRIFT')
    print('EXECUTION_SOURCE_STATE=ACTIVE FROZEN_HASH_MATCH=true PUBLICATION_MATCH=true')
    scope = "source_id='" + SOURCE + "' and bundle_checksum='" + checksum + "'"
    ingestion = sql('ouf_ingestion', "with r as (select run_id,state,phase,failure_code from ouf_ingestion.ing_run where " + scope + "), h as (select handoff_id,state,attempts,downstream_receipt_ref is not null receipt_present from ouf_ingestion.handoff_outbox where run_id in(select run_id from r)), s as (select schedule_id,state,trigger_once,publication_enabled,activation_failures,activation_blocked,consumed_publication_id is not null consumed from ouf_ingestion.ing_schedule where source_id='" + SOURCE + "' and publication_id='" + PUBLICATION + "') select json_build_object('runs',coalesce((select json_agg(r) from r),'[]'::json),'handoffs',coalesce((select json_agg(h) from h),'[]'::json),'schedules',coalesce((select json_agg(s) from s),'[]'::json),'attempts',(select count(*) from ouf_ingestion.processing_attempt where run_id in(select run_id from r)),'lineages',(select count(*) from ouf_ingestion.ing_lineage where run_id in(select run_id from r)),'quarantine',(select count(*) from ouf_ingestion.ing_quarantine where run_id in(select run_id from r) and state='OPEN'))")
    run_ids = [str(uuid.UUID(x['run_id'])) for x in ingestion['runs']]
    predicate = ("ingestion_run_id in (" + ','.join("'" + x + "'" for x in run_ids) + ")") if run_ids else 'false'
    udp = sql('ouf_udp', "with h as (select handoff_id,state,failure_code from ouf_udp.handoff_intake where source_id='" + SOURCE + "' and " + predicate + "), j as (select state,attempts from ouf_udp.materialization_job where handoff_id in(select handoff_id from h)), d as (select outcome state from ouf_udp.resolution_decision where handoff_id in(select handoff_id from h)) select json_build_object('intakes',coalesce((select json_agg(h) from h),'[]'::json),'jobs',coalesce((select json_agg(j) from j),'[]'::json),'decisions',coalesce((select json_agg(d) from d),'[]'::json),'open_issues',(select count(*) from ouf_udp.resolution_issue where handoff_id in(select handoff_id from h) and state='OPEN'),'issue_codes',coalesce((select json_agg(distinct reason_code) from ouf_udp.resolution_issue where handoff_id in(select handoff_id from h) and state='OPEN'),'[]'::json),'observations',(select count(*) from ouf_udp.materialization_observation where handoff_id in(select handoff_id from h)),'revisions',(select count(*) from ouf_udp.object_revision where source_handoff_id in(select handoff_id from h)),'bindings',(select count(*) from ouf_udp.source_binding where source_id='" + SOURCE + "' and first_handoff_id in(select handoff_id from h)),'active_objects',(select count(distinct o.urban_object_id) from ouf_udp.urban_object o join ouf_udp.source_binding b on b.urban_object_id=o.urban_object_id where o.status='ACTIVE' and o.current_revision_id is not null and b.source_id='" + SOURCE + "' and b.first_handoff_id in(select handoff_id from h)))")
    print('ING_RUN_COUNT=' + str(len(run_ids)))
    for item in ingestion['runs']:
        print('ING_RUN_ID=' + str(uuid.UUID(item['run_id'])) + ' STATE=' + next(iter(counts([item]))) + ' FAILURE_CODES=' + json.dumps(codes([item], 'failure_code')))
    print('ING_SCHEDULES=' + json.dumps(ingestion['schedules'], sort_keys=True))
    for name in ('attempts', 'lineages', 'quarantine'):
        print('ING_' + name.upper() + '_COUNT=' + str(ingestion[name]))
    print('ING_HANDOFF_STATES=' + json.dumps(counts(ingestion['handoffs']), sort_keys=True))
    for name in ('intakes', 'jobs', 'decisions'):
        print('UDP_' + name.upper() + '_STATES=' + json.dumps(counts(udp[name]), sort_keys=True))
    print('UDP_FAILURE_CODES=' + json.dumps(codes(udp['intakes'], 'failure_code')))
    print('UDP_OPEN_ISSUE_CODES=' + json.dumps(codes([{'code':x} for x in udp['issue_codes']], 'code')))
    for name in ('open_issues', 'observations', 'revisions', 'bindings', 'active_objects'):
        print('UDP_' + name.upper() + '_COUNT=' + str(udp[name]))
    matched, delivered, materialized = classify(ingestion, udp)
    print('EXECUTION_HANDOFF_ID_SETS_MATCH=' + str(matched).lower())
    print('ING_DELIVERY_EIGHT_ROWS=' + ('PASS' if delivered else 'NOT_PROVEN'))
    print('UDP_MATERIALIZATION_EIGHT_ROWS=' + ('PASS' if materialized else 'NOT_PROVEN'))
    activated = datetime.fromisoformat(str(response['bundle']['effectiveFrom']).replace('Z', '+00:00'))
    if activated.tzinfo is None:
        raise RuntimeError('PUBLICATION_EFFECTIVE_TIME_INVALID')
    since = str(int(activated.timestamp()) - 5)
    markers = ('ING_ACTIVATION_DISCOVERY_UNAVAILABLE','ING_ACTIVATION_PUBLICATION_REJECTED',
        'ING_ACTIVATION_DISPATCH_FAILED','ING_AUTOMATIC_DELIVERY_FAILED','ING_AUTOMATIC_EXECUTION_FAILED')
    result = subprocess.run(['docker','logs','--since',since,'--tail','1000','ouf-ingestion'], capture_output=True, text=True, timeout=15, check=True)
    logs = result.stdout + result.stderr
    print('ING_RECENT_FAILURE_MARKERS=' + json.dumps({m:logs.count(m) for m in markers}, sort_keys=True))
    if run_ids and (not delivered or not materialized):
        try:
            from types import SimpleNamespace
            import r4a_execution_failure_bundle as diagnostic
            for run_id in run_ids:
                diagnostic.main(SimpleNamespace(run=run_id))
        except Exception as error:
            print('EXECUTION_FAILURE_BUNDLE=UNAVAILABLE TYPE='+type(error).__name__)
    print('R4A_CINEMA_EXECUTION_READBACK=COMPLETE READ_ONLY=true CROSS_DATABASE_ATOMIC=false SEARCH_NOT_VERIFIED=true SECRETS_NOT_PRINTED=true')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_CINEMA_EXECUTION_READBACK=BLOCKED CODE=' + code + ' READ_ONLY=true SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
