import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('preflight',Path(__file__).resolve().parents[1]/'scripts/r4a_consultation_runtime_preflight.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class PreflightTest(unittest.TestCase):
    def fixture(self):
        return {'Name':'/configured-runtime','Image':'sha256:image','State':{'Running':True},
                'Config':{'Env':['PASSWORD=do-not-print','ISSUER=https://secret-value'],'Labels':{'org.opencontainers.image.revision':'a'*40},'User':'12:12'},
                'HostConfig':{'Privileged':False,'RestartPolicy':{'Name':'unless-stopped'}},
                'NetworkSettings':{'Networks':{'network-one':{}}},
                'Mounts':[{'Source':'/private/source-do-not-print','Destination':'/run/secrets/owner-key','Type':'bind','RW':False}]}
    def test_summary_redacts_values_and_mount_sources(self):
        x=m.summary(self.fixture(),'a'*40);raw=str(x)
        self.assertNotIn('do-not-print',raw);self.assertNotIn('secret-value',raw)
        self.assertEqual(x['environment_names'],['ISSUER','PASSWORD'])
        self.assertEqual(x['mount_targets'][0]['target'],'/run/secrets/owner-key')
    def test_wrong_revision_stopped_or_privileged_fails(self):
        for change in ['revision','running','privileged']:
            x=self.fixture()
            if change=='revision':x['Config']['Labels']['org.opencontainers.image.revision']='b'*40
            if change=='running':x['State']['Running']=False
            if change=='privileged':x['HostConfig']['Privileged']=True
            with self.assertRaises(RuntimeError):m.summary(x,'a'*40)
