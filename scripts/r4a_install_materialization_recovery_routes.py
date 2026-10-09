#!/usr/bin/env python3
"""Install/verify parameterized HUMAN recovery routes; no owner business writes."""
import argparse
import copy
import fnmatch
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit
import r4a_recovery_binding_inventory as inventory
import r4a_prepare_scoped_human_policy as private

UUID='[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}'
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



def comparable(row):
    return {k:v for k,v in row.items() if k not in ('id','create_time','update_time')}

def index(rows):
    result={}
    for row in rows:
        ident=str(row['id'])
        private.require(ident not in result,'DUPLICATE_ROUTE_ID')
        result[ident]=comparable(row)
    return result

def desired(rows,args):
    templates=[r for r in rows if str(r.get('id'))==args.template_id]
    private.require(len(templates)==1,'TEMPLATE_NOT_UNIQUE')
    template=templates[0];plugins=template.get('plugins',{});oidc=plugins.get('openid-connect',{})
    private.require(template.get('status',1)==1 and template.get('uri')==args.template_uri
        and template.get('methods')==['GET']
        and not any(k in template for k in ('upstream_id','service_id','plugin_config_id','uris'))
        and not any(template.get(k) for k in ('vars','filter_func','remote_addr','remote_addrs'))
        and template.get('upstream',{}).get('nodes')=={args.template_node:1}
        and oidc.get('bearer_only') is True and oidc.get('required_scopes')==[args.template_scope]
        and not oidc.get('_meta',{}).get('disable',False)
        and bool(plugins.get('limit-count')) and not plugins['limit-count'].get('_meta',{}).get('disable',False)
        and bool(oidc.get('discovery')) and bool(oidc.get('client_id'))
        and set(plugins)<= {'openid-connect','proxy-rewrite','cors','request-id','prometheus','limit-count',
                          'serverless-pre-function','serverless-post-function','client-control'}
        and (not template.get('host') or template['host']==args.public_host)
        and (not template.get('hosts') or template['hosts']==[args.public_host]),'TEMPLATE_SECURITY_UNSUPPORTED')
    result={}
    for ident,method,action in ((args.review_id,'GET',''),(args.retry_id,'POST','/retry')):
        copied=copy.deepcopy(plugins);copied.pop('proxy-rewrite',None)
        copied['openid-connect']['required_scopes']=[args.scope]
        copied['serverless-pre-function']={'phase':'rewrite','functions':[strip_identity_headers()]}
        copied['serverless-post-function']={'phase':'access','functions':[human_guard()]}
        result[ident]={'status':1,'name':ident,'desc':'Governed HUMAN recovery; owner authorization retained',
            'uri':args.base_path+'/*','methods':[method],'host':args.public_host,
            'vars':[['uri','~~','^'+re.escape(args.base_path)+'/'+UUID+action+'$']],
            'plugins':copied,'upstream':{'type':'roundrobin','scheme':'http','nodes':{args.udp_node:1}}}
    return result

def collision(rows,wanted):
    for row in rows:
        for route in wanted.values():
            if row.get('methods') and route['methods'][0] not in row['methods']:continue
            prefix=route['uri'][:-1]
            for pattern in [row.get('uri')]+(row.get('uris') or []):
                private.require(not isinstance(pattern,str) or not
                    (pattern.startswith(prefix) or fnmatch.fnmatchcase(prefix+'00000000-0000-0000-0000-000000000000',pattern)),
                    'PATH_ALREADY_ROUTED_RECONCILE')

class Gateway:
    def __init__(self,args):
        self.args=args;self.before=inventory.inspect(args.gateway_container)
        private.require(self.before['State']['Running'],'GATEWAY_NOT_RUNNING')
        origin=urlsplit(args.admin_origin)
        private.require(origin.scheme in ('http','https') and origin.hostname and not origin.username
            and not origin.password and not origin.query and not origin.fragment and origin.path in ('','/')
            and (origin.scheme=='https' or origin.hostname in ('127.0.0.1','localhost','::1')),'ADMIN_ORIGIN_INVALID')
        self.key=inventory.parsing.admin_key(inventory.config_source(self.before,args.config_destination).read_text())
    def api(self,method,path,body=None,accepted=('200',)):
        config='silent\nshow-error\nmax-time = 15\nmax-filesize = 10485760\n'
        config+='request = '+json.dumps(method)+'\nheader = '+json.dumps('X-API-KEY: '+self.key)+'\n'
        config+='url = '+json.dumps(self.args.admin_origin.rstrip('/')+'/apisix/admin/'+path)+'\n'
        if body is not None:
            config+='header = "Content-Type: application/json"\ndata = '+json.dumps(json.dumps(body))+'\n'
        config+='write-out = "\\n%{http_code}"\n'
        raw=inventory.run(['docker','run','--rm','--pull','never','-i','--read-only','--cap-drop','ALL',
            '--security-opt','no-new-privileges','--network','container:'+self.args.gateway_container,
            self.args.curl_image,'--config','-'],config)
        payload,sep,status=raw.rpartition('\n')
        private.require(sep and status in accepted,'ADMIN_HTTP_UNEXPECTED')
        return (json.loads(payload) if payload.strip() else {}),status
    def rows(self):return inventory.parsing.route_values(self.api('GET','routes')[0])
    def unchanged(self):
        after=inventory.inspect(self.args.gateway_container)
        private.require(all(after.get(k)==self.before.get(k) for k in ('Id','Image','Config','HostConfig','Mounts'))
            and after['State']['Running'] and after['State']['StartedAt']==self.before['State']['StartedAt'],
            'GATEWAY_RUNTIME_CHANGED')

def one(document):
    row=document.get('value',document.get('node',{}).get('value'))
    if isinstance(row,str):row=json.loads(row)
    private.require(isinstance(row,dict),'ADMIN_ROUTE_SHAPE_INVALID')
    return comparable(row)

def readback(rows,wanted,baseline):
    current=index(rows)
    private.require(all(current.get(k)==v for k,v in wanted.items()),'ROUTE_READBACK_MISMATCH')
    private.require({k:v for k,v in current.items() if k not in wanted}==index(baseline),'EXISTING_ROUTES_DRIFT')

def rollback(gateway,state):
    for ident in reversed(state['attempted']):
        doc,status=gateway.api('GET','routes/'+ident,accepted=('200','404'))
        if status=='404':continue
        private.require(one(doc)==state['desired'][ident],'ROLLBACK_ROUTE_DRIFT_MANUAL_REVIEW')
        gateway.api('DELETE','routes/'+ident,accepted=('200','204'))
        private.require(gateway.api('GET','routes/'+ident,accepted=('200','404'))[1]=='404','ROLLBACK_NOT_VERIFIED')
    private.require(index(gateway.rows())==index(state['baseline']),'ROLLBACK_EXISTING_ROUTES_DRIFT')

def execute(args,gateway,baseline):
    wanted=desired(baseline,args);rows=gateway.rows()
    if args.mode=='verify':
        private.private(args.receipt);state=json.loads(args.receipt.read_text())
        private.require(state.get('desired')==wanted and state.get('baseline')==baseline
            and state.get('attempted')==list(wanted)
            and state.get('status') in ('PASS','UNVERIFIED_DO_NOT_REPUT','MANUAL_RECOVERY_REQUIRED'),'RECEIPT_RECONCILIATION_REQUIRED')
        readback(rows,wanted,baseline);gateway.unchanged()
        print('R4A_UDP_RECOVERY_ROUTES_VERIFY=PASS READ_ONLY=true ROUTE_COUNT=2 EXISTING_ROUTES_PRESERVED=true RETRY=false OWNER_AUTHORIZATION_NOT_PROVEN=true SECRETS_NOT_PRINTED=true')
        return
    private.require(not args.receipt.exists() and not args.receipt.is_symlink(),'RECEIPT_EXISTS_DO_NOT_REPUT')
    private.require(index(rows)==index(baseline),'INVENTORY_DRIFT')
    collision(rows,wanted)
    for ident in wanted:
        private.require(gateway.api('GET','routes/'+ident,accepted=('200','404'))[1]=='404','ROUTE_ID_ALREADY_OWNED')
    gateway.unchanged()
    print('R4A_UDP_RECOVERY_ROUTES_PLAN=PASS ROUTE_COUNT=2 EXACT_UUID_ACTIONS=true POLICY_PUBLISH_NOT_CALLED=true RETRY=false',flush=True)
    if args.mode=='plan':return
    private.reserve(args.receipt)
    state={'status':'UNVERIFIED_DO_NOT_REPUT','baseline':baseline,'desired':wanted,'attempted':[]}
    private.write(args.receipt,state)
    try:
        private.require(index(gateway.rows())==index(baseline),'DRIFT_BEFORE_PUT')
        for ident in wanted:
            private.require(gateway.api('GET','routes/'+ident,accepted=('200','404'))[1]=='404','ROUTE_ID_RACE')
            state['attempted'].append(ident);private.write(args.receipt,state)
            gateway.api('PUT','routes/'+ident,wanted[ident],accepted=('200','201'))
        readback(gateway.rows(),wanted,baseline);gateway.unchanged()
        state['status']='PASS';private.write(args.receipt,state)
    except BaseException:
        try:rollback(gateway,state);state['status']='ROLLED_BACK'
        except Exception:state['status']='MANUAL_RECOVERY_REQUIRED'
        private.write(args.receipt,state)
        print('R4A_UDP_RECOVERY_ROUTES_ROLLBACK='+state['status'],flush=True)
        raise
    print('R4A_UDP_RECOVERY_ROUTES_RECEIPT='+str(args.receipt)+' PRIVATE=true')
    print('R4A_UDP_RECOVERY_ROUTES_APPLY=PASS ROUTE_COUNT=2 EXISTING_ROUTES_PRESERVED=true POLICY_PUBLISH_NOT_CALLED=true RETRY=false OWNER_AUTHORIZATION_NOT_PROVEN=true SECRETS_NOT_PRINTED=true')

def main(args):
    private.require(os.geteuid()==0,'ROOT_REQUIRED')
    private.private(args.snapshot);private.private(args.receipt.parent,True)
    snapshot=json.loads(args.snapshot.read_text())
    private.require(snapshot.get('gateway',{}).get('status')=='PASS_READ_ONLY','GATEWAY_SNAPSHOT_NOT_PASS')
    for value in (args.review_id,args.retry_id,args.template_id,args.scope):
        private.require(bool(re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,159}',value)),'IDENTIFIER_INVALID')
    private.require(args.review_id!=args.retry_id,'ROUTE_IDS_NOT_DISTINCT')
    private.require(bool(re.fullmatch('/[A-Za-z0-9_/-]+',args.base_path)) and not args.base_path.endswith('/'),'BASE_PATH_INVALID')
    private.require(bool(re.fullmatch('[A-Za-z0-9.-]+',args.public_host)),'PUBLIC_HOST_INVALID')
    gateway=Gateway(args)
    private.require(gateway.before['Id']==snapshot['gateway']['containerId'],'GATEWAY_ID_CHANGED')
    execute(args,gateway,snapshot['gateway']['routes'])

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('plan','apply','verify'))
    for name in ('gateway-container','config-destination','admin-origin','curl-image','template-id','template-uri',
                 'template-node','template-scope','public-host','udp-node','base-path','scope','review-id','retry-id'):
        parser.add_argument('--'+name,required=True)
    for name in ('snapshot','receipt'):parser.add_argument('--'+name,type=Path,required=True)
    try:main(parser.parse_args())
    except Exception as error:
        code=str(error) if isinstance(error,private.Blocked) else 'UNCLASSIFIED'
        print('R4A_UDP_RECOVERY_ROUTES=BLOCKED CODE='+code+' TYPE='+type(error).__name__+' RETRY=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
