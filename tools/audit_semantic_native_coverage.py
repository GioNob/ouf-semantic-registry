"""Public CI bundle audit: supplement native identities, never grant acceptance.

The whole original ZIP is hash pinned. No image files are extracted to the host,
imported or executed. Original Syft packages and relationships remain intact.
"""
import argparse
import copy
import gzip
import hashlib
import json
import re
import tarfile
import tempfile
import time
import zipfile
from pathlib import Path, PurePosixPath

ORIGINAL_ZIP = 'bf369a5e445a7e84c51d0252b6714912b0d92897097f3afeb2a21c85db38fa2a'
ROOT = 'usr/local/openresty/'
CAP = 1073741824


def require(value):
    if not value:
        raise ValueError('NATIVE_COVERAGE_UNPROVEN')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def name(value):
    p = PurePosixPath(value)
    require(not p.is_absolute() and '..' not in p.parts and '\x00' not in value)
    return str(p)


def bounded(stream, limit):
    data = stream.read(limit + 1)
    require(len(data) <= limit)
    return data


def native_files(stream, archive_hash, archive_bytes):
    """Apply ordered layer replacements/whiteouts in memory; no extraction."""
    end = time.monotonic() + 180
    rows = {}
    with tempfile.TemporaryFile() as spool:
        h = hashlib.sha256()
        size = 0
        while chunk := stream.read(1048576):
            size += len(chunk)
            require(size <= CAP and time.monotonic() < end)
            h.update(chunk)
            spool.write(chunk)
        require(h.hexdigest() == archive_hash and size == archive_bytes)
        spool.seek(0)
        with tarfile.open(fileobj=spool, mode='r:') as outer:
            members = outer.getmembers()
            require(len(members) <= 1024)
            entries = {name(e.name): e for e in members}
            require(len(entries) == len(members))
            manifest = json.loads(bounded(outer.extractfile(entries['manifest.json']), 131072))
            require(len(manifest) == 1 and len(manifest[0]['Layers']) <= 256)
            config = bounded(outer.extractfile(entries[name(manifest[0]['Config'])]), 131072)
            config_hash = sha(config)
            for layer in manifest[0]['Layers']:
                updates = {}
                whiteouts = []
                with tarfile.open(fileobj=outer.extractfile(entries[name(layer)]), mode='r|*') as inner:
                    seen = set()
                    for item in inner:
                        require(time.monotonic() < end and len(seen) < 100000)
                        path = name(item.name)
                        require(path not in seen)
                        seen.add(path)
                        base = PurePosixPath(path).name
                        if base.startswith('.wh.'):
                            require(item.isfile() and item.size == 0)
                            parent = str(PurePosixPath(path).parent)
                            target = parent if base == '.wh..wh..opq' else str(PurePosixPath(parent) / base[4:])
                            whiteouts.append((target, base == '.wh..wh..opq'))
                        elif path.startswith(ROOT):
                            if item.isfile():
                                require(item.size <= CAP)
                                content = inner.extractfile(item)
                                prefix = content.read(min(item.size, 4))
                                retain = prefix == b'\x7fELF' or path.endswith('/pcre.h')
                                require(not retain or item.size <= 67108864)
                                chunks = [prefix] if retain else []
                                h = hashlib.sha256(prefix)
                                count = len(prefix)
                                while chunk := content.read(1048576):
                                    require(time.monotonic() < end)
                                    h.update(chunk)
                                    count += len(chunk)
                                    if retain:
                                        chunks.append(chunk)
                                require(count == item.size)
                                updates[path] = {'sha256': h.hexdigest(), 'bytes': count,
                                                 'elf': prefix == b'\x7fELF', 'raw': b''.join(chunks)}
                            elif item.issym() or item.islnk():
                                updates[path] = {'link': item.linkname}
                            elif item.isdir():
                                updates[path] = {'directory': True}
                            else:
                                raise ValueError('NATIVE_SPECIAL_FILE')
                        inner.members.clear()
                for target, opaque in whiteouts:
                    prefix = '' if target == '.' else target + '/'
                    for path in list(rows):
                        if (path == target and not opaque) or path.startswith(prefix):
                            del rows[path]
                rows.update(updates)
    return rows, config_hash


def wasmtime_release(stream):
    with tarfile.open(fileobj=stream, mode='r:xz') as source:
        matches = [e for e in source.getmembers() if e.isfile() and name(e.name).endswith('/lib/libwasmtime.so')]
        require(len(matches) == 1)
        return sha(bounded(source.extractfile(matches[0]), 67108864))


def supplement(original, rows, release_hash):
    """Explicit CPE identities; unresolved components remain unresolved."""
    require(rows[ROOT + 'wasmtime-c-api/lib/libwasmtime.so']['sha256'] == release_hash)
    pcre = rows[ROOT + 'pcre/lib/libpcre.so.1.2.13']['raw']
    require(b'8.45 2021-06-15\x00' in pcre)
    header = rows[ROOT + 'pcre/include/pcre.h']['raw']
    require(re.search(rb'#define PCRE_MAJOR\s+8\b', header) and re.search(rb'#define PCRE_MINOR\s+45\b', header))
    # Versions of custom copies are tied below to actual bytes and runtime proof
    # from the hash-pinned original CI bundle, not inferred from OS packages.
    components = [
        ('openssl', '3.4.8', 'openssl', 'openssl', ROOT + 'openssl3/lib/libssl.so.3'),
        ('zlib', '1.3.2.1-motley', 'zlib', 'zlib', ROOT + 'zlib/lib/libz.so.1.3.2.1-motley'),
        ('pcre', '8.45', 'pcre', 'pcre', ROOT + 'pcre/lib/libpcre.so.1.2.13'),
        ('wasmtime', '0.38.1', 'bytecodealliance', 'wasmtime', ROOT + 'wasmtime-c-api/lib/libwasmtime.so'),
    ]
    result = copy.deepcopy(original)
    evidence = []
    for component, version, vendor, product, path in components:
        require(rows[path]['elf'])
        identifier = sha(('ouf-native:' + component + ':' + rows[path]['sha256']).encode())[:16]
        require(not any(a['id'] == identifier for a in result['artifacts']))
        result['artifacts'].append({'id': identifier, 'name': component, 'version': version, 'type': 'binary',
            'foundBy': 'ouf-byte-bound-native-supplement', 'locations': [{'path': '/' + path}],
            'licenses': [], 'language': '', 'cpes': [{'cpe': f'cpe:2.3:a:{vendor}:{product}:{version}:*:*:*:*:*:*:*',
            'source': 'ouf-reviewed-native-identity'}], 'purl': f'pkg:generic/{component}@{version}',
            'metadataType': '', 'metadata': None})
        evidence.append({'component': component, 'version': version, 'path': '/' + path,
                         'sha256': rows[path]['sha256']})
    # Package ownership by APISIX alone is not an identity/version for embedded libraries.
    known_prefixes = [ROOT + p for p in ('openssl3/', 'zlib/', 'pcre/', 'wasmtime-c-api/')]
    unresolved = [{'path': '/' + path, 'sha256': row['sha256']}
                  for path, row in sorted(rows.items()) if row.get('elf')
                  and not any(path.startswith(p) for p in known_prefixes)]
    inventory = [{'path': '/' + path, 'sha256': row['sha256'], 'bytes': row['bytes']}
                 for path, row in sorted(rows.items()) if row.get('elf')]
    return result, {'components': evidence, 'nativeElfFiles': inventory,
                    'unresolvedNativeIdentities': unresolved, 'dependencyCoverageAccepted': False,
                    'acceptanceGranted': False, 'startAuthorized': False}


def audit(bundle_path, release_path, output):
    with bundle_path.open('rb') as stream:
        require(hashlib.file_digest(stream, 'sha256').hexdigest() == ORIGINAL_ZIP)
    with zipfile.ZipFile(bundle_path) as bundle:
        infos = bundle.infolist()
        require(len(infos) <= 2048 and len({i.filename for i in infos}) == len(infos))
        require(all(name(i.filename) == i.filename and i.file_size <= CAP for i in infos))
        receipt = json.loads(bundle.read('receipt.json'))
        row = next(r for r in receipt['images'] if r['role'] == 'southbound')
        raw = bundle.read('sbom/southbound.syft.json')
        require(sha(raw) == row['syftJsonSha256'])
        record = next(r for r in receipt['candidateArchives'] if r['role'] == 'southbound')
        with bundle.open(record['file']) as compressed, gzip.GzipFile(fileobj=compressed) as plain:
            rows, config_hash = native_files(plain, record['uncompressedSha256'], record['uncompressedBytes'])
        require('sha256:' + config_hash == row['imageId'])
        # Cross-check custom SSL bytes against the original runtime proof.
        proof = bundle.read('bundled-openssl-runtime-proof.txt').decode()
        for lib in ('libssl.so.3', 'libcrypto.so.3'):
            require(rows[ROOT + 'openssl3/lib/' + lib]['sha256'] + '  /' + ROOT + 'openssl3/lib/' + lib in proof)
        require('OpenSSL 3.4.8' in proof)
        zlib = rows[ROOT + 'zlib/lib/libz.so.1.3.2.1-motley']['raw']
        require(b'1.3.2.1-motley\x00' in zlib)
        with release_path.open('rb') as release:
            release_hash = wasmtime_release(release)
        sbom, result = supplement(json.loads(raw), rows, release_hash)
    output.mkdir(mode=0o700, parents=True)
    (output / 'southbound.native.syft.json').write_text(json.dumps(sbom, sort_keys=True) + '\n')
    result.update(schema='ouf.semantic-native-coverage-audit.v1', sourceArtifactSha256=ORIGINAL_ZIP,
                  imageId=row['imageId'], originalSyftSha256=sha(raw),
                  supplementedSyftSha256=sha((output / 'southbound.native.syft.json').read_bytes()),
                  wasmtimeReleaseBinarySha256=release_hash, originalPackagesPreserved=True,
                  scannerInvoked=False, imageImportPerformed=False, containerOperations=0)
    (output / 'native-coverage.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--wasmtime-release', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    audit(args.bundle, args.wasmtime_release, args.output)
