import argparse
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import uuid
import r4a_release_udp_recovery as release
import test_r4a_stage_udp_recovery as staging_tests


class ReleaseTests(unittest.TestCase):
    def args(self):
        return argparse.Namespace(postgres_container='pg',database='db',db_user='owner',gateway_container='gw',
            curl_image='curl:tested',health_origin='http://127.0.0.1:8080',health_path='/actuator/health',
            gateway_health_url='http://udp:8080/actuator/health',expected_flyway='34',source='source',
            run=str(uuid.uuid4()),probe_job=str(uuid.uuid4()),expected_job_count=8,expected_succeeded=5,
            expected_quarantined=3,stop_seconds=60,health_attempts=45)

    def run_release(self,mode='pass'):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);root.chmod(0o700);args=self.args()
            live,old_image,image=staging_tests.StageTests().fixture()
            if mode=='enabled-upgrade':live['Config']['Env'].append(release.stage.FLAG+'=true')
            new=copy.deepcopy(live)
            new.update(Id='e'*64,Name='/udp-new',Image=image['Id'])
            new['State']={'Running':False,'Status':'created'};new['HostConfig']['RestartPolicy']={'Name':'no'}
            expected_env=dict(entry.split('=',1) for entry in live['Config']['Env'])
            expected_env[release.stage.FLAG]='true'
            new['Config'].update(Hostname='e'*12,Env=[k+'='+v for k,v in expected_env.items()],
                                 Labels={**image['Config']['Labels'],**live['Config']['Labels']})
            snapshot=root/'snapshot.json';snapshot.write_text(json.dumps(live));snapshot.chmod(0o600)
            staged={'runtime_snapshot':str(snapshot),'runtime_snapshot_hash':release.stage.digest(live),
              'live_id':live['Id'],'candidate_id':new['Id'],'live_name':'udp','candidate_name':'udp-new',
              'candidate_image_id':new['Image'],'revision':'a'*40}
            records={live['Id']:live,new['Id']:new,image['Id']:image,old_image['Id']:old_image,
                     'gw':{'State':{'Running':True}},args.curl_image:image}
            calls=[];raised=False;db_reads=0
            baseline={'schema':[{'version':'34','success':True}], 'original_jobs':[{'job_id':args.probe_job}]}
            def inspect(name):
                if name in records:return copy.deepcopy(records[name])
                for row in (live,new):
                    if row['Name'].lstrip('/')==name:return copy.deepcopy(row)
                raise AssertionError('missing container')
            def docker(*cmd):
                nonlocal raised
                calls.append(cmd)
                if cmd[0]=='ps':return '\n'.join(r['Name'].lstrip('/') for r in (live,new))
                row=records[cmd[-1]] if cmd[0]=='update' else records[cmd[1] if cmd[0] in ('rename','start') else cmd[-1]]
                if cmd[0]=='update':row['HostConfig']['RestartPolicy']={'Name':cmd[cmd.index('--restart')+1]};return ''
                if cmd[0]=='stop':row['State'].update(Running=False,Status='exited',ExitCode=137 if mode=='forced-stop' else 0);return ''
                if cmd[0]=='rename':
                    row['Name']='/'+cmd[2]
                    if mode=='rename-response-lost' and not raised:
                        raised=True;raise RuntimeError('PRIVATE_SECRET_ERROR')
                    return ''
                if cmd[0]=='start':
                    if mode=='manual' and row is live:raise RuntimeError('PRIVATE_SECRET_ERROR')
                    row['State'].update(Running=True,Status='running');return ''
                raise AssertionError(cmd)
            def db_state(args):
                nonlocal db_reads
                db_reads+=1
                if mode=='job-change' and db_reads==3:return {'schema':[], 'original_jobs':[]}
                return baseline
            def health(args,name,attempts):return not (name==new['Id'] and mode in ('health','manual'))
            def status(args,container,url,spoof=False):
                if mode=='auth' and '/governance/' in url:return '200'
                return '403' if '/governance/' in url else '200'
            out=io.StringIO();previous=os.umask(0o077)
            try:
                with patch.object(release.stage,'inspect',side_effect=inspect),patch.object(release.stage,'docker',side_effect=docker), \
                     patch.object(release,'database_state',side_effect=db_state),patch.object(release,'healthy',side_effect=health), \
                     patch.object(release,'status',side_effect=status),patch.object(release,'backup',
                         side_effect=RuntimeError('PRIVATE_SECRET_ERROR') if mode=='backup' else None,
                         return_value={'path':str(root/'backup.dump'),'sha256':'a'*64,'restore_list_valid':True}), \
                     contextlib.redirect_stdout(out):
                    try:release.release(args,staged,root)
                    except (ValueError,RuntimeError):pass
            finally:os.umask(previous)
            receipt=json.loads((root/'release-receipt.json').read_text())
            self.assertNotIn('PRIVATE_SECRET_ERROR',out.getvalue());self.assertNotIn('PRIVATE_TOKEN',out.getvalue())
            self.assertNotIn('PRIVATE_SECRET_ERROR',str(receipt));self.assertNotIn('PRIVATE_TOKEN',str(receipt))
            self.assertFalse(any(c[0] in ('rm','exec') for c in calls))
            return calls,receipt,copy.deepcopy(live),copy.deepcopy(new),out.getvalue()

    def test_switch_retains_old_disabled_and_validated_snapshot(self):
        calls,state,old,new,out=self.run_release()
        self.assertEqual(state['state'],'RELEASED');self.assertIn('RELEASE=PASS',out)
        self.assertFalse(old['State']['Running']);self.assertEqual(old['HostConfig']['RestartPolicy']['Name'],'no')
        self.assertTrue(new['State']['Running']);self.assertEqual(new['Name'],'/udp')
        self.assertEqual(new['HostConfig']['RestartPolicy']['Name'],'unless-stopped')
        self.assertFalse(state['database_restored']);self.assertFalse(state['retry_executed'])

    def assert_rollback(self,mode):
        calls,state,old,new,out=self.run_release(mode)
        self.assertEqual(state['state'],'ROLLED_BACK');self.assertNotIn('RELEASE=PASS',out)
        self.assertTrue(old['State']['Running']);self.assertEqual(old['Name'],'/udp')
        self.assertFalse(new['State']['Running']);self.assertFalse(state['database_restored'])
        return calls

    def test_upgrade_of_enabled_live_preserves_environment_without_requeue(self):
        calls,state,old,new,out=self.run_release('enabled-upgrade')
        self.assertEqual(state['state'],'RELEASED');self.assertIn('RELEASE=PASS',out)
        self.assertEqual(set(old['Config']['Env']),set(new['Config']['Env']))
        self.assertFalse(state['retry_executed']);self.assertFalse(state['database_restored'])

    def test_backup_failure_restores_old_before_any_rename(self):
        calls=self.assert_rollback('backup');self.assertFalse(any(c[0]=='rename' for c in calls))

    def test_health_failure_rolls_back_by_id(self):self.assert_rollback('health')
    def test_anonymous_allow_blocks_release(self):self.assert_rollback('auth')
    def test_original_job_change_blocks_release(self):self.assert_rollback('job-change')
    def test_lost_rename_response_reconciles_ids(self):self.assert_rollback('rename-response-lost')
    def test_forced_stop_blocks_before_backup_switch(self):self.assert_rollback('forced-stop')

    def test_rollback_failure_requires_manual_reconciliation(self):
        _,state,_,_,out=self.run_release('manual')
        self.assertEqual(state['state'],'MANUAL_RECONCILIATION_REQUIRED');self.assertNotIn('RELEASE=PASS',out)

    def test_backup_hash_and_restore_list_without_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            args=self.args();data=b'x'*2048;calls=[]
            def process(argv,**kwargs):
                calls.append(argv)
                if 'pg_dump' in argv:kwargs['stdout'].write(data)
                return None
            with patch.object(release.subprocess,'run',side_effect=process):
                result=release.backup(args,Path(directory))
            self.assertEqual(result['sha256'],hashlib.sha256(data).hexdigest())
            self.assertIn('-l',calls[1]);self.assertNotIn('-d',calls[1])

    def test_database_requires_no_ready_or_running_jobs(self):
        args=self.args();schema=[{'version':'34','success':True}]
        rows=[{'state':'SUCCEEDED' if n<5 else 'QUARANTINED'} for n in range(8)]
        with patch.object(release,'query',side_effect=[json.dumps(schema),json.dumps(rows),'1']):
            with self.assertRaisesRegex(ValueError,'WORKER_NOT_IDLE'):release.database_state(args)

    def test_schema_drift_blocks_before_original_job_query(self):
        with patch.object(release,'query',return_value='[{"version":"35","success":true}]') as query:
            with self.assertRaisesRegex(ValueError,'FLYWAY_CHANGED'):release.database_state(self.args())
            self.assertEqual(query.call_count,1)


if __name__=='__main__':unittest.main()
