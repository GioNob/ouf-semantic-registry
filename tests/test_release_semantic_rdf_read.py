import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import r4a_release_semantic_rdf_read as script


class ReleaseTest(unittest.TestCase):
    def run_apply(self,fail=None):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            old={'Id':'old-id','Name':'/ouf-semantic','HostConfig':{'RestartPolicy':{'Name':'unless-stopped','MaximumRetryCount':0}}}
            before={'live':{'ouf-semantic':old}}
            candidate={'id':'new-id','image':script.IMAGE,'name':'candidate'}
            prepared={'candidate':candidate}
            actions=[];history=[{'version':'1','success':True}]
            def switch(role,old,candidate,state,path):
                actions.append('switch');state['switchAttempted'].append(role)
            def verify(*args):
                actions.append('verify')
                if fail=='verify':raise RuntimeError('READINESS_TIMEOUT')
            def backup(*args):
                actions.append('backup')
                if fail=='backup':raise RuntimeError('BACKUP_FAILED')
                return {'tocVerified':True,'restoreToDatabaseTested':False}
            histories=[history,history]
            if fail=='history-before':histories[0]=[]
            if fail=='history-after':histories[1]=[]
            with patch.object(script,'unchanged',side_effect=lambda *a,**kw:actions.append('unchanged')),\
                patch.object(script.release,'backup',side_effect=backup),\
                patch.object(script.release,'history',side_effect=histories),\
                patch.object(script.release,'switch',side_effect=switch),\
                patch.object(script,'verify_new',side_effect=verify),\
                patch.object(script.stage,'run',side_effect=lambda *a,**kw:actions.append('restart')),\
                patch.object(script.stage,'inspect',return_value={'HostConfig':old['HostConfig']}),\
                patch.object(script.release,'restore_container',side_effect=lambda *a:actions.append('restore')),\
                patch.object(script.release,'ready',side_effect=lambda *a:actions.append('old-ready')),\
                contextlib.redirect_stdout(io.StringIO()):
                error=None
                try:script.apply(root,before,{},prepared,{'Id':'pg-id'},'pg-user','db',history,'backup','failed','pg')
                except RuntimeError as exc:error=str(exc)
                receipt=json.loads((root/'rdf-release-receipt.json').read_text())
            return error,receipt,actions
    def test_success_backs_up_before_switch_and_retains_original(self):
        error,receipt,actions=self.run_apply()
        self.assertIsNone(error);self.assertEqual(receipt['status'],'PASS')
        self.assertEqual(receipt['retainedOriginal'],'backup')
        self.assertLess(actions.index('backup'),actions.index('switch'))
        self.assertNotIn('restore',actions)
        self.assertFalse(receipt['backup']['restoreToDatabaseTested'])
    def test_readiness_failure_restores_original_and_requires_reconciliation(self):
        error,receipt,actions=self.run_apply('verify')
        self.assertEqual(error,'READINESS_TIMEOUT')
        self.assertEqual(receipt['status'],'SEMANTIC_RESTORED_RECONCILIATION_REQUIRED')
        self.assertIn('restore',actions);self.assertIn('old-ready',actions)
    def test_backup_failure_never_stops_original(self):
        error,receipt,actions=self.run_apply('backup')
        self.assertEqual(error,'BACKUP_FAILED');self.assertNotIn('switch',actions)
        self.assertNotIn('restore',actions)
        self.assertEqual(receipt['status'],'PRE_SWITCH_FAILED_LIVE_NOT_SWITCHED')
    def test_history_drift_before_switch_blocks_without_rollback(self):
        error,receipt,actions=self.run_apply('history-before')
        self.assertEqual(error,'MIGRATION_CHANGED_BEFORE_SWITCH')
        self.assertNotIn('switch',actions);self.assertNotIn('restore',actions)
    def test_history_drift_after_switch_restores_container_without_db_restore(self):
        error,receipt,actions=self.run_apply('history-after')
        self.assertEqual(error,'MIGRATION_CHANGED_AFTER_SWITCH');self.assertIn('restore',actions)
        self.assertEqual(receipt['status'],'SEMANTIC_RESTORED_RECONCILIATION_REQUIRED')
    def test_packaged_migrations_compare_bytes_not_only_filenames(self):
        with tempfile.TemporaryDirectory() as folder:
            paths=[Path(folder)/n for n in ('old.jar','new.jar')]
            for p,sql in zip(paths,['select 1;','select 2;']):
                with zipfile.ZipFile(p,'w') as jar:jar.writestr('BOOT-INF/classes/db/migration/V1.sql',sql)
            self.assertNotEqual(script.migration_bytes(paths[0]),script.migration_bytes(paths[1]))
            with zipfile.ZipFile(paths[0],'w') as jar:jar.writestr('other','x')
            with self.assertRaisesRegex(RuntimeError,'PACKAGED_MIGRATIONS_EMPTY'):script.migration_bytes(paths[0])
    def test_live_owner_or_route_drift_is_detected(self):
        row={'Id':'x','State':{'Running':True,'StartedAt':'a'},'Config':{},'HostConfig':{},'Mounts':[],'Image':'old'}
        before={'live':{'ouf-semantic':row,'ouf-mcp':row},'gatewayConfig':{},'routes':[{'id':'original'}]}
        with patch.object(script.stage,'inspect',return_value=dict(row,Image='changed')):
            with self.assertRaisesRegex(RuntimeError,'LIVE_CHANGED_SINCE_STAGE'):script.unchanged(before)
        with patch.object(script.stage,'inspect',return_value=row),patch.object(script.stage,'routes',return_value=[]):
            with self.assertRaisesRegex(RuntimeError,'ROUTES_CHANGED_SINCE_STAGE'):script.unchanged(before,semantic=False)
    def test_existing_multimount_contract_is_verified_on_new_live_container(self):
        old={'Id':'old','Name':'/ouf-semantic','HostConfig':{'RestartPolicy':{'Name':'unless-stopped'}}}
        candidate={'id':'new'};mounts=[{'Destination':'/run/ouf-semantic-auth'},{'Destination':'/run/secrets/semantic-read-owner.key'}]
        prepared={'candidate':candidate,'environment':{'secret':'private'},'mounts':mounts}
        row={'Name':'/ouf-semantic','State':{'Running':True},'HostConfig':{'RestartPolicy':{'Name':'no'}}}
        before={'live':{'ouf-semantic':old},'routes':[{'uri':'/internal/capabilities/v1/execute/semantic/'+n} for n in ('search','get')]}
        with patch.object(script.stage,'inspect',side_effect=[row,{'State':{'Running':False}}]),\
            patch.object(script.prep,'matches') as matches,patch.object(script.release,'ready'),\
            patch.object(script.release,'http_code',return_value=403) as probe,patch.object(script,'unchanged'):
            script.verify_new(before,prepared,{})
            self.assertEqual(matches.call_args.args[4],mounts)
            self.assertEqual(probe.call_count,4)
            for call,name in zip(probe.call_args_list[::2],('search','get')):
                self.assertEqual(call.args[3],'/api/internal/v1/semantic/consultation/'+name)
                self.assertEqual(call.args[5],{'Content-Type':'application/json','X-OUF-Semantic-Read-Receipt':'invalid'})
            for call,name in zip(probe.call_args_list[1::2],('search','get')):
                self.assertEqual(call.args[3],'/internal/capabilities/v1/execute/semantic/'+name)
    def test_missing_owner_route_is_not_accepted_as_security_denial(self):
        with patch.object(script.release,'http_code',return_value=404),contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError,'FORGED_DIRECT_REQUEST_NOT_DENIED'):
                script.denial({'routes':[]},'candidate')
    def reconciliation(self,failure=None):
        import copy
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);root=base/'attempt';root.mkdir();retry=base/'retry'
            old={'Id':'old-id','Image':'original','Name':'/ouf-semantic','Config':{},'Mounts':[],
                'HostConfig':{'RestartPolicy':{'Name':'unless-stopped','MaximumRetryCount':0}},
                'State':{'Running':True,'StartedAt':'before'}}
            current=copy.deepcopy(old);current['State']['StartedAt']='after-rollback'
            if failure=='original':current['Image']='unexpected'
            failed={'Id':'new-id','Image':script.IMAGE,'Name':'/ouf-semantic-rdf-read-failed-new-id','State':{'Running':False}}
            history=[{'version':'1','success':True}]
            before={'live':{'ouf-semantic':old,'ouf-mcp':{}},'routes':[]}
            state={'status':'SEMANTIC_RESTORED_RECONCILIATION_REQUIRED','oldId':'old-id','commit':script.PIN,
                'image':script.IMAGE,'candidate':{'id':'new-id'},'postgresId':'pg','history':history}
            (root/'rdf-release-receipt.json').write_text(json.dumps(state))
            (root/'image-receipt.json').write_text(json.dumps({'status':'PASS','commit':script.PIN,'image':script.IMAGE}))
            def inspect(name):return failed if name=='new-id' else current
            error=None
            with patch.object(script,'ROOT',base),patch.object(script.prep,'private'),\
                patch.object(script.stage,'inspect',side_effect=inspect),patch.object(script,'unchanged'),\
                patch.object(script.release,'databases',return_value=({'Id':'pg'},'user',{'semantic':'db'})),\
                patch.object(script.release,'history',return_value=[] if failure=='history' else history),\
                patch.object(script.release,'ready'),patch.object(script,'denial'),contextlib.redirect_stdout(io.StringIO()):
                try:script.reconcile(root,before,{},'pg',retry)
                except RuntimeError as exc:error=str(exc)
            renewed=json.loads((retry/'runtime-snapshot.json').read_text()) if retry.exists() else None
            self.assertEqual(json.loads((root/'rdf-release-receipt.json').read_text()),state)
            return error,renewed
    def test_reconciliation_preserves_failed_receipt_and_rebases_only_verified_restart(self):
        error,renewed=self.reconciliation()
        self.assertIsNone(error)
        self.assertEqual(renewed['live']['ouf-semantic']['Id'],'old-id')
        self.assertEqual(renewed['live']['ouf-semantic']['State']['StartedAt'],'after-rollback')
    def test_reconciliation_blocks_changed_original(self):
        error,renewed=self.reconciliation('original')
        self.assertEqual(error,'ORIGINAL_NOT_EXACTLY_RESTORED');self.assertIsNone(renewed)
    def test_reconciliation_blocks_migration_drift_without_creating_retry(self):
        error,renewed=self.reconciliation('history')
        self.assertEqual(error,'RECONCILIATION_MIGRATION_DRIFT');self.assertIsNone(renewed)

if __name__=='__main__':unittest.main()
