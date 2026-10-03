#!/usr/bin/env python3
"""Stage/adopt a shared UDP lake profile on the same image with runtime rollback."""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import time
import uuid
import r4a_prepare_frozen_compatibility_probe as runtime
import r4a_runtime_lake_prerequisites as lake
import r4a_runtime_intake_refresher as queues

ROOT = Path('/etc/ouf/deploy-snapshots')
STATE = ROOT / 'udp-lake-profile-prepare.json'
RECEIPT = ROOT / 'udp-lake-profile-switch.json'
LIVE = 'ouf-udp'
CANDIDATE = 'ouf-udp-lake-profile-candidate'


def docker(*args):
    return runtime.run(['docker', *args], timeout=90)


def optional(name):
    return runtime.inspect(name) if name in docker('container','ls','--all','--format','{{.Names}}').splitlines() else None


def stable(doc):
    return {k:doc[k] for k in ('Id','Image','Config','HostConfig','Mounts')}


def mounts(doc):
    return sorted((m['Type'],m['Source'],m['Destination'],m['RW']) for m in doc['Mounts'])


def profile(args):
    if not 1 <= args.days <= 36500 or args.retention_class not in lake.RETENTIONS or args.access_label not in lake.LABELS:
        raise RuntimeError('LAKE_PROFILE_INVALID')
    return {'OUF_UDP_RAW_RETENTION_DAYS':str(args.days),'OUF_UDP_RAW_RETENTION_CLASS':args.retention_class,'OUF_UDP_RAW_ACCESS_LABEL':args.access_label}


def guard(old):
    image = runtime.inspect(old['Image'],'image')
    host, config = old['HostConfig'], old['Config']
    unsupported = ('PortBindings','Binds','VolumesFrom','Privileged','ReadonlyRootfs','ExtraHosts','Dns','DnsSearch','CapAdd','SecurityOpt','Devices','Tmpfs','AutoRemove','Init','Ulimits','CapDrop','GroupAdd','Memory','MemorySwap','NanoCpus','CpuShares','PidsLimit','OomKillDisable','CpusetCpus','CpusetMems','UsernsMode','PidMode','Sysctls')
    if (not old['State']['Running'] or image['Config'].get('Labels',{}).get('org.opencontainers.image.revision') != lake.REVISION or
        host.get('NetworkMode') != 'ouf-backend' or set(old['NetworkSettings']['Networks']) != {'ouf-backend'} or
        config.get('User') != '10004:10004' or host.get('RestartPolicy',{}).get('Name') != 'unless-stopped' or
        host.get('LogConfig',{}).get('Type') != 'json-file' or config.get('Healthcheck') or any(host.get(k) for k in unsupported) or
        any(config.get(k) != image['Config'].get(k) for k in ('User','Entrypoint','Cmd','WorkingDir'))):
        raise RuntimeError('UDP_RUNTIME_SETTINGS_UNSUPPORTED')
    lake.environment(old)
    if any('\n' in item or '\r' in item or '=' not in item for item in config.get('Env',[])):
        raise RuntimeError('UDP_ENV_FORMAT_UNSUPPORTED')
    if any(kind != 'bind' or any(c in source+target for c in ',\n\r') for kind,source,target,_ in mounts(old)):
        raise RuntimeError('UDP_MOUNTS_UNSUPPORTED')


def candidate_matches(candidate, old, values, running=False):
    expected = lake.environment(old) | values
    return (candidate['Image'] == old['Image'] and candidate['State']['Running'] == running and
        (running or candidate['State']['Status'] == 'created') and lake.environment(candidate) == expected and
        mounts(candidate) == mounts(old) and candidate['HostConfig'].get('NetworkMode') == 'ouf-backend' and
        set(candidate['NetworkSettings']['Networks']) == {'ouf-backend'} and
        candidate['HostConfig'].get('LogConfig') == old['HostConfig'].get('LogConfig') and
        candidate['HostConfig'].get('RestartPolicy',{}).get('Name') == ('unless-stopped' if running else 'no') and
        all(candidate['Config'].get(k) == old['Config'].get(k) for k in ('User','Entrypoint','Cmd','WorkingDir')))


def sql(query, database='ouf_udp'):
    return docker('exec','ouf-postgres','psql','-X','-qAt','-v','ON_ERROR_STOP=1','-U',database,'-d',database,'-c','begin read only; set local statement_timeout=15000; '+query+'; rollback;')


def history():
    return json.loads(sql("select coalesce(json_agg(json_build_object('version',version,'script',script,'checksum',checksum,'success',success,'type',type) order by installed_rank),'[]'::json)::text from ouf_udp.flyway_schema_history"))


def exposure():
    snapshot = queues.snapshot()
    udp = json.loads(sql("select json_build_object('busyJobs',(select count(*) from ouf_udp.materialization_job where state <> 'SUCCEEDED'),'intakeCount',(select count(*) from ouf_udp.handoff_intake),'jobCount',(select count(*) from ouf_udp.materialization_job),'lakeCount',(select count(*) from ouf_udp.lake_object))::text"))
    if udp['busyJobs']:
        raise RuntimeError('UDP_MATERIALIZATION_NOT_QUIESCENT')
    return {'ingestionAndPublication':snapshot,'udp':udp}


def health(attempts=1):
    for n in range(attempts):
        if not runtime.inspect(LIVE)['State']['Running']:
            raise RuntimeError('UDP_NOT_RUNNING')
        try:
            code = docker('run','--rm','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--network','container:'+LIVE,'curlimages/curl:8.16.0','--max-time','3','-sS','-o','/dev/null','-w','%{http_code}','http://127.0.0.1:8080/actuator/health')
            if code == '200':
                return
        except subprocess.SubprocessError:
            pass
        if n and n % 10 == 0:
            print('R4A_UDP_LAKE_PROFILE_HEALTH_WAIT_SECONDS='+str(n*2),flush=True)
        time.sleep(2)
    raise RuntimeError('UDP_HEALTH_TIMEOUT')


def gateway_health():
    code = docker('run','--rm','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--network','container:ouf-apisix','curlimages/curl:8.16.0','--max-time','5','-sS','-o','/dev/null','-w','%{http_code}','http://ouf-udp:8080/actuator/health')
    if code != '200':
        raise RuntimeError('GATEWAY_TO_UDP_UNREACHABLE')


def backup_restore(before):
    env = lake.environment(runtime.inspect('ouf-postgres'))
    user = env.get('POSTGRES_USER','')
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,62}',user):
        raise RuntimeError('BACKUP_ADMIN_USER_UNSUPPORTED')
    fd,name = tempfile.mkstemp(prefix='udp-before-lake-profile-',suffix='.dump',dir=ROOT)
    path = Path(name)
    print('R4A_UDP_LAKE_PROFILE_DB_BACKUP='+str(path)+' PRIVATE=true',flush=True)
    with os.fdopen(fd,'wb') as output:
        subprocess.run(['docker','exec','ouf-postgres','pg_dump','-U',user,'-d','ouf_udp','-Fc'],stdout=output,stderr=subprocess.PIPE,check=True,timeout=600)
        output.flush()
        os.fsync(output.fileno())
    if path.stat().st_size < 1024:
        raise RuntimeError('BACKUP_TOO_SMALL')
    scratch = 'ouf_lake_profile_restore_'+uuid.uuid4().hex[:12]
    docker('exec','ouf-postgres','createdb','-U',user,scratch)
    try:
        with path.open('rb') as source:
            subprocess.run(['docker','exec','-i','ouf-postgres','pg_restore','-U',user,'--no-owner','--no-acl','-d',scratch],stdin=source,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,check=True,timeout=600)
        result = docker('exec','ouf-postgres','psql','-X','-qAt','-v','ON_ERROR_STOP=1','-U',user,'-d',scratch,'-c',"select coalesce(json_agg(json_build_object('version',version,'script',script,'checksum',checksum,'success',success,'type',type) order by installed_rank),'[]'::json)::text from ouf_udp.flyway_schema_history")
        if json.loads(result) != before:
            raise RuntimeError('BACKUP_RESTORE_HISTORY_MISMATCH')
    finally:
        docker('exec','ouf-postgres','dropdb','-U',user,scratch)
    print('R4A_UDP_LAKE_PROFILE_DB_RESTORE_TO_SCRATCH=PASS BACKUP_RETAINED=true',flush=True)
    return str(path)


def recover(state, previous, failed):
    old_id, new_id = state['old']['Id'], state['candidateId']
    current = optional(LIVE)
    if current and current['Id'] == new_id:
        docker('update','--restart','no',LIVE)
        if current['State']['Running']:
            docker('stop','--time','30',LIVE)
        if optional(failed):
            raise RuntimeError('FAILED_CONTAINER_NAME_OCCUPIED')
        docker('rename',LIVE,failed)
        current = None
    if current is None:
        if runtime.inspect(previous)['Id'] != old_id:
            raise RuntimeError('ROLLBACK_CONTAINER_ID_MISMATCH')
        docker('rename',previous,LIVE)
    elif current['Id'] != old_id:
        raise RuntimeError('ROLLBACK_LIVE_ID_MISMATCH')
    docker('update','--restart','unless-stopped',LIVE)
    if not runtime.inspect(LIVE)['State']['Running']:
        docker('start',LIVE)
    health(25)
    restored = runtime.inspect(LIVE)
    if lake.environment(restored) != lake.environment(state['old']) or restored['Image'] != state['old']['Image'] or mounts(restored) != mounts(state['old']):
        raise RuntimeError('ROLLBACK_READBACK_MISMATCH')


def main(args):
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    os.umask(0o077)
    rm = ROOT.lstat()
    if not stat.S_ISDIR(rm.st_mode) or rm.st_uid != 0 or stat.S_IMODE(rm.st_mode) != 0o700:
        raise RuntimeError('PRIVATE_ROOT_UNSAFE')
    if RECEIPT.exists() or RECEIPT.is_symlink():
        raise RuntimeError('SWITCH_RECEIPT_EXISTS_RECONCILE')
    values = profile(args)
    old = runtime.inspect(LIVE)
    guard(old)
    overrides, checks, _ = lake.facts(old,args.tenant)
    if any(overrides.values()) or any(not v for k,v in checks.items() if not k.startswith('RAW_')):
        raise RuntimeError('UDP_BASE_BINDINGS_NOT_READY')
    before = exposure()
    migrations = history()
    if not migrations or any(not x['success'] for x in migrations) or max(int(x['version']) for x in migrations if x['version'] and str(x['version']).isdigit()) != 34:
        raise RuntimeError('UDP_FLYWAY_NOT_34')
    health()
    if args.mode == 'prepare':
        if STATE.exists() or STATE.is_symlink() or optional(CANDIDATE):
            raise RuntimeError('PREPARATION_EXISTS_RECONCILE')
        state = dict(status='PREPARING',tenant=args.tenant,profile=values,old=old,queues=before,history=migrations,candidateId=None)
        queues.save(STATE,state,True)
        folder = Path(tempfile.mkdtemp(prefix='udp-lake-profile-',dir=ROOT))
        env_file = folder/'candidate.env'
        created = None
        try:
            expected = lake.environment(old) | values
            queues.write(env_file, ('\n'.join(k+'='+v for k,v in expected.items())+'\n').encode(),True)
            command = ['create','--name',CANDIDATE,'--network','ouf-backend','--network-alias',LIVE,'--restart','no','--user','10004:10004','--log-driver','json-file','--env-file',str(env_file)]
            for k,v in old['HostConfig']['LogConfig'].get('Config',{}).items():
                command += ['--log-opt',k+'='+v]
            for _,source,target,writable in mounts(old):
                command += ['--mount','type=bind,src='+source+',dst='+target+('' if writable else ',readonly')]
            created = docker(*command,old['Image'])
            candidate = runtime.inspect(CANDIDATE)
            if candidate['Id'] != created or not candidate_matches(candidate,old,values) or stable(runtime.inspect(LIVE)) != stable(old) or exposure() != before:
                raise RuntimeError('CANDIDATE_OR_LIVE_READBACK_MISMATCH')
            state.update(status='PASS',candidateId=created)
            queues.save(STATE,state)
        except BaseException:
            state['status']='PREPARATION_FAILED_RECONCILE'
            queues.save(STATE,state)
            if created and optional(CANDIDATE) and runtime.inspect(CANDIDATE)['Id'] == created and not runtime.inspect(CANDIDATE)['State']['Running']:
                docker('rm',CANDIDATE)
            raise
        finally:
            env_file.unlink(missing_ok=True)
        print('R4A_UDP_LAKE_PROFILE_PREPARE=PASS STOPPED=true SAME_IMAGE=true LIVE_UNCHANGED=true RUN_RESUME=false SECRETS_NOT_PRINTED=true')
        return
    state = queues.private(STATE)
    candidate = runtime.inspect(CANDIDATE)
    if (state.get('status') != 'PASS' or state['tenant'] != args.tenant or state['profile'] != values or stable(state['old']) != stable(old) or
        candidate['Id'] != state['candidateId'] or not candidate_matches(candidate,old,values) or state['history'] != migrations or state['queues'] != before):
        raise RuntimeError('PREPARED_PROFILE_CONTEXT_DRIFT')
    previous = 'ouf-udp-lake-profile-rollback-'+old['Id'][:12]
    failed = 'ouf-udp-lake-profile-failed-'+candidate['Id'][:12]
    if optional(previous) or optional(failed):
        raise RuntimeError('ROLLBACK_NAME_OCCUPIED')
    print('R4A_UDP_LAKE_PROFILE_PLAN=PASS MODE='+args.mode+' SAME_IMAGE=true FLYWAY=34 RETENTION_DAYS='+str(args.days)+' RETENTION_CLASS='+args.retention_class+' ACCESS_LABEL='+args.access_label,flush=True)
    if args.mode == 'plan':
        print('R4A_UDP_LAKE_PROFILE=PLANNED LIVE_UNCHANGED=true RUN_RESUME=false')
        return
    receipt = dict(status='STARTING',profile=values,tenant=args.tenant,candidateId=candidate['Id'],rollbackContainer=previous,backup=None,runResume=False)
    queues.save(RECEIPT,receipt,True)
    try:
        if stable(runtime.inspect(LIVE)) != stable(old) or exposure() != before:
            raise RuntimeError('CONTEXT_CHANGED_BEFORE_STOP')
        print('R4A_UDP_LAKE_PROFILE=STOPPING_LIVE RUN_RESUME=false',flush=True)
        docker('update','--restart','no',LIVE)
        docker('stop','--time','60',LIVE)
        receipt['backup'] = backup_restore(migrations)
        queues.save(RECEIPT,receipt)
        if exposure() != before or history() != migrations:
            raise RuntimeError('QUEUES_OR_FLYWAY_CHANGED_DURING_BACKUP')
        docker('rename',LIVE,previous)
        docker('rename',CANDIDATE,LIVE)
        docker('start',LIVE)
        health(45)
        gateway_health()
        docker('update','--restart','unless-stopped',LIVE)
        current = runtime.inspect(LIVE)
        guard(current)
        overrides, checks, _ = lake.facts(current,args.tenant)
        if current['Id'] != state['candidateId'] or not candidate_matches(current,old,values,True) or any(overrides.values()) or not all(checks.values()) or history() != migrations or exposure() != before:
            raise RuntimeError('POST_SWITCH_READBACK_MISMATCH')
        receipt['status']='PASS'
        queues.save(RECEIPT,receipt)
        print('R4A_UDP_LAKE_PROFILE=PASS SAME_IMAGE=true PROFILE_MATCH=true IAM_AND_S3_PRESERVED=true FLYWAY_UNCHANGED=true QUEUES_UNCHANGED=true')
        print('R4A_UDP_LAKE_PROFILE_RECEIPT='+str(RECEIPT)+' PRIVATE=true')
        print('R4A_UDP_LAKE_PROFILE_ROLLBACK_CONTAINER='+previous)
        print('R4A_UDP_LAKE_PROFILE_COMPLETE=PASS RUN_RESUME=false INTAKE_POST=false S3_AUTHORIZATION_NOT_PROVEN=true SECRETS_NOT_PRINTED=true')
    except BaseException:
        try:
            recover(state,previous,failed)
            receipt['status']='ROLLED_BACK'
        except BaseException:
            receipt['status']='MANUAL_RECOVERY_REQUIRED'
        queues.save(RECEIPT,receipt)
        print('R4A_UDP_LAKE_PROFILE_RECOVERY='+receipt['status']+' DB_NOT_AUTOMATICALLY_RESTORED=true',flush=True)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=('prepare','plan','apply'),required=True)
    parser.add_argument('--tenant',required=True)
    parser.add_argument('--days',type=int,required=True)
    parser.add_argument('--retention-class',choices=sorted(lake.RETENTIONS),required=True)
    parser.add_argument('--access-label',choices=sorted(lake.LABELS),required=True)
    try:
        main(parser.parse_args())
    except Exception as error:
        code = str(error) if isinstance(error,RuntimeError) else type(error).__name__
        print('R4A_UDP_LAKE_PROFILE=BLOCKED CODE='+code+' RUN_RESUME=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
