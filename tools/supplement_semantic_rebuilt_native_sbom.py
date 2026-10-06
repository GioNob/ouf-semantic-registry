"""Bind the source-built CI native payload to the exact scanned image archive.

Keep the original Syft output intact and emit a separate supplemented document.
Source closure and identity evidence do not confer publisher trust/acceptance.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from tools.audit_semantic_native_coverage import ROOT, native_files, require, sha


def supplement(original, rows, sources, binaries, lock):
    require(all(sources[k] == v for k, v in lock.items()))
    require(sources['wasm']['compiled'] is False)
    require(not any('wasmtime' in p or 'wasm-nginx-module' in p for p in rows))
    actual = {'/' + p: r['sha256'] for p, r in rows.items() if r.get('elf')}
    require(actual == binaries and len(actual) >= 10)
    embedded = sources['embeddedSourceDirectories']
    components = [
        ('openssl', '3.4.8', 'openssl', 'openssl', 'openssl3/', None),
        ('zlib', '1.3.2.1-motley', 'zlib', 'zlib', 'zlib/', None),
        ('pcre', '8.45', 'pcre', 'pcre', 'pcre/', None),
        ('luajit', '2.1-20260415', 'luajit', 'luajit', 'luajit/', 'LuaJIT-2.1-20260415'),
        ('lua-cjson', '2.1.0.17', None, None, 'lualib/cjson.so', 'lua-cjson-2.1.0.17'),
        ('lua-resty-signal', '0.04', None, None, 'lualib/librestysignal.so', 'lua-resty-signal-0.04'),
        ('lua-redis-parser', '0.13', None, None, 'lualib/redis/parser.so', 'lua-redis-parser-0.13'),
        ('openresty', '1.29.2.4', 'openresty', 'openresty', 'nginx/sbin/nginx', 'nginx-1.29.2'),
    ]
    result = copy.deepcopy(original)
    proof = []
    covered = set()
    for component, version, vendor, product, path, directory in components:
        if directory:
            require(directory in embedded)
        matches = {p: h for p, h in actual.items() if p.startswith('/' + ROOT + path)}
        require(matches)
        covered.update(matches)
        if component == 'openssl':
            require(any(b'OpenSSL 3.4.8' in r.get('raw', b'') for p, r in rows.items() if p.startswith(ROOT + path)))
        if component == 'zlib':
            require(any(b'1.3.2.1-motley\x00' in r.get('raw', b'') for p, r in rows.items() if p.startswith(ROOT + path)))
        if component == 'pcre':
            require(any(b'8.45 2021-06-15\x00' in r.get('raw', b'') for p, r in rows.items() if p.startswith(ROOT + path)))
        identifier = sha(('ouf-source-native:' + component + ':' + json.dumps(matches, sort_keys=True)).encode())[:16]
        require(not any(a['id'] == identifier for a in result['artifacts']))
        result['artifacts'].append({'id': identifier, 'name': component, 'version': version, 'type': 'binary',
            'foundBy': 'ouf-ci-source-byte-bound-native-supplement',
            'locations': [{'path': p} for p in sorted(matches)], 'licenses': [], 'language': '',
            'cpes': ([{'cpe': f'cpe:2.3:a:{vendor}:{product}:{version}:*:*:*:*:*:*:*',
                'source': 'ouf-reviewed-native-identity'}] if vendor else []),
            'purl': f'pkg:generic/{component}@{version}', 'metadataType': '', 'metadata': None})
        proof.append({'component': component, 'version': version, 'sourceDirectory': directory, 'binaryHashes': matches})
    require(covered == set(actual))
    # Static APISIX modules are inventoried from their immutable source closure.
    for module in sources['modules']:
        identifier = sha(('ouf-native-module:' + module['repository'] + ':' + module['commit']).encode())[:16]
        result['artifacts'].append({'id': identifier, 'name': module['repository'].split('/')[-1],
            'version': module['commit'], 'type': 'binary', 'foundBy': 'ouf-ci-source-byte-bound-native-supplement',
            'locations': [{'path': '/' + ROOT + 'nginx/sbin/nginx'}], 'licenses': [], 'language': '',
            'cpes': [], 'purl': 'pkg:github/' + module['repository'] + '@' + module['commit'],
            'metadataType': '', 'metadata': None})
    return result, {'nativeComponents': proof, 'nativeElfFilesIdentified': len(actual),
        'unresolvedNativeElfFiles': [], 'sourceClosureRecorded': True, 'wasmCompiled': False,
        'nativeVulnerabilityReviewComplete': False, 'dependencyCoverageAccepted': False,
        'publisherTrustAccepted': False, 'acceptanceGranted': False, 'startAuthorized': False}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--sbom', type=Path, required=True)
    p.add_argument('--sources', type=Path, required=True)
    p.add_argument('--binaries', type=Path, required=True)
    p.add_argument('--lock', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    original = json.loads(a.sbom.read_bytes())
    with a.archive.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        stream.seek(0)
        rows, config = native_files(stream, digest, a.archive.stat().st_size)
    require('sha256:' + config == original['source']['metadata']['imageID'])
    result, facts = supplement(original, rows, json.loads(a.sources.read_bytes()),
        json.loads(a.binaries.read_bytes()), json.loads(a.lock.read_bytes()))
    a.output.mkdir(mode=0o700, parents=True)
    target = a.output / 'southbound.native.syft.json'
    target.write_text(json.dumps(result, sort_keys=True) + '\n')
    facts.update(schema='ouf.semantic-rebuilt-native-identity.v1', imageId='sha256:' + config,
        imageArchiveSha256=digest, originalSyftSha256=sha(a.sbom.read_bytes()),
        supplementedSyftSha256=sha(target.read_bytes()), nativeSourceManifestSha256=sha(a.sources.read_bytes()),
        nativeBinaryManifestSha256=sha(a.binaries.read_bytes()), originalPackagesPreserved=True)
    (a.output / 'native-coverage.json').write_text(json.dumps(facts, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
