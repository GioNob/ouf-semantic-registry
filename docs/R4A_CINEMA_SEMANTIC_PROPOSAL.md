# Cinema CSV — Semantic review candidate (not published)

Input evidence: Onboarding asset `8ec8ae90-808a-4d9e-907c-d56de119e376`,
profile `4462692b-9c85-446b-b6fd-779f01eab64d`, eight rows, non-null
string fields `cinema` and `indirizzo`. The preview redacts address values.

| CSV field | Proposed target | Proposed access | Review needed |
| --- | --- | --- | --- |
| row object | `https://schema.org/MovieTheater` | — | Confirm that each row represents a physical cinema venue. |
| `cinema` | `https://schema.org/name` | `OPEN` | Confirm public name and whether it is stable enough as the source key. |
| `indirizzo` | `https://schema.org/address` (Text value) | `OPEN` | Confirm it describes the venue, not a private person's address. |

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

This document is a review candidate only. The seven HUMAN Semantic Gateway
routes and their IAM/Authorization grants have passed live authenticated
acceptance; the RDF import route and the Registry review-card upgrade remain
deployment candidates. The import route uses `ouf.semantic.propose` and an
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
