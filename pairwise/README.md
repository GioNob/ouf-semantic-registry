# Pairwise verification

`run-semantic-gateway-live.sh` executes the first real two-process pairwise:
Semantic Model Registry -> minimal Gateway fixture -> the live official
`https://schema.gov.it/sparql` service. It uses PostgreSQL 17 and persists and
adopts the returned CLV Address class. The external catalog is live; it is not
replaced by a local mock. This remains a fixture-level pairwise because the
complete Urban API Gateway is not yet implemented.

This directory is the controlled entry point for future real 1+1 module tests.
The workflow intentionally refuses to report success until a versioned fixture
set and its peer adapter have been committed under `pairwise/fixtures/`.

Inputs are restricted to immutable/explicit image references and simple fixture
names. No workflow input is evaluated as a shell command.
