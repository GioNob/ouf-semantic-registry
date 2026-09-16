"""Validate evidence bookkeeping, never certify PET conformance."""
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
data = json.loads((root / 'evidence/ouf-pet-gap-register-v1.7.json').read_text())
assert data['normativeAuthority']['matrix'] == '1.7'
assert re.fullmatch(r'[a-f0-9]{64}', data['normativeAuthority']['packageSha256'])
versions = {'Authorization': '1.5', 'Onboarding/THS': '1.6', 'Ingestion': '1.3',
            'UDP': '1.3', 'Semantic': '1.3', 'Gateway': '1.5', 'MCP Go': '1.4'}
ids = set()
for gap in data['gaps']:
    assert gap['id'] not in ids, gap['id']
    ids.add(gap['id'])
    assert gap['petVersion'] == versions[gap['pet']], gap['id']
    assert gap['normativeReferences'] and gap['assessment'] and gap['exitCriterion'], gap['id']
    assert re.fullmatch(r'[a-f0-9]{40}', gap['baselineCommit']), gap['id']
    assert gap['baselineEvidence'] and gap['ownerRepository'].startswith('GioNob/'), gap['id']
    assert gap['status'] in {'OPEN', 'IN_PROGRESS', 'PARTIAL', 'CLOSED'}, gap['id']
    if gap['status'] == 'CLOSED':
        assert gap['closureEvidence'], gap['id']
        for evidence in gap['closureEvidence']:
            assert re.fullmatch(r'[a-f0-9]{40}', evidence['commit']), gap['id']
            assert evidence['conclusion'] == 'success' and evidence['ciUrl'] and evidence['test'], gap['id']
if data['r0']['status'] == 'CLOSED':
    assert data['r0']['evidence'], 'R0 closure requires immutable evidence'
print(f'PET register valid: {len(ids)} gap groups; this is not acceptance certification')
