# R1b owner enforcement evidence

Normative authority remains the attached Reality Baseline Package v1.7, particularly Authorization 1.5 §§109, 36.10 and 34.2 and Semantic 1.3 §§65/160.7. This report records implementation evidence; it does not amend PET acceptance criteria.

The follow-up adds the request-bound owner evaluator in Java SDK 1.2.0, canonical source commit `0bf7a926e7a348a02f348e2444a020f135769a80`. All three Java consumers pin byte-identical mirrors. Java/Go decision semantics and the 28 common vectors are unchanged. Runtime bundle pinning and freshness remain authoritative for each decision.

| Delivered boundary | Pull request | Validation |
|---|---|---|
| SDK and Onboarding protected logs | [Onboarding #11](https://github.com/GioNob/ouf-source-onboarding/pull/11) | SDK resource/snapshot test, HTTP log detail/namespace boundary, complete module CI |
| Semantic route enforcement | [Semantic #7](https://github.com/GioNob/ouf-semantic-registry/pull/7) | 47 module tests, including 6 HTTP tests and registered-route enumeration; all four CI workflows green |
| Ingestion Operational Awareness | [Ingestion #21](https://github.com/GioNob/ouf-ingestion-runtime/pull/21) | Real HTTP/evaluator/projection with controlled rows: source/detail denial, minimized evidence, UNKNOWN summary; complete module CI and SDK pairwise |
| Ingestion protected logs | [Ingestion #22](https://github.com/GioNob/ouf-ingestion-runtime/pull/22) | Both HTTP routes deny missing detail, AI actor, missing/wrong namespace before data access; positive HUMAN policy and exact audit reference |
| UDP serving, graph, related and spatial queries | [UDP #25](https://github.com/GioNob/ouf-udp-object-resolution/pull/25) | 95 module tests with PostgreSQL/PostGIS, including graph 10 and spatial 6; SDK pairwise, performance, DR and supply-chain/deployment gates |

Immutable commits, merge commits, CI runs and artifact metadata are in `evidence/ouf-pet-gap-register-v1.7.json`, section `r1bOwnerEnforcement`. CI artifact identifiers and digests are GitHub metadata; archive contents have not been independently downloaded and hashed. Java 21/Maven execution occurred in CI, not in the local editing workspace.

Semantic development failures were corrected without weakening gates: select the application MVC handler mapping explicitly when Actuator registers another mapping; store route inventory in `evidence/`, preserving the schema-only `contracts/` directory. Historical failed runs remain visible.

Operational requirements: register the separated Semantic search/review.prepare capabilities and scopes; configure protected-log owner namespaces and explicit SECURITY_SENSITIVE grants; grant object/geometry visibility alongside UDP query capabilities as appropriate. Missing required configuration or detail grants fail closed. Do not infer namespaces or grant authority from user-supplied headers/attributes.

Remaining work is explicit: real IAM/SSO/workload/THS binding and revocation/rotation acceptance (AUT-04/R6); full owner projection acceptance for governance/historical/runtime-issue routes and channel-neutral Gateway/MCP paths (AUT-03/R2–R6). R2a is the next vertical: approved ACTIVE source bundle must start file/PULL ingestion automatically, using the same authorization constraints. Module fixtures are not proof of that full path.
