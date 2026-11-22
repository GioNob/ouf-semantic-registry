> **Policy di piattaforma vigente:** [Resilienza, quarantena, incidenti e alert — v3](https://github.com/GioNob/ouf-deploy/blob/main/docs/OUF_RESILIENCE_POLICY.md). Obbligatoria per sviluppo e revisione; [adozione e prove](https://github.com/GioNob/ouf-deploy/blob/main/docs/OUF_RESILIENCE_ADOPTION.md).


**Resilience v3 — prima tranche integrata:** priorità incidenti e catch-up qualificati per i perimetri MCP/Ingestion/Gateway; [prove e limiti](https://github.com/GioNob/ouf-deploy/blob/main/docs/OUF_RESILIENCE_ADOPTION.md), [piano operativo](https://github.com/GioNob/ouf-deploy/blob/main/docs/OUF_OPERATIONAL_RESILIENCE_PLAN.md). Cursor/memoria operatore, correlazione dipendenze e alert restano aperti.

# OUF Semantic Model Registry

Implementation of the OUF Semantic Model / Registry v1.4 contract. Java 21,
Spring Boot, PostgreSQL 17, Flyway and Apache Jena. This repository is under
active completion; no acceptance criterion is reported as passed unless its
test has executed and its evidence is retained under `evidence/`.

## Tipi strutturati governati (D-084)

Una proposta nativa con `artifactType: DATATYPE` usa `definition.components`. L’etichetta è in `labels.it` e la descrizione editoriale può arrivare in `definition.description.it`. Il Registry conserva la descrizione con la revisione e la include nell’impronta approvata dall’umano. La definizione destinata ai consumatori contiene i componenti nell’ordine dichiarato. [Contratto dei tipi](contracts/ouf-value-types-v1.json)

Per risolvere un tipo, inviare `semanticId` e `publicationSetId` a `GET /api/semantic/v1/references:resolve`. Un eventuale `revisionId` deve coincidere con il membro del set. La risposta contiene `definition` e `definitionSha256`, calcolato sul JSON compatto UTF-8 con chiavi ordinate ricorsivamente. Ogni componente strutturato porta il proprio pin, da risolvere nello stesso modo. Una nuova versione attraversa validazione, challenge e pubblicazione con lo stesso IRI e una nuova `semanticVersion`.

Lo snapshot N-Triples dichiara l’IRI come `rdfs:Datatype` e usa `rdf:value` con un letterale `rdf:JSON` per conservare nomi, cardinalità, vincoli e riferimenti esatti. Questa forma rappresenta i valori strutturati anche quando i componenti non hanno un predicato RDF proprio. La pubblicazione registra i byte e il loro hash nella stessa transazione del set. Il digest per Onboarding, Ingestion e UDP è quello della definizione JSON.

Il campo `status` di `references:resolve` indica lo stato corrente della revisione fissata. In preparazione Onboarding richiede `ACTIVE` per il tipo e per ciascun pin annidato. La rilettura storica accetta anche `DEPRECATED` e `RETIRED`, con la stessa definizione e lo stesso hash.

Nei vincoli dei componenti, `minInclusive` e `maxInclusive` sono stringhe JSON canoniche del tipo integer, decimal, date o datetime. Per esempio, un limite intero si scrive `"9007199254740993"`. Per string, `maxLength` è un intero JSON non negativo. Per concept, `vocabularyRef` è l’IRI assoluto di un vocabolario pubblicato. La validazione segnala un vincolo non valido con il codice `DT-CONSTRAINT`.

## CI gates

`.github/workflows/module-ci.yml` is the authoritative single-module gate. It
runs Java 21, Maven and all Flyway migrations against PostgreSQL 17, records
Surefire evidence, builds the production container and verifies its non-root
runtime identity. Maven network operations and jobs have explicit timeouts.

`.github/workflows/pairwise.yml` is the future 1+1 gate. It intentionally
refuses execution until the requested, versioned fixture set exists: absence of
real pairwise fixtures can never be reported as PASS.
