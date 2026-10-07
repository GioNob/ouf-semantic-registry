import gzip
import hashlib
import io
import json
import tarfile
import unittest
from tools.plan_semantic_v2_isolated_dossier import role_plan,config_from_archive

class IsolatedDossierTests(unittest.TestCase):
    def test_accepts_manifest_bound_oci_blob_config(self):
        raw=b'{"os":"linux","architecture":"amd64","config":{}}';digest=hashlib.sha256(raw).hexdigest()
        out=io.BytesIO();path='blobs/sha256/'+digest
        with tarfile.open(fileobj=out,mode='w') as archive:
            for name,content in [(path,raw),('manifest.json',json.dumps([{'Config':path}]).encode())]:
                item=tarfile.TarInfo(name);item.size=len(content);archive.addfile(item,io.BytesIO(content))
        self.assertEqual(config_from_archive(io.BytesIO(gzip.compress(out.getvalue())),'sha256:'+digest)['architecture'],'amd64')
    def test_environment_values_are_not_serialized_and_start_is_not_granted(self):
        config={'os':'linux','architecture':'amd64','config':{'Env':['SECRET=do-not-print'],
                'Entrypoint':['/entrypoint'],'Cmd':[],'User':'10006','WorkingDir':'/app'}}
        result=role_plan('adapter','sha256:'+'a'*64,config)
        self.assertEqual(result['packagedEnvironmentNames'],['SECRET'])
        self.assertNotIn('do-not-print',json.dumps(result));self.assertFalse(result['startAuthorized'])
        self.assertEqual(result['hostPublishedPorts'],[])
    def test_rejects_config_from_a_different_image_and_wrong_architecture(self):
        raw=b'{}';out=io.BytesIO()
        with tarfile.open(fileobj=out,mode='w') as archive:
            item=tarfile.TarInfo('a'*64+'.json');item.size=len(raw);archive.addfile(item,io.BytesIO(raw))
        with self.assertRaises(ValueError):config_from_archive(io.BytesIO(gzip.compress(out.getvalue())),'sha256:'+'a'*64)
        with self.assertRaises(ValueError):role_plan('adapter','sha256:'+'a'*64,{'os':'linux','architecture':'arm64'})

if __name__=='__main__':unittest.main()
