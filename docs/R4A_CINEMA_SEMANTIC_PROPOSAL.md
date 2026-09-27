# Cinema CSV — published Semantic and open Onboarding gate

The real managed-file asset `8ec8ae90-808a-4d9e-907c-d56de119e376`
has profile `4462692b-9c85-446b-b6fd-779f01eab64d`: eight rows and
two non-null text fields, `cinema` and `indirizzo`. Their **property meanings**
are mapped to governed Semantic Registry IRIs aligned to schema.org;
the free-text **values** have no controlled concept/code-list mapping.
Those are different notions of vocabulary, and neither value is a unique key.

The HUMAN reviewed the exact RDF approval card and published:

| Reference | Exact value |
| --- | --- |
| Semantic ID | `https://api.ouf-lab.it/semantic/cinema` |
| Version | `1.0.0` |
| Revision ID | `51706bed-81e4-4306-aca1-70119821727d` |
| Publication set ID | `f92a2e17-30c9-456f-bb12-63afa84f41e6` |
| RDF SHA-256 | `4340986102db6e47345dd8157734d9db83b928edd94485f1b9a5b9e81c497a2e` |
| Manifest hash | `a711d0428f1cbe24c73cbf0fa5cabfcb52f85df774e7238d884e7f83f41b84e9` |

The source RDF is [`r4a_cinema_draft.ttl`](r4a_cinema_draft.ttl).
Each row describes a physical cinema. The class
`https://api.ouf-lab.it/semantic/cinema#Cinema` aligns to
`https://schema.org/MovieTheater`; `cinema` maps to `#nome`
(schema:name) and `indirizzo` maps to `#indirizzo`
(schema:address, text). The HUMAN classified both properties `OPEN`.

The owned Onboarding DRAFT is source `managed-cinema-8ec8ae90`,
version `68394f42-5c82-4127-a1f3-126516665749`.
It uses `MANAGED_DETERMINISTIC` source-row identity derived from the
immutable managed asset and row ordinal. The cinema name is not a row key.
This technical provenance is distinct from UDP canonical Urban Object identity.

## General object-resolution contract and release gate

The Semantic Registry publishes the meaning of classes, properties and
controlled concepts. Onboarding maps source fields to those versioned
semantic references. The values of a property may still be free text:
schema:name and schema:address are examples, not special cases in UDP.

A reusable resolution policy compares two observations by the same approved
class and mapped property IRI (and compatible ontology version), on their
shared property set. A versioned comparator is selected by value type:

- Controlled concept: resolve to the published concept identifier/version
  before comparison, preserving native code and mapping provenance.
- Free text: normalize with a documented, reversible-evidence policy and
  compare exact or approximate strings; this is candidate evidence, not a
  universal identifier. Address text may first be parsed into structured
  components where the mapping supports it.
- Numeric, temporal, geometric and stable identifier values: use their
  respective explicit unit, tolerance, CRS or exact-key policies.

Candidate generation is bounded. The class-neutral engine applies the
published semantics of each mapped property or relation: comparator and
version, evidence role, justified uniqueness scope, cardinality, temporal
validity and geometry where relevant. A mapping alone does not make a value
an identifier. Blocking rules retrieve candidates; value prevalence can
inform retrieval and evidence explanation but never grants identity
authority through a frequency cutoff. The published identity policy declares
sufficient conditions for automatic decisions. A weighted score may rank
candidates but is not itself sufficient authority to merge. Uncertain
identity requires HUMAN review. Names, addresses and other example fields
receive no special production branches.
On MATCH, UDP keeps distinct source-object bindings and the union of property
contributions. Overlapping conflicting values are handled by versioned
property-level authority or an explicit HUMAN decision, retaining both raw
values and provenance. The rule applies to every object class, not just
cinemas.

### Ambiguous identity across acquisition modes

For any object class, an ambiguous candidate set or an unresolved conflict
between comparable values produces a durable `REVIEW_REQUIRED` item with
the source observation, candidate canonical objects, shared semantic property
references, normalized comparison evidence, policy/comparator versions and
provenance. No candidate is selected, merged or published as a canonical
object until a HUMAN makes an explicit, auditable decision. Uncertain absence
of a match must not silently become `NEW`.

The acquisition mode changes when that decision is requested, not the rule:
an interactive managed-file upload presents the review to the available HUMAN
and persists the item if that person leaves; a scheduled SUO pull persists
the affected record in the UDP resolution review queue until a HUMAN returns.
Other independent records can continue under their own policy. Review is
resumable and does not hold open a request, database transaction or worker.
A confirmed match then links the source observation to the canonical object;
a confirmed new object may be materialized; conflicting overlapping values
follow property authority or explicit HUMAN choice with provenance retained.

Per the Ingestion/UDP PET boundary, a durable handoff/ACK can precede this
resolution review after the raw observation and handoff are safely persisted.
`REVIEW_REQUIRED` prevents canonical materialization and serving of that
unresolved record; it does not retroactively invalidate the durable ACK or
automatically stall the entire source watermark. A source-contract failure
before handoff is a separate Ingestion quarantine condition.


The cinema CSV offers two comparable, mapped free-text properties but no
controlled concept values. It can produce candidate matches after versioned
text/address normalization; there is currently no approved or deployed
general resolution policy for automatic matching on this evidence.
The Onboarding preflight returned `ONBOARDING_VALIDATION=PASS` against the
then-running validator but `UDP_RESOLUTION_CONFIGURED=false`. A validator correction is present in the Onboarding work branch and had
CI evidence, but deployment to the running VPS validator is not attested.
It rejects managed submissions without exact execution, Semantic publication,
UDP resolution and materialization profiles.
The DRAFT remains unsubmitted; no Ingestion run, UDP materialization or
R-SMOKE PASS has been claimed.

Cross-module status and next step: [PET 1.7 handoff 27 September 2026](https://github.com/GioNob/ouf-semantic-registry/blob/codex/r4a-smoke-semantic-inventory/docs/handoffs/OUF_HANDOFF_2026-09-27_R4A.md).
