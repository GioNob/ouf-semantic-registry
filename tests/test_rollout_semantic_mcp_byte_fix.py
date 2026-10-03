from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import r4a_rollout_semantic_mcp_byte_fix as m

class LauncherTests(unittest.TestCase):
    def receipt(self):
        return {'snapshot':'/private/snapshot','candidate':'/private/candidate','tag':'pinned-image','image':'sha256:fixture',
          'backupName':'ouf-mcp-r4a-rollback-fixture','options':{'upload_mode':'picker','picker_url':'https://api.test/trusted-human/managed-files/','host_origin':None}}
    def test_plan_preserves_picker_and_never_requests_apply(self):
        argv=m.launcher_arguments(self.receipt())
        self.assertNotIn('--apply',argv);self.assertNotIn('--rollback',argv)
        self.assertEqual(argv[argv.index('--upload-mode')+1],'picker')
        self.assertEqual(argv[argv.index('--picker-url')+1],self.receipt()['options']['picker_url'])
    def test_apply_has_exact_same_bindings_as_plan(self):
        self.assertEqual(m.launcher_arguments(self.receipt(),True),m.launcher_arguments(self.receipt())+['--apply'])
    def test_other_modes_do_not_invent_picker_or_host_origin(self):
        for mode in ('off','probe','enabled'):
            receipt=self.receipt();receipt['options'].update(upload_mode=mode,picker_url=None)
            argv=m.launcher_arguments(receipt)
            self.assertNotIn('--picker-url',argv);self.assertNotIn('--host-origin',argv)

if __name__=='__main__':unittest.main()
