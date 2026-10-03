#!/usr/bin/env python3
"""Read Ingestion IAM binding sources before release adoption; no runtime mutation."""
import argparse
import json
import os
from pathlib import Path
import re
import r4a_prepare_frozen_compatibility_probe as helper


def flag(name,value):print(name+'='+str(bool(value)).lower())


def external_config_status(env):
    """Recognize one explicit properties file; refuse additional config sources."""
    selectors={k:v for k,v in env.items() if v and re.sub(r'[^a-z0-9]','',k.lower()) in
        {'springconfiglocation','springconfigadditionallocation','springconfigimport'}}
    accepted={'file:'+helper.PROPERTIES,'optional:file:'+helper.PROPERTIES}
    supported=(len(selectors)==1 and next(iter(selectors)) in
        {'SPRING_CONFIG_LOCATION','SPRING_CONFIG_ADDITIONAL_LOCATION'} and
        next(iter(selectors.values())) in accepted)
    return selectors,supported


def main(args):
    if os.geteuid()!=0:raise RuntimeError('ROOT_REQUIRED')
    live=helper.inspect('ouf-ingestion')
    image=helper.inspect(live['Image'],'image')
    revision=image['Config'].get('Labels',{}).get('org.opencontainers.image.revision')
    print('R4A_INGESTION_IAM_INVENTORY=READ_ONLY',flush=True)
    flag('ING_IAM_LIVE_RUNNING',live['State']['Running'])
    flag('ING_IAM_EXPECTED_LIVE_REVISION_MATCH',revision==args.expected_live_revision)
    env=dict(v.split('=',1) for v in live['Config'].get('Env',[]) if '=' in v)
    for key,wanted in [('ENABLED','true'),('ISSUER',args.issuer),('AUDIENCE',args.audience)]:
        value=env.get('OUF_ING_IAM_'+key)
        flag('ING_IAM_'+key+'_ENV_PRESENT',value is not None)
        flag('ING_IAM_'+key+'_ENV_MATCH',value==wanted)
    flag('ING_IAM_SPRING_JSON_PRESENT',bool(env.get('SPRING_APPLICATION_JSON')))
    flag('ING_IAM_EXTERNAL_CONFIG_ENV_PRESENT',any(env.get(k) for k in ('SPRING_CONFIG_LOCATION','SPRING_CONFIG_ADDITIONAL_LOCATION','SPRING_CONFIG_IMPORT')))
    selectors,supported=external_config_status(env)
    print('ING_IAM_EXTERNAL_CONFIG_SELECTOR_COUNT='+str(len(selectors)))
    flag('ING_IAM_EXTERNAL_CONFIG_SINGLE_PROPERTIES_FILE',supported)
    flag('ING_IAM_EXTERNAL_CONFIG_LOCATION_SELECTOR', 'SPRING_CONFIG_LOCATION' in selectors)
    flag('ING_IAM_EXTERNAL_CONFIG_ADDITIONAL_LOCATION_SELECTOR', 'SPRING_CONFIG_ADDITIONAL_LOCATION' in selectors)
    flag('ING_IAM_EXTERNAL_CONFIG_IMPORT_SELECTOR',any(re.sub(r'[^a-z0-9]','',k.lower())=='springconfigimport' for k in selectors))
    flag('ING_IAM_DIRECT_PROPERTY_ENV_PRESENT',any(re.sub(r'[^a-z0-9]','',k.lower()).startswith('oufingestioniam') for k in env))
    command=[str(x) for x in [*(live['Config'].get('Cmd') or []),*(live['Config'].get('Entrypoint') or [])]]
    flag('ING_IAM_COMMAND_OVERRIDE_PRESENT',any(re.search(r'ouf[._-]ingestion[._-]iam|spring[._-]config|SPRING_APPLICATION_JSON',x,re.I) for x in command))
    mounts=[m for m in live.get('Mounts',[]) if m.get('Destination')==helper.PROPERTIES]
    if len(mounts)!=1:raise RuntimeError('ING_IAM_PROPERTIES_MOUNT_NOT_UNIQUE')
    props=Path(mounts[0]['Source']).read_text()
    for key,wanted in [('enabled','true'),('issuer',args.issuer),('audience',args.audience)]:
        entries=re.findall(r'^\s*ouf\.ingestion\.iam\.'+key+r'\s*[=:]\s*(.*?)\s*$',props,re.M)
        print('ING_IAM_'+key.upper()+'_PROPERTY_COUNT='+str(len(entries)))
        flag('ING_IAM_'+key.upper()+'_PROPERTY_MATCH',entries==[wanted])
    flag('ING_IAM_CONFIG_IMPORT_PRESENT',bool(re.search(r'^\s*spring\.config\.(?:import|location|additional-location)\s*[=:]',props,re.M)))
    for name in ('activation','execution'):
        entries=re.findall(r'^\s*ouf\.ingestion\.'+name+r'\.enabled\s*[=:]\s*(.*?)\s*$',props,re.M)
        flag('ING_IAM_'+name.upper()+'_PROPERTY_TRUE',entries==['true'])
    after=helper.inspect('ouf-ingestion')
    if any(after[k]!=live[k] for k in ('Id','Image','Config','HostConfig','Mounts')):raise RuntimeError('ING_IAM_RUNTIME_CHANGED_DURING_READ')
    print('R4A_INGESTION_IAM_INVENTORY=COMPLETE READ_ONLY=true LIVE_UNCHANGED=true IAM_UNCHANGED=true WORKLOAD_TOKEN_UNCHANGED=true RETRY=false RUN_RESUME=false BINDINGS_ARE_DIAGNOSTIC=true LIVE_PRINCIPAL_BEAN_NOT_INSPECTED=true OWNER_AUTHORIZATION_NOT_PROVEN=true SECRETS_NOT_PRINTED=true')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--issuer',required=True)
    p.add_argument('--audience',required=True)
    p.add_argument('--expected-live-revision',required=True)
    try:main(p.parse_args())
    except Exception as error:
        code=str(error) if isinstance(error,RuntimeError) else type(error).__name__
        print('R4A_INGESTION_IAM_INVENTORY=BLOCKED CODE='+code+' READ_ONLY=true RETRY=false RUN_RESUME=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
