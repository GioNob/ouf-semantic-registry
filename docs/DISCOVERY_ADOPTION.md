# Adozione di un candidato della discovery

Il tool `semantic.discovery.adopt` esegue un comando HUMAN dell’owner Semantic. Gateway invia `POST /api/semantic/v1/proposal-commands/adopt` con `Content-Type: application/json` e la prova `X-OUF-Semantic-Proposal-Receipt`. Lo schema JSON 2020-12 definisce gli argomenti del tool per riferimento allo schema v1 e la risposta HTTP 200 in `#/$defs/receipt`. Entrambi gli oggetti sono chiusi. [Schema macchina v2](discovery-adoption-v2.schema.json)

## Trasporto

Esempio di envelope minimo prima della firma. Gli identificativi sono illustrativi.

```json
{
  "CapabilityID": "ouf.semantic.discovery.adopt",
  "GatewayBindingRef": "capability://ouf.semantic.discovery.adopt",
  "Owner": "semantic",
  "OperationClass": "COMMAND",
  "IdempotencyKey": "edicole-adopt-01",
  "Identity": {"PrincipalID": "mapper", "TenantID": "tenant-esempio", "ActorType": "HUMAN"},
  "Arguments": {
    "commandKey": "edicole-adopt-01",
    "requestId": "11111111-1111-4111-8111-111111111111",
    "candidateId": "22222222-2222-4222-8222-222222222222"
  }
}
```

Usare la firma v1 delle proposte, purpose `semantic-proposal-owner`, dominio MAC `ouf-semantic-proposal-owner-v1.`, metodo POST e path esatto. La prova lega SHA-256 dei byte dell’envelope, capability, issuer, audience, workload, identità, ruoli, scope, `iat`, `exp` (durata massima 30 secondi) e `idempotencyKey`. Ripetere la stessa chiave in `Arguments.commandKey` e `IdempotencyKey`. Il filtro ricava dalla firma l’header owner `Idempotency-Key`. Usare issuer, tenant e subject della delega con cui è stato aperto il job. Lo scope richiesto è `ouf.semantic.discovery`. La policy owner verifica il grant corrente su ogni invocazione, compreso il replay.

La prova HTTP ha la forma `payload.signature`. `payload` è il JSON della prova codificato Base64URL senza padding. `signature` è il Base64URL senza padding di HMAC-SHA256 sui byte ASCII di `ouf-semantic-proposal-owner-v1.` seguiti da `payload`. Il firmatario riusa la custodia del canale proposte. I campi della prova sono quelli del record `SemanticProposalReceiptVerifier.Receipt`. `bodyHash` è SHA-256 esadecimale minuscolo dell’envelope serializzato prima del trasporto.

## Ricevuta e riconciliazione

```json
{
  "requestId": "11111111-1111-4111-8111-111111111111",
  "candidateId": "22222222-2222-4222-8222-222222222222",
  "artifactId": "33333333-3333-4333-8333-333333333333",
  "revisionId": "44444444-4444-4444-8444-444444444444",
  "expectedRowVersion": 0,
  "semanticId": "https://example.org/onto/Place",
  "status": "DRAFT",
  "provenance": {
    "providerId": "SCHEMA_GOV_IT",
    "canonicalUri": "https://example.org/onto/Place",
    "sourceLocation": "https://example.org/catalogue/place.ttl",
    "publisher": "https://example.org/publisher",
    "license": null,
    "licenseWarning": "licenza mancante",
    "snapshotId": "55555555-5555-4555-8555-555555555555",
    "rdfSha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  },
  "receiptSemantics": "DURABLE_COMMAND_RESULT_NOT_CURRENT_STATE",
  "runtimeAuthorityIssued": false,
  "notReleaseAcceptance": true
}
```

L’owner rilegge solo candidati di job `SUCCEEDED` dello stesso delegato. Usa URI canonico come `semanticId`, namespace e nome locale della risorsa RDF, soggetto come owner, publisher come authority e `1.0.0` come versione locale iniziale. `sourceLocation` è la sorgente registrata dal provider. Publisher e licenza si leggono dai predicati Dublin Core `publisher` e `license` (terms o elements/1.1) sul soggetto canonico. In mancanza del predicato, si esaminano le risorse esplicitamente collegate da `rdfs:isDefinedBy` nello stesso grafo. Sono ammessi IRI o valori letterali univoci. Con licenza presente, `licenseWarning` vale `null`. La selezione di classe e categoria per il mapping resta all’umano dopo la discovery (D-059 e D-060).

La chiave appartiene alla coppia tenant/soggetto e condivide lo spazio delle chiavi degli altri comandi di proposta. Commit di DRAFT, snapshot, audit e ricevuta avvengono nella stessa transazione. In caso di esito incerto usare `semantic.proposal.read` con `commandKey` originale oppure ripresentare l’intento identico con prova fresca. La lettura richiede HUMAN e i grant correnti `ouf.semantic.proposal.read` e `ouf.semantic.discovery.adopt`, con i rispettivi scope. Restituisce `operation: "ADOPT"`, `result` uguale alla ricevuta, `historicalSnapshot: true` e `ownerStateMustBeRechecked: true`. La ricevuta storica resta leggibile dopo la scadenza e la pubblicazione. Ripresentare il comando ADOPT verifica lo stato corrente anche con la stessa chiave. Se differisce dalla ricevuta, la risposta indica `receiptSemantics=CURRENT_ADOPTION_REFERENCE`.

Un candidato di un nuovo job può riusare la revisione se coincidono URI, tipo, provider, sorgente e snapshot RDF con la provenienza attestata. Una bozza è visibile al delegato del job di adozione originario, identificato da issuer, tenant e soggetto. La risposta `DRAFT` contiene la versione da preparare. La risposta `UNDER_REVIEW` contiene anche `challengeId`, `challengeStatus` e `trustedApprovalRef`. Con `ACTIVE` usare direttamente `semanticId`, `revisionId` e `publicationSetId` per il mapping e la lettura esatta. Il comando conserva la ricevuta v1 della prima creazione.

| HTTP | Codice | Significato |
|---|---|---|
| 403 | `SEM_PROPOSAL_RECEIPT_INVALID` | Prova, attore, scope o envelope incompatibili. Anche un argomento aggiuntivo invalida la prova del comando. |
| 403 | `SEM_CAPABILITY_REQUIRED:ouf.semantic.discovery.adopt` | Grant owner assente o revocato. |
| 404 | `SEMANTIC_CANDIDATE_NOT_FOUND` | Coppia assente o fuori dal job del delegato. |
| 409 | `CANDIDATE_EXPIRED` | Candidato scaduto prima dell’adozione. |
| 409 | `IDEMPOTENCY_KEY_REUSE` | Intento o operazione diversi sotto la stessa chiave. |
| 409 | `SEMANTIC_IDENTITY_MISMATCH` | Il campo `reason` vale `NAME_OR_ORIGIN_ALREADY_BOUND` per un nome o un’origine già assegnati, oppure `TYPE_OR_PROVENANCE_UNMATCHED` se tipo o provenienza non confermano la corrispondenza. |
| 409 | `SEMANTIC_REVISION_UNAVAILABLE` | Revisione deprecata o ritirata. |
| 409 | `PUBLICATION_RECONCILIATION_REQUIRED` / `REVIEW_RECONCILIATION_REQUIRED` | Evidenza insufficiente per indicare un riferimento univoco. |
| 409 | `CANDIDATE_PUBLISHER_MISSING` / `CANDIDATE_METADATA_AMBIGUOUS` / `CANDIDATE_METADATA_UNRESOLVED` | I byte disponibili non identificano il publisher o un valore di metadato univoco e leggibile. |
| 409 | `CANDIDATE_REFERENCE_UNRESOLVED` / `CANDIDATE_VOCABULARY_UNRESOLVED` | Domain/range di una relazione o schema di un concetto non identificabili nel registro locale. |

## Approvazione e lettura

Passare `revisionId` e `expectedRowVersion` a `semantic.review.prepare`. Con `PASS`, invocare `semantic.approval.request` con la stessa revisione/versione e il `validationRunId` ottenuto. Usare una chiave distinta per ciascun comando. La scheda THS `GET /api/trusted-human/v1/semantic-approval-challenges/{id}` contiene `adoptionProvenance`, identica alla provenienza della ricevuta e inclusa in `definition_json` per il calcolo del fingerprint approvato. Il campo `rdfSha256` identifica i byte RDF, mentre `targetContentHash` identifica il contenuto della revisione sottoposta alla decisione. La decisione e la pubblicazione seguono i due comandi HUMAN della THS.

`semantic.get(semanticId,revisionId,publicationSetId)` risolve anche una pubblicazione storica. Per una revisione adottata, `rdf_snapshot` espone `snapshot_id`, `content_hash`, `media_type`, `byte_count` e `content_path`. `content_base64` contiene i byte esatti quando entrano nel limite JSON dell’owner. Per leggere integralmente uno snapshot più grande, usare GET sull’owner al `content_path` con grant `ouf.semantic.read` e `Accept` uguale a `media_type`. Il path è vincolato a PublicationSet e artefatto. Il limite JSON può ridurre anche la lista delle triple proiettate, segnalata da `partial`.

Con una challenge scaduta il chatbot avvia un nuovo `semantic.review.prepare` con la versione nota. Il registro chiude la challenge come `EXPIRED` e valida la bozza alla versione successiva. Passare `validated_row_version` e il nuovo run alla richiesta di approvazione. Anche una nuova `semantic.approval.request` che presenta il run verde della versione appena scaduta esegue la nuova validazione prima di aprire la challenge. Per una nuova preparazione o richiesta serve una nuova chiave. La THS presenta la nuova challenge sul percorso di decisione esistente.

V16 applica questa riconciliazione anche alle challenge aperte prima del rilascio. Per i claim di pubblicazione esistenti, V16 cerca una sola coppia revisione/decisione compatibile con evento, membro del manifesto, hash e tempi della decisione. Un replay dubbio restituisce HTTP 409 con `PUBLICATION_RECONCILIATION_REQUIRED`. Una chiave vincolata a un intento diverso restituisce HTTP 409 con `PUBLICATION_IDEMPOTENCY_CONFLICT`.

## Catalogo e grant al rilascio

Aggiungere questo elemento a `catalogue/r4a-semantic-human-capabilities.json` nell’artefatto Onboarding.

```json
{
  "ownerRef": "semantic",
  "descriptor": {
    "capabilityId": "ouf.semantic.discovery.adopt",
    "operation": "COMMAND",
    "requiredScope": "ouf.semantic.discovery",
    "allowedActors": ["HUMAN"]
  }
}
```

Per D-071, Onboarding registra il descrittore al rilascio. Nel catalogo completo dei ruoli di `authorization.permissions.propose` (`REPLACE_ROLES`), aggiungere la capability al ruolo mapper scelto, conservando tenant, assegnazioni, vincoli e scadenze approvati. Il grant compilato ha `capabilityId=ouf.semantic.discovery.adopt`, effetto `ALLOW` e `externalRoleRef` del ruolo autorizzato. La THS amministrativa presenta il diff e attiva descrittore e grant con la conferma umana.

Flyway applica V13 dopo V12. L’upgrade ricostruisce i legami V4 dall’audit originale. Per le DRAFT storiche aggiornate incrementa `row_version` e richiede una nuova validazione. I dati già approvati conservano il fingerprint storico. La tabella `ouf_sem.revision_adoption` fa parte dei dati applicativi PostgreSQL da salvare e ripristinare insieme a revisioni, audit e snapshot. D-065 non introduce un nuovo archivio di configurazione in Semantic. La registrazione e l’attivazione del grant spettano al rilascio Onboarding.

## Consegna governata e ritorno dopo V13

Sulle pull request, il workflow di modulo conserva l’immagine di produzione dopo i test Java/PostgreSQL e la verifica non-root. L’artefatto GitHub Actions `semantic-registry-governed-image-<runId>` dura 14 giorni e contiene `image.tar.gz`, `manifest.json` e `SHA256SUMS`. La CI conserva l’immagine come artefatto, senza pubblicarla su un registry.

Il manifest del publisher `ouf.semantic-tested-image.v1` lega il commit sorgente della PR, il commit e l’albero del checkout provato, il run e il tentativo CI, il tag e l’ID dell’immagine, l’etichetta di revisione e il digest SHA-256 dell’archivio. La lista `flywayMigrations` contiene `name` e `sha256` per ogni `db/migration/V*.sql`, calcolati sui byte del JAR estratto dall’immagine. L’esecutore privilegiato di `ouf-deploy` verifica la provenienza e presenta le migrazioni nel piano A2 da approvare. L’autorizzazione sul target segue il cutover governato.

Il ritorno v29 rimette in servizio l’immagine precedente sullo stesso database, dove V13 resta applicata. Nel job PostgreSQL 17, `Postgres17RuntimeTest` verifica che V13 sia applicata, ripete la validazione sullo stesso database con la configurazione Flyway di `application.yml` e le sole risorse V1–V12, e controlla che V13 sia classificata come migrazione futura. La validazione usa il comportamento predefinito di Flyway per le migrazioni future e lascia intatta la cronologia. La prova riguarda la compatibilità della validazione Flyway.
