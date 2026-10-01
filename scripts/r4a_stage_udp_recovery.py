#!/usr/bin/env python3
"""Stage a stopped recovery container and private runtime snapshot; no live switch."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

FLAG='OUF_UDP_MATERIALIZATION_RECOVERY_ENABLED'


class StageError(ValueError):
    """Static symbolic stage failure, safe to report without private values."""


def docker(*args):
    return subprocess.run(['docker',*args],capture_output=True,text=True,check=True,timeout=60).stdout.strip()


def inspect(name):return json.loads(docker('inspect',name))[0]


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def mount_set(row):
    return sorted((m['Type'],m['Source'],m['Destination'],bool(m['RW']),m.get('Propagation',''))
                  for m in row.get('Mounts',[]))


def identity(row):
    return (row['Id'],row['Image'],row['State']['Running'],row['State']['StartedAt'],row['RestartCount'])


def profile(live,old_image,image):
    host,config=live['HostConfig'],live['Config']
    networks=live['NetworkSettings']['Networks']
    if len(networks)!=1 or host['NetworkMode'] not in networks:raise StageError('SINGLE_NAMED_NETWORK_REQUIRED')
    forbidden=('PortBindings','Binds','VolumesFrom','Privileged','ReadonlyRootfs','ExtraHosts','Dns','DnsSearch',
        'DnsOptions','CapAdd','SecurityOpt','Devices','DeviceRequests','Tmpfs','AutoRemove','Init','Ulimits',
        'CapDrop','GroupAdd','Memory','MemorySwap','MemoryReservation','NanoCpus','CpuShares','PidsLimit',
        'OomKillDisable','CpusetCpus','CpusetMems','UsernsMode','PidMode','Sysctls','CgroupParent','Cgroup',
        'CpuPeriod','CpuQuota','CpuRealtimePeriod','CpuRealtimeRuntime','BlkioWeight','BlkioWeightDevice',
        'BlkioDeviceReadBps','BlkioDeviceWriteBps','BlkioDeviceReadIOps','BlkioDeviceWriteIOps','Runtime')
    for key in forbidden:
        value=host.get(key)
        if key=='Runtime' and value in (None,'','runc'):continue
        if value:raise StageError('UNSUPPORTED_HOST_SETTING')
    if host.get('IpcMode') not in ('private',''):raise StageError('UNSUPPORTED_IPC_MODE')
    if host.get('ShmSize')!=64*1024*1024:raise StageError('UNSUPPORTED_SHM_SIZE')
    if host.get('RestartPolicy',{}).get('Name') not in ('no','always','unless-stopped','on-failure'):
        raise StageError('RESTART_POLICY_INVALID')
    if config.get('Tty') or config.get('OpenStdin'):raise StageError('INTERACTIVE_LIVE_UNSUPPORTED')
    if config.get('Domainname') or config.get('StopTimeout') is not None or config.get('Hostname')!=live['Id'][:12]:
        raise StageError('CUSTOM_CONTAINER_SETTING_UNSUPPORTED')
    if not re.fullmatch(r'[1-9][0-9]*:[1-9][0-9]*',config.get('User','')):raise StageError('NUMERIC_NONROOT_USER_REQUIRED')
    for key in ('User','Entrypoint','Cmd','WorkingDir','StopSignal','Healthcheck','ExposedPorts','Volumes'):
        if config.get(key)!=old_image['Config'].get(key) or config.get(key)!=image['Config'].get(key):
            raise StageError('IMAGE_RUNTIME_DEFAULTS_CHANGED')
    endpoint=next(iter(networks.values()))
    if endpoint.get('IPAMConfig') or endpoint.get('Links'):
        raise StageError('CUSTOM_NETWORK_BINDING_UNSUPPORTED')
    if any(not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,252}',alias) for alias in endpoint.get('Aliases') or []):
        raise StageError('NETWORK_ALIAS_INVALID')
    mounts=mount_set(live)
    if any(kind!='bind' or propagation!='rprivate' or ',' in source or ',' in destination
           for kind,source,destination,rw,propagation in mounts):raise StageError('MOUNT_PROFILE_UNSUPPORTED')
    for mount in host.get('Mounts') or []:
        options=mount.get('BindOptions') or {}
        if any(value for key,value in options.items() if key!='Propagation'):
            raise StageError('BIND_OPTIONS_UNSUPPORTED')
    env={}
    for entry in config.get('Env') or []:
        key,sep,value=entry.partition('=')
        if not sep or not re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',key) or key in env or '\n' in value or '\r' in value:
            raise StageError('ENVIRONMENT_UNSUPPORTED')
        env[key]=value
    return host['NetworkMode'],mounts,env


def private_file(path):
    info=path.stat()
    if path.is_symlink() or not path.is_file() or info.st_uid!=0 or info.st_mode&0o077:
        raise StageError('PRIVATE_RECEIPT_REQUIRED')


def main(args):
    if os.geteuid()!=0:raise StageError('ROOT_REQUIRED')
    for value in (args.container,args.candidate_container):
        if not re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,159}',value):raise StageError('NAME_INVALID')
    if args.container==args.candidate_container:raise StageError('DISTINCT_NAMES_REQUIRED')
    private_file(Path(args.build_receipt));build=json.loads(Path(args.build_receipt).read_text())
    if (build.get('state')!='BUILT' or build.get('service_switched') is not False
            or not re.fullmatch('[a-f0-9]{40}',build.get('revision',''))
            or not re.fullmatch('sha256:[a-f0-9]{64}',build.get('image_id',''))):raise StageError('BUILD_RECEIPT_INVALID')
    parent=Path(args.work_parent)
    if (not parent.is_absolute() or parent.is_symlink() or not parent.is_dir() or parent.stat().st_uid!=0
            or parent.stat().st_mode&0o022):raise StageError('PRIVATE_WORK_PARENT_REQUIRED')
    live=inspect(args.container)
    if not live['State']['Running'] or live['Id']!=build['live_before']['id'] or live['Image']!=build['live_before']['image']:
        raise StageError('LIVE_BINDING_CHANGED')
    image=inspect(build['image_id']);old_image=inspect(live['Image'])
    if image['Id']!=build['image_id'] or (image['Config'].get('Labels') or {}).get('org.opencontainers.image.revision')!=build['revision']:
        raise StageError('CANDIDATE_IMAGE_BINDING_CHANGED')
    network,mounts,env=profile(live,old_image,image)
    live_feature=env.get(FLAG,'false').lower()
    if live_feature not in ('true','false'):raise StageError('LIVE_RECOVERY_FLAG_INVALID')
    if live_feature=='true' and not getattr(args,'allow_enabled_live',False):
        raise StageError('LIVE_RECOVERY_ALREADY_ENABLED')
    if args.candidate_container in docker('ps','-a','--format','{{.Names}}').splitlines():
        raise StageError('CANDIDATE_EXISTS_RECONCILE')
    if getattr(args,'check_only',False):
        print('R4A_UDP_RECOVERY_STAGE_PREFLIGHT=PASS READ_ONLY=true LIVE_RECOVERY_ENABLED='
              +live_feature+' CANDIDATE_ABSENT=true DEPLOY=false RETRY=false SECRETS_NOT_PRINTED=true',flush=True)
        return
    os.umask(0o077);root=Path(tempfile.mkdtemp(prefix='udp-recovery-stage-',dir=parent))
    snapshot=root/'runtime-private.json';snapshot.write_text(json.dumps(live,sort_keys=True,indent=2)+'\n')
    receipt=root/'receipt.json';env_file=root/'candidate.env';env[FLAG]='true'
    evidence={'state':'PREPARING','candidate_name':args.candidate_container,'live_name':args.container,
        'candidate_image_id':build['image_id'],'revision':build['revision'],'build_receipt':args.build_receipt,
        'live_id':live['Id'],'live_image_id':live['Image'],'runtime_snapshot':str(snapshot),
        'runtime_snapshot_hash':digest(live),'live_restart_policy':live['HostConfig'].get('RestartPolicy'),
        'feature_enabled_on_candidate_only':live_feature=='false','live_recovery_enabled':live_feature=='true',
        'service_switched':False,'database_backup_taken':False}
    def save():receipt.write_text(json.dumps(evidence,sort_keys=True,indent=2)+'\n')
    print('R4A_UDP_RECOVERY_STAGE_RECEIPT='+str(receipt)+' PRIVATE=true',flush=True);save()
    created=None
    try:
        env_file.write_text('\n'.join(k+'='+v for k,v in sorted(env.items()))+'\n')
        cmd=['create','--pull','never','--name',args.candidate_container,'--network',network,
             '--restart','no','--user',live['Config']['User'],'--env-file',str(env_file)]
        aliases=set(live['NetworkSettings']['Networks'][network].get('Aliases') or [])-{live['Id'],live['Id'][:12]}
        for alias in sorted(aliases):cmd+=['--network-alias',alias]
        log=live['HostConfig'].get('LogConfig') or {}
        if log.get('Type'):cmd+=['--log-driver',log['Type']]
        for key,value in sorted((log.get('Config') or {}).items()):cmd+=['--log-opt',key+'='+value]
        old_labels=old_image['Config'].get('Labels') or {}
        expected_labels=dict(image['Config'].get('Labels') or {})
        for key,value in sorted((live['Config'].get('Labels') or {}).items()):
            if key not in old_labels or value!=old_labels[key]:
                if key=='org.opencontainers.image.revision':raise StageError('CUSTOM_REVISION_LABEL_UNSUPPORTED')
                cmd+=['--label',key+'='+value]
                expected_labels[key]=value
        for kind,source,destination,rw,propagation in mounts:
            spec='type=bind,src='+source+',dst='+destination+',bind-propagation='+propagation
            cmd+=['--mount',spec if rw else spec+',readonly']
        cmd.append(build['image_id']);created=docker(*cmd)
        if not re.fullmatch('[a-f0-9]{64}',created):raise StageError('CREATE_ID_INVALID')
        evidence['candidate_id']=created;save()
        candidate=inspect(created)
        actual_env={x.partition('=')[0]:x.partition('=')[2] for x in candidate['Config'].get('Env',[])}
        if (candidate['Image']!=build['image_id'] or candidate['State']['Status']!='created' or candidate['State']['Running']
                or candidate['HostConfig']['RestartPolicy']['Name']!='no' or mount_set(candidate)!=mounts
                or candidate['HostConfig']['NetworkMode']!=network or actual_env!=env
                or candidate['Config'].get('User')!=live['Config'].get('User')
                or candidate['Config'].get('Labels')!=expected_labels
                or set(candidate['NetworkSettings']['Networks'])!={network}
                or not aliases<=set(candidate['NetworkSettings']['Networks'].get(network,{}).get('Aliases') or [])
                or candidate['HostConfig'].get('LogConfig')!=live['HostConfig'].get('LogConfig')):
            raise StageError('STAGED_READBACK_MISMATCH')
        for key in ('MaskedPaths','ReadonlyPaths','CgroupnsMode','IpcMode','ShmSize','Privileged','ReadonlyRootfs',
                    'SecurityOpt','CapAdd','CapDrop','Dns','DnsSearch','DnsOptions','Runtime'):
            if candidate['HostConfig'].get(key)!=live['HostConfig'].get(key):raise StageError('HOST_DEFAULTS_CHANGED')
        after=inspect(args.container)
        if identity(after)!=identity(live) or digest(after['Config'])!=digest(live['Config']) or digest(after['HostConfig'])!=digest(live['HostConfig']):
            raise StageError('LIVE_CHANGED_DURING_STAGE')
        evidence.update(state='STAGED',candidate_stopped=True,live_identity_and_config_unchanged=True,
                        environment_match_except_feature=True,mount_count=len(mounts));save()
        print('R4A_UDP_RECOVERY_STAGE=PASS CANDIDATE_STOPPED=true CANDIDATE_RESTART_DISABLED=true ENV_PRESERVED_EXCEPT_RECOVERY_FLAG=true MOUNTS_MATCH=true LIVE_UNCHANGED=true DEPLOY=false DATABASE_BACKUP_TAKEN=false RETRY=false SECRETS_NOT_PRINTED=true',flush=True)
    except BaseException as error:
        evidence.update(state='BLOCKED',failure_type=type(error).__name__)
        if created and re.fullmatch('[a-f0-9]{64}',created):
            try:
                # No force removal and never target the live name. Preserve an unexpectedly started helper.
                if not inspect(created)['State']['Running']:docker('rm',created);evidence['candidate_removed']=True
            except Exception:evidence['cleanup_unverified']=True
        save();raise
    finally:env_file.unlink(missing_ok=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('container','candidate-container','build-receipt','work-parent'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--allow-enabled-live',action='store_true',help='Explicit upgrade of a live recovery-enabled installation')
    parser.add_argument('--check-only',action='store_true',help='Validate all stage preconditions without creating files or containers')
    try:main(parser.parse_args())
    except Exception as error:
        code=error.args[0] if isinstance(error,StageError) else 'UNCLASSIFIED'
        print('R4A_UDP_RECOVERY_STAGE=BLOCKED TYPE='+type(error).__name__+' CODE='+code+' DEPLOY=false RETRY=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
