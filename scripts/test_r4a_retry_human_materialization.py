import argparse
import base64
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import uuid
import r4a_prepare_scoped_human_policy as api
import r4a_retry_human_materialization as retry
import test_r4a_review_publish_scoped_human_policy as fixtures


class HumanRetry(unittest.TestCase):
    def run_case(self,failure=None):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);args,state,resources,_=fixtures.Review().fixture(root,'publish')
            args.run=str(uuid.uuid4());args.source='source';args.scope=args.capability
            args.expected_policy='policy:8';args.expected_resources=3;args.expected_version=2
            args.expected_failure='UDP_REFERENCE_INTEGRITY_CONTRACT_INVALID'
            args.outside_job=str(uuid.uuid4());args.reason='Reviewed original technical quarantine'
            template=copy.deepcopy(resources[0]);resources=[];values={};args.binding=[]
            for i in range(3):
                resource=copy.deepcopy(template);resource['resourceId']=str(uuid.uuid4())
                resource['resourceAttributes']['jobRef']=args.run;resources.append(resource)
                handoff=str(uuid.uuid4());args.binding.append(resource['resourceId']+':'+handoff)
                values[resource['resourceId']]={'jobId':resource['resourceId'],'handoffId':handoff,
                    'sourceId':args.source,'ingestionRunId':args.run,'state':'QUARANTINED','stateVersion':2,
                    'intakeState':'DURABLE','safeFailureCode':args.expected_failure,'retryEligible':True,
                    'contractReady':True,'contractCheck':'READY','verifiedBaselineHash':'sha256:'+'a'*64,
                    'snapshotHash':'sha256:'+str(i)*64,'attempts':1,'integrityAttempts':1}
            grant=copy.deepcopy(state['candidate']['grants'][0]);grants=[]
            for resource in resources:
                row=copy.deepcopy(grant);row['grantId']=str(uuid.uuid4())
                row['constraints']['resourceId']=resource['resourceId'];grants.append(row)
            state['candidate']['grants']=grants
            publication={'status':'PASS_PUBLISHED','resourcesHash':api.digest(resources),
                'activeReadback':{'policyRef':'policy:8','policy':state['candidate']}}
            prior={'status':'PASS_READY','resourcesHash':api.digest(resources),
                'publicationReceiptHash':api.digest(publication),'anonymousHttp':401,'outsideScopeHttp':403,
                'reviews':[{'review':copy.deepcopy(v),'ready':True} for v in values.values()]}
            selective=bool(failure and failure.startswith('selected-'))
            if selective:
                target=resources[1]['resourceId'];args.select_job=[target]
                args.prior_expected_version=2;args.expected_version=5
                for key,value in values.items():
                    value['stateVersion']=5
                    if key!=target:value.update(state='SUCCEEDED',intakeState='PROCESSED',retryEligible=False)
                if failure=='selected-outside':args.select_job=[args.outside_job]
                if failure=='selected-duplicate':args.select_job=[target,target]
                if failure=='selected-stale':values[target]['stateVersion']=6
                if failure=='selected-contract':values[target].update(contractReady=False,contractCheck='CONTRACT_INVALID')
            if failure=='prior':prior['status']='BLOCKED'
            args.publication_receipt=root/'publication.json';args.prior_review_receipt=root/'prior.json'
            args.receipt=root/'retry.json'
            for path,value in ((args.publication_receipt,publication),(args.prior_review_receipt,prior),
                               (args.resources,resources)):
                path.write_text(json.dumps(value));path.chmod(0o600)
            if failure=='source':args.source='other'
            exp=int(time.time()+(-1 if failure=='expired' else 300))
            token='PRIVATE.'+base64.urlsafe_b64encode(json.dumps({'exp':exp}).encode()).decode().rstrip('=')+'.TOKEN'
            calls=[];posts=[];confirmed=[];fresh_gets=[];output=io.StringIO()
            def http(url,token=None,method='GET',body=None,**kw):
                calls.append((method,url));self.assertFalse(kw)
                if method=='GET':
                    self.assertIsNone(body)
                    if token is None:raise api.Blocked('HTTP_401')
                    if url.endswith('/'+args.outside_job):raise api.Blocked('HTTP_403')
                    key=url.rsplit('/',1)[-1];fresh_gets.append(key)
                    value=copy.deepcopy(values[key])
                    if failure=='fresh-reference':value.update(contractReady=False,contractCheck='CATALOG_UNAVAILABLE')
                    if failure=='fresh-stale':value['stateVersion']=3
                    return 200,value,{}
                self.assertEqual(method,'POST');self.assertTrue(url.endswith('/retry'))
                self.assertTrue(confirmed);self.assertEqual(len(fresh_gets),1 if selective else 3)
                evidence=json.loads(args.receipt.read_text());self.assertTrue(evidence['humanConfirmed'])
                job=url.split('/')[-2];row=next(r for r in evidence['rows'] if r['jobId']==job)
                self.assertEqual(row['status'],'POST_INTENT_OUTCOME_UNKNOWN');self.assertEqual(row['request'],body)
                self.assertEqual(body['expectedVersion'],args.expected_version);self.assertEqual(body['expectedSnapshotHash'],values[job]['snapshotHash'])
                self.assertEqual(str(uuid.UUID(body['operationId'])),body['operationId']);posts.append(copy.deepcopy(body))
                if failure=='timeout-second' and len(posts)==2:raise TimeoutError('PRIVATE_TRANSPORT_DETAIL')
                if failure=='conflict':raise api.Blocked('HTTP_409')
                result={'operationId':body['operationId'],'jobId':job,'handoffId':row['handoffId'],
                    'acceptedVersion':args.expected_version+1,'state':'READY','repeated':False}
                if failure=='bad-response':result['payload']='PRIVATE_PAYLOAD'
                return 200,result,{}
            def confirm(run):
                self.assertEqual(run,args.run);confirmed.append(run)
                if failure=='confirmation':raise api.Blocked('HUMAN_CONFIRMATION_NOT_MATCHED')
            error=None
            with patch.object(api,'login',return_value=token) as login,patch.object(api,'http',side_effect=http),\
                 patch.object(retry,'confirm',side_effect=confirm),contextlib.redirect_stdout(output):
                try:retry.execute(args)
                except Exception as caught:error=caught;retry.save_failure(args,caught)
                evidence=json.loads(args.receipt.read_text()) if args.receipt.exists() else None
                if evidence:
                    self.assertEqual(args.receipt.stat().st_mode&0o777,0o600)
                    before=args.receipt.read_bytes();count=len(posts)
                    with self.assertRaises(api.Blocked):retry.execute(args)
                    self.assertEqual(len(posts),count);self.assertEqual(args.receipt.read_bytes(),before)
                if failure in ('prior','source'):login.assert_not_called()
            self.assertNotIn(token,output.getvalue());self.assertNotIn('PRIVATE_TRANSPORT_DETAIL',output.getvalue())
            self.assertNotIn('PRIVATE_PAYLOAD',output.getvalue());self.assertNotIn('sha256:',output.getvalue())
            if evidence:self.assertNotIn(token,json.dumps(evidence))
            return error,evidence,posts,output.getvalue()

    def test_three_fresh_reviews_then_confirmed_exact_original_posts(self):
        error,evidence,posts,out=self.run_case()
        self.assertIsNone(error);self.assertEqual(evidence['status'],'PASS_AUTHORIZED_REQUEUE')
        self.assertEqual(len(posts),3);self.assertEqual(len({p['operationId'] for p in posts}),3)
        self.assertTrue(all(r['status']=='PASS_ACCEPTED' for r in evidence['rows']))
        self.assertIn('MATERIALIZATION_NOT_YET_VERIFIED=true',out)

    def test_selected_remaining_job_v5_only_and_full_prior_v2_unchanged(self):
        error,evidence,posts,out=self.run_case('selected-success')
        self.assertIsNone(error);self.assertEqual(len(posts),1)
        self.assertEqual(posts[0]['expectedVersion'],5)
        self.assertEqual(len(evidence['rows']),1)
        self.assertEqual(evidence['rows'][0]['receipt']['acceptedVersion'],6)
        self.assertIn('JOBS=1',out)

    def test_selected_outside_or_duplicate_blocks_before_post(self):
        for mode in ('selected-outside','selected-duplicate'):
            with self.subTest(mode=mode):
                error,evidence,posts,_=self.run_case(mode)
                self.assertIsInstance(error,api.Blocked);self.assertIsNone(evidence);self.assertEqual(posts,[])

    def test_selected_stale_or_contract_invalid_prevents_post(self):
        for mode in ('selected-stale','selected-contract'):
            with self.subTest(mode=mode):
                error,evidence,posts,_=self.run_case(mode)
                self.assertIsInstance(error,api.Blocked);self.assertEqual(posts,[])
                self.assertFalse(evidence['retryPostAttempted']);self.assertNotIn('humanConfirmed',evidence)

    def test_prior_or_source_drift_prevents_login_and_post(self):
        for failure in ('prior','source'):
            with self.subTest(failure=failure):
                error,evidence,posts,_=self.run_case(failure)
                self.assertIsInstance(error,api.Blocked);self.assertIsNone(evidence);self.assertEqual(posts,[])

    def test_fresh_reference_gate_or_version_drift_prevents_confirmation_and_post(self):
        for failure in ('fresh-reference','fresh-stale'):
            with self.subTest(failure=failure):
                error,evidence,posts,_=self.run_case(failure)
                self.assertIsInstance(error,api.Blocked);self.assertEqual(posts,[])
                self.assertFalse(evidence['retryPostAttempted']);self.assertNotIn('humanConfirmed',evidence)

    def test_confirmation_or_expired_token_prevents_every_post(self):
        for failure in ('confirmation','expired'):
            with self.subTest(failure=failure):
                error,evidence,posts,_=self.run_case(failure)
                self.assertIsInstance(error,api.Blocked);self.assertEqual(posts,[])
                self.assertFalse(evidence['retryPostAttempted']);self.assertEqual(evidence['acceptedCount'],0)

    def test_uncertain_second_response_stops_third_post_and_preserves_first_acceptance(self):
        error,evidence,posts,out=self.run_case('timeout-second')
        self.assertIsInstance(error,TimeoutError);self.assertEqual(len(posts),2)
        self.assertEqual(evidence['acceptedCount'],1);self.assertTrue(evidence['outcomeUncertain'])
        self.assertEqual([r['status'] for r in evidence['rows']],
            ['PASS_ACCEPTED','POST_INTENT_OUTCOME_UNKNOWN','PREPARED_NO_POST'])
        self.assertNotIn('R4A_UDP_HUMAN_RETRY=PASS',out)

    def test_http_conflict_or_unexpected_response_never_reposts_or_accepts_payload(self):
        for failure in ('conflict','bad-response'):
            with self.subTest(failure=failure):
                error,evidence,posts,_=self.run_case(failure)
                self.assertIsInstance(error,api.Blocked);self.assertEqual(len(posts),1)
                self.assertEqual(evidence['acceptedCount'],0);self.assertTrue(evidence['outcomeUncertain'])
                self.assertNotIn('PRIVATE_PAYLOAD',json.dumps(evidence))

    def test_failure_does_not_modify_unowned_existing_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'receipt.json';path.write_text('{"status":"EXISTING"}')
            args=argparse.Namespace(receipt=path,_receipt_owned=False)
            retry.save_failure(args,TimeoutError('PRIVATE'))
            self.assertEqual(path.read_text(),'{"status":"EXISTING"}')

    def test_real_nonseekable_terminal_confirmation_and_wrong_phrase(self):
        import pty,select
        run=str(uuid.uuid4())
        for denied in (False,True):
            pid,master=pty.fork()
            if pid==0:
                try:retry.confirm(run);os._exit(1 if denied else 0)
                except api.Blocked:os._exit(0 if denied else 2)
                except BaseException:os._exit(3)
            sent=False;reaped=False;data=b'';deadline=time.monotonic()+5
            try:
                while time.monotonic()<deadline:
                    ready,_,_=select.select([master],[],[],0.05)
                    if ready:
                        try:data+=os.read(master,4096)
                        except OSError:pass
                    if not sent and b'CONFERMA HUMAN>' in data:
                        os.write(master,('NO\n' if denied else 'CONFERMO RETRY ORIGINALE '+run+'\n').encode());sent=True
                    done,status=os.waitpid(pid,os.WNOHANG)
                    if done:
                        reaped=True;self.assertTrue(sent);self.assertEqual(os.waitstatus_to_exitcode(status),0);break
                self.assertTrue(reaped)
            finally:
                if not reaped:os.kill(pid,9);os.waitpid(pid,0)
                os.close(master)


if __name__=='__main__':unittest.main()
