#!/usr/bin/env python3
"""Compose proven IAM reconcilers: scope definitions and additive SERVICE binding.

Never creates a client, edits mappers/flags, retrieves a secret or publishes policy.
Plan and verify are read-only; apply requires an already correct workload profile.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def load(name):
    path=Path(__file__).resolve().parent/(name+'.py')
    spec=importlib.util.spec_from_file_location(name.replace('-','_'),path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def modules(args):
    def run(*values,input_text=None):
        result=subprocess.run(['docker','exec','-i',args.iam_container,args.kcadm_path,*values],input=input_text,
            capture_output=True,text=True,timeout=20)
        if result.returncode:
            text=(result.stdout+result.stderr).lower()
            raise RuntimeError('KCADM_SESSION_EXPIRED' if 'session has expired' in text or 'invalid_grant' in text else 'KCADM_COMMAND_FAILED')
        return result.stdout
    catalog=load('reconcile-keycloak-client-scope-definition')
    workload=load('provision-keycloak-workload')
    binding=load('reconcile-keycloak-client-scope')
    for module in (catalog,workload,binding):module.run=run
    # Resolve only the selected client; do not depend on realm-wide pagination.
    def exact(realm,client):
        rows=workload.get_json('get','clients','-r',realm,'-q','clientId='+client,'--fields','id,clientId')
        matches=[r for r in rows if r.get('clientId')==client]
        if len(matches)>1:raise RuntimeError('CLIENT_NOT_UNIQUE')
        return matches[0] if matches else None
    workload.exact_client=exact
    return catalog,workload,binding


def prepare(args,catalog,workload,binding):
    names=(args.provider_scope,args.discovery_scope)
    if names[0]==names[1]:raise RuntimeError('DISTINCT_SCOPES_REQUIRED')
    state=workload.inspect_state(args.realm,args.client_id,args.provider_scope,args.audience,args.tenant)
    ignored={'REQUIRED_SCOPE_NOT_DEFAULT','BASE_DEFAULT_SCOPES_MISSING','BASE_OPTIONAL_SCOPES_MISSING'}
    profile_drift=[d for d in state['drift'] if d not in ignored]
    scopes={name:catalog.inspect(args.realm,name) for name in names}
    before={'mode':args.mode,'clientId':args.client_id,'profileDrift':profile_drift,
        'scopes':[{'name':name,'exists':scopes[name]['exists'],'drift':scopes[name]['drift']} for name in names],
        'scopeDefinitionActions':{name:('REVIEW_EXISTING_DRIFT' if scopes[name]['exists'] and scopes[name]['drift'] else 'KEEP' if scopes[name]['exists'] else 'CREATE') for name in names},
        'providerScopeDefault':'REQUIRED_SCOPE_NOT_DEFAULT' not in state['drift'] and state['exists'],
        'discoveryScopeClientBindingRequested':False,'mapperChangesRequested':False,'secretReadRequested':False}
    print('SEMANTIC_PROVIDER_IAM_PLAN='+json.dumps(before,sort_keys=True),flush=True)
    if args.mode=='plan':
        print('SEMANTIC_PROVIDER_IAM_PLAN=PASS READ_ONLY=true EXISTING_PROFILE_READY='+str(not profile_drift).lower()+' NO_SECRETS_PRINTED=true',flush=True)
        return before
    if profile_drift:raise RuntimeError('EXISTING_WORKLOAD_PROFILE_REQUIRES_REVIEW')
    if any(s['exists'] and s['drift'] for s in scopes.values()):raise RuntimeError('EXISTING_SCOPE_DRIFT_REQUIRES_REVIEW')
    if args.mode=='apply':
        for name in names:
            if not scopes[name]['exists']:catalog.create(args.realm,name)
        # Preserve every existing client flag, mapper, credential and other scope.
        sid=catalog.inspect(args.realm,args.provider_scope)['id']
        if not sid:raise RuntimeError('PROVIDER_SCOPE_NOT_CREATED')
        if 'REQUIRED_SCOPE_NOT_DEFAULT' in state['drift']:
            binding.assign(args.realm,state['internalId'],sid,'default')
    after=workload.inspect_state(args.realm,args.client_id,args.provider_scope,args.audience,args.tenant)
    if any(d not in {'BASE_DEFAULT_SCOPES_MISSING','BASE_OPTIONAL_SCOPES_MISSING'} for d in after['drift']):raise RuntimeError('WORKLOAD_VERIFY_FAILED')
    if any(catalog.inspect(args.realm,name)['drift'] for name in names):raise RuntimeError('SCOPE_VERIFY_FAILED')
    print('SEMANTIC_PROVIDER_IAM_PREPARE=PASS MODE='+args.mode+' POLICY_UNCHANGED=true MAPPERS_UNCHANGED=true CREDENTIALS_UNCHANGED=true TOKEN_CLAIMS_NOT_PROVEN=true NO_SECRETS_PRINTED=true',flush=True)
    return before


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('plan','apply','verify'))
    for option in ('iam-container','kcadm-path','realm','client-id','audience','tenant','provider-scope','discovery-scope'):
        p.add_argument('--'+option,required=True)
    args=p.parse_args()
    try:
        if os.geteuid()!=0:raise RuntimeError('ROOT_REQUIRED')
        for key in ('iam_container','realm','client_id','audience','tenant','provider_scope','discovery_scope'):
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}',getattr(args,key)):raise RuntimeError('INSTALLATION_BINDING_INVALID')
        if not args.kcadm_path.startswith('/') or '..' in Path(args.kcadm_path).parts:raise RuntimeError('KCADM_PATH_INVALID')
        prepare(args,*modules(args))
    except Exception as error:
        # Imported helpers may contain details; emit only known fixed outer codes.
        code=str(error) if type(error) is RuntimeError and re.fullmatch(r'[A-Z_]{1,80}',str(error)) else type(error).__name__
        print('SEMANTIC_PROVIDER_IAM_PREPARE=BLOCKED CODE='+code+' NO_SECRETS_PRINTED=true',flush=True)
        sys.exit(1)
