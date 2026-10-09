import contextlib
import io
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import r4a_prepare_semantic_provider_iam as script


class PrepareTest(unittest.TestCase):
    def setup_modules(self,mode='plan',drift=(),scope_drift=()):
        args=SimpleNamespace(mode=mode,realm='custom-realm',client_id='custom-service',audience='custom-audience',tenant='custom-tenant',provider_scope='provider.read',discovery_scope='discovery.request')
        calls=[];scopes={};default=[]
        def inspect(realm,name):return {'exists':name in scopes,'id':scopes.get(name),'drift':list(scope_drift) if name in scopes else ['SCOPE_MISSING']}
        def create(realm,name):calls.append(('create',name));scopes[name]=name+'-id'
        def state(*values):return {'exists':True,'internalId':'existing-id','drift':list(drift)+([] if default else ['REQUIRED_SCOPE_NOT_DEFAULT'])}
        def assign(realm,cid,sid,kind):calls.append(('assign',cid,sid,kind));default.append(sid)
        return args,SimpleNamespace(inspect=inspect,create=create),SimpleNamespace(inspect_state=state),SimpleNamespace(assign=assign),calls,scopes
    def run_prepare(self,*modules):
        with contextlib.redirect_stdout(io.StringIO()) as output:result=script.prepare(*modules)
        return result,output.getvalue()
    def test_plan_allows_missing_scope_and_performs_no_mutations(self):
        a,c,w,b,calls,_=self.setup_modules();result,text=self.run_prepare(a,c,w,b)
        self.assertFalse(result['providerScopeDefault']);self.assertEqual(calls,[])
        self.assertIn('discoveryScopeClientBindingRequested',text)
    def test_apply_creates_definitions_but_binds_only_provider_scope_to_existing_client(self):
        a,c,w,b,calls,scopes=self.setup_modules('apply');self.run_prepare(a,c,w,b)
        self.assertEqual(calls,[('create','provider.read'),('create','discovery.request'),('assign','existing-id','provider.read-id','default')])
        calls.clear();self.run_prepare(a,c,w,b);self.assertEqual(calls,[])
    def test_wrong_workload_profile_blocks_before_any_scope_or_binding_write(self):
        for drift in ('CLIENT_PUBLICCLIENT','MAPPER_DRIFT:ouf-service-actor-type','MAPPER_MISSING:ouf-lab-tenant','CLIENT_MISSING'):
            a,c,w,b,calls,_=self.setup_modules('apply',(drift,))
            with self.assertRaisesRegex(RuntimeError,'PROFILE_REQUIRES_REVIEW'):self.run_prepare(a,c,w,b)
            self.assertEqual(calls,[])
    def test_existing_shared_scope_drift_is_not_silently_repaired(self):
        a,c,w,b,calls,scopes=self.setup_modules('apply',scope_drift=('PROTOCOL',));scopes['provider.read']='id'
        with self.assertRaisesRegex(RuntimeError,'SCOPE_DRIFT_REQUIRES_REVIEW'):self.run_prepare(a,c,w,b)
        self.assertEqual(calls,[])
    def test_verify_is_read_only_and_requires_binding_and_both_scopes(self):
        a,c,w,b,calls,scopes=self.setup_modules('verify')
        with self.assertRaisesRegex(RuntimeError,'VERIFY_FAILED'):self.run_prepare(a,c,w,b)
        self.assertEqual(calls,[])
    def test_composer_uses_existing_helpers_without_adding_mapper_or_secret_operations(self):
        self.assertTrue(hasattr(script.load('provision-keycloak-workload'),'inspect_state'))
        source=Path(script.__file__).read_text()
        for call in ('ensure_mappers(','ensure_client_flags(','write_secret(','create_client('):self.assertNotIn(call,source)

if __name__=='__main__':unittest.main()
