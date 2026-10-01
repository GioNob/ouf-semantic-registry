import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import uuid
import r4a_read_human_materialization_review as read
import r4a_prepare_scoped_human_policy as api
import test_r4a_review_publish_scoped_human_policy as fixtures

class HumanRead(unittest.TestCase):
    def run_case(self,failure=None):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);args,state,resources,_=fixtures.Review().fixture(root,'publish')
            args.scope=args.capability;args.expected_policy='policy:8'
            args.expected_failure='UDP_REFERENCE_INTEGRITY_CONTRACT_INVALID';args.expected_version=2
            args.outside_job=str(uuid.uuid4());handoff=str(uuid.uuid4())
            args.binding=[resources[0]['resourceId']+':'+handoff]
            args.publication_receipt=root/'publication.json';args.receipt=root/'human.json'
            pub={'status':'PASS_PUBLISHED','resourcesHash':api.digest(resources),
                'activeReadback':{'policyRef':'policy:8','policy':state['candidate']}}
            if failure=='receipt-drift':pub['resourcesHash']='wrong'
            args.publication_receipt.write_text(json.dumps(pub));args.publication_receipt.chmod(0o600)
            calls=[];value={'jobId':resources[0]['resourceId'],'handoffId':handoff,
                'sourceId':'source','ingestionRunId':'run','state':'QUARANTINED','stateVersion':2,
                'intakeState':'DURABLE','safeFailureCode':args.expected_failure,'retryEligible':True,
                'contractReady':True,'contractCheck':'READY','verifiedBaselineHash':'sha256:'+'a'*64,
                'snapshotHash':'sha256:'+'b'*64,'attempts':1,'integrityAttempts':1}
            if failure=='contract':value.update(contractReady=False,contractCheck='CATALOG_UNAVAILABLE',verifiedBaselineHash=None)
            if failure=='binding':value['handoffId']=str(uuid.uuid4())
            if failure=='payload':value['payload']={'PRIVATE':'do not expose'}
            if failure=='stale':value['stateVersion']=3
            def http(url,token=None,method='GET',**kw):
                self.assertEqual(method,'GET');self.assertFalse(kw);calls.append(url)
                if token is None:
                    if failure=='anonymous-allowed':return 200,value,{}
                    raise api.Blocked('HTTP_401')
                if url.endswith('/'+args.outside_job):
                    if failure=='outside-allowed':return 200,value,{}
                    raise api.Blocked('HTTP_403')
                if failure=='owner-denied':raise api.Blocked('HTTP_403')
                if failure=='transport':raise TimeoutError('PRIVATE_TRANSPORT_DETAIL')
                return 200,copy.deepcopy(value),{}
            out=io.StringIO();error=None
            with patch.object(api,'http',side_effect=http),patch.object(api,'login',return_value='PRIVATE_TOKEN') as login,contextlib.redirect_stdout(out):
                try:read.execute(args)
                except BaseException as caught:
                    error=caught
                    if isinstance(caught,Exception):read.save_failure(args,caught)
                evidence=json.loads(args.receipt.read_text()) if args.receipt.exists() else None
                if evidence:
                    self.assertEqual(args.receipt.stat().st_mode&0o777,0o600)
                    with self.assertRaises(api.Blocked):read.execute(args)
                if failure=='receipt-drift':login.assert_not_called()
            self.assertNotIn('PRIVATE_TOKEN',out.getvalue());self.assertNotIn('sha256:',out.getvalue())
            self.assertNotIn('do not expose',out.getvalue())
            return error,evidence,calls,out.getvalue()
    def test_real_gets_only_success_and_private_snapshots(self):
        error,state,calls,out=self.run_case()
        self.assertIsNone(error);self.assertEqual(state['status'],'PASS_READY')
        self.assertEqual(len(calls),3);self.assertIn('HUMAN_OWNER_AUTHORIZATION_PROVEN=true',out)
    def test_contract_block_retains_authorization_proof_without_retry(self):
        error,state,_,out=self.run_case('contract')
        self.assertIsInstance(error,SystemExit);self.assertEqual(error.code,2)
        self.assertEqual(state['status'],'AUTHORIZATION_PASS_REFERENCE_GATE_BLOCKED')
        self.assertIn('SPRING_REVIEW_REFERENCE_GATE=BLOCKED',out)
    def test_receipt_drift_blocks_before_login(self):
        error,state,calls,_=self.run_case('receipt-drift')
        self.assertIsInstance(error,api.Blocked);self.assertIsNone(state);self.assertEqual(calls,[])
    def test_unexpected_scope_admission_blocks(self):
        for failure in ('anonymous-allowed','outside-allowed'):
            with self.subTest(failure=failure):
                error,state,_,_=self.run_case(failure)
                self.assertIsInstance(error,api.Blocked);self.assertNotEqual(state['status'],'PASS_READY')
    def test_stale_wrong_binding_or_extra_payload_not_accepted(self):
        for failure in ('binding','payload','stale'):
            with self.subTest(failure=failure):
                error,state,_,_=self.run_case(failure)
                self.assertIsInstance(error,api.Blocked);self.assertNotEqual(state['status'],'PASS_READY')
    def test_duplicate_original_job_binding_rejected(self):
        job=str(uuid.uuid4());handoff=str(uuid.uuid4())
        with self.assertRaises(api.Blocked):read.bindings([job+':'+handoff,job+':'+handoff])
    def test_owner_denial_saved_with_phase_and_negative_probes(self):
        error,state,_,_=self.run_case('owner-denied')
        self.assertIsInstance(error,api.Blocked)
        self.assertEqual(state['status'],'BLOCKED');self.assertEqual(state['safeFailureCode'],'HTTP_403')
        self.assertEqual(state['phase'],'OWNER_REVIEW_GET_1')
        self.assertEqual(state['anonymousHttp'],401);self.assertEqual(state['outsideScopeHttp'],403)
        self.assertEqual(state['reviews'],[])
    def test_validation_or_transport_errors_saved_without_sensitive_message(self):
        for failure,phase,code in (('payload','OWNER_REVIEW_VALIDATE_1','UDP_REVIEW_SHAPE_UNSUPPORTED'),
                                  ('transport','OWNER_REVIEW_GET_1','UNCLASSIFIED')):
            with self.subTest(failure=failure):
                error,state,_,out=self.run_case(failure)
                self.assertIsNotNone(error);self.assertEqual(state['status'],'BLOCKED')
                self.assertEqual(state['phase'],phase);self.assertEqual(state['safeFailureCode'],code)
                self.assertNotIn('PRIVATE_TRANSPORT_DETAIL',json.dumps(state)+out)
                if failure=='payload':self.assertEqual(state['ownerHttp'],[200])
    def test_error_handler_never_overwrites_unowned_receipt(self):
        import argparse
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'receipt.json';p.write_text('{"status":"PASS_READY"}')
            args=argparse.Namespace(receipt=p,_receipt_owned=False)
            self.assertEqual(read.save_failure(args,api.Blocked('HTTP_403')),('HTTP_403',False))
            self.assertEqual(p.read_text(),'{"status":"PASS_READY"}')

if __name__=='__main__':unittest.main()
