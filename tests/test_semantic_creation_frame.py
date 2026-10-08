import hashlib,json,os,stat,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import observe_semantic_creation_frame as m
from tools.review_semantic_oci_policy import Denied
from tools import observe_semantic_mount_view as mounts
from test_semantic_oci_policy import fixture

class Frame(unittest.TestCase):
    def test_large_source_streamed_and_one_mib_ceiling_enforced(self):
        with tempfile.TemporaryDirectory() as dirname:
            path=Path(dirname)/'source';path.write_bytes(b'C'*262144);path.chmod(0o600)
            item=self.source(path);item['maxBytes']=1048576;m.inputs([item])
            fd=os.open(path,os.O_PATH|os.O_NOFOLLOW)
            try:
                self.assertEqual(m.source_hash(item,fd,mounts.attributes(os.fstat(fd)),mounts.Budget()),262144)
                item['sha256']='0'*64
                with self.assertRaisesRegex(Denied,'SOURCE_FRAME_BYTE_HASH_DRIFT'):
                    m.source_hash(item,fd,mounts.attributes(os.fstat(fd)),mounts.Budget())
            finally:os.close(fd)
            item['maxBytes']=1048577
            with self.assertRaisesRegex(Denied,'EXACT_SOURCE_FRAME_INPUTS_REQUIRED'):m.inputs([item])
            path.write_bytes(b'C'*1048577);item=self.source(path);item['maxBytes']=1048576
            fd=os.open(path,os.O_PATH|os.O_NOFOLLOW)
            try:
                with self.assertRaisesRegex(Denied,'SOURCE_FRAME_CUSTODY_DRIFT'):
                    m.source_hash(item,fd,mounts.attributes(os.fstat(fd)),mounts.Budget())
            finally:os.close(fd)

    def source(self,filename):
        info=filename.lstat()
        return {'source':str(filename),'target':'/proof','readOnly':True,'uid':info.st_uid,'gid':info.st_gid,
            'mode':stat.S_IMODE(info.st_mode),'sha256':hashlib.sha256(filename.read_bytes()).hexdigest(),'maxBytes':131072}

    def test_streamed_hash_matches_with_exact_metadata_and_no_spooled_content(self):
        with tempfile.TemporaryDirectory() as dirname:
            path=Path(dirname)/'source';path.write_bytes(b'CI_PRIVATE_CONTENT'*5000);path.chmod(0o600)
            item=self.source(path);fd=os.open(path,os.O_PATH|os.O_NOFOLLOW)
            try:
                result=m.source_hash(item,fd,mounts.attributes(os.fstat(fd)),mounts.Budget())
                self.assertEqual(result,path.stat().st_size)
                self.assertEqual(list(Path(dirname).iterdir()),[path])
            finally:os.close(fd)

    def test_wrong_hash_metadata_size_or_replacement_denied_without_private_output(self):
        for variant in ('hash','mode','limit','replacement'):
            with self.subTest(variant=variant),tempfile.TemporaryDirectory() as dirname:
                path=Path(dirname)/'source';path.write_bytes(b'CI_PRIVATE_CONTENT');path.chmod(0o600)
                item=self.source(path);fd=os.open(path,os.O_PATH|os.O_NOFOLLOW);before=mounts.attributes(os.fstat(fd))
                try:
                    if variant=='hash':item['sha256']='0'*64
                    elif variant=='mode':item['mode']=0o400
                    elif variant=='limit':item['maxBytes']=1
                    else:
                        replacement=Path(dirname)/'replacement';replacement.write_bytes(path.read_bytes())
                        replacement.chmod(0o600);os.replace(replacement,path)
                    with self.assertRaises(Denied) as caught:m.source_hash(item,fd,before,mounts.Budget())
                    self.assertNotIn('CI_PRIVATE',str(caught.exception));self.assertNotIn(dirname,str(caught.exception))
                finally:os.close(fd)

    def test_invalid_or_duplicate_policy_inputs_denied_before_proc_access(self):
        base={'source':'/CI_PRIVATE_SOURCE','target':'/proof','readOnly':True,'uid':10006,'gid':10006,
            'mode':0o600,'sha256':'a'*64,'maxBytes':131072}
        for key,value in [('uid',True),('gid',-1),('mode',0o666),('sha256','CI_PRIVATE_HASH'),
            ('maxBytes',1048577),('target','/../proof'),('readOnly',False)]:
            item=dict(base);item[key]=value
            with self.subTest(key=key),self.assertRaises(Denied):m.source_mount_frame(0,{}, {},[item])
        with self.assertRaises(Denied):m.source_mount_frame(0,{}, {},[base,base])

    def test_source_policy_must_equal_entire_manifest_mount_binding_before_observation(self):
        doc,expected,spec,startup,hooks,schema=fixture()
        item={'source':'/CI_PRIVATE_DIFFERENT','target':'/proof','readOnly':True,'uid':10006,'gid':10006,
            'mode':0o600,'sha256':'a'*64,'maxBytes':131072}
        with self.assertRaisesRegex(Denied,'EXACT_SOURCE_FRAME_MOUNT_BINDING_REQUIRED'):
            m.configured_creation_frame(0,{},doc,expected,spec,startup,hooks,schema,[item])

if __name__=='__main__':unittest.main()
