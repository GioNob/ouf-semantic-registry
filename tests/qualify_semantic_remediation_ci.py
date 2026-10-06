"""Exercise the same standalone byte qualifier on the actual signed CI bundle."""
import hashlib,json,os,subprocess,sys,zipfile
from pathlib import Path
semantic=Path(__file__).resolve().parents[1]
out=semantic/'generated/alpine-ubuntu-source-fixed'
receipt=json.loads((out/'receipt.json').read_text())
assert receipt['allScannerSeverityThresholdsMet'] is True
bundle=Path(os.environ['RUNNER_TEMP'])/'ouf-remediation-qualified-input.zip'
with zipfile.ZipFile(bundle,'x',compression=zipfile.ZIP_STORED) as archive:
    for path in sorted(out.rglob('*')):
        if path.is_file():
            assert not path.is_symlink()
            archive.write(path,str(path.relative_to(out)))
with bundle.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
result=subprocess.run(['sudo','/usr/bin/python3','-I','-B',str(semantic/'tools/semantic_remediation_bundle_qualifier.py'),
    '--bundle',str(bundle),'--root','/root/ouf-ci-remediation-qualification','--sha256',digest,
    '--ci-commit',receipt['semanticBuildCommit']],check=True,capture_output=True,text=True,timeout=480)
print(result.stdout)
qualified=json.loads(subprocess.check_output(['sudo','cat','/root/ouf-ci-remediation-qualification/receipt.json'],text=True))
assert qualified['sourceArtifactSha256']==digest and len(qualified['images'])==2
assert all(row['bytesVerified'] is True for row in qualified['images'])
assert all(qualified[key] is False for key in ('imageImportPerformed','scannerInvoked','acceptanceGranted','runtimeRegistered','startAuthorized'))
assert qualified['containerOperations']==0
(out/'byte-qualification-ci.json').write_text(json.dumps(qualified,indent=2,sort_keys=True)+'\n')
