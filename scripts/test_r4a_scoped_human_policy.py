import argparse
import copy
import contextlib
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import uuid
import r4a_prepare_scoped_human_policy as policy
import r4a_materialization_recovery_scope as scope


class PolicyTests(unittest.TestCase):
    def fixture(self,root):
        cap={'capabilityId':'module.recover','operation':'COMMAND','requiredScope':'module.recover','allowedActors':['HUMAN']}
        manifest=root/'manifest.json';manifest.write_text(json.dumps([{'ownerRef':'module','descriptor':cap}]))
        resource={'capabilityId':'module.recover','resourceType':'job','resourceId':'exact-job',
                  'resourceAttributes':{'module':'module','sourceRef':'source','jobRef':'run'},'allowedDataLabels':['RESTRICTED']}
        resources=root/'resources.json';resources.write_text(json.dumps([resource]));resources.chmod(0o600)
        args=argparse.Namespace(manifest=manifest,resources=resources,state_file=root/'receipt.json',
            issuer='https://identity.example/realm',client='admin',audience='gateway',admin_scope='policy.admin',
            base_url='https://gateway.example/control',tenant='tenant',subject='human',
            valid_until='2099-01-01T00:00:00Z',validate_only=False)
        old={'bundleId':'policy','version':7,'publishedAt':'2026-10-01T10:00:00Z',
             'capabilities':[{'capabilityId':'existing','operation':'READ','requiredScope':'existing','allowedActors':['SERVICE']}],
             'grants':[{'grantId':'existing-private','capabilityId':'existing','subjectId':'PRIVATE_SUBJECT'}]}
        current={'policyRef':'policy:7','policy':old,'contentHash':'hash','activatedAt':'date'}
        return args,cap,resource,current

    def execute(self,mode='pass'):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);root.chmod(0o700);args,cap,resource,current=self.fixture(root)
            registered=[];posts=[];target=None;draft=str(uuid.uuid4());active_reads=0
            def http(url,token=None,method='GET',body=None,form=None,etag=None):
                nonlocal target,active_reads
                if url.endswith('/policies/active'):
                    active_reads+=1
                    if mode=='drift' and active_reads>=2:return 200,{**current,'policyRef':'policy:8'},{}
                    return 200,copy.deepcopy(current),{}
                if '/capabilities?' in url:
                    if mode=='catalogue-conflict':return 200,[{'capability_id':cap['capabilityId'],'owner_ref':'other','descriptor':cap}],{}
                    return 200,copy.deepcopy(registered),{}
                if method=='POST':
                    saved=json.loads(args.state_file.read_text());posts.append((url,saved['status']))
                    if url.endswith('/capabilities'):
                        self.assertEqual(saved['pendingCapability'],cap['capabilityId'])
                        if mode=='registration-lost':raise TimeoutError('PRIVATE_RESPONSE')
                        registered.append({'capability_id':cap['capabilityId'],'owner_ref':'module','descriptor':cap})
                        return 201,None,{}
                    if url.endswith('/policies'):
                        if mode=='draft-lost':raise TimeoutError('PRIVATE_RESPONSE')
                        target=copy.deepcopy(body);return 200,{'id':draft,'baseActiveRef':current['policyRef'],'state':'DRAFT'},{'ETag':'"0"'}
                    if url.endswith(':preview'):
                        changes=[{'grantId':g['grantId'],'before':None,'after':g} for g in target['grants'][1:]]
                        if mode=='preview-drift':changes[0]['after']={**changes[0]['after'],'tenantId':'other'}
                        return 200,{'addedCapabilities':[cap],'removedCapabilities':[],'grantChanges':changes,
                            'baseActiveRef':current['policyRef'],'draftId':draft,'revision':0,'authoritative':False},{}
                    raise AssertionError('unexpected mutation')
                if url.endswith('/policies/'+draft):return 200,{'policy':target,'baseActiveRef':current['policyRef'],'state':'DRAFT'},{'ETag':'"0"'}
                raise AssertionError('unexpected request')
            output=io.StringIO();error=None
            with patch.object(policy,'http',side_effect=http),patch.object(policy,'login',return_value='PRIVATE_TOKEN'),contextlib.redirect_stdout(output):
                try:policy.prepare(args)
                except Exception as caught:error=caught
                state=json.loads(args.state_file.read_text())
                self.assertEqual(args.state_file.stat().st_mode&0o777,0o600)
                # Receipt must prevent repeat before login or any HTTP call.
                with patch.object(policy,'login') as login,patch.object(policy,'http') as retry_http:
                    with self.assertRaises(policy.Blocked):policy.prepare(args)
                    login.assert_not_called();retry_http.assert_not_called()
            self.assertNotIn('PRIVATE_TOKEN',output.getvalue());self.assertNotIn('PRIVATE_SUBJECT',output.getvalue())
            self.assertNotIn('PRIVATE_RESPONSE',output.getvalue())
            return state,posts,error,current,output.getvalue()

    def test_success_preserves_all_existing_entries_and_never_publishes(self):
        state,posts,error,current,out=self.execute()
        self.assertIsNone(error);self.assertEqual(state['status'],'PASS_UNPUBLISHED')
        self.assertEqual(state['candidate']['capabilities'][:1],current['policy']['capabilities'])
        self.assertEqual(state['candidate']['grants'][:1],current['policy']['grants'])
        grant=state['addedGrants'][0];self.assertEqual(grant['constraints']['resourceId'],'exact-job')
        self.assertEqual(grant['constraints']['allowedDataLabels'],['RESTRICTED'])
        self.assertIsNone(grant['organizationId']);self.assertIsNone(grant['servicePrincipalId'])
        self.assertTrue(all(':publish' not in url for url,status in posts));self.assertIn('ACTIVE_UNCHANGED=true',out)

    def test_uncertain_registration_persists_intent_and_never_blindly_reposts(self):
        state,posts,error,_,_=self.execute('registration-lost')
        self.assertIsInstance(error,TimeoutError);self.assertEqual(len(posts),1)
        self.assertEqual(state['status'],'REGISTRATION_POST_UNVERIFIED_DO_NOT_REPOST')

    def test_uncertain_draft_persists_intent_and_never_blindly_reposts(self):
        state,posts,error,_,_=self.execute('draft-lost')
        self.assertIsInstance(error,TimeoutError);self.assertEqual(len(posts),2)
        self.assertEqual(state['status'],'DRAFT_POST_UNVERIFIED_DO_NOT_REPOST')

    def test_all_catalogue_conflicts_block_before_any_post(self):
        _,posts,error,_,_=self.execute('catalogue-conflict')
        self.assertIsInstance(error,policy.Blocked);self.assertEqual(posts,[])

    def test_active_drift_blocks_before_any_post(self):
        _,posts,error,_,_=self.execute('drift');self.assertIsInstance(error,policy.Blocked);self.assertEqual(posts,[])

    def test_preview_cannot_widen_scoped_grants(self):
        state,posts,error,_,_=self.execute('preview-drift')
        self.assertIsInstance(error,policy.Blocked);self.assertNotEqual(state['status'],'PASS_UNPUBLISHED')
        self.assertFalse(any(':publish' in url for url,status in posts))

    def test_missing_labels_service_actors_and_duplicate_resources_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            args,cap,resource,_=self.fixture(Path(directory))
            for resources in ([{**resource,'allowedDataLabels':[]}],[resource,resource]):
                args.resources.write_text(json.dumps(resources))
                with self.assertRaises(policy.Blocked):policy.inputs(args)
            args.resources.write_text(json.dumps([resource]))
            args.manifest.write_text(json.dumps([{'ownerRef':'module','descriptor':{**cap,'allowedActors':['SERVICE']}}]))
            with self.assertRaises(policy.Blocked):policy.inputs(args)

    def test_expired_grants_and_unrestricted_existing_grants_require_reconciliation(self):
        with tempfile.TemporaryDirectory() as directory:
            args,cap,resource,current=self.fixture(Path(directory))
            args.valid_until='2025-01-01T00:00:00Z'
            with self.assertRaises(policy.Blocked):policy.inputs(args)
            current['policy']['grants'].append({'grantId':'wide','capabilityId':cap['capabilityId']})
            with self.assertRaises(policy.Blocked):policy.candidate(current,{cap['capabilityId']:{'descriptor':cap}},[])

    def test_https_and_redirect_controls(self):
        for url in ('http://example/control','https://user:password@example/control','https://example/control?token=PRIVATE'):
            with self.assertRaises(policy.Blocked):policy.https(url)
        self.assertIsNone(policy.NoRedirect().redirect_request(None,None,302,'',{},'https://other.example'))

    def test_raw_scope_rejects_other_tenants_and_canonical_effects(self):
        job=str(uuid.uuid4());args=argparse.Namespace(job=[job],tenant='tenant',source='source',run='run',capability='recover')
        row={'job_id':job,'tenant_id':'tenant','source_id':'source','ingestion_run_id':'run','raw_source':'source',
            'raw_type':'ROAD','type_code':'ROAD','tier':'RAW','state':'QUARANTINED','intake_state':'DURABLE',
            'safe_failure_code':'UDP_REFERENCE_INTEGRITY_CONTRACT_INVALID','claimed_by':None,'lease_until':None,
            'decision_present':False,'lake_state':'VERIFIED','access_label':'RESTRICTED'}
        actual=scope.resources([row],args)[0]
        self.assertEqual(actual['resourceId'],job);self.assertEqual(actual['allowedDataLabels'],['RESTRICTED'])
        for changed in ({'tenant_id':'other'},{'decision_present':True},{'access_label':''},{'state':'SUCCEEDED'}):
            with self.assertRaises(policy.Blocked):scope.resources([{**row,**changed}],args)


if __name__=='__main__':unittest.main()
