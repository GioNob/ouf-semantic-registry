"""Hosted CI: refresh evidence for the exact retained Semantic/MCP images.

No build, target access, image import, deployment, authority or provider call.
Original public artifact bytes and Sigstore subjects are verified before scanning.
"""
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
import zipfile

SEMANTIC = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(SEMANTIC))
from tools import review_semantic_image_vulnerabilities as reviewer

ROOT = Path('/root/ouf-ci-vulnerability')
OUT = Path('generated/discovery-existing-sbom-refresh').resolve()
SPECS = (
    dict(role='semantic', repo='GioNob/ouf-semantic-registry', artifact=11503486152,
         artifactSha256='22b114df0918988bc666ce2dc6bfe6cfd0c127d90493e608e973b7cfa63eb5f6',
         producer='91381f96be0a3fbd75dcdc44c22aeb90c9f12b8a',
         ref='refs/heads/codex/semantic-discovery-oss-runtime',
         source='67cb426995d7b0723e34bfe54e52ea89ae02b81d',
         image='sha256:e9730d879f171530d56843670d7d5139dd7ef2f4ee59c812a1361224392a73b3',
         user='10001:10001',
         archiveSha256='a6a9bfbaffa0396b30016a47ce948ed1c03b46b74d99b0a77299b2695ebfc107'),
    dict(role='mcp', repo='GioNob/ouf-mcp-server', artifact=11502059493,
         artifactSha256='0f7a5aa89f7ce1a26b9f6ad9a143ecd330f50635b3dc96919e3407328d165b63',
         producer='32bc369b0ab98629db82620c4ae14525ae412650',
         ref='refs/heads/codex/semantic-discovery-mcp-tools',
         source='3d51524eeddb539d6f78961447e64d9d640141c4',
         image='sha256:a0bfc5a3c4eb8710d64b7621224a373d3cfe6db03bc79fc6adbf071c3a220e47',
         user='10005:10005',
         archiveSha256='8043f74313823c0f1cf387e0802e75692930f4b83f7782c6dbad2e008cb3d2af'),
)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def require(value, reason):
    if not value:
        raise RuntimeError(reason)

def run(argv, **kwargs):
    return subprocess.run(argv, stdin=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                          timeout=240, check=True, **kwargs)

def fetch(url, limit):
    request = urllib.request.Request(url, headers={'User-Agent': 'grype 0.120.0'})
    with urllib.request.urlopen(request, timeout=30) as response:
        require(response.geturl().startswith('https://'), 'HTTPS_REQUIRED')
        raw = response.read(limit + 1)
    require(0 < len(raw) <= limit, 'DOWNLOAD_BOUND_EXCEEDED')
    return raw

def original(spec):
    role = spec['role']
    raw = run(['gh', 'api', f"repos/{spec['repo']}/actions/artifacts/{spec['artifact']}/zip"],
              stdout=subprocess.PIPE).stdout
    require(len(raw) <= 268435456 and sha(raw) == spec['artifactSha256'],
            'EXACT_ORIGINAL_ARTIFACT_REQUIRED')
    directory = ROOT / ('original-' + role)
    directory.mkdir(mode=0o700)
    subjects = (role + '.image.tar.gz', 'inventory.json', role + '.syft.json',
                role + '.grype.json', 'build-image.json')
    wanted = set(subjects) | {'provenance.json'}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = archive.infolist()
        require(len(members) <= 64 and sum(i.file_size for i in members) <= 536870912,
                'ORIGINAL_ARCHIVE_BOUND_EXCEEDED')
        names = [i.filename for i in members if not i.is_dir()]
        require(len(names) == len(set(names)), 'DUPLICATE_ARCHIVE_MEMBER')
        require(all(Path(n).name == n for n in names), 'FLAT_ORIGINAL_ARCHIVE_REQUIRED')
        require(wanted <= set(names), 'ORIGINAL_SIGNED_SUBJECT_MISSING')
        for name in sorted(wanted):
            (directory / name).write_bytes(archive.read(name))
    for name in subjects:
        with (OUT / (role + '-original-' + name + '.verification.json')).open('wb') as output:
            run(['gh', 'attestation', 'verify', str(directory / name), '--repo', spec['repo'],
                 '--signer-workflow', spec['repo'] + '/.github/workflows/signed-discovery-candidate.yml',
                 '--source-digest', spec['producer'], '--source-ref', spec['ref'],
                 '--deny-self-hosted-runners', '--bundle', str(directory / 'provenance.json'),
                 '--format', 'json'], stdout=output)
    inventory = json.loads((directory / 'inventory.json').read_bytes())
    require(inventory['imageId'] == spec['image'] and inventory['sourceCommit'] == spec['source']
            and inventory['runtimeUser'] == spec['user'] and inventory['archiveByteVerified'] is True,
            'EXACT_SIGNED_IMAGE_BINDING_REQUIRED')
    require(sha((directory / (role + '.image.tar.gz')).read_bytes()) == spec['archiveSha256'],
            'RETAINED_TARGET_ARCHIVE_BINDING_REQUIRED')
    sbom_raw = (directory / (role + '.syft.json')).read_bytes()
    document = json.loads(sbom_raw)
    require(document['source']['metadata']['imageID'] == spec['image'],
            'SIGNED_SBOM_IMAGE_BINDING_REQUIRED')
    (OUT / (role + '.syft.json')).write_bytes(sbom_raw)
    (OUT / (role + '.original-inventory.json')).write_bytes((directory / 'inventory.json').read_bytes())
    return sha(sbom_raw)

def main():
    require(os.geteuid() == 0, 'ROOT_HOSTED_SCANNER_REQUIRED')
    os.umask(0o077)
    OUT.mkdir(parents=True, mode=0o700)
    ROOT.mkdir(mode=0o700)
    bindings = {s['role']: original(s) for s in SPECS}
    listing = fetch('https://grype.anchore.io/databases/v6/latest.json', 65536)
    pin = reviewer.database_pin(json.loads(listing))
    now = datetime.datetime.now(datetime.timezone.utc).timestamp()
    built = datetime.datetime.fromisoformat(pin['built'].replace('Z', '+00:00')).timestamp()
    require(0 <= now - built <= 86400, 'DATABASE_REQUIRES_24_HOURS_REMAINING')
    (OUT / 'database-listing.json').write_bytes(listing)
    (OUT / 'database-pin.json').write_bytes(canonical(pin))
    reviewer.scanner_from_archive(fetch(
        'https://github.com/anchore/grype/releases/download/v0.120.0/grype_0.120.0_linux_amd64.tar.gz',
        reviewer.LIMIT), ROOT / 'grype')
    database = ROOT / 'database.tar.zst'
    run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--location', '--proto', '=https',
         '--tlsv1.2', '--max-time', '180', '--max-filesize', '1073741824', '--user-agent',
         'grype 0.120.0', 'https://grype.anchore.io/databases/v6/' + pin['path'],
         '--output', str(database)], stdout=subprocess.DEVNULL)
    database.chmod(0o600)
    reviewer.hash_file(database, pin['checksum'][7:], 1073741824)
    (ROOT / 'database-pin.json').write_bytes(canonical(pin))
    scans = []
    for spec in SPECS:
        role = spec['role']
        with (OUT / (role + '.grype.json')).open('wb') as output:
            run([sys.executable, '-B', str(SEMANTIC / 'tests/scan_semantic_extended_inventory.py'),
                 '--sbom', str(OUT / (role + '.syft.json'))], stdout=output)
        report_raw = (OUT / (role + '.grype.json')).read_bytes()
        report = json.loads(report_raw)
        require(not report.get('ignoredMatches'), 'IGNORED_MATCHES_FORBIDDEN')
        counts = {k: 0 for k in ('Critical', 'High', 'Medium', 'Low', 'Negligible', 'Unknown')}
        for match in report['matches']:
            counts[match['vulnerability']['severity']] += 1
        scans.append(dict(spec, unchangedSbomSha256=bindings[role], severityCounts=counts,
                          reportSha256=sha(report_raw), scannerSeverityThresholdMet=
                          not any(counts[k] for k in ('Critical', 'High', 'Unknown'))
                          and not report.get('alertsByPackage')))
    inventory = dict(schema='ouf.discovery.existing-sbom-refresh.v1', databasePin=pin,
                     scans=scans, scannerInvoked=True, networkIsolatedScanner=True,
                     allScannerSeverityThresholdsMet=all(s['scannerSeverityThresholdMet'] for s in scans),
                     imagesModified=False, targetOperations=0, acceptanceGranted=False,
                     startAuthorized=False, releaseApplied=False, notReleaseAcceptance=True)
    (OUT / 'inventory.json').write_bytes(canonical(inventory))
    files = sorted(p for p in OUT.iterdir() if p.is_file())
    (OUT / 'checksums.sha256').write_text('\n'.join(
        sha(p.read_bytes()) + '  ' + str(p.relative_to(Path.cwd())) for p in files) + '\n')
    print('OUF_DISCOVERY_FRESH_SCAN=' + json.dumps(inventory, sort_keys=True))
    # Retain and sign actual reports even if the vulnerability threshold requires review.

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        if OUT.is_dir():
            import traceback
            (OUT / 'scan-denial.json').write_bytes(canonical(dict(
                status='BLOCKED', phase='VERIFY_OR_SCAN_EXISTING_SIGNED_ARTIFACTS',
                errorType=type(error).__name__, reason=str(error) if type(error) is RuntimeError
                else 'SCANNER_OR_SOURCE_OPERATION_FAILED', targetOperations=0,
                exceptionPoints=[dict(file=Path(p.filename).name, function=p.name, line=p.lineno)
                                 for p in traceback.extract_tb(error.__traceback__)])))
        raise
