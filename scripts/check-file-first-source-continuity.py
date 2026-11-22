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
composition = json.loads((root / 'evidence/m2-discovery-source-composition-20261029.json').read_text())
assert composition['baseSourceCommit'] == 'eccef11a97367f20e278db40b9ed6f45dd980c37'
assert composition['reusedDiscoverySourceCommit'] == '3ec99277b8383e496913b9fd3bb05c877825abf5'
assert composition['targetApplyAuthorized'] is False
proposal = root / baseline['addedMigration']
if hashlib.sha256(proposal.read_bytes()).hexdigest() != composition['retainedProposalMigrationSha256']:
    raise SystemExit('retained proposal migration changed')
expected_additions = {'src/main/resources/db/migration/V11__discovery_request_idempotency.sql',
                      'src/main/resources/db/migration/V12__discovery_durable_recovery.sql'}
assert set(composition['appendedMigrations']) == expected_additions
for path, digest in composition['appendedMigrations'].items():
    if hashlib.sha256((root / path).read_bytes()).hexdigest() != digest:
        raise SystemExit('composed discovery migration changed: ' + path)
expected |= expected_additions
expected.add('src/main/resources/db/migration/V13__governed_discovery_adoption.sql')
expected.add('src/main/resources/db/migration/V14__discovery_candidate_resilience.sql')
expected.add('src/main/resources/db/migration/V15__discovery_version_probe_episode.sql')
expected.add('src/main/resources/db/migration/V16__semantic_repeatability.sql')
expected.add('src/main/resources/db/migration/V17__ontology_provenance.sql')
expected.add('src/main/resources/db/migration/V18__discovery_candidate_fetch_denied.sql')
expected.add('src/main/resources/db/migration/V19__adoption_description.sql')
expected.add('src/main/resources/db/migration/V20__structured_datatypes.sql')
expected.add('src/main/resources/db/migration/V21__published_component_vocabulary.sql')
expected.add('src/main/resources/db/migration/V22__published_value_maps.sql')
actual = {p.relative_to(root).as_posix() for p in (root / 'src/main/resources/db/migration').glob('*.sql')}
if actual != expected:
    raise SystemExit('file-first migration set changed; target compatibility review required')
for name in ('SemanticIamSecurityConfiguration', 'SemanticConsultationApi', 'SemanticReadDelegation', 'ProposalCommandApi'):
    if not (root / ('src/main/java/it/comune/trieste/ouf/semantic/api/' + name + '.java')).is_file():
        raise SystemExit('required owner adapter missing: ' + name)
print('FILE_FIRST_SOURCE_CONTINUITY=PASS RETAINED_MIGRATIONS=10 APPENDED_DISCOVERY_MIGRATIONS=4 ADOPTION_MIGRATIONS=1 REPEATABILITY_MIGRATIONS=1 ONTOLOGY_PROVENANCE_MIGRATIONS=1 FETCH_EXCLUSION_MIGRATIONS=1 ADOPTION_DESCRIPTION_MIGRATIONS=1 TARGET_ACCEPTANCE=false')

