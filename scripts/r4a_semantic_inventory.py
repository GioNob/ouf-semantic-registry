#!/usr/bin/env python3
"""Read the lab Semantic publication inventory without changing the database.

Runs a single bounded SELECT through the installed PostgreSQL container. It
does not inspect Docker environment variables, tokens, or database passwords.
"""

import json
import subprocess
import sys


QUERY = """
WITH latest AS (
  SELECT publication_set_id, publication_no
  FROM ouf_sem.semantic_publication_set
  WHERE status = 'PUBLISHED'
  ORDER BY publication_no DESC LIMIT 1
), members AS (
  SELECT a.semantic_id, a.artifact_type, r.semantic_version,
         a.namespace, a.local_name, m.revision_id
  FROM ouf_sem.semantic_publication_member m
  JOIN ouf_sem.semantic_artifact a ON a.semantic_id = m.semantic_id
  JOIN ouf_sem.artifact_revision r ON r.revision_id = m.revision_id
  WHERE m.publication_set_id = (SELECT publication_set_id FROM latest)
  ORDER BY a.artifact_type, a.semantic_id LIMIT 100
)
SELECT jsonb_build_object(
  'published_sets', (SELECT count(*) FROM ouf_sem.semantic_publication_set WHERE status = 'PUBLISHED'),
  'active_artifacts', (SELECT count(*) FROM ouf_sem.artifact_active_revision),
  'latest_set_id', (SELECT publication_set_id FROM latest),
  'latest_set_no', (SELECT publication_no FROM latest),
  'member_count', (SELECT count(*) FROM ouf_sem.semantic_publication_member
                   WHERE publication_set_id = (SELECT publication_set_id FROM latest)),
  'members', (SELECT coalesce(jsonb_agg(to_jsonb(members)), '[]'::jsonb) FROM members)
);
"""


def main() -> None:
    result = subprocess.run(
        ['docker', 'exec', '-e', 'PGOPTIONS=-c default_transaction_read_only=on',
         'ouf-postgres', 'psql', '-X', '-w', '-A', '-t', '-v', 'ON_ERROR_STOP=1',
         '-U', 'ouf_semantic', '-d', 'ouf_semantic', '-c', QUERY],
        text=True, capture_output=True, timeout=20, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError('QUERY_FAILED')
    data = json.loads(result.stdout.strip())
    for key in ('published_sets', 'active_artifacts', 'member_count'):
        if not isinstance(data.get(key), int) or data[key] < 0:
            raise RuntimeError('INVALID_RESULT')
    members = data.get('members')
    if not isinstance(members, list) or len(members) > 100:
        raise RuntimeError('INVALID_RESULT')
    print('SEMANTIC_PUBLISHED_SETS=' + str(data['published_sets']))
    print('SEMANTIC_ACTIVE_ARTIFACTS=' + str(data['active_artifacts']))
    print('SEMANTIC_LATEST_SET=' + str(data['latest_set_id'] or 'NONE'))
    print('SEMANTIC_LATEST_SET_NO=' + str(data['latest_set_no'] or 'NONE'))
    print('SEMANTIC_PUBLISHED_MEMBER_COUNT=' + str(data['member_count']))
    print('SEMANTIC_MEMBER_LIST_TRUNCATED=' + str(data['member_count'] > len(members)).lower())
    for item in members:
        if not isinstance(item, dict) or not all(item.get(k) for k in
                ('semantic_id', 'artifact_type', 'semantic_version', 'revision_id')):
            raise RuntimeError('INVALID_RESULT')
        print('SEMANTIC_PUBLISHED_MEMBER=' + json.dumps(item, ensure_ascii=False, sort_keys=True))
    print('NO_WRITES=true SECRET_VALUES_NOT_READ_OR_PRINTED=true')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        code = str(exc) if isinstance(exc, RuntimeError) else type(exc).__name__.upper()
        print('SEMANTIC_INVENTORY_BLOCKED=' + code, file=sys.stderr)
        raise SystemExit(1)
