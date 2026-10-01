#!/usr/bin/env python3
"""Fresh scoped HUMAN review and one confirmed retry per original durable job.

Persist operation IDs, exact requests and intent before POST. Never repost an
existing receipt, loop retries, replay ingestion or claim materialization success.
"""
import argparse
import base64
import copy
import json
import os
from pathlib import Path
import re
import time
import uuid
import r4a_prepare_scoped_human_policy as api
import r4a_read_human_materialization_review as review


def require_token_time(token):
    api.require(isinstance(token,str) and token.count('.')==2,'TOKEN_FORMAT_INVALID')
    part=token.split('.')[1]
    claims=json.loads(base64.urlsafe_b64decode(part+'='*(-len(part)%4)))
    api.require(type(claims.get('exp')) is int and claims['exp']>time.time()+60,
                'HUMAN_TOKEN_TOO_CLOSE_TO_EXPIRY_NO_POST')


def confirm(run):
    phrase='CONFERMO RETRY ORIGINALE '+run
    print('Digitare nel terminale: '+phrase,flush=True)
    print('CONFERMA HUMAN> ',end='',flush=True)
    # Terminal is non-seekable; do not open r+ and do not consume pipeline stdin.
    with open('/dev/tty','r') as terminal:
        api.require(terminal.readline().strip()==phrase,'HUMAN_CONFIRMATION_NOT_MATCHED')


def accepted(value,row):
    api.require(isinstance(value,dict) and set(value)=={
        'operationId','jobId','handoffId','acceptedVersion','state','repeated'},'UDP_RETRY_RECEIPT_SHAPE_INVALID')
    api.require(value['operationId']==row['request']['operationId'] and value['jobId']==row['jobId']
        and value['handoffId']==row['handoffId'] and type(value['acceptedVersion']) is int
        and value['acceptedVersion']==row['request']['expectedVersion']+1
        and value['state']=='READY' and value['repeated'] is False,'UDP_RETRY_RECEIPT_MISMATCH')


def execute(args):
    args._receipt_owned=False;args._phase='INPUT_VALIDATION'
    api.require(os.geteuid()==0,'ROOT_REQUIRED');os.umask(0o077)
    api.https(args.base_url);api.https(args.issuer)
    api.require(re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,200}',args.source) is not None,
                'SOURCE_BINDING_INVALID')
    api.require(str(uuid.UUID(args.run))==args.run,'RUN_BINDING_INVALID')
    api.require(isinstance(args.reason,str) and 0<len(args.reason.strip())<=2000
        and not any(ord(c)<32 or 127<=ord(c)<=159 for c in args.reason),'REASON_INVALID')
    for path in (args.prior_review_receipt,args.resources,args.publication_receipt):api.private(path)
    resources=json.loads(args.resources.read_text());prior=json.loads(args.prior_review_receipt.read_text())
    publication=json.loads(args.publication_receipt.read_text());expected=review.bindings(args.binding)
    api.require(isinstance(resources,list) and len(resources)==args.expected_resources
        and {r['resourceId'] for r in resources}==set(expected)
        and all(r['resourceAttributes'].get('sourceRef')==args.source
                and r['resourceAttributes'].get('jobRef')==args.run for r in resources),
                'ORIGINAL_SOURCE_RUN_RESOURCE_SET_MISMATCH')
    api.require(prior.get('status')=='PASS_READY' and prior.get('resourcesHash')==api.digest(resources)
        and prior.get('publicationReceiptHash')==api.digest(publication)
        and prior.get('anonymousHttp') in (401,403) and prior.get('outsideScopeHttp')==403,
                'PRIOR_OWNER_REVIEW_NOT_EXACT_READY')
    old=prior.get('reviews',[])
    api.require(len(old)==len(resources) and {r['review']['jobId'] for r in old}==set(expected),
                'PRIOR_REVIEW_JOB_SET_MISMATCH')
    by_id={r['resourceId']:r for r in resources}
    for entry in old:
        value=entry['review']
        api.require(entry.get('ready') is True and review.check_review(
            value,by_id[value['jobId']],expected[value['jobId']],args),'PRIOR_REVIEW_NOT_READY')
    api.reserve(args.receipt);args._receipt_owned=True
    evidence={'status':'FRESH_REVIEW_PENDING_NO_POST','phase':'FRESH_REVIEW',
        'priorReviewReceiptHash':api.digest(prior),'resourcesHash':api.digest(resources),
        'runId':args.run,'sourceId':args.source,'rows':[]}
    api.write(args.receipt,evidence)
    print('R4A_UDP_HUMAN_RETRY_RECEIPT='+str(args.receipt)+' PRIVATE=true',flush=True)
    def phase(name):
        args._phase=name;evidence['phase']=name;api.write(args.receipt,evidence)
    fresh_args=copy.copy(args)
    fresh_args.receipt=args.receipt.with_name(args.receipt.stem+'-fresh-review.json')
    phase('FRESH_REVIEW')
    try:token=review.execute(fresh_args)
    except Exception as error:
        review.save_failure(fresh_args,error);raise
    except SystemExit as error:
        if error.code==2:raise api.Blocked('FRESH_REFERENCE_GATE_NOT_READY') from None
        raise
    fresh=json.loads(fresh_args.receipt.read_text())
    api.require(fresh.get('status')=='PASS_READY','FRESH_REVIEW_NOT_READY')
    evidence['freshReviewReceipt']=str(fresh_args.receipt)
    evidence['freshReviewReceiptHash']=api.digest(fresh)
    for entry in fresh['reviews']:
        value=entry['review']
        evidence['rows'].append({'jobId':value['jobId'],'handoffId':value['handoffId'],
            'status':'PREPARED_NO_POST','request':{'operationId':str(uuid.uuid4()),
                'expectedVersion':value['stateVersion'],'expectedSnapshotHash':value['snapshotHash'],
                'reason':args.reason}})
    evidence['status']='PREPARED_NO_POST';phase('HUMAN_CONFIRMATION')
    print('UDP_HUMAN_RETRY_PLAN RUN='+args.run+' SOURCE='+args.source
        +' JOBS='+str(len(evidence['rows']))+' EFFECT=ORIGINAL_JOB_REQUEUE REPLAY=false',flush=True)
    for index,row in enumerate(evidence['rows'],1):
        print('UDP_HUMAN_RETRY_TARGET_'+str(index)+' JOB='+row['jobId']+' HANDOFF='+row['handoffId']
            +' FROM=QUARANTINED VERSION='+str(row['request']['expectedVersion'])
            +' TO=READY VERSION='+str(row['request']['expectedVersion']+1),flush=True)
    confirm(args.run)
    evidence['humanConfirmed']=True;evidence['status']='CONFIRMED_NO_POST';phase('CONFIRMED')
    for index,row in enumerate(evidence['rows'],1):
        require_token_time(token)
        # Exact request and stable operation ID are durable before transmission.
        row['status']='POST_INTENT_OUTCOME_UNKNOWN';evidence['status']='POSTING'
        phase('OWNER_RETRY_POST_'+str(index))
        status,value,_=api.http(args.base_url.rstrip('/')+'/'+row['jobId']+'/retry',
                              token,method='POST',body=row['request'])
        api.require(status==200,'UDP_RETRY_NOT_200');accepted(value,row)
        row.update(status='PASS_ACCEPTED',receipt=value);phase('OWNER_RETRY_ACCEPTED_'+str(index))
        print('UDP_HUMAN_RETRY_'+str(index)+'=PASS HTTP=200 ORIGINAL_JOB_MATCH=true'
            +' ACCEPTED_VERSION='+str(value['acceptedVersion'])+' STATE=READY REPEATED=false',flush=True)
    evidence['status']='PASS_AUTHORIZED_REQUEUE';phase('COMPLETE')
    print('R4A_UDP_HUMAN_RETRY=PASS ACCEPTED_COUNT='+str(len(evidence['rows']))
        +' HUMAN_OWNER_AUTHORIZATION_PROVEN=true ORIGINAL_JOBS_REQUEUED=true'
        +' REPLAY=false INTAKE_POST=false MATERIALIZATION_NOT_YET_VERIFIED=true'
        +' SECRETS_NOT_PRINTED=true',flush=True)


def save_failure(args,error):
    code=str(error) if isinstance(error,api.Blocked) else 'UNCLASSIFIED'
    saved=False;count=0;attempted=False;uncertain=False
    if getattr(args,'_receipt_owned',False):
        try:
            api.private(args.receipt);value=json.loads(args.receipt.read_text());rows=value.get('rows',[])
            count=sum(r.get('status')=='PASS_ACCEPTED' for r in rows)
            uncertain=any(r.get('status')=='POST_INTENT_OUTCOME_UNKNOWN' for r in rows)
            attempted=bool(count or uncertain)
            value.update(status='BLOCKED_RECONCILE_DO_NOT_REPOST',phase=args._phase,
                safeFailureCode=code,failureType=type(error).__name__,acceptedCount=count,
                retryPostAttempted=attempted,outcomeUncertain=uncertain)
            api.write(args.receipt,value);saved=True
        except Exception:pass
    return code,saved,count,attempted,uncertain


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('issuer','client','audience','base-url','tenant','subject','scope','expected-policy',
                 'expected-failure','outside-job','source','run','reason'):
        p.add_argument('--'+name,required=True)
    for name in ('publication-receipt','resources','prior-review-receipt','receipt'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--binding',action='append',required=True)
    p.add_argument('--expected-version',type=int,required=True)
    p.add_argument('--expected-resources',type=int,required=True)
    args=p.parse_args()
    try:execute(args)
    except Exception as error:
        code,saved,count,attempted,uncertain=save_failure(args,error)
        print('R4A_UDP_HUMAN_RETRY=BLOCKED CODE='+code+' TYPE='+type(error).__name__
            +' PHASE='+args._phase+' ERROR_SAVED='+str(saved).lower()+' ACCEPTED_COUNT='+str(count)
            +' RETRY_POST_ATTEMPTED='+str(attempted).lower()+' OUTCOME_UNCERTAIN='+str(uncertain).lower()
            +' RECONCILE_RECEIPT_DO_NOT_REPOST=true SECRETS_NOT_PRINTED=true',flush=True)
        raise SystemExit(1)
