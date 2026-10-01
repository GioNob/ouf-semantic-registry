import argparse
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import r4a_stage_udp_recovery as stage


class StageTests(unittest.TestCase):
    def fixture(self):
        image={'Id':'sha256:'+'b'*64,'Config':{'User':'10004:10004','Entrypoint':['java','-jar','/app/app.jar'],
          'WorkingDir':'/app','StopSignal':'SIGTERM','Labels':{'org.opencontainers.image.revision':'a'*40}}}
        old=copy.deepcopy(image);old['Id']='sha256:'+'c'*64;old['Config']['Labels']={}
        live={'Id':'d'*64,'Name':'/udp','Image':old['Id'],'RestartCount':0,
          'State':{'Running':True,'StartedAt':'start'},'Config':copy.deepcopy(old['Config']),
          'HostConfig':{'NetworkMode':'separate-network','ShmSize':67108864,'IpcMode':'private','Runtime':'runc',
            'RestartPolicy':{'Name':'unless-stopped'},'LogConfig':{'Type':'json-file','Config':{'max-size':'10m'}}},
          'NetworkSettings':{'Networks':{'separate-network':{'Aliases':['udp','d'*12]}}},
          'Mounts':[{'Type':'bind','Source':'/private/tokens','Destination':'/tokens','RW':False,'Propagation':'rprivate'}]}
        live['Config'].update(Hostname='d'*12,Env=['SECRET=PRIVATE_TOKEN','TENANT=other-tenant'],Labels={'installation':'custom'})
        return live,old,image

    def run_stage(self,mode='pass'):
        with tempfile.TemporaryDirectory() as directory:
            parent=Path(directory);live,old,image=self.fixture();calls=[];candidate=None;live_reads=0
            args=argparse.Namespace(container='udp',candidate_container='udp-new',work_parent=str(parent),
                                    build_receipt=str(parent/'build.json'))
            receipt={'state':'BUILT','service_switched':False,'revision':'a'*40,'image_id':image['Id'],
                     'live_before':{'id':live['Id'],'image':live['Image']}}
            Path(args.build_receipt).write_text(json.dumps(receipt));Path(args.build_receipt).chmod(0o600)
            if mode=='unsupported':live['HostConfig']['Dns']=['10.1.2.3']
            def inspect(name):
                nonlocal live_reads
                if name=='udp':
                    live_reads+=1;value=copy.deepcopy(live)
                    if mode=='live-change' and live_reads>1:value['RestartCount']=1
                    return value
                if name==image['Id']:return image
                if name==old['Id']:return old
                if name=='e'*64:return copy.deepcopy(candidate)
                raise AssertionError('unexpected inspection')
            def docker(*cmd):
                nonlocal candidate
                calls.append(cmd)
                if cmd[0]=='ps':return 'udp\nudp-new' if mode=='exists' else 'udp'
                if cmd[0]=='create':
                    envfile=Path(cmd[cmd.index('--env-file')+1]);self.assertEqual(envfile.stat().st_mode&0o777,0o600)
                    candidate=copy.deepcopy(live);candidate.update(Id='e'*64,Image=image['Id'])
                    candidate['State']={'Running':False,'Status':'created'}
                    candidate['HostConfig']['RestartPolicy']={'Name':'no'}
                    candidate['Config']['Env']=envfile.read_text().splitlines()
                    candidate['Config']['Labels']={**image['Config']['Labels'],**live['Config']['Labels']}
                    if mode=='readback':candidate['Config']['Env'].append('UNEXPECTED=wrong')
                    if mode=='started':candidate['State']['Running']=True
                    return 'e'*64
                if cmd[0]=='rm':return 'e'*64
                raise AssertionError('unexpected Docker mutation')
            output=io.StringIO()
            with patch.object(stage,'inspect',side_effect=inspect),patch.object(stage,'docker',side_effect=docker), \
                 patch.object(stage.os,'geteuid',return_value=0),patch.object(stage,'private_file'), \
                 contextlib.redirect_stdout(output):
                try:stage.main(args)
                except ValueError:pass
            receipts=list(parent.glob('udp-recovery-stage-*/receipt.json'))
            state=json.loads(receipts[0].read_text()) if receipts else None
            if receipts:
                self.assertEqual(receipts[0].stat().st_mode&0o777,0o600)
                root=receipts[0].parent
                self.assertEqual(root.stat().st_mode&0o777,0o700)
                self.assertEqual((root/'runtime-private.json').stat().st_mode&0o777,0o600)
                self.assertFalse((root/'candidate.env').exists())
            self.assertNotIn('PRIVATE_TOKEN',output.getvalue());self.assertNotIn('PRIVATE_TOKEN',str(state))
            return calls,state,output.getvalue()

    def test_preserves_environment_mounts_and_custom_labels_without_start(self):
        calls,state,out=self.run_stage()
        self.assertEqual(state['state'],'STAGED');self.assertIn('STAGE=PASS',out)
        self.assertFalse(state['service_switched']);self.assertFalse(state['database_backup_taken'])
        self.assertEqual([c[0] for c in calls],['ps','create'])
        command=calls[1];self.assertEqual(command[command.index('--restart')+1],'no')
        self.assertIn('installation=custom',command);self.assertNotIn('PRIVATE_TOKEN',str(calls))
        self.assertIn('type=bind,src=/private/tokens,dst=/tokens,bind-propagation=rprivate,readonly',command)

    def test_unsupported_binding_blocks_before_creation(self):
        calls,state,_=self.run_stage('unsupported');self.assertEqual(calls,[]);self.assertIsNone(state)

    def test_existing_name_is_never_overwritten(self):
        calls,state,_=self.run_stage('exists');self.assertEqual([c[0] for c in calls],['ps']);self.assertIsNone(state)

    def test_bad_readback_removes_only_created_stopped_id(self):
        calls,state,out=self.run_stage('readback')
        self.assertEqual(state['state'],'BLOCKED');self.assertEqual(calls[-1],('rm','e'*64));self.assertNotIn('STAGE=PASS',out)

    def test_live_restart_blocks_and_preserves_live(self):
        calls,state,_=self.run_stage('live-change')
        self.assertEqual(state['state'],'BLOCKED');self.assertEqual(calls[-1],('rm','e'*64))
        self.assertFalse(any('udp' in c and c[0]=='rm' for c in calls))

    def test_unexpectedly_started_candidate_is_retained_for_reconciliation(self):
        calls,state,_=self.run_stage('started')
        self.assertEqual(state['state'],'BLOCKED');self.assertFalse(any(c[0]=='rm' for c in calls))

    def test_private_receipt_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/'receipt';file.write_text('{}');file.chmod(0o644)
            with self.assertRaises(ValueError):stage.private_file(file)


if __name__=='__main__':unittest.main()
