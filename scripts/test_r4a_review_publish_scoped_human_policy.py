import argparse
import contextlib
import copy
from datetime import datetime,timezone,timedelta
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import uuid
import r4a_review_publish_scoped_human_policy as review
import r4a_prepare_scoped_human_policy as policy

class Review(unittest.TestCase):
    def fixture(self,root,mode):
        root.chmod(0o700)
        desc={'capabilityId':'module.retry','operation':'COMMAND','requiredScope':'module.retry','allowedActors':['HUMAN']}
        resource={'capabilityId':'module.retry','resourceType':'materialization-job','resourceId':str(uuid.uuid4()),
            'resourceAttributes':{'module':'UDP','sourceRef':'source','jobRef':'run','typeRef':'type'},
            'allowedDataLabels':['RESTRICTED']}
        args=argparse.Namespace(mode=mode,issuer='https://issuer.example/realm',client='admin',audience='gateway',
            admin_scope='policy.admin',base_url='https://gateway.example/control',tenant='tenant',subject='human',
            capability=desc['capabilityId'],required_scope=desc['requiredScope'],operation='COMMAND',owner='udp',
            expected_resources=1,min_remaining_seconds=120,draft_receipt=root/'draft.json',
            resources=root/'resources.json',receipt=root/'review.json')
        manifest=root/'manifest.json';manifest.write_text(json.dumps([{'ownerRef':'udp','descriptor':desc}]))
        args.manifest=manifest;args.valid_until=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat()
        args.resources.write_text(json.dumps([resource]));args.resources.chmod(0o600)
        desired,grants=policy.inputs(args)
        current={'policyRef':'policy:7','activatedAt':'date','contentHash':'old-hash',
            'policy':{'bundleId':'policy','version':7,'publishedAt':'2026-10-01T10:00:00Z','capabilities':[],
                      'grants':[]}}
        target,missing=policy.candidate(current,desired,grants)
        state={'status':'PASS_UNPUBLISHED','tenant':'tenant','subject':'human','baseActive':current,
            'candidate':target,'addedDescriptors':missing,'addedGrants':grants,'baselineHash':policy.digest(current),
            'draftId':str(uuid.uuid4()),'revision':0}
        args.draft_receipt.write_text(json.dumps(state));args.draft_receipt.chmod(0o600)
        return args,state,[resource],desc

    def run_case(self,mode='publish',failure=None):
        with tempfile.TemporaryDirectory() as folder:
            args,state,resources,desc=self.fixture(Path(folder),mode)
            calls=[];published=False;confirmed=[];active_reads=0
            expected=review.scenarios(args,resources)
            def normalize(value):
                if isinstance(value,dict):return {k:normalize(v) for k,v in value.items()}
                if isinstance(value,list):return [normalize(v) for v in value]
                return 'outside-fixture' if isinstance(value,str) and value.startswith('outside-') else value
            def http(url,token=None,method='GET',body=None,form=None,etag=None):
                nonlocal published,active_reads
                calls.append((method,url))
                if url.endswith('/policies/active'):
                    active_reads+=1
                    current=copy.deepcopy(state['baseActive'])
                    if published:current.update(policyRef='policy:8',policy=copy.deepcopy(state['candidate']))
                    if failure=='active-drift' and not published:current['policyRef']='policy:99'
                    return 200,current,{}
                if '/capabilities?' in url:
                    return 200,[{'capability_id':desc['capabilityId'],'owner_ref':'udp','descriptor':desc}],{}
                if url.endswith('/policies/'+state['draftId']):
                    return 200,{'id':state['draftId'],'revision':1 if published else 0,
                        'state':'PUBLISHED' if published else 'DRAFT','baseActiveRef':'policy:7',
                        'policy':state['candidate']},{'ETag':'"1"' if published else '"0"'}
                if url.endswith(':preview'):
                    changes=[{'grantId':g['grantId'],'before':None,'after':copy.deepcopy(g)} for g in state['addedGrants']]
                    if failure=='preview-widen':changes[0]['after']['constraints']['allowedDataLabels']=[]
                    return 200,{'draftId':state['draftId'],'revision':0,'baseActiveRef':'policy:7',
                        'activeHash':'old-hash','draftHash':'new-hash','authoritative':False,
                        'addedCapabilities':[desc],'removedCapabilities':[],'grantChanges':changes},{}
                if url.endswith(':simulate'):
                    self.assertEqual(etag,0)
                    match=next(x for x in expected if normalize(x[1])==normalize(body));name,_,allow,code=match
                    if code=='HTTP_403':raise policy.Blocked('HTTP_403')
                    if failure=='negative-allows' and name.startswith('SERVICE'):allow=True
                    return 200,{'draftId':state['draftId'],'revision':0,'baseActiveRef':'policy:7',
                        'activeHash':'old-hash','draftHash':'new-hash','authoritative':False,
                        'contextSource':'HYPOTHETICAL_NOT_IAM_VERIFIED',
                        'before':{'allowed':False,'code':'CAPABILITY_NOT_DECLARED'},
                        'after':{'allowed':allow,'code':'ALLOW' if allow else code}},{}
                if url.endswith(':publish'):
                    saved=json.loads(args.receipt.read_text())
                    self.assertEqual(saved['status'],'PUBLISH_POST_UNVERIFIED_DO_NOT_REPOST')
                    self.assertTrue(confirmed);self.assertEqual(etag,0)
                    published=True
                    if failure=='lost-response':raise TimeoutError('PRIVATE_RESPONSE')
                    return 200,{'state':'PUBLISHED'},{}
                raise AssertionError('unplanned HTTP')
            def confirm(ref):
                confirmed.append(ref)
                if failure=='tty-then-resume' and len(confirmed)==1:
                    raise io.UnsupportedOperation('terminal is not seekable')
                if failure=='confirmation':raise policy.Blocked('HUMAN_CONFIRMATION_NOT_MATCHED')
                if failure=='expiry-after-confirm':
                    # Receipt is immutable; patch validity gate for the final check.
                    args.min_remaining_seconds=100000
            out=io.StringIO();error=None
            with patch.object(policy,'http',side_effect=http),patch.object(policy,'login',return_value='PRIVATE_TOKEN'),\
                 patch.object(review,'confirm',side_effect=confirm),contextlib.redirect_stdout(out):
                try:review.execute(args)
                except Exception as caught:error=caught
                evidence=json.loads(args.receipt.read_text())
                if failure=='tty-then-resume':
                    self.assertIsInstance(error,io.UnsupportedOperation)
                    self.assertEqual(evidence['status'],'REVIEWED_NOT_PUBLISHED')
                    args.mode='resume';review.execute(args)
                    evidence=json.loads(args.receipt.read_text());error=None
                elif failure=='lost-response':
                    args.mode='verify';review.execute(args)
                    self.assertEqual(json.loads(args.receipt.read_text())['status'],'PASS_PUBLISHED')
                elif mode=='publish' and not error:
                    args.mode='verify';review.execute(args)
                args.mode='publish'
                with patch.object(policy,'login') as login:
                    with self.assertRaises(policy.Blocked):review.execute(args)
                    login.assert_not_called()
            self.assertNotIn('PRIVATE_TOKEN',out.getvalue());self.assertNotIn('PRIVATE_RESPONSE',out.getvalue())
            self.assertEqual(args.receipt.stat().st_mode&0o777,0o600)
            return calls,evidence,error,published

    def test_review_only_never_publishes(self):
        calls,state,error,published=self.run_case('review')
        self.assertIsNone(error);self.assertFalse(published);self.assertEqual(state['status'],'REVIEWED_NOT_PUBLISHED')
        self.assertFalse(any(url.endswith(':publish') for _,url in calls))
        self.assertEqual(len(state['simulations']),15)
    def test_publish_confirm_intent_and_readback_exact(self):
        calls,state,error,published=self.run_case()
        self.assertIsNone(error);self.assertTrue(published);self.assertEqual(state['status'],'PASS_PUBLISHED')
        self.assertEqual(sum(url.endswith(':publish') for _,url in calls),1)
    def test_drift_preview_negative_allow_and_confirmation_block_publication(self):
        for failure in ('active-drift','preview-widen','negative-allows','confirmation','expiry-after-confirm'):
            with self.subTest(failure=failure):
                calls,_,error,published=self.run_case(failure=failure)
                self.assertIsNotNone(error);self.assertFalse(published)
                self.assertFalse(any(url.endswith(':publish') for _,url in calls))
    def test_lost_publish_response_verify_never_reposts(self):
        calls,state,error,published=self.run_case(failure='lost-response')
        self.assertIsInstance(error,TimeoutError);self.assertTrue(published)
        self.assertEqual(state['status'],'PUBLISH_POST_UNVERIFIED_DO_NOT_REPOST')
        self.assertEqual(sum(url.endswith(':publish') for _,url in calls),1)
    def test_terminal_failure_resume_fresh_review_then_one_publish(self):
        calls,state,error,published=self.run_case(failure='tty-then-resume')
        self.assertIsNone(error);self.assertTrue(published)
        self.assertEqual(state['status'],'PASS_PUBLISHED')
        self.assertEqual(sum(url.endswith(':publish') for _,url in calls),1)
        self.assertEqual(sum(url.endswith(':preview') for _,url in calls),2)
    def test_resume_refuses_existing_publish_intent_or_identity_drift_before_login(self):
        with tempfile.TemporaryDirectory() as folder:
            args,state,resources,_=self.fixture(Path(folder),'resume')
            saved={'draftReceiptHash':policy.digest(state),'resourcesHash':policy.digest(resources),'mode':'publish'}
            for status in ('PASS_PUBLISHED','PUBLISH_POST_UNVERIFIED_DO_NOT_REPOST','LOGIN_PENDING_NO_PUBLISH'):
                args.receipt.write_text(json.dumps({**saved,'status':status}));args.receipt.chmod(0o600)
                with patch.object(policy,'login') as login:
                    with self.assertRaises(policy.Blocked):review.execute(args)
                    login.assert_not_called()
            args.receipt.write_text(json.dumps({**saved,'status':'REVIEWED_NOT_PUBLISHED','resourcesHash':'drift'}))
            with patch.object(policy,'login') as login:
                with self.assertRaises(policy.Blocked):review.execute(args)
                login.assert_not_called()
    def terminal_case(self,phrase,denied):
        import os,pty,select,time
        pid,master=pty.fork()
        if pid==0:
            try:
                review.confirm('policy:8')
                os._exit(1 if denied else 0)
            except policy.Blocked as error:
                os._exit(0 if denied and str(error)=='HUMAN_CONFIRMATION_NOT_MATCHED' else 2)
            except BaseException:os._exit(3)
        data=b'';sent=False;reaped=False;deadline=time.monotonic()+5
        try:
            while time.monotonic()<deadline:
                ready,_,_=select.select([master],[],[],0.1)
                if ready:
                    try:chunk=os.read(master,4096)
                    # PTY hangup can precede waitpid visibility of child exit.
                    except OSError:chunk=b''
                    data+=chunk
                    if b'CONFERMA HUMAN>' in data and not sent:
                        os.write(master,(phrase+'\n').encode());sent=True
                ended,status=os.waitpid(pid,os.WNOHANG)
                if ended:reaped=True;break
            if not reaped:
                ended,status=os.waitpid(pid,os.WNOHANG)
                reaped=bool(ended)
            self.assertTrue(sent);self.assertTrue(reaped,'terminal child did not finish')
            self.assertEqual(os.waitstatus_to_exitcode(status),0)
        finally:
            os.close(master)
            if not reaped:
                os.kill(pid,9);os.waitpid(pid,0)
    def test_real_nonseekable_terminal_confirmation(self):
        self.terminal_case('PUBBLICO policy:8',False)
    def test_real_terminal_wrong_confirmation_denied(self):
        self.terminal_case('NO',True)
    def test_receipt_scope_widening_and_expiry_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            args,state,resources,_=self.fixture(Path(folder),'publish')
            for key,value in (('resourceId',None),('allowedDataLabels',[]),('externalRoleRef','role')):
                altered=copy.deepcopy(state);altered['addedGrants'][0]['constraints'][key]=value
                altered['candidate']['grants']=altered['addedGrants']
                with self.assertRaises(policy.Blocked):review.validate(args,altered,resources)
            expired=datetime.now(timezone.utc)+timedelta(hours=2)
            with self.assertRaises(policy.Blocked):review.validate(args,state,resources,expired)
            args.mode='verify';review.validate(args,state,resources,expired)
    def test_mutation_after_publish_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as folder:
            args,state,_,_=self.fixture(Path(folder),'verify')
            wrong=copy.deepcopy(state['candidate']);wrong['grants']=[]
            def http(url,*a,**kw):
                if url.endswith('/policies/active'):return 200,{'policyRef':'policy:8','policy':wrong},{}
                return 200,{'id':state['draftId'],'revision':1,'state':'PUBLISHED','baseActiveRef':'policy:7',
                    'policy':state['candidate']},{'ETag':'"1"'}
            with patch.object(policy,'http',side_effect=http):
                with self.assertRaises(policy.Blocked):review.publication_readback(args,'token',state,{})

if __name__=='__main__':unittest.main()
