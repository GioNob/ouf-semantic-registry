import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import r4a_semantic_provider_iam_inventory as script


class InventoryTest(unittest.TestCase):
    def test_only_read_commands_and_no_authentication_credentials(self):
        with patch.object(script.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout='[]',stderr='')) as run:
            script.read('custom-iam','/custom/kcadm.sh','custom-realm','clients','clientId',('first=0','max=100'))
            args=run.call_args.args[0]
            self.assertEqual(args[:6],['docker','exec','custom-iam','/custom/kcadm.sh','get','clients'])
            self.assertNotIn('config',args);self.assertNotIn('credentials',args)
    def test_workload_and_scope_inventory_redacts_unexpected_secrets(self):
        def read(c,p,r,resource,fields,queries=()):
            if resource=='client-scopes':return [{'name':'configured.scope','secret':'DO_NOT_PRINT'}]
            return [{'clientId':'custom-service','enabled':True,'publicClient':False,'serviceAccountsEnabled':True,'secret':'DO_NOT_PRINT'},
                {'clientId':'human','serviceAccountsEnabled':False}]
        out=script.inventory('custom-iam','/custom/kcadm.sh','custom-realm',['configured.scope','missing.scope'],read)
        self.assertEqual([r['clientId'] for r in out['workloadClients']],['custom-service'])
        self.assertEqual(out['scopes'],[{'name':'configured.scope','exists':True},{'name':'missing.scope','exists':False}])
        self.assertNotIn('DO_NOT_PRINT',json.dumps(out));self.assertFalse(out['tokenClaimsProven'])
    def test_pagination_does_not_silently_drop_the_next_page(self):
        calls=[]
        def read(c,p,r,resource,fields,queries=()):
            if resource=='client-scopes':return []
            calls.append(queries)
            if queries[0]=='first=0':return [{'clientId':str(i)} for i in range(100)]
            return [{'clientId':'last','serviceAccountsEnabled':True}]
        out=script.inventory('iam','/kcadm.sh','realm',['scope'],read)
        self.assertEqual(len(calls),2);self.assertEqual(out['workloadClients'][0]['clientId'],'last')
    def test_failed_or_expired_session_never_prints_server_output(self):
        for text,code in [('Session has expired. DO_NOT_PRINT','KCADM_SESSION_EXPIRED'),('forbidden DO_NOT_PRINT','KCADM_READ_FAILED')]:
            with patch.object(script.subprocess,'run',return_value=SimpleNamespace(returncode=1,stdout='',stderr=text)):
                with self.assertRaisesRegex(RuntimeError,code) as error:script.read('iam','/kcadm.sh','realm','clients','clientId')
                self.assertNotIn('DO_NOT_PRINT',str(error.exception))
    def test_invalid_bindings_fail_before_any_iam_read(self):
        def read(*args):self.fail('IAM read before validation')
        for container,path,realm,scopes in [('bad/name','/kcadm.sh','realm',['scope']),('iam','/a/../kcadm.sh','realm',['scope']),('iam','/kcadm.sh','realm',[])]:
            with self.assertRaises(RuntimeError):script.inventory(container,path,realm,scopes,read)

if __name__=='__main__':unittest.main()
