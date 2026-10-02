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


## Checkpoint operatore e preparazione immagini — 2026-10-02 08:49 Europe/Rome

Preflight live ricevuto PASS: Semantic e MCP alle revisioni attese, entrambi su ouf-backend, senza porte pubblicate o privileged. Semantic user 10001:10001, mount bind read-only /run/ouf-semantic-auth; env IAM/Authorization presenti, nessuna configurazione della ricevuta semantica ancora presente. MCP user 10005:10005, mount read-only dei due secret-file client/fingerprint, managed upload e picker configurati; restart unless-stopped. Nessun healthcheck Docker configurato: il futuro switch richiede readiness applicativa esplicita, non sola verifica Running. Questi fatti non dimostrano la salute delle API o l'accesso autorizzato.

Script nuovo scripts/r4a_stage_semantic_consultation.py: configurazione JSON con stageRoot, due immagini (repository, commit exact, nome container, liveRevision), container/configDestination/adminOrigin Gateway. Nessun binding installazione implicito nello script. Crea una directory nuova privata 0700, legge le route APISIX via Admin loopback nel network namespace Gateway; chiave letta dal bind config, passata via stdin, mai argomento o output. Snapshot completo di inspect/config/routes soltanto in file privato 0600; output solo metadati route/plugin/scopes e nomi env. Checkout detached dei commit exact, build log privato e label OCI controllata; conserva immagini staged, senza creare/avviare candidati. Verifica live config/stato e route invariati alla fine. Non scrive a owner, IAM, Gateway o policy; nessuna nuova source/run. Directory già esistente blocca e richiede lettura dello stato, senza sovrascrivere snapshot o rilanciare build implicitamente.

Tre test locali PASS: percorso due immagini con snapshot/receipt privati e nessuna operazione live, drift pin bloccato prima della build, endpoint Admin remoto/pin simbolico rifiutati. Le build VPS restano da eseguire; Dockerfile Semantic/MCP produce immagini applicative, i test Java/Go sono quelli della CI già verde sui pin sorgente, non eseguiti di nuovo dalla build.

Parametri espliciti per questa installazione nel comando operatore: ouf-semantic, ouf-mcp, ouf-apisix; config APISIX /usr/local/apisix/conf/config.yaml, Admin http://127.0.0.1:9180; directory nuova sotto /etc/ouf/deploy-snapshots. Se config bind non corrisponde, lo script blocca senza switch e senza stampare segreti. L'output e lo snapshot preparano il successivo piano add-only per route, key binding, scopes/catalog/policy e switch con readiness/rollback. Non equivalgono a rilascio, nuova capability autorizzata o percorso file/API→UDP completato. Tutti i gate precedenti rimangono tracciati.


## Checkpoint immagini VPS e candidati fermi — 2026-10-02 08:58 Europe/Rome

Operatore: CONSULTATION_STAGE=PASS, LIVE_UNCHANGED=true, ROUTES_UNCHANGED=true, NO_SWITCH=true, NO_SOURCE_RUN=true. Directory privata /etc/ouf/deploy-snapshots/consultation-20261002-0850. Non ripetere le build:
- Semantic source 8985d0d7f772dc7a7fd3deb3d5a569b1406d5d6c → sha256:6a13b3fe2febad93d23e8c699f1139cfd616a29598b406f0a46a6534631a9555.
- MCP source 8476a689fc6e59055001f59fc79a024bd14aca4a → sha256:eb6169e33d6d50ba25ea100a11898dee26a0eb1f993ec8ce8ea33e32b8c40808.

Gateway readback: route mcp-generic-execution, managed-file create/handoff/preview/profile/upload, permissions e urban-object-search presenti; letture Semantic GET search e references:resolve già attive su ouf-semantic:8080 con i rispettivi scope. Le nuove route execute semantic/search|get sono assenti. Gateway possiede env per delegazione/Authorization/Search, non la chiave nuova OUF_SEMANTIC_READ_OWNER_KEY. Related-search risulta disabilitato nelle due route mostrate: stato ereditato, non attivato da questo sprint.

Nuovo preparatore scripts/r4a_prepare_semantic_consultation.py (dipendenza sibling r4a_stage_semantic_consultation.py): consuma snapshot/receipt dello staging già PASS, verifica live/image/routes freschi e concordanza issuer/audience/workload fra Lua execute e env Semantic/MCP. Checkout Gateway exact e8ef4b72093f4138d0efe78e9947ddfc4b471e27 e materializer già verificato generano soltanto due route private. Chiave casuale dedicata 32 bytes resa hex ASCII, semantic-owner.key UID/GID owner e mode0400, Gateway env privato0600; APISIX config nuovo conserva tutto tranne una nuova voce nginx_config.envs. Bind originali e file live non modificati.

Crea tre candidati con restart=no, mai start/stop/rename: ouf-semantic-consultation-candidate, ouf-mcp-consultation-candidate e ouf-apisix-consultation-candidate. Gateway riusa la stessa immagine live. Conserva launch contract, env precedenti, bind RO, resource limits e reti/alias dai dati reali; impostazioni non supportate bloccano prima dei create. Receipt salva intent prima di ogni create e ID verificati; directory prepared esistente blocca una ripetizione cieca. Candidato parziale/errore richiede readback degli intent/ID senza cancellare o riavviare i live.

Test locali cumulativi stage+prepare: 8 PASS; preflight 2 PASS. Nuovo workflow Consultation deploy scripts esegue questi test; esito CI sul commit da verificare prima di dichiararlo PASS. Questo preparatore non esegue switch, PUT route, grant/catalog/IAM/policy publication, approvazioni, attivazione source o run. Prossimo passo operatore: preparare tre candidati fermi dalla directory sopra; successivamente verificare receipt, predisporre backup/health/rollback e installer add-only con gestione esiti incerti prima del rilascio coordinato. Scope/catalog/policy Semantic correnti e HUMAN autorizzata rimangono da verificare. Non equiparare candidatura tecnica a filiera completa accettata; gate ereditati invariati.

### CI preparazione verificata — 2026-10-02

[Consultation deploy scripts](https://github.com/GioNob/ouf-semantic-registry/actions/runs/36977385047) SUCCESS sul commit 72ab11dee9b670c58cc04dd06c82e244dbb188df: otto test stage/prepare e due preflight eseguiti. Corretto il test di reentry per runner non-root; nessun cambiamento alle immagini applicative già staged. Comando operatore di preparazione deve usare i due helper pinned a questo commit; risultato VPS dei tre candidati ancora da acquisire. Non dichiara PASS il futuro switch o la filiera complessiva.


## Candidati VPS pronti e rilascio coordinato — 2026-10-02

Operatore CONSULTATION_PREPARE=PASS: tre candidati created/fermi, live/routes/policy invariati, nessuna nuova source/run. Receipt privata /etc/ouf/deploy-snapshots/consultation-20261002-0850/prepared/prepare-receipt.json.
- Semantic e32dd8c43b7b56bdff2c04ac4d9f34619fea2ab0be045f61d1a034beff8f1af6; immagine sha256:6a13b3fe2febad93d23e8c699f1139cfd616a29598b406f0a46a6534631a9555.
- MCP e3e4d3e5ec5efc6556ed9d0033c5433ffbc0424de2f41d7976080242689f79d6; immagine sha256:eb6169e33d6d50ba25ea100a11898dee26a0eb1f993ec8ce8ea33e32b8c40808.
- APISIX a076e563ab558277b1ee718c7aac0be26ac4ee8fc543fbd6582fa9cf30d642ed; stessa immagine live sha256:84e6b5e787e9f889ebff88161cb9a16599bafcffa236c6b54c7f779a0655940d.

Errore finale rm esclusivamente sul pycache root del download temporaneo /tmp/tmp.JP4RJSnZeW; preparazione PASS non invalidata. Per i successivi helper eseguire Python con -B, anche nei subprocess nsenter. Pulizia limitata a quella cartella temporanea creata dal comando precedente; snapshot/key/receipt restano nella directory privata persistente.

Nuovo scripts/r4a_release_semantic_consultation.py, dipendenze sibling stage e prepare: modalità plan/apply/verify, parametri espliciti stage-root/PostgreSQL container e origini loopback dei tre servizi. Plan rigenera le route dal sorgente Gateway pinned/clean, confronta artefatti e stato live/candidati/secret binding, controlla readiness preesistente e legge history migration. Apply ferma MCP/Semantic, crea dump privati completi dei due DB identificati dagli env e controlla pg_restore --list (TOC, non restore reale), attiva Semantic/Gateway, aggiunge soltanto due route, poi attiva MCP. Confronta migration history, env/mount/alias/resource config e readiness, nega richieste anonime e ricevute false. Non pubblica policy, non chiama approvazioni o nuove source/run, non pretende verifica HUMAN positiva.

Originali conservati con restart=no per rollback. Intent prima di switch/PUT; rename e risposte DELETE perse riconciliate con GET/readback. Recupero per container ID e cancellazione soltanto delle route nuove ancora esattamente possedute; nessun restore automatico dei DB, nessuna cancellazione dei container originali. Receipt esistente blocca apply; errore mantiene receipt e richiede readback invece di rilancio cieco. Test locali cumulativi stage/prepare/release 14 PASS, preflight 2 PASS; workflow deploy script deve essere verificato sul nuovo commit prima dell'esecuzione operatore. Tutti i gate ereditati invariati; rilascio effettivo, accesso HUMAN/scopes/catalog/policy e percorso completo restano da acquisire.

### Rilascio tecnico pronto: CI verificata — 2026-10-02 09:41 Europe/Rome

Commit helper 2b42cbcfecb92bfa8a484a5a72fa56863656bdc9: tutti i workflow associati SUCCESS, inclusi [Consultation deploy scripts](https://github.com/GioNob/ouf-semantic-registry/actions/runs/36979828930) con 14 test stage/prepare/release e 2 preflight, module CI, Authorization/SDK e Semantic Gateway live pairwise. Helper pinned e verifica CI completati; nessuno switch ancora effettuato. Comando successivo operatore: Python -B, modalità plan poi apply soltanto se plan PASS, parametri stage-root esistente/PostgreSQL ouf-postgres/origini loopback esplicite (Semantic/MCP8080, APISIX9080). Esito runtime richiesto prima di dichiarare il deploy PASS; futura verifica HUMAN/scopes/catalog/policy e mapping dello stesso asset Teatri rimangono il passo seguente. Tutti i gate ereditati restano invariati.


## Audit richiesto dall'utente: riuso delle correzioni e PR aperte — 2026-10-02

Verificate le 26 PR aperte nei tre repository coinvolti (5 Semantic, 13 MCP, 8 Gateway), con elenco file completo/paginato e manifest MCP dei 13 head. Nessuna di queste PR MCP espone semantic.search/semantic.get. Confronto sorgente exact MCP live 04e871601e393672a1d62759dfdee09e2e66dc6d → candidato 8476a689fc6e59055001f59fc79a024bd14aca4a: 16 capability precedenti identiche semanticamente, zero modificate/rimosse; totale18 con le sole nuove ouf.semantic.search e ouf.semantic.read. Non inferire feature deployed dal nome PR o da main.

Semantic live 12dc4bcad788bfdf96e15af716c8fa39ea0d12ef: search filtra similarity del solo semantic_id e restituisce ID/revisione/status/score. Il candidato 8985d0d7f772dc7a7fd3deb3d5a569b1406d5d6c aggiunge lettura label/descrizione/definition/pin e delegazione per consultazione MCP, riusando le letture owner esistenti. Diff produzione limitato ad ArtifactApi, ArtifactService, ValidationService e tre nuovi file SemanticReadService/SemanticReadDelegation/SemanticConsultationApi. SDK/vendor, pom, Dockerfile, migration, SemanticIamSecurityConfiguration e GovernanceService invariati rispetto al live. L'insieme di molti script/documenti nel compare Git non implica che entrino nell'immagine: il Dockerfile copia soltanto src/contracts/vendor/pom nel build.

Gateway candidato resta sulla stessa immagine live sha256:84e6b5e787e9f889ebff88161cb9a16599bafcffa236c6b54c7f779a0655940d. Preparazione modifica soltanto il bind config privato per nuova whitelist env/key e le due route add-only. Onboarding/Ingestion/UDP non vengono sostituiti dal rilascio consultazione. Gli originali conservati per rollback servono soltanto al recupero di un rilascio fallito; nessun rollback è una fase del percorso file→UDP né una ripetizione di test/source/run.

Riuso da trattare nel prossimo incremento: [MCP PR48 resolution.issue.read](https://github.com/GioNob/ouf-mcp-server/pull/48) e [Gateway PR55 pacchetto review/preflight identity](https://github.com/GioNob/ouf-api-gateway/pull/55) contengono lavoro precedente da verificare/integrarsi sulla baseline live. resolution.issue.read è nel manifest di PR48 ma assente nel manifest live04e8716. Non reimplementare il pacchetto review: riconciliare codice/ownership/route e prove già esistenti, mantenendo upload/Search del live; i branch delle PR hanno basi differenti. Gate branch/release reconciliation rimane OPEN, senza invalidare le evidenze funzionali precedenti.

Conclusione limitata a questo incremento: modifiche di consultazione e collegamento MCP necessarie, nessuna proiezione equivalente nelle PR aperte MCP esaminate. Regressioni automatiche e readiness/denial del nuovo collegamento non sostituiscono né richiedono di ripetere le centinaia di ore di prove manuali pregresse. Ultimo esito VPS confermato: candidati fermi PASS; esito release da acquisire. Nessun gate pregresso chiuso per omissione.

## Checkpoint 2026-10-02 — consultation release applicato PASS

Questo checkpoint aggiorna e supera l'ultimo stato «candidati fermi / esito release da acquisire», conservato sopra come cronologia. Output dell'operatore VPS: plan PASS; apply PASS; 3 container rilasciati; 2 nuove route; route preesistenti preservate; migration history invariata; nessuna pubblicazione policy; nessuna source/run avviata. Readiness e denial PASS; POSITIVE_HUMAN_NOT_PROVEN=true.

Pin applicativi rilasciati: Semantic 8985d0d7f772dc7a7fd3deb3d5a569b1406d5d6c, image sha256:6a13b3fe2febad93d23e8c699f1139cfd616a29598b406f0a46a6534631a9555; MCP 8476a689fc6e59055001f59fc79a024bd14aca4a, image sha256:eb6169e33d6d50ba25ea100a11898dee26a0eb1f993ec8ce8ea33e32b8c40808. Gateway mantiene la stessa immagine e applica le due route/addizioni config preparate; Onboarding/Ingestion/UDP invariati.

Backup Semantic e MCP PASS, TOC verificato e file privati: non equivale a una prova di restore. Receipt privato: /etc/ouf/deploy-snapshots/consultation-20261002-0850/prepared/release-receipt.json.
Originali conservati: ouf-apisix-consultation-rollback-dcfc7a47b09a; ouf-mcp-consultation-rollback-5e9c92958b0e; ouf-semantic-consultation-rollback-b13602a456da. La conservazione non indica un rollback eseguito: rilascio riuscito.

Readback autenticato MCP dell'account ouf-admin: ROLES e configured grants letti con successo. Policy ouf-lab-authorization:36; assegnazione nominale admin confermata dal registro, non dedotta dal nome del connector. Nella pagina completa dei grant nominali (nextAfter=null) sono presenti grant ouf.semantic.search, assenti grant ouf.semantic.read; anche il ruolo admin letto contiene search e non read. Queste sono configurazioni, NON prova di permessi effettivi o di deny completo (restano condizioni/scope ed eventuali altri percorsi di assegnazione da verificare). Il client della conversazione non espone ancora semantic.search / semantic.get; CAPABILITIES è respinto dallo schema MCP corrente. Non ripubblicare policy né sostituire altri software senza inventario mirato e proposta THS.

Prossimo gate: refresh discovery client e prova positiva HUMAN delle due letture, con verifica mirata di scope/catalogo/grant. Il PASS tecnico non chiude il percorso completo file/API→UDP né i gate pregressi, e non richiede di ripetere upload, profiling, approvazioni o ingestion già provati.

## Checkpoint 2026-10-02 10:20 Europe/Rome — IAM consultation inventory PASS

Dopo rinnovo interattivo della sessione kcadm scaduta, operatore conferma inventario READ_ONLY PASS, nessun segreto stampato. Scope ouf.semantic.search e ouf.semantic.read entrambi esistenti, OIDC e attributi conformi (drift=[]). Client abilitati: ouf-chatgpt entrambi MISSING; ouf-human-admin search OPTIONAL, read MISSING; ouf-mcp-server entrambi MISSING.

Verifica del contratto Gateway execute_semantic_read.lua: il workload è autenticato come SERVICE; il controllo di scope della capability avviene su p.scope della delega HUMAN firmata. Non aggiungere scope HUMAN a ouf-mcp-server per questo percorso.

Prossima azione proposta all'operatore: riusare r4a_keycloak_client_scope_catalogue.py e r4a_keycloak_client_scope_binding.py, entrambi pin Onboarding 6340d5bf120e09b47c32177656e2c377a4c03640. Un batch plan/apply/verify per tre binding esatti: ouf-chatgpt/ouf.semantic.search DEFAULT; ouf-chatgpt/ouf.semantic.read DEFAULT; ouf-human-admin/ouf.semantic.read OPTIONAL. Preflight verifica i due contratti esistenti e pianifica tutti i binding prima delle scritture. Preservare search OPTIONAL su ouf-human-admin e tutti gli altri binding. Nessuna modifica ai software o alla policy. Apply non ancora provato: attendere output operatore; nessun gate positivo chiuso.

Poi: inventario mirato del descriptor/grant ouf.semantic.read e proposta di modifica con conferma THS se necessaria; token HUMAN fresco/refresh discovery per chiamate positive semantic.search/get. Binding OAuth non equivale a grant applicativo né prova di accesso; configurazione role/nominal grants letta nella policy36 non contiene semantic.read. Non ripetere source/run/onboarding precedenti. Script generici già esistenti, non reimplementare.

## Checkpoint 2026-10-02 10:32 Europe/Rome — consultation HUMAN bindings applicati PASS

Output operatore: entrambi i contratti scope verify PASS, drift NONE; batch plan/apply/verify PASS per ouf-chatgpt search DEFAULT, ouf-chatgpt read DEFAULT, ouf-human-admin read OPTIONAL; verifica finale STATE=BOUND per tutti e tre. SEMANTIC_HUMAN_BINDINGS=PASS POLICY_UNCHANGED=true. Non modificato il workload MCP, nessun rilascio o nuova source/run.

Readback autenticato MCP successivo: policy36 invariata, pagina completa nextAfter=null; grant nominali/compilati search presenti, read assente. Nessuna proposta/publicazione eseguita. Non basta il binding OAuth per rendere una capability autorizzata.

Prossimo inventario operatore in sola lettura: riuso del preflight r4a_authorization_catalogue_preflight.py pin Onboarding6340d5bf120e09b47c32177656e2c377a4c03640. Adapter in memoria sostituisce il literal urban.object.search della sola query SQL con i due ID esatti ouf.semantic.search/read, uno alla volta; output etichettato con CAPABILITY_ID e CAPABILITY_REGISTERED/CAPABILITY_IN_ACTIVE_BUNDLE. Non modificare file software installati. Occorre sapere se read è registrata e/o pubblicata prima di scegliere il riuso del percorso di registrazione/policy o la sola proposta grant via MCP e THS. Conferma HUMAN e prova positiva restano pendenti; refresh OAuth/discovery ancora necessario. Conservati tutti i gate pregressi.

## Checkpoint 2026-10-02 10:35–10:37 Europe/Rome — catalogo PASS, proposta grant read PENDING

Operatore conferma entrambe le capability ouf.semantic.search/read registrate e nella policy attiva ouf-lab-authorization:36. Preflight READ_ONLY, NO_POLICY_CHANGED=true. Nessuna nuova registrazione necessaria. Readback grant via MCP: policy36, nextAfter=null, search presente; read assente nei grant nominali/compilati del soggetto admin letto.

Preparata tramite plugin OUF - MCP Server (account ouf-admin) una sola proposta UPSERT grant-semantic-read-human-admin, capability ouf.semantic.read, tenant ouf-lab, subject b93d8cf6-cd14-4ee6-91d7-84cd76c4f500; servicePrincipalId/organizationId null. Validità e struttura copiate dal grant-semantic-search-human-admin attivo (validFrom 2026-09-18T07:12:50.968730Z, validUntil 2036-09-15T07:13:50.968730Z), senza modifica del ruolo admin o degli altri grant. Conferma richiede controllo diretto HUMAN della card/delta in THS; proposta NON pubblicata.

Receipt e status riletti: proposalId 4b59b8ab-5063-442b-973f-e52b49768d3b, revision0, PENDING; finalPolicyRef null; scadenza 2026-10-02T08:51:28.041537Z (10:51:28 Europe/Rome).
THS: https://api.ouf-lab.it/trusted-human/authorization/?proposal=4b59b8ab-5063-442b-973f-e52b49768d3b

Prossimo passo: conferma/reiezione dell'operatore sulla THS autenticata, poi rilettura receipt e grant attivi (non presumere versione37), refresh token OAuth/discovery e prove positive semantic.search/get. Se scade o la policy cambia, rileggere la policy e preparare nuova proposta solo se ancora necessaria; non ripetere alla cieca. Non approvare via chatbot né inviare bearer HUMAN al modello. Nessuna source/run avviata, nessun gate E2E chiuso.

## Checkpoint 2026-10-02 10:38 Europe/Rome — grant read pubblicato, policy37 riletta

Operatore conferma pubblicazione sulla THS. Verifica indipendente tramite plugin OUF - MCP Server/account ouf-admin: proposal4b59b8ab-5063-442b-973f-e52b49768d3b revision1 state=PUBLISHED finalPolicyRef=ouf-lab-authorization:37. Read configured grants restituisce policy37, nextAfter=null, grant-semantic-read-human-admin presente con capability ouf.semantic.read, tenant ouf-lab e subject admin b93d8cf6-cd14-4ee6-91d7-84cd76c4f500; servicePrincipalId/organizationId null, validità invariata rispetto alla proposta. Stato PENDING precedente superato; non ripetere registrazione, proposta o pubblicazione.

Restano distinti configured grant e prova positiva di owner authorization. Il registry di tool disponibile nella conversazione non espone ancora semantic.search/get. Prossimo passo: rinnovo autenticazione della connessione OUF come ouf-admin per ottenere token OAuth con i due scope DEFAULT appena associati a ouf-chatgpt e aggiornare discovery, poi chiamate positive search e get con triple esatte ottenute dai risultati autorizzati. Se il client mantiene discovery in cache, diagnosticare il client/server prima di altri cambiamenti software. Nessun bearer umano va riportato in chat. In alternativa il probe MCP pubblico con HUMAN device flow deve riusare il client/protocollo già testato e non avviare source/run.

NESSUNA prova positiva semantica ancora acquisita; nessun gate E2E completo chiuso. Container e flow pregressi non ritestati.

## Checkpoint 2026-10-02 10:41 Europe/Rome — refresh client eseguito, probe pubblico predisposto

Operatore dichiara aggiornamento strumenti e riconnessione ouf-admin. Il registry esposto a questa conversazione continua a non contenere semantic.search/get; questa osservazione non prova che il server non li esponga. Non richiedere ulteriori refresh alla cieca.

Predisposto scripts/r4a_probe_semantic_human_mcp.py, parametrizzato issuer/MCP URL/client/subject/tenant/audience/query. Riusa senza modifiche il client standardlib scripts/r4a_admin_permission_proposal.py da MCP8476a689fc6e59055001f59fc79a024bd14aca4a (copiato come dipendenza auditabile). Adapter richiede solo openid,mcp.connect,ouf.semantic.search,ouf.semantic.read; controlla contesto HUMAN e scadenza localmente, token in memoria mai stampato. Un login Device Flow per tools/list, search limit1 e get sulla tripletta esatta ritornata dalla ricerca. Nessuna proposta, registrazione, pubblicazione o source/run. Output limitato a disponibilità tool, numero risultati e match dei riferimenti: non stampa payload semantici né JWT.

Tre test locali PASS: get usa la tripletta autorizzata; discovery mancante arresta il probe prima dei tools/call; tripletta alterata non passa. Workflow dedicato automatizza questi test. Prova LIVE ancora da eseguire: il PASS locale non è una prova positiva HUMAN. Query proposta Cinema sui dati già presenti; ricerca vuota è SEARCH PASS ma GET NON PROVATO, senza creare nuovi artefatti. Il probe distingue discovery server da tool registry del chatbot.

## Checkpoint 2026-10-02 10:49 Europe/Rome — discovery server PASS; ricerca rifiutata; correzione isolata predisposta

Output probe LIVE: SEMANTIC_HUMAN_TOKEN_CONTEXT=PASS; tools/list espone semantic.search=true, semantic.get=true; SEMANTIC_HUMAN_MCP=BLOCKED REASON=MCP_TOOL_DENIED alla search. Non attribuire più il blocco alla discovery server o chiedere altri refresh alla cieca. Prova positiva search/get NON acquisita. Rifiuto tool soppresso dal probe generico; l'esatto codice LIVE non è stato acquisito. Chiamata read-only operations.incidents successiva con account admin restituisce authorization denied; non usarla come prova dell'errore specifico semantic.search.

Audit del codice ESATTO MCP8476: manifest search OperationClass SEARCH, mentre il descriptor semantic.search registrato storicamente dal bootstrap è READ; cache Authorization MCP richiede match esatto capability+operation. Il kernel registra inoltre semantic.search/get tramite fallback relatedSearchInput UDP, perdendo gli argomenti semantici prima del dispatch. Sono difetti del nuovo collegamento, non motivi per ripetere source/run/onboarding; prior readiness/denial e test per-componenti non coprivano tools/call con policy READ e argomenti reali.

Correzioni sorgenti isolate, NON ancora live:
- MCP e64cb3938efb95c4f83cd9ca9cb0aa4874c7d215 (sostituisce bbfab0 test-only): decoder map governato per semantic.*, manifest search READ, read-only annotation; due nuovi test protocollo tools/call con policy descriptor READ, grant/scope, esatta conservazione dei sei filtri search e dei tre riferimenti get, deny senza dispatch in assenza di scope.
- Gateway 2cdeb194028a2e5ba8cac859bd8814665969deaf: solo search READ in Lua e schema, test aggiornato; nessuna nuova route/capability/policy. 12 test mirati locali PASS; CI Gateway completa success.
- Semantic 12133a8ef67ba538619799d8bab68e340a21952d: search envelope READ, test e pin Gateway pairwise allineati; checksum solo dei due file modificati aggiornati. Parent630 CI pairwise Lua→Java/SDK/Auth success, module inizialmente bloccato dalla verifica checksum; CI completa del pin12133 in attesa di readback. Non confondere quel fallimento checksum con una prova di Java non funzionante.

CI MCP: protocol/lifecycle verify.sh, Docker build, staticcheck completati success, workflow ancora in progress al checkpoint (govulncheck); conformance Java/Go success. Attendere esito finale prima di switch live; non chiamare ancora tutte le CI GREEN. Pipeline e gate E2E aperti.

Prossima azione operatore: riuso immutabile dello staging helper per build delle sole due immagini corrette e snapshot live attuale, in nuova root /etc/ouf/deploy-snapshots/consultation-read-fix-20261002-1049. Derivare config dalla precedente runtime-snapshot privata e cambiare SOLO stageRoot, commit sorgenti e liveRevision attesi (Semantic8985, MCP8476). Stage non crea container né modifica route/runtime/policy, e può procedere durante CI. La futura preparazione/rilascio deve gestire due route semantic già esistenti con ownership/delta e ripristino config originali: NON riusare alla cieca il release add-only della prima installazione; non eliminare vecchi rollback container.
