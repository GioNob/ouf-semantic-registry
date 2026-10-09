import base64
import json
from types import SimpleNamespace
import time
import unittest
from unittest.mock import patch
import r4a_verify_human_recovery_access as probe


class RecoveryReadTests(unittest.TestCase):
    def test_owner_response_must_match_lifecycle_version_and_identity(self):
        baseline={'run_id':'run','state':'PAUSED','control_version':0,'tenant_id':'tenant'}
        probe.match_response({'run_id':'run','state':'PAUSED','control_version':0,'extra':'ignored'},baseline)
        for field,value in [('run_id','other'),('state','RUNNING'),('control_version',1)]:
            doc={'run_id':'run','state':'PAUSED','control_version':0};doc[field]=value
            with self.subTest(field=field),self.assertRaises(RuntimeError):probe.match_response(doc,baseline)

    def test_claim_diagnostics_reject_wrong_actor_scope_and_tenant(self):
        args=SimpleNamespace(issuer='https://auth.example/realms/ouf',client='human',subject='subject',tenant='tenant',audience='aud')
        doc={'iss':args.issuer,'azp':args.client,'sub':args.subject,'tenant_id':args.tenant,'aud':'aud','ouf_actor_type':'HUMAN','exp':int(time.time())+300,'scope':'ingestion.run.read ingestion.quarantine.read'}
        def token(value):return 'e30.'+base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip('=')+'.sig'
        probe.claims_check(token(doc),args)
        for field,value in [('ouf_actor_type','SERVICE'),('tenant_id','other'),('scope','ingestion.run.read'),('exp',0),('azp','service')]:
            with self.subTest(field=field),self.assertRaises(RuntimeError):probe.claims_check(token({**doc,field:value}),args)

    def test_request_uses_get_and_bearer_only_on_stdin(self):
        with patch.object(probe.helper,'run',return_value='{}\n200') as run:
            probe.get('https://api.example','/api/trusted-human/v1/ingestion/runs/id','hidden-token')
            argv=run.call_args.args[0];config=run.call_args.kwargs['input']
            self.assertNotIn('hidden-token',' '.join(argv))
            self.assertIn('request = "GET"',config)
            self.assertNotIn('POST',config)

    def test_failed_http_never_prints_private_body(self):
        with patch.object(probe.helper,'run',return_value='PRIVATE_RESPONSE\n403'):
            with self.assertRaisesRegex(RuntimeError,'^RECOVERY_READ_HTTP_403$'):
                probe.get('https://api.example','/path','token')


if __name__=='__main__':unittest.main()
