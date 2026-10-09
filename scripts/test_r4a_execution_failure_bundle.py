from contextlib import redirect_stdout
from datetime import datetime,timezone,timedelta
import io
import unittest
from unittest.mock import patch
import r4a_execution_failure_bundle as diag


class FailureBundleTests(unittest.TestCase):
    def test_logs_export_symbols_only(self):
        output=diag.log_facts('Bearer SECRET payload Alice 123 ING_EXECUTION_GATEWAY_403 UDP_RUNTIME_INTAKE_DENIED')
        self.assertEqual(output,{'ING_EXECUTION_GATEWAY_403':1,'UDP_RUNTIME_INTAKE_DENIED':1})

    def test_access_status_separates_gateway_and_upstream_without_payload(self):
        line='{"request":"POST /api/internal/v1/lake/objects HTTP/1.1","status":403,"upstream_status":403,"token":"SECRET"}'
        self.assertEqual(diag.access_facts(line),[{'endpoint':'LAKE','http':'403','upstream_http':'403','count':1}])
        line='1.2.3.4 - - [01/Oct/2026:04:00:00 +0000] api.example "POST /api/internal/v1/lake/objects HTTP/1.1" 403 22 0.1 "-" "client" 172.18.0.8:8080 403 0.1 "/api/internal/v1/lake/objects"'
        self.assertEqual(diag.access_facts(line)[0]['upstream_http'],'403')

    def test_policy_missing_and_compatible_intake_grants_are_distinguished(self):
        now=datetime.now(timezone.utc)
        cap={'capabilityId':'datalake.write','requiredScope':'datalake.write','allowedActors':['SERVICE']}
        grant={'capabilityId':'datalake.write','grantId':'id','servicePrincipalId':'ouf-ingestion','tenantId':'lab','validFrom':(now-timedelta(days=1)).isoformat(),'validUntil':(now+timedelta(days=1)).isoformat(),'constraints':{'effect':'ALLOW','resourceType':'ingestion-intake','resourceAttributes':{'module':'UDP'}}}
        claims={'azp':'ouf-ingestion','tenant_id':'lab'}
        stream=io.StringIO()
        with redirect_stdout(stream):diag.policy_facts({'bundle':{'capabilities':[cap],'grants':[grant]}},claims,'P')
        self.assertIn('P_datalake.write_MATCHING_UNRESTRICTED_GRANTS_DIAGNOSTIC=1',stream.getvalue())
        grant['tenantId']='other';stream=io.StringIO()
        with redirect_stdout(stream):diag.policy_facts({'capabilities':[cap],'grants':[grant]},claims,'P')
        self.assertIn('P_datalake.write_MATCHING_UNRESTRICTED_GRANTS_DIAGNOSTIC=0',stream.getvalue())

    def test_section_failure_is_redacted_and_does_not_abort_collection(self):
        stream=io.StringIO()
        with redirect_stdout(stream):diag.section('LOG',lambda:(_ for _ in ()).throw(ValueError('SECRET')))
        self.assertEqual(stream.getvalue(),'DIAGNOSTIC_LOG=UNAVAILABLE TYPE=ValueError\n')

    def test_empty_get_error_is_parsed_without_losing_diagnostics(self):
        with patch.object(diag.helper,'run',return_value='403') as tool:
            self.assertEqual(diag.curl_json('https://api.example/internal/bundle','token'),('403',None))
            self.assertNotIn('token',' '.join(tool.call_args.args[0]))


if __name__=='__main__':unittest.main()
