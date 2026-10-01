#!/usr/bin/env python3
"""Read only one source/run's UDP jobs and symbolic handoff events."""
import argparse
import json
import re
import subprocess
import uuid


def query(args):
    run=str(uuid.UUID(args.run))
    if not re.fullmatch(r'[A-Za-z0-9._-]{1,160}',args.source):
        raise ValueError('source')
    for value in (args.postgres_container,args.database,args.db_user):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,159}',value):
            raise ValueError('binding')
    return ("begin read only; set local statement_timeout='15s'; set local lock_timeout='2s'; "
        "with h as (select handoff_id,state,failure_code from ouf_udp.handoff_intake "
        "where source_id='"+args.source+"' and ingestion_run_id='"+run+"'), "
        "j as (select h.handoff_id,h.state intake_state,h.failure_code intake_failure_code,"
        "m.job_id,m.state job_state,m.state_version,m.attempts,m.integrity_attempts,"
        "m.safe_failure_code,(m.integrity_baseline_hash is not null) integrity_baseline_present,"
        "jsonb_array_length(m.missing_ref_hashes) missing_ref_count,"
        "(m.next_integrity_check_at is not null) next_check_present "
        "from h left join ouf_udp.materialization_job m using(handoff_id)), "
        "e as (select e.handoff_id,e.event_type,count(*) event_count "
        "from ouf_udp.handoff_event e join h using(handoff_id) group by e.handoff_id,e.event_type) "
        "select json_build_object('jobs',coalesce((select json_agg(j order by handoff_id) from j),'[]'::json),"
        "'events',coalesce((select json_agg(e order by handoff_id,event_type) from e),'[]'::json)); rollback;")


def sanitize(document):
    fields={'handoff_id','intake_state','intake_failure_code','job_id','job_state',
            'state_version','attempts','integrity_attempts','safe_failure_code',
            'integrity_baseline_present','missing_ref_count','next_check_present'}
    result={'jobs':[], 'events':[]}
    for row in document['jobs']:
        clean={k:v for k,v in row.items() if k in fields}
        for key in ('intake_state','intake_failure_code','job_state','safe_failure_code'):
            if clean.get(key) is not None and not re.fullmatch(r'[A-Z0-9_]{1,120}',str(clean[key])):
                clean[key]='NON_SYMBOLIC_REDACTED'
        if clean.get('job_id') is not None:clean['job_id']=str(uuid.UUID(clean['job_id']))
        if not re.fullmatch(r'[A-Za-z0-9._:-]{1,200}',str(clean.get('handoff_id',''))):
            raise ValueError('handoff identifier')
        result['jobs'].append(clean)
    for row in document['events']:
        handoff=row['handoff_id']
        if not isinstance(handoff,str) or not re.fullmatch(r'[A-Za-z0-9._:-]{1,200}',handoff):
            raise ValueError('handoff identifier')
        code=row['event_type']
        if not isinstance(code,str) or not re.fullmatch(r'[A-Z0-9_]{1,120}',code):
            code='NON_SYMBOLIC_REDACTED'
        result['events'].append({'handoff_id':handoff,'event_type':code,'event_count':row['event_count']})
    return result


def main(args):
    sql=query(args)
    command=['docker','exec',args.postgres_container,'psql','-X','-qAt','-v',
             'ON_ERROR_STOP=1','-U',args.db_user,'-d',args.database,'-c',sql]
    raw=subprocess.run(command,check=True,capture_output=True,text=True,timeout=25).stdout.strip()
    result=sanitize(json.loads(raw))
    print('R4A_UDP_MATERIALIZATION_DIAGNOSTIC=READ_ONLY RUN_ID='+str(uuid.UUID(args.run)))
    print('UDP_JOB_AND_EVENT_EVIDENCE='+json.dumps(result,sort_keys=True))
    print('R4A_UDP_MATERIALIZATION_DIAGNOSTIC=COMPLETE READ_ONLY=true RETRY=false REPLAY=false PAYLOADS_NOT_PRINTED=true')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('run','source','postgres-container','database','db-user'):
        parser.add_argument('--'+name,required=True)
    try:main(parser.parse_args())
    except Exception as error:
        print('R4A_UDP_MATERIALIZATION_DIAGNOSTIC=BLOCKED TYPE='+type(error).__name__+' READ_ONLY=true SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
