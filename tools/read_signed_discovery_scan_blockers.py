"""Read exact existing signed fresh reports; no rescan, rebuild or target action."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

OUT = Path('generated/discovery-scan-blockers')
OUT.mkdir(parents=True, exist_ok=False)
ARTIFACT_SHA = '592173f3d41765e64b046c6769610e1a178a8a9259eabeebc67fd58e4042e1fa'
SOURCE = 'd126146246453b51ae51d92e696f11cafa2e16cc'

def run(argv, **kwargs):
    return subprocess.run(argv, stdin=subprocess.DEVNULL, timeout=180, check=True, **kwargs)

raw = run(['gh', 'api', 'repos/GioNob/ouf-semantic-registry/actions/artifacts/11646112165/zip'],
          stdout=subprocess.PIPE).stdout
assert len(raw) <= 8388608 and hashlib.sha256(raw).hexdigest() == ARTIFACT_SHA
with zipfile.ZipFile(io.BytesIO(raw)) as archive:
    names = archive.namelist()
    assert len(names) == len(set(names)) and all(Path(n).name == n for n in names)
    assert sum(i.file_size for i in archive.infolist()) <= 67108864
    for name in ('inventory.json', 'semantic.grype.json', 'mcp.grype.json', 'provenance.json'):
        (OUT / name).write_bytes(archive.read(name))
for name in ('inventory.json', 'semantic.grype.json', 'mcp.grype.json'):
    with (OUT / (name + '.verification.json')).open('wb') as output:
        run(['gh', 'attestation', 'verify', str(OUT / name), '--repo', 'GioNob/ouf-semantic-registry',
             '--signer-workflow', 'GioNob/ouf-semantic-registry/.github/workflows/discovery-existing-sbom-refresh.yml',
             '--source-digest', SOURCE, '--source-ref', 'refs/heads/codex/discovery-existing-sbom-refresh-20261009',
             '--deny-self-hosted-runners', '--bundle', str(OUT / 'provenance.json'), '--format', 'json'],
            stdout=output)
inventory = json.loads((OUT / 'inventory.json').read_bytes())
result = dict(schema='ouf.discovery.signed-scan-blockers.v1', artifactSha256=ARTIFACT_SHA,
              producerCommit=SOURCE, databasePin=inventory['databasePin'], roles=[],
              targetOperations=0, acceptanceGranted=False, noRescanPerformed=True)
for scan in inventory['scans']:
    report_raw = (OUT / (scan['role'] + '.grype.json')).read_bytes()
    assert hashlib.sha256(report_raw).hexdigest() == scan['reportSha256']
    report = json.loads(report_raw)
    blockers = []
    for match in report['matches']:
        v, a = match['vulnerability'], match['artifact']
        if v['severity'] not in ('Critical', 'High', 'Unknown'):
            continue
        blockers.append(dict(id=v['id'], severity=v['severity'], namespace=v['namespace'],
                             dataSource=v.get('dataSource'), urls=v.get('urls', []),
                             fix=v.get('fix'), package=a['name'], version=a['version'],
                             packageType=a['type'], locations=a.get('locations', []),
                             relatedVulnerabilities=match.get('relatedVulnerabilities', []),
                             matchDetails=match.get('matchDetails', [])))
    result['roles'].append(dict(role=scan['role'], image=scan['image'],
                               severityCounts=scan['severityCounts'], blockers=blockers,
                               alertsByPackage=report.get('alertsByPackage', [])))
(OUT / 'blockers.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
print('OUF_DISCOVERY_SIGNED_SCAN_BLOCKERS=' + json.dumps(result, sort_keys=True))
