#!/usr/bin/env python3
"""Deploy the stopped IAM release without resuming any run; retain runtime rollback."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import time
import r4a_prepare_ingestion_iam_candidate as candidate_prepare
import r4a_switch_ingestion_candidate as rollout

prepare = rollout.prepare
probe = rollout.inventory
LIVE = rollout.LIVE
RECEIPT = prepare.ROOT / 'ingestion-iam-release-switch.json'
rollout.RECEIPT = RECEIPT


def snapshot():
    result = json.loads(rollout.sql("""select json_build_object(
      'busyRuns',(select count(*) from ouf_ingestion.ing_run where state in ('READY','PREFLIGHT','RUNNING','DRAINING')),
      'activeSchedules',(select count(*) from ouf_ingestion.ing_schedule where state='ACTIVE' and publication_enabled and not activation_blocked),
      'busyReplays',(select count(*) from ouf_ingestion.replay_execution where state in ('QUEUED','RUNNING','RETRY_WAIT')),
      'deliverable',(select count(*) from ouf_ingestion.handoff_outbox where state in ('READY','DELIVERING','FAILED_RETRYABLE')),
      'attempts',coalesce((select json_agg(x order by attempt_id) from (select attempt_id,run_id,attempt_no,state,reason_code from ouf_ingestion.processing_attempt) x),'[]'::json),
      'partitions',coalesce((select json_agg(x order by run_id,partition_key) from (select run_id,partition_key,state,checkpoint_json,committed_watermark_json from ouf_ingestion.ing_partition) x),'[]'::json),
      'lineageCount',(select count(*) from ouf_ingestion.ing_lineage),
      'runs',coalesce((select json_agg(x order by run_id) from (select run_id,state,failure_code,control_version from ouf_ingestion.ing_run) x),'[]'::json),
      'schedules',coalesce((select json_agg(x order by schedule_id) from (select schedule_id,state,publication_enabled,activation_blocked,consumed_publication_id from ouf_ingestion.ing_schedule) x),'[]'::json),
      'handoffs',coalesce((select json_agg(x order by handoff_id) from (select handoff_id,state,attempts from ouf_ingestion.handoff_outbox) x),'[]'::json),
      'quarantine',coalesce((select json_agg(x order by quarantine_id) from (select quarantine_id,state,lifecycle_state,lifecycle_version from ouf_ingestion.ing_quarantine) x),'[]'::json))"""))
    if any(result[k] != 0 for k in ('busyRuns','activeSchedules','busyReplays','deliverable')):
        raise RuntimeError('ING_WORK_IN_PROGRESS_SWITCH_REQUIRES_QUIESCENCE')
    result['publications'] = json.loads(rollout.docker('exec','ouf-postgres','psql','-X','-qAt','-v','ON_ERROR_STOP=1','-U','ouf_onboarding','-d','ouf_onboarding','-c', "begin read only; set local statement_timeout=15000; select coalesce(json_agg(x order by publication_id),'[]'::json)::text from (select publication_id,source_id,onboarding_version_id,checksum,active from ouf_onboarding.published_configuration where active) x; rollback;"))
    return result


def validate_runtime(state, old, candidate, image, properties, original):
    prepare.private(properties, 0o440)
    if (state.get('status') != 'PASS' or state.get('deployed') is not False
            or state.get('candidateName') != candidate_prepare.NAME
            or prepare.stable(old) != prepare.stable(state['old'])
            or not old['State']['Running'] or candidate['Id'] != state['candidateId']
            or not prepare.matches(candidate, old, image, properties)
            or image['Config'].get('Labels',{}).get('org.opencontainers.image.revision') != state['revision']
            or hashlib.sha256(original).hexdigest() != state['originalPropertiesSha256']
            or hashlib.sha256(properties.read_bytes()).hexdigest() != state['propertiesSha256']
            or candidate_prepare.content_for(original, prepare.environment(old), state['issuer'], state['audience']) != properties.read_bytes()):
        raise RuntimeError('ING_IAM_PREPARED_BASELINE_DRIFT')
    prepare.guard(old, image)


def main(mode):
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    os.umask(0o077)
    meta = prepare.ROOT.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o700:
        raise RuntimeError('ING_PRIVATE_ROOT_UNSAFE')
    state = rollout.private_json(candidate_prepare.STATE)
    if RECEIPT.exists() or RECEIPT.is_symlink():
        raise RuntimeError('ING_IAM_SWITCH_RECEIPT_EXISTS_REVIEW_BEFORE_RETRY')
    old = probe.inspect(LIVE)
    candidate = probe.inspect(state['candidateName'])
    image = probe.inspect(state['imageId'], 'image')
    properties = Path(state['properties'])
    original_path = Path(next(m['Source'] for m in old['Mounts'] if m['Destination'] == probe.PROPERTIES))
    original = original_path.read_bytes()
    validate_runtime(state, old, candidate, image, properties, original)
    before = rollout.history()
    if (len([x for x in before if x['version'] is not None]) != 14
            or not all(x['success'] for x in before) or before[-1]['version'] != '14'):
        raise RuntimeError('ING_FLYWAY14_DRIFT')
    queues = snapshot()
    rollout.ready(1)
    previous = 'ouf-ingestion-iam-rollback-' + old['Id'][:12]
    failed = 'ouf-ingestion-iam-failed-' + candidate['Id'][:12]
    if prepare.optional(previous) is not None or prepare.optional(failed) is not None:
        raise RuntimeError('ING_ROLLBACK_NAME_OCCUPIED')
    print('R4A_INGESTION_IAM_SWITCH_PLAN=PASS MODE='+mode+' FLYWAY=14 BOTH_LOOPS_PRESERVED=true QUIESCENT=true', flush=True)
    if mode == 'plan':
        print('R4A_INGESTION_IAM_SWITCH=PLANNED LIVE_UNCHANGED=true RETRY=false RUN_RESUME=false')
        return
    receipt = {'status':'STARTING','old_id':old['Id'],'candidate_id':candidate['Id'],'revision':state['revision'],'rollback_container':previous,'failed_container':failed,'db_dump':None,'history':before,'snapshot':queues}
    rollout.save(receipt)
    print('R4A_INGESTION_IAM_SWITCH=STOPPING_LIVE RETRY=false RUN_RESUME=false', flush=True)
    try:
        validate_runtime(state, probe.inspect(LIVE), probe.inspect(state['candidateName']), image, properties, original_path.read_bytes())
        if snapshot() != queues:
            raise RuntimeError('ING_QUEUES_CHANGED_BEFORE_STOP')
        rollout.docker('update','--restart','no',LIVE)
        rollout.docker('stop','--time','60',LIVE)
        receipt['db_dump'] = str(rollout.backup_restore(before))
        rollout.save(receipt)
        if rollout.history() != before or snapshot() != queues or original_path.read_bytes() != original:
            raise RuntimeError('ING_DATABASE_CHANGED_DURING_BACKUP')
        if (hashlib.sha256(properties.read_bytes()).hexdigest() != state['propertiesSha256']
                or not prepare.matches(probe.inspect(state['candidateName']), old, image, properties)):
            raise RuntimeError('ING_CANDIDATE_CHANGED_BEFORE_START')
        rollout.docker('rename',LIVE,previous)
        rollout.docker('rename',state['candidateName'],LIVE)
        rollout.docker('start',LIVE)
        rollout.ready()
        # Direct owner request exercises the protected HTTP boundary with no token.
        if rollout.http_code('/api/trusted-human/v1/ingestion/runs/00000000-0000-0000-0000-000000000000') != '401':
            raise RuntimeError('ING_IAM_OWNER_UNAUTHENTICATED_BOUNDARY_NOT_401')
        for seconds in (8,16):
            time.sleep(8)
            print('R4A_INGESTION_IAM_OBSERVATION_WAIT_SECONDS='+str(seconds), flush=True)
            rollout.ready(1)
            if rollout.history() != before or snapshot() != queues:
                raise RuntimeError('ING_LIFECYCLE_OR_SCHEMA_CHANGED_AFTER_SWITCH')
        current = probe.inspect(LIVE)
        if (current['Id'] != state['candidateId'] or current['Image'] != state['imageId']
                or prepare.environment(current) != prepare.environment(old)
                or prepare.mounts(current) != prepare.mounts(old, properties)
                or original_path.read_bytes() != original
                or hashlib.sha256(properties.read_bytes()).hexdigest() != state['propertiesSha256']):
            raise RuntimeError('ING_POST_SWITCH_BINDINGS_DRIFT')
        rollout.docker('update','--restart','unless-stopped',LIVE)
        prepare.guard(probe.inspect(LIVE), image)
        receipt.update(status='PASS',unauthenticatedOwnerHttp=401,observationSeconds=16,queuesUnchanged=True)
        rollout.save(receipt)
        print('R4A_INGESTION_IAM_SWITCH=PASS LIVE_REVISION='+state['revision']+' FLYWAY_UNCHANGED=true BOTH_LOOPS_PRESERVED=true')
        print('R4A_INGESTION_IAM_OWNER_BOUNDARY=PASS UNAUTHENTICATED_HTTP=401 HUMAN_AUTHORIZATION_NOT_YET_PROVEN=true')
        print('R4A_INGESTION_IAM_ROLLBACK_CONTAINER='+previous)
        print('R4A_INGESTION_IAM_RECEIPT='+str(RECEIPT)+' PRIVATE=true')
        print('R4A_INGESTION_IAM_COMPLETE=PASS QUEUES_UNCHANGED=true RETRY=false RUN_RESUME=false SOURCE_ACTIVATION=false WORKLOAD_TOKEN_UNCHANGED_BY_SCRIPT=true SECRETS_NOT_PRINTED=true')
    except BaseException:
        try:
            rollout.recover({'old':old,'candidate_id':state['candidateId']},previous,failed)
            receipt['status'] = 'ROLLED_BACK'
            print('R4A_INGESTION_IAM_RUNTIME_ROLLBACK=PASS DB_NOT_AUTOMATICALLY_RESTORED=true', flush=True)
        except Exception:
            receipt['status'] = 'MANUAL_RECOVERY_REQUIRED'
            print('R4A_INGESTION_IAM_RUNTIME_ROLLBACK=MANUAL_RECOVERY_REQUIRED', flush=True)
        rollout.save(receipt)
        raise


class Output:
    def write(self, text):
        return sys.__stdout__.write(text.replace('R4A_ING_COMPAT','R4A_INGESTION_IAM'))
    def flush(self):
        return sys.__stdout__.flush()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('plan','apply'))
    try:
        with contextlib.redirect_stdout(Output()):
            main(parser.parse_args().mode)
    except Exception as error:
        code = str(error) if isinstance(error,RuntimeError) else type(error).__name__
        print('R4A_INGESTION_IAM_SWITCH=BLOCKED CODE='+code+' RETRY=false RUN_RESUME=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
