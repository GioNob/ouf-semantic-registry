#!/usr/bin/env python3
"""Read sanitized ingestion OIDC route-template and router facts; no mutation."""
import os
import re
import r4a_install_runtime_publication_list_route as admin


def flag(name,value):
    print(name+'='+str(bool(value)).lower())


def safe(value):
    return str(value) if isinstance(value,(str,int)) and re.fullmatch(r'[A-Za-z0-9._:-]{1,160}',str(value)) else 'UNSUPPORTED_REDACTED'


def router_fact(text):
    # Return explicit scalar only; absence is not proof of a router default.
    values = re.findall(r'^\s*http:\s*[\"\']?(radixtree_[a-z_]+)[\"\']?\s*(?:#.*)?$', text, re.M)
    if len(values)>1:
        raise RuntimeError('RECOVERY_ROUTER_CONFIG_AMBIGUOUS')
    return values[0] if values else 'NOT_EXPLICIT_OR_UNSUPPORTED'


def report(values):
    owner = [r for r in values if r.get('upstream',{}).get('nodes')=={'ouf-ingestion:8080':1}]
    print('RECOVERY_INLINE_INGESTION_ROUTE_COUNT='+str(len(owner)))
    for index,route in enumerate(owner,1):
        prefix='RECOVERY_TEMPLATE_'+str(index)+'_'
        plugins=route.get('plugins',{})
        oidc=plugins.get('openid-connect',{})
        hosts=([route['host']] if route.get('host') else [])+(route.get('hosts') or [])
        print(prefix+'ROUTE_ID='+safe(route.get('id')))
        flag(prefix+'ENABLED',route.get('status',1)==1)
        flag(prefix+'NO_REFERENCES',not any(k in route for k in ('upstream_id','service_id','plugin_config_id')))
        flag(prefix+'NO_EXTRA_MATCH_CONDITIONS',not any(route.get(k) for k in ('vars','filter_func','remote_addr','remote_addrs')))
        flag(prefix+'OIDC_ENABLED',bool(oidc) and not oidc.get('_meta',{}).get('disable',False))
        flag(prefix+'OIDC_BEARER_ONLY',oidc.get('bearer_only') is True)
        flag(prefix+'PROXY_REWRITE_PRESENT',bool(plugins.get('proxy-rewrite')))
        flag(prefix+'PUBLIC_HOST_SUPPORTED',not hosts or hosts==['api.ouf-lab.it'])
        names=sorted(plugins)
        if any(not re.fullmatch(r'[a-z0-9_-]{1,80}',name) for name in names):
            raise RuntimeError('RECOVERY_PLUGIN_NAME_UNSUPPORTED')
        print(prefix+'PLUGIN_NAMES='+','.join(names))
        scopes=oidc.get('required_scopes') or []
        if not isinstance(scopes,list) or any(not isinstance(s,str) or safe(s)=='UNSUPPORTED_REDACTED' for s in scopes):
            raise RuntimeError('RECOVERY_TEMPLATE_SCOPE_UNSUPPORTED')
        print(prefix+'REQUIRED_SCOPES='+(','.join(scopes) or 'NONE_INLINE'))
    sample='00000000-0000-0000-0000-000000000000'
    targets=[('RUN_READ','GET','/api/trusted-human/v1/ingestion/runs/'+sample),
             ('RUN_RESUME','POST','/api/trusted-human/v1/ingestion/runs/'+sample+'/resume'),
             ('QUARANTINE_READ','GET','/api/trusted-human/v1/ingestion/quarantine/'+sample),
             ('QUARANTINE_RETRY','POST','/api/trusted-human/v1/ingestion/quarantine/'+sample+'/retry')]
    for name,method,path in targets:
        print('RECOVERY_SHARED_'+name+'_URI_CANDIDATE_COUNT='+str(len(admin.inventory.candidates(values,method,path))))


def main():
    if os.geteuid()!=0: raise RuntimeError('ROOT_REQUIRED')
    print('R4A_RECOVERY_ROUTE_TEMPLATE_INVENTORY=READ_ONLY',flush=True)
    helper=admin.inventory.routes.helper
    live=helper.inspect('ouf-ingestion')
    flag('RECOVERY_TEMPLATE_ING_RUNNING',live['State']['Running'])
    apisix=helper.inspect('ouf-apisix')
    if not apisix['State']['Running']:raise RuntimeError('APISIX_NOT_RUNNING')
    text=admin.inventory.routes.mounted_config(apisix).read_text()
    print('RECOVERY_APISIX_HTTP_ROUTER='+router_fact(text))
    raw,_=admin.api(admin.inventory.routes.admin_key(text),'GET','routes')
    report(admin.inventory.routes.route_values(raw))
    after=helper.inspect('ouf-ingestion')
    if any(after[k]!=live[k] for k in ('Id','Image','Config','HostConfig','Mounts')):
        raise RuntimeError('RECOVERY_ING_CHANGED_DURING_INVENTORY')
    print('R4A_RECOVERY_ROUTE_TEMPLATE_INVENTORY=COMPLETE READ_ONLY=true ROUTES_UNCHANGED=true IAM_UNCHANGED=true RETRY=false RUN_RESUME=false HUMAN_TOKEN_NOT_TESTED=true OWNER_AUTHORIZATION_NOT_PROVEN=true SECRETS_NOT_PRINTED=true')


if __name__=='__main__':
    try:main()
    except Exception as error:
        code=str(error) if isinstance(error,RuntimeError) else type(error).__name__
        print('R4A_RECOVERY_ROUTE_TEMPLATE_INVENTORY=BLOCKED CODE='+code+' READ_ONLY=true RETRY=false RUN_RESUME=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
