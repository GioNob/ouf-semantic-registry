"""Mandatory CI Docker save compatibility; owned scratch image, never started."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import uuid

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('image_archive',ROOT/'tools/verify_semantic_image_archive.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class DockerArchiveTest(unittest.TestCase):
    def test_real_local_save_and_layer_payload_bindings(self):
        self.assertEqual(os.geteuid(),0)
        self.assertEqual(os.environ.get('OUF_REQUIRE_IMAGE_ARCHIVE_DOCKER'),'1')
        docker=Path(os.environ.get('OUF_IMAGE_ARCHIVE_DOCKER_PATH','/usr/bin/docker'));host=os.environ.get('OUF_IMAGE_ARCHIVE_DOCKER_HOST','unix:///var/run/docker.sock');tag='ouf-ci-image-byte-'+uuid.uuid4().hex
        with tempfile.TemporaryDirectory(dir=os.environ.get('OUF_IMAGE_ARCHIVE_TEST_PARENT',str(ROOT.parent))) as d:
            context=Path(d);context.chmod(0o700)
            tools=context/'rootfs/app/tools';tools.mkdir(parents=True,mode=0o555)
            payload={}
            for i in range(5):
                p=tools/('file'+str(i)+'.py');raw=('fixture='+str(i)+'\n').encode();p.write_bytes(raw)
                payload['app/tools/'+p.name]=m.digest(raw)
            dockerfile='''FROM scratch
ARG SOURCE_REVISION
ARG PAYLOAD_SHA256
COPY --chmod=0555 rootfs/ /
COPY --chmod=0444 rootfs/app/tools/file0.py rootfs/app/tools/file1.py rootfs/app/tools/file2.py rootfs/app/tools/file3.py rootfs/app/tools/file4.py /app/tools/
WORKDIR /app
USER 10006:10006
LABEL org.opencontainers.image.revision=${SOURCE_REVISION} ouf.component=semantic-provider-transport ouf.payload.sha256=${PAYLOAD_SHA256}
ENTRYPOINT ["python3", "-B", "-m", "tools.semantic_provider_adapter"]
'''
            (context/'Dockerfile').write_text(dockerfile)
            manifest={**payload,'Dockerfile':m.digest(dockerfile.encode())}
            payload_hash=m.digest(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode())
            metadata=dict(user='10006:10006',sourceCommit='a'*40,payloadHash=payload_hash)
            try:
                build=subprocess.run([str(docker),'--host',host,'build','--network=none','--pull=false','--tag',tag,
                    '--build-arg','SOURCE_REVISION='+metadata['sourceCommit'],'--build-arg','PAYLOAD_SHA256='+payload_hash,d],
                    capture_output=True,timeout=120)
                self.assertEqual(build.returncode,0,build.stderr.decode()[-2000:])
                image=subprocess.check_output([str(docker),'--host',host,'image','inspect','--format','{{.Id}}',tag],timeout=10).decode().strip()
                result=m.docker_verify(docker,host,image,m.Budget(seconds=30,max_bytes=10000000),payload,metadata)
                self.assertTrue(result['adapterPayloadVerified'])
                self.assertTrue(result['layerDiffIdsMatchConfig'])
                self.assertTrue(result['imageTargetChainVerified'])
                if os.environ.get('OUF_REQUIRE_CONTAINERD_IMAGE_ID') == '1':
                    self.assertFalse(result['configBytesMatchImageId'])
                    self.assertEqual(result['imageIdentityBindingKind'],'MANIFEST')
                self.assertFalse(result['acceptanceGranted'])
            finally:
                cleanup=subprocess.run([str(docker),'--host',host,'image','rm',tag],capture_output=True,timeout=15)
                self.assertEqual(cleanup.returncode,0,cleanup.stderr.decode()[-1000:])

if __name__=='__main__':unittest.main()
