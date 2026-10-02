# OUF — acquisizione → onboarding → ingestion → UDP

## Obiettivo e decisione utente del 2 ottobre 2026

Completare il percorso di prodotto tramite MCP per chatbot compatibili, mantenendo le decisioni autoritative nelle THS e le API channel-neutral. Riusare backend e prove esistenti; nessun nuovo motore AI in Onboarding. PET v1.7 obbligatori, baseline e gate ereditati nell'handoff.

| Ingresso | Interazioni iniziali | Attivazione acquisizione |
| --- | --- | --- |
| File gestito | THS scelta file → staging → profiling | Dopo onboarding/review/approvazione e bundle ACTIVE compatibile, avvio automatico una tantum, senza attendere uno scheduler periodico. Riutilizzare trigger governato e idempotenza già presenti. |
| Verticale API | THS endpoint e credenziali → THS scelta profilo di estrazione → discovery/schema governati | Configurazione scheduler nel percorso Onboarding e pubblicazione dei parametri nel bundle. Ingestion Runtime esegue alle scadenze pubblicate; Onboarding non fa polling. |

Dal profilo/schema in poi: chatbot consulta il Registry, valuta eventuali gap/discovery, propone mapping/trasformazioni/identità/classificazioni; Onboarding valida/persiste; decisioni autoritative tramite owner/THS; bundle ACTIVE → Ingestion/RAW/lineage/handoff → UDP resolution → materializzazione → Search autorizzato. La verifica autoritativa dei doppioni avviene in UDP dopo l'handoff, sia per file sia per run schedulati. Non spostarla nel profiler o nel mapping semantico.

Credenziali soltanto in THS e secret manager: MCP riceve riferimenti opachi/stati redatti. Endpoint, protocollo, route binding, trust TLS, identity, timezone, cadence, misfire, timeout e retry restano configurazione d'installazione/source governata. Nessuna dipendenza da un chatbot specifico; il secondo host rimane un gate da provare.

## Incremento Semantic preparato

Branch candidato `codex/file-to-udp-semantic-read`, base `b50f3d88ef17f4d2013e17e6441f4380a0e9d29b`.

- `/search`: label/alias/descrizione/definizione e ID/localName, ranking deterministico e filtri opzionali type/namespace/domain/range. ACTIVE usa il pointer della revisione corrente e richiede membership in un set PUBLISHED. Restituisce JSON nativo e pin revision/set/checksum.
- `/references:resolve`: riusa l'endpoint esistente, verifica tripla exact semanticId/revisionId/publicationSetId e set PUBLISHED, espone label/description/definition, ownership/origin kind e dipendenze bounded. Nessun fallback latest/ACTIVE. Le revisioni storiche rimangono leggibili anche dopo switch/deprecation/retirement.
- Mantiene le capability owner `ouf.semantic.search`/`ouf.semantic.read` e il guard aggiuntivo delle letture non-ACTIVE. La lettura latest editoriale `/artifacts/{id}` rimane separata e non è il binding di `semantic.get`.
- Input hard maxima: q 256 caratteri, 1–100 risultati, namespace 512, semantic refs/domain/range 2048; massimo 100 dipendenze con flag `dependencies_partial`. Byte cap configurabile `ouf.semantic.read.max-result-bytes`, default 262144, min 1024, max 1048576; config invalida blocca startup. Overflow fallisce esplicitamente e non restituisce mapping incompleto silenziosamente.
- Nessuna migration o mutazione dello storico. Contratti frozen invariati: la presente estensione HTTP non equivale alla certificazione di tutti i DTO PET.

Test nuovi Java/PostgreSQL/HTTP: label e alias diversi da ID, filtro type/domain/range, pin pubblicato, switch ACTIVE con lettura vecchia invariata, triple mismatches, limiti/overflow, denial anonimo e non-ACTIVE senza grant aggiuntivo. Esecuzione tramite CI Java21/PostgreSQL17: nel workspace mancano Maven/Java21/PostgreSQL. Non dichiarare questi test PASS prima del risultato sul commit esatto.

## Prossimi collegamenti

1. Readback minimo live di revisioni/immagini MCP e owner. Nessuna equivalenza presunta fra main, branch candidato e live; preservare managed upload e Search.
2. Proiezioni MCP `semantic.search` e `semantic.get` tipizzate, con i binding owner sopra; install/reconcile route/scopes/catalog/policy parametrico e idempotente. Il candidato Semantic non è ancora deployed.
3. Discovery Ontopia on demand via provider/Gateway configurabili e adozione THS quando serve; niente SPARQL arbitrario dal client o adozione implicita.
4. Mapping dello stesso asset Teatri e review/activation THS con stato owner persistito per ripresa. Non ri-uploadare/ri-profilare o scegliere nome come chiave canonica senza decisione.
5. Collegare automatico una tantum file e percorso scheduler verticale; esito incerto richiede readback, mai nuova run/replay cieco. Collegare status/incident/review UDP e serving finale.
6. Collaudo nuovo percorso, denial/stale/resume/duplicazioni, secondo chatbot, file formati previsti e profilo API rappresentativo. Handoff/roadmap/manuale deploy aggiornati a ogni checkpoint.

Nessun gate ereditato chiuso per omissione: R-SMOKE, seconda fonte sovrapposta, storage/hash/replay, portabilità/R-INSTALL, TLS/reti, performance e awareness restano OPEN negli ambiti già tracciati.
