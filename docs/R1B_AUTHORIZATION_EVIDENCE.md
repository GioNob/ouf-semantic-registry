# R1b Authorization implementation and acceptance evidence

PET Authorization 1.5 is normative. Central implementation is delivered; full owner endpoint/resource and real IAM acceptance remains open as recorded under AUT-02/AUT-03/AUT-04. `docs/R1B_ENDPOINT_COVERAGE_AUDIT.md` and the 33-controller inventory describe the residual code boundaries.

Implemented: HUMAN administration, trusted CSRF requirement, immutable capability registration, policy/grant drafts and ETags, serialized publish/revocation, append-only audit, SDK 1.1 constrained policy, explicit DENY precedence, authenticated bounded refresh, deterministic SHA-256 transport, immutable atomic cache, max-staleness fail-closed, 28 shared Java/Go vectors. The owner CI executed 67 application tests, including six admin lifecycle/concurrency/transport tests; nine SDK test methods include the 28-vector loop. MCP complete CI includes transport tamper/size/deadline tests, cache revocation/freshness and race detection.

| Repository | Code commit | CI evidence |
|---|---|---|
| GioNob/ouf-source-onboarding | `8ac76d345df3b13b7b858ef1ba45ea22856e9d31` | [Source Onboarding module CI](https://github.com/GioNob/ouf-source-onboarding/actions/runs/35173364353) |
| GioNob/ouf-semantic-registry | `1af9b96f63e4582e8568e9914631c2a1d65c39a7` | [Authorization Semantic pairwise](https://github.com/GioNob/ouf-semantic-registry/actions/runs/35173376766) |
| GioNob/ouf-semantic-registry | `1af9b96f63e4582e8568e9914631c2a1d65c39a7` | [Shared Authorization SDK pairwise](https://github.com/GioNob/ouf-semantic-registry/actions/runs/35173376710) |
| GioNob/ouf-semantic-registry | `1af9b96f63e4582e8568e9914631c2a1d65c39a7` | [Semantic Gateway live pairwise](https://github.com/GioNob/ouf-semantic-registry/actions/runs/35173376721) |
| GioNob/ouf-semantic-registry | `1af9b96f63e4582e8568e9914631c2a1d65c39a7` | [Semantic Registry module CI](https://github.com/GioNob/ouf-semantic-registry/actions/runs/35173376779) |
| GioNob/ouf-ingestion-runtime | `8195f571a0b35cb833b92ba8a2520fa4a8516ca7` | [Shared Authorization SDK pairwise](https://github.com/GioNob/ouf-ingestion-runtime/actions/runs/35173381231) |
| GioNob/ouf-ingestion-runtime | `8195f571a0b35cb833b92ba8a2520fa4a8516ca7` | [Ingestion Runtime module CI](https://github.com/GioNob/ouf-ingestion-runtime/actions/runs/35173381242) |
| GioNob/ouf-udp-object-resolution | `2bb2dff206849d5d50d8ab44257953f9bd5232f6` | [Shared Authorization SDK pairwise](https://github.com/GioNob/ouf-udp-object-resolution/actions/runs/35173382910) |
| GioNob/ouf-udp-object-resolution | `2bb2dff206849d5d50d8ab44257953f9bd5232f6` | [UDP Object Resolution module CI](https://github.com/GioNob/ouf-udp-object-resolution/actions/runs/35173382909) |
| GioNob/ouf-mcp-server | `55e6a88dd6d6e5f30f00275c63ad09918864392d` | [Authorization Java Go conformance](https://github.com/GioNob/ouf-mcp-server/actions/runs/35173385863) |
| GioNob/ouf-mcp-server | `55e6a88dd6d6e5f30f00275c63ad09918864392d` | [MCP evidence and late recovery](https://github.com/GioNob/ouf-mcp-server/actions/runs/35173385824) |

Artifact IDs/digests and evidence levels are in `evidence/ouf-pet-gap-register-v1.7.json`. Digests are reported GitHub metadata, not an independently verified archive hash. PR numbers: Onboarding 10, Semantic 6, Ingestion 20, UDP 24, MCP 25. The coordination commit may follow the code commits listed here; it must also pass CI before merge.

Validation history retained: MCP push run 35173383194 first attempt failed Reserve p95 (67.44ms versus <25ms); same-head PR run and unchanged second attempt passed. No gate weakened. An earlier Onboarding run 35173316108 had a protected-log lease fixture failure; same-head push and final-head runs passed. These are not claims of representative production performance.
