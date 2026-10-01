#!/usr/bin/env python3
"""Collect failure, token, policy, routes and redacted logs in one read-only run."""
import argparse
import base64
from collections import Counter
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import uuid
from urllib.parse import urlparse
import r4a_execution_route_inventory as routes
helper=routes.helper
CAPS=('datalake.write','udp.candidate.write')
PATHS={'/api/internal/v1/lake/objects':'LAKE','/api/internal/v1/handoffs':'HANDOFF','/api/onboarding/v1/runtime/publications':'PUBLICATIONS','/internal/object-storage/v1/content':'MANAGED_CONTENT'}


def flag(key,value):print(key+'='+str(bool(value)).lower())


def section(name,call):
    try:call()
    except Exception as error:
        # Never include raw exception text: it may embed a credential or response.
        print('DIAGNOSTIC_'+name+'=UNAVAILABLE TYPE='+type(error).__name__)


def query(database,sql):
    return json.loads(helper.run(['docker','exec','ouf-postgres','psql','-X','-qAt','-v','ON_ERROR_STOP=1','-U',database,'-d',database,'-c','begin read only; set local statement_timeout=15000; '+sql+'; rollback;']))


def objects(value):
    if isinstance(value,dict):
        yield value
        for child in value.values():yield from objects(child)
    elif isinstance(value,list):
        for child in value:yield from objects(child)


def policy_facts(doc,claims,prefix):
    rows=list(objects(doc))
    service=claims.get('client_id') or claims.get('azp')
    now=datetime.now(timezone.utc)
    for cap in CAPS:
        descriptors=[x for x in rows if x.get('capabilityId')==cap and 'requiredScope' in x and 'allowedActors' in x]
        grants=[x for x in rows if x.get('capabilityId')==cap and 'grantId' in x]
        matching=[]
        for grant in grants:
            try:
                start=datetime.fromisoformat(grant['validFrom'].replace('Z','+00:00'));end=datetime.fromisoformat(grant['validUntil'].replace('Z','+00:00'))
                constraint=grant.get('constraints') or {}
                if (grant.get('tenantId')==claims.get('tenant_id') and grant.get('servicePrincipalId')==service
                    and (grant.get('subjectId') is None or grant.get('subjectId')==claims.get('sub'))
                    and not grant.get('organizationId') and start<=now<end
                    and constraint.get('effect')=='ALLOW' and constraint.get('resourceType')=='ingestion-intake'
                    and constraint.get('resourceId') is None and constraint.get('resourceAttributes')=={'module':'UDP'}
                    and not any(constraint.get(k) for k in ('externalRoleRef','allowedDataLabels','allowedDetailLevels','requiredAcr','requiredAmr','maxAuthenticationAgeSeconds'))):matching.append(grant)
            except (TypeError,ValueError,KeyError):pass
        print(prefix+'_'+cap+'_DESCRIPTORS='+str(len(descriptors)))
        print(prefix+'_'+cap+'_GRANTS='+str(len(grants)))
        flag(prefix+'_'+cap+'_SERVICE_SCOPE_DESCRIPTOR',len(descriptors)==1 and 'SERVICE' in descriptors[0]['allowedActors'] and descriptors[0]['requiredScope']==cap)
        print(prefix+'_'+cap+'_MATCHING_UNRESTRICTED_GRANTS_DIAGNOSTIC='+str(len(matching)))


def curl_json(url,token,network='ouf-backend'):
    parsed=urlparse(url)
    if parsed.scheme!='https' or parsed.username or parsed.password or parsed.fragment:raise ValueError('endpoint')
    config='silent\nshow-error\nmax-time = 10\nmax-filesize = 2097152\nheader = "Authorization: Bearer '+token+'"\nurl = '+json.dumps(url)+'\nwrite-out = "\\n%{http_code}"\n'
    raw=helper.run(['docker','run','--rm','-i','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--network',network,'curlimages/curl:8.16.0','--config','-'],input=config,timeout=20)
    body,sep,code=raw.rpartition('\n')
    if not sep:body,code='',raw
    if not re.fullmatch(r'\d{3}',code):raise ValueError('status')
    return code,json.loads(body) if code=='200' else None


def mapped_file(container,path):
    target=Path(path)
    if not target.is_absolute():raise ValueError('mount path')
    found=[]
    for mount in container['Mounts']:
        dest=Path(mount['Destination'])
        if mount['Type']=='bind' and (target==dest or target.is_relative_to(dest)):
            found.append(Path(mount['Source'])/target.relative_to(dest))
    if len(found)!=1:raise ValueError('mount ambiguity')
    return found[0]


def log_facts(text):
    codes=Counter(re.findall(r'\b(?:ING|UDP|AUTHZ|AUTHORIZATION|POLICY|SNAPSHOT)_[A-Z0-9_]{2,100}\b',text))
    safe={key:value for key,value in sorted(codes.items()) if any(word in key for word in ('DENIED','FAIL','UNAVAILABLE','EXPIRED','STALE','MISSING','REQUIRED','REJECT','FORBIDDEN','QUARANTINE','GATEWAY','INVALID','BUNDLE'))}
    return safe


def access_facts(text):
    result=Counter()
    for line in text.splitlines():
        try:
            row=json.loads(line)
            request=row.get('request','');path=row.get('uri') or (request.split()[1] if len(request.split())>=2 else '')
            status=str(row.get('status','UNKNOWN'));upstream=str(row.get('upstream_status','UNKNOWN'))
        except (ValueError,AttributeError):
            try:
                parts=shlex.split(line);idx=next(i for i,x in enumerate(parts) if re.match(r'^(GET|POST|HEAD|OPTIONS) /',x))
                path=parts[idx].split()[1];status=parts[idx+1];upstream='UNKNOWN'
                for j in range(idx+2,len(parts)-1):
                    if re.fullmatch(r'\d{1,3}(?:\.\d{1,3}){3}:\d{1,5}',parts[j]):upstream=parts[j+1];break
            except (ValueError,StopIteration,IndexError):continue
        label=PATHS.get(path.split('?')[0])
        if label and re.fullmatch(r'\d{3}',status):
            result[(label,status,upstream if re.fullmatch(r'\d{3}|-',upstream) else 'UNKNOWN')]+=1
    return [{'endpoint':p,'http':s,'upstream_http':u,'count':n} for (p,s,u),n in sorted(result.items())]


def main(args):
    if os.geteuid()!=0:raise RuntimeError('root')
    args.run=str(uuid.UUID(args.run))
    print('R4A_EXECUTION_FAILURE_BUNDLE=READ_ONLY RUN_ID='+args.run,flush=True)
    def failures():
        data=query('ouf_ingestion',"select json_build_object('run',(select row_to_json(x) from (select run_id,state,failure_code,control_version from ouf_ingestion.ing_run where run_id='"+args.run+"') x),'attempts',coalesce((select json_agg(x order by attempt_no) from (select a.attempt_no,a.state,a.reason_code,q.quarantine_id,q.lifecycle_state,q.lifecycle_version,q.blocking,(q.payload_ref like 'lake://%') raw_lake_ref_present from ouf_ingestion.processing_attempt a left join ouf_ingestion.ing_quarantine q on q.attempt_id=a.attempt_id where a.run_id='"+args.run+"') x),'[]'::json))")
        for row in [data.get('run') or {},*data.get('attempts',[])]:
            for key in ('state','failure_code','reason_code','lifecycle_state'):
                if row.get(key) is not None and not re.fullmatch(r'[A-Z0-9_]{1,120}',str(row[key])):row[key]='REDACTED'
        print('EXECUTION_FAILURES='+json.dumps(data,sort_keys=True))
    section('FAILURES',failures)
    # Collect logs before config/token parsing, so missing bindings do not hide
    # the evidence that explains them.
    for name in ('ouf-ingestion','ouf-udp','ouf-apisix'):
        def logs(name=name):
            result=subprocess.run(['docker','logs','--since','1h','--tail','3000',name],check=True,capture_output=True,text=True,timeout=20)
            print('LOG_'+name+'_SYMBOLIC_FAILURES='+json.dumps(log_facts(result.stdout+'\n'+result.stderr),sort_keys=True))
        section('LOG_'+name,logs)
    def access_logs():
        raw=helper.run(['docker','exec','ouf-apisix','tail','-n','3000','/usr/local/apisix/logs/access.log'])
        print('APISIX_ACCESS_STATUS_EVIDENCE='+json.dumps(access_facts(raw),sort_keys=True))
        print('APISIX_LOG_WINDOW_BOUNDED=true EXACT_REQUEST_CORRELATION_NOT_PROVEN=true')
    section('ACCESS_LOG',access_logs)
    ing=helper.inspect('ouf-ingestion');udp=helper.inspect('ouf-udp');apisix=helper.inspect('ouf-apisix')
    for name,container in [('ING',ing),('UDP',udp)]:
        flag(name+'_RUNNING',container['State']['Running'])
    props=mapped_file(ing,helper.PROPERTIES).read_text()
    token=mapped_file(ing,helper.literal_property(props,'ouf.ingestion.activation.token-file')).read_text().strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',token):raise ValueError('token')
    part=token.split('.')[1];claims=json.loads(base64.urlsafe_b64decode(part+'='*(-len(part)%4)))
    env=dict(x.split('=',1) for x in udp['Config'].get('Env',[]) if '=' in x)
    flag('TOKEN_NOT_EXPIRED',type(claims.get('exp')) is int and claims['exp']>time_now())
    flag('TOKEN_SERVICE_ACTOR',claims.get('ouf_actor_type')=='SERVICE')
    flag('TOKEN_SERVICE_PRINCIPAL_INGESTION',(claims.get('client_id') or claims.get('azp'))=='ouf-ingestion')
    flag('TOKEN_CLIENT_ALIAS_CONSISTENT',not claims.get('client_id') or not claims.get('azp') or claims['client_id']==claims['azp'])
    flag('UDP_TENANT_MATCHES_TOKEN',env.get('OUF_UDP_TENANT_ID')==claims.get('tenant_id'))
    flag('UDP_IAM_ENABLED_ENV',env.get('OUF_UDP_IAM_ENABLED')=='true')
    flag('UDP_ISSUER_ENV_MATCH',env.get('OUF_UDP_IAM_ISSUER')==claims.get('iss'))
    audience=claims.get('aud',[])
    if isinstance(audience,str):audience=[audience]
    flag('UDP_AUDIENCE_ENV_IN_TOKEN',isinstance(audience,list) and env.get('OUF_UDP_IAM_AUDIENCE') in audience)
    flag('TOKEN_ACR_PRESENT',isinstance(claims.get('acr'),str) and bool(claims['acr']))
    for cap in CAPS:flag('TOKEN_SCOPE_'+cap,cap in str(claims.get('scope','')).split())
    def active_policy():
        code,doc=curl_json(helper.literal_property(props,'ouf.authorization.registry-url'),token)
        print('ACTIVE_POLICY_HTTP='+code)
        if doc is not None:
            version=doc.get('bundleVersion');print('ACTIVE_POLICY_VERSION='+str(version if type(version) is int else 'UNSUPPORTED'))
            policy_facts(doc,claims,'ACTIVE_POLICY')
    section('ACTIVE_POLICY',active_policy)
    def owner_policy():
        settings={}
        def add(key,value):settings.setdefault(re.sub(r'[^a-z0-9]','',key.lower()),[]).append(value)
        for key,value in env.items():add(key,value)
        def flatten(doc,prefix=''):
            for key,value in doc.items():
                name=prefix+'.'+key if prefix else key
                if isinstance(value,dict):flatten(value,name)
                else:add(name,value)
        if env.get('SPRING_APPLICATION_JSON'):flatten(json.loads(env['SPRING_APPLICATION_JSON']))
        for mount in udp['Mounts']:
            if mount['Destination'].endswith('.properties') and mount['Type']=='bind':
                for line in Path(mount['Source']).read_text().splitlines():
                    match=re.match(r'^\s*([^#!\s=:]+)\s*[=:]\s*(.*?)\s*$',line)
                    if match:add(match[1],match[2])
        file=settings.get('oufauthorizationbundlefile',[])
        flag('UDP_POLICY_REGISTRY_CONFIG_PRESENT',bool(settings.get('oufauthorizationregistryurl')))
        print('UDP_POLICY_FILE_BINDING_COUNT='+str(len(file)))
        if len(file)==1:policy_facts(json.loads(mapped_file(udp,file[0]).read_text()),claims,'UDP_MOUNTED_POLICY')
        print('UDP_LOADED_IN_MEMORY_POLICY_NOT_PROVEN=true')
    section('UDP_POLICY_BINDINGS',owner_policy)
    def route_inventory():
        key=routes.admin_key(routes.mounted_config(apisix).read_text())
        config='silent\nshow-error\nfail\nmax-time = 10\nmax-filesize = 10485760\nheader = "X-API-KEY: '+key+'"\nurl = "http://127.0.0.1:9180/apisix/admin/routes"\n'
        raw=helper.run(['docker','run','--rm','-i','--network','container:ouf-apisix','curlimages/curl:8.16.0','--config','-'],input=config,timeout=20)
        values=routes.route_values(json.loads(raw))
        for path,label in list(PATHS.items())[:2]:
            found=[x for x in values if x.get('uri')==path and ('methods' not in x or 'POST' in x['methods'])]
            print('ROUTE_'+label+'_COUNT='+str(len(found)))
            for x in found:
                plugins=x.get('plugins',{});oidc=plugins.get('openid-connect',{})
                flag('ROUTE_'+label+'_ENABLED',x.get('status',1)==1)
                flag('ROUTE_'+label+'_UDP_INLINE',x.get('upstream',{}).get('nodes')=={'ouf-udp:8080':1})
                flag('ROUTE_'+label+'_TOKEN_SCOPES_MATCH',set(oidc.get('required_scopes',[]))<=set(str(claims.get('scope','')).split()))
                print('ROUTE_'+label+'_PLUGIN_NAMES='+','.join(sorted(k for k in plugins if re.fullmatch(r'[a-z0-9-]+',k))))
    section('ROUTES',route_inventory)
    print('R4A_EXECUTION_FAILURE_BUNDLE=COMPLETE READ_ONLY=true INTAKE_POST=false RETRY=false RUN_RESUME=false OWNER_AUTHORIZATION_NOT_PROVEN=true PAYLOADS_NOT_PRINTED=true SECRETS_NOT_PRINTED=true')


def time_now():return datetime.now(timezone.utc).timestamp()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',required=True)
    try:main(p.parse_args())
    except Exception as error:
        print('R4A_EXECUTION_FAILURE_BUNDLE=BLOCKED TYPE='+type(error).__name__+' RETRY=false RUN_RESUME=false SECRETS_NOT_PRINTED=true');raise SystemExit(1)
