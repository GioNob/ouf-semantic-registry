# R4a Semantic inventory and publication evidence

This document separates the **read-only cold-start inventory** from the later
HUMAN publication. Normative sources: Semantic Registry PET v1.3,
Onboarding/THS PET v1.6, Gateway PET v1.5, MCP PET v1.4 and Matrix v1.7.
[Cross-module handoff](https://github.com/GioNob/ouf-semantic-registry/blob/codex/r4a-smoke-semantic-inventory/docs/handoffs/OUF_HANDOFF_2026-09-27_R4A.md).

## Chronology, 27 September 2026

| Checkpoint | Operator evidence | Meaning |
| --- | --- | --- |
| Before publication | `SEMANTIC_PUBLISHED_SETS=0`, `SEMANTIC_ACTIVE_ARTIFACTS=0` | No published set at that time; superseded by later evidence |
| Gateway cold start | 42 routes, none for the seven needed HUMAN Semantic actions | The routes were then materialized and installed with private rollback snapshot |
| Gateway acceptance | `SEMANTIC_HUMAN_ROUTES_ACTIVE=true COUNT=7`; search HTTP 200; invalid owner proposal HTTP 400 | Route and limited owner acceptance, not end-to-end ingestion |
| Reviewed RDF | `VALIDATION=PASS ERRORS=0 WARNINGS=2`; HUMAN card checked exact RDF hash | Warning count is not an approval |
| HUMAN publication | `SEMANTIC_HUMAN_PUBLICATION=PASS`, published set and manifest below | Published ontology, not an ACTIVE Onboarding source |

Asset `8ec8ae90-808a-4d9e-907c-d56de119e376`, profile
`4462692b-9c85-446b-b6fd-779f01eab64d`, eight rows,
fields `cinema` and `indirizzo`. The initial profile suggested
`cinema` as a native key; the HUMAN rejected its use as an identity key.
The DRAFT uses `MANAGED_DETERMINISTIC` asset/ordinal source-row identity.
That technical key is distinct from UDP canonical identity.

Published Semantic ID `https://api.ouf-lab.it/semantic/cinema`,
revision `51706bed-81e4-4306-aca1-70119821727d`, set
`f92a2e17-30c9-456f-bb12-63afa84f41e6`, RDF SHA-256
`4340986102db6e47345dd8157734d9db83b928edd94485f1b9a5b9e81c497a2e`,
manifest hash
`a711d0428f1cbe24c73cbf0fa5cabfcb52f85df774e7238d884e7f83f41b84e9`.
The class/property meanings use governed Semantic Registry IRIs aligned to
schema.org. Their actual values are free text with no controlled concept
code-list mapping. Mapping gives comparable meaning; it does not give
identity authority.

The Onboarding DRAFT `managed-cinema-8ec8ae90`, version
`68394f42-5c82-4127-a1f3-126516665749`, is neither submitted nor ACTIVE.
The former validator returned PASS while `UDP_RESOLUTION_CONFIGURED=false`.
A validator correction exists on the work branch but its VPS deployment is not
attested. R-SMOKE remains **OPEN**: there is no run for this asset through
Ingestion → UDP materialization → governed search.

## Repeatable read-only inventory

`scripts/r4a_semantic_inventory.py` performs a bounded query in the lab
PostgreSQL container, reporting latest published set, members and a truncation
flag. It does not read credentials or modify data. It assumes the lab
`ouf-postgres` container, `ouf_semantic` role and database; a missing
binding fails with `QUERY_FAILED`. Pin the script revision, run only when
a fresh inventory is needed, and do not repeat publication based on the
old zero-set result.

The picker rollout had previously replaced the owner-key declaration in four
managed-file MCP routes by using an old Gateway revision. A repair restored
those routes. The versioned rollout coordinator now rejects materialization
without that declaration before APISIX mutation. Keep this guard in the
installation path and preserve its rollback snapshot.

The first-party upload, Semantic publication and any future Onboarding
activation are separate transactions. No SQL fixture, direct Semantic
container call, or installed route alone substitutes for the governed
Gateway/THS acceptance.
