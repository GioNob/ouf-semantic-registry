> Aggiornamento 7 ottobre: profilo Teatri riletto/PASS dopo autorizzazione; proposta mapping completa dei 20 campi pronta. Diagnosi read-only UDP503 preparata e 4 test locali PASS, esecuzione VPS pendente. Nessuna DRAFT/ACTIVE/run o mutazione target.

# OUF: percorso da ChatGPT a UDP — stato operativo 7 ottobre 2026

## Risultato richiesto
Da ChatGPT: selezionare un file → profilazione → mapping semantico assistito dal chatbot → DRAFT Onboarding → decisioni HUMAN previste → configurazione ACTIVE → Ingestion/RAW/handoff → risoluzione identità e materializzazione UDP → lettura autorizzata del risultato in ChatGPT. Controlli di autorizzazione, riferimenti semantici, classificazioni, compatibilità, duplicati, lineage e audit restano nel percorso.

La prova termina quando lo stesso asset è correlato a fonte/versione, run, handoff e oggetti UDP, con risultato leggibile tramite ChatGPT. Una build, una firma o un report non chiude questa prova. Il matching autoritativo UDP avviene dopo l'handoff; un preflight non lo sostituisce.

## Prove riutilizzabili e verifiche di questa ripresa

| Passaggio | Evidenza | Residuo |
| --- | --- | --- |
| Upload e profile | Teatri già caricato: asset 6609b245-86ed-4315-8ce0-73f2a8555bf3; profile 7984c39c-7396-4248-ab0a-f2efc390b49c; 13 righe, 20 colonne, output operatore storico | Nessun nuovo upload/profile richiesto. Rilettura autorizzata dall'utente ed eseguita/PASS il 7 ottobre; nessun nuovo upload/profile. |
| Consultazione semantica interna | semantic.get Cinema eseguito ora via account ouf-admin: revisione 51706bed-81e4-4306-aca1-70119821727d, publication set f92a2e17-30c9-456f-bb12-63afa84f41e6, ACTIVE, RDF 17 statement, partial=false | Ricerca CLASS Theatre e Teatro entrambe []: non prova assenza globale. Nessuna classe Teatro scelta per analogia con Cinema. |
| Mapping Teatri | Proposta storica PENDING_HUMAN_REVIEW | Classe/proprietà/vocabolari e pin, access label, chiave source, CRS, temporalità e provenienza da completare; nessuna DRAFT/ACTIVE Teatri provata. |
| Review e attivazione | OnboardingService al commit 6340d5bf120e09b47c32177656e2c377a4c03640 implementa freeze, challenge, conferma HUMAN, compatibilità Ingestion e gate identità UDP prima di ACTIVE | Tool corrente source.onboarding.create produce solo DRAFT. Collegamento conversazionale a review THS e ripresa da stato owner non provato; non inventare tool approvazione MCP. |
| Ingestion → UDP | Cinema storico: run 86809c17-3354-45ca-a7e6-57e903944b24 SUCCEEDED, 8 handoff ACKED, 8 oggetti materializzati | Lettura attuale ouf.ingestion.status per managed-cinema-8ec8ae90: authorization denied. Non significa run fallito. |
| Serving in ChatGPT | urban.object.search eseguito ora per https://api.ouf-lab.it/semantic/cinema, pageSize 2 | HTTP503 senza codice/correlazione utile; componente responsabile non provato. Nessun replay necessario per diagnosticare la lettura. |
| Semantica esterna | Software/provider e nuove immagini sviluppati e verificati nei propri scope | Target provider non avviato. Discovery/adoption richiede questo ramo quando il mapping non è soddisfatto dai riferimenti interni. Non bloccare con questo ramo diagnosi e completamento delle parti indipendenti. |

Verifiche correnti eseguite 2026-10-07T05:16:58.727Z, account ouf-admin selezionato dalle indicazioni attuali del connector. Nessun cambio account dopo diniego.

## Ordine di lavoro e criterio di completamento

1. **Rendere leggibili i risultati già prodotti.** Diagnosticare il 503 UDP e il diniego ingestion.operations.read usando route/owner/SDK e binding attuali. Preparare una sola diagnosi VPS mirata se serve una lettura effettiva del server. Nessun grant indiscriminato, cambio account, rigenerazione chiavi o restart ipotetico. Completamento: ChatGPT legge run Cinema e almeno due pagine UDP autorizzate senza duplicati, con minimizzazione e gestione cursor.
2. **Preparare il mapping Teatri già caricato.** Profilo riletto con autorizzazione specifica; [proposta completa dei 20 campi](TEATRI_MAPPING_REVIEW_CURRENT.md) preparata, non approvata; consultare il Registry interno e leggere i riferimenti esatti. Se manca semantica adeguata, concretizzare la discovery/adoption governata; provider resta una dipendenza condizionale, senza false scorciatoie. Presentare proposta completa e dubbi al HUMAN. Completamento: mapping source-specific valido e revision/publication pin documentati, decisioni ancora non falsamente approvate.
3. **Collegare DRAFT, THS e ripresa.** Riutilizzare API esistenti e test precedenti. Esaminare il collegamento mancante prima di implementare doppioni; preparare card/link fidato e lettura stato necessaria, mantenendo decisioni autoritative nel THS. Attestazione reale Ingestion e gate identità UDP sullo stesso hash congelato. Completamento: approvazione HUMAN e ACTIVE validi per la sola fonte selezionata.
4. **Eseguire e mostrare il giro completo.** Una sola ingestion governata per Teatri, correlazione asset/source/version/run/handoff/UDP, dubbi duplicati o merge al THS quando previsti. Completamento: oggetti risultanti leggibili in ChatGPT, lineage/audit e controlli pertinenti documentati; nessun successo dichiarato dai soli conteggi CI.

Nessuna durata promessa prima della diagnosi dei blocchi. Stato attuale: prova completa NON consegnata.

## Limiti e attività conservate
Il nuovo ZIP di evidenze è pendente e il percorso Windows precedente non esisteva. Il False stampato dopo Resolve-Path non è un mismatch SHA dimostrato. Trasferimento sospeso come azione immediata: non riproporlo automaticamente alla ripresa. Crypto PASS precedenti e nuovi risultati CI restano validi soltanto nei rispettivi scope; nessuna acceptance o start concessa.

Preservare Cinema 8/8, asset/profile Teatri, snapshot, vecchi report, gateway live e candidati fermati. PR restano draft, nessun merge/deploy. R-INSTALL, portabilità, RAW replay, storage indipendente, seconda fonte sovrapposta, prove security/negative e release acceptance restano aperti nei documenti storici; non sono cancellati e non diventano tutti prerequisiti nuovi della prima prova senza motivazione normativa concreta.

Il codice verificato ora non è automaticamente il codice deployed. Nessuna modifica a runtime, IAM, policy, DB o dati effettuata in questa ripresa. Questo documento sostituisce il NEXT centrato sul trasferimento del sidecar; lo storico rimane consultabile.
