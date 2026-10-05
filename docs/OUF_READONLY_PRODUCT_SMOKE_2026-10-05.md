# Controllo prodotto in sola lettura — 5 ottobre2026

OsservazioneUTC `2026-10-05T20:05:29.027Z`, account selezionato `ouf-admin` tramite plugin OUF. Nessun cambio account, upload, profiling, ingestion, grant, configurazione o riavvio richiesto.

| Operazione | Risposta osservata | Stato |
|---|---|---|
| `urban.object.search`, tipo `https://api.ouf-lab.it/semantic/cinema`, pageSize2 | isError=true; Status503; Type/Title/Code/Detail/RetryAfter vuoti; connector error_code=INVALID_ARGUMENT | R-SMOKE ancora aperto: nessun oggetto/pagina positiva provato |
| `semantic.search`, q=Theatre, type=CLASS, limit3 | isError=false; lista `[]` | Ricerca valida nel perimetro richiesto; non censimento completo né definizione/closure ontologica |

Il codice INVALID_ARGUMENT del connector non dimostra la causa del503 o un errore del tipo canonico: il corpo effettivo riportato dal tool resta503 con Problem vuoto. Nessun correlation/backend id disponibile. Non ripetere con altre identità, non aggiungere grant né effettuare restart/ingestion per tentativi. La diagnosi di componente/upstream/owner receipt binding richiede evidenza target mirata; non è stata eseguita in questo controllo.

Cinema8/8ACKED storico e triggerDISABLED restano distinti da serving/search acceptance. Teatri/PENDING_HUMAN_REVIEW preservati. Il provider esterno non è stato richiesto e la verifica Grype delle immagini è un'attività separata. Receipt redatta: `docs/handoffs/receipts/OUF_READONLY_PRODUCT_SMOKE_2026-10-05.json`.
