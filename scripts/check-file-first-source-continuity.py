#!/usr/bin/env python3
"""Prevent a file-first package from dropping existing IAM/read behavior again."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
baseline = json.loads((root / 'evidence/file-first-source-baseline-20261014.json').read_text())
for path, digest in baseline['migrationSha256'].items():
    if hashlib.sha256((root / path).read_bytes()).hexdigest() != digest:
        raise SystemExit('retained migration changed: ' + path)
expected = set(baseline['migrationSha256']) | {baseline['addedMigration']}
actual = {str(p.relative_to(root)) for p in (root / 'src/main/resources/db/migration').glob('*.sql')}
if actual != expected:
    raise SystemExit('file-first migration set changed; target compatibility review required')
for name in ('SemanticIamSecurityConfiguration', 'SemanticConsultationApi', 'SemanticReadDelegation', 'ProposalCommandApi'):
    if not (root / ('src/main/java/it/comune/trieste/ouf/semantic/api/' + name + '.java')).is_file():
        raise SystemExit('required owner adapter missing: ' + name)
print('FILE_FIRST_SOURCE_CONTINUITY=PASS RETAINED_MIGRATIONS=9 ADDED_MIGRATIONS=1 TARGET_ACCEPTANCE=false')
