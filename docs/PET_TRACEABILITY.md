# PET traceability — Semantic Model Registry

Normative priority is L0 invariants, then the Semantic Registry PET, then frozen contracts, then implementation.

| PET concern | Implementation | Evidence |
|---|---|---|
| Authorization boundary | `TrustedActorResolver` consumes the common `TrustedPrincipal` and derives capabilities from the local, hash-verified SDK bundle pinned to the request. Container roles and coarse capability attributes alone are insufficient. Client actor headers are ignored. | `HttpApiRuntimeTest.spoofedIdentityHeadersCannotCrossTrustBoundary` |
| Trusted human approval | Normal API creates a challenge and returns `trustedApprovalRef`; card, decision and publish are under `/api/trusted-human/v1` and require canonical HUMAN, a locally evaluated capability and pinned bundle decision reference. | `semantic-v1.yaml`, `semantic-ths-v1.yaml`, lifecycle HTTP test |
| MCP boundary | Only challenge creation is MCP-capability annotated. Human decision and publication OpenAPI operations explicitly carry `x-ouf-mcp-exposed: false`. | `OpenApiBoundaryTest` |
| Audit | Artifact creation/edit, challenge, decision, migration decision and atomic publication append audit events with subject, actor type/context where applicable and correlation. Audit rows and decisions are append-only. | migrations V2/V7 and PostgreSQL runtime tests |
| Technical logs | Every HTTP completion emits a structured event with correlation ID, method, safe path, status and duration. The common THS/logging platform owns protected visualization; this module does not duplicate it. | `RequestObservabilityFilter`, `ObservabilityRuntimeTest` |
| Secrets | Database credentials have no deployable fallback values. | `application.yml`, CI environment |
| D-084 r2 published value maps | V22 checks exact vocabulary membership, the Unicode White_Space code boundaries, and the compact UTF-8 definition budget. The signed owner path limits VALUE_MAP envelopes to 1 MiB. The HUMAN card projects labels from the pinned set, changes, and optional proposal metadata. | PET-semantic-022, 023, 076, 104, 265, 271, 273, 275, 276, 278 and 349. Evidence entry points are `ContractInventoryTest`, `ValueMapRuntimeTest`, `ValueMapReviewCardTest`, `SemanticProposalReceiptVerifierTest`, `SemanticProposalReceiptHttpTest` and `predecessor-return`. Browser qualification belongs to the Onboarding THS integration. |

Authorization policy evaluation, authentication and protected-log visualization are intentionally owned by the Authorization and common THS/observability modules. Semantic Registry owns the authoritative semantic cards, decisions, state transitions and audit records.

R1a evidence and current integration limits: [shared SDK traceability](R1A_AUTHORIZATION_SDK.md).
Policy evaluation executes locally through Authorization-owned SDK 1.0.0.
Authentication adapters, governed ACTIVE refresh and full policy/route acceptance
remain explicit R1b/R2/R6 obligations; existing CI does not certify those gates.

## Sprint 03 · Ricerca a lotti del pubblicato

| ID PET | Requisito | Prova e criterio |
|---|---|---|
| SEM-51O-01 | Indice per revisione e lingua, normalizzazione A.2, aggiornamento atomico e ricostruzione | V23, confronto dei mapping con ICU4J 75.1, prove di rollback e dei prefissi letterali in `PublishedBatchRuntimeTest`. Il manuale di installazione §14.1 registra backup e ripristino. |
| SEM-51O-02 | Una revisione, un riscontro, con il set A.1 | `oneStrongRevisionInTwoPublishedSetsKeepsLatestPinAndCountsOnce` richiede MATCH, un solo hit e hasMore falso con limiti 1 e 8. |
| SEM-51O-03 | Costo della consultazione selettiva | `PublishedBatchIndexMeasureTest` usa gli stessi 5.000 artefatti e 64 intenti prima e dopo V23. Il test richiede 5.000 righe SQL sul predecessore (320.000 valutazioni in Java) e 64 sul candidato. Verifica l’indice nel piano e il lavoro dei nodi di scansione. I report Surefire della run registrano righe, blocchi e millisecondi di esecuzione PostgreSQL dopo un riscaldamento per versione. |
| SEM-51O-04 | D-080, ritorno del predecessore sullo schema candidato | `predecessor-return` verifica la storia V23, ripete le letture e le scritture del predecessore e controlla il termine locale di POIState creato dopo il ritorno. L’accettazione richiede la run con i pin del rilascio. |
