import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

scripts=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(scripts))
spec=importlib.util.spec_from_file_location('prepare',scripts/'r4a_prepare_semantic_consultation.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class PreparationTest(unittest.TestCase):
    def row(self):
        return {'Id':'a'*64,'Name':'/live','Image':'old','State':{'Running':True},
                'Config':{'User':'10001:10001','Entrypoint':['app'],'Cmd':['server'],'WorkingDir':'/app',
                          'Env':['SECRET=never-command-line'],'Labels':{'org.opencontainers.image.revision':'old'},'Hostname':'original'},
                'HostConfig':{'NetworkMode':'network-one','RestartPolicy':{'Name':'unless-stopped'},
                              'LogConfig':{'Type':'json-file','Config':{}},'IpcMode':'private','ShmSize':67108864,
                              'Memory':1000,'MemorySwap':2000,'MemoryReservation':0,'PidsLimit':None,'ReadonlyRootfs':False},
                'Mounts':[{'Type':'bind','Source':'/private/secret','Destination':'/run/secret','RW':False,'Propagation':'rprivate'}],
                'NetworkSettings':{'Networks':{'network-one':{'Aliases':['live','service-alias','a'*12]}}}}
    def image(self,row):return {'Id':'new-image','Config':copy.deepcopy(row['Config'])}
    def test_clone_command_preserves_resources_aliases_and_secret_file_only(self):
        row=self.row();argv=m.command(row,self.image(row),'candidate',Path('/private/env'),row['Mounts'],'new-pin')
        self.assertNotIn('never-command-line',' '.join(argv))
        self.assertEqual(argv[argv.index('--restart')+1],'no')
        self.assertEqual(argv[argv.index('--memory')+1],'1000')
        self.assertEqual(argv[argv.index('--memory-swap')+1],'2000')
        self.assertIn('service-alias',argv);self.assertIn('live',argv)
        self.assertIn('org.opencontainers.image.revision=new-pin',argv)
        self.assertNotIn('start',argv)
    def test_unsupported_settings_fail_before_create(self):
        for field,value in [('Privileged',True),('PortBindings',{'8080':[]}),('Dns',['1.1.1.1']),('CpuShares',99)]:
            row=self.row();row['HostConfig'][field]=value
            with self.assertRaisesRegex(RuntimeError,'UNSUPPORTED_HOST_SETTING'):m.launch_guard(row,self.image(row))
    def test_inert_clone_checks_mount_env_alias_and_resources(self):
        row=self.row();candidate=copy.deepcopy(row);image=self.image(row)
        candidate['Image']=image['Id'];candidate['State']={'Running':False,'Status':'created'}
        candidate['HostConfig']['RestartPolicy']['Name']='no'
        m.matches(candidate,row,image,m.env(row),row['Mounts'])
        candidate['HostConfig']['MemorySwap']=1
        with self.assertRaisesRegex(RuntimeError,'CANDIDATE_HOST_DRIFT'):m.matches(candidate,row,image,m.env(row),row['Mounts'])
        candidate['HostConfig']['MemorySwap']=2000;candidate['Mounts'][0]['RW']=True
        with self.assertRaisesRegex(RuntimeError,'CANDIDATE_MOUNTS_DRIFT'):m.matches(candidate,row,image,m.env(row),row['Mounts'])
    def test_binding_extraction_and_single_yaml_env_addition(self):
        code='\n'.join('local '+k+' = '+json.dumps(v) for k,v in {'ISSUER':'https://issuer','AUDIENCE':'aud','MCP_WORKLOAD':'workload','DELEGATION_KEY_ENV':'EXISTING_KEY'}.items())
        rows=[{'uri':'/internal/capabilities/v1/execute','plugins':{'serverless-post-function':{'functions':[code]}}}]
        self.assertEqual(m.bindings(rows)['MCP_WORKLOAD'],'workload')
        with self.assertRaisesRegex(RuntimeError,'EXECUTE_TEMPLATE_NOT_UNIQUE'):m.bindings(rows+rows)
        yaml='apisix:\n  key: private\nnginx_config:\n  envs:\n  - EXISTING_KEY\n'
        result=m.patch_yaml(yaml,'NEW_OWNER_KEY')
        self.assertEqual(result.replace('  - NEW_OWNER_KEY\n',''),yaml)
        with self.assertRaisesRegex(RuntimeError,'NGINX_ENV_LAYOUT_UNSUPPORTED'):m.patch_yaml(result,'NEW_OWNER_KEY')
    def test_duplicate_env_fails(self):
        row=self.row();row['Config']['Env'].append('SECRET=another')
        with self.assertRaisesRegex(RuntimeError,'ENV_INVALID'):m.env(row)


if __name__=='__main__':unittest.main()
