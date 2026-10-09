#!/usr/bin/env python3
"""Read-only workload client/scope inventory through an existing kcadm session.

No credentials, tokens, client secrets, mapper values or session data are printed.
All installation bindings are explicit arguments; no login or IAM mutation.
"""
import argparse
import json
import os
from pathlib import PurePosixPath
import re
import subprocess
import sys


def read(container,path,realm,resource,fields,queries=()):
    args=['docker','exec',container,path,'get',resource,'-r',realm,'--fields',fields]
    for query in queries:args.extend(['-q',query])
    result=subprocess.run(args,capture_output=True,text=True,timeout=20)
    if result.returncode:
        text=(result.stdout+result.stderr).lower()
        if 'session has expired' in text or 'not logged in' in text or 'invalid_grant' in text:
            raise RuntimeError('KCADM_SESSION_EXPIRED')
        raise RuntimeError('KCADM_READ_FAILED')
    rows=json.loads(result.stdout)
    if not isinstance(rows,list):raise RuntimeError('IAM_RESPONSE_INVALID')
    return rows


def inventory(container,path,realm,scopes,reader=read):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',container):raise RuntimeError('IAM_CONTAINER_INVALID')
    if not path.startswith('/') or '..' in PurePosixPath(path).parts or str(PurePosixPath(path))!=path:raise RuntimeError('KCADM_PATH_INVALID')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',realm):raise RuntimeError('IAM_REALM_INVALID')
    if not scopes or any(not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}',s) for s in scopes):raise RuntimeError('SCOPE_SELECTION_INVALID')
    clients=[]
    for first in range(0,1000,100):
        page=reader(container,path,realm,'clients','clientId,enabled,publicClient,serviceAccountsEnabled',(f'first={first}','max=100'))
        clients.extend(page)
        if len(page)<100:break
    else:raise RuntimeError('CLIENT_INVENTORY_LIMIT_EXCEEDED')
    existing=reader(container,path,realm,'client-scopes','name')
    names={r.get('name') for r in existing}
    workloads=[{'clientId':r['clientId'],'enabled':r.get('enabled') is True,
        'publicClient':r.get('publicClient') is True,'serviceAccountsEnabled':True}
        for r in clients if r.get('serviceAccountsEnabled') is True and isinstance(r.get('clientId'),str)]
    return {'realm':realm,'workloadClients':sorted(workloads,key=lambda r:r['clientId']),
        'scopes':[{'name':s,'exists':s in names} for s in sorted(set(scopes))],
        'clientScopeBindingsProven':False,'credentialProvisioningProven':False,
        'tokenClaimsProven':False,'readOnly':True,'noSecretsPrinted':True}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--iam-container',required=True);p.add_argument('--kcadm-path',required=True)
    p.add_argument('--realm',required=True);p.add_argument('--scope',action='append',required=True)
    args=p.parse_args()
    try:
        if os.geteuid()!=0:raise RuntimeError('ROOT_REQUIRED')
        print('SEMANTIC_PROVIDER_IAM='+json.dumps(inventory(args.iam_container,args.kcadm_path,args.realm,args.scope),sort_keys=True),flush=True)
        print('SEMANTIC_PROVIDER_IAM_INVENTORY=PASS READ_ONLY=true NO_IAM_CHANGED=true NO_POLICY_CHANGED=true NO_SECRETS_PRINTED=true',flush=True)
    except Exception as error:
        code=str(error) if isinstance(error,RuntimeError) else type(error).__name__
        print('SEMANTIC_PROVIDER_IAM_INVENTORY=BLOCKED REASON='+code+' NO_SECRETS_PRINTED=true',flush=True)
        sys.exit(1)
