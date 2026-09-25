# OUF — HANDOFF OPERATIVO COMPLETO
## Stato al 25 settembre 2026 — ripartenza da Keycloak client-scope bootstrap

## 0. Punto esatto di ripartenza

L'ultimo passo applicato è stato l'aggiornamento GitHub del Source Onboarding con un reconciler generico dei Keycloak client scope.

PR Source Onboarding #37:
- branch: `codex/r4a-authorization-catalogue`
- HEAD: `3d21b0b31ac3547a4c810e67d17c45f687d0cb23`
- CI:
  - il commit funzionale precedente `648b6cab5d6b1deda900dcc4c39316bcafae5ae1` aveva Module CI #554 e R2f #374: SUCCESS
  - il nuovo HEAD `3d21b0b31ac3547a4c810e67d17c45f687d0cb23` aggiunge solo l'aggiornamento `docs/RUNBOOK.md`; CI #556/#376 era in esecuzione al momento dell'handoff

Nuovi file:
- `scripts/r4a_keycloak_client_scope_catalogue.py`
- `tests/test_r4a_keycloak_client_scope_catalogue.py`

Il controllo live Keycloak ha restituito:
```text
ouf.onboarding.configuration.write=MISSING
ouf.ingestion.configuration.attest=MISSING
```

NON è stato ancora eseguito alcun apply del nuovo reconciler su Keycloak.

La nuova chat deve ripartire da qui.

## 1. Regole operative mandatory

- PET v1.7 + Cross-Module Alignment Matrix sono la BIBBIA.
- A ogni sprint/cambio area confrontare il lavoro con PET e matrix.
- Standardizzare, automatizzare, versionare; evitare hack live one-off.
- GitHub-first: branch/commit/PR -> CI -> VPS fetch/build/test/deploy.
- Un blocco corto di comandi per volta.
- Indicare sempre la sede di esecuzione: SSH `oufadmin`, PowerShell PC, Browser, GitHub/ChatGPT.
- Mai stampare token, password, client secret, private key o admin key.
- Preservare rollback, container precedenti, snapshot e backup fino a chiusura acceptance.
- Niente INSERT SQL diretti per “far passare” acceptance dati.
- R-INSTALL resta OPEN finché non esiste prova clean-install/upgrade/restore.
- Nuovo gate formale R-SMOKE: “vedere il fumo” end-to-end da source reale a ricerca oggetti.

## 2. Obiettivo corrente

Completare R4a `urban.object.search` con dati reali governati.

Vertical slice attesa:
source -> Onboarding -> semantic references -> activation -> Ingestion -> RAW/Lake -> handoff -> UDP materialization -> `urban.object.search`.

Acceptance dati:
- almeno 3 oggetti reali dello stesso canonical type;
- almeno un candidato non accessibile per test minimizzazione;
- due pagine reali;
- cursor;
- partial;
- invalid cursor;
- property/minimization authorization;
- audit/evidence.

## 3. Authorization

PolicyBundle ACTIVE:
`ouf-lab-authorization:22`.

v21 ha aggiunto:
- `ouf.onboarding.configuration.write`
- `ouf.ingestion.configuration.attest`

v22 ha aggiunto il grant SERVICE:
- grantId: `grant-onboarding-configuration-attest-ingestion`
- capability: `ouf.ingestion.configuration.attest`
- tenant: `ouf-lab`
- servicePrincipalId: `ouf-ingestion`

Lifecycle v22 verificato:
```text
PUBLISHED=true POLICY_REF=ouf-lab-authorization:22
ACTIVE_VERIFIED=true EXISTING_GRANTS_PRESERVED=true
```

Rimane da creare il grant HUMAN per `ouf.onboarding.configuration.write` al principal HUMAN `ouf-admin` attraverso percorso governato. Non usare lo script SERVICE per un subject grant e non modificare direttamente DB/PolicyBundle.

## 4. Keycloak — punto aperto immediato

Sessione `kcadm` era scaduta ed è stata rinnovata tramite login interattivo come bootstrap admin `oufadmin`.

Controllo live:
```text
ouf.onboarding.configuration.write=MISSING
ouf.ingestion.configuration.attest=MISSING
```

Nuovo helper Source Onboarding verde:
`scripts/r4a_keycloak_client_scope_catalogue.py`.

Contratto:
- plan/apply/verify;
- scope OIDC;
- `include.in.token.scope=true`;
- `display.on.consent.screen=false`;
- matching esatto;
- preserva attributi extra;
- non stampa segreti.

Ordine previsto:
1. fetch del branch/HEAD verde sul VPS;
2. `plan` per i due scope;
3. `apply`;
4. `verify`;
5. assegnazione:
   - `ouf-human-admin` -> OPTIONAL `ouf.onboarding.configuration.write`;
   - `ouf-ingestion` -> DEFAULT `ouf.ingestion.configuration.attest`;
6. token acceptance, senza stampare token;
7. grant HUMAN governato;
8. test autenticati.

## 5. Source Onboarding live

Repository:
`GioNob/ouf-source-onboarding`

Branch R4a:
`codex/r4a-authorization-catalogue`

Live container:
`ouf-onboarding:r4a-5866007`

Rollback recente:
`ouf-onboarding-pre-5866007`

Backup recente:
`/opt/ouf/backup/onboarding-runtime-20260925T111539Z`

Smoke:
`ouf-onboarding-r4a-smoke`

Nuove route/app behavior:
- HUMAN mutating source lifecycle richiede `ouf.onboarding.configuration.write`;
- compatibility attestation richiede SERVICE + `ouf.ingestion.configuration.attest`;
- endpoint M2M:
  `POST /api/internal/v1/onboarding/compatibility/ingestion-runtime`.

Lifecycle source atteso:
source -> version -> validate/submit -> approval challenge -> HUMAN approval -> SERVICE ingestion compatibility attestation -> HUMAN activate -> `published_configuration`.

Le tabelle live erano ancora vuote per source/onboarding publication. Non creare fixture via SQL.

## 6. Gateway

Repository:
`GioNob/ouf-api-gateway`

Branch:
`codex/r4a-object-search`

HEAD versionato noto:
`9fb177de3021ffc90b45a847a42ac7eec24d6784`

Deploy route R4a completato.

Backup HUMAN:
`/opt/ouf/backup/trusted-human-onboarding-p9k1x5zk/previous.json`

Backup M2M:
`/opt/ouf/backup/internal-m2m-routes-5c04fc48/previous.json`

WORK preservato:
`/tmp/r4a-onboarding-gw.W9tTnm`

Acceptance anonima:
```text
GET /api/onboarding/v1/sources -> 401
POST /api/onboarding/v1/sources -> 401
GET /api/trusted-human/v1/approval-challenges/<dummy> -> 401
POST /api/internal/v1/onboarding/compatibility/ingestion-runtime -> 401
```

Questa acceptance è PASS.

## 7. InstallationConfiguration

ACTIVE revision: 5.

Projection:
`/opt/ouf/installation/active-projection.json`

installationId:
`ouf-lab-netcup-01`

Valori verificati:
- issuer: `https://auth.ouf-lab.it/realms/ouf`
- audience: `ouf-api-gateway`
- public API base: `https://api.ouf-lab.it`
- ingestion workload client: `ouf-ingestion`
- onboarding service binding: `ouf-onboarding`
- semantic service binding: `ouf-semantic`

Backup:
`/opt/ouf/backup/active-projection-pre-r5.json`

## 8. UDP R4a live

Repository:
`GioNob/ouf-udp-object-resolution`

Branch:
`codex/r4a-object-search`

Current known HEAD:
`944c2f5af8c6b760186af7ede5170318f932e812`

Live:
`ouf-udp:r4a-944c2f5`

Rollback:
`ouf-udp-pre-944c2f5`

Backup:
`/opt/ouf/backup/udp-runtime-20260925T103336Z/container-inspect.json`

Smoke:
`ouf-udp-r4a-smoke`

Published Execution:
- enabled = true;
- Gateway URL = `https://api.ouf-lab.it`;
- token file = `/run/ouf-udp-auth/token`;
- tenant = `ouf-lab`.

Flyway:
- 27 migrations validate;
- DB schema current version 26;
- up to date.

Dati live:
```text
handoff_intake=0
materialization_job=0
urban_object=0
```

Quindi il runtime è pronto ma non ha ancora ricevuto dati governati.

## 9. Semantic live

Repository:
`GioNob/ouf-semantic-registry`

R4a branch noto:
`codex/r4a-udp-workload-bootstrap`

HEAD verde noto:
`b5e5c837efd30ff16e6a486df419d619244a93b3`

Live:
`ouf-semantic:r4a-b5e5c83`

Rollback:
`ouf-semantic-pre-b5e5c83`

Backup:
`/opt/ouf/backup/semantic-runtime-20260925T094420Z`

Smoke:
`ouf-semantic-r4a-smoke`

Prima di creare la prima PublishedRuntimeConfiguration bisogna inventariare i riferimenti Semantic live realmente disponibili e usare exact identities valide. Non creare bundle di prova incompatibili con il runtime UDP.

## 10. Ingestion — prossimo tratto dopo IAM

Il runtime Ingestion dovrà:
- ottenere token workload con `ouf.ingestion.configuration.attest`;
- attestare la compatibility della configurazione Onboarding;
- consumare una source ACTIVE;
- scrivere RAW/Lake tramite capability governata;
- produrre handoff UDP durable;
- causare materializzazione di Urban Object.

Prima di mutare Ingestion fare inventory del runtime live e riusare i meccanismi versionati esistenti.

## 11. Backup/rollback da preservare

Non cancellare:
- `/opt/ouf/backup/internal-m2m-routes-g6w5z9p6/previous.json`
- `/opt/ouf/backup/internal-m2m-routes-vop_6efs/previous.json`
- `/opt/ouf/backup/internal-m2m-routes-5c04fc48/previous.json`
- `/opt/ouf/backup/trusted-human-onboarding-p9k1x5zk/previous.json`
- `/opt/ouf/backup/authorization-bundle-route-bs_do58x/previous.json`
- `/opt/ouf/backup/onboarding-runtime-20260925T074324Z/container-inspect.json`
- `/opt/ouf/backup/onboarding-runtime-20260925T111539Z`
- `/opt/ouf/backup/active-projection-pre-r4.json`
- `/opt/ouf/backup/active-projection-pre-r5.json`
- `/opt/ouf/backup/semantic-runtime-20260925T094420Z`
- `/opt/ouf/backup/udp-runtime-20260925T103336Z/container-inspect.json`

Preservare anche rollback e smoke container elencati sopra.

## 12. R-INSTALL — gate formale

R-INSTALL non si chiude finché chi possiede accesso ai repository non può installare OUF su una nuova macchina senza ricostruire la procedura dalle chat.

Deliverable minimi:
- bootstrap/install orchestrator top-level;
- Installation manifest dichiarativo;
- secret reference model;
- IAM bootstrap idempotente;
- capability/grant lifecycle automatico e versionato;
- Gateway materialization/deploy;
- build/deploy dei sei moduli;
- clean install;
- upgrade;
- backup/restore;
- rollback;
- acceptance E2E;
- CI di installabilità.

Ogni pattern scoperto in R4a va assorbito in questo percorso.

## 13. R-SMOKE — gate formale “vedere il fumo”

Obiettivo operatore:
“carico/collego una source, OUF capisce cosa contiene, vedo come viene semantizzata, parte l'Ingestion e poi ritrovo gli oggetti”.

Primo smoke:
- CSV oppure GeoPackage reale;
- schema/profilo osservabile;
- ontologia e vocabolario controllato proposti/selezionati;
- approval governata;
- Ingestion reale;
- Lake/handoff/materialization;
- almeno 3 Urban Object;
- ricerca reale.

Estensioni successive:
- XLSX;
- Shapefile ZIP;
- Microsoft Access con suggerimento da chiavi/relazioni;
- layer dinamici via web service;
- suggerimento di relazioni ontologiche;
- verifica duplicati/soglia di similarità;
- aggiornamento incrementale.

La UI completa può arrivare dopo il primo smoke tecnico, ma il percorso non può bypassare governance/Authorization.

## 14. Supply chain

La CI UDP usa temporaneamente un mirror MinIO terzo pinned:
`docker.io/tobi312/minio@sha256:e2226dea4b9aef896db02f7396102d48eb58cd339d930332e3d8bdac80012a78`.

È una soluzione temporanea. R-INSTALL deve portare a un'immagine OUF-owned/vendor-built riproducibile, pinned, con SBOM/scanning.

## 15. Punto operativo immediato per la nuova chat

Prima di qualunque altra mutazione:
1. leggere PET v1.7 / Matrix per IAM-Onboarding;
2. verificare che PR #37 sia ancora verde sul HEAD atteso;
3. sul VPS fare fetch del branch senza checkout distruttivo;
4. eseguire il nuovo reconciler dei client scope in modalità `plan` per:
   - `ouf.onboarding.configuration.write`
   - `ouf.ingestion.configuration.attest`
5. solo dopo output pulito procedere con apply/verify.

Non reinstallare servizi.
Non rigenerare password.
Non eliminare rollback.
Non creare dati direttamente nel DB.


## 16. Aggiornamento operativo — 25 settembre 2026, sera (sostituisce §15)

Source Onboarding PR #37, branch `codex/r4a-authorization-catalogue`, HEAD
`44b4bea40efcf0c4d78e30f6d1d4102e1a7c9d45`. CI module #600 e trusted
review browser #420 entrambe SUCCESS. Il branch aggiunge riconciliazione dei
binding client scope, controllo dell'attributo Device Flow, smoke token HUMAN,
lifecycle add-only del grant HUMAN, test CI espliciti e runbook.

Keycloak live:
- `ouf.onboarding.configuration.write` e `ouf.ingestion.configuration.attest` creati e verificati;
- `ouf-human-admin` -> OPTIONAL write; `ouf-ingestion` -> DEFAULT attest;
- attributo effettivo Device Flow del client HUMAN
  `oauth2.device.authorization.grant.enabled=true` già presente; il primo
  reconciler leggeva erroneamente un campo assente e il suo tentativo di apply
  è stato respinto. Script e runbook corretti, verify PASS, nessuna modifica
  necessaria al Device Flow;
- token workload Ingestion rinnovato: client, freshness, expiry e attest scope PASS;
- token HUMAN nuovo con write scope: issuer, client, user `ouf-admin`, actor,
  Gateway audience, scope, freshness e expiry PASS.

Authorization ACTIVE è ora `ouf-lab-authorization:23`. Grant HUMAN
`grant-onboarding-configuration-write-human-admin` per il subject IAM corrente
`b93d8cf6-cd14-4ee6-91d7-84cd76c4f500`, capability
`ouf.onboarding.configuration.write`, tenant `ouf-lab`, validità
2026-09-25T00:00:00Z–2026-10-25T00:00:00Z. Lifecycle governato
plan/draft/preview/publish/verify completato. Existing grants preserved.

Acceptance applicativa: token HUMAN fresco attraverso Gateway su
`POST /api/onboarding/v1/sources/<random-nonexistent>/onboarding-versions`
restituisce HTTP 404 con owner code `ONB_NOT_FOUND` e
`ONBOARDING_AUTHORIZED_NO_WRITE=true`. Nessuna source/versione è stata creata
in questo smoke.

Semantic live: `published_sets=0`, `active_artifacts=0`, nessun latest
publication set. Nel container non sono impostati
`OUF_SCHEMA_GOV_ENABLED` o `OUF_DISCOVERY_WORKER_ENABLED`: default versionati
rispettivamente false e true. L'unico provider runtime di discovery esterna è
`SCHEMA_GOV_IT`; disabilitato, restituisce zero candidati. Non inventare
riferimenti Semantic o configurazioni UDP. Il PET supporta cold start governato:
DRAFT Semantic -> validazione -> approvazione HUMAN -> publication set ->
exact SemanticReference in Onboarding.

**Prossimo tratto:** acquisire un CSV reale per R-SMOKE, inventariare il
percorso di staging `object://` e il worker di profiling Onboarding; produrre
schema/profilo osservabile e proposta semantica, poi pubblicare reference
Semantic tramite review HUMAN. Solo dopo creare/attivare una
PublishedRuntimeConfiguration valida per Ingestion/UDP. Non usare SQL fixture.
R-INSTALL e R-SMOKE restano OPEN.

## 17. R-SMOKE CSV reale e gap intake — 25 settembre 2026, 23:08 Europe/Rome

L'utente ha allegato `cinema_trieste(1).csv`: 509 byte, SHA-256
`a07c2dcdc21aa9a23fb5585a69d52031dc08010d251bf39bfa67c8e0962c6e1a`,
UTF-8 con BOM, CRLF, due colonne `cinema` e `indirizzo`, 8 righe
senza campi vuoti. Non pubblicare l'allegato né caricarlo direttamente
su MinIO eludendo l'intake Gateway; mantenere i byte originali/hash.
Il profiler Source Onboarding lasciava il BOM nella prima intestazione:
corretto in PR #37, commit `32d2713529adbe4434c731fe5a516f085b20af3e`,
con test per intestazioni BOM e campi con virgole tra virgolette.
Source Onboarding module CI #36189548425 SUCCESS e trusted review
browser #36189548448 SUCCESS. Il runtime live non incorpora ancora il fix.

VPS: `ouf-minio`, `ouf-onboarding` e `ouf-apisix` condividono la rete
`ouf-backend`; APISIX è anche in `ouf-gateway-control`.
Probe anonimo della route `GET /internal/object-storage/v1/content`
ha restituito HTTP 404. Il Gateway dichiara la route verso
`ouf-object-storage:8080/v1/content`, ma non esiste un container
`ouf-object-storage` né un repository OUF omonimo trovato. Non dedurre
dal solo 404 l'assenza certa di una route per ogni principal; l'endpoint
non è comunque funzionante end-to-end senza backend.

Mount `ouf-onboarding`: solo
`/run/secrets/authorization-owner-key` e
`/run/secrets/onboarding-ths.yaml`; manca un token workload dedicato
alle letture dello storage. Mount `ouf-ingestion` include
`/run/ouf-ingestion-auth`, il cui token/client non va riutilizzato
come identità Onboarding. `GatewayManagedFileObjectStore` è condizionale
su `ouf.onboarding.object-store.gateway-base-url`, assente dalle env live,
e non allega oggi alcuna credenziale alla richiesta.
La route dichiarativa specifica `MTLS_SERVICE`, mentre il materializer
`tools/materialize_apisix_internal_m2m_routes.py` accetta soltanto
`M2M` con scope/attore SERVICE. Risolvere coerentemente identità,
materializzazione e autenticazione del client senza cambiare tacitamente
il contratto PET. Il PET Gateway T25 richiede upload streaming tramite
Gateway verso il servizio intake; upload diretto a MinIO con URL firmati
richiede una decisione architetturale esplicita.

Sequenza necessaria: implementare e testare il servizio intake/object
storage su MinIO con upload HUMAN governato e lettura SERVICE governata,
riconciliare scope/grant e credenziali di workload, materializzare route
APISIX con backup/rollback, configurare e deployare Onboarding profiler,
poi registrare l'asset usando stagingRef, size 509 e hash esatto.
Eseguire profiling/preview e cold start Semantic governato prima di
qualsiasi ACTIVE bundle. Non creare fixture DB o reference Semantic inventate.

## 18. Candidato intake governato del CSV — 25 settembre, notte

Con l'autorizzazione dell'utente, sviluppato senza deploy live il percorso per
l'allegato reale. Source Onboarding PR #37, branch
`codex/r4a-authorization-catalogue`, HEAD
`243606edb55a61ed55d9c3bb6ce082d40d275b92`: adapter MinIO condizionale
nel deployable Onboarding (nessun nuovo container), upload HUMAN
`POST /api/managed-sources/v1/files`, read SERVICE
`GET /api/internal/v1/onboarding/managed-files/content`, limite 10 MiB,
hash byte esatti, registrazione con hash e riferimento oggetto opaco, capability
owner su upload/profiling/preview/create-onboarding/read, token workload
Onboarding letto da file a ogni chiamata Gateway, manifest capability/grant,
batch HUMAN add-only, helper per catturare secret esistente senza stamparlo o
ruotarlo, procedura `docs/R4A_MANAGED_CSV_INTAKE.md` e
`scripts/r4a_managed_csv_smoke.py` sul CSV esatto. Il test locale legge
l'allegato: 509 byte e SHA-256 atteso PASS. Non committare il CSV.

Gateway PR #51, branch `codex/r4a-object-search`, HEAD
`83444c1f06de6e332a92b1163be01974655a7194`, CI Gateway SUCCESS:
route upload HUMAN e GET/POST HUMAN bounded namespace managed-files, route
read M2M verso `ouf-onboarding:8080`, capability/actor/scope dichiarati,
materializer e installer con snapshot/restore. Il contratto iniziale
`MTLS_SERVICE` verso un backend inesistente è stato sostituito da M2M
workload già supportato dagli installer APISIX; resta necessario bootstrap
client e concessioni governate. La route POST per `create-onboarding`
richiede a bordo lo scope profile e nel backend anche capability
`ouf.managed-source.onboarding.create`; sono previsti entrambi nel bundle
di scope/grant HUMAN.

La CI Onboarding sul HEAD `243606edb55a61ed55d9c3bb6ce082d40d275b92` è SUCCESS
(module CI `36192565381`, inclusa la build immagine non-root; trusted review
browser `36192565373` SUCCESS). Onboarding live è ancora il tag precedente e
APISIX non è stato mutato. Sul VPS risultano: nessun bucket/intake nuovo
verificato; nessun token `ouf-onboarding` montato; minio/onboarding/apisix
nella rete `ouf-backend`. Il CSV della chat NON è automaticamente sul VPS.

Prossimo gate operatore, solo dopo CI verde: checkout GitHub-first degli
script, `plan` del client workload `ouf-onboarding` e dei cinque nuovi
scope, quindi capability/grant plan e bootstrap MinIO con secret ristretti,
backup e rollback. Attivare route e deploy solo a valle dei gate; eseguire
lo smoke esatto tramite Gateway, poi Semantic cold start, approval e
Ingestion→UDP→search. R-INSTALL e R-SMOKE restano OPEN.
