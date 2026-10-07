"""Reverify and byte-qualify one immutable, actually downloadable Actions ZIP."""
import argparse,hashlib,json,os,subprocess,zipfile
from pathlib import Path

def require(ok):
    if not ok:raise ValueError('IMMUTABLE_ARTIFACT_QUALIFICATION_UNPROVEN')
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--lock',type=Path,required=True)
    a=p.parse_args();pin=json.loads(a.lock.read_bytes());repo='GioNob/ouf-semantic-registry'
    root=Path(os.environ['RUNNER_TEMP'])/'ouf-downloaded-v2-artifact';root.mkdir(mode=0o700)
    full=root/'bundle.zip'
    with full.open('xb') as output:
        subprocess.run(['gh','api',f"/repos/{repo}/actions/artifacts/{pin['artifactId']}/zip"],stdout=output,check=True,timeout=180)
    with full.open('rb') as stream:
        require(full.stat().st_size==pin['artifactBytes'] and hashlib.file_digest(stream,'sha256').hexdigest()==pin['artifactSha256'])
    commit=json.loads(subprocess.check_output(['gh','api',f"/repos/{repo}/git/commits/{pin['sourceMergeCommit']}"],timeout=60))
    require(pin['sourceCodeCommit'] in [p['sha'] for p in commit['parents']])
    names=('adapter.image.tar.gz','southbound.image.tar.gz','attestations/provenance.json','attestations/adapter-sbom.json','attestations/southbound-sbom.json',
           'native/native-coverage.json','native/southbound.native.syft.json','native/southbound.native.grype.json')
    with zipfile.ZipFile(full) as z:
        require(len(z.namelist())==len(set(z.namelist())))
        for name in names:
            info=z.getinfo(name);require(0<info.file_size<=1073741824)
            target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
            with z.open(name) as incoming,target.open('xb') as output:
                import shutil
                shutil.copyfileobj(incoming,output,1048576)
    expected_workflow=repo+'/.github/workflows/semantic-image-remediation.yml'
    flags=['--repo',repo,'--signer-workflow',expected_workflow,'--source-digest',pin['sourceMergeCommit'],
           '--source-ref','refs/pull/26/merge','--deny-self-hosted-runners']
    for name in ('adapter.image.tar.gz','southbound.image.tar.gz','native/native-coverage.json','native/southbound.native.syft.json','native/southbound.native.grype.json'):
        subprocess.run(['gh','attestation','verify',str(root/name)]+flags+['--bundle',str(root/'attestations/provenance.json')],
                       check=True,stdout=subprocess.DEVNULL,timeout=90)
    for role in ('adapter','southbound'):
        subprocess.run(['gh','attestation','verify',str(root/(role+'.image.tar.gz'))]+flags+
                       ['--bundle',str(root/('attestations/'+role+'-sbom.json')),'--predicate-type','https://spdx.dev/Document/v2.3'],
                       check=True,stdout=subprocess.DEVNULL,timeout=90)
    q=Path('tools/semantic_remediation_bundle_qualifier.py')
    require(hashlib.sha256(q.read_bytes()).hexdigest()==pin['qualifierSha256'])
    run=subprocess.run(['sudo','/usr/bin/python3','-I','-B',str(q),'--bundle',str(full),
                        '--root','/root/ouf-ci-remediation-qualification','--sha256',pin['artifactSha256'],
                        '--ci-commit',pin['sourceMergeCommit'],'--historical-evidence'],check=True,capture_output=True,text=True,timeout=480)
    tag='SEMANTIC_REMEDIATION_BYTE_QUALIFICATION='
    lines=[s for s in run.stdout.splitlines() if s.startswith(tag)];require(len(lines)==1)
    receipt=json.loads(lines[0][len(tag):])
    require(receipt['sourceArtifactSha256']==pin['artifactSha256'] and receipt['nativeEvidenceByteVerified'] is True)
    require(all(r['bytesVerified'] is True for r in receipt['images']))
    require(receipt['historicalEvidenceOnly'] is True and receipt['currentVulnerabilityScanProven'] is False)
    require(all(receipt[k] is False for k in ('scannerInvoked','imageImportPerformed','acceptanceGranted','runtimeRegistered','startAuthorized')))
    subprocess.run(['/usr/bin/python3','-B','-m','tools.review_semantic_static_module_coverage',
                    '--bundle',str(full),'--sha256',pin['artifactSha256'],
                    '--output','generated/static-module-coverage-review.json'],check=True,timeout=240)
    result=dict(schema='ouf.semantic-downloaded-remediation-artifact-qualification.v1',producer=pin,
                wholeArchiveHashVerified=True,archiveAttestationsIndependentlyCryptoVerified=True,
                nativeAttestationsIndependentlyCryptoVerified=True,actualDownloadedZipByteQualified=True,
                byteQualification=receipt,targetOperations=0,targetModified=False,
                acceptanceGranted=False,startAuthorized=False)
    out=Path('generated/downloaded-v2-artifact-qualification.json');out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('SEMANTIC_DOWNLOADED_ARTIFACT_QUALIFICATION='+json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
