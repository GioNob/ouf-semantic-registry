import copy
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import r4a_udp_lake_profile as target


class ProfileTest(unittest.TestCase):
    def old(self):
        return {'Id':'oldid','Image':'sameimage','State':{'Running':False,'Status':'exited'},
                'Config':{'Env':['TOKEN_SECRET=private','OUF_UDP_RAW_RETENTION_DAYS=0'], 'User':'10004:10004', 'Entrypoint':['java'],'Cmd':['app.jar'],'WorkingDir':'/app'},
                'Mounts':[{'Type':'bind','Source':'/auth','Destination':'/auth','RW':False}],
                'HostConfig':{'NetworkMode':'ouf-backend','LogConfig':{'Type':'json-file','Config':{}},'RestartPolicy':{'Name':'unless-stopped'}},
                'NetworkSettings':{'Networks':{'ouf-backend':{}}}}

    def values(self):
        return target.profile(SimpleNamespace(days=90, retention_class='OPERATIONAL', access_label='RESTRICTED'))

    def test_profile_has_only_the_three_approved_fields(self):
        self.assertEqual(self.values(), {'OUF_UDP_RAW_RETENTION_DAYS':'90','OUF_UDP_RAW_RETENTION_CLASS':'OPERATIONAL','OUF_UDP_RAW_ACCESS_LABEL':'RESTRICTED'})
        with self.assertRaisesRegex(RuntimeError,'PROFILE_INVALID'):
            target.profile(SimpleNamespace(days=0,retention_class='OPERATIONAL',access_label='RESTRICTED'))

    def test_candidate_preserves_secret_and_mounts_and_same_image(self):
        old = self.old()
        candidate = copy.deepcopy(old)
        candidate['Id']='newid'
        candidate['State']['Status']='created'
        candidate['HostConfig']['RestartPolicy']['Name']='no'
        expected = target.lake.environment(old) | self.values()
        candidate['Config']['Env']=[k+'='+v for k,v in expected.items()]
        self.assertTrue(target.candidate_matches(candidate,old,self.values()))
        candidate['Config']['Env']=[x for x in candidate['Config']['Env'] if not x.startswith('TOKEN_SECRET=')]
        self.assertFalse(target.candidate_matches(candidate,old,self.values()))

    def test_running_candidate_is_rejected(self):
        old = self.old()
        candidate=copy.deepcopy(old)
        candidate['State']['Running']=True
        self.assertFalse(target.candidate_matches(candidate,old,self.values()))

    def test_recovery_before_rename_restarts_old_container(self):
        old=self.old()
        with patch.object(target,'optional',return_value=old), patch.object(target.runtime,'inspect',return_value=old), \
             patch.object(target,'docker') as docker, patch.object(target,'health'):
            target.recover({'old':old,'candidateId':'newid'},'previous','failed')
        self.assertEqual([c.args for c in docker.call_args_list], [('update','--restart','unless-stopped','ouf-udp'),('start','ouf-udp')])

    def test_recovery_after_swap_retains_failed_candidate_and_restores_old(self):
        old=self.old()
        new=copy.deepcopy(old)
        new['Id']='newid'
        new['State']['Running']=True
        with patch.object(target,'optional',side_effect=[new,None]), patch.object(target.runtime,'inspect',return_value=old), \
             patch.object(target,'docker') as docker, patch.object(target,'health'):
            target.recover({'old':old,'candidateId':'newid'},'previous','failed')
        self.assertIn(('rename','ouf-udp','failed'),[c.args for c in docker.call_args_list])
        self.assertIn(('rename','previous','ouf-udp'),[c.args for c in docker.call_args_list])

    def test_recovery_rejects_unrelated_live_container(self):
        old=self.old()
        unrelated=copy.deepcopy(old)
        unrelated['Id']='unrelated'
        with patch.object(target,'optional',return_value=unrelated),patch.object(target,'docker') as docker:
            with self.assertRaisesRegex(RuntimeError,'LIVE_ID_MISMATCH'):
                target.recover({'old':old,'candidateId':'newid'},'previous','failed')
        docker.assert_not_called()


if __name__ == '__main__':
    unittest.main()
