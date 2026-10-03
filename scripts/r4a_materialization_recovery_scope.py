#!/usr/bin/env python3
"""Read-only original-job/RAW metadata inventory for an exact HUMAN policy scope.

Writes only a new private local resource file. Does not resolve contracts,
materialize, requeue or read payload/token/reference values.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import uuid
import r4a_prepare_scoped_human_policy as policy


def resources(rows,args):
    policy.require(isinstance(rows,list) and len(rows)==len(args.job),'JOB_COUNT_MISMATCH')
    policy.require({r['job_id'] for r in rows}==set(args.job),'JOB_ID_SET_MISMATCH')
    result=[]
    for row in rows:
        policy.require(row['tenant_id']==args.tenant and row['source_id']==args.source
            and row['ingestion_run_id']==args.run and row['raw_source']==row['source_id']
            and row['raw_type']==row['type_code'] and row['tier']=='RAW','RAW_SCOPE_MISMATCH')
        policy.require(row['state']=='QUARANTINED' and row['intake_state']=='DURABLE'
            and row['safe_failure_code'] in ('UDP_REFERENCE_INTEGRITY_CONTRACT_INVALID',
            'UDP_REFERENCE_INTEGRITY_CATALOG_INVALID','UDP_REFERENCE_INTEGRITY_MISSING')
            and row['claimed_by'] is None and row['lease_until'] is None and not row['decision_present']
            and row['lake_state'] in ('VERIFIED','COMPACTED','COLD'),'JOB_NOT_TECHNICAL_RECOVERY_ELIGIBLE')
        policy.require(policy.text(row['access_label']) and policy.text(row['type_code']),'RAW_LABEL_OR_TYPE_INVALID')
        result.append({'capabilityId':args.capability,'resourceType':'materialization-job','resourceId':row['job_id'],
            'resourceAttributes':{'module':'UDP','sourceRef':args.source,'jobRef':args.run,'typeRef':row['type_code']},
            'allowedDataLabels':[row['access_label']]})
    return sorted(result,key=lambda row:row['resourceId'])


def main(args):
    for value in (args.postgres_container,args.database,args.db_user,args.source,args.tenant):
        policy.require(re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',value),'INSTALLATION_IDENTIFIER_INVALID')
    args.run=str(uuid.UUID(args.run));args.job=[str(uuid.UUID(job)) for job in args.job]
    policy.require(0<len(args.job)<=1000 and len(set(args.job))==len(args.job),'JOB_IDS_INVALID')
    policy.require(policy.text(args.capability),'CAPABILITY_INVALID')
    policy.private(args.output.parent,True)
    policy.require(not args.output.exists() and not args.output.is_symlink(),'OUTPUT_EXISTS_RECONCILE')
    ids=','.join("'"+job+"'" for job in args.job)
    sql="""begin read only; set local statement_timeout='15s';
select coalesce(json_agg(q order by job_id),'[]'::json) from (
select j.job_id,j.state,j.safe_failure_code,j.claimed_by,j.lease_until,h.state intake_state,
h.source_id,h.ingestion_run_id,h.type_code,l.tenant_id,l.source_id raw_source,l.type_code raw_type,
l.tier,l.state lake_state,l.access_label,
(exists(select 1 from ouf_udp.resolution_decision d where d.handoff_id=h.handoff_id)
or exists(select 1 from ouf_udp.materialization_observation o where o.handoff_id=h.handoff_id)
or exists(select 1 from ouf_udp.object_revision r where r.source_handoff_id=h.handoff_id)
or exists(select 1 from ouf_udp.property_contribution p where p.handoff_id=h.handoff_id)
or exists(select 1 from ouf_udp.source_binding b where b.first_handoff_id=h.handoff_id)) decision_present
from ouf_udp.materialization_job j join ouf_udp.handoff_intake h using(handoff_id)
join ouf_udp.lake_object l on l.lake_object_id=h.raw_lake_object_id
where j.job_id in ("""+ids+")) q; rollback;"
    value=subprocess.run(['docker','exec',args.postgres_container,'psql','-X','-qAt','-v','ON_ERROR_STOP=1',
        '-U',args.db_user,'-d',args.database,'-c',sql],capture_output=True,text=True,check=True,timeout=30)
    scopes=resources(json.loads(value.stdout),args)
    os.umask(0o077);policy.reserve(args.output);policy.write(args.output,scopes)
    print('R4A_UDP_RECOVERY_RESOURCE_SCOPE=PASS READ_ONLY=true JOB_COUNT='+str(len(scopes))
          +' EXACT_JOB_SOURCE_RUN_TENANT=true RAW_LABELS_BOUND=true RETRY=false PAYLOADS_NOT_READ=true VALUES_NOT_PRINTED=true')
    print('R4A_UDP_RECOVERY_RESOURCE_FILE='+str(args.output)+' PRIVATE=true')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('postgres-container','database','db-user','source','tenant','run','capability'):p.add_argument('--'+name,required=True)
    p.add_argument('--job',action='append',required=True);p.add_argument('--output',type=Path,required=True)
    try:main(p.parse_args())
    except Exception as error:
        code=str(error) if isinstance(error,policy.Blocked) else 'UNCLASSIFIED'
        print('R4A_UDP_RECOVERY_RESOURCE_SCOPE=BLOCKED CODE='+code+' TYPE='+type(error).__name__+' RETRY=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
