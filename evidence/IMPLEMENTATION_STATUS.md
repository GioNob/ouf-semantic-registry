# Implementation status

This is the full-module workstream, not the earlier pilot. Current checkpoint:

- repository, Java 21/Spring Boot build and twelve frozen JSON contracts: present;
- Flyway V1 core physical model: imported and being extended;
- artifact create/read/search and ETag draft update: implemented;
- governed approval and atomic/idempotent publication: implemented and DB-tested;
- discovery request/candidate persistence, provider SPI and lease/recovery claims:
  implemented; V1-V3 migrations and concurrent claims DB-tested;
- local-only RDF parser with media/size/DTD/entity guards: implemented, pending the
  Java 21/Jena build and adversarial parser suite;
- schema.gov.it/OntoPiA adapter boundary: implemented through configurable Urban
  API Gateway routes; no undocumented public endpoint is hard-coded;
- candidate adoption, immutable local snapshot, provenance and idempotent replay:
  implemented and DB-tested;
- live provider connectivity remains environment-required until the Gateway
  owner supplies the concrete route bindings and response contract;
- Java/Jena adversarial tests are authored but not yet executed: the current
  workspace has a Java 17 runtime (compiler module but no Java 21 JDK) and no
  Maven installation; external toolchain download was blocked by environment
  policy. This is recorded as BLOCKED, never as PASS;
- observability and full acceptance traceability: not yet complete;
- production readiness: **not claimed**.
# Incremento discovery schema.gov.it / OntoPiA

- Query SPARQL Results JSON bounded per tipo semantico, con `PROPERTY` estesa a object e datatype property.
- Chiamate esclusivamente attraverso route same-origin dell'Urban API Gateway; redirect e media type non ammessi sono rifiutati.
- Fetch RDF bounded, deduplicazione URI e massimo candidati configurabile (default 10).
- Retry solo per indisponibilità/429/5xx, numero tentativi e backoff limitati; circuit breaker locale diagnostico.
- Worker schedulato con lease/recovery PostgreSQL e isolamento degli errori per provider.
- Test di integrazione con Gateway HTTP locale aggiunto; esecuzione Java in attesa del toolchain Java 21/Maven.

# Incremento validation e compatibility

- Livelli L0-L2 materializzati come validation run e issue append-only.
- Dependency graph ricostruito deterministicamente da domain, range, vocabulary e inverse reference.
- Ruoli DOMAIN/RANGE separati nella chiave del grafo, evitando collisioni quando la stessa classe svolge entrambi i ruoli.
- Publication gate fail-closed vincolato a un PASS riferito allo stesso `row_version` e allo stesso hash del contenuto corrente.
- Classificazione deterministica delle modifiche e ImpactReport append-only con conteggio di artefatti, publication set e consumer registrati.
- Risoluzione dei SemanticReference esclusivamente sulla tripla esatta semanticId/revisionId/publicationSetId; nessun fallback ad ACTIVE/latest.
- Suite concreta V1-V5 superata su PostgreSQL 16.14: 10 controlli. PostgreSQL 17 e test Java/Spring restano gate separati non ancora attestati.

# Incremento RDF interchange e change governance

- Import RDF bounded in Turtle, JSON-LD, RDF/XML e N-Triples con snapshot immutabile per revisione.
- Binding obbligatorio tra semanticId, artifactType e risorsa realmente dichiarata nel payload RDF.
- Export `application/json`, JSON-LD, Turtle, RDF/XML, N-Triples e CSV limitato a Vocabulary/Concept.
- Nessun import/dereference di rete implicito: `owl:imports` resta informazione serializzata.
- SemanticChangeNotice append-only con replay idempotente e conflitto sul payload rilevato.
- MigrationProposal governata: proposta separata dalla decisione umana; un BREAKING change non viene pubblicato senza proposta APPROVED.
- Corretto lo switch di lifecycle: al nuovo publish la revisione precedentemente ACTIVE diventa DEPRECATED senza mutarne il contenuto.
- Suite concreta V1-V6 superata su PostgreSQL 16.14: 9 controlli; regressione V1-V5 nuovamente verde (10 controlli).
- I test Jena di transcodifica e identity/type binding sono presenti ma restano non eseguiti fino alla disponibilità del toolchain Java 21/Maven.
