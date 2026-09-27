# R4a Semantic inventory for managed-file onboarding

After a file is staged and profiled, the PET R-SMOKE gate requires a governed
Semantic publication and human-reviewed mapping before an Onboarding DRAFT is
created. Do not substitute example IRIs or CI fixtures for live references.

`scripts/r4a_semantic_inventory.py` performs one read-only, bounded query in
the lab PostgreSQL container. It reports the latest published set, its member
identities and versions, and whether the first 100-member listing is truncated.
It does not read credentials or modify the database. Run the script from an
exact reviewed repository revision as `oufadmin` on the lab VPS. The script
assumes the existing lab container `ouf-postgres`, role `ouf_semantic`, and
database `ouf_semantic`; a missing binding stops with `QUERY_FAILED`.

If `SEMANTIC_PUBLISHED_SETS=0`, first perform the governed Semantic DRAFT,
validation, HUMAN approval and publication workflow. A published member list
is evidence for review, not automatic approval of a class/property mapping.
The operator must review `cinema` and `indirizzo` field classifications and
select exact published class/property references before invoking
`source.onboarding.create`. Continue R-SMOKE through Ingestion and UDP only
after the governed Onboarding configuration is approved and active.

Regression record (27 September 2026): the coordinated picker rollout pinned
an older Gateway revision and overwrote the owner-key declaration in four
managed-file MCP routes. The repair restored those routes; the coordinator
now pins the corrected Gateway revision and rejects any materialization that
omits the declaration before mutating APISIX. Keep that guard in the reusable
installation/configuration path.

## Lab observation, 27 September 2026

The pinned read-only inventory returned `published_sets=0`,
`active_artifacts=0`, and no latest set. The real picker staged asset
`8ec8ae90-808a-4d9e-907c-d56de119e376`; Onboarding profile
`4462692b-9c85-446b-b6fd-779f01eab64d` succeeded with eight CSV rows,
fields `cinema` and `indirizzo`, and a proposed native key `cinema` awaiting
human review. No Onboarding DRAFT, Semantic publication, Ingestion run or UDP
object was produced by these checks.

The versioned Gateway catalogue currently contains an internal
`ouf.semantic.read` reference-resolution route but no route materialization
for the Semantic proposal/validation/HUMAN approval/publication lifecycle.
The Semantic service implements these owner endpoints; they must be wired
through Gateway with exact capability, IAM scope and Authorization grants
before a cold-start publication can be exercised on this installation.
Do not call the Semantic container directly or insert a publication with SQL
to bypass the governed path. Bundle this bootstrap in a reusable installer
with readback and rollback rather than an operator sequence of raw commands.
