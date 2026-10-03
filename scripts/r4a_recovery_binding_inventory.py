#!/usr/bin/env python3
"""Parameterized read-only IAM/Gateway inventory; private snapshot, no apply."""
import argparse
import fnmatch
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit
import r4a_execution_route_inventory as parsing
import r4a_prepare_scoped_human_policy as private


def run(argv,stdin=None):
    return subprocess.run(argv,input=stdin,capture_output=True,text=True,check=True,timeout=30).stdout.strip()


def inspect(name):return json.loads(run(['docker','inspect',name]))[0]


def config_source(row,destination):
    target=Path(destination);private.require(target.is_absolute(),'CONFIG_DESTINATION_INVALID')
    paths=[Path(m['Source'])/target.relative_to(Path(m['Destination'])) for m in row.get('Mounts',[])
        if m.get('Type')=='bind' and target.is_relative_to(Path(m['Destination']))]
    private.require(len(paths)==1,'CONFIG_BIND_NOT_UNIQUE')
    return paths[0]


def candidates(routes,method,path):
    # Conservative URI candidates only: no claim of radixtree/vars priority parity.
    return [row for row in routes if (not row.get('methods') or method in row['methods'])
        and any(isinstance(uri,str) and fnmatch.fnmatchcase(path,uri) for uri in
                [row.get('uri')]+(row.get('uris') or []))]


def safe(value):
    return str(value) if isinstance(value,(str,int)) and re.fullmatch(r'[A-Za-z0-9_./:*{}-]{1,256}',str(value)) else 'REDACTED'


def gateway(args):
    before=inspect(args.gateway_container);private.require(before['State']['Running'],'GATEWAY_NOT_RUNNING')
    origin=urlsplit(args.admin_origin)
    private.require(origin.scheme in ('http','https') and origin.hostname and not origin.username and not origin.password
        and not origin.query and not origin.fragment and origin.path in ('','/'),'ADMIN_ORIGIN_INVALID')
    private.require(origin.scheme=='https' or origin.hostname in ('127.0.0.1','localhost','::1'),'ADMIN_CLEAR_HTTP_NOT_LOOPBACK')
    key=parsing.admin_key(config_source(before,args.config_destination).read_text())
    curl=('silent\nshow-error\nmax-time = 15\nmax-filesize = 10485760\nrequest = "GET"\n'
          +'header = '+json.dumps('X-API-KEY: '+key)+'\nurl = '+json.dumps(args.admin_origin.rstrip('/')+'/apisix/admin/routes')
          +'\nwrite-out = "\\n%{http_code}"\n')
    raw=run(['docker','run','--rm','--pull','never','-i','--read-only','--cap-drop','ALL','--security-opt',
        'no-new-privileges','--network','container:'+args.gateway_container,args.curl_image,'--config','-'],curl)
    body,sep,status=raw.rpartition('\n');private.require(sep and status=='200','GATEWAY_ADMIN_READ_NOT_200')
    routes=parsing.route_values(json.loads(body))
    for name,method,path in (('REVIEW','GET',args.review_path),('RETRY','POST',args.retry_path)):
        rows=candidates(routes,method,path)
        print('RECOVERY_GATEWAY_'+name+'_URI_CANDIDATES='+str(len(rows)),flush=True)
        for row in rows:
            plugins=row.get('plugins',{});oidc=plugins.get('openid-connect',{})
            print('RECOVERY_GATEWAY_'+name+'_CANDIDATE='+safe(row.get('id'))
                +' ENABLED='+str(row.get('status',1)==1).lower()
                +' UDP_INLINE='+str(row.get('upstream',{}).get('nodes')=={args.udp_node:1}).lower()
                +' SCOPE_MATCH='+str(oidc.get('required_scopes')==[args.scope]).lower()
                +' REWRITE='+str(bool(plugins.get('proxy-rewrite'))).lower()
                +' EXTRA_MATCH_CONDITIONS='+str(any(row.get(k) for k in ('vars','filter_func','remote_addr','remote_addrs'))).lower())
    selected=[row for row in routes if row.get('upstream',{}).get('nodes') in [{node:1} for node in args.template_node]]
    print('RECOVERY_GATEWAY_TEMPLATE_COUNT='+str(len(selected)))
    for row in selected:
        plugins=row.get('plugins',{});oidc=plugins.get('openid-connect',{})
        print('RECOVERY_GATEWAY_TEMPLATE_ID='+safe(row.get('id'))+' URI='+safe(row.get('uri'))
            +' OIDC_BEARER_ONLY='+str(oidc.get('bearer_only') is True).lower()
            +' LIMITS='+str(bool(plugins.get('limit-count'))).lower()
            +' INLINE='+str(not any(k in row for k in ('upstream_id','service_id','plugin_config_id'))).lower())
    after=inspect(args.gateway_container)
    private.require(all(after.get(k)==before.get(k) for k in ('Id','Image','Config','HostConfig','Mounts'))
        and after['State']['Running'] and after['State']['StartedAt']==before['State']['StartedAt'],'GATEWAY_CHANGED_DURING_READ')
    return {'status':'PASS_READ_ONLY','containerId':before['Id'],'routes':routes,'uriRoutingParityProven':False}


def iam(args):
    def get(path,*flags):return json.loads(run(['docker','exec',args.keycloak_container,args.kcadm,'get',path,*flags,'-r',args.realm]))
    rows=[r for r in get('client-scopes') if r.get('name')==args.scope]
    private.require(len(rows)<=1,'IAM_DUPLICATE_SCOPE')
    clients=[r for r in get('clients','--fields','id,clientId') if r.get('clientId')==args.client]
    private.require(len(clients)==1,'IAM_CLIENT_NOT_UNIQUE')
    client=clients[0];base='clients/'+client['id']
    defaults=get(base+'/default-client-scopes');optionals=get(base+'/optional-client-scopes')
    default=any(r.get('name')==args.scope for r in defaults);optional=any(r.get('name')==args.scope for r in optionals)
    private.require(not (default and optional),'IAM_BINDING_CONFLICT')
    details=get(base,'--fields','enabled,publicClient,serviceAccountsEnabled')
    print('RECOVERY_IAM_SCOPE_EXISTS='+str(bool(rows)).lower()
        +' OIDC_PROTOCOL='+str(bool(rows) and rows[0].get('protocol')=='openid-connect').lower()
        +' INCLUDED_IN_TOKEN_SCOPE='+str(bool(rows) and rows[0].get('attributes',{}).get('include.in.token.scope')=='true').lower())
    print('RECOVERY_IAM_CLIENT_ENABLED='+str(details.get('enabled') is True).lower()
        +' SCOPE_BINDING='+('DEFAULT' if default else 'OPTIONAL' if optional else 'NONE'))
    return {'status':'PASS_READ_ONLY','scope':rows,'client':client,'details':details,
            'defaultScopes':defaults,'optionalScopes':optionals}


def main(args):
    private.require(os.geteuid()==0,'ROOT_REQUIRED');private.private(args.snapshot.parent,True)
    for value in (args.gateway_container,args.keycloak_container,args.realm,args.client,args.scope):
        private.require(re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,159}',value),'IDENTIFIER_INVALID')
    private.reserve(args.snapshot);state={'status':'READING','iam':None,'gateway':None};private.write(args.snapshot,state)
    for name,action in (('gateway',gateway),('iam',iam)):
        try:state[name]=action(args)
        except Exception as error:
            code=str(error) if isinstance(error,private.Blocked) else 'UNCLASSIFIED'
            state[name]={'status':'BLOCKED','code':code,'type':type(error).__name__}
            print('RECOVERY_'+name.upper()+'_INVENTORY=BLOCKED CODE='+code+' TYPE='+type(error).__name__)
        private.write(args.snapshot,state)
    passed=all(state[name]['status']=='PASS_READ_ONLY' for name in ('gateway','iam'))
    state['status']='PASS_READ_ONLY' if passed else 'PARTIAL_READ_ONLY';private.write(args.snapshot,state)
    print('R4A_RECOVERY_BINDING_SNAPSHOT='+str(args.snapshot)+' PRIVATE=true')
    print('R4A_RECOVERY_BINDING_INVENTORY='+('PASS' if passed else 'PARTIAL')
        +' READ_ONLY=true IAM_UNCHANGED=true ROUTES_UNCHANGED=true POLICY_UNPUBLISHED=true RETRY=false SECRETS_NOT_PRINTED=true')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('gateway-container','config-destination','admin-origin','curl-image','udp-node','review-path','retry-path',
                 'keycloak-container','kcadm','realm','client','scope'):p.add_argument('--'+name,required=True)
    p.add_argument('--template-node',action='append',required=True);p.add_argument('--snapshot',type=Path,required=True)
    try:main(p.parse_args())
    except Exception as error:
        code=str(error) if isinstance(error,private.Blocked) else 'UNCLASSIFIED'
        print('R4A_RECOVERY_BINDING_INVENTORY=BLOCKED CODE='+code+' TYPE='+type(error).__name__+' READ_ONLY=true RETRY=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
