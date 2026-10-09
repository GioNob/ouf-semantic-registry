"""Hosted CI: refresh vulnerability evidence for the two unchanged signed images."""
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

SPECS = {
    'semantic': dict(repo='GioNob/ouf-semantic-registry', artifact=11503486152,
        zipSha='22b114df0918988bc666ce2dc6bfe6cfd0c127d90493e608e973b7cfa63eb5f6',
        producer='91381f96be0a3fbd75dcdc44c22aeb90c9f12b8a',
        ref='refs/heads/codex/semantic-discovery-oss-runtime',
        source='67cb426995d7b0723e34bfe54e52ea89ae02b81d',
        image='sha256:e9730d879f171530d56843670d7d5139dd7ef2f4ee59c812a1361224392a73b3',
        archiveSha='a6a9bfbaffa0396b30016a47ce948ed1c03b46b74d99b0a77299b2695ebfc107'),
    'mcp': dict(repo='GioNob/ouf-mcp-server', artifact=11502059493,
        zipSha='0f7a5aa89f7ce1a26b9f6ad9a143ecd330f50635b3dc96919e3407328d165b63',
        producer='32bc369b0ab98629db82620c4ae14525ae412650',
        ref='refs/heads/codex/semantic-discovery-mcp-tools',
        source='3d51524eeddb539d6f78961447e64d9d640141c4',
        image='sha256:a0bfc5a3c4eb8710d64b7621224a373d3cfe6db03bc79fc6adbf071c3a220e47',
        archiveSha='8043f74313823c0f1cf387e0802e75692930f4b83f7782c6dbad2e008cb3d2af')}
SEVERITIES = ('Critical', 'High', 'Medium', 'Low', 'Negligible', 'Unknown')

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def extract_subjects(raw, spec, role, root):
    require(sha(raw) == spec['zipSha'], 'ORIGINAL_ARTIFACT_ZIP_HASH_MISMATCH')
    names = ('inventory.json', 'build-image.json', role+'.syft.json', role+'.grype.json', 'provenance.json')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = archive.infolist()
        require(len(members) <= 64 and len({m.filename for m in members}) == len(members), 'ARTIFACT_MEMBER_BOUND_OR_DUPLICATE')
        require(all(Path(m.filename).name == m.filename and not m.is_dir() for m in members), 'FLAT_ARTIFACT_REQUIRED')
        require(sum(m.file_size for m in members) <= 1073741824, 'ARTIFACT_EXPANSION_BOUND')
        for name in names:
            item = archive.getinfo(name)
            require(0 < item.file_size <= 67108864, 'SIGNED_SUBJECT_SIZE_BOUND')
            (root/name).write_bytes(archive.read(item))
        item = archive.getinfo(role+'.image.tar.gz')
        require(0 < item.file_size <= 536870912, 'IMAGE_ARCHIVE_BOUND')
        digest = hashlib.sha256()
        with archive.open(item) as stream:
            while chunk := stream.read(1048576):
                digest.update(chunk)
        require(digest.hexdigest() == spec['archiveSha'], 'STAGED_ARCHIVE_HASH_MISMATCH')
    return names[:-1]

def binding(root, spec, role):
    inventory = json.loads((root/'inventory.json').read_bytes())
    image = json.loads((root/'build-image.json').read_bytes())[0]
    document = json.loads((root/(role+'.syft.json')).read_bytes())
    require(inventory['sourceCommit'] == spec['source'] and inventory['imageId'] == image['Id'] == spec['image'], 'ORIGINAL_SOURCE_IMAGE_MISMATCH')
    require(inventory['archiveByteVerified'] is True and inventory['thresholdMet'] is True, 'ORIGINAL_SCAN_BINDING_UNPROVEN')
    import base64
    config = base64.b64decode(document['source']['metadata']['config'], validate=True)
    require(document['source']['metadata']['imageID'] == spec['image'] == 'sha256:'+sha(config), 'SIGNED_SBOM_CONFIG_BINDING_MISMATCH')
    return document

def scan_summary(raw, pin):
    report = json.loads(raw)
    require(report['descriptor']['version'] == '0.120.0', 'SCANNER_VERSION_MISMATCH')
    db = report['descriptor']['db']['status']
    require(db['built'] == pin['built'] and db['schemaVersion'] == pin['schemaVersion'] and db['valid'] is True and not db.get('error'), 'FRESH_DATABASE_REPORT_MISMATCH')
    require(not report.get('ignoredMatches'), 'IGNORED_MATCHES_NOT_ALLOWED')
    counts = dict.fromkeys(SEVERITIES, 0)
    advisories = set()
    for match in report['matches']:
        severity = match['vulnerability']['severity']
        require(severity in counts, 'UNRECOGNIZED_SEVERITY')
        counts[severity] += 1
        if severity in ('Critical', 'High'):
            advisories.add(match['vulnerability']['id'])
    return dict(severityCounts=counts, packageAlertCount=len(report.get('alertsByPackage') or []),
        highCriticalAdvisoryIds=sorted(advisories), thresholdMet=not any(counts[k] for k in ('Critical','High','Unknown')) and not report.get('alertsByPackage'))

def main():
    phase = 'INITIALIZE'
    output = Path('generated/discovery-existing-sbom-refresh').resolve()
    try:
        require(os.geteuid() == 0 and os.environ.get('GITHUB_ACTIONS') == 'true' and os.environ.get('RUNNER_ENVIRONMENT') == 'github-hosted', 'HOSTED_CI_ONLY')
        os.umask(0o077)
        output.mkdir(parents=True, mode=0o700)
        source = Path(sys.argv[1]).resolve()
        sys.path.insert(0, str(source))
        from tools import review_semantic_image_vulnerabilities as reviewer
        root = Path('/root/ouf-ci-vulnerability')
        root.mkdir(mode=0o700)
        def run(argv, **kwargs):
            result = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, timeout=400, **kwargs)
            if result.returncode:
                (output/'command-failure.json').write_bytes(canonical(dict(phase=phase, executable=Path(argv[0]).name, exitCode=result.returncode, stdoutSha256=sha(result.stdout), stderrSha256=sha(result.stderr))))
                raise ValueError('NATIVE_COMMAND_FAILED')
            return result.stdout
        def fetch(url, limit):
            request = urllib.request.Request(url, headers={'User-Agent':'grype 0.120.0'})
            with urllib.request.urlopen(request, timeout=60) as response:
                require(response.geturl().startswith('https://'), 'HTTPS_REQUIRED')
                raw = response.read(limit+1)
            require(0 < len(raw) <= limit, 'PUBLIC_DOWNLOAD_BOUND')
            return raw
        documents = {}
        for role, spec in SPECS.items():
            phase = 'VERIFY_ORIGINAL_'+role.upper()
            folder = root/role
            folder.mkdir(mode=0o700)
            raw = run(['gh','api',f"repos/{spec['repo']}/actions/artifacts/{spec['artifact']}/zip"])
            require(len(raw) <= 536870912, 'ARTIFACT_ZIP_BOUND')
            names = extract_subjects(raw, spec, role, folder)
            for name in names:
                verified = run(['gh','attestation','verify',str(folder/name),'--repo',spec['repo'],
                    '--signer-workflow',spec['repo']+'/.github/workflows/signed-discovery-candidate.yml',
                    '--source-digest',spec['producer'],'--source-ref',spec['ref'],'--deny-self-hosted-runners',
                    '--bundle',str(folder/'provenance.json'),'--format','json'])
                (output/(role+'.original-'+name+'.verification.json')).write_bytes(verified)
            documents[role] = binding(folder, spec, role)
            (output/(role+'.syft.json')).write_bytes((folder/(role+'.syft.json')).read_bytes())
        phase = 'FREEZE_FRESH_DATABASE'
        listing = fetch('https://grype.anchore.io/databases/v6/latest.json', 65536)
        pin = reviewer.database_pin(json.loads(listing))
        built = datetime.datetime.fromisoformat(pin['built'].replace('Z','+00:00'))
        require(0 <= (datetime.datetime.now(datetime.timezone.utc)-built).total_seconds() <= 86400, 'DATABASE_REQUIRES_24_HOURS_REMAINING')
        (output/'database-listing.json').write_bytes(listing)
        (output/'database-pin.json').write_bytes(canonical(pin))
        reviewer.scanner_from_archive(fetch('https://github.com/anchore/grype/releases/download/v0.120.0/grype_0.120.0_linux_amd64.tar.gz', reviewer.LIMIT), root/'grype')
        database = root/'database.tar.zst'
        run(['/usr/bin/curl','--fail','--silent','--show-error','--location','--proto','=https','--tlsv1.2',
             '--max-time','180','--max-filesize','1073741824','--user-agent','grype 0.120.0',
             'https://grype.anchore.io/databases/v6/'+pin['path'],'--output',str(database)])
        database.chmod(0o600)
        reviewer.hash_file(database, pin['checksum'][7:], 1073741824)
        (root/'database-pin.json').write_bytes(canonical(pin))
        rows = []
        for role, spec in SPECS.items():
            phase = 'OFFLINE_SCAN_'+role.upper()
            raw = run([sys.executable,'-B',str(source/'tests/scan_semantic_extended_inventory.py'),'--sbom',str(output/(role+'.syft.json'))])
            (output/(role+'.grype.json')).write_bytes(raw)
            facts = scan_summary(raw, pin)
            facts.update(role=role, sourceCommit=spec['source'], imageId=spec['image'], archiveSha256=spec['archiveSha'],
                originalArtifactId=spec['artifact'], originalArtifactZipSha256=spec['zipSha'], originalProducerCommit=spec['producer'],
                originalSignaturesVerified=4, unchangedSbomSha256=sha((output/(role+'.syft.json')).read_bytes()),
                reportSha256=sha(raw), packageCount=len(documents[role]['artifacts']))
            rows.append(facts)
        reviewer.database_pin(pin)
        result = dict(schema='ouf.discovery.existing-sbom-fresh-scan.v1', databasePin=pin,
            validUntil=(built+datetime.timedelta(hours=48)).isoformat().replace('+00:00','Z'), roles=rows,
            allSeverityThresholdsMet=all(r['thresholdMet'] for r in rows), networkIsolatedScanners=True,
            imagesModified=False, targetOperations=0, acceptanceGranted=False, startAuthorized=False, notReleaseAcceptance=True)
        (output/'inventory.json').write_bytes(canonical(result))
        files = sorted(output.iterdir())
        (output/'checksums.sha256').write_text(''.join(sha(p.read_bytes())+'  '+str(p.relative_to(Path.cwd()))+'\n' for p in files if p.is_file()))
        print('OUF_DISCOVERY_FRESH_SCAN='+json.dumps(result,sort_keys=True))
        return 0
    except Exception as exc:
        reason = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        diagnostic = dict(status='BLOCKED', phase=phase, reason=reason, evidenceDirectory=str(output), targetOperations=0)
        if output.is_dir():
            (output/'failure.json').write_bytes(canonical(diagnostic))
        print('OUF_DISCOVERY_FRESH_SCAN='+json.dumps(diagnostic,sort_keys=True))
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
