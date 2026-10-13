# Delegated semantic consultation — candidate

Adds a purpose-bound signed receipt adapter for MCP and other approved Gateway clients.
Existing OIDC GET search/exact-reference APIs remain available; owner capability identity
and resource types are the same. No mutation or HUMAN approval endpoint in this adapter.

- `ouf.semantic.delegation.key-file`: optional secret-file path, startup-only; absence denies all delegated consultation. When configured, file must contain exactly 64 hex characters and issuer/audience/workload must all be configured; invalid config blocks startup.
- `ouf.semantic.delegation.workload`: required exact trusted Gateway/MCP workload binding when the receipt adapter is configured; no installation-specific default.
- `ouf.iam.issuer` / `ouf.iam.audience`: existing OIDC installation bindings also pin receipts.
- `ouf.semantic.read.max-result-bytes`: existing bounded read response property.

Secrets are shared only with Gateway, never MCP/model. Receipt MAC domain
`ouf-semantic-read-owner-v1.` and purpose `semantic-read-owner`, max30-second lifetime,
body hash/exact method/path/capability/issuer/audience/workload. Replay during the short
validity window is safe only because these endpoints are reads; current owner policy is
checked again on every request. No caller-supplied authorization grant is accepted.

MCP search accepts ACTIVE only; editorial draft queries remain on the existing guarded API.
get requires all three exact reference components. Missing pin, over-limit query, unknown
argument, fractional limit, wrong receipt or denied local policy fails closed.

New Java tests exercise actual HMAC, wrong domain/bindings/body/expiry/scope, tenant and
local-policy denial, malformed arguments and unconfigured key; tests are candidate evidence
until CI passes the resulting commit. No database migration or existing payload mutation.


## Imported RDF consultation

Exact reads optionally include `rdf_snapshot` from the immutable revision interchange snapshot. The stored RDF hash and statement count are verified before returning typed subject/predicate/object statements. Original JSON label/description/definition remain unchanged; import currently stores the graph separately and does not populate those fields. No revision/publication rewrite, migration, policy change, discovery, adoption, remote fetch or inference occurs.

The projection contains at most 1000 asserted statements and reports `partial`; the existing entire-response byte budget still fails closed on overflow. Blank node identifiers are scoped to this response. Terms retain the containing artifact revision and publication pins; they are not separately registered artifacts or independent publication references. An incomplete projection cannot establish complete mapping constraints. Remote JSON-LD contexts/imports are rejected before parsing. Search continues to search registered artifacts; it does not invent CLASS entries for ontology members. Large-graph paging and governed discovery remain separate gates.
