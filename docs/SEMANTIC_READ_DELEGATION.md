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
