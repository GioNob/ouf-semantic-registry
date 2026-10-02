#!/usr/bin/env python3
"""Read-only Docker topology inventory; never prints secrets, addresses or host paths."""
import json
import os
import subprocess
import sys


def docker(*args):
    return subprocess.run(['docker',*args],check=True,capture_output=True,text=True,timeout=20).stdout


def summary(row):
    config=row.get('Config',{})
    return {'name':row['Name'].lstrip('/'),'imageId':row['Image'],
        'revision':(config.get('Labels') or {}).get('org.opencontainers.image.revision'),
        'running':row['State']['Running'],'user':config.get('User',''),
        'environmentNames':sorted(x.split('=',1)[0] for x in config.get('Env') or []),
        'portBindingCount':sum(len(v or []) for v in row.get('HostConfig',{}).get('PortBindings',{}).values()),
        'networks':sorted(row.get('NetworkSettings',{}).get('Networks',{})),
        'mounts':[{'target':m['Destination'],'readOnly':not m['RW'],'type':m['Type']} for m in row.get('Mounts',[])],
        'readOnlyRoot':row.get('HostConfig',{}).get('ReadonlyRootfs',False),
        'privileged':row.get('HostConfig',{}).get('Privileged',False)}


def inventory(run=docker):
    ids=run('ps','-q').split()
    if not ids:raise RuntimeError('NO_RUNNING_CONTAINERS')
    rows=json.loads(run('inspect',*ids))
    required={'ouf-semantic','ouf-apisix','ouf-caddy','ouf-etcd'}
    relevant=[r for r in rows if r['Name'].lstrip('/') in required
        or 'apisix' in r.get('Config',{}).get('Image','').lower()
        or 'apisix' in r['Name'].lower()]
    if not required.issubset({r['Name'].lstrip('/') for r in relevant}):raise RuntimeError('REQUIRED_CONTAINER_MISSING')
    network_names=sorted({name for r in relevant for name in r.get('NetworkSettings',{}).get('Networks',{})})
    networks=json.loads(run('network','inspect',*network_names)) if network_names else []
    fresh=json.loads(run('inspect',*(r['Id'] for r in relevant)))
    def stable(r):return r['Id'],r['Image'],r['State']['Running'],r['State']['StartedAt'],r.get('Config'),r.get('HostConfig'),r.get('Mounts'),r.get('NetworkSettings')
    if sorted(map(stable,relevant),key=lambda x:x[0])!=sorted(map(stable,fresh),key=lambda x:x[0]):raise RuntimeError('TOPOLOGY_CHANGED_DURING_INVENTORY')
    southbound=any('southbound' in r['Name'].lower() or (r.get('Config',{}).get('Labels') or {}).get('ouf.component')=='apisix-southbound' for r in relevant)
    return {'containers':[summary(r) for r in sorted(relevant,key=lambda r:r['Name'])],
        'networks':[{'name':n['Name'],'driver':n['Driver'],'internal':n.get('Internal',False),'ipv6Enabled':n.get('EnableIPv6',False)} for n in networks],
        'dedicatedSouthboundContainerObserved':southbound,
        'tlsConfigurationProven':False,'egressDefaultDenyProven':False,'workloadAuthenticationProven':False,
        'providerCalls':0,'readOnly':True,'noSecretsPrinted':True}


if __name__=='__main__':
    try:
        if os.geteuid()!=0:raise RuntimeError('ROOT_REQUIRED')
        print('SEMANTIC_SOUTHBOUND_TOPOLOGY='+json.dumps(inventory(),sort_keys=True),flush=True)
        print('SEMANTIC_SOUTHBOUND_TOPOLOGY_INVENTORY=PASS NO_CONTAINER_CHANGED=true NO_ROUTE_CHANGED=true NO_PROVIDER_CALL=true NO_SECRETS_PRINTED=true',flush=True)
    except Exception as error:
        code=str(error) if isinstance(error,RuntimeError) else type(error).__name__
        print('SEMANTIC_SOUTHBOUND_TOPOLOGY_INVENTORY=BLOCKED CODE='+code+' NO_SECRETS_PRINTED=true',flush=True)
        sys.exit(1)
