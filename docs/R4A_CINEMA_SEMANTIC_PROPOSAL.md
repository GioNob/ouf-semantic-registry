# Cinema CSV — published Semantic and open Onboarding gate

The real managed-file asset `8ec8ae90-808a-4d9e-907c-d56de119e376`
has profile `4462692b-9c85-446b-b6fd-779f01eab64d`: eight rows and
two non-null text fields, `cinema` and `indirizzo`. No controlled
vocabulary is mapped for either field.

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

## Resolution decision and release gate

For automatic object matching, compare only normalized data mapped to
controlled-vocabulary concepts under the same semantic class/property and
vocabulary version. Two source observations may expose different property
sets; compare the semantically comparable intersection. A likely common
object requires governed resolution evidence and, where ambiguous, HUMAN
review. On MATCH, UDP retains both source bindings and property provenance,
forms one canonical object with the union of contributions, and resolves
overlapping values through property-level authority or an explicit HUMAN
decision. It does not overwrite either raw source record.

This CSV has **no controlled-vocabulary values**. Its free-text name and
address cannot be used for automatic identity matching under the reviewed
rule. The Onboarding preflight returned `ONBOARDING_VALIDATION=PASS`
against the then-running validator but also
`UDP_RESOLUTION_CONFIGURED=false`. A validator correction is in progress
to reject managed submissions without exact execution, Semantic
publication, UDP resolution and materialization profiles. The DRAFT remains
unsubmitted; no Ingestion run, UDP materialization or R-SMOKE PASS has been
claimed. Any policy for absent comparable evidence must be reviewed before
activation.
