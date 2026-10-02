#!/usr/bin/env python3
"""Prepare secret, additive routes and stopped runtime candidates; never switch live."""
import argparse
import copy
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import tempfile
import r4a_stage_semantic_consultation as stage


def require(ok,code):
    if not ok:raise RuntimeError(code)


def private(path,mode):
    s=path.lstat()
    require(not path.is_symlink() and s.st_uid==0 and stat.S_IMODE(s.st_mode)==mode,'PRIVATE_PATH_INVALID')


def env(row):
    result={}
    for value in row['Config'].get('Env') or []:
        k,sep,v=value.partition('=')
        require(sep and re.fullmatch('[A-Za-z_][A-Za-z_0-9]*',k) and k not in result and '\n' not in v and '\r' not in v,'ENV_INVALID')
        result[k]=v
    return result


def bindings(routes):
    templates=[r for r in routes if r.get('uri')=='/internal/capabilities/v1/execute' and r.get('status',1)==1]
    require(len(templates)==1,'EXECUTE_TEMPLATE_NOT_UNIQUE')
    functions=templates[0]['plugins']['serverless-post-function']['functions']
    require(len(functions)==1,'EXECUTE_FUNCTION_NOT_UNIQUE')
    result={}
    for name in ('ISSUER','AUDIENCE','MCP_WORKLOAD','DELEGATION_KEY_ENV'):
        values=re.findall(r'^local '+name+r' = ("[^\n]*")$',functions[0],re.M)
        require(len(values)==1,'EXECUTE_BINDING_NOT_UNIQUE')
        result[name]=json.loads(values[0])
    return result


def patch_yaml(original,key_name):
    require(original.count('nginx_config:\n  envs:\n')==1 and not re.search(r'\b'+re.escape(key_name)+r'\b',original),'NGINX_ENV_LAYOUT_UNSUPPORTED')
    marker='nginx_config:\n  envs:\n'
    result=original.replace(marker,marker+'  - '+key_name+'\n',1)
    require(result.replace(marker+'  - '+key_name+'\n',marker,1)==original,'CONFIG_CHANGED_BEYOND_ENV')
    return result


def write(path,text,uid=0,gid=0,mode=0o600):
    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,mode)
    with os.fdopen(fd,'w') as f:
        os.fchown(f.fileno(),uid,gid);os.fchmod(f.fileno(),mode)
        f.write(text);f.flush();os.fsync(f.fileno())


def checkpoint(path,state):
    fd,name=tempfile.mkstemp(dir=path.parent,prefix='.receipt-')
    try:
        with os.fdopen(fd,'w') as f:
            json.dump(state,f,sort_keys=True);f.flush();os.fsync(f.fileno())
        os.replace(name,path)
        directory=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(directory)
        finally:os.close(directory)
    finally:Path(name).unlink(missing_ok=True)


def launch_guard(old,image):
    h=old['HostConfig'];c=old['Config'];nets=old['NetworkSettings']['Networks']
    unsupported=('AutoRemove','PublishAllPorts','Privileged','PortBindings','VolumesFrom','Links','Tmpfs',
                 'CapAdd','CapDrop','SecurityOpt','Devices','DeviceRequests','Dns','DnsSearch','DnsOptions',
                 'ExtraHosts','Ulimits','Sysctls','GroupAdd','PidMode','UsernsMode','NanoCpus','CpuShares',
                 'CpuQuota','CpuPeriod','CpuRealtimePeriod','CpuRealtimeRuntime','CpusetCpus','CpusetMems',
                 'OomKillDisable','Init','CgroupParent','CgroupnsMode','DeviceCgroupRules','StorageOpt')
    # Docker's normal private cgroup namespace is preserved by default.
    require(all(not h.get(k) for k in unsupported if k!='CgroupnsMode') and h.get('CgroupnsMode') in (None,'','private'), 'UNSUPPORTED_HOST_SETTING')
    require(h.get('IpcMode')=='private' and h.get('NetworkMode') in nets and h.get('RestartPolicy',{}).get('Name')=='unless-stopped','LAUNCH_MODE_UNSUPPORTED')
    require(h.get('LogConfig',{})=={'Type':'json-file','Config':{}},'LOG_SETTINGS_UNSUPPORTED')
    require(not c.get('Healthcheck') and not c.get('Volumes') and not c.get('Tty') and not c.get('OpenStdin'),'CONFIG_SETTINGS_UNSUPPORTED')
    for k in ('User','Entrypoint','Cmd','WorkingDir','StopSignal'):
        require((c.get(k) or None)==(image['Config'].get(k) or None),'IMAGE_LAUNCH_CONTRACT_CHANGED')
    require(not image['Config'].get('Volumes') and not image['Config'].get('Healthcheck'),'IMAGE_IMPLICIT_STORAGE_OR_HEALTHCHECK')
    for network in nets.values():
        require(not network.get('IPAMConfig') and not network.get('Links') and not network.get('DriverOpts'),'NETWORK_SETTING_UNSUPPORTED')
    for mount in old.get('Mounts',[]):
        require(mount['Type']=='bind' and not mount['RW'] and mount.get('Propagation','rprivate')=='rprivate'
                and not any(x in mount['Source']+mount['Destination'] for x in ',\n\r'),'MOUNT_SETTING_UNSUPPORTED')
    env(old)


def command(old,image,name,env_file,mounts,revision):
    launch_guard(old,image)
    h=old['HostConfig'];c=old['Config'];nets=old['NetworkSettings']['Networks'];primary=h['NetworkMode']
    args=['docker','create','--pull','never','--name',name,'--restart','no','--network',primary,
          '--env-file',str(env_file),'--user',c['User'],'--workdir',c['WorkingDir'],
          '--shm-size',str(h['ShmSize']),'--ipc','private','--log-driver','json-file']
    if h.get('ReadonlyRootfs'):args+=['--read-only']
    for key,flag in (('Memory','--memory'),('MemorySwap','--memory-swap'),('MemoryReservation','--memory-reservation'),('PidsLimit','--pids-limit')):
        if h.get(key):args+=[flag,str(h[key])]
    if c.get('Hostname'):args+=['--hostname',c['Hostname']]
    if c.get('Domainname'):args+=['--domainname',c['Domainname']]
    if c.get('StopSignal'):args+=['--stop-signal',c['StopSignal']]
    if c.get('StopTimeout') is not None:args+=['--stop-timeout',str(c['StopTimeout'])]
    labels=copy.deepcopy(c.get('Labels') or {})
    if revision:labels['org.opencontainers.image.revision']=revision
    for k,v in sorted(labels.items()):args+=['--label',k+'='+v]
    for alias in aliases(old,primary):args+=['--network-alias',alias]
    for mount in mounts:
        args+=['--mount','type=bind,src='+mount['Source']+',dst='+mount['Destination']+',readonly']
    args.append(image['Id'])
    return args


def aliases(old,network):
    return sorted(set(old['NetworkSettings']['Networks'][network].get('Aliases') or [])-{old['Id'],old['Id'][:12]})


def matches(candidate,old,image,expected_env,mounts):
    require(candidate['Image']==image['Id'] and candidate['State']['Status']=='created' and not candidate['State']['Running'],'CANDIDATE_NOT_INERT')
    require(env(candidate)==expected_env and candidate['HostConfig']['RestartPolicy']['Name']=='no','CANDIDATE_CONFIG_DRIFT')
    actual=sorted((m['Type'],m['Source'],m['Destination'],m['RW']) for m in candidate['Mounts'])
    wanted=sorted(('bind',m['Source'],m['Destination'],False) for m in mounts)
    require(actual==wanted,'CANDIDATE_MOUNTS_DRIFT')
    for k in ('User','Entrypoint','Cmd','WorkingDir','StopSignal','StopTimeout','Hostname','Domainname'):
        require((candidate['Config'].get(k) or None)==(old['Config'].get(k) or None),'CANDIDATE_LAUNCH_DRIFT')
    for k in ('NetworkMode','LogConfig','Memory','MemorySwap','MemoryReservation','PidsLimit','ShmSize','IpcMode','ReadonlyRootfs'):
        require(candidate['HostConfig'].get(k)==old['HostConfig'].get(k),'CANDIDATE_HOST_DRIFT')
    require(set(candidate['NetworkSettings']['Networks'])==set(old['NetworkSettings']['Networks']),'CANDIDATE_NETWORK_DRIFT')
    for n in old['NetworkSettings']['Networks']:
        require(set(aliases(old,n))<=set(candidate['NetworkSettings']['Networks'][n].get('Aliases') or []),'CANDIDATE_ALIASES_DRIFT')


def route_body(row):
    return {k:v for k,v in row.items() if k not in ('id','create_time','update_time')}


def render_routes(source,routes,installation,delegation_key,owner_key,upstream,ids):
    # Separate interpreters prevent module caching across the old/new source pins.
    script=('import json,sys;sys.path.insert(0,sys.argv[1]);'
            'from tools.materialize_semantic_read import materialize;'
            'a=json.load(sys.stdin);print(json.dumps(materialize(*a)["routes"][-2:]))')
    inputs=[{'routes':routes},installation,delegation_key,owner_key,upstream,ids]
    return json.loads(stage.run([sys.executable,'-B','-c',script,str(source)],stdin=json.dumps(inputs)))


def check_replaced_routes(baseline,expected):
    indexed={str(r['id']):route_body(r) for r in baseline}
    require(len(indexed)==len(baseline),'ROUTE_IDS_NOT_UNIQUE')
    for row in expected:
        body=route_body(row);ident=str(row['id'])
        body.update(name=ident,desc='Governed bounded semantic consultation')
        require(indexed.get(ident)==body,'EXISTING_SEMANTIC_ROUTE_OWNERSHIP_DRIFT')


def main(root,args):
    require(os.geteuid()==0,'ROOT_REQUIRED');os.umask(0o077)
    private(root,0o700)
    for name in ('runtime-snapshot.json','image-receipt.json'):private(root/name,0o600)
    baseline=json.loads((root/'runtime-snapshot.json').read_text());receipt=json.loads((root/'image-receipt.json').read_text())
    require(receipt.get('status')=='PASS' and receipt.get('liveUnchanged') is True,'IMAGE_STAGE_NOT_PASS')
    configs=baseline['config'];g=configs['gateway'];old=baseline['live']|{'gateway':baseline['gateway']}
    for role,row in old.items():
        require(stage.fingerprint(stage.inspect(row['Id']))==stage.fingerprint(row),'LIVE_DRIFT')
    require(stage.routes(g,old['gateway'])==baseline['routes'],'ROUTE_DRIFT')
    b=bindings(baseline['routes']);owner_env=env(old['semantic']);mcp_env=env(old['mcp']);gateway_env=env(old['gateway'])
    require(owner_env.get('OUF_IAM_ISSUER')==b['ISSUER'] and owner_env.get('OUF_IAM_AUDIENCE')==b['AUDIENCE']
            and mcp_env.get('MCP_OIDC_CLIENT_ID')==b['MCP_WORKLOAD'],'INSTALLATION_IDENTITY_MISMATCH')
    replacing=getattr(args,'replace_existing',False)
    require(re.fullmatch('[A-Z][A-Z0-9_]{0,127}',args.key_env) and (args.key_env in gateway_env if replacing else args.key_env not in gateway_env)
            and b['DELEGATION_KEY_ENV'] in gateway_env and args.key_env!=b['DELEGATION_KEY_ENV'],'KEY_ENV_CONFLICT')
    require(re.fullmatch('[0-9a-f]{40}',args.gateway_revision),'GATEWAY_PIN_INVALID')
    require(args.key_target.startswith('/run/') and '..' not in Path(args.key_target).parts and not any(x in args.key_target for x in ',\n\r'),'KEY_TARGET_INVALID')
    require(all(re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',v) for v in (args.search_id,args.get_id)) and args.search_id!=args.get_id,'ROUTE_ID_INVALID')
    if replacing:
        require(bool(re.fullmatch('[0-9a-f]{40}',getattr(args,'previous_gateway_revision','') or '')),'PREVIOUS_GATEWAY_PIN_REQUIRED')
        require(owner_env.get('OUF_SEMANTIC_DELEGATION_KEY_FILE')==args.key_target
                and owner_env.get('OUF_SEMANTIC_DELEGATION_WORKLOAD')==b['MCP_WORKLOAD'],'EXISTING_OWNER_BINDING_DRIFT')
    else:require(not any(k.startswith('OUF_SEMANTIC_DELEGATION_') for k in owner_env),'OWNER_BINDING_ALREADY_PRESENT')
    images={x['role']:stage.inspect(x['image']) for x in receipt['images']}
    revisions={x['role']:x['commit'] for x in receipt['images']}
    require(set(images)=={'semantic','mcp'},'IMAGE_ROLES_INVALID')
    for x in configs['images']:
        require(revisions[x['role']]==x['commit'] and (images[x['role']]['Config'].get('Labels') or {}).get('org.opencontainers.image.revision')==x['commit'],'STAGED_IMAGE_DRIFT')
    images['gateway']=stage.inspect(old['gateway']['Image'])
    for role,row in old.items():launch_guard(row,images[role])
    # Reserve once before secret/container preparation. Failure is reconciled, not rerun.
    folder=root/'prepared';folder.mkdir(mode=0o700,exist_ok=False)
    state={'status':'PREPARING','attempted':[],'candidates':{},'liveIds':{r:x['Id'] for r,x in old.items()}}
    checkpoint(folder/'prepare-receipt.json',state)
    source=folder/'gateway-source'
    stage.run(['git','clone','--no-checkout','https://github.com/GioNob/ouf-api-gateway',str(source)],180)
    stage.run(['git','-C',str(source),'fetch','--no-tags','origin',args.gateway_revision],180)
    stage.run(['git','-C',str(source),'checkout','--detach',args.gateway_revision],60)
    require(stage.run(['git','-C',str(source),'rev-parse','HEAD'])==args.gateway_revision,'GATEWAY_SOURCE_DRIFT')
    installation={'issuerUrl':b['ISSUER'],'gatewayAudience':b['AUDIENCE'],'mcpServiceIdentity':b['MCP_WORKLOAD']}
    upstreams=[r['upstream'] for r in baseline['routes'] if r.get('uri')=='/api/semantic/v1/search' and r.get('status',1)==1]
    require(len(upstreams)==1,'SEMANTIC_UPSTREAM_NOT_UNIQUE')
    ids={'search':args.search_id,'get':args.get_id}
    route_base=baseline['routes']
    if replacing:
        prior=folder/'gateway-previous-source'
        stage.run(['git','clone','--no-checkout','https://github.com/GioNob/ouf-api-gateway',str(prior)],180)
        stage.run(['git','-C',str(prior),'fetch','--no-tags','origin',args.previous_gateway_revision],180)
        stage.run(['git','-C',str(prior),'checkout','--detach',args.previous_gateway_revision],60)
        require(stage.run(['git','-C',str(prior),'rev-parse','HEAD'])==args.previous_gateway_revision,'PREVIOUS_GATEWAY_SOURCE_DRIFT')
        route_base=[r for r in route_base if str(r['id']) not in ids.values()]
        expected=render_routes(prior,route_base,installation,b['DELEGATION_KEY_ENV'],args.key_env,upstreams[0],ids)
        check_replaced_routes(baseline['routes'],expected)
    desired=render_routes(source,route_base,installation,b['DELEGATION_KEY_ENV'],args.key_env,upstreams[0],ids)
    # Exact new URIs must be unclaimed even by wildcard routes.
    import fnmatch
    for r in route_base:
        if r.get('status',1)==0 or (r.get('methods') and 'POST' not in r['methods']):continue
        for pattern in [r.get('uri')]+r.get('uris',[]):
            require(not isinstance(pattern,str) or not any(fnmatch.fnmatchcase(d['uri'],pattern) for d in desired),'SEMANTIC_PATH_ALREADY_ROUTED')
    stage.save(folder/'desired-routes.json',desired)
    user=old['semantic']['Config']['User'];require(bool(re.fullmatch('[0-9]+:[0-9]+',user)),'OWNER_UID_GID_NOT_NUMERIC')
    uid,gid=map(int,user.split(':'))
    if replacing:
        key_mounts=[m for m in old['semantic']['Mounts'] if m['Destination']==args.key_target]
        require(len(key_mounts)==1,'EXISTING_KEY_BIND_NOT_UNIQUE')
        key_file=Path(key_mounts[0]['Source']);meta=key_file.lstat()
        require(not key_file.is_symlink() and (meta.st_uid,meta.st_gid,stat.S_IMODE(meta.st_mode))==(uid,gid,0o400),'EXISTING_OWNER_KEY_PERMISSION_DRIFT')
        key=key_file.read_text().strip()
        require(bool(re.fullmatch('[0-9a-fA-F]{64}',key)) and key==gateway_env[args.key_env],'EXISTING_OWNER_GATEWAY_KEY_DRIFT')
    else:
        key=secrets.token_hex(32)
        require(key not in gateway_env.values(),'SECRET_COLLISION')
    write(folder/'semantic-owner.key',key+'\n',uid,gid,0o400)
    owner_env.update(OUF_SEMANTIC_DELEGATION_KEY_FILE=args.key_target,OUF_SEMANTIC_DELEGATION_WORKLOAD=b['MCP_WORKLOAD'])
    gateway_env[args.key_env]=key
    yaml_mounts=[m for m in old['gateway']['Mounts'] if m['Destination']==g['configDestination']]
    require(len(yaml_mounts)==1,'CONFIG_FILE_BIND_REQUIRED')
    original=Path(yaml_mounts[0]['Source']);meta=original.stat()
    if replacing:
        require(len(re.findall(r'^  - '+re.escape(args.key_env)+r'$',original.read_text(),re.M))==1,'EXISTING_NGINX_KEY_ENV_DRIFT')
    write(folder/'apisix-config.yaml',original.read_text() if replacing else patch_yaml(original.read_text(),args.key_env),meta.st_uid,meta.st_gid,stat.S_IMODE(meta.st_mode))
    environments={'semantic':owner_env,'mcp':mcp_env,'gateway':gateway_env}
    mounts={r:copy.deepcopy(x['Mounts']) for r,x in old.items()}
    if replacing:
        for mount in mounts['semantic']:
            if mount['Destination']==args.key_target:mount['Source']=str(folder/'semantic-owner.key')
    else:
        require(not any(m['Destination']==args.key_target for m in mounts['semantic']),'KEY_MOUNT_ALREADY_PRESENT')
        mounts['semantic'].append({'Type':'bind','Source':str(folder/'semantic-owner.key'),'Destination':args.key_target,'RW':False})
    for mount in mounts['gateway']:
        if mount['Destination']==g['configDestination']:mount['Source']=str(folder/'apisix-config.yaml')
    names={r:old[r]['Name'].lstrip('/')+'-consultation-candidate' for r in old}
    existing=stage.run(['docker','container','ls','--all','--format','{{.Names}}']).splitlines()
    require(not set(names.values())&set(existing),'CANDIDATE_NAME_OCCUPIED')
    for role in ('semantic','mcp','gateway'):
        write(folder/(role+'.env'),''.join(k+'='+v+'\n' for k,v in environments[role].items()))
        argv=command(old[role],images[role],names[role],folder/(role+'.env'),mounts[role],revisions.get(role))
        for r,row in old.items():require(stage.fingerprint(stage.inspect(row['Id']))==stage.fingerprint(row),'LIVE_CHANGED_BEFORE_CREATE')
        state['attempted'].append({'role':role,'name':names[role]});checkpoint(folder/'prepare-receipt.json',state)
        ident=stage.run(argv,60)
        for network in old[role]['NetworkSettings']['Networks']:
            if network==old[role]['HostConfig']['NetworkMode']:continue
            connect=['docker','network','connect']
            for alias in aliases(old[role],network):connect+=['--alias',alias]
            stage.run(connect+[network,ident],60)
        candidate=stage.inspect(ident);matches(candidate,old[role],images[role],environments[role],mounts[role])
        state['candidates'][role]={'id':ident,'name':names[role],'image':images[role]['Id']}
        checkpoint(folder/'prepare-receipt.json',state)
        print('CONSULTATION_CANDIDATE='+json.dumps(state['candidates'][role],sort_keys=True)+' STOPPED=true',flush=True)
    require(stage.routes(g,old['gateway'])==baseline['routes'],'ROUTES_CHANGED_DURING_PREPARE')
    for r,row in old.items():require(stage.fingerprint(stage.inspect(row['Id']))==stage.fingerprint(row),'LIVE_CHANGED_DURING_PREPARE')
    state.update(status='PASS',routesPrepared=2,keyEnv=args.key_env,keyTarget=args.key_target,
                 gatewayRevision=args.gateway_revision,installation=installation,expectedEnvironments=environments,mounts=mounts)
    if replacing:state.update(replaceExisting=True,previousGatewayRevision=args.previous_gateway_revision)
    checkpoint(folder/'prepare-receipt.json',state)
    print('CONSULTATION_PREPARE=PASS CANDIDATES=3 STOPPED=true LIVE_UNCHANGED=true ROUTES_UNCHANGED=true POLICY_UNCHANGED=true NO_SOURCE_RUN=true PRIVATE_ROOT='+str(folder),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage-root',type=Path,required=True)
    for name in ('gateway-revision','key-env','key-target','search-id','get-id'):p.add_argument('--'+name,required=True)
    p.add_argument('--replace-existing',action='store_true')
    p.add_argument('--previous-gateway-revision')
    try:
        args=p.parse_args();main(args.stage_root,args)
    except Exception as error:
        code=str(error) if isinstance(error,RuntimeError) and re.fullmatch('[A-Z_]{1,80}',str(error)) else type(error).__name__
        print('CONSULTATION_PREPARE=BLOCKED CODE='+code+' NO_SWITCH=true DO_NOT_RERUN_BLINDLY=true SECRETS_NOT_PRINTED=true',file=sys.stderr)
        raise SystemExit(1) from None
