# Discovery nazionale Teatri: prossimo passo

## Risultati già conclusi

Cinema ha restituito 8/8 oggetti in ChatGPT. Il file Teatri è già profilato: 13 righe e 20 campi. L'utente ha scelto la Discovery nazionale; la proposta di modello locale resta non selezionata.

Il 7 ottobre alle 13:55:40 Europe/Rome l'operatore ha riportato PASS della verifica fresca sul VPS: archivio, verifier, pin database e cinque firme. Report: `/home/oufadmin/ouf-extended-fresh-v2.Bs2U5B/reports`. Producer37613612404 e readback37614224542 PASS, quest'ultimo con38 test. Le immagini non sono cambiate; nessuna operazione runtime è stata eseguita. Il DB del7 ottobre resta fresco fino al9 ottobre08:31:48 Europe/Rome.

## Perché serve una lettura della configurazione

Il precedente output descriveva solo le variabili Docker: provider e worker non dichiarati o invalidi. La sorgente esaminata usa provider=false e worker=true come default, ma non era provato che il JAR in esecuzione contenesse quei default né che file/opzioni aggiuntivi li sovrascrivessero. Il vecchio preflight richiede pin e snapshot storici; non va rieseguito con assunzioni sul runtime attuale.

Il nuovo reader `scripts/r4a_read_semantic_national_discovery_configuration.py` legge il JAR del container già avviato `ouf-semantic`, verifica il solo application.yml contro il testo pubblico esaminato e rileva altri file, mount, opzioni o variabili di configurazione. Se la prova è ambigua restituisce UNPROVEN. Non esegue il JAR, chiama provider, crea job, legge file chiavi o modifica servizi. La copia privata temporanea del JAR viene rimossa. Le variabili vengono trattate in memoria; i valori e gli endpoint non sono stampati.

Cinque test locali PASS: default, config differente, override Spring anche minuscoli, mount/opzioni aggiuntivi, endpoint con credenziali e redazione. Hash reader: `0faa9f9b3fe7bdce893113a0c5164fbbdcd567bd9e14babfcf09a6e7effe53b4`. Verifica target non eseguita; CI dedicata da leggere dopo il push.

## Roadmap restante

1. Dall'esito della lettura, correggere la configurazione effettiva del provider nazionale e il raccordo Gateway. L'avvio dei candidati resta subordinato ai controlli concreti di publisher/copertura, dossier, authority, runtime e trasporto già tracciati; nessuna nuova authority è dedotta dalle firme.
2. Collegare richiesta e lettura candidati Discovery nel MCP con input chiusi, endpoint owner reale /api/semantic/v1/discovery-requests, idempotenza e receipt autorizzata. La versione corrente espone semantic.search/get, non discovery.request. Il chatbot non invia SPARQL o endpoint arbitrari.
3. Richiedere CLASS, intent teatro, lingue it/en; confrontare candidati e governare adozione/pubblicazione tramite HUMAN/THS. Completare decisioni sui20 campi e contratti Onboarding, DRAFT/THS/compatibilità/ACTIVE, un solo run Teatri, materializzazione e lettura ChatGPT.

Una riga rappresenta un teatro; capienza riferita a una sala va qualificata separatamente. Non rifare upload/profile o ingestion Cinema. Conservare candidati fermi, gateway e tutte le prove esistenti. Publisher trust, copertura completa, acceptance, registrazione runtime e avvio non sono concessi dalla verifica delle firme.
