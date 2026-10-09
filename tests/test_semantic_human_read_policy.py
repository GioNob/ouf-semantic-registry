import contextlib
import copy
import io
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import r4a_semantic_human_read_policy as m

SUBJECT='human-admin'
TENANT='tenant-a'


def active():
    search={'grantId':'grant-semantic-search-human-admin','capabilityId':'ouf.semantic.search','tenantId':TENANT,
      'subjectId':SUBJECT,'servicePrincipalId':None,'organizationId':None,'constraints':None,
      'validFrom':'2026-09-18T07:12:50.968730Z','validUntil':'2036-09-15T07:13:50.968730Z'}
    return {'policyRef':'ouf-lab-authorization:37','policy':{'bundleId':'ouf-lab-authorization','version':37,
      'publishedAt':'2026-10-02T08:00:00Z','capabilities':[
      {'capabilityId':'ouf.semantic.read','operation':'READ','requiredScope':'ouf.semantic.read','allowedActors':['SERVICE']},
      {'capabilityId':'ouf.semantic.search','operation':'READ','requiredScope':'ouf.semantic.search','allowedActors':['HUMAN']}],
      'grants':[search,{**search,'grantId':m.OLD,'capabilityId':'ouf.semantic.read'},
      {**search,'grantId':'service-read','capabilityId':'ouf.semantic.read','subjectId':None,'servicePrincipalId':'udp'},
      {**search,'grantId':'compiled:role:admin','constraints':{'externalRoleRef':'admin'}}]}}


class HumanReadPolicyTests(unittest.TestCase):
    def delta(self):return m.candidate(active(),SUBJECT,TENANT)
    def test_exact_delta_preserves_service_and_compiled_role_and_baseline(self):
        baseline=active();before=copy.deepcopy(baseline)
        proposed,added,changes=m.candidate(baseline,SUBJECT,TENANT)
        self.assertEqual(baseline,before)
        self.assertEqual(added,[m.DESCRIPTOR]);self.assertEqual(m.DESCRIPTOR['requiredScope'],'ouf.semantic.read')
        self.assertEqual({c['grantId'] for c in changes},{m.OLD,m.NEW})
        old=m.structure(baseline['policy']);new=m.structure(proposed)
        for cap,descriptor in old['capabilities'].items():self.assertEqual(new['capabilities'][cap],descriptor)
        for ident,grant in old['grants'].items():
            if ident!=m.OLD:self.assertEqual(new['grants'][ident],grant)
        self.assertNotIn(m.OLD,new['grants']);self.assertEqual(new['grants'][m.NEW]['subjectId'],SUBJECT)
    def test_repeating_after_publication_has_no_delta(self):
        proposed,_,_=self.delta()
        again,added,changes=m.candidate({'policyRef':'ouf-lab-authorization:38','policy':proposed},SUBJECT,TENANT)
        self.assertEqual(added,[]);self.assertEqual(changes,[])
        self.assertEqual(m.structure(again),m.structure(proposed))
    def test_native_descriptor_or_old_grant_drift_is_blocked(self):
        for modify in (lambda a:a['policy']['capabilities'][0].update(allowedActors=['HUMAN','SERVICE']),
                       lambda a:a['policy']['grants'][1].update(subjectId='another-human')):
            a=active();modify(a)
            with self.assertRaises(ValueError):m.candidate(a,SUBJECT,TENANT)
    def test_expired_or_other_subject_template_is_blocked(self):
        for field,value in (('validUntil','2020-01-01T00:00:00Z'),('subjectId','other')):
            a=active();a['policy']['grants'][0][field]=value
            with self.assertRaises(ValueError):m.candidate(a,SUBJECT,TENANT)
    def test_owner_preview_allows_only_exact_delta_including_before_values(self):
        _,added,changes=self.delta();p={'addedCapabilities':added,'removedCapabilities':[],'grantChanges':changes}
        m.validate_preview(p,added,changes)
        for altered in ({**p,'removedCapabilities':[active()['policy']['capabilities'][0]]},
                        {**p,'grantChanges':changes+[{'grantId':'service-read','before':None,'after':{}}]},
                        {**p,'addedCapabilities':added+added}):
            with self.assertRaises(ValueError):m.validate_preview(altered,added,changes)
    def test_active_readback_accepts_null_serialization_but_blocks_other_grant_change(self):
        proposed,_,_=self.delta();state={'targetPolicyRef':'ouf-lab-authorization:38','expectedStructureHash':m.policy.digest(m.structure(proposed))}
        readback=copy.deepcopy(proposed)
        readback['grants']=[m.normalized(g) for g in readback['grants']]
        m.verify({'policyRef':state['targetPolicyRef'],'policy':readback},state)
        readback['grants'][0]['subjectId']='different'
        with self.assertRaisesRegex(ValueError,'DELTA_MISMATCH'):m.verify({'policyRef':state['targetPolicyRef'],'policy':readback},state)
    def test_catalogue_existing_contract_reused_and_conflict_blocks(self):
        row={'capability_id':m.CAP,'owner_ref':'semantic','descriptor':{'type':'jsonb','value':json.dumps(m.DESCRIPTOR)}}
        with patch.object(m.policy,'request',return_value=(200,[row],{})) as request:
            self.assertTrue(m.catalogue('https://owner','memory-token'))
            self.assertEqual(len(request.call_args.args),3)
        row['owner_ref']='other'
        with patch.object(m.policy,'request',return_value=(200,[row],{})):
            with self.assertRaisesRegex(ValueError,'CONFLICT'):m.catalogue('https://owner','memory-token')
    def setup_publish(self):
        proposed,added,changes=self.delta()
        state={'draftId':'draft','revision':0,'basePolicyRef':'ouf-lab-authorization:37','targetPolicyRef':'ouf-lab-authorization:38',
          'addedDescriptors':added,'expectedGrantChanges':changes,'expectedStructureHash':m.policy.digest(m.structure(proposed))}
        preview={'draftId':'draft','revision':0,'baseActiveRef':state['basePolicyRef'],'authoritative':False,
          'addedCapabilities':added,'removedCapabilities':[],'grantChanges':changes}
        return proposed,state,preview
    def test_terminal_confirmation_is_required_before_publish(self):
        _,state,preview=self.setup_publish();args=SimpleNamespace(base_url='https://owner',state_file=Path('/private/state'))
        with patch.object(m.policy,'active',return_value=active()),patch.object(m.policy,'request',return_value=(200,preview,{})) as request,patch('builtins.input',return_value=''),contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError,'NOT_CONFIRMED'):m.publish(args,'memory-token',state)
        self.assertEqual(request.call_count,1);self.assertIn(':preview',request.call_args.args[2])
    def test_lost_publish_response_recovers_exact_readback_without_second_publish(self):
        proposed,state,preview=self.setup_publish();args=SimpleNamespace(base_url='https://owner',state_file=Path('/private/state'))
        target={'policyRef':state['targetPolicyRef'],'policy':proposed}
        with patch.object(m.policy,'active',side_effect=[active(),target,target]),patch.object(m.policy,'request',side_effect=[(200,preview,{}),TimeoutError()]) as request,patch.object(m.policy,'write_state'),patch('builtins.input',return_value='PUBBLICA LETTURA SEMANTICA HUMAN'),contextlib.redirect_stdout(io.StringIO()):
            m.publish(args,'memory-token',state)
        self.assertEqual(state['status'],'PUBLISHED');self.assertEqual(request.call_count,2)
    def test_already_published_is_verified_without_preview_or_confirmation(self):
        proposed,state,_=self.setup_publish();args=SimpleNamespace(base_url='https://owner',state_file=Path('/private/state'))
        with patch.object(m.policy,'active',return_value={'policyRef':state['targetPolicyRef'],'policy':proposed}),patch.object(m.policy,'request') as request,patch.object(m.policy,'write_state'),patch('builtins.input') as prompt:
            m.publish(args,'memory-token',state)
        request.assert_not_called();prompt.assert_not_called()
    def test_private_state_contains_no_human_token(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'state.json';m.state_file(path)
            _,state,_=self.setup_publish();m.policy.write_state(path,state)
            self.assertEqual(path.stat().st_mode&0o777,0o600)
            self.assertNotIn('token',path.read_text())

if __name__=='__main__':unittest.main()
