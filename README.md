> **Policy di piattaforma vigente:** [Resilienza, quarantena, incidenti e alert — v3](https://github.com/GioNob/ouf-deploy/blob/main/docs/OUF_RESILIENCE_POLICY.md). Obbligatoria per sviluppo e revisione; [adozione e prove](https://github.com/GioNob/ouf-deploy/blob/main/docs/OUF_RESILIENCE_ADOPTION.md).


**Resilience v3 — prima tranche integrata:** priorità incidenti e catch-up qualificati per i perimetri MCP/Ingestion/Gateway; [prove e limiti](https://github.com/GioNob/ouf-deploy/blob/main/docs/OUF_RESILIENCE_ADOPTION.md), [piano operativo](https://github.com/GioNob/ouf-deploy/blob/main/docs/OUF_OPERATIONAL_RESILIENCE_PLAN.md). Cursor/memoria operatore, correlazione dipendenze e alert restano aperti.

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
