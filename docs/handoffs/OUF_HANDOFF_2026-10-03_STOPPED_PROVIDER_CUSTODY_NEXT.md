# OUF — ripartenza dopo creazione dei candidati provider fermi

## Checkpoint corrente — inventario candidati pronto; prossimo intervento VPS §21

Gateway PR56 head `6e84e5ca1134cd8e26b603380a0adcb06a15fb0c`. Helper nuovo `scripts/inventory_semantic_preexec_candidates.py`, SHA256 `63fb3da6682861cd033c236a2830668bb4648b27ddc139799a05a8c62652f0bb`. Readback di helper, test, workflow e protocollo su GitHub verificato. Locale: **32 PASS + 2 Docker opt-in skip**, Docker assente nel workspace. **Job dedicati 111284288072 e 111284295941 completed/success**, log letti: ciascuno **34 test (32 regressioni + 2 Docker reali), 3 prove native di rete e 1 prova OCI reale senza skip**; runc 1.5.1. **CI complessiva verificata sull'esatto head: 34/34 completed/success, nessun pending/failure.**

Ultimo intervento VPS §20 **ESEGUITO plan/apply/verify PASS**, undici hash OK; package root `/etc/ouf/deploy-snapshots/semantic-preexec-package-20261003-195926`, source `1a020edea42cdf60a38298bec2ffebc97b3fad02`, Python 3.13.5, strumenti metadata tutti presenti. Il package sigillato resta immutabile, runtimeRegistered/startAuthorized=false e nessuna modifica di rule/unit/container.

**Prossimo intervento operatore: handoff §21, inventario candidati di sola lettura, NON ESEGUITO.** Il comando pubblica un nuovo snapshot privato del solo helper e legge candidati/reti tramite socket Docker locale, CLI config privata vuota, ambiente minimale e proiezioni allowlist. Lega manifest/creation journal agli hash attestati e network receipt al manifest; controlla custody CREATED/PID zero/mai avviato/restart no, runtime assegnato, network/IPAM/alias configurati, owner/bridge e assenza di membri estranei sulle sole reti dedicate. Due letture concordanti e rilettura dei file attestano stabilità osservata, mai atomicità. Output ridotto a hash/runtime/conteggi, niente Env/mount/comandi/indirizzi o namespace path. Non usa il vecchio inventario DENY_ONLY per accettare il nuovo guard RUNTIME_EMPTY.

**Rischi e decisione documentati prima dell'implementazione:** (1) endpoint configurati differiti non sono namespace live: NetworkID vuoto ammesso con verifica separata del network ID e liveNamespaceBindingProven=false; (2) letture Docker multiple non sono atomiche: drift blocca ma atomicSnapshotProven=false; (3) inspect integrale/ambiente ereditato/output illimitato potrebbero esporre segreti, selezionare host remoto o consumare memoria: proiezioni allowlist, socket locale, configurazione privata vuota, output 128 KiB e deadline totale 30 s. Test negativi coprono start/drift/ownership/IPAM, duplicati JSON, output e deadline; Docker reale prova il helper CLI con due nuovi candidati sintetici mai avviati, ripuliti dopo la prova.

La documentazione ufficiale Docker richiede registrazione esplicita per runtime drop-in runc o integrazione shim containerd: [Alternative runtimes](https://docs.docker.com/engine/daemon/alternative-runtimes/). Decisione ordinaria: progettare un'integrazione nominata e scoped, preservando default/cohort; nessun cambio globale per aggirare binding non provati. Runtime osservato non prova che il gate sia invocato. Il wrapper/shim di integrazione Docker **non è ancora implementato né provato**. Authority reale, binding namespace/PID/veth live, admission OIDC/purpose/TLS/revoca, lease attiva e reboot rimangono aperti. Nessuna registrazione/reload/restart/ricreazione/start/merge/replay impliciti. Topologie distribuite e co-localizzate, migliaia di Enti e assenza di default IP/bridge fixture restano requisiti permanenti.

## Checkpoint precedente — source package VPS ESEGUITO; integrazione Docker da verificare

Gateway PR56 head `1a020edea42cdf60a38298bec2ffebc97b3fad02`. **Job dedicati 111273368756 e 111273359644 completed/success**: ciascuno **29 test (28 regressioni + 1 Docker reale), 3 prove native di rete e 1 prova OCI reale senza skip**; log letti. Entrambi riportano **runc version 1.5.1**, la stessa versione standalone rilevata sul VPS. **CI complessiva verificata sull'esatto head: 34/34 completed/success, nessun pending/failure.** Localmente 28 PASS + 1 Docker opt-in skip, con dipendenze riallineate all'esatto source remoto. Undici sorgenti del package letti da GitHub e confrontati esattamente; comando staging controllato con bash -n.

La nuova prova esegue il driver source-sealed con runc, nft, namespace/veth, lock e journal privati reali. Source tamper, start authority assente, lease non quiescente, MAC/bundle drift impediscono l'applicazione; create valido lascia assente il marker fino allo start esplicito; rollback con generazione viva e nuova creazione con handle estranei sono rifiutati. Fixture con sola shell statica e authority sintetica, nessun provider chiamato. Corrette le dipendenze CI senza rimpiazzare il runtime Docker del runner e l'isolamento stdio/dev della fixture. I fallimenti delle revisioni precedenti sono storici, non PASS retroattivi.

| Componente nuovo | SHA256 |
| --- | --- |
| `scripts/stage_semantic_preexec_package.py` | `bf86bc438c39a1f8f7752797110bcfcf18b9e7deb23a662f850fffb900df2fd8` |
| `scripts/semantic_provider_preexec_hook.py` | `e904774d50626e3ce93d6bcd187571b03d0698ad6a7472a7b6a862b4816eb850` |
| `tools/semantic_provider_preexec_native.py` | `c45d343308a311790bcd5c9ed9687925d4af0fec59f96fc79f4af7a685b8c70f` |

Decisione: prepared-namespace/static IPv4 come primo backend sincrono, separato dal contratto di identity/authority/flow e lifecycle. Il driver root/Python -I -B verifica dieci sorgenti prima degli import, bundle privato, namespace inode, veth peer/ifindex, bridge, MAC/IP e PID/start ticks; rifiuta hook successivi capaci di modificare la rete. Nessuna assunzione Docker/IP/bridge fixture diventa default di piattaforma. Migliaia di Enti e distribuzione/co-localizzazione rimangono invarianti permanenti.

**Ultimo intervento operatore: §20 ESEGUITO, plan/apply/verify PASS; package `semantic-preexec-package-20261003-195926`.** Undici file pin/hash, receipt esclusiva/fsynced e tool availability/Python version rilevati via metadata. Non crea profilo driver, namespace, coordination journal, hook OCI installato, tabelle, unità, runtime registration o container. Non avvia processi applicativi/owner; source staging non abilita lease. Il source receipt non è acceptance, tool presence non prova static busybox né backend target utilizzabile.

**Limiti aperti:** la prova è standalone runc in CI, non Docker del VPS né startup/admission target. Occorrono profilo/binding/authority reali, template indipendente, integration/wrapper o shim con registrazione esplicita, gestione cohort e lifecycle servizi/reboot. Default runtime e vecchi candidati restano invariati; nessun reload/restart, merge o replay impliciti. Target resta RUNTIME_EMPTY/EMPTY_ONLY, due candidati mai avviati, providerCalls=0/startAuthorized=false. Inventario VPS §19 **ESEGUITO PASS**, source `semantic-preexec-runtime-inventory-20261003-183915`, Docker 29.8.1/default runc e runc standalone 1.5.1; il percorso invocato da Docker non è dimostrato dal numero di versione.

## Source package VPS — ESEGUITO, PASS (3 ottobre 2026)

Output operatore ricevuto e registrato: **plan/apply/verify PASS**, tutti gli undici SHA256 OK. Package root `/etc/ouf/deploy-snapshots/semantic-preexec-package-20261003-195926`; receipt `source-package-receipt.json`, schema `ouf.semantic-preexec-source-package.v1`, source commit Gateway `1a020edea42cdf60a38298bec2ffebc97b3fad02`. Python **3.13.5**; busybox/ip/nft/nsenter/python/runc/unshare risultano tutti disponibili secondo il controllo metadata dello stager.

**Comando handoff §20 ESEGUITO: conservarlo come registro, non ripetere apply.** PRIVATE_SOURCE_ONLY=true; runtimeRegistered=false, startAuthorized=false, rulesChanged=false, unitsChanged=false, containersChanged=false, providerCalls=0, notReleaseAcceptance=true, noSecretsPrinted=true in tutti i modi. Evidenza ricevuta dall'operatore, distinta dalle prove CI: nessuna verifica dell'integrazione Docker o dell'admission target può essere dichiarata superata da questa receipt.

**Prossimo passo preciso:** preparare e verificare il contratto di integrazione Docker e un inventario privato dei binding dei candidati fermi e delle reti, vincolato ai manifest/journal già sigillati. Il successivo comando VPS dovrà essere di sola lettura e pubblicazione di evidenza privata, senza registrazione runtime, reload/restart, modifica cohort o avvio. Namespace live, authority di infrastruttura, admission OIDC/purpose/TLS/revoca, coordinazione lease attiva e reboot restano gate aperti. Nessun indirizzo o bridge osservato diventa default di piattaforma; restano obbligatorie topologie distribuite e co-localizzate per migliaia di Enti.


## Inventario runtime VPS — ESEGUITO, PASS (3 ottobre 2026)

Output operatore ricevuto: source root `/etc/ouf/deploy-snapshots/semantic-preexec-runtime-inventory-20261003-183915`. Schema `ouf.semantic-preexec-runtime-inventory.v1`, Docker serverVersion **29.8.1**, defaultRuntime **runc**, runtimeNames **io.containerd.runc.v2, runc**, runcBinaryVersion **1.5.1**. READ_ONLY=true, stableAcrossReads=true, atomicSnapshotProven=false, ociHookIntegrationProven=false, runtimeRegistrationAuthorized=false, startAuthorized=false, providerCalls=0, notReleaseAcceptance=true, noSecretsPrinted=true. Righe JSON e PASS attestate dall'operatore; nessuna modifica rule/unit/container.

**Comando §19 ESEGUITO: conservarlo come registro, non ripeterlo.** Il binario runc locale non è prova che Docker utilizzi quel percorso; l'inventario non autorizza registrazione runtime, avvio o restart. Prossimo lavoro autonomo: backend con binding live e verifica sincrona OCI prima del processo, prove positive/negative reali e nuovo staging sealed; Docker target e authority rimangono gate separati.

## Checkpoint precedente — core install/recovery e inventario runtime (82d1db7)

Core Gateway `a0473e397d90d46cda2ca33404670c514dd435c9`: **34/34 check completed/success**, nessun pending/failure; job 111261718405 e 111261707562 ciascuno **19 regressioni + 3 prove native PASS senza skip**. Head corrente Gateway PR56 `82d1db716b1015dac52feca217af1c5ed600a520`: job dedicato 111264097837 **PASS, 24 test (23 regressioni + 1 Docker reale) e 3 prove native senza skip**, log controllato. È PASS anche il job 111263877173 del precedente d0fa3d1. **Verifica successiva sull'esatto head: CI complessiva 34/34 completed/success, nessun pending/failure.** Validazione locale: 23 PASS e 1 Docker reale skip perché assente nel workspace. Readback dei file pubblicati e dei quattro documenti verificato.

Il nuovo core `tools/semantic_provider_preexec.py` (SHA256 `5086f893ac22e962816e76709883c9c7f341989919339c579a4f28bfbd403804`) implementa STAGED/INSTALLING/PROTECTED/REMOVING/ROLLED_BACK, installazione esclusiva atomica delle due tabelle, ownership/readback, journal fsynced e lock comune con coordination, recupero esplicito dopo crash e rollback solo con generazione provata morta. Liveness sconosciuta non equivale a morte. Rifiuta replay apply, tabelle/handle estranei, footprint/binding/generazione alterati e lease non quiescenti. Footprint indipendente e commento transaction univoco sono prerequisiti del driver.

Il helper `scripts/inventory_semantic_preexec_runtime.py` è ora verificato con Docker reale in CI. Legge soltanto serverVersion/defaultRuntime/runtimeNames e versione runc locale, da socket locale root-owned e CLI configuration privato vuoto. Non eredita DOCKER_HOST/proxy/credential helper e non stampa daemon config/argomenti/credenziali. Corrette e testate due incompatibilità emerse in CI: newline finale aggiuntivo del formatter Docker e timestamp di accesso del socket; resta controllata l'identità device/inode/mode/uid/gid/nlink. SHA256 helper `5caf118353fbb49457ad083bdcf26e778413ba9ea699978ce52465a8480860e1`.

**Limite esplicito:** core con backend/driver iniettati, non hook OCI distribuito né registrazione Docker. La prova nativa del lifecycle usa un processo fixture già vivo e verifica namespace/PID/start ticks; **non prova protezione prima dell'esecuzione dell'applicazione**. Restano source-sealed driver/staging, aggancio OCI reale, integrazione runtime target e migrazione servizi guard/owner. Una versione runc locale non prova che Docker usi quel binario; letture stabili non provano snapshot atomico o compatibilità OCI.

**Inventario read-only del §19 ESEGUITO, PASS:** output e source root nel nuovo checkpoint sopra. Il comando è registro storico e pinna source/hash verificati; non ripeterlo. Conservare output e nuovo source root, fermarsi su BLOCKED senza replay di runtime apply. Runtime rilevato: Docker 29.8.1/default runc, versione standalone 1.5.1. Integrare e provare il driver; l'inventario non dimostra il percorso binario usato da Docker. Nessuna registrazione/avvio/restart autorizzati dall'inventario.

Restano attestati i comandi VPS già **ESEGUITI** ai §§11–16: intent privato, staging, runtime plan/apply/verify RUNTIME_EMPTY e readiness read-only PASS. Stage `semantic-runtime-transition-stage-20261003-160211/prepared`, readiness source `semantic-runtime-readiness-20261003-165430`; **EMPTY_ONLY**, due candidati mai avviati, zero provider call, start non autorizzato. Nessun merge, avvio/replay, Docker restart, mutazione target o riattivazione lease eseguiti da questo lavoro. Scala di migliaia di Enti e topologie distribuite/co-localizzate rimangono vincoli permanenti; backend Linux non diventa default universale. PET e business acceptance conservati.

## Checkpoint precedente — shared-face compiler e core guard/lease verificati (d382891)

Dopo la richiesta dell'operatore «Proseguiamo con enforcement sulle interfacce condivise e coordinazione guard/lease», Gateway PR56 contiene il commit `d38289132e49c9e9be4cb6245bb70a63cfaa82dc` (precedente `2a4499fb17e174f57c5f557d1fdaace793e8ec06`). **CI sull'esatto head: 34/34 completed/success**, nessun pending/failure. I job `shared-face-lease-coordination` 111254451253 e 111254440087 hanno eseguito ciascuno **9 regressioni + 2 prove native PASS senza skip**. Readback esatto dei sei file nuovi/modificati. Nuovi test locali: 9 eseguiti PASS, 2 native skip perché questo workspace non ha nft/ip/netns; la prova nativa è CI, non VPS. Nessun merge.

| Componente software nuovo | SHA256 / risultato |
| --- | --- |
| `tools/materialize_semantic_shared_faces.py` | `b97f31cc17c22abbb7a021c274be73816f649196762f9c6dfcc54a58d8382e8a` |
| `tools/semantic_provider_lease_coordination.py` | `25c6df90d33e39fe83321df6ab9e5c38d4c33bcd290ad57c7a85c03b1bb8ba78` |
| Fixture shared faces | Same-subnet, routed-network e host-local positivi; porte/peer non governati, spoof IP/MAC e peer port negati; altri peer IPv4/IPv6 conservati; rinomina conserva binding ifindex |
| Fixture coordination | DNS locale fresco A+AAAA, nft timeout sets, flock comune e journal root privato/fsynced reali; quiesce/revoke, nuova risoluzione dopo riattivazione esplicita, gate incompleto e handle ricreati negati |

Decisione architetturale coerente con scala di qualche migliaio di Enti e topologie distribuite/co-localizzate: contratti identity/authority/flow e lifecycle separati dal backend di enforcement. Il backend Linux seleziona port ifindex+bridge+MAC+IPv4 dei workload e ingress kind/index del peer, senza applicare default-deny all'intero bridge shared. Ogni flow dichiara authorityRef e coppia/protocollo/porta esatti; un ref dichiarato non prova approval. IPv6/VLAN/data non governati sono negati sulle porte selezionate in questo backend iniziale IPv4, preservati sugli altri peer. Fixture routed non prova multi-server/tenant acceptance né SLO a migliaia di Enti.

Il core `Coordinator` usa il medesimo boot lock durante DNS fresco/apply/readback/pubblicazione. Fasi LEASE_READY → LEASE_UPDATING → LEASE_READY; QUIESCING prima della revoca e QUIESCED soltanto dopo empty readback; BLOCKED su failure. `PrivateJournal` compare-and-replace/fsync sotto lock, root:root0600/nofollow/single-link/bounds/duplicate checks; lock inode esistente riusato, non creato. Config/DNS/hash handle dell'owner congelati e ricontrollati; membership autorizzata dal receipt dell'ultimo ciclo, TTL finita, niente cached TTL replay, auto-reactivation o ricreazione/rebinding automatico. startAuthorized resta sempre false. Il journal attuale EMPTY_ONLY non è adottato da questo protocollo nuovo.

**Questi componenti non sono installati sul VPS e non costituiscono ancora un nuovo profilo deploy completo.** Il target resta al §16 PASS: RUNTIME_EMPTY, guard EMPTY_ONLY, 2 candidati mai avviati, provider sets vuoti, zero DNS/provider calls, avvio non autorizzato; source cohort target `ef2270a57446da1f23a58548aa4d44920e578fe0` e hash config/journal/lease attestati invariati. Nessun comando VPS, restart, reboot, start o lease activation eseguito in questa fase.

Gate di integrazione concreto: il binding namespace/ifindex/iflink/parent/MAC/IP/generazione deve essere verificato e protetto **prima dell'esecuzione applicativa**. Un listener Docker post-start sarebbe una finestra di bypass e non viene scelto. I candidati mai avviati attuali non forniscono tale prova o il lifecycle di ricreazione delle porte. Occorre integrare un meccanismo runtime sincrono network-before-process e un nuovo installer sealed con recovery/rollback, owner/guard service lifecycle e migrazione dall'EMPTY_ONLY; non cambiare cohort/manifests/reti produttive per comodità. Nessun nuovo apply target è predisposto.

Protocollo e limiti: [documento Gateway fissato](https://github.com/GioNob/ouf-api-gateway/blob/d38289132e49c9e9be4cb6245bb70a63cfaa82dc/docs/SEMANTIC_PROVIDER_SHARED_FACE_LEASE_PROTOCOL.md). Rischi verificati: spoof da porta distinta anche con IP+MAC falsificati; port rename/reparent; race restore vs writer (lock denial), incomplete gate e revoca fallita; source/authority injection, journal/config/DNS/handle drift; foreign journal preservato. Restano authority/shared-face live binding, bootstrap pre-process, real IPv6 dove richiesto, OIDC/purpose/TLS/revocation admission, real reboot, tenant/distributed/load acceptance e gate Semantic/Discovery/THS/file/API→UDP/Search. PET e business evidence conservati.

## Requisito architetturale permanente e vincolante — scala Enti e topologie indipendenti

**Istruzione esplicita dell'operatore, 3 ottobre 2026: OUF sarà ragionevolmente adottata da qualche migliaio di Enti. Deve supportare microservizi su reti e server differenti e installazioni su un unico server nella stessa rete/sottorete. Questo requisito governa ogni scelta architetturale, implementazione, test e procedura di installazione futura.**

- La posizione di rete non conferisce identità, fiducia, tenant authority o autorizzazione. I medesimi contratti di autenticazione/autorizzazione, segregazione e transito obbligatorio attraverso Gateway devono valere anche fra servizi sullo stesso host o nella stessa sottorete.
- Endpoint, porte, service identity, trust/secret reference, tenant binding e policy devono essere parametri espliciti e governati per installazione. Nessuna dipendenza obbligatoria da IP, nomi Docker, bridge, subnet, percorsi host o domini del laboratorio.
- Gli adapter di deployment/enforcement possono differire fra topologie, ma devono preservare invarianti di default-deny, protezione SSRF/DNS/redirect, prevenzione del bypass e isolamento applicabile fra Enti. Non assumere che firewall inter-subnet o bridge dedicati siano presenti o sufficienti.
- Installazione, registrazione delle capability, configurazione, upgrade, riconciliazione e verifica devono essere automatizzabili e idempotenti; niente procedure manuali ripetute per ogni Ente/capability. Parametri e ownership devono permettere convivenza senza collisioni e deployment separati.
- Validare sia topologia distribuita su host/reti distinti sia topologia co-localizzata su singolo host e stessa sottorete, includendo negative-path di accesso diretto/bypass e isolamento fra Enti dove condividono risorse. Non dedurre scalabilità o performance a migliaia di Enti da fixture del laboratorio: servono profili di carico e SLO rappresentativi.
- Il profilo Docker/nft di ouf-lab è una realizzazione di deployment, non il contratto generale della piattaforma. Conservare le evidenze già ottenute, senza universalizzare dettagli locali né riscrivere il lavoro validato per convenienza.

La previsione di qualche migliaio di Enti non impone automaticamente migliaia di tenant nella stessa istanza: cardinalità, deployment condivisi/separati, isolamento e capacità vanno dichiarati nei profili. Ogni proposta futura deve spiegare come funziona nelle due topologie, senza ampliamenti impliciti di authority o bypass dei confini PET. Se una soluzione copre soltanto il laboratorio, dichiarare il limite e mantenere il gate portabilità aperto. Non chiudere R-INSTALL o scalabilità sulla sola CI.

Questo requisito si aggiunge alle regole permanenti di validazione/autonomia/checkpoint e va conservato in ogni nuovo handoff. Registrazione documentale: nessuna modifica al runtime VPS e nessuna nuova prova di scala/topologia dichiarata.

## Checkpoint target attestato — inventario readiness VPS ESEGUITO, PASS; gate startup aperti

Il 3 ottobre 2026 alle 16:54 UTC (18:54 Europe/Rome) l'operatore ha eseguito il comando §16 e restituito `SEMANTIC_RUNTIME_READINESS_INVENTORY=PASS READ_ONLY=true STARTUP_READY=false START_AUTHORIZED=false NO_IAM_OR_DNS_CALL=true NO_RULE_UNIT_CONTAINER_CHANGED=true NO_SECRETS_PRINTED=true`. Source snapshot attestato: `/etc/ouf/deploy-snapshots/semantic-runtime-readiness-20261003-165430`. Helper Gateway `4daad06b71695ad839d1865e55d5aeaf765df861`, checksum `ecb0326b9f97f76598d9bad56aa241b01802bf0a601f4eda38fef41fb15c655a`; runtime cohort originale resta `ef2270a57446da1f23a58548aa4d44920e578fe0`.

| Binding runtime attestato | Valore |
| --- | --- |
| Stage root | `/etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/prepared` |
| configurationHash | `24968cf990a32b87f3169b9226fe63d224c93a403540afec197011fbd670b0bb` |
| journalHash | `4ccb05b0a28b6e7e823de3d9af81f29255d60b38271d0a74a00f64e2e5828a74` |
| leaseStructureHash | `26f6f80af9d1e4898c1a6fe6dc8721cd6f67f1ceed05c7eea35e3b9f4a040e54` |
| Custody / stato / guard | runtimeCustodyVerified=true, RUNTIME_EMPTY, EMPTY_ONLY |
| Candidati | 2, candidatesNeverStarted=true |
| Regole statiche | 9; purpose DNS e GATEWAY_ADAPTER |
| Provider / interfacce | 1 provider flow, insiemi vuoti; 2 guarded interfaces, 4 shared interfaces escluse |
| Limiti | stableAcrossReads=true, atomicSnapshotProven=false; startupReady=false, activeLeaseLifecycleReady=false; DNS/provider calls 0; notReleaseAcceptance=true |

**Custody, intent, staging, runtime plan/apply/verify e readiness sono completati nel proprio scope. Non ripetere §§6,11–16.** L'inventario ha verificato binding e stato corrente senza promuoverli ad authority/startup/packet acceptance. In particolare le 9 staticFlows non contengono WORKLOAD_GATEWAY o IDENTITY; l'assenza di tali purpose non prova da sola l'assenza di ogni percorso host, ma richiede un piano autoritativo per i percorsi necessari e l'enforcement sulle shared faces. Nessuna regola shared o permesso è stato inventato.

Restano sette gate esplicitamente non provati: INFRASTRUCTURE_AUTHORITY, SHARED_FACE_SOURCE_ENFORCEMENT, LIVE_NAMESPACE_ADDRESS_BINDING, PACKET_SPOOF_BYPASS_IPV6, OIDC_PURPOSE_TLS_REVOCATION_ADMISSION, ACTIVE_LEASE_GUARD_COORDINATION, REAL_REBOOT. Il prossimo lavoro indipendente è il piano di enforcement source-specific sulle shared faces e il protocollo guard/lease attivo, da validare con fixture native prima di un nuovo staging/apply target. Il lease owner isolato esistente non può essere attivato sotto EMPTY_ONLY: quando popola gli insiemi il guard attuale lo rifiuta; inoltre ricreazione tabelle e handle rebinding devono essere serializzati contro i writer, senza replay TTL.

Ciò non cambia i gate Semantic rollout migration-aware, Discovery governata/THS, mapping Teatri e file immediate ingestion o API scheduler-before-ingestion → UDP/Search. Main/live software, run business e cohort storici preservati; niente merge/restart/reboot/provider start/lease activation. CI sul software readiness già verificata 32/32 success, job root 16 test senza skip; questa nuova prova VPS è distinta dalla CI. Aggiornamento documentale del presente esito: nessun nuovo codice o nuovo comando VPS eseguito dopo l'inventario.

## Cronologia — readiness software PASS, prima dell'inventario VPS

Dopo il comando `prosegui`, è stato implementato `scripts/inventory_semantic_runtime_readiness.py` in Gateway PR56, commit `4daad06b71695ad839d1865e55d5aeaf765df861`, SHA256 `ecb0326b9f97f76598d9bad56aa241b01802bf0a601f4eda38fef41fb15c655a`. **CI sull'esatto head: 32/32 completed/success**, nessun pending/failure. Il job root nativo 111247226355 ha eseguito **16 test PASS senza skip**, con `RUNTIME_READINESS_NATIVE=PASS READ_ONLY=true STARTUP_READY=false DNS_CALLS=0`. Locale: 13 test eseguiti PASS, 3 fixture native saltate perché Docker/nft/systemd assenti. Readback esatto dei cinque file modificati, sintassi shell del comando target verificata. PR56 descrizione riallineata alla transizione target; nessun merge.

Il target resta al risultato già attestato: apply/verify PASS RUNTIME_EMPTY sul root `/etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/prepared`; due candidati mai avviati, avvio non autorizzato, zero chiamate provider, Docker non riavviato. **Il nuovo inventario readiness sul VPS NON È ESEGUITO.** Prossimo intervento: soltanto il comando read-only §16 dell'handoff. La preparazione salva un nuovo source snapshot root privato, senza modificare il cohort runtime esistente; l'inventario non scrive regole/unità/container/journal e non chiama DNS/IAM/provider.

Decisione tecnica: riusare l'installer sealed del cohort originale attraverso SHA256 esplicito `a3818878086a40377125816b776606f936ad02496d891f4bc72477c4c731ecf4` e source commit target `ef2270a57446da1f23a58548aa4d44920e578fe0`. Il nuovo commit dell'inventario non sostituisce i source installati. Evitare il vecchio custody deny-only/intent verifier dopo la transizione, perché attendono tabelle originali. Il nuovo helper valida receipt/source/config/artifact, journal completo, footprint e hash lease con handle, unità installate/caricate, shared structure/PID Docker/candidati/input immutabili e ripete i readback sotto lo stesso boot lock. Stable read non è snapshot host globalmente atomico.

Rischi affrontati e verificati: import di source alterato o non privato (hash/mode/owner/nofollow/nlink/bounds), promozione di journal incompleto o lease/handle estranei (blocco senza flush), drift tra letture e divulgazione di config/errori (blocco redatto). La fixture nativa attesta inventario dopo transizione reale con entrambi i readback nft, journal e PID invariati. L'output espone soltanto hash/count/purpose e gate non provati; `staticPurposes` non è prova di authority e `startupReady=false` resta obbligatorio.

Vincolo verificato nel codice: guard installato EMPTY_ONLY, mentre lease owner isolato popola insiemi con DNS fresco. **Lifecycle attivo ancora da implementare/integrare col guard, non attivare il lease owner attuale.** La futura transizione deve coordinare gate persistente, owner writer e ricreazione/handle rebinding, pre-start Docker, revoca stop/failure/restart, expiry finita e nessun replay TTL. Restano inoltre authority/shared-face enforcement, live namespace/IP e pacchetti/spoof/bypass/IPv6, OIDC/purpose/TLS/revocation, reboot reale, rollout Semantic migration-aware, Discovery/THS e acceptance file/API→UDP/Search. PET Gateway v1.5 T11/T11.3 GW-NET-01..05 e Semantic v1.3 §§9.2/10–11 riletti; nessuna modifica ai confini dominio/THS e al requisito di egress cumulativo. Nessun provider start/restart/reboot, upload/job replay o alterazione business evidence eseguito.

## Regole permanenti di esecuzione — adottate dall'operatore il 3 ottobre 2026

**Validazione obbligatoria.** Prima dell’implementazione, verifica il flusso, le dipendenze e i principali rischi logici, di concorrenza, memoria e compatibilità. Correggi autonomamente i problemi individuati e valida il risultato con test pertinenti e CI. Presenta il codice completato insieme alle verifiche eseguite e agli eventuali limiti residui. Non dichiarare superata una verifica basandoti soltanto sull’auto-revisione.

**Autonomia e completamento.** Procedi autonomamente entro l’obiettivo concordato. Risolvi le scelte tecniche privilegiando coerenza con PET e repository, semplicità, reversibilità e scalabilità necessaria; documenta le decisioni nell’handoff senza fermarti per scelte ordinarie. Mantieni aggiornati handoff, roadmap, manuale e sprint, comprese le sezioni dei comandi eseguiti. Fermati soltanto quando serve un’azione sul VPS, un’informazione indispensabile o una decisione di autorità non già conferita. Niente merge, avvii o replay impliciti.

**Checkpoint.** Lascia sempre un risultato verificabile: commit, stato dei test/CI, lavoro completato, questioni aperte e prossimo passo preciso. Se un blocco impedisce una parte, completa comunque le attività indipendenti.

**Autonomia rafforzata — nuova regola dell'operatore, 3 ottobre 2026.** «procedi e vai avanti “a manetta” fermandoti solo quando devo intervenire io». Proseguire senza pause o richieste di conferma per scelte tecniche ordinarie, completando le attività autonome e quelle indipendenti da eventuali blocchi. Fermarsi soltanto quando l'intervento dell'operatore è indispensabile: azione VPS, informazione necessaria o autorità non già conferita. Usare checkpoint frequenti, salvati su GitHub, per conservare continuità anche in caso di disconnessione della chat; un checkpoint non costituisce motivo per interrompere il lavoro autonomo. Restano obbligatorie validazione con test/CI, coerenza PET e aggiornamento dei quattro documenti/comandi. Nessun merge, avvio, replay o restart implicito.

Queste regole si applicano alla continuazione del progetto e alle nuove chat. Il prossimo lavoro tecnico rimane la preparazione dei gate rete/authority e del lifecycle lease dopo RUNTIME_EMPTY (§15 dell'handoff). La loro adozione non attesta verifiche aggiuntive e non conferisce autorizzazione startup, merge, replay o restart. Stato target confermato: apply/verify PASS RUNTIME_EMPTY, startAuthorized=false. Nessun nuovo codice, test/CI o comando VPS eseguito in questo checkpoint di regole.

## Checkpoint target attestato — runtime VPS ESEGUITO, PASS apply/verify, RUNTIME_EMPTY

Il 3 ottobre 2026 l'operatore ha restituito entrambi gli esiti del §14: `SEMANTIC_RUNTIME_TRANSITION=PASS MODE=apply STATE=RUNTIME_EMPTY` e `SEMANTIC_RUNTIME_TRANSITION=PASS MODE=verify STATE=RUNTIME_EMPTY`. Entrambi attestano `START_AUTHORIZED=false PROVIDER_CALLS=0 DOCKER_RESTARTED=false NOT_RELEASE_ACCEPTANCE=true NO_SECRETS_PRINTED=true`. Il messaggio successivo ripete gli stessi esiti; è duplicato della stessa attestazione, non evidenza di un secondo apply.

Stage/transaction root: `/etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/prepared`; journal `transition-journal.json` sotto tale root; source Gateway `ef2270a57446da1f23a58548aa4d44920e578fe0`. Intent precedente `/etc/ouf/deploy-snapshots/semantic-provider-transition-intent-20261003-151036/prepared` conservato. Custody, intent, staging, plan e apply/verify sono completati nel loro scope. **Non ripetere i comandi §§6,11–14.**

Stato host corrente: guard/drop-in runtime installati e caricati tramite daemon-reload; le due tabelle possedute sono nel profilo runtime con insiemi provider vuoti, footprint e binding leaseStructureHash verificati e journal completato RUNTIME_EMPTY. Il precedente DENY_ONLY è baseline storica conservata, non il profilo host attuale. Docker non riavviato, due candidati mai avviati, nessuna chiamata provider, avvio non autorizzato. Gli insiemi timeout vuoti non attestano installazione/attivazione del lease owner o lease attive.

Prossimo lavoro: chiudere i gate residui di authority infrastrutturale, namespace/source/live IP e pacchetti/spoof/direct bypass/IPv6, admission OIDC/purpose/TLS/revocation e lifecycle lease prima di proporre startup. Il guard attuale è empty-only e rifiuta elementi lease attivi: non installare/attivare una lease owner sotto questo profilo senza transizione coordinata e prove. Reboot reale, rollout Semantic migration-aware, Discovery/THS, mapping Teatri e percorso file/API→UDP/Search restano aperti. Il comando read-only readiness §16 è ora predisposto e pendente; nessun comando start/restart/reboot. Main/live software e run business conservati; nessun merge.

L'apply host è una prova target della transizione vuota, non release acceptance né prova di provider operativo/reboot. Conservare gli originali sealed e questo journal. In caso di drift/interruzione futura usare diagnosi e reconcile/rollback espliciti, mai replay apply. Una ricreazione delle tabelle cambia gli handle e richiede riconciliazione del binding lease; il rollback logico non fabbrica un nuovo PASS custody legacy.

## Cronologia — runtime plan PASS, prima di apply/verify

Il 3 ottobre 2026 l'operatore ha restituito `SEMANTIC_RUNTIME_TRANSITION=PASS MODE=plan STATE=PREPARING START_AUTHORIZED=false PROVIDER_CALLS=0 DOCKER_RESTARTED=false NOT_RELEASE_ACCEPTANCE=true NO_SECRETS_PRINTED=true` per il §13 dell'handoff, sullo stage `/etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/prepared`, source Gateway `ef2270a57446da1f23a58548aa4d44920e578fe0`. **Plan eseguito; non ripeterlo come passo autonomo.** `PREPARING` è il record restituito dal plan: il codice ritorna prima di scrivere il journal e prima di qualsiasi installazione; non prova una transizione apply iniziata.

Custody, intent e staging privato già PASS; nessuna regola/unità/container host modificata da questo plan. Host ancora DENY_ONLY, kernel lease assente, due candidati mai avviati, avvio non autorizzato. Prossimo comando pendente: transizione runtime `apply` seguita da `verify`, §14 dell'handoff. Questo successivo apply sostituisce soltanto le due tabelle possedute con il profilo runtime a provider set vuoti e gli artefatti guard/drop-in posseduti, con journal persistente e `systemctl daemon-reload`; non riavvia Docker/container e non autorizza start né installa/attiva lease. Non è release acceptance.

Runtime apply/verify target **NON ESEGUITI**. Se BLOCKED o interruzione, conservare snapshot/journal e non rieseguire apply: diagnosticare per reconcile/rollback espliciti. Tutti i gate PET, authority, namespace/pacchetti/IPv6, admission/lease lifecycle/reboot e business acceptance restano aperti; main/live e run Cinema/Teatri invariati. CI software già verificata 32/32 e job runtime 11 test senza skip.

## Cronologia — staging privato PASS, prima del runtime plan

Il 3 ottobre 2026 alle 16:02 UTC (18:02 Europe/Rome) l'operatore ha eseguito il blocco staging del §12 dell'handoff. I tre checksum source sono OK; `SEMANTIC_RUNTIME_TRANSITION_STAGE=PASS` nei modi `plan/apply/verify`. Root del tentativo: `/etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211`; root preparato privato: `/etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/prepared`.

Output attestato: `ISOLATED_NATIVE_TEMPLATE=true`, `HOST_RULES_UNCHANGED=true`, `UNITS_UNCHANGED=true`, `CONTAINERS_UNCHANGED=true`, `EMPTY_PROVIDER_SETS=true`, `START_AUTHORIZED=false`, `PROVIDER_CALLS=0`, `NOT_RELEASE_ACCEPTANCE=true`, `NO_SECRETS_PRINTED=true`. Il template vuoto è compilato in namespace isolato; non prova regole runtime host installate. Intent precedente PASS al root `semantic-provider-transition-intent-20261003-151036/prepared` conservato. Non ripetere custody, intent o staging come passi autonomi.

Source Gateway fissato: `ef2270a57446da1f23a58548aa4d44920e578fe0`; CI software già verificata 32/32 PASS, job runtime 11 test senza skip. Main/live e business evidence Cinema/Teatri invariati. Boot host DENY_ONLY, nessuna kernel lease installata, due candidati mai avviati; avvio non autorizzato. Rimangono tutti i gate PET/admission/authority/live namespace/packets/IPv6/lease lifecycle/reboot e acceptance già elencati.

**Prossimo intervento pendente: solo runtime transition `--mode plan`**, read-only sulle regole/unità/container, sullo stage attestato; comando nel §13 dell'handoff. Runtime `apply/verify/reconcile/rollback` host NON ESEGUITI. Non avviare container, non fare restart Docker/reboot e non presumere che PASS stage sia release acceptance.

## Cronologia — intent PASS e software verificato, prima dello staging target

Il 3 ottobre 2026 l'operatore ha restituito PASS per `prepare_semantic_provider_transition_intent.py` nei tre modi `plan/apply/verify`. Root privato attestato: `/etc/ouf/deploy-snapshots/semantic-provider-transition-intent-20261003-151036/prepared`. Il boot lock è stato riusato; sono stati scritti soltanto artefatti privati. Nessuna regola runtime, unità o container modificata; `startAuthorized=false`, `providerCalls=0`, `notReleaseAcceptance=true`. Questa prova supera le diciture intent pendente sotto, conservate come cronologia; non ripetere l'intent come passo autonomo.

Gateway PR56, ancora aperta/draft: commit `ef2270a57446da1f23a58548aa4d44920e578fe0`, **32/32 check run completed/success**, nessun pending/failure. Il log del job `provider-runtime-transition` 111236177469 attesta **11 test PASS senza skip**: 8 prove di file privati/lock e 3 fixture native con Docker/nft/systemd. Le fixture provano staging, apply/verify, ripristino delle sole tabelle vuote, blocco di tabelle estranee/parziali, riconciliazione esplicita degli handle, gate persistente dopo crash/reload fallita, rollback degli artefatti posseduti e rifiuto atomico nft con conservazione delle due tabelle precedenti. Queste sono prove CI, non prove sul VPS.

| Source fissato nel commit Gateway | SHA256 |
| --- | --- |
| `scripts/restore_semantic_runtime_boot_guard.py` | `cceab662620d1abf97c09be1147c79e4e43022298cb0560dc604ed4bdeb6a606` |
| `scripts/stage_semantic_runtime_transition.py` | `f88740a293d78906b0a4c8915cc6b760a2dc3f9ab97f110cbb4308e950e519dd` |
| `scripts/transition_semantic_runtime_guard.py` | `a3818878086a40377125816b776606f936ad02496d891f4bc72477c4c731ecf4` |

Lo staging prepara esclusivamente file root privati e compila il template nft in un namespace di rete isolato tramite `unshare`; non installa unità/regole host e non avvia container. L'installer runtime è implementato con journal persistente e recovery/rollback, ma **né staging né transizione runtime sono stati eseguiti sul VPS**. Il target resta DENY_ONLY, senza kernel lease, con due candidati mai avviati e avvio non autorizzato.

Prossimo passo target: solo staging privato `plan/apply/verify`, dopo ripresa esplicita della sessione, con i pin sopra e l'intent attestato. Parametri espliciti: `--source-commit ef2270a57446da1f23a58548aa4d44920e578fe0`, `--intent-source-commit 392234edc50c6e8cd19a3028b3e9e19d6f1955b4`, `--intent-source-sha256 f1cc60568118387cad11a8546f3b0c2c64941c6a51a28611e4c62a009db57422`, `--runtime-guard-sha256 cceab662620d1abf97c09be1147c79e4e43022298cb0560dc604ed4bdeb6a606`, nuovo `--snapshot-root /etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-<UTC>/prepared` esclusivo, `--docker-path /usr/bin/docker`, `--nft-path /usr/sbin/nft`, `--systemctl-path /usr/bin/systemctl`, `--unshare-path /usr/bin/unshare`, `--python-path /usr/bin/python3`, `--provider-endpoint-ref schema-gov`, `--resolution-evidence-ref fresh-lease-owner`, `--lease-seconds 30`. Conservare i tre source verificati sotto il nuovo parent `source/scripts` (directory root 0700, file root 0600). Procedura software: [runbook Gateway fissato](https://github.com/GioNob/ouf-api-gateway/blob/ef2270a57446da1f23a58548aa4d44920e578fe0/docs/SEMANTIC_PROVIDER_BOOT_RUNTIME_TRANSITION.md). Nessun runtime apply host è il passo corrente.

Restano aperti prima dell'avvio: prova target, autorità infrastrutturale/live namespace e pacchetti, profilo IPv6, admission/start, lifecycle lease attiva, riconciliazione lease degli handle ricreati e reboot reale. Il profilo vuoto rifiuta lease attive; non le adotta né le svuota. I gate PET Gateway v1.5 T11/T11.3 GW-NET01..05 e Semantic v1.3 §§9.2/10–11 restano invariati: chatbot propone, THS adotta con autorità prevista. Non modificare main/live, non eseguire merge, replay dei run Cinema/Teatri, upload/job o ricreazione delle reti di produzione.

L'operatore ha interrotto la sessione per apparente loop/problema dell'interfaccia. Dopo l'interruzione sono stati verificati soltanto la CI e questo checkpoint documentale; nessun nuovo sviluppo o comando VPS è stato avviato.

## Cronologia — custody PASS, prima dell'esecuzione dell'intent

Il 3 ottobre 2026 l'operatore ha eseguito il blocco custody del §6 dell'handoff e restituito `SEMANTIC_PROVIDER_GUARD_CUSTODY_INVENTORY=PASS`. Questa prova **supera le precedenti diciture NON ESEGUITO/custody pending**, mantenute sotto come cronologia. Nessun replay del comando custody è richiesto come passo autonomo.

| Evidenza target | Valore |
| --- | --- |
| Schema | `ouf.semantic-provider-guard-custody.v1` |
| Manifest hash | `052b46a56ea666971f135c75af48b3342dbeb68e2f17f1f16263a99351df88bd` |
| Creation journal hash | `a1c2acd9924fc0f924ded7c2d59f128ef2d8b8dd11c62484a901f628022aaae7` |
| Boot install journal hash | `44dfac2145f509c8fb0b66983630616d25958b40f3ffc811074ebb9b3c1edda5` |
| Candidati / start | 2, neverStarted=true, startAuthorized=false |
| Boot / lease | DENY_ONLY, kernelLeaseInstalled=false, bootTransitionRequiredBeforeRuntimeRules=true |
| Effetti | Read-only; no IAM/DNS/provider calls; nessun container/regola modificato; nessun segreto stampato |

Non è release acceptance né snapshot atomico: l'helper custody non prende lock. Il path timestamped del suo source snapshot non compare nell'output fornito e non viene inventato. Gli hash sopra e i journal originali sono sufficienti a vincolare il nuovo preflight.

Gateway PR56 ora contiene `392234edc50c6e8cd19a3028b3e9e19d6f1955b4`: helper `prepare_semantic_provider_transition_intent.py`, SHA256 `f1cc60568118387cad11a8546f3b0c2c64941c6a51a28611e4c62a009db57422`. Readback esatto dei quattro file modificati; 8 test locali PASS senza skip, con file privati/flock reali e readback host simulati. CI Gateway sul nuovo head: **30/30 check run completed/success** (push e PR); i due job root intent hanno eseguito 8/8 test senza skip (0.079s/0.078s). Semantic PR30 resta `c2b4ae5abed1236378c7060b3eb3dac126672cbc`, OPEN DRAFT, 14/14 completed/success. CI non equivale a target transition acceptance. Nessun software live sostituito, merge o cambio main.

[Protocollo completo e limiti](https://github.com/GioNob/ouf-api-gateway/blob/392234edc50c6e8cd19a3028b3e9e19d6f1955b4/docs/SEMANTIC_PROVIDER_BOOT_RUNTIME_TRANSITION.md). Il restore deny-only installato rifiuta i set: non basta sostituire le regole nft. Il prossimo passo prende lo **stesso lock inode del boot guard**, revalida gli hash custody, il runtime sealed e il cohort lease9, poi registra due readback bounded di struttura propria/condivisa in un nuovo intent root-private. Plan non crea intent; apply scrive **soltanto tre file privati**; verify ricontrolla tutto. Nessuna modifica nft/unit/Docker, nessun login KC, DNS, lease o provider call. Il lock boot non serializza scrittori esterni: globalAtomicSnapshotProven=false. Collisioni, lock conteso/assente/symlink, drift e parziali bloccano; conservare la prova senza retry apply cieco.

**NON ESEGUITO sul VPS:** transition intent plan/apply/verify. **Non implementato:** nuovo runtime restore guard e apply coordinato. Il protocollo richiede gate persistente nel Docker pre-start prima delle mutazioni, intent/journal fsynced e lock comune, sostituzione atomica delle sole due tabelle con empty provider sets, confronto readback con struttura compilata attendibile, verifica shared/PID/pre-start, rollback per fase e nuova attestazione hash lease dopo ricreazione. Native failure/recovery tests prima di host apply; niente seed storico DNS né adozione cieca di hash osservati. Start/daemon/provider admission/reboot restano distinti.

Il primo head di questa sessione `844ebb1979196e847061f82ebb6cdab66948ea19` ha passato il job root intent (8/8 senza skip), ma request-boundary/config-contract non privilegiati hanno raccolto gli stessi fixture root e fallito. Head `392234edc50c6e8cd19a3028b3e9e19d6f1955b4` corregge esclusivamente test/workflow: opt-in/skip nel discovery generale e OUF_TRANSITION_FULL_OWNER_TEST=1 nel job root, che deve fallire se non è davvero root. Helper e SHA256 restano identici; nessuna attenuazione del controllo root in produzione.

Il pacchetto PET autorizzato è presente nel workspace: SHA256 `e63df67e8817eec38a9d4b3eb736b020f693b932f3360dc02f4555330f2201ce`, 323 checksum interni riletti, zero mismatch. Consultati i testi Gateway v1.5 T11/T11.3/GW-NET-01..05 e Semantic v1.3 §§9.2/10–11: default-deny cumulativo, endpoint governati, confini north/south, discovery on-demand, mapping proposto dal chatbot e autorità THS invariati. Nessuna nuova API/identity authority introdotta.

Cinema/Teatri, reti/immagini/trust/credenziali, policy38, receipt/backup e tutti i gate ereditati restano preservati. File: ingestion immediata dopo onboarding/ACTIVE; API: endpoint/credenziali/extraction profile/onboarding/scheduler prima dell'ingestion automatica. Nessun gate di startup, rete runtime o filiera completa chiuso da questo PASS.

## Cronologia — ripresa verificata precedente

Letto integralmente questo handoff al commit `381fc2ae00c52f1952e941edbc43d7fda7fa01be` attraverso il connector GitHub; acquisiti roadmap, manuale, sprint, registro ereditato del 1 ottobre e riferimenti storici 25/27/29/30 settembre e audit 27 settembre. La cronologia resta preservata: nessun gate chiuso per omissione.

Baseline allegata `OUF_Reality_Baseline_Package_v1_7(20261003-142932).zip`: SHA256 `e63df67e8817eec38a9d4b3eb736b020f693b932f3360dc02f4555330f2201ce`; tutti i 323 checksum interni coincidono. Il contenuto dell'archivio coincide con la baseline citata al §3 anche se il nome di upload differisce. Consultati Matrix L0 v1.7, Onboarding v1.6 §§92–92.2, Semantic v1.3 §§9.2/10–11/17–18, UDP v1.3 §§21–22/109.2/109.6–109.9, Authorization v1.5 §36.10 e confini MCP v1.4/Gateway v1.5. Mapping assistito esterno, autorità THS, ingestion file dopo ACTIVE e scheduler governato per API rimangono il percorso concordato.

### Pin riletti dal connector

| Repository / PR | HEAD verificato | Stato |
| --- | --- | --- |
| Gateway PR56 | `85914e39bd0aa9f8e7a0a0a9d3b9db6007633ff8` | OPEN DRAFT, 28/28 check run completed/success |
| Semantic PR30 | `c2b4ae5abed1236378c7060b3eb3dac126672cbc` | OPEN DRAFT, 14/14 check run completed/success |
| Semantic PR26 | `381fc2ae00c52f1952e941edbc43d7fda7fa01be` | OPEN DRAFT; pin di ingresso prima di questo aggiornamento documentale |
| Semantic PR27 | `e7bc5190f9e6afbbc4cf3c90d5d4970afbfad14b` | OPEN DRAFT; coincide con ultima revisione live riferita, senza nuova prova target |
| Semantic PR28 | `bf35e930fb239c61ea8ceebb41e187d653a3d96a` | OPEN DRAFT |
| MCP PR48 | `d7d5330d2b2588b3f896ea23e2c47e19b7b905a1` | OPEN DRAFT |
| Gateway PR55 | `b368284b3f6a7675863f85eeafc42d67bf9187dc` | OPEN DRAFT |

Main riletti separatamente: Semantic `d188e5e727eca7a22f414f43f164f85c31411bcf`, Gateway `dbdc24b5481dc9473b21b360ab1142c9aef0194b`, MCP `5615fdcad8cbcad9ff41ec3d0ad2ccbf9423c042`. Nessun merge o spostamento di main. Compare PR28→PR30: ahead 3, behind 0, merge-base uguale al pin PR28; la correzione disponibilità Discovery è ereditata. Il delta include V10 e rimane candidato software, non rollout. Gli stati live al §5 sono ultima evidenza operatore, non una nuova interrogazione VPS.

### Primo intervento e dipendenza target

Scaricato e letto l'helper custody dal pin Gateway sopra; byte UTF-8 verificati SHA256 `fabd47c6ce8919bc7a910cbaf63f66f1fb786b00c239ae41757c1fd0df829b8d`. Il blocco §6 è riproposto invariato come primo intervento VPS; controllo sintattico shell riuscito. **NON ESEGUITO sul target; nessun PASS custody, nuovo snapshot host o autorizzazione start è attestato.** Nessun accesso SSH è disponibile in questa sessione: l'operatore esegue il blocco e restituisce solo output redatto.

Dopo l'esito target: se BLOCKED, isolare read-only la differenza senza replay create/apply; se PASS, usare i journal/hash restituiti come precondizioni di un nuovo piano boot/runtime. La transizione richiede profilo nuovo sealed, intent/journal e lock comune con la custodia boot, stato fail-closed ad ogni fase, provider sets inizialmente vuoti, verifica della struttura condivisa e del Docker pre-start, rollback/reconciliation dei parziali. Conservare separati footprint boot e hash struttura lease; non riusare una vecchia osservazione DNS come lease. Nessun helper di transizione è dichiarato implementato o target-verified da questa ripresa. Start/daemon/provider admission e reboot restano gate distinti successivi, con binding d'installazione espliciti.

Cinema/Teatri, asset/profile/job, reti, immagini, credenziali, policy38, receipt originali e backup restano preservati; nessuna mutazione VPS, nuova ingestion o chiamata provider eseguita in questa sessione.


Checkpoint: **2026-10-03, 16:14 Europe/Rome**. L'utente interrompe la chat per lentezza, non interrompe il progetto. Questo è il punto di ingresso della nuova chat. Conserva e integra il registro storico del [1 ottobre](OUF_HANDOFF_2026-10-01_FILE_TO_UDP_NEXT_SPRINT.md), senza chiudere gate per omissione.

## 1. Checkpoint storico 16:14 — il custody allora non era eseguito

Ultima azione sul VPS provata dall'output dell'utente: `create_semantic_provider_stopped_candidates.py`, plan/apply/verify PASS. Journal:

`/etc/ouf/deploy-snapshots/semantic-provider-stopped-create-20261003-135106/prepared/creation-journal.json`

- Plan: `PLANNED`, 0 container; apply e verify: `CREATED_STOPPED`, **2 container**.
- `NEVER_STARTED=true`, `START_AUTHORIZED=false`, `NETWORK_CONFIGURATION_ONLY=true`.
- Nessun container condiviso modificato, nessuna scrittura di regole/route/IAM, zero provider call, nessuna release acceptance.
- Nomi/TLS alias: **ouf-semantic-southbound** (APISIX) e **ouf-semantic-provider** (adapter). Gli ID sono nel journal privato, non sono stati stampati né ricostruiti dalla chat.
- Le immagini sono riusate, non ricompilate. Configurazione Docker delle reti/IP non prova namespace o allocazione live, pacchetti, TLS o lease.

**NON ESEGUITO:** download/installazione/invocazione di `inventory_semantic_provider_guard_custody.py`, proposto nel messaggio successivo. Non esiste alcun output target `SEMANTIC_PROVIDER_GUARD_CUSTODY_INVENTORY=PASS` in questa chat. Non assumere nemmeno la creazione del suo snapshot timestamped. Non avviare i candidati. Primo passo operativo rimasto è il comando completo al §6.

La parte software/documentale è invece pubblicata: Gateway helper `85914e39bd0aa9f8e7a0a0a9d3b9db6007633ff8`, SHA256 `fabd47c6ce8919bc7a910cbaf63f66f1fb786b00c239ae41757c1fd0df829b8d`, sette test di admission con readback fixture. CI Gateway **28/28 SUCCESS**, verificata nuovamente durante questo handoff. Le fixture non provano lo stato del VPS.

## 2. Obiettivo e regole di collaborazione

Completare acquisizione → onboarding → mapping semantico → ingestion → UDP, utilizzabile in modo semplice tramite MCP con chatbot compatibili. Il chatbot consulta, confronta e propone il mapping; **nessun agente AI aggiunto dentro Onboarding**. Onboarding valida/persiste il mapping della source; Semantic governa artefatti/versioni; UDP decide l'identità canonica. Le decisioni autoritative HUMAN restano in THS; nessun tool MCP di approvazione/pubblicazione/merge privilegiato.

| Ingresso | Avvio del percorso | Dopo mapping e decisioni governate |
| --- | --- | --- |
| File gestito | THS scelta file → upload/staging → profiling | Onboarding/review/ACTIVE compatibile → ingestion automatica una tantum immediata → handoff/UDP/dedup; nessuna attesa di cadence periodica. |
| Verticale API | THS endpoint e credenziali → THS scelta extraction profile | Stesso percorso di mapping/governance; configurazione scheduler e pubblicazione parametri → ingestion automatica alle scadenze. Onboarding non fa polling. |

La verifica autoritativa di doppioni/identità è UDP dopo l'handoff; non spostarla nel profiler. Credenziali mediante THS/secret manager, MCP riceve riferimenti opachi e stati redatti. Il sistema deve gestire dubbi/quarantene e ripresa idempotente da stato persistito.

Regole persistenti:

1. Riusare centinaia di ore di prove/correzioni backend. Nessun replay Cinema/Teatri, nuovo upload/profile/job, riattivazione schedule o retry per comodità. Nuovi test sui collegamenti cambiati e regressioni appropriate, non ripetizione integrale manuale.
2. L'utente autorizza a proseguire autonomamente finché serve realmente il suo aiuto. Preparare codice, test/CI, piani e readback prima di chiedere login/decisione o esecuzione VPS. Non presumere accesso SSH: qui il VPS è operato dall'utente con comandi pinned.
3. Aggiornare a ogni checkpoint handoff, roadmap, manuale installazione/configurazione e sprint. Non cambiare main/mergiare automaticamente PR o trasformare CI/staging in release acceptance.
4. Tutti domini, indirizzi, porte, reti, subnet, bridge, nomi, UID/GID, path, trust, issuer/client/scope, tenant, timeout e scheduler sono parametri espliciti. I valori lab sotto sono binding di questa installazione, non default del prodotto.
5. Non stampare token, secret, env completi, private key, payload raw o log integrali. Ricevute/journal restano privati sul VPS. Usare Python **-B** nelle procedure host. Conservare backup, originali/rollback e tentativi falliti; cleanup solo proprio e verificato, mai force su container avviati/estranei.
6. Revisioni live, branch, main e candidato non sono equivalenti. Prima di modificare inventariare diff/PR per evitare doppioni. Nel workspace vecchio il repo Gateway è dirty: pubblicare soltanto file mirati su tree GitHub fresco, mai l'intero checkout.
7. Nella chat conclusa niente Docker/nft/systemd/Java runtime native locali disponibili; test native in CI e sul target. UID0 mappato non permette chown636/10006: skip locali non sono acceptance. Non generare nuove prove host fittizie.

## 3. PET e documentazione da leggere

[Roadmap](../OUF_ROADMAP_PET_1_7.md), [manuale installazione](../installation/OUF_INSTALLATION_MANUAL.md), [sprint](../sprints/OUF_ACQUISITION_TO_UDP_2026-10-02.md), storico [1 ottobre](OUF_HANDOFF_2026-10-01_FILE_TO_UDP_NEXT_SPRINT.md), con registro gate ereditati e collegamenti agli handoff 25/27/29/30 settembre e audit 27 settembre. Le sezioni cronologiche vecchie non sostituiscono questo checkpoint attuale.

Normativa: L0 Alignment Matrix v1.7; Source Onboarding v1.6 §§92–92.2 e THS; Semantic v1.3 §§9.2,10–11,17–18; UDP v1.3 §§21–22,109.2,109.6–109.9; Authorization v1.5 §36.10; MCP v1.4; Gateway v1.5. Gateway prescrive confini northbound/southbound distinguibili per route, policy, credenziali, log e zone; il proxy non fa ETL né decisioni di dominio.

Pacchetto letto nella chat: `OUF_Reality_Baseline_Package_v1_7(20261001-185201).zip`, SHA256 `e63df67e8817eec38a9d4b3eb736b020f693b932f3360dc02f4555330f2201ce`; 323 checksum interni verificati senza mismatch. Nel vecchio workspace esistono `baseline/OUF_Reality_Baseline_Package_v1_7/` e `pet-text/`. Possono non sopravvivere alla nuova chat. Verificare disponibilità autorizzata; se mancano, richiedere il pacchetto normativo. Non accedere alla Library di altre chat e non trattare questa sintesi come sostituto PET. Si può proseguire il readback già preparato senza reinterpretare una norma assente.

## 4. Repository, PR, revisioni e CI verificate

Owner GitHub **GioNob**. Pin verificati durante preparazione del presente handoff:

| Repository / PR | Branch / pin | Stato |
| --- | --- | --- |
| ouf-api-gateway [PR56](https://github.com/GioNob/ouf-api-gateway/pull/56) | `codex/semantic-provider-request-boundary`, HEAD `85914e39bd0aa9f8e7a0a0a9d3b9db6007633ff8`, base `codex/consultation-live-c14d3f23` | OPEN DRAFT; 28/28 check runs SUCCESS, push+PR. config-contract 454 passed/64 opt-in skips; native Docker/kernel/TLS/systemd separatamente verdi. |
| ouf-semantic-registry [PR30](https://github.com/GioNob/ouf-semantic-registry/pull/30) | `codex/semantic-provider-workload-auth`, HEAD `c2b4ae5abed1236378c7060b3eb3dac126672cbc`, base `codex/semantic-discovery-jobs` | OPEN DRAFT; 14/14 check runs SUCCESS. Workload OAuth/HTTPS testato; **nessuna immagine staged/built/live provata** per questo incremento. |
| ouf-semantic-registry [PR26](https://github.com/GioNob/ouf-semantic-registry/pull/26) | `codex/r4a-smoke-semantic-inventory`, base main; prima di questo handoff HEAD `ade6315eda1020efe37dbfa0ec6586ed75a720cc` | OPEN DRAFT; coordinamento e procedure. Il commit che contiene questo file aggiorna HEAD; il pin precedente non è l'HEAD finale. |

Riferimenti storici da riconciliare prima di usare/modificare: Semantic PR27 delta RDF già live, PR28 disponibilità Discovery, MCP PR48/Gateway PR55 pacchetto identità. Il tentativo di rilettura di queste quattro PR durante l'handoff ha avuto timeout connector: il loro stato corrente non è attestato qui. Non inferire merge/chiusura/assenza da timeout. Non ricostruire un nuovo motore identità o nuove API Discovery perché la PR non è stata riletta.

Correzioni già sviluppate:

- Source read/search/exact refs Semantic, proiezione MCP `semantic.search`/`semantic.get`, contratto HUMAN consultation distinto da SERVICE read, byte-body fix MCP e RDF asserted snapshot: rollout e positivo HUMAN già provati.
- Discovery già ha API request/status/candidates/providers/adoption governata; riusare, non creare un secondo percorso.
- PR28 corregge provider disabled/nessun provider: nuove richieste 503 `SEM_DISCOVERY_NO_ENABLED_PROVIDER`, queued jobs fail esplicito; un provider realmente consultato senza risultati può invece riuscire. Verificare eredità nel branch PR30 e rollout futuro; il live è ancora e7bc5190.
- Adoption formalizzata scrive `immutable_semantic_snapshot`/`external_semantic_origin`; projection RDF imported legge `revision_interchange_snapshot`. Restano da verificare definizioni e snapshot esatti dell'adozione, niente fallback latest. normalized_payload candidato `{}` e projection metadata insufficiente non diventano mapping completo per sola connettività.
- Test-only Gateway `8b1fadb31060cce4deaf3962691aa0aaf17f5865`: tamper MAC deve decodificare, flip byte e ricodificare; cambiare solo padding Base64 non garantiva alterazione MAC. Non revertire né ricompilare container per questo test.

## 5. Baseline live e preparazioni target da riusare

### 5.1 Container produttivi e policy

| Ruolo | Revisione live / digest |
| --- | --- |
| Semantic `ouf-semantic` | `e7bc5190f9e6afbbc4cf3c90d5d4970afbfad14b`, `sha256:f6525f2512c72a600ebcbc7060d55355d86e0627487b655e7c5c6288a0be7fc6` |
| MCP `ouf-mcp` | `394b4b1540b575564f0ba58541df9d7efc59fb87`, `sha256:99a158f780243b3fa05199bed9db01197be8ae60ae1e75ad5432964509422872` |
| Gateway `ouf-apisix` | APISIX **3.18.0**, image `sha256:84e6b5e787e9f889ebff88161cb9a16599bafcffa236c6b54c7f779a0655940d`, c14d3f23-derived routes |
| Onboarding | `6340d5bf120e09b47c32177656e2c377a4c03640`, `sha256:ec6f2a962261a8433bfe103347afa2202837fcec90d210d9b5232711b854ee8a` |
| Ingestion | `163c167d09b8371ff7a62ce7068e9d485b6969b7`, `sha256:b07a4a786ca48335feae887e18dc7c4c6cdd9bd0a3a255f83d18c7c1616eec48` |
| UDP | `83249a897eb4add4289b5181b3299f48ea4c0f99`, `sha256:5e048a859716d6674355e72238f03f899abd705a943ceadbdc5c8863d28f4e9f`, Flyway34 |

Last observed IDs: live Gateway `dcbe26bed97dd5c7ac8a131ec2badf77b0291c2ef32907be639bfa09c36596d9`; Semantic `7ae83be8c1fe9fe25774b7d748e35153652b29b2501886f89daeabb83bd1a147`; Ingestion `1fa5450574e72ef15ebb2c74e0f421f04d24c842975e324ac958f071672fbb7e`. These are readback bindings, not permanent role defaults. Other shared infrastructure (Caddy, etcd, Keycloak, MinIO, Postgres, operational owner) was not switched in the provider preparation.

Authorization remains **ouf-lab-authorization:38**. Historical :36 recovery grants expired; don't reuse them. `gateway.southbound.invoke` and `ouf.semantic.discovery` scopes exist/no drift; only `gateway.southbound.invoke` DEFAULT-bound to **ouf-semantic** SERVICE. Discovery scope not client-bound/descriptor not registered or published at last inventory. Provider disabled, live workload/provider OAuth configuration uninstalled, worker enabled, queue/adopted/unexpired counts zero at inventory. HUMAN discovery/MCP binding and live provider connectivity unproven.

Calling workload: `ouf-semantic` existing confidential service account. Private credential `/etc/ouf/semantic-provider-auth/client-secret`, UID/GID10001,0600; prepared/verified, no rotation. RS256/JWKS signature, SERVICE claims/tenant/audience/TTL299 verified; introspection inactive was corrected by signature verification. Revocation and Gateway admission not proven; no mount on live Semantic.

Passive OIDC validator: **ouf-api-gateway**, enabled/confidential/client-secret, **serviceAccountsEnabled=false**. It validates bearer/JWKS; do not enable service accounts or invent a second M2M identity. Validator credential is distinct from caller credential. Successful master login administrative user **oufadmin** was explicitly observed; SSH user alone is not evidence of KC identity. Session may expire; the §6 inventory does not use kcadm.

Issuer `https://auth.ouf-lab.it/realms/ouf`, token endpoint `/protocol/openid-connect/token` under issuer; MCP execution `https://api.ouf-lab.it/internal/capabilities/v1/execute`. These are explicit lab configuration only.

### 5.2 Receipt roots — absolute paths are host bindings, not defaults

All roots below are under `/etc/ouf/deploy-snapshots/`; keep private root ownership/modes and referenced cohorts. Preparation flags describe time of receipt, not current mounts after creation.

| Preparation | Exact receipt relative to parent | Proven / residual |
| --- | --- | --- |
| Adapter image | `semantic-provider-adapter-20261002-173408/stage-receipt.json` | image `sha256:a697bf75bf7d51afadadfaccd3d80537e9a5fb2a08f0d194c6dfd9462e812468`, source `52c0dcf11654a4d3d0f17a6902ed095975466fb9`, UID10006; now created stopped, no rebuild. Base `python@sha256:bb2988715db2cf7ace7b53f38f3cffbef7c7046a656bee66245eb0ed386e2e81`. |
| Trust PKI/MAC | `semantic-provider-trust-20261002-212033/trust-receipt.json` | CA/public-root merged bundle/role leaves/purpose MAC pair verified. Offline ca.key never mounted/read by launch; role files individually RO mounted on stopped candidates. |
| Runtime plan | `semantic-provider-runtime-20261002-222530/stage-receipt.json` | root-private binding.json/runtime-plan.json compiled; native runtime activation not proved. |
| TLS startup | `semantic-provider-tls-runtime-20261002-230418/tls-runtime-receipt.json` | config.yaml/apisix.yaml/adapter.json prepared, now mounted RO on stopped candidates. apisix.yaml includes private leaf key: never cat. |
| Java trust | `semantic-provider-java-trust-20261003-061729/java-trust-receipt.json` | merged public roots preserved for selected old Semantic image; private PKCS12/JVM options UID10001, no private keys. Not mounted on live Semantic. Recheck public roots for future selected PR30 image. |
| DNS observation | `semantic-provider-dns-20261003-063746/dns-receipt.json` | Historical only, one address observed, **no kernel lease**. Expired observation must never seed runtime sets. |
| Cold networks/guards | `semantic-provider-networks-20261003-072023/prepared/network-receipt.json` | Two dedicated networks + owned inet/bridge deny-only tables installed. Candidate configuration now exists: old EMPTY predicates are historical. |
| Lease source package | `semantic-lease-package-20261003-075940/source-package-receipt.json` | Nine sealed files staged, no daemon/unit installed or started. Reuse frozen cohort. |
| Boot stage | `semantic-boot-guard-20261003-083310/boot-stage-receipt.json` | Sealed deny-only restore profile, unit and Docker drop-in. |
| Boot installation | `semantic-boot-install-20261003-103547/install-journal.json` | Plan/apply/verify PASS, loaded guard/drop-in, Docker PID1740 preserved, no restart/rule/provider call. Real reboot unproven. |
| Candidate-input inventory | `semantic-candidate-inputs-20261003-111502` | Original false block retained; corrected inventory-public-trust-fix.py PASS. Do not reuse bad original inventory.py. |
| Validator credential | `semantic-southbound-validator-20261003-114001/prepared/credential-receipt.json` | Existing secret private copy636:6360600, current profile/secret verified; no rotate/config/grant. |
| Launch inputs | `semantic-provider-launch-inputs-20261003-124906/prepared/launch-input-receipt.json` | Leaf key pairs/receipt MAC pair verified, root0600 southbound.env created; no offline CA key read; no grants/providers. |
| Stopped manifest | `semantic-provider-candidate-manifest-20261003-130410/prepared/stopped-manifest.json` | Sealed exact images/mounts/network/IP/resource specs; initial no-container/no-reservation state historical. |
| Static IPAM | `semantic-provider-static-ipam-20261003-133526/prepared/ipam-receipt.json` | Target accepted never-started disposable static create on all THREE existing networks; probes removed; no address reservation/packet proof. |
| Actual stopped creation | `semantic-provider-stopped-create-20261003-135106/prepared/creation-journal.json` | Two actual candidates, owned transaction/manifest labels, never started, checked strict config/env/RO mounts/net IDs/static IP config. This is latest target PASS. |

Metadata pitfall resolved: public trust-bundle.pem225117 bytes/root644 was incorrectly subjected to 131072 private-JSON cap. Only public CA/trust bundle cap raised to1MiB; private JSON/ownership/mode/link/ancestor checks preserved. Correct inventory source840abe...; no chmod/chown of valid artifacts needed.

IPAM pitfall resolved: one CI daemon rejected static IP on an auto-allocated subnet. This did NOT prove the target incapable. Target Docker29.8.1 positively accepted static create on backend/internal/egress. **Do not recreate/normalize these networks, rebind boot guard or restage all artifacts for that old inference.** Do not infer causality from daemon version alone; evidence is the target probe.

### 5.3 Source pins for frozen helpers

| Helper | Source commit | SHA256 |
| --- | --- | --- |
| create_semantic_provider_stopped_candidates.py | `93e861fe8c8a43912f0cb78a74adceb2db509dd9` | `4babe7ebfdffe6ef1ab4f81bacad52c86eabbbe991d30bf3c41de65d7f47ffdd` |
| stage_semantic_provider_candidates.py | `9596f450ccb2ee38730b147e22e58ceaafd52841` | `cb04a31e4d13e182b08de2df75fa13a4ec01a7c0671239339451523f2dfc9f84` |
| prepare_semantic_provider_launch_inputs.py | `732d65a8bcebb1545086702da54ee01c01c3b823` | `4a5483d5ff54bdc79ef26e4ae436ac41ebd12363be0640005d1d6f695df93e8d` |
| prepare_semantic_southbound_validator_credentials.py | `faaf43748648207f51edee890be4b3dc6592cfc5` | `3d349fd816c1c04091daada0c20eefae7b41396230e89fb7dcc46cb427aace31` |
| inventory_semantic_provider_candidate_inputs.py | `840abe970bde4ab1edc1c6aeecd84eee9d1fc5a8` | `7bbf6a50722f475323b33568e3bc875b57d7f3e3de78d62c8f7410442c48c6c9` |
| inventory_semantic_provider_static_ipam.py | `8c04d8fb6dd251407e8c86c583d40b53a66f1179` | `426d3aab4c05bb24a46b2c41279a6f6fc847b85d3fc6c2954d236200a4cc68a3` |
| inventory_semantic_provider_guard_custody.py — target PASS | `85914e39bd0aa9f8e7a0a0a9d3b9db6007633ff8` | `fabd47c6ce8919bc7a910cbaf63f66f1fb786b00c239ae41757c1fd0df829b8d` |

Frozen lease cohort source `7a81cc344b513d04fd276cd1923a9c23197aceee`: scripts stage_semantic_lease_package.py/run_semantic_provider_lease_owner.py/prepare_semantic_provider_trust.py; tools materialize_semantic_lease_service.py/materialize_southbound_kernel.py/materialize_southbound_lease_refresh.py/semantic_provider_dns.py/semantic_provider_lease_owner.py/semantic_provider_lease_nft.py. Nine root0600 files in source/scripts and source/tools; no daemon/API started.

Boot stage source `d7f65fc73a6beb0a36e77972301a4c823fe21c5d`; installer `39923852d93a3b0907edce91cf87e9386b11621b`. Host source files and artifact hashes are bound by receipts. Do not mutate frozen cohorts in place.

### 5.4 Network/trust/runtime facts

Host rootful Docker29.8.1, systemd257, Python3.13.5, nftables1.1.3. Paths `/usr/bin/docker`, `/usr/bin/python3`, `/usr/sbin/nft`, `/usr/sbin/ip`, `/usr/bin/systemctl`, `/usr/bin/openssl`; Keycloak `/opt/keycloak/bin/kcadm.sh` in ouf-keycloak.

| Network | ID | Binding |
| --- | --- | --- |
| ouf-backend | `113b5f0a3c53059b087a2ce997d2670cc057e88c0c17d4291b3b41a51ce26ba3` | internal, br-113b5f0a3c53,172.18.0.0/16,gateway172.18.0.1,v4 |
| ouf-gateway-control | `1209d67944755d95601b96719c0a5b1860ac2a6f137c10077da7b4e9967637aa` | internal,br-1209d6794475,172.20/16,v4; shared |
| ouf-semantic-provider-internal | `2a6652422b45db6f359d94d779ab8625b1ad99b1750bb54582b4b8c4e8aa9307` | bridge oufsp-int,internal,v4,172.21.0.0/16,gateway172.21.0.1 |
| ouf-semantic-provider-egress | `db8bc9f8feccc3c14f2818a5c843f5c08e5eb2e192530858d88a70ce1cc0a86d` | bridge oufsp-egress,non-internal,v4,172.22.0.0/16,gateway172.22.0.1 |

Owned **inet + bridge table ouf_sem_provider**, currently **deny-only**, no provider sets/flows/lease installed. Never DROP the entire shared backend/control network. Original topology snapshot hash `8b0eb1c691a5010f98f22e34bb3de8de0b65cf8f9bab3079fc6c193778b857d4` is historical, not an atomic current state proof.

Southbound candidate primary backend, secondary provider-internal + provider-egress; adapter primary provider-internal + provider-egress. Planned static addresses in private manifest/journal, not inferred as allocated while stopped. Both restart=no/capDropALL/no published ports/512MiB memory and same swap limit/pids128/no healthcheck; adapter read-only root, APISIX root writable; exact individual RO mounts. Created Docker endpoints can defer NetworkID until start: helper binds current network name→ID separately and checks IPAMConfig rather than claiming packet proof.

Selected lab DNS resolvers `46.38.252.230`, `46.38.225.230`, UDP/TCP53. Supplied IPv6 `2a03:4000:0:1::e1e6` deferred; current profileIPv4 only. Provider `https://schema.gov.it:443/sparql`; namespaces https://w3id.org/italia/ont/ and controlled-vocabulary/. No arbitrary chatbot SPARQL/provider URL.

Southbound TLS-only10443/SNIouf-semantic-southbound, no HTTP/admin/control/extra-metrics listeners. Adapter9443/SNIouf-semantic-provider; POST `/internal/providers/schema-gov/search`, GET `/internal/providers/schema-gov/fetch`. Adapter worker4/deadline20/providerTimeout10/maxRequest65536/maxResponse8388608/maxIntent2000. TLS cert/key/purpose MAC paths under `/run/ouf-semantic-provider/`, upstream CA/trust-bundle.pem. Separate purpose-bound receipt MAC, not OAuth/delegation key. Issuer/audience/service workload/tenant/scopes bound by private plan. Northbound Gateway env must not be copied wholesale into southbound.

Boot guard installed targets `/etc/systemd/system/ouf-semantic-boot-guard.service` and `/etc/systemd/system/docker.service.d/90-ouf-semantic-boot-guard.conf`. DefaultDependencies=no, after local-fs/nftables, before Docker; Docker Requires/After guard and **ExecStartPre validates every start**. Existing tables must match; both absent can restore strict-create; partial/foreign tables block. Original installer verifies Docker PID preservation, not a permanent verifier after a legitimate restart/reboot. Current expected PID1740 is intentional custody binding; any later change requires reconciliation, not silent adoption.

### 5.5 Already proven native tests — don't rerun indiscriminately

- Real nft/netns default-deny and expiry rejecting new **and established** packets,9 host tests PASS.
- Real Docker bridge native hook + scoped host forward, default-deny/unregistered workload/expired leases, own cleanup,1 host test17.521s PASS.
- Real APISIX3.18 CI OIDC → purpose receipt → adapter TLS, forged/direct/incomplete TLS+HTTP and wrong-hostname/SNI/plaintext denials.
- Boot/systemd native CI restore/dependency/foreign/partial recovery, no Docker restart/PID change. Actual host boot install PASS; **real reboot not proven**.
- Target embedded DockerDNS fixture at `semantic-docker-dns-20261003-105129`: source `b4c2faefb7a526c3455632212275633c60d826e7`; UDP/TCPA+AAAA, forwarded source bound to container, selected resolver/default deny/unregistered denial/flow removal, shared structure unchanged, own cleanup,15.661s. **provider0/externalDNS0**; isolated fixture, not production packet acceptance.
- Real Docker stopped-create tests4 and target static-IPAM admission tests4, plus root role-owned launch/trust/credential fixtures in CI. Target creation itself now PASS.
- Current custody helper7 fixture tests pass; native jobs inherited unchanged are green. **Custody inventory target PASS ora registrato nel checkpoint corrente; intent target ancora pendente**.

## 6. Comando custody storico — ora eseguito con PASS

Questa è la riproduzione completa dell'ultimo comando proposto. Fa download checksum-pinned e installa un nuovo helper root0600 in snapshot privato, poi legge stato Docker/reti/nft/systemd e ricevute. **Nessuna IAM/DNS/provider call, nessuno start o cambiamento container/regole/route. Non necessita refresh kcadm.** L'utente ha esplicitamente rinviato l'intero blocco alla nuova chat.

```bash
(
set -euo pipefail

OUF_CUSTODY_DOWNLOAD=$(mktemp)
trap 'rm -f "$OUF_CUSTODY_DOWNLOAD"' EXIT

curl --fail --silent --show-error \
  https://raw.githubusercontent.com/GioNob/ouf-api-gateway/85914e39bd0aa9f8e7a0a0a9d3b9db6007633ff8/scripts/inventory_semantic_provider_guard_custody.py \
  -o "$OUF_CUSTODY_DOWNLOAD"

printf '%s  %s\n' \
  fabd47c6ce8919bc7a910cbaf63f66f1fb786b00c239ae41757c1fd0df829b8d \
  "$OUF_CUSTODY_DOWNLOAD" | sha256sum -c -

OUF_CUSTODY_ROOT="/etc/ouf/deploy-snapshots/semantic-provider-guard-custody-$(date -u +%Y%m%d-%H%M%S)"
sudo install -d -m 0700 -o root -g root "$OUF_CUSTODY_ROOT"
sudo install -m 0600 -o root -g root \
  "$OUF_CUSTODY_DOWNLOAD" "$OUF_CUSTODY_ROOT/inventory.py"

sudo /usr/bin/python3 -B "$OUF_CUSTODY_ROOT/inventory.py" \
  --manifest-root /etc/ouf/deploy-snapshots/semantic-provider-candidate-manifest-20261003-130410/prepared \
  --creation-root /etc/ouf/deploy-snapshots/semantic-provider-stopped-create-20261003-135106/prepared \
  --network-root /etc/ouf/deploy-snapshots/semantic-provider-networks-20261003-072023/prepared \
  --boot-stage-root /etc/ouf/deploy-snapshots/semantic-boot-guard-20261003-083310 \
  --boot-install-root /etc/ouf/deploy-snapshots/semantic-boot-install-20261003-103547 \
  --creation-source-commit 93e861fe8c8a43912f0cb78a74adceb2db509dd9 \
  --docker-path /usr/bin/docker \
  --nft-path /usr/sbin/nft \
  --systemctl-path /usr/bin/systemctl
)
```

Atteso (non ancora osservato sul target): JSON schema `ouf.semantic-provider-guard-custody.v1`, candidateCount2/neverStartedtrue/bootProfileDENY_ONLY/startAuthorizedfalse/kernelLeaseInstalledfalse/bootTransitionRequiredBeforeRuntimeRulestrue, quindi `SEMANTIC_PROVIDER_GUARD_CUSTODY_INVENTORY=PASS`.

Il helper è **custody inventory**, non sostituisce il readback completo config/env/mounts effettuato dal creator. Verifica binding journal/manifest/cold/boot, ID/image/labels/never-started/restart=no, assenza endpoint estranei dedicati, boot files/sorgenti hash, stato systemd/PID/pre-start fingerprint e footprint guard inet+bridge. Non prende lock e non certifica uno snapshot atomico. Se BLOCKED, stampato solo codice generico redatto: diagnosi puntuale read-only, non replay della create né correzione live alla cieca.

## 7. Cosa fare dopo il readback, senza rifare lavoro precedente

1. **Custody e transition intent PASS riconciliati** nel checkpoint corrente: apply/verify runtime §14 sono PASS RUNTIME_EMPTY; readiness §16 PASS; componenti §17 verificati; proseguire dall'integrazione §18 e dai gate §15. I comandi §6, §11 e §12 sono già eseguiti con PASS; non ripeterli come passi autonomi. Non chiamare i vecchi stage/cold verifiers che pretendono nomi assenti/reti vuote. Se drift nel preflight, isolare la differenza conservando journal e container.
2. **Preparare una transizione coordinata** dalle tabelle deny-only al profilo statico/empty provider sets, insieme alla custodia boot/systemd. La precedente incompatibilità del boot guard deny-only è stata risolta dalla transizione coordinata §14; il nuovo guard verifica il profilo runtime vuoto e il journal completo, senza autorizzare startup. Gli helper di staging, guard e transizione sono implementati nel commit Gateway `ef2270a57446da1f23a58548aa4d44920e578fe0`, con journal persistente, fail-closed, recovery/rollback e CI 32/32 PASS. Staging sul VPS PASS al root `semantic-runtime-transition-stage-20261003-160211/prepared`; runtime apply/verify sul VPS PASS RUNTIME_EMPTY; il guard runtime vuoto è installato; compatibilità target/reboot e gate di avvio non sono provati dalla CI. Non alterare gli originali sealed in place.
3. Riusare kernel compiler/lease9cohort. `materialize(..., empty_provider_sets=True)` emette insiemi timeout **vuoti** in inet+bridge; static exact flows per gateway→adapter, DNS e infrastruttura autorizzata. `guardedInterfaces` soltanto dedicate; mai aprire broad egress né scambiare eccezione indirizzo privato per authority. Governare distintamente identity/JWKS e provider esterno. Resolver/endpoint/source/IP/port e private exception espliciti, nessun seed dai vecchi DNS. LeaseOwner query fresh A+AAAA a tutti i resolver selezionati, TTL bounded/tempo sottratto, apply atomico entrambe famiglie/readback, revoca su failure/stop/start. Finite expiry nega anche established.
4. Prima di start/daemon: provare namespace/IP/bridge source binding e confini/pacchetti/DNS/direct bypass/spoof/IPv6 nel perimetro effettivamente scelto. Valutare con attenzione due funzioni diverse di hash: boot footprint elimina handles/metainfo; NftBackend structure hash mantiene metadata/handles e rimuove set elem. Ricreazione tabelle e leases attivi richiedono binding coerenti, non riutilizzo cieco di un expected hash né accettazione automatica di struttura estranea. Non dichiarare supporto reboot sulla sola CI.
5. Quando il piano è concreto e verificato, installare/avviare solo i componenti necessari con procedure governate. La creazione non è autorizzazione startup, la connettività TLS non è IAM admission, il JWT verificato non prova revocation. Provare OIDC/purpose receipt/TLS adapter/hostname, owner diretti negati e workload gateway admission prima di chiamate provider.
6. PR30 Semantic: future build/stage/release con backup/migration-aware history delta. Il branch eredita **V10**, quindi NON usare alla cieca il vecchio helper RDF «migrations identical». Confrontare il truststore pubblico dell'immagine selezionata con il Java trust preparato; se diverso, preparare solo trust appropriato alla nuova immagine. Coordinare config provider/gateway/workload token+mounts; live attuale resta disabled.
7. Attivare Discovery governata solo dopo provider e autorizzazioni pronte: inventariare descriptor actors/operation/purpose; scopes≠capability registration≠policy grant≠route≠MCP discovery. Riutilizzare API asynchronous native con ownership/idempotency/bounds/status/candidate expiry/adozione THS e exact snapshot. `SUCCEEDED` vuoto non prova provider consultato se disabled. Non allargare read receipt in write/adoption authority.
8. Riprendere il mapping Teatri con artefatti adeguati, proposta source/field/identity/classifications/transformazioni/version pins, THS e bundle ACTIVE; collegare file immediate ingestion e API scheduler-before-ingestion, UDP resolution/THS/resume/recovery e Search autorizzato. Poi acceptance per nuovo percorso e secondo chatbot, preservando il resto del backlog.

Reboot/Docker restart del VPS hanno impatto condiviso: non farli per comodità. Se un gate li richiede realmente, predisporre verifica/backup/restore/rollback e finestra concreta prima della coordinazione con l'utente. Nessun reboot/restart è stato eseguito né pianificato come prossimo comando.

## 8. Business evidence congelata e decisioni mapping ancora aperte

### Cinema

Source `managed-cinema-8ec8ae90`, run `86809c17-3354-45ca-a7e6-57e903944b24` SUCCEEDED; otto handoff ACKED/lineage e otto UDP intake PROCESSED/jobsSUCCEEDED/NEW_OBJECT/observations/revisions/bindings/active objects; quarantene recuperate governatamente, audit conservato. Schedule trigger_once consumed/DISABLED. Vecchio `ouf-udp-r4a-smoke` con JAR incompatibile è stato fermato/retained/restart=no; non riavviare. Historical owner causa non provata integralmente.

Semantic artifact `5ae731cc-e4c5-43a3-aa5e-a7576adbd3a1`, semanticId `https://api.ouf-lab.it/semantic/cinema`, revision `51706bed-81e4-4306-aca1-70119821727d`, publication set `f92a2e17-30c9-456f-bb12-63afa84f41e6`, ACTIVEv1. Positivo HUMAN ChatGPT/MCP semantic.get pinned dopo RDF rollout:17 asserted triples,partialfalse,text/turtle,RDF SHA256 `4340986102db6e47345dd8157734d9db83b928edd94485f1b9a5b9e81c497a2e`. JSON metadata hash distinto `78a39fc30dab8bf221bc9eb8c2567bb2abef57e72ba1e4e29a87a23db4142391`. Cinema subClassOf schema:MovieTheater, nome/indirizzo labels/domain/range. Non prova ontology closure/inference o class Teatro; JSON definitions restano vuote. R-SMOKE Search completo rimane aperto.

### Teatri

Account MCP precedente `ouf-admin`, subject `b93d8cf6-cd14-4ee6-91d7-84cd76c4f500`; non confonderlo con master admin/SSH oufadmin. Nuova chat deve seguire account routing connector corrente, non ricostruire link_id. Connector storico `6aafef96b4148191b767e9af7b756a07` è un riferimento, non autorizzazione a presumere sessione o tool attivi.

Picker `b6de7b63-4a1a-47d8-858e-3cc5f0adad51`; asset `6609b245-86ed-4315-8ce0-73f2a8555bf3`; profile job `2f49ea03-b715-493b-ba25-a3f82007cd3d` SUCCEEDED; profile `7984c39c-7396-4248-ab0a-f2efc390b49c`v1. CSVUTF8/semicolon/header1,13rows20cols/ONE_ROW_ONE_SOURCE_OBJECT, proposta PENDING_HUMAN_REVIEW. Nessuna nuova DRAFT/ACTIVE/run/UDP Teatri provata.

Fields: nome_teatro,tipologia,toponimo,nome_indirizzo,civico,cap,citta,provincia,latitudine,longitudine,sistema_riferimento,precisione_coordinate,capienza_posti,spettacoli_stagione,stagione_riferimento,note,fonte_indirizzo,fonte_coordinate,fonte_altri_dati,data_verifica. Non riportare sample raw. CAP inferitoLONG non è tipo semantico/codice preservato; CRS dichiarato non valida geometria. data_verifica≠businessvalidFrom. Multi-hall granularity e provenance per-field da governare. Proposta NATIVE_KEY nome_teatro ancora unapproved: unicità su13righe non prova stabilità e non è chiave canonica. CLASS Teatro/Theatre search[] osservato non è censimento completo. Cinema/MovieTheater non autorizza analogia Theatre. Official vocabulary tipologia/precisione e transformations whitelist da valutare.

Identità: source-row key distinta da canonical UDP identity. Motore class-neutral già nel branch corretto; non riscrivere weighted legacy. Policy proprietà/comparatori/candidate coverage; subset sufficiente concorde anche in entrambe direzioni può MATCH con premesse/unicità; tutti comuni confrontabili diversi→distinct; partial/conflict/missing→incerto. NEW solo allowAutoNew + coverage completa; overflow REVIEW_REQUIRED/RESOLUTION_TOO_BROAD. Score/frequenza/selettività non conferiscono autorità. MATCH non equivale a merge canonico automatico. Review HUMAN/THS non blocca durable ACK/watermark né tiene transazione DB aperta; append-only audit/lineage.

## 9. Backlog ereditato: nessuna chiusura per omissione

| Gate | Residuo / limite della prova |
| --- | --- |
| R-SMOKE completo | Cinema8/8 non basta: Search Gateway/MCP almeno3oggetti, minimizzazione proprietà/oggetto,2pagine,cursor invalid/partial,label/authority/audit. |
| Seconda fonte sovrapposta/identity review | Source distinta con class/candidate overlap, subset entrambe direzioni, concorde/differente/conflicts/missing/authority, disjoint forms,boundedness/overflow/coverage/backfill, THS atomic/resume. Teatri non prova automaticamente questo gate. |
| Gateway managed upload acceptance | Streaming/primi byte,413 oversized senza assetparziale,415,media-type/digest,anonimi,limiti/idempotenza/rollback. Upload/profile reale è solo una parte. |
| MCP/channel neutrality | Secondo host/client senza copia manuale AssetID,login continuity e limiti/adattatori; niente bridge hostfiles arbitrario. |
| Semantic generalità | Exact refs/provenance/DTO/schema/consumer compatibilità, external discovery/adoption snapshot/definitions, class/property/vocab sufficienti, mapping completo. HUMAN read positivo provato soltanto per il path attuale. |
| Data Lake indipendente | Byte/hash/S3 e DB-objectstore reconciliation, backup/restore oggetti. ACK/materializzazione non sono lettura indipendente byte. |
| Replay RAW/SPI | Trasporto/esecutore e RAW durevole. UDP REPRODUCE non sostituisce retry originale/source replay. Nessun replay per chiudere formalmente questo handoff. |
| Lake policy | Retention/access per source/type/zone,enforcement/cancellazione effettiva; no defaults lab universalizzati. |
| R-INSTALL/portabilità | Manifest/secretrefs,bootstrap idempotente capabilities/IAM/Authorization/routes,cleaninstall,upgradeN/N+1,rollback/restore/PITR/reconciliation,macchine/reti/domain/Enti diversi. Le oltre100capabilities devono avere procedura batch/reconcile automatizzabile, non una lunga sequenza manuale ciascuna. |
| Network/TLS/egress | Native fixture/CI PASS nel proprio scope; target provider deployment/boot custody e runtime packets/admission ancora da provare. Real reboot/IPv6/FQDN leases non attestati dal cold stage. |
| Performance/concurrency | Profili/SLO rappresentativi,race lease/rollout/governor multi-replica; fixture vuote non acceptance. |
| Awareness/collectors | Cross-owner raccolta/proiezioni/alert e13marker ING_ACTIVATION_DISCOVERY_UNAVAILABLE da correlare; non dichiarare run riuscito fallito né healthy dalla mancanza log. |
| Latenza ChatGPT–MCP | Correlare host/tool/Gateway/owner; la lentezza chat percepita non prova latenza backend. |
| Cross-module release/branch/PR | Reconcile main/stalebase/live/pin,SBOM/checksum/security/compatibility/consumer schema; workercompatibility generale non divieto arbitrario N/N+1. CI/build/tag/deploy/live acceptance distinti. |
| Causalità storica403/reference | Non integralmente provata; conservare evidenze, niente mutazioni aggiuntive solo per una spiegazione. |

## 10. Checklist di ingresso della nuova chat

- Leggere questo file e il registro ereditato; verificare PET realmente disponibili. Riassumere brevemente obiettivo e ultimoPASS, senza rifare inventario completo manuale.
- Rileggere pin GitHub/PR/CI correnti con connector, senza assumere che HEAD/main/live coincidano. Timeout non è assenza. Niente merge automatico.
- I comandi custody §6 e transition intent §11 sono eseguiti con PASS. Staging §12 eseguito con PASS. Il plan §13 è PASS; apply/verify §14 sono PASS RUNTIME_EMPTY. Non riproporre custody, intent, staging, plan o apply; readiness §16 PASS; componenti §17 verificati; riprendere dall'integrazione §18 e dai gate §15.
- Custody e intent PASS registrati; helper boot/runtime/emptysets con native tests PASS. Staging privato target PASS: apply/verify runtime §14 PASS: riprendere dai gate §15, conservando i gate lease/admission/start prima di attivazione.
- Se serve HUMAN decision/login o SSH reale, preparare prima il risultato verificabile. Non chiedere permessi già conferiti per codice/test/read-only/aggiornamento docs.
- Conservare e aggiornare questo handoff come punto di ingresso insieme ai quattro documenti canonici. Questa chat ha eseguito solo aggiornamenti GitHub nella fase di handoff, non azioni VPS.


## 11. Transition intent privato — ESEGUITO, PASS plan/apply/verify

**ESEGUITO il 3 ottobre 2026 dall'operatore su VPS/sessione SSH oufadmin: PASS in tutti i modi `plan/apply/verify`.** Entrambi i checksum source sono risultati OK. Root attestato: `/etc/ouf/deploy-snapshots/semantic-provider-transition-intent-20261003-151036/prepared`, privato. Boot lock riusato; nessuna regola runtime, unità o container modificata; `START_AUTHORIZED=false`, `PROVIDER_CALLS=0`, `NOT_RELEASE_ACCEPTANCE=true`, `NO_SECRETS_PRINTED=true`.

Il comando sotto è conservato **solo come registro del comando eseguito: non rieseguirlo**. Il prossimo passo pendente è lo staging runtime privato del §12.

```bash
(
set -euo pipefail
OUF_TRANSITION_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_TRANSITION_TMP"' EXIT

curl --fail --silent --show-error --proto '=https' --max-time 30 \
  https://raw.githubusercontent.com/GioNob/ouf-api-gateway/392234edc50c6e8cd19a3028b3e9e19d6f1955b4/scripts/prepare_semantic_provider_transition_intent.py \
  -o "$OUF_TRANSITION_TMP/prepare_semantic_provider_transition_intent.py"
curl --fail --silent --show-error --proto '=https' --max-time 30 \
  https://raw.githubusercontent.com/GioNob/ouf-api-gateway/85914e39bd0aa9f8e7a0a0a9d3b9db6007633ff8/scripts/inventory_semantic_provider_guard_custody.py \
  -o "$OUF_TRANSITION_TMP/inventory_semantic_provider_guard_custody.py"

printf '%s  %s\n' \
  f1cc60568118387cad11a8546f3b0c2c64941c6a51a28611e4c62a009db57422 \
  "$OUF_TRANSITION_TMP/prepare_semantic_provider_transition_intent.py" \
  fabd47c6ce8919bc7a910cbaf63f66f1fb786b00c239ae41757c1fd0df829b8d \
  "$OUF_TRANSITION_TMP/inventory_semantic_provider_guard_custody.py" | sha256sum -c -

OUF_TRANSITION_ROOT="/etc/ouf/deploy-snapshots/semantic-provider-transition-intent-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_TRANSITION_ROOT"
sudo install -d -m 0700 -o root -g root "$OUF_TRANSITION_ROOT/source/scripts"
sudo install -m 0600 -o root -g root \
  "$OUF_TRANSITION_TMP/"*.py "$OUF_TRANSITION_ROOT/source/scripts/"

OUF_TRANSITION_LOCK=$(sudo /usr/bin/python3 -B - <<'PY'
import json
from pathlib import Path
import re
p=Path('/etc/ouf/deploy-snapshots/semantic-boot-guard-20261003-083310/boot-stage-receipt.json')
v=json.loads(p.read_bytes())['profile']['runtimeDirectory']
if not isinstance(v,str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,63}',v):
    raise SystemExit('BOOT_LOCK_BINDING_BLOCKED')
print('/run/'+v+'/guard.lock')
PY
)

for OUF_TRANSITION_MODE in plan apply verify; do
  sudo /usr/bin/python3 -B "$OUF_TRANSITION_ROOT/source/scripts/prepare_semantic_provider_transition_intent.py" \
    --mode "$OUF_TRANSITION_MODE" \
    --source-commit 392234edc50c6e8cd19a3028b3e9e19d6f1955b4 \
    --custody-source-sha256 fabd47c6ce8919bc7a910cbaf63f66f1fb786b00c239ae41757c1fd0df829b8d \
    --manifest-root /etc/ouf/deploy-snapshots/semantic-provider-candidate-manifest-20261003-130410/prepared \
    --creation-root /etc/ouf/deploy-snapshots/semantic-provider-stopped-create-20261003-135106/prepared \
    --network-root /etc/ouf/deploy-snapshots/semantic-provider-networks-20261003-072023/prepared \
    --boot-stage-root /etc/ouf/deploy-snapshots/semantic-boot-guard-20261003-083310 \
    --boot-install-root /etc/ouf/deploy-snapshots/semantic-boot-install-20261003-103547 \
    --runtime-root /etc/ouf/deploy-snapshots/semantic-provider-runtime-20261002-222530 \
    --lease-package-root /etc/ouf/deploy-snapshots/semantic-lease-package-20261003-075940 \
    --snapshot-root "$OUF_TRANSITION_ROOT/prepared" \
    --boot-lock-file "$OUF_TRANSITION_LOCK" \
    --lease-source-commit 7a81cc344b513d04fd276cd1923a9c23197aceee \
    --creation-source-commit 93e861fe8c8a43912f0cb78a74adceb2db509dd9 \
    --expected-manifest-hash 052b46a56ea666971f135c75af48b3342dbeb68e2f17f1f16263a99351df88bd \
    --expected-creation-journal-hash a1c2acd9924fc0f924ded7c2d59f128ef2d8b8dd11c62484a901f628022aaae7 \
    --expected-boot-install-journal-hash 44dfac2145f509c8fb0b66983630616d25958b40f3ffc811074ebb9b3c1edda5 \
    --docker-path /usr/bin/docker \
    --nft-path /usr/sbin/nft \
    --systemctl-path /usr/bin/systemctl
done
)
```

## 12. Staging runtime privato — ESEGUITO, PASS plan/apply/verify

**ESEGUITO il 3 ottobre 2026: PASS plan/apply/verify.** Root privato attestato: `/etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/prepared`. I tre checksum sono OK. Il blocco sotto è registro storico: non rieseguirlo. Il plan §13 e apply/verify §14 sono ora PASS; readiness §16 PASS; prossimo lavoro piano §17, gate §15 aperti. Usare gli helper e i parametri fissati nel checkpoint corrente iniziale e nel runbook Gateway al commit `ef2270a57446da1f23a58548aa4d44920e578fe0`; preparare un nuovo snapshot esclusivo root privato e verificare i tre checksum prima dell'esecuzione. Modi `plan/apply/verify` dello staging: scrittura di soli artefatti privati e compilazione nft in namespace isolato tramite `unshare`; nessuna installazione di regole/unità host o avvio container. Restituire solo output redatto, conservare root/parziali in caso di BLOCKED, non ripetere apply alla cieca. Nessuna transizione runtime host o autorizzazione startup è inclusa in questo passo.

Regola permanente di documentazione: dopo ogni risultato comunicato dall'operatore, aggiornare autonomamente checkpoint, sezione del comando, checklist e prossimo passo nei documenti canonici applicabili. Le procedure superate vanno marcate come cronologia/comandi già eseguiti; un PASS nel checkpoint non basta a lasciare pendente la relativa sezione operativa.

### Blocco staging privato eseguito — PASS

Richiesto dall'operatore il 3 ottobre 2026 dopo l'intent PASS. Eseguire in SSH come oufadmin; non richiede Keycloak. Il root del tentativo viene stampato prima della preparazione per conservare il binding anche in caso di BLOCKED. Nessun installer runtime è invocato. Esito ricevuto: PASS in plan/apply/verify, root `/etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/prepared`, nessuna regola/unità/container host modificata, start non autorizzato, provider calls 0.

```bash
(
set -euo pipefail
OUF_RUNTIME_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_RUNTIME_TMP"' EXIT

for OUF_RUNTIME_SCRIPT in \
  restore_semantic_runtime_boot_guard.py \
  stage_semantic_runtime_transition.py \
  transition_semantic_runtime_guard.py; do
  curl --fail --silent --show-error --proto '=https' --max-time 30 \
    "https://raw.githubusercontent.com/GioNob/ouf-api-gateway/ef2270a57446da1f23a58548aa4d44920e578fe0/scripts/$OUF_RUNTIME_SCRIPT" \
    -o "$OUF_RUNTIME_TMP/$OUF_RUNTIME_SCRIPT"
done

printf '%s  %s\n' \
  cceab662620d1abf97c09be1147c79e4e43022298cb0560dc604ed4bdeb6a606 \
  "$OUF_RUNTIME_TMP/restore_semantic_runtime_boot_guard.py" \
  f88740a293d78906b0a4c8915cc6b760a2dc3f9ab97f110cbb4308e950e519dd \
  "$OUF_RUNTIME_TMP/stage_semantic_runtime_transition.py" \
  a3818878086a40377125816b776606f936ad02496d891f4bc72477c4c731ecf4 \
  "$OUF_RUNTIME_TMP/transition_semantic_runtime_guard.py" | sha256sum -c -

OUF_RUNTIME_ROOT="/etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_RUNTIME_ROOT"
printf 'SEMANTIC_RUNTIME_STAGE_ATTEMPT_ROOT=%s\n' "$OUF_RUNTIME_ROOT"
sudo install -d -m 0700 -o root -g root "$OUF_RUNTIME_ROOT/source/scripts"
sudo install -m 0600 -o root -g root \
  "$OUF_RUNTIME_TMP/"*.py "$OUF_RUNTIME_ROOT/source/scripts/"

for OUF_RUNTIME_MODE in plan apply verify; do
  sudo /usr/bin/python3 -B "$OUF_RUNTIME_ROOT/source/scripts/stage_semantic_runtime_transition.py" \
    --mode "$OUF_RUNTIME_MODE" \
    --source-commit ef2270a57446da1f23a58548aa4d44920e578fe0 \
    --intent-root /etc/ouf/deploy-snapshots/semantic-provider-transition-intent-20261003-151036/prepared \
    --intent-source-commit 392234edc50c6e8cd19a3028b3e9e19d6f1955b4 \
    --intent-source-sha256 f1cc60568118387cad11a8546f3b0c2c64941c6a51a28611e4c62a009db57422 \
    --runtime-guard-sha256 cceab662620d1abf97c09be1147c79e4e43022298cb0560dc604ed4bdeb6a606 \
    --snapshot-root "$OUF_RUNTIME_ROOT/prepared" \
    --docker-path /usr/bin/docker \
    --nft-path /usr/sbin/nft \
    --systemctl-path /usr/bin/systemctl \
    --unshare-path /usr/bin/unshare \
    --python-path /usr/bin/python3 \
    --provider-endpoint-ref schema-gov \
    --resolution-evidence-ref fresh-lease-owner \
    --lease-seconds 30
done
)
```

## 13. Plan transizione runtime — ESEGUITO, PASS

**ESEGUITO il 3 ottobre 2026: PASS MODE=plan STATE=PREPARING.** Start non autorizzato, provider calls 0, Docker non riavviato, non release acceptance, nessun segreto stampato. Il plan ritorna prima della scrittura del journal; PREPARING non attesta apply iniziato. Comando sotto conservato come registro storico, non rieseguirlo. Apply/verify §14 sono ora PASS RUNTIME_EMPTY; prossimo lavoro ai gate §15. Ha invocato soltanto `--mode plan` sullo stage privato già verificato. Rilegge binding, custodia, unità, container e tabelle sotto il boot lock; non applica regole/unità e non riavvia Docker o candidati. Non eseguire apply prima del readback plan. In caso di BLOCKED conservare tutti gli artefatti e diagnosticare, senza replay apply.

```bash
sudo /usr/bin/python3 -B \
  /etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/source/scripts/transition_semantic_runtime_guard.py \
  --mode plan \
  --stage-root /etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/prepared \
  --stage-source-commit ef2270a57446da1f23a58548aa4d44920e578fe0 \
  --analyze-path /usr/bin/systemd-analyze
```

## 14. Apply/verify runtime vuoto — ESEGUITO, PASS RUNTIME_EMPTY

**ESEGUITO il 3 ottobre 2026: PASS MODE=apply e PASS MODE=verify, entrambi STATE=RUNTIME_EMPTY.** Start non autorizzato, provider calls 0, Docker non riavviato, non release acceptance, nessun segreto stampato. Root `/etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/prepared`. Il blocco sotto è conservato come registro del comando eseguito: non ripeterlo. Prerequisiti attestati: intent, staging e runtime plan PASS sullo stesso stage e source. Questo blocco invoca l'installer e cambia le sole tabelle e unità possedute, con journal e daemon-reload, mantenendo Docker/candidati senza restart/start. Il profilo resta vuoto e startAuthorized=false. `set -e` ferma il blocco al primo errore. Non cancellare journal o snapshot; se BLOCKED/interrotto non ripetere apply e riportare output per diagnosi/reconcile/rollback. Esito atteso in entrambi i modi: PASS STATE=RUNTIME_EMPTY; non equivale ad avvio autorizzato o acceptance.

```bash
(
set -euo pipefail
for OUF_RUNTIME_MODE in apply verify; do
  sudo /usr/bin/python3 -B \
    /etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/source/scripts/transition_semantic_runtime_guard.py \
    --mode "$OUF_RUNTIME_MODE" \
    --stage-root /etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/prepared \
    --stage-source-commit ef2270a57446da1f23a58548aa4d44920e578fe0 \
    --analyze-path /usr/bin/systemd-analyze
done
)
```

## 15. Gate successivi dopo RUNTIME_EMPTY — startup non autorizzato

Apply/verify §14 completati. Non ci sono comandi da ripetere. Inventario read-only §16 eseguito PASS. Preparare e verificare il piano per authority infrastrutturale e source-specific shared faces, namespace/live binding, pacchetti/DNS/spoof/bypass/IPv6, admission/TLS/purpose/revocation e transizione del guard empty-only verso lifecycle lease governata. Il template e la transizione vuota non chiudono questi gate. Nessun Docker restart/reboot/provider start/lease activation autorizzato dal PASS RUNTIME_EMPTY. Preservare business evidence, journal e vecchi cohort; aggiornare autonomamente checkpoint e sezioni operative dopo ogni nuovo esito.

## 16. Inventario readiness runtime read-only — ESEGUITO, PASS

**ESEGUITO il 3 ottobre 2026: PASS READ_ONLY=true STARTUP_READY=false START_AUTHORIZED=false.** Source root `/etc/ouf/deploy-snapshots/semantic-runtime-readiness-20261003-165430`. Hash e quantità nel checkpoint corrente. Nessuna chiamata DNS/IAM/provider o modifica rule/unit/container. Il blocco sotto è registro storico, non rieseguirlo. Helper nuovo, source commit `4daad06b71695ad839d1865e55d5aeaf765df861`, hash `ecb0326b9f97f76598d9bad56aa241b01802bf0a601f4eda38fef41fb15c655a`. Il source runtime installato resta al vecchio commit `ef2270a57446da1f23a58548aa4d44920e578fe0`; non confondere i due pin. Non richiede login Keycloak. La preparazione scrive solo un nuovo source snapshot privato; il helper esegue read-only sulle evidenze e sullo stato host, sotto lock già esistente. Non applica nft, non crea journal, non chiama DNS/IAM, non esegue Docker start/exec/restart. Il risultato atteso è inventory PASS con startupReady=false, non startup/admission acceptance. In caso di BLOCKED conservare output/source root e cohort; niente replay runtime apply o reconcile/rollback alla cieca.

```bash
(
set -euo pipefail
OUF_READINESS_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_READINESS_TMP"' EXIT

curl --fail --silent --show-error --proto '=https' --max-time 30 \
  https://raw.githubusercontent.com/GioNob/ouf-api-gateway/4daad06b71695ad839d1865e55d5aeaf765df861/scripts/inventory_semantic_runtime_readiness.py \
  -o "$OUF_READINESS_TMP/inventory_semantic_runtime_readiness.py"

printf '%s  %s\n' \
  ecb0326b9f97f76598d9bad56aa241b01802bf0a601f4eda38fef41fb15c655a \
  "$OUF_READINESS_TMP/inventory_semantic_runtime_readiness.py" | sha256sum -c -

OUF_READINESS_ROOT="/etc/ouf/deploy-snapshots/semantic-runtime-readiness-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_READINESS_ROOT"
printf 'SEMANTIC_RUNTIME_READINESS_SOURCE_ROOT=%s\n' "$OUF_READINESS_ROOT"
sudo install -d -m 0700 -o root -g root "$OUF_READINESS_ROOT/source/scripts"
sudo install -m 0600 -o root -g root \
  "$OUF_READINESS_TMP/inventory_semantic_runtime_readiness.py" "$OUF_READINESS_ROOT/source/scripts/"

sudo /usr/bin/python3 -B "$OUF_READINESS_ROOT/source/scripts/inventory_semantic_runtime_readiness.py" \
  --stage-root /etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/prepared \
  --stage-source-commit ef2270a57446da1f23a58548aa4d44920e578fe0 \
  --installer-sha256 a3818878086a40377125816b776606f936ad02496d891f4bc72477c4c731ecf4
)
```

Output JSON e riga finale ricevuti con PASS e conservati nel checkpoint corrente; sezione del comando, checklist e quattro documenti canonici aggiornati. Il prossimo lavoro è il piano del §17. Le quantità e i purpose stampati aiutano a vincolare il piano successivo; non inventare indirizzi/namespace o authority dalla configurazione pianificata.

## 17. Piano shared faces e lifecycle — componenti software verificati, integrazione aperta

Non c'è un nuovo comando VPS da eseguire in questo checkpoint. Compiler, core di coordinazione e fixture native sono ora implementati e verificati nel commit Gateway `d38289132e49c9e9be4cb6245bb70a63cfaa82dc`, come riportato nel checkpoint corrente. L'integrazione target rimane aperta al §18. Il piano originario richiedeva enforcement del candidato southbound sulle interfacce shared (senza trasformare intere reti condivise in default-deny), anti-spoof/source binding e percorsi workload/identity autorizzati; usare porte e endpoint governati da configurazione, non inferire authority da IP osservati o route. I container mai avviati non forniscono prova di namespace/veth live; le prove isolate devono precedere una procedura target esplicita.

Per il lifecycle attivo servono coordinamento gate persistente/guard/owner con lo stesso lock, fresh DNS A+AAAA bounded per tutti i resolver selezionati, apply/readback atomico inet+bridge, stop/failure/restart revoke e expiry anche su established, binding handle riconciliato esplicitamente e niente auto-adoption di tabelle estranee. Il guard EMPTY_ONLY corrente e il package lease9 restano sealed; non modificarli in place né avviare il vecchio owner per convenienza. Anche un futuro profilo lease-aware non conferisce startup authority. Conservare gate admission/reboot e business acceptance, aggiornare documentazione dopo ogni esito.

## 18. Integrazione prima dell'esecuzione — core install/recovery PASS, hook runtime ancora aperto

I componenti e le fixture §17 sono PASS; nessun comando host da eseguire è ancora predisposto. Il nuovo backend richiede binding di porta/generazione verificato prima che il processo applicativo possa emettere pacchetti. Non fare attach delle regole in risposta a un evento Docker già avvenuto. Il runtime deve fornire un ordinamento sincrono network-before-process con fail-closed su creazione/ricreazione, rifiuto di ifindex riusati o binding incompleto e verifica prima di start. Integrare questo meccanismo e fixture di crash/recovery/port recreation prima del nuovo staging target.

Completare poi nuovo installer sealed/profile migrator, journal e artefatti guard/owner con lo stesso lock, bounded contention, service stop/restart/quiesce, readback/rollback e autorità infrastrutturale. Nessuna auto-adoption del vecchio journal o binding lease; il journal di coordination ha schema nuovo e startAuthorized=false. Non attivare il package lease9 sotto il guard EMPTY_ONLY attuale. Conservare tutti i cohort originali; le prove native nuove sono isolate, non prove di startup/admission del VPS. Aggiornare autonomamente handoff/roadmap/manuale/sprint/PR dopo ogni esito.

## 19. Inventario runtime preexec — ESEGUITO, PASS

Helper verificato nel job CI 111264097837 dell'esatto head Gateway `82d1db716b1015dac52feca217af1c5ed600a520`: 24 test e 3 native PASS senza skip. Suite complessiva verificata sull'esatto head: 34/34 completed/success, nessun pending/failure; prova distinta dalla precedente revisione core. Nessuna prova target inventata.

Questo blocco prepara soltanto un nuovo source snapshot root privato e legge informazioni pubbliche/sanitizzate del runtime locale. **Non cambia nft/unit/container, non registra runtime e non esegue inspect/start/exec/restart/DNS/IAM/provider.** Non richiede rinnovo Keycloak. Se /usr/bin/runc non è il binario disponibile o un dato/metadata non è provato, il helper restituisce BLOCKED con motivo non sensibile: conservare output e source root, non cambiare il daemon e non ripetere vecchi apply. La versione standalone non prova il binario usato da Docker.

```bash
(
set -euo pipefail
OUF_PREEXEC_INV_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_PREEXEC_INV_TMP"' EXIT

curl --fail --silent --show-error --proto '=https' --max-time 30 \
  https://raw.githubusercontent.com/GioNob/ouf-api-gateway/82d1db716b1015dac52feca217af1c5ed600a520/scripts/inventory_semantic_preexec_runtime.py \
  -o "$OUF_PREEXEC_INV_TMP/inventory_semantic_preexec_runtime.py"

printf '%s  %s\n' \
  5caf118353fbb49457ad083bdcf26e778413ba9ea699978ce52465a8480860e1 \
  "$OUF_PREEXEC_INV_TMP/inventory_semantic_preexec_runtime.py" | sha256sum -c -

OUF_PREEXEC_INV_ROOT="/etc/ouf/deploy-snapshots/semantic-preexec-runtime-inventory-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_PREEXEC_INV_ROOT"
sudo install -d -m 0700 -o root -g root "$OUF_PREEXEC_INV_ROOT/source/scripts"
sudo install -m 0600 -o root -g root \
  "$OUF_PREEXEC_INV_TMP/inventory_semantic_preexec_runtime.py" "$OUF_PREEXEC_INV_ROOT/source/scripts/"
printf 'SEMANTIC_PREEXEC_RUNTIME_SOURCE_ROOT=%s\n' "$OUF_PREEXEC_INV_ROOT"

sudo /usr/bin/python3 -I -B \
  "$OUF_PREEXEC_INV_ROOT/source/scripts/inventory_semantic_preexec_runtime.py" \
  --docker-path /usr/bin/docker \
  --runc-path /usr/bin/runc
)
```

Esito atteso: JSON schema ouf.semantic-preexec-runtime-inventory.v1 seguito da PASS READ_ONLY=true OCI_HOOK_INTEGRATION_PROVEN=false START_AUTHORIZED=false. **ESEGUITO, PASS:** output operatore e source root riportati sopra; quattro documenti aggiornati. Non ripetere il blocco storico. Nessuna successiva installazione o applicazione implicita.

## 20. Source package preexec privato — ESEGUITO; plan/apply/verify PASS

Il comando seguente prepara soltanto un nuovo source snapshot. L'apply è **pubblicazione della receipt privata**, non installazione di regole/hook/unit/runtime o start. Non modifica il package lease9, cohort runtime, reti, candidati, daemon Docker o journal già esistenti. Pinna undici file del commit Gateway `1a020edea42cdf60a38298bec2ffebc97b3fad02` e verifica ciascun SHA256 prima di copiarlo in root:root 0600. Il nuovo stager è provato con plan/apply/verify, rifiuto replay e source drift; la prova OCI con runc 1.5.1 è PASS nei due job del checkpoint. Non trasferire questa prova CI al VPS.

Atteso PASS per tutti e tre i modi con PRIVATE_SOURCE_ONLY=true RUNTIME_REGISTERED=false START_AUTHORIZED=false. JSON contiene Python version e disponibilità di strumenti root-owned: può essere PASS anche se busybox/tool opzionali sono assenti, perché il source staging non prova la readiness del runtime. Riportare l'intero output e PACKAGE_ROOT. Su BLOCKED conservare snapshot/output; niente replay apply, rimozione dei cohort o apt/restart per convenienza. Non richiede login Keycloak.

```bash
(
set -euo pipefail
OUF_PREEXEC_PKG_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_PREEXEC_PKG_TMP"' EXIT

cat > "$OUF_PREEXEC_PKG_TMP/sources.sha256" <<'OUF_PREEXEC_SHA'
bf86bc438c39a1f8f7752797110bcfcf18b9e7deb23a662f850fffb900df2fd8  scripts/stage_semantic_preexec_package.py
e904774d50626e3ce93d6bcd187571b03d0698ad6a7472a7b6a862b4816eb850  scripts/semantic_provider_preexec_hook.py
98e3004300226fecd509a46c009585df14021927f20d4e5c82d8ff7a8a8180de  tools/materialize_southbound_kernel.py
1c0d7f1243752fe216ef62eefbc2e3253b8f2503b518fafe11277e4d7721a084  tools/materialize_southbound_lease_refresh.py
c466172113d1ffe850bf2c69762113b55fbc65d9091c96dca98a74548fddf930  tools/semantic_provider_dns.py
7a5f2b21c096228a3e4d298674e380f667c3004dd6d8ec19934a2302844c0f93  tools/semantic_provider_lease_nft.py
92736eebeccf344e565186bce94d29c65ffe1d50638d57eae81486e7b26e884d  tools/semantic_provider_lease_owner.py
b97f31cc17c22abbb7a021c274be73816f649196762f9c6dfcc54a58d8382e8a  tools/materialize_semantic_shared_faces.py
25c6df90d33e39fe83321df6ab9e5c38d4c33bcd290ad57c7a85c03b1bb8ba78  tools/semantic_provider_lease_coordination.py
5086f893ac22e962816e76709883c9c7f341989919339c579a4f28bfbd403804  tools/semantic_provider_preexec.py
c45d343308a311790bcd5c9ed9687925d4af0fec59f96fc79f4af7a685b8c70f  tools/semantic_provider_preexec_native.py
OUF_PREEXEC_SHA

while read -r OUF_PREEXEC_HASH OUF_PREEXEC_FILE; do
  mkdir -p -- "$OUF_PREEXEC_PKG_TMP/$(dirname -- "$OUF_PREEXEC_FILE")"
  curl --fail --silent --show-error --proto '=https' --max-time 30 \
    "https://raw.githubusercontent.com/GioNob/ouf-api-gateway/1a020edea42cdf60a38298bec2ffebc97b3fad02/$OUF_PREEXEC_FILE" \
    -o "$OUF_PREEXEC_PKG_TMP/$OUF_PREEXEC_FILE"
done < "$OUF_PREEXEC_PKG_TMP/sources.sha256"

(cd "$OUF_PREEXEC_PKG_TMP"; sha256sum -c sources.sha256)

OUF_PREEXEC_PKG_ROOT="/etc/ouf/deploy-snapshots/semantic-preexec-package-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_PREEXEC_PKG_ROOT"
sudo install -d -m 0700 -o root -g root \
  "$OUF_PREEXEC_PKG_ROOT/source/scripts" "$OUF_PREEXEC_PKG_ROOT/source/tools"
while read -r OUF_PREEXEC_HASH OUF_PREEXEC_FILE; do
  sudo install -m 0600 -o root -g root \
    "$OUF_PREEXEC_PKG_TMP/$OUF_PREEXEC_FILE" "$OUF_PREEXEC_PKG_ROOT/source/$OUF_PREEXEC_FILE"
done < "$OUF_PREEXEC_PKG_TMP/sources.sha256"
printf 'SEMANTIC_PREEXEC_PACKAGE_ROOT=%s\n' "$OUF_PREEXEC_PKG_ROOT"

for OUF_PREEXEC_PKG_MODE in plan apply verify; do
  sudo /usr/bin/python3 -I -B \
    "$OUF_PREEXEC_PKG_ROOT/source/scripts/stage_semantic_preexec_package.py" \
    --mode "$OUF_PREEXEC_PKG_MODE" \
    --package-root "$OUF_PREEXEC_PKG_ROOT" \
    --source-commit 1a020edea42cdf60a38298bec2ffebc97b3fad02 \
    --hook-source-sha256 e904774d50626e3ce93d6bcd187571b03d0698ad6a7472a7b6a862b4816eb850
done
)
```

**ESEGUITO:** output operatore plan/apply/verify PASS ricevuto; handoff/roadmap/manuale/sprint aggiornati con package root e receipt. Il comando sopra è storico, non da rieseguire. Per il passo successivo restano authority e profilo target/generazione/runtime integration, senza avvii o registrazioni impliciti.

## 21. Inventario runtime/binding dei candidati fermi — NON ESEGUITO; comando di sola lettura

Prerequisiti attestati: §20 ESEGUITO PASS e candidati mai avviati; manifest/creation journal pin agli hash seguenti. Lo snapshot del helper è nuovo e privato, separato dal package preexec sigillato. Il helper non scrive receipt/journal o regole e non interroga IAM/DNS/provider. Nessun login Keycloak necessario. Non verifica l'intera configurazione della creazione né il guard runtime attuale.

Atteso: due righe JSON/PASS con READ_ONLY=true, configuredBindingsMatchManifest=true, candidatesNeverStarted=true, liveNamespaceBindingProven=false, atomicSnapshotProven=false, ociHookIntegrationProven=false e startAuthorized=false. CandidateRuntimes e sandboxKeyPresentCount sono risultati da raccogliere, **non predetti né acceptance**. Su BLOCKED conservare source root/output; niente avvio, registrazione runtime, ricreazione o replay automatico. Riportare source root e intero output redatto.

```bash
(
set -euo pipefail
OUF_CANDIDATE_INV_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_CANDIDATE_INV_TMP"' EXIT
curl --fail --silent --show-error --proto '=https' --max-time 30 \
  https://raw.githubusercontent.com/GioNob/ouf-api-gateway/6e84e5ca1134cd8e26b603380a0adcb06a15fb0c/scripts/inventory_semantic_preexec_candidates.py \
  -o "$OUF_CANDIDATE_INV_TMP/inventory_semantic_preexec_candidates.py"
printf '%s  %s\n' \
  63fb3da6682861cd033c236a2830668bb4648b27ddc139799a05a8c62652f0bb \
  "$OUF_CANDIDATE_INV_TMP/inventory_semantic_preexec_candidates.py" | sha256sum -c -
OUF_CANDIDATE_INV_ROOT="/etc/ouf/deploy-snapshots/semantic-preexec-candidate-inventory-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_CANDIDATE_INV_ROOT"
sudo install -d -m 0700 -o root -g root "$OUF_CANDIDATE_INV_ROOT/source"
sudo install -m 0600 -o root -g root \
  "$OUF_CANDIDATE_INV_TMP/inventory_semantic_preexec_candidates.py" "$OUF_CANDIDATE_INV_ROOT/source/"
printf 'SEMANTIC_PREEXEC_CANDIDATE_SOURCE_ROOT=%s\n' "$OUF_CANDIDATE_INV_ROOT"
sudo /usr/bin/python3 -I -B "$OUF_CANDIDATE_INV_ROOT/source/inventory_semantic_preexec_candidates.py" \
  --manifest-root /etc/ouf/deploy-snapshots/semantic-provider-candidate-manifest-20261003-130410/prepared \
  --creation-root /etc/ouf/deploy-snapshots/semantic-provider-stopped-create-20261003-135106/prepared \
  --network-root /etc/ouf/deploy-snapshots/semantic-provider-networks-20261003-072023/prepared \
  --expected-manifest-hash 052b46a56ea666971f135c75af48b3342dbeb68e2f17f1f16263a99351df88bd \
  --expected-creation-journal-hash a1c2acd9924fc0f924ded7c2d59f128ef2d8b8dd11c62484a901f628022aaae7 \
  --creation-source-commit 93e861fe8c8a43912f0cb78a74adceb2db509dd9 \
  --docker-path /usr/bin/docker
)
```

**NON ESEGUITO sul VPS:** attendere output operatore e aggiornare autonomamente handoff/roadmap/manuale/sprint. Dopo il risultato, definire l'adapter Docker contro il binding osservato, mantenendo separata l'authority di infrastruttura dal semplice inventario.

