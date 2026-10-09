#!/usr/bin/env python3
"""Read recovery metadata and shared HUMAN routes; no retry/replay/resume or payload output."""
import argparse
import json
import os
import re
import uuid
import r4a_install_runtime_publication_list_route as admin


def sql(query):
    return admin.inventory.routes.helper.run(['docker','exec','ouf-postgres','psql','-X','-qAt','-v','ON_ERROR_STOP=1','-U','ouf_ingestion','-d','ouf_ingestion','-c','begin read only; set local statement_timeout=15000; '+query+'; rollback;'])


def flag(name,value):
    print(name+'='+str(bool(value)).lower())


def main(args):
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    run, quarantine = str(uuid.UUID(args.run)), str(uuid.UUID(args.quarantine))
    print('R4A_RUN_RECOVERY_INVENTORY=READ_ONLY',flush=True)
    row = json.loads(sql("select json_build_object('runState',r.state,'controlVersion',r.control_version,'runFailure',r.failure_code,'quarantineState',q.lifecycle_state,'quarantineVersion',q.lifecycle_version,'reason',q.reason_code,'blocking',q.blocking,'payloadRefKind',case when q.payload_ref like 'lake://%' then 'LAKE' when q.payload_ref is null then 'ABSENT' else 'OTHER_REFERENCE_NOT_DURABILITY_PROOF' end,'attempts',(select count(*) from ouf_ingestion.processing_attempt a where a.run_id=r.run_id),'failedAttemptOne',(select count(*) from ouf_ingestion.processing_attempt a where a.run_id=r.run_id and a.source_object_id=q.source_object_id and a.attempt_no=1 and a.state='FAILED'),'handoffs',(select count(*) from ouf_ingestion.handoff_outbox h where h.run_id=r.run_id),'replays',(select count(*) from ouf_ingestion.replay_request x where x.quarantine_id=q.quarantine_id))::text from ouf_ingestion.ing_run r join ouf_ingestion.ing_quarantine q on q.run_id=r.run_id where r.run_id='"+run+"' and q.quarantine_id='"+quarantine+"'"))
    for key,value in row.items():
        if isinstance(value,bool):
            flag('RECOVERY_'+key.upper(),value)
        elif isinstance(value,int) or (isinstance(value,str) and re.fullmatch(r'[A-Z0-9_]{1,100}',value)):
            print('RECOVERY_'+key.upper()+'='+str(value))
        elif value is None:
            print('RECOVERY_'+key.upper()+'=ABSENT')
        else:
            raise RuntimeError('RECOVERY_METADATA_LAYOUT_UNSUPPORTED')
    helper = admin.inventory.routes.helper
    live = helper.inspect('ouf-ingestion')
    image = helper.inspect(live['Image'],'image')
    flag('RECOVERY_ING_RUNNING',live['State']['Running'])
    flag('RECOVERY_ING_REVISION_MATCH',image['Config'].get('Labels',{}).get('org.opencontainers.image.revision') == '0dfab1e7b2253fd939088259ea61754d6e56706c')
    apisix = helper.inspect('ouf-apisix')
    if not apisix['State']['Running']:
        raise RuntimeError('APISIX_NOT_RUNNING')
    key = admin.inventory.routes.admin_key(admin.inventory.routes.mounted_config(apisix).read_text())
    raw,_ = admin.api(key,'GET','routes')
    values = admin.inventory.routes.route_values(raw)
    targets = [('RUN_READ','GET','/api/trusted-human/v1/ingestion/runs/'+run),('RUN_RESUME','POST','/api/trusted-human/v1/ingestion/runs/'+run+'/resume'),('QUARANTINE_READ','GET','/api/trusted-human/v1/ingestion/quarantine/'+quarantine),('QUARANTINE_RETRY','POST','/api/trusted-human/v1/ingestion/quarantine/'+quarantine+'/retry'),('QUARANTINE_REPROCESS','POST','/api/trusted-human/v1/ingestion/quarantine/'+quarantine+'/reprocess')]
    for name,method,path in targets:
        found = admin.inventory.candidates(values,method,path)
        print('RECOVERY_'+name+'_ROUTE_COUNT='+str(len(found)))
        for index,route in enumerate(found,1):
            prefix = 'RECOVERY_'+name+'_'+str(index)+'_'
            plugins = route.get('plugins',{})
            oidc = plugins.get('openid-connect',{})
            flag(prefix+'ENABLED',route.get('status',1)==1)
            flag(prefix+'UPSTREAM_INGESTION',route.get('upstream',{}).get('nodes')=={'ouf-ingestion:8080':1})
            flag(prefix+'OIDC_ENABLED',bool(oidc) and not oidc.get('_meta',{}).get('disable',False))
            flag(prefix+'REWRITE_PRESENT',bool(plugins.get('proxy-rewrite')))
            scopes = oidc.get('required_scopes') or []
            if not isinstance(scopes,list) or any(not isinstance(s,str) or not re.fullmatch(r'[A-Za-z0-9._:-]{1,160}',s) for s in scopes):
                raise RuntimeError('RECOVERY_SCOPE_LAYOUT_UNSUPPORTED')
            print(prefix+'REQUIRED_SCOPES='+(','.join(scopes) or 'NONE_INLINE'))
    after = helper.inspect('ouf-ingestion')
    if any(after[k] != live[k] for k in ('Id','Image','Config','HostConfig','Mounts')):
        raise RuntimeError('INGESTION_CHANGED_DURING_READ')
    print('R4A_RUN_RECOVERY_INVENTORY=COMPLETE READ_ONLY=true LIVE_UNCHANGED=true RETRY=false REPLAY=false RUN_RESUME=false OWNER_AUTHORIZATION_NOT_PROVEN=true SECRETS_NOT_PRINTED=true')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',required=True)
    parser.add_argument('--quarantine',required=True)
    try:
        main(parser.parse_args())
    except Exception as error:
        code=str(error) if isinstance(error,RuntimeError) else type(error).__name__
        print('R4A_RUN_RECOVERY_INVENTORY=BLOCKED CODE='+code+' READ_ONLY=true RUN_RESUME=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
