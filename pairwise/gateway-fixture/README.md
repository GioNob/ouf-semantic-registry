# Semantic Provider Gateway Fixture

Test-only Java 21 workload exposing only the two routes required by the
Semantic Registry schema.gov.it adapter. It is not the OUF Urban API Gateway.

- `POST /semantic-providers/schema-gov/sparql`
- `GET /semantic-providers/schema-gov/fetch?uri=...`

The SPARQL upstream is fixed by configuration. Fetch targets are restricted to
an explicit host allowlist. Redirects, unexpected media types, oversized
requests/responses, credentials in URIs and non-HTTPS remote targets are
rejected. Loopback HTTP is permitted only for deterministic tests.
