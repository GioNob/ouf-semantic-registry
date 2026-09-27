# Cinema CSV — Semantic review candidate (not published)

Input evidence: Onboarding asset `8ec8ae90-808a-4d9e-907c-d56de119e376`,
profile `4462692b-9c85-446b-b6fd-779f01eab64d`, eight rows, non-null
string fields `cinema` and `indirizzo`. The preview redacts address values.

| CSV field | Proposed target | Proposed access | Review needed |
| --- | --- | --- | --- |
| row object | local `https://api.ouf-lab.it/semantic/cinema#Cinema`, aligned to `https://schema.org/MovieTheater` | — | Confirm that each row represents a physical cinema venue. |
| `cinema` | local `https://api.ouf-lab.it/semantic/cinema#nome`, aligned to `https://schema.org/name` | `OPEN` proposed | Confirm public name and whether it is stable enough as the source key. |
| `indirizzo` | local `https://api.ouf-lab.it/semantic/cinema#indirizzo`, aligned to `https://schema.org/address` (Text value) | `OPEN` proposed | Confirm it describes the venue, not a private person's address. |

Schema.org defines MovieTheater as a cinema venue and lists address as a
Text or PostalAddress property; name is a general property of Thing. Primary
term pages: https://schema.org/MovieTheater,
https://schema.org/name, https://schema.org/address.

The proposed row identity is `NATIVE_KEY(cinema)` under
`normalization://managed-file/native-key-v1`. The eight current values are
distinct, but this does not prove stability across future renames or
incremental updates. No controlled vocabulary mapping is proposed for these
two free-text fields. The HUMAN reviewer may replace the class, properties,
key or access labels before any Onboarding DRAFT or Semantic publication.

The reviewable Turtle source is [`r4a_cinema_draft.ttl`](r4a_cinema_draft.ttl).
The proposed local ontology ID is
`https://api.ouf-lab.it/semantic/cinema` with semantic version `1.0.0`.
It aligns local terms with Schema.org and records the exact source profile;
it does not claim to redefine Schema.org. A HUMAN decision may require a
different model, field mapping, key, or access classification. Importing
the Turtle only creates a DRAFT and does not authorize Onboarding activation.

This document is a review candidate only. Eight HUMAN Semantic Gateway
routes and their IAM/Authorization grants are installed; the Registry
review-card upgrade is active. The RDF import route uses `ouf.semantic.propose` and an
8 MiB body limit matching the Registry's parser. For imported RDF, the
HUMAN approval card now includes the immutable source bytes, media type,
statement count and independently verified SHA-256. A governed draft must
be examined in that card before decision and publication.

The reviewed RDF proposal must define the actual class and properties, with
the exact published SemanticReference used in Onboarding. Merely storing a
field-mapping JSON object inside an ONTOLOGY revision does not populate the
Registry's RDF view with those class and property triples. No Semantic
publication or Onboarding DRAFT has been performed for this asset. Do not
submit `source.onboarding.create` until a HUMAN reviewer has approved the
ontology, row key and field access, and the exact publication is verified.
