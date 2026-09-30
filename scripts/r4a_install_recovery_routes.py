#!/usr/bin/env python3
"""Install four source-independent HUMAN recovery routes; never POST to Ingestion."""
import argparse
import copy
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import r4a_install_runtime_publication_list_route as admin

ROOT=Path('/etc/ouf/deploy-snapshots')
RECEIPT=ROOT/'ingestion-recovery-routes.json'
TEMPLATE='/api/onboarding/v1/runtime/publications'
UUID='[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}'
BASE='/api/trusted-human/v1/ingestion/'
TARGETS=[('r4a-ingestion-human-run-read','GET','runs','', 'ingestion.run.read'),
         ('r4a-ingestion-human-run-resume','POST','runs','/resume','ingestion.run.resume'),
         ('r4a-ingestion-human-quarantine-read','GET','quarantine','', 'ingestion.quarantine.read'),
         ('r4a-ingestion-human-quarantine-retry','POST','quarantine','/retry','ouf.ingestion.quarantine.retry')]


def objects(value):
    if isinstance(value,dict):
        yield value
        for item in value.values():yield from objects(item)
    elif isinstance(value,list):
        for item in value:yield from objects(item)


def scopes(document):
    result={}
    for _,method,_,_,cap in TARGETS:
        rows=[v for v in objects(document) if v.get('capabilityId')==cap and 'allowedActors' in v and 'requiredScope' in v]
        if len(rows)!=1 or rows[0].get('allowedActors')!=['HUMAN'] or rows[0].get('operation')!=('READ' if method=='GET' else 'WRITE') or rows[0].get('requiredScope')!=cap:
            raise RuntimeError('RECOVERY_HUMAN_DESCRIPTOR_MISMATCH')
        result[cap]=cap
    return result


def published(live,tenant):
    helper=admin.inventory.routes.helper
    settings=helper.transport_settings(live,tenant)
    mounts={m['Destination']:m for m in live['Mounts']}
    text=Path(mounts[helper.PROPERTIES]['Source']).read_text()
    endpoint=helper.literal_property(text,'ouf.authorization.registry-url')
    token_path=Path(mounts[helper.AUTH]['Source'])/Path(settings['ouf.ingestion.activation.token-file']).relative_to(helper.AUTH)
    token=token_path.read_text().strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',token):raise RuntimeError('TOKEN_FORMAT_INVALID')
    config='silent\nshow-error\nmax-time = 5\nmax-filesize = 2097152\nheader = "Authorization: Bearer '+token+'"\nurl = '+json.dumps(endpoint)+'\nwrite-out = "\\n%{http_code}"\n'
    raw=helper.run(['docker','run','--rm','-i','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--network','ouf-backend','curlimages/curl:8.16.0','--config','-'],input=config,timeout=15)
    body,code=raw.rsplit('\n',1)
    if code!='200':raise RuntimeError('RECOVERY_POLICY_READ_NOT_200')
    return json.loads(body)


def strip_identity_headers():
    # Never trust identity/capability headers supplied by a client. Keep Authorization.
    return ("return function(conf, ctx) "
            "local headers=ngx.req.get_headers(0,true); "
            "for name,_ in pairs(headers) do "
            "if string.lower(name):sub(1,6)=='x-ouf-' then ngx.req.clear_header(name) end "
            "end end")


def human_guard():
    # This runs in access after OIDC verification; decoding is an additional actor check.
    # Preserve the bearer token for the independent owner principal adapter.
    return ("return function(conf, ctx) "
            "local cjson=require('cjson.safe'); local auth=ngx.var.http_authorization; "
            "local token=auth and auth:match('^[Bb]earer%s+(.+)$'); "
            "local part=token and token:match('^[^.]+%.([^.]+)%.[^.]+$'); "
            "if not part then return ngx.exit(401) end; "
            "part=part:gsub('-','+'):gsub('_','/'); "
            "local rem=#part%4; if rem>0 then part=part..string.rep('=',4-rem) end; "
            "local raw=ngx.decode_base64(part); local claims=raw and cjson.decode(raw); "
            "if type(claims)~='table' then return ngx.exit(401) end; "
            "local actor=claims['ouf_actor_type']; "
            "if actor~='HUMAN' and actor~='HUMAN_USER' then return ngx.exit(403) end; "
            "end")


def template_facts(template):
    plugins=template.get('plugins',{})
    oidc=plugins.get('openid-connect',{})
    hosts=([template['host']] if template.get('host') else [])+(template.get('hosts') or [])
    return {
        'ENABLED':template.get('status',1)==1,
        'UPSTREAM_INLINE_ONBOARDING_EXACT':template.get('upstream',{}).get('nodes')=={'ouf-onboarding:8080':1},
        'NO_REFERENCES':not any(k in template for k in ('upstream_id','service_id','plugin_config_id')),
        'NO_EXTRA_MATCH_CONDITIONS':not any(template.get(k) for k in ('vars','filter_func','remote_addr','remote_addrs')),
        'OIDC_PRESENT':bool(oidc),
        'OIDC_ENABLED':bool(oidc) and not oidc.get('_meta',{}).get('disable',False),
        'OIDC_BEARER_ONLY_TRUE':oidc.get('bearer_only') is True,
        'EXPECTED_TEMPLATE_SCOPE':oidc.get('required_scopes')==['ouf.onboarding.configuration.read'],
        'KNOWN_PLUGIN_SET':not bool(set(plugins)-{'openid-connect','proxy-rewrite','cors','request-id','prometheus','limit-count','serverless-pre-function','serverless-post-function'}),
        'PUBLIC_HOST_SUPPORTED':not hosts or hosts==['api.ouf-lab.it'],
    }


def template_report(values):
    found=admin.inventory.candidates(values,'GET',TEMPLATE)
    print('RECOVERY_OIDC_TEMPLATE_ROUTE_COUNT='+str(len(found)))
    for index,template in enumerate(found,1):
        prefix='RECOVERY_OIDC_TEMPLATE_'+str(index)+'_'
        facts=template_facts(template)
        for name,value in facts.items():print(prefix+name+'='+str(bool(value)).lower())
        plugins=template.get('plugins',{})
        names=sorted(plugins)
        if any(not re.fullmatch(r'[a-z0-9_-]{1,80}',name) for name in names):raise RuntimeError('RECOVERY_PLUGIN_NAME_UNSUPPORTED')
        print(prefix+'PLUGIN_NAMES='+','.join(names))
        scopes=plugins.get('openid-connect',{}).get('required_scopes') or []
        if not isinstance(scopes,list) or any(not isinstance(x,str) or not re.fullmatch(r'[A-Za-z0-9._:-]{1,160}',x) for x in scopes):raise RuntimeError('RECOVERY_TEMPLATE_SCOPE_UNSUPPORTED')
        print(prefix+'REQUIRED_SCOPES='+(','.join(scopes) or 'NONE_INLINE'))
        bearer=plugins.get('openid-connect',{}).get('bearer_only')
        print(prefix+'BEARER_ONLY_LAYOUT='+('ABSENT' if bearer is None else 'BOOLEAN_TRUE' if bearer is True else 'BOOLEAN_FALSE' if bearer is False else 'UNSUPPORTED_TYPE'))
        print(prefix+'PROXY_REWRITE_PRESENT='+str(bool(plugins.get('proxy-rewrite'))).lower())
        print(prefix+'FAILED_CHECKS='+(','.join(name for name,value in facts.items() if not value) or 'NONE'))
    print('R4A_RECOVERY_OIDC_TEMPLATE_DIAGNOSTIC=COMPLETE READ_ONLY=true ROUTES_UNCHANGED=true IAM_UNCHANGED=true RETRY=false RUN_RESUME=false SECRETS_NOT_PRINTED=true')


def desired_routes(values,required):
    found=admin.inventory.candidates(values,'GET',TEMPLATE)
    if len(found)!=1:raise RuntimeError('RECOVERY_OIDC_TEMPLATE_NOT_UNIQUE')
    template=found[0]
    plugins=template.get('plugins',{})
    oidc=plugins.get('openid-connect',{})
    hosts=([template['host']] if template.get('host') else [])+(template.get('hosts') or [])
    if not all(template_facts(template).values()):
        raise RuntimeError('RECOVERY_OIDC_TEMPLATE_UNSUPPORTED')
    result={}
    for ident,method,resource,action,cap in TARGETS:
        route=dict(status=1,name=ident,desc='Governed HUMAN recovery; exact UUID action; owner authorization retained',
                   uri=BASE+resource+'/*', methods=[method],
                   vars=[['uri','~~','^'+BASE+resource+'/'+UUID+action+'$']],
                   plugins=copy.deepcopy(plugins),
                   upstream={'type':'roundrobin','scheme':'http','nodes':{'ouf-ingestion:8080':1}})
        route['plugins'].pop('proxy-rewrite',None)
        # Never copy template Lua, which can carry another actor/owner contract.
        route['plugins']['serverless-pre-function']={'phase':'rewrite','functions':[strip_identity_headers()]}
        route['plugins']['serverless-post-function']={'phase':'access','functions':[human_guard()]}
        route['plugins']['openid-connect']['required_scopes']=[required[cap]]
        for key in ('host','hosts'):
            if key in template:route[key]=copy.deepcopy(template[key])
        result[ident]=route
    return result


def collision(values,desired):
    for route in values:
        patterns=[route.get('uri')]+(route.get('uris') or [])
        for wanted in desired.values():
            method=wanted['methods'][0];prefix=wanted['uri'][:-1]
            if route.get('methods') and method not in route['methods']:continue
            for pattern in patterns:
                if isinstance(pattern,str) and (pattern.startswith(prefix) or admin.inventory.uri_matches(pattern,prefix+'00000000-0000-0000-0000-000000000000')):
                    raise RuntimeError('RECOVERY_PATH_ALREADY_ROUTED_RECONCILE')


def existing(values):return {str(r['id']):admin.comparable(r) for r in values}


def save(value,exclusive=False):
    if exclusive:
        fd=os.open(RECEIPT,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);temporary=None
    else:
        fd,name=tempfile.mkstemp(prefix='.recovery-routes-',dir=ROOT);temporary=Path(name)
    with os.fdopen(fd,'w') as out:
        json.dump(value,out);out.flush();os.fsync(out.fileno())
    if temporary:os.replace(temporary,RECEIPT)
    fd=os.open(ROOT,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def rollback(key,desired,attempted):
    for ident in reversed(attempted):
        raw,status=admin.api(key,'GET','routes/'+ident,accepted=('200','404'))
        if status=='404':continue
        value=raw.get('value',raw.get('node',{}).get('value'))
        if isinstance(value,str):value=json.loads(value)
        if not isinstance(value,dict) or admin.comparable(value)!=desired[ident]:
            raise RuntimeError('RECOVERY_ROLLBACK_ROUTE_DRIFT_MANUAL_REVIEW')
        admin.api(key,'DELETE','routes/'+ident,accepted=('200','204'))
        _,status=admin.api(key,'GET','routes/'+ident,accepted=('200','404'))
        if status!='404':raise RuntimeError('RECOVERY_ROLLBACK_NOT_VERIFIED')


def private_json(path):
    meta=path.lstat()
    if not stat.S_ISREG(meta.st_mode) or meta.st_uid!=0 or stat.S_IMODE(meta.st_mode)!=0o600:
        raise RuntimeError('RECOVERY_PRIVATE_EVIDENCE_UNSAFE')
    return json.loads(path.read_text())


def verify_saved(values,desired,receipt,before):
    if receipt.get('status')!='PASS':raise RuntimeError('RECOVERY_RECEIPT_NOT_PASS_RECONCILE_DO_NOT_REPUT')
    if receipt.get('desired')!=desired or set(receipt.get('attempted',[]))!=set(desired):
        raise RuntimeError('RECOVERY_RECEIPT_ROUTE_SET_MISMATCH')
    if len(receipt.get('attempted',[]))!=len(desired):raise RuntimeError('RECOVERY_RECEIPT_DUPLICATE_ATTEMPT')
    for ident in desired:
        found=[r for r in values if str(r['id'])==ident]
        if len(found)!=1 or admin.comparable(found[0])!=desired[ident]:
            raise RuntimeError('RECOVERY_SAVED_ROUTE_READBACK_MISMATCH')
    if existing([r for r in values if str(r['id']) not in desired])!=existing(before):
        raise RuntimeError('RECOVERY_EXISTING_ROUTES_DRIFT_SINCE_SNAPSHOT')


def main(args):
    if os.geteuid()!=0:raise RuntimeError('ROOT_REQUIRED')
    os.umask(0o077)
    meta=ROOT.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid!=0 or stat.S_IMODE(meta.st_mode)!=0o700:raise RuntimeError('PRIVATE_ROOT_UNSAFE')
    if args.mode not in ('verify','template') and (RECEIPT.exists() or RECEIPT.is_symlink()):raise RuntimeError('RECOVERY_ROUTE_RECEIPT_EXISTS_RECONCILE_DO_NOT_REPUT')
    helper=admin.inventory.routes.helper
    live=helper.inspect('ouf-ingestion')
    if not live['State']['Running']:raise RuntimeError('INGESTION_NOT_RUNNING')
    if args.mode=='template':
        apisix=helper.inspect('ouf-apisix')
        if not apisix['State']['Running']:raise RuntimeError('APISIX_NOT_RUNNING')
        key=admin.inventory.routes.admin_key(admin.inventory.routes.mounted_config(apisix).read_text())
        raw,_=admin.api(key,'GET','routes')
        template_report(admin.inventory.routes.route_values(raw))
        return
    document=published(live,args.tenant)
    if document.get('bundleId')+':'+str(document.get('bundleVersion'))!=args.expected_policy:
        raise RuntimeError('RECOVERY_ACTIVE_POLICY_DRIFT')
    required=scopes(document)
    apisix=helper.inspect('ouf-apisix')
    if not apisix['State']['Running']:raise RuntimeError('APISIX_NOT_RUNNING')
    key=admin.inventory.routes.admin_key(admin.inventory.routes.mounted_config(apisix).read_text())
    raw,_=admin.api(key,'GET','routes');values=admin.inventory.routes.route_values(raw)
    desired=desired_routes(values,required)
    if args.mode=='verify':
        if not RECEIPT.exists():raise RuntimeError('RECOVERY_RECEIPT_ABSENT_DO_NOT_ASSUME_SUCCESS')
        receipt=private_json(RECEIPT)
        status=receipt.get('status')
        if status not in ('PASS','UNVERIFIED_DO_NOT_REPUT','ROLLED_BACK','MANUAL_RECOVERY_REQUIRED'):
            raise RuntimeError('RECOVERY_RECEIPT_STATUS_UNSUPPORTED')
        print('RECOVERY_SAVED_RECEIPT_STATUS='+status,flush=True)
        snapshot=Path(receipt['beforeSnapshot'])
        if snapshot.name!='routes-before.json' or snapshot.parent.parent!=ROOT:
            raise RuntimeError('RECOVERY_SNAPSHOT_PATH_UNSUPPORTED')
        parent=snapshot.parent.lstat()
        if not stat.S_ISDIR(parent.st_mode) or parent.st_uid!=0 or stat.S_IMODE(parent.st_mode)!=0o700:
            raise RuntimeError('RECOVERY_SNAPSHOT_DIRECTORY_UNSAFE')
        before=admin.inventory.routes.route_values(private_json(snapshot))
        verify_saved(values,desired,receipt,before)
        now=helper.inspect('ouf-ingestion')
        if any(now[k]!=live[k] for k in ('Id','Image','Config','HostConfig','Mounts')):
            raise RuntimeError('INGESTION_CHANGED_DURING_ROUTE_VERIFY')
        print('R4A_RECOVERY_ROUTES_READBACK=PASS RECEIPT_MATCH=true ROUTE_COUNT=4 EXISTING_ROUTES_PRESERVED=true')
        print('R4A_RECOVERY_ROUTES_VERIFY=COMPLETE READ_ONLY=true ROUTES_UNCHANGED=true IAM_UNCHANGED=true RETRY=false RUN_RESUME=false OWNER_AUTHORIZATION_NOT_PROVEN=true SECRETS_NOT_PRINTED=true')
        return
    collision(values,desired)
    for ident,method,resource,action,cap in TARGETS:
        _,status=admin.api(key,'GET','routes/'+ident,accepted=('200','404'))
        if status!='404':raise RuntimeError('RECOVERY_ROUTE_ID_ALREADY_OWNED')
        print('RECOVERY_ROUTE_PLANNED='+ident+' METHOD='+method+' REQUIRED_SCOPE='+cap+' EXACT_UUID_ACTION_MATCH=true OWNER_PATH_PRESERVED=true PROXY_REWRITE_ABSENT=true')
    print('R4A_RECOVERY_ROUTES_PLAN=PASS MODE='+args.mode+' ROUTE_COUNT=4 SHARED_ALL_TENANT_SOURCES=true',flush=True)
    if args.mode=='plan':
        print('R4A_RECOVERY_ROUTES=PLANNED LIVE_UNCHANGED=true RETRY=false RUN_RESUME=false');return
    snapshot=Path(tempfile.mkdtemp(prefix='ingestion-recovery-routes-',dir=ROOT))/'routes-before.json'
    with snapshot.open('w') as out:json.dump(raw,out);out.flush();os.fsync(out.fileno())
    snapshot.chmod(0o600)
    receipt=dict(status='UNVERIFIED_DO_NOT_REPUT',beforeSnapshot=str(snapshot),desired=desired,attempted=[])
    save(receipt,exclusive=True)
    try:
        current,_=admin.api(key,'GET','routes')
        if existing(admin.inventory.routes.route_values(current))!=existing(values) or published(live,args.tenant)!=document:
            raise RuntimeError('RECOVERY_ROUTE_OR_POLICY_DRIFT_BEFORE_PUT')
        for ident,_,_,_,_ in TARGETS:
            receipt['attempted'].append(ident);save(receipt)
            admin.api(key,'PUT','routes/'+ident,desired[ident],accepted=('200','201'))
        after,_=admin.api(key,'GET','routes');new=admin.inventory.routes.route_values(after)
        if existing([r for r in new if str(r['id']) not in desired])!=existing(values):
            raise RuntimeError('RECOVERY_EXISTING_ROUTES_CHANGED')
        for ident in desired:
            found=[r for r in new if str(r['id'])==ident]
            if len(found)!=1 or admin.comparable(found[0])!=desired[ident]:
                raise RuntimeError('RECOVERY_ROUTE_READBACK_MISMATCH')
        now=helper.inspect('ouf-ingestion')
        if any(now[k]!=live[k] for k in ('Id','Image','Config','HostConfig','Mounts')):
            raise RuntimeError('INGESTION_CHANGED_DURING_ROUTE_INSTALL')
        receipt['status']='PASS';save(receipt)
    except BaseException:
        try:rollback(key,desired,receipt['attempted']);receipt['status']='ROLLED_BACK'
        except Exception:receipt['status']='MANUAL_RECOVERY_REQUIRED'
        save(receipt);print('R4A_RECOVERY_ROUTES_ROLLBACK='+receipt['status']);raise
    print('R4A_RECOVERY_ROUTES=PASS ROUTE_COUNT=4 EXISTING_ROUTES_PRESERVED=true')
    print('R4A_RECOVERY_ROUTES_RECEIPT='+str(RECEIPT)+' PRIVATE=true')
    print('R4A_RECOVERY_ROUTES_SNAPSHOT='+str(snapshot)+' PRIVATE=true')
    print('R4A_RECOVERY_ROUTES_COMPLETE=PASS IAM_UNCHANGED=true WORKERS_UNCHANGED=true RETRY=false RUN_RESUME=false INTAKE_POST=false HUMAN_TOKEN_NOT_TESTED=true OWNER_AUTHORIZATION_NOT_PROVEN=true SECRETS_NOT_PRINTED=true')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('template','plan','apply','verify'))
    p.add_argument('--tenant',required=True)
    p.add_argument('--expected-policy',required=True)
    try:main(p.parse_args())
    except Exception as error:
        code=str(error) if isinstance(error,RuntimeError) else type(error).__name__
        print('R4A_RECOVERY_ROUTES=BLOCKED CODE='+code+' RETRY=false RUN_RESUME=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
