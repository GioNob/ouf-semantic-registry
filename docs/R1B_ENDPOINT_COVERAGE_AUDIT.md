# R1b endpoint coverage audit — owner enforcement follow-up

Authority: PET Authorization 1.5 §§109.2–109.3, 36.10, 34.2 and Semantic 1.3 §§65/160.7. `evidence/r1b-endpoint-inventory.json` is a refreshed source inventory, not universal route acceptance. Executed evidence is recorded in `R1B_OWNER_ENFORCEMENT_EVIDENCE.md` and the PET gap register.

| Boundary | Implemented enforcement | Executed evidence |
|---|---|---|
| Authorization admin/distribution | Existing HUMAN/admin/CSRF/ETag/audit and SERVICE bundle-read guards retained | R1b administrative/cache tests and unchanged common Java/Go vectors |
| All Semantic API routes | Fail-closed declared operation capability before argument binding; owner resource ID and same policy snapshot; separate search/review; non-ACTIVE artifact visibility needs propose/review | Runtime HTTP route enumeration without grants, anonymous/coarse-forged negatives, draft restriction and publication lifecycle |
| Onboarding protected logs | Configured platform audit-owner namespace, HUMAN, explicit SECURITY_SENSITIVE policy, exact decision reference | HTTP boundary: missing detail, wrong namespace, positive policy and audit reference |
| Ingestion Operational Awareness | Persisted/query-derived source/job resources, explicit TENANT_OPERATIONAL detail, projection before output; protected references removed; denied summary UNKNOWN | HTTP controller/projection/evaluator tests with stubbed DB rows, positive scoped source and denial/partial cases |
| Ingestion protected logs | Configured platform audit-owner namespace, HUMAN, explicit SECURITY_SENSITIVE policy before search/aggregate | Both HTTP routes: actor/detail/namespace negatives and positive decision reference; existing runtime event/audit tests |
| UDP current/history/search/relationships/lineage | Persisted resource/DAL/source/job checks; object target visibility; separate geometry/source-identity/raw grants; supplied allowed-label attribute ignored | Real PostgreSQL HTTP projection tests for forged labels, wrong object, source/job deny and denied relationship target; existing domain runtime suite |
| UDP graph and related search | Per-edge DAL/source/job and both object endpoints; traversal cannot cross a denied path | Real PostgreSQL HTTP tests for neighbors/traverse/related-search, positive controls, target and source/job denials |
| UDP spatial queries | Object and geometry visibility plus operation policy on each hit and anchor; no denied IDs/distances; same DB snapshot | Real PostGIS HTTP tests for nearby/intersects/within/intersection-search, restricted DAL and geometry source/job/anchor denials |
| MCP | Existing common Go policy/cache implementation; owner remains authoritative | Prior Java/Go conformance; no evaluator semantics or common vector changes in SDK 1.2 |

SDK 1.2 `OwnerAuthorization.candidates()` permits admission only. Owners evaluate real resources through `decide`/`require` using the same immutable request snapshot. Query candidate labels do not grant visibility. Filtered query responses explicitly report partial results.

This closes the concrete Semantic, serving/query, OA and protected-log defects listed above. It does not certify every domain governance, historical-contract or runtime-issue projection through the real Gateway/MCP/THS path. AUT-02 records the delivered SDK/adapter criterion; AUT-03 retains the remaining cross-owner projection acceptance scope. AUT-04 retains real IAM/workload/THS authentication, CSRF, claims, rotation and revocation acceptance. Future endpoints need their own resource-policy tests.

Both protected-log stores are platform-wide. `ouf.protected-log.tenant-id` identifies the platform audit-owner namespace, not a SQL tenant filter; absent configuration denies. Deployment policies must restrict it to operators authorized for the whole store. No resolved migration decision was reopened.
