# Authorization ↔ Semantic Registry pairwise traceability

Normative baseline: Cross-Module Alignment Matrix v1.7, Authorization PET v1.5, Semantic Registry PET v1.3.

## Contract alignment

- The pinned shared SDK is `GioNob/ouf-source-onboarding@fb2dd51dfc204577a47c1e702f17531dd0709b3c:contracts/authorization/authorization-sdk-v1.json`.
- Semantic authenticated roles are normalized to the scenario-neutral actor vocabulary `HUMAN`, `SERVICE`, `AI_AGENT`.
- `OUF_MCP_SERVER` remains an authentication/service role but resolves to canonical actor type `SERVICE`; it is not a fourth Authorization actor type.
- Trusted-human endpoints require canonical actor type `HUMAN` plus the operation capability.
- `ouf.authorizationDecisionRef` is the canonical propagated decision reference. `ouf.authorizationContextRef` is accepted only as a bounded compatibility alias for existing callers during the compatibility window; the canonical attribute takes precedence when both exist.
- Actor-supplied identity headers remain outside the trust boundary; the resolver consumes the authenticated principal, container-established roles, and server-established authorization attributes.

## Executable evidence

- `TrustedActorResolverTest` exercises role-to-actor normalization, MCP-as-SERVICE, capability attributes, canonical decisionRef precedence, and the compatibility alias.
- `.github/workflows/authorization-pairwise.yml` checks out the exact Source Onboarding commit and validates the Semantic boundary against the shared SDK.
- The existing PostgreSQL 17 module CI and THS HTTP tests remain the regression gate; frozen source checksums include the modified production boundary files.

## Evidence limits

CI proves source-contract compatibility and module behavior. Production issuer/JWKS/audience configuration, real Gateway-to-Semantic attribute propagation, credential rotation/revocation, and deployed NetworkPolicy behavior remain **EVIDENCE PENDING**.
