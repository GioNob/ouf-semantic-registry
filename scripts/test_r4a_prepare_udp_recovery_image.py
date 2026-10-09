import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
import r4a_prepare_udp_recovery_image as build


class BuildTests(unittest.TestCase):
    def args(self,parent):
        return argparse.Namespace(repository='https://example.test/owner/udp.git',revision='a'*40,
            baseline_revision='b'*40,container='udp-live',expected_live_image='sha256:'+'c'*64,
            image_repository='udp-candidate',work_parent=str(parent))

    def run_build(self,mode='success'):
        with tempfile.TemporaryDirectory() as directory:
            args=self.args(Path(directory));calls=[];output=io.StringIO()
            live={'Id':'live-id','Image':args.expected_live_image,'Config':{'User':'10004:10004'},
                  'State':{'Running':True,'StartedAt':'original-start'},'RestartCount':0}
            reads=0
            def execute(argv,log,cwd=None,timeout=60):
                nonlocal reads
                calls.append(argv)
                if argv[:2]==['docker','inspect']:
                    reads+=1
                    if mode=='live-change' and reads>1:live['State']['StartedAt']='changed'
                    return json.dumps([live])
                if argv[:3]==['git','rev-parse','HEAD']:return 'd'*40 if mode=='checkout' else args.revision
                if argv[:3]==['docker','image','inspect']:
                    return json.dumps([{'Id':'sha256:'+'e'*64,'Config':{'User':'10004:10004',
                      'Labels':{'org.opencontainers.image.revision':args.revision}}}])
                return ''
            def process(argv,**kwargs):
                calls.append(argv)
                if mode=='build-failure':raise RuntimeError('PRIVATE_SECRET_ERROR')
                return types.SimpleNamespace(returncode=0)
            values=[{'V1.sql':'original'},{'V1.sql':'changed' if mode=='migration' else 'original'}]
            with patch.object(build,'execute',side_effect=execute),patch.object(build,'migrations',side_effect=values), \
                 patch.object(build.subprocess,'run',side_effect=process),patch.object(build.os,'geteuid',return_value=0), \
                 patch.object(build,'validate'),contextlib.redirect_stdout(output):
                try:build.main(args)
                except (ValueError,RuntimeError):pass
            receipt=json.loads(next(Path(directory).glob('*/receipt.json')).read_text())
            self.assertNotIn('PRIVATE_SECRET_ERROR',output.getvalue())
            self.assertNotIn('PRIVATE_SECRET_ERROR',str(receipt))
            return calls,receipt,output.getvalue()

    def test_isolated_build_receipt_and_no_live_mutation(self):
        calls,receipt,out=self.run_build()
        self.assertEqual(receipt['state'],'BUILT');self.assertIn('BUILD=PASS',out)
        self.assertEqual([c[1] for c in calls if c[0]=='docker'],['inspect','build','image','inspect'])
        command=next(c for c in calls if c[:2]==['docker','build'])
        self.assertNotIn('--build-arg',command);self.assertNotIn('--secret',command)
        self.assertFalse(receipt['service_switched']);self.assertFalse(receipt['probe_executed'])

    def test_revision_mismatch_blocks_before_build(self):
        calls,receipt,_=self.run_build('checkout')
        self.assertEqual(receipt['state'],'BLOCKED');self.assertFalse(any(c[:2]==['docker','build'] for c in calls))

    def test_migration_drift_blocks_before_build(self):
        calls,receipt,_=self.run_build('migration')
        self.assertEqual(receipt['state'],'BLOCKED');self.assertFalse(any(c[:2]==['docker','build'] for c in calls))

    def test_concurrent_live_restart_invalidates_receipt(self):
        _,receipt,out=self.run_build('live-change')
        self.assertEqual(receipt['state'],'BLOCKED');self.assertNotIn('BUILD=PASS',out)

    def test_build_failure_retains_safe_receipt(self):
        _,receipt,out=self.run_build('build-failure')
        self.assertEqual(receipt['state'],'BLOCKED');self.assertEqual(receipt['failure_type'],'RuntimeError')
        self.assertNotIn('BUILD=PASS',out)

    def test_migration_hash_uses_exact_bytes(self):
        data=b'  select 1;\n\n'
        with patch.object(build,'execute',return_value='src/main/resources/db/migration/V1.sql'), \
             patch.object(build.subprocess,'run',return_value=types.SimpleNamespace(stdout=data)):
            result=build.migrations(Path('/source'),'a'*40,io.StringIO())
        self.assertEqual(next(iter(result.values())),hashlib.sha256(data).hexdigest())

    def test_validation_rejects_credentials_and_writable_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            args=self.args(Path(directory));args.repository='https://secret@example.test/udp'
            with self.assertRaises(ValueError):build.validate(args)
            args.repository='https://example.test/udp';Path(directory).chmod(0o777)
            with self.assertRaises(ValueError):build.validate(args)


if __name__=='__main__':unittest.main()
