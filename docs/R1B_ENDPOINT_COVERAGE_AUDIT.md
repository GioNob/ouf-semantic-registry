# R1b endpoint coverage audit

Authority: PET Authorization 1.5 §§109.2–109.3, 36.10, 34.2 and Semantic 1.3 §160.7. Inventory: `evidence/r1b-endpoint-inventory.json`; these are source observations, not a claim of full route acceptance.

| Boundary | Observed enforcement | Remaining acceptance |
|---|---|---|
| New Authorization admin routes | HUMAN + local admin capability before body parsing, trusted CSRF for mutations, bounded input, controller recheck, ETag and append-only audit | Real IdP/THS CSRF adapter deployment under AUT-04 |
| Authorization ACTIVE distribution | SERVICE + authorization.bundle.read via shared local SDK; immutable content hash | Governed workload bootstrap and revocation propagation in target environment |
| Semantic trusted-human governance | SDK actor, canonical HUMAN and per-operation capability checks | Real authenticated path |
| Semantic artifact/discovery/interchange/change/validation routes | Several mutation routes resolve the trusted actor but do not explicitly require their operation capability; several reads do not call the resolver | AUT-02 stays PARTIAL. Require route-to-capability mapping and backend enforcement before platform acceptance |
| Ingestion existing trusted boundaries | Existing shared-SDK authorization context and domain checks retained | Full route/capability/resource matrix and target deployment claims |
| UDP serving and governance | Shared SDK capability set plus domain capability, tenant and data-label guards; explicit canonical HUMAN adapter | Owner-derived fine-grained resource evaluation and returned detail obligations must be wired across every output boundary; current trusted allowedDataLabels attribute is not proof of policy-derived label authorization |
| MCP | Common Go evaluator and bounded immutable cache; separate backend owner checks remain necessary | Real authenticated role/assurance claims and owner data projection |

R1b delivers the central administrative/policy/cache implementation and this audit. It does not close AUT-02 endpoint coverage or certify every owner projection. Those residual code obligations remain explicit in the gap register; a green shared SDK test is insufficient to close them. AUT-04 remains the real environment gate. No resolved migration decision was reopened.
