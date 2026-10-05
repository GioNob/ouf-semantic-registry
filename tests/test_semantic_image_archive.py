import copy
from unittest.mock import patch
import gzip
import importlib.util
import io
import json
import os
import subprocess
import tempfile
from pathlib import Path
import tarfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('archive_verifier',ROOT/'tools/verify_semantic_image_archive.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def tar(entries):
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w') as archive:
        for name,raw,kind,mode in entries:
            info=tarfile.TarInfo(name);info.mode=mode
            if kind=='directory':info.type=tarfile.DIRTYPE
            elif kind=='symlink':info.type=tarfile.SYMTYPE;info.linkname='/outside'
            else:info.size=len(raw)
            archive.addfile(info,io.BytesIO(raw) if kind=='file' else None)
    return stream.getvalue()

def fixture(compressed=False,entries=None,extra_layers=None):
    payload={'app/tools/file'+str(i)+'.py':m.digest(('code'+str(i)).encode()) for i in range(5)}
    metadata=dict(user='10006:10006',sourceCommit='a'*40,payloadHash='b'*64)
    entries=entries if entries is not None else [('app',b'','directory',0o555),('app/tools',b'','directory',0o555)]+[
        (name,('code'+str(i)).encode(),'file',0o444) for i,name in enumerate(payload)]
    layers=[tar(entries)]+[tar(e) for e in (extra_layers or [])]
    blobs=[gzip.compress(raw) if compressed else raw for raw in layers]
    cfg=dict(os='linux',architecture='amd64',rootfs={'type':'layers','diff_ids':['sha256:'+m.digest(x) for x in layers]},
        config={'User':'10006:10006','WorkingDir':'/app','Entrypoint':['python3','-B','-m','tools.semantic_provider_adapter'],
            'Labels':{'org.opencontainers.image.revision':'a'*40,'ouf.component':'semantic-provider-transport','ouf.payload.sha256':'b'*64},
            'Env':['PRIVATE_IMAGE_SENTINEL=DO_NOT_PRINT']})
    raw=json.dumps(cfg,sort_keys=True).encode();image='sha256:'+m.digest(raw)
    config_name='blobs/sha256/'+m.digest(raw)
    names=['blobs/sha256/'+m.digest(x) for x in blobs]
    manifest=[{'Config':config_name,'Layers':names,'RepoTags':[]}]
    members=[(config_name,raw,'file',0o644)]+[(n,b,'file',0o644) for n,b in zip(names,blobs)]+[
        ('manifest.json',json.dumps(manifest).encode(),'file',0o644)]
    return tar(members),image,payload,metadata,members,cfg

class Tests(unittest.TestCase):
    def verify(self,data,image,payload=None,metadata=None,budget=None):
        return m.archive_verify(io.BytesIO(data),image,budget or m.Budget(),payload,metadata)

    def test_raw_and_gzip_bytes_and_payload_without_extraction(self):
        for compressed in (False,True):
            data,image,payload,meta,_,_=fixture(compressed)
            result=self.verify(data,image,payload,meta)
            self.assertEqual(result['archiveSha256'],m.digest(data))
            self.assertTrue(result['adapterPayloadVerified']);self.assertEqual(result['archiveFilesExtracted'],0)
            self.assertFalse(result['acceptanceGranted']);self.assertFalse(result['imagePublisherProvenanceVerified'])
            self.assertNotIn('SENTINEL',json.dumps(result))

    def test_config_image_hash_and_layer_hash_drift(self):
        data,image,payload,meta,members,cfg=fixture()
        with self.assertRaises(ValueError):self.verify(data,'sha256:'+'f'*64,payload,meta)
        members[1]=(members[1][0],members[1][1].replace(b'code0',b'evil0'),*members[1][2:])
        with self.assertRaises(ValueError):self.verify(tar(members),image,payload,meta)

    def test_diff_id_drift_even_with_valid_encoded_blob_hash(self):
        _,image,payload,meta,members,cfg=fixture()
        blob=tar([('unexpected',b'different','file',0o644)])
        members[1]=('blobs/sha256/'+m.digest(blob),blob,'file',0o644)
        manifest=json.loads(members[-1][1]);manifest[0]['Layers']=[members[1][0]]
        members[-1]=('manifest.json',json.dumps(manifest).encode(),'file',0o644)
        with self.assertRaises(ValueError):self.verify(tar(members),image,payload,meta)

    def test_payload_metadata_and_extra_module_rejected(self):
        for mutation in ('bytes','mode','symlink','extra'):
            entries=[('app',b'','directory',0o555),('app/tools',b'','directory',0o555)]+[
                ('app/tools/file'+str(i)+'.py',('code'+str(i)).encode(),'file',0o444) for i in range(5)]
            if mutation=='bytes':entries[2]=(entries[2][0],b'evil','file',0o444)
            elif mutation=='mode':entries[2]=(*entries[2][:3],0o755)
            elif mutation=='symlink':entries[1]=('app/tools',b'','symlink',0o555)
            else:entries.append(('app/tools/__init__.py',b'evil','file',0o444))
            data,image,payload,meta,_,_=fixture(entries=entries)
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):self.verify(data,image,payload,meta)

    def test_whiteout_removes_payload_and_opaque_does_not_hide_new_same_layer_files(self):
        layer=[('app/tools/.wh.file0.py',b'','file',0o644)]
        data,image,payload,meta,_,_=fixture(extra_layers=[layer])
        with self.assertRaises(ValueError):self.verify(data,image,payload,meta)
        layer=[('app/tools/file'+str(i)+'.py',('code'+str(i)).encode(),'file',0o444) for i in range(5)]
        layer.append(('app/tools/.wh..wh..opq',b'','file',0o644))
        data,image,payload,meta,_,_=fixture(extra_layers=[layer])
        self.assertTrue(self.verify(data,image,payload,meta)['adapterPayloadVerified'])

    def test_duplicate_paths_traversal_and_absolute_refused(self):
        for entries in ([('same',b'a','file',0o644),('same',b'b','file',0o644)],
                        [('../escape',b'a','file',0o644)],[('/absolute',b'a','file',0o644)]):
            data,image,payload,meta,_,_=fixture(entries=entries)
            with self.assertRaises(ValueError):self.verify(data,image)

    def test_entry_byte_and_deadline_limits(self):
        data,image,_,_,_,_=fixture(compressed=True)
        for budget in (m.Budget(max_bytes=1),m.Budget(max_entries=1)):
            with self.assertRaises(ValueError):self.verify(data,image,budget=budget)
        budget=m.Budget();budget.deadline=0
        with self.assertRaises(ValueError):self.verify(data,image,budget=budget)

    def test_gzip_expansion_bound(self):
        data,image,_,_,_,_=fixture(entries=[('large',b'x'*1000000,'file',0o644)],compressed=True)
        with self.assertRaises(ValueError):self.verify(data,image,budget=m.Budget(max_bytes=200000))

    def test_manifest_multiple_images_and_missing_layer_blocked(self):
        _,image,_,_,members,_=fixture();value=json.loads(members[-1][1])
        for manifest in (value*2,[{**value[0],'Layers':['missing']} ]):
            members[-1]=('manifest.json',json.dumps(manifest).encode(),'file',0o644)
            with self.assertRaises((ValueError,KeyError)):self.verify(tar(members),image)

    def test_legacy_archive_metadata_supported(self):
        _,image,payload,meta,members,_=fixture()
        old=[]
        for i,(name,raw,kind,mode) in enumerate(members[:-1]):old.append(('config.json' if i==0 else 'layer/layer.tar',raw,kind,mode))
        old.extend([('layer/VERSION',b'1.0','file',0o644),('layer/json',b'{}','file',0o644),
                    ('manifest.json',json.dumps([{'Config':'config.json','Layers':['layer/layer.tar']}]).encode(),'file',0o644)])
        self.assertTrue(self.verify(tar(old),image,payload,meta)['adapterPayloadVerified'])

    def test_wrong_startup_labels_and_implicit_volumes_blocked(self):
        for key,value in (('User','0:0'),('Volumes',{'/unapproved':{}}),('Entrypoint',['sh']),('Cmd',['evil'])):
            _,_,payload,meta,members,cfg=fixture();cfg['config'][key]=value
            raw=json.dumps(cfg,sort_keys=True).encode();name='blobs/sha256/'+m.digest(raw)
            members[0]=(name,raw,'file',0o644);manifest=json.loads(members[-1][1]);manifest[0]['Config']=name
            members[-1]=('manifest.json',json.dumps(manifest).encode(),'file',0o644)
            with self.subTest(key=key),self.assertRaises(ValueError):self.verify(tar(members),'sha256:'+m.digest(raw),payload,meta)

    def test_isolated_cli_redaction_and_empty_docker_config(self):
        data,image,payload,meta,_,cfg=fixture()
        with tempfile.TemporaryDirectory(dir=os.environ.get('OUF_TEST_ROOT',str(ROOT.parent))) as d:
            root=Path(d);root.chmod(0o700)
            binary=root/'docker-fixture'
            # This fake CLI exposes the exact save transport contract. Image
            # files are never executed; root ownership matches the real tool.
            import base64
            binary.write_text('#!/usr/bin/python3\nimport base64,sys,os\n'
                'assert sys.argv[1]=="--config" and os.listdir(sys.argv[2])==[]\n'
                'assert sys.argv[3:6]==["--host","unix:///fixture","image"]\n'
                'assert sys.argv[6:9]==["save","--platform","linux/amd64"]\n'
                'sys.stdout.buffer.write(base64.b64decode('+repr(base64.b64encode(data).decode())+'))\n')
            binary.chmod(0o755)
            args=['/usr/bin/python3','-I','-B',str(ROOT/'tools/verify_semantic_image_archive.py'),
                '--docker-path',str(binary),'--docker-host','unix:///fixture','--platform','linux/amd64',
                '--adapter-image',image,'--southbound-image',image,'--payload-hashes',json.dumps(payload),
                '--source-commit',meta['sourceCommit'],'--payload-hash',meta['payloadHash'],'--runtime-user',meta['user'],
                '--seconds','10','--max-bytes','1000000','--max-entries','1000']
            descriptor=m.digest(json.dumps({'Type':'layers','Layers':cfg['rootfs']['diff_ids']},sort_keys=True,separators=(',',':')).encode())
            args+=['--adapter-rootfs-descriptors-hash',descriptor,'--southbound-rootfs-descriptors-hash',descriptor]
            proc=subprocess.run(args,capture_output=True);self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
            self.assertNotIn(b'SENTINEL',proc.stdout+proc.stderr)
            args[args.index('--southbound-rootfs-descriptors-hash')+1]='f'*64
            proc=subprocess.run(args,capture_output=True);self.assertEqual(proc.returncode,1)
            self.assertIn(b'ROOTFS_DESCRIPTOR_COMPARISON',proc.stdout)
            self.assertIn(b'SOUTHBOUND',proc.stdout)
            self.assertNotIn(b'SENTINEL',proc.stdout+proc.stderr)
            args[args.index('--southbound-rootfs-descriptors-hash')+1]=descriptor
            args[args.index('--payload-hash')+1]='f'*64
            proc=subprocess.run(args,capture_output=True);self.assertEqual(proc.returncode,1)
            self.assertNotIn(b'SENTINEL',proc.stdout+proc.stderr);self.assertNotIn(d.encode(),proc.stdout+proc.stderr)

    def test_diagnostic_never_serializes_error_message_or_foreign_frame(self):
        secret = 'PRIVATE_KEY_SENTINEL=/secret/path'
        try:
            exec(compile('raise KeyError('+repr(secret)+')', '/secret/archive/path', 'exec'))
        except Exception as error:
            diagnostic = m.blocked_diagnostic(error)
        raw = json.dumps(diagnostic)
        self.assertEqual(diagnostic['errorClass'], 'KeyError')
        self.assertEqual(diagnostic['verifierLine'], 0)
        self.assertNotIn('SENTINEL', raw)
        self.assertNotIn('/secret', raw)
        class PrivateException(Exception): pass
        self.assertEqual(m.blocked_diagnostic(PrivateException(secret))['errorClass'], 'OTHER')

    def test_failed_export_reports_only_fixed_role_stage_and_numeric_budget(self):
        data,image,payload,meta,_,_=fixture()
        m.DIAGNOSTIC.clear();m.DIAGNOSTIC.update(imageRole='ADAPTER')
        with patch.object(m, 'command_snapshot', return_value='a'*64), \
             patch.object(m.subprocess, 'Popen', side_effect=FileNotFoundError('SECRET_STDERR')):
            try:
                m.docker_verify(Path('/usr/bin/docker'),'unix:///fixture',image,m.Budget(),payload,meta)
            except Exception as error:
                diagnostic=m.blocked_diagnostic(error)
        self.assertEqual(diagnostic['stage'],'DOCKER_EXPORT_OPEN')
        self.assertEqual(diagnostic['imageRole'],'ADAPTER')
        self.assertEqual(diagnostic['parserBytes'],0)
        self.assertIsNone(diagnostic['dockerExitCode'])
        self.assertNotIn('SECRET',json.dumps(diagnostic))

    def test_pipe_deadline_on_stalled_export_and_early_image_argument_rejection(self):
        read,write=os.pipe();budget=m.Budget(seconds=1);budget.deadline=0
        with os.fdopen(read,'rb',buffering=0) as pipe:
            try:
                with self.assertRaises(ValueError):m.PipeReader(pipe,budget).read(512)
            finally:os.close(write)
        with self.assertRaises(ValueError):m.docker_verify(Path('/does/not/exist'),'unix:///fixture','--invalid',m.Budget())

if __name__=='__main__':unittest.main()
