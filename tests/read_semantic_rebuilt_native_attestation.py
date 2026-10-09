"""Read immutable public CI evidence; verify its signature without image operations."""
import base64, collections, hashlib, json, os, subprocess, zipfile
from pathlib import Path

ARTIFACT=11397838781
DIGEST='c3a284af013942a0fc33b2a7855e84d347315f061f5bf65072101403e7a51312'
RUN=37433261779
REPO='GioNob/ouf-semantic-registry'
CODE='385809bde50a20e4987c9c55c2b57a614dc240e0'
root=Path(os.environ['RUNNER_TEMP'])/'ouf-rebuilt-native-evidence-readback'
root.mkdir()
archive=root/'evidence.zip'
with archive.open('xb') as out:
    subprocess.run(['gh','api',f'/repos/{REPO}/actions/artifacts/{ARTIFACT}/zip'],stdout=out,check=True,timeout=120)
assert archive.stat().st_size==7236277 and hashlib.sha256(archive.read_bytes()).hexdigest()==DIGEST
with zipfile.ZipFile(archive) as z:
    names=z.namelist()
    assert len(names)==len(set(names)) and sum(x.file_size for x in z.infolist())<268435456
    for name in ('native/native-coverage.json','native/southbound.native.syft.json','native/southbound.native.grype.json','attestations/provenance.json'):
        assert 0<z.getinfo(name).file_size<16777216
        (root/name).parent.mkdir(parents=True,exist_ok=True)
        (root/name).write_bytes(z.read(name))
bundle=json.loads((root/'attestations/provenance.json').read_bytes())
statement=json.loads(base64.b64decode(bundle['dsseEnvelope']['payload']))
assert statement['predicate']['runDetails']['metadata']['invocationId']==f'https://github.com/{REPO}/actions/runs/{RUN}/attempts/1'
deps=statement['predicate']['buildDefinition']['resolvedDependencies']
commits=[r['digest']['gitCommit'] for r in deps if 'gitCommit' in r.get('digest',{})]
assert len(commits)==1
merge=commits[0]
commit=json.loads(subprocess.check_output(['gh','api',f'/repos/{REPO}/git/commits/{merge}'],timeout=60))
assert CODE in [p['sha'] for p in commit['parents']]
for name in ('native/native-coverage.json','native/southbound.native.syft.json','native/southbound.native.grype.json'):
    expected=hashlib.sha256((root/name).read_bytes()).hexdigest()
    rows=[r for r in statement['subject'] if (r['name']==name or r['name'].endswith('/'+name))]
    assert len(rows)==1 and rows[0]['digest']['sha256']==expected
    subprocess.run(['gh','attestation','verify',str(root/name),'--repo',REPO,'--signer-workflow',
        REPO+'/.github/workflows/semantic-image-remediation.yml','--source-digest',merge,
        '--source-ref','refs/pull/26/merge','--deny-self-hosted-runners',
        '--bundle',str(root/'attestations/provenance.json'),'--format','json'],check=True,stdout=subprocess.DEVNULL,timeout=90)
report=json.loads((root/'native/southbound.native.grype.json').read_bytes())
facts=json.loads((root/'native/native-coverage.json').read_bytes())
counts={k:0 for k in ('Critical','High','Medium','Low','Negligible','Unknown')}
findings=[]
for row in report['matches']:
    v=row['vulnerability'];a=row['artifact'];counts[v['severity']]+=1
    if v['severity'] in ('Critical','High','Unknown'):
        findings.append(dict(id=v['id'],severity=v['severity'],package=a['name'],version=a['version'],namespace=v['namespace']))
assert counts==facts['severityCounts']
assert facts['wasmCompiled'] is False and facts['nativeElfFilesIdentified']==17 and facts['unresolvedNativeElfFiles']==[]
result=dict(schema='ouf.semantic-rebuilt-native-attestation-readback.v1',artifactId=ARTIFACT,artifactSha256=DIGEST,
    nativeElfFilesIdentified=facts['nativeElfFilesIdentified'],wasmCompiled=facts['wasmCompiled'],sourceRun=RUN,sourceCodeCommit=CODE,sourceMergeCommit=merge,wholeArchiveHashVerified=True,
    supplementalAttestationIndependentlyCryptoVerified=True,severityCounts=counts,blockingFindings=findings,
    scannerInvoked=False,containerOperations=0,targetModified=False,publisherTrustAccepted=False,
    dependencyCoverageAccepted=False,acceptanceGranted=False,startAuthorized=False)
print('SEMANTIC_REBUILT_NATIVE_ATTESTATION_READBACK='+json.dumps(result,sort_keys=True))
