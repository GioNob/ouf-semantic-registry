# Native semantic discovery jobs

Candidate implementation layered on availability PR #28; not deployed or MCP-enabled.

POST /api/semantic/v1/discovery-requests accepts an optional idempotencyKey (16–128 ASCII letters, digits, '.', '_', ':' or '-'). Keep the same key for transport retries of the same request; use a new key for a deliberate new search after failure or candidate expiry. Keys are caller scoped and stored only as SHA-256 hashes. The request fingerprint includes validated artifact type, stripped intent, normalized language preference order and sorted registered provider IDs. Different content under the same key returns HTTP 409 SEM_DISCOVERY_IDEMPOTENCY_CONFLICT. The unique database index handles concurrent retries. A replay reports the actual current job state, including completed jobs when the provider is now disabled. Existing unkeyed callers retain one new job per request.

GET /api/semantic/v1/discovery-requests/{id} returns requestId, state, attemptCount, createdAt, completedAt, unexpired candidateCount and a bounded errorCode. Status and candidate listing require the trusted requesting subject; foreign and missing IDs both return HTTP 404. Raw intent, provider error text, key hashes, request fingerprints and candidate RDF bytes are excluded from status. Candidate metadata remain untrusted data.

V10 is an additive migration: two nullable columns, a consistency check and a caller/key unique partial index. Historical rows are not rewritten. Existing migration bytes are unchanged. The prior RDF-read rollout helper explicitly requires identical packaged migrations and MUST NOT be used to deploy this candidate; migration-aware backup/restore and acceptance are still required.

This native boundary uses the existing trusted actor resolver and native capability annotation. It does not introduce HUMAN-to-SERVICE impersonation or reuse READ delegation for a command. Deployment currently uses one configured IAM issuer; a future multi-issuer/tenant context needs explicit tenant/issuer persistence and owner checks before expansion. No adoption, confirmation, activation, publication, identity mapping, ingestion or source replay is added.

Remaining: separate MCP command/read capabilities and receipts; temporary RDF candidate inspection; governed provider service authentication and isolated southbound routes/egress; complete provider-policy/version fingerprinting if configurable providers are introduced; trusted human review; revision-pinned adopted graphs; operator migration-aware release acceptance.

Tests cover concurrent retries, changed payload conflict, caller isolation, redaction, disabled-provider replay, validation and native HTTP status ownership. CI results are recorded in the PR and coordination documents.
