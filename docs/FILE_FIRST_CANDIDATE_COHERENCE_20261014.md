# File-first Registry source continuity

The proposal package from main `0b150851487640bf3841433f48264aa8914c1d6c`
contained the new single-artifact command API but had lost the IAM JWT adapter,
delegated consultation and current semantic read projection from the qualified
candidate line `8a2e84b32d4ce2bdc3bc529b56afb5663ab133e3`. Packaging that combination
would regress authenticated reads and the existing chatbot consultation route.
The qualified candidate source is not asserted to be the currently installed source.

This change restores those existing adapters and search/read services onto main,
retains the main single-artifact proposal commands and durable V10 receipts, and
keeps the patched Spring Boot 4 dependencies. The IAM adapter also retains bounded
canonical/legacy signed external-role claims, following the existing Onboarding
contract, so current role grants remain evaluable by owner policy. Receipt identity
is bound only after signature verification; headers cannot create an identity.

V1–V9 migration bytes are unchanged. The file-first schema adds only main's
`V10__proposal_command_receipts.sql`. Discovery candidate V10/V11 are not relabelled
or imported. A database where those alternate migrations already ran is not a
compatible apply target for this package and must not be forced through Flyway.

Use the explicit `file-first` Spring profile for this path. It disables external
schema.gov provider work and the discovery worker, while keeping internal semantic
reuse, bounded search, exact publication reads, DRAFT validation/review and HUMAN
decision/publication. This is not a claim that the old default discovery worker
meets the current resilience policy. No automatic retry or new retry budget is added.

`FileFirstIamHttpRuntimeTest` starts a local test issuer/JWKS, signs fresh RSA JWTs,
uses the production decoder/filter chain and role-constrained owner policy, and
executes DRAFT → validation → review → HUMAN decision → publication → search/exact
read through HTTP and PostgreSQL. It rejects AI approval, missing current grants,
wrong audience, expired JWTs, malformed roles and spoofed identity headers.
The retained consultation/RDF tests and proposal receipt tests run in the same
module suite. These are isolated test evidence, never proof of a deployed target
or completed CSV → ingestion → UDP → MCP cycle. Browser THS and target rollout
are separate integration work; this change does not issue runtime authority.


The same CREATE command also accepts a bounded imported ontology: `artifactType`
ONTOLOGY, `rdfTurtle` at most 49,152 UTF-8 bytes, `mediaType` exactly `text/turtle`,
and empty/absent `definition`. Native commands remain supported. The existing
InterchangeService validates the ontology identity and stores the immutable RDF;
its exact SHA-256 is bound into the definition validated and approved by the owner.
The durable intent hash includes exact RDF bytes, media type and artifact identity.
There is no URL input/fetch, JSON-LD context resolution or OWL import resolution.
The whole delegated envelope remains bounded at 65,536 bytes.

The Teatri fixture is the exact prepared review from 14 October (RDF SHA-256
`6e4668ea42cf1c75b822e17a8ca9cb71fb2c4d8f500eed628282fa6039a6dbaa`).
The HTTP/JWT test runs it through one imported ontology, owner validation, HUMAN
review/publication and exact semantic read. It checks all 21 declared terms,
including CAP as xsd:string. This validates the code against the proposed schema;
it does not approve those semantics or read the production CSV.

Review cards expose the verified RDF snapshot, durable approvalDecisionId,
lifecycleStatus and publicationSetId so a browser can reconcile after a lost
response without repeating a decision. `ouf.authorization.ths.public-origin`
(HTTPS origin) adds `/trusted-human/semantic/?challenge=<uuid>` review URLs for
the shared Onboarding THS session; no second login implementation is introduced.

The restored SDK is an exact mirror of canonical Onboarding commit
`77df1d780f9a7164e3ae5374691be7915a7d715e`, including its checksum manifest.
Gateway receipt integration is pinned to
`0a95ae3e0d56f71252fe830a180df8b08cd5e558`; actual Lua generates the read receipt
and the committed proposal vectors include the imported-ontology variant.
