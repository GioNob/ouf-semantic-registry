"""CI-only compatibility experiment; public owned fixtures, never target deployment."""
import argparse,gzip,hashlib,json,os,re,shutil,subprocess,sys,time
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
        (out/'openssl-source-lock.json').write_text(json.dumps({'version':'3.4.8','archiveSha256':'9de9ce2f29e584044ae07ab93fc601637be01fdc91d109c5a655ec7419e6022b','openrestyPatchCommit':'bc8bf89488f2d02572389158533b3f85ca0ded7f','openrestyOriginalPatchSha256':hashlib.sha256((semantic/'tests/openssl-3.4.1-sess_set_get_cb_yield.patch').read_bytes()).hexdigest(),'openrestyPortPatchSha256':'acf063b2848342272881d7f6a03da6cd58ac03de95c0a88ac94193cc3ee1b2ea'},indent=2)+'\n')
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
            command.append(str(semantic));run(command,timeout=2400)
            locks[role]['updatedImageId']=inspect(tag)['Id']
        env['OUF_PROVIDER_TEST_FINAL_IMAGE']=locks['adapter']['updatedImageId']
        env['OUF_PROVIDER_TEST_APISIX_IMAGE']=locks['southbound']['updatedImageId']
        run([sys.executable,'-B','-m','unittest','tests.test_semantic_provider_container'],cwd=gateway,env=env,timeout=420)
    run([sys.executable,'-B','-m','unittest','tests.test_semantic_provider_apisix_live'],cwd=gateway,env=env,timeout=420)
    adapter=json.loads((gateway/'generated/semantic-provider-package-proof.json').read_text())
    southbound=json.loads((gateway/'generated/semantic-southbound-package-proof.json').read_text())
    assert adapter['baseImage']==images['adapter'] and southbound['requestedImage']==env['OUF_PROVIDER_TEST_APISIX_IMAGE']
    assert adapter['tlsAdmissionProven'] is True and southbound['tlsOidcNegativeBoundariesProven'] is True
    inventory=run(['docker','run','--rm','--network','none','--user','0:0','--entrypoint','sh',southbound['imageId'],'-c','/usr/local/openresty/openssl3/bin/openssl version; dpkg-query -W zlib1g; ldd /usr/local/openresty/nginx/sbin/nginx; sha256sum /usr/local/openresty/openssl3/lib/libssl.so.3 /usr/local/openresty/openssl3/lib/libcrypto.so.3'],capture_output=True,text=True,timeout=30)
    assert 'OpenSSL 3.4.8' in inventory.stdout
    assert 'libssl.so.3 => /usr/local/openresty/openssl3/lib/libssl.so.3' in inventory.stdout
    assert 'libcrypto.so.3 => /usr/local/openresty/openssl3/lib/libcrypto.so.3' in inventory.stdout
    (out/'bundled-openssl-runtime-proof.txt').write_text(inventory.stdout)
    native=run(['docker','run','--rm','--network','none','--user','0:0','--entrypoint','sh',southbound['imageId'],
        '-c', 'test ! -e /usr/local/openresty/wasmtime-c-api && /usr/local/openresty/nginx/sbin/nginx -V 2>&1 && ldd /usr/local/openresty/nginx/sbin/nginx'],capture_output=True,text=True,timeout=30)
    assert 'wasmtime' not in native.stdout and 'wasm-nginx-module' not in native.stdout
    (out/'native-runtime-link-proof.txt').write_text(native.stdout)
    guard_lua = "local d=ngx.shared.guard; assert(d:set('ok',1)); assert(d:get('ok')==1); " \
        "local k=string.rep('x',65536); local ok,err=d:set(k,1); assert(ok==nil and err=='key too long'); " \
        "local v,e=d:incr(k,1,0); assert(v==nil and e=='key too long'); print('SHDICT_KEY_BOUNDARY_PASS')"
    guard=run(['docker','run','--rm','--network','none','--user','0:0',
        '--entrypoint','/usr/local/openresty/bin/resty',southbound['imageId'],
        '--shdict','guard 1m','-e',guard_lua],capture_output=True,text=True,timeout=30)
    assert 'SHDICT_KEY_BOUNDARY_PASS' in guard.stdout
    (out/'native-shdict-regression.txt').write_text(guard.stdout)
    grpc_config = 'server { listen 127.0.0.1:18082; http2 on; location / { ' \
        'content_by_lua_block { ngx.say("AUTHORITY=" .. ngx.var.host) } } } ' \
        'server { listen 127.0.0.1:18083; location / { ' \
        'grpc_set_header :authority ouf-authority.example.invalid; grpc_pass grpc://127.0.0.1:18082; } }'
    grpc_lua = "local s=ngx.socket.tcp(); s:settimeout(5000); assert(s:connect('127.0.0.1',18083)); " \
        "assert(s:send('POST /probe HTTP/1.1\\r\\nHost: original.example.invalid\\r\\n" \
        "Content-Type: application/grpc\\r\\nContent-Length: 0\\r\\nConnection: close\\r\\n\\r\\n')); " \
        "local body=assert(s:receive('*a')); assert(body:find('AUTHORITY=ouf%-authority%.example%.invalid')); " \
        "s:close(); print('GRPC_AUTHORITY_PASS')"
    grpc=run(['docker','run','--rm','--network','none','--user','0:0',
        '--entrypoint','/usr/local/openresty/bin/resty',southbound['imageId'],
        '--http-conf',grpc_config,'-e',grpc_lua],capture_output=True,text=True,timeout=30)
    assert 'GRPC_AUTHORITY_PASS' in grpc.stdout
    (out/'native-grpc-authority-regression.txt').write_text(grpc.stdout)
    for filename in ('native-runtime-sources.json','native-runtime-binaries.json'):
        payload=run(['docker','run','--rm','--network','none','--user','0:0','--entrypoint','cat',southbound['imageId'],
            '/usr/local/share/ouf/'+filename],capture_output=True,timeout=30)
        parsed=json.loads(payload.stdout)
        assert type(parsed) is dict
        (out/filename).write_bytes(payload.stdout)

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
    receipt['semanticBuildCommit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=semantic,text=True).strip()
    receipt['candidateArchives']=[]
    for binding in receipt['imageArchiveBindings']:
        role=binding['role'];target=out/(role+'.image.tar.gz')
        reader=subprocess.Popen(['sudo','cat','/root/ouf-ci-image-remediation/sbom/'+role+'.tar'],stdout=subprocess.PIPE)
        raw_hash=hashlib.sha256();raw_size=0;deadline=time.monotonic()+180
        try:
            with target.open('xb') as file:
                with gzip.GzipFile(filename='',mode='wb',compresslevel=3,mtime=0,fileobj=file) as compressed:
                    while chunk:=reader.stdout.read(1024*1024):
                        assert time.monotonic()<deadline
                        raw_size+=len(chunk);assert raw_size<=8589934592
                        raw_hash.update(chunk);compressed.write(chunk)
            assert reader.wait(timeout=10)==0
        finally:
            reader.stdout.close()
            if reader.poll() is None:reader.kill();reader.wait()
        assert raw_hash.hexdigest()==binding['archiveSha256'] and raw_size==binding['archiveBytes']
        with target.open('rb') as file:compressed_hash=hashlib.file_digest(file,'sha256').hexdigest()
        receipt['candidateArchives'].append({'role':role,'file':target.name,'sha256':compressed_hash,'bytes':target.stat().st_size,'uncompressedSha256':binding['archiveSha256'],'uncompressedBytes':raw_size,'imageId':binding['imageId'],'kind':'docker-save-tar-gzip'})
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    sums=[]
    for file in sorted(out.rglob('*')):
        if not file.is_file() or 'source-zlib' in file.parts:continue
        with file.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        sums.append(digest+'  '+str(file.relative_to(semantic)))
    (out/'checksums.sha256').write_text('\n'.join(sums)+'\n')
    print('SEMANTIC_IMAGE_REMEDIATION_EXPERIMENT='+json.dumps(receipt,sort_keys=True))
    print('EXPERIMENT_COMPLETED=true THRESHOLD_MET='+str(receipt['allScannerSeverityThresholdsMet']).lower()+' TARGET_ACCEPTANCE=false')
if __name__=='__main__':main()

