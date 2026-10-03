import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import r4a_recover_ingestion_run as recovery


class RecoveryCycleTests(unittest.TestCase):
    def args(self,root):
        return SimpleNamespace(run='86809c17-3354-45ca-a7e6-57e903944b24',quarantine='2fac075e-0862-4ae6-a799-cf63c41b651b',cycle='2fac075e-0862-4ae6-a799-cf63c41b651b',subject='b93d8cf6-cd14-4ee6-91d7-84cd76c4f500',tenant='other-tenant',expected_revision='a'*40,api='https://other.example',issuer='https://auth.other.example/realms/other',client='other-human',audience='other-api',mode='recover',previous_receipt=root/'previous.json',receipt_root=str(root),ingestion_container='other-ingestion',postgres_container='other-db',database='other_runtime',db_user='other_user',network='other-network',curl_image='registry.example/curl:reviewed')

    def current(self,args):
        return {'run':{'run_id':args.run,'state':'PAUSED','control_version':1,'source_id':'source','tenant_id':args.tenant},'quarantine':{'run_id':args.run,'quarantine_id':args.quarantine,'lifecycle_state':'OPEN','lifecycle_version':0}}

    def prior(self,args):
        return {'phase':'RESUME_CONFIRMED','run':args.run,'quarantine':'7741f1f3-479b-42be-bb0d-a711efb20722','subject':args.subject,'tenant':args.tenant,'revision':args.expected_revision,'resumedControlVersion':1}

    def test_paths_are_deterministic_separate_from_legacy_and_wrong_cycle_refused(self):
        with tempfile.TemporaryDirectory() as root,patch.object(recovery.read,'ROOT',Path(root)):
            args=self.args(Path(root));intent,proof=recovery.cycle_paths(args)
            self.assertIn(args.quarantine,intent.name);self.assertIn(args.quarantine,proof.name)
            legacy=copy.copy(args);legacy.cycle=None
            self.assertNotEqual(intent,recovery.cycle_paths(legacy)[0])
            args.cycle='7741f1f3-479b-42be-bb0d-a711efb20722'
            with self.assertRaises(RuntimeError):recovery.cycle_paths(args)

    def test_previous_ambiguous_wrong_actor_same_quarantine_and_version_drift_refused(self):
        with tempfile.TemporaryDirectory() as root,patch.object(recovery.read,'ROOT',Path(root)):
            args=self.args(Path(root));current=self.current(args);prior=self.prior(args)
            for field,value in [('phase','RESUME_REQUESTED_DO_NOT_REPOST'),('subject','wrong'),('quarantine',args.quarantine),('resumedControlVersion',0)]:
                bad={**prior,field:value}
                with self.subTest(field=field),patch.object(recovery,'private',return_value=bad):
                    with self.assertRaises(RuntimeError):recovery.validate_predecessor(args,current)

    def exercise(self,cancel=False,timeout=False):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);root.chmod(0o700);args=self.args(root)
            prior=json.dumps(self.prior(args));args.previous_receipt.write_text(prior);args.previous_receipt.chmod(0o600)
            current=self.current(args);after=copy.deepcopy(current);after['quarantine'].update(lifecycle_state='RETRY_READY',lifecycle_version=1)
            live={'Id':'live','Image':'image','State':{'Running':True}}
            calls=[]
            def post(a,action,version,token,correlation):
                intent=recovery.private(recovery.cycle_paths(args)[0])
                self.assertEqual(intent['phase'],'RETRY_REQUESTED_DO_NOT_REPOST' if action=='retry' else 'RESUME_REQUESTED_DO_NOT_REPOST')
                calls.append((action,version))
                if timeout and action=='resume':raise RuntimeError('simulated_timeout')
                return None if action=='retry' else {'run_id':args.run,'state':'RUNNING','control_version':2}
            def inspect(name,kind='container'):
                if kind=='image':return {'Config':{'Labels':{'org.opencontainers.image.revision':args.expected_revision}}}
                self.assertEqual(name,'other-ingestion');return live
            with patch.object(recovery.os,'geteuid',return_value=0),patch.object(recovery.read.helper,'inspect',side_effect=inspect),patch.object(recovery.read,'login',return_value='token'),patch.object(recovery.read,'claims_check'),patch.object(recovery,'views',side_effect=[current,current,after,after]),patch.object(recovery,'confirmation',return_value=not cancel),patch.object(recovery,'post',side_effect=post):
                if timeout:
                    with self.assertRaisesRegex(RuntimeError,'simulated_timeout'):recovery.main(args)
                else:recovery.main(args)
                intent,proof=recovery.cycle_paths(args)
                self.assertEqual(args.previous_receipt.read_text(),prior)
                if cancel:
                    self.assertFalse(intent.exists());self.assertEqual(calls,[])
                else:
                    self.assertEqual(calls,[('retry',0),('resume',1)])
                    self.assertEqual(recovery.private(intent)['phase'],'RESUME_REQUESTED_DO_NOT_REPOST' if timeout else 'RESUME_CONFIRMED')
                    with self.assertRaisesRegex(RuntimeError,'INTENT_EXISTS'):recovery.main(args)
                self.assertEqual(recovery.private(proof)['quarantineId'],args.quarantine)

    def test_second_cycle_fresh_reads_and_versioned_posts_preserve_predecessor(self):self.exercise()
    def test_cancellation_has_no_intent_or_post(self):self.exercise(cancel=True)
    def test_timeout_retains_resume_intent_and_blocks_repost(self):self.exercise(timeout=True)

    def test_new_cycle_requires_explicit_installation_bindings(self):
        with tempfile.TemporaryDirectory() as root:
            args=self.args(Path(root));args.network=None
            with self.assertRaisesRegex(RuntimeError,'BINDINGS_REQUIRED'):recovery.read.configure(args)

    def test_nonlab_database_network_and_image_bindings_reach_transport(self):
        with tempfile.TemporaryDirectory() as root:
            args=self.args(Path(root));recovery.read.configure(args)
            with patch.object(recovery.read.helper,'run',return_value='{}') as run:
                recovery.read.snapshot(args.run,args.quarantine)
                command=run.call_args.args[0]
                for value in ('other-db','other_user','other_runtime'):self.assertIn(value,command)
            with patch.object(recovery.read.helper,'run',return_value='204') as run:
                recovery.post(args,'retry',0,'e30.e30.sig',args.quarantine)
                command=run.call_args.args[0]
                for value in ('other-network','registry.example/curl:reviewed'):self.assertIn(value,command)
                self.assertNotIn('e30.e30.sig',' '.join(command))

    def tearDown(self):
        recovery.read.ROOT=Path('/etc/ouf/deploy-snapshots');recovery.read.RUNTIME={}
        recovery.read.SCOPES={'ingestion.run.read','ingestion.quarantine.read'}


if __name__=='__main__':unittest.main()
