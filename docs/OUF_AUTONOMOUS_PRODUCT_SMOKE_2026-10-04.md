# Prova prodotto autonoma — 4 ottobre2026

Due sole letture dirette via connettore OUF corrente, account HUMAN `ouf-admin` coerente col precedente percorso e presente nel routing attuale. Nessun token, raw profile, log protetto o credential letto/stampato; nessun cambio account per superare un diniego. [Receipt redatta](handoffs/receipts/OUF_AUTONOMOUS_PRODUCT_READ_SMOKE_2026-10-04.json).

| Operazione | Risultato effettivo | Cosa resta aperto |
| --- | --- | --- |
| urban.object.search, type=https://api.ouf-lab.it/semantic/cinema, pageSize2 | isError=true, HTTP503; Type/Title/Code/Detail vuoti, nessun backend/correlation id nel risultato | Ricerca positiva, due pagine, almeno3 oggetti distinti, minimizzazione, invalid cursor/partial/label/authority/audit |
| semantic.search, q=Theatre,type=CLASS,limit3 | risposta valida `[]` | Non è censimento completo del Registry, definizione della classe Teatro o prova di ontology closure; non adottare MovieTheater per analogia |

**R-SMOKE NON chiuso.** Non ripetuta ingestion Cinema, upload/profiling Teatri o test manuale8/8; nessuna nuova DRAFT/ACTIVE/source/run/UDP mutation. Otto oggetti Cinema e relativo run storico86809c17-3354-45ca-a7e6-57e903944b24 restano evidenza separata. Il provider esterno non è stato avviato/chiamato per questo smoke.

## Diagnosi source-only del503

MCP `394b4b1540b575564f0ba58541df9d7efc59fb87`, `internal/adapter/httpclient/clients.go`: urban.object.search ha dispatch dedicato; non2xx viene decodificato in Problem, senza garantire che un corpo non-Problem riempia i campi. Uno Status503 con altri campi vuoti non identifica il componente responsabile.

Gateway source `ff51ac967feb8ccd0d00924ee76eb20a613fb863`, `tools/lua/execute_object_search.lua`:503 possibile quando manca/è invalida la chiave per firma delega o la chiave owner search, oppure la firma HMAC non riesce. Questi sono rami del codice, **non cause target dimostrate**. La route target è storicamente c14d3f23-derived; non nuova lettura dei bytes live.

UDP source target storico `83249a897eb4add4289b5181b3299f48ea4c0f99`, `ObjectSearchReceiptFilter.java`:503 UDP_SEARCH_IDENTITY_UNAVAILABLE per binding tenant/issuer/audience/workload/key-file mancanti o chiave owner non leggibile/formato diverso da64hex. Receipt/policy non valida invece403. `ServingApi` rifiuta input/cursor non valido con400. Questo restringe i controlli utili, ma un upstream indisponibile può anch'esso produrre503: non attribuire il problema a key/env, policy o URI senza correlazione backend.

La correzione non può essere un grant aggiunto, cambio account, restart/replay Cinema o fallback di sicurezza. Prima di qualsiasi modifica, acquisire nell'unico scope target pertinente e concordato: binding effettivo route/upstream, quale componente ha emesso503, presenza dei nomi dei5 binding search e accessibilità metadata del file owner come UID UDP, preservazione delle chiavi/mount e alias durante i rollout. Stampare soltanto esiti/count/hash/status/correlation; non Env values, secret bytes o raw logs. Non preparato un nuovo wrapper di inventory generale né eseguita questa diagnosi sul VPS.

## Ripresa del ciclo live

1. Riutilizzare upload/profile/proposta Teatri già conservati; non rifarli. Ricerca interna class/property/vocab e exact refs sufficienti; se gap, Discovery esterna governata, candidate temporanei→DRAFT→review HUMAN/THS→ACTIVE. Nessun default classe/chiave/vocab dal nome del file o da13righe.
2. Completare mapping source-specific compatibile e decisione THS; la proposta Teatri attuale resta PENDING_HUMAN_REVIEW. CAP, CRS/geometria, temporalità, provenance per-field e granularity devono avere scelte esplicite. Chiave source distinta da identity canonica UDP.
3. Solo dopo ACTIVE/compatibilità, file manuale→ingestion one-time immediata; registrare RAW/ACK/handoff e UDP materializzazione/review senza transazioni DB aperte in attesa HUMAN.
4. Sbloccare Search col punto di failure effettivo; stessa identità HUMAN autorizzata, pageSize2, almeno3 oggetti in due pagine senza duplicati, proprietà minimizzate/authority/labels/audit; invalid cursor e partial restano casi separati. Successo del solo lookup semantico o del job ingestion non equivale a serving acceptance.

PET riletti/riferimenti: Semantic9.2/10–11/159.2, Onboarding92–92.3 e109, UDP21–22/109, Authorization36.10; confini già riportati nell'handoff. Ricerca interna indipendente dal provider. R-INSTALL, full acceptance/runtime/start esterno, Lake/replay/portabilità/reboot rimangono aperti.
