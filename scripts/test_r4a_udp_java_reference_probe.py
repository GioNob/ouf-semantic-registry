import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
import zipfile
import r4a_udp_java_reference_probe as probe

RESOLVER='BOOT-INF/classes/it/comune/trieste/ouf/udp/PublishedRuntimeConfiguration.class'


class JavaProbeTests(unittest.TestCase):
    def test_private_umask_keeps_bytecode_readable_and_refs_private(self):
        previous=os.umask(0o077)
        try:self.test_isolation_sql_mounts_and_redaction()
        finally:os.umask(previous)

    def test_jvm_categories_never_return_stderr_values(self):
        self.assertEqual(probe.jvm_failure_category('PRIVATE_TOKEN Could not find or load main class private.name'),
                         'MAIN_CLASS_UNAVAILABLE')
        self.assertEqual(probe.jvm_failure_category('private arbitrary error'),'UNCLASSIFIED')

    def test_candidate_requires_exact_revision_and_same_numeric_identity(self):
        image={'Id':'sha256:'+'b'*64,'Config':{'User':'10004:10004',
            'Labels':{'org.opencontainers.image.revision':'a'*40}}}
        live={'Image':'sha256:'+'c'*64,'Config':{'User':'10004:10004'}}
        args=argparse.Namespace(resolver_image='candidate:tested',expected_revision='a'*40)
        with patch.object(probe.inventory,'run',return_value=json.dumps([image])):
            self.assertEqual(probe.resolver_image(args,live),(image['Id'],'a'*40))
            args.expected_revision='b'*40
            with self.assertRaises(ValueError):probe.resolver_image(args,live)
            args.expected_revision='a'*40;image['Config']['User']='0:0'
        with patch.object(probe.inventory,'run',return_value=json.dumps([image])):
            with self.assertRaises(ValueError):probe.resolver_image(args,live)

    def test_candidate_copy_never_starts_and_removes_only_created_helper_on_failure(self):
        args=argparse.Namespace(container='live',jar_path='/app/app.jar');helper='a'*64;image='sha256:'+'b'*64
        calls=[]
        def execute(argv):
            calls.append(argv)
            if argv[1]=='create':return helper
            if argv[1]=='cp':raise RuntimeError('copy failed')
            return ''
        with patch.object(probe,'invoke',side_effect=execute):
            with self.assertRaises(RuntimeError):probe.copy_jar(args,Path('/private/jar'),image,'c'*40)
        self.assertEqual([c[1] for c in calls],['create','cp','rm'])
        self.assertIn('none',calls[0]);self.assertEqual(calls[-1],['docker','rm',helper])
        self.assertNotIn('live',str(calls))

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
            if 'javac' in argv:
                mount=next(x for x in argv if x.startswith('type=bind,src='))
                root=Path(mount.split('src=',1)[1].split(',dst=',1)[0])
                compiled=root/'probe-classes'/'it'/'ouf';compiled.mkdir(parents=True,mode=0o700)
                (compiled/'Probe.class').write_bytes(b'non-secret-bytecode')
            return ''
        def execute(argv,**kwargs):
            commands.append(argv)
            mount=next(x for x in argv if x.startswith('type=bind,src='))
            root=Path(mount.split('src=',1)[1].split(',dst=',1)[0])
            self.assertEqual((root/'probe-classes').stat().st_mode&0o777,0o755)
            self.assertEqual((root/'probe-classes'/'it').stat().st_mode&0o777,0o755)
            self.assertEqual((root/'probe-classes'/'it'/'ouf').stat().st_mode&0o777,0o755)
            self.assertEqual((root/'probe-classes'/'it'/'ouf'/'Probe.class').stat().st_mode&0o777,0o644)
            self.assertEqual((root/'refs.json').stat().st_mode&0o777,0o600)
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
