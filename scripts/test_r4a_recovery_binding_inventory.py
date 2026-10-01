import argparse
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import r4a_recovery_binding_inventory as inventory
import r4a_prepare_scoped_human_policy as private


class InventoryTests(unittest.TestCase):
    def args(self,root):
        return argparse.Namespace(gateway_container='other-gateway',keycloak_container='other-iam',
            config_destination='/custom/config.yaml',admin_origin='http://127.0.0.1:9199',curl_image='curl:reviewed',
            udp_node='other-udp:8090',template_node=['other-udp:8090'],review_path='/api/recovery/jobs/job',
            retry_path='/api/recovery/jobs/job/retry',kcadm='/custom/kcadm',realm='other-realm',client='other-client',
            scope='module.recover',snapshot=root/'snapshot.json')

    def test_gateway_reads_with_key_on_stdin_and_never_mutates_or_prints_secret(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);args=self.args(root);config=root/'config.yaml'
            config.write_text('deployment:\n  admin:\n    admin_key:\n    - name: admin\n      key: PRIVATE_ADMIN_KEY\n      role: admin\n')
            live={'Id':'live','Image':'image','State':{'Running':True,'StartedAt':'start'},'Config':{},'HostConfig':{},
                'Mounts':[{'Type':'bind','Source':str(config),'Destination':args.config_destination}]}
            route={'id':'route','uri':'/api/recovery/jobs/*','methods':['GET'],'upstream':{'nodes':{args.udp_node:1}},
                'plugins':{'openid-connect':{'required_scopes':[args.scope],'bearer_only':True,'client_secret':'PRIVATE_CLIENT_SECRET'}}}
            calls=[]
            def run(argv,stdin=None):
                calls.append((argv,stdin));self.assertNotIn('PRIVATE_ADMIN_KEY',str(argv))
                self.assertIn('request = "GET"',stdin);self.assertNotIn('POST',stdin)
                return json.dumps({'list':[{'value':route}]})+'\n200'
            output=io.StringIO()
            with patch.object(inventory,'inspect',return_value=live),patch.object(inventory,'run',side_effect=run),contextlib.redirect_stdout(output):
                snapshot=inventory.gateway(args)
            self.assertEqual(len(calls),1);self.assertEqual(snapshot['routes'],[route])
            self.assertFalse(snapshot['uriRoutingParityProven'])
            self.assertNotIn('PRIVATE_ADMIN_KEY',output.getvalue());self.assertNotIn('PRIVATE_CLIENT_SECRET',output.getvalue())

    def test_iam_reads_are_explicit_and_report_optional_binding(self):
        args=self.args(Path('/unused'));calls=[]
        responses=[[{'name':args.scope,'protocol':'openid-connect','attributes':{'include.in.token.scope':'true'}}],
            [{'id':'client-id','clientId':args.client}],[],[{'name':args.scope}],{'enabled':True}]
        def run(argv,stdin=None):calls.append(argv);return json.dumps(responses.pop(0))
        output=io.StringIO()
        with patch.object(inventory,'run',side_effect=run),contextlib.redirect_stdout(output):result=inventory.iam(args)
        self.assertEqual(result['status'],'PASS_READ_ONLY');self.assertIn('SCOPE_BINDING=OPTIONAL',output.getvalue())
        self.assertTrue(all(cmd[4]=='get' and cmd[-2:]==['-r',args.realm] for cmd in calls))

    def test_missing_or_duplicate_mount_and_remote_clear_http_fail_closed(self):
        with self.assertRaises(private.Blocked):inventory.config_source({'Mounts':[]},'/config')
        with self.assertRaises(private.Blocked):inventory.config_source({'Mounts':[
            {'Type':'bind','Source':'/one','Destination':'/config'},
            {'Type':'bind','Source':'/two','Destination':'/config'}]},'/config')
        args=self.args(Path('/unused'));args.admin_origin='http://external.example:9199'
        with patch.object(inventory,'inspect',return_value={'State':{'Running':True}}),patch.object(inventory,'run') as run:
            with self.assertRaises(private.Blocked):inventory.gateway(args)
            run.assert_not_called()

    def test_one_access_failure_keeps_other_inventory_private_without_claiming_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);root.chmod(0o700);args=self.args(root);output=io.StringIO()
            with patch.object(inventory.os,'geteuid',return_value=0),patch.object(inventory,'gateway',return_value={'status':'PASS_READ_ONLY','private':'PRIVATE_SECRET'}), \
                 patch.object(inventory,'iam',side_effect=RuntimeError('PRIVATE_ERROR')),contextlib.redirect_stdout(output):
                inventory.main(args)
            state=json.loads(args.snapshot.read_text());self.assertEqual(state['status'],'PARTIAL_READ_ONLY')
            self.assertEqual(args.snapshot.stat().st_mode&0o777,0o600)
            self.assertNotIn('PRIVATE_SECRET',output.getvalue());self.assertNotIn('PRIVATE_ERROR',output.getvalue())


if __name__=='__main__':unittest.main()
