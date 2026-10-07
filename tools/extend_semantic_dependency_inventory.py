"""Extend inventory for existing signed archives without changing images or granting trust."""
import argparse
import copy
import gzip
import hashlib
import json
import re
import shlex
import struct
import tarfile
import tempfile
import time
import zipfile
from pathlib import Path, PurePosixPath
from tools.audit_semantic_native_coverage import name, bounded, require, sha
from tools.review_semantic_static_module_coverage import review

CAP = 1073741824
PREFIX = 'usr/local/openresty/'
NGINX = PREFIX + 'nginx/sbin/nginx'

def image_files(stream, expected_hash, expected_bytes):
    """Fold layer changes; hash every regular file; never extract or execute payloads."""
    rows = {}; end = time.monotonic() + 240
    with tempfile.TemporaryFile() as spool:
        digest = hashlib.sha256(); size = 0
        while chunk := stream.read(1048576):
            size += len(chunk); require(size <= CAP and time.monotonic() < end)
            digest.update(chunk); spool.write(chunk)
        require(size == expected_bytes and digest.hexdigest() == expected_hash)
        spool.seek(0)
        with tarfile.open(fileobj=spool, mode='r:') as outer:
            entries = {name(m.name): m for m in outer.getmembers()}
            require(len(entries) == len(outer.getmembers()) and len(entries) <= 1024)
            manifests = json.loads(bounded(outer.extractfile(entries['manifest.json']), 131072))
            require(len(manifests) == 1 and len(manifests[0]['Layers']) <= 256)
            config = bounded(outer.extractfile(entries[name(manifests[0]['Config'])]), 131072)
            for layer in manifests[0]['Layers']:
                updates = {}; whiteouts = []; seen = set()
                with tarfile.open(fileobj=outer.extractfile(entries[name(layer)]), mode='r|*') as inner:
                    for item in inner:
                        require(time.monotonic() < end and len(seen) < 100000)
                        path = name(item.name); require(path not in seen); seen.add(path)
                        base = PurePosixPath(path).name
                        if base.startswith('.wh.'):
                            require(item.isfile() and item.size == 0)
                            parent = str(PurePosixPath(path).parent)
                            whiteouts.append((parent if base == '.wh..wh..opq' else str(PurePosixPath(parent) / base[4:]), base == '.wh..wh..opq'))
                        elif item.isfile():
                            require(0 <= item.size <= CAP)
                            retain = path == NGINX or path.startswith('usr/local/brotli/') or path == 'usr/local/lib/libpython3.so' or path == 'usr/local/openresty/luajit/share/luajit-2.1/jit/vmdef.lua' or base == 'rock_manifest'
                            require(not retain or item.size <= 67108864)
                            content = inner.extractfile(item); first = content.read(min(4, item.size))
                            sha256 = hashlib.sha256(first); md5 = hashlib.md5(first, usedforsecurity=False)
                            chunks = [first] if retain else []; count = len(first)
                            while chunk := content.read(1048576):
                                require(time.monotonic() < end)
                                sha256.update(chunk); md5.update(chunk); count += len(chunk)
                                if retain: chunks.append(chunk)
                            require(count == item.size)
                            updates[path] = dict(sha256=sha256.hexdigest(), md5=md5.hexdigest(), bytes=count,
                                                 elf=first == b'\x7fELF', raw=b''.join(chunks))
                        elif item.issym() or item.islnk(): updates[path] = {'link': item.linkname}
                        elif item.isdir(): updates[path] = {'directory': True}
                        else: require(False)
                        inner.members.clear()
                for target, opaque in whiteouts:
                    prefix = '' if target == '.' else target + '/'
                    for path in list(rows):
                        if (path == target and not opaque) or path.startswith(prefix): del rows[path]
                rows.update(updates)
    return rows, sha(config)

def literal_manifest(raw):
    """Parse only LuaRocks' literal map grammar, never evaluate Lua."""
    text = raw.decode('utf-8'); tokens = []; at = 0
    pattern = re.compile(r'\s+|"(?:[^"\\]|\\["\\])*"|[A-Za-z_][A-Za-z_0-9]*|[{}\[\]=,;]')
    while at < len(text):
        match = pattern.match(text, at); require(match is not None)
        value = match.group(); at = match.end()
        if not value.isspace(): tokens.append(value)
    require(len(tokens) < 100000 and tokens[:2] == ['rock_manifest', '='])
    position = 2
    def take():
        nonlocal position
        require(position < len(tokens)); value = tokens[position]; position += 1; return value
    def table(depth=0):
        require(depth < 32 and take() == '{'); result = {}
        while tokens[position] != '}':
            key = take()
            if key == '[':
                key = take(); require(key.startswith('"')); key = json.loads(key); require(take() == ']')
            else: require(re.fullmatch('[A-Za-z_][A-Za-z_0-9]*', key))
            require(key not in result and take() == '=')
            if tokens[position] == '{': value = table(depth + 1)
            else:
                value = take(); require(value.startswith('"')); value = json.loads(value)
            result[key] = value
            if tokens[position] in (',', ';'): take()
            else: require(tokens[position] == '}')
        take(); return result
    result = table(); require(position == len(tokens)); return result

def leaves(tree, prefix=''):
    for key, value in tree.items():
        require('/' not in key and key not in ('.', '..') and '\x00' not in key)
        path = prefix + key
        if isinstance(value, dict): yield from leaves(value, path + '/')
        else:
            require(re.fullmatch('[0-9a-f]{32}', value)); yield path, value

def add_package(document, identity, version, repository, paths):
    identifier = sha(('ouf-extended:' + identity + ':' + version + ':' + json.dumps(sorted(paths))).encode())[:16]
    require(not any(p['id'] == identifier for p in document['artifacts']))
    document['artifacts'].append(dict(id=identifier, name=identity, version=version, type='binary',
        foundBy='ouf-byte-bound-source-inventory', locations=[{'path': '/' + p} for p in sorted(paths)],
        licenses=[], language='', cpes=[], purl='pkg:github/' + repository + '@' + version,
        metadataType='', metadata=None))

def constant_elf_function(raw, symbol):
    """Read a constant-return amd64 version accessor, without executing its ELF."""
    require(raw[:6] == b'\x7fELF\x02\x01' and struct.unpack_from('<H', raw, 18)[0] == 62)
    shoff = struct.unpack_from('<Q', raw, 40)[0]
    shsize, count = struct.unpack_from('<HH', raw, 58)
    require(shsize == 64 and 0 < count <= 4096 and shoff + shsize * count <= len(raw))
    sections = [struct.unpack_from('<IIQQQQIIQQ', raw, shoff + n * shsize) for n in range(count)]
    values = []
    for section in sections:
        if section[1] != 11: continue
        require(section[9] == 24 and section[6] < count and section[4] + section[5] <= len(raw))
        strings = sections[section[6]]; require(strings[4] + strings[5] <= len(raw))
        names = raw[strings[4]:strings[4] + strings[5]]
        for offset in range(section[4], section[4] + section[5], 24):
            label, info, _, index, address, size = struct.unpack_from('<IBBHQQ', raw, offset)
            require(label < len(names))
            if names[label:].split(b'\x00', 1)[0] != symbol.encode(): continue
            require(info & 15 == 2 and index < count and 0 < size <= 64)
            text = sections[index]; start = text[4] + address - text[3]
            require(start >= text[4] and start + size <= text[4] + text[5] <= len(raw))
            body = raw[start:start + size]
            if body.startswith(b'\xf3\x0f\x1e\xfa'): body = body[4:]
            require(len(body) == 6 and body[:1] == b'\xb8' and body[-1:] == b'\xc3')
            values.append(struct.unpack_from('<I', body, 1)[0])
    require(len(values) == 1); return values[0]

def add_brotli(document, rows):
    prefix = 'usr/local/brotli/'
    files = {p: r for p, r in rows.items() if p.startswith(prefix) and r.get('elf')}
    require(set(files) == {prefix + 'bin/brotli', prefix + 'lib/libbrotlicommon.so.1.1.0',
                           prefix + 'lib/libbrotlidec.so.1.1.0', prefix + 'lib/libbrotlienc.so.1.1.0'})
    enc = constant_elf_function(files[prefix + 'lib/libbrotlienc.so.1.1.0']['raw'], 'BrotliEncoderVersion')
    dec = constant_elf_function(files[prefix + 'lib/libbrotlidec.so.1.1.0']['raw'], 'BrotliDecoderVersion')
    require(enc == dec == 0x01001000)
    add_package(document, 'brotli', '1.1.0', 'google/brotli', files)
    document['artifacts'][-1]['cpes'] = [{'cpe':'cpe:2.3:a:google:brotli:1.1.0:*:*:*:*:*:*:*','source':'ouf-byte-bound-native-version-accessor'}]
    return dict(component='brotli', version='1.1.0', inheritedFromBaseImage=True,
                versionEvidence='Identical constant-return encoder/decoder ELF accessors, read without execution',
                installedFileSha256={p:r['sha256'] for p,r in files.items()}, upstreamSourceProvenanceAccepted=False)

def extend(original, sources, rows, configure):
    document = copy.deepcopy(original)
    elf = rows[NGINX]['raw']
    # Nginx may concatenate its display label with NGX_CONFIGURE in the ELF.
    # Reuse the recorded line only after requiring the exact bytes in the ELF.
    static = review(configure, elf, sources, document)
    additions = []
    for row in static['modules']:
        directory = row['directory']; version = directory.split('-', 1)[1]
        archive = next(a for a in sources['openresty']['archives'] if a['sha256'] == row['sourceArchiveSha256'])
        tag = re.search(r'(?:/tarball/|/archive/(?:refs/tags/)?)([^/]+?)(?:\.tar\.gz)?$', archive['url'])
        require(tag is not None)
        version = tag.group(1)
        if version.startswith('v'): version = version[1:]
        add_package(document, row['repository'].split('/')[-1], version, row['repository'], [NGINX])
        additions.append(dict(component=row['repository'], version=version, kind='compiled-static-module',
                              sourceDirectory=directory, sourceArchiveSha256=row['sourceArchiveSha256'],
                              installedFileSha256={NGINX: rows[NGINX]['sha256']}))
    # Map exact installed Lua hashes to the complete source manifests, including patched/copy-overridden sources.
    by_hash = {}
    for path, digest in sources['sourceFiles']['compiledSourceFiles'].items():
        if path.endswith('.lua') and path.startswith('bundle/'):
            by_hash.setdefault(digest, []).append(('bundle', path.split('/')[1], path))
    for module in sources['sourceFiles']['modules']:
        for path, digest in module['files'].items():
            if path.endswith('.lua'): by_hash.setdefault(digest, []).append(('module', module['directory'], path))
    lua_groups = {}; unresolved_lua = []
    for path, record in rows.items():
        if not path.startswith(PREFIX) or not path.endswith('.lua') or 'sha256' not in record: continue
        matches = by_hash.get(record['sha256'], [])
        if not matches:
            unresolved_lua.append(path); continue
        # Identical installed bytes can occur in more than one source component.
        # Retain every proven association rather than guessing one owner.
        for kind, directory, source_path in matches:
            lua_groups.setdefault(directory, {})[path] = dict(sha256=record['sha256'], sourceFile=source_path)
    for directory, files in sorted(lua_groups.items()):
        module = next((m for m in sources['modules'] if m['directory'] == directory), None)
        # The OpenResty slot has been replaced with the API7 pinned source before hashing.
        if directory == 'lua-resty-limit-traffic-0.09': module = next(m for m in sources['modules'] if m['repository'] == 'api7/lua-resty-limit-traffic')
        if module: repository = module['repository']; version = module['commit']; source_hash = None
        else:
            archive_directory = directory
            for old, new in (('ngx_lua-', 'lua-nginx-module-'), ('ngx_lua_upstream-', 'lua-upstream-nginx-module-'), ('ngx_stream_lua-', 'stream-lua-nginx-module-')):
                if directory.startswith(old): archive_directory = new + directory[len(old):]
            archive = next((a for a in sources['openresty']['archives'] if a['file'] == archive_directory + '.tar.gz'), None)
            require(archive is not None)
            match = re.match(r'https://github\.com/([^/]+/[^/]+)/', archive['url']); require(match is not None)
            repository = match.group(1)
            tag = re.search(r'(?:/tarball/|/archive/(?:refs/tags/)?)([^/]+?)(?:\.tar\.gz)?$', archive['url'])
            require(tag is not None); version = tag.group(1).removeprefix('v')
            # LuaJIT and the renamed ngx_* build directories are handled separately below.
            if directory.startswith('LuaJIT-'): repository = 'openresty/luajit2'; version = directory[len('LuaJIT-'):]
            require(version); source_hash = archive['sha256']
        existing = next((p for p in document['artifacts'] if p['name'] == repository.split('/')[-1]), None)
        if directory.startswith('LuaJIT-'):
            existing = next(p for p in document['artifacts'] if p['name'] == 'luajit')
        if existing:
            version = existing['version']
            locations = {l['path'] for l in existing['locations']}
            existing['locations'] += [{'path': '/' + p} for p in sorted(files) if '/' + p not in locations]
        else:
            add_package(document, repository.split('/')[-1], version, repository, files)
        additions.append(dict(component=repository, version=version, kind='installed-lua-source',
                              sourceDirectory=directory, sourceArchiveSha256=source_hash, files=files))
    return document, dict(staticModuleInventory=static, additions=additions,
                          installedOpenRestyLuaFiles=sum(len(f) for f in lua_groups.values()),
                          unresolvedOpenRestyLuaFiles=unresolved_lua)

def rock_bindings(document, rows):
    """Keep all catalogued versions, bind deployed files where manifests agree."""
    by_md5 = {}
    runtime_prefix = 'usr/local/apisix/deps/'
    for path, row in rows.items():
        if path.startswith(runtime_prefix) and 'md5' in row: by_md5.setdefault(row['md5'], []).append(path)
    records = []; unbound = []
    for package in document['artifacts']:
        if package['type'] != 'lua-rocks': continue
        specs = [l['path'].lstrip('/') for l in package['locations'] if l['path'].endswith('.rockspec')]
        require(len(specs) == 1); manifest_path = str(PurePosixPath(specs[0]).parent / 'rock_manifest')
        require(manifest_path in rows and rows[manifest_path]['raw'])
        manifest = literal_manifest(rows[manifest_path]['raw']); files = {}
        for section in ('lua', 'lib'):
            for relative, md5 in leaves(manifest.get(section, {})):
                candidates = [p for p in by_md5.get(md5, []) if ('/share/lua/' in p if section == 'lua' else '/lib/lua/' in p)]
                if not candidates: unbound.append(dict(package=package['name'], version=package['version'], manifestFile=relative, kind=section))
                for path in candidates: files[path] = rows[path]['sha256']
        existing = {l['path'] for l in package['locations']}
        package['locations'] += [{'path': '/' + p} for p in sorted(files) if '/' + p not in existing]
        records.append(dict(package=package['name'], version=package['version'], manifestPath=manifest_path,
                            manifestSha256=rows[manifest_path]['sha256'], installedFileSha256=files))
    return dict(rocks=records, unboundRockManifestFiles=unbound,
                associationMethod='Archive-bound rock_manifest MD5 associations; measured installed SHA256 retained. Not upstream source provenance.')

def ownership(document, rows):
    claimed = {}
    def resolve(path):
        path = name(path.lstrip('/'))
        for _ in range(24):
            parts = path.split('/'); replaced = False
            for n in range(1, len(parts) + 1):
                prefix = '/'.join(parts[:n]); link = rows.get(prefix, {}).get('link')
                if link is None: continue
                target = link.lstrip('/') if link.startswith('/') else str(PurePosixPath(prefix).parent / link)
                combined = target.split('/') + parts[n:]; normalized = []
                for part in combined:
                    if part in ('', '.'): continue
                    if part == '..': require(normalized); normalized.pop()
                    else: normalized.append(part)
                path = '/'.join(normalized); replaced = True; break
            if not replaced: return path
        require(False)
    for package in document['artifacts']:
        paths = [l.get('path', '') for l in package.get('locations', [])]
        paths += [f.get('path', '') for f in (package.get('metadata') or {}).get('files', [])]
        for path in paths:
            # Python RECORD may use paths relative to site-packages. Do not
            # guess a base for such entries; native ownership remains explicit.
            if path and '..' not in path.split('/'):
                claimed.setdefault(resolve(path), set()).add(package['id'])
    resolved = []; unresolved = []
    python = next((p for p in document['artifacts'] if p['name'] == 'python' and p['type'] == 'binary'), None)
    for path, row in sorted(rows.items()):
        if not row.get('elf'): continue
        owners = claimed.get(path, set())
        if not owners and python and ((path.startswith('usr/local/lib/python3.13/') and '/site-packages/' not in path) or path.startswith('usr/local/lib/libpython3.13') or (path == 'usr/local/lib/libpython3.so' and b'libpython3.13.so.1.0\x00' in row['raw'])):
            owners = {python['id']}
        record = dict(path=path, sha256=row['sha256'], packageIds=sorted(owners))
        (resolved if owners else unresolved).append(record)
    return dict(elfFileCount=len(resolved) + len(unresolved), identifiedElfFiles=resolved, unresolvedElfFiles=unresolved)

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--sha256', required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.bundle.open('rb') as stream: require(hashlib.file_digest(stream, 'sha256').hexdigest() == args.sha256)
    args.output.mkdir(mode=0o700)
    with zipfile.ZipFile(args.bundle) as z:
        require(len(z.namelist()) == len(set(z.namelist())))
        def read(path): require(z.getinfo(path).file_size <= 67108864); return z.read(path)
        receipt = json.loads(read('receipt.json')); sources_raw = read('native-runtime-sources.json')
        native_raw = read('native/southbound.native.syft.json')
        require(sha(sources_raw) == receipt['nativeScan']['nativeSourceManifestSha256'])
        require(sha(native_raw) == receipt['nativeScan']['supplementedSyftSha256'])
        results = []
        for role in ('adapter', 'southbound'):
            archive = next(r for r in receipt['candidateArchives'] if r['role'] == role)
            with z.open(role + '.image.tar.gz') as incoming, gzip.GzipFile(fileobj=incoming) as plain:
                rows, config = image_files(plain, archive['uncompressedSha256'], archive['uncompressedBytes'])
            require('sha256:' + config == archive['imageId'])
            original = json.loads(read('native/southbound.native.syft.json' if role == 'southbound' else 'sbom/adapter.syft.json'))
            document = copy.deepcopy(original); details = {}
            if role == 'southbound':
                lines = read('native-runtime-link-proof.txt').decode().splitlines()
                arguments = [line[len('configure arguments: '):] for line in lines if line.startswith('configure arguments: ')]
                require(len(arguments) == 1)
                document, details = extend(original, json.loads(sources_raw), rows, arguments[0])
                details['luaRocks'] = rock_bindings(document, rows)
                details['brotli'] = add_brotli(document, rows)
            details['elfOwnership'] = ownership(document, rows)
            output = args.output / (role + '.extended.syft.json')
            output.write_text(json.dumps(document, sort_keys=True) + '\n')
            # Original metadata stays present; added deployed paths only enrich locations.
            require(all(any(p['id'] == old['id'] and p['name'] == old['name'] and p['version'] == old['version'] for p in document['artifacts']) for old in original['artifacts']))
            results.append(dict(role=role, imageId=archive['imageId'], imageArchiveSha256=archive['sha256'],
                                extendedSyftSha256=sha(output.read_bytes()), packageCount=len(document['artifacts']), **details))
        result = dict(schema='ouf.semantic-extended-dependency-inventory.v1', sourceArtifactSha256=args.sha256,
                      images=results, imagesModified=False, originalSyftDocumentsPreserved=True,
                      scannerInvoked=False, containerOperations=0, dependencyCoverageAccepted=False,
                      publisherTrustAccepted=False, acceptanceGranted=False, runtimeRegistered=False, startAuthorized=False)
        (args.output / 'inventory.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
        print('SEMANTIC_EXTENDED_INVENTORY=' + json.dumps(result, sort_keys=True))

if __name__ == '__main__': main()
