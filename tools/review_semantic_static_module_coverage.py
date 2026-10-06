"""Audit static module identities in the existing v2 bundle; never grant acceptance."""
import argparse
import gzip
import hashlib
import json
import re
import shlex
import zipfile
from pathlib import Path, PurePosixPath
from tools.audit_semantic_native_coverage import native_files, require

ALIASES = {
    'ngx_lua': 'lua-nginx-module',
    'ngx_stream_lua': 'stream-lua-nginx-module',
    'ngx_lua_upstream': 'lua-upstream-nginx-module',
}

def review(configure, elf, sources, supplemented):
    require(isinstance(configure, str) and configure.encode() in elf)
    tokens = shlex.split(configure)
    paths = [t.split('=', 1)[1] for t in tokens if t.startswith('--add-module=')]
    require(paths and len(paths) == len(set(paths)))
    archives = sources['openresty']['archives']
    embedded = set(sources['embeddedSourceDirectories'])
    compiled = sources['sourceFiles']['compiledSourceFiles']
    records = []
    for path in paths:
        if not path.startswith('../'):
            continue
        directory = PurePosixPath(path).name
        require(path == '../' + directory and directory in embedded)
        matched = [a for a in archives if a['file'] == directory + '.tar.gz']
        if not matched:
            alias = next((v for k, v in ALIASES.items() if directory.startswith(k + '-')), None)
            require(alias is not None)
            version = directory.split('-', 1)[1]
            matched = [a for a in archives if a['file'] == alias + '-' + version + '.tar.gz']
        require(len(matched) == 1)
        archive = matched[0]
        repository = re.match(r'https://github\.com/([^/]+/[^/]+)/', archive['url'])
        require(repository is not None and re.fullmatch('[0-9a-f]{64}', archive['sha256']))
        prefix = 'bundle/' + directory + '/'
        file_hashes = {p: h for p, h in compiled.items() if p.startswith(prefix)}
        require(file_hashes and all(re.fullmatch('[0-9a-f]{64}', h) for h in file_hashes.values()))
        name = repository.group(1).split('/')[-1]
        represented = [
            p for p in supplemented['artifacts']
            if p['name'] in {name, directory}
            and any(l.get('path') == '/usr/local/openresty/nginx/sbin/nginx' for l in p.get('locations', []))
        ]
        records.append(dict(directory=directory, repository=repository.group(1),
                            sourceArchiveSha256=archive['sha256'],
                            compiledSourceFileCount=len(file_hashes),
                            individuallyRepresentedInSupplement=bool(represented)))
    require(records)
    return dict(schema='ouf.semantic-static-module-coverage-review.v1',
                configureArgumentsBoundToActualNginxElf=True,
                configuredBundledModuleCount=len(records), modules=records,
                unrepresentedStaticModules=[r['directory'] for r in records if not r['individuallyRepresentedInSupplement']],
                originalSbomModified=False, scannerInvoked=False, imageImportPerformed=False,
                dependencyCoverageAccepted=False, publisherTrustAccepted=False,
                acceptanceGranted=False, startAuthorized=False)

def bundle_review(bundle_path, expected_zip_hash):
    with bundle_path.open('rb') as stream:
        require(hashlib.file_digest(stream, 'sha256').hexdigest() == expected_zip_hash)
    with zipfile.ZipFile(bundle_path) as z:
        require(len(z.namelist()) == len(set(z.namelist())))
        def read(name):
            info = z.getinfo(name)
            require(0 < info.file_size <= 67108864)
            return z.read(name)
        receipt = json.loads(read('receipt.json'))
        facts = json.loads(read('native/native-coverage.json'))
        require(facts == receipt['nativeScan'])
        source_raw = read('native-runtime-sources.json')
        sbom_raw = read('native/southbound.native.syft.json')
        require(hashlib.sha256(source_raw).hexdigest() == facts['nativeSourceManifestSha256'])
        require(hashlib.sha256(sbom_raw).hexdigest() == facts['supplementedSyftSha256'])
        record = next(r for r in receipt['candidateArchives'] if r['role'] == 'southbound')
        with z.open('southbound.image.tar.gz') as incoming, gzip.GzipFile(fileobj=incoming) as plain:
            rows, config = native_files(plain, record['uncompressedSha256'], record['uncompressedBytes'])
        require('sha256:' + config == facts['imageId'])
        elf = rows['usr/local/openresty/nginx/sbin/nginx']['raw']
        lines = read('native-runtime-link-proof.txt').decode().splitlines()
        configure = [line[len('configure arguments: '):] for line in lines if line.startswith('configure arguments: ')]
        require(len(configure) == 1)
        result = review(configure[0], elf, json.loads(source_raw), json.loads(sbom_raw))
        result.update(sourceArtifactSha256=expected_zip_hash, imageId=facts['imageId'],
                      nativeSourceManifestSha256=facts['nativeSourceManifestSha256'],
                      supplementedSyftSha256=facts['supplementedSyftSha256'])
        return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = bundle_review(args.bundle, args.sha256)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print('SEMANTIC_STATIC_MODULE_COVERAGE=' + json.dumps(result, sort_keys=True))

if __name__ == '__main__':
    main()
