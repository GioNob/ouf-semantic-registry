# R2b — risultato acquisito, consultabile e verificabile

Autorità: Reality Baseline Package v1.7, PET Ingestion v1.3 §§21, 45.2, 128, 139 e PET UDP v1.3 §§95–97, 109.6–109.7. Nessuna decisione già risolta viene riaperta senza nuova evidenza.

## Criterio umano

Un operatore approva una fonte con significato dei campi, identità e classificazioni espliciti. Il lettore autorizzato deve poi poter trovare i valori prodotti e controllarne la provenienza. Il test R2b richiede `Alpha` dal file e `Beta` dalla fonte PULL attraverso le API reali di serving, l'omissione del campo riservato e una risposta di lineage. Il solo stato RUNNING o una riga presente nel database non soddisfano il criterio.

Ogni incremento successivo deve dichiarare: persona/ruolo, obiettivo, superficie utilizzabile, risultato osservabile e modo di verificarlo. I criteri tecnici accompagnano questo scenario. Una superficie browser o conversazionale mancante resta un gap esplicito.

## Cambiamenti

- Onboarding espone anche la pubblicazione storica esatta `bundleId:version:checksum`; il runtime non sostituisce una versione fissata con l'ACTIVE corrente.
- Ingestion compone i port Gateway autenticati, gli adapter esistenti e i loop automatici. La persistenza di record, outbox e checkpoint è vincolata alla lease corrente. Il checkpoint vuoto di una nuova run managed viene interpretato come inizio file.
- Lake/UDP verificano e conservano RAW, NORMALIZED e CURATED, trattengono il raw sorgente necessario alla provenienza, emettono un ACK durevole e rifiutano il riuso di un handoff con diverso contenuto/contesto.
- UDP risolve i profili dalla pubblicazione pinning, controlla classi/mapping/label e materializza nella transazione di completamento del job. Il tenant configurato è conservato negli oggetti.
- Gateway registra i contratti delle route owner e mantiene il percorso originale nelle route di namespace. La dichiarazione di route non costituisce attivazione del dataplane APISIX.

## Prova tra processi

Workflow Ingestion `R2b source to authorized serving`, script `pairwise/r2b_serving.py`:

1. lifecycle Onboarding reale e due fonti approvate;
2. JAR Ingestion con admission/acquisizione/outbox schedulati, UDP reale e MinIO reale;
3. HTTP 202 dopo una vera persistenza UDP: watermark fermo;
4. interruzione forzata e riavvio Ingestion, consegna idempotente e ACK recuperato;
5. due run concluse, watermark coerenti, materializzazione e lettura autorizzata dei valori;
6. campo riservato omesso, lettura anonima negata e identità writer priva di lettura;
7. lineage, riferimenti RAW trattenuti, zone Lake verificate e serving dopo riavvio UDP senza duplicare revisioni.

Il test produce `summary.json` e `human-scenario.json` negli artifact CI. I commit e gli esiti finali sono nel registro JSON di coordinamento.

## Limiti che restano aperti

La prova utilizza tre JVM reali, PostgreSQL/PostGIS e MinIO, con fixture dichiarate per HTTP Gateway, sorgenti, Semantic e identità/approvazione. Le fixture di bootstrap sono escluse dai JAR di produzione. Non si attribuisce loro valore di autenticazione IAM/THS reale.

APISIX/etcd, adapter southbound governato per `/internal/sources/v1/fetch`, servizio effettivo di managed object storage, identità reali e Semantic reale rimangono gate nominati GW-01/AUT-04/R6/SEM-01. Il test non esegue questi componenti reali e non prova da solo la piattaforma distribuita completa.

Il profilo dimostrato è CSV + REST JSON, proprietà canoniche e serving. Gli altri profili GIS, la catena completa relationship/spatial, replay, feedback drift/Onboarding e scenari storici estesi restano nelle rispettive righe PET. I gruppi ONB-02, ING-01 e UDP-01 restano PARTIAL: il loro criterio di chiusura è più ampio di questa prova.

Per l'utente, la superficie verificata qui è l'API autorizzata. Browser THS, catalogo MCP e presentazione integrata di avanzamento/errore restano R4/R3. L'esito Ingestion SUCCEEDED attesta la consegna durevole; la disponibilità alla consultazione viene verificata separatamente attraverso UDP.

## Evidenza finale accettata

[CI del percorso completo, 16 verifiche superate](https://github.com/GioNob/ouf-ingestion-runtime/actions/runs/35189931361). Tre consegne HTTP, una risposta 202 simulata dopo persistenza e un ACK duplicato recuperato. Tutte le CI di modulo/SDK sui commit finali delle PR sono verdi.

| Repository | PR | Commit mergiato |
|---|---|---|
| Onboarding | [13](https://github.com/GioNob/ouf-source-onboarding/pull/13) | `9a94246071958d34391e28c8e38158023052d311` |
| Ingestion | [24](https://github.com/GioNob/ouf-ingestion-runtime/pull/24) | `249166c9be5469c4212c61d620476dfebe52f60a` |
| UDP | [26](https://github.com/GioNob/ouf-udp-object-resolution/pull/26) | `6944db56317b43073299a93f1603c065d03e50e3` |
| Gateway | [27](https://github.com/GioNob/ouf-api-gateway/pull/27) | `8fa1dc383333de4eab704924cc4acf249f4a56d8` |

La run PR esegue il merge sintetico GitHub `a1619d414e7075c93ada1a51847c720d82f8343f`, distinto dal commit finale di merge. Il registro conserva entrambi i riferimenti e i digest degli artifact.
