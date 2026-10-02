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

Pin sorgente candidato Semantic: `527fe074a7f6fb9c2990aac2fc9a7a98b8e97e4f` (CI da verificare; nessun deploy).

### Verifica candidato Semantic — 2026-10-02

Commit sorgente `527fe074a7f6fb9c2990aac2fc9a7a98b8e97e4f`: job Java21/PostgreSQL17 PASS (nuovi test SemanticReadRuntimeTest inclusi nel verify), recovery-cycle-scripts PASS e i due workflow Authorization pairwise SUCCESS. [CI runtime](https://github.com/GioNob/ouf-semantic-registry/actions/runs/36972327013): container-smoke SUCCESS, workflow completo SUCCESS. Nessun rollout. Lettura live necessaria di running/image/revision dei cinque container MCP/Semantic/Onboarding/Ingestion/UDP prima del deploy MCP: usare docker inspect con template limitato; non esporre env, mount sources, token o log.


## Checkpoint consultazione MCP e baseline live — 2026-10-02

Questo checkpoint aggiorna l'inventario dei paragrafi precedenti. Readback operatore: tutti e cinque i container sono running=true.

| Container | Revisione live | Image digest |
| --- | --- | --- |
| ouf-mcp | 04e871601e393672a1d62759dfdee09e2e66dc6d | sha256:b25c282882a858e8192d69170bc769e3c79f43e04330fc19ccd538b56c41716c |
| ouf-semantic | 12dc4bcad788bfdf96e15af716c8fa39ea0d12ef | sha256:9e7ec63f1a69195bd2e0688de9d491d30fe50024220b7a9f79dd991fc2113a3b |
| ouf-onboarding | 6340d5bf120e09b47c32177656e2c377a4c03640 | sha256:ec6f2a962261a8433bfe103347afa2202837fcec90d210d9b5232711b854ee8a |
| ouf-ingestion | 163c167d09b8371ff7a62ce7068e9d485b6969b7 | sha256:b07a4a786ca48335feae887e18dc7c4c6cdd9bd0a3a255f83d18c7c1616eec48 |
| ouf-udp | 83249a897eb4add4289b5181b3299f48ea4c0f99 | sha256:5e048a859716d6674355e72238f03f899abd705a943ceadbdc5c8863d28f4e9f |

Il sorgente MCP alla revisione live contiene sia managed upload/picker sia Search. Il candidato deriva da questa revisione e preserva le voci precedenti del manifest. Il confronto Semantic con il sorgente live conferma che SDK, pom e migrations non sono modificati dall'incremento.

| Repository / branch candidato | Commit sorgente |
| --- | --- |
| ouf-mcp-server / codex/file-to-udp-semantic-mcp | 8476a689fc6e59055001f59fc79a024bd14aca4a |
| ouf-api-gateway / codex/file-to-udp-semantic-mediation | e8ef4b72093f4138d0efe78e9947ddfc4b471e27 |
| ouf-semantic-registry / codex/file-to-udp-semantic-delegation | 8985d0d7f772dc7a7fd3deb3d5a569b1406d5d6c |

MCP espone semantic.search e semantic.get con input chiusi. Gateway verifica OIDC workload e delega HUMAN/tenant tramite ricevuta purpose/body/path/capability-bound di massimo 30 secondi. Semantic verifica la ricevuta e rivaluta la policy owner corrente con lo stesso SDK/resource type delle letture esistenti. Search consente soltanto ACTIVE; get richiede semanticId/revisionId/publicationSetId exact. Nessuna authority di approvazione, adozione o pubblicazione passa al chatbot.

CI MCP SUCCESS ([conformance](https://github.com/GioNob/ouf-mcp-server/actions/runs/36974180113), [evidence](https://github.com/GioNob/ouf-mcp-server/actions/runs/36974180119)). CI Gateway SUCCESS ([run](https://github.com/GioNob/ouf-api-gateway/actions/runs/36974491284)); suite locale completa 341 PASS / 4 SKIP. Il test cross-repository esegue il Lua Gateway reale e verifica la ricevuta nel Java owner; non equivale alla prova live di APISIX/OIDC/JWKS/TLS. CI Semantic sul pin sopra: tutti e quattro i workflow SUCCESS: [Java/PostgreSQL/container](https://github.com/GioNob/ouf-semantic-registry/actions/runs/36975096810), [Lua Gateway→Java owner](https://github.com/GioNob/ouf-semantic-registry/actions/runs/36975096768), Authorization Semantic e Shared Authorization SDK pairwise.

### Installazione: passo disponibile e limiti concreti

Script read-only scripts/r4a_consultation_runtime_preflight.py e due test PASS: controlla revisioni esatte/stato/privileged di Semantic e MCP e restituisce solo nomi delle variabili, destinazioni dei mount, nomi reti e metadati. Non restituisce valori env, mount host source o comandi container. Usare nomi container e revisioni espliciti; drift blocca senza mutazioni.

Configurazione nuova owner: ouf.semantic.delegation.key-file, ouf.semantic.delegation.workload e binding esistenti ouf.iam.issuer/audience. Chiave dedicata di 64 caratteri hex come bytes ASCII, distinta dalla chiave delegazione; soltanto Gateway e secret-file owner. Assenza chiave nega queste letture; configurazione incompleta/invalida blocca startup. Nessun segreto in MCP o chatbot.

Il materializer Gateway aggiunge soltanto le due route a un runtime già materializzato, con route IDs/upstream/issuer/audience/workload/key env names espliciti. Non è ancora un installer live plan/apply: prima del rollout completare readback scopes/catalog/policy/routes, snapshot privato, riconciliazione parametrica idempotente, key mount e rollback coordinato owner/MCP. Non sostituire l'intero runtime Gateway con una baseline sorgente presunta. Poi verificare discovery tool, letture positive/denial/exact storico e regressione picker/Search esistenti.

Nessun deploy, nuova source, upload, profiling, DRAFT, approvazione, run ingestion, retry UDP o materializzazione è stato eseguito in questo checkpoint. Cinema e Teatri rimangono invariati. Tutti i gate ereditati restano OPEN nei rispettivi ambiti. Il percorso intero non è ancora accettato: dopo la consultazione occorrono mapping/review/activation THS, trigger file una tantum, scheduler verticale, esiti UDP/Search e secondo chatbot. Deduplication autoritativa rimane in UDP.
