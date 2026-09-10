# OUF Semantic Model Registry

Implementation of the OUF Semantic Model / Registry v1.4 contract. Java 21,
Spring Boot, PostgreSQL 17, Flyway and Apache Jena. This repository is under
active completion; no acceptance criterion is reported as passed unless its
test has executed and its evidence is retained under `evidence/`.

## CI gates

`.github/workflows/module-ci.yml` is the authoritative single-module gate. It
runs Java 21, Maven and all Flyway migrations against PostgreSQL 17, records
Surefire evidence, builds the production container and verifies its non-root
runtime identity. Maven network operations and jobs have explicit timeouts.

`.github/workflows/pairwise.yml` is the future 1+1 gate. It intentionally
refuses execution until the requested, versioned fixture set exists: absence of
real pairwise fixtures can never be reported as PASS.
