#!/usr/bin/env python3
"""Controlled UDP application switch with private backup and ID-bound runtime rollback."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import uuid
import r4a_stage_udp_recovery as stage

SAFE_CODES={'FLYWAY_CHANGED','RUN_JOB_STATES_CHANGED','WORKER_NOT_IDLE','BACKUP_TOO_SMALL',
    'LIVE_NAME_REASSIGNED','OLD_NAME_REASSIGNED','ROLLBACK_NOT_HEALTHY','STAGE_NOT_READY',
    'RELEASE_EXISTS_RECONCILE','SNAPSHOT_CHANGED','STAGED_BINDING_CHANGED','STAGED_CONFIGURATION_CHANGED',
    'IMAGE_PROVENANCE_CHANGED','STAGED_HOST_CONFIGURATION_CHANGED','STAGED_SECURITY_DEFAULTS_CHANGED',
    'LIVE_HEALTH_UNAVAILABLE','LIVE_GATEWAY_HEALTH_UNAVAILABLE','PROBE_JOB_OUTSIDE_RUN','ROLLBACK_NAME_OCCUPIED',
    'GRACEFUL_STOP_FAILED','DRAIN_STATE_CHANGED','CANDIDATE_HEALTH_FAILED','GATEWAY_BACKEND_HEALTH_FAILED',
    'ANONYMOUS_OR_SPOOFED_REQUEST_NOT_DENIED','POST_RELEASE_DATABASE_STATE_CHANGED','FINAL_RUNTIME_STATE_CHANGED'}


def safe_code(error):return str(error) if isinstance(error,ValueError) and str(error) in SAFE_CODES else 'UNCLASSIFIED'


def query(args,sql):
    return stage.docker('exec',args.postgres_container,'psql','-X','-qAt','-v','ON_ERROR_STOP=1',
        '-U',args.db_user,'-d',args.database,'-c',"begin read only; set local statement_timeout='15s'; "+sql+'; rollback;')


def database_state(args):
    schema=json.loads(query(args,"select coalesce(json_agg(q order by installed_rank),'[]'::json) from "
        "(select installed_rank,version,script,checksum,success from ouf_udp.flyway_schema_history) q"))
    if not schema or schema[-1]['version']!=args.expected_flyway or any(not r['success'] for r in schema):
        raise ValueError('FLYWAY_CHANGED')
    rows=json.loads(query(args,"select coalesce(json_agg(q order by job_id),'[]'::json) from "
        "(select j.job_id,j.handoff_id,j.state,j.state_version,j.attempts,j.integrity_attempts,j.safe_failure_code,"
        "h.state intake_state from ouf_udp.materialization_job j join ouf_udp.handoff_intake h using(handoff_id) "
        "where h.source_id='"+args.source+"' and h.ingestion_run_id='"+args.run+"') q"))
    if (len(rows)!=args.expected_job_count or sum(r['state']=='SUCCEEDED' for r in rows)!=args.expected_succeeded
            or sum(r['state']=='QUARANTINED' for r in rows)!=args.expected_quarantined):raise ValueError('RUN_JOB_STATES_CHANGED')
    if query(args,"select count(*) from ouf_udp.materialization_job where state in ('READY','RUNNING')")!='0':
        raise ValueError('WORKER_NOT_IDLE')
    return {'schema':schema,'original_jobs':rows}


def status(args,container,url,spoof=False):
    cmd=['run','--rm','--pull','never','--network','container:'+container,'--read-only','--cap-drop','ALL',
         '--security-opt','no-new-privileges',args.curl_image,'--max-time','3','-sS','-o','/dev/null','-w','%{http_code}']
    if spoof:cmd+=['-H','X-Actor-Type: HUMAN','-H','X-Principal-Id: '+str(uuid.uuid4())]
    try:return stage.docker(*cmd,url)
    except subprocess.SubprocessError:return 'UNAVAILABLE'


def healthy(args,container,attempts):
    for number in range(attempts):
        if stage.inspect(container)['State']['Running'] and status(args,container,args.health_origin+args.health_path)=='200':return True
        if number and number%10==0:print('R4A_UDP_RECOVERY_HEALTH_CHECK='+str(number),flush=True)
        if number+1<attempts:time.sleep(2)
    return False


def backup(args,root):
    path=root/'udp-before-release.dump'
    with path.open('xb') as out:
        subprocess.run(['docker','exec',args.postgres_container,'pg_dump','-U',args.db_user,'-d',args.database,'-Fc'],
            stdout=out,stderr=subprocess.PIPE,check=True,timeout=600)
        out.flush();os.fsync(out.fileno())
    if path.stat().st_size<1024:raise ValueError('BACKUP_TOO_SMALL')
    with path.open('rb') as source:
        subprocess.run(['docker','exec','-i',args.postgres_container,'pg_restore','-l'],stdin=source,
            stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,check=True,timeout=90)
    sha=hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda:source.read(1024*1024),b''):sha.update(chunk)
    return {'path':str(path),'bytes':path.stat().st_size,'sha256':sha.hexdigest(),'restore_list_valid':True}


def restart_policy(value):
    name=value['Name']
    return name+':'+str(value.get('MaximumRetryCount',0)) if name=='on-failure' else name


def rollback(args,evidence):
    old_id,new_id=evidence['old_id'],evidence['new_id'];live=evidence['live_name']
    names=stage.docker('ps','-a','--format','{{.Names}}').splitlines()
    if live in names and stage.inspect(live)['Id'] not in (old_id,new_id):raise ValueError('LIVE_NAME_REASSIGNED')
    new=stage.inspect(new_id)
    stage.docker('update','--restart','no',new_id)
    if new['State']['Running']:stage.docker('stop','--time',str(args.stop_seconds),new_id)
    if stage.inspect(new_id)['Name'].lstrip('/')==live:stage.docker('rename',new_id,evidence['failed_name'])
    old=stage.inspect(old_id)
    if old['Name'].lstrip('/')!=live:
        if old['Name'].lstrip('/')!=evidence['rollback_name']:raise ValueError('OLD_NAME_REASSIGNED')
        stage.docker('rename',old_id,live)
    stage.docker('update','--restart',restart_policy(evidence['restart_policy']),old_id)
    if not stage.inspect(old_id)['State']['Running']:stage.docker('start',old_id)
    if not healthy(args,old_id,args.health_attempts):raise ValueError('ROLLBACK_NOT_HEALTHY')


def validate(args):
    args.run=str(uuid.UUID(args.run));args.probe_job=str(uuid.UUID(args.probe_job))
    for value in (args.source,args.postgres_container,args.database,args.db_user,args.gateway_container):
        if not re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,159}',value):raise ValueError('BINDING_INVALID')
    if not re.fullmatch('[A-Za-z0-9][A-Za-z0-9._:/@-]{0,255}',args.curl_image):raise ValueError('IMAGE_INVALID')
    # Health URLs are installation bindings, restricted to clear internal HTTP for this Docker release profile.
    for value in (args.health_origin,args.gateway_health_url):
        if not re.fullmatch(r'http://[A-Za-z0-9._-]+:[0-9]{1,5}(?:/[A-Za-z0-9_./-]+)?',value):raise ValueError('HEALTH_URL_INVALID')
    if not re.fullmatch('/[A-Za-z0-9_/-]+',args.health_path):raise ValueError('HEALTH_PATH_INVALID')
    if not 1<=args.health_attempts<=90 or not 45<=args.stop_seconds<=300:raise ValueError('TIME_BOUNDS_INVALID')
    if args.expected_job_count!=args.expected_succeeded+args.expected_quarantined:raise ValueError('COUNTS_INVALID')
    if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)*',args.expected_flyway):raise ValueError('FLYWAY_BINDING_INVALID')


def main(args):
    if os.geteuid()!=0:raise ValueError('ROOT_REQUIRED')
    validate(args);os.umask(0o077)
    path=Path(args.stage_receipt);stage.private_file(path);staged=json.loads(path.read_text())
    if staged.get('state')!='STAGED' or staged.get('candidate_stopped') is not True:raise ValueError('STAGE_NOT_READY')
    root=path.parent
    if root.stat().st_uid!=0 or root.stat().st_mode&0o077:raise ValueError('PRIVATE_STAGE_REQUIRED')
    lock=root.parent/('release-lock-'+hashlib.sha256(staged['live_name'].encode()).hexdigest())
    descriptor=os.open(lock,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    with os.fdopen(descriptor,'r+') as locked:
        fcntl.flock(locked,fcntl.LOCK_EX|fcntl.LOCK_NB)
        release(args,staged,root)


def release(args,staged,root):
    receipt=root/'release-receipt.json'
    if receipt.exists() or receipt.is_symlink():raise ValueError('RELEASE_EXISTS_RECONCILE')
    stage.private_file(Path(staged['runtime_snapshot']))
    before=json.loads(Path(staged['runtime_snapshot']).read_text())
    if stage.digest(before)!=staged['runtime_snapshot_hash']:raise ValueError('SNAPSHOT_CHANGED')
    live=stage.inspect(staged['live_id']);new=stage.inspect(staged['candidate_id'])
    if (stage.identity(live)!=stage.identity(before) or live['Name'].lstrip('/')!=staged['live_name']
            or stage.digest(live['Config'])!=stage.digest(before['Config'])
            or stage.digest(live['HostConfig'])!=stage.digest(before['HostConfig'])
            or new['Name'].lstrip('/')!=staged['candidate_name'] or new['State']['Status']!='created'
            or new['Image']!=staged['candidate_image_id'] or new['HostConfig']['RestartPolicy']['Name']!='no'):
        raise ValueError('STAGED_BINDING_CHANGED')
    env=dict(x.split('=',1) for x in live['Config']['Env']);env[stage.FLAG]='true'
    if dict(x.split('=',1) for x in new['Config']['Env'])!=env or stage.mount_set(live)!=stage.mount_set(new):
        raise ValueError('STAGED_CONFIGURATION_CHANGED')
    image=stage.inspect(new['Image']);old_image=stage.inspect(live['Image'])
    if (image['Config'].get('Labels') or {}).get('org.opencontainers.image.revision')!=staged['revision']:
        raise ValueError('IMAGE_PROVENANCE_CHANGED')
    old_network,_,_=stage.profile(live,old_image,image)
    new_network,_,_=stage.profile(new,image,image)
    if (old_network!=new_network or new['Config']['User']!=live['Config']['User']
            or new['HostConfig'].get('LogConfig')!=live['HostConfig'].get('LogConfig')):raise ValueError('STAGED_HOST_CONFIGURATION_CHANGED')
    for key in ('MaskedPaths','ReadonlyPaths','CgroupnsMode','IpcMode','ShmSize','Runtime'):
        if new['HostConfig'].get(key)!=live['HostConfig'].get(key):raise ValueError('STAGED_SECURITY_DEFAULTS_CHANGED')
    # Compiler/probe images are not used as the application. No implicit curl image pull either.
    stage.inspect(args.curl_image)
    if not stage.inspect(args.gateway_container)['State']['Running'] or not healthy(args,live['Id'],1):raise ValueError('LIVE_HEALTH_UNAVAILABLE')
    if status(args,args.gateway_container,args.gateway_health_url)!='200':raise ValueError('LIVE_GATEWAY_HEALTH_UNAVAILABLE')
    baseline=database_state(args)
    if not any(r['job_id']==args.probe_job for r in baseline['original_jobs']):raise ValueError('PROBE_JOB_OUTSIDE_RUN')
    evidence={'state':'PREPARED','old_id':live['Id'],'new_id':new['Id'],'live_name':staged['live_name'],
        'rollback_name':staged['live_name']+'-rollback-'+live['Id'][:12],
        'failed_name':staged['live_name']+'-failed-'+new['Id'][:12],
        'restart_policy':live['HostConfig']['RestartPolicy'],'original_database_state':baseline,
        'candidate_image_id':new['Image'],'revision':staged['revision'],'retry_executed':False,'database_restored':False}
    occupied=stage.docker('ps','-a','--format','{{.Names}}').splitlines()
    if evidence['rollback_name'] in occupied or evidence['failed_name'] in occupied:raise ValueError('ROLLBACK_NAME_OCCUPIED')
    def save():
        temporary=root/'release-receipt.tmp'
        with temporary.open('w') as stream:
            stream.write(json.dumps(evidence,sort_keys=True,indent=2)+'\n');stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,receipt)
        directory=os.open(root,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(directory)
        finally:os.close(directory)
    save();print('R4A_UDP_RECOVERY_RELEASE_RECEIPT='+str(receipt)+' PRIVATE=true',flush=True)
    try:
        evidence['state']='STOP_INTENT';save()
        stage.docker('update','--restart','no',live['Id'])
        print('R4A_UDP_RECOVERY_RELEASE_STOPPING_LIVE=true',flush=True)
        stage.docker('stop','--time',str(args.stop_seconds),live['Id'])
        stopped=stage.inspect(live['Id'])
        if stopped['State']['Running'] or stopped['State'].get('OOMKilled') or stopped['State'].get('ExitCode') not in (0,143):
            raise ValueError('GRACEFUL_STOP_FAILED')
        if database_state(args)!=baseline:raise ValueError('DRAIN_STATE_CHANGED')
        evidence['state']='BACKUP_INTENT';save();evidence['backup']=backup(args,root);save()
        print('R4A_UDP_RECOVERY_RELEASE_BACKUP=PASS RESTORE_LIST=true PRIVATE=true',flush=True)
        evidence['state']='SWITCH_INTENT';save()
        stage.docker('rename',live['Id'],evidence['rollback_name'])
        stage.docker('rename',new['Id'],evidence['live_name'])
        stage.docker('start',new['Id'])
        if not healthy(args,new['Id'],args.health_attempts):raise ValueError('CANDIDATE_HEALTH_FAILED')
        if status(args,args.gateway_container,args.gateway_health_url)!='200':raise ValueError('GATEWAY_BACKEND_HEALTH_FAILED')
        protected=args.health_origin+'/api/udp/v1/governance/materialization/jobs/'+args.probe_job
        if status(args,new['Id'],protected) not in ('401','403') or status(args,new['Id'],protected,True) not in ('401','403'):
            raise ValueError('ANONYMOUS_OR_SPOOFED_REQUEST_NOT_DENIED')
        if database_state(args)!=baseline:raise ValueError('POST_RELEASE_DATABASE_STATE_CHANGED')
        stage.docker('update','--restart',restart_policy(evidence['restart_policy']),new['Id'])
        if (not stage.inspect(new['Id'])['State']['Running'] or stage.inspect(live['Id'])['State']['Running']
                or stage.inspect(live['Id'])['HostConfig']['RestartPolicy']['Name']!='no'):
            raise ValueError('FINAL_RUNTIME_STATE_CHANGED')
        evidence['state']='RELEASED';save()
        print('R4A_UDP_RECOVERY_RELEASE=PASS LIVE_IMAGE_ID='+new['Image']+' FLYWAY='+args.expected_flyway+
            ' ORIGINAL_JOBS_UNCHANGED=true GATEWAY_BACKEND_HEALTH=true ANONYMOUS_AND_SPOOF_DENIED=true HUMAN_AUTHORIZATION_NOT_PROVEN=true RETRY=false SECRETS_NOT_PRINTED=true',flush=True)
        print('R4A_UDP_RECOVERY_ROLLBACK_CONTAINER='+evidence['rollback_name']+' STOPPED=true RESTART_DISABLED=true',flush=True)
    except BaseException as error:
        evidence.update(state='ROLLBACK_INTENT',failure_type=type(error).__name__,failure_code=safe_code(error))
        try:save()
        except OSError:evidence['receipt_persistence_unverified']=True
        try:rollback(args,evidence);evidence['state']='ROLLED_BACK'
        except BaseException:evidence['state']='MANUAL_RECONCILIATION_REQUIRED'
        try:save()
        except OSError:evidence['receipt_persistence_unverified']=True
        print('R4A_UDP_RECOVERY_RELEASE_ROLLBACK='+evidence['state']+' FAILURE_CODE='+evidence['failure_code']+' DATABASE_RESTORED=false SECRETS_NOT_PRINTED=true',flush=True)
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('stage-receipt','postgres-container','database','db-user','gateway-container','curl-image',
                 'health-origin','health-path','gateway-health-url','expected-flyway','source','run','probe-job'):
        parser.add_argument('--'+name,required=True)
    for name in ('stop-seconds','health-attempts','expected-job-count','expected-succeeded','expected-quarantined'):
        parser.add_argument('--'+name,required=True,type=int)
    try:main(parser.parse_args())
    except Exception as error:
        print('R4A_UDP_RECOVERY_RELEASE=BLOCKED TYPE='+type(error).__name__+' FAILURE_CODE='+safe_code(error)+' RECONCILE_RECEIPT_BEFORE_REPEAT=true RETRY=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
