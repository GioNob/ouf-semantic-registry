"""Bind the source-built CI native payload to the exact scanned image archive.

Keep the original Syft output intact and emit a separate supplemented document.
Source closure and identity evidence do not confer publisher trust/acceptance.
"""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from tools.audit_semantic_native_coverage import ROOT, native_files, require, sha


def luajit_runtime_version(rows, sources):
    """Use the version built into both ELFs, retaining the separate source tag."""
    paths = [p for p, row in rows.items() if row.get('elf') and p.startswith(ROOT + 'luajit/')]
    require(len(paths) == 2)
    versions = set()
    for path in paths:
        name = re.fullmatch(re.escape(ROOT) + r'luajit/(?:bin/luajit-|lib/libluajit-5\.1\.so\.)(2\.1\.[0-9]{9,12})', path)
        require(name is not None)
        version = name.group(1)
        embedded = set(v.decode('ascii') for v in re.findall(rb'LuaJIT (2\.1\.[0-9]{9,12})(?![0-9])', rows[path]['raw']))
        require(embedded == {version})
        versions.add(version)
    require(len(versions) == 1)
    version = versions.pop()
    relver = (version.split('.')[-1] + '\n').encode('ascii')
    require(sources['sourceFiles']['compiledSourceFiles']['bundle/LuaJIT-2.1-20260824/.relver'] == sha(relver))
    return version


def supplement(original, rows, sources, binaries, lock):
    require(all(sources[k] == v for k, v in lock.items()))
    require(sources['wasm']['compiled'] is False)
    require(not any('wasmtime' in p or 'wasm-nginx-module' in p for p in rows))
    actual = {'/' + p: r['sha256'] for p, r in rows.items() if r.get('elf')}
    require(actual == binaries and len(actual) >= 10)
    luajit_version = luajit_runtime_version(rows, sources)
    embedded = sources['embeddedSourceDirectories']
    components = [
        ('openssl', '3.4.8', 'openssl', 'openssl', 'openssl3/', None),
        ('zlib', '1.3.2.1-motley', 'zlib', 'zlib', 'zlib/', None),
        ('pcre', '8.45', 'pcre', 'pcre', 'pcre/', None),
        ('luajit', luajit_version, 'luajit', 'luajit', 'luajit/', 'LuaJIT-2.1-20260824'),
        ('lua-cjson', '2.1.0.19', None, None, 'lualib/cjson.so', 'lua-cjson-2.1.0.19'),
        ('lua-resty-signal', '0.05', None, None, 'lualib/librestysignal.so', 'lua-resty-signal-0.05'),
        ('lua-redis-parser', '0.13', None, None, 'lualib/redis/parser.so', 'lua-redis-parser-0.13'),
        ('openresty', '1.31.6.1', 'openresty', 'openresty', 'nginx/sbin/nginx', 'nginx-1.31.6'),
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
            require(all(b'1.3.2.1-motley\x00' in rows[p[1:]]['raw'] for p in matches))
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
        if component == 'luajit':
            proof[-1].update(sourceReleaseTag='v2.1-20260824',
                             versionEvidence='Both ELF embedded LuaJIT versions, installed names and compiled .relver hash agree')
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
        'nativeIdentityScope': '/' + ROOT, 'unresolvedNativeElfFiles': [], 'sourceClosureRecorded': True, 'wasmCompiled': False,
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
