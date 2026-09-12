# PET traceability — Semantic Model Registry

Normative priority is L0 invariants, then the Semantic Registry PET, then frozen contracts, then implementation.

| PET concern | Implementation | Evidence |
|---|---|---|
| Authorization boundary | `TrustedActorResolver` consumes only the authenticated principal, container roles and trusted request attributes populated by Authorization/Gateway. Client actor headers are ignored. | `HttpApiRuntimeTest.spoofedIdentityHeadersCannotCrossTrustBoundary` |
| Trusted human approval | Normal API creates a challenge and returns `trustedApprovalRef`; card, decision and publish are under `/api/trusted-human/v1` and require a human role, capability and opaque authorization context. | `semantic-v1.yaml`, `semantic-ths-v1.yaml`, lifecycle HTTP test |
| MCP boundary | Only challenge creation is MCP-capability annotated. Human decision and publication OpenAPI operations explicitly carry `x-ouf-mcp-exposed: false`. | `OpenApiBoundaryTest` |
| Audit | Artifact creation/edit, challenge, decision, migration decision and atomic publication append audit events with subject, actor type/context where applicable and correlation. Audit rows and decisions are append-only. | migrations V2/V7 and PostgreSQL runtime tests |
| Technical logs | Every HTTP completion emits a structured event with correlation ID, method, safe path, status and duration. The common THS/logging platform owns protected visualization; this module does not duplicate it. | `RequestObservabilityFilter`, `ObservabilityRuntimeTest` |
| Secrets | Database credentials have no deployable fallback values. | `application.yml`, CI environment |

Authorization policy evaluation, authentication and protected-log visualization are intentionally owned by the Authorization and common THS/observability modules. Semantic Registry owns the authoritative semantic cards, decisions, state transitions and audit records.
