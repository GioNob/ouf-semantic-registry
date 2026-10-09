import json
import unittest
from unittest.mock import patch
import r4a_switch_ingestion_iam_candidate as switch


class QuiescenceTests(unittest.TestCase):
    def base(self):
        return {k:0 for k in ('busyRuns','activeSchedules','busyReplays','deliverable')}

    def test_every_active_work_category_blocks_before_publication_read(self):
        for category in self.base():
            with self.subTest(category=category):
                doc=self.base();doc[category]=1
                with patch.object(switch.rollout,'sql',return_value=json.dumps(doc)), patch.object(switch.rollout,'docker') as docker:
                    with self.assertRaisesRegex(RuntimeError,'QUIESCENCE'):
                        switch.snapshot()
                    docker.assert_not_called()

    def test_paused_work_is_retained_and_active_publications_are_allowed(self):
        doc={**self.base(),'runs':[{'state':'PAUSED','control_version':0}], 'quarantine':[{'lifecycle_state':'OPEN','lifecycle_version':0}]}
        publication=[{'active':True,'source_id':'any-tenant-source'}]
        with patch.object(switch.rollout,'sql',return_value=json.dumps(doc)) as sql, patch.object(switch.rollout,'docker',return_value=json.dumps(publication)):
            result=switch.snapshot()
            self.assertEqual(result['runs'],doc['runs'])
            self.assertEqual(result['quarantine'],doc['quarantine'])
            self.assertEqual(result['publications'],publication)
            self.assertIn('processing_attempt',sql.call_args.args[0])
            self.assertIn('checkpoint_json',sql.call_args.args[0])


if __name__=='__main__':unittest.main()
