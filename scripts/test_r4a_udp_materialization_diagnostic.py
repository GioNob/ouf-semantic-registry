import unittest
from types import SimpleNamespace
import r4a_udp_materialization_diagnostic as diag


class DiagnosticTests(unittest.TestCase):
    def args(self):return SimpleNamespace(run='86809c17-3354-45ca-a7e6-57e903944b24',source='other-source',postgres_container='other-pg',database='other_udp',db_user='other-user')
    def test_query_is_read_only_scoped_and_has_no_payload_projection(self):
        query=diag.query(self.args())
        self.assertIn('begin read only',query);self.assertIn('other-source',query)
        self.assertIn(self.args().run,query)
        for word in ('payload_json','safe_detail','update ','insert ','delete '):self.assertNotIn(word,query)
        self.assertIn('safe_failure_code',query);self.assertIn('missing_ref_count',query)
    def test_injected_scope_and_invalid_run_rejected(self):
        for field,value in [('source',"x' or true--"),('run','bad'),('database','db;cmd')]:
            args=self.args();setattr(args,field,value)
            with self.assertRaises(ValueError):diag.query(args)
    def test_redaction_and_output_allowlist(self):
        ident=self.args().run
        result=diag.sanitize({'jobs':[{'handoff_id':ident,'job_id':ident,'job_state':'QUARANTINED','safe_failure_code':'private raw detail','payload_json':'SECRET'}], 'events':[{'handoff_id':ident,'event_type':'raw private detail','event_count':1,'safe_detail':'SECRET'}]})
        self.assertEqual(result['jobs'][0]['safe_failure_code'],'NON_SYMBOLIC_REDACTED')
        self.assertEqual(result['events'][0]['event_type'],'NON_SYMBOLIC_REDACTED')
        self.assertNotIn('SECRET',str(result))


if __name__=='__main__':unittest.main()
