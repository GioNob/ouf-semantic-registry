# Independent technical review — OUF Semantic Model Registry

Reviewed commit: `7c76997489f2df8e213a2f2920f71efffd9b89cb`  
Normative order: L0 invariants > Semantic Registry PET v1.3 > frozen contracts > implementation/tests.

## Executive result

The first remediation closed the critical actor-spoofing and autonomous-agent approval defects. The review then found two remaining normative gaps. Both have now received a minimum forward-only correction: governed deprecation/retirement in migration V8 and complete implemented-route inventory in the versioned OpenAPI. Final acceptance remains conditional on the follow-up CI run.

## 1. Confirmed normative violations

### SR-N01 — Governed deprecate/retire lifecycle was absent — HIGH — CORRECTED, CI PENDING

- Evidence: `ArtifactApi.java` exposes create/read/search/edit only; `GovernanceApi.java` exposes challenge creation only; `SemanticTrustedHumanApi.java` exposes review/decision/publish and migration decisions. No controller or service command performs ACTIVE→DEPRECATED or DEPRECATED→RETIRED.
- Precise references: `src/main/java/it/comune/trieste/ouf/semantic/api/ArtifactApi.java:29-37`; `GovernanceApi.java:17`; `SemanticTrustedHumanApi.java:18-22`.
- Norm: PET sections 9, 21, 60 and 64 require DRAFT→UNDER_REVIEW→ACTIVE→DEPRECATED→RETIRED, human-governed deprecate/retire and impact analysis before commit.
- Correction: migration V8 and THS commands now enforce HUMAN_USER, capability and Authorization context; block registered consumers and semantic dependencies transactionally; preserve historical rows; remove the active pointer; and append correlated audit events.

### SR-N02 — Versioned OpenAPI did not cover the frozen module surface — HIGH — CORRECTED, CI PENDING

- Evidence: `openapi/semantic-v1.yaml` defines only `POST /approval-challenges`; the implementation exposes artifact, search, discovery, validation, impact, reference, import/export and change-governance endpoints. The THS file covers only five human operations.
- Precise references: `openapi/semantic-v1.yaml:1-49`; `openapi/semantic-ths-v1.yaml:1-59`; controller inventory under `src/main/java/it/comune/trieste/ouf/semantic/api/`.
- Norm: PET sections 15, 49, 60, 61 and 68 freeze a versioned OpenAPI 3.1 contract for read/search/discovery/lifecycle/publication and reusable schemas.
- Correction: the normal OpenAPI now inventories every implemented route and the THS OpenAPI includes governed lifecycle commands. Strong schema-level parity validation remains tracked under SR-T02.

## 2. Confirmed implementation defects

No additional implementation defect was confirmed by the available executable evidence after remediation. In particular, publication still validates the decision/revision/hash relationship inside the database function and is atomic/idempotent.

## 3. Intentionally delegated functionality

- Authentication, IAM policy evaluation, role assignment and capability decisions belong to Authorization/Gateway. `TrustedActorResolver` correctly consumes the authenticated principal and trusted request attributes rather than implementing IAM.
- Protected technical-log visualization belongs to the common THS/observability stack. Semantic correctly emits structured correlated events and owns semantic audit records; duplicating a log UI here would violate ownership.
- Runtime object ingestion, object identity and data-plane scheduling do not belong to Semantic Registry.

## 4. Test coverage gaps

### SR-T01 — Lifecycle conformance coverage — HIGH — PARTIALLY CORRECTED

- Evidence: a PostgreSQL test now exercises ACTIVE→DEPRECATED→RETIRED, history retention and audit; HTTP tests deny a human without capability. Blocking-consumer rollback and concurrent lifecycle tests remain absent.

### SR-T02 — OpenAPI parity test is only a boundary smoke test — MEDIUM

- Evidence: `OpenApiBoundaryTest.java` checks string presence/absence but does not parse OpenAPI or compare operations with controller mappings.
- Minimum correction: parse both specifications, validate OpenAPI 3.1, assert unique operation IDs, schema references and complete route/method parity.

### SR-T03 — Trusted authorization-context negative cases are incomplete — MEDIUM

- Evidence: `HttpApiRuntimeTest.spoofedIdentityHeadersCannotCrossTrustBoundary` proves header spoofing and AI denial, but does not assert failure for a human lacking capability or `ouf.authorizationContextRef`.
- Minimum correction: add 403 tests for missing role, capability and authorization context for decision, publish and migration decision.

### SR-T04 — Structured log payload is not asserted — LOW

- Evidence: `RequestObservabilityFilter` emits the event, while `ObservabilityRuntimeTest` covers correlation/metrics but not log fields or secret/query-string exclusion.
- Minimum correction: capture logs in a test appender and assert event, method, safe path, status, duration and correlation ID.

## 5. Acceptable design choices

- Normal/MCP-eligible code may create an approval challenge, while decision and publication remain on the human-only THS backend.
- Approval is bound to revision and content hash and stored append-only with actor type and opaque Authorization context.
- PostgreSQL remains the system of record; RDF/Jena is an interchange/validation mechanism rather than a mandatory graph store.
- Structured application logs are exported for centralized protected visualization rather than exposed by a module-specific log endpoint.
- Existing frozen JSON contracts remain byte-for-byte unchanged; `sha256sum -c evidence/source-checksums.txt` passes.

## Evidence limits

CI run `34668586429` proves compile/test/package on Java 21 with PostgreSQL 17 and a successful non-root container build. It does not prove production Gateway/IAM integration, deployment-level log ingestion, disaster recovery, load targets, or behavior for commands that do not yet exist.
