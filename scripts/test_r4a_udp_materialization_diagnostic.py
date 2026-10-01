import unittest
import json
from unittest.mock import patch
from types import SimpleNamespace
import r4a_udp_materialization_diagnostic as diag


class DiagnosticTests(unittest.TestCase):
    def test_contract_comparison_projects_counts_not_reference_values(self):
        args=self.args();sql=diag.contract_query(args)
        self.assertIn('group by refs',sql)
        self.assertIn('json_agg(summary',sql)
        self.assertIn('other-source',sql)
        row={'ref_group':1,'total':8,'succeeded':5,'quarantined':3,'refs_object':True,'required_strings_valid':True,'mapping_refs_shape':'array','authority_policy_shape':'string','relationship_refs_shape':'array','raw_ref':'PRIVATE'}
        with patch.object(diag.subprocess,'run',return_value=SimpleNamespace(stdout=json.dumps([row]))),patch('builtins.print') as output:
            diag.contract_compare(args)
            self.assertNotIn('PRIVATE',str(output.call_args_list))
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
