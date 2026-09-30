import unittest
import r4a_cinema_execution_readback as readback

class ExecutionEvidenceTests(unittest.TestCase):
    def evidence(self):
        ing = dict(runs=[{'state':'SUCCEEDED'}], handoffs=[dict(handoff_id=str(i),state='ACKED',receipt_present=True) for i in range(8)], quarantine=0)
        udp = dict(intakes=[dict(handoff_id=str(i),state='PROCESSED') for i in range(8)],jobs=[{'state':'SUCCEEDED'} for i in range(8)],observations=8,open_issues=0,bindings=8,active_objects=8)
        return ing, udp

    def test_eight_matching_delivered_materialized_rows_pass(self):
        self.assertEqual(readback.classify(*self.evidence()), (True,True,True))

    def test_durable_intake_is_not_materialization(self):
        ing, udp = self.evidence()
        udp['intakes'][0]['state'] = 'DURABLE'
        self.assertEqual(readback.classify(ing,udp), (True,True,False))

    def test_same_counts_for_different_handoffs_cannot_pass(self):
        ing, udp = self.evidence()
        udp['intakes'][0]['handoff_id'] = 'another-run'
        self.assertEqual(readback.classify(ing,udp), (False,False,False))

    def test_resolution_issue_prevents_materialization_pass(self):
        ing, udp = self.evidence()
        udp['open_issues'] = 1
        self.assertEqual(readback.classify(ing,udp), (True,True,False))

    def test_quarantined_records_prevent_delivery_pass(self):
        ing, udp = self.evidence()
        ing['quarantine'] = 1
        self.assertEqual(readback.classify(ing,udp), (True,False,False))

if __name__ == '__main__':
    unittest.main()
