"""CI-only: reproduce the generated LuaJIT table from byte-locked sources."""
import argparse
import gzip
import hashlib
import io
import json
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from tools.extend_semantic_dependency_inventory import image_files

FILE = 'usr/local/openresty/luajit/share/luajit-2.1/jit/vmdef.lua'
ORIGINAL = '2cdd7a73c1fc2a710f1e6604eb6cab2988492e4c45b5252defffa9832b91d9d0'
FLAGS = '-DLUAJIT_NUMMODE=2 -DLUAJIT_ENABLE_LUA52COMPAT'

def require(value):
    if not value: raise ValueError('GENERATED_LUAJIT_BINDING_UNPROVEN')

def source_files(raw, expected):
    """Retain only the exact source set measured before the original build."""
    entries = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
        for member in archive:
            parts = PurePosixPath(member.name).parts
            require(parts and '..' not in parts and not member.name.startswith('/'))
            if member.isdir(): continue
            require(member.isfile() and 0 <= member.size <= 33554432)
            path = '/'.join(parts[1:]); require(path and path not in entries)
            entries[path] = archive.extractfile(member).read()
    original = entries['src/luaconf.h']
    before = b'".\\\\?.lua;" LUA_LDIR"?.lua;" LUA_LDIR"?\\\\init.lua;"'
    after = b'".\\\\?.lua;" "!\\\\lualib\\\\?.lua;" LUA_LDIR"?.lua;" LUA_LDIR"?\\\\init.lua;"'
    require(original.count(before) == 1)
    patched = original.replace(before, after)
    before = b'".\\\\?.dll;" LUA_CDIR"?.dll;" LUA_CDIR"loadall.dll"'
    after = b'".\\\\?.dll;" "!\\\\lualib\\\\?.so;" LUA_CDIR"?.dll;" LUA_CDIR"loadall.dll"'
    require(patched.count(before) == 1)
    entries['src/luaconf.h'] = patched.replace(before, after)
    if 'src/luaconf.h.orig' in expected: entries['src/luaconf.h.orig'] = original
    require(set(expected) <= set(entries))
    selected = {path: entries[path] for path in expected}
    require(all(hashlib.sha256(raw).hexdigest() == expected[path] for path, raw in selected.items()))
    return selected

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--inventory-directory',type=Path,required=True);args=parser.parse_args()
    with args.bundle.open('rb') as stream:require(hashlib.file_digest(stream,'sha256').hexdigest()==ORIGINAL)
    with zipfile.ZipFile(args.bundle) as archive:
        receipt=json.loads(archive.read('receipt.json'));manifest_raw=archive.read('native-runtime-sources.json')
        require(hashlib.sha256(manifest_raw).hexdigest()==receipt['nativeScan']['nativeSourceManifestSha256'])
        sources=json.loads(manifest_raw)
        lock=next(a for a in sources['openresty']['archives'] if a['file']=='LuaJIT-2.1-20260824.tar.gz')
        require(lock['sha256']=='d73577495b63373079fe65e89613aee383db4369c22cf5b88a20a57be3d9f33a')
        prefix='bundle/LuaJIT-2.1-20260824/'
        expected={p[len(prefix):]:h for p,h in sources['sourceFiles']['compiledSourceFiles'].items() if p.startswith(prefix)}
        require(len(expected)==246)
        image=next(r for r in receipt['candidateArchives'] if r['role']=='southbound')
        with archive.open('southbound.image.tar.gz') as incoming,gzip.GzipFile(fileobj=incoming) as plain:
            rows,config=image_files(plain,image['uncompressedSha256'],image['uncompressedBytes'])
        require('sha256:'+config==image['imageId'])
    with tempfile.TemporaryDirectory(prefix='ouf-generated-luajit-') as directory:
        root=Path(directory);download=root/'source.tar.gz'
        subprocess.run(['curl','--fail','--silent','--show-error','--location','--proto','=https',
                        '--max-time','120','--max-filesize','33554432',lock['url'],'-o',str(download)],check=True,timeout=130)
        raw=download.read_bytes();require(len(raw)==lock['bytes'] and hashlib.sha256(raw).hexdigest()==lock['sha256'])
        selected=source_files(raw,expected)
        source=root/'source';source.mkdir(mode=0o700)
        for path,raw in selected.items():
            target=source/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        # Execute only the newly compiled upstream generator, after every source hash matches.
        subprocess.run(['make','-C',str(source/'src'),'-j2','jit/vmdef.lua','XCFLAGS='+FLAGS],check=True,timeout=180)
        output=(source/'src/jit/vmdef.lua').read_bytes()
        require(output==rows[FILE]['raw'])
        proof=dict(schema='ouf.semantic-generated-luajit-output.v1',sourceArtifactSha256=ORIGINAL,
            imageId=image['imageId'],sourceArchiveSha256=lock['sha256'],sourceManifestSha256=hashlib.sha256(manifest_raw).hexdigest(),
            verifiedSourceFileCount=len(selected),buildFlags=FLAGS,installedPath=FILE,
            generatedFileSha256=hashlib.sha256(output).hexdigest(),reconstructedOutputMatchesInstalledBytes=True,
            imagePayloadExecuted=False,imagesModified=False,containerOperations=0,
            generatorBinarySha256=hashlib.sha256((source/'src/host/buildvm').read_bytes()).hexdigest())
    root=args.inventory_directory
    inventory=json.loads((root/'inventory.json').read_bytes())
    require(inventory['sourceArtifactSha256']==ORIGINAL)
    southbound=next(i for i in inventory['images'] if i['role']=='southbound')
    require(southbound['imageId']==proof['imageId'] and southbound['unresolvedOpenRestyLuaFiles']==[FILE])
    sbom=json.loads((root/'southbound.extended.syft.json').read_bytes())
    package=next(p for p in sbom['artifacts'] if p['name']=='luajit')
    require(package['version']=='2.1.1787558776')
    package['locations'].append({'path':'/'+FILE})
    (root/'southbound.extended.syft.json').write_text(json.dumps(sbom,sort_keys=True)+'\n')
    southbound['extendedSyftSha256']=hashlib.sha256((root/'southbound.extended.syft.json').read_bytes()).hexdigest()
    southbound['unresolvedOpenRestyLuaFiles']=[];southbound['generatedLuaJitProof']=proof
    (root/'inventory.json').write_text(json.dumps(inventory,indent=2,sort_keys=True)+'\n')
    print('OUF_GENERATED_LUAJIT_RECONCILIATION='+json.dumps(proof,sort_keys=True))

if __name__=='__main__':main()
