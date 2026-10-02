import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

scripts=Path(__file__).resolve().parents[1]/'scripts';sys.path.insert(0,str(scripts))
spec=importlib.util.spec_from_file_location('release',scripts/'r4a_release_semantic_consultation.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class Gateway:
    def __init__(self):
        self.original={'id':'upload','uri':'/upload','plugins':{'oidc':{'secret':'private'}}}
        self.data={'upload':copy.deepcopy(self.original)};self.calls=[];self.lose_put=None;self.lose_delete=None
    def rows(self):return copy.deepcopy(list(self.data.values()))
    def api(self,method,path,body=None,statuses=(200,)):
        ident=path.split('/')[-1];self.calls.append((method,ident))
        if method=='GET':return ({'value':copy.deepcopy(self.data[ident])},200) if ident in self.data else ({},404)
        if method=='PUT':
            self.data[ident]={'id':ident,**copy.deepcopy(body)}
            if ident==self.lose_put:raise TimeoutError('response lost')
            return {'value':self.data[ident]},201
        if method=='DELETE':
            self.data.pop(ident)
            if ident==self.lose_delete:raise TimeoutError('response lost')
            return {},200
        raise AssertionError(method)


class ReleaseTest(unittest.TestCase):
    def wanted(self):return {'search':{'uri':'/semantic/search'},'get':{'uri':'/semantic/get'}}
    def test_uncertain_put_reconciled_by_read_then_only_new_routes_deleted(self):
        gateway=Gateway();baseline=gateway.rows();state={'routesAttempted':[]};wanted=self.wanted()
        gateway.lose_put='get'
        with patch.object(m.prep,'checkpoint') as save:
            with self.assertRaises(TimeoutError):m.install_routes(gateway,baseline,wanted,state,Path('/private'))
            self.assertEqual(save.call_count,2)
        self.assertEqual(state['routesAttempted'],['search','get'])
        m.delete_routes(gateway,baseline,wanted,state['routesAttempted'])
        self.assertEqual(gateway.rows(),baseline)
        self.assertNotIn(('PUT','upload'),gateway.calls);self.assertNotIn(('DELETE','upload'),gateway.calls)
        self.assertEqual(gateway.calls.count(('PUT','get')),1)
    def test_route_ownership_drift_blocks_delete(self):
        gateway=Gateway();baseline=gateway.rows();wanted=self.wanted()
        gateway.data['search']={'id':'search','uri':'/other-owner'}
        with self.assertRaisesRegex(RuntimeError,'ROLLBACK_ROUTE_OWNERSHIP_DRIFT'):m.delete_routes(gateway,baseline,wanted,['search'])
        self.assertNotIn(('DELETE','search'),gateway.calls)
    def test_lost_delete_response_accepted_only_after_404_readback(self):
        gateway=Gateway();baseline=gateway.rows();wanted=self.wanted()
        gateway.data['search']={'id':'search',**wanted['search']};gateway.lose_delete='search'
        m.delete_routes(gateway,baseline,wanted,['search'])
        self.assertEqual(gateway.calls.count(('DELETE','search')),1)
        self.assertEqual(gateway.rows(),baseline)
    def test_unrelated_route_change_prevents_installation(self):
        gateway=Gateway();baseline=gateway.rows();gateway.data['upload']['plugins']={}
        with self.assertRaisesRegex(RuntimeError,'EXISTING_ROUTES_DRIFT'):m.install_routes(gateway,baseline,self.wanted(),{'routesAttempted':[]},Path('/private'))
        self.assertFalse(any(method=='PUT' for method,_ in gateway.calls))
    def test_container_rollback_by_id_survives_lost_rename_reply(self):
        original={'Id':'old','Name':'/live','Image':'old-image','Config':{},'HostConfig':{'RestartPolicy':{'Name':'unless-stopped'}},'Mounts':[],'State':{'Running':True,'StartedAt':'old-start'}}
        old=copy.deepcopy(original);old['Name']='/retained';old['State']['Running']=False;old['HostConfig']['RestartPolicy']['Name']='no'
        new=copy.deepcopy(original);new.update(Id='new',Image='new-image');rows={'old':old,'new':new};calls=[]
        def run(argv,*args,**kwargs):
            calls.append(argv);action=argv[1];ident=argv[-1] if action!='rename' else argv[-2]
            if action=='rename':
                rows[ident]['Name']='/'+argv[-1]
                raise TimeoutError('committed rename response lost')
            if action in ('start','stop'):rows[ident]['State']['Running']=action=='start'
            if action=='update':rows[ident]['HostConfig']['RestartPolicy']['Name']=argv[3]
            return ''
        with patch.object(m.stage,'inspect',side_effect=lambda ident:copy.deepcopy(rows[ident])),patch.object(m.stage,'run',side_effect=run):
            m.restore_container(original,{'id':'new'},'failed')
        self.assertEqual(rows['old']['Name'],'/live');self.assertTrue(rows['old']['State']['Running'])
        self.assertFalse(rows['new']['State']['Running']);self.assertEqual(rows['new']['Name'],'/failed')
        self.assertEqual(rows['old']['HostConfig']['RestartPolicy']['Name'],'unless-stopped')
        self.assertFalse(any('rm' in c or 'pg_restore' in c for c in calls))
    def test_probe_is_bounded_read_and_never_authoritative(self):
        for name in ('search','get'):
            body=json.loads(m.probe_body(name))
            self.assertEqual(body['Owner'],'semantic');self.assertIn(body['OperationClass'],('SEARCH','READ'))
            self.assertEqual(body['MaxResultBytes'],262144)
            self.assertNotIn('approve',body['CapabilityID'])
    def existing(self):
        gateway=Gateway()
        for name in ('search','get'):
            gateway.data[name]={'id':name,'uri':'/semantic/'+name,'operation':'OLD'}
        return gateway,gateway.rows(),{name:{'uri':'/semantic/'+name,'operation':'READ'} for name in ('search','get')}
    def test_existing_routes_updated_and_exact_originals_restored_without_delete(self):
        gateway,baseline,wanted=self.existing();state={'routesAttempted':[]}
        with patch.object(m.prep,'checkpoint'):
            m.install_routes(gateway,baseline,wanted,state,Path('/private'))
        m.readback(gateway,baseline,wanted,['search','get'])
        m.delete_routes(gateway,baseline,wanted,state['routesAttempted'])
        self.assertEqual(m.index(gateway.rows()),m.index(baseline))
        self.assertFalse(any(verb=='DELETE' or ident=='upload' and verb=='PUT' for verb,ident in gateway.calls))
    def test_lost_existing_put_response_restores_both_originals(self):
        gateway,baseline,wanted=self.existing();state={'routesAttempted':[]};gateway.lose_put='get'
        with patch.object(m.prep,'checkpoint'):
            with self.assertRaises(TimeoutError):m.install_routes(gateway,baseline,wanted,state,Path('/private'))
        # Restoration PUT may itself lose its response; exact GET readback resolves it.
        m.delete_routes(gateway,baseline,wanted,state['routesAttempted'])
        self.assertEqual(m.index(gateway.rows()),m.index(baseline))
        self.assertFalse(any(verb=='DELETE' for verb,_ in gateway.calls))
    def test_third_party_change_blocks_existing_route_restore(self):
        gateway,baseline,wanted=self.existing()
        gateway.data['search']={'id':'search','uri':'/third-party'}
        with self.assertRaisesRegex(RuntimeError,'ROLLBACK_ROUTE_OWNERSHIP_DRIFT'):
            m.delete_routes(gateway,baseline,wanted,['search'])
        self.assertFalse(any(verb in ('PUT','DELETE') for verb,_ in gateway.calls))
    def test_read_probe_matches_corrected_route_contract(self):
        self.assertEqual(json.loads(m.probe_body('search','READ'))['OperationClass'],'READ')


if __name__=='__main__':unittest.main()
