"""Verify source fixes and actual-image regressions; never change scanner decisions."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile

REPO = 'GioNob/ouf-semantic-registry'
EVIDENCE_DIGEST = 'c3a284af013942a0fc33b2a7855e84d347315f061f5bf65072101403e7a51312'
FULL_ARTIFACT = 11397709159
FULL_DIGEST = '0614b43d8843b8ebe24b4a6a4d564dfb1d36271b8660e8d0379d147a1db231c0'
IMAGE = 'sha256:516f49278f48c808427d346ad8d1520f60433d071949435774395e6c0ebc29b3'
IMAGE_ARCHIVE_DIGEST = '8b1042906bf4d48a5fc07f1e0797cbe343d1c38b9e352ee1d51dfdd6322cc6e8'
SOURCE_PREFIX = 'bundle/LuaJIT-2.1-20260824/'
SOURCE_COMMIT = 'fbfc558aacd57a54623df0ced4c31a28f81f8ff2'
PROBES = {
    'src/lj_strfmt_num.c': ['ndlo = (ndlo + 1) & 0x3f;', 'lj_strfmt_wuint9(tail, nd[ndlo]);'],
    'src/lj_snap.c': ['case IR_KNULL: return lj_ir_knull(J, irt_type(ir->t));',
                      'if (T->ir[irs->op2].o == IR_KNULL)', 'setgcrefnull(t->metatable);'],
    'src/lj_debug.c': ['if (!ins) return NO_BCPOS;'],
    'src/lj_err.c': ['lj_state_checkstack(L, LUA_MINSTACK * 2);', 'void LJ_FASTCALL lj_err_stkov(lua_State *L)'],
    'src/lj_err.h': ['LJ_FUNC_NORET void LJ_FASTCALL lj_err_stkov(lua_State *L);'],
    'src/lj_state.c': ['lj_err_stkov(L);', 'if (L->top > tvref(L->maxstack))',
                     'setframe_gc(L->base - 1 - LJ_FR2, obj2gco(L), LJ_TTHREAD);'],
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def reconcile(report, facts, sources, source_bytes, lock):
    require(lock['sourceCommit'] == SOURCE_COMMIT, 'unexpected source commit')
    expected = {r['id']: r for r in lock['findings']}
    require(set(expected) == {'CVE-2024-25176', 'CVE-2024-25177', 'CVE-2024-25178'}, 'unexpected finding set')
    counts = {k: 0 for k in ('Critical', 'High', 'Medium', 'Low', 'Negligible', 'Unknown')}
    blocking = []
    for row in report['matches']:
        v = row['vulnerability']; counts[v['severity']] += 1
        if v['severity'] in ('Critical', 'High', 'Unknown'):
            require(v['id'] in expected and v['severity'] == expected[v['id']]['severity'], 'unexpected blocker')
            a = row['artifact']
            require(a['name'] == 'luajit' and a['version'] == lock['sourceVersion'], 'unexpected component')
            require(a['purl'] == 'pkg:generic/luajit@2.1-20260824', 'unexpected package identity')
            require(v['namespace'] == 'nvd:cpe', 'unexpected advisory namespace')
            require(len(row['matchDetails']) == 1, 'ambiguous match')
            detail = row['matchDetails'][0]
            require(detail['type'] == 'cpe-match' and detail['found']['versionConstraint'] == '<= 2.1 (unknown)', 'unexpected range')
            require(detail['searchedBy']['cpes'] == ['cpe:2.3:a:luajit:luajit:2.1-20260824:*:*:*:*:*:*:*'], 'unexpected CPE')
            blocking.append(v['id'])
    require(len(blocking) == 3 and set(blocking) == set(expected), 'missing or duplicate blocker')
    require(counts == facts['severityCounts'], 'scanner count mismatch')
    require(facts['imageId'] == IMAGE and facts['scannerSeverityThresholdMet'] is False, 'unexpected image or gate')
    files = sources['sourceFiles']['compiledSourceFiles']
    require(set(source_bytes) == set(PROBES), 'incomplete source evidence')
    hashes = {}
    for path, probes in PROBES.items():
        data = source_bytes[path]; h = digest(data)
        require(files[SOURCE_PREFIX + path] == h, 'source differs from signed compiled manifest: ' + path)
        require(all(p.encode() in data for p in probes), 'fix missing: ' + path)
        hashes[path] = h
    return dict(schema='ouf.semantic-luajit-source-reconciliation.v1', imageId=IMAGE,
                sourceCommit=SOURCE_COMMIT, sourceVersion=lock['sourceVersion'], compiledSourceHashes=hashes,
                findings=[dict(id=r['id'], severity=r['severity'], fixCommit=r['fixCommit'],
                               disposition='upstream_fix_present_in_exact_compiled_source',
                               rawFindingRetained=True) for r in lock['findings']],
                rawSeverityCounts=counts, scannerSeverityThresholdMet=False,
                scannerReportModified=False, sbomModified=False, suppressionApplied=False,
                publisherTrustAccepted=False, dependencyCoverageAccepted=False,
                acceptanceGranted=False, startAuthorized=False, targetOperations=0)


def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', path], timeout=90))


def blob(repo, sha):
    response = api('/repos/' + repo + '/git/blobs/' + sha)
    require(response['sha'] == sha and response['encoding'] == 'base64', 'unexpected source blob')
    data = base64.b64decode(response['content'])
    require(len(data) < 1048576, 'oversized source blob')
    return data


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--evidence-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); root = a.evidence_root
    lock = json.loads(Path('tests/semantic-luajit-reconciliation-lock.json').read_bytes())
    archive = root / 'evidence.zip'
    require(archive.stat().st_size == 7236277 and digest(archive.read_bytes()) == EVIDENCE_DIGEST, 'wrong evidence archive')
    with zipfile.ZipFile(archive) as z:
        source_data = z.read('native-runtime-sources.json')
        binary_data = z.read('native-runtime-binaries.json')
        facts = json.loads((root/'native/native-coverage.json').read_bytes())
        require(digest(source_data) == facts['nativeSourceManifestSha256'], 'source manifest hash mismatch')
        require(digest(binary_data) == facts['nativeBinaryManifestSha256'], 'binary manifest hash mismatch')
    sources = json.loads(source_data)
    source_bytes = {r['path']: blob('openresty/luajit2', r['blob']) for r in lock['sourceFiles']}
    report = json.loads((root/'native/southbound.native.grype.json').read_bytes())
    result = reconcile(report, facts, sources, source_bytes, lock)
    ancestry = []
    for row in lock['findings']:
        compare = api('/repos/openresty/luajit2/compare/' + row['fixCommit'] + '...' + SOURCE_COMMIT)
        require(compare['merge_base_commit']['sha'] == row['fixCommit'] and compare['behind_by'] == 0, 'fix is not an ancestor')
        cna = json.loads(blob('CVEProject/cvelistV5', row['cnaBlob']))
        require(cna['cveMetadata']['cveId'] == row['id'], 'wrong CNA record')
        refs = [r['url'] for r in cna['containers']['cna']['references']]
        require('https://github.com/openresty/luajit2/commit/' + row['fixCommit'] in refs, 'CNA does not reference fix')
        ancestry.append(dict(id=row['id'], fixCommit=row['fixCommit'], sourceCommit=SOURCE_COMMIT,
                             fixIsAncestor=True, cnaRecordBlob=row['cnaBlob'], cnaRecordSha256=digest(json.dumps(cna,sort_keys=True).encode())))
    result['upstreamFixAncestry'] = ancestry
    # The full signed image is imported only into this disposable hosted CI runner.
    full = root/'full.zip'
    with full.open('xb') as out:
        subprocess.run(['gh','api',f'/repos/{REPO}/actions/artifacts/{FULL_ARTIFACT}/zip'], stdout=out, check=True, timeout=180)
    with full.open('rb') as stream:
        require(full.stat().st_size == 230682834 and hashlib.file_digest(stream,'sha256').hexdigest() == FULL_DIGEST, 'wrong full archive')
    image_archive = root/'southbound.image.tar.gz'
    with zipfile.ZipFile(full) as z:
        entry = z.getinfo('southbound.image.tar.gz')
        require(entry.file_size == 204087997, 'wrong image archive size')
        with z.open(entry) as src, image_archive.open('xb') as dst:
            import shutil
            shutil.copyfileobj(src,dst,1048576)
    with image_archive.open('rb') as stream:
        require(hashlib.file_digest(stream,'sha256').hexdigest() == IMAGE_ARCHIVE_DIGEST, 'wrong image archive bytes')
    subprocess.run(['gh','attestation','verify',str(image_archive),'--repo',REPO,'--signer-workflow',
                    REPO+'/.github/workflows/semantic-image-remediation.yml','--source-digest',
                    '1c7e31a26c664a12f2588292d38b3896b4c4e7ec','--source-ref','refs/pull/26/merge',
                    '--deny-self-hosted-runners','--bundle',str(root/'attestations/provenance.json')],check=True,timeout=90)
    subprocess.run(['docker','load','--input',str(image_archive)],check=True,timeout=180)
    command = ['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL',
               '--security-opt','no-new-privileges','--memory','128m','--pids-limit','32','--cpus','1','--user','10006:10006']
    binary_path = '/usr/local/openresty/luajit/bin/luajit-2.1.1787558776'
    actual = subprocess.check_output(command+['--entrypoint','sha256sum',IMAGE,binary_path],timeout=30).decode().split()[0]
    require(actual == json.loads(binary_data)[binary_path], 'runtime binary hash differs')
    fixtures = json.loads(Path('tests/semantic-luajit-upstream-regressions.json').read_bytes())
    regressions = []
    for cve, source in fixtures.items():
        for mode in ('jit-on','jit-off'):
            args = [] if mode == 'jit-on' else ['-joff']
            run = subprocess.run(command+['-i','--entrypoint',binary_path,IMAGE]+args+['-'],
                                 input=source.encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45)
            require(run.returncode == 0, 'upstream regression failed: '+cve+' '+mode+': '+run.stderr.decode(errors='replace')[:1000])
            regressions.append(dict(id=cve,mode=mode,exitCode=run.returncode,
                                    fixtureSha256=digest(source.encode()),stdoutSha256=digest(run.stdout)))
    result.update(fullArtifactSha256Verified=FULL_DIGEST,imageProvenanceCryptoVerified=True,
                  actualRuntimeBinarySha256=actual,actualImageRegressions=regressions,
                  runtimeTestsAreSanitizerInstrumented=False,ciImageImportPerformed=True,
                  imageImportPerformedOnTarget=False,scannerInvoked=False)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('SEMANTIC_LUAJIT_RECONCILIATION='+json.dumps(result,sort_keys=True))


if __name__ == '__main__':
    main()
