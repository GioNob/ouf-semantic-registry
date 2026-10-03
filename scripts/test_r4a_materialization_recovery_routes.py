import copy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
import r4a_install_materialization_recovery_routes as route

def args(root,mode='apply'):
    return SimpleNamespace(mode=mode,receipt=root/'receipt.json',template_id='template',template_uri='/publications',
        template_node='onboard:8080',template_scope='config.read',public_host='example.test',udp_node='udp:8080',
        base_path='/jobs',scope='materialization.retry',review_id='review',retry_id='retry')

def baseline():
    return [{'id':'template','uri':'/publications','methods':['GET'],'host':'example.test',
        'upstream':{'nodes':{'onboard:8080':1}},'plugins':{
        'openid-connect':{'bearer_only':True,'required_scopes':['config.read'],'discovery':'https://issuer/discovery',
                          'client_id':'gateway','client_secret':'private-secret'},
        'limit-count':{'count':20,'time_window':60,'key':'remote_addr'},
        'serverless-post-function':{'functions':['old Lua must not survive']}}}]

class Fake:
    def __init__(self,rows,lost=False,drift=False):
        self.values={str(r['id']):copy.deepcopy(r) for r in rows};self.writes=[];self.lost=lost;self.drift=drift
    def rows(self):return copy.deepcopy(list(self.values.values()))
    def unchanged(self):pass
    def api(self,method,path,body=None,accepted=()):
        ident=path.split('/')[-1]
        if method=='GET':return ({'value':self.values[ident]},'200') if ident in self.values else ({},'404')
        self.writes.append((method,ident))
        if method=='PUT':
            self.values[ident]={'id':ident,**copy.deepcopy(body)}
            if self.lost:
                if self.drift:self.values[ident]['desc']='concurrent operator change'
                raise RuntimeError('lost response')
            return {},'201'
        del self.values[ident];return {},'200'

class Routes(unittest.TestCase):
    def test_preserves_security_and_exact_action(self):
        with tempfile.TemporaryDirectory() as folder:
            a=args(Path(folder));wanted=route.desired(baseline(),a)
            for r in wanted.values():
                self.assertEqual(r['plugins']['openid-connect']['client_secret'],'private-secret')
                self.assertEqual(r['plugins']['openid-connect']['required_scopes'],[a.scope])
                self.assertNotIn('old Lua',str(r))
                self.assertIn("actor~='HUMAN'",str(r))
            uuid='12345678-1234-1234-1234-123456789012'
            import re
            self.assertTrue(re.fullmatch(wanted['review']['vars'][0][2],'/jobs/'+uuid))
            self.assertFalse(re.fullmatch(wanted['review']['vars'][0][2],'/jobs/'+uuid+'/retry'))
            self.assertFalse(re.fullmatch(wanted['retry']['vars'][0][2],'/jobs/'+uuid+'/replay'))
    def test_unsafe_template_denied(self):
        with tempfile.TemporaryDirectory() as folder:
            for mutate in (lambda r:r['plugins']['openid-connect'].update(bearer_only=False),
                           lambda r:r['plugins']['limit-count'].update(_meta={'disable':True}),
                           lambda r:r.update(service_id='foreign')):
                rows=baseline();mutate(rows[0])
                with self.assertRaises(route.private.Blocked):route.desired(rows,args(Path(folder)))
    def test_collision_and_inventory_drift_no_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            a=args(Path(folder));rows=baseline()+[{'id':'wildcard','uri':'/*'}];gw=Fake(rows)
            with self.assertRaises(route.private.Blocked):route.execute(a,gw,rows)
            self.assertEqual(gw.writes,[])
            with self.assertRaises(route.private.Blocked):route.execute(a,gw,baseline())
            self.assertEqual(gw.writes,[])
    def test_apply_verify_private_intent_no_reput(self):
        with tempfile.TemporaryDirectory() as folder:
            a=args(Path(folder));rows=baseline();gw=Fake(rows)
            original=route.private.write;intents=[]
            def save(path,state):
                intents.append(copy.deepcopy(state));original(path,state)
            with patch.object(route.private,'write',side_effect=save):route.execute(a,gw,rows)
            self.assertEqual(a.receipt.stat().st_mode&0o777,0o600)
            self.assertTrue(any(s.get('attempted')==['review'] for s in intents))
            self.assertEqual(len(gw.writes),2)
            a.mode='verify';route.execute(a,gw,rows);self.assertEqual(len(gw.writes),2)
            a.mode='apply'
            with self.assertRaises(route.private.Blocked):route.execute(a,gw,rows)
            self.assertEqual(len(gw.writes),2)
    def test_lost_put_response_rolls_back_only_owned(self):
        with tempfile.TemporaryDirectory() as folder:
            import json
            a=args(Path(folder));rows=baseline();gw=Fake(rows,lost=True)
            with self.assertRaises(RuntimeError):route.execute(a,gw,rows)
            self.assertEqual(json.loads(a.receipt.read_text())['status'],'ROLLED_BACK')
            self.assertEqual(route.index(gw.rows()),route.index(rows))
    def test_rollback_drift_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            import json
            a=args(Path(folder));gw=Fake(baseline(),lost=True,drift=True)
            with self.assertRaises(RuntimeError):route.execute(a,gw,baseline())
            self.assertEqual(json.loads(a.receipt.read_text())['status'],'MANUAL_RECOVERY_REQUIRED')
            self.assertEqual(gw.values['review']['desc'],'concurrent operator change')
            self.assertFalse(any(method=='DELETE' for method,_ in gw.writes))

if __name__=='__main__':unittest.main()
