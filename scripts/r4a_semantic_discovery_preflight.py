#!/usr/bin/env python3
"""Read-only discovery configuration, routes, authorization descriptors and queue counts.

Never calls an external provider, creates a discovery job, or prints endpoint,
credential, environment value, host mount source, intent or candidate payload.
"""
import argparse
import json
import os
from pathlib import Path
import re
import sys
from types import SimpleNamespace
from urllib.parse import urlsplit
import r4a_release_semantic_consultation as release
stage=release.stage
prep=release.prep
require=release.require
SEMANTIC_PIN='e7bc5190f9e6afbbc4cf3c90d5d4970afbfad14b'
MCP_PIN='394b4b1540b575564f0ba58541df9d7efc59fb87'


def flag(values,key,alias,default):
    raw=values.get(key,values.get(alias,str(default))).strip().lower()
    return {'true':True,'false':False}.get(raw,'UNPROVEN')


def settings(row):
    values=prep.env(row)
    provider=flag(values,'OUF_SEMANTIC_PROVIDERS_SCHEMA_GOV_ENABLED','OUF_SCHEMA_GOV_ENABLED',False)
    worker=flag(values,'OUF_SEMANTIC_DISCOVERY_WORKER_ENABLED','OUF_DISCOVERY_WORKER_ENABLED',True)
    override_names=[k for k in values if k=='SPRING_APPLICATION_JSON' or k.startswith('SPRING_CONFIG')
        or k in ('SPRING_PROFILES_ACTIVE','SPRING_PROFILES_INCLUDE','JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','JAVA_OPTS','_JAVA_OPTIONS')]
    commands=(row['Config'].get('Entrypoint') or [])+(row['Config'].get('Cmd') or [])
    command_override=any(re.search(r'(^--(?:spring|ouf)\.|^-D(?:spring|ouf)\.)',x) for x in commands)
    mount_override=any(m['Destination'] not in ('/run/ouf-semantic-auth','/run/secrets/semantic-read-owner.key') for m in row.get('Mounts',[]))
    proven=not override_names and not command_override and not mount_override and provider!='UNPROVEN' and worker!='UNPROVEN'
    base=values.get('OUF_SEMANTIC_PROVIDERS_SCHEMA_GOV_GATEWAY_BASE_URL',values.get('OUF_SCHEMA_GOV_GATEWAY_BASE_URL','https://gateway.invalid'))
    try:
        parsed=urlsplit(base)
        port=parsed.port
        transport=parsed.scheme=='https' or (parsed.scheme=='http' and parsed.hostname in ('127.0.0.1','localhost','::1'))
        origin_safe=transport and bool(parsed.hostname) and port!=0 and not parsed.username and not parsed.password and not parsed.query and not parsed.fragment
        origin_configured=origin_safe and parsed.hostname!='gateway.invalid'
    except ValueError:origin_safe=False;origin_configured=False
    paths={name:values.get('OUF_SEMANTIC_PROVIDERS_SCHEMA_GOV_'+name.upper()+'_PATH',
        values.get('OUF_SCHEMA_GOV_'+name.upper()+'_PATH','/semantic-providers/schema-gov/'+suffix))
        for name,suffix in [('search','sparql'),('fetch','fetch')]}
    path_safe=all(isinstance(p,str) and p.startswith('/') and not p.startswith('//')
        and not any(c in p for c in ('?','#','\n','\r')) for p in paths.values())
    return {'providerEnabled':provider if proven else 'UNPROVEN','workerEnabled':worker if proven else 'UNPROVEN',
        'configurationProven':proven,'overrideEnvironmentNames':sorted(override_names),
        'commandOverridePresent':command_override,'unexpectedMountOverridePresent':mount_override,
        'gatewayOriginConfigured':origin_configured,'gatewayOriginSafe':origin_safe,'pathsSafe':path_safe},paths


def route_summary(routes,paths):
    def matches(uri,path):
        return isinstance(uri,str) and (uri==path or uri.endswith('*') and path.startswith(uri[:-1]))
    result={}
    for name,path in paths.items():
        method='POST' if name=='search' else 'GET'
        chosen=[r for r in routes if r.get('status',1)==1 and (not r.get('methods') or method in r['methods'])
            and any(matches(u,path) for u in [r.get('uri')]+r.get('uris',[]))]
        result[name]={'activeRouteCount':len(chosen),'oidcEnforcedRouteCount':sum('openid-connect' in r.get('plugins',{}) for r in chosen),
            'upstreamBindingPresent':any(r.get('upstream') or r.get('upstream_id') or r.get('service_id') for r in chosen)}
    for name,path in [('request','/api/semantic/v1/discovery-requests'),('providers','/api/semantic/v1/discovery-requests/providers')]:
        result[name]={'activeRouteCount':sum(r.get('status',1)==1 and any(matches(u,path) for u in [r.get('uri')]+r.get('uris',[])) for r in routes)}
    return result


POLICY_SQL="""
begin read only;
select jsonb_build_object('policyRef',a.bundle_id||':'||a.version,
 'registeredDescriptors',(select coalesce(jsonb_agg(jsonb_build_object('capabilityId',r.capability_id,
  'operation',r.descriptor->>'operation','requiredScope',r.descriptor->>'requiredScope',
  'allowedActors',r.descriptor->'allowedActors')),'[]'::jsonb) from ouf_authorization.capability_registration r
  where r.capability_id='ouf.semantic.discovery'),
 'publishedDescriptors',(select coalesce(jsonb_agg(jsonb_build_object('capabilityId',c->>'capabilityId',
  'operation',c->>'operation','requiredScope',c->>'requiredScope','allowedActors',c->'allowedActors')),'[]'::jsonb)
  from jsonb_array_elements(p.bundle_payload->'capabilities') c where c->>'capabilityId'='ouf.semantic.discovery'))
 from ouf_authorization.active_policy_bundle a join ouf_authorization.policy_bundle p
 on p.bundle_id=a.bundle_id and p.version=a.version where a.singleton_key=true;
commit;
"""
QUEUE_SQL="""
begin read only;
select jsonb_build_object('requestsByState',(select coalesce(jsonb_object_agg(state,n),'{}'::jsonb)
 from (select state,count(*) n from ouf_sem.discovery_request group by state) x),
 'unexpiredCandidateCount',(select count(*) from ouf_sem.discovery_candidate where expires_at>transaction_timestamp()),
 'adoptedCandidateCount',(select count(*) from ouf_sem.discovery_candidate where adopted_at is not null));
commit;
"""


def query(pg,user,database,sql):
    return json.loads(stage.run(['docker','exec',pg,'psql','-X','-qAt','-v','ON_ERROR_STOP=1',
        '-U',user,'-d',database,'-c',sql],timeout=20))


def main(args):
    require(os.geteuid()==0,'ROOT_REQUIRED')
    prep.private(args.stage_root,0o700);prep.private(args.stage_root/'runtime-snapshot.json',0o600)
    previous=json.loads((args.stage_root/'runtime-snapshot.json').read_text())
    gateway=previous['gatewayConfig']
    current={name:stage.inspect(name) for name in ('ouf-semantic','ouf-mcp','ouf-apisix','ouf-onboarding')}
    stage.guard(current['ouf-semantic'],SEMANTIC_PIN);stage.guard(current['ouf-mcp'],MCP_PIN)
    require(all(r['State']['Running'] for r in current.values()),'OWNER_NOT_RUNNING')
    config,paths=settings(current['ouf-semantic']);routes=stage.routes(gateway,current['ouf-apisix'])
    pg,user,databases=release.databases(SimpleNamespace(postgres_container=args.postgres_container),
        {'semantic':current['ouf-semantic'],'mcp':current['ouf-mcp']})
    allowed={args.postgres_container,pg['Name'].lstrip('/')}
    for n in pg['NetworkSettings']['Networks'].values():allowed.update(n.get('Aliases') or [])
    parsed=urlsplit(prep.env(current['ouf-onboarding'])['OUF_ONB_DB_URL'].removeprefix('jdbc:'))
    require(parsed.scheme=='postgresql' and parsed.hostname in allowed and parsed.port in (None,5432)
        and bool(re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,62}',parsed.path.lstrip('/'))),'AUTHORIZATION_DATABASE_BINDING_INVALID')
    policy=query(args.postgres_container,user,parsed.path.lstrip('/'),POLICY_SQL)
    queue=query(args.postgres_container,user,databases['semantic'],QUEUE_SQL)
    for name,row in current.items():require(stage.fingerprint(stage.inspect(name))==stage.fingerprint(row),'LIVE_CHANGED_DURING_INVENTORY')
    require(stage.routes(gateway,stage.inspect('ouf-apisix'))==routes,'ROUTES_CHANGED_DURING_INVENTORY')
    blockers=[]
    if config['providerEnabled'] is not True:blockers.append('PROVIDER_DISABLED_OR_UNPROVEN')
    if config['workerEnabled'] is not True:blockers.append('WORKER_DISABLED_OR_UNPROVEN')
    if not config['gatewayOriginConfigured']:blockers.append('GATEWAY_ORIGIN_MISSING_OR_UNSAFE')
    if not config['pathsSafe']:blockers.append('PROVIDER_PATHS_UNSAFE')
    route_info=route_summary(routes,paths)
    if any(route_info[n]['activeRouteCount']!=1 for n in ('search','fetch')):blockers.append('SOUTHBOUND_BINDING_MISSING_OR_AMBIGUOUS')
    print('SEMANTIC_DISCOVERY_PREFLIGHT='+json.dumps({'configuration':config,'routes':route_info,'authorization':policy,
        'queue':queue,'configurationBlockers':blockers,'configurationReady':not blockers,
        'providerConnectivityProven':False,'humanAuthorizationProven':False,'mcpDiscoveryBindingProven':False},sort_keys=True),flush=True)
    print('SEMANTIC_DISCOVERY_INVENTORY=PASS READ_ONLY=true NO_DATABASE_WRITES=true NO_POLICY_CHANGED=true NO_SOURCE_RUN=true NO_PROVIDER_CALL=true NO_SECRETS_PRINTED=true',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage-root',type=Path,required=True)
    p.add_argument('--postgres-container',required=True)
    try:main(p.parse_args())
    except BaseException as error:
        if isinstance(error,SystemExit) and error.code==0:raise
        code=str(error) if isinstance(error,RuntimeError) and re.fullmatch('[A-Z_]{1,80}',str(error)) else type(error).__name__
        print('SEMANTIC_DISCOVERY_INVENTORY=BLOCKED CODE='+code+' NO_SECRETS_PRINTED=true',flush=True)
        sys.exit(1)
