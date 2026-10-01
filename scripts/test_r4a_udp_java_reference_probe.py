import argparse
import contextlib
import io
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
import zipfile
import r4a_udp_java_reference_probe as probe

RESOLVER='BOOT-INF/classes/it/comune/trieste/ouf/udp/PublishedRuntimeConfiguration.class'


class JavaProbeTests(unittest.TestCase):
    def jar(self,path,extra=None):
        with zipfile.ZipFile(path,'w') as jar:
            jar.writestr(RESOLVER,b'byte-identical-live-class')
            jar.writestr('BOOT-INF/lib/jackson.jar',b'live-dependency')
            jar.writestr('META-INF/not-extracted','other')
            if extra:jar.writestr(extra,'unsafe')

    def test_extract_preserves_live_class_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.jar(root/'app.jar');probe.extract(root/'app.jar',root)
            self.assertEqual((root/RESOLVER).read_bytes(),b'byte-identical-live-class')
            self.assertFalse((root/'META-INF').exists())

    def test_rejects_archive_escape_before_extract(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.jar(root/'app.jar','BOOT-INF/classes/../../../escaped')
            with self.assertRaises(ValueError):probe.extract(root/'app.jar',root)
            self.assertFalse((root/'BOOT-INF').exists())

    def test_missing_resolver_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with zipfile.ZipFile(root/'app.jar','w') as jar:jar.writestr('BOOT-INF/lib/a.jar','x')
            with self.assertRaises(ValueError):probe.extract(root/'app.jar',root)

    def test_isolation_sql_mounts_and_redaction(self):
        if not hasattr(__import__('os'),'geteuid') or __import__('os').geteuid()!=0:
            self.skipTest('same production root runner required')
        image='sha256:'+'a'*64;compiler='sha256:'+'b'*64
        live={'Image':image,'State':{'Running':True},'Config':{'User':'10004:10004','Env':[
            'OUF_UDP_EXECUTION_GATEWAY_URL=https://gateway.example',
            'OUF_UDP_EXECUTION_TOKEN_FILE=/private/access.jwt','OUF_UDP_TENANT_ID=tenant']}}
        args=argparse.Namespace(run='86809c17-3354-45ca-a7e6-57e903944b24',source='source',
            container='udp',postgres_container='pg',database='db',db_user='user',
            network='backend',jdk_image='jdk:21',jar_path='/app/app.jar')
        sql=[];commands=[]
        def inventory(argv):
            if argv[1]=='inspect':return json.dumps([live])
            if argv[1:3]==['image','inspect']:return json.dumps([{'Id':compiler}])
            sql.append(argv[-1]);return '[{"bundleRef":"private-reference"}]'
        def invoke(argv,timeout=30):
            commands.append(argv)
            if argv[1]=='cp':self.jar(Path(argv[-1]))
            return ''
        def execute(argv,**kwargs):
            commands.append(argv)
            return types.SimpleNamespace(returncode=0,stdout='private-token\nUDP_SHIPPED_JAVA_RESOLVE_CONTRACTS=PASS\n',stderr='private body')
        output=io.StringIO()
        with patch.object(probe.inventory,'run',side_effect=inventory), \
             patch.object(probe.inventory,'mapped',return_value=(Path('/private/access.jwt'),False)), \
             patch.object(probe,'invoke',side_effect=invoke), \
             patch.object(probe.os,'chown') as ownership, \
             patch.object(probe.subprocess,'run',side_effect=execute),contextlib.redirect_stdout(output):
            probe.main(args)
        self.assertEqual(ownership.call_args.args[1:],(10004,10004))
        self.assertIn('begin read only',sql[0]);self.assertIn('rollback;',sql[0])
        compile_cmd=commands[1];java_cmd=commands[2]
        self.assertEqual(compile_cmd[compile_cmd.index('--network')+1],'none')
        self.assertIn(compiler,compile_cmd);self.assertIn(image,java_cmd)
        self.assertIn('type=bind,src=/private,dst=/probe-token,readonly',java_cmd)
        self.assertEqual(java_cmd[java_cmd.index('--user')+1],'10004:10004')
        self.assertNotIn('-e',java_cmd);self.assertIn('--read-only',java_cmd)
        self.assertNotIn('private-token',output.getvalue());self.assertNotIn('private-reference',str(commands))
        self.assertIn('UDP_SHIPPED_JAVA_RESOLVE_CONTRACTS=PASS',output.getvalue())


if __name__=='__main__':unittest.main()
