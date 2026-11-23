# Worker discovery al cutover A2

## Inventario prima dell'avvio di Java

Dopo la sospensione dei nuovi ingressi e la riconciliazione delle richieste in transito, eseguire la [query SQL di inventario](discovery-queue.sql) con una sessione PostgreSQL autorizzata in sola lettura. La SELECT restituisce una riga per richiesta, comprese quelle terminali e quelle in pausa. Conservare l'inventario nel perimetro operativo privato.

La tabella `ouf_sem.discovery_request` contiene l'ambito proprietario in `created_by_subject`. Per l'ingresso MCP è un identificatore derivato da issuer, tenant e subject verificati. Per l'API nativa è il subject. Le migrazioni V3, V11 e V12 non persistono un tenant separato. Per un inventario per tenant, correlare ciascun request ID con evidenza autorizzata del tenant all'ingresso. Conservare le righe prive di riscontro come **tenant non determinato**. Se il piano richiede di trattenerne una potenzialmente eseguibile, mantenere chiuso il cancello fino alla decisione umana sulla coda.

Leggere insieme `state` e `recovery_state`. Un job PENDING può essere in attesa o avere esaurito il budget. Un job RUNNING può tornare acquisibile alla scadenza del lease. La SELECT mostra tentativi, generazione, lease, prossimo tentativo e intervallo del budget della richiesta. L'ammissione effettiva verifica anche lo stato della dipendenza per ambito e provider. L'inventario fotografa la coda al momento della lettura.

## Configurazione del successore

Confronto con la baseline descritta nei report 04 §3 e 17. I valori operativi e i mount effettivi vanno confrontati privatamente con il profilo autorizzato prima del segnale di avvio. I default del modulo sono in [application.yml](../../src/main/resources/application.yml).

| Funzione | Baseline documentata e configurazione del successore |
|---|---|
| Avvio | Cambiare `OUF_DISCOVERY_WORKER_ENABLED` da `false` a `true` nella configurazione di creazione. Spring valuta la condizione all'avvio. |
| Poll | Conservare `OUF_DISCOVERY_WORKER_DELAY` (default 2 s dopo il termine del poll). Verificare che `ouf.semantic.discovery-worker.batch-size` valga 8 o usi il default 8 del costruttore. Il limite è configurabile fino a 32. L'esclusione dei poll concorrenti vale per istanza di worker. |
| Persistenza | Riutilizzare `OUF_SEM_DB_URL`, `OUF_SEM_DB_USER`, `OUF_SEM_DB_PASSWORD` e il relativo meccanismo di iniezione. Il successore deve accedere allo stesso PostgreSQL con schema Flyway `ouf_sem` fino a V12. |
| Provider | Conservare `OUF_SCHEMA_GOV_ENABLED=true`, `OUF_SCHEMA_GOV_GATEWAY_BASE_URL` HTTPS e le route approvate `OUF_SCHEMA_GOV_SEARCH_PATH` e `OUF_SCHEMA_GOV_FETCH_PATH`. I default delle route sono `/semantic-providers/schema-gov/sparql` e `/semantic-providers/schema-gov/fetch`. |
| Namespace del provider (D-065) | `ouf.semantic.providers.schema-gov.namespace-prefixes` deve coincidere con `provider.namespace_prefixes` del southbound. Il profilo di installazione fornisce la stessa lista a entrambi. Default di sviluppo `["https://w3id.org/italia/onto/"]`. Spring accetta una lista YAML oppure `OUF_SCHEMA_GOV_NAMESPACE_PREFIXES` con valori separati da virgole. Per prefissi che contengono virgole usare la lista YAML. |
| OAuth workload | Conservare `OUF_SCHEMA_GOV_GATEWAY_AUTH_ENABLED=true`, `OUF_SCHEMA_GOV_TOKEN_ENDPOINT` HTTPS, `OUF_SCHEMA_GOV_CLIENT_ID`, `OUF_SCHEMA_GOV_WORKLOAD_SCOPE` e `OUF_SCHEMA_GOV_CLIENT_SECRET_FILE`. Quest'ultima variabile contiene il percorso nel container del file credenziale. Il profilo nativo usa un mount in sola lettura con proprietario root, gruppo 10001 e modo 0440. |
| Token e TLS | Conservare gli eventuali override `OUF_SCHEMA_GOV_TOKEN_TIMEOUT`, `OUF_SCHEMA_GOV_TOKEN_REFRESH_SKEW` e `OUF_SCHEMA_GOV_TOKEN_MAX_BYTES` (default 5 s, 10 s e 32768 byte). Riutilizzare il truststore Java montato in sola lettura, la sua configurazione JVM, i nomi TLS e i binding di rete per issuer e Gateway. |
| Ingresso MCP | Per creare la richiesta di prova e rileggerla, preservare la configurazione IAM e di delega già autorizzata, incluso il file di chiave indicato da `ouf.semantic.discovery-delegation.key-file`. Questi binding servono all'ingresso. Il fetch usa la credenziale workload della riga OAuth. |

Il solo delta applicativo previsto è il flag worker, a condizione che i prerequisiti del provider corrispondano al profilo. Il cambio ENV modifica l'impronta della configurazione e richiede la nuova autorizzazione operativa del profilo successore descritta nel report 17. La qualifica di repository usa risposte Gateway sintetiche. La prova sul successore deve rileggere stato SUCCEEDED, URI nel namespace approvato e provider `SCHEMA_GOV_IT` per lo stesso request ID.

## Esiti della discovery

All'avvio Semantic richiede da 1 a 32 prefissi IRI assoluti distinti, lunghi al massimo 2.048 caratteri e terminanti con `/` o `#`. Un URI deve iniziare con uno dei prefissi e avere almeno un carattere aggiuntivo. Il confronto è letterale e distingue maiuscole e minuscole.

Dopo la search, il worker esamina gli URI distinti in ordine di ranking. I soli GET obbligatori inviati consumano il limite dei tentativi, pari a tre volte `max-candidates`. Una descrizione valida occupa un posto candidato. Lo stato espone i conteggi del tentativo pubblicato in `excludedCandidates`.

| Codice | Quando aumenta |
|---|---|
| `CANDIDATE_NAMESPACE_EXCLUDED` | Semantic salta il GET di una descrizione o di una provenienza fuori namespace. Le righe duplicate della search contano una volta. Un link di provenienza condiviso conta una volta per tentativo. Le richieste storiche espongono zero. |
| `CANDIDATE_FETCH_DENIED` | Il GET della descrizione riceve 400, 404, 406, 409, 410, 414, 422 o 451. Per esempio, il Gateway rifiuta il namespace oppure la risorsa è assente. |
| `CANDIDATE_RDF_INVALID` | Il parser rifiuta il contenuto RDF ricevuto. |
| `CANDIDATE_RDF_BOUND` | Il parser riceve un contenuto vuoto o oltre il proprio limite di dimensione. |

Il worker prosegue con gli altri URI. Un 4xx sul GET facoltativo di un’ontologia collegata da `rdfs:isDefinedBy` può lasciare `ONTOLOGY_PROVENANCE_UNAVAILABLE` sul candidato. La richiesta può terminare `SUCCEEDED` con `candidateCount` pari a zero.

Un 429 sulla search o sul GET obbligatorio produce `SEM_DISCOVERY_RATE_LIMITED`, con origine non attestata. Durante `RETRY_WAIT`, `nextAttemptAt` rispetta il massimo tra il backoff con jitter e il `Retry-After` valido, in secondi o come data HTTP. Un header malformato conserva il blocco del recupero automatico. Un 429 sulla sola provenienza facoltativa lascia un gap sul candidato. I 5xx e i timeout su operazioni obbligatorie espongono `SEM_DISCOVERY_PROVIDER_FAILED`.

Gli errori della ricerca e i guasti del canale durante i fetch obbligatori seguono la politica di recupero del provider, inclusi 401/403, errori del token, 408/429, 5xx, timeout, limiti di trasporto e risposte malformate. Per un incidente `OPEN` con codice `PROVIDER_HTTP_400` aperto dalla 1.0.2, la 1.0.3 è eleggibile al sondaggio V15. Un tentativo ammesso e concluso con successo risolve l’incidente e riporta la dipendenza a `HEALTHY`. La migrazione V18 aggiunge il contatore inizializzato a zero e conserva la funzione di pubblicazione usata dalla 1.0.2.
