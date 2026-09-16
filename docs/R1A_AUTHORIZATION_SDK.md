# R1a Authorization integration

Authority: Reality Baseline Package 1.7 / Matrix 1.7, Authorization PET 1.5
§§109.2–3, 109.5–8; relevant module PET retains its current version.

Shared artifact: `it.comune.trieste.ouf:authorization-sdk:1.0.0`.
Canonical source: GioNob/ouf-source-onboarding `authorization-sdk/`, commit
`63f238fa78abe2e6834430af618366ce865977fd`. Consumers mirror the same source
artifact with checksums and verify byte identity against that commit in CI.
Build with `bash scripts/install-authorization-sdk.sh` before Maven; Docker
performs the same bounded installation. Production dependencies exclude the
tests classifier. This avoids a new service or a private package-registry token.

The server authentication adapter must construct the common `TrustedPrincipal`
only after token signature/issuer/audience/claim validation. Old role-only
principals and capability/identity headers cannot establish business authority.
The domain adapter uses `ServletAuthorization` to evaluate a locally verified
bundle, derive allowed capabilities and pin policy version for the request.
Coarse Gateway allow cannot grant a capability denied by this bundle.
The SDK rejects missing/stale/tampered/reference-mismatched bundles; invalid
refresh cannot replace the immutable last-known-good snapshot. New requests
observe new versions, in-flight requests remain pinned within freshness limits.

Startup exact-reference configuration and explicit refresh SPI are documented
in the SDK README. Missing bundle denies protected adapter calls. No fallback
accepts the old trusted-capability attributes. Provision identity adapter and
bundle distribution before deploying protected operations. Automatic governed
ACTIVE polling/revocation distribution and IAM scenario A/B/C are not supplied
by the local-file loader; they remain integration/release gates.

This tranche covers shared types/evaluator, Java consumer adapters, canonical
human boundary and executable consumer tests. It does not certify all HTTP
routes, complete resource/DataAccessLabel/assurance policy, administrative CRUD,
production IAM/SSO, or representative full-path acceptance. R1b retains those
policy/control-plane residuals, and R2/R6 retain runtime/production integration.
Existing domain guards still own resource state and data-label enforcement.
No migration or historical audit row is rewritten.

The R0 live fixture still validates its ephemeral credential before constructing
the shared trusted SERVICE principal. Its fixed laboratory grant is now evaluated
by the same SDK as the domain adapter; the fixture remains absent from the
production JAR. Real Gateway/IAM integration remains SEM-01.

## Executed evidence

| Repository | Executed commit | Gate | CI |
|---|---|---|---|
| GioNob/ouf-source-onboarding | `4144a2518e88e9d61e95ab9c1b531a151d4b5ed7` | Source Onboarding module CI | [PASS](https://github.com/GioNob/ouf-source-onboarding/actions/runs/35148466075) |
| GioNob/ouf-semantic-registry | `0dbd981a559fd736828057d886cb0604e62d298d` | Authorization Semantic pairwise | [PASS](https://github.com/GioNob/ouf-semantic-registry/actions/runs/35148028028) |
| GioNob/ouf-semantic-registry | `0dbd981a559fd736828057d886cb0604e62d298d` | Shared Authorization SDK pairwise | [PASS](https://github.com/GioNob/ouf-semantic-registry/actions/runs/35148027893) |
| GioNob/ouf-semantic-registry | `0dbd981a559fd736828057d886cb0604e62d298d` | Semantic Gateway live pairwise | [PASS](https://github.com/GioNob/ouf-semantic-registry/actions/runs/35148027807) |
| GioNob/ouf-semantic-registry | `0dbd981a559fd736828057d886cb0604e62d298d` | Semantic Registry module CI | [PASS](https://github.com/GioNob/ouf-semantic-registry/actions/runs/35148027856) |
| GioNob/ouf-ingestion-runtime | `b249e763bd0aa96f8d780f71120681a64493a3b3` | Shared Authorization SDK pairwise | [PASS](https://github.com/GioNob/ouf-ingestion-runtime/actions/runs/35148248565) |
| GioNob/ouf-ingestion-runtime | `b249e763bd0aa96f8d780f71120681a64493a3b3` | Ingestion Runtime module CI | [PASS](https://github.com/GioNob/ouf-ingestion-runtime/actions/runs/35148248575) |
| GioNob/ouf-udp-object-resolution | `8f20ad2bc74fdce78979a6f6db2f4cc893affb58` | Shared Authorization SDK pairwise | [PASS](https://github.com/GioNob/ouf-udp-object-resolution/actions/runs/35148048232) |
| GioNob/ouf-udp-object-resolution | `8f20ad2bc74fdce78979a6f6db2f4cc893affb58` | UDP Object Resolution module CI | [PASS](https://github.com/GioNob/ouf-udp-object-resolution/actions/runs/35148048137) |
| GioNob/ouf-mcp-server | `7f3e0956a3f6092563894513e7aef17c80735c9c` | Authorization Java Go conformance | [PASS](https://github.com/GioNob/ouf-mcp-server/actions/runs/35148370587) |
| GioNob/ouf-mcp-server | `7f3e0956a3f6092563894513e7aef17c80735c9c` | MCP evidence and late recovery | [PASS](https://github.com/GioNob/ouf-mcp-server/actions/runs/35148370452) |

UDP module run 35148048137 attempt 1 exceeded intake p95 (129.88 ms vs
100 ms); identical-head push run 35148044787 passed. The failed performance
job was repeated without code/threshold/sample changes, and attempt 2 passed.
Preserve both outcomes; this is laboratory evidence, not production SLO sign-off.

R1a closes the shared-artifact, consumer-boundary and common-fixture tranche.
AUT-02 remains PARTIAL in the common register because complete policy/route
coverage, governed distribution and real IAM acceptance are broader obligations.
Evidence pins executed code; subsequent main workflows remain integration gates.
