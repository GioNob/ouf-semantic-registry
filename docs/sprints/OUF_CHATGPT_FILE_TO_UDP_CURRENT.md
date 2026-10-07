# OUF: percorso file → UDP tramite ChatGPT — stato corrente

## Criterio di accettazione confermato il 7 ottobre alle 14:10 Europe/Rome

La procedura operativa deve essere eseguita integralmente dalla chat tramite un chatbot compatibile MCP: caricamento, profilazione, mapping semantico assistito, onboarding governato, ingestion, UDP e risultati. SSH, sudo, script e trasferimenti di archivi eseguiti dall'utente non sono passi ammessi del flusso prodotto. I controlli tecnici finora eseguiti verificano la preparazione dell'infrastruttura; non valgono come dimostrazione del giro completo. La governance HUMAN/THS resta un requisito del prodotto e non viene sostituita da decisioni del chatbot.

## Risultato verificato il 7 ottobre 2026

La ricerca Cinema funziona realmente tramite ChatGPT, account ouf-admin: **8 oggetti ACTIVE, revisione1, 4 pagine da2, zero duplicati, partial=false e cursore finale nullo**. Le sole proprietà restituite sono nome e indirizzo. Dati già materializzati, nessun nuovo upload o replay/run. La riparazione cambia soltanto il nome upstream della rotta di ricerca, da ouf-udp-object-resolution:8080 (non risolto) a ouf-udp:8080, qualificato verso UDPcorrente. Snapshot privato /etc/ouf/deploy-snapshots/search-upstream-tb4mcsuu; nessun restart o modifica ai file storici.

Il filtro corretto è la classe **https://api.ouf-lab.it/semantic/cinema#Cinema**. L'URI dell'ontologia https://api.ouf-lab.it/semantic/cinema restituisce validamente zero oggetti: non usare quell'URI come tipo canonico. Classe verificata con semantic.get sulla revisione51706bed-81e4-4306-aca1-70119821727d, publicationsetf92a2e17-30c9-456f-bb12-63afa84f41e6. [Ricevuta minimizzata](../handoffs/receipts/OUF_CINEMA_CHATGPT_SERVING_2026-10-07.json), senza nomi/indirizzi/valori dei risultati.

## Obiettivo e prossimo lavoro

Da ChatGPT: selezione file, profilazione, mapping assistito, DRAFT Onboarding, review HUMAN/THS, compatibilità reale e ACTIVE, un run Ingestion/RAW/handoff, risoluzione identità/materializzazione UDP, lettura autorizzata in ChatGPT con lineage e audit pertinenti. Il giro interamente conversazionale di Teatri **non è ancora consegnato**. Il matching autoritativo UDP avviene dopo handoff; preflight non lo sostituisce.

| Passaggio | Stato concreto | Prossimo passo |
| --- | --- | --- |
| Upload/profile Teatri | Asset6609b245-86ed-4315-8ce0-73f2a8555bf3, profile7984c39c-7396-4248-ab0a-f2efc390b49c v1; 13righe/20campi. Rilettura già autorizzata/PASS | Riutilizzare, nessun nuovo upload/profile |
| Mapping Teatri | [Proposta dei20campi](TEATRI_MAPPING_REVIEW_CURRENT.md), non approvata | Granularità teatro/sala già confermata; semantica pubblicata con pin esatti, identitàsource, classificazione e gestione dubbi |
| Discovery/adoption | Discovery nazionale selezionata. Configurazione VPS provata: provider disabilitato, worker abilitato, Gateway origin mancante. MCP attuale privo di discovery.request. Cultural-ON/Schema restano candidati, non pin pubblicati | Implementare raccordo nazionale governato e richiesta/stato/candidati via MCP; poi riferimenti pubblicati con governance HUMAN/THS |
| DRAFT e review | Tool crea DRAFTbase, non ACTIVE; validator richiede contratti e semanticReferenceBindings | Riutilizzare completamentoCinema, freeze/challenge/HUMANTHS e ripresa da stato owner; non simulare attestazioni |
| Ingestion/UDP Cinema | Storico run86809c17-3354-45ca-a7e6-57e903944b24 SUCCEEDED, 8handoffACKED e 8materializzati | Preservare. ingestion.status resta authorizationdenied, non prova runfallito; risolvere osservabilità distintamente |
| Serving Cinema | Lettura ChatGPT8/8 provata con paginazione | Evitare regressioni: generator Gateway ancora hardcoded su vecchio hostname, correggere binding installazione prima di redeploy. Prove negative/authority/audit complete restano aperte |
| Esecuzione Teatri | Nessuna DRAFT/ACTIVE/run creati | Dopo mapping/review/compatibilità, un run governato e correlazione asset/source/version/run/handoff/UDP; mostrare esito in ChatGPT |

## Vincoli conservati

Preservare Cinema8/8, Teatri, snapshot/report storici, Gatewaylive, candidati semanticifermati. PRdraft, nessun merge/deploy indiscriminato. Provideresterno è dipendenza condizionale quando serve al mapping, senza aggirare trust/compatibilità/start. Nuove evidenze del 7 ottobre: producer, readback indipendente e firme VPS PASS; non riproporre trasferimenti o verifiche concluse. Scansioni hanno validità nei propri scope/finestra, nessuna freshnessbypass. R-INSTALL, replayRAW, storageindipendente, seconda fonte sovrapposta e releaseacceptance restano aperti, senza trasformarli in nuovi prerequisiti indistinti per la prima prova. Nessuna nuova durata promessa.
