"""CI-only compatibility experiment; public owned fixtures, never target deployment."""
import argparse,hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path

CANDIDATES={'alpine-ubuntu':('python:3.13-alpine','apache/apisix:3.18.0-ubuntu'),
            'slim-debian':('python:3.13-slim','apache/apisix:3.18.0-debian'),
            'alpine-ubuntu-source-fixed':('python@sha256:2d9aefe2fef018a7eb2c13064c89c71929800fd2e5dccdbf52ea5da5bb8d929a',
              'apache/apisix@sha256:9ee5df1611f98a902d1bbacf760b35632498006854a223837ab290d27a928846')}
def run(args,**kwargs):return subprocess.run(args,check=kwargs.pop('check',True),timeout=kwargs.pop('timeout',240),**kwargs)
def inspect(reference):
    return json.loads(subprocess.check_output(['docker','image','inspect',reference],text=True,timeout=20))[0]
def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',choices=CANDIDATES,required=True);p.add_argument('--gateway',type=Path,required=True)
    a=p.parse_args();gateway=a.gateway.resolve();semantic=Path(__file__).resolve().parents[1]
    images={};locks={}
    for role,tag in zip(('adapter','southbound'),CANDIDATES[a.candidate]):
        run(['docker','pull','--platform=linux/amd64',tag],timeout=180)
        info=inspect(tag);assert info['Architecture']=='amd64' and info['Os']=='linux'
        prefix='python@sha256:' if role=='adapter' else 'apache/apisix@sha256:'
        digests=[d for d in info['RepoDigests'] if d.startswith(prefix) and re.fullmatch(r'.+@sha256:[0-9a-f]{64}',d)]
        assert len(digests)==1;images[role]=digests[0]
        locks[role]={'discoveryTag':tag,'resolvedDigest':digests[0],'pulledImageId':info['Id']}
    out=semantic/'generated'/a.candidate;out.mkdir(parents=True,exist_ok=False)
    (out/'inputs.json').write_text(json.dumps(locks,sort_keys=True,indent=2)+'\n')
    env=dict(os.environ,OUF_PROVIDER_CONTAINER_TEST='1',OUF_SEMANTIC_PROVIDER_APISIX_TEST='1',
        OUF_PROVIDER_TEST_BASE_IMAGE=images['adapter'],OUF_PROVIDER_TEST_APISIX_IMAGE=images['southbound'])
    run([sys.executable,'-B','-m','unittest','tests.test_semantic_provider_container'],cwd=gateway,env=env,timeout=420)
    if a.candidate=='alpine-ubuntu-source-fixed':
        inventory_command=['docker','run','--rm','--network','none','--user','0:0','--entrypoint','sh',images['southbound'],
            '-c', "cat /etc/os-release; dpkg-query -W -f='$"+"{binary:Package} $"+"{Version}\\n' 'libssl*' '*openresty*' openssl 2>/dev/null || true; openssl version; /usr/local/openresty/openssl3/bin/openssl version || true; ldd /usr/local/openresty/nginx/sbin/nginx | grep -E 'ssl|crypto' || true"]
        # Only public base-image OS/package/link facts; no fixture config or credentials.
        inventory=run(inventory_command,capture_output=True,text=True,timeout=30)
        (out/'public-runtime-inventory.txt').write_text(inventory.stdout)
        print('PUBLIC_SOUTHBOUND_RUNTIME_INVENTORY='+inventory.stdout)

        source=out/'source-zlib'
        source.mkdir()
        source_commit='df84af25dc1942490e1d1c899a07619152a46148'
        run(['git','init',str(source)],capture_output=True)
        run(['git','-C',str(source),'fetch','--depth=1','https://github.com/madler/zlib.git',source_commit],capture_output=True)
        run(['git','-C',str(source),'checkout','--detach','FETCH_HEAD'],capture_output=True)
        assert subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()==source_commit
        run(['git','-C',str(source),'fsck','--full'],capture_output=True)
        source_tree=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD^{tree}'],text=True).strip()
        shutil.rmtree(source/'.git')
        source_hashes={str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source.rglob('*')) if p.is_file()}
        source_manifest=json.dumps(source_hashes,sort_keys=True,separators=(',',':'))
        locks['zlibSource']={'commit':source_commit,'gitTree':source_tree,'sourceManifestSha256':hashlib.sha256(source_manifest.encode()).hexdigest(),'releaseStatus':'unreleased upstream'}
        (out/'zlib-source-files.json').write_text(source_manifest+'\n')
        (out/'openssl-source-lock.json').write_text(json.dumps({'version':'3.4.8','archiveSha256':'9de9ce2f29e584044ae07ab93fc601637be01fdc91d109c5a655ec7419e6022b','openrestyPatchCommit':'bc8bf89488f2d02572389158533b3f85ca0ded7f','openrestyPatchSha256':hashlib.sha256((semantic/'tests/openssl-3.4.1-sess_set_get_cb_yield.patch').read_bytes()).hexdigest()},indent=2)+'\n')
        initial=json.loads((gateway/'generated/semantic-provider-package-proof.json').read_text())
        initial_tag='ouf-provider-package-ci:'+initial['sourceRevision'][:12]
        assert inspect(initial_tag)['Id']==initial['imageId']
        adapter_tag='ouf-remediation-updated-adapter:ci'
        southbound_tag='ouf-remediation-updated-southbound:ci'
        for role,source,tag,dockerfile in (
                ('adapter',initial_tag,adapter_tag,'Dockerfile.semantic-provider-source-fixed'),
                ('southbound',images['southbound'],southbound_tag,'Dockerfile.semantic-southbound-source-fixed')):
            command=['docker','build','--pull=false','--file',str(semantic/dockerfile),'--tag',tag,
                '--build-arg','INPUT_IMAGE='+source]
            if role=='southbound':
                command+=['--build-arg','RUNTIME_USER='+(inspect(source)['Config'].get('User') or '0:0')]
            command.append(str(semantic));run(command,timeout=1200)
            locks[role]['updatedImageId']=inspect(tag)['Id']
        env['OUF_PROVIDER_TEST_FINAL_IMAGE']=locks['adapter']['updatedImageId']
        env['OUF_PROVIDER_TEST_APISIX_IMAGE']=locks['southbound']['updatedImageId']
        run([sys.executable,'-B','-m','unittest','tests.test_semantic_provider_container'],cwd=gateway,env=env,timeout=420)
    run([sys.executable,'-B','-m','unittest','tests.test_semantic_provider_apisix_live'],cwd=gateway,env=env,timeout=420)
    adapter=json.loads((gateway/'generated/semantic-provider-package-proof.json').read_text())
    southbound=json.loads((gateway/'generated/semantic-southbound-package-proof.json').read_text())
    assert adapter['baseImage']==images['adapter'] and southbound['requestedImage']==env['OUF_PROVIDER_TEST_APISIX_IMAGE']
    assert adapter['tlsAdmissionProven'] is True and southbound['tlsOidcNegativeBoundariesProven'] is True
    inventory=run(['docker','run','--rm','--network','none','--user','0:0','--entrypoint','sh',southbound['imageId'],'-c','/usr/local/openresty/openssl3/bin/openssl version; ldd /usr/local/openresty/nginx/sbin/nginx; sha256sum /usr/local/openresty/openssl3/lib/libssl.so.3 /usr/local/openresty/openssl3/lib/libcrypto.so.3'],capture_output=True,text=True,timeout=30)
    assert 'OpenSSL 3.4.8' in inventory.stdout
    assert 'libssl.so.3 => /usr/local/openresty/openssl3/lib/libssl.so.3' in inventory.stdout
    assert 'libcrypto.so.3 => /usr/local/openresty/openssl3/lib/libcrypto.so.3' in inventory.stdout
    (out/'bundled-openssl-runtime-proof.txt').write_text(inventory.stdout)
    (out/'compatibility.json').write_text(json.dumps({'adapter':adapter,'southbound':southbound},indent=2,sort_keys=True)+'\n')
    result=run(['sudo','/usr/bin/python3','-B',str(semantic/'tests/scan_semantic_image_remediation.py'),
        '--adapter',adapter['imageId'],'--southbound',southbound['imageId']],capture_output=True,text=True,timeout=900,check=False)
    if result.returncode:
        print(result.stderr[-12000:],file=sys.stderr)
        raise RuntimeError('CI_OFFLINE_SCAN_FAILED')
    for directory,names in (('sbom',('receipt.json','adapter.syft.json','adapter.spdx.json','southbound.syft.json','southbound.spdx.json')),('review',('receipt.json','adapter.grype.json','southbound.grype.json'))):
        destination=out/directory;destination.mkdir()
        for name in names:
            # CI-owned public image metadata only; fixed read paths, no target access.
            public=run(['sudo','cat','/root/ouf-ci-image-remediation/'+directory+'/'+name],capture_output=True,timeout=30)
            (destination/name).write_bytes(public.stdout)
    receipt=json.loads(result.stdout);assert receipt['schema']=='ouf.semantic-image-remediation-experiment.v1'
    receipt.update(candidate=a.candidate,inputs=locks,gatewayCodeCommit=adapter['sourceRevision'],compatibilityProven=True)
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print('SEMANTIC_IMAGE_REMEDIATION_EXPERIMENT='+json.dumps(receipt,sort_keys=True))
    print('EXPERIMENT_COMPLETED=true THRESHOLD_MET='+str(receipt['allScannerSeverityThresholdsMet']).lower()+' TARGET_ACCEPTANCE=false')
if __name__=='__main__':main()
