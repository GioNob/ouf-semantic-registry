"""Verify a signed evidence sidecar against the unchanged v2 ZIP; no runtime operations."""
import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path

SUBJECTS = ('inventory.json', 'adapter.extended.syft.json', 'southbound.extended.syft.json',
            'adapter.extended.grype.json', 'southbound.extended.grype.json')
ORIGINAL_SHA = '2cdd7a73c1fc2a710f1e6604eb6cab2988492e4c45b5252defffa9832b91d9d0'
WORKFLOW = 'GioNob/ouf-semantic-registry/.github/workflows/semantic-extended-dependency-inventory.yml'

def require(value, message):
    if not value: raise ValueError(message)

def digest(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()

def read_sidecar(path, expected_sha):
    require(digest(path) == expected_sha, 'SIDECAR_SHA_MISMATCH')
    allowed = set(SUBJECTS) | {'checksums.sha256', 'provenance.json'} | {s + '.verification.json' for s in SUBJECTS}
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        require(len(entries) == len(allowed) and {e.filename for e in entries} == allowed,
                'UNEXPECTED_SIDECAR_CONTENTS')
        require(all(not e.is_dir() and e.file_size <= 67108864 and not e.flag_bits & 1 for e in entries),
                'SIDECAR_ENTRY_BOUNDARY')
        require(sum(e.file_size for e in entries) <= 134217728, 'SIDECAR_TOTAL_BOUNDARY')
        files = {e.filename: archive.read(e) for e in entries}
    return files

def review(files, receipt):
    inventory = json.loads(files['inventory.json'])
    require(inventory['schema'] == 'ouf.semantic-extended-dependency-inventory.v1', 'INVENTORY_SCHEMA')
    require(inventory['sourceArtifactSha256'] == ORIGINAL_SHA, 'ORIGINAL_ARTIFACT_BINDING')
    require(inventory['imagesModified'] is False and inventory['originalSyftDocumentsPreserved'] is True,
            'IMAGE_PRESERVATION')
    require(inventory['containerOperations'] == 0 and inventory['scannerInvoked'] is True and
            inventory['networkIsolatedScanner'] is True, 'SCAN_BOUNDARY')
    for field in ('dependencyCoverageAccepted', 'publisherTrustAccepted', 'acceptanceGranted',
                  'runtimeRegistered', 'startAuthorized'):
        require(inventory[field] is False, 'UNEXPECTED_ACCEPTANCE:' + field)
    require({r['role'] for r in inventory['images']} == {'adapter', 'southbound'} and
            len(inventory['images']) == 2, 'IMAGE_ROLES')
    require({r['role'] for r in inventory['scans']} == {'adapter', 'southbound'} and
            len(inventory['scans']) == 2, 'SCAN_ROLES')
    for role in ('adapter', 'southbound'):
        image = next(r for r in inventory['images'] if r['role'] == role)
        original = next(r for r in receipt['candidateArchives'] if r['role'] == role)
        require(image['imageId'] == original['imageId'] and image['imageArchiveSha256'] == original['sha256'],
                'IMAGE_BINDING:' + role)
        require(hashlib.sha256(files[role + '.extended.syft.json']).hexdigest() == image['extendedSyftSha256'],
                'SBOM_BINDING:' + role)
        scan = next(r for r in inventory['scans'] if r['role'] == role)
        raw = files[role + '.extended.grype.json']; report = json.loads(raw)
        require(hashlib.sha256(raw).hexdigest() == scan['reportSha256'], 'SCAN_BINDING:' + role)
        counts = {k: 0 for k in ('Critical', 'High', 'Medium', 'Low', 'Negligible', 'Unknown')}
        for match in report['matches']: counts[match['vulnerability']['severity']] += 1
        require(counts == scan['severityCounts'] and not report.get('ignoredMatches'), 'SCAN_COUNTS:' + role)
        threshold = not any(counts[k] for k in ('Critical', 'High', 'Unknown')) and not report.get('alertsByPackage')
        require(scan['scannerSeverityThresholdMet'] is threshold, 'SCAN_THRESHOLD:' + role)
    require(inventory['allScannerSeverityThresholdsMet'] is all(s['scannerSeverityThresholdMet'] for s in inventory['scans']),
            'AGGREGATE_THRESHOLD')
    return inventory

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sidecar', type=Path, required=True)
    parser.add_argument('--sidecar-sha256', required=True)
    parser.add_argument('--original-bundle', type=Path, required=True)
    parser.add_argument('--source-merge-commit', required=True)
    parser.add_argument('--gh', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(args.gh.is_absolute(), 'GH_ABSOLUTE_PATH_REQUIRED')
    require(re.fullmatch('[0-9a-f]{40}', args.source_merge_commit), 'SOURCE_COMMIT_FORMAT')
    version = subprocess.run([str(args.gh), '--version'], check=True, capture_output=True, text=True, timeout=15)
    require(version.stdout.startswith('gh version 2.102.0 '), 'EXPECTED_GH_VERSION_2_102_0')
    require(digest(args.original_bundle) == ORIGINAL_SHA, 'ORIGINAL_ZIP_SHA_MISMATCH')
    files = read_sidecar(args.sidecar, args.sidecar_sha256)
    with zipfile.ZipFile(args.original_bundle) as archive:
        require(archive.getinfo('receipt.json').file_size <= 1048576, 'ORIGINAL_RECEIPT_BOUNDARY')
        receipt = json.loads(archive.read('receipt.json'))
    inventory = review(files, receipt)
    args.output.mkdir(mode=0o700)
    for filename, content in files.items():
        target = args.output / filename
        target.write_bytes(content); target.chmod(0o600)
    for filename in SUBJECTS:
        result = subprocess.run([str(args.gh), 'attestation', 'verify', str(args.output / filename),
            '--repo', 'GioNob/ouf-semantic-registry', '--signer-workflow', WORKFLOW,
            '--source-digest', args.source_merge_commit, '--source-ref', 'refs/pull/26/merge',
            '--deny-self-hosted-runners', '--bundle', str(args.output / 'provenance.json'), '--format', 'json'],
            check=True, capture_output=True, timeout=120)
        target = args.output / (filename + '.target-verification.json')
        target.write_bytes(result.stdout); target.chmod(0o600)
        print('FIRMA_EXTENDED_PASS=' + filename, flush=True)
    result = dict(schema='ouf.semantic-extended-evidence-target-verification.v1',
        sourceArtifactSha256=ORIGINAL_SHA, sidecarSha256=args.sidecar_sha256,
        evidenceSourceMergeCommit=args.source_merge_commit, targetAttestationCryptoVerified=True,
        allScannerSeverityThresholdsMet=inventory['allScannerSeverityThresholdsMet'],
        imageImportPerformed=False, containerOperations=0, dependencyCoverageAccepted=False,
        publisherTrustAccepted=False, acceptanceGranted=False, runtimeRegistered=False, startAuthorized=False)
    target = args.output / 'target-receipt.json'
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n'); target.chmod(0o600)
    print('OUF_EXTENDED_TARGET_CRYPTO=PASS', flush=True)
    print('OUF_EXTENDED_REPORT_DIR=' + str(args.output), flush=True)

if __name__ == '__main__': main()
