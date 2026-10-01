#!/usr/bin/env python3
"""Direct HUMAN versioned retry/resume with private intent receipts; no SQL mutation."""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import uuid
import r4a_verify_human_recovery_access as read

WRITE_SCOPES = {'ouf.ingestion.quarantine.retry','ingestion.run.resume'}


def private(path):
    meta=path.lstat()
    if not stat.S_ISREG(meta.st_mode) or meta.st_uid!=0 or stat.S_IMODE(meta.st_mode)!=0o600:
        raise RuntimeError('RECOVERY_PRIVATE_RECEIPT_UNSAFE')
    return json.loads(path.read_text())


def save(path,value,exclusive=False):
    if exclusive:
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'w') as stream:
            json.dump(value,stream,sort_keys=True);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    else:
        fd,name=tempfile.mkstemp(prefix='.recovery-intent-',dir=read.ROOT)
        try:
            with os.fdopen(fd,'w') as stream:
                json.dump(value,stream,sort_keys=True);stream.write('\n');stream.flush();os.fsync(stream.fileno())
            os.replace(name,path)
        finally:Path(name).unlink(missing_ok=True)
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def post(args,kind,version,token,correlation):
    if kind=='retry':path='/api/trusted-human/v1/ingestion/quarantine/'+str(uuid.UUID(args.quarantine))+'/retry'
    elif kind=='resume':path='/api/trusted-human/v1/ingestion/runs/'+str(uuid.UUID(args.run))+'/resume'
    else:raise RuntimeError('RECOVERY_POST_ACTION_FORBIDDEN')
    if type(version) is not int or version<0:raise RuntimeError('RECOVERY_VERSION_INVALID')
    if not re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',token):raise RuntimeError('RECOVERY_TOKEN_INVALID')
    correlation=str(uuid.UUID(correlation))
    body=json.dumps({'expectedVersion':version},separators=(',',':'))
    config=('silent\nshow-error\nmax-time = 30\nmax-filesize = 1048576\nrequest = "POST"\n'
            'header = "Authorization: Bearer '+token+'"\nheader = "Content-Type: application/json"\n'
            'header = "X-Correlation-ID: '+correlation+'"\ndata = '+json.dumps(body)+'\n'
            'url = "'+args.api+path+'"\nwrite-out = "\\n%{http_code}"\n')
    raw=read.helper.run(['docker','run','--rm','-i','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--network',read.RUNTIME.get('network','ouf-backend'),read.RUNTIME.get('curl_image','curlimages/curl:8.16.0'),'--config','-'],input=config,timeout=40)
    # helper.run strips outer whitespace; an empty HTTP204 becomes just "204".
    body,separator,code=raw.rpartition('\n')
    if not separator:
        body,code='',raw
    if code!=('204' if kind=='retry' else '200'):
        raise RuntimeError('RECOVERY_'+kind.upper()+'_HTTP_'+(code if re.fullmatch(r'\d{3}',code) else 'INVALID')+'_RECONCILE_DO_NOT_REPOST')
    return None if kind=='retry' else json.loads(body)


def views(args,token):
    run=read.get(args.api,'/api/trusted-human/v1/ingestion/runs/'+args.run,token)
    q=read.get(args.api,'/api/trusted-human/v1/ingestion/quarantine/'+args.quarantine,token)
    baseline=read.snapshot(args.run,args.quarantine)
    if not baseline['run'] or not baseline['quarantine'] or baseline['run']['tenant_id']!=args.tenant or baseline['quarantine']['run_id']!=args.run:
        raise RuntimeError('RECOVERY_OWNER_TENANT_OR_RUN_MISMATCH')
    read.match_response(run,baseline['run']);read.match_response(q,baseline['quarantine'])
    return baseline


def expect_initial(value,expected):
    if (value!=expected or value['run']['state']!='PAUSED' or value['quarantine']['lifecycle_state']!='OPEN'
            or type(value['run']['control_version']) is not int or type(value['quarantine']['lifecycle_version']) is not int):
        raise RuntimeError('RECOVERY_INITIAL_VERSION_OR_STATE_DRIFT')


def report(value):
    print('RECOVERY_RUN_STATE='+str(value['run']['state'])+' CONTROL_VERSION='+str(value['run']['control_version']))
    print('RECOVERY_QUARANTINE_STATE='+str(value['quarantine']['lifecycle_state'])+' LIFECYCLE_VERSION='+str(value['quarantine']['lifecycle_version']))


def confirmation(phrase):
    # TTYs are not seekable: avoid a buffered read/write TextIOWrapper (r+).
    with open('/dev/tty','w') as output:
        output.write('Per confermare digita '+phrase+'\n> ')
        output.flush()
    with open('/dev/tty','r') as source:
        return source.readline().strip()==phrase


def cycle_paths(args):
    suffix=args.run
    if getattr(args,'cycle',None):
        if str(uuid.UUID(args.cycle))!=args.quarantine:
            raise RuntimeError('RECOVERY_CYCLE_MUST_EQUAL_QUARANTINE')
        suffix+='-'+args.quarantine
    return (read.ROOT/('ingestion-human-recovery-'+suffix+'.json'),
            read.ROOT/('ingestion-human-recovery-read-'+suffix+'.json'))


def validate_predecessor(args,current):
    path=getattr(args,'previous_receipt',None)
    if path is None or path.parent!=read.ROOT:
        raise RuntimeError('RECOVERY_PREVIOUS_RECEIPT_REQUIRED_IN_PRIVATE_ROOT')
    prior=private(path)
    if (prior.get('phase')!='RESUME_CONFIRMED'
            or any(prior.get(k)!=getattr(args,k) for k in ('run','subject','tenant'))
            or prior.get('revision')!=args.expected_revision
            or prior.get('quarantine')==args.quarantine
            or type(prior.get('resumedControlVersion')) is not int
            or prior['resumedControlVersion']!=current['run']['control_version']):
        raise RuntimeError('RECOVERY_PREVIOUS_CYCLE_NOT_CONFIRMED_OR_CONTEXT_DRIFT')
    return prior


def resume_only(args,token,current,live,receipt_path):
    receipt=private(receipt_path)
    if (any(receipt.get(k)!=getattr(args,k) for k in ('run','quarantine','subject','tenant'))
            or receipt.get('revision')!=args.expected_revision):
        raise RuntimeError('RECOVERY_RECEIPT_CONTEXT_MISMATCH')
    if receipt.get('phase') not in ('RETRY_REQUESTED_DO_NOT_REPOST','RETRY_CONFIRMED','RETRY_RECONCILED'):
        raise RuntimeError('RECOVERY_RESUME_INTENT_EXISTS_OR_PHASE_UNSUPPORTED_USE_VERIFY')
    rv=receipt['expectedRunVersion'];qv=receipt['expectedQuarantineVersion']
    if type(rv) is not int or type(qv) is not int or min(rv,qv)<0:
        raise RuntimeError('RECOVERY_RECEIPT_VERSION_INVALID')
    initial=receipt['initial']
    if (initial['run']['state']!='PAUSED' or initial['run']['control_version']!=rv
            or initial['quarantine']['lifecycle_state']!='OPEN' or initial['quarantine']['lifecycle_version']!=qv):
        raise RuntimeError('RECOVERY_INITIAL_RECEIPT_INCONSISTENT')
    expected={'run':initial['run'],'quarantine':{**initial['quarantine'],'lifecycle_state':'RETRY_READY','lifecycle_version':qv+1}}
    if current!=expected:
        raise RuntimeError('RECOVERY_RESUME_ONLY_OWNER_STATE_MISMATCH')
    read.claims_check(token,args)
    if views(args,token)!=expected or read.helper.inspect(read.ingestion_container())['Id']!=live['Id']:
        raise RuntimeError('RECOVERY_CONTEXT_CHANGED_BEFORE_RESUME')
    # This receipt was created after the original HUMAN confirmation of both
    # actions. Reconcile the committed retry; do not issue it a second time.
    receipt.update(phase='RETRY_RECONCILED',afterRetry=current,retryConfirmedByReadback=True)
    save(receipt_path,receipt)
    print('R4A_HUMAN_RETRY_RECONCILIATION=PASS STATE=RETRY_READY VERSION='+str(qv+1)+' RETRY_POST=false',flush=True)
    receipt['phase']='RESUME_REQUESTED_DO_NOT_REPOST';save(receipt_path,receipt)
    response=post(args,'resume',rv,token,receipt['resumeCorrelationId'])
    if (not isinstance(response,dict) or response.get('run_id')!=args.run or response.get('state')!='RUNNING'
            or response.get('control_version')!=rv+1):
        raise RuntimeError('RECOVERY_RESUME_RESPONSE_MISMATCH_DO_NOT_REPOST')
    receipt.update(phase='RESUME_CONFIRMED',resumeHttp=200,resumedControlVersion=rv+1)
    save(receipt_path,receipt)
    print('R4A_HUMAN_RUN_RESUME=PASS HTTP=200 CONTROL_VERSION='+str(rv+1),flush=True)
    print('R4A_HUMAN_RUN_RECOVERY=PASS RETRY_POST=false RESUME_AUTHORIZATION_PROVEN=true SOURCE_REACTIVATION=false REPLAY=false INGESTION_RESULT_NOT_YET_VERIFIED=true SECRETS_NOT_PRINTED=true')


def main(args):
    if os.geteuid()!=0:raise RuntimeError('ROOT_REQUIRED')
    os.umask(0o077)
    read.configure(args)
    meta=read.ROOT.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid!=0 or stat.S_IMODE(meta.st_mode)!=0o700:raise RuntimeError('RECOVERY_ROOT_UNSAFE')
    args.run=str(uuid.UUID(args.run));args.quarantine=str(uuid.UUID(args.quarantine));args.subject=str(uuid.UUID(args.subject))
    read.origin(args.api);read.origin(args.issuer)
    if read.urlparse(args.api).path not in ('','/') or args.api.endswith('/') or args.issuer.endswith('/'):
        raise RuntimeError('RECOVERY_ENDPOINT_PATH_UNSUPPORTED')
    for value in (args.client,args.tenant,args.audience):
        if not re.fullmatch(r'[A-Za-z0-9._:-]{1,160}',value):raise RuntimeError('RECOVERY_IDENTIFIER_INVALID')
    if not re.fullmatch(r'[0-9a-f]{40}',args.expected_revision):raise RuntimeError('RECOVERY_REVISION_INVALID')
    live=read.helper.inspect(read.ingestion_container())
    image=read.helper.inspect(live['Image'],'image')
    if not live['State']['Running'] or image['Config'].get('Labels',{}).get('org.opencontainers.image.revision')!=args.expected_revision:
        raise RuntimeError('RECOVERY_LIVE_RELEASE_DRIFT')
    receipt_path,proof_path=cycle_paths(args)
    if args.mode=='recover' and (receipt_path.exists() or receipt_path.is_symlink()):
        raise RuntimeError('RECOVERY_INTENT_EXISTS_USE_VERIFY_DO_NOT_REPOST')
    if args.mode=='recover':read.SCOPES |= WRITE_SCOPES
    if args.mode=='resume-only':read.SCOPES |= {'ingestion.run.resume'}
    token=read.login(args)
    current=views(args,token)
    if args.mode=='verify':
        receipt=private(receipt_path)
        if any(receipt.get(k)!=getattr(args,k) for k in ('run','quarantine','subject','tenant')):
            raise RuntimeError('RECOVERY_RECEIPT_CONTEXT_MISMATCH')
        report(current)
        print('RECOVERY_SAVED_PHASE='+str(receipt['phase']))
        print('R4A_HUMAN_RUN_RECOVERY_VERIFY=PASS READ_ONLY=true RETRY=false RUN_RESUME=false AUTOMATIC_REPOST=false INGESTION_RESULT_NOT_YET_VERIFIED=true')
        return
    if args.mode=='resume-only':
        resume_only(args,token,current,live,receipt_path)
        return
    if getattr(args,'cycle',None):
        validate_predecessor(args,current)
        expect_initial(current,current)
        previous={'status':'PASS','runId':args.run,'quarantineId':args.quarantine,'subject':args.subject,'tenant':args.tenant,'revision':args.expected_revision,'snapshot':current}
        if proof_path.exists() or proof_path.is_symlink():
            old=private(proof_path)
            if any(old.get(k)!=previous[k] for k in ('runId','quarantineId','subject','tenant','revision')):
                raise RuntimeError('RECOVERY_CYCLE_READ_CONTEXT_DRIFT')
            save(proof_path,previous)
        else:save(proof_path,previous,exclusive=True)
        print('R4A_FRESH_CYCLE_READ=PASS HTTP=200 BUSINESS_STATE_UNCHANGED=true',flush=True)
    else:
        previous=private(proof_path)
    if (previous.get('status')!='PASS' or previous.get('quarantineId')!=args.quarantine
            or previous.get('subject')!=args.subject or previous.get('tenant')!=args.tenant
            or previous.get('revision')!=args.expected_revision):
        raise RuntimeError('RECOVERY_READ_PROOF_CONTEXT_MISMATCH')
    expect_initial(current,previous['snapshot'])
    rv=current['run']['control_version'];qv=current['quarantine']['lifecycle_version']
    report(current)
    print('SOURCE='+current['run']['source_id'],flush=True)
    print('Il retry autorizza il record in quarantena. Il resume avvia nuovamente ingestion e consegna a UDP.',flush=True)
    phrase='RECUPERO '+args.run+(' '+args.quarantine if getattr(args,'cycle',None) else '')
    if not confirmation(phrase):
        print('R4A_HUMAN_RUN_RECOVERY=CANCELLED RETRY=false RUN_RESUME=false');return
    read.claims_check(token,args)
    expect_initial(views(args,token),current)
    if read.helper.inspect(read.ingestion_container())['Id']!=live['Id']:raise RuntimeError('RECOVERY_RUNTIME_DRIFT')
    receipt={'phase':'RETRY_REQUESTED_DO_NOT_REPOST','run':args.run,'quarantine':args.quarantine,'subject':args.subject,'tenant':args.tenant,'revision':args.expected_revision,'expectedRunVersion':rv,'expectedQuarantineVersion':qv,'retryCorrelationId':str(uuid.uuid4()),'resumeCorrelationId':str(uuid.uuid4()),'initial':current}
    save(receipt_path,receipt,exclusive=True)
    print('R4A_HUMAN_RUN_RECOVERY_RECEIPT='+str(receipt_path)+' PRIVATE=true',flush=True)
    post(args,'retry',qv,token,receipt['retryCorrelationId'])
    after_retry=views(args,token)
    expected_retry={'run':current['run'],'quarantine':{**current['quarantine'],'lifecycle_state':'RETRY_READY','lifecycle_version':qv+1}}
    if after_retry!=expected_retry:
        raise RuntimeError('RECOVERY_RETRY_READBACK_MISMATCH_DO_NOT_REPOST')
    receipt.update(phase='RETRY_CONFIRMED',afterRetry=after_retry);save(receipt_path,receipt)
    print('R4A_HUMAN_QUARANTINE_RETRY=PASS HTTP=204 STATE=RETRY_READY VERSION='+str(qv+1),flush=True)
    read.claims_check(token,args)
    if views(args,token)!=after_retry:raise RuntimeError('RECOVERY_CONTEXT_CHANGED_BEFORE_RESUME')
    if read.helper.inspect(read.ingestion_container())['Id']!=live['Id']:raise RuntimeError('RECOVERY_RUNTIME_DRIFT')
    receipt['phase']='RESUME_REQUESTED_DO_NOT_REPOST';save(receipt_path,receipt)
    response=post(args,'resume',rv,token,receipt['resumeCorrelationId'])
    if (not isinstance(response,dict) or response.get('run_id')!=args.run or response.get('state')!='RUNNING'
            or response.get('control_version')!=rv+1):
        raise RuntimeError('RECOVERY_RESUME_RESPONSE_MISMATCH_DO_NOT_REPOST')
    receipt.update(phase='RESUME_CONFIRMED',resumeHttp=200,resumedControlVersion=rv+1);save(receipt_path,receipt)
    print('R4A_HUMAN_RUN_RESUME=PASS HTTP=200 CONTROL_VERSION='+str(rv+1),flush=True)
    print('R4A_HUMAN_RUN_RECOVERY=PASS RETRY_AUTHORIZATION_PROVEN=true RESUME_AUTHORIZATION_PROVEN=true SOURCE_REACTIVATION=false REPLAY=false INGESTION_RESULT_NOT_YET_VERIFIED=true SECRETS_NOT_PRINTED=true')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('recover','verify','resume-only'))
    parser.add_argument('--cycle',help='New cycle: must equal the quarantine UUID; preserves legacy receipts')
    parser.add_argument('--previous-receipt',type=Path)
    for name in ('receipt-root','ingestion-container','postgres-container','database','db-user','network','curl-image'):
        parser.add_argument('--'+name)
    for name in ('issuer','api','client','subject','tenant','audience','run','quarantine','expected-revision'):
        parser.add_argument('--'+name,required=True)
    try:main(parser.parse_args())
    except Exception as error:
        code=str(error) if isinstance(error,RuntimeError) else type(error).__name__
        print('R4A_HUMAN_RUN_RECOVERY=BLOCKED CODE='+code+' AUTOMATIC_REPOST=false RECONCILE_RECEIPT_AND_OWNER_STATE=true SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
