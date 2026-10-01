#!/usr/bin/env python3
"""Fresh HUMAN scope login and real UDP recovery GETs; no business POST."""
import argparse
import json
import os
from pathlib import Path
import re
import uuid
import r4a_prepare_scoped_human_policy as api

def bindings(values):
    result={}
    for value in values:
        job,handoff=value.split(':',1)
        job=str(uuid.UUID(job));handoff=str(uuid.UUID(handoff))
        api.require(job not in result,'DUPLICATE_JOB_BINDING');result[job]=handoff
    return result

def http_deny(url,token,codes):
    try:api.http(url,token)
    except api.Blocked as error:
        api.require(str(error) in {'HTTP_'+str(c) for c in codes},'NEGATIVE_GET_UNEXPECTED_HTTP')
        return int(str(error)[5:])
    raise api.Blocked('NEGATIVE_GET_NOT_DENIED')

def check_review(value,resource,handoff,args):
    fields={'jobId','handoffId','ingestionRunId','sourceId','state','stateVersion','intakeState','safeFailureCode',
        'retryEligible','contractReady','contractCheck','verifiedBaselineHash','snapshotHash','attempts','integrityAttempts'}
    api.require(isinstance(value,dict) and set(value)<=fields
        and fields-{'verifiedBaselineHash'}<=set(value),'UDP_REVIEW_SHAPE_UNSUPPORTED')
    api.require(value['jobId']==resource['resourceId'] and value['handoffId']==handoff
        and value['sourceId']==resource['resourceAttributes']['sourceRef']
        and value['ingestionRunId']==resource['resourceAttributes']['jobRef'],'UDP_REVIEW_BINDING_MISMATCH')
    api.require(value['state']=='QUARANTINED' and value['intakeState']=='DURABLE'
        and type(value['stateVersion']) is int and value['stateVersion']==args.expected_version
        and value['safeFailureCode']==args.expected_failure
        and type(value['retryEligible']) is bool and type(value['contractReady']) is bool
        and value['contractCheck'] in ('READY','MISSING','CONTRACT_INVALID','CATALOG_UNAVAILABLE','NOT_ELIGIBLE')
        and isinstance(value['snapshotHash'],str)
        and re.fullmatch('sha256:[a-f0-9]{64}',value['snapshotHash']),'UDP_REVIEW_STATE_OR_SNAPSHOT_MISMATCH')
    ready=value['retryEligible'] and value['contractReady'] and value['contractCheck']=='READY'
    if ready:api.require(isinstance(value.get('verifiedBaselineHash'),str)
        and re.fullmatch('sha256:[a-f0-9]{64}',value['verifiedBaselineHash']),'UDP_BASELINE_HASH_INVALID')
    return bool(ready)

def execute(args):
    args._receipt_owned=False;args._phase='INPUT_VALIDATION'
    api.require(os.geteuid()==0,'ROOT_REQUIRED');os.umask(0o077)
    api.https(args.base_url);api.https(args.issuer)
    api.private(args.publication_receipt);api.private(args.resources);api.private(args.receipt.parent,True)
    publication=json.loads(args.publication_receipt.read_text());resources=json.loads(args.resources.read_text())
    expected=bindings(args.binding)
    api.require(publication.get('status')=='PASS_PUBLISHED'
        and publication.get('activeReadback',{}).get('policyRef')==args.expected_policy
        and publication.get('resourcesHash')==api.digest(resources),'PUBLICATION_RECEIPT_NOT_EXACT')
    api.require(isinstance(resources,list) and len(resources)==args.expected_resources
        and {r['resourceId'] for r in resources}==set(expected)
        and all(r['capabilityId']==args.scope and r['resourceType']=='materialization-job'
                and r['resourceAttributes'].get('module')=='UDP' for r in resources),'RESOURCE_SET_MISMATCH')
    policy=publication['activeReadback']['policy']
    descriptors=[c for c in policy['capabilities'] if c['capabilityId']==args.scope]
    api.require(descriptors==[{'capabilityId':args.scope,'operation':'COMMAND','requiredScope':args.scope,
        'allowedActors':['HUMAN']}],'ACTIVE_RECEIPT_DESCRIPTOR_MISMATCH')
    grants=[g for g in policy['grants'] if g['capabilityId']==args.scope]
    api.require(len(grants)==len(resources) and all(g['tenantId']==args.tenant and g['subjectId']==args.subject
        and g['servicePrincipalId'] is None and g['constraints']['resourceId'] in expected for g in grants),
        'ACTIVE_RECEIPT_GRANT_MISMATCH')
    outside=str(uuid.UUID(args.outside_job));api.require(outside not in expected,'OUTSIDE_JOB_IN_SCOPE')
    api.reserve(args.receipt)
    args._receipt_owned=True
    evidence={'status':'LOGIN_PENDING_NO_BUSINESS_POST','publicationReceiptHash':api.digest(publication),
        'resourcesHash':api.digest(resources),'reviews':[]};api.write(args.receipt,evidence)
    def phase(name):
        args._phase=name;evidence['phase']=name
        api.write(args.receipt,evidence)
    # Reuse defensive Device Grant checks; request the dedicated optional scope.
    phase('LOGIN')
    args.admin_scope=args.scope;token=api.login(args);base=args.base_url.rstrip('/')
    phase('ANONYMOUS_GET')
    evidence['anonymousHttp']=http_deny(base+'/'+next(iter(expected)),None,(401,403))
    phase('OUTSIDE_SCOPE_GET')
    evidence['outsideScopeHttp']=http_deny(base+'/'+outside,token,(403,))
    api.write(args.receipt,evidence)
    for index,resource in enumerate(resources,1):
        phase('OWNER_REVIEW_GET_'+str(index))
        status,value,_=api.http(base+'/'+resource['resourceId'],token)
        evidence.setdefault('ownerHttp',[]).append(status)
        # Structural diagnostics only; never retain an unexpected payload response.
        evidence['lastResponseShape']={'type':type(value).__name__}
        if isinstance(value,dict):
            evidence['lastResponseShape'].update(fieldCount=len(value),fields={
                k:type(v).__name__ for k,v in list(value.items())[:64]
                if isinstance(k,str) and re.fullmatch('[A-Za-z0-9_]{1,64}',k)})
        phase('OWNER_REVIEW_VALIDATE_'+str(index))
        print('UDP_HUMAN_REVIEW_'+str(index)+'_HTTP='+str(status)+' CONTENT_VALIDATION_PENDING=true',flush=True)
        api.require(status==200,'UDP_HUMAN_REVIEW_NOT_200')
        ready=check_review(value,resource,expected[resource['resourceId']],args)
        evidence['reviews'].append({'review':value,'ready':ready});api.write(args.receipt,evidence)
        print('UDP_HUMAN_REVIEW_'+str(index)+'=PASS HTTP=200 JOB_BINDING_MATCH=true STATE=QUARANTINED INTAKE=DURABLE'
            +' VERSION='+str(value['stateVersion'])+' RETRY_ELIGIBLE='+str(value['retryEligible']).lower()
            +' CONTRACT_READY='+str(value['contractReady']).lower()+' CONTRACT_CHECK='+value['contractCheck'],flush=True)
    ready=all(r['ready'] for r in evidence['reviews'])
    evidence['status']='PASS_READY' if ready else 'AUTHORIZATION_PASS_REFERENCE_GATE_BLOCKED';api.write(args.receipt,evidence)
    print('R4A_UDP_HUMAN_REVIEW_RECEIPT='+str(args.receipt)+' PRIVATE=true')
    print('R4A_UDP_HUMAN_REVIEW='+('PASS' if ready else 'BLOCKED')
        +' HUMAN_OWNER_AUTHORIZATION_PROVEN=true ANONYMOUS_DENIED=true OUTSIDE_JOB_DENIED=true'
        +' SPRING_REVIEW_REFERENCE_GATE='+('PASS' if ready else 'BLOCKED')
        +' OWNER_GET_ONLY=true RETRY=false REPLAY=false INTAKE_POST=false MATERIALIZATION_NOT_TRIGGERED=true'
        +' HISTORICAL_CAUSALITY_NOT_PROVEN=true SECRETS_NOT_PRINTED=true')
    if not ready:raise SystemExit(2)

def save_failure(args,error):
    # Never modify a receipt this invocation did not exclusively reserve.
    code=str(error) if isinstance(error,api.Blocked) else 'UNCLASSIFIED'
    if not getattr(args,'_receipt_owned',False):return code,False
    try:
        api.private(args.receipt);evidence=json.loads(args.receipt.read_text())
        evidence.update(status='BLOCKED',phase=args._phase,
                        safeFailureCode=code,failureType=type(error).__name__)
        api.write(args.receipt,evidence);return code,True
    except Exception:return code,False

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('issuer','client','audience','base-url','tenant','subject','scope','expected-policy','expected-failure','outside-job'):
        p.add_argument('--'+name,required=True)
    for name in ('publication-receipt','resources','receipt'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--binding',action='append',required=True)
    p.add_argument('--expected-version',type=int,required=True);p.add_argument('--expected-resources',type=int,required=True)
    args=p.parse_args()
    try:execute(args)
    except Exception as error:
        code,saved=save_failure(args,error)
        print('R4A_UDP_HUMAN_REVIEW=BLOCKED CODE='+code+' TYPE='+type(error).__name__
            +' PHASE='+args._phase+' ERROR_SAVED='+str(saved).lower()
            +' OWNER_GET_ONLY=true RETRY=false SECRETS_NOT_PRINTED=true',flush=True)
        raise SystemExit(1)
