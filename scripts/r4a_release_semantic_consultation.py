#!/usr/bin/env python3
"""Coordinated consultation rollout; retain original containers and never publish policy."""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.parse import urlsplit,unquote
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import r4a_prepare_semantic_consultation as prep
import r4a_stage_semantic_consultation as stage

require=prep.require


def comparable(row):
    return {k:v for k,v in row.items() if k not in ('id','create_time','update_time')}


def index(rows):
    result={}
    for row in rows:
        ident=str(row['id']);require(ident not in result,'DUPLICATE_ROUTE_ID')
        result[ident]=comparable(row)
    return result


def wire(container,origin,method,path,headers=None,body=None):
    row=stage.inspect(container);require(row['State']['Running'],'HTTP_CONTAINER_NOT_RUNNING')
    message={'url':origin+path,'method':method,'headers':headers or {},'body':body}
    raw=stage.run(['nsenter','-t',str(row['State']['Pid']),'-n',sys.executable,'-B',str(Path(__file__).resolve()),'--inside'],
                  stdin=json.dumps(message),timeout=20)
    return json.loads(raw)


def http_code(container,origin,method,path,body=None,headers=None):
    return wire(container,origin,method,path,headers,body)['status']


class Gateway:
    def __init__(self,name,config):self.name=name;self.config=config
    def api(self,method,path,body=None,statuses=(200,)):
        row=stage.inspect(self.name);target=Path(self.config['configDestination'])
        files=[Path(m['Source'])/target.relative_to(Path(m['Destination'])) for m in row.get('Mounts',[])
               if m['Type']=='bind' and target.is_relative_to(Path(m['Destination']))]
        require(len(files)==1,'ADMIN_CONFIG_BIND_AMBIGUOUS')
        key=stage.admin_key(files[0].read_text())
        answer=wire(self.name,self.config['adminOrigin'],method,'/apisix/admin/'+path,
                    {'X-API-KEY':key,'Content-Type':'application/json'},None if body is None else json.dumps(body))
        require(answer['status'] in statuses,'ADMIN_STATUS_UNEXPECTED')
        return (json.loads(answer['body']) if answer['body'] else {}),answer['status']
    def rows(self):
        doc,_=self.api('GET','routes')
        require(doc.get('total',len(doc.get('list',[])))<=len(doc.get('list',[])),'ROUTES_TRUNCATED')
        return stage.route_values(doc)


def one(doc):
    value=doc.get('value',doc.get('node',{}).get('value'))
    if isinstance(value,str):value=json.loads(value)
    require(isinstance(value,dict),'ROUTE_RESPONSE_INVALID')
    return comparable(value)


def readback(gateway,baseline,wanted,installed):
    current=index(gateway.rows());original=index(baseline)
    require({k:v for k,v in current.items() if k not in wanted}=={k:v for k,v in original.items() if k not in wanted},'EXISTING_ROUTES_DRIFT')
    for ident in wanted:
        expected=wanted[ident] if ident in installed else original.get(ident)
        require(current.get(ident)==expected,'NEW_ROUTE_DRIFT')


def install_routes(gateway,baseline,wanted,state,path):
    readback(gateway,baseline,wanted,[])
    original=index(baseline)
    for ident,body in wanted.items():
        doc,status=gateway.api('GET','routes/'+ident,statuses=(200,404))
        require((status==200 and one(doc)==original[ident]) if ident in original else status==404,'ROUTE_ID_OCCUPIED')
        state['routesAttempted'].append(ident);prep.checkpoint(path,state)
        gateway.api('PUT','routes/'+ident,body,statuses=(200,201))
        readback(gateway,baseline,wanted,state['routesAttempted'])


def delete_routes(gateway,baseline,wanted,attempted):
    # GET before DELETE reconciles PUT/DELETE responses lost in transit.
    original=index(baseline)
    for ident in reversed(attempted):
        doc,status=gateway.api('GET','routes/'+ident,statuses=(200,404))
        if ident in original:
            require(status==200,'ROLLBACK_EXISTING_ROUTE_MISSING')
            if one(doc)==original[ident]:continue
            require(one(doc)==wanted[ident],'ROLLBACK_ROUTE_OWNERSHIP_DRIFT')
            try:gateway.api('PUT','routes/'+ident,original[ident],statuses=(200,201))
            except Exception:
                require(one(gateway.api('GET','routes/'+ident)[0])==original[ident],'RESTORE_OUTCOME_UNCERTAIN')
            require(one(gateway.api('GET','routes/'+ident)[0])==original[ident],'RESTORE_NOT_VERIFIED')
            continue
        if status==404:continue
        require(one(doc)==wanted[ident],'ROLLBACK_ROUTE_OWNERSHIP_DRIFT')
        try:gateway.api('DELETE','routes/'+ident,statuses=(200,204))
        except Exception:
            require(gateway.api('GET','routes/'+ident,statuses=(200,404))[1]==404,'DELETE_OUTCOME_UNCERTAIN')
        require(gateway.api('GET','routes/'+ident,statuses=(200,404))[1]==404,'ROUTE_DELETE_NOT_VERIFIED')
    require(index(gateway.rows())==index(baseline),'ROLLBACK_ROUTE_BASELINE_DRIFT')


def history(pg,user,database,role):
    query={'semantic':"select coalesce(json_agg(json_build_object('version',version,'script',script,'checksum',checksum,'success',success,'type',type) order by installed_rank),'[]'::json) from ouf_sem.flyway_schema_history",
           'mcp':"select coalesce(json_agg(json_build_object('version',version,'checksum',checksum) order by version),'[]'::json) from ouf_mcp.schema_migration"}[role]
    return json.loads(stage.run(['docker','exec',pg,'psql','-X','-qAt','-v','ON_ERROR_STOP=1','-U',user,'-d',database,'-c','begin read only; '+query+'; commit;']))


def backup(pg,user,database,path):
    with path.open('xb') as f:
        subprocess.run(['docker','exec',pg,'pg_dump','-U',user,'-d',database,'-Fc'],stdout=f,stderr=subprocess.PIPE,check=True,timeout=600)
        f.flush();os.fsync(f.fileno())
    require(path.stat().st_size>1024,'BACKUP_TOO_SMALL')
    with path.open('rb') as f:
        subprocess.run(['docker','exec','-i',pg,'pg_restore','--list'],stdin=f,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,check=True,timeout=120)
    with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    return {'path':str(path),'sha256':digest,'tocVerified':True,'restoreToDatabaseTested':False}


def ready(name,origin,path,expected):
    for attempt in range(45):
        row=stage.inspect(name);require(row['State']['Running'],'CANDIDATE_EXITED')
        try:
            if http_code(name,origin,'GET',path)==expected:return
        except (OSError,ValueError,RuntimeError,subprocess.SubprocessError):pass
        if attempt and attempt%10==0:print('CONSULTATION_WAIT_READY='+row['Name'],flush=True)
        time.sleep(2)
    raise RuntimeError('READINESS_TIMEOUT')


def stable_except_restart(row):
    value=stage.fingerprint(row);value.pop('running');value.pop('startedAt')
    value=copy.deepcopy(value);value['HostConfig'].pop('RestartPolicy',None)
    return value


def rename_verified(ident,name):
    try:stage.run(['docker','rename',ident,name])
    except Exception:
        require(stage.inspect(ident)['Name'].lstrip('/')==name,'RENAME_OUTCOME_UNCERTAIN')
    require(stage.inspect(ident)['Name'].lstrip('/')==name,'RENAME_READBACK_MISMATCH')


def restore_container(original,candidate,failed):
    name=original['Name'].lstrip('/');old=stage.inspect(original['Id']);new=stage.inspect(candidate['id'])
    if new['State']['Running']:
        stage.run(['docker','update','--restart','no',new['Id']]);stage.run(['docker','stop','--time','30',new['Id']],60)
    if new['Name'].lstrip('/')==name:rename_verified(new['Id'],failed)
    # Inspect IDs again: a rename response can be lost after the daemon committed it.
    old=stage.inspect(original['Id'])
    require(stable_except_restart(old)==stable_except_restart(original),'ORIGINAL_CONFIG_DRIFT')
    if old['Name'].lstrip('/')!=name:rename_verified(old['Id'],name)
    if not old['State']['Running']:stage.run(['docker','start',old['Id']],60)
    stage.run(['docker','update','--restart',original['HostConfig']['RestartPolicy']['Name'],old['Id']])
    row=stage.inspect(old['Id'])
    require(row['Name'].lstrip('/')==name and row['State']['Running'],'ORIGINAL_NOT_RESTORED')


def switch(role,old,candidate,state,path):
    name=old['Name'].lstrip('/');state['switchAttempted'].append(role);prep.checkpoint(path,state)
    current=stage.inspect(old['Id'])
    require(current['Name']==old['Name'] and stable_except_restart(current)==stable_except_restart(old),'OLD_CONTAINER_CHANGED')
    if current['State']['Running']:
        stage.run(['docker','update','--restart','no',old['Id']]);stage.run(['docker','stop','--time','30',old['Id']],60)
    rename_verified(old['Id'],state['rollbackNames'][role])
    rename_verified(candidate['id'],name)
    stage.run(['docker','start',candidate['id']],60)


def probe_body(name,operation=None,capability=None):
    cap=capability or ('ouf.semantic.search' if name=='search' else 'ouf.semantic.read')
    return json.dumps({'GatewayBindingRef':'capability://'+cap,'CapabilityID':cap,'Owner':'semantic',
      'OperationClass':operation or ('SEARCH' if name=='search' else 'READ'),'Arguments':{'q':'consultation-denial-probe','limit':1} if name=='search' else {'semanticId':'probe:unpublished','revisionId':'11111111-1111-4111-8111-111111111111','publicationSetId':'22222222-2222-4222-8222-222222222222'},
      'Identity':{'ServicePrincipalID':'probe','PrincipalID':'probe','TenantID':'probe','ActorType':'HUMAN','AuthenticationContextRef':'probe'},
      'AuthorizationDecisionRef':'probe','CorrelationID':'probe','IdempotencyKey':'probe','AttemptID':'33333333-3333-4333-8333-333333333333','RequestHash':'0'*64,'MaxResultBytes':262144})


def configuration(args):
    root=args.stage_root;prep.private(root,0o700);folder=root/'prepared';prep.private(folder,0o700)
    for file in (root/'runtime-snapshot.json',root/'image-receipt.json',folder/'prepare-receipt.json',folder/'desired-routes.json'):prep.private(file,0o600)
    before=json.loads((root/'runtime-snapshot.json').read_text());prepared=json.loads((folder/'prepare-receipt.json').read_text())
    require(prepared.get('status')=='PASS' and set(prepared['candidates'])=={'semantic','mcp','gateway'},'PREPARATION_NOT_PASS')
    old=before['live']|{'gateway':before['gateway']};candidates=prepared['candidates']
    raw=json.loads((folder/'desired-routes.json').read_text())
    source=folder/'gateway-source'
    require(stage.run(['git','-C',str(source),'rev-parse','HEAD'])==prepared['gatewayRevision']
            and not stage.run(['git','-C',str(source),'status','--porcelain']),'GATEWAY_SOURCE_ARTIFACT_DRIFT')
    b=prep.bindings(before['routes'])
    upstreams=[r['upstream'] for r in before['routes'] if r.get('uri')=='/api/semantic/v1/search' and r.get('status',1)==1]
    require(len(upstreams)==1 and len(raw)==2,'PREPARED_SOURCE_BINDING_INVALID')
    ids={r['uri'].rsplit('/',1)[-1]:r['id'] for r in raw}
    replacing=prepared.get('replaceExisting',False)
    route_base=before['routes']
    if replacing:
        prior=folder/'gateway-previous-source'
        require(stage.run(['git','-C',str(prior),'rev-parse','HEAD'])==prepared['previousGatewayRevision']
                and not stage.run(['git','-C',str(prior),'status','--porcelain']),'PREVIOUS_GATEWAY_SOURCE_ARTIFACT_DRIFT')
        route_base=[r for r in route_base if str(r['id']) not in ids.values()]
        expected=prep.render_routes(prior,route_base,prepared['installation'],b['DELEGATION_KEY_ENV'],prepared['keyEnv'],upstreams[0],ids)
        prep.check_replaced_routes(before['routes'],expected)
    regenerated=prep.render_routes(source,route_base,prepared['installation'],b['DELEGATION_KEY_ENV'],prepared['keyEnv'],upstreams[0],ids)
    require(raw==regenerated,'DESIRED_ROUTE_ARTIFACT_DRIFT')
    wanted={str(r['id']):comparable(r) for r in raw}
    require(len(wanted)==2 and {r['uri'] for r in raw}=={'/internal/capabilities/v1/execute/semantic/search','/internal/capabilities/v1/execute/semantic/get'},'DESIRED_ROUTES_INVALID')
    for ident,body in wanted.items():body['name']=ident;body['desc']='Governed bounded semantic consultation'
    require(replacing or not set(wanted)&set(index(before['routes'])),'ADD_ONLY_ROUTE_ID_ALREADY_PRESENT')
    gateway=Gateway(old['gateway']['Name'].lstrip('/'),before['config']['gateway'])
    return folder,before,prepared,old,candidates,wanted,gateway


def databases(args,old):
    pg=stage.inspect(args.postgres_container);require(pg['State']['Running'],'POSTGRES_NOT_RUNNING')
    user=prep.env(pg).get('POSTGRES_USER','');require(bool(re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,62}',user)),'POSTGRES_ADMIN_USER_INVALID')
    allowed={args.postgres_container,pg['Name'].lstrip('/')}
    for network in pg['NetworkSettings']['Networks'].values():allowed.update(network.get('Aliases') or [])
    values={'semantic':prep.env(old['semantic'])['OUF_SEM_DB_URL'].removeprefix('jdbc:'),'mcp':prep.env(old['mcp'])['MCP_DATABASE_URL']}
    names={}
    for role,value in values.items():
        u=urlsplit(value);name=unquote(u.path.lstrip('/'))
        require(u.scheme in ('postgres','postgresql') and u.hostname in allowed and u.port in (None,5432)
                and re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,62}',name),'DATABASE_BINDING_NOT_LOCAL_POSTGRES')
        names[role]=name
    return pg,user,names


def verify_live(args,before,prepared,candidates,wanted,gateway):
    readback(gateway,before['routes'],wanted,list(wanted))
    old=before['live']|{'gateway':before['gateway']}
    for role,info in candidates.items():
        row=stage.inspect(info['id']);require(row['State']['Running'] and row['Image']==info['image'],'NEW_LIVE_ID_OR_IMAGE_DRIFT')
        require(row['Name']==old[role]['Name'] and not stage.inspect(old[role]['Id'])['State']['Running'],'LIVE_OR_RETAINED_NAME_STATE_DRIFT')
        view=copy.deepcopy(row);view['State']={'Running':False,'Status':'created'};view['HostConfig']['RestartPolicy']['Name']='no'
        prep.matches(view,old[role],stage.inspect(info['image']),prepared['expectedEnvironments'][role],prepared['mounts'][role])
    ready(candidates['semantic']['id'],args.semantic_origin,'/actuator/health/readiness',200)
    ready(candidates['mcp']['id'],args.mcp_origin,'/health/ready',204)
    for name in ('search','get'):
        route=next(r for r in wanted.values() if r['uri'].endswith('/'+name))
        schema=route['plugins']['request-validation']['body_schema']['properties']
        body=probe_body(name,schema['OperationClass']['const'],schema['CapabilityID']['const'])
        owner=http_code(candidates['semantic']['id'],args.semantic_origin,'POST','/api/internal/v1/semantic/consultation/'+name,body,{'Content-Type':'application/json','X-OUF-Semantic-Read-Receipt':'invalid'})
        headers={'Content-Type':'application/json'}
        host=route.get('host') or (route.get('hosts') or [None])[0]
        if host:headers['Host']=host.replace('*','probe')
        gw=http_code(candidates['gateway']['id'],args.gateway_origin,'POST','/internal/capabilities/v1/execute/semantic/'+name,body,headers)
        require(owner in (401,403) and gw in (401,403),'ANONYMOUS_OR_FORGED_REQUEST_NOT_DENIED')
    print('CONSULTATION_READINESS_AND_DENIAL=PASS POSITIVE_HUMAN_NOT_PROVEN=true',flush=True)


def main(args):
    require(os.geteuid()==0,'ROOT_REQUIRED');os.umask(0o077)
    for origin in (args.semantic_origin,args.mcp_origin,args.gateway_origin):
        require(bool(re.fullmatch(r'http://127\.0\.0\.1:[0-9]{1,5}',origin)),'PROBE_ORIGIN_NOT_LOOPBACK')
    require(bool(re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',args.postgres_container)),'POSTGRES_CONTAINER_INVALID')
    folder,before,prepared,old,candidates,wanted,gateway=configuration(args)
    with (folder/'release.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        path=folder/'release-receipt.json'
        if args.mode=='verify':
            prep.private(path,0o600);state=json.loads(path.read_text());require(state.get('status')=='PASS','RELEASE_NOT_PASS')
            verify_live(args,before,prepared,candidates,wanted,gateway)
            print('CONSULTATION_RELEASE_VERIFY=PASS READ_ONLY=true');return
        require(not path.exists(),'RELEASE_RECEIPT_EXISTS_RECONCILE')
        for role,row in old.items():
            require(stage.fingerprint(stage.inspect(row['Id']))==stage.fingerprint(row),'OLD_LIVE_DRIFT')
            prep.matches(stage.inspect(candidates[role]['id']),row,stage.inspect(candidates[role]['image']),prepared['expectedEnvironments'][role],prepared['mounts'][role])
        readback(gateway,before['routes'],wanted,[])
        key=folder/'semantic-owner.key';meta=key.lstat()
        uid,gid=map(int,old['semantic']['Config']['User'].split(':'))
        require(not key.is_symlink() and (meta.st_uid,meta.st_gid,meta.st_mode&0o777)==(uid,gid,0o400),'OWNER_KEY_PERMISSION_DRIFT')
        require(key.read_text().strip()==prepared['expectedEnvironments']['gateway'][prepared['keyEnv']],'OWNER_GATEWAY_KEY_DRIFT')
        original_config=[m for m in old['gateway']['Mounts'] if m['Destination']==before['config']['gateway']['configDestination']]
        require(len(original_config)==1,'GATEWAY_CONFIG_BIND_DRIFT')
        config_text=Path(original_config[0]['Source']).read_text()
        expected_config=config_text if prepared.get('replaceExisting') else prep.patch_yaml(config_text,prepared['keyEnv'])
        require((folder/'apisix-config.yaml').read_text()==expected_config,'GATEWAY_CONFIG_DRIFT')
        pg,user,db=databases(args,old);hist={r:history(args.postgres_container,user,db[r],r) for r in db}
        require(all(hist.values()) and all(x.get('success',True) for x in hist['semantic']),'MIGRATION_HISTORY_INVALID')
        rollback_names={r:x['Name'].lstrip('/')+'-consultation-rollback-'+x['Id'][:12] for r,x in old.items()}
        failed_names={r:x['Name'].lstrip('/')+'-consultation-failed-'+candidates[r]['id'][:12] for r,x in old.items()}
        existing=stage.run(['docker','container','ls','--all','--format','{{.Names}}']).splitlines()
        require(not (set(rollback_names.values())|set(failed_names.values()))&set(existing),'RETENTION_NAME_OCCUPIED')
        ready(old['semantic']['Id'],args.semantic_origin,'/actuator/health/readiness',200)
        ready(old['mcp']['Id'],args.mcp_origin,'/health/ready',204)
        print('CONSULTATION_RELEASE_PLAN=PASS MODE='+args.mode+' CANDIDATES=3 EXISTING_ROUTES_PRESERVED=true NO_POLICY_PUBLICATION=true',flush=True)
        if args.mode=='plan':return
        state={'status':'STARTING','switchAttempted':[],'routesAttempted':[],'rollbackNames':rollback_names,'failedNames':failed_names,'backups':{},'history':hist,'postgresId':pg['Id']}
        stage.save(path,state)
        try:
            for role in ('mcp','semantic'):
                state['switchAttempted'].append(role);prep.checkpoint(path,state)
                stage.run(['docker','update','--restart','no',old[role]['Id']]);stage.run(['docker','stop','--time','30',old[role]['Id']],60)
            require(stage.inspect(pg['Id'])['State']['Running'],'POSTGRES_STOPPED')
            for role in ('semantic','mcp'):
                state['backups'][role]=backup(args.postgres_container,user,db[role],folder/(role+'-before-consultation.dump'))
                prep.checkpoint(path,state)
                require(history(args.postgres_container,user,db[role],role)==hist[role],'MIGRATION_HISTORY_CHANGED_BEFORE_START')
                print('CONSULTATION_BACKUP=PASS ROLE='+role+' TOC_VERIFIED=true PRIVATE=true',flush=True)
            switch('semantic',old['semantic'],candidates['semantic'],state,path)
            ready(candidates['semantic']['id'],args.semantic_origin,'/actuator/health/readiness',200)
            switch('gateway',old['gateway'],candidates['gateway'],state,path)
            # Admin API readiness is separate from a Running container.
            for attempt in range(30):
                try:readback(gateway,before['routes'],wanted,[]);break
                except Exception:
                    if attempt==29:raise
                    time.sleep(2)
            install_routes(gateway,before['routes'],wanted,state,path)
            switch('mcp',old['mcp'],candidates['mcp'],state,path)
            verify_live(args,before,prepared,candidates,wanted,gateway)
            for role in db:require(history(args.postgres_container,user,db[role],role)==hist[role],'MIGRATION_HISTORY_CHANGED_AFTER_START')
            for role in candidates:stage.run(['docker','update','--restart',old[role]['HostConfig']['RestartPolicy']['Name'],candidates[role]['id']])
            state['status']='PASS';prep.checkpoint(path,state)
        except BaseException:
            failures=[]
            # Keep trying container recovery even when route cleanup cannot be verified.
            for role in ('mcp','gateway','semantic'):
                try:restore_container(old[role],candidates[role],failed_names[role])
                except Exception:failures.append('CONTAINER_'+role.upper())
            try:delete_routes(gateway,before['routes'],wanted,state['routesAttempted'])
            except Exception:failures.append('ROUTES')
            for role,origin,health,status in [('semantic',args.semantic_origin,'/actuator/health/readiness',200),('mcp',args.mcp_origin,'/health/ready',204)]:
                try:ready(old[role]['Id'],origin,health,status)
                except Exception:failures.append('READINESS_'+role.upper())
            state.update(status='MANUAL_RECONCILIATION_REQUIRED' if failures else 'ROLLED_BACK',recoveryFailures=failures)
            try:prep.checkpoint(path,state)
            except Exception:print('CONSULTATION_RECEIPT_PERSISTENCE_FAILED=true',flush=True)
            print('CONSULTATION_ROLLBACK='+state['status']+' DB_NOT_AUTOMATICALLY_RESTORED=true',flush=True)
            raise
        route_result='UPDATED_ROUTES=2 NEW_ROUTES=0' if prepared.get('replaceExisting') else 'NEW_ROUTES=2'
        print('CONSULTATION_RELEASE=PASS CONTAINERS=3 '+route_result+' MIGRATION_HISTORY_UNCHANGED=true POLICY_PUBLICATION_NOT_CALLED=true NO_SOURCE_RUN=true POSITIVE_HUMAN_NOT_PROVEN=true',flush=True)
        print('CONSULTATION_ROLLBACK_CONTAINERS='+json.dumps(rollback_names,sort_keys=True),flush=True)
        print('CONSULTATION_RELEASE_RECEIPT='+str(path)+' PRIVATE=true',flush=True)


if __name__=='__main__':
    try:
        if sys.argv[1:]==['--inside']:
            data=json.load(sys.stdin);body=data['body']
            req=Request(data['url'],data=None if body is None else body.encode(),headers=data['headers'],method=data['method'])
            try:
                with urlopen(req,timeout=10) as response:status=response.status;raw=response.read(10485761)
            except HTTPError as error:status=error.code;raw=error.read(10485761)
            require(len(raw)<=10485760,'HTTP_RESPONSE_LIMIT')
            print(json.dumps({'status':status,'body':raw.decode()}))
        else:
            p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('plan','apply','verify'))
            p.add_argument('--stage-root',type=Path,required=True)
            for name in ('postgres-container','semantic-origin','mcp-origin','gateway-origin'):p.add_argument('--'+name,required=True)
            main(p.parse_args())
    except Exception as error:
        code=str(error) if isinstance(error,RuntimeError) and re.fullmatch('[A-Z_]{1,80}',str(error)) else type(error).__name__
        print('CONSULTATION_RELEASE=BLOCKED CODE='+code+' DO_NOT_RERUN_BLINDLY=true SECRETS_NOT_PRINTED=true',file=sys.stderr)
        raise SystemExit(1) from None
