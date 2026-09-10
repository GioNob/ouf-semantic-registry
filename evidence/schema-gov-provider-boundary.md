# schema.gov.it / OntoPiA provider boundary

The official public material identifies schema.gov.it as the national catalogue
for ontologies, controlled vocabularies and data schemas, and OntoPiA as the
linked network of Italian public-administration ontologies. No stable public
search/fetch API contract was extracted from the material initially inspected on
2026-09-10. The user subsequently supplied `https://schema.gov.it/api-docs/`.
Its server-rendered page currently exposes the message “Nessun dato API
disponibile” rather than an OpenAPI path catalogue; its embedded application
could not be inspected because browser access to that separate host was denied.

The subsequently supplied official SPARQL tool page identifies the stable
Virtuoso endpoint `https://schema.gov.it/sparql` and publishes bounded example
queries for graphs, OWL classes/properties and SKOS concepts. The adapter now
uses standard SPARQL Results JSON, a fixed query template and `LIMIT 50`.
Production still routes the equivalent call through the Urban API Gateway; the
Registry does not bypass the platform egress boundary.

The module therefore does not fabricate a public endpoint. `SchemaGovProvider`
uses two explicit deployment bindings owned by the Urban API Gateway:
`search-path` and `fetch-path`. Both calls are same-origin to the configured
Gateway, HTTPS-only outside loopback tests, redirect-free, bounded by timeout and
response size, and media-type allowlisted. The external resource URI is data
passed to the Gateway fetch route; the Registry never connects to it directly.

Sources inspected:

- https://schema.gov.it/
- https://schema.gov.it/api-docs/
- https://schema.gov.it/sparql-tool/
- https://schema.gov.it/sparql
- https://www.agid.gov.it/it/agenzia/stampa-e-comunicazione/notizie/2020/10/14/ontopia-si-arricchisce-rete-ontologie-vocabolari-controllati
- https://github.com/italia/daf-ontologie-vocabolari-controllati

The real environment test remains blocked until the Gateway owner supplies the
two concrete route bindings and their machine-readable response contract.
