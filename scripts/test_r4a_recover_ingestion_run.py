import copy
import os
import pty
import select
import signal
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import r4a_recover_ingestion_run as recovery


class GovernedRecoveryTests(unittest.TestCase):
    def test_confirmation_on_real_nonseekable_controlling_terminal(self):
        for answer,wanted in [('RECUPERO test',True),('annullo',False)]:
            with self.subTest(answer=answer):
                pid,fd=pty.fork()
                if pid==0:
                    try:
                        result=recovery.confirmation('RECUPERO test')
                        os._exit(0 if result is wanted else 2)
                    except Exception:
                        os._exit(3)
                completed=False
                try:
                    prompt=b''
                    deadline=time.monotonic()+3
                    while b'\n> ' not in prompt and b'\r\n> ' not in prompt:
                        ready,_,_=select.select([fd],[],[],max(0,deadline-time.monotonic()))
                        self.assertTrue(ready,'TTY prompt not displayed')
                        prompt+=os.read(fd,4096)
                    self.assertIn(b'Per confermare digita RECUPERO test',prompt)
                    os.write(fd,(answer+'\n').encode())
                    while time.monotonic()<deadline:
                        result,status=os.waitpid(pid,os.WNOHANG)
                        if result:
                            completed=True
                            self.assertEqual(os.waitstatus_to_exitcode(status),0)
                            break
                        time.sleep(0.01)
                    self.assertTrue(completed,'TTY confirmation did not finish')
                finally:
                    if not completed:
                        os.kill(pid,signal.SIGKILL)
                        os.waitpid(pid,0)
                    os.close(fd)

    def args(self):
        return SimpleNamespace(api='https://api.example',run='86809c17-3354-45ca-a7e6-57e903944b24',quarantine='7741f1f3-479b-42be-bb0d-a711efb20722')

    def test_only_versioned_retry_and_resume_posts_are_permitted(self):
        correlation='81a9168c-0e83-4eae-aa25-9d72aa817099'
        for action,raw,path in [('retry','204','quarantine/'+self.args().quarantine+'/retry'),('retry','\n204','quarantine/'+self.args().quarantine+'/retry'),('resume','{}\n200','runs/'+self.args().run+'/resume')]:
            with self.subTest(action=action),patch.object(recovery.read.helper,'run',return_value=raw) as run:
                recovery.post(self.args(),action,0,'e30.e30.sig',correlation)
                config=run.call_args.kwargs['input']
                self.assertIn(path,config)
                self.assertIn('expectedVersion',config)
                self.assertNotIn('e30.e30.sig',' '.join(run.call_args.args[0]))
        with self.assertRaisesRegex(RuntimeError,'FORBIDDEN'):
            recovery.post(self.args(),'replay',0,'e30.e30.sig',correlation)

    def test_failure_requires_reconciliation_without_body_disclosure(self):
        with patch.object(recovery.read.helper,'run',return_value='PRIVATE\n409') as run:
            with self.assertRaisesRegex(RuntimeError,'^RECOVERY_RETRY_HTTP_409_RECONCILE_DO_NOT_REPOST$'):
                recovery.post(self.args(),'retry',0,'e30.e30.sig','81a9168c-0e83-4eae-aa25-9d72aa817099')
            self.assertEqual(run.call_count,1)

    def test_initial_state_and_fresh_versions_must_match_read_proof(self):
        expected={'run':{'state':'PAUSED','control_version':0},'quarantine':{'lifecycle_state':'OPEN','lifecycle_version':0}}
        recovery.expect_initial(expected,expected)
        for category,field,value in [('run','control_version',1),('run','state','RUNNING'),('quarantine','lifecycle_state','RETRY_READY'),('quarantine','lifecycle_version',1)]:
            changed=copy.deepcopy(expected);changed[category][field]=value
            with self.subTest(field=field),self.assertRaises(RuntimeError):recovery.expect_initial(changed,expected)


if __name__=='__main__':unittest.main()
