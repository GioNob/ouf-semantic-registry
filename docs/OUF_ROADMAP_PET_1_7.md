# Roadmap OUF rispetto ai PET della baseline v1.7

## Checkpoint corrente — preparer e footprint indipendente validati; §23 staging source-only v3 NON ESEGUITO

Gateway PR56 commit `2020a6d274e5a45f1ef0ed2208c2d6acc980342e`, **38/38 CI check completed/success** (push e PR), log delle sei esecuzioni pertinenti letti. Locale: 51 test, 46 PASS e 5 native/Docker opt-in skip. Nuovo job preparer: 8 test unitari/source-package e 2 native senza skip; namespace PREPARED e OCI_CREATED, template isolato con host rules invariati, sorgente alterato negato, preparer sigillato, runc/nft reali, revoca prima del start negata, rollback live negato e cleanup owned. Shared job: 40 regressioni/inventari + 3 native rete/lease + 1 OCI reale senza skip. Docker job: 4 test, named runtime legacy positivo/negative/cleanup/default preservato. Queste sono prove sintetiche CI, non release acceptance VPS.

**Implementazione:** `scripts/semantic_provider_admission_preparer.py`, `tools/semantic_provider_deployment_admission.py`, `scripts/stage_semantic_admission_package.py`. Preparer source-sealed a dodici sorgenti e comandi con hash; intent per CID con intero documento OCI, receipt esterno di creation acceptance, approval esterna per issuer/Ente/installazione/CID/transaction/application/transport/creation hash, ACTIVE e validità massima 300s. Riutilizza soltanto lease custody/journal/common lock esistenti, QUIESCED e provider sets vuoti. Rifiuta NIC non approvate, MAC/IP/bridge/peer/runtime/PID drift. Non emette approval, non interroga IAM/DNS/provider, non è authorization applicativa. Driver v3 ricontrolla approval hash/scopo/expiry sotto common lock prima della release FIFO; v1/v2 restano compatibili. Revoca cooperante deve usare lo stesso lock; mutazioni privilegiate esterne non sono escluse.

**Footprint indipendente:** compilato in un namespace network nuovo con mirror bounded di nomi/indici approvati, non ricavato calibrando regole host. Worker rifiuta namespace del chiamante prima di ogni write. Binding live usa query ai soli indici selezionati, evitando inventari globali di migliaia di NIC. Adapter schema v2 effettua dispatch del preparer/config hash per CID e richiede grant v3/approval SHA corrispondente; un solo runtime/cohort nominato può servire candidati diversi. Dispatch v2 coperto dai contract test; la prova Docker completa resta sul percorso legacy e le prove v3 complete sono runc native. L'integrazione Docker v2/v3 target non è dichiarata provata.

**Recovery:** journal STAGED → PREPARING → PREPARED → PROTECTED → CLEANED; PREPARING/PREPARED interrotti non vengono adottati o ripetuti automaticamente. Cleanup richiede rollback indipendente e morte della generazione registrata anche se non ha raggiunto il hook. Recovery operativo delle fasi incomplete resta esplicito; nessun reset/rebind implicito. La CI ha corretto il confronto atime e una collisione del nome helper; l'esistente provider `tools/semantic_provider_admission.py` è ripristinato byte-per-byte, SHA256 `dca670d1f0ced678db6af9810199da07419901a21523385e0ebea623b608bbfc`. I fallimenti delle revisioni precedenti non sono PASS retroattivi.

**Ultimo VPS invariato:** §22 ESEGUITO plan/apply/verify PASS in `/etc/ouf/deploy-snapshots/semantic-preexec-adapter-package-20261003-213033`, schema v2, source `b5260260fff1adf798626f12e24323c20ae1bb2e`, Python 3.13.5. Adapter/preparer non installati, runtime non registrato, start non autorizzato, regole/unità/container invariati, providerCalls=0. §20/§21 restano ESEGUITI PASS; candidati mai avviati, ultimo guard attestato RUNTIME_EMPTY/EMPTY_ONLY. Snapshot v1/v2 immutabili.

**Prossimo passo preciso che richiede operatore VPS:** handoff §23 **NON ESEGUITO**, nuovo source-only package v3 a quindici file, nuova radice `semantic-admission-package-<UTC>`. Contenuti/hash verificati contro GitHub 15/15 e sintassi bash verificata. Non include fixture, profili, approval o receipt di acceptance sintetici. Atteso schema `ouf.semantic-admission-source-package.v3`, plan/apply/verify PASS e tutti i flag installation/registration/start/rules/units/containers false. Riportare root/output; su BLOCKED preservare tutto, niente replay automatico.

**Gate successivi:** issuer/attestor di deployment realmente approvati, creation acceptance completa e authority infrastructure target, profili e journal/common lock sigillati, compatibilità template/backend VPS, integrazione Docker v2/v3, atomic snapshot, OIDC/purpose/TLS/revoca applicativa, lease attiva e reboot restano aperti. Approval JSON root-private con hash è un artefatto trusted del deployer, non verifica una firma IAM o autentica da solo issuerRef; il produttore approvato deve essere identificato prima dell'uso reale. Migliaia di Enti, host/reti distribuiti e co-localizzazione nella stessa rete/sottorete restano vincoli permanenti; backend bridge IPv4 è una realizzazione, non un default della piattaforma.

## Checkpoint VPS attestato — §22 ESEGUITO; nuovo source package v2 PASS

Output operatore ricevuto il 3 ottobre 2026 alle 23:31 Europe/Rome: **§22 ESEGUITO, plan/apply/verify PASS**. Nuovo package `/etc/ouf/deploy-snapshots/semantic-preexec-adapter-package-20261003-213033`, schema `ouf.semantic-preexec-source-package.v2`, source commit `b5260260fff1adf798626f12e24323c20ae1bb2e`; dodici checksum iniziali OK e dodici sourceHashes attestati, Python 3.13.5. Receipt e flag concordanti nei tre output. Attestazione operatore registrata in `docs/handoffs/receipts/SEMANTIC_PREEXEC_PACKAGE_V2_2026-10-03_OPERATOR.json`; nessuna lettura indipendente del VPS né digest del receipt dichiarati.

**Effetto attestato limitato ai sorgenti privati:** runtimeAdapterInstalled=false, admissionPreparerInstalled=false, runtimeRegistered=false, startAuthorized=false; rulesChanged/unitsChanged/containersChanged=false, providerCalls=0, notReleaseAcceptance=true, noSecretsPrinted=true. trustedToolsAvailable è true per busybox/ip/nft/nsenter/python/runc/unshare e indica solo metadata, non compatibilità funzionale. Package v1 e snapshot precedenti restano immutabili. Il comando §22 è ora storico: non rieseguirlo automaticamente.

**Validazione codice già completata:** gateway `b5260260fff1adf798626f12e24323c20ae1bb2e`, 36/36 CI check success, riconfermati dopo il receipt; Docker adapter positivo/negative/owned cleanup, 38 regressioni/inventari + 3 native rete/lease + 1 OCI reale senza skip nelle rispettive esecuzioni. Locale 36 PASS e 3 Docker opt-in skip. Docker prepara la rete fra NewTask e Task.Start: admission al proprio start verifica CID/bundle/PID/generazione/owned tables/lease prima del rilascio dell'applicazione, mantenendo il common guard/lease lock fino a runc start. Default/cohort invariati; CI sintetica non è acceptance VPS. Ultima documentazione precedente `215e63dfd6e284f0f5be29937f28fe372b71adaa`, CI 13/13 success.

**Custody target:** §20 e §21 restano ESEGUITI PASS; due candidati runc mai avviati e nessun binding namespace live provato da quegli inventari. Ultimo guard attestato RUNTIME_EMPTY/EMPTY_ONLY: questo staging non lo verifica nuovamente né conferisce readiness/authority. Nessuna registrazione runtime, reload/restart, ricreazione, avvio, merge o replay implicito.

**Prossimo lavoro tecnico preciso:** preparer di admission di produzione e compilazione indipendente del footprint, con contratto di approval/authority, binding live e recovery espliciti; la fixture sintetica CI non può essere installata o riusata come preparer di produzione. Usare il nuovo package v2 come radice source-only attestata, senza alterarlo. Prima di qualunque piano di registrazione/start target restano infrastructure authority reale, full creation acceptance, atomic snapshot, OIDC/purpose/TLS/revoca, lease attiva e reboot. Migliaia di Enti, host/reti distribuiti e co-localizzazione sulla stessa rete/sottorete restano vincoli permanenti. Nessun nuovo comando VPS di registrazione/start è autorizzato o presentato da questo receipt.

## Checkpoint precedente — inventario candidati VPS ESEGUITO; adapter Docker da implementare

Gateway PR56 head `6e84e5ca1134cd8e26b603380a0adcb06a15fb0c`. Helper nuovo `scripts/inventory_semantic_preexec_candidates.py`, SHA256 `63fb3da6682861cd033c236a2830668bb4648b27ddc139799a05a8c62652f0bb`. Readback di helper, test, workflow e protocollo su GitHub verificato. Locale: **32 PASS + 2 Docker opt-in skip**, Docker assente nel workspace. **Job dedicati 111284288072 e 111284295941 completed/success**, log letti: ciascuno **34 test (32 regressioni + 2 Docker reali), 3 prove native di rete e 1 prova OCI reale senza skip**; runc 1.5.1. **CI complessiva verificata sull'esatto head: 34/34 completed/success, nessun pending/failure.**

Ultimo intervento VPS §20 **ESEGUITO plan/apply/verify PASS**, undici hash OK; package root `/etc/ouf/deploy-snapshots/semantic-preexec-package-20261003-195926`, source `1a020edea42cdf60a38298bec2ffebc97b3fad02`, Python 3.13.5, strumenti metadata tutti presenti. Il package sigillato resta immutabile, runtimeRegistered/startAuthorized=false e nessuna modifica di rule/unit/container.

**Ultimo intervento operatore: handoff §21 ESEGUITO, inventario candidati PASS; source root `semantic-preexec-candidate-inventory-20261003-203221`.** Il comando pubblica un nuovo snapshot privato del solo helper e legge candidati/reti tramite socket Docker locale, CLI config privata vuota, ambiente minimale e proiezioni allowlist. Lega manifest/creation journal agli hash attestati e network receipt al manifest; controlla custody CREATED/PID zero/mai avviato/restart no, runtime assegnato, network/IPAM/alias configurati, owner/bridge e assenza di membri estranei sulle sole reti dedicate. Due letture concordanti e rilettura dei file attestano stabilità osservata, mai atomicità. Output ridotto a hash/runtime/conteggi, niente Env/mount/comandi/indirizzi o namespace path. Non usa il vecchio inventario DENY_ONLY per accettare il nuovo guard RUNTIME_EMPTY.

**Rischi e decisione documentati prima dell'implementazione:** (1) endpoint configurati differiti non sono namespace live: NetworkID vuoto ammesso con verifica separata del network ID e liveNamespaceBindingProven=false; (2) letture Docker multiple non sono atomiche: drift blocca ma atomicSnapshotProven=false; (3) inspect integrale/ambiente ereditato/output illimitato potrebbero esporre segreti, selezionare host remoto o consumare memoria: proiezioni allowlist, socket locale, configurazione privata vuota, output 128 KiB e deadline totale 30 s. Test negativi coprono start/drift/ownership/IPAM, duplicati JSON, output e deadline; Docker reale prova il helper CLI con due nuovi candidati sintetici mai avviati, ripuliti dopo la prova.

La documentazione ufficiale Docker richiede registrazione esplicita per runtime drop-in runc o integrazione shim containerd: [Alternative runtimes](https://docs.docker.com/engine/daemon/alternative-runtimes/). Decisione ordinaria: progettare un'integrazione nominata e scoped, preservando default/cohort; nessun cambio globale per aggirare binding non provati. Runtime osservato non prova che il gate sia invocato. Il wrapper/shim di integrazione Docker **non è ancora implementato né provato**. Authority reale, binding namespace/PID/veth live, admission OIDC/purpose/TLS/revoca, lease attiva e reboot rimangono aperti. Nessuna registrazione/reload/restart/ricreazione/start/merge/replay impliciti. Topologie distribuite e co-localizzate, migliaia di Enti e assenza di default IP/bridge fixture restano requisiti permanenti.

## Inventario candidati VPS — ESEGUITO, PASS (3 ottobre 2026)

Output operatore ricevuto alle 22:32 Europe/Rome: source root `/etc/ouf/deploy-snapshots/semantic-preexec-candidate-inventory-20261003-203221`. SHA256 del helper OK; schema `ouf.semantic-preexec-candidate-inventory.v1`, **PASS READ_ONLY=true**. Due candidati, candidateRuntimes=[runc], candidatesNeverStarted=true, configuredBindingsMatchManifest=true, configuredNetworkCount=3, sandboxKeyPresentCount=0 e stableAcrossReads=true. Tre reti configurate non implicano tre interfacce live; l'assenza di SandboxKey nell'inspect non prova l'assenza di ogni namespace sul sistema.

| Binding verificato dall'inventario | SHA256 |
| --- | --- |
| bindingHash | `0337655a5c3d6d80653aca363d8479ce10e6d27cde024518060a6c628e542aeb` |
| manifestHash | `052b46a56ea666971f135c75af48b3342dbeb68e2f17f1f16263a99351df88bd` |
| creationJournalHash | `a1c2acd9924fc0f924ded7c2d59f128ef2d8b8dd11c62484a901f628022aaae7` |

atomicSnapshotProven=false, fullCreationAcceptanceProven=false, liveNamespaceBindingProven=false, ociHookIntegrationProven=false, runtimeRegistrationAuthorized=false, startAuthorized=false; providerCalls=0, notReleaseAcceptance=true, noSecretsPrinted=true. Nessuna modifica rule/unit/container attestata dall'operatore. Questa è evidenza del comando di inventario sul target, non una nuova verifica del guard runtime o acceptance di avvio.

**Handoff §21 ESEGUITO: conservarne il comando come registro, non rieseguirlo automaticamente.** §20 resta ESEGUITO PASS, package e vecchi cohort immutabili. Ultimo guard runtime attestato RUNTIME_EMPTY/EMPTY_ONLY; questo inventario non lo aggiorna né lo riconferma atomicamente.

**Prossimo passo autonomo preciso:** implementare e provare in CI un adapter Docker nominato e scoped che colleghi la preparazione del bundle/namespace al gate OCI prima del processo applicativo, con binding indipendente al manifest approvato, common lock e journal di guard/lease. Le prove positive/negative devono usare cohort sintetici separati, coprire create/start/delete e crash/rollback, dimostrare che gli errori del gate impediscano il processo e preservare default runtime/cohort esistenti. Solo dopo codice e CI verificati preparare un nuovo package privato e il relativo piano target reviewable. Non c'è un nuovo comando VPS pronto in questo checkpoint.

**Decisione derivata dall'evidenza:** non costruire un profilo prepared-namespace target da indirizzi soltanto configurati o da un SandboxKey assente, e non assumere che i candidati assegnati a runc invochino il driver standalone sigillato. L'eventuale registrazione runtime, reload e gestione del nuovo cohort saranno azioni target esplicite e separate; nessun avvio, ricreazione, replay o merge implicito. Authority di infrastruttura e admission reale non sono conferite da questo PASS e restano gate aperti insieme a coordinazione lease attiva e reboot. Distribuzione su reti/host differenti e co-localizzazione nella stessa rete/sottorete per migliaia di Enti restano vincoli permanenti.


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

Prossimo lavoro: chiudere i gate residui di authority infrastrutturale, namespace/source/live IP e pacchetti/spoof/direct bypass/IPv6, admission OIDC/purpose/TLS/revocation e lifecycle lease prima di proporre startup. Il guard attuale è empty-only e rifiuta elementi lease attivi: non installare/attivare una lease owner sotto questo profilo senza transizione coordinata e prove. Reboot reale, rollout Semantic migration-aware, Discovery/THS, mapping Teatri e percorso file/API→UDP/Search restano aperti. Nessun nuovo comando VPS/start/restart/reboot è predisposto in questo checkpoint. Main/live software e run business conservati; nessun merge.

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


## Ripresa del 3 ottobre 2026 — custody target ancora pendente

Baseline PET allegata verificata: 323 checksum, zero mismatch; SHA256 archivio `e63df67e8817eec38a9d4b3eb736b020f693b932f3360dc02f4555330f2201ce`. Pin correnti riletti tramite connector: Gateway PR56 `85914e39…` (28/28 SUCCESS), Semantic PR30 `c2b4ae5a…` (14/14 SUCCESS); PR27/28, MCP PR48 e Gateway PR55 sono OPEN DRAFT. PR30 eredita PR28 (ahead3/behind0); main, PR e ultima prova live sono distinti. Registro completo e pin nel [handoff corrente](handoffs/OUF_HANDOFF_2026-10-03_STOPPED_PROVIDER_CUSTODY_NEXT.md).

**Il blocco §6 dell'handoff resta il primo intervento VPS, NON ESEGUITO e senza PASS presunto.** Helper e checksum verificati; nessun login Keycloak necessario. Ultimo target PASS: due candidati CREATED_STOPPED, mai avviati. Attendere l'output redatto dell'operatore prima di ammettere la transizione coordinata boot/runtime/empty sets. Profilo nuovo sealed, journal/lock, fail-closed, rollback dei parziali e hash boot/lease distinti sono precondizioni; nessun helper di transizione o start è attestato qui. Tutti i binding restano parametri. Percorso file immediate ingestion dopo ACTIVE e API scheduler-before-ingestion invariati, con mapping assistito e decisioni THS. Gate ereditati e prove Cinema/Teatri preservati, nessun replay o nuova risorsa.


> **Ripartenza aggiornata — 2026-10-03 16:14 Europe/Rome:** leggere prima il [nuovo handoff completo](handoffs/OUF_HANDOFF_2026-10-03_STOPPED_PROVIDER_CUSTODY_NEXT.md). Ultimo VPS PASS: due provider candidate `CREATED_STOPPED`, mai avviati. **Il comando `inventory_semantic_provider_guard_custody.py` NON è stato eseguito dall'utente**; blocco pinned completo nel §6 del nuovo handoff, nessun esito target da presumere. Gateway PR56 `85914e39bd0aa9f8e7a0a0a9d3b9db6007633ff8`: 28/28 check SUCCESS; Semantic PR30 `c2b4ae5abed1236378c7060b3eb3dac126672cbc`: 14/14 SUCCESS, incremento non deployed. Prima delle regole runtime coordinare boot custody/empty sets; non startare né ricreare le reti, non replay Cinema/Teatri. Cronologia e gate ereditati sotto restano conservati; i pin live e gli stati attuali sono nel nuovo handoff.


> **Ripresa 2026-10-01 20:54:** PET allegati verificati (323 checksum, zero mismatch); [inventario iniziale file → UDP](audits/OUF_FILE_TO_UDP_INITIAL_INVENTORY_2026-10-01.md) acquisito. API Semantic presenti ma ricerca/lettura attuali non forniscono ancora tutto il necessario al mapping pinned; baseline MCP da riconciliare tra managed-file e object-search. Nessun rollout o nuova esecuzione; tutti i gate ereditati invariati.

> **Continuità verificata — 2026-10-01 20:33:** il [checkpoint della nuova chat](handoffs/OUF_HANDOFF_2026-10-01_FILE_TO_UDP_NEXT_SPRINT.md) contiene ora il registro esplicito di tutti i gate ereditati e la regola d'identità concordata nell'handoff 29/09. R-SMOKE completo e R-INSTALL restano OPEN; 8/8 chiude solo consegna/materializzazione della fixture. Nessuna issue si chiude per omissione dal prossimo sprint.


## Prossimo sprint concordato — file → UDP guidato dal chatbot

Checkpoint 2026-10-01 20:24 Europe/Rome: [handoff completo per nuova chat](handoffs/OUF_HANDOFF_2026-10-01_FILE_TO_UDP_NEXT_SPRINT.md).

Ordine dei deliverable: (1) baseline/evidenze dei passi già corretti; (2) consultazione Semantic governata dal chatbot; (3) proposta mapping completa del CSV Teatri già caricato; (4) THS e ripresa da esito persistito; (5) collegamento activation/ingestion/risoluzione UDP e recovery; (6) collaudo E2E/serving e installazione parametrica dei collegamenti.

**Il chatbot lavora al mapping; Onboarding valida/persiste; Semantic governa le versioni; decisioni autoritative restano owner/THS.** Riusare servizi/test/fix e receipt già acquisiti. Nuove prove sui collegamenti, non ripetizione indiscriminata dei passaggi manuali. Nessun nuovo upload o replay della fixture Cinema. PET obbligatori; lacune/ambiguità da decidere con l'utente. Il dettaglio dei deliverable e del criterio di chiusura è nel checkpoint collegato.


> **Stato corrente — 2026-10-01 19:28 Europe/Rome:** consegna e materializzazione **8/8 PASS**; Search/serving, storage indipendente e R-INSTALL **aperti**. PET obbligatori a ogni sprint; ambiguità o lacune normative da decidere con l’utente. Dettaglio nell’ultimo checkpoint R4A.


### 2026-10-01 — Unified403 diagnostics PASS; intake template Lua requires contract correction

Actual operator bundle evidence: runPAUSED/controlVersion1; first404 quarantineRETRY_READY/version1, second403 quarantine2fac075e-0862-4ae6-a799-cf63c41b651b OPEN/version0, both raw_lake_ref_present=false. Ingestion logs403 once and discoveryUnavailable once; UDP/APISIX symbolic error sets empty. APISIX access log collection timed out, so403 origin remains unproven. Token current SERVICE, canonical serviceouf-ingestion, aliases consistent, both intake scopes present, UDP tenant/issuer/audience/envIAM/ACR diagnostic matches. Active policyHTTP200/version35 has each intake SERVICE descriptor and matching unrestricted grant. UDP registry config present, static file count0, loaded in-memory policy unproven. Both route upstream/scopes enabled; plugins client-control,limit-count,openid-connect,request-id,serverless-pre-function,serverless-post-function. These facts rule out the reported simple missing-scope/active-grant diagnostics; they do not prove owner admission.

Static installer inspection identifies a concrete design flaw: intake route generation changed OIDC scope and removed proxy-rewrite but copied complete preflight Lua, potentially retaining another actor/owner/capability contract. Future installer now replaces BOTH serverless configs with reviewed intake guards: rewrite clears client X-OUF-* only (bearer retained); access post runs after OIDC and admits SERVICE only. Owner still independently validates JWT and resource grants. OIDC configuration/client-control/body limits/rate limits/request-ID retained; unknown plugins/bearer-only mismatch rejected. This is generic all tenant sources, not cinema logic. Original live403 causality must be demonstrated, not assumed solely from this flaw.

New scripts/r4a_reconcile_intake_service_guards.py plan/apply/verify handles only the two originally owned routes, requires private original installation PASS receipt/body equality, exact UDP pinned revisionedaba2bff18a2aaf52d1180f21f0e68984cc3437 and unchanged surrounding routes. Plan prints only Lua semantic booleans and proposed scope-preserving change. Apply FIRST probes direct UDP with real source/run plus typeCodeFILE/zoneRAW but intentionally MISSING contentBase64. Pinned RuntimeLakeApi requires owner authorization before input validation, and the missing content fails UDP_LAKE_INPUT_INVALID before lake.store. HTTP400 therefore proves the lake resource admission path for this pinned handler; no S3 content is written. Direct401/403/503/etc stops BEFORE route mutation, localizing an owner/config blocker. Only if direct400 is returned does apply privately snapshot both route bodies, persist intent, PUT canonical guard bodies, verify unrelated routes and repeat the same incomplete request through gateway, requiring400. Failure rolls back only matching owned route bodies; concurrent drift/manual ambiguity retained. Private receipt runtime-intake-service-guards.json supports verify rather than replaying PUT after SSH disconnect.

These are negative intake POST probes, not READ_ONLY HTTP GET; script prints STORAGE_NOT_INVOKED only under pinned missing-content invariant. Authorization logs may append. No IAM/token refresher change, retry/resume/source activation or real ingestion delivery occurs. Handoff resource admission and S3 writes remain unproven. Ten installer tests plus three new guard/probe unit tests PASS locally; no local Lua interpreter or LIVE admission/repair was exercised. Next operator plan/apply tests owner first and may correct gateway guards safely without restarting run. If direct owner denies, do not change grants blindly; investigate loaded SDK snapshot/refresher evidence. Existing broader PET/retention/replay/search/eight-row open items remain OPEN.

### 2026-10-01 — Second failure403 confirmed; unified failure readback replaces fragmented diagnosis

Actual operator SQL: attempt1 ING_EXECUTION_GATEWAY_404, original quarantine7741f1f3-479b-42be-bb0d-a711efb20722 remainsRETRY_READY/version1; attempt2 ING_EXECUTION_GATEWAY_403, new quarantine2fac075e-0862-4ae6-a799-cf63c41b651b OPEN/version0. RunPAUSED, no lineage/handoff or UDP materialization proof. No further retry/resume until403 origin and remaining prerequisites are understood. The original retry authorized the first item; it did not remove history or authorize a newly failed item.

Inspected pinned LIVE UDP source edaba2bff18a2aaf52d1180f21f0e68984cc3437: RuntimeIntakeAuthorization admits SERVICE with configured lake tenant and capability candidate from loaded SDK policy/scopes; require uses ResourceContext ingestion-intake with moduleUDP/sourceRef/jobRef. Existing intake manifest grant resourceType ingestion-intake/moduleUDP is consistent with this contract. That is static evidence, not proof of loaded runtime policy or gateway admission. Gateway403 and owner403 must be distinguished. SDK supports static bundle-file bindings and optional registry refresher; active Onboarding bundle need not equal UDP's in-memory snapshot.

New generic scripts/r4a_execution_failure_bundle.py (--run UUID) performs one READ_ONLY collection: run/control version and both attempt/quarantine reasons/lifecycle versions with raw lake ref presence only; redacted symbolic failure counts from bounded1h Docker logs for Ingestion/UDP/APISIX; bounded APISIX access-log HTTP/upstreamHTTP grouped by known endpoint (no URL query/identity/body/token); workload token expiry/actor/service/alias/scope and UDP tenant/issuer/audience diagnostics; authenticated GET to existing registry-url for active capability/grant diagnostics; supported UDP env/JSON/properties static bundle binding and mounted intake descriptors/grants; route upstream/plugin/scope diagnostics. Each optional section reports unavailable exception type without secret text and continues. Logs are collected before token/config parsing to retain evidence even if bindings fail. No intake POST, S3 write, retry, resume, login or policy mutation. Mounted file is not proof of loaded in-memory snapshot, and aggregate bounded log status is not exact per-request correlation. Full raw logs and payloads are never printed.

The existing cinema smoke readback now automatically invokes this generic failure bundle when delivery/materialization are not proven and run IDs exist. All next downloads must include r4a_execution_failure_bundle.py, r4a_execution_route_inventory.py and r4a_prepare_frozen_compatibility_probe.py; missing dependency reports unavailable rather than hiding base evidence. This implements the requested unified readback; cinema remains a fixture, production mechanisms are source-independent. Five new unit tests cover log redaction, HTTP/upstream status parsing, policy grant diagnostic matching, optional-section failures and stripped empty403 parsing. Relevant execution-script suite18 tests PASS locally (mocked operational flows included); LIVE bundle diagnostics not yet operator-confirmed. Next operator command should run the generic bundle only for existing run, without redoing login or execution. Broad existing PET open items, S3 durability, owner authorization and eight-row/search proof remain OPEN.

### 2026-10-01 — Post-resume execution PAUSED again; stop retry loop and diagnose second attempt

Actual operator execution READ_ONLY readback: sourceACTIVE/frozen hash/publication match; one run86809c17-3354-45ca-a7e6-57e903944b24 isPAUSED with ING_RECORD_QUARANTINED. Attempts2, lineages0, legacyOPEN quarantine count2, handoff/intake/job/decision sets empty, UDP observations/revisions/bindings/active objects0. Delivery and materialization bothNOT_PROVEN. Matching empty handoff ID sets is not successful delivery. Schedule remains correctly DISABLED/once/consumed/publication_enabled. Original quarantine was RETRY_READY/version1 before resume; legacyOPEN count includes such authorized pending quarantine and does not imply two newly unauthorized items. Need latest reason and lifecycle state for both items. Ingestion recent activation discovery unavailable markers3; these cumulative markers alone do not identify this attempt's failure. No automatic-execution/delivery failure markers were printed, which also does not prove success.

Code inspection: CanonicalRecordPipeline persists RAW, NORMALIZED, CURATED before committing lineage/handoff; failures at these steps or contract validation create quarantine and preserve failed attempt. ExecutionGatewayClient has one generic ING_EXECUTION_GATEWAY_<HTTP> code for several endpoints, so HTTP status alone must not be conflated with a unique endpoint. Zero lineages places the new failure before durable stage commit, not necessarily before every S3 write. No raw durable proof can be inferred from zero UDP candidate counts. Next operator evidence should be one targeted READ_ONLY SQL query of processing_attempt joined to ing_quarantine, ordered by attempt_no, printing only symbolic reason/state, lifecycle version and quarantine UUID. Do not submit more retry/resume, reactivate the source, delete receipts or dismiss original history. Use exact new reason to audit affected runtime prerequisites and remaining pipeline boundaries together before another controlled run. Broad S3/intake/search/8-row evidence and all prior PET open items remainOPEN.

### 2026-10-01 — LIVE resume-only PASS; execution outcome awaits readback

Actual operator resume-only completed: RETRY_RECONCILIATION PASS (RETRY_READY/version1, RETRY_POST=false), RUN_RESUME PASS HTTP200/controlVersion1, RESUME_AUTHORIZATION_PROVEN=true. No repeat retry, source reactivation or replay occurred. Wrapper reports INGESTION_RESULT_NOT_YET_VERIFIED=true. Original recovery intent now should be RESUME_CONFIRMED according to successful script flow; private receipt retained. Both HUMAN write paths have durable evidence (retry state readback and resume ownerHTTP200); this does not prove completed acquisition, delivery, S3 durability or UDP materialization.

Next operator action is existing READ_ONLY scripts/r4a_cinema_execution_readback.py, a cinema smoke evidence fixture only. Shared production IAM/routes/recovery implementations remain source-independent. This script validates private activation receipt/frozen owner publication, scopes Ingestion by source/checksum and UDP by matching ingestion run IDs, reports run failure codes/quarantine/attempt/lineage/outbox/intake/job/decision/observation/revision/binding/object counts and recent symbolic failure markers. It distinguishes ACKED matching handoff delivery from PROCESSED/SUCCEEDED materialization and never calls retry/resume. Empty/mismatched evidence must remain NOT_PROVEN. It does not verify search and cross-database reads are not atomic. No schema/API modifications are required for this readback. All prior open items remain OPEN pending operator evidence; do not infer eight-row success from resumeHTTP200. If a new block is reported, diagnose the symbolic reason from the existing run without source reactivation or blind retry.

### 2026-10-01 — Committed retry confirmed; resume-only continuation prepared

Actual operator targeted READ_ONLY SQL returned PAUSED|0|RETRY_READY|1. Retry transition committed despite wrapper HTTP204 parse failure. Run was not resumed. Receipt remains the original private intent, not deleted; original terminal confirmation authorized both actions before intent creation. This establishes durable retry state; do not replay retry. No new ingestion/UDP result proof exists.

Generic recovery CLI now offers resume-only. It authenticates with read scopes plus ingestion.run.resume (no quarantine retry scope requested), matches receipt actor/tenant/run/quarantine/revision, permits only prior retry phases, verifies initial receiptPAUSED/OPEN versions and current owner/API+DB snapshot equals original run plus RETRY_READY/version+1. It rechecks live container and token claims, records RETRY_RECONCILED and BEFORE POST records RESUME_REQUESTED_DO_NOT_REPOST. Exactly one resume POST carries original control version. HTTP200 must return same runRUNNING/controlVersion+1; then records RESUME_CONFIRMED. RESUME_REQUESTED or RESUME_CONFIRMED receipts refuse this path and require GET-only verify. No duplicate retry, SQL lifecycle changes or receipt deletion occurs. Existing direct HUMAN confirmation of retry and resume persists; continuation does not ask a second phrase. Fresh device authentication is necessary because previous process kept token only in memory and terminated; no token is saved to avoid relogin.

Seven local regression/unit tests PASS: realTTY, stripped empty204 and prior action/version tests; new continuation tests verify sole resume action after persisted intent, refusal of ambiguous resume/already-confirmed phases and wrong versions, and preservation of ambiguous intent after timeout. Tests mock transport/owner responses; they are not LIVE resume authorization or ingestion evidence. Next operator resume-only uses existing lab CLI IDs and deployed163c167d09b8371ff7a62ce7068e9d485b6969b7. All broader open work and S3/intake/delivery/eight-row/search proof remain OPEN until actual readback. Even resume PASS establishes API acceptance, not completed ingestion.

### 2026-10-01 — Recovery HTTP204 parser failure after intent creation; do NOT repeat retry

Actual operator next attempt printed private recovery intent receipt then BLOCKED CODE=ValueError. Unlike the preceding TTY failure, this is after receipt creation and may be after a committed retry. Reproduced locally: helper.run returns subprocess stdout.strip(); curl empty204 response originally newline+204 becomes string204; post() raw.rsplit(newline,1) raisesValueError. Previous test incorrectly mocked the unstripped response, missing real helper behavior. Parser now accepts the status-only204 response, and regression tests cover both stripped and unstripped forms. Four tests PASS, including real controllingTTY. This fixes parsing only; it does NOT authorize retry repetition or reconcile the LIVE partial outcome.

Private intent receipt must be retained. No recover rerun, receipt deletion or lifecycle SQL mutation. Expected but UNPROVEN partial state is runPAUSED/controlVersion0 and quarantineRETRY_READY/lifecycleVersion1; the resume call follows retry parsing/readback and was not reached in the reproduced failure. Next operator evidence should be a single targeted read-only SQL join for this run/quarantine (states and versions only), avoiding another login. GET-only verify remains available for full HUMAN/receipt readback. Then implement explicit phase reconciliation and, if retry committed, resume-only continuation with fresh owner checks and intent receipt; never submit retry again. Until actual readback, both successful retry and write authorization remain unconfirmed. Deployment/frozen source unchanged; all delivery/materialization/S3/search proof and broader open items remain open.

### 2026-10-01 — Recovery stopped before confirmation; nonseekable TTY fix

Actual operator recovery attempt reached owner readback runPAUSED/controlVersion0 and quarantineOPEN/lifecycleVersion0, printed source and action explanation, then BLOCKED CODE=UnsupportedOperation before showing the confirmation prompt. Root cause is Python buffered text open('/dev/tty','r+'), which requires seekable stream behavior incompatible with TTY. In the pinned script this failure point precedes exclusive intent receipt creation and both POST calls; no retry or resume was performed by this attempt. Read proof remains PASS; write authorization and execution remain unverified. Do not misclassify this as policy/API failure or change IAM/routes.

Fix uses separate write-only and read-only /dev/tty handles. New local regression exercises a real Linux controlling pseudoterminal (pty.fork), verifies prompt emission and both exact-phrase acceptance and cancellation. Four recovery tests PASS, including prior version/action/redaction tests. No LIVE terminal/write proof yet. Operator may rerun recover with the corrected pinned script: existing receipt guard still refuses any attempted recovery when an intent already exists, and owner/database versions must match the saved read proof. No need to delete receipts or manually adjust lifecycle versions. Exact terminal phrase remains RECUPERO <run UUID>. If another failure occurs after receipt creation, use GET-only verify and reconcile rather than re-POST. Both LIVE loops and ACTIVE source remain unchanged; S3 durability/intake authorization/eight-row materialization/search and broader PET open items remain open.

### 2026-10-01 — HUMAN recovery reads LIVE PASS; versioned retry/resume ready for operator

Actual operator HUMAN read proof PASS through existing shared gateway routes: run GET200, quarantine GET200; runPAUSED/controlVersion0, quarantineOPEN/lifecycleVersion0. Private receipt /etc/ouf/deploy-snapshots/ingestion-human-recovery-read-86809c17-3354-45ca-a7e6-57e903944b24.json. Read authorization is proven end-to-end; write authorization has NOT been tested. No retry/resume occurred. Ingestion LIVE163c167d09b8371ff7a62ce7068e9d485b6969b7 remains the deployed IAM + governed retry release.

New generic scripts/r4a_recover_ingestion_run.py supports recover and GET-only verify. It authenticates HUMAN with read scopes plus ouf.ingestion.quarantine.retry and ingestion.run.resume only in recover mode. It requires root/private receipt safety, pinned live release, existing operator read-proof identity/tenant/run/quarantine context, fresh owner GET and database versions exactly equal to that proof, and initial runPAUSED/quarantineOPEN. Direct /dev/tty confirmation phrase RECUPERO <run UUID> authorizes both versioned API actions and states that execution/UDP delivery can restart. Retry POST uses expectedVersion from owner evidence; HTTP204 then readback must show only lifecycle transition toRETRY_READY and version+1 with run unchanged. Resume POST uses original run control version; HTTP200 response must show same runRUNNING/controlVersion+1. Backend performs the pinned resume preflight and rejects any other blocking quarantine. No source reactivation, replay, SQL mutation, attempt deletion or false dismissal occurs.

Private intent receipt ingestion-human-recovery-<run UUID>.json is created BEFORE retry and updated BEFORE resume with correlation IDs, versions and phases RETRY_REQUESTED_DO_NOT_REPOST, RETRY_CONFIRMED, RESUME_REQUESTED_DO_NOT_REPOST, RESUME_CONFIRMED. Existing intent blocks recover; do not re-POST after network ambiguity or SSH disconnect. Use the same CLI with mode verify (read scopes only) to inspect owner state and saved phase, then reconcile explicitly. HTTP error or context drift stops further writes; a successful retry remains authorized if later resume is rejected. The operational wrapper does not promise raw replay durability; it resumes the paused acquisition pipeline under the original pinned contract, retaining failed attempt history. Three local unit tests PASS covering allowed actions/version payloads/stdin bearer, single-request error handling/redaction and state/version drift. These are not LIVE write or delivery tests.

Operator next: device login and terminal-confirmed recover for run86809c17-3354-45ca-a7e6-57e903944b24 / quarantine7741f1f3-479b-42be-bb0d-a711efb20722 using subjectb93d8cf6-cd14-4ee6-91d7-84cd76c4f500 tenantouf-lab clientouf-human-admin. IDs are CLI smoke arguments only; recovery code is source-independent. Both write authorizations and recovery remain NOT YET operator-verified. Even after recovery PASS, execution, rawS3 durability, UDP intake owner authorization, eight-row observations/revisions/bindings/objects and search remain unverified until explicit readback. Existing broader handoff/PET open items remain OPEN.

### 2026-10-01 — LIVE IAM release deployed; HUMAN recovery read proof is next

Actual operator plan/apply PASS: Ingestion LIVE revision163c167d09b8371ff7a62ce7068e9d485b6969b7, Flyway unchanged14, both loops preserved, quiescent lifecycle snapshots unchanged. Database backup /etc/ouf/deploy-snapshots/ingestion-before-compatibility-24wvedd2.dump was restored to scratch successfully and retained privately. Rollback container ouf-ingestion-iam-rollback-5cbeefee1c65 is retained. Private PASS receipt /etc/ouf/deploy-snapshots/ingestion-iam-release-switch.json. Readiness and 16-second observation passed. Direct protected owner GET without token returned401. HUMAN authorization is NOT YET proven; HTTP401 does not establish policy/grant authorization. No retry/resume/source activation occurred. Workload token was not changed by the rollout script; normal refresher may continue.

Next automation scripts/r4a_verify_human_recovery_access.py is a generic tenant/source-independent GET-only probe with CLI run/quarantine/subject/tenant/client/issuer/audience/API/revision. It authenticates using device login, requests only ingestion.run.read and ingestion.quarantine.read (plus openid), keeps token in memory and transports bearer to curl through stdin, never argv/files. Diagnostic claim checks do not substitute cryptographic owner verification. It calls the two existing shared gateway routes, requires200 and owner response identity/lifecycle versions equal to database snapshot, then repeats snapshot/live container ID checks. No preview/retry/reprocess/resume endpoint is called and no write authorization is claimed. A private receipt records reads and versions under ingestion-human-recovery-read-<run UUID>.json. Read-only means business lifecycle is unchanged; login and authorization audit records may be created normally. Four local unit tests PASS covering response versions, claim diagnostics, GET/secret transport and HTTP error redaction; device login/gateway/owner LIVE read remains unverified pending operator output.

Use existing lab HUMAN subject b93d8cf6-cd14-4ee6-91d7-84cd76c4f500 and client ouf-human-admin, tenantouf-lab, issuer https://auth.ouf-lab.it/realms/ouf, audienceouf-api-gateway. Target run86809c17-3354-45ca-a7e6-57e903944b24 and quarantine7741f1f3-479b-42be-bb0d-a711efb20722 are test arguments only. Expected runPAUSED/controlVersion0 and quarantineOPEN/lifecycleVersion0 are preserved from rollout. The private receipt will provide fresh operator-confirmed versions. Do not paste device codes or bearer tokens in chat. Frozen source remains ACTIVE with unchanged approval/hash/publication. Broader open items, versioned HUMAN retry/resume, S3 raw durability, intake owner authorization, eight-row materialization and search remain OPEN.

### 2026-09-30 — Operator stopped IAM candidate PASS; rollout prepared, not yet deployed

Actual operator candidate preparation PASS: pinned new image built, candidate STOPPED, environment preserved, both loops preserved, migration tree unchanged. Private state /etc/ouf/deploy-snapshots/ingestion-iam-release-prepare.json exists. Live revision remains the old release; workload token was unchanged by preparation; no retry, resume, activation or owner authorization proof occurred.

New scripts/r4a_switch_ingestion_iam_candidate.py provides plan/apply using the private receipt, independent of cinema source identifiers and source APPROVED-only helpers. It rejects running/ready/prefight/draining work, active enabled schedules, queued/running/retry-wait replays and deliverable handoffs. Existing PAUSED runs and active consumed publications are permitted and snapshotted. It compares unchanged lifecycle/control versions, quarantine versions, attempt state, partition checkpoints, lineage counts, outbox and active publications before/after rollout. Cross-database reads are not atomic; quiescence and repeat equality checks are operational guards. Both loops remain enabled. Apply stops old Ingestion, retains private database dump, restores to scratch and checks Flyway history, swaps container names, starts the candidate, checks readiness and protected owner GET without bearer returns401, observes16seconds and checks snapshots/schema/bindings. Old container is retained for rollback; failures use the existing runtime rollback algorithm and never automatically restore the live database. The script does not modify token refresher/IAM policy, resume runs or re-activate sources. Independent periodic token refresh may continue.

Private receipt /etc/ouf/deploy-snapshots/ingestion-iam-release-switch.json records STARTING/PASS/ROLLED_BACK/MANUAL_RECOVERY_REQUIRED. Existing receipt causes refusal, requiring readback after SSH disconnect rather than replaying mutation. Four local prepare/rollout unit tests PASS (properties preservation/conflicts and quiescence, using mocks for database reads); actual Docker rollout, backup restoration and HTTP boundary are NOT yet operator-verified. Required next evidence: operator plan/apply PASS, then real HUMAN read authorization through gateway/owner before versioned retry/resume. HTTP401 for no token alone is not HUMAN authorization proof. CI-green target163c167d09b8371ff7a62ce7068e9d485b6969b7 and frozen configuration remain pinned; previous broader open items and eight-row/S3/intake/search proof remain OPEN.

### 2026-09-30 — External configuration proven; generic stopped IAM release candidate is next

Operator extended READ_ONLY inventory PASS: one SPRING_CONFIG_ADDITIONAL_LOCATION selects only the supported mounted properties file; SPRING_CONFIG_LOCATION and IMPORT are absent. No IAM bindings exist in environment or properties. Both activation and execution remain true, expected live revision matches 0dfab1e7b2253fd939088259ea61754d6e56706c. No live mutation, retry, resume or owner authorization proof occurred.

New automation scripts/r4a_prepare_ingestion_iam_candidate.py builds a pinned revision from the existing stage manifest checkout, verifies repository origin and branch head, requires unchanged migration blob tree against the live revision and Flyway14, then creates a stopped generic candidate. It preserves environment, launch contract, supported host settings and read-only mounts; only the properties mount is replaced with a private copy appending IAM enabled/issuer/audience. Both loops must remain true. Conflicting config selectors, IAM overrides, duplicate or escaped property layouts are rejected without printing values. Image build output and candidate metadata are private under /etc/ouf/deploy-snapshots; receipt ingestion-iam-release-prepare.json is exclusively created. Repeated preparation with a receipt or candidate present stops for receipt review rather than overwriting it. No active-source-specific approval checks, source reactivation, queue mutations or IAM/token changes are performed. Local unit checks pass: exact existing property bytes retained and eight conflict cases rejected. These tests do not exercise Docker, issuer/JWKS or live owner authorization.

Operator next command downloads four dependencies plus the new prepare script and runs it with --revision 163c167d09b8371ff7a62ce7068e9d485b6969b7 --expected-live-revision 0dfab1e7b2253fd939088259ea61754d6e56706c --issuer https://auth.ouf-lab.it/realms/ouf --audience ouf-api-gateway. Candidate preparation is NOT YET operator-confirmed; deployment and HUMAN retry/resume are NOT performed. Do not use old source-APPROVED-only compatibility/loop switch entrypoints for this ACTIVE source. A new rollout must consume the private candidate receipt, back up/restore-check the database, preserve frozen approval and both loops, and verify the protected HTTP boundary before recovery. All previous open items, including S3 raw durability, intake owner authorization and eight-row materialization/search, remain open. This is a shared production mechanism for tenant sources, not a cinema-specific implementation.

### 2026-09-30 — Operator LIVE Ingestion IAM binding inventory

Operator read-only inventory PASS: running Ingestion matches expected live revision 0dfab1e7b2253fd939088259ea61754d6e56706c; activation and execution properties are both true. IAM enabled/issuer/audience are absent from environment and mounted properties; no Spring JSON, command IAM override, direct IAM property environment or properties config import was reported. External Spring configuration environment is PRESENT, so its source must be classified before candidate preparation. This is diagnostic evidence, not proof of the live principal bean or owner authorization. Routes and published policy remain installed; workload token, IAM, runtime and queues were unchanged. Retry and run resume were NOT performed.

Next: rerun the extended read-only IAM inventory to identify one supported explicit mounted properties source without printing selector values. The classifier accepts only a single SPRING_CONFIG_LOCATION or SPRING_CONFIG_ADDITIONAL_LOCATION pointing to file:/run/secrets/ingestion-summary.properties (optional: prefix allowed); other layouts require review, not removal of configuration. Seven local classifier checks pass; no live configuration loading or authorization was tested locally. The CI-green IAM + governed retry release 163c167d09b8371ff7a62ce7068e9d485b6969b7 remains NOT DEPLOYED. A stopped candidate must preserve existing external configuration and both enabled loops. Production support is shared across tenant sources; cinema remains test data. S3 durability, intake owner authorization, HUMAN recovery authorization, retry/resume and eight-row UDP/search evidence remain OPEN.

## 2026-09-30 — Four recovery routes VERIFIED LIVE; Ingestion principal adapter CI all green, not deployed

Actual operator READ_ONLY route readback PASS: saved receipt PASS, RECEIPT_MATCH=true, ROUTE_COUNT=4, EXISTING_ROUTES_PRESERVED=true. This resolves the uncertain SSH result; do not rerun installation. Control-plane route state verified, no live HUMAN owner authorization proof. Policy35 remains 42 capabilities/83 grants; four HUMAN scopes OPTIONAL on ouf-human-admin already verified. No retry/resume; source ACTIVE/run PAUSED/quarantine OPEN remains checkpoint.

Ingestion branch `codex/r4a-governed-record-retry` now has tested release commit `163c167d09b8371ff7a62ce7068e9d485b6969b7`, superseding retry-only `759d916cc9a45a39e9be0156f54677225a172e1f`. Implemented IngestionIamSecurityConfiguration with Spring OAuth2 resource server, Nimbus HTTPS issuer discovery/JWKS signature verification, issuer/timestamp validators, required expiration and audience. Only signed claims form TrustedPrincipal on final servlet request after SecurityContextHolderAwareRequestFilter. HUMAN_USER normalizes HUMAN; malformed actor/subject claim conflicts fail; SERVICE/AI_AGENT require workload client identity and conflicting client_id/azp rejected. Client identity/capability headers ignored. Existing SDK remains unchanged and independently evaluates policy capability, scope/grant/resource/tenant. IAM disabled/missing enablement denies protected API namespaces; no fallback generated login. Health and outgoing worker execution remain independent. No Flyway migration or frozen/source config changes.

Runtime bindings to prepare (not yet applied): OUF_ING_IAM_ENABLED=true, OUF_ING_IAM_ISSUER=https://auth.ouf-lab.it/realms/ouf, OUF_ING_IAM_AUDIENCE=ouf-api-gateway (property equivalents ouf.ingestion.iam.*). No source/run hardcoding. Both activation and execution loops must remain enabled, plus existing properties/auth mounts, registry/token refresher and settings. The old live ingestion remains `0dfab1e7b2253fd939088259ea61754d6e56706c`. No new release deployed yet.

Exact final CI verified complete/success for all seven workflows on 163c167d09b8371ff7a62ce7068e9d485b6969b7:
- R4a frozen configuration consumer probe: 36778449732 SUCCESS
- Shared Authorization SDK pairwise: 36778449784 SUCCESS
- R2a Onboarding automatic activation: 36778449742 SUCCESS
- Ingestion Runtime module CI: 36778449726 SUCCESS
- R2c governed publication to historical serving: 36778449744 SUCCESS
- R2e GeoPackage features and governed camera-cabinet relations: 36778449725 SUCCESS
- R2b source to authorized serving: 36778450074 SUCCESS

Module Java/PostgreSQL job 110102186713: 118 tests, failures/errors/skips zero; IngestionIamHttpBoundaryTest six tests PASS (real locally signed RSA tokens verified by Nimbus public key and production validators), RunExecutionWorkerRuntimeTest nine PASS. OpenAPI gate, non-root image/SDK package checks, supply-chain/deployment job110102186468 and database restore drill job110102186749 PASS. First adapter commit db3daa2080b13cf08a073bae6beeef26b91678a0 had six errors from isolated HTTP fixture missing ingestionReadiness; final commit corrects that test fixture and explicitly installs fixture policy into MockServletContext. No production readiness validation disabled. No local Maven available; remote CI is evidence. Public-key fixture decoder stands in for external JWKS discovery in tests, so production discovery/JWKS/network/authentication is still unproven.

New generic READ_ONLY scripts/r4a_ingestion_iam_inventory.py imports only the standalone frozen helper. CLI --issuer, --audience, --expected-live-revision; reads live container metadata and three IAM ENV/property source flags, SpringJSON/external imports/command/direct overrides and both loop property flags. Prints diagnostics only, no config values/secrets, no runtime changes, token changes, policy/IAM or SQL mutation. Local CLI/import PASS, not server binding evidence. Next operator: pin/download this script and r4a_prepare_frozen_compatibility_probe.py; run against expected OLD live revision above, lab issuer/audience. This identifies overrides before preparing a stopped candidate with tested image and explicit IAM settings. Then verify image/revision/dependencies plus actual readiness, backup+scratch restore/retained rollback, adopt release, prove authenticated HUMAN GETs, only then versioned retry and resume. Do not reactivate the source, reset consumed once schedule, modify lifecycle SQL or retry on old release.

Open proof remains: production principal/JWKS discovery and HUMAN owner access, S3 RAW write durability and UDP intake owner authorization, eight-row delivery/materialization/search, RAW replay SPI readiness, governed per-source/per-zone lake retention/access and broader previous PET/RSMOKE/RINSTALL issues. All code/bootstrap remains production-general; cinema is exclusively the smoke fixture.

## 2026-09-30 — SSH disconnected; recovery route installation success unverified

Operator reports SSH disconnected and output unavailable; recalls PASS markers. Treat installation as UNKNOWN until readback; do not claim four routes installed or rerun plan/apply. The existing exclusive receipt intentionally prevents blind repeats after uncertain results. No evidence of retry/resume; installer never calls recovery APIs.

Generic installer now exposes READ_ONLY `verify` mode. It reads root-owned 0600 `/etc/ouf/deploy-snapshots/ingestion-recovery-routes.json`, reports sanitized receipt status, validates snapshot path under the private root and root-owned 0700 parent/0600 snapshot, verifies receipt PASS and exact four expected bodies/attempted IDs, compares current route bodies and all pre-existing routes against saved snapshot, checks unchanged Ingestion container context and expected active policy/descriptors. It never writes a receipt or marks an ambiguous result successful. Missing/unverified/rolled-back/manual-recovery receipt or drift blocks for reconciliation; no PUT/DELETE/POST/retry/resume in verify path. Template mode can also read after receipt exists; plan/apply retain the exclusive receipt guard.

Thirteen local unit tests PASS, including saved PASS acceptance, unverified receipt rejection, route-body drift and prior-route drift; server readback not yet executed. Proposed next: download installer and four helper scripts pinned together, run `verify --tenant ouf-lab --expected-policy ouf-lab-authorization:35`. Output contains no complete receipts, OIDC config, snapshot contents, Lua or tokens. A verify PASS proves route control-plane state and receipt matching only, not live HTTP routing or HUMAN owner authorization.

Production principal adapter work in Ingestion remains blocking before retry/resume (see preceding source review); CI-green retry commit `759d916cc9a45a39e9be0156f54677225a172e1f` alone is insufficient. Preserve both loops and existing frozen activation/run history; no source reactivation, once-schedule reset or lifecycle SQL mutations. S3/intake durability and authorization, eight-row smoke/materialization/search, RAW replay SPI, governed per-source/per-zone lake policies and prior PET/RSMOKE/RINSTALL gaps remain open.

## 2026-09-30 — Template failure identified; explicit HUMAN route guards prepared; owner principal adapter gap found

Operator diagnostic proves exactly KNOWN_PLUGIN_SET=false; every other predicate true. Actual plugins: limit-count, openid-connect, request-id, serverless-post-function, serverless-pre-function; no proxy-rewrite. OIDC enabled/bearer-only and expected config.read scope; exact inline Onboarding and supported public host. Do not drop security functions or permit arbitrary Lua cloning based solely on plugin names.

Gateway primary source review (`GioNob/ouf-api-gateway`, tools/materialize_apisix_runtime.py and materialize_apisix_authorization_runtime.py) shows serverless functions can strip/inject trusted headers, remove bearer tokens or enforce SERVICE identities. The actual live template function bodies were not fetched or classified; no claim they equal any repository example. Installer now accepts their names only because both serverless configurations are REPLACED completely with explicit generated recovery guards on new routes. Rewrite guard clears all client X-OUF-* identity/capability headers while retaining Authorization; access guard runs after OIDC and admits HUMAN/HUMAN_USER only. It decodes claims solely for an additional actor check, not signature validation, and retains bearer for owner verification. Existing template remains unchanged. Request-id and limit-count settings are preserved. Other unknown transforming plugins still block. Exact UUID/action URI conditions, scope checks, private snapshot/receipt, existing-route preservation and conditional rollback unchanged.

Nine local Python structural/unit tests PASS, including other-tenant policy paths, path/action rejection, existing collisions, sanitized diagnostic, replacing owner-specific template functions and preserving rate limit/bearer. Local Lua runtime unavailable; no live Lua/APISIX execution or authorization proof claimed. Plan/apply next on server, followed by owner authentication work before any retry/resume. No policy, IAM or worker mutation by route installer.

NEW blocking production gap discovered in primary ingestion source: trusted-HUMAN controllers call ServletAuthorization.resolve, which requires a TrustedPrincipal on the HttpServletRequest. Repo tree at `759d916cc9a45a39e9be0156f54677225a172e1f` and vendored SDK contain no servlet JWT/identity principal adapter; tests provide fixtures. Therefore the previously CI-green retry commit alone is NOT a sufficient production recovery release. Implement an independently signature/issuer/audience/expiry-validated bearer principal adapter for Ingestion, tenant/actor/scope/authentication-context normalization and meaningful HTTP boundary tests, then rerun CI on the resulting exact release before deployment. Ignore client X-OUF-* and capability headers; do not recreate a trusted principal from unverified payloads or gateway marker headers. Current deployed code remains `0dfab1e7b2253fd939088259ea61754d6e56706c`.

Next operator route install: pinned helper downloads then plan/apply --tenant ouf-lab --expected-policy ouf-lab-authorization:35. This is only routing preparation; owner HUMAN GETs may remain blocked until principal adapter adoption. Required sequence now: complete adapter + CI, prepare verified release/runtime principal settings preserving both loops and frozen baseline, backups/scratch restore/rollback, adopt release, prove HUMAN GET authorization, authorize quarantine retry version0 then resume controlVersion0 after fresh readbacks. No source reactivation, once schedule reset, SQL lifecycle mutation or retry on old release. Source ACTIVE/run PAUSED/quarantine OPEN remains checkpoint. Real S3 durability/intake owner authorization, eight-row delivery/materialization/search, raw replay SPI, per-source/per-zone policies and prior PET/RSMOKE/RINSTALL issues remain open.

## 2026-09-30 — Recovery route plan blocked; targeted read-only template diagnostics ready

Operator reports `R4A_RECOVERY_ROUTES=BLOCKED CODE=RECOVERY_OIDC_TEMPLATE_UNSUPPORTED RETRY=false RUN_RESUME=false`. In installer control flow this is before snapshot/receipt creation and before any route PUT, so the attempt did not install routes. The exact failed template requirement is not yet known; do not guess that bearer mode, plugins or host caused it. Recovery policy35 and verified HUMAN OPTIONAL scopes remain unchanged; source ACTIVE/run PAUSED/quarantine OPEN; live ingestion still old release. No retry/resume evidence.

Installer now has `template` mode, strictly read-only. It selects the actual Onboarding runtime-publication GET OIDC template and prints the same predicates used by installation: enabled, exact inline owner, no references/extra match conditions, OIDC present/enabled/bearer-only, expected scope, known plugin set, host support, plus sanitized plugin names, scope names, bearer-only value type and exact FAILED_CHECKS list. It never prints route bodies, client credentials, serverless plugin code or tokens. Conditions were centralized with no guard weakening. Template mode does not require a published bundle fetch and never calls helper source-specific mains. Eight local tests PASS including failure reporting and secret/code exclusion; local evidence only.

Next operator: download updated `r4a_install_recovery_routes.py` and its four helper scripts pinned together, then run `template --tenant ouf-lab --expected-policy ouf-lab-authorization:35`. No plan/apply retry until diagnostic has been reviewed. Route installation, authorized HUMAN GETs, adoption of CI-tested ingestion `759d916cc9a45a39e9be0156f54677225a172e1f` preserving both loops and backups/rollback, then governed versioned retry/resume remain the sequence. Do not reactivate the source or mutate lifecycle SQL. All prior open evidence remains: S3 durability and intake owner authorization, eight-row delivery/materialization/search, raw replay SPI, per-source/per-zone lake policies, PET/RSMOKE/RINSTALL gaps.

## 2026-09-30 — No inline Ingestion template; generic bounded recovery routes ready

Actual READ_ONLY template inventory: Ingestion running; APISIX HTTP router `NOT_EXPLICIT_OR_UNSUPPORTED`; zero inline Ingestion routes and zero URI candidates for run read/resume and quarantine read/retry. This does not identify the effective router default. No routes, IAM, retry/resume changed.

`scripts/r4a_install_recovery_routes.py` plan/apply uses the installed exact GET `/api/onboarding/v1/runtime/publications` route solely as a verified OIDC template (inline Onboarding, enabled bearer-only OIDC, configuration.read scope, no references/extra match conditions, supported host, known plugin set). It creates an explicit HTTP roundrobin `ouf-ingestion:8080` upstream, preserves OIDC security, removes the complete proxy-rewrite plugin and rejects unknown transforming plugins. It does not call source-specific helper mains. Template and source routing remain unchanged.

Four shared routes: GET `/api/trusted-human/v1/ingestion/runs/<UUID>` scope `ingestion.run.read`; POST same `/resume` scope `ingestion.run.resume`; GET `/api/trusted-human/v1/ingestion/quarantine/<UUID>` scope `ingestion.quarantine.read`; POST same `/retry` scope `ouf.ingestion.quarantine.retry`. Each uses the resource prefix trailing wildcard plus exactly one `vars` rule `["uri","~~","^<resource>/<generic UUID><exact action>$"]`. These are intentional bounded action conditions, not unrecognized template conditions. GET excludes action suffixes; POST accepts only resume or retry respectively, excluding pause/abort/reprocess. No named-parameter router assumption or router configuration change. Official APISIX documents prefix routing and Nginx variable regex rules: https://apisix.apache.org/docs/apisix/router-radixtree/ . Local unit regex tests are not live APISIX runtime validation.

Plan verifies active expected policy and four exact HUMAN READ/WRITE descriptors via published bundle GET, existing route/path/ID absence and owner running. Apply persists a private snapshot and exclusive pre-PUT receipt, rechecks route/policy baseline, installs four routes, verifies exact readback and preserves all existing routes plus owner container identity/config/mounts. Failed apply rolls back only attempted new routes if their bodies still match expected; otherwise requires manual reconciliation. Receipt `/etc/ouf/deploy-snapshots/ingestion-recovery-routes.json` PRIVATE; snapshot under private `ingestion-recovery-routes-*`. Seven local unit tests PASS plus CLI/import; server installation not yet executed. No HUMAN token proof, no Ingestion POST, no retry/resume or IAM mutation.

Next operator: download installer and four existing helpers `r4a_install_runtime_publication_list_route.py`, `r4a_approval_route_inventory.py`, `r4a_execution_route_inventory.py`, `r4a_prepare_frozen_compatibility_probe.py` pinned together; run plan then apply with `--tenant ouf-lab --expected-policy ouf-lab-authorization:35`. Then authorized HUMAN GETs and adoption of tested ingestion revision `759d916cc9a45a39e9be0156f54677225a172e1f` before governed retry/resume. Live code is still old; source ACTIVE/run PAUSED/quarantine OPEN. Both loops, frozen baseline, failed attempt and consumed once schedule must be preserved. Real S3 durability/UDP intake owner authorization, eight-row delivery/materialization/search, RAW replay SPI, governed per-source/per-zone lake policy and all prior PET/RSMOKE/RINSTALL gaps remain open.

## 2026-09-30 — Four HUMAN recovery scopes LIVE verified; route template inventory next

Operator plan/apply/verify evidence confirms all four scope definitions exist with DRIFT=NONE and OPTIONAL bindings on `ouf-human-admin`: `ingestion.run.read`, `ingestion.run.resume`, `ingestion.quarantine.read`, `ouf.ingestion.quarantine.retry`. Each binding has CURRENT_DEFAULT=false, CURRENT_OPTIONAL=true, DRIFT=false, VERIFY=PASS. Definition/assignment steps were executed; no new recovery HUMAN access token or owner authorization has been tested. Recovery policy remains `ouf-lab-authorization:35`, 42 descriptors/83 grants. No retry/resume occurred; no scopes assigned to workload client by this command.

Before installing shared routes, inspect the actual APISIX HTTP router and existing inline Ingestion OIDC template. `scripts/r4a_recovery_route_template_inventory.py` is generic read-only: outputs sanitized route IDs, enabled/OIDC/bearer-only/reference/extra-condition/rewrite/host flags, plugin names and required scopes; reports only an explicit recognizable HTTP router scalar, never guesses a default. Counts matching sample UUID URIs are diagnostic only, not routing/authorization proof. The four routes need distinct exact resource/action matching for any UUID; do not add cinema/run/quarantine-specific routes or widen retry/resume scope to unrelated actions. No router reconfiguration is authorized by this inventory.

Download this inventory plus `r4a_install_runtime_publication_list_route.py`, `r4a_approval_route_inventory.py`, `r4a_execution_route_inventory.py`, `r4a_prepare_frozen_compatibility_probe.py` at one pinned commit; run root Python `-B`. Only stateless helper functions are called, never their source-specific main/approval helpers. No full OIDC route config, admin key, credentials or token printed. Local import and explicit/missing router parser checks PASS; this is not server template evidence. Inventory is proposed next, not yet operator-executed.

Shared routes, fresh HUMAN authorized GETs and the adoption of tested ingestion commit `759d916cc9a45a39e9be0156f54677225a172e1f` remain before governed quarantine retry/run resume. Live ingestion remains `0dfab1e7b2253fd939088259ea61754d6e56706c`, source ACTIVE/run PAUSED/quarantine OPEN. Keep both activation and execution loops, preserved frozen hash, failed attempt and consumed schedule. No reactivation, lifecycle SQL changes or retry on old code. Actual S3 durability, UDP owner intake authorization, eight-row delivery/materialization/search, RAW replay SPI, per-source/per-zone lake policies and existing PET/RSMOKE/RINSTALL gaps remain open.

## 2026-09-30 — Recovery policy 35 LIVE; HUMAN OIDC scope reconciliation next

Operator LIVE publication/readback PASS: `ouf-lab-authorization:35`, 42 capabilities, 83 grants, all previous entries preserved. Four HUMAN-only recovery capabilities and four subject-bound grants cover all tenant sources; no SERVICE grants. Publication receipt `/etc/ouf/deploy-snapshots/ingestion-recovery-policy-publication.json` PRIVATE. IAM, shared routes and workload token unchanged by publication. No quarantine retry or run resume occurred. Do not rerun draft preparation or publication; existing private receipts are recovery evidence.

Next IAM step reuses existing generic `scripts/reconcile-keycloak-client-scope-definition.py` and `scripts/reconcile-keycloak-client-scope.py`: for each scope `ingestion.run.read`, `ingestion.run.resume`, `ingestion.quarantine.read`, `ouf.ingestion.quarantine.retry`, run definition plan/apply/verify, then assignment plan/apply/verify with `--realm ouf --client-id ouf-human-admin --assignment optional`. All four are OPTIONAL and must be explicitly requested by a fresh HUMAN device login; do not bind them to the ingestion workload client or add them to its refresher. Existing helpers use installation `ouf-keycloak` container and already-authenticated kcadm session. Renew the admin session interactively with `sudo docker exec -it ouf-keycloak /opt/keycloak/bin/kcadm.sh config credentials --server http://localhost:8080 --realm master --user oufadmin`; password entered at the terminal only, never argv/env/chat. Pin helper downloads to one Git commit and run Python with `-B`. This reconciliation is the proposed next action, not yet verified operator evidence. Helpers have not changed in this step.

After IAM: shared recovery routes with exact owner path, OIDC scope and upstream ingestion; fresh HUMAN authorized GETs; deployment/adoption of tested ingestion commit `759d916cc9a45a39e9be0156f54677225a172e1f` preserving both activation and execution loops, backup/restore evidence and rollback. Only then versioned HUMAN quarantine retry and run resume. No source reactivation, once-schedule reset or lifecycle SQL mutation. Source ACTIVE/run PAUSED/quarantine OPEN remains the recovery checkpoint; live ingestion is still the old commit `0dfab1e7b2253fd939088259ea61754d6e56706c`.

Still open: actual S3 durability and intake owner authorization, eight-row delivery/materialization/search, raw replay SPI readiness, governed per-source/per-zone lake policies and prior PET/RSMOKE/RINSTALL issues. Published recovery permissions are not end-to-end smoke evidence.

## 2026-09-30 — Operator recovery draft PASS; publication command ready, not executed

Actual operator evidence: registered 4 recovery descriptors; add-only draft `7eaf57fe-bfd6-4929-b897-fe7f7f7c0a2d`, revision 0, base `ouf-lab-authorization:34`, target `ouf-lab-authorization:35`, four HUMAN subject-bound tenant grants across all tenant sources, no SERVICE grants, validity until `2036-09-15T07:13:50.968730Z`. Existing entries preserved in preview. State `/etc/ouf/deploy-snapshots/ingestion-recovery-policy-draft.json` PRIVATE. POLICY_NOT_PUBLISHED=true, IAM/routes unchanged, no retry/resume. Do not rerun draft creation.

Generic `scripts/r4a_publish_recovery_policy.py` takes explicit draft/revision/base/target/tenant/subject/validity inputs; contains no lab draft IDs, source/run IDs or fixed counts of existing entries. It reconstructs the expected HUMAN add-only permission diff, validates private state and baseline, repeats server preview, requires exact terminal `PUBBLICO <target>`, persists an exclusive private pre-POST receipt, publishes once and reads ACTIVE back for exact descriptors and grants (normalizes omitted null constraints). Ambiguous responses or existing receipt require reconciliation, never blind repost. Receipt `/etc/ouf/deploy-snapshots/ingestion-recovery-policy-publication.json` PRIVATE. Five publication regression tests plus six preparation tests pass locally; CLI/import pass. These are local tests, not server publication evidence.

Next operator step: pin/download publication script, preparation script, authorization lifecycle and capability registration helpers from one commit; publish with above draft inputs, administrator subject `b93d8cf6-cd14-4ee6-91d7-84cd76c4f500`, tenant `ouf-lab`. Login is HUMAN administration; workload tokens are untouched. Publication adds permissions only, no actual recovery. After publication: reconcile HUMAN OIDC scopes/bindings and shared recovery routes, prove HUMAN read access, adopt CI-tested ingestion revision `759d916cc9a45a39e9be0156f54677225a172e1f` with both loops preserved, then versioned quarantine retry and run resume. Current live ingestion remains `0dfab1e7b2253fd939088259ea61754d6e56706c`; do not retry on it. Source remains ACTIVE, run PAUSED and quarantine OPEN; source reactivation/once schedule reset/SQL lifecycle mutations are not recovery paths.

All previously documented open issues remain, including real S3/UDP intake authorization and durability, eight-row delivery/materialization/search, raw replay SPI, per-source/per-zone lake policies, broader PET smoke/installation completion. This evidence is production-general bootstrap machinery tested with the cinema example, not proof of completed end-to-end smoke.

## 2026-09-30 — Recovery HUMAN catalogue missing; generic draft preparation ready

Operator evidence: READ_ONLY HTTP 200 on `ouf-lab-authorization:34`; descriptors and grants are zero for `ingestion.run.read`, `ingestion.run.resume`, `ingestion.quarantine.read`, `ouf.ingestion.quarantine.retry`. Human token and owner recovery authorization are not proven. Run remains PAUSED, quarantine OPEN; no retry/resume occurred.

`scripts/r4a_prepare_recovery_policy.py` prepares four READ/WRITE descriptors, HUMAN only, owner `ingestion`, and four subject-bound tenant grants for all tenant sources. Tenant, administrator subject, validity and expected active baseline are explicit CLI inputs. Authentication uses the existing installation OIDC device flow; its endpoints/client are deployment defaults, not a portable installation config abstraction. No cinema/source/run IDs are built into policy logic. Grants have null resource constraints; capability plus subject and tenant define access across the tenant. Grant validity is explicitly reviewed; laboratory command uses the existing lab authorization horizon 2036-09-15T07:13:50.968730Z, not a mandatory production duration.

Private exclusive pre-POST state `/etc/ouf/deploy-snapshots/ingestion-recovery-policy-draft.json` prevents blind repost after ambiguous responses. The script preserves all existing entries, verifies exact add-only preview and baseline stability, registers missing catalogue descriptors and creates a DRAFT only. It never publishes, modifies Keycloak/routes/workload token or resumes/retries. Existing descriptors or grants in ACTIVE require reconciliation. Six local unit tests pass, including a different tenant, preservation, drift and preview rejection; CLI/import validated with exact current repository helpers. This is local automation validation, not server execution evidence.

Next operator step: download this script plus `r4a_authorization_lifecycle.py` and `r4a_register_capabilities.py` at one pinned commit; execute with `--expected-base ouf-lab-authorization:34 --tenant ouf-lab --subject b93d8cf6-cd14-4ee6-91d7-84cd76c4f500 --valid-until 2036-09-15T07:13:50.968730Z`. Publication remains separate and reviewed. Thereafter reconcile four HUMAN scopes/bindings and shared routes, prove read access, adopt tested ingestion commit `759d916cc9a45a39e9be0156f54677225a172e1f` preserving activation/execution loops, then authorize quarantine retry and resume via versioned APIs. Never retry on the old deployed ingestion release, reactivate the source, re-enable consumed once schedules, delete attempts, or manipulate lifecycle rows by SQL.

Open evidence remains: actual S3 write durability and UDP intake owner authorization; eight-row delivery/materialization/search; RAW replay SPI readiness; governed per-source/per-zone retention and access policies; broader PET/RSMOKE/RINSTALL issues already listed below. Source ACTIVE is not smoke completion.


### CI esatta verde della correzione retry (non ancora live)

Verificato commit `759d916cc9a45a39e9be0156f54677225a172e1f`, branch `codex/r4a-governed-record-retry`, GioNob/ouf-ingestion-runtime. Tutti e sette i workflow associati risultano completed/success: module CI (run 36762530058), R4a frozen consumer (36762529950), R2a (36762530202), R2b (36762529995), R2c (36762529910), R2e (36762529885), Shared Authorization SDK pairwise (36762530005). Module job Java21/PostgreSQL17: 112 test, zero failures/errors/skips; RunExecutionWorkerRuntimeTest nove test, tutti PASS, inclusi tre nuovi casi di retry. OpenAPI release gate PASS; non-root image/package, supply-chain/deployment e database DR job PASS sul medesimo commit.

Questa è evidenza CI sul nuovo codice, non recupero del run live o prova owner/S3. Il live resta revision 0dfab1e7b2253fd939088259ea61754d6e56706c, run PAUSED/controlVersion=0 e quarantena OPEN/version=0. Il prossimo comando operatore è il solo inventario `r4a_recovery_access_catalogue.py --tenant ouf-lab` (pinned Semantic d6059ed9038abc2eee172bef16d9622e8aa55724). Successivi gate ancora da eseguire: bootstrap HUMAN condiviso (descriptor/grant/scope/route e owner access), candidato e switch Ingestion conservando loop/transport/token/history e backup restore drill, retry della quarantena e resume con expectedVersion/receipt/readback. Non aggiungere scope HUMAN a ouf-ingestion, non ripetere source activation, non trattare il riferimento payload come RAW durevole, non dichiarare SPI replay o smoke/search completati.



### Recovery readback e correzione generica del retry in preparazione

Readback live: run PAUSED/controlVersion=0, quarantena OPEN/lifecycleVersion=0 blocking per ING_EXECUTION_GATEWAY_404, un tentativo fallito n.1, zero handoff/replay. payload_ref OTHER_REFERENCE_NOT_DURABILITY_PROOF: non assumere RAW lake durevole. Ingestion running/revision 0dfab1e7b2253fd939088259ea61754d6e56706c match. Route HUMAN run read/resume e quarantine read/retry/reprocess tutte count=0. Nessun retry/replay/resume eseguito.

Implementata su GioNob/ouf-ingestion-runtime, branch `codex/r4a-governed-record-retry` (base release live), correzione generica: worker legge nuovo attempt number con verifica lease; failed attempts restano append-only. Resume blocca quarantene blocking OPEN/REPROCESSING finché HUMAN non autorizza RETRY_READY con expectedVersion. ACK durevole risolve solo quarantene RETRY_READY di precedenti FAILED attempts dello stesso run/source object, con decision ref: aggiornamento quarantena, runtime issue e audit nella transazione ACK, duplicate ACK idempotente. Nessuna migrazione, override business-source o raw replay SPI aggiunto. Tre regressioni PostgreSQL aggiunte a RunExecutionWorkerRuntimeTest, OpenAPI resume aggiornato, traceability `docs/R4A_GOVERNED_RECORD_RETRY.md`.

Commit candidato corrente `759d916cc9a45a39e9be0156f54677225a172e1f`, NON deployed. Prima CI su 608a52da4175328efe64d28b9cf1beb573afec80: 112 test, una nuova asserzione usava vista senza control_version; corretta alla vista governata. Build/supply-chain e DR PASS sul primo commit, ma non trasferire tale prova al nuovo head; CI del nuovo commit da verificare. Nessuna Maven/PostgreSQL locale disponibile in workspace, non dichiarare test locali Java PASS.

Prossimo inventario indipendente: `r4a_recovery_access_catalogue.py --tenant ouf-lab`, GET del bundle attivo e descriptor/grant diagnostici per ingestion.run.read, ingestion.run.resume, ingestion.quarantine.read, ouf.ingestion.quarantine.retry. Non aggiunge scope HUMAN al workload ouf-ingestion, non pubblica policy, non crea route. Conta grant subject-bound nel tenant senza stampare identità; non è prova di grant per l'operatore, validità o owner authorization. Gate successivi: CI esatta verde, release/candidate/switch conservando loop/mount/token/history/run PAUSED, bootstrap condiviso HUMAN reviewabile e owner GET, poi retry/resume governati con receipt e readback. SPI raw replay e policy lake per fonte/zona restano aperti.



### Profilo lake live PASS; recupero del run richiede correzione Ingestion

Readback operativo: prepare/plan/apply lake profile PASS, stessa immagine, profile match 90/OPERATIONAL/RESTRICTED, IAM/S3 preservati, Flyway invariato, code/pubblicazioni invariati. Backup `/etc/ouf/deploy-snapshots/udp-before-lake-profile-y_fx48s_.dump` root-private, restore reale scratch PASS; receipt `/etc/ouf/deploy-snapshots/udp-lake-profile-switch.json`, rollback container `ouf-udp-lake-profile-rollback-82c813b86bfa`. Inventario successivo: tutti i binding lake/IAM validi, nessun override, LAKE_BINDINGS_READY_DIAGNOSTIC=true/invalid checks NONE. Nessun POST intake/resume; permessi S3 e owner intake ancora non provati.

Prima della ripresa verificato il codice esatto della release Ingestion `0dfab1e7b2253fd939088259ea61754d6e56706c` nel repository GioNob/ouf-ingestion-runtime. RunExecutionWorker passa sempre attemptNo=1 a CanonicalRecordPipeline.Command. V1 impone UNIQUE(run_id,source_object_id,attempt_no) e i tentativi sono append-only: il primo record già fallito collide con il nuovo tentativo dopo resume. Inoltre RunExecutionRepository.completeDrained blocca SUCCEEDED finché quarantene blocking sono OPEN/RETRY_READY/REPROCESSING; un retry/resume ordinario non le risolve. QuarantineService.markRetryReady modifica soltanto lifecycle_state; la risoluzione è attualmente nel percorso ReplayRepository.succeeded. ReplayWorker è condizionato alla presenza di ReplayExecutionPort: non assumere esecutore/bean vivo o raw lake durevole dalla sola presenza di payload_ref. Non inviare resume/replay né dismiss artificiale della quarantena, non cancellare il tentativo fallito, non creare una nuova attivazione per aggirare il problema.

Nuovo script source-independent `r4a_run_recovery_inventory.py --run <uuid> --quarantine <uuid>`: sola lettura SQL metadata (versioni controllo/lifecycle, motivo, tentativo fallito n.1, conteggi handoff/replay, tipo riferimento senza payload) e inventario route HUMAN run read/resume, quarantine read/retry/reprocess; nessuna mutazione. CLI/import check PASS, nessun test runtime/live nuovo. Il prossimo gate comprende correzione generica del retry (numero tentativo nuovo, fencing/idempotenza, lifecycle quarantena/issue con evidence durevole e audit, HUMAN expectedVersion) e test di regressione prima di nuova release/switch. Nessuna correzione Java già implementata o rilasciata. R-SMOKE/R-INSTALL e search restano aperti; possibile lavoro di codice, non solo bootstrap configurazione.



### Profilo lake lab approvato: 90 / OPERATIONAL / RESTRICTED; rollout preparato

Il 2026-09-30 l'utente ha approvato il profilo iniziale `ouf-lab`: 90 giorni, classe OPERATIONAL, access label RESTRICTED, per uso operativo/debug/replay della pipeline. Non è una durata prescritta dai PET o una policy universale di produzione. La proposta riguarda il lake, non durata/storico degli oggetti UDP. Restano da implementare policy lake governate per fonte e zona, definite in onboarding e approvate/versionate; l'attuale release usa un profilo runtime globale per RAW/NORMALIZED/CURATED. Non dichiarare tale evoluzione già implementata.

Preparato `r4a_udp_lake_profile.py --mode prepare|plan|apply --tenant ouf-lab --days 90 --retention-class OPERATIONAL --access-label RESTRICTED`. Modifica soltanto i tre ENV nel candidato, stessa immagine UDP revision edaba2bff18a2aaf52d1180f21f0e68984cc3437; IAM, S3, credenziali, mount e launch contract preservati. Candidate stopped/restart=no, state privato O_EXCL; runtime non supportati o override config bloccano. Prima dello switch richiede code ingestion/replay/schedule/outbox quiescenti e job UDP tutti SUCCEEDED; pubblicazioni ACTIVE/run PAUSED ammessi. Backup UDP privato e ripristino reale su database scratch con confronto completa Flyway history; storia deve restare a 34. Verifica health locale e reachability dal namespace APISIX, profilo e altre configurazioni, snapshot code/pubblicazioni prima/dopo. Snapshot tra database non atomici. Rollback del container con immagine/ENV/mount readback, nessun ripristino automatico DB e receipt obbligatorio per riconciliazione.

Stati previsti: `/etc/ouf/deploy-snapshots/udp-lake-profile-prepare.json`, `/etc/ouf/deploy-snapshots/udp-lake-profile-switch.json`. Sei test locali PASS (profile bounds, conservazione ENV/secret/mount/immagine, candidato running rifiutato, rollback prima/dopo rename, container estraneo non toccato). Nuova CI non acquisita. Il rollout LIVE NON è ancora eseguito. Le impostazioni si applicano ai nuovi oggetti lake, non aggiornano retention degli esistenti e non provano cancellazione automatica dopo 90 giorni. Fonte ACTIVE e run PAUSED: nessun intake POST/resume. Permessi S3/owner intake, otto record UDP e search ancora da provare.



### Prerequisiti lake: tre binding RAW non validi, nessun cambio live

Readback operativo 2026-09-30: assenti override Spring JSON/env external config/command/mount/direct relaxed properties. Tenant match, bucket/endpoint/region/path-style diagnostici validi; IAM enabled/issuer/audience presenti e coppia credenziali AWS ENV presente. Tre controlli falliscono: RAW_RETENTION_DAYS_VALID, RAW_RETENTION_CLASS_VALID, RAW_ACCESS_LABEL_VALID. `LAKE_BINDINGS_READY_DIAGNOSTIC=false`. Non sono stati stampati i valori; il readback non distingue assenza da valore invalido. Permessi S3 e owner intake restano non provati.

Prima di rollout UDP occorre definire esplicitamente i tre valori del profilo: giorni retention (1..36500), classe (OPERATIONAL/AUDIT/ARCHIVAL/LEGAL_HOLD/DERIVED_REBUILDABLE), access label (OPEN/ANONYMOUS/PERSONAL/SENSITIVE/RESTRICTED). Nei documenti correnti verificati non emerge un profilo RAW già approvato. Non scegliere arbitrariamente durata/classe, non dedurre OPEN dalle proprietà semanticamente pubblicate del CSV: accesso RAW e materializzazione sono distinti.

La release UDP corrente applica questi binding a RuntimeLakeApi per tutte le zone RAW/NORMALIZED/CURATED e tutte le fonti servite dal runtime; sono un profilo runtime condiviso, non una policy per fonte passata dall'onboarding. Eventuale differenziazione per fonte/zona richiede una policy governata esplicita e relativo supporto applicativo: non dichiararla implementata. Il prossimo passo, ricevuti i valori, è preparare candidato UDP stessa immagine e piano di adozione/rollback, preservando IAM/S3/altre configurazioni; nessun resume prima del readback. Nessun candidato o modifica live effettuato in questo passaggio. Fonte ACTIVE, run PAUSED, gate smoke/install/search aperti.



### Route intake live PASS; prerequisiti lake/IAM da leggere

Output operativo del 2026-09-30: plan/apply route intake PASS; due route aggiunte, esistenti preservate. Receipt `/etc/ouf/deploy-snapshots/runtime-intake-routes.json`, snapshot privato `/etc/ouf/deploy-snapshots/runtime-intake-routes-ywv2y19i/routes-before.json`. Inventario read-only: una route LAKE e una HANDOFF, entrambe enabled, upstream inline `ouf-udp:8080`, OIDC enabled, nessun riferimento upstream/service/plugin esterno, nessuna riscrittura o condizione extra, host supportato; scope `datalake.write` / `udp.candidate.write` presenti nel token. IAM e worker invariati, nessun POST intake o resume. Non rieseguire l'installer: receipt presente richiede riconciliazione.

Prossimo passo `r4a_runtime_lake_prerequisites.py --tenant ouf-lab`: inventario source-independent della release UDP verificata, tenant lake, retention RAW (giorni 1..36500, classi OPERATIONAL/AUDIT/ARCHIVAL/LEGAL_HOLD/DERIVED_REBUILDABLE), access label, bucket/endpoint/region/path-style e IAM enabled/issuer/audience. Rileva override JSON, configurazione esterna, command/env property e mount. Riporta booleani, non valori sensibili; credenziali AWS eventualmente presenti non provano risoluzione della credential chain o permessi S3. Le verifiche ENV sono diagnostiche, non introspezione dei bean Spring. Nessuna rete S3, richiesta POST, scrittura DB o modifica live. Controlli locali su fixture validi/invalidi PASS; nuova CI non acquisita.

Owner intake e durabilità S3 restano non provati: confermarli nell'esecuzione governata dopo aver risolto i binding. Fonte ACTIVE e run PAUSED restano il checkpoint; otto record UDP, R-SMOKE/R-INSTALL e search ancora aperti.



### Template verificato: esclusione proxy-rewrite dalle nuove route intake

Diagnostica live: una route template; tutti i controlli PASS tranne presenza di `proxy-rewrite`. Il contenuto della riscrittura non è stato stampato e non è assunto. L'installer precedente imponeva inutilmente l'assenza del plugin anche sul modello. Corretto `desired_routes`: mantiene OIDC e upstream del modello, rimuove l'intero `proxy-rewrite` dalle sole nuove route POST (nessuna trasformazione URI/method/host/header ereditata). La route di preflight resta invariata; tutti gli altri controlli, snapshot e rollback restano attivi. La presenza della riscrittura nel modello è ora informativa nella diagnostica, non un fallimento.

Verificati sul codice UDP della release `edaba2bff18a2aaf52d1180f21f0e68984cc3437`: RuntimeLakeApi e HandoffApi ricevono esattamente `/api/internal/v1/lake/objects` e `/api/internal/v1/handoffs`; UdpIamSecurityConfiguration valida bearer/issuer/audience e costruisce il TrustedPrincipal, mentre ServletAuthorization ignora header identità/capability del client. Dieci test locali installer PASS, inclusa esclusione completa della riscrittura senza mutazione del modello e mantenimento dei blocchi sui riferimenti upstream esterni. Nessuna nuova CI acquisita.

Prossimo comando: nuovo installer plan/apply e inventario condiviso. Ancora nessun PUT live riuscito, nessun POST intake, nessun resume; prerequisiti lake/owner e materiale UDP/search restano da verificare. Procedura indipendente dalla fonte cinema.



### Route intake bloccate sul template OIDC: diagnostica read-only

Il tentativo plan delle route intake ha verificato entrambi i descriptor univoci, operation WRITE, scope corrispondenti e actor SERVICE, poi si è fermato con `UDP_OIDC_TEMPLATE_UNSUPPORTED`. La causa specifica non è ancora provata; non attribuirla a scope, upstream o rewrite senza readback. Il blocco avviene prima di snapshot/receipt e di qualsiasi PUT: nessuna route intake creata e run non ripreso.

Aggiunta modalità `r4a_install_runtime_intake_routes.py template`: sola lettura APISIX, conteggio delle route modello e booleani per ciascuna condizione dell'installer, layout dei nodi e `FAILED_CHECKS`. Nessun body route, token, secret o configurazione OIDC stampato. Otto test locali PASS, incluso redaction dei segreti nella diagnostica; nuova CI non acquisita. Il prossimo comando è esclusivamente `template`, non apply. Requisiti dell'installer invariati fino all'evidenza del layout live. Refresher/token/policy già adottati restano PASS; owner intake, otto record UDP e search non ancora provati.



### Adozione refresher intake live PASS; route condivise prossime

Output operativo ricevuto il 2026-09-30: prepare/plan/apply PASS del refresher intake, token cambiato, scope precedenti preservati, `datalake.write` e `udp.candidate.write` presenti, discovery HTTP 200, timer ripristinato. Configurazione runtime e snapshot delle code invariati; nessun resume. Receipt privato `/etc/ouf/deploy-snapshots/ingestion-runtime-intake-refresher-adoption.json`. È prova del token e della discovery ONBOARDING, non dell'autorizzazione owner sui POST di intake.

Prossimo passaggio operativo: `r4a_install_runtime_intake_routes.py plan` e `apply`, poi `r4a_runtime_intake_route_inventory.py`. Installer e inventario coprono route condivise senza dipendenza da una fonte business; l'inventario ora usa il checkpoint cinema solo con `--smoke-cinema`. Le due route sono POST esatti `/api/internal/v1/lake/objects` e `/api/internal/v1/handoffs`, upstream UDP, OIDC con scope derivati dai descriptor della policy. Installer additivo, snapshot privato, readback delle route e rollback limitato alle proprie creazioni. Sette test locali installer PASS; nessuna nuova prova CI. Installazione route non ancora eseguita e nessun POST intake di prova inviato.

Run smoke ancora PAUSED, fonte ACTIVE: prima di qualsiasi recupero governato verificare prerequisiti lake (tenant, retention/access/S3) e autorizzazione owner. Materializzazione degli otto record e search ancora non provate. Non riattivare la fonte, non riabilitare la schedule once consumata, non modificare stati via SQL.



### Scope Keycloak intake verificati; adozione refresher preparata

Il readback operativo conferma `datalake.write` e `udp.candidate.write` presenti senza drift, entrambi con binding OPTIONAL al client `ouf-ingestion`. La policy `ouf-lab-authorization:34` è già pubblicata (38 capability, 79 grant, baseline preservata). Il binding OPTIONAL richiede che il refresher chieda esplicitamente gli scope: non costituisce prova che il token montato li contenga.

Preparato `scripts/r4a_runtime_intake_refresher.py` (`--mode prepare|plan|apply --tenant ouf-lab`): candidato privato, confronto hash con receipt del refresher precedente, conservazione dell'espressione scope, rinnovo via servizio esistente, verifica dei vecchi e nuovi scope, discovery reale HTTP 200 e ripristino timer. La procedura è comune a tutte le fonti del tenant e non contiene identificatori cinema. Richiede code quiescenti; pubblicazioni ACTIVE e run PAUSED sono ammessi. Confronta configurazione runtime e snapshot SQL di run, schedule, outbox, quarantene e pubblicazioni prima/dopo; i due database non sono letti atomicamente. Nessuna modifica a policy, route, fonte o stato del run. Receipt pre-mutation impedisce retry ciechi; rollback dello script e rinnovo token precedente in caso di errore.

Cinque test locali PASS (scope precedenti/espressione conservati, layout ambigui rifiutati, adozione e rollback). Questo non prova l'adozione live; nuova CI non acquisita. Stato live ancora: cinema ACTIVE, run `86809c17-3354-45ca-a7e6-57e903944b24` PAUSED per `ING_EXECUTION_GATEWAY_404`, nessuna consegna/materializzazione verificata. Prossimi passi: adozione refresher, route POST condivise e verifiche dei prerequisiti lake/owner, poi recupero governato della quarantena/run. R-SMOKE, R-INSTALL e search restano aperti.


## 2026-09-30 — generic runtime intake policy34 LIVE publication PASS

Operator HUMAN terminal confirmation `PUBBLICO ouf-lab-authorization:34` completed. Publication/readback PASS: active policy :34, 38 capabilities/79 grants, all previous entries preserved. Private receipt `/etc/ouf/deploy-snapshots/ingestion-runtime-intake-policy-publication.json`. Common SERVICE intake rights apply to all tenant sources, not cinema. Token/routes unchanged by publication; run not resumed. Do not repeat registration/draft/publication.

Next verified existing Keycloak helpers, unchanged pinned Onboarding `6340d5bf120e09b47c32177656e2c377a4c03640`: `scripts/r4a_keycloak_client_scope_catalogue.py` and `scripts/r4a_keycloak_client_scope_binding.py`. For each requiredScope `datalake.write`, `udp.candidate.write`: realm ouf, OIDC protocol, include.in.token.scope=true/display.on.consent.screen=false, reconcile plan/apply/verify; exact OPTIONAL client binding for ouf-ingestion, preserving other client scopes; conflicting default binding fails for review. Helpers use existing authenticated kcadm session; if read check fails renew inside ouf-keycloak with realm master/admin oufadmin and terminal password input only. No scope per CSV/source.

This next operation changes Keycloak scope catalogue/bindings only, does not publish policy again, alter refresher requests, install routes or resume/replay. Timer may continue ordinary background refresh; do not claim token file unchanged over elapsed time. After operator PASS, prepare private AST patch of existing installed ingestion refresher to explicitly request both OPTIONAL scopes while preserving prior scopes; reviewed atomic adoption, token freshness/claims checks and owner authorization validation precede shared route installation and governed run recovery. ACTIVE source/PAUSED run/OPEN quarantine and absent routes remain last-verified. R-SMOKE/R-INSTALL/search OPEN.

Reusable installation mapping: datalake.write → requiredScope datalake.write → OPTIONAL binding on ingestion workload → explicit token scope request → POST /api/internal/v1/lake/objects to UDP; udp.candidate.write → same-name scope/binding/request → POST /api/internal/v1/handoffs. Tenant/service/module grants are installation profile configuration; business source identity is absent from these common permission/route definitions.

## 2026-09-30 — generic intake registration/draft LIVE PASS; publication prepared

Operator registration COUNT2 PASS, policy unpublished. Combined draft `34a9b8f5-50e2-4c6a-86b1-6d869d053a95`, revision0, base `ouf-lab-authorization:33` → target :34, adds datalake.write and udp.candidate.write plus two SERVICE grants; existing capability/grant entries preserved. Tenant ouf-lab/servicePrincipal ouf-ingestion/resourceType ingestion-intake/module UDP, ALL_TENANT_SOURCES. Private state `/etc/ouf/deploy-snapshots/ingestion-runtime-intake-policy-draft.json` PASS. Token/routes unchanged, run not resumed. Do not re-register or recreate draft.

Prepared reviewed-operation publisher `scripts/r4a_publish_runtime_intake_policy.py` at 8f464923ee4f32580fcee9df61bd591897deb438. Exact draft/base/revision/manifests and add-only candidate validation, fresh HUMAN policy-admin login, owner preview before/after terminal phrase `PUBBLICO ouf-lab-authorization:34`; active baseline/draft drift check. Durable private O_EXCL publication receipt before single POST; no auto retry on uncertain outcome. Full ACTIVE capabilities/grants must match reviewed candidate, expected 38/79 with all baseline entries preserved. Receipt `/etc/ouf/deploy-snapshots/ingestion-runtime-intake-policy-publication.json`. Source-independent capability/grant mechanism remains generic; this publisher pins one reviewed administrative decision, not a business source.

Three local publication mock tests PASS: baseline-grant drift rejection, full readback beyond counts, uncertain POST retains private receipt and blocks second publish. All eight command dependency paths verified present at immutable commit via GitHub. No VPS publication/CI proof yet. After publication: Keycloak scope entries/bindings + refresher requests, fresh token scope/owner authorization, shared route install, governed recovery. Source ACTIVE/run PAUSED/quarantine OPEN; no UDP delivery, R-SMOKE/R-INSTALL/search OPEN.

## 2026-09-30 — download prerequisite fixed before policy preparation

Operator command stopped at curl404 before Python execution; no registration/draft/publication from that attempt. Verified exact old commit dependencies: `scripts/r4a_service_grant_lifecycle.py` was missing from Semantic although present in pinned Onboarding. Added unchanged source from Onboarding `6340d5bf120e09b47c32177656e2c377a4c03640` (blob `2c6c749cc5bcb68ba0a1831da31e1a7eea76d5b3`) at Semantic commit aa503b518f75411af7e836792d4ee4e2bd992aff.

All seven exact download paths (five helpers plus two manifests) verified present at that immutable commit through GitHub contents reads; four local intake-policy tests PASS. Retry preparation using this complete commit. Source-independent grants unchanged (SERVICE/tenant/module UDP, all tenant sources); no cinema sourceRef. This repair is dependency completeness evidence, not VPS preparation/CI proof. Active policy last verified :33; source ACTIVE/run PAUSED/quarantine OPEN, routes absent, no UDP delivery. All existing open gates retained.

## 2026-09-30 — generic production intake scope; catalogue prerequisites confirmed

Operator authenticated policy catalogue: `ouf-lab-authorization:33`, contentHash `db0f30b05de9abf4920c66be4c2873202c051ec153c65d66b17e7ca60a46df69`; both `datalake.write` and `udp.candidate.write` have EXACT_OBJECT_COUNT=0, DESCRIPTOR_COUNT=0, GRANT_COUNT=0, no related token scopes. No route/IAM mutation or resume. Active-bundle absence does not by itself prove capability registration catalogue absence; preparation reconciles that separately.

User clarified production must support every source: cinema is only smoke data. The unexecuted initial sourceRef=cinema proposal was discarded before any registration/draft/publication. Prepared manifests now define common UDP SERVICE capabilities with explicit WRITE operation and same-name OAuth scopes, plus grants for `ouf-ingestion` / tenant `ouf-lab` / resourceType `ingestion-intake` / module UDP. No sourceRef, jobRef, cinema ID or record field constraint; these rights support all tenant sources through the same runtime intake. Tenant/principal/validity are installation profile values, not per-source additions. Source onboarding/semantic/identity approval policies remain independently governed. Do not register new capabilities, grants, Keycloak scopes or routes for each CSV/source. Existing route installer is source-independent by default; optional `--smoke-cinema` checks the lab checkpoint without changing route or grant scope. Runtime version pins remain release checks; this is not evidence of completed clean-install/upgrade verification.

Prepared at commit b4d5a1f3336ca1a59720a74d3aa88d0ad0946ed7: two `catalogue/r4a-ingestion-runtime-intake-*.json` manifests, `scripts/r4a_prepare_runtime_intake_policy.py --expected-base ouf-lab-authorization:33`. Direct HUMAN policy-admin login (token in memory); register only missing exact descriptors via trusted HUMAN catalogue API, reject existing semantic conflicts; read back registrations; build one add-only draft from expected active base and snapshot all prior entries; preview must add exactly two descriptors and two grants without removal/change. Expected target :34 is computed from base, not hardcoded counts/source. Durable private state `/etc/ouf/deploy-snapshots/ingestion-runtime-intake-policy-draft.json` records registration/draft phases and blocks blind retries after uncertain POST. This command DOES NOT publish the policy, refresh token, alter Keycloak/routes or resume run. Capabilities become registration entries only; active policy remains :33 until explicit publication. Helper lifecycle/registration sources mirrored unchanged from pinned Onboarding `6340d5bf120e09b47c32177656e2c377a4c03640`.

Eleven local tests PASS: seven route guards/rollback tests plus four policy candidate/preview/conflict/source-independent grant checks. Live preparation still pending. Next: review actual draft diff, HUMAN publish, configure both Keycloak scope entries/bindings and refresher requested scopes generically, confirm fresh token and owner ALLOW; install shared routes; governed paused-run recovery and smoke verification. Do not claim production/multi-source live proof yet. Source ACTIVE/run PAUSED/quarantine OPEN, zero UDP intake; R-SMOKE/R-INSTALL/search OPEN.

## 2026-09-30 — exact datalake.write descriptor count zero; catalogue prerequisite investigation

Operator corrected plan reports `INTAKE_DESCRIPTOR_CAPABILITY=datalake.write COUNT=0` and precise NOT_UNIQUE_COUNT=0 block. No apply/route mutation or resume. This confirms no exact usable flat descriptor selected, not yet whether all exact capability objects are absent or use unsupported structure; udp.candidate.write was not reached because the first check stopped. Earlier WRITE assumption correction did not resolve this separate missing-descriptor prerequisite.

Prepared read-only `catalogue` mode in installer at 95b4228b9b306c83c4f63d854407583bdb05fe28: authenticates to existing configured registry URL with mounted ingestion SERVICE token; reports policy ref metadata, exact object/descriptor/grant counts for BOTH owner IDs, declared operation/scope, SERVICE and token-scope flags, diagnostic principal/tenant grant count, and related lake/candidate IDs/scopes. It does not dump grants, subjects, conditions, credentials or whole policy. Related-ID reporting distinguishes naming mismatch from genuinely absent catalogue entries; token membership/diagnostic grants do not prove owner ALLOW. No route admin write, IAM change, refresh, replay/resume or reactivation. Existing seven installer regression tests PASS; new mode is read-only. Route installation remains blocked, source ACTIVE/run paused/quarantine OPEN. After evidence reconcile owner exact capability IDs with catalog and token, then use existing reviewed policy workflow if new entries are required. R-SMOKE/R-INSTALL/search OPEN.

## 2026-09-30 — intake route plan blocked; descriptor operation assumption corrected

Operator first plan returned `INTAKE_CAPABILITY_DESCRIPTOR_UNSUPPORTED`; set-e sequence stopped before apply, no route mutation/receipt or run resume. The generic code did not identify whether descriptor count, SERVICE actor, operation or scope failed; actual active descriptor values are not yet operator evidence.

Pinned SDK inspection (`OwnerAuthorization.decide` at deployed Onboarding/UDP SDK source) proves owner evaluation uses the capability descriptor's declared operation; it does not infer WRITE from the POST method. Installer's imposed operation=WRITE was an incorrect assumption. Corrected script/tests at 23d93c08a7a9bbc41f4727b1b67c8fd5fc1c6650: operation must be a valid nonblank symbolic catalogue value, while unique descriptor, SERVICE actor and valid requiredScope/token membership checks remain. Plan now prints exact capability descriptor count, safe operation/scope and SERVICE flag; errors identify failing capability/check. Missing/duplicate descriptors or token scope still block before mutation; correction is not a claim that active capabilities/grants already exist or that WRITE was the actual live failure.

Seven local tests PASS, including non-CRUD catalogue operation and missing descriptor precise block; prior rollback/security tests remain PASS. Repeat pinned plan and apply only if plan succeeds, then inventory. Routes remain last-verified absent; source ACTIVE, run paused and quarantine OPEN, no UDP delivery. R-SMOKE/R-INSTALL/search remain OPEN.

## 2026-09-30 — both runtime intake POST routes absent; guarded installer prepared

Operator read-only inventory confirms UDP running and pinned revision match; `INTAKE_LAKE_ROUTE_COUNT=0` and `INTAKE_HANDOFF_ROUTE_COUNT=0`. No live/IAM change, intake POST or resume. Missing lake route explains the execution Gateway404; missing handoff route would also block subsequent delivery.

Prepared installer at 115edfd5993abf9a4ce29e62f6fd0eaa7021c8a0: `scripts/r4a_install_runtime_intake_routes.py plan|apply`. Adds only exact POST `/api/internal/v1/lake/objects` (ID `r4a-udp-runtime-lake-write`) and `/api/internal/v1/handoffs` (ID `r4a-udp-runtime-handoff-write`) to inline `ouf-udp:8080`. Clones verified enabled UDP identity-preflight OIDC template, requires no references/rewrites/extra match conditions and valid public host; replaces required scopes using unique SERVICE/WRITE descriptors for datalake.write and udp.candidate.write from the active authenticated policy bundle. Stops if mounted ingestion token lacks scope; no IAM/token mutation. Requires exact paused-run baseline/no outbox and activation receipt. Rejects existing paths/IDs/receipt; snapshots all routes privately, durably reserves receipt before PUTs, checks policy/routes drift and verifies new routes plus preservation of every prior route. On failure removes only attempted routes whose exact content still matches this installer, verifies absence, and retains ROLLED_BACK or MANUAL_RECOVERY_REQUIRED receipt; no blind retry after uncertain write.

Five local mock tests PASS: security cloning/original preservation, duplicate template rejection, SERVICE descriptor enforcement, partial rollback scoped to new route, concurrent route drift refuses deletion. Syntax PASS; not live rollout or new CI evidence. Private planned receipt `/etc/ouf/deploy-snapshots/runtime-intake-routes.json`. Run/quarantine stays paused/open; no source reactivation, replay/resume or UDP payload POST. After operator install/readback, inspect owner authorization/runtime lake prerequisites and prepare governed recovery. R-SMOKE/R-INSTALL/search remain OPEN.

## 2026-09-30 — precise quarantine cause Gateway HTTP404; intake route diagnosis next

Operator safe diagnosis confirms run `86809c17-3354-45ca-a7e6-57e903944b24` PAUSED, partition PAUSED; attempt `fef12546-677d-47c6-9eb0-c5e42fb4449e` FAILED with `ING_EXECUTION_GATEWAY_404`. Blocking quarantine `7741f1f3-479b-42be-bb0d-a711efb20722` OPEN, lifecycle_version=0, same reason, contract-or-mapping evidence, not schema evidence; payload_ref_present does not prove durable lake persistence (source fallback ref is also possible). Source remains ACTIVE; no UDP handoff or materialization.

Pinned deployed Ingestion pipeline persists RAW/NORMALIZED/CURATED through POST `/api/internal/v1/lake/objects` before staging lineage/outbox; handoff delivery later POSTs `/api/internal/v1/handoffs`. Pinned UDP owner exposes both exact paths (`RuntimeLakeApi`, `HandoffApi`) and returns 201 on success. Reason404 identifies the execution Gateway response, not yet whether route is absent, mismatched or upstream returns404. Malformed CSV is not established; absence of lineage points to persistence or earlier pipeline stage, no handoff delivery occurred.

Next read-only script at 094ea6b7690b9db74f9c5475ee6f7fc1a99825c4: `scripts/r4a_runtime_intake_route_inventory.py`. Supports already ACTIVE source without frozen-only version helper; reads actual APISIX routes matching both POST paths, reports route counts/enablement/upstream UDP/OIDC/rewrite/extra matches/host/scopes and mounted ingestion token scope membership. Reads owner running/revision facts. No POST, route/IAM mutation, token refresh, run resume, replay or source reactivation. Scope membership alone does not prove owner authorization. Syntax compilation PASS; live inventory pending. After diagnosis prepare targeted correction, then governed recovery preserving paused run/quarantine evidence. R-SMOKE/R-INSTALL/search remain OPEN.

## 2026-09-30 — real execution PAUSED in Ingestion, not delivered to UDP

Operator readback: source ACTIVE and frozen hash/publication match. Exactly one run `86809c17-3354-45ca-a7e6-57e903944b24`, state PAUSED, generic `ING_RECORD_QUARANTINED`; one processing attempt, one open quarantine, zero lineages/outbox. UDP intakes/jobs/decisions/issues/observations/revisions/bindings/current objects all zero for this run. Both eight-row delivery/materialization NOT_PROVEN. Recent bounded activation/execution loop failure marker counts zero; handled record failure need not produce those markers. Equality of two empty handoff sets is not evidence of delivery.

Managed-once schedule `304d4515-a283-4ec3-880f-7a2e6b3b8d40` DISABLED, trigger_once/consumed/publication_enabled true, activation_failures=0 and not blocked. The once trigger has been consumed; do not re-activate source or change schedule/DB blindly. Approval, publication, runtime loop rollout and UDP gate remain distinct successful evidence; actual pipeline smoke is OPEN.

Pinned production pipeline inspection shows generic pause wraps a more precise `ing_quarantine.reason_code` and `processing_attempt.reason_code`; record quarantine can include DataLake/Gateway/persistence/contract errors, so malformed CSV is not established. Next prepared script at a737c4cc1ea8289fc1b2b26cb0a72613af017500: `scripts/r4a_cinema_quarantine_diagnostic.py` plus standalone readback helper. Exact run/source/publication-checksum scope, read-only SQL; prints UUIDs, symbolic reason codes, lifecycle/attempt/partition states, safe operational event codes and reference-presence/evidence-kind booleans. No payload, source values, token, reference contents or free-form details printed. No retry/replay/resume, IAM change or source reactivation. Syntax compilation PASS; live diagnosis pending. Determine precise reason before preparing a correction and governed resume/replay. R-SMOKE/R-INSTALL and search remain OPEN.

## 2026-09-30 — HUMAN source activation LIVE PASS; real execution readback next

Operator typed `ATTIVO managed-cinema-8ec8ae90` after direct HUMAN review. Fresh route inventory and UDP current gate HTTP200/all bindings/hash/coverage PASS preceded single activation POST. Owner response plus DB readback PASS: source version `68394f42-5c82-4127-a1f3-126516665749` is ACTIVE, frozen configuration/hash unchanged; publication `82a8a210-32fd-4ca3-adeb-ff0ec7872bf6`. Private PASS receipt: `/etc/ouf/deploy-snapshots/cinema-source-activation.json`. Do not rerun activation, renew/confirm approval, or call frozen-version helpers that only support IN_REVIEW/APPROVED. Ingestion result is not yet operator-verified.

Next prepared read-only standalone script at commit 8da1c2a9143a1c72ee7c6b2cdc6e848d86ba35e1: `scripts/r4a_cinema_execution_readback.py`. Requires the exact activation PASS receipt and verifies current ACTIVE owner publication/bundle/hash/checksum. Reads schedules and runs scoped to source/publication checksum, attempts/lineage/quarantine and outbox; reads UDP intake/jobs/decisions/issues/observations/revisions/bindings/current objects scoped to those run IDs. Reports only safe states, counts, IDs and symbolic failure codes; payloads/tokens are not printed. Delivery PASS requires one SUCCEEDED run, eight ACKED handoffs with receipts, identical UDP handoff ID set and no open quarantine. Materialization PASS additionally requires eight PROCESSED intakes, SUCCEEDED jobs, observations and source bindings, at least one active current object, and no open resolution issues. Unique object count is reported, not forced to eight (governed identity may merge records). Bounded recent Ingestion log marker counts are diagnostic only. Cross-database reads are not atomic; a snapshot may need repeating while work progresses. SEARCH remains unverified and R-SMOKE/R-INSTALL OPEN. Five local classification tests PASS; real VPS execution evidence still pending.

## 2026-09-30 — execution rollout LIVE PASS; HUMAN source activation next

Operator evidence confirms execution prepare/plan/apply PASS. Both execution and activation flags true, same image, Flyway14 unchanged; authorized HTTP200 empty discovery, active publications/schedules/unfinished runs and deliverable handoffs all zero. Sixteen-second observation: no new runs, no failure markers; poll count not measured. Source remains APPROVED, source activation false. Backup retained and scratch restore PASS: `/etc/ouf/deploy-snapshots/ingestion-before-compatibility-th5469rr.dump`. Rollback container: `ouf-ingestion-execution-loop-rollback-32eb259ea1e6`. Private receipt: `/etc/ouf/deploy-snapshots/ingestion-execution-loop-switch.json`. Do not repeat either runtime rollout.

Next script prepared at commit b89f630a82d3e58d1802d4afb21a4294f76f98bc: `scripts/r4a_activate_cinema_source.py preflight|activate`. Reuses PASS HUMAN approval receipt and CONFIRMED challenge, checks current source/hash/compatibility and both runtime flags against pinned execution state; checks empty discovery, queues/outbox, routes and fresh UDP activation gate. Direct HUMAN device login requests configuration.write; terminal confirmation is `ATTIVO managed-cinema-8ec8ae90`. Exactly one activation POST after durable private O_EXCL receipt, with no automatic repost after timeout. Confirmed challenges do not need renewal on creation expiry (verified against pinned owner code); no new approval challenge or confirmation is created. Owner publication response and read-only DB readback must match source/version/bundle/checksum, ACTIVE state and unchanged frozen configuration. A PASS proves activation/publication only, not ingestion/UDP/search. Run verification follows actual operator activation evidence. Local four mock tests PASS (confirmed expiry, card drift, uncertain POST/no retry, hash-drift readback); no new VPS activation or CI evidence yet. R-SMOKE/R-INSTALL remain OPEN.

## 2026-09-30 — execution loop prerequisite, not source activation

Operator read-only inventory confirms source APPROVED, activation property true, execution property/env absent (effective diagnostic FALSE), no JSON/command overrides. Live bean presence was not inspected. Source remains non-active.

Prepared scripts at commit e13ebe465686a73705fd2fc47c277bd4e3f05683: `scripts/r4a_enable_execution_loop.py` reuses the same-image worker rollout with a separate candidate, state/receipt and rollback namespace. Adds only `ouf.ingestion.execution.enabled=true`, preserving activation=true and original property bytes. Requires pinned activation/refresher receipts, unchanged source/hash, Flyway14, authorized empty discovery, no active schedules/unfinished runs and zero READY/DELIVERING/FAILED_RETRYABLE handoffs. Full retained DB backup plus scratch restore precedes switch; 16-second observation checks readiness, unchanged run/schedule/outbox counts and both activation/execution failure markers. Automatic rollback preserves the prior activation-enabled, execution-disabled runtime; durable receipt blocks blind retries. No source approval/activation is performed.

Local mock verification: 5 execution checks (backup failure/recovery, failed recovery, legacy schedules, pending handoff, receipt flags) and 3 existing worker regression checks PASS in separate processes. These are not VPS or CI evidence. Execution rollout is PREPARED, not applied; R-SMOKE and R-INSTALL remain OPEN. Next: operator prepare/plan/apply, then HUMAN activation of already-approved source and actual run/UDP/search verification.

## 2026-09-30 — activation worker live PASS; verificare execution loop separato prima di activate

Operatore: prepare/plan/apply activation worker PASS, stessa immagine
0dfab1e…, enabled=true, Flyway14 invariato, nessuna nuova run/schedule.
Backup con restore drill PASS conservato:
 /etc/ouf/deploy-snapshots/ingestion-before-compatibility-1sa6j7hd.dump.
Rollback container:
 ouf-ingestion-activation-worker-rollback-5ee98a4a7cb3.
Receipt /etc/ouf/deploy-snapshots/ingestion-activation-worker-switch.json PASS.
Osservazione16s, failure markers assenti; poll count NON misurato.
Fonte sempre APPROVED, NON ACTIVE. Non ripetere worker switch.

Verifica primaria nel codice release Ingestion:
ActivationLoop/RunCoordinator/PublicationGatewayClient sono condizionati da
ouf.ingestion.activation.enabled=true; ExecutionLoop/ExecutionGatewayClient/
ExecutionRuntimeConfiguration hanno un SECONDO flag distinto
ouf.ingestion.execution.enabled=true, senza matchIfMissing.
ExecutionLoop è quello che acquisisce ed esegue outbox dispatch ogni1000ms.
Il worker switch appena completato aggiungeva soltanto activation.enabled.
Non assumere che execution.enabled sia già attivo perché discovery dà200,
readiness è200 o perché il consumer standalone ha validato8righe.
L'effettivo flag execution live NON ancora osservato in output operatore.
Prima di attivare serve questa lettura mirata; niente altra source approval.

Helper read-only scripts/r4a_execution_loop_inventory.py, Semantic commit
2491573dd110e7068f6c1d7ff857b6a6df0bda39. Parsing sintattico Python PASS;
nessun nuovo test unit speculare per questa sola diagnostica, CI non acquisita.
Legge receipt worker PASS, state preparazione, ID/Image/revision esatti,
bind properties/hash uguali allo state worker, env esatto rispetto al baseline
conservato. Stampa soltanto count/property/env boolean/override presence per
activation/execution, JSON presence e effective diagnostic.
Property assente equivale FALSE in questi ConditionalOnProperty.
Priorità diagnostica ENV sopra file properties; command/JVM override o JSON
presente o valori duplicati/unsupported impediscono concludere readiness.
Non enumera tutti i possibili property source Spring e non ispeziona bean live:
SWITCHES_READY è diagnostico, non prova di esecuzione.
Readonly completo: nessuna modifica flag/env/DB/IAM/worker/source activation.

Se execution èFALSE/ABSENT: preparare/adottare candidata stessa immagine che
aggiunga solo execution.enabled, preservando il flag activation giàTRUE,
con backup/rollback e code vuote. SeTRUE: procedere a HUMAN activate con
gate UDP corrente/readback frozenconfig/compatibilità/hash e receipt univoca.

Codice Owner TrustedHumanApi.activate usa la challenge confermata
4f7a8248-ef40-4dc4-8a64-8a6101c98511 per risolvere source/version, poi
OnboardingService.activate richiede versione APPROVED, compatibilità
INGESTION_RUNTIME corrente sullo stesso hash, surveillance e UDP gate.
Non usa la vecchia challenge CREATED scaduta né richiede nuova conferma:
non richiamare check_card(CREATED/expiry), non ripetere source approval.
Activate genera pubblicazione, statoACTIVE e audit; worker giàenabled inizierà
automaticamente la run dopo discovery. Preparare conferma terminale HUMAN
sul concreto source/version/hash e osservazione run, senza automatizzare una
decisione HUMAN come SERVICE.
R-SMOKE/R-INSTALL OPEN; source activation ancora non eseguita.


## 2026-09-30 — refresher/discovery live PASS; worker enablement preparato

Operatore: refresher plan/apply PASS, token cambiato con scope config-read,
discovery effettiva HTTP200/items[]/nextAfter vuoto/owner ALLOW module-level.
Timer ripristinato attivo; active publications/schedules/unfinished runs0.
Receipt /etc/ouf/deploy-snapshots/publication-refresher-adoption.json PASS.
Fonte APPROVED e non attivata, worker disabled. Non ripetere refresher apply,
owner switch, policy publication o source approval.

Helper scripts/r4a_enable_activation_worker.py Semantic commit
f7fc08d76c8945aaaffa4738b03e2208f083d354; tre test locali mock PASS:
backup failure recupera vecchio runtime e blocca retry, recovery failure
conserva MANUAL_RECOVERY_REQUIRED, schedule ACTIVE legacy blocca enablement.
CI non acquisita. Mode prepare/plan/apply.
Candidato ouf-ingestion-r4a-activation-worker-candidate fermo, stessa immagine
live0dfab1e…/user10002, env/memoria/logging/mount/launch/network preservati;
sostituisce soltanto il bind della copia privata properties0440/root:10002.
Properties originali rimangono byte identiche; copia aggiunge un solo flag
ouf.ingestion.activation.enabled=true. Niente ricompilazione/schema.

Prerequisiti: receipt refresher PASS, fonte/hash APPROVED invariati,
Flyway14 e image revision esatta, properties hash baseline compatibility,
worker prima disabled senza overrideENV/JSON/JVM, token fresco con scope
semantic-read/object-store-read/attest/config-read, discovery200 vuota.
Code pubblicazioni/unfinished vuote; inoltre TUTTE le ing_schedule stateACTIVE
devono essere0, incluse legacy senza publication e fuori dai filtri
publication_enabled/activation_blocked, perché claimDue può prenderle.
Run/schedule totali acquisiti per rilevare qualsiasi nuova riga, incluse run
che terminassero tra due osservazioni.

State privato /etc/ouf/deploy-snapshots/ingestion-activation-worker-prepare.json.
Preparazione idempotente soltanto se candidato/state/props/old runtime esatti.
Apply receipt root0600 STARTING O_EXCL/fsync prima della mutazione:
 /etc/ouf/deploy-snapshots/ingestion-activation-worker-switch.json.
Stop Ingestion, backup completo e restore drill con history14 identica su DB
scratch, retain backup; ricontrolla queue/fonte/properties/candidato,
rename vecchio rollback, rename/start candidato, readiness.
Controlla same image/env/mount/memoria/launch/props/history e token fresh.
Osservazione16s dopo readiness con check ogni2s: queues/allACTIVE0, conteggi
TOTALI run/schedule identici, readiness200; cattura stdout+stderr dockerlogs
privatamente e blocca sui marker discovery/publication/dispatch failure.
Assenza marker NON è contatore poll: output POLL_COUNT_NOT_MEASURED=true.
Non abilita nuovi endpoint Actuator. Prova effettiva dispatch/filiera verrà
dalla run dopo attivazione HUMAN, non dall'assenza dei log.

Fonte deve restareAPPROVED/esatta. Restartunless-stopped finale e runtimeguard.
Receipt PASS; rollback container e backup conservati. Error/interrupt:
recupero per ID del vecchio runtime disabilitato, receipt ROLLED_BACK o
MANUAL_RECOVERY_REQUIRED; DB live mai restaurata automaticamente.
Receipt esistente blocca retry; non cancellare/ritentare alla cieca.
Output backup/readiness conservano prefissi ING_COMPAT degli helper riusati.
Dopo switch properties hash del worker va letto dallo state worker; la vecchia
release compatibility descrive il bind originale conservato e non deve
essere sovrascritta per fingere che sia la configurazione corrente.

Enablement sul VPS ancora non eseguito fino a output PASS. Fonte non attiva.
Prossimo: HUMAN activate della versione APPROVED, readback publication esatta,
watch run vera fino a handoff/lake/UDP materializzazione/search con evidence.
R-SMOKE/R-INSTALL OPEN.


## 2026-09-30 — owner tenant live PASS; adozione refresher/discovery pronta

Operatore: plan/apply owner PASS, tenantENV match=true, stessa immagine,
Flyway invariato31, fonte ancora APPROVED e non attivata.
Backup completo con restore drill PASS conservato:
 /etc/ouf/deploy-snapshots/onboarding-before-managed-identity-jshhzuxc.dump.
Rollback container:
 ouf-onboarding-runtime-tenant-rollback-c0bd1523b4fb.
Receipt /etc/ouf/deploy-snapshots/publication-owner-switch.json PASS.
Refresher/token/worker invariati. Non ripetere owner apply o approval.

Nuovo helper scripts/r4a_adopt_publication_refresher.py, Semantic commit
f48fc39402f0166ff54b8e1cb1f87a8c95d4ae3a; quattro test locali PASS
(installazione atomica mantiene owner/mode e ripristina contenuto originale,
rollback dopo validation failure, failure restore segnala manual e tenta timer,
discovery richiede200 e catalogo vuoto). HTTP nei test simulato,
nessuna prova HTTP live aggiuntiva/CI acquisita fino a output VPS.

PLAN/APPLY legge state preparazione, receipt owner/grant PASS e runtime owner
esatto candidato tenant; richiede fonte/hash APPROVED e code Ingestion
0dfab1e…/properties hash uguale release compatibilità.
Worker flag deve essere assente/false, JSON/command override non accettati.
Code queue/catologo devono essere vuote (publications/schedules/unfinished runs0).
Refresher installato root regular non scrivibile da group/other,
hash esatto af427550…; candidato private root0600 interno snapshots,
hash stato e scope_patch(original) esatti. Unico Python ExecStart deve essere
/opt/ouf/ops/refresh-ingestion-policy-token.py; service Type oneshot,
TriggeredBy timer OUF univoci/attivi. Contratti differenti bloccano prima
dell'installazione e richiedono inventario mirato, non cambio alla cieca.

Apply conserva backup script privato0600 e receipt root0600 STARTING fsync,
sospende timer e service, sostituisce solo script atomicamente con owner/gid/mode
originali, reset-failed/start service e ExecMainStatus0.
Verifica che il token realmente montato sia nuovo e includa config-read,
riusa transport validation per identità/audience/tenant/expiry e scope
object-store preesistente. Nessun bearer/secret/ExecStart completo stampato.
GET effettiva via Gateway LIST deve dare200/items[]/nextAfter vuoto:
prova owner ALLOW module-level, non ancora source-level (catalogo vuoto).
Ripete queue/runtimes/properties/fonte invariati e worker disabled,
ripristina tutti i timer attivi, receipt PASS.

Errore/interrupt dopo riserva: tenta stop timer/service, reinstalla byte
originali con metadata originali, rinnova bearer col vecchio refresher e
valida transport; ripristina timer. Receipt ROLLED_BACK o
MANUAL_RECOVERY_REQUIRED. Se recupero fallisce tenta comunque avvio timer.
Receipt publication-refresher-adoption.json esistente blocca nuova apply:
non cancellarla o ritentare ciecamente. Il token precedente non viene
copiato/restaurato: il bearer di rollback è rinnovato, evitando token scaduti.
Non modifica unit systemd/IAM/DB/worker/source activation.
Adozione VPS ancora non eseguita fino a output operatore PASS.

Dopo discovery200: preparazione/switch worker enabled=true con contesto code
vuote verificato, HUMAN source activate già APPROVED, run reale e
materializzazione UDP/search. R-SMOKE/R-INSTALL OPEN.


## 2026-09-30 — policy33 pubblicata PASS; rollout tenant owner pronto

Operatore: conferma HUMAN PUBBLICO ouf-lab-authorization:33 acquisita.
R4A_PUBLICATION_GRANT_PUBLISH/READBACK PASS: active33, 36 capability/77 grant,
grant Ingestion presente, tutti i precedenti preservati.
Receipt privato:
 /etc/ouf/deploy-snapshots/ingestion-runtime-publication-grant-publication.json.
Non ripubblicare policy, non rifare draft/approval.
Worker/refresher/token invariati, fonte non attivata e ancora APPROVED.

Helper Semantic scripts/r4a_switch_publication_owner.py, commit
6662ae05a4e25e29b1b9212c0a2aa8378ebc30c6; due test locali mock PASS:
backup failure invoca recupero del vecchio runtime e receipt blocca re-entry;
recovery failure conserva MANUAL_RECOVERY_REQUIRED. CI non acquisita.
Plan/apply: adotta il candidato tenant già PASS, stessa immagine live,
OUF_RUNTIME_PUBLICATIONS_TENANT_ID=ouf-lab, nessun nuovo build/schema.
Richiede receipt grant33 PASS, state preparazione root0600,
old stable esatto, candidate ID/created/env/mount/network/launch/image revision
6340d5bf… esatti, root snapshots0700, token owner freschi e readiness200.
Fonte/hash/config devono restare APPROVED/esatti; history Flyway31 e nessun
errore migration. Nomi rollback/failed liberi prima di iniziare.

Receipt publication-owner-switch.json riservata O_EXCL STARTING e fsync
file/directory prima di mutare live. Stop owner, backup completo DB privato e
restore drill su DB scratch con31 migrations usando helper già collaudato;
backup conservato. Nessun restore automatico della DB live.
Controlla history/fonte e candidato ancora identici dopo backup, rename
vecchio runtime conservato, rename/start candidato, readiness e token.
Verifica cambio solo tenantENV, immagine/mount/user/launch/Flyway/fonte/hash
invariati; anonymous managed-file read deve dare401/403.
Restart unless-stopped finale e runtime guard, receipt PASS.

Errore o KeyboardInterrupt durante switch: recupero per ID esatto del vecchio
container tramite helper già esistente, conservando il candidato fallito/log
privato; receipt ROLLED_BACK o MANUAL_RECOVERY_REQUIRED. Receipt anche PASS/
incerto blocca qualunque nuova apply automatica: non cancellarla né ritentare
alla cieca. Backup/restore helper conserva prefissi MANAGED_IDENTITY negli
output, ma in questo passo non cambia il motore identità: solo binding tenant.
Rollout VPS ancora NON eseguito fino a output operatore PASS.

Prossimo dopo owner PASS: adottare refresher privato preparato con verifica
hash e coordinamento timer/service; acquisire bearer nuovo con scope read e
verificare discovery reale200/policy owner ALLOW. Solo dopo worker enablement
e HUMAN activate; smoke ingestione/materializzazione/search ancora aperto.
R-SMOKE/R-INSTALL OPEN.


## 2026-09-30 — draft grant Ingestion acquisito; pubblicazione HUMAN preparata

Operatore: ACTIVE_POLICY_REF=ouf-lab-authorization:32, 36 capability/76 grant.
DRAFT_ID=c957ad91-95f3-43fe-8a43-808e0566f977, revision=0.
Preview una sola aggiunta grant-onboarding-runtime-publication-read-ingestion,
capability change=0, existing grants preserved=true, policy NOT PUBLISHED.
State privato
/etc/ouf/deploy-snapshots/ingestion-runtime-publication-grant-draft.json.
Output specifico Keycloak apply/verify non allegato in questo messaggio;
se eseguita l'intera sequenza precedente, il raggiungimento del draft implica
che i passi precedenti abbiano superato set -e. Non sostituisce readback scope
nel nuovo bearer: attualmente ultimo token osservato config-read=false.
Non creare un altro draft e non ripetere source approval.

Nuovo helper Semantic scripts/r4a_publish_publication_grant.py, commit
cf24008501ea6ba084fb4f46ccf1adc8af587a62; tre test locali con HTTP simulado PASS
(baseline drift blocca POST, timeout conserva receipt e blocca repost,
success verifica grant e baseline), CI non acquisita.
Importa il lifecycle Onboarding pinned 6340d5bf120e09b47c32177656e2c377a4c03640
e il manifest Semantic pinned 20617e48a61b8431a011ff50b237c68d28c1106d.
Verifica hash manifest, state root0600, exact draftId/revision0/desired grant,
target ouf-lab-authorization:33. Login Device Flow HUMAN, legge active32
e verifica 36 capability/76 grant con hash baseline dello state; preview
add-only con zero capability change. Stampa oggetto della decisione:
SERVICE ouf-ingestion, tenant ouf-lab, published-configuration/module ONBOARDING,
validUntil 2036-09-15T07:13:50.968730Z.
Conferma terminale esatta PUBBLICO ouf-lab-authorization:33.

Dopo conferma rilegge active/base/state e preview. Riserva receipt root0600
/etc/ouf/deploy-snapshots/ingestion-runtime-publication-grant-publication.json,
UNVERIFIED_DO_NOT_REPOST, fsync file+directory prima dell'unico POST publish
con If-Match 0. Nessun retry/secondo POST automatico. Se receipt già esiste,
anche PASS o incerto, blocca: prima riconciliare con GET.
Dopo risposta200/PUBLISHED richiede active33, hash capability immutato,
desired grant esatto, hash tutti i grant precedenti invariato; receipt PASS.
Risultato atteso36 capability/77 grant. Nessun token/HUMAN credential in output.
Non modifica worker/tenant/refresher e non attiva la fonte.
Pubblicazione sul VPS ancora NON eseguita fino a output operatore PASS.

Successivamente leggere bundle usando workload, adottare i candidati owner
tenant/refresher con backup/rollback, verificare tokenconfig-read e discovery200,
quindi worker enablement/HUMAN activate/smoke UDP/search. Grant policy publication
e source approval/activation sono decisioni distinte; fonte già APPROVED.
R-SMOKE/R-INSTALL OPEN.


## 2026-09-30 — scope Ingestion non associato; grant runtime preparato per draft HUMAN

Output VPS: descriptor SERVICE/scope=1; grant flat=1/service-bound=1,
subject-only=0, organization-bound=0; principal owner match=0.
Token configuration.read=false. Login interattivo oufadmin nel realm master
riuscito (nessuna password/token forniti in chat); Keycloak GET PASS:
scope e client univoci, binding default=0/optional=0.
Fonte APPROVED, nessuna attivazione, candidati tenant/refresher già PASS e inerti.

Manifest precedente Onboarding catalogue/r4a-udp-published-execution-grants.json
include grant-onboarding-configuration-read-udp per ouf-udp; non è un grant
Ingestion. Nuovo manifest Semantic
catalogue/r4a-ingestion-runtime-publication-grant.json, commit
20617e48a61b8431a011ff50b237c68d28c1106d:
grant-onboarding-runtime-publication-read-ingestion,
capability ouf.onboarding.configuration.read, tenant ouf-lab,
servicePrincipalId ouf-ingestion, subjectId/organizationId null;
ALLOW resourceType published-configuration e module ONBOARDING,
senza vincolo sourceRef perché LIST richiede accesso module-level.
Validità 2026-09-30T00:00:00Z → 2036-09-15T07:13:50.968730Z,
allineata alla scadenza del grant workload UDP precedente.
Manifest validato dal parser lifecycle/plan localmente: un'aggiunta,
baseline invariata. Nessuna nuova policy attiva o evidenza CI.

Comando operatore successivo usa helper Onboarding pinned alla release
6340d5bf120e09b47c32177656e2c377a4c03640:
r4a_keycloak_client_scope_catalogue.py VERIFY (nessuna creazione scope),
r4a_keycloak_client_scope_binding.py PLAN/APPLY/VERIFY OPTIONAL per
ouf-ingestion/configuration.read, preservando gli altri binding.
Scelta OPTIONAL coerente con il refresher già preparato che richiede lo
scope esplicitamente; token attuale resta invariato finché non rinnovato.

Poi r4a_service_grant_lifecycle.py --draft --device-login sul manifest:
login HUMAN ouf-human-admin scope authorization.policy.admin, crea solo draft
e preview add-only (nessuna capability change, preserva grant esistenti).
State privato root0600
/etc/ouf/deploy-snapshots/ingestion-runtime-publication-grant-draft.json.
Il comando rifiuta state già esistente prima di creare il draft; non rilanciare
POST alla cieca dopo esito incerto. In caso di errore dopo POST e prima dello
state, riconciliare draft remoto prima di ritentare.
PUBBLICAZIONE POLICY NON ESEGUITA. Niente source approval/activation/worker.
Tutti i passi VPS ancora da acquisire; non segnare binding/draft PASS finché
l'operatore non restituisce output. Dopo anteprima: conferma HUMAN publish,
readback bundle grant, rollout owner/refresher con backup/rollback,
discovery200, worker e activate. R-SMOKE/R-INSTALL OPEN.


## 2026-09-30 — access inventory acquisito; claim owner verificati e sessione Keycloak da ripristinare

Output VPS: token configuration.read=false; descriptor flat=1 e
descriptor SERVICE/scope=1; grant flat=1, tutti i match diagnostici=0.
Keycloak GET UNAVAILABLE. IAM/live/fonte invariati.
Non è una prova che manchi un grant SERVICE: la diagnostica precedente
confrontava alias multipli e non la precisa precedenza dell'owner.

Verificati i sorgenti della release Onboarding 6340d5bf120e09b47c32177656e2c377a4c03640:
IamSecurityConfiguration usa client_id (trim), fallback azp per SERVICE;
subject usa ouf_subject (trim), fallback sub. AuthorizationPolicy.Grant
accetta subject/principal null o blank come non vincolati; validFrom/validUntil
sono obbligatori, start incluso/end escluso; organizationId se presente
deve corrispondere alla risorsa. Nessuna normalizzazione service principal
ulteriore in questi sorgenti. IAM deployment/claim authenticity e ALLOW
effettivo restano da verificare con la richiesta reale.

Helper aggiornato scripts/r4a_publication_access_inventory.py, commit
a942c81caeaa0b789ad1916d6f98d91be52808cf: precedenza claim conforme,
conteggi separati subject-only/service-bound/organization-bound,
validità obbligatoria. Tre test locali PASS, CI non acquisita.
Keycloak diagnostica container assente/fermo, executable assente,
GET fallito; flag di session renewal quando stderr riconosce errore auth.
--login-keycloak opzionale: solo dopo errore auth riconosciuto e con TTY,
chiede username admin e kcadm config credentials chiede password direttamente
nel terminale. Server interno http://localhost:8080, realm master; non legge
password/env secret e non cambia client/scope/policy. Aggiorna soltanto
la sessione amministrativa locale. Nessun login in assenza del flag.
Fonte sempre APPROVED, candidati binding inerti già PASS; worker disabled.

Correzione comando operatore: sudo python3 -B per evitare __pycache__ root
nella directory temporanea creata dall'utente. La precedente pulizia ha
lasciato /tmp/r4a-publication-access.KjQTkK con sole cache root non rimosse;
rimuovere soltanto quel percorso esatto con sudo rm -rf --, niente wildcard.
Prossimo: acquisire diagnostica precisa/binding Keycloak, eventuale correzione
scope/grant governata; poi rollout tenant/refresher con rollback e discovery200.
R-SMOKE/R-INSTALL OPEN.


## 2026-09-30 — candidati binding PASS; verifica accesso prima del rollout

Output VPS: owner candidate fermo/stessa immagine/tenant ENV preparato PASS,
refresher candidate PASS con script installato e token invariati.
State privato: /etc/ouf/deploy-snapshots/publication-bindings-prepare.json.
Policy reale root activatedAt,bundle,bundleId,bundleVersion,contentHash;
descriptor con allowedActors/operation/requiredScope; grant flat con
servicePrincipalId/subjectId/tenantId/organizationId/validFrom/validUntil.
Capability presente: i precedenti zeri del parser non provano assenza.

Nuovo helper read-only scripts/r4a_publication_access_inventory.py, commit
c6a02fc5026f42e8a5a1313de3220a956f5176f2; due test locali PASS, CI non acquisita.
Conta descriptor SERVICE/scope e grant flat, confronta principal con claim
noti, subject/tenant e finestra temporale. Tutti i conteggi sono diagnostici:
normalizzazione SDK, organization e autorizzazione effettiva non sono provate.
Non aggiungere grant sulla sola base di zero match diagnostici.
Legge Keycloak con kcadm GET e sessione admin già disponibile: realm dal
token issuer, client ouf-ingestion, scope omonimo e associazioni default/optional.
Container default ouf-keycloak, override esplicito --keycloak-container.
Se sessione/container non disponibili stampa UNAVAILABLE senza credenziali:
nessun login automatico e nessuna modifica IAM. Token/bundle/output kcadm
restano in memoria e non sono stampati; solo conteggi/flag.
Nessun avvio candidato/installazione refresher/enable worker/attivazione fonte.
Prossimo: risolvere eventuale binding scope, rollout owner con backup/rollback,
adozione refresher e readback token, discovery reale HTTP200 prima del worker.
Fonte APPROVED; R-SMOKE/R-INSTALL OPEN.


## 2026-09-30 — tenant assente nei binding osservati; candidati owner/refresher pronti

Output VPS READ_ONLY: tenant JSON relaxed count=0, imported property count=0,
unsupported import count=0, command override=false; scope config-read nel
bearer Ingestion=false. GET registry bundle HTTP200, conteggi riconosciuti
descriptor/grant/service/principal-match=0: non concludere assenza prima della
verifica del layout reale del bundle.
Un solo refresher systemd: ouf-ingestion-policy-token.service,
`/opt/ouf/ops/refresh-ingestion-policy-token.py`, SHA256
af4275509ab66841e77a04e1cf04605228d12e627de51e1c043588eb151f50d0.
CAP nel sorgente=false; token host path literal=false (può essere costruito
dinamicamente: non prova che il refresher non aggiorni il token giusto).

Helper scripts/r4a_prepare_publication_bindings.py, Semantic
**946ec112d37cfa466f91c549150a1b396bb422c4**; quattro test locali PASS sulla
trasformazione AST: append scope esistente senza rimuoverlo, aggiunta scope
mancante, UTF8/commenti e blocco su dizionari ambigui/unpack. CI non acquisita.
Preparazione soltanto: stessa immagine owner live 6340d5bf…/user10003,
candidato ouf-onboarding-r4a-runtime-tenant-candidate fermo, aggiunge solo
OUF_RUNTIME_PUBLICATIONS_TENANT_ID=ouf-lab agli env; mount read-only/logging/
launch contract preservati, restart=no e alias ouf-onboarding su ouf-backend.
Rifiuta runtime/settings/env/image/source hash drift o candidato non posseduto.
Non ricostruisce immagine, non avvia container né migrazioni.

Verifica hash esatto del refresher installato; identifica un unico dict
grant_type=client_credentials tramite AST. Nella copia privata aggiunge lo
scope ouf.onboarding.configuration.read, preservando gli altri scope/espressioni
e tutte le parti esterne al dict; parsing sintattico verificato, niente exec
della copia. Il dict può essere riformattato da ast.unparse, semantica delle
altre chiavi preservata. Dizionari multipli/unpack o sorgente cambiato bloccano.
Originale/refresher/systemd/token restano invariati, nessuna credenziale nuova.
Copia .py e stato possono contenere valori privati già presenti nel runtime:
root0600 in directory root0700, non stamparli/uploadarli in chat.
State `/etc/ouf/deploy-snapshots/publication-bindings-prepare.json`.

GET registry mostra soltanto root field names, presence testo capability,
parent field names in caso di capability presente come valore O chiave:
serve a distinguere schema non riconosciuto da assenza vera, non è ALLOW.
Nessuna policy/IAM mutata, fonte ancora APPROVED, niente activate/worker.
Preparazione ancora da eseguire sul VPS fino a output PASS; in seguito:
verificare binding IAM scope e autorità SERVICE nel layout esatto; eventuale
grant governato HUMAN, rollout tenant con backup/rollback, adozione privata
refresher e token nuovo con readback, GET discovery200 e worker enablement,
quindi HUMAN activate e smoke reale. R-SMOKE/R-INSTALL OPEN.


## 2026-09-30 — route LIST installata PASS; binding owner/token da completare

Operatore: plan/apply PASS, ID r4a-onboarding-runtime-publications-list.
Snapshot privato conservato:
`/etc/ouf/deploy-snapshots/publication-list-route-rre_yv8a/routes-before.json`.
IAM_UNCHANGED=true, WORKER_ENABLED=false, SOURCE_ACTIVATION=false.
Receipt `/etc/ouf/deploy-snapshots/runtime-publication-list-route.json`.
Non rilanciare l'apply e non rimuovere receipt/snapshot alla cieca.
Fonte APPROVED/hash invariato. JSON tenant mirato standard PRESENT=false/MATCH=false;
precedente tenant ENV false. Altri property source/alias relaxed non ancora esclusi.

Prossimo helper read-only scripts/r4a_publication_bindings_inventory.py,
Semantic **36cdfb83f5160cccfb98a3565d282a62abf87a0d**, tre test locali PASS,
CI non acquisita. Legge tenant JSON flat/nested con alias normalizzati,
import file .properties dichiarati e flag override command/JVM; stampa solo
presence/count/match, niente JSON/property values. Import non supportati o
alias multipli restano diagnostica incompleta, non prova di tenant assente.

Usa binding registry e bearer workload Ingestion live per GET bundle reale;
stampa HTTP e conteggi configurati della capability
ouf.onboarding.configuration.read, actor SERVICE/SERVICE_IDENTITY, principal
diagnostic match e presence resource conditions. Parsing è diagnostico sui
campi riconosciuti, non ALLOW evaluator: conta anche grant non effettivi, e non
prova validità/status/tenant/resource/assurance/deny né compatibilità di altri
layout. Non aggiungere grant se un conteggio zero deriva da layout non riconosciuto.
Il token continua a mancare dello scope config-read al precedente inventario.

Identifica unit systemd OUF ingestion/token (massimo sei), script Python
ExecStart e hash installato; legge privatamente il sorgente per due soli flag:
scope config-read presente nel codice e token host path corrispondente.
Non stampa ExecStart completo, sorgente, secret o bearer; service/script path
e hash sono metadata operativi. Questo rende concreta la futura correzione
del refresher invece di un bearer manuale non rinnovabile.
Nessuna mutazione scope/client IAM/policy/env/worker/fonte. Dopo output,
preparare correzioni versionate e rollout per tenant/refresher; eventualmente
decisione HUMAN per il grant owner se realmente mancante, preservando :31 e
la fonte già APPROVED. Confermare discovery HTTP200 con workload reale prima
di abilitare worker e attivare fonte. R-SMOKE/R-INSTALL OPEN.


## 2026-09-30 — LIST runtime assente; correzione route pronta

Output VPS: LIST_ROUTE_COUNT=0; ACTIVE/RESOLVE ciascuna una route enabled,
upstream Onboarding inline, OIDC abilitato, owner path preservato, nessun
rewrite/reference/extra condition; required scope ouf.onboarding.configuration.read.
Bearer Ingestion CONFIG_READ_SCOPE_PRESENT=false. Owner TENANT_ENV_PRESENT=false
ma SPRING_APPLICATION_JSON_PRESENT=true: tenant effettivo NON ancora diagnosticato.
Questi sono layer distinti; il 404 LIST è coerente con route mancante, non prova
di policy deny. Fonte resta APPROVED, worker disabilitato, nessuna fonte ACTIVE.

Helper scripts/r4a_install_runtime_publication_list_route.py, Semantic
**78b41071beae7c613e8eedc856865f68a3a6124b**, plan/apply; sei test locali PASS,
CI non acquisita. Plan GET admin solamente, nessun snapshot/receipt/PUT.
Richiede owner live 6340d5bf…/APPROVED/hash, template ACTIVE univoco/upstream/
OIDC/scope esatti, assenza route GET root e assenza del nuovo ID.
La nuova route è GET esatta /api/onboarding/v1/runtime/publications, ID
r4a-onboarding-runtime-publications-list, clone di upstream/plugins/host/
security del template ACTIVE; non modifica ACTIVE/RESOLVE né IAM/grant.
Legge solo il tenant mirato da Spring JSON (flat/nested) e stampa presence/match
bool; nessuna stampa JSON/env/credenziale.

Apply conserva admin route snapshot completo privato root0600 in directory
privata /etc/ouf/deploy-snapshots/publication-list-route-*/routes-before.json,
riserva receipt runtime-publication-list-route.json root0600
UNVERIFIED_DO_NOT_REPUT, singolo PUT nuovo ID e GET readback univoco/contenuto
esatto; fonte/hash devono restare invariati. Admin key/body sono su stdin curl,
niente redirect/retry e nessuna stampa route body o secret. Receipt PASS o
incerto blocca un secondo PUT automatico: riconciliare, non cancellare alla cieca.
Nessuna modifica worker/Onboarding env/DB, nessuna approval/activation.

Blocchi successivi: token Ingestion deve acquisire lo scope configuration.read
tramite configurazione IAM/refresher corretta e owner policy SERVICE adeguata;
verificare GET effettiva (non inventario scope soltanto), incluso module-level
per list e source-level quando esisterà la pubblicazione. Se JSON tenant non
corrisponde, correggere binding owner con rollout governato, non inferire da
assenza ENV. Solo dopo discovery HTTP200 e scope/tenant/owner ALLOW: candidato
worker enabled=true, switch/prova, HUMAN activate e prima run fino a UDP/search.
Route correction ancora non eseguita sul VPS fino a output PASS.
R-SMOKE/R-INSTALL OPEN; approvazione acquisita non va ripetuta.


## 2026-09-30 — code worker vuote; discovery runtime HTTP404

Output VPS: catalogo ACTIVE=0, cinema ACTIVE=0, schedule ACTIVE=0, run non finite=0.
GET SERVICE /api/onboarding/v1/runtime/publications?limit=20&after= restituisce
HTTP404. AUTHORIZED=false del helper significa accesso non dimostrato, NON
diagnosi di diniego IAM/capability. Nessun worker abilitato o fonte attivata.
Fonte resta APPROVED/hash invariato. Non assumere che worker abilitato possa
scoprire la fonte finché questo percorso non risponde correttamente.

RuntimePublicationApi del prodotto Onboarding live 6340d5bf… verificato:
GET root/list, /{sourceId}/active e /resolve sono presenti; page restituisce
items=[]/nextAfter="" quando non ci sono publication ACTIVE (non 404).
Owner richiede SERVICE, tenant configurato tramite
ouf.runtime-publications.tenant-id (default vuoto) e capability
ouf.onboarding.configuration.read sul ResourceContext published-configuration.
Per page/resolve controlla anche accesso module-level prima dei singoli source.
Il 404 può provenire da route assente o instradamento/path errato: prima
verificare APISIX, senza attribuirlo alla policy né aggiungere grant alla cieca.

Helper scripts/r4a_runtime_publication_route_inventory.py, Semantic
**54d3889c8ab3a8566d97bed23245b4ee062791a2**, compilazione Python verificata:
riusa parser admin e matcher route già testati, enumera LIST/ACTIVE/RESOLVE
con conteggio e flag upstream/OIDC/scope/rewrite/references/host/conditions.
Nessuna stampa chiave/bearer/policy/bundle; scope names e flag solamente.
Aggiunge flag espliciti di tenant ENV owner e scope config-read nel bearer
Ingestion. Questi non sostituiscono GET reale/ALLOW owner e non escludono
altri property source per il tenant; niente POST o mutazione IAM/route/env.
Prossimo output richiesto: inventario route; poi correggere il layer realmente
mancante, riprovare discovery e preparare worker candidate/switch controllato.
R-SMOKE/R-INSTALL OPEN; approvazione HUMAN non va ripetuta.


## 2026-09-30 — worker activation live disabilitato; preflight prima dell'abilitazione

Inventario VPS COMPLETE: fonte APPROVED, Ingestion running su revisione attesa,
properties corrispondenti al release; activation.enabled PROPERTY_COUNT=0,
PROPERTY=ABSENT, ENV=ABSENT, nessun Spring JSON/command/JVM override.
application.yml della revisione prodotto 0dfab1e7… verificato via GitHub:
nessun default activation.enabled. ActivationLoop, PublicationGatewayClient e
RunCoordinator richiedono ConditionalOnProperty havingValue=true senza
matchIfMissing. Il worker non è abilitato nella configurazione verificata.
Questo non invalida il PASS consumer in JVM separata né l'approvazione della
fonte, ma impedisce di assumere l'avvio automatico della run dopo publication.

Prima di aggiungere activation.enabled=true e riavviare/sostituire il runtime,
inventariare catalogo ACTIVE e schedule/run preesistenti: il loop scopre e
riconcilia pubblicazioni visibili, non soltanto la fonte cinema.
Helper scripts/r4a_worker_enablement_preflight.py, Semantic
**9e53089f089631a0a1689e5347878671f0638ca5**, compilazione Python verificata.
READ_ONLY: conteggi SQL pubblicazioni ACTIVE (globale e cinema), schedule ACTIVE/
publication_enabled/non blocked e run non finite. GET reale con token SERVICE
Ingestion e trasporto live verso /api/onboarding/v1/runtime/publications?limit=20&after=,
lo stesso endpoint del consumer. Token su stdin curl, nessun redirect/retry o
stampa bundle/credenziali; solo HTTP/count/next-page flag.
COMPLETE non equivale a accesso autorizzato se HTTP diverso da 200 né a inventario
completo del catalogo visibile se nextAfter non vuoto. Conteggi SQL globali e
pagina Gateway autorizzata sono evidenze distinte. Nessun worker abilitato,
nessuna property modificata, fonte ancora non attiva.
Dopo output: risolvere eventuale route/capability/blocker, preparare candidato
con copia privata delle properties e flag esplicito, preservare env/mount/
memoria, prova e switch controllato; poi decisione HUMAN activate e smoke reale.
Conservare tutti i dump/rollback/receipt; R-SMOKE/R-INSTALL OPEN.


## 2026-09-30 — approvazione HUMAN acquisita PASS; attivazione ancora da eseguire

Output VPS: HUMAN_APPROVAL=PASS challenge **4f7a8248-ef40-4dc4-8a64-8a6101c98511**,
owner readback PASS **STATE=APPROVED**, hash congelato invariato.
Receipt privato `/etc/ouf/deploy-snapshots/cinema-approval-confirmation.json`.
SOURCE_ACTIVATION=false. Non rilanciare conferma/rinnovo; conservare receipt
corrente, archive della challenge scaduta e receipt renewal.
La nuova challenge sostituisce quella scaduta nel workflow locale; nessun
cambio retroattivo del record storico scaduto. Compatibilità SERVICE e UDP
corrente restano evidenze acquisite; Onboarding ricontrolla i gate all'activation.

Contratto owner 6340d5bf… verificato: activate richiede HUMAN e versione APPROVED,
latest INGESTION_RUNTIME compatible=true sullo stesso hash, surveillance e gate
UDP; compila/persistisce bundle ACTIVE e proiezioni atomiche e porta versione
ACTIVE. La THS activate legge la challenge e delega all'owner; il TTL della
challenge già CONFIRMED non viene usato come nuovo gate di conferma.
Non confondere publication ACTIVE con run Ingestion o materializzazione PASS.

Prima del POST activate: controllare anche abilitazione worker live. La prova
precedente era JVM separata e non certifica ActivationLoop/RunCoordinator.
Helper `scripts/r4a_activation_worker_inventory.py`, Semantic
**9c65cddf8f563b0413d11b883a03ed8202989aef**, compilazione Python verificata.
READ_ONLY: verifica stato APPROVED/hash, container/revisione Ingestion, mount
properties, hash corrispondente al release receipt; mostra esclusivamente
TRUE/FALSE/ABSENT/UNSUPPORTED per activation.enabled property/env e flag su
Spring JSON/command/JVM override. Non dichiara valore effettivo quando potrebbe
esserci precedenza di altri property source; COMPLETE non equivale a worker
abilitato o ALLOW. Nessun cambio properties/runtime/DB o POST.
Acquisire inventario worker, poi preparare decisione HUMAN di activation e
osservazione run→CDE→handoff→ACK→materializzazione→ricerca. R-SMOKE/R-INSTALL OPEN.


## 2026-09-30 — conferma bloccata per expiry; rinnovo esplicito pronto

Operatore alle 15:14 Europe/Rome: HUMAN_APPROVAL=BLOCKED
APPROVAL_CHALLENGE_EXPIRED_OR_TOO_SHORT, SOURCE_ACTIVATION=false.
Il codice si è arrestato in review.main prima di login/riserva receipt di
conferma/POST confirm. Non dedurre APPROVED: versione attesa ancora IN_REVIEW,
da ricontrollare nel rinnovo. Challenge d56c8e00-de2b-4f47-a940-38b453facf2f
scaduta alle 15:13:21 italiane; non modificare status/expiry via SQL.

Helper scripts/r4a_renew_cinema_approval.py, Semantic
**1bea4f9d68a3062f2d0ea002cf11144496bc024e**, quattro test locali PASS,
CI non acquisita. Rinnovo esplicito con --expired-challenge; verifica vecchio
receipt PASS root0600, card/config/hash esatti, versione IN_REVIEW, challenge
expired e CREATED/EXPIRED, zero decisioni sulla versione, zero altre challenge
CREATED non scadute e assenza receipt di conferma. Ripete i controlli dopo
Device Flow e verifica route/runtime/hash invariati.
Riserva file renewal-{expiredId}.json root0600 prima del POST; archivia senza
sovrascrittura il vecchio receipt in cinema-approval-challenge-expired-{id}.json.
Salva nel receipt corrente UNVERIFIED_DO_NOT_REPOST, poi singolo POST create,
GET card e proof di nuova challenge/config/hash/expiry. A PASS aggiorna anche
il receipt di rinnovo con nuovo ID. Vecchia challenge nel DB rimane immutata.
Timeout o receipt incerto richiedono riconciliazione, niente secondo POST.

Con --review-and-confirm prosegue nella stessa sessione HUMAN (token solo in
memoria) al preparatore di conferma già testato: card riletta, sezioni
decisionali mostrate, richiesta di digitare APPROVO seguito dal NUOVO UUID.
Nessuna conferma automatica dal rinnovo/device login; rifiuto annulla.
Riduce i passaggi fra creazione e decisione senza cambiare TTL o policy.
Non chiama activate e non avvia ingestion. Rinnovo/conferma ancora da eseguire
sul VPS fino a output PASS; R-SMOKE/R-INSTALL OPEN.


## 2026-09-30 — review card acquisita PASS; conferma HUMAN pronta, non eseguita

Operatore: REVIEW=PASS CARD_AND_OWNER_MATCH=true, hash invariato,
challenge d56c8e00-de2b-4f47-a940-38b453facf2f CREATED/non scaduta al controllo.
Mapping cinema→nome e indirizzo→indirizzo IDENTITY, classe Cinema, proprietà
OPEN, ontology 1.0.0 e binding revision/publication set esatti; CSV managed
509 byte, otto righe validate, identità sorgente asset+ordinal.
La limitazione al riordino delle righe riguarda l'identità sorgente;
la risoluzione canonica UDP usa la policy governed separata.
La review PASS certifica corrispondenza tecnica, non consenso HUMAN.
Scadenza challenge 2026-09-30T13:13:21.263Z; non estenderla via SQL.

Helper `scripts/r4a_confirm_cinema_approval.py`, commit
**58a561a94d31d3a69e2ee0c3aaa9922fd30ebf27**: quattro test locali PASS
(cancel senza POST, consenso esplicito e readback, timeout/no-repost,
token privato e solo endpoint confirm); CI non acquisita.
Solo operatore umano nel terminale: nuova login Device Flow, GET card THS
corrente, sezioni decisionali stampate direttamente dalla card e richiesta
di digitare APPROVO seguito dall'UUID challenge. Una risposta differente
annulla senza POST o receipt. Controlla expiry/hash/config prima del consenso
e di nuovo dopo, route/runtime/versione invariati. Riserva receipt root0600
`/etc/ouf/deploy-snapshots/cinema-approval-confirmation.json`, poi singolo
POST /api/trusted-human/v1/approval-challenges/{id}/confirm.
Richiede HTTP200/APPROVED/config e hash invariati, readback versione APPROVED
e una approval_decision APPROVE sullo stesso challenge/versione/hash.
Esito incerto conserva receipt e blocca ogni secondo POST automatico.
Non invia activate, non esegue ingestion; conferma non ancora eseguita
finché l'operatore non fornisce output PASS. È prova diretta del backend THS
con consenso HUMAN locale, non completamento della superficie browser THS.
Dopo PASS: attivazione separata, gate corrente e prima run managed reale.
Se expiry precede conferma, recupero esplicito conservando receipt/challenge.
R-SMOKE/R-INSTALL OPEN.


## 2026-09-30 — challenge cinema e card create PASS; review ancora da completare

Output VPS: challenge **d56c8e00-de2b-4f47-a940-38b453facf2f**,
card PASS con configurazione congelata corrispondente, receipt privato
`/etc/ouf/deploy-snapshots/cinema-approval-challenge.json`.
Scadenza **2026-09-30T13:13:21.263Z** (15:13:21 Europe/Rome).
PREPARE=PASS, SOURCE_APPROVAL=false, SOURCE_ACTIVATION=false.
Non interpretare il device login come decisione di approvazione.
Il blocco preparazione è ora storico/eseguito: non ricreare la challenge.

Prossimo passo: review effettiva prima della decisione HUMAN.
Helper `scripts/r4a_review_cinema_approval.py`, Semantic
**87d8eb17d97b934ee8e9c162a70e5a531fcc4987**, compilazione Python verificata.
Non fa login, HTTP POST, confirm o activate. Verifica receipt root0600,
contesto/hash, configurazione della card esattamente uguale all'owner,
challenge CREATED/non scaduta nel DB in transazione read-only e versione
IN_REVIEW invariata. Mostra soltanto sezioni decisionali della configurazione:
mapping/binding semantici, identità sorgente, access labels, modello di record,
execution e policy UDP resolution/materialization; niente righe CSV/token.
Non è il collaudo di una UI browser THS; il browser shell resta un gate distinto.
Se la challenge scade, richiedere recupero esplicito, conservando il receipt;
non modificare DB/status/expiry per aggirare il TTL. Dopo review segue la
conferma HUMAN sul backend THS verificato, poi attivazione distinta.
R-SMOKE e R-INSTALL restano OPEN.


## 2026-09-30 — route review acquisite; preparatore challenge pronto

Output VPS: CREATE/CARD/CONFIRM/ACTIVATE hanno ciascuna una route, enabled=true,
upstream Onboarding inline, OIDC abilitato, owner path preservato, nessun rewrite,
riferimento upstream/service/plugin config o ulteriore condizione di match.
Host pubblico ammesso e required scope inline ouf.onboarding.configuration.write.
Fonte ancora IN_REVIEW; inventory COMPLETE senza POST/approval/activation.
Questo inventario non prova ALLOW owner né sessione/assurance HUMAN o browser THS.

Helper scripts/r4a_prepare_cinema_approval.py, commit Semantic
ba99054c1652cd7648f44962086d2077b17f8447 (include sei nuovi test locali PASS;
CI non ancora acquisita). Riutilizza il device flow già versionato, con solo
scope ouf.onboarding.configuration.write, stessa identità amministrativa attesa;
token soltanto in memoria e su stdin curl, niente redirect automatici.
Ricontrolla route dopo login, runtime owner e versione/hash congelati.
Non usa credenziali SERVICE per simulare l'approvazione umana.

Crea esclusivamente POST /api/onboarding/v1/sources/managed-cinema-8ec8ae90/
onboarding-versions/68394f42-5c82-4127-a1f3-126516665749/approval-challenges.
Riserva prima del POST un receipt root0600 in directory root0700:
`/etc/ouf/deploy-snapshots/cinema-approval-challenge.json`.
Richiede HTTP201, challenge UUID, CREATED, contesto/hash/ref ed expiry coerenti;
poi GET card /api/trusted-human/v1/approval-challenges/{id}, HTTP200,
configurazione esattamente uguale alla versione congelata.
Card/risposta salvate privatamente, token mai persistito. Stampa solo ID/ref/
expiry e flag, non la configurazione integrale o actor_subject.

Receipt PASS riutilizzabile: nuovo login e GET della stessa card, nessun POST.
Receipt incerto, challenge preesistente senza receipt o challenge scaduta
richiedono riconciliazione; non cancellare il receipt e non rilanciare per
creare doppioni. Un timeout può avere già creato la challenge nell'owner.
Il receipt conservato impedisce un secondo POST automatico di questo helper.

Nessuna challenge è ancora dichiarata creata: attendere output VPS.
Il preparatore non chiama confirm/reject/activate; fonte non approvata/non attiva.
Dopo card verificata occorre review effettiva del contenuto e decisione HUMAN
attraverso il percorso fiduciario; il login device da solo non approva.
La challenge ha TTL: se scade prima della review, recuperare in modo esplicito.
Seguono attivazione e prima run reale; R-SMOKE e R-INSTALL rimangono OPEN.


## 2026-09-30 — UDP corrente PASS; versione IN_REVIEW senza challenge

Evidenza VPS incollata dall'operatore: UDP gate HTTP200/valid=true,
source/hash/tenant/classe/policyRef/policyVersion corrispondenti, coverageRef
presente, live invariato. L'attestazione Ingestion
00006776-5970-4f5c-acf0-145171a6f944 e la prova del consumer deployato su otto
righe restano acquisite. Versione cinema
68394f42-5c82-4127-a1f3-126516665749, fonte managed-cinema-8ec8ae90:
IN_REVIEW, hash congelato invariato, zero approval_challenge per la versione.
Non è stata acquisita l'approvazione finale di questo pacchetto; non dedurre
che siano assenti o invalide precedenti decisioni su schema/mapping semantici.
Nessuna nuova approvazione, attivazione o materializzazione effettuata.

Prossimo comando: scripts/r4a_approval_route_inventory.py (Semantic
66a78a99b6167605934c4f9936666612be784483), con dipendenze
r4a_execution_route_inventory.py e r4a_prepare_frozen_compatibility_probe.py.
Inventaria CREATE/CARD/CONFIRM/ACTIVATE e scope inline; controlla owner/versione
invariati; nessun POST. Quattro test locali PASS, CI non ancora acquisita.
Non certifica ALLOW owner, sessione HUMAN, browser THS o enforcement; riferimenti
service/plugin/upstream, rewrite e condizioni ulteriori richiedono verifica.
Non crea challenge prima della verifica del percorso; non conferma o attiva.

Distinguere il gate HUMAN della configurazione/attivazione della fonte dalla
risoluzione UDP per record: NEW_OBJECT e MATCH non ambiguo procedono secondo
policy governata senza THS per ogni riga; REVIEW_REQUIRED apre review umana.
Identità della pratica, tipo NUOVA_LICENZA/RINNOVO e identità dehor/concessione
sono distinti, con chiavi/relazioni approvate in onboarding. Il flag non decide
l'identità; nuove pratiche possono collegarsi allo stesso dehor, mentre stesso
ID pratica può produrre revisioni/evidenze senza duplicazione dell'oggetto.
Questa è una regola di modellazione concordata, non prova di un deploy aggiuntivo.
Dopo approvazione e attivazione seguono run managed reale, CDE/handoff/ACK,
materializzazione e ricerca. R-SMOKE e R-INSTALL restano OPEN.


Data della baseline: 16 settembre 2026. Snapshot operativo R4a: 27 settembre 2026. Stato: proposta esecutiva basata sui repository, non attestazione di conformità finale.

La priorità è completare la catena eseguibile e autorizzata tra i moduli. I repository contengono una parte consistente del dominio e dei test, ma rimangono codice di integrazione, capability, superfici umane e criteri di accettazione da realizzare. Non è corretto descrivere il lavoro residuo come sola configurazione IAM o collaudo di produzione.

## Avanzamento live al 29 settembre 2026

Lo [stato corrente e il punto esatto di ripresa](handoffs/OUF_HANDOFF_2026-09-29_R4A_PREFLIGHT_TO_INGESTION.md)
superano lo snapshot del 27 settembre qui sotto. UDP live usa l'immagine
`edaba2bff18a2aaf52d1180f21f0e68984cc3437`, Flyway 34, con backup e
container rollback conservati. Policy `ouf-lab-authorization:31`; scope/client
IAM e tre route APISIX di preflight sono attivi. Onboarding live ha token
SERVICE rinnovabile e la versione cinema è `IN_REVIEW`, lock 2, hash
congelato; il preflight HUMAN e la lettura dell'attestazione SERVICE sono
`PASS`, attestazione `57499699-dbc5-419d-a14b-27cd3604ec6f` con **zero**
oggetti ancora indicizzati. **Compatibilità Ingestion ABSENT**, immagine
Ingestion staged diversa dal live; nessuna approval/activation Onboarding o
run Ingestion → UDP → search attestata. L'inventario Ingestion read-only
preparato sul branch Semantic non è stato eseguito per scelta dell'utente.
**R-SMOKE OPEN; R-INSTALL OPEN.** Procedura e backup:
[attivazione R4a](R4A_IDENTITY_LAB_ACTIVATION.md). PR UDP
[#37](https://github.com/GioNob/ouf-udp-object-resolution/pull/37) open;
rollout live e merge sono fatti diversi.

## Snapshot R4a al 27 settembre 2026

[Handoff cross-module per nuova chat](https://github.com/GioNob/ouf-semantic-registry/blob/codex/r4a-smoke-semantic-inventory/docs/handoffs/OUF_HANDOFF_2026-09-27_R4A.md). L'upload HUMAN attraverso picker/Gateway ha prodotto l'asset `8ec8ae90-808a-4d9e-907c-d56de119e376`; il profilo è `4462692b-9c85-446b-b6fd-779f01eab64d`. Semantic ha pubblicato con conferma HUMAN la revisione `51706bed-81e4-4306-aca1-70119821727d` nel set `f92a2e17-30c9-456f-bb12-63afa84f41e6`. Il DRAFT Onboarding `managed-cinema-8ec8ae90` non è submitted/ACTIVE e non c'è evidenza di Ingestion → UDP → search per questo asset. **R-SMOKE OPEN**.

Prerequisito in review: [UDP PR #34](https://github.com/GioNob/ouf-udp-object-resolution/pull/34) rende durevole la review per record e rifiuta weighted non eseguito; [issue #35](https://github.com/GioNob/ouf-udp-object-resolution/issues/35) definisce il **prossimo incremento**, il motore di identità canonica generale. La regola usa proprietà semantiche condivise e vincoli governati, non nomi o frequenza dei valori; uno score non autorizza da solo MATCH. Allineare Onboarding/UDP prima di attivare il DRAFT. Distinguere CI, PR e rollout live. L'ordine e i gate sono dettagliati nell'handoff e nell'[audit PET R4a](audits/OUF_R4A_FINAL_AUDIT_2026-09-27.md). **R-INSTALL OPEN**: gli script lab non sostituiscono clean install, upgrade, restore e CI d'installabilità.

## 1. Autorità e metodo

Fonte normativa: `OUF_Reality_Baseline_Package_v1_7.zip` allegato. Verificati tutti i 323 checksum del pacchetto: nessuna difformità. Gerarchia applicata: Blueprint L0 v0.3 e Cross-Module Alignment Matrix v1.7, PET L1 applicabili, contratti macchina secondo la gerarchia del pacchetto, implementazione ed evidenze. La Terminology Supersession Notice v1.1 governa la terminologia; non sostituisce la semantica dei campi contrattuali.

| Documento L1 | Versione applicabile |
|---|---|
| Source Onboarding, Configuration e THS | 1.6 |
| Authorization e Access Control | 1.5 |
| Urban API Gateway | 1.5 |
| Ingestion Runtime | 1.3 |
| Data Lake, UDP e Urban Object Registry | 1.3 |
| Semantic Model Registry | 1.3 |
| MCP Server | 1.4, Go |

Esaminati i sei repository OUF trovati sotto GioNob: alberi completi, codice e wiring delle aree critiche, workflow CI, test, contratti e documenti di tracciabilità. Authorization è correttamente co-locata in Onboarding: la mancanza di un repository autonomo non è un gap. Nel primo audit del 16 settembre non furono modificati repository/PET né rieseguite suite: gli esiti CI di quella sezione sono storici. La revisione R4a del 27 settembre ha aggiornato documenti, un widget MCP e uno script di inventario su branch di lavoro; i workflow vanno riletti sui rispettivi nuovi HEAD.

La roadmap copre i principali ambiti dei sette PET e le dipendenze cross-module. Non equivale a una verifica esecutiva riga per riga di tutte le acceptance suite. Un'assenza è riferita ai sei repository ispezionati; eventuali componenti esterni non forniti richiedono evidenza nominata. I limiti non diventano implicitamente deroghe.

Classificazione: **CODICE** = implementazione/wiring mancante o incompleto osservato; **INTEGRAZIONE** = componenti presenti ma percorso tra processi non dimostrato; **EVIDENZA** = criterio da provare con test mirati; **AMBIENTE** = infrastruttura/binding e collaudo rappresentativo; **TRACCIABILITÀ** = documentazione/evidence da riconciliare.

## 2. Snapshot autorevole dei repository

| Repository | Commit main esaminato | CI sul commit |
|---|---|---|
| ouf-source-onboarding | `fb2dd51dfc204577a47c1e702f17531dd0709b3c` | Module CI verde, run 35121897270 |
| ouf-ingestion-runtime | `e732d3b17b6a75c35a2b52eedc2d0c586d2d2cf2` | Module CI verde, run 35129774169 |
| ouf-udp-object-resolution | `a18e1c1d1f6add41bb11c975e5f2487f352d1bdb` | Module CI verde, run 34886224933 |
| ouf-api-gateway | `8a1757e5879f73ee60c2786a7f5e2b325741c940` | Control-plane CI verde, run 35123350078 |
| ouf-mcp-server | `6980aac2e113ebbbe5f7b7329f58854d60dd6846` | MCP CI verde, run 35122560464 |
| ouf-semantic-registry | `353d2fc821035c5c3db1c2b142aeb9e3800ec0e3` | Module CI e Authorization pairwise verdi; Semantic Gateway live pairwise rosso |

Fonti CI: [Onboarding](https://github.com/GioNob/ouf-source-onboarding/actions/runs/35121897270), [Ingestion](https://github.com/GioNob/ouf-ingestion-runtime/actions/runs/35129774169), [UDP](https://github.com/GioNob/ouf-udp-object-resolution/actions/runs/34886224933), [Gateway](https://github.com/GioNob/ouf-api-gateway/actions/runs/35123350078), [MCP](https://github.com/GioNob/ouf-mcp-server/actions/runs/35122560464), [Semantic module](https://github.com/GioNob/ouf-semantic-registry/actions/runs/35142826809), [Authorization Semantic](https://github.com/GioNob/ouf-semantic-registry/actions/runs/35142826747), [Semantic Gateway live](https://github.com/GioNob/ouf-semantic-registry/actions/runs/35142826742).

### Primo blocco osservato

Il workflow Semantic Gateway live fallisce con HTTP 403 dopo l'avvio dei container. Lo script invia `X-OUF-Subject` come identità; il `TrustedActorResolver` corrente richiede invece un principal autenticato. Questa incoerenza offre una spiegazione concreta del fallimento, da chiudere con una nuova esecuzione dopo la correzione della fixture. Il vecchio header non deve essere reintrodotto come autorità.

Il workflow usa una **fixture Gateway Java**, non il Gateway APISIX completo, e dipende da schema.gov.it live. Anche una sua futura run verde non proverà automaticamente l'integrazione con il Gateway reale. Fonti: [script live](https://github.com/GioNob/ouf-semantic-registry/blob/353d2fc821035c5c3db1c2b142aeb9e3800ec0e3/pairwise/run-semantic-gateway-live.sh), [resolver](https://github.com/GioNob/ouf-semantic-registry/blob/353d2fc821035c5c3db1c2b142aeb9e3800ec0e3/src/main/java/it/comune/trieste/ouf/semantic/api/TrustedActorResolver.java).

La V9 duplicata è stata rimossa e la CI di modulo è verde: questo problema resta chiuso. Il 403 è un'evidenza nuova e distinta.

## 3. Gap verificati per modulo

### Authorization — priorità trasversale

Presenti: evaluator scenario-neutral, bundle immutabili, active pointer, decision evidence nel Registry, endpoint di distribuzione e cache locale MCP. È preservata l'architettura senza servizio Authorization sincrono sul percorso di ogni richiesta.

**AUT-01 — CODICE: completare il piano amministrativo.** Il controller Authorization esposto distribuisce il bundle ACTIVE; non costituisce il CRUD governato di policy/grant, registrazione capability, authoring con ETag e workflow amministrativo human-only richiesti da §§4.3, 109.1–109.4. I metodi Java di publish/activate non sostituiscono l'API amministrativa e i suoi controlli. Uscita: OpenAPI admin versionata, lifecycle e revoca con audit, stale ETag e actor negativi testati.

**AUT-02 — CODICE/INTEGRAZIONE: shared SDK e enforcement nei servizi.** Il contratto JSON esiste, ma la valutazione Java è nel package Onboarding e MCP ne ha un evaluator Go. Semantic e Ingestion consumano attributi trusted e capability; questo non dimostra lo SDK locale sui bundle previsto da Authorization §§109.1–109.3 e Semantic §160.7. Occorre artifact Java versionato, implementazione Go semanticamente conforme, loader/cache e security adapter nei servizi, con test comuni. Per UDP serve anche il pairwise Authorization e l'adattamento esplicito dei vocaboli legacy: `TrustedHumanContext` richiede ancora `HUMAN_USER`, mentre il contratto consumer recente usa `HUMAN/SERVICE/AI_AGENT`. Non rinominare alla cieca i dati storici.

**AUT-03 — CODICE: completare policy e freshness.** Il motore attuale verifica tenant, capability, actor, scope, soggetto/service principal, organizzazione e validità temporale del grant. Non realizza da solo tutti i vincoli di risorsa, DataAccessLabel, assurance/step-up e permitted detail level/visibility OA previsti da §§36.10, 109.2 e 34.2. La cache MCP conserva il last-known-good in caso di errore ma non applica `max-staleness` al momento della decisione (§109.6); la validità dei grant è un controllo diverso. Uscita: policy di freschezza governata, fail-closed oltre soglia, hash/integrità bundle verificabili, medesimi fixture allow/deny tra linguaggi, coarse allow/backend deny e revoca dimostrati.

**AUT-04 — AMBIENTE:** selezionare/configurare scenario A/B/C, issuer/JWKS, audience, claim mapping, rotazione/revoca e identità workload (§109.5). Avviare questa dipendenza subito, senza bloccare lo sviluppo scenario-neutral.

Fonti: [API distribuzione](https://github.com/GioNob/ouf-source-onboarding/blob/fb2dd51dfc204577a47c1e702f17531dd0709b3c/src/main/java/it/comune/trieste/ouf/onboarding/api/AuthorizationBundleApi.java), [evaluator Java](https://github.com/GioNob/ouf-source-onboarding/blob/fb2dd51dfc204577a47c1e702f17531dd0709b3c/src/main/java/it/comune/trieste/ouf/onboarding/authorization/AuthorizationPolicy.java), [cache MCP](https://github.com/GioNob/ouf-mcp-server/blob/6980aac2e113ebbbe5f7b7329f58854d60dd6846/internal/authorization/cache.go), [guard UDP](https://github.com/GioNob/ouf-udp-object-resolution/blob/a18e1c1d1f6add41bb11c975e5f2487f352d1bdb/src/main/java/it/comune/trieste/ouf/udp/TrustedHumanContext.java).

### Onboarding e THS

Presenti: registry/versioni, mapping, validazione, bundle, challenge umani, CSV/XLSX, quarantena intake, proiezioni runtime, semantic gap, backend protected logs/export.

**ONB-01 — CODICE/INTEGRAZIONE:** completare discovery tecnica automatica attraverso Gateway. `DiscoveryService` gestisce start/claim/complete e snapshot, ma non è presente un worker di discovery sorgenti equivalente ai worker schedulati file-profile ed export. Collegare fetch schema/type/state, retry/recovery e callback Semantic, senza confondere registrazione di uno snapshot con acquisizione automatica. PET §§109.4–109.5, 109.9 e gate §109.17.

**ONB-02 — INTEGRAZIONE:** ACTIVE bundle → proiezione Gateway → compatibilità Ingestion → prima ingestione file o PULL. Verificare exact references, acknowledgement e riattivazione dopo schema drift; la policy operativa va realmente consumata dall'Ingestion, non soltanto serializzata. PET §37 e §109.17; OUF-E2E-001/017/019/020.

**THS-01 — CODICE/INTEGRAZIONE:** realizzare la superficie browser fiduciaria comune e i relativi adapter ai backend owner. Il repository dichiara il browser shell delegato; nessun frontend THS è stato trovato nei sei repository. Completare card cross-module, sessione umana, assurance/freshness, stale challenge e handoff di approvazione; collegare il log store condiviso oltre l'adapter audit Onboarding. Il frontend amministrativo generico resta opzionale, la THS prevista dal PET no. Riferimenti §§101–106, 109.1 e OUF-E2E-014/016.

**ONB-03 — CODICE/EVIDENZA/AMBIENTE:** configuration catalog completo, packaging Helm/NetworkPolicy, upgrade N/N+1, capacity fixture e restore THS con challenge scadute non riattivate. Mancano nel repository gli artefatti operativi completi richiesti da §§109.10–109.16; non sono tutte semplici coordinate esterne. Profilo normativo: 1.000 source, 10.000 type, 500.000 field, concorrenza amministrativa/job dichiarata dal PET.

Fonti: [tracciabilità](https://github.com/GioNob/ouf-source-onboarding/blob/fb2dd51dfc204577a47c1e702f17531dd0709b3c/docs/PET_TRACEABILITY.md), [discovery](https://github.com/GioNob/ouf-source-onboarding/blob/fb2dd51dfc204577a47c1e702f17531dd0709b3c/src/main/java/it/comune/trieste/ouf/onboarding/application/DiscoveryService.java), [OA](https://github.com/GioNob/ouf-source-onboarding/blob/fb2dd51dfc204577a47c1e702f17531dd0709b3c/docs/OPERATIONAL_AWARENESS_TRACEABILITY.md).

### Ingestion Runtime

Presenti: stato run/checkpoint/watermark, outbox/durable ACK, lease/fairness/retry, pipeline, CSV/XLSX e REST/WFS, replay, quarantena e controllo umano. Questa implementazione va riusata.

**ING-01 — CODICE/INTEGRAZIONE, blocco della catena:** collegare gli adapter di produzione per bundle ACTIVE, Semantic preflight, Data Lake, durable handoff UDP, replay e ritorno Onboarding. `RunCoordinator`, `RunExecutionWorker`, `OutboxDispatcher` e `ReplayWorker` sono condizionati alla presenza di port; non risultano bean di produzione per l'intera composizione né un loop schedulato che invochi questi metodi. `@EnableScheduling` da solo non avvia l'ingestion. I test costruiscono percorsi eseguibili ma non dimostrano che il container confezionato li avvii. Uscita: una source ACTIVE viene acquisita senza chiamate manuali ai metodi Java, ACK e watermark rispettano i vincoli, restart e lease recovery provati. PET §§21, 32–37, 80–89, 128 e 139.

**ING-02 — CODICE/INTEGRAZIONE: chiudere il producer Operational Awareness.** La proiezione corrente legge `runtime_issue` e traduce OPEN/altri stati in OPEN/RESOLVED. Non implementa l'intera timeline RETRY_WAIT/RECOVERING/RESOLVED, dedup correlato, misfire, attempt count/nextRetryAt e retention governata ≥30 giorni. Inoltre `summary` conta gli OPEN nella lista limitata: occorre impedire HEALTHY quando incidenti aperti sono fuori dalla pagina/finestra. Query e riepilogo devono avere semantiche distinte e complete. Riferimenti §46.1–46.5, OA-ING-01…06, Matrix §6.

**ING-03 — CODICE/EVIDENZA:** coprire i profili GIS richiesti dal §143.2 oltre REST/WFS e managed CSV/XLSX: OGC API Features, GeoPackage, GeoJSON/JSON-FG e Shapefile ZIP, con layer/CRS e limiti di parser espliciti. Un adapter JSON generico non dimostra automaticamente conformità a questi formati. Procedere per fixture verticali, senza introdurre un nuovo runtime non richiesto.

Fonti: [coordinatore](https://github.com/GioNob/ouf-ingestion-runtime/blob/e732d3b17b6a75c35a2b52eedc2d0c586d2d2cf2/src/main/java/it/comune/trieste/ouf/ingestion/RunCoordinator.java), [worker](https://github.com/GioNob/ouf-ingestion-runtime/blob/e732d3b17b6a75c35a2b52eedc2d0c586d2d2cf2/src/main/java/it/comune/trieste/ouf/ingestion/RunExecutionWorker.java), [runtime ports](https://github.com/GioNob/ouf-ingestion-runtime/blob/e732d3b17b6a75c35a2b52eedc2d0c586d2d2cf2/src/main/java/it/comune/trieste/ouf/ingestion/RuntimePorts.java), [OA service](https://github.com/GioNob/ouf-ingestion-runtime/blob/e732d3b17b6a75c35a2b52eedc2d0c586d2d2cf2/src/main/java/it/comune/trieste/ouf/ingestion/OperationalAwarenessService.java).

### UDP, Object Resolution e Data Lake

Presenti: durable intake, resolution, authority/provenance, materializzazione temporale/delta, graph/spatial/related search, budget condiviso, human merge/split, lake retention/rebuild, replay e prove DR di laboratorio.

**UDP-01 — CODICE/INTEGRAZIONE:** collegare configuration ports ai bundle storici esatti e avviare il resolution worker nel runtime. `ResolutionWorker` è condizionato a due port di configurazione, senza adapter bean/loop di produzione individuati. Dimostrare poi nel medesimo percorso resolution, proprietà, relazioni e spatial: test separati dei materializer non bastano. PET §§95–97, 109.6–109.7.

**UDP-02 — CODICE/EVIDENZA:** chiudere i residui espliciti del registro attuale: cleanup globale query_budget e prova bloat/lock (A42); progressive pruning e protezione ingestion/current read sotto carico agentico (A29/A35); history/asOf/lineage da cold storage (A23); limiti graph completi (A15/E2E-10); N/N+1 (A19); concorrenza materializzazione/merge (A21 v1.0); validTo e non-triplicazione (A06/A02).

**UDP-03 — INTEGRAZIONE/EVIDENZA:** breaking drift senza perdita dello storico, preflight contro registry reali, WFS conversazionale/GIS statico, source-to-serving correlation e capacity gate per nuove fonti (E2E-04/13/15, A07/08/09/10/20).

Il JSON corrente contiene **48 VERIFIED, 16 PARTIAL, 3 VERIFIED-LAB, 2 EXTERNAL-OPEN** su 69 righe. Sono classificazioni del repository, non 48 certificazioni indipendenti di questo audit. Il Markdown riporta ancora conteggi e blocchi precedenti. Non riaprire analytical rejection, delta/bitemporal, retry guard e resilienza replica già implementati; rimangono le prove realmente mancanti.

Fonti: [registro puntuale](https://github.com/GioNob/ouf-udp-object-resolution/blob/a18e1c1d1f6add41bb11c975e5f2487f352d1bdb/docs/pet-traceability-v1.3.json), [resolution worker](https://github.com/GioNob/ouf-udp-object-resolution/blob/a18e1c1d1f6add41bb11c975e5f2487f352d1bdb/src/main/java/it/comune/trieste/ouf/udp/ResolutionWorker.java), [resilienza governor](https://github.com/GioNob/ouf-udp-object-resolution/blob/a18e1c1d1f6add41bb11c975e5f2487f352d1bdb/docs/QUERY_BUDGET_GOVERNOR_RESILIENCE.md).

### Semantic Registry

Presenti: artefatti/revisioni, parser Jena locale, discovery provider, adozione/snapshot, validation/impact, approval/publication atomica, deprecate/retire e risoluzione storica. La V9 è chiusa.

**SEM-01 — INTEGRAZIONE (PARTIAL, evidenza R2c):** correggere il live pairwise e successivamente provarlo contro Gateway e identità conformi. Agganciare Onboarding/Ingestion/UDP agli exact SemanticReference; non basta il test Authorization basato su ispezione di schema e stringhe del resolver. PET §§133–136, 160.7, 160.15.

**SEM-02 — CODICE/EVIDENZA:** chiudere pause/cancel e partial-result semantics dei job; admission per classe/per-provider, fan-out, parser/time/size e publication limits nel configuration catalog; startup/reference-integrity e restore reconciliation. L'API discovery attuale espone creazione, candidates, adoption e providers, senza coprire tutto §160.4. Verificare separatamente la completezza dell'upstream lifecycle §§61/134, distinguendo notice/proposal già presenti dalle operazioni di check/recovery ancora da completare.

**SEM-03 — CODICE/EVIDENZA/AMBIENTE:** Helm/GitOps, dashboard/alert, runbook e configuration reference, capability/job schema e release package; upgrade N/N+1, security scans/SBOM/provenance, restore e profilo 100k artefatti/1M concept con isolamento provider failure. Sono deliverable obbligatori §§160.1, 160.8–160.14 e DoD §160.17 non coperti dalla sola build Maven/container attuale.

Fonti: [API discovery](https://github.com/GioNob/ouf-semantic-registry/blob/353d2fc821035c5c3db1c2b142aeb9e3800ec0e3/src/main/java/it/comune/trieste/ouf/semantic/api/DiscoveryApi.java), [config](https://github.com/GioNob/ouf-semantic-registry/blob/353d2fc821035c5c3db1c2b142aeb9e3800ec0e3/src/main/resources/application.yml), [CI modulo](https://github.com/GioNob/ouf-semantic-registry/blob/353d2fc821035c5c3db1c2b142aeb9e3800ec0e3/.github/workflows/module-ci.yml), [pairwise Authorization](https://github.com/GioNob/ouf-semantic-registry/blob/353d2fc821035c5c3db1c2b142aeb9e3800ec0e3/.github/workflows/authorization-pairwise.yml).

### Gateway

Presenti: config compiler, manifest e route, publication/LKG, adapter Admin API, activation gates, controlli anti-SSRF/identità, manifest HA/network, incident store e route OA channel-neutral.

**GW-01 — INTEGRAZIONE/CODICE:** esercitare compiler/publication/controller con APISIX ed etcd reali, con entrypoint e scheduling/deployment operativo del control plane. Oggi la CI principale esegue Python/pytest e compile config; non avvia la topologia APISIX/etcd. Implementazioni dei port e manifest non sono prova del dataplane. Collegare anche i binding business mancanti man mano che si espande il catalogo.

**GW-02 — CODICE/AMBIENTE:** portare la persistenza incidenti dal riferimento SQLite a un backend di produzione coerente con HA, backup e retention, oppure produrre una soluzione governata che dimostri tali requisiti. Verificare fault reali APISIX/etcd/trust e recovery stesso incidente. Riferimenti PET §34 e T33.9–T33.10; Matrix §6.

**GW-03 — AMBIENTE/EVIDENZA:** prove packet-level default deny e bypass southbound, FQDN/DNS rebinding sul CNI scelto, mTLS/JWKS, etcd quorum/partition/member-loss/restore, rolling N/N+1, drain/HPA/PDB, upload/realtime e capacity. T33.4–T33.16 e OUF-E2E-023/024. Non introdurre un bypass per rendere verde un test.

Fonti: [CI](https://github.com/GioNob/ouf-api-gateway/blob/8a1757e5879f73ee60c2786a7f5e2b325741c940/.github/workflows/ci.yml), [producer OA](https://github.com/GioNob/ouf-api-gateway/blob/8a1757e5879f73ee60c2786a7f5e2b325741c940/docs/GATEWAY_OPERATIONAL_AWARENESS_PRODUCER_TRACEABILITY.md), [etcd acceptance](https://github.com/GioNob/ouf-api-gateway/blob/8a1757e5879f73ee60c2786a7f5e2b325741c940/docs/GATEWAY_1H_BC_TRACEABILITY.md).

### MCP

Presenti: SDK Go, kernel/protocollo, budget/admission, reconciliation/recovery, evidence, retention parziale, maintenance, cache Authorization locale, owner API separate e aggregazione OA Ingestion/Gateway/MCP.

**MCP-01 — CODICE/INTEGRAZIONE:** completare la proiezione del catalogo owner. Il manifest attuale registra **sette tool**, di cui sei OA e `urban.object.related_search`, più un descriptor human-only non esposto. Non copre ancora l'intero serving UDP, onboarding/file/discovery/semantic e proposal/handoff prescritti. Pubblicare per tranche complete owner→Gateway→MCP, con schemi input/output, versioni e classificazione; non annunciare tool senza backend. Protected Operations non diventa un tool. Riferimenti PET §§91–96, 114, 122 e OUF-E2E-022.

**MCP-02 — CODICE/INTEGRAZIONE:** completare OA con finestra since/until, cursor pagination, timeline, durata/attempt/retry, distinguendo denial, redaction e producer unavailable. `ouf.system.status` descrive oggi il solo stato MCP, mentre §33.2 richiede lo snapshot dei moduli visibili; `operations.summary` aggrega già tre producer. Chiarire e coprire il requisito senza cancellare l'owner API channel-neutral. `operations.explain` è ancora legato all'Ingestion: aggiungere dispatch owner-aware per gli incidenti degli altri producer previsti. Gate OA-MCP-01…08 e OA-CN.

**MCP-03 — EVIDENZA/CODICE:** aggiungere gate di conformance ufficiale della versione MCP normativa e interoperabilità con client SDK indipendente; non individuati nella CI corrente. Non basta la dipendenza dall'SDK ufficiale. Completare retention invariant-preserving dei manifest snapshot dove dovuta (esplicitamente pending nel registro), mantenendo le prove già ottenute per audit/attempt/evidence. Packaging OCI/SBOM/provenance e collaudo HA/DR restano parte della chiusura.

Fonti: [manifest attuale](https://github.com/GioNob/ouf-mcp-server/blob/6980aac2e113ebbbe5f7b7329f58854d60dd6846/internal/manifest/capabilities.json), [CI](https://github.com/GioNob/ouf-mcp-server/blob/6980aac2e113ebbbe5f7b7329f58854d60dd6846/.github/workflows/ci.yml), [OA aggregazione](https://github.com/GioNob/ouf-mcp-server/blob/6980aac2e113ebbbe5f7b7329f58854d60dd6846/docs/MCP_OPERATIONAL_AWARENESS_AGGREGATION_TRACEABILITY.md), [retention](https://github.com/GioNob/ouf-mcp-server/blob/6980aac2e113ebbbe5f7b7329f58854d60dd6846/docs/MCP_1G_RETENTION_CHAIN_TRACEABILITY.md).

## 4. Roadmap ordinata e criteri di uscita

Le tranche seguenti sono una proposta di sequenza, non nuove prescrizioni dei PET. Non assegno date o percentuali complessive senza capacità del team, ambiente e consuntivi: darebbero una precisione ingannevole.

| Ordine | Tranche e obiettivo | Dipendenze | Criterio di uscita verificabile |
|---|---|---|---|
| R0, immediata | Ripristinare Semantic live pairwise; registro unico requisiti/evidenze | Nessuna | Fixture autenticata senza header spoofing; workflow verde; baseline v1.7 e commit/CI associati a ogni claim |
| R1a | Authorization↔UDP e shared SDK/security adapter Java | R0 | HUMAN/legacy boundary esplicito; deny backend con coarse allow; bundle pinning e contesto trusted su tutti i servizi |
| R1b | Authorization amministrativa, policy completa e cache freshness | R1a, sviluppabile in parte insieme | Admin human-only/ETag/audit, resource/DataAccessLabel/assurance/detail policy, max-staleness, rotazione bundle e fixture comuni |
| R2a | Onboarding→Ingestion reale | R1; Gateway di integrazione | ACTIVE bundle genera prima run file e PULL senza invocazioni manuali dei worker; preflight exact e schedule versionato |
| R2b | Ingestion→Lake/UDP→serving reale | R2a | Persistenza raw, ACK, watermark, resolution/materialization e lettura autorizzata nello stesso percorso; crash/retry senza perdita/duplicazione |
| R2c | Semantic↔Onboarding↔runtime | R1, R2 | Discovery/adoption/publication governate; cambio ACTIVE non cambia la run pinned; historical replay esatto |
| R2d | Fondazioni geografiche e decisione CRS | R2c | CRS configurabile per Comune; trasformazioni effettive e ordine assi; grigliati verificati/versionati; scelta umana converti/rigetta registrata nel profilo |
| R2e | GeoPackage → oggetti e relazioni | R2d | Telecamere e armadi acquisiti come oggetti con identità stabile; relazione per identificativo, navigabile nei due sensi; riferimenti mancanti/ambigui espliciti |
| R3 | Operational Awareness completa, priorità prodotto | R1 e R2a/b | OUF-OA-001…006 e OUF-OA-CN-001…005: fault offline, retry/dedup/recovery, misfire, retention, partial/deny, medesimo owner via MCP/API |
| R4a | Catalogo capability e THS comune | R1/R2; può procedere con R3 | Onboarding/file, serving e proposal esposti via Gateway/MCP; decisioni umane e protected logs confinati a THS browser |
| R4b | Residui di dominio | R2; per moduli indipendenti | UDP PARTIAL chiusi; altri formati/casi GIS previsti oltre GeoPackage; Semantic job/limits/upstream lifecycle e Onboarding discovery automatica completi |
| R5 | Gate riproducibili di release | Avvio già in R0, chiusura dopo R4 | Upgrade N/N+1, contract diff, protocol/interoperability, negative security, supply chain e package operativo conformi per ciascun modulo |
| R6 | Acceptance cross-module e rappresentativa | R1–R5; IAM/CNI/storage pronti | 25 scenari E2E, suite locali PET, HA/fault/load/restore, RPO/RTO misurati e sign-off delle evidenze |

Il lavoro di piattaforma va avviato **subito in parallelo alla pianificazione**: scelta IAM A/B/C, ambiente APISIX/etcd, PostgreSQL/object storage, CNI/NetworkPolicy, log/metrics e client THS. Il PET consente fixture conformi nello sviluppo; la vera integrazione e l'accettazione richiedono binding effettivi. Questa è una dipendenza da governare, non un motivo per fermare ogni sviluppo.

Ogni tranche deve produrre PR limitate, riferimenti PET/Matrix, test negativi e criterio di uscita. Nessun nuovo microservizio Authorization, incident hub o Agent Host interno è necessario per questa roadmap.

## 5. Piano delle evidenze cross-module

Il catalogo normativo è E2E v0.3 incluso nel pacchetto. Nei sei repository non è stato trovato un runner comune tracciato ai 25 ID canonici. Alcuni scenari hanno prove locali o pairwise; non vanno contati come full-path senza un report che colleghi versioni, risultati ed evidenze.

| Gruppo | ID canonici | Quando chiudere |
|---|---|---|
| Attivazione, acquisizione, identità oggetto e storico | 001, 002, 003, 004, 006, 015, 017, 019, 020 | R2, poi regressione R6 |
| WFS conversazionale e dati personali | 005, 007 | R4a/b + R1 |
| Tool routing, retry, budget e confine analitico | 008, 009, 010, 011, 012, 013 | R4a/b, multi-Pod rappresentativo R6 |
| Decisione umana e protected logs | 014, 016 | R4a |
| Coarse/fine deny, M2M e capability projection | 018, 021, 022 | R1/R4a |
| Egress, LKG e error/correlation full-path | 023, 024, 025 | R2/R5, CNI/etcd reali R6 |
| Operational Awareness e channel neutrality | OUF-OA-001…006, OUF-OA-CN-001…005 | R3, validazione ambiente R6 |

R6 deve includere anche i target dei PET, non solo happy path: isolamento sotto carico, multi-worker/multi-Pod, revoca credenziali/policy, producer outage, failover, restore e continuità dei riferimenti storici. Per UDP esistono già restore/PITR e performance di laboratorio: si riusano, senza spacciare il laboratorio per accettazione dei target di produzione.

## 6. Correzioni necessarie alla tracciabilità

1. Il documento UDP `PET_TRACEABILITY.md` mantiene conteggi vecchi e richiama un pacchetto precedente; il JSON attuale ha esiti più avanzati. Riconciliare il riepilogo conservando lo storico.
2. Semantic `evidence/acceptance-traceability.json` indica "Semantic Model Registry v1.4", mentre il PET nel pacchetto v1.7 è v1.3. Correggere il riferimento documentale, senza attribuire una nuova versione al PET.
3. Le note iniziali MCP/Gateway marcano pending funzioni poi realizzate. Ogni gap va chiuso con link al commit/test successivo, non lasciato come falso arretrato.
4. Le CI pairwise pin-nano revisioni precise dei peer, talvolta precedenti ai main qui esaminati. È corretto per riproducibilità, ma serve anche una matrice della combinazione candidata al rilascio: un vecchio pin verde non dimostra compatibilità con tutti i main correnti.
5. Distinguere test su stringhe/config, test di modulo con stub, integrazione tra processi reali e prova nell'ambiente rappresentativo. Il nome "pairwise" da solo non determina il livello di evidenza.

Registro minimo per ogni requisito: documento/versione/sezione/ID, owner, stato, codice e commit, test e livello, CI/artifact/hash, gap residuo, dipendenze, criterio di chiusura. Gli ID della presente roadmap sono locali al report e non rinumerano i PET. La Matrix L0 resta normativa: si aggiorna con change control se cambia il contratto/ownership; il registro di implementazione registra l'avanzamento.

Regola operativa permanente per il seguito: **una decisione risolta non viene riaperta senza nuova evidenza da repository o CI**. Una build verde non modifica i requisiti dei PET; una voce "CHIUSO" nel gap register del documento di progetto indica completezza della specifica, non implementazione avvenuta.

## 7. Prossimo passo raccomandato

R0 e R1a sono consegnati; R1b ha ora implementazione centrale e controlli owner nei percorsi descritti in `R1B_OWNER_ENFORCEMENT_EVIDENCE.md`. R2a ora consegna admission automatica file/PULL, bundle ACTIVE verificato, preflight esatto e schedule versionato. R2b ora dimostra il percorso CSV/REST fino alla lettura autorizzata e al lineage, con ACK e watermark verificati fra processi. R2d consegna ora le fondazioni CRS governate descritte in `R2D_GOVERNED_CRS_EVIDENCE.md`. R2e aggiunge ora GeoPackage, identità stabile per feature e relazioni telecamere↔armadi; evidenze in `R2E_GEOPACKAGE_RELATIONSHIPS_EVIDENCE.md`. Il prossimo incremento è **R3**, mantenendo separati i gate di ambiente e le superfici umane ancora mancanti. I controlli owner implementati devono essere mantenuti nel percorso; l'accettazione completa dei restanti domini/proiezioni e dell'identità reale rimane tracciata in AUT-03/AUT-04, senza riaprire decisioni già risolte.


## Avanzamento R1b — 17 settembre 2026

Implementazione centrale Authorization e cache consegnata; evidenze in `R1B_AUTHORIZATION_EVIDENCE.md`. AUT-01 chiuso per l'API amministrativa verificata in laboratorio. AUT-02 e AUT-03 restano parziali per enforcement e proiezioni owner-specific, con audit esplicito in `R1B_ENDPOINT_COVERAGE_AUDIT.md`. AUT-04 resta il gate IAM/THS reale. Lo stato `IMPLEMENTED_WITH_INTEGRATION_GAPS` non equivale ad accettazione completa del PET o a chiusura di tutti i requisiti della fase.

## Follow-up R1b: enforcement owner — 17 settembre 2026

Corretti tutti i percorsi Semantic mediante matrice capability fail-closed, le proiezioni UDP incluse query graph/related/spatial, la Operational Awareness Ingestion e i protected log Onboarding/Ingestion. Evidenze immutabili e PR: `R1B_OWNER_ENFORCEMENT_EVIDENCE.md`. AUT-02 soddisfa il criterio SDK/adapter/conformità e backend deny; AUT-03 conserva l'accettazione completa delle proiezioni owner nei restanti domini e canali. AUT-04 resta il gate IAM/THS reale. I test di modulo non chiudono R2/R6.

## Avanzamento R2a — 17 settembre 2026

Admission automatica e preflight file/PULL implementati; evidenze in `R2A_ACTIVATION_EVIDENCE.md`. Il test tra processi usa Onboarding reale e il JAR di produzione Ingestion, con Gateway/Semantic/identità di laboratorio dichiarati. ONB-02 e ING-01 avanzano a PARTIAL: ACK, acquisizione completa, watermark, replay e ritorno Onboarding restano da verificare in R2b/c. La successiva evidenza R2b è descritta sotto; RUNNING mantiene il solo significato di admission.

## Aggiornamento R2b — 17 settembre 2026

Scenario CSV/REST implementato, verificato e mergiato: il lettore autorizzato trova i valori acquisiti, il campo riservato è omesso e il lineage è consultabile. La prova completa usa Onboarding, JAR Ingestion, UDP, PostgreSQL/PostGIS e MinIO reali; verifica perdita ACK, HTTP 202 senza watermark, kill/restart e assenza di duplicati. Evidenze e commit in `R2B_SERVING_EVIDENCE.md` e `r2b` del registro JSON.

**Limite del risultato:** Gateway HTTP, sorgenti, Semantic e identità/approvazione sono fixture dichiarate. APISIX, adapter di invocazione southbound e managed storage reali restano GW-01; IAM/THS, profili estesi e ambiente rappresentativo restano gate aperti. La superficie utilizzabile verificata è l’API; browser/MCP e presentazione integrata dello stato restano R4/R3. ONB-02, ING-01 e UDP-01 rimangono PARTIAL rispetto ai criteri PET completi.

Per ogni incremento, accanto a commit e CI, dichiarare persona, obiettivo, superficie, risultato osservabile e verifica. Prossimo passo della sequenza: R3; questa regola umana resta vincolante anche nei blocchi infrastrutturali.


## R2c — pubblicazioni governate e riferimenti storici

L'incremento collega il processo Semantic reale ai processi Onboarding, Ingestion e UDP. Il provider esterno, Gateway e identità/decisioni umane restano fixture dichiarate. Le correzioni permettono di assegnare una versione a una bozza adottata, vincolano il candidato alla richiesta di discovery e impediscono di risolvere un gap Onboarding prima della pubblicazione.

Il cambio ACTIVE è verificato durante consegne non ancora confermate: snapshot precedenti immutati, nuova pubblicazione distinta, recupero outbox al riavvio, lookup storico esatto senza fallback. L'accesso storico distingue revisioni pubblicate poi deprecate/ritirate da bozze mai pubblicate. I riferimenti contrattuali sono visibili anche negli snapshot nel formato R2.

**Prova di replay R2c:** oltre alla riconsegna outbox, il piano umano UDP REPRODUCE deve verificare i byte Lake del vecchio handoff, risolvere i suoi riferimenti storici e completare la materializzazione mentre la nuova configurazione è ACTIVE. Il confronto deve usare il checksum del file di evidenza, distinto dal contentHash canonico. L’esecuzione deve essere idempotente e conservare il riferimento al raw sorgente. **Gate generale ancora aperto:** questo non certifica REPRODUCE/REPROCESS dei raw in quarantena Ingestion; ReplayExecutionPort e la conservazione dei metadati di riproduzione restano nel completamento operativo R3/ING-01.

**Verifica umana:** il lettore autorizzato consulta gli oggetti e la provenienza dei dati; una nuova configurazione non riscrive la configurazione delle elaborazioni precedenti. Superficie verificata: API. La superficie THS e il percorso operatore completo restano R4a.

## Requisiti GIS concordati per R2d/R2e/R3/R4a

- Ogni feature (geometria e riga attributi) alimenta un oggetto canonico secondo mapping e identità approvati. Riacquisire aggiorna senza duplicare. Telecamera→armadio usa l'identificativo dell'armadio; target assenti restano irrisolti e si riconciliano al successivo caricamento, target ambigui richiedono revisione.
- CRS sorgente per layer conservato; CRS comunale configurabile (Trieste EPSG:6708), distinto dal CRS di esposizione. Ordine assi, area d'uso, precisione e trasformazione sono espliciti; nessuna semplice rietichettatura SRID.
- CRS diverso: l'umano sceglie conversione o rigetto dopo aver visto operazione proposta, accuratezza dichiarata o non nota e limitazioni. La scelta vale nel profilo versionato anche per fonti dinamiche; cambi di CRS/operazione/condizioni richiedono nuova decisione. CRS ignoto non viene indovinato.
- Grigliati: inventario per coppia CRS e territorio, verifica condizioni d'uso, versione/checksum fissati, conservazione dell'originale e test su punti noti. Nessun ripiego silenzioso verso trasformazioni meno accurate se manca una risorsa richiesta. Disponibilità dei grigliati IGM/locali non ancora attestata.
- R3 espone progressi, errori geometrici/CRS e collegamenti irrisolti. R4a fornisce anteprima cartografica, importazione guidata, schede e relazioni navigabili. La geocodifica conserva fonte/precisione e converte nel CRS comunale; punto del civico e perimetro effettivo del dehor devono restare distinguibili.
- R4b conserva i restanti formati e casi GIS prescritti dai PET. La CI tecnica di R2e non equivale alla completa accettazione umana, che richiede R4a.

R2c: **36 verifiche PASS** nello scenario tra quattro owner, incluso REPRODUCE UDP. Evidenze, SHA dei consumer e limiti in `R2C_GOVERNED_PUBLICATION_EVIDENCE.md` e nel registro JSON. R2d è implementato e verificato nel perimetro delle fondazioni CRS; R2e verifica ora GeoPackage e relazioni con 25 controlli fra quattro owner; R3 è il prossimo incremento; i gate generali elencati restano aperti.

SEM-01 e UDP-03 passano a PARTIAL per le prove R2c; i residui sono esplicitati nel registro. Il live pairwise già ripristinato in R0 non viene riaperto.


## Stato R2d — fondazioni CRS governate

R2d implementa CRS comunale configurabile (test EPSG:6708 e altro Comune), ordine assi esplicito, operazioni PROJ effettive approvate, originale e provenance, verifiche di area/punti/grigliati e scelta CONVERT/REJECT congelata nel profilo. Il loop automatico rifiuta geometrie incompatibili prima di creare oggetti vuoti. La scheda owner THS espone la decisione; il serving owner espone canonico e CRS/provenance con omissione autorizzata.

Evidenze e limiti: `R2D_GOVERNED_CRS_EVIDENCE.md` e sezione `r2d` del registro. I grigliati sono stati collaudati con una risorsa sintetica: **la disponibilità/licenza/precisione dei grigliati IGM per Trieste resta un gate di ambiente**. La fixture 6708 non certifica equivalenza geodetica RDN2008/WGS84. I gruppi PET generali restano aperti dove mancano formati, percorsi e acceptance.

R2e è ora descritto nella sezione seguente. R3 e R4a completano osservabilità, remediation e superfici umane cartografiche.

## Stato R2e — GeoPackage e relazioni governate

R2e consegna profilazione dei layer, scelta esplicita di layer/chiavi, acquisizione bounded in sola lettura, identità per feature stabile nel ricaricamento, geometria originale/canonica e riferimenti storici. Le relazioni telecamere↔armadi sono navigabili nei due sensi; i target tardivi vengono riconciliati con la regola originale, quelli ambigui restano in revisione e i riferimenti cambiati ritirano gli edge precedenti.

La CI fra quattro owner, PostGIS e MinIO contiene **25 verifiche PASS**. Fixture Gateway/identità dichiarate, commit, run, limiti e stato dei merge sono riportati in [R2E_GEOPACKAGE_RELATIONSHIPS_EVIDENCE.md](R2E_GEOPACKAGE_RELATIONSHIPS_EVIDENCE.md) e nella sezione `r2e` del registro JSON. La geometria sorgente mappata richiede il permesso geometrico anche in current, history e search.

Restano 2D simple features e limiti di parser espliciti; altri formati/casi sono R4b. Nessun grigliato IGM reale o collaudo territoriale è attestato. La UI cartografica resta R4a; prossimo incremento **R3 — Operational Awareness**.

Ogni sprint deve consultare tutti i sette PET e L0: [regola obbligatoria e manifest delle fonti](OUF_SPRINT_PET_ALIGNMENT.md).

## Ripresa R4a — 30 settembre: inventario Ingestion e sonda candidata

L’operatore ha eseguito l’inventario rimasto sospeso: **PASS**. Flyway live/staged
è 14/14; lo staged `e3f04f1…` differisce dal live. Policy
`ouf-lab-authorization:31`: un descriptor SERVICE e un grant SERVICE per
`ouf.ingestion.configuration.attest`, zero altri grant. I conteggi non provano
che il bearer effettivo sia il principal destinatario del grant né che la route
risponda; la compatibilità della versione resta non attestata.

La [PR Ingestion #33](https://github.com/GioNob/ouf-ingestion-runtime/pull/33),
commit `da941666643d83f9f417da85be91fb3b10d4db01`, aggiunge una sonda nel jar
che usa mapper, adapter e validator dei contratti CDE/lineage/handoff di
produzione. Verifica hash/stato congelato, riferimenti Semantic esatti, integrità
dell’asset, identità sorgente e tutte le righe. Lo script versionato costruisce
una candidata isolata, senza avviare Spring/Flyway/worker o scrivere run,
materializzazioni e attestazioni. Il PASS della sonda avrà
`candidateDeployed=false` e `attestationSubmitted=false`.

La prima revisione passa i sei test Python, i 23 test consumer/regressione Java,
la suite funzionale con PostgreSQL e il restore drill. Trivy ha rilevato
CVE-2026-68497 nella dipendenza Jackson Databind 2.21.4 ereditata dal ramo: la BOM
è stata aggiornata a 2.21.6, senza abbassare il gate HIGH/CRITICAL. Sul commit aggiornato sono PASS la CI dedicata, la suite completa Ingestion
con PostgreSQL, il restore drill e il gate supply-chain (Trivy e chart).
Il risultato VPS rimane da acquisire, distinto dalle prove CI. Il prossimo
intervento dell’operatore è la preparazione/prova candidata; seguono backup
verificato, switch/rollback, prova contro l’immagine effettivamente live e POST
SERVICE governata. Poi approvazione HUMAN in THS, attivazione e filiera fino
alla ricerca UDP. **R-SMOKE e R-INSTALL restano OPEN**.

Contratto, parametri, limiti e procedura:
[R4A_FROZEN_CONFIGURATION_COMPATIBILITY.md](https://github.com/GioNob/ouf-ingestion-runtime/blob/da941666643d83f9f417da85be91fb3b10d4db01/docs/R4A_FROZEN_CONFIGURATION_COMPATIBILITY.md).

## Aggiornamento operatore — 30 settembre: trasporto della sonda

Il primo tentativo su `da941666…` è arrivato al build e poi si è fermato con
`ING_COMPAT_TRANSPORT_CONFIG_REQUIRED`: tutte le tre proprietà activation erano
assenti dal file summary live. Nessuno switch o POST attestazione. Il successivo
`docker exec cat` è una diagnostica non adatta all'immagine distroless, non prova
assenza del token. La lettura del bind mount sul VPS ha confermato file presente,
SERVICE/client Ingestion/tenant/issuer/audience corrispondenti, TTL 277 secondi
all'osservazione e scope `authorization.bundle.read`,
`ouf.ingestion.configuration.attest`, `ouf.internal.object-storage.read`,
`email`, `profile`. Claim decodificati: diagnostica, non autenticazione.

La correzione Ingestion è `160e3391862083bd8779aed69493484f5d2b086d` sulla PR #33. Dieci test Python locali PASS;
CI sulla nuova revisione avviata, risultato non ancora acquisito in questo aggiornamento.
Nessuna modifica Java, DB, IAM/policy o configurazione live.
Il preparatore legge i riferimenti registry HTTPS/token già presenti, controlla
le dipendenze prima del build e crea un file temporaneo solo per la sonda con
Gateway origin, token-file e tenant esplicito (`--tenant-id ouf-lab`). File root:10002,
0440, montato read-only al posto delle proprietà solo nel container usa-e-getta;
nessun token copiato, file rimosso anche in caso di errore della sonda. Directory
auth esistente in sola lettura, rinnovo token conservato. Non aggiungere le
proprietà al summary live né abilitare activation/execution durante questa prova.

L'accesso Semantic esatto resta da provare: nessuno scope Semantic esplicito è
presente nell'output. Il consumer deve attraversare Gateway con owner enforcement;
un 401/403/404 richiede correzione governata di IAM/grant/route/owner, mai accesso
diretto allo storage o attestazione sintetica. La versione resta congelata e
compatibilità non attestata. **R-SMOKE e R-INSTALL OPEN.**

### Correzione dell'ordine di preparazione — 30 settembre

Il tentativo operatore su `160e339…` ha superato il controllo trasporto iniziale,
poi si è fermato con `UnboundLocalError`: la creazione del file temporaneo usava
`current` prima della sua assegnazione. Stop prima del build, del file trasporto
e dei GET consumer; nessuno switch/POST. Le CI precedenti erano tutte verdi,
ma non esercitavano il main del preparatore.

Correzione attuale Ingestion `1eb70c4c3aa6de7e3c3f1ffc4f78ca7b63331872`: il file temporaneo viene creato
solo dopo build, snapshot live verificato e rilettura della versione congelata.
Dodici test Python locali PASS, inclusi due nuovi test del main completo con
operazioni VPS simulate (successo/proof e diniego/cleanup). CI nuova revisione
avviata; il risultato VPS resta da acquisire. Il comando aggiornato, dove presente,
fissa questa revisione e mantiene `--tenant-id ouf-lab`. Non rieseguire i comandi
storici su `160e339…`. R-SMOKE/R-INSTALL restano OPEN e nessuna attestazione positiva.

### Sonda VPS — correzione del contratto d'identità sorgente

Tentativo su `1eb70c4…`: trasporto PASS, build raggiunto, poi
`ING_COMPAT_IDENTITY_POLICY_UNSUPPORTED`. Nessun switch/attestazione;
stop prima dei GET Semantic/asset. Il probe confondeva
`extractionProfile.runtime.rowIdentityBasis=ASSET_AND_ROW_ORDINAL` con
`sourceObjectIdentityPolicy.strategy`, il cui valore normativo è
`MANAGED_DETERMINISTIC` per questa policy. Contratto owner e
`ManagedFileService` Onboarding confermano campi `[$managedRowOrdinal]` e
normalizzazione `normalization://managed-file/asset-row-ordinal-v1`.

Correzione Ingestion `dae05e6d4e8aa5dcd2f1ff2b6642b1ff4356dd37` (PR #33): verifica quella combinazione
esatta, supporta anche NATIVE_KEY/COMPOSITE_NATIVE_KEY con cardinalità/campi
validi; non modifica la configurazione congelata o l'hash. Quattro regressioni
Java aggiunte e fixture managed corretta; dodici test Python PASS, CI Java 21
nuova revisione in corso al momento dell'aggiornamento. Il comando aggiornato,
dove presente, punta alla nuova revisione. Compatibilità live non attestata;
accesso Gateway/Semantic ancora non provato. R-SMOKE/R-INSTALL OPEN.

### Gate storico: 403 alla risoluzione Semantic

L'operatore ha eseguito la sonda `dae05e6…`: trasporto PASS, build raggiunto,
identità superata, `ING_ACTIVATION_GATEWAY_403` durante Semantic preflight,
prima di lettura asset e validazione righe. Nessuno switch/POST compatibilità.
La route versionata `r2b-semantic-reference` usa `ouf.semantic.read`; lo scope
richiesto manca nel token osservato. Assegnazione Keycloak, descriptor SERVICE,
grant effettivo e route live rimangono evidenze distinte, non dedurre ALLOW.

Inventario read-only in PR #33, commit `e4e1f095c53b7ec4819b8d99fcd79769027330bb`: scope corrente,
descriptor/grant del PolicyBundle ACTIVE e scope DEFAULT/OPTIONAL del client
Ingestion nel realm tramite la sessione kcadm esistente. Nessun build, rinnovo
credenziali, GET dei dati, modifica IAM/policy o attestazione. Una sessione scaduta
stampa `KCADM_SESSION_EXPIRED`, non i dettagli/credenziali. Tre test locali PASS
su conteggi senza identità, sessione scaduta e Keycloak solo GET. Prossimo passo:
acquisire questo inventario e preparare correzione governata del prerequisito
mancante; eventuale nuova policy si pubblica solo con conferma HUMAN THS.
R-SMOKE/R-INSTALL OPEN, compatibilità ancora non attestata.

### Inventario Semantic acquisito dall'operatore — 30 settembre

`SEM_TOKEN_SCOPE_PRESENT=false`, TTL 259 secondi alla lettura. Descriptor unico,
scope corretto e SERVICE ammesso. Un solo grant, SERVICE, zero corrispondenze con
client/sub di Ingestion e zero subject-grant corrispondenti, nessun constraint
nel grant esistente. Il bridge Semantic versionato risolve servicePrincipalId da
client_id/azp: il selector esistente non copre il client Ingestion. Non sostituire
il grant preesistente, aggiungere la nuova autorizzazione con il percorso HUMAN
THS preservando il resto del bundle quando la proposta sarà pronta.

Keycloak: `KCADM_SESSION_EXPIRED`; nessuna evidenza ancora su esistenza e binding
DEFAULT/OPTIONAL dello scope. Il runbook già dispone di
`scripts/r4a_refresh_kcadm_session.py`, che usa le variabili bootstrap soltanto
nel container Keycloak senza stamparle. Prossimo intervento: refresh della
sessione amministrativa e ripetizione dell'inventario esistente; nessuna modifica
a scope/client/grant/route, nessun build o POST compatibilità. Seguiranno piano
IAM additivo per lo scope read e proposta di grant SERVICE governata. R-SMOKE e
R-INSTALL OPEN; versione e hash congelati preservati.

### Sessione kcadm ripristinata e piano scope Ingestion

Output operatore: refresh PASS e inventario Keycloak PASS; un solo scope
`ouf.semantic.read`, un solo client `ouf-ingestion`, assegnazioni DEFAULT e
OPTIONAL entrambe false. Token senza scope, TTL 254 secondi all'osservazione;
descriptor SERVICE valido, grant con selector non corrispondente come sopra.
Nessun cambio IAM/policy è stato eseguito da questo inventario.

Prossimo intervento: reconciler scope esistente in sequenza plan/apply/verify,
solo `ouf.semantic.read` come DEFAULT di Ingestion. Preserva le assegnazioni
agli altri scope; non ricrea scope/client, mapper o secret. Nel lab il client
credentials usa gli scope default e il token esistente rimane invariato fino
al normale rinnovo: DEFAULT=true non implica immediatamente token scope=true.
Ripetere l'inventario senza build; non inviare attestazioni o attivare la fonte.

Il grant va aggiunto separatamente, preservando quello esistente: capability
`ouf.semantic.read`, tenant `ouf-lab`, servicePrincipalId `ouf-ingestion`.
La API PermissionProposal supporta UPSERT di un grant e conserva il resto del
PolicyBundle; nessuna proposta è ancora creata. Verificare scadenza, hash,
base ACTIVE e accesso Gateway/delegation prima di proporla; pubblicazione
richiede conferma HUMAN THS, mai SQL o script storico di publish diretto.
R-SMOKE/R-INSTALL OPEN.

### Scope Semantic applicato e proposta grant PENDING — 30 settembre

Operatore: reconciler plan/apply/verify PASS, `ouf.semantic.read` DEFAULT=true e
OPTIONAL=false su `ouf-ingestion`; nessuna drift al verify. Subito dopo il bearer
esistente aveva scope assente e TTL 269 secondi: verifica del token rinnovato
ancora da acquisire, non diagnosticare fallimento del binding da quel solo output.
Inventario policy invariato: descriptor SERVICE valido, un grant non corrispondente.

L'assistente ha usato il plugin OUF MCP con il collegamento `ouf-admin`, prima
ROLES (catalogo preservato), poi GRANTS filtrato `subjectId=ouf-ingestion`:
policyRef :31, hash `sha256:3c043bf01564b1fc0647d8114220b8cd114d0d6d701371e2fd9cb44ff4ec3bc7`,
proiezione vuota; una proiezione configurata non è prova di permessi effettivi.
Creata via `authorization.permissions.propose` una UPSERT di un solo grant:
`grant-r4a-semantic-read-ingestion-20260930`, capability `ouf.semantic.read`,
tenant `ouf-lab`, servicePrincipalId `ouf-ingestion`, subject/organization null,
constraints null, validFrom 2026-09-30T00:00:00Z, validUntil 2027-09-30T00:00:00Z.
Il resto del PolicyBundle e il ruolo admin restano preservati. Nessun publish.

Ricevuta: proposta `44817d9d-e66c-4c02-8ef5-53ca2b2548e9`, revision 0, PENDING,
expiresAt **2026-09-30T08:28:55.717003Z** (10:28:55 Europe/Rome).
[Conferma HUMAN nel THS](https://api.ouf-lab.it/trusted-human/authorization/?proposal=44817d9d-e66c-4c02-8ef5-53ca2b2548e9).
La scadenza della proposta è distinta dalla validUntil del grant. Il chatbot non
conferma; dopo la decisione leggere la ricevuta con `authorization.proposal.read`
(same account), verificare finalPolicyRef e rinnovo token. Se la proposta è scaduta,
non usare il link come conferma valida: preparare una nuova proposta sullo stato
ACTIVE corrente. Compatibilità, prova Semantic/asset e rollout ancora aperti;
R-SMOKE/R-INSTALL OPEN. Nessuna attestazione o attivazione della fonte.

### Conferma HUMAN verificata: policy :32 pubblicata

L'utente ha confermato la proposta nel THS. L'assistente ha letto la ricevuta
attraverso OUF MCP (account ouf-admin): proposta
`44817d9d-e66c-4c02-8ef5-53ca2b2548e9`, revision **1**, **PUBLISHED**,
finalPolicyRef **ouf-lab-authorization:32**. Non ricreare o riconfermare la proposta.
Lo scope DEFAULT resta quello applicato/verificato dall'operatore. Questo chiude
la pubblicazione governata del grant Semantic Ingestion, non la prova consumer.

La candidata corrente PR #33 è `e4e1f095c53b7ec4819b8d99fcd79769027330bb`: tutte le 14 run CI
push/PR risultano completed/success alla verifica, comprese suite consumer,
module/security/recovery e pairwise. Nessun deploy live né attestazione positiva.
Prossimo passo VPS: rileggere inventario, richiedere scope Semantic presente nel
bearer ruotato prima del build e rieseguire la sonda sulla revisione corrente.
L'inventario non equivale a decisione ALLOW: la sonda deve risolvere riferimenti,
leggere l'asset e validare tutte le righe. La sessione amministrativa kcadm non
serve a quelle letture; un suo eventuale expiry nell'inventario resta separato
quando il token e il grant sono già verificati. Conservare versione/hash congelati,
backup e rollback. R-SMOKE/R-INSTALL OPEN.

### Stato corrente — Semantic superato, lettura asset bloccata da 404

Ultimo output VPS: scope Semantic presente nel token ruotato (TTL 296s),
DEFAULT=true, OPTIONAL=false; due grant SERVICE e un selector client corrispondente.
Policy :32 già pubblicata via conferma HUMAN. Sonda e4e1f095…: trasporto PASS,
preflight Semantic superato, poi **ING_EXECUTION_GATEWAY_404** alla lettura
Gateway dell'asset. Nessuna validazione completa delle otto righe, attestazione,
attivazione o switch. R-SMOKE/R-INSTALL restano OPEN; versione/hash congelati
e backup/rollback restano preservati.

Riscontro statico, da confrontare con il runtime: ExecutionGatewayClient legge
GET `/internal/object-storage/v1/content?ref=…`; il binding Gateway
`onboarding-managed-file-read` a 3014f3c… punta a
`/api/internal/v1/onboarding/managed-files/content` su Onboarding. Quel controller
non è nel tree della baseline Onboarding f74c3a9…. La capability owner
`ouf.object-storage.content.read` richiede lo scope `ouf.internal.object-storage.read` del bearer.
Questo non dimostra che la route live coincida con quel binding, né che
l'asset manchi. Non ricaricare il file, cambiare hash o introdurre accesso diretto
allo storage per aggirare il 404.

PR #33 aggiornata a **0dfab1e7b2253fd939088259ea61754d6e56706c**: aggiunto
`scripts/r4a_execution_route_inventory.py`, solo Docker inspect e GET
dell'Admin API APISIX; nessun GET del contenuto asset, build, cambio IAM/route,
deploy o POST attestazione. Stampa conteggi/booleani su route esatta, rewrite,
upstream, scope e revisione owner. Chiave Admin letta dal bind config.yaml
(oppure file esplicito), passata al curl via stdin, mai argv/output o file temporanei.
Layout chiave non letterale/ambiguo blocca senza stampare il valore.
Diciannove test Python locali PASS, inclusi parser fail-closed, GET esatto,
formati Admin API e assenza chiave da argv/output. CI nuova revisione avviata,
non ancora acquisita. Prossimo passo: inventario live, poi correzione governata
del binding/owner effettivamente osservato.

### Inventario route: chiave esplicita nel comando

Output VPS acquisito: `EXEC_READ_OWNER_BASELINE_REVISION_MATCH=true`, poi
`APISIX_ADMIN_KEY_LAYOUT_UNSUPPORTED`. La lettura dell'Admin API non è stata
eseguita: non sono ancora disponibili evidenze sulle route attive. La baseline
Onboarding f74c3a9… è invece confermata dall'immagine live.

Il parser ristretto del bind config.yaml non accetta il layout osservato.
Usare l'opzione già disponibile `--admin-key /opt/ouf/secrets/apisix-admin-key`:
è lo stesso riferimento del rollout Gateway versionato
`scripts/r4a_semantic_rdf_route_rollout.py` a 3014f3c….
La presenza del file sul VPS sarà verificata dalla lettura, non è stata dedotta
dalla sola fonte GitHub. La chiave resta in memoria/stdin, non in argv/output;
il layout YAML non viene interpretato. Nessuna modifica a configurazione, token,
route, policy, asset, immagini live o attestazioni.

Revisione inventario invariata: `0dfab1e7b2253fd939088259ea61754d6e56706c`.
Tutte le 14 run CI push/PR ora completed/success. I 19 test Python locali erano
già PASS. Il blocco consumer resta `ING_EXECUTION_GATEWAY_404`; compatibilità,
R-SMOKE e R-INSTALL restano aperti.

### Gate corrente confermato — endpoint owner assente nella release live

Output VPS: baseline owner=true, una route GET esatta, rewrite al vecchio
endpoint content=true, upstream Onboarding=true, nessun upstream_id,
OIDC=true, required scope match=true, rewrite=true; inventario completo
in sola lettura. La route invia la richiesta al controller assente nel tree
f74c3a9…. Non vi è evidenza che l'asset sia perso. Il preflight Semantic
è già superato; otto righe, compatibilità live, attestazione Ingestion e
filiera Ingestion → UDP → search rimangono aperti.

Correzione della precedente nota sullo scope: `ouf.object-storage.content.read`
è il nome della capability owner, mentre il descriptor richiede proprio
`ouf.internal.object-storage.read`, già presente nel token. Questa distinzione
non richiede un cambio IAM. Il backend dovrà comunque effettuare la sua
decisione effettiva di autorizzazione dopo il ripristino dell'endpoint.

I rami intake (5d770df…) e identity live (f74c3a9…) divergono dal parent
21de5f2…; il rollout identity ha lasciato fuori l'implementazione intake.
Preparata **Onboarding PR #39**, branch
`codex/r4a-onboarding-managed-identity-integration`, commit
**6340d5bf120e09b47c32177656e2c377a4c03640**, con entrambi i parent nella storia. Ripristina
intake/picker/delegation e conserva gate UDP e PermissionProposal publication.
Cinque file modificati da entrambi i rami integrati con merge a tre vie;
conflitti risolti sulle tre superfici sessione HUMAN e sulle due validazioni,
entrambe mantenute. Il test storico che attivava un managed DRAFT incompleto
resta sostituito dalla regressione fail-closed già introdotta nell'intake.

Tutte le **quattro CI push/PR completed/success** alla verifica: module e
browser. La CI del container verifica GET owner anonimo 403 con
ONB_AUTHORIZATION_DENIED oltre alla readiness, quindi rileva anche una
release priva del controller. Nessun deploy VPS effettuato.
Procedura specifica nel repo Onboarding:
`docs/R4A_MANAGED_IDENTITY_INTEGRATION.md`. Non eseguire il vecchio rollout
picker: riguarda un'altra fase e il suo controllo git non risolve questo caso.

Il DB live è già V31, ma V30/V31 mancano nel tree identity f74c3a9….
La candidata conserva i file originali intake: occorre confrontare ogni
script/checksum con la storia Flyway effettiva, non dichiarare migrazioni
invariate dal solo confronto con quel tree. Preflight Semantic versionato a
**721d81a25c194615eb0ddf48fca8b9bd0a281ef9**, quattro test locali PASS e test aggiunto alla CI:
`scripts/r4a_managed_identity_release_inventory.py`. Solo git read/ancestor,
Docker inspect e SQL BEGIN READ ONLY/ROLLBACK; verifica entrambe le storie,
baseline, env/mount read-only, metadati file per UID/GID 10003 e migrazioni
esatte già applicate. Stampa conteggi/booleani; nessun valore o identità.
Un mismatch blocca i prerequisiti della release. La CI Semantic nuova è in
corso; CI della candidata Onboarding già verde.

Acquisire questo inventario prima di build/candidato fermo e switch con
backup recuperabile. Conservare i rollback e i dump già registrati,
versione/hash congelati e attestazione UDP esistente. La prova isolata e
il gate d'identità devono restare insieme alla lettura managed. Nessun
restore automatico del DB, reupload, cambio hash o aggiramento diretto
dello storage. R-SMOKE/R-INSTALL OPEN.

### Preflight release acquisito PASS — candidata da costruire e lasciare ferma

L'operatore ha eseguito il preflight sulla candidata Onboarding
6340d5bf120e09b47c32177656e2c377a4c03640: entrambe le storie preservate,
31 migrazioni tutte corrispondenti al DB, baseline live attiva, quattro env
staging presenti, mount credenziali read-only e file privati leggibili,
gateway/token managed presenti, gateway/token identity presenti e leggibili.
RELEASE_PREREQUISITES=PASS, LIVE_UNCHANGED=true. Nessun nuovo prerequisito
IAM/configurazione va introdotto per riparare l'endpoint mancante.

Automazione Semantic aggiornata a **6fc4ed9b4e74cb038250c609f3688b4276aadb31**:
`scripts/r4a_prepare_managed_identity_candidate.py`. Fissa la candidata
Onboarding alla revisione verde; ripete l'inventario prima e dopo la build da
git archive, verifica label immagine e contratto di avvio, e blocca se live,
env, mount, migrazioni o impostazioni Docker cambiano. Crea solo il container
`ouf-onboarding-r4a-managed-identity-candidate`, in stato created,
restart=no, alias ouf-onboarding, UID/GID 10003, con env/mount/log del live.
Non lo avvia, non cambia il live, non accede al bucket e non invia attestazioni.

Un candidato già presente è riutilizzato solo se fermo e identico; eventuale
drift blocca senza sostituzione. Il readback deve confermare l'ID creato,
immagine, env, mount, rete e stato. In caso d'errore ripulisce solo il proprio
container ancora fermo e non tocca container sostituiti da altri operatori.
Il file env temporaneo è privato e rimosso nel finally.

Manifest privato root 0600:
`/etc/ouf/deploy-snapshots/onboarding-managed-identity-release.json`;
contiene lo snapshot Docker live (anche env segreti), candidate ID e image ID.
Non stamparlo, condividerlo o committarlo. Le build log sono in una directory
root 0700 sotto /etc/ouf/deploy-snapshots, il solo percorso viene stampato; conservate su errore.
Lo stato esistente non viene sovrascritto; deve corrispondere al live/candidato.
Non modificare `identity-images.json` e non eliminare i rollback precedenti.

Otto test Python locali PASS e discovery CI estesa a entrambi gli script:
checksum/migrazioni, mount privati, preparazione completa, drift durante build,
cleanup per ID e candidati preesistenti. CI preparatore avviata, non ancora
acquisita; le quattro CI della candidata Onboarding restano completed/success.
Prossimo passo: acquisire BUILDING → CANDIDATE PASS/STOPPED; poi backup
recuperabile e switch con verifica di readiness, endpoint e Flyway invariata.
Il preparatore non crea backup e non esegue lo switch. Compatibilità consumer,
attestazione e HUMAN approval/activation restano gate successivi.
Versione/hash congelati, attestazione UDP e backup/rollback preservati;
R-SMOKE/R-INSTALL OPEN.

### Correzione percorso privato del preparatore — stop prima del build

Tentativo VPS su 6fc4ed9…: OWNER_STAGE_DIRECTORY_UNSAFE, prima di git archive,
build, candidato o file di stato. Il preflight precedente resta PASS; non
dedurre drift del runtime, IAM o migrazioni da questo blocco.

Il preparatore aveva usato /opt/ouf/r4a-stage come parent per stato contenente
env segreti: quel percorso di staging condiviso non soddisfa il requisito
root-only. Correzione **76073d25ceff9f8a54684fee214071c564423b83**: usa la directory già prevista dai rollout
Onboarding `/etc/ouf/deploy-snapshots`, richiede directory reale (non symlink),
owner root e modo esatto 0700. Non modifica permessi/owner del vecchio staging.
Stato ora `/etc/ouf/deploy-snapshots/onboarding-managed-identity-release.json`,
root 0600; log ed env temporanei nelle sottodirectory private della stessa root.
Non esiste uno stato precedente creato dal tentativo bloccato da spostare.

Nove test locali PASS, inclusa regressione che blocca directory user-owned,
accessibile ad altri o symlink prima di inspect/build. CI della correzione
avviata; candidata Onboarding invariata 6340d5bf… con CI già verde.
Il comando corrente è aggiornato alla correzione. Ancora nessun build o
candidato fermo attestato dall'operatore, nessuno switch/POST. Versione/hash,
live, IAM, route, asset e rollback precedenti restano invariati.
R-SMOKE/R-INSTALL OPEN.

### Build eseguita, stop nel lookup candidato — correzione indipendente dagli errori Docker

Output operatore su 76073d2…: preflight PASS prima e dopo la build, poi
OWNER_DOCKER_INSPECT_FAILED nel lookup opzionale del candidato. La build è
terminata e il controllo di provenance/contratto di avvio è superato;
nessuna nuova creazione candidato attestata, nessun avvio/switch o POST.
Log privato conservato:
`/etc/ouf/deploy-snapshots/onboarding-managed-identity-bmvgzvr2/build.log`.
Non stampare lo stato/env privato. Il live e il DB restano invariati.

Il vecchio helper distingueva assenza da guasto leggendo due stringhe d'errore
di docker inspect; l'output redatto non permette di confermare quale errore
Docker specifico si sia presentato. Correzione Semantic **6eb09c963b39cfc67401d15e39397df4663f456a**:
docker container ls --all con formato Names, confronto per nome esatto,
poi inspect solo quando il candidato esiste. Il risultato vuoto è assenza;
un errore del daemon o un race dell'inspect blocca, senza trattarlo come
assenza e senza mostrarne i dettagli. Nessuna dipendenza dalla lingua/forma
del messaggio No such object/container/image.

Dieci test Python locali PASS, inclusi assenza/nome simile/nome esatto,
errore daemon fail-closed, main completo, drift e cleanup per ID.
Candidata Onboarding invariata 6340d5bf…, stessa immagine/tag: la build ripetuta
può riusare la cache, i due preflight restano obbligatori. Comando corrente
aggiornato alla nuova revisione. CI helper avviata, non ancora acquisita;
le quattro CI Onboarding erano già verdi.
Nessuna modifica IAM/route/asset/versione congelata o ai rollback;
R-SMOKE/R-INSTALL OPEN. Prossimo risultato richiesto: CANDIDATE PASS STOPPED=true,
prima di preparare il backup/switch.

### Candidato combinato preparato PASS — switch ancora da eseguire

Output VPS acquisito: inventario PASS prima/dopo build, CANDIDATE=PASS
STOPPED=true ENV_AND_MOUNTS_PRESERVED=true; PREPARE=PASS LIVE_UNCHANGED=true
DB_UNCHANGED=true. Il candidato fermo è
`ouf-onboarding-r4a-managed-identity-candidate`, revisione Onboarding
6340d5bf120e09b47c32177656e2c377a4c03640. Stato privato root 0600:
`/etc/ouf/deploy-snapshots/onboarding-managed-identity-release.json`.
Build log del tentativo riuscito:
`/etc/ouf/deploy-snapshots/onboarding-managed-identity-h4pcqei_/build.log`.
Non stampare i contenuti; i log precedenti restano conservati.

Automazione switch Semantic a **13feb098621f3c08889f875e92c0d381905a7b7a**:
`scripts/r4a_switch_managed_identity_candidate.py`, modalità plan/apply.
Verifica manifest/ID, snapshot live, env/mount/rete, label/contratto immagine,
31 checksum, token managed e identity freschi con client/scopo/tenant/issuer/
audience corretti, readiness live e versione/hash congelati.
Plan è di sola lettura e non crea receipt/backup. Apply ferma il live,
crea un dump custom dell'intero DB Onboarding e prova pg_restore in un
database temporaneo, rimosso nel finally; exige 31 migrazioni ripristinate.
Rilegge storia Flyway e versione congelata dopo backup e dopo avvio.

Conserva il vecchio container come
`ouf-onboarding-managed-identity-rollback-<old-id-prefix>`; rinomina e avvia
solo il candidato verificato, richiede readiness, stesso ID/immagine/env/mount,
storia Flyway identica e versione congelata invariata. Verifica diniego anonimo
401/403 sul port owner content e freshness dei due token, poi imposta
restart=unless-stopped. Il diniego anonimo non è lettura positiva dell'asset:
la sonda consumer resta il gate seguente, prima di attestazioni.

Receipt privato root 0600:
`/etc/ouf/deploy-snapshots/onboarding-managed-identity-switch.json`;
conserva fase, ID, nome rollback/failed, dump e storia migration. Un receipt
preesistente blocca per evitare doppio switch. In caso di errore tenta ritorno
al vecchio runtime per ID, conserva il nuovo failed e fino a 120 righe di log
in file privato. Se il backup fallisce prima dello swap, riavvia l'originale.
Non rimuove il vecchio rollback e non ripristina automaticamente il DB;
un ID live estraneo blocca il recupero senza toccare quel container.
Ogni fallimento va analizzato dal suo output redatto e stato privato,
senza rilanciare alla cieca un receipt già esistente.

Sedici test Python locali PASS (aggiunti plan senza scritture, apply completo,
backup-before-swap, rollback su backup/start fallito, ID estraneo e cleanup
scratch con dump privato conservato); discovery CI già comprende la suite.
CI nuova helper avviata, non ancora acquisita. Le quattro CI Onboarding
della revisione candidata sono completed/success alla verifica.
Nessuno switch effettivo ancora attestato, nessun cambio route/IAM/asset,
nessun POST compatibilità/approval/activation. Prossimo passo: plan/apply
sulla versione e hash congelati; poi prova Ingestion, mai attivare la fonte
in base alla sola readiness. R-SMOKE/R-INSTALL OPEN.

## 2026-09-30 — switch managed intake + identity eseguito: PASS

L'output VPS di plan/apply conferma Onboarding live a
**6340d5bf120e09b47c32177656e2c377a4c03640**, Flyway **31**,
versione congelata e hash invariati. Backup completo ripristinato con successo
nel database temporaneo e conservato:
`/etc/ouf/deploy-snapshots/onboarding-before-managed-identity-_6czsruy.dump`.
Container precedente conservato:
`ouf-onboarding-managed-identity-rollback-260c56287584`.
Receipt privato:
`/etc/ouf/deploy-snapshots/onboarding-managed-identity-switch.json`.
Non stampare dump, receipt, token, env o snapshot privati.

Il GET anonimo owner content restituisce **401**: il controllo di accesso
nega l'accesso anonimo. La lettura autenticata dell'asset da Ingestion e la
validazione delle otto righe restano da verificare. Nessun POST attestazione
è stato eseguito, nessuna approval/activation della fonte.

Il precedente blocco switch è storico ed eseguito: non rilanciarlo.
Prossimo gate: sonda Ingestion isolata alla revisione
**0dfab1e7b2253fd939088259ea61754d6e56706c** (14 CI completed/success
verificate), con Semantic storico esatto e lettura via Execution Gateway.
Policy pubblicata ouf-lab-authorization:32 e scope ouf.semantic.read nel
token restano le evidenze IAM precedenti. La sonda non cambia il live
Ingestion, non migra DB e non invia attestazioni.

Solo dopo PASS della sonda: rilascio controllato Ingestion e prova positiva
del consumer live prima dell'attestazione; approval/activation restano HUMAN THS.
R-SMOKE/R-INSTALL **OPEN**.

## 2026-09-30 — sonda frozen Ingestion PASS, otto righe validate

Output VPS acquisito: R4A_ING_COMPAT_TRANSPORT=PASS; sonda reale
R4A_ING_COMPAT_PROBE=PASS VALIDATED_ROWS=8, candidato
**0dfab1e7b2253fd939088259ea61754d6e56706c**.
La lettura via Gateway e la validazione del consumer isolato hanno superato
il gate sulla versione congelata. Il candidato **non è deployato**:
LIVE_CONTAINER_UNCHANGED=true, ATTESTATION_POST=false.
Proof locale privato: `/opt/ouf/r4a-stage/ingestion-compatibility-probe.json`;
non stamparne contenuti o altri snapshot privati.

Il precedente blocco sonda è storico ed eseguito. Prossimo passo:
inventario read-only del contratto live/candidato Ingestion e delle sole
presenze delle proprietà/env activation; la sonda ha usato proprietà
temporanee senza modificare il live. L'inventario serve alla preparazione
del rilascio controllato, con backup e rollback, e non è uno switch.
Prima dell'attestazione occorre prova positiva del consumer deployato.
Approval/activation della fonte restano HUMAN THS; R-SMOKE/R-INSTALL OPEN.

## 2026-09-30 — inventario rilascio Ingestion acquisito; preparatore candidato fermo

Inventario VPS COMPLETE read-only: proof revisione/otto righe PASS, baseline live,
runtime running, provenance immagine, contratto di avvio, rete e mount read-only
tutti true; Flyway **14**. Le tre proprietà activation gateway-url/token-file/
tenant-id sono assenti sia nel file sia nell'ambiente del live.

Helper Semantic **f763a5b7949f26298d9dde11a470528bdead096f**:
`scripts/r4a_prepare_ingestion_candidate.py`. Riusa l'immagine immutabile
della proof candidata **0dfab1e7b2253fd939088259ea61754d6e56706c**;
non ricostruisce e non modifica il branch/revisione prodotto Ingestion.
La dipendenza `scripts/r4a_prepare_frozen_compatibility_probe.py` è copia
esatta del helper Ingestion a 0dfab1e7… (per import/tests autonomi del repo
Semantic); nel preparatore sono usati solo inspect, GET/SQL read-only e
validazione trasporto/proof, non il main di build/sonda.

Richiede directory root 0700 `/etc/ouf/deploy-snapshots`, proof PASS esatta,
baseline/image label/launch contract, rete, mount, env univoci, Flyway14,
versione/hash congelati e token trasporto fresco. Copia tutte le properties
live in file privato root:10002 mode0440, aggiungendo esclusivamente le tre
chiavi activation derivate dal trasporto verificato. Nessun valore/token/env
è stampato; il file properties live rimane identico.

Crea solo `ouf-ingestion-r4a-compatibility-candidate` con restart=no, env
identici, mount read-only identici salvo la copia properties e alias
ouf-ingestion; non lo avvia. Verifica readback e snapshot live, conserva
stato privato root0600:
`/etc/ouf/deploy-snapshots/ingestion-compatibility-release.json`.
Riuso consentito solo per candidato/state posseduti e coincidenti;
drift blocca. Un fallimento dopo creazione rimuove soltanto il proprio ID
ancora fermo; il file temporaneo env viene sempre rimosso.
Cinque nuovi test PASS, 17 test locali dei preparatori PASS; CI nuova revisione
non ancora acquisita. Nessun candidato preparato attestato dal VPS finora.

Il blocco inventario precedente è storico ed eseguito. Prossimo gate:
CANDIDATE PASS STOPPED=true, prima di predisporre backup/switch Ingestion.
Nessun live switch, migrazione, attestazione, approval/activation in questo
blocco. R-SMOKE/R-INSTALL OPEN.

## 2026-09-30 — preparazione Ingestion bloccata dal contratto runtime

Output VPS acquisito:
R4A_ING_COMPAT_RELEASE_PREPARE=BLOCKED CODE=ING_RUNTIME_SETTINGS_UNSUPPORTED.
Il guard precede la creazione di directory/file del candidato e docker create:
questo tentativo non ha creato o avviato il candidato né modificato live/DB.
La proof isolata otto righe PASS a 0dfab1e7… resta valida come evidenza del
consumer isolato; nessun POST attestazione.

Il codice aggrega campi HostConfig non supportati, Healthcheck, restart/log
driver e tipo/readonly/formato dei mount. L'output non identifica quale
condizione abbia bloccato: causa specifica ancora da acquisire.
Nessun allentamento del guard e nessuna copia indiscriminata di HostConfig.
Il blocco preparazione precedente è storico (tentativo bloccato);
prossimo passo inventario read-only dei soli nomi dei campi non vuoti e flag
di conformità, senza stampare valori, env o mount path.
La correzione deve preservare il contratto reale rilevato; poi ripetere
preparazione fermo, backup/switch e prova consumer deployato prima del POST.
R-SMOKE/R-INSTALL OPEN.

## 2026-09-30 — contratto runtime identificato: bind e limiti memoria preservati

Inventario read-only VPS: tre campi non vuoti **Binds, Memory, MemorySwap**;
Healthcheck assente; restart/log driver conformi; tutti i mount bind read-only
e formato path conforme. Live invariato; valori e identità non stampati.

Correzione helper Semantic **c1bbb31d81ee067008f264ad0f8c662aa1c014e2**: valida ogni bind ro rispetto al mount
risolto (nessun bind extra/duplicato, niente opzioni sconosciute); accetta solo
propagazione rprivate e ricrea i mount via --mount readonly.
Non ricopia ciecamente HostConfig.Binds. Mantiene sostituzione della sola copia
properties del candidato, mentre tutti gli altri source/target restano uguali.

Valida Memory/MemorySwap come interi coerenti, conserva i valori via
--memory/--memory-swap (incluso swap -1) e richiede uguaglianza nel readback.
Gli altri campi non supportati restano bloccanti; MemoryReservation è
esplicitamente bloccante. Nessun numero/valore di configurazione è stampato.
20 test locali dei preparatori PASS, di cui 8 per il preparatore Ingestion:
flusso completo con bind/memoria, candidato fermo, riuso, cleanup, drift,
swap illimitato e rifiuto bind/limiti incoerenti. CI nuova revisione non
ancora acquisita; revisione prodotto candidata rimane 0dfab1e7… con prova
isolata otto righe PASS. Nessun candidato preparato attestato dal VPS finora.

Il blocco diagnostico precedente è storico ed eseguito. Prossimo comando:
ripetere la preparazione con il helper corretto, senza build/avvio/switch,
migrazioni o POST. Risultato richiesto CANDIDATE PASS STOPPED=true; poi backup
e switch controllato, prova positiva consumer deployato prima dell'attestazione.
Approval/activation HUMAN THS; R-SMOKE/R-INSTALL OPEN.

## 2026-09-30 — candidato Ingestion preparato PASS; switch plan/apply pronto

Output VPS acquisito: CANDIDATE=PASS STOPPED=true ENV_PRESERVED=true
TRANSPORT_CONFIG_PREPARED=true; RELEASE_PREPARE=PASS LIVE_UNCHANGED=true
DB_UNCHANGED=true ATTESTATION_POST=false. Candidato fermo:
`ouf-ingestion-r4a-compatibility-candidate`; stato privato root0600:
`/etc/ouf/deploy-snapshots/ingestion-compatibility-release.json`.
Prodotto candidato **0dfab1e7b2253fd939088259ea61754d6e56706c**, immagine
immutabile della proof con otto righe PASS. Non ancora live.

Helper Semantic **ca5d44a76b3b8ed6592e3aedb61ad2d386e58507**:
`scripts/r4a_switch_ingestion_candidate.py`, plan/apply.
Plan è read-only: richiede stato/ID/revisione/context esatti, immagine/label,
env/mount/rete/launch contract/limiti memoria coerenti, properties private
0440 e hash/content identici a copia baseline più trasporto, token fresco
SERVICE/client/tenant/issuer/audience/scopi Semantic/object-storage/attest,
storia Flyway 14 tutta successful, versione/hash congelati e readiness.

Apply crea receipt privato, ferma live con restart=no; dump custom completo
del DB Ingestion, pg_restore in DB temporaneo e confronto dell'intera storia
Flyway (version/script/checksum/success/type), poi drop scratch con dump
conservato. Nessun DDL/migrazione previsto nel DB live: stessa storia richiesta
prima/dopo. Rilegge candidato e properties prima dello swap per ID.
Conserva vecchio runtime come `ouf-ingestion-compatibility-rollback-<id>`;
rinomina/avvia solo il candidato verificato, richiede readiness e stesso
image/env/mount/Memory/MemorySwap, storia Flyway/versione congelata identiche,
properties baseline intatte e token fresco; poi restart=unless-stopped.

Receipt privato root0600:
`/etc/ouf/deploy-snapshots/ingestion-compatibility-switch.json`.
Receipt preesistente blocca doppi switch. In caso di errore, recupero per ID
del vecchio runtime, nuovo failed e fino a 120 righe di log conservati in file
privati; nessun DB restore automatico. Un ID estraneo live blocca recupero.
Non rilanciare alla cieca uno switch con receipt già creato, anche rolled-back.

28 test locali dei preparatori/switch PASS, inclusi 8 nuovi dello switch
Ingestion: plan senza scritture, sequenza stop/backup/swap, recupero su
backup/start fallito, drift properties, ID estraneo, cleanup scratch e
claims/freshness token. CI nuova helper non ancora acquisita.
Il precedente blocco preparazione è storico ed eseguito. Prossimo gate:
plan/apply dello switch; dopo PASS occorre sonda della revisione deployata
con i mount/properties effettivi, distinta dalla sola readiness.
Nessun POST attestazione/approval/activation nel blocco switch; HUMAN THS
resta il gate fonte. R-SMOKE/R-INSTALL OPEN.

## 2026-09-30 — switch Ingestion eseguito PASS; sonda deployata pronta

Output VPS plan/apply acquisito: SWITCH=PASS live
**0dfab1e7b2253fd939088259ea61754d6e56706c**, Flyway **14**,
versione e hash congelati invariati. Dump completo verificato tramite restore
in DB temporaneo e conservato:
`/etc/ouf/deploy-snapshots/ingestion-before-compatibility-2weff4yv.dump`.
Vecchio runtime conservato:
`ouf-ingestion-compatibility-rollback-f55cbf453460`.
Receipt privato `/etc/ouf/deploy-snapshots/ingestion-compatibility-switch.json`.
Onboarding resta live 6340d5bf… Flyway31, UDP edaba2bf… Flyway34.
ATTESTATION_POST=false; DEPLOYED_CONSUMER_PROBE_PENDING=true.
Non stampare stato/receipt/dump/env/token; non rilanciare il blocco switch
già eseguito, perché il receipt blocca doppi switch.

Helper Semantic **974f5eff2e80fa1224cd5581b89fb312e9b4ceef**:
`scripts/r4a_probe_deployed_ingestion.py`.
Richiede receipt PASS, ID/image/revisione/label/context esatti, contratto
runtime/env/mount/memoria e properties hash invariati, trasporto conforme
alle tre properties effettivamente montate, token SERVICE fresco con issuer/
audience/scopi e Flyway identico al receipt; verifica readiness.

Esegue il consumer reale **in una JVM separata**, immagine ID del container
live e stessi mount AUTH/properties read-only, rete ouf-backend. Nessuna copia
temporanea del trasporto: le properties sono quelle effettivamente deployate.
Nessun endpoint del processo applicativo live viene invocato per la
compatibilità: questa è prova del consumer della revisione deployata con
configurazione effettiva, distinta dalla sola readiness. Non avvia Spring,
Flyway/scheduler/worker, non fornisce DB o persistenza, non POSTa attestazioni.

Richiede otto righe, stesso hash asset/adapter/runtime/binding della proof
predeploy, versione/hash congelati e snapshot live/Flyway/properties
invariati dopo lettura e validazione. Cleanup del solo probe disposable
anche in timeout/diniego. Salva solo dopo PASS proof privata root0600:
`/etc/ouf/deploy-snapshots/ingestion-deployed-compatibility-probe.json`,
con timestamp, image/container ID, candidateDeployed=true e modalità
SEPARATE_JVM_DEPLOYED_IMAGE_AND_LIVE_MOUNTS; attestationSubmitted=false.

Quattro nuovi test locali PASS (flusso completo immagine/mount reali,
diniego, timeout, drift); 28 test preparatori/switch già PASS. CI nuova helper
non ancora acquisita. Prossimo risultato richiesto DEPLOYED_COMPAT_PROBE PASS;
solo dopo questa evidenza predisporre attestazione vincolata a proof/context
e consumer deployato. Approval/activation restano HUMAN THS; fonte congelata
e R-SMOKE/R-INSTALL OPEN. Nessuna attestazione inviata dal blocco corrente.

## 2026-09-30 — consumer deployato PASS su otto righe, nessuna attestazione

Output VPS acquisito: DEPLOYED_COMPAT_PROBE=PASS VALIDATED_ROWS=8,
revisione live **0dfab1e7b2253fd939088259ea61754d6e56706c**;
COMPLETE=PASS SEPARATE_JVM=true LIVE_CONFIG_CHANGED=false ATTESTATION_POST=false.
Proof privata:
`/etc/ouf/deploy-snapshots/ingestion-deployed-compatibility-probe.json`.
Consumer reale eseguito in JVM separata con immagine deployata e mount/properties
live; nessuna invocation dell'endpoint applicativo live per la compatibilità,
nessun avvio Spring/scheduler/persistenza nella sonda. Otto righe validate,
immagine/configurazione/Flyway/versione/hash vincolati e ricontrollati.

Contratto owner alla revisione Onboarding 6340d5bf… verificato:
POST `/api/internal/v1/onboarding/compatibility/ingestion-runtime`;
body sourceId/onboardingVersionId/compatible/detail; autorità SERVICE con
capability ouf.ingestion.configuration.attest. L'owner accetta solo
IN_REVIEW/APPROVED e registra l'hash corrente della versione nel proprio
consumer_compatibility_attestation; non approva/attiva. Il futuro submitter
deve vincolare detail alla proof, image ID/revisione/versione/hash esatti e
verificare response/readback owner; nessuna scrittura SQL diretta.

Il blocco sonda precedente è storico ed eseguito. Prossimo passo ancora
read-only: inventario route APISIX per POST attestation (owner path, upstream,
OIDC e required scope); non assumere esistenza o mapping dal solo contratto
Java/repository. Nessun nuovo scope/grant/proposal o cambio route autorizzato
da questa evidenza; eventuali blocchi vanno risolti nel rispettivo owner.
Solo dopo verifica route e autorità token/capability preparare POST attestazione;
HUMAN THS mantiene approval/activation. R-SMOKE/R-INSTALL OPEN.

## 2026-09-30 — route attestazione non ancora acquisita; parser APISIX corretto

Output VPS: owner revision match=true, poi BLOCKED
APISIX_ADMIN_KEY_LAYOUT_UNSUPPORTED prima del GET admin/routes.
Nessuna evidenza su conteggio/mapping/scopo route da questo tentativo,
nessun POST o cambio live/IAM/route. La proof consumer deployato otto righe
PASS resta acquisita; R-SMOKE/R-INSTALL OPEN.

Il parser precedente fermava la lettura quando una lista YAML admin_key era
allineata alla chiave proprietaria (indentless sequence). Correzione Semantic
**ea588d84cb7a848fe3bc3e6867b22e4f24043428**: ammette questa forma standard oltre alla lista indentata e
commenti inline su scalari letterali quotati/non quotati. Arresta il parsing
alla successiva mapping sibling; richiede sempre una sola key di role=admin
con formato ristretto. Ambiguità, riferimenti a env e forme non supportate
restano bloccanti. Nessuna chiave stampata o inserita nell'argv:
curl config viene passato solo su stdin.

La forma effettiva della configurazione live non è stata stampata/acquisita:
la correzione copre un limite certo del codice, senza attribuire ancora una
causa specifica al file live. Sei test locali PASS (incluse indentless,
commenti, confine sibling, ambiguità/ref, trasmissione privata su stdin e
formati response Admin API). CI nuova helper non ancora acquisita.

Il helper read-only route attestazione è ora
`scripts/r4a_ingestion_attestation_route_inventory.py`, con dipendenza
`scripts/r4a_execution_route_inventory.py` corretta nel repo Semantic;
il main storico di execution inventory non viene invocato. Il branch prodotto
Ingestion resta invariato a 0dfab1e7… già deployato. Il blocco precedente è
storico e bloccato. Prossimo passo: ripetere solo inventario route; eventuale
nuovo BLOCKED richiede diagnosi del layout senza stampare valori. Ancora nessun
submit attestation; approval/activation HUMAN THS.

## 2026-09-30 — route attestazione PASS; submitter SERVICE pronto, POST non ancora eseguito

Output VPS read-only acquisito: owner revision match=true; route count=1,
enabled=true, owner path match=true, upstream Onboarding inline=true,
upstream reference=false, OIDC presente/abilitato e scope
ouf.ingestion.configuration.attest conforme. Inventario COMPLETE live invariato,
ATTESTATION_POST=false. Parser corretto ha permesso la lettura admin/routes;
nessuna chiave/identità/valore stampato.

Helper Semantic **26366fbdf5ad1c212ccd146888fbaa098b99766f**:
`scripts/r4a_attest_ingestion_compatibility.py`, plan/apply.
Ogni modalità rigenera la sonda consumer deployato (JVM separata, immagine e
mount/properties live) prima di valutare il payload: non usa una proof stantia.
Plan esegue GET/SQL read-only e salva la proof locale aggiornata, ma non crea
receipt attestazione e non POSTa. Richiede proof/context/revisione/otto righe,
live ID/image, token SERVICE fresco, route owner revision/upstream/scope/host/
path univoci e abilitati e fonte ancora IN_REVIEW/hash congelato.
Verifica in sola lettura assenza di attestazione INGESTION_RUNTIME già presente
per versione/hash; se presente richiede riconciliazione, senza duplicare.

Apply ricontrolla runtime/properties/fonte/token e assenza di attestazione;
riserva atomicamente receipt locale privato root0600:
`/etc/ouf/deploy-snapshots/ingestion-compatibility-attestation.json`.
La creazione esclusiva impedisce POST concorrenti di questi submitter.
Invia una sola richiesta via Gateway con token Ingestion; nessun HUMAN token,
nessuna scrittura SQL diretta, niente retry/redirect automatici.
Credenziale e body sono solo su stdin del curl disposable, mai nell'argv/output.

Payload owner sourceId/onboardingVersionId/compatible=true/detail; detail
contiene schema evidence v1 e proof della revisione deployata: image/container ID,
versione/hash, hash asset, adapter/versione, binding count/otto righe, hash
properties, timestamp e modalità separate JVM. L'owner resta autoritativo su
capability/resource enforcement e hash corrente della versione; plan non
sostituisce il suo ALLOW. Richiede HTTP201, risposta con ID UUID, consumer,
versione/hash/compatible/detail esatti e readback SQL read-only del record owner.
Fonte/hash congelati devono restare identici dopo POST. Stampa solo ID
attestazione e flag; risposta con eventuale actor_subject resta privata.

Receipt preesistente blocca ogni nuovo POST. Errori dopo riserva conservano
UNVERIFIED_DO_NOT_REPOST e flag post_attempted; timeout può aver committato
nell'owner, quindi mai rilanciare/rimuovere receipt alla cieca. Prima di un
eventuale recupero, riconciliare il record owner e il receipt senza stamparli.
Sette nuovi test locali PASS: route/context negativi, evidence vincolata,
plan senza POST/receipt, singolo POST+readback, timeout/no-repost, stdin privato
e riserva esclusiva. CI nuova helper non ancora acquisita.

Il blocco inventario route precedente è storico ed eseguito. Prossimo comando:
plan/apply dell'attestazione. **POST ancora non eseguito** dall'operatore.
Non approva o attiva la fonte, non cambia policy/IAM/route, non ingesta/persiste
righe/ACK. Dopo PASS attestazione occorre rileggere l'activation gate UDP
corrente e presentare review HUMAN THS della versione/hash congelati;
R-SMOKE/R-INSTALL OPEN fino alla catena reale Ingestion→UDP→search e installazione.

## 2026-09-30 — attestazione Ingestion owner PASS; UDP corrente da verificare

Output VPS acquisito: plan PASS senza POST, nuova sonda deployata PASS otto
righe in apply, ATTESTATION=PASS, READBACK=PASS, fonte/hash congelati invariati.
**Attestazione Ingestion acquisita: 00006776-5970-4f5c-acf0-145171a6f944**,
consumer INGESTION_RUNTIME, revisione deployata 0dfab1e7b2253fd939088259ea61754d6e56706c.
ATTESTATION_POST=true, SOURCE_APPROVAL=false, SOURCE_ACTIVATION=false.
Receipt privato conservato:
`/etc/ouf/deploy-snapshots/ingestion-compatibility-attestation.json`.
Il blocco attestazione è storico ed eseguito: non rilanciarlo o rimuovere il
receipt. Nessuna duplicazione dell'attestazione, nessun nuovo cambio live/DB
schema/route/IAM; backup e rollback restano conservati.

Prossimo gate prima della review HUMAN: rileggere coverage UDP corrente per
fonte/hash esatti. Helper Semantic **0a8ebe92d0f8628f9c2f5458cbb5647b58fcb210**:
`scripts/r4a_current_udp_activation_gate.py`, solo GET/SQL read-only.
Legge configurazione congelata e governedIdentity, verifica source/tenant/
policyRef/strategyVersion e Onboarding live 6340d5bf…; usa solo il binding
live OUF_ONB_UDP_IDENTITY_GATEWAY_URL/TOKEN_FILE e token SERVICE
ouf-source-onboarding fresco con scope ouf.udp.identity.attestation.read,
issuer/audience/tenant esatti. Token privato root:10003 e montato read-only;
non stampato, trasmesso al curl disposable esclusivamente su stdin.

GET dello stesso endpoint usato da UdpIdentityActivationVerifier:
`/api/udp/v1/governance/internal/identity/preflight`, sourceId e
configurationHash esatti. Richiede HTTP200, valid=true, source/hash/tenant/
canonicalClass/policyRef/policyVersion corrispondenti e coverageRef coverage://,
poi owner runtime e versione congelata invariati. Stampa solo status/booleani.
Due test locali PASS con tutte le corrispondenze/negativi/attestazione assente;
CI nuova helper non ancora acquisita. Un PASS resta una lettura puntuale:
Onboarding ricontrolla comunque il gate all'attivazione; mutazioni UDP possono
invalidarlo. Non rigenera copertura/backfill e non POSTa alcun preflight.

UDP preflight storico 57499699-dbc5-419d-a14b-27cd3604ec6f non sostituisce questa
verifica corrente. Fonte resta congelata IN_REVIEW, versione
68394f42-5c82-4127-a1f3-126516665749/hash invariati.
Dopo UDP corrente PASS predisporre card/challenge di review nella THS,
con decisione approval/activation esclusivamente HUMAN. Catena reale
Ingestion→UDP→search ancora da eseguire; R-SMOKE/R-INSTALL OPEN.

## 2026-10-01 — Intake guard repair LIVE PASS; restart checkpoint

Operator evidence carried into this conversation: plan/apply PASS, two owned intake routes repaired, OIDC and limits preserved; direct UDP Lake and Gateway Lake incomplete-body probes both HTTP400. STORAGE_NOT_INVOKED=true under the pinned missing-content invariant; private receipt /etc/ouf/deploy-snapshots/runtime-intake-service-guards.json retained. IAM unchanged and no token modification by this script. RETRY=false, RUN_RESUME=false. This establishes Lake admission for the tested source/run, not S3 durability, handoff admission, ACK, materialization or search. No claim that the historical403 request has been exactly correlated to a route guard.

Last execution evidence remains run86809c17-3354-45ca-a7e6-57e903944b24 PAUSED/controlVersion1; attempt1 Gateway404 and quarantine7741f1f3-479b-42be-bb0d-a711efb20722 RETRY_READY/version1; attempt2 Gateway403 and quarantine2fac075e-0862-4ae6-a799-cf63c41b651b OPEN/version0. Those are last-verified states, not a fresh database snapshot. Original recovery intent/read receipt must remain intact. Existing recovery files are keyed by run, so a second-quarantine recovery needs explicit separate operation/context handling; do NOT delete or overwrite the first recovery receipt or reuse the original read proof as proof of the second item.

PET sprint review: L0 Blueprint0.3, Matrix1.7, terminology notice1.1; Ingestion1.3 (watermark/durable ACK, retry idempotency, attempt history, recovery ownership), UDP1.3 (handoff validation before durability, ACK distinct from materialization, environment bindings), Authorization1.5 and Gateway1.5 (owner fine-grained enforcement, governed transport, configuration as code). Onboarding1.6, Semantic1.3 and MCP1.4 boundaries remain unchanged: frozen source/publication pins, no AI HUMAN decision, no source reactivation. The user explicitly mandates PET consultation EVERY sprint, continuously updated handoff and installation/configuration/deploy documentation, and parameterized installations across hosts/networks/domains/Enti.

Pinned UDP edaba2bff18a2aaf52d1180f21f0e68984cc3437 inspection: HandoffApi authorizes udp.candidate.write for sourceIdentity.sourceId/ingestionRunId BEFORE HandoffIntakeService.accept. accept validates handoff schema BEFORE DB lookup or lake.store. A source/run-only payload omitting handoffId fails FrozenContractValidator with UDP_CONTRACT_INVALID. This revision does not map ContractViolation to a dedicated HTTP status/body; a generic500 is NOT a reliable handoff admission proof. Do not promise a400 handoff probe or treat an arbitrary500 as successful authorization. Lake's400 probe remains a different pinned invariant.

Next operator step: one fresh READ_ONLY unified bundle on the existing run, using all three dependencies from one immutable revision in an isolated temporary directory. It verifies current run/quarantine context, workload token/policy diagnostics and route inventory after the repair. Optional sections may report UNAVAILABLE; COMPLETE means collection finished, not all prerequisites passed. It does not test handoff owner admission, S3 configuration/durability, ACK or materialization. No login, intake POST, IAM/route change, retry or resume. The historical403 may have aged out of the bounded logs; absence of markers is not proof of recovery.

```bash
(
set -e
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
ouf_diag_dir=$(mktemp -d /tmp/ouf-r4a-prerequisites.XXXXXX)
trap 'rm -rf -- "$ouf_diag_dir"' EXIT
for script in r4a_execution_failure_bundle.py r4a_execution_route_inventory.py r4a_prepare_frozen_compatibility_probe.py; do
  git show 6e3a7094f3e36debfd1eabe531c73c66a4f4a50b:scripts/"$script" > "$ouf_diag_dir/$script"
done
sudo python3 -B "$ouf_diag_dir/r4a_execution_failure_bundle.py" \
  --run 86809c17-3354-45ca-a7e6-57e903944b24
)
```

**Command prepared, NOT executed in this conversation.** Await the operator output before designing the second recovery. Fresh owner reads and a new explicit recovery operation must cover quarantine2fac075e… and current run control version, preserve first operation/failed attempts, and persist intent BEFORE each versioned action. No blind retries, no lifecycle SQL changes, no dismissal, no once-schedule reset. Delivery/materialization/search readback follows any real recovery; remaining pipeline boundaries can still fail independently.

### Mandatory industrialization backlog (R-INSTALL OPEN)

Existing lab helpers are not an industrialized multi-installation deploy system: inspected scripts still contain installation literals (ouf-lab, domains, container names, network, paths, upstream endpoints). Source-independent logic alone does not satisfy portability. These are legacy constraints to remove, not examples to copy into new generic code. Lab IDs/domain bindings may appear only in named fixture/example configuration and operator arguments.

New or revised production/deployment mechanisms must accept explicit versioned installation profiles/CLI/environment references for tenant/Ente, per-module hosts and ports, Gateway and issuer URLs/audiences, service identities, container/network/runtime names, storage endpoint/bucket, database connectivity, mounts/paths, deployment topology and retention/classification settings. Keep credential references private; no secret values in tracked profiles or chat. Validate bindings before mutation; reject missing/ambiguous values. Preserve domain capability IDs, schema invariants and reviewed release safety pins as protocol/safety constants, distinct from installation configuration. Support separated module hosts/networks through governed bindings rather than assuming a shared Docker network.

R-INSTALL closure needs automated plan/apply/verify, idempotent reconciliation, immutable revisions/images, backup+restore drill, retained rollback and durable receipts, drift checks, fresh authorization/readiness tests, full parameter catalog and documented cold install/upgrade. Require at least two different installation profiles/topologies in meaningful portability verification. No such acceptance is claimed here. Keep all previous open PET/roadmap items, including RAW replay SPI, per-source/type/zone retention policy, eight-row delivery/materialization/search, second source matching/review, cross-module gates and operational-awareness/latency work.

## 2026-10-01 — Fresh failure bundle acquired; second recovery cycle prepared

Actual operator READ_ONLY output: run86809c17-3354-45ca-a7e6-57e903944b24 PAUSED/controlVersion1; attempt1 FAILED/Gateway404, quarantine7741f1f3-479b-42be-bb0d-a711efb20722 RETRY_READY/version1; attempt2 FAILED/Gateway403, quarantine2fac075e-0862-4ae6-a799-cf63c41b651b OPEN/version0. Both raw_lake_ref_present=false. Ingestion/UDP running, fresh SERVICE token, identity/tenant/issuer/audience diagnostics coherent, both intake scopes present. Active policy35 GET200, each descriptor SERVICE/scope correct with one diagnostic matching unrestricted grant; both intake routes unique/enabled/UDP upstream/scope diagnostics match. UDP registry configured, no static bundle file; loaded in-memory bundle still unproven. Bounded symbolic logs empty; APISIX access log TimeoutExpired again. Historical403 exact request correlation remains unproven. These facts do not erase failures or prove S3/handoff/materialization.

Sprint PET constraints consulted: Ingestion1.3 retry/resume idempotency (§7), preserved processing attempt/replay history (§37.1), owner versioned recovery (§39); UDP1.3 environment bindings and durable ACK (ACK-01), Matrix1.7 owner enforcement and governed transport. This is a paused acquisition retry/resume, NOT implemented RAW replay SPI. Broader mandatory PET/R-SMOKE/R-INSTALL gaps from earlier handoffs stay OPEN.

Generic recovery wrapper now supports --cycle equal to the quarantine UUID. Intent and fresh read proof filenames include BOTH run and quarantine; the original run-only receipt/proof remain untouched. No arbitrary operation UUID can bypass the deterministic intent collision guard. New-cycle mode requires explicit receipt-root/container/database/user/network/curl-image bindings; existing legacy mode retains compatibility defaults, which remain portability debt outside this incremental path. Per-module topology is supplied via the configured PostgreSQL control-plane container and governed API origin; this increment does not implement a remote SSH executor.

Before retry, it requires a private predecessor receipt in the configured root with phase RESUME_CONFIRMED, same run/subject/tenant/release, a different quarantine, and resumedControlVersion equal to the current PAUSED run controlVersion. A single fresh HUMAN device login requests read+retry+resume scopes. Fresh owner GETs and READ_ONLY DB snapshot must match exact run/quarantine/tenant; a scoped private read proof is saved. Terminal confirmation is now RECUPERO <run UUID> <quarantine UUID> for this cycle; cancellation creates no intent or business mutation (scoped read proof may exist). Recheck owner versions/token/live container after confirmation. Exclusive intent creation precedes retry; expectedVersion0 for the current second quarantine, then matching RETRY_READY/version1 readback, then intent persisted BEFORE resume with run expectedVersion1. No source reactivation, attempt deletion, SQL lifecycle changes or repeated first retry.

On success, intent RESUME_CONFIRMED/controlVersion2 records only API acceptance; real execution may still fail at S3 or handoff. If timeout/disconnect/error occurs after intent creation, do NOT rerun recover or delete receipts: use verify with the SAME --cycle and bindings. resume-only is allowed only for reconciled retry phases and current owner state; an ambiguous resume intent refuses repost. Predecessor ambiguity, actor/tenant/release mismatch, wrong control version or wrong cycle stops the new recovery. Original first-cycle terminal authorization is NOT reused for the second failure.

14 local tests PASS, including real controlling TTY, stripped HTTP204, predecessor ambiguity/context/version refusal, deterministic separate paths, second cycle single retry(version0)/resume(version1), canceled operation, timeout/no-repost, and non-lab database/network/image arguments reaching transport with bearer on stdin. New independent CI job recovery-cycle-scripts added; CI and LIVE second-cycle recovery are NOT claimed by local tests. No deployed Java/image or live configuration change in this increment.

Next operator action: corrected pinned wrapper recover with --cycle2fac075e… and predecessor /etc/ouf/deploy-snapshots/ingestion-human-recovery-86809c17-3354-45ca-a7e6-57e903944b24.json. Deployment revision remains163c167d09b8371ff7a62ce7068e9d485b6969b7. A single fresh device login followed by exact terminal confirmation is necessary for this new HUMAN action. Preserve all receipts. Await actual operator result; then run scoped delivery/materialization readback (with generic failure bundle dependencies) and distinguish ACK/materialization/search. Handoff admission and S3 writes remain NOT_PROVEN until actual execution evidence. Current correction establishes Lake admission only.

### Exact next operator command — prepared, not executed

Lab profile values below are CLI example bindings only. Open the device verification URI printed by the process, authenticate as the authorized HUMAN, then confirm in the VPS terminal with `RECUPERO 86809c17-3354-45ca-a7e6-57e903944b24 2fac075e-0862-4ae6-a799-cf63c41b651b`. This authorizes retry and resume; the run can execute and write Lake/UDP afterward. Do not paste device codes or bearer tokens in chat. On any BLOCKED after intent creation, preserve receipt and use verify, never repeat recover blindly.

```bash
(
set -e
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
ouf_recovery_dir=$(mktemp -d /tmp/ouf-r4a-recovery-cycle.XXXXXX)
trap 'rm -rf -- "$ouf_recovery_dir"' EXIT
for script in r4a_recover_ingestion_run.py r4a_verify_human_recovery_access.py r4a_prepare_frozen_compatibility_probe.py; do
  git show 634dc70db74a6c3d54faedb8727e6004ec2803fe:scripts/"$script" > "$ouf_recovery_dir/$script"
done
sudo python3 -B "$ouf_recovery_dir/r4a_recover_ingestion_run.py" recover \
  --cycle 2fac075e-0862-4ae6-a799-cf63c41b651b \
  --previous-receipt /etc/ouf/deploy-snapshots/ingestion-human-recovery-86809c17-3354-45ca-a7e6-57e903944b24.json \
  --receipt-root /etc/ouf/deploy-snapshots \
  --ingestion-container ouf-ingestion --postgres-container ouf-postgres \
  --database ouf_ingestion --db-user ouf_ingestion \
  --network ouf-backend --curl-image curlimages/curl:8.16.0 \
  --issuer https://auth.ouf-lab.it/realms/ouf \
  --api https://api.ouf-lab.it --client ouf-human-admin \
  --subject b93d8cf6-cd14-4ee6-91d7-84cd76c4f500 \
  --tenant ouf-lab --audience ouf-api-gateway \
  --run 86809c17-3354-45ca-a7e6-57e903944b24 \
  --quarantine 2fac075e-0862-4ae6-a799-cf63c41b651b \
  --expected-revision 163c167d09b8371ff7a62ce7068e9d485b6969b7
)
```

### Recovery cycle CI evidence acquired

GitHub module CI run36826901911 on commit4f3e6e8f19d40b7e78b425e4fb6bbbafa503a927: independent job recovery-cycle-scripts110254498715 completed SUCCESS (14 tests). Full module/container and pairwise suites were still in progress at observation. The operator command pins634dc70db74a6c3d54faedb8727e6004ec2803fe with identical recovery/proof code; later4f3e6e8 only corrects root-context CI and saves the command. No LIVE second recovery output yet. Do not infer full CI or S3/handoff success from this script job.

## 2026-10-01 — Second quarantine recovery LIVE PASS; execution readback next

Actual operator output: private cycle receipt /etc/ouf/deploy-snapshots/ingestion-human-recovery-86809c17-3354-45ca-a7e6-57e903944b24-2fac075e-0862-4ae6-a799-cf63c41b651b.json; retry HTTP204, RETRY_READY/version1; resume HTTP200/controlVersion2. Both HUMAN write authorizations proven for this cycle. No source reactivation or RAW replay. Successful script flow records RESUME_CONFIRMED; retain this intent, scoped read proof and original first-cycle receipts. Do NOT repeat recover for either cycle.

The API acceptance is NOT execution completion. Current ingestion outcome has not yet been read; source remains last-verified ACTIVE/frozen. S3 durability, handoff/ACK, eight-row materialization and search remain NOT_PROVEN. PET sprint check Ingestion1.3 §45.2 and UDP1.3 §4.1/ACK-01: ACK requires durable input/metadata but does not imply resolution/materialization or serving completion. No schema, deploy or configuration change in this step.

Next command uses existing cinema smoke readback (fixture, not a generic production deploy tool), plus all three failure-bundle dependencies pinned together. Only READ_ONLY domain SQL/log/config reads and existing policy GETs; no login/retry/resume/intake POST. It checks exact ACTIVE publication/hash, schedules/runs/attempts/lineage/outbox receipts and matching UDP intake/jobs/observations/revisions/bindings/current objects. Cross-database snapshot is not atomic; in-flight work may require another read. A NOT_PROVEN result requires interpreting actual states/reasons before any action. The legacy OPEN quarantine count is NOT a lifecycle-aware count of newly blocking items; RETRY_READY historical items can remain included. Never delete/dismiss historical quarantines merely to make this fixture PASS; reconcile classification if delivery otherwise succeeds. Empty matching handoff sets alone are not success. Readback does not perform independent S3 byte/hash verification or search. If failure occurs, attached unified bundle preserves symbolic diagnosis; APISIX log timeout is diagnostic unavailability, not proof of owner deny.

```bash
(
set -e
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
ouf_readback_dir=$(mktemp -d /tmp/ouf-r4a-execution-readback.XXXXXX)
trap 'rm -rf -- "$ouf_readback_dir"' EXIT
for script in r4a_cinema_execution_readback.py r4a_execution_failure_bundle.py r4a_execution_route_inventory.py r4a_prepare_frozen_compatibility_probe.py; do
  git show 4db36e14fe47adc80c4886d31548d0a638d776a9:scripts/"$script" > "$ouf_readback_dir/$script"
done
sudo python3 -B "$ouf_readback_dir/r4a_cinema_execution_readback.py"
)
```

Command prepared, not yet operator-executed. Await actual output; classify delivery separately from materialization, then search and second-source matching/review. All preceding PET/R-SMOKE/R-INSTALL/replay/retention/portability/operational-awareness/latency open items remain OPEN.

## 2026-10-01 — Eight-row delivery LIVE PASS; three UDP jobs quarantined

Actual operator readback: sourceACTIVE/frozen hash/publication match; run86809c17-3354-45ca-a7e6-57e903944b24 SUCCEEDED/controlVersion2, no run failure; consumed once schedule DISABLED correctly. Ten processing attempts retain failed history; eight lineages, zero OPEN Ingestion quarantine. Both prior quarantines RESOLVED/lifecycleVersion2 with original404/403 reasons preserved. Eight handoffs ACKED and matching UDP ID sets: ING_DELIVERY_EIGHT_ROWS=PASS.

UDP: five PROCESSED intakes/SUCCEEDED jobs/NEW_OBJECT decisions, five observations/revisions/bindings/active objects; three DURABLE intakes/QUARANTINED jobs. No intake failure codes or open resolution issues reported. UDP_MATERIALIZATION_EIGHT_ROWS=NOT_PROVEN; search remains unverified. This is not an Ingestion recovery blocker anymore. Do not resume/retry the SUCCEEDED run, reactivate source, reset schedule or re-send ACKED handoffs. Expected10 attempts comprise eight successful records plus two preserved failed attempts; not ten delivered rows. Diagnostic logs: discovery-unavailable cumulative4/recent1 remains separate operational debt; empty UDP symbolic logs do not explain quarantined jobs; APISIX access TimeoutExpired persists.

PET sprint check UDP1.3 §4.1 and Ingestion1.3 §45.2: durable ACK deliberately precedes resolution/materialization. Static pinned UDP HandoffIntakeService requires VERIFIED Lake stores before ACK and source RAW verification in execution mode; operator ACK evidence is consistent with this runtime durability contract, but independent S3 bytes/hash readback remains unperformed. Report intake durability separately from serving/materialization.

Pinned UDP ResolutionRepository distinguishes job.safe_failure_code from handoff_intake.failure_code. quarantine()/pause() can set QUARANTINED plus symbolic code and integrity counters/events while intake stays DURABLE and no resolution_issue is created. Thus empty UDP_FAILURE_CODES/open issues in the old fixture do NOT prove no downstream error. Possible gate reasons must be acquired, not inferred: reference integrity missing/invalid/drift or review-required have different remediation. ResolutionWorker first checks MaterializationReferenceGate, then resolution/materialization. No terminal quarantine automatically retries in claim(); waiting alone does not recover QUARANTINED.

New generic scripts/r4a_udp_materialization_diagnostic.py requires explicit run/source/PostgreSQL container/database/user CLI bindings. One bounded READ_ONLY transaction joins only this source/run's intake+jobs and grouped symbolic handoff events. Projects job ID/state/version, attempts, integrity_attempts, safe_failure_code, missing-ref COUNT (no reference values), baseline/next-check presence and safe event counts. No payload/safe_detail/raw exception text/token. SQL scopes validated; subprocess output and errors captured; non-symbolic codes redacted. Three local tests PASS for transaction/scope/projection, injection refusal and redaction. CI/live diagnostic not yet verified. No production code/schema/deploy change.

Next operator: run this diagnostic once, then use exact reason/version to inspect the governed reference/configuration or review owner. No SQL job-state mutation, blanket replay or discarded evidence. Preserve all eight ACKs, five successful objects and three quarantined jobs. R-SMOKE is PARTIAL (delivery PASS, materialization5/8, search OPEN); R-INSTALL and all earlier replay/retention/portability/PET/cross-module/operational-awareness/latency/second-source work remain OPEN.

### Exact next operator diagnostic — prepared, not executed

Installation/source values are lab fixture CLI bindings, not production code literals. Paste only its safe output; no login needed.

```bash
(
set -e
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
ouf_udp_diag=$(mktemp /tmp/ouf-r4a-udp-jobs.XXXXXX.py)
trap 'rm -f -- "$ouf_udp_diag"' EXIT
git show 19a8e9a8054be9ccd5f3e1cd25cdde8a3d14cbd8:scripts/r4a_udp_materialization_diagnostic.py > "$ouf_udp_diag"
sudo python3 -B "$ouf_udp_diag" \
  --run 86809c17-3354-45ca-a7e6-57e903944b24 \
  --source managed-cinema-8ec8ae90 \
  --postgres-container ouf-postgres --database ouf_udp --db-user ouf_udp
)
```

## 2026-10-01 — UDP gate reason acquired: CONTRACT_INVALID on three jobs

Actual READ_ONLY operator evidence: all eight HANDOFF_DURABLE events present. Five jobs SUCCEEDED/stateVersion2, attempts1/integrityAttempts0, baseline present, REFERENCE_INTEGRITY_PASSED and RESOLUTION_COMPLETED each once. Three jobs QUARANTINED/stateVersion2, attempts1/integrityAttempts1, no baseline, missingRefCount0/no next check, safe_failure_code UDP_REFERENCE_INTEGRITY_CONTRACT_INVALID; intake still DURABLE and no intake failure. Job IDs:7793566d-b9d4-4402-8cda-c09b8f135c04 (handoff8869a6d6-3d82-4514-a63a-d23f9b26d48f), e7572836-f8af-4c58-b5fc-12d7aff5db1d (handoffaed8ef93-6d00-4cf0-868d-d2d82d79b524), e5b6ca24-6143-4ae5-8907-5dce398abfa3 (handoffe58faf8c-c35a-4106-b4b6-67e58dec9774). Each has exactly one REFERENCE_INTEGRITY_QUARANTINED event. No resolution attempt/decision or retry for those three is proven. Preserve eight ACKs, five objects and complete history.

Pinned MaterializationReferenceGate catches ANY IllegalArgumentException from HistoricalContractCatalog.resolve and labels it CONTRACT_INVALID. HistoricalContractCatalog validates required refs and then, in execution mode, delegates to PublishedRuntimeConfiguration.resolveContracts. That path also validates/checksums the published bundle/profiles, exact handoff refs and Semantic bindings via Gateway. Its get() can throw IllegalArgumentException for empty/malformed credential or invalid HTTP header; these are currently indistinguishable from payload/profile integrity errors at the gate. Therefore this safe code alone does NOT prove bad CSV data or mismatched handoff refs, and missingRefCount0 does NOT establish full resolution readiness (exception precedes that result). Token-file refresh race is a hypothesis ONLY, not diagnosed fact; do not modify token/refresher or weaken reference validation from this output.

Sprint PET UDP1.3 §109.7 consulted: point-of-use reference-integrity fail closed; no silent fallback, no manual business-state repair. Ingestion run remains SUCCEEDED and must not be replayed to solve UDP jobs.

Next increment adds --compare-contracts to the existing generic diagnostic. One READ_ONLY query groups this exact source/run's persisted contractRefs using JSONB equality; reports groups, succeeded/quarantined counts, required nonblank-string validity and optional value shapes only, never refs/payload. Four local unit tests PASS including scope/SQL projection validation and output redaction (mocked transport); LIVE query and CI not yet verified. Missing required strings explicitly count false. Grouping all8 in one ref group spanning5 successes/3 failures would rule out differing persisted contractRefs as discriminator but would NOT independently prove bundle validity or token-race causality. Multiple groups require owner-pinned comparison; do not change frozen configuration.

Await operator comparison before designing a deployed-code/transport probe or corrective release. No retry/replay/SQL state reset, token mutation, new policy or source activation. Delivery PASS, materialization5/8/search OPEN; every earlier PET/R-INSTALL/portability/retention/replay/operational-awareness/latency/second-source gap remains open.

### Exact next operator comparison — prepared, not executed

```bash
(
set -e
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
ouf_refs_diag=$(mktemp /tmp/ouf-r4a-contract-refs.XXXXXX.py)
trap 'rm -f -- "$ouf_refs_diag"' EXIT
git show 17d96fb5cdcea7e378cee660d4ac33cb019c3dfa:scripts/r4a_udp_materialization_diagnostic.py > "$ouf_refs_diag"
sudo python3 -B "$ouf_refs_diag" --compare-contracts \
  --run 86809c17-3354-45ca-a7e6-57e903944b24 \
  --source managed-cinema-8ec8ae90 \
  --postgres-container ouf-postgres --database ouf_udp --db-user ouf_udp
)
```

Lab values supplied as CLI fixture bindings only. No login. No contract-reference values printed; preserve all job states until the result is interpreted.

## 2026-10-01 — All eight persisted contractRefs equal; UDP token transport inventory next

Actual operator comparison: EXACT_JSON_EQUALITY true; one group total8/succeeded5/quarantined3; refs object and all four required nonblank strings valid; mappingRefs, authorityPolicyRef and relationshipResolutionStrategyRefs ABSENT on all8. Thus different persisted handoff contractRefs cannot explain the5/3 split. Optional ABSENT alone is not an error (five identical refs passed); do not synthesize those fields or alter frozen source/bundle.

The broader PublishedRuntimeConfiguration validation and current Gateway/owner responses remain separate. IllegalArgumentException can arise from profile/JSON conversion or token/header checks; no exact nested exception or contemporaneous request correlation is retained by current job code. Hypothesis: token read during non-atomic refresh may fail the credential check and be misclassified as CONTRACT_INVALID. NOT PROVEN; structural detection of a truncating write does not itself identify its target or prove a race occurred. Identical refs also do not rule out transient/concurrent resolution bugs or mutable response evidence.

PET sprint: UDP1.3 §109.7 reference integrity at point of use and no silent fallback; Matrix1.7 actual secret/environment bindings and service identity lifecycle. Next generic scripts/r4a_udp_token_transport_inventory.py reads explicit container and service-name regex bindings. It reads only configured OUF_UDP_EXECUTION_TOKEN_FILE, host bind metadata/current bounded JWT and safe expiry/actor/scope diagnostics; distinguishes file bind vs directory bind (important for atomic replacement visibility). Requires a supported explicit env binding rather than guessing hidden external configuration. Reads matching systemd service ExecStart privately and inspects Python AST only, reports truncating-write and replace/rename site counts. It never executes refresher scripts, invokes token refresh, prints token/secret/script contents or changes services. Dynamic writer modes/uninspected helpers/shell scripts are not classified and absence of sites is NOT proof of atomic publication. Whole-script sites are structural evidence only; destination not proven.

Three local tests PASS for structural redaction, read/dynamic-mode classification and safe bind mapping/file-vs-directory. CI/live inventory not yet verified. No policy/route/deploy/token/job mutation; eight ACKs, five objects and three QUARANTINED jobs remain intact. After inventory, inspect exact token-writer target and preserved metadata before any corrective deployment. Do not blindly requeue jobs: recovery needs versioned owner action/new technical evidence and retained quarantine history. Full R-SMOKE, search, independent S3 verification, R-INSTALL and earlier replay/retention/portability/operational-awareness/latency/second-source gaps stay OPEN.

### Exact next operator inventory — prepared, not executed

```bash
(
set -e
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
ouf_token_diag=$(mktemp /tmp/ouf-r4a-udp-token.XXXXXX.py)
trap 'rm -f -- "$ouf_token_diag"' EXIT
git show c7ee0e4c2fd5f36646762506f6b563c82e48dcc6:scripts/r4a_udp_token_transport_inventory.py > "$ouf_token_diag"
sudo python3 -B "$ouf_token_diag" \
  --container ouf-udp --service-match 'udp.*token|token.*udp'
)
```

No login or service restart; the service matcher is a lab CLI binding. Structural writer facts are not proof of token-target behavior or historical causality.

## 2026-10-01 — UDP token current read PASS; writer not found by narrow service matcher

Actual operator token inventory: execution token explicit ENV present, JWT format valid, SERVICE actor, age28s/TTL271s, directory bind (file-bind=false), ouf.semantic.read present. Zero matching services under regex udp.*token|token.*udp. This proves only the current token diagnostics and lack of matching installed systemd names; it does NOT prove no refresh mechanism or atomic token writes. No writer script was inspected. Directory bind supports atomic file replacement visibility, unlike a file bind; actual writer behavior and historical empty/partial read remain unproven.

Correction to diagnostic: configuration.read=false tested the WRONG generic scope name, not the runtime publication owner's capability. Verified pinned Onboarding6340d5bf… RuntimePublicationApi.require uses ouf.onboarding.configuration.read, matching r4a_publication_bindings_inventory.CAP. The script now tests that exact scope plus ouf.semantic.read. No reason to add generic configuration.read or change IAM/grants. Any owner authorization proof still requires actual Gateway/owner request, not decoded scope claims. Scope omission alone would normally lead HTTP unavailable classification in this pinned UDP client, not establish the CONTRACT_INVALID cause.

Next READ_ONLY inventory reuses corrected script with broader lab CLI service matcher ouf.*(token|auth|refresh), covering shared/Onboarding credential services instead of requiring UDP in their name. It prints only service names, Python script count and redacted AST structural counts. No source/config/token values, login, token refresh, service restart or job mutation. Shell/helper/dynamic writer behavior stays explicitly unproven. If still no writer, inspect deployment-specific scheduler/container binding through a targeted read-only inventory rather than scanning arbitrary secret/config trees.

PET sprint UDP1.3 §109.7 and owner authorization boundaries consulted; fail closed preserved. All eight refs remain identical/valid-required;5 objects succeeded and3 jobs QUARANTINED/CONTRACT_INVALID,8 ACKs/runSUCCEEDED unchanged. No corrective release or recovery yet. Existing S3 independent verification/search/PET/R-INSTALL/replay/retention/portability/operational-awareness/latency/second-source gaps remain open.

### Exact next operator inventory — prepared, not executed

```bash
(
set -e
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
ouf_token_diag=$(mktemp /tmp/ouf-r4a-udp-token.XXXXXX.py)
trap 'rm -f -- "$ouf_token_diag"' EXIT
git show b9818c170ed41d99a58f9a7810ecbc9923487cb3:scripts/r4a_udp_token_transport_inventory.py > "$ouf_token_diag"
sudo python3 -B "$ouf_token_diag" \
  --container ouf-udp --service-match 'ouf.*(token|auth|refresh)'
)
```

## 2026-10-01 — Correct UDP scopes present; refresher inventory partial and hardened

Actual operator evidence: UDP execution token ENV present, current valid SERVICE JWT, directory bind, age30s/TTL268s; BOTH ouf.onboarding.configuration.read and ouf.semantic.read true. Four installed services match broad selector. Successfully inspected: ouf-gateway-policy-token.service (replace/rename1, truncating0), ouf-ingestion-policy-token.service (1/0), ouf-onboarding-identity-token.service (3/0). Then inventory BLOCKED CalledProcessError BEFORE printing fourth unit; exact service/stage unknown in the old script. This is a diagnostic failure, not a production/refresher failure or proof of token-race causality. No refresh or business mutation occurred.

Current missing scope and simple invalid/expired token diagnostics are not present. Three static script results weaken a broad claim of non-atomic writes, but do not identify which output feeds UDP or classify dynamic/helper writes. The3-replacement Onboarding identity writer may publish several credentials; target matching has NOT yet been demonstrated. Do not change script/token/IAM or jobs based on counts alone.

Generic token inventory corrected to print each unit BEFORE systemctl read; skip uninstantiated @.service templates without calling show; isolate failures per unit and print only stage EXEC_START/SCRIPT_METADATA/SCRIPT_AST plus exception TYPE. Every other selected unit continues. Adds safe boolean execution_token_target_literal_present from AST string constants matching the resolved host execution-token filename. A false value does not rule out assembled/dynamic paths, and a true literal presence does not prove that replace/rename targets that file. Overall COMPLETE means bounded collection finished, not all sections succeeded or causal proof.

Five local tests PASS, including new unavailable-service redaction/continuation and template skip checks. UDP job and token inventory tests added to independent module CI script job alongside recovery regressions; CI result not yet acquired for this change. No deployed Java/config/state change. PET sprint UDP1.3 §109.7 diagnostic vs readiness/integrity separation consulted. Shared scope/profile bindings remain parameterized; service matcher stays a CLI lab argument.

Next operator reruns only the hardened READ_ONLY inventory. Inspect fourth-unit outcome and exact-target structural evidence before selecting further runtime verification. If no destination can be proven, use a supported point-of-use resolver probe with precise symbolic cause; do not keep assuming a token race. RunSUCCEEDED/eight ACKs/five materialized/three QUARANTINED CONTRACT_INVALID and all prior broad open items remain unchanged. Preserve all receipts/job events/objects; no blind replay or SQL state repair.

### Exact next operator inventory — prepared, not executed

```bash
(
set -e
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
ouf_token_diag=$(mktemp /tmp/ouf-r4a-udp-token.XXXXXX.py)
trap 'rm -f -- "$ouf_token_diag"' EXIT
git show ab50b5d0d40684ed0f5c16b0792aa0b5f004edf7:scripts/r4a_udp_token_transport_inventory.py > "$ouf_token_diag"
sudo python3 -B "$ouf_token_diag" \
  --container ouf-udp --service-match 'ouf.*(token|auth|refresh)'
)
```

## 2026-10-01 — Template explains prior show failure; parser regression fixed and live GET probe prepared

Actual inventory: current SERVICE token valid/fresh age37s/TTL262s, directory bind, both correct scopes present. Fourth service is ouf-policy-token@.service, an uninstantiated template; skipped safely. Hardened inventory unexpectedly showed scriptCount0 for all three previously inspected concrete services. Reproduced defect in new inspect_services regex: raw Python pattern double-escaped dot/whitespace, preventing matching normal .py argv. Corrected escaping; added regression using realistic systemctl ExecStart that asserts scriptCount1 and AST/literal check reached. This invalid0-count observation must NOT be treated as deployment drift/no writers. Previous concrete-service replace/rename counts remain prior structural evidence, not destination/atomicity or historical race proof.

Six token-inventory tests PASS. New GET-only scripts/r4a_udp_reference_transport_probe.py uses explicitly bound UDP container/gateway/token mount, supplied PostgreSQL container/db/user/network/curl image, and this run/source's exact persisted ref group. One READ_ONLY SQL obtains refs privately. Real Gateway GET resolves exact historical publication with current UDP bearer; checks source, envelope/checksum equality, bundleRef and exact execution refs (including optional absent fields). Iterates exact semantic bindings via existing governed reference GET, checks IDs/version/revision/publication against response, and requires handoff publication present. Credential re-read before each GET, stdin transport only; no redirect/retry/replay/payload output. HTTP200 with matching pins demonstrates CURRENT transport/owner admission for those reads, not historical causality.

Probe intentionally does NOT recalculate bundle checksum bytes, instantiate Java Profiles/PublishedIdentityPolicy/MaterializationProfile or run the shipped Java resolver; even PASS prints JAVA_PROFILE_VALIDATION_NOT_PROVEN=true. Therefore a PASS narrows transport/access/pin diagnostics; it is not authorization to reset/requeue three jobs. A BLOCKED reports only safe status/boolean/exception type; source/reference values/token/body remain private. It will reject unsupported/missing explicit UDP gateway/token environment binding rather than guess an external config override.

Two new transport tests PASS for absent optional refs/drift comparison and actual GET-only/stdin/redaction behavior with mocked responses. Combined local script suite26 tests PASS (recovery14, materialization diagnostic4, token inventory6, transport probe2); CI job extended with transport tests, current CI result pending. No UDP live code/schema/config/job mutation or service refresh. SourceACTIVE/runSUCCEEDED/eight ACKs/five materialized/three QUARANTINED CONTRACT_INVALID preserved.

PET sprint UDP1.3 §109.7 point-of-use reference integrity and Gateway/owner boundaries consulted. Next operator runs corrected structural inventory AND fresh owner GET probe in one pinned block. If transport pins PASS, move to precise shipped-Java validation/error classification evidence before corrective release/governed job recovery. Do not continue to assume token race, change frozen bundles, or replay Ingestion. Full materialization/search/independent S3 readback/R-INSTALL and every earlier retention/replay/portability/operational-awareness/latency/second-source gate stay OPEN.

### Exact next operator combined block — prepared, not executed

```bash
(
set -e
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
ouf_probe_dir=$(mktemp -d /tmp/ouf-r4a-udp-reference.XXXXXX)
trap 'rm -rf -- "$ouf_probe_dir"' EXIT
for script in r4a_udp_token_transport_inventory.py r4a_udp_reference_transport_probe.py; do
  git show 9ebd98307075395f095fe9ed0d1d2916ee16f494:scripts/"$script" > "$ouf_probe_dir/$script"
done
sudo python3 -B "$ouf_probe_dir/r4a_udp_token_transport_inventory.py" \
  --container ouf-udp --service-match 'ouf.*(token|auth|refresh)'
sudo python3 -B "$ouf_probe_dir/r4a_udp_reference_transport_probe.py" \
  --container ouf-udp \
  --run 86809c17-3354-45ca-a7e6-57e903944b24 \
  --source managed-cinema-8ec8ae90 \
  --postgres-container ouf-postgres --database ouf_udp --db-user ouf_udp \
  --network ouf-backend --curl-image curlimages/curl:8.16.0
)
```

Lab installation values are CLI bindings. No login, token refresh, service restart, retry, replay or materialization. Owner authorization/audit records from normal GETs may be recorded. Preserve complete safe output including any individual UNAVAILABLE marker.


## R4A checkpoint 2026-10-01 — owner GET transport PASS; isolated shipped Java probe prepared

Operator evidence for run `86809c17-3354-45ca-a7e6-57e903944b24`: current UDP bearer valid SERVICE, age42s/TTL257s, both `ouf.onboarding.configuration.read` and `ouf.semantic.read` present, token mounted through directory. Corrected structural inventory discovers one Python script in each of gateway-policy-token, ingestion-policy-token and onboarding-identity-token units. Recognized replace/rename sites1/1/3, truncating writes0/0/0; execution-token target literal absent in each script. Dynamic/helper paths remain unproven. Template skipped. Token race and historical token failure remain hypotheses, not established root cause.

GET-only reference transport probe PASS: publication200, source/envelope checksum/exact bundleRef/execution refs match; semantic binding1 GET200, exact pin match, handoff publication found. This proves current HTTP admission and declared-reference correspondence. It does not recompute the canonical Java checksum, instantiate Java profiles, or explain the three historical quarantines. No permission/scope/bundle change is justified by this evidence.

PET UDP1.3 §109.7 reference-integrity at point of use and Ingestion1.3 §45.2 durable ACK consulted for this sprint. Last business-state readback remains ingestionSUCCEEDED/eightACKED, UDPfivePROCESSED/SUCCEEDED/materialized plus threeDURABLE/QUARANTINED `UDP_REFERENCE_INTEGRITY_CONTRACT_INVALID`. All eight persisted contractRefs exactly equal. Full eight-row materialization remains OPEN; search, independent S3 byte/hash readback, R-INSTALL, second-source matching/review, replay/retention/portability/operational-awareness and previous release gates remain OPEN.

Shipped UDP source at `edaba2bff18a2aaf52d1180f21f0e68984cc3437` inspected: `MaterializationReferenceGate.verify` maps every IllegalArgumentException from reference extraction/catalog/resolver to CONTRACT_INVALID without retaining nested symbolic code or Java location. `PublishedRuntimeConfiguration.resolveContracts` includes two publication GETs, sorted-Jackson canonical checksum recomputation, strict profile conversion and governed identity/profile consistency checks before semantic GET pin validation. The current curl probe covers only part of this path. Five passes with identical refs mean a permanently invalid common reference shape is insufficient to explain the split; timing/runtime differences remain unresolved.

New generic `scripts/r4a_udp_java_reference_probe.py`: reads only one scoped exact reference group with BEGIN READ ONLY/ROLLBACK; copies the actual running UDP jar to private temporary storage; bounded extraction of byte-identical BOOT-INF classes/libs with traversal rejection; compiles only a diagnostic main offline with explicitly provisioned JDK image pinned to local immutable image ID and Java21 target. Executes that main in the immutable actual UDP image, same numeric non-root UID/GID, no inherited application environment/DB credentials, read-only root/classes/token-directory mounts, capabilities dropped. No Spring startup, Flyway, worker, job mutation, retry, replay or materialization. Original UDP continues running. The token is read at each GET by the original resolver, preserving directory rename visibility. Temporary refs mode0600 owned by runtime UID; cleaned after execution.

The diagnostic invokes original `PublishedRuntimeConfiguration.resolveContracts`, including Java checksum/profile validation. On failure prints exception category, allowlisted symbolic code only and at most four application Java class/method/line frames; never raw exception message/body/token/refs. A PASS demonstrates current isolated shipped-code validation only. Uses Spring Jackson2ObjectMapperBuilder defaults plus disabled timestamp dates; live Spring ObjectMapper customizer/runtime parity is explicitly NOT PROVEN. No application context is initialized to obtain that bean. Historical causality and three-job recovery remain unproven even on PASS. If compiler/container/binding unavailable, fails closed with safe type; Java compile/run against live jar is still pending operator execution.

Validation: local combined suite30 tests PASS, including four new tests for byte preservation, traversal rejection, missing resolver and runner SQL/network/non-root/private-reference/output isolation. These are runner tests, not a completed live Java compile. CI extended. Previous code `9ebd98307075395f095fe9ed0d1d2916ee16f494`: recovery-cycle-scripts job SUCCESS in runs36830206038 and36830210649; full module CI failed at exactly one checksum, `.github/workflows/module-ci.yml`, as verified in decoded logs. Refresh its manifest hash with the current reviewed workflow; other frozen source hashes unchanged. New full CI result pending.

Next operator action: execute isolated Java probe from pinned coordination commit using lab bindings in the next block. JDK helper image provision only if absent; no deployment/restart. Capture complete safe output, especially UDP_JAVA_SAFE_CODE/UDP_JAVA_FRAME or PASS. If PASS, do not reset quarantined jobs: next work is governed recovery plus diagnostic retention for historical failures. If BLOCKED, use precise code/frame and live image evidence to select corrective work. Never replay the successful ingestion run or modify frozen source publication to bypass integrity.

### Exact next operator Java diagnostic — pinned, prepared, not yet executed

Code/tests/checksum fix commit: `307a652a7103457847409ee303237d6d2f22618d`. From the operator shell as oufadmin:

```bash
(
set -e
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
ouf_probe_dir=$(mktemp -d /tmp/ouf-r4a-java-reference.XXXXXX)
trap 'rm -rf -- "$ouf_probe_dir"' EXIT
for script in r4a_udp_token_transport_inventory.py r4a_udp_java_reference_probe.py; do
  git show 307a652a7103457847409ee303237d6d2f22618d:scripts/"$script" > "$ouf_probe_dir/$script"
done
if ! sudo docker image inspect maven:3.9.11-eclipse-temurin-21 >/dev/null 2>&1; then
  sudo docker pull maven:3.9.11-eclipse-temurin-21
fi
sudo python3 -B "$ouf_probe_dir/r4a_udp_java_reference_probe.py" \
  --container ouf-udp --jar-path /app/app.jar \
  --run 86809c17-3354-45ca-a7e6-57e903944b24 \
  --source managed-cinema-8ec8ae90 \
  --postgres-container ouf-postgres --database ouf_udp --db-user ouf_udp \
  --network ouf-backend --jdk-image maven:3.9.11-eclipse-temurin-21
)
```

All lab paths/source/run/container/network/compiler references are operator CLI bindings, not installation defaults inside the diagnostic. The Maven JDK21 image is a compiler helper only; if absent this block provisions its local image cache, without building/deploying OUF or restarting services. Compiler is subsequently resolved to immutable local image ID, offline compilation, no implicit pulls. UDP execution uses actual immutable running image ID, not this helper image. Capture safe output only. No HUMAN recovery action authorized by a Java PASS alone. Current CI for this new commit is pending; the Python runner local tests PASS and earlier script CI PASS are distinct from live Java compile/run evidence.

### CI follow-up 2026-10-01 — runner30 PASS; checksum PASS; managed candidate privilege context corrected

New pinned probe documentation commit `4d2f294f0392f4161b532f227fd4bfe8e0833979`, module CI run36831553184: recovery-cycle-scripts SUCCESS (30 tests); checksum step SUCCESS. Full module job reached existing managed identity candidate tests, then failed with ROOT_REQUIRED (four assertion failures/three errors) because its unittest discovery ran unprivileged while prepare/switch intentionally require root and private root-owned temporary fixtures. Tests inspected: Docker/build/HTTP/backup effects are mocked in the affected execution fixtures. Align this test command with root-context script CI using sudo python3 -B; retain production ROOT_REQUIRED guard. Refresh only reviewed workflow checksum again. Full module pipeline result after this correction remains pending. This is CI harness repair, no live candidate build/switch/deploy or privileged VPS operation. The exact Java operator block above remains pinned to `307a652a7103457847409ee303237d6d2f22618d` and unchanged. Live Java compile/run and historical quarantine cause remain pending; all prior business-state/open acceptance gates remain as recorded.


## R4A checkpoint 2026-10-01 10:06 Europe/Rome — shipped Java resolver PASS; original-job recovery candidate

### Latest operator evidence and live boundary

Operator ran the pinned isolated Java probe from coordination code `307a652a7103457847409ee303237d6d2f22618d`:
- Live UDP image `sha256:a47c8607c53451f7d0affba5994ec20dc6c09272ace68808daa9e63c33bc572e`.
- Offline compiler image `sha256:6fdc855a6ed81d288ca7ca37ac6ff5e9308b612485c0801d70b25a858c83d237`.
- `UDP_SHIPPED_JAVA_RESOLVE_CONTRACTS=PASS`; GET_ONLY, no Spring startup, materialization or retry; values/token not printed.
- Original resolver completed sorted-Jackson canonical checksum recomputation, profile decoding/governed identity consistency, execution-reference correspondence and Semantic pin checks in the isolated JVM. This extends the preceding curl owner-GET PASS.
- `MAPPER_RUNTIME_PARITY_NOT_PROVEN=true` and `HISTORICAL_CAUSALITY_NOT_PROVEN=true` remain material limits. No cause of the three historical exceptions is established. Token race, malformed persisted refs, insufficient current scopes and permanently invalid common profile are not proven root causes.

Last business-state readback remains run `86809c17-3354-45ca-a7e6-57e903944b24` SUCCEEDED/controlVersion2, eight original lineage/handoff rows ACKED, both Ingestion404/403 quarantines RESOLVED/version2; consumed trigger_once schedule DISABLED is correct; source ACTIVE with frozen hash/publication match. UDPfive PROCESSED/SUCCEEDED/materialized and three DURABLE/QUARANTINED `UDP_REFERENCE_INTEGRITY_CONTRACT_INVALID`, stateVersion2/attempts1/integrityAttempts1, no baseline/no scheduled recheck. All eight contractRefs exact JSON equal. This Java PASS does not reread or change those states. Full eight-row canonical materialization remains OPEN.

Original quarantined job/handoff pairs:
- `7793566d-b9d4-4402-8cda-c09b8f135c04` / `8869a6d6-3d82-4514-a63a-d23f9b26d48f`.
- `e7572836-f8af-4c58-b5fc-12d7aff5db1d` / `aed8ef93-6d00-4cf0-868d-d2d82d79b524`.
- `e5b6ca24-6143-4ae5-8907-5dce398abfa3` / `e58faf8c-c35a-4106-b4b6-67e58dec9774`.

Do not replay the successful ingestion run, reactivate its source/schedule, resend ACKed handoffs, alter frozen bundle/optional contract fields or UPDATE job states directly. Previous HUMAN recovery receipts remain private and retain authorization provenance; they authorize earlier Ingestion recovery, not UDP retry or policy changes.

### PET review and implementation gap

Consulted UDP1.3 §§109.6/109.7/109.9 and Ingestion1.3 §45.2: state/version/evidence-controlled re-run, reference-integrity at point of use, privileged recovery audit and distinction between durable ACK and completed materialization. Shipped ResolutionRepository claims READY/expiredRUNNING/duePAUSED only; technical QUARANTINED jobs have no governed retry endpoint. HistoricalReplayService REPRODUCE creates a NEW replay handoff/job and does not recover the original eight-row job set. Resolution issue decisions serve a different HUMAN identity-review workflow and must not bypass reference quarantine.

### Reviewable UDP candidate — not deployed

Draft PR [ouf-udp-object-resolution#38](https://github.com/GioNob/ouf-udp-object-resolution/pull/38), branch `codex/r4a-materialization-recovery`, candidate revision `c0b6c98c5029682a51e5ed82717092f86bfbb318`.
Review base `codex/r4a-materialization-recovery-base` is frozen at deployed `edaba2bff18a2aaf52d1180f21f0e68984cc3437`; main predates the deployed runtime, so PR targets the frozen baseline rather than including prior unrelated branch history. No main merge/force update/live release or migration. Existing Flyway34 unchanged.

New default-off HUMAN-only API:
- GET `/api/udp/v1/governance/materialization/jobs/{jobId}`: safe read-only review and real live Spring catalog/mapper check.
- POST `/{jobId}/retry`: operationUUID + expectedVersion + exact reviewed snapshotHash + explicit bounded reason.
- Capability `udp.materialization.retry`, operation COMMAND, requiredScope same ID, actors HUMAN only, MCP-ineligible. Immutable ownerRef/descriptor registration input in `catalogue/r4a-udp-materialization-recovery.json`, locally validated by existing batch registrar without network/writes.
- SDK owner decision on same request snapshot for tenant/RAW label and scopes module UDP/sourceRef/jobRef(ingestionRun)/typeRef. Resource denied before profile read/retry. No implicit SERVICE/AI_AGENT authority.
- Only technical reference CONTRACT_INVALID/CATALOG_INVALID/MISSING quarantine, intakeDURABLE, no claim/lease, matching tenant/source/type durable RAW metadata, and NO resolution decision/observation/revision/property contribution/initial source binding. HUMAN resolution review, DRIFT, completed/failed canonical processing excluded.
- Transaction serializes operationUUID, locks job/intake/RAW metadata, revalidates exact snapshot and contracts, preserves any integrity baseline, advances QUARANTINED -> READY/version once and appends immutable HUMAN evidence atomically. Original payload/RAW refs/job/handoff/run/attempts/integrityAttempts and historical events retained.
- Duplicate identical authorized operation returns original acceptedVersion even after worker claim/completion; no second requeue. Changed request/actor/job conflicts. Audit write failure rolls back requeue. Worker performs normal integrity gate/resolution;200 means admission only.
- Future gate errors retain allowlisted symbolic diagnostic code/category and at most four application Java frames, without raw exception messages, token, payload, refs or cause dumps. Prior lost details cannot be recovered retrospectively.

Configuration `OUF_UDP_MATERIALIZATION_RECOVERY_ENABLED` maps to `ouf.udp.materialization-recovery.enabled`, defaultfalse. Existing tenant/IAM/Gateway/token/policy/DB/S3 bindings remain installation configuration. No lab domain/source/tenant/host/user/image hardcoded in new production code. Install/recovery acceptance procedure: [module runbook](https://github.com/GioNob/ouf-udp-object-resolution/blob/codex/r4a-materialization-recovery/docs/materialization-recovery.md), OpenAPI updated. New capability/scope/grant/Gateway bindings are NOT registered/activated by committing this input. Require governed draft/preview/simulate/publish preserving complete ACTIVE policy and exact intended human/source/tenant/run scope. Last observed policy35 must be freshly reread, not assumed current.

### Verification and security gate

Coordination Semantic full CI run36831760279 at `8f2f52ecb2f86333810742d6693b48f0044a4e39` SUCCESS, including corrected checksum, root-context mocked candidate fixtures,30 script tests and container smoke.

UDP feature code `b437f0fb2e3a732342c1334d30120b4c04af224c`: focused PostgreSQL17 CI run36833579424 SUCCESS,14 tests/0failures/0errors/0skipped: recovery9, safe diagnostics2, existing integrity gate3. SDK tests10 pass. Full module run36833579517 Java21/PostgreSQL17/build SUCCESS, disaster-recovery drill SUCCESS, performance baseline SUCCESS; SDK pairwise and CRS/grid workflows SUCCESS. Initial Mockito exception-restubbing fixture error corrected; no production guard weakened.

Supply-chain gate on that candidate failed for two scanner-reported HIGH jackson-databind2.21.6 findings, CVE-2026-91776/CVE-2026-91777, fixed2.21.7. Candidate `c0b6c98c5029682a51e5ed82717092f86bfbb318` pins Jackson BOM2.21.7 in the same maintained family; official FasterXML jackson-bom-2.21.7 tag/pom verified. No vulnerability suppression/waiver or gate weakening. Patched candidate focused/full/security/DR/performance/deploy-chart CI still pending at this checkpoint. Feature pre-patch PASS is not proof that this patched candidate is release-ready. Other modules/deployed artifacts require separate dependency/security review; candidate scan is not a live-image scan.

### Exact continuation and remaining gates

Next: finish patched candidate gates, prepare parameterized stopped candidate preserving actual runtime configuration/mounts/user/networks and private build/rollback/backup receipts; do not start/switch it or run migrations without the concrete verified release workflow. Reconcile/register only new HUMAN capability descriptor and IAM scope through existing generic governed catalogue/lifecycle helpers using explicit installation bindings; derive intended scoped grant and owner simulations, then exact GET/POST Gateway deny/allow acceptance. Legacy batch registrar Device Grant includes lab defaults: use explicit endpoint/private-token path or parameterize issuer/client before portable use; never reuse its lab defaults silently in industrial deploy.

After candidate release acceptance: fresh HUMAN login, GET exact original three jobs through Gateway/owner (this verifies live mapper), review ready/eligible/version/snapshot and explicit operator confirmation in same human session; stable operation IDs/private receipts; POST only those jobs, then read back original eight IDs and canonical evidence. No live commands or mutations from this candidate have yet been executed. Any repeat failure must preserve diagnostic event and stop, without automatic retry loop.

All inherited open items remain OPEN: eight-row materialization and search, independent S3 byte/hash readback, second-source matching/review, original source RAW replay SPI versus handoff REPRODUCE, per-source/type/zone retention, portability/multi-host/multi-network/multi-tenant/domain parameterization, clean install/upgrade/restore/automated deploy (R-INSTALL), operational-awareness collectors/gates, ChatGPT-MCP latency, cross-module acceptance/release/branch reconciliation and every unresolved gate from previous handoffs. Documentation/PET consultation remain mandatory each sprint; no obligation waived by transport or Java PASS.


## Checkpoint conclusivo 2026-10-01 10:27 Europe/Rome — candidata verificata; server invariato

La candidata UDP `c0b6c98c5029682a51e5ed82717092f86bfbb318`, PR draft [#38](https://github.com/GioNob/ouf-udp-object-resolution/pull/38), supera tutti i job del module CI run36834423853: Java21/PostgreSQL17/build, disaster recovery, performance baseline e supply-chain/security/deployment chart SUCCESS. Confermati anche test mirati14, SDK pairwise e CRS/grid. Jackson BOM2.21.7 rimuove i due HIGH rilevati sulla candidata precedente; nessuna soppressione o indebolimento del gate. Questo aggiorna la precedente dicitura “CI patched pending”; non dimostra un deploy o una scansione dell'immagine live.

Il PASS della sonda Java fornito dall'operatore resta l'ultima azione sul server: nessun deploy/restart, nessuna nuova capability/scope/policy/grant/route attivata, nessun retry/replay/materialization. Ultimo stato dati noto: otto originali ACKED, cinque materializzati e tre job in quarantena tecnica. Causa storica e parità ObjectMapper del processo live restano non provate; gli altri gate aperti del checkpoint precedente rimangono aperti.

Preparata estensione parametrizzata di `r4a_udp_java_reference_probe.py`: opzionali `--resolver-image` + `--expected-revision` insieme. Verifica label OCI della revisione e stesso UID/GID non-root del live; risolve l'image ID immutabile, crea soltanto un helper fermo con networknone per copiare il JAR, lo rimuove e richiama il resolver nell'immagine candidata isolata con i binding/token/refs del live. Non avvia Spring, worker, migrazioni o applicazione candidata. Modalità live preesistente conservata. Due nuovi test coprono revisione/identità e cleanup senza start, anche su errore copia. Suite locale32 PASS; l'estensione non è ancora stata eseguita dall'operatore contro una candidata VPS.

Prossimo passo preciso: predisporre il blocco parametrizzato di build dell'immagine candidata fissata alla revisione CI-verificata e relativa prova GET-only contro i riferimenti reali, senza sostituire UDP live. Il blocco di build/prova non è ancora stato consegnato o eseguito: non presumere che la candidata sia presente sul VPS. Successivamente restano preparazione privata/rollback/backup, registrazione governata della capability HUMAN e relativi binding, acceptance owner/Gateway, rilascio controllato, lettura fresca e conferma HUMAN dei tre job originali. Non usare il vecchio blocco live come se verificasse la candidata e non riaprire job tramite SQL.

Il comando locale in corso è stato interrotto dal messaggio di stato dell'utente; patch verificata presente e test32 ripetuti PASS. Nessun task remoto di deploy era in corso. Handoff, installazione e roadmap aggiornati insieme per conservare questo punto di ripartenza.


## Checkpoint 2026-10-01 — build candidata isolata pronta; attesa esecuzione operatore

Consultati di nuovo UDP PET1.3 §§109.6/109.7/109.9 e Ingestion PET1.3 §45.2. Nuovo helper parametrizzato di build `r4a_prepare_udp_recovery_image.py`, codice fissato al commit coordinamento `0f872e39cc76778d3a7df218be706e25360148ec`: repository sorgente separato, SHA esatto, confronto path+hash byte delle migrazioni con baseline installata, tag univoco, label OCI, UID/GID e image ID, guard identità/restart live e receipt/log/source privati. Non avvia Spring, non modifica live/config/policy/DB e non esegue retry. [Procedura e limiti](https://github.com/GioNob/ouf-semantic-registry/blob/0f872e39cc76778d3a7df218be706e25360148ec/docs/installation/R4A_UDP_RECOVERY_CANDIDATE.md). Sette test nuovi + precedenti32 =39 PASS locale e CI recovery-cycle-scripts run36837613268. Bash del comando verificata sintatticamente. La build VPS e la sonda candidata sono ancora NON ESEGUITE.

Ultime prove distinte: candidata UDP `c0b6c98c5029682a51e5ed82717092f86bfbb318` module CI36834423853 tutti i gate SUCCESS; coordinamento precedente `5673633c899d4ad6a1b742b2dd06b613d75b603a` module CI36836641384 SUCCESS. Nuova CI del codice build, run36837613268: Java21/PostgreSQL17,39script test e container smoke tutti SUCCESS, esito finale verificato prima della consegna del comando. Non confondere CI con esecuzione sul VPS o rollout.

Nessuna nuova evidenza business: run SUCCEEDED, otto originali ACKED, cinque materializzati e tre quarantene tecniche. L'helper costruisce solo una candidata e mantiene dati/token/refs fuori chat. Mutable base image tags impediscono ancora riproducibilità bit per bit; usare l'image ID immutabile della build. Tutti i gate aperti del checkpoint precedente rimangono aperti. Nessun merge main, rilascio, nuova capability/scope/grant/route o job retry eseguito.

### Prossimo intervento operatore esatto — build e GET-only, non deploy

Questo blocco usa i binding laboratorio già osservati come argomenti, non come default dello script. Directory candidata nuova e privata; source/build.log/receipt restano sul server. JDK helper deve essere già presente dalla sonda precedente; se assente il preflight blocca prima build. Build può durare diversi minuti: stampa START e receipt, i dettagli restano nel log privato. Solo al PASS viene usato il suo image ID nella JVM isolata, con classi/librerie della candidata. Le sole scritture sono checkout/cache/immagine/ricevuta diagnostica; accessi business SELECT read-only e GET. Nessun riavvio/switch o migrazione. L'assistente non ha SSH: l'operatore deve eseguire questo blocco e riportare solo output protocollo, mai build.log/token/payload/receipt completo.

```bash
(
set -euo pipefail
umask 077
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
ouf_probe_dir=$(mktemp -d /tmp/ouf-r4a-udp-candidate.XXXXXX)
trap 'rm -rf -- "$ouf_probe_dir"' EXIT
for script in r4a_prepare_udp_recovery_image.py r4a_udp_java_reference_probe.py r4a_udp_token_transport_inventory.py; do
  git show 0f872e39cc76778d3a7df218be706e25360148ec:scripts/"$script" > "$ouf_probe_dir/$script"
done
sudo docker image inspect maven:3.9.11-eclipse-temurin-21 >/dev/null
sudo install -d -m 0700 /opt/ouf/udp-recovery-candidates
sudo python3 -B "$ouf_probe_dir/r4a_prepare_udp_recovery_image.py" \
  --repository https://github.com/GioNob/ouf-udp-object-resolution.git \
  --revision c0b6c98c5029682a51e5ed82717092f86bfbb318 \
  --baseline-revision edaba2bff18a2aaf52d1180f21f0e68984cc3437 \
  --container ouf-udp \
  --expected-live-image sha256:a47c8607c53451f7d0affba5994ec20dc6c09272ace68808daa9e63c33bc572e \
  --image-repository ouf-udp-recovery-candidate \
  --work-parent /opt/ouf/udp-recovery-candidates \
  | tee "$ouf_probe_dir/build-protocol.txt"
ouf_candidate_id=$(sed -n 's/^UDP_RECOVERY_CANDIDATE_IMAGE_ID=//p' "$ouf_probe_dir/build-protocol.txt")
test -n "$ouf_candidate_id"
sudo python3 -B "$ouf_probe_dir/r4a_udp_java_reference_probe.py" \
  --resolver-image "$ouf_candidate_id" \
  --expected-revision c0b6c98c5029682a51e5ed82717092f86bfbb318 \
  --container ouf-udp --jar-path /app/app.jar \
  --run 86809c17-3354-45ca-a7e6-57e903944b24 \
  --source managed-cinema-8ec8ae90 \
  --postgres-container ouf-postgres --database ouf_udp --db-user ouf_udp \
  --network ouf-backend --jdk-image maven:3.9.11-eclipse-temurin-21
)
```

Dopo l'output, aggiornare handoff/manuale/roadmap e usare receipt+image ID per preparazione rollback/backup/release e capability HUMAN governata. Solo dopo acceptance owner/Gateway e lettura fresca della reale istanza Spring, conferma HUMAN e retry dei tre originali. Non riattivare source/schedule, non replay/resend/SQL repair. Il PASS della sonda mantiene `MAPPER_RUNTIME_PARITY_NOT_PROVEN=true` e `HISTORICAL_CAUSALITY_NOT_PROVEN=true`; otto materializzazioni/search rimangono da dimostrare.


## Evidenza operatore 2026-10-01 10:44 Europe/Rome — immagine candidata costruita; sonda BLOCKED

Build dalla candidata UDP `c0b6c98c5029682a51e5ed82717092f86bfbb318` PASS, MIGRATIONS_IDENTICAL e LIVE_IDENTITY_UNCHANGED; nessun deploy/retry. Image ID risultante `sha256:e15fb3493992d67b065ecb3035beb36fd36b139a590544bd9fb55879bc782229`, tag `ouf-udp-recovery-candidate:r4a-c0b6c98c5029-f314176a6a7f`. Receipt privata `/opt/ouf/udp-recovery-candidates/udp-recovery-image-08py8slk/receipt.json`, non inoltrare il contenuto. La build non includeva la sonda: PROBE_EXECUTED=false è coerente con la successiva esecuzione separata.

La sonda GET-only identifica questa candidata e il precedente live `sha256:a47c8607c53451f7d0affba5994ec20dc6c09272ace68808daa9e63c33bc572e`, compiler `sha256:6fdc855a6ed81d288ca7ca37ac6ff5e9308b612485c0801d70b25a858c83d237`; poi BLOCKED TYPE=RuntimeError senza protocollo Java. Questo NON prova incompatibilità dei riferimenti né materializzazione. BUSINESS_STATE_UNCHANGED; gli ultimi conteggi restano cinque materializzati/tre quarantene, non un nuovo readback.

Difetto riprodotto nel runner: il blocco imposta umask077, ma mkdir(mode0755) crea probe-classes0700 root-owned. La JVM non-root non può attraversare tale directory. Correzione circoscritta ai permessi di directory/classi compilate non segrete: chmod0755 directory e0644 bytecode dopo javac; refs.json resta0600 UID live, token directory bind read-only. Nessuna chmod su token/refs/installazione/server. Nuove righe sicure COMPILE=PASS e LAUNCH_FAILURE_CATEGORY enum da marker JVM, senza stderr/exception values. Due nuovi test coprono umask077 con refs privati e categoria senza leakage; suite locale41 PASS. Consultato di nuovo UDP PET1.3 §109.7, gate punto d'uso preservato. CI nuova correzione pending; non dichiarare risolta la sonda VPS prima del suo output. Il difetto del runner non spiega le tre quarantene storiche nel worker.

Prossimo intervento: rieseguire SOLO la sonda GET-only corretta sulla stessa immagine candidata immutabile già costruita, senza rebuild/deploy/policy/retry. Verrà consegnato un nuovo blocco fissato al commit della correzione dopo verifica CI. Tutti i gate precedenti restano aperti (mapper reale Spring, recovery HUMAN, release/rollback/backup, otto materializzazioni, search, S3 byte/hash, matching/replay/retention, R-INSTALL/portabilità, operational awareness/latency/riconciliazione).


### Continuazione fissata — correzione runner verificata in CI; solo nuova sonda

Correzione runner `2ef5c18e8706b4e8150576628b5cdfeef067bec8`, module CI [36838517239](https://github.com/GioNob/ouf-semantic-registry/actions/runs/36838517239): Java21/PostgreSQL17, recovery-cycle-scripts41 e container smoke tutti SUCCESS. Comando Bash validato. Il precedente blocco build+probe è superato per questa continuazione: la build è già PASS e l'immagine candidata va riutilizzata per ID. Questa correzione è solo nei tool di coordinamento; candidata UDP/image ID e baseline installata invariati. Difetto permessi riprodotto localmente, causalità precisa del BLOCKED VPS da confermare con l'output della sonda corretta. Non equiparare difetto della sonda a causa delle quarantene worker.

Eseguire come oufadmin e riportare solo righe protocollo. Nessun rebuild/pull/start Spring/deploy/retry/replay/policy. Il container helper viene creato fermo unicamente per copiare il JAR e rimosso; la JVM usa mount read-only, GET Gateway e SELECT read-only già previsti. Nuovo output COMPILE=PASS distingue compilazione da avvio; eventuale LAUNCH_FAILURE_CATEGORY enum non contiene stderr. Se BLOCKED, conservare codice/categoria/frame sicuri e fermare la recovery; nessun loop di tentativi business.

```bash
(
set -euo pipefail
umask 077
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
ouf_probe_dir=$(mktemp -d /tmp/ouf-r4a-udp-candidate.XXXXXX)
trap 'rm -rf -- "$ouf_probe_dir"' EXIT
for script in r4a_udp_java_reference_probe.py r4a_udp_token_transport_inventory.py; do
  git show 2ef5c18e8706b4e8150576628b5cdfeef067bec8:scripts/"$script" > "$ouf_probe_dir/$script"
done
sudo python3 -B "$ouf_probe_dir/r4a_udp_java_reference_probe.py" \
  --resolver-image sha256:e15fb3493992d67b065ecb3035beb36fd36b139a590544bd9fb55879bc782229 \
  --expected-revision c0b6c98c5029682a51e5ed82717092f86bfbb318 \
  --container ouf-udp --jar-path /app/app.jar \
  --run 86809c17-3354-45ca-a7e6-57e903944b24 \
  --source managed-cinema-8ec8ae90 \
  --postgres-container ouf-postgres --database ouf_udp --db-user ouf_udp \
  --network ouf-backend --jdk-image maven:3.9.11-eclipse-temurin-21
)
```

Punto di attesa preciso: sonda candidata corretta non ancora eseguita. Dopo PASS aggiornare tre documenti e proseguire con release preparata/rollback/backup/capability HUMAN e scope/grant/route governati, acceptance reale e recovery dei tre job originali. Tutti i gate aperti sopra restano validi; ultimo stato business cinque materializzati/tre quarantene non reread da questa CI.


## Evidenza operatore 2026-10-01 10:51 Europe/Rome — sonda candidata PASS; preparazione container fermo

L'operatore ha rieseguito il runner corretto `2ef5c18e8706b4e8150576628b5cdfeef067bec8`: COMPILE=PASS e UDP_SHIPPED_JAVA_RESOLVE_CONTRACTS=PASS, candidato=true. Identità immutabili: live `sha256:a47c8607c53451f7d0affba5994ec20dc6c09272ace68808daa9e63c33bc572e`, candidata `sha256:e15fb3493992d67b065ecb3035beb36fd36b139a590544bd9fb55879bc782229`, compiler `sha256:6fdc855a6ed81d288ca7ca37ac6ff5e9308b612485c0801d70b25a858c83d237`. Non ha avviato Spring, materializzato o fatto retry. Il BLOCKED della sonda precedente è superato dal nuovo PASS; il difetto umask077 riprodotto/corretto nel runner è compatibile con questo esito, senza diagnosticare retroattivamente il worker. MAPPER_RUNTIME_PARITY_NOT_PROVEN e HISTORICAL_CAUSALITY_NOT_PROVEN restano limiti. Ultimo stato business noto cinque materializzati/tre quarantene, nessun nuovo readback da questa sonda.

Consultati UDP PET1.3 §§109.6/109.7. Gli helper legacy prepare/switch UDP hanno commit, container, rete e dominio laboratorio hardcoded e talvolta eseguono preflight di una versione precedentemente IN_REVIEW: NON riutilizzarli per questa release. Nuovo `scripts/r4a_stage_udp_recovery.py` parametrizzato: argomenti container, candidate-container, build-receipt e work-parent; dalla receipt build valida identifica SHA/image ID/live ID. Profilo supportato attuale: una rete nominata derivata dal live, UID/GID non-root, bind mount rprivate, logging/restart/config normali senza port/DNS/device/resource/custom override. Nessuna costante macchina/rete/tenant/domain nel codice. Config non supportata viene rifiutata, non omessa. Multi-network e altri profili industriali restano gate aperti; questo helper non certifica portabilità generale.

Conserva snapshot Docker completo (contiene segreti/env) in file root-only sotto directory0700, receipt privata, hash config, restart policy precedente e binding build. Replica env completo, mount incl. RW/propagation, rete/logging/label installazione, confronta UID e default runtime immagine. Unica variazione di env della candidata è OUF_UDP_MATERIALIZATION_RECOVERY_ENABLED=true; NON è una configurazione attivata sul live. Crea soltanto container fermo, restart=no per impedire avvio a riavvio daemon; nessun pull, stop/start/rename live, dump/restore/migrazione/policy/retry. Readback immagine/env/mount/log/defaults sicurezza/rete, verifica identità/config/restart live. Env file temporaneo viene eliminato, snapshot privato mantenuto. Se errore rimuove solo l'ID appena creato e fermo, mai live e mai force; container avviato da altro attore viene preservato per riconciliazione. Nome candidato preesistente blocca, nessuna sostituzione automatica.

Sette test nuovi (preservazione/snapshot privato/no start, binding non supportato, nome occupato, readback errato, live restart concorrente, candidata avviata da terzi, receipt non privata), suite locale48 PASS. CI estesa con hash workflow aggiornato; CI nuova pending a questo checkpoint. Lo staging sul VPS è ancora NON ESEGUITO, nessun nuovo container applicativo preparato dall'assistente.

Dopo staging PASS: usare receipt/snapshot privati per workflow switch/rollback con drain/backup DB coerente e conservazione container precedente, senza restore automatico dei dati; prerequisiti capability HUMAN udp.materialization.retry, scope/grant/route governati, fresh policy e owner/Gateway deny/allow, nuova lettura della reale istanza Spring e conferma HUMAN per i tre job. Database backup NON è stato preso dal helper stage, schema/recovery/search/R-INSTALL e tutti i gate precedenti restano aperti. Un container con flag=true ma fermo non prova API disponibile né autorizzazione o rilascio.


### Staging definitivo verificato — attesa operatore, nessun switch

Script staging definitivo `d1d123a801d4dabe2d6479a05b48e39b0b2d952c`, module CI [36840164603](https://github.com/GioNob/ouf-semantic-registry/actions/runs/36840164603): Java21/PostgreSQL17,48 test degli script e container smoke tutti SUCCESS. Verificata conservazione degli alias di rete, inclusi nomi rimasti da precedenti rename, con candidata ferma; nessun alias/endpoint attivo sostituito sul live. Label installazione preservate, provenienza OCI della candidata coerente con il suo SHA, default sicurezza host confrontati a readback. Bash del comando validata. Questo supera la dicitura CI staging pending; NON prova esecuzione VPS.

Eseguire il blocco seguente come oufadmin. Conservare solo sul server snapshot/env/receipt; inoltrare soltanto protocollo. Candidata applicativa `ouf-udp-materialization-candidate` viene creata FERMA con restart=no, flag recovery=true solo nei suoi env non attivi. Se il nome esiste già, riconciliare senza rimuoverlo o ripetere alla cieca. Il servizio live rimane attivo. Non eseguire docker start sulla candidata: release, backup coerente, rollback e registrazione governata HUMAN sono ancora da completare.

```bash
(
set -euo pipefail
umask 077
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
ouf_stage_script=$(mktemp /tmp/ouf-r4a-udp-stage.XXXXXX.py)
trap 'rm -f -- "$ouf_stage_script"' EXIT
git show d1d123a801d4dabe2d6479a05b48e39b0b2d952c:scripts/r4a_stage_udp_recovery.py > "$ouf_stage_script"
sudo python3 -B "$ouf_stage_script" \
  --container ouf-udp \
  --candidate-container ouf-udp-materialization-candidate \
  --build-receipt /opt/ouf/udp-recovery-candidates/udp-recovery-image-08py8slk/receipt.json \
  --work-parent /opt/ouf/udp-recovery-candidates
)
```

Punto di attesa preciso: script stage pubblicato e CI verde, operatore non ha ancora eseguito questo blocco. Dopo PASS acquisire receipt e aggiornare handoff/manuale/roadmap; preparare workflow release/rollback e capability HUMAN/scope/grant/route con policy fresca. Nessun nuovo deploy/backup DB/policy/retry da questa chat, otto materializzazioni e tutti gli altri gate ereditati rimangono aperti. Il PASS della sonda candidata resta acquisito, mapper reale Spring e causa storica restano non provati.


## Evidenza operatore 2026-10-01 11:41 Europe/Rome — staging PASS; release tecnica preparata

Staging operatore dal codice `d1d123a801d4dabe2d6479a05b48e39b0b2d952c` PASS: CANDIDATE_STOPPED, RESTART_DISABLED, ENV preservato eccetto flag recovery, mount match, live invariato, DEPLOY=false, DATABASE_BACKUP_TAKEN=false, RETRY=false. Receipt privata `/opt/ouf/udp-recovery-candidates/udp-recovery-stage-qys1tqlg/receipt.json`. Candidata `ouf-udp-materialization-candidate`, immagine `sha256:e15fb3493992d67b065ecb3035beb36fd36b139a590544bd9fb55879bc782229` da UDP SHA `c0b6c98c5029682a51e5ed82717092f86bfbb318`; live resta precedente. Snapshot completo env/token/endpoint resta soltanto sul server, non inoltrare.

Consultati UDP PET1.3 §§109.6/109.9 (lease/drain/release/rollback, nessun UPDATE business). Preparato `scripts/r4a_release_udp_recovery.py`: tutti i binding stage receipt, PostgreSQL/database/user, Gateway container, helper curl image, URL/porta/path health, versione Flyway, source/run/probe job/conteggi attesi, stop timeout e health attempts sono CLI espliciti. Importa helper stage dallo stesso commit fisso. Nessun dominio/host/tenant/client/installazione hardcoded. Profilo Docker dello staging conservato; non chiude i gate deployment industriale multi-network/resource profiles.

Preflight verifica ID/name/config live e candidata da snapshot/receipt, flag e mount, user/rete/log/defaults sicurezza, label OCI, helper curl già presente (no pull), salute live e raggiungibilità da Gateway, Flyway34/checksum/history, otto job del run con cinque SUCCEEDED/tre QUARANTINED; zero job globali READY/RUNNING. Non include payload nelle evidenze. Lock per nome live e receipt release non ripetibile senza riconciliazione. Snapshot/receipt root-only, write atomica con fsync, intent persistita prima di operazioni. Disabilita restart vecchio, stop graceful60s e reject exit137/OOM, ricontrolla drain/stati, pg_dump -Fc privato dopo stop, fsync/SHA256/pg_restore -l; NON esegue restore. Mantiene dump anche su fallimento per riconciliazione.

Poi rename e start della candidata usando gli ID verificati, health locale e dal Gateway, GET endpoint recovery anonimo e con header HUMAN contraffatto devono401/403; ricontrolla identica Flyway history e stati/versioni/attempts degli otto originali, nessun job READY/RUNNING. Ripristina restart policy originale sul nuovo live; vecchio resta fermo con restart=no per rollback. Errori dopo inizio operazioni attivano rollback per ID (anche risposta rename persa), fermano candidata e ripristinano nome/restart/health precedente, senza cancellare container o ripristinare DB. Persistenza receipt fallita non impedisce il tentativo di rollback; stato MANUAL_RECONCILIATION_REQUIRED se recovery runtime non verificata. Codici failure allowlisted, mai stderr/message arbitrari.

**Distinzione di gate:** il prossimo comando è rilascio tecnico dell'applicazione, non pubblicazione/abilitazione autorizzata della capability recovery. Capability udp.materialization.retry/descrittore/scope/grant/route HUMAN non sono ancora registrati/attivati da questa chat; SDK default-deny resta il confine. L'API condizionale viene caricata dall'env già staged, ma i GET anonimi/spoof negati NON provano autorizzazione HUMAN, disponibilità tramite route governata o mapper reale in richiesta autorizzata. Non dichiarare AUTHZ-READY/GATEWAY-BINDING o R-SMOKE chiusi con questo rilascio. Dopo deploy tecnico serve workflow governato registry/IAM/policy fresh/draft/preview/simulate/publish preservando policy completa, grant HUMAN ristretto source/run/tenant e prove SERVICE/AI/HUMAN deny/allow, poi lettura fresca Spring dei tre originali e conferma HUMAN. Nessun retry/resume/replay/reactivate o attestazione business nel comando release.

Undici test release nuovi: switch, rollback da backup/health/auth/changed jobs/forced stop, risposta rename persa, rollback manuale, backup hash+lista senza restore, worker non-idle e schema drift. Suite combinata59 PASS localmente; CI estesa e solo hash workflow aggiornato. CI nuova pending. Release operator NON ESEGUITA, backup DB ancora NON PRESO. Ultimo readback business cinque materializzati/tre quarantene e tutti i gate ereditati rimangono aperti (otto materializzazioni/search, mapper Spring/causa storica, S3 bytes/hash, seconda source matching/review, RAW replay SPI, retention, R-INSTALL install/upgrade/restore/portabilità/deploy automatico, operational awareness/MCP latency/riconciliazione branches).


### Release tecnica fissata e CI verde — prossimo intervento operatore

Codice release `53ee0c69d6ecabc5d8bdbfdaa838beb476b06537`, module CI [36846088719](https://github.com/GioNob/ouf-semantic-registry/actions/runs/36846088719): Java21/PostgreSQL17,59 test degli script e container smoke tutti SUCCESS. Dopo aggiunta dei codici diagnostici allowlisted,11 test release ripetuti PASS e poi CI completa59 PASS. Questo supera CI pending sopra. Verificato anche codice shipped UdpIamSecurityConfiguration: /api/udp/v1/governance/** richiede autenticazione JWT; spoof senza bearer viene negato prima della guard HUMAN. Il controllo anonimo/spoof del release non verifica un bearer HUMAN/SERVICE valido né grants e resta diagnostica amministrativa senza operazioni business, non bypass Gateway per materializzazione. Consultati inoltre Authorization v1.5 (atomic publication/enforcement/fail-closed) e Gateway v1.5 (owner fine-grained enforcement e binding governato); confini preservati.

Il blocco seguente comporta una breve indisponibilità UDP: stop graceful, backup PostgreSQL dopo drain, switch e controlli; rollback automatico del solo runtime se falliscono. Mantiene vecchio container fermo/restart=no e backup privato, NON esegue restore/migrazioni nuove/policy/grant/route/retry. Helper curl deve già essere presente; in caso contrario blocca prima dello stop, nessun pull implicito. Se receipt release esiste o il comando si interrompe, riconciliare receipt/container ID prima di qualsiasi ripetizione, non rilanciare alla cieca. Receipt release/root snapshot/dump restano privati sul server; riportare soltanto output sicuro.

```bash
(
set -euo pipefail
umask 077
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
ouf_release_dir=$(mktemp -d /tmp/ouf-r4a-udp-release.XXXXXX)
trap 'rm -rf -- "$ouf_release_dir"' EXIT
for script in r4a_stage_udp_recovery.py r4a_release_udp_recovery.py; do
  git show 53ee0c69d6ecabc5d8bdbfdaa838beb476b06537:scripts/"$script" > "$ouf_release_dir/$script"
done
sudo python3 -B "$ouf_release_dir/r4a_release_udp_recovery.py" \
  --stage-receipt /opt/ouf/udp-recovery-candidates/udp-recovery-stage-qys1tqlg/receipt.json \
  --postgres-container ouf-postgres --database ouf_udp --db-user ouf_udp \
  --gateway-container ouf-apisix --curl-image curlimages/curl:8.16.0 \
  --health-origin http://127.0.0.1:8080 --health-path /actuator/health \
  --gateway-health-url http://ouf-udp:8080/actuator/health \
  --expected-flyway 34 --stop-seconds 60 --health-attempts 45 \
  --source managed-cinema-8ec8ae90 \
  --run 86809c17-3354-45ca-a7e6-57e903944b24 \
  --probe-job 7793566d-b9d4-4402-8cda-c09b8f135c04 \
  --expected-job-count 8 --expected-succeeded 5 --expected-quarantined 3
)
```

Punto di attesa: operatore non ha ancora eseguito la release. In questa chat release e backup DB NON ESEGUITI. Stage PASS e sonda candidata PASS restano acquisiti. Dopo output aggiornare handoff/manuale/roadmap e registrare versione/image live o rollback; poi workflow governato capability HUMAN/IAM/policy/route, prove negative e HUMAN reali, review Spring delle tre quarantene e conferma prima dei tre retry originali. Non dichiarare full acceptance né otto materializzazioni; tutti i gate ereditati sopra restano aperti.


## Evidenza operatore 2026-10-01 12:05 Europe/Rome — rilascio tecnico UDP PASS

Operatore ha eseguito release `53ee0c69d6ecabc5d8bdbfdaa838beb476b06537`: nuova immagine LIVE `sha256:e15fb3493992d67b065ecb3035beb36fd36b139a590544bd9fb55879bc782229`, candidata UDP source `c0b6c98c5029682a51e5ed82717092f86bfbb318`. Flyway34 invariata e otto job originali invariati, cinque SUCCEEDED/tre QUARANTINED secondo guard release; health locale e da Gateway PASS, anonimo/header HUMAN spoof negati. Backup PostgreSQL privato preso dopo drain, pg_restore -l PASS; hash/path nel receipt privato, non incollare contenuto. Receipt `/opt/ouf/udp-recovery-candidates/udp-recovery-stage-qys1tqlg/release-receipt.json`. Rollback `ouf-udp-rollback-1ecc26af3181` fermo, restart disabilitato. Vecchia immagine `sha256:a47c8607c53451f7d0affba5994ec20dc6c09272ace68808daa9e63c33bc572e` conservata. Nessun restore/policy/route/grant/retry. Non ripetere stage/build/switch già PASS.

HUMAN_AUTHORIZATION_NOT_PROVEN=true. Nuova API caricata per flag già staged; i GET negati non dimostrano mapper Spring in richiesta autorizzata, scope/grant/route, materializzazione o serving. Tre job originali continuano in quarantena; la causa storica rimane non provata. Registro/governance capability `udp.materialization.retry` ancora da attivare. Nuovo passo in preparazione: batch registrar/lifecycle parametrico per issuer/client/base endpoint/tenant/subject, receipt privata con intent prima POST e gestione incertezza; un login HUMAN per registrazione catalogo e draft ristretto ai tre job del source/run, conservando intera policy ACTIVE fresca. Nessuna pubblicazione automatica del draft. Scope IAM, route Gateway, simulazioni e conferma HUMAN di publication/recovery rimangono passi separati. Baseline politica35 era ultima osservata, non assumere attuale: rileggere.

Consultati Authorization PET1.5 §109.2, UDP §109.9 e Gateway confini binding/owner enforcement. Contratti deployed SDK/AuthorizationAdminApi verificati: CapabilityDescriptor.operation è stringa (COMMAND supportato), grant constraints resourceType/resourceId/resourceAttributes consentono scope esatto per source/run/job; ownerResource del retry usa materialization-job, tenant e attributi module=UDP/sourceRef/jobRef/typeRef. Schema contrattuale baseline field-level draft più esteso non equivale al DTO del runtime: conservare entrambi come gap alignment, nessun cambio silenzioso dello SDK. Tutti i gate ereditati restano aperti (full8/search, mapper Spring/causa storica, S3 bytes/hash, matching/replay/retention, R-INSTALL/portabilità/install/upgrade/restore/deploy automatico, operational awareness/MCP latency/release reconciliation).


### Checkpoint 2026-10-01 — recovery: correzione del binding DataAccessLabel prima dei grant

Il release receipt privato `/opt/ouf/udp-recovery-candidates/udp-recovery-stage-qys1tqlg/release-receipt.json` attesta il deploy tecnico della candidata c0b6c98c5029682a51e5ed82717092f86bfbb318 (immagine sha256:e15fb3493992d67b065ecb3035beb36fd36b139a590544bd9fb55879bc782229), backup verificato con restore-list, Flyway 34 e job originali invariati. HUMAN authorization non provata; nessun retry.

La revisione dei grant ha rilevato che MaterializationRecoveryService passava RAW access_label come ResourceContext.organizationId. Il PET Authorization v1.5 §36.10 e lo SDK richiedono invece l'attributo dataAccessLabel. Fix `afa5c4c4cf03bff4e39b02e27f898256c3776cbc`: organizationId nullo, etichetta RAW in dataAccessLabel, scope tenant/source/run/job conservato. Un test Spring/PostgreSQL usa AuthorizationPolicy.evaluate reale: etichetta diversa nega review e retry prima della lettura dei contratti, senza evento o transizione; etichetta corretta ammette il retry. CI avviata, risultato non ancora acquisito. Non attivare capability/grant prima del fix verificato e distribuito. La capability nuova non è stata attivata: nessun ampliamento di autorità eseguito.

Prossimo passo: una sola esecuzione operatore di build con baseline c0b6, probe Java GET-only, stage fermo e release controllato con backup/rollback. Parametri di ambiente espliciti; nessun replay, retry o riattivazione source. Dopo readback del release corretto, preparare catalogo e policy DRAFT a scope dei tre job, senza pubblicare ACTIVE automaticamente. Restano aperti full8/search, mapper Spring e causalità storica, industrializzazione deploy e tutti i gate precedenti.


### Checkpoint 2026-10-01 — fix DataAccessLabel verificato, release operatore pronto

UDP `afa5c4c4cf03bff4e39b02e27f898256c3776cbc`: workflow PR run36848626832 SUCCESS, 15 test (recovery10, diagnostica2, gate3), zero failure/error/skipped; run36848626818 SUCCESS in tutti i job Java21/PostgreSQL17, supply-chain/deployment con vulnerability gate, disaster recovery e performance. Shared SDK run36848626776 e CRS run36848626844 SUCCESS. Nessuna migrazione aggiunta; compatibilità con la baseline live c0b6 sarà verificata di nuovo dalla build sul server. Il deploy del fix NON è ancora eseguito: live resta immagine e15fb349… / Flyway34; 5 SUCCEEDED + 3 QUARANTINED originali; nessun retry né nuova capability/grant attivata.

Il runbook R4A_UDP_RECOVERY_CANDIDATE contiene il blocco unico build → Java GET-only → stage fermo → release con backup, snapshot job invariato, negative anonymous/spoof, health Gateway e rollback conservato. Helper pinnati a 53ee0c69d6ecabc5d8bdbfdaa838beb476b06537; baseline live e immagine attesa aggiornate. Bash syntax validata; esecuzione Docker/DB resta a carico dell'operatore, senza accesso remoto da questa sessione. Fermarsi al primo errore. Richiesto solo protocollo simbolico, non receipt privati o log completi. Dopo PASS, riprendere preparazione governata del catalogo e policy DRAFT con fresh HUMAN login; ACTIVE/retry ancora non autorizzati/provati dalle evidenze.


### Checkpoint 2026-10-01 — fix image costruita, stage bloccato prima di ogni deploy

Evidenze operatore: build UDP afa5c4c4cf03bff4e39b02e27f898256c3776cbc PASS, immagine sha256:024c6691888855ef4d5574cadacf060e0dfbf7ff891dbc9a747628f5b5c8a519; receipt privato /opt/ouf/udp-recovery-candidates/udp-recovery-image-ckrhncjk/receipt.json. Migrazioni identiche e live invariato durante build. Probe Java candidata GET-only PASS; mapper Spring e causalità storica non provati. Stage BLOCKED ValueError, senza stage receipt riportato, DEPLOY=false e RETRY=false; release non eseguito.

Revisione helper: lo stage richiedeva feature recovery false sul live, incompatibile con un successivo upgrade del runtime c0b6 già recovery-enabled. Questo è un difetto del percorso upgrade; il messaggio generico non prova ancora il codice effettivo sul server. Lo stage ora richiede --allow-enabled-live per quell'upgrade, rifiuta valori diversi da true/false, conserva gli altri guard e aggiunge --check-only per preflight in sola lettura. StageError riporta esclusivamente codici statici senza valori privati. Receipt distingue prima abilitazione da upgrade. Test per enabled-live negato senza opzione, upgrade consentito, flag invalido, preflight senza receipt/container e release con ambiente invariato. Non disabilitare la feature sul live per aggirare il guard. Riutilizzare la build già validata; nuovo blocco preflight → stage → release, senza rebuild/replay/retry. Se emerge un altro guard, bloccare e riconciliare dal codice simbolico.


### Checkpoint 2026-10-01 — helper upgrade verificato; ripresa senza ricostruire immagine

Fix helper deploy `b71a964b663e47bb23a93f7c46c62d3ecaa84e0b`: 22 test locali stage/release PASS, suite helper completa 63 test PASS. CI Semantic Registry run36849541342 job recovery-cycle-scripts SUCCESS (63 test); gli altri job del modulo sono ancora in corso. Il codice applicativo UDP resta afa5c4c4cf03bff4e39b02e27f898256c3776cbc, già verde in tutte le sue CI; si riusa esattamente immagine 024c6691… e receipt build ckrhncjk. Nessun stage/release del fix è provato finché non arriva il nuovo protocollo operatore. Live atteso resta e15fb349… / Flyway34. La prima verifica del blocco seguente è --check-only, GET/inspect soltanto: se non PASS, set -e interrompe senza stage o release. Se PASS, stage fermo e release guardato. Non inviare file privati o messaggi raw di errore; usare CODE statico. Con esito incerto non ripetere release, riconciliare receipt.


CI finale helper upgrade: Semantic Registry run36849692475 su 71c84cebf5a91a3d8d879019ff7eed4f36bf44f6 SUCCESS nei tre job recovery-cycle-scripts (63 test), java21-postgresql17 e container-smoke. Codice helper pinnato b71a964b663e47bb23a93f7c46c62d3ecaa84e0b invariato. Il successivo aggiornamento è solo documentale. Rilascio sul server ancora NON eseguito/provato.


### Checkpoint 2026-10-01 12:37 Europe/Rome — fix DataAccessLabel distribuito

Preflight READ_ONLY PASS (LIVE_RECOVERY_ENABLED=true, CANDIDATE_ABSENT=true); stage receipt privato /opt/ouf/udp-recovery-candidates/udp-recovery-stage-8oc0p5t1/receipt.json PASS. Release receipt privato nello stesso directory release-receipt.json: PASS, immagine live sha256:024c6691888855ef4d5574cadacf060e0dfbf7ff891dbc9a747628f5b5c8a519, codice afa5c4c4cf03bff4e39b02e27f898256c3776cbc, Flyway34, backup restore-list PASS, original jobs unchanged, health Gateway PASS, anonymous/spoof denied. Rollback ouf-udp-rollback-2f9a72e60975 fermo/restart disabilitato; conservare anche i rollback precedenti finché non riconciliati. Nessun retry. HUMAN authorization non ancora provata. Stato precedente 5 SUCCEEDED + 3 QUARANTINED resta invariato nel guard del release; full8/search non acquisito. Prossimo passo: registrazione batch parametrizzata e policy DRAFT HUMAN, tre grant a resourceId esatto/source/run/tenant e DataAccessLabel RAW effettivo, conservando interamente fresh ACTIVE. Nessuna pubblicazione implicita o modifica IAM/route. Il login admin HUMAN sarà necessario per le API amministrative; non usare token SERVICE.


### Checkpoint 2026-10-01 — batch scoped HUMAN policy preparation

Nuovi helper parametrizzati: r4a_materialization_recovery_scope.py legge soltanto metadata dei job originali/RAW, richiede stato tecnico recuperabile e nessun effetto canonico, scrive scope privato exact-job/source/run/type + DataAccessLabel effettivo. r4a_prepare_scoped_human_policy.py accetta manifest batch HUMAN e scope privati, issuer/client/audience/admin scope/API base/tenant/subject/expiry/state-file obbligatori. Registra soltanto descrittori mancanti semanticamente compatibili e crea un DRAFT add-only: ACTIVE fresco e tutte le entry esistenti preservate; baseline/revision/readback/diff preview ricontrollati, nessuna pubblicazione. State file esclusivo 0600 con intent fsync prima di ogni POST; esito incerto obbliga riconciliazione, nessun repost automatico. Token solo in memoria, no redirect e nessuna modifica IAM/route/job. La preview non è prova di autorizzazione runtime. Test di perdita risposta registration/draft, conflitti pre-write, ACTIVE drift, preview scoped-grant drift, deny tenant/canonical effects/labels assenti/SERVICE/duplicati/expiry/redirect; test locali PASS, CI avviata. Per l'esecuzione admin serve fresh Device Grant HUMAN del soggetto esplicito; mantenere il codice fuori dalla chat. Dopo DRAFT: simulazioni deny/allow governate, IAM scope client binding e Gateway exact routes, pubblicazione esplicita HUMAN e poi lettura Spring dei tre job; retry soltanto dopo review/confirm nello stesso contesto umano. Full8/search e gli altri gate precedenti restano aperti.


### Checkpoint 2026-10-01 — scoped batch operatore pronto, nessuna activation

CI helper run36851261430 recovery-cycle-scripts SUCCESS, 73 test; modulo fermato prima di Maven perché checksum workflow non aggiornato insieme al nuovo test. Registro source-checksums corretto in 7a163de5bb0351f5bf332f7ad9f42d0cdf4240ea, includendo anche i tre nuovi file helper/test; gate invariato. Nuova CI avviata, completamento non ancora acquisito. Il codice dei due helper resta quello del commit 4c8600c45510ae451dd8385bbb66b3903eb3d080. Operator binding: soggetto HUMAN b93d8cf6-cd14-4ee6-91d7-84cd76c4f500, tenant ouf-lab, admin scope authorization.policy.admin, IAM client ouf-human-admin; validUntil esplicito 2026-10-02T10:00:00Z (12:00 Europe/Rome), da sostituire se la ripresa avviene dopo scadenza. State directory privato /etc/ouf/deploy-snapshots/udp-materialization-recovery-policy; resources.json e draft-receipt.json non stampare. Non rieseguire il blocco se uno di questi file esiste: riconciliare prima lo stato privato; zero repost automatici. DRAFT e preview non provano capability runtime allow. Nessuna publication/IAM/Gateway/retry implicita. Il blocco richiede login Device Grant HUMAN nel browser e non deve essere autenticato con identità SERVICE o altro subject.


### Checkpoint finale 2026-10-01 — scoped HUMAN batch verificato, in attesa login operatore

Semantic Registry CI push run36851593724 su 88b5b1802eeac5538f8e2205ed86a46d52d55cde SUCCESS: recovery-cycle-scripts (73 test), Java21/PostgreSQL17, container-smoke. Pairwise Shared SDK run36851598351, Authorization Semantic run36851598357 e Gateway live run36851598405 SUCCESS. Source checksum gate ripristinato e verificato. Helper code 4c8600c45510ae451dd8385bbb66b3903eb3d080 immutato. Aggiornamento seguente solo documentale. Il blocco è pronto ma NON ancora eseguito: catalogue/DRAFT/ACTIVE/IAM/Gateway/job invariati da questa sessione; prossimo intervento richiesto è l'esecuzione operatore con fresh Device Grant HUMAN amministratore. Nessun retry eseguito o provato. Conservare tutte le limitazioni e gate indicati sopra.


### Checkpoint 2026-10-01 12:54 Europe/Rome — scoped HUMAN DRAFT creato

Operatore: R4A_SCOPED_HUMAN_POLICY_DRAFT PASS, base ouf-lab-authorization:35, draft b305bcae-a03f-4f0d-8b81-81508bcddb24 revision0; una capability e tre grant scoped, entry esistenti preservate, ACTIVE invariato. Receipt privato /etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/draft-receipt.json. POLICY_UNPUBLISHED=true; preview non è prova di autorizzazione; IAM/route invariati; RETRY=false. Non rieseguire prepare o rigenerare resources/receipt: bozza registrata, da riprendere per ID/revision esatti. Target atteso :36 da confermare dal receipt/API. Prossimi gate: simulazioni SDK del DRAFT con scope RAW effettivi (allow dei tre job e deny actor/tenant/subject/source/run/job/label/scope), binding opzionale IAM della nuova scope al client HUMAN e route Gateway esatte senza modificare OIDC/limiti; pubblicazione con revisione e conferma HUMAN esplicita; poi GET della recovery sul runtime Spring reale e soltanto dopo conferma eventuale retry originale. Tutte le evidenze e limitazioni precedenti preservate.


### Checkpoint 2026-10-01 — inventario binding parametrizzato prima di apply/publish

Nuovo r4a_recovery_binding_inventory.py: tutti i binding IAM/Gateway/realm/client/scope/config destination/admin origin/curl image/backend/path/snapshot espliciti. Riusa soltanto parser pure del precedente inventory, senza i suoi default runtime. Legge route con APISIX Admin GET e chiave solo via stdin; legge client/scope/binding con kcadm GET esistente, nessuna ricerca o stampa credenziali. Controlla Gateway identity/config invariati; scrive snapshot esclusivo root0600 sotto parent0700, contenente configurazione tecnica privata, da non condividere. Output pubblico solo fatti/ID/path sanitizzati. URI candidates sono conservativi: priority/vars/radixtree parity non provata. Un accesso IAM bloccato non impedisce acquisire l'inventario Gateway; stato PARTIAL non equivale a PASS. Non cambia scope, route, policy o job e non fa retry. Quattro test locali PASS (secret/stdin-only + GET, IAM binding, mount/clear HTTP fail closed, snapshot parziale privato). Nuovo test aggiunto alla CI; checksum workflow e nuovi file aggiornati nello stesso commit. DRAFT b305bcae-a03f-4f0d-8b81-81508bcddb24 revision0 resta in attesa simulazioni/binding/pubblicazione HUMAN. Necessario l'output inventario del server per preparare un apply che preservi la configurazione effettiva; non ricreare bozza o scope resource file.


### Prossima esecuzione — binding inventory read-only

Blocco nel runbook R4A_UDP_RECOVERY_CANDIDATE per inventario IAM/Gateway, codice c353542fb687b23147d10e76e478d8286e840a2a. Snapshot /etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/binding-inventory.json PRIVATE: include route complete e segreti tecnici OIDC; non incollare o esportare. Solo output simbolico. Non richiede nuovo Device Grant HUMAN, riusa soltanto la sessione amministrativa kcadm già configurata e legge APISIX tramite root/mount esistente. Se accesso IAM fallisce, PARTIAL riporta comunque Gateway; nessuna ricerca/stampa delle credenziali e nessun cambiamento applicativo. CI del nuovo commit avviata, risultato non ancora acquisito. Il DRAFT e ACTIVE restano invariati, nessun retry, le simulazioni e i binding apply/pubblicazione restano gate successivi.


### Checkpoint 2026-10-01 13:30 Europe/Rome — Gateway acquisito, IAM inventory parziale

Operatore: review GET URI candidates0, retry POST URI candidates0; 42 template inline nei backend selezionati. Esistono template HUMAN Ingestion r4a-ingestion-human-quarantine-read/retry/run-read/resume e UDP ths-identity-preflight-read/create, con OIDC bearer-only e limit-count. Questo non prova routing parity, né la correttezza completa di un template da clonare: i body completi sono nel private snapshot /etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/binding-inventory.json. IAM inventory BLOCKED UNCLASSIFIED CalledProcessError, causa/sessione scaduta NON provata; overall PARTIAL READ_ONLY, nessun cambio IAM/route/policy/retry. Scope existence/assignment non acquisiti. Non rieseguire l'inventory con stesso filename esclusivo.

CI completa inventory f961fb1c4c8409418af1c78b430a14333f36855a SUCCESS: run36853251203 modulo (77 test helper, Java/PostgreSQL e container), Shared SDK36853251233, Authorization Semantic36853251113, Gateway36853251194. DRAFT b305bcae-a03f-4f0d-8b81-81508bcddb24 revision0 ancora non pubblicato nell'ultima evidenza, ACTIVE:35 nell'ultima lettura; UDP immagine024c6691…/afa5c4c4…/Flyway34,5SUCCEEDED+3QUARANTINED invariati nell'ultimo guard. Target:36 da riconfermare fresh prima di publish. Handoff e gate precedenti preservati.

Prossimo blocco: rinnovo interattivo kcadm realm master, administrator configurato oufadmin nel runbook, password esclusivamente nel terminale (non argv/env/chat); login distinto dal Device Grant HUMAN ouf-admin. Con lettura client esatto riuscita, helper Keycloak immutati Onboarding6340d5bf120e09b47c32177656e2c377a4c03640, tutti gli argomenti container/realm/client/scope/binding espliciti: catalogue plan; se scope esiste binding plan prima delle mutazioni per negare DEFAULT confliggente; catalogue apply/verify; binding plan/apply/verify OPTIONAL solo udp.materialization.retry su ouf-human-admin. Nessun altro scope/binding modificato; nessuna modifica del DRAFT/pubblicazione/route/job. Software path kcadm resta il percorso canonico dei helper esistenti, limite di portabilità da parametrizzare nel successivo consolidamento R-INSTALL. Bash syntax verificata; la riconciliazione effettiva IAM resta da provare sul server. Se login/plan fallisce, stop; non stampare credenziali o raw kcadm output e non reiterare una create incerta senza readback.


### Checkpoint 2026-10-01 13:44 Europe/Rome — output SSH IAM perso, esito da riconciliare

L'operatore riferisce di aver eseguito il blocco di rinnovo kcadm e scope OPTIONAL, ma di aver perso l'output SSH. Non assumere PASS o FAIL, né ripetere login/apply/create. Prossima azione: due soli verify read-only dei helper Keycloak immutati6340d5bf120e09b47c32177656e2c377a4c03640, scope udp.materialization.retry e binding OPTIONAL a ouf-human-admin nel realm ouf. Si riusa la sessione kcadm già configurata. Catalogue verify prova protocollo/attributi attuali; binding verify prova l'assegnazione attuale e nega un DEFAULT confliggente. Se sessione scaduta o scope/binding mancante, acquisire il codice simbolico prima di ulteriori azioni; non usare apply per diagnostica. La verifica non ricostruisce il log storico perduto. DRAFT b305bcae-a03f-4f0d-8b81-81508bcddb24 revision0 e ACTIVE:35 nell'ultima evidenza, nuove route recovery ancora assenti nell'ultimo inventory, nessuna pubblicazione/retry provati. Handoff e gate precedenti preservati.


### Checkpoint 2026-10-01 13:48 Europe/Rome — IAM scope OPTIONAL verificato

Readback operatore in sola lettura: scope udp.materialization.retry EXISTS=true, DRIFT=NONE, catalogue VERIFY PASS; client ouf-human-admin, OPTIONAL STATE=BOUND, binding VERIFY PASS. R4A_IAM_RECONCILIATION PASS READ_ONLY=true RETRY=false. Protocollo privato /etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/iam-verify.22IAo3. Questa verifica recupera stato attuale; non ricostruisce il log SSH storico perduto. Nuovo token HUMAN con scope esplicito non ancora acquisito. DRAFT b305bcae-a03f-4f0d-8b81-81508bcddb24 revision0, ACTIVE:35 nell'ultima evidenza; pubblicazione/retry non eseguiti/provati. Route review/retry ancora assenti nell'ultimo inventory; prossimo passo preparazione di due route HUMAN UUID esatte, riusando template protetto e preservando OIDC/limiti/route esistenti, con snapshot/intent/readback/rollback. Seguono simulazioni della bozza, conferma/pubblicazione HUMAN, GET reale Spring dei tre job e solo poi eventuale conferma retry. Gate full8/search/causalità storica/industrializzazione e tutti i precedenti invariati.


### R4A — Gateway recovery parameterizzato, preparazione dopo IAM verificato (2026-10-01)

IAM verify dell'operatore: `udp.materialization.retry` esiste, DRIFT=NONE; client `ouf-human-admin` OPTIONAL/BOUND. Log privato `iam-verify.22IAo3`, nessun retry. Consultati PET Authorization v1.5 §36.10 e UDP v1.3 §§109.6–109.7: coarse Gateway, fine-grained owner, reference integrity nel punto d'uso; nessun silent fallback.

Nuovo helper `scripts/r4a_install_materialization_recovery_routes.py`: ogni binding obbligatorio da CLI, due route condivise GET review/POST retry con UUID/action ancorati, OIDC bearer-only e limit-count preservati da template validato, guard HUMAN access e rimozione header x-ouf nel rewrite, token preservato per verifica owner indipendente. Non copia Lua di altre capability. Snapshot Gateway privato precedente deve combaciare con lettura fresca; collisione/drift bloccano prima di PUT. Ricevuta esclusiva root 0600 con intent fsync prima di ogni PUT; rollback elimina soltanto route create che combaciano ancora con il desiderato. Se output perso, `verify` legge senza PUT; stato incerto richiede riconciliazione e mai blind retry. Nessun POST owner, nessuna pubblicazione policy, nessun replay/source activation. Test locali 20 PASS (6 nuovi +14 preesistenti); CI aggiunta a 83 test e checksum aggiornati nello stesso commit. Deploy effettivo e HUMAN authorization rimangono da verificare dall'operatore. Bozza b305bcae-a03f-4f0d-8b81-81508bcddb24 non pubblicata; ultimo ACTIVE osservato :35; invariato obiettivo materializzazione 8/8 e search non provata. Limiti: snapshot+readback non sono transazione APISIX distribuita; evitare writer concorrenti nella finestra.

Runbook Gateway pin codice `2011743b06f685004f74ccef045d1b34b273192b`, procedura in docs/installation/R4A_UDP_RECOVERY_CANDIDATE.md; attesa readback operatore, nessun retry.


R4A CI aggiornamento: 83/83 recovery-cycle test PASS. Primo check checksum ha rilevato newline finale divergente nelle copie locali di workflow/helper; correggere hash ai byte Git pubblicati (codice invariato). La procedura operatore rimane pinnata a 2011743b06f685004f74ccef045d1b34b273192b; nessun deploy/retry effettuato da questo controllo. Attendere CI sul commit checksum prima dell'esecuzione operatore.


R4A Gateway recovery — CI verificata su `9b029beaec1f5419ff3820a1f038597bb4e8dcbf`: module run 36859068962, recovery-cycle 83/83 PASS, Java 51/51 PASS, source checksums PASS, container-smoke/non-root PASS. Pairwise Authorization 36859069018, Shared SDK 36859068821 e Gateway 36859068774 SUCCESS. Codice operativo pinnato 2011743b06f685004f74ccef045d1b34b273192b identico al codice verificato; successiva correzione riguarda soltanto hash dei byte Git e documentazione. Pronto blocco SSH; prossimo gate: apply/readback due route Gateway dall'operatore. Nessun deploy Gateway dichiarato eseguito prima del suo output; DRAFT ancora non pubblicata, HUMAN owner authorization e materializzazione 8/8 da provare.


### R4A — Gateway recovery installato/verificato dall'operatore (2026-10-01 14:15 Europe/Rome)

Output operatore: plan/apply/verify PASS, 2 route GET review/POST retry con UUID/action esatti, tutte le route esistenti preservate. Ricevuta privata `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/gateway-routes-receipt.json`; protocollo privato `gateway-routes.xG4lR0`. Non stampare receipt/snapshot OIDC. IAM precedentemente verificato: scope `udp.materialization.retry` senza drift, OPTIONAL/BOUND sul client `ouf-human-admin`. Nessuna pubblicazione policy chiamata, nessun retry/replay/reactivation. Owner HUMAN authorization ancora NOT_PROVEN. Prossimo gate: leggere bozza b305bcae-a03f-4f0d-8b81-81508bcddb24 rev0 e ACTIVE da sessione HUMAN fresca, preview esatta e simulazioni positive/negative; pubblicazione separata governata. Target invariato: recuperare soltanto i 3 job UDP originali, poi provare 8/8 materializzazione e search. PET Authorization §36.10 e UDP §§109.6–109.7 obbligatori; parametro environment esplicito e doc/deploy automation sempre aggiornati.


### R4A — Review/publicazione HUMAN della bozza esistente, helper governato (2026-10-01)

Nuovo helper parametrizzato `scripts/r4a_review_publish_scoped_human_policy.py` con modi review/publish/verify. Usa soltanto draft-receipt/resources esistenti, nessuna ricreazione del draft, registrazione o modifica di grant. Confronta identità, hash baseline, diff esatta, resourceType/ID/attrs/DataAccessLabel e scadenza; mantiene ogni entry preesistente. Legge ACTIVE e draft/ETag, verifica catalogue owner/descriptor, preview e simulazioni lato owner Authorization: ALLOW per ogni risorsa/label; DENY per SERVICE, AI_AGENT, scope assente, soggetto/ID/type/attrs/label diversi o label assente; contesti tenant esterni respinti HTTP403 dal boundary (non confondere con decisione SDK). Response deve essere HYPOTHETICAL_NOT_IAM_VERIFIED/authoritative=false, hash e revisioni coerenti. Le POST preview/simulate scrivono audit amministrativo, non mutano policy ACTIVE/draft o business UDP: non dichiararle globalmente read-only. Tre risorse lab con quattro attrs e una label ciascuna producono 41 scenari. Nessuna prova HUMAN owner UDP ottenuta dalle simulazioni.

Pubblicazione: login Device Grant HUMAN fresco sul client configurato, account OUF corretto verificato per sub/tenant/issuer/audience/adminscope; conferma locale esatta `PUBBLICO <bundle:version>` dopo review. La bozza lab è b305bcae-a03f-4f0d-8b81-81508bcddb24 rev0/base:35, target:36, grant scadono 2026-10-02T10:00:00Z. Recheck dopo conferma di expiry/draft/ACTIVE; durable intent root 0600 prima di POST publish; response + GET draft PUBLISHED rev1 e ACTIVE esatto (publishedAt stabilito dall'owner). Receipt privata impedisce repost; verify legge soltanto policy/draft con sessione HUMAN fresca, anche dopo expiry per diagnosticare una pubblicazione storica, senza ripubblicare. Per state senza publish intent serve riconciliazione, non forzare receipt né blind retry. Nessuna chiamata UDP retry/intake/replay/source activation. Runbook esegue fresh GET Gateway verify prima del login. Test locali 26 PASS, 6 nuovi; CI recovery passa da83 a89 con checksum esatti sui byte pubblicati. Attendere CI e output operatore prima di dichiarare pubblicato :36. Dopo pubblicazione, next gate sessione HUMAN col nuovo scope + reale GET review dei tre job e controlli Spring/reference, poi eventuale retry HUMAN originale, poi readback8/8/search. Restano tutti i blocker ereditati e R-INSTALL/portabilità/autodeploy non chiusi.

Runbook review/publish/verify pinnato codice `190e3f052e5a0612109da3145534e73ae519dae7`; procedura in docs/installation/R4A_UDP_RECOVERY_CANDIDATE.md. Non ancora eseguito dall'operatore, ACTIVE:36 NOT_PROVEN.


R4A policy review/publish CI finale verificata su `66ac8b1db36e83a8558aa4a8ab3fa9366f1205a8`: module run 36861896858 SUCCESS, recovery-cycle 89/89 PASS, Java 51/51 PASS, checksum/build/non-root container PASS; Authorization pairwise36861896871, Shared SDK36861896859, Gateway36861896946 SUCCESS. Codice pinnato190e3f052e5a0612109da3145534e73ae519dae7; runbook pronto. Stato al passaggio operatore: IAM/Gateway PASS già ricevuti, bozza ancora non pubblicata secondo ultima prova, nessun retry eseguito; richiede login OUF ouf-admin e conferma HUMAN terminale dopo review41scenari. Ricevuta publication-receipt.json root privata, output perso -> verify senza repost. Nessuna prova owner UDP/materializzazione8/8/search anticipata.


### R4A — Conferma terminale fallita prima della pubblicazione, fix e ripresa (2026-10-01 14:32 Europe/Rome)

Operatore: REVIEW PASS 3 risorse/41 scenari, ACTIVE_UNCHANGED=true, SIMULATION_AUTHORITATIVE=false. Receipt privata publication-receipt.json scritta. La proposta :35->:36 è stata mostrata ma `confirm()` ha sollevato UnsupportedOperation prima del durable publish intent e prima del POST. Causa riprodotta: Python open('/dev/tty','r+') tenta buffered random I/O su terminale non seekable. Nessun publish/retry UDP eseguito in questa invocazione; non eliminare/ricreare la receipt né bozza. Owner HUMAN authorization resta NOT_PROVEN.

Fix: prompt su stdout flush e terminale aperto solo lettura 'r'. Test reali pty.fork con /dev/tty non seekable: frase corretta PASS, frase errata DENY. Nuovo modo resume accetta esclusivamente receipt root0600 REVIEWED_NOT_PUBLISHED con mode originario publish e hash draft/resources identici; fresh HUMAN login + preview/simulazioni completo + ACTIVE/draft/ETag/expiry recheck + nuova conferma terminale. Non utilizza vecchie simulazioni come autorizzazione. Publish intent/PASS_PUBLISHED/altre receipt bloccano resume prima del login, richiedono verify senza repost. Lost response originaria e scope/expiry/drift restano fail-closed. Test locali10 helper PASS (4 nuovi); totale CI93 previsto. Consultati PET Authorization§36.10 e UDP§109.6. Nessun binding installativo nuovo hardcoded e nessuna modifica Gateway/IAM/UDPbusiness/migrazione. Next gate rimane pubblicazione HUMAN :36 verificata, poi GET reale UDP nuovo scope, reference readiness e recovery originale3job; 8/8/search ancora NOT_PROVEN e blocker ereditati invariati.

Ripresa terminale pinnata codice `dcd6703e7bb5d8a1f7e29b6a9c15f4c8be0e58d4`, heading runbook R4A UDP recovery policy — ripresa dopo errore terminale non seekable. Nessuna pubblicazione dichiarata avvenuta; attendere operatore.


R4A terminal fix CI finale su `303758a89ebe4d00c4ee3056774b421bfb38fd9d`: module run36863065590 tutti job SUCCESS (Java, recovery93/93, checksum, container-smoke); SharedSDK36863065702, Authorization36863065777 e Gateway36863065591 SUCCESS. Fix operativo pinnato dcd6703e7bb5d8a1f7e29b6a9c15f4c8be0e58d4, test includono tty reale non seekable e resume dopo UnsupportedOperation con una sola pubblicazione. Pronto ripartire in SSH interattiva usando receipt originale REVIEWED_NOT_PUBLISHED. Nessun POST policy da questo agente; ultimo output operatore è reviewPASS/pubbloccata prima di intent, retryUDP=false. Dopo ripresa verificare ACTIVE:36 prima del prossimo gate ownerHUMAN/3job/8materializzazione/search.


### R4A — Pubblicazione scoped HUMAN confermata (2026-10-01 15:28 Europe/Rome)

Operatore ha ripetuto review PASS (3 risorse,41scenari, ACTIVE invariata durante review) e inserito conferma terminale esatta. PUBLISH PASS ACTIVE=ouf-lab-authorization:36, draft PUBLISHED revision1, exact scoped diff/readback verificati. Receipt privata publication-receipt.json; non stampare. La precedente conferma non seekable è superata. Grant nominali HUMAN per soltanto tre job originali, attrs/type/DataAccessLabel esatti, expiry2026-10-02T10:00Z, altre entry preservate. Nessun retry UDP ancora eseguito; simulation authoritative=false; HUMAN owner authorization ancora NOT_PROVEN. Next gate: login HUMAN fresco richiedendo udp.materialization.retry, GET reali Gateway->UDP review dei tre job; verificare authz owner, QUARANTINED/DURABLE/v2 e reference contractReady nel profilo Spring effettivo. Solo dopo PASS preparare eventuale retry HUMAN per originale job con expectedVersion/snapshotHash/operationId, poi readback8/8/search. Non replay/reactivation/resend, nessun repair DB. Restano tutti i blocker ereditati e industrializzazione R-INSTALL/multi-host/network/domain/tenant.


### R4A — Reale HUMAN GET review UDP, prossimo gate dopo ACTIVE:36 (2026-10-01)

Helper `scripts/r4a_read_human_materialization_review.py` parametrizzato: root receipt nuova/esclusiva privata, verifica publication PASS_PUBLISHED/resourcesHash/descriptor COMMAND HUMAN, set esatto3job/handoff ed expectedstate. Nuovo Device Grant richiede solo scope OPTIONAL udp.materialization.retry; verifica sub/tenant/issuer/client/audience/scope. UDP owner riceve solo GET (nessun business POST): anonimo deve401/403, job esistente fuori scope deve403, quindi GET3job originali200 con binding source/run/handoff esatto, QUARANTINED/DURABLE/v2 e failure tecnica attesa. Legge retryEligible/contractReady/contractCheck/snapshotHash/verifiedBaselineHash nella vera applicazione Spring; valori dei ref/hash solo receipt privata. PASS_AUTHORIZATION_REFERENCE_BLOCKED distingue auth riuscita da reference gate non-ready e vieta retry. Anche PASS non esegue materializzazione. Le normali decisioni di autorizzazione possono produrre audit; OWNER_GET_ONLY non implica assenza globale di audit. Sessione login OIDC utilizza POST token endpoints, nessun owner UDP POST. ReviewGET corrente non prova causalità dei3failurestorici né materializzazione8/8/search.

Se99testCI PASS, consegnare runbook per login ouf-admin e GET reale. Scope fine-grained/HUMAN prova dalla risposta reale owner, non simulazione. Expected policy:36 è confronto con ricevuta di pubblicazione verificata, non ulteriore prova della versione globale ACTIVE corrente o contenuto in-memory del resolver. Test6 nuovi coprono soleGET/deny, receipt drift prelogin, scope anon/outside erroneamenteallow, source/handoff/version mismatch, payloadextra respinto, contract blocked. Corretto soltanto test pty precedente: hangup può anticipare visibilità waitpid, ora attende exit entro timeout senza falsa failure; nessuna modifica runtime di quella conferma. PET UDP§109.7 reference readiness e Authorization§36.10 owner enforcement consultati; binding installativi solo CLI/runbook, altri gate ereditati invariati.

Runbook GET HUMAN pinnato codice `d06a5ca48d2cfc058f04ce73e4ba0703fdce5566` in docs/installation/R4A_UDP_RECOVERY_CANDIDATE.md; owner proof non ancora ricevuta, retryfalse.


R4A HUMAN GET review CI finale su `0bd124c2fdc9554d784273fb3aad14fe4dedbb8c`: module run36870489064 Java/checksum/container SUCCESS, recovery99/99 PASS; Authorization36870489030, SharedSDK36870489031 e Gateway36870489124 SUCCESS. Codice operativo pinnato d06a5ca48d2cfc058f04ce73e4ba0703fdce5566. Pronto gate operatore: sessione HUMAN scopeudp.materialization.retry e soleGET reali. Receipt interna in caso reference nonready è AUTHORIZATION_PASS_REFERENCE_GATE_BLOCKED, output R4A_UDP_HUMAN_REVIEW=BLOCKED/HUMAN_OWNER_AUTHORIZATION_PROVEN=true. Non confondere con PASS della materializzazione: nessun retry finora,8/8/search ancora da provare. Pubblicazione:36 giàPASS ricevuta da operatore, GETowner proof non ancora ricevuta.


### R4A — Output GET HUMAN perso / shell chiusa dopo THS (2026-10-01 16:35 Europe/Rome)

Operatore segnala shell chiusa dopo conferma THS, output finale non disponibile. Non assumere review PASS né owner authz/reference ready; ultima prova certa resta pubblicazione ACTIVE:36 PASS, retryUDP mai chiamato dal blocco GET-only consegnato. Recuperare esclusivamente receipt human-review-*.json rootprivate, soli metadata/stati, senza nuovo login/GET/POST/retry. Receipt può essere RESERVED/LOGIN_PENDING/partial oppure PASS_READY o AUTHORIZATION_PASS_REFERENCE_GATE_BLOCKED; stati incompleti non provano esito positivo e il vecchio helper non persiste l'exception finale, quindi la causa remota può restare ignota dopo lettura. Le receipt sono evidenza salvata, non query live né snapshot fresco per futuro retry.

Difetto certo individuato nel bootstrap incollato in SSH: `set -euo pipefail` impostava opzioni della shell interattiva chiamante. Qualsiasi exit nonzero (incluso gate reference bloccato previsto, exit2) può chiudere tale shell/sessione. Non attribuire automaticamente la chiusura a nuovo bug applicativo né escluderlo senza evidence. Da ora bootstrap in processo bash separato, status gestito con OR nel chiamante; non alterare opzioni interattive. I runbook interni possono usare set-e dentro il processo isolato. Recovery metadata testato localmente con fixture LOGIN_PENDING/PASS_READY/REFERENCE_BLOCKED e private-mode unsafe: nessun ref/hash/payload/token stampato, nessuna falsa prova completa da partial. Nessun deploy/cambioIAM/Gateway/policy/UDPbusiness e nessun nuovo retry. Handoff/manuale/roadmap/runbook aggiornati; nextgate invariato fino a recupero output reale.

Recupero output sola lettura: heading R4A UDP recovery — recupero output perso dalle ricevute HUMAN, nel runbook candidato. Shell bootstrap isolata obbligatoria per evitare effetto set-e nel chiamante.


### R4A — Receipt reale recuperata: negativi PASS, zero review validate (2026-10-01 16:46 Europe/Rome)

Operatore: una receipt human-review-20261001T143329-3493421.json, status LOGIN_PENDING_NO_BUSINESS_POST, anonymousHttp401, outsideScopeHttp403, reviews0. Questo prova login concluso e due negativi osservati/salvati, non successo delle tre review autorizzate. Non reinterpretare il vecchio status come login ancora pendente; il marker non veniva aggiornato dopo il login. Errore/stato HTTP della successiva richiesta non registrati dal vecchio helper, causa corrente ignota: possibileHTTPdeny/trasporto/parser, non dichiarare guastoIAM/mapper. Nessun retryUDP. Ultima policy provata:36, vecchie3QUARANTINED non riverificatelive.

Fix osservabilità helper: phase persistita prima di login/anon/outside/ogniGET e validation, negativi salvati progressivamente; ownerHTTP e responseShape solo tipologie/campi, nessun valore inatteso/payload, salvati prima di check. Main persiste BLOCKED/safeFailureCode/type/phase solo su receipt esclusivamente creata da quella invocazione; errori estranei ->UNCLASSIFIED, mai exception-message arbitrario, mai overwrite di receipt precedente. SystemExit2 referencegate atteso preserva AUTHORIZATION_PASS_REFERENCE_GATE_BLOCKED. Tre test nuovi provano denial/transport/schema salvati, negativi preservati e receiptnonowned intatta; 9 testhelperPASS, CI102previsto. Runbook nuovo: nuova receipt GET-only, protocollo root0600 che filtra solo righe UDP_HUMAN/R4A_UDP (nessun devicecode/token), loginouf-admin, shell bootstrap in bash separato con status gestito; nessun POSTUDP/publish/replay. Conservare receipt precedente. PET UDP109.7 consultato; ownerpositive/referenceSpring/8materializzazioni/search ancoraNOTPROVEN.

Nuovo runbook GET/error/protocol capture pinnato codice `d6c32cbf062618f0b255c51f8a7a8d6fb521e839`; bootstrap isolato nel chiamante. Esito ownerpositivo ancoraatteso.


R4A safe GET error capture CI finale su f89e9983b39759d8a45fc470dc2b14deca971904: module36880091805 Java/checksum/container SUCCESS, recovery102/102 PASS; Authorization36880092062, SDK36880092071 e Gateway36880091803 SUCCESS. Codice operativo d6c32cbf062618f0b255c51f8a7a8d6fb521e839. Protocol-filter testPASS: codice Device Grant visibile al terminale ma escluso dal fileprivato. Nuovo blocco pronto, bootstrap externalbash con ORhandler protegge shell; nessun retrybusiness. Attesa nuovaGET per classificare errore successivo ai due negativi, ownerpositivo/refgate non ancora provati; conservata receipt143329.


### R4A — Attesa dopo LOG causata dal filtro interattivo, correzione (2026-10-01 17:05 Europe/Rome)

Operatore segnala attesa prolungata subito dopo HUMAN_REVIEW_PROTOCOL_LOG=...TwWflM, prima del codice THS. Raccomandato Ctrl+C, nessun inserimento credenziali alla cieca. Riprodotto localmente con mawk1.3.4: producer stampa DeviceCode flush e attende input, filtro awk precedente non consegna la linea prima di EOF (fflush agiva solo sull'output). Deadlock di presentazione: login attende conferma che non può essere effettuata perché il codice è trattenuto. Difetto del runbook/logger, il precedente test di filtraggio controllava solo processo terminato, non interattività. Non usare quel filtro e non attribuire questa attesa a nuova prova di failureowner.

Sostituito awk con python3-u logger stdin line-by-line, stdout write+flush immediato; scrive sul protocollo root0600 solo prefixUDP_HUMAN/R4A_UDP, nessun devicecode/token. Producer helper avviato anche -u. Test interattivo PASS: codice visibile entro2sec prima della conferma, producer ancora in attesa, poi esito salvato e codice escluso dal protocollo; filtrovecchio WITHHELD=true riprodotto. bash-nPASS. Solo documentazione/runbook modificati, Pythonhelperresta codice d6c32cbf062618f0b255c51f8a7a8d6fb521e839 giàCI102PASS; nessun cambio owner/Docker/IAM/Gateway/policy o retry. Nuovo loginGET-only dopo interruzione, nuova receipt/protocollo; conservare TwWflM e receiptprecedenti, sono evidencepotenzialmenteparziali. Sempre bootstrap externalbash con ORhandler, mai set-einterattivo. Ultime prove owner: negativi401/403 salvati, reviewpositive0 nella receiptprima; nuovaownerpositive/refgate/8materializzazioni/search ancoraNOTPROVEN. Aggiornati handoff/manuale/roadmap/runbook.

Runbook corretto: heading R4A UDP recovery — GET HUMAN con protocollo immediato senza awk. Non riusare filtroawkprecedente; helperimmutato102CI, testsinterattivopresentationPASS.


### R4A — 2026-10-01: HTTP 403 HUMAN e difetto di ammissione scoped identificato

Ultimo output operatore: `R4A_UDP_HUMAN_REVIEW=BLOCKED CODE=HTTP_403 PHASE=OWNER_REVIEW_GET_1`, errore persistito; protocollo privato `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/human-review-protocol.79bSK5`. Processo review exit 1, capture exit 0, shell mantenuta aperta. Solo GET, nessun retry/replay. Policy attiva rimane `ouf-lab-authorization:36`, tre grant HUMAN nominali su job/label esatti, expiry 2026-10-02T10:00:00Z. Live rimane revisione afa5c4c4cf03bff4e39b02e27f898256c3776cbc / immagine sha256:024c6691888855ef4d5574cadacf060e0dfbf7ff891dbc9a747628f5b5c8a519 / Flyway 34. Ultimo business readback: cinque materializzati, tre QUARANTINED; otto consegne ACKED. Nessun nuovo business readback dopo questo GET negato.

Consultati PET Authorization v1.5 §36.10 e UDP v1.3 §§109.6–109.7: Gateway coarse, enforcement owner sul contesto autorevole, reference gate fail-closed e originali durable conservati. Difetto sorgente certo: MaterializationRecoveryApi ricava le capability da ServletAuthorization.resolve sul resourceContext generico capability; i grant esatti materialization-job non autorizzano quel contesto. Il servizio poi actor.require nega prima di poter chiamare owner.require sul job. Test precedenti di dominio non attraversavano il servlet/SDK endpoint.

Correzione candidate commit UDP `1aaa1f6b6a27281ea2d97106ec2033748bab1aee` su codex/r4a-materialization-recovery: solo API recovery usa OwnerAuthorization.candidates per ammissione descriptor/actor/scope fresca, mantenendo identità autenticata e snapshot SDK pinned; servizio continua obbligatoriamente owner.require prima della risoluzione contratti/serializzazione o transizione. Nessuna modifica SDK globale, IAM, grant, route, DB/migrazioni. Nuovi test HTTP MockMvc con SDK LocalAuthorization reale, grant nominale job/source/run/type/RAW label, PostgreSQL: GET e POST ammessi senza grant generico; altri job/soggetti/label/sorgenti, actor SERVICE/AI_AGENT, scope assente, anonimo/spoof negati senza catalog/eventi. Filtri JWT disabilitati in questi test per esercitare il server SPI autenticato; firma token/Gateway hanno verifiche separate. CI in corso, fix non ancora rilasciata. Causalità del 403 live compatibile con difetto, non ancora dimostrata end-to-end; possibili ulteriori problemi Gateway/cache/subject non esclusi.

Prossimo gate: completare CI candidate, build parametrizzata/pinned con migrazioni identiche, stage con live invariato, backup e release verificata senza retry; poi nuova GET HUMAN per prova owner/runtime e readiness storica. Non ripubblicare policy, non aggiungere grant generici, non ripetere intake/replay. Restano aperti materializzazione 8/8, verifica search/storage indipendente e industrializzazione R-INSTALL multi-host/network/domain/Ente.


### R4A — fix ammissione scoped verificata, pronta al rilascio (2026-10-01)

Codice candidate definitivo `83249a897eb4add4289b5181b3299f48ea4c0f99` (correzione API nel parent 1aaa1f6b, seconda commit corregge solo fixture SERVICE con servicePrincipalId obbligatorio). Primo run ha rilevato quella fixture invalida, non un fallo nel caso HTTP positivo; conservare traccia e non dichiarare verde quel run. Run definitivo recovery push36884410381 e PR36884416179 SUCCESS: 18/18 test, zero failures/errors/skipped (recovery13, referencegate3, evidence2); dipendenza SDK10/10 PASS. Module push36884410102/PR36884416158 SUCCESS in tutti e quattro job Java21/PostgreSQL17/image, DR, performance, supply-chain/deployment (vulnerability gate e Helm inclusi). SDK pairwise36884410299/36884416285 e CRS/grid36884410315/36884416242 SUCCESS. PR38 aggiornata sul comportamento finale; niente merge a main.

Il test HTTP autorizzato dimostra GET200 e POST200/v3 sul job originale senza grant generico; denied GET/POST non raggiungono catalogo né appendono eventi; input originale preservato. Sono verifiche CI con fixture, non prova della corrente identità/route/cache/policy live. Fix non ancora deployata, HUMAN owner positivo e mapper storico runtime ancora da provare. Ultimo output operatore resta HTTP403 OWNER_REVIEW_GET_1/no retry e live024c/afa5/Flyway34. Nuovo runbook usa helper già testati al pin3c0e5ef7, feature-enabled upgrade esplicito, preflight check-only, backup prima dello switch, readback originali e rollback fermo. Binding host/DB/rete/source/run/image/percorsi soltanto nel runbook, tutti helper parametrizzati; nessuna nuova migrazione/config hardcoded applicativa. Base image tag non digest-pinned: riproducibilità bit-for-bit non provata, gate industrializzazione resta aperto.

Prossima azione operatore: blocco unico build/probe/preflight/stage/backup/release nella sezione “fix ammissione scoped e release controllata” del runbook R4A_UDP_RECOVERY_CANDIDATE. Breve indisponibilità UDP durante backup/switch; nessun retry/intake/replay/publish policy. Build stampa START e salva output esteso nel build.log privato, timeout1800sec; non confondere silenzio del build con attesa THS. Dopo PASS release, nuova login/GET HUMAN attraverso Gateway e owner; se401/403 persiste, diagnosticare layer e subject/cache senza allargare grant. Non rieseguire release con stato incerto: riconciliare receipt privato. Grant scadono 2026-10-02T10:00Z. Materializzazione8/8 e search non provate; tutti gate ereditati e R-INSTALL invariati.


### R4A — release fix ammissione scoped confermata dall’operatore (2026-10-01 17:37 Europe/Rome)

Output operatore: build revisione UDP `83249a897eb4add4289b5181b3299f48ea4c0f99` PASS, candidate/live finale `sha256:5e048a859716d6674355e72238f03f899abd705a943ceadbdc5c8863d28f4e9f`, tag `ouf-udp-recovery-candidate:r4a-83249a897eb4-3fdecb4873a0`. Receipt build privata `/opt/ouf/udp-recovery-candidates/udp-recovery-image-ijxpujl8/receipt.json`. Migrazioni identiche e live precedente024c invariato durante build. Probe compilato/shipped Java resolve PASS GET_ONLY/candidate, senza Spring: non prova mapper runtime o causalità storica.

Preflight PASS READ_ONLY/live recovery-enabled/candidate assente; stage PASS candidate fermo/no restart, mounts uguali, ambiente conservato salvo flag recovery, live invariato. Receipt stage privata `/opt/ouf/udp-recovery-candidates/udp-recovery-stage-5gvo9w_0/receipt.json`. Release PASS dopo stop live e backup PASS con restore-list; receipt privata `/opt/ouf/udp-recovery-candidates/udp-recovery-stage-5gvo9w_0/release-receipt.json`. Live finale5e048a/Flyway34, ORIGINAL_JOBS_UNCHANGED, Gateway backend health, anon/spoof negati. Rollback `ouf-udp-rollback-d2450009a153` fermo/restart-disabled; conservare backup e rollback precedenti. Non ripetere build/release né rimuovere ricevute. Queste sono evidenze operatore, non ispezione SSH diretta dell’agente.

HUMAN_AUTHORIZATION_NOT_PROVEN=true, RETRY=false. Ultimo business stato noto resta 8handoff ACKED, 5PROCESSED/SUCCEEDED e 3DURABLE/QUARANTINED; release dichiara originali invariati, non materializzazione8/8 o search. La fix sorgente è ora rilasciata, ma causalità del precedenteHTTP403 e prova owner positiva richiedono GET reale. PET Authorization§36.10 e UDP§109.7 consultati: health/negativi non sostituiscono AUTHZ-READY e reference gate al punto d’uso. Policy ultima pubblicata:36, grant3 nominali/scoped, expiry2026-10-02T10:00Z; nessuna nuova pubblicazione, route o IAM change richiesta.

Prossimo intervento operatore: nuova sessione HUMAN ouf-admin/clientouf-human-admin con scope OPTIONAL udp.materialization.retry; GET anonimo, fuori scope e tre job originali tramite Gateway->UDP, utilizzando helper giàCI102PASS d6c32cbf e logger Python unbuffered verificato interattivamente. Nuove receipt/protocollo root-private, phase/HTTP/error persistiti. Se GET3PASS e contractReady/retryEligible confermati, preparare soltanto allora retry originale con expectedVersion/snapshotHash/operationId e conferma HUMAN. Se403 persiste diagnosticare Gateway/owner/subject/policycache, senza grant generici o nuovi tentativi di business. Block reference gate con ownerpositive resta esito incompleto e vieta retry. Restano tutti i gate ereditati, storage/search indipendenti e industrializzazione R-INSTALL.


### R4A — prova owner HUMAN e reference gate Spring completa (2026-10-01 17:55 Europe/Rome)

Operatore: tre review HTTP200 PASS, JOB_BINDING_MATCH=true, QUARANTINED/DURABLE/version2, retryEligible=true, contractReady=true, contractCheck=READY per tutti e tre job originali. R4A_UDP_HUMAN_REVIEW=PASS, HUMAN_OWNER_AUTHORIZATION_PROVEN=true, ANONYMOUS_DENIED=true, OUTSIDE_JOB_DENIED=true, SPRING_REVIEW_REFERENCE_GATE=PASS. Receipt privata `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/human-review-20261001T155349-3513740.json`; protocollo privato `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/human-review-protocol.MIvo9G`; process/capture exit0. Solo owner GET: RETRY=false, REPLAY=false, INTAKE_POST=false, materializzazione non triggerata. Causalità storica resta NOT_PROVEN; la sequenza prima403/poi200 dopofix non è ricostruzione dell'errore storico di reference integrity. Live83249a/5e048a/Flyway34, originali preservati.

Gate owner positivo e risoluzione attuale nel mapper Spring superati per i tre job sotto questa sessione; non dichiarare materializzazione8/8/search/storage indipendente. Policy36 nominale HUMAN, soli3job/type/source/run/RAWlabel esatti, expiry2026-10-02T10:00Z. Non ripubblicare policy o modificare IAM/routes. PET Authorization36.10/UDP109.6–109.7 consultati: retry originale governato, version/snapshot e reference gate al punto d'uso, nessun replay/repair DB/silent fallback.

Preparato helper parametrizzato scripts/r4a_retry_human_materialization.py: richiede receipt review precedente PASS_READY e hash/set esatti, risorse/private publication, binding originali e motivo bounded; nuova sessione HUMAN e nuove GET owner per i tre job. Il helper GET riutilizzabile restituisce token soltanto in-process, mai lo salva. Dopo tutte le review READY persiste tre operationId e richieste esatte, mostra job/handoff/source/run e transizioneQUARANTINEDv2->READYv3, richiede frase sul /dev/tty read-only. Conferma non pubblica policy. Prima di ogni POST verifica TTL>60sec e fsync dell'intento/operationId/body nella receipt esclusiva0600. Solo un POST per originale, nessun loop/repost. HTTP200 verificato con operation/job/handoff/version3/READY/repeatedfalse, append progressivo; successo è PASS_AUTHORIZED_REQUEUE, non prova materializzazione. Qualsiasi failure ferma il batch; timeout/response invalida conserva POST_INTENT_OUTCOME_UNKNOWN e precedenti successi, vieta repost fino a riconciliazione. Nessun messaggio eccezione arbitrario, payload/token/hash sul terminale.

Otto test nuovi coprono tre review fresche prima della conferma/POST, drift input/prior/source, reference/version gate, conferma/TTL, intent durevole, partial timeout/409/schema error e nessun overwrite/repost, token non persistito, terminale reale corretto/negato. 17 test retry+review locali PASS, 47 policy/Gateway/helper locali PASS. CI helper/package da completare prima del blocco operativo. Nessun retry remoto ancora effettuato; prossimo intervento umano sarà login THS e conferma batch mostrato, poi readback8handoff/job originali ed effetti canonici/search. Tutti i gate ereditati/industrializzazione R-INSTALL restano aperti.


### R4A — retry HUMAN originale verificato e pronto alla conferma operatore (2026-10-01)

Helper operativo pin `fe8b957907106925acbca95fe8e63595c88f806c`: recovery scripts CI PR36889604556 job110461624123 SUCCESS, 110/110 test PASS. PR module completo Java21/PostgreSQL17/checksum e production container SUCCESS; Authorization pairwise36889604582, Shared SDK36889604497 e Gateway live pairwise36889604635 SUCCESS. Push Authorization36889598494 e SDK36889598423 SUCCESS; pushmodule36889598409 SUCCESS, inclusi checksum/Java,110testhelper e production container. Prompt conferma emesso con newline/flush per il logger a righe: test locale reale producer->logger->PTY PASS, prompt visibile prima di input, codice login escluso dal protocollo. bash-n e published-code readback PASS. Nessun deploy aggiuntivo richiesto: UDP live resta83249a/5e048a/Flyway34. Non confondere CI helper con autorizzazione remota POST; quest'ultima non ancora esercitata.

Blocco operativo nel runbook “retry HUMAN dei tre job originali dopo review PASS”: nuova receipt human-retry-* root0600 e fresh-review separata; sessione HUMAN dedicata, tre nuove GET READY e negativi, piano con tutti job/handoff/run/source, frase esatta da digitare su tty, poi tre POST originali uno per volta. Scope/grant già governati:36, nessuna ripubblicazione, replay/intake/reactivation. Snapshot fresh e version2 da owner, operationId stabili persistiti prima dell'intento; version3/READY è ammissione, non materializzazione. Logger filtra sole righe simboliche, non devicecode/token/hash/payload. Con exitnonzero o connessione persa dopo intent, fermarsi e riconciliare receipt: non rieseguire il batch, non inventare nuova operation né sommare automaticamente una risposta persa ai successi. Conserva pass già registrati e unknown separati, mai claimfalseRETRY=false dopo POST.

Ultima prova remota certa: receipt human-review-20261001T155349-3513740.json PASS_READY,3reviewHTTP200/QUARANTINED/DURABLE/v2/eligible/READY e anon/outside denied. Nessun retry al momento di questo checkpoint. Dopo receipt3POST200 PASS_AUTHORIZED_REQUEUE, nextgate è readback sugli otto originali Ingestion/UDP, stati ed eventi di retry/resolution, effetti canonici e search; non fare nuove ingestion/replay. Restano storage/hash indipendente, causalità storica NOT_PROVEN e tutti gate R-INSTALL/industrializzazione ereditati. Grant expiry2026-10-02T10:00Z, owner enforcement deve continuare fail-closed.


### R4A — retry HUMAN dei tre job originali accettato (2026-10-01 18:14 Europe/Rome)

Operatore ha effettuato nuova sessione HUMAN, tre GET owner200 con job binding esatto, QUARANTINED/DURABLE/v2, retryEligible=true e contractReady=true/READY; anonimo e job fuori scope negati. Fresh review privata `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/human-retry-20261001T161313-3517748-fresh-review.json`. Piano source managed-cinema-8ec8ae90/run86809c17-3354-45ca-a7e6-57e903944b24, tre originali e transizionev2->v3 mostrati. Operatore ha digitato frase esatta CONFERMO RETRY ORIGINALE con runID, quindi tutti e tre POST/retry HTTP200 PASS/ORIGINAL_JOB_MATCH/acceptedVersion3/READY/repeatedfalse.

Ordine confermato: job7793566d-b9d4-4402-8cda-c09b8f135c04/handoff8869a6d6-3d82-4514-a63a-d23f9b26d48f; jobe5b6ca24-6143-4ae5-8907-5dce398abfa3/handoffe58faf8c-c35a-4106-b4b6-67e58dec9774; jobe7572836-f8af-4c58-b5fc-12d7aff5db1d/handoffaed8ef93-6d00-4cf0-868d-d2d82d79b524. R4A_UDP_HUMAN_RETRY=PASS/ACCEPTED_COUNT3/HUMAN_OWNER_AUTHORIZATION_PROVEN/ORIGINAL_JOBS_REQUEUED. REPLAY=false, INTAKE_POST=false, MATERIALIZATION_NOT_YET_VERIFIED=true. Protocollo privato `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/human-retry-protocol.edA735`; process e capture exit0. Receipt retry principale derivabile senza ambiguità dal nome fresh-review del helper: `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/human-retry-20261001T161313-3517748.json`; contiene operationId/body/snapshot e risposta per ciascun POST, non stampare. Il prossimo reader ne verifica presenza/privacy/schema/set prima dei readback live.

Non ripetere i retry: ammissione originale completata, il worker procede asincrono. Non riattivare sorgente/schedule trigger_once, non replay/reintake/repair DB. Version3/READY è accettazione, non SUCCEEDED o effetto canonico. Ultimo stato Ingestion noto resta SUCCEEDED/control2/8ACKED, lineages8, attempts10 con due failstorici risolti; cinque materializzazioni UDP precedenti più tre ora in coda, totale effettivo corrente da leggere. Live83249a/5e048a/Flyway34, policy36 nominale3scope, nessun cambio deploy/IAM/Gateway/policy. Causalità storica reference failures NOT_PROVEN.

PET UDP109.6–109.7 e Authorization36.10 consultati: re-run da evidence/version/snapshot e durable originals, owner fine-grained, reference gate senza fallback. Preparato blocco READ_ONLY: valida ricevuta retry originale0600/root e parent0700, set3job/handoff, distinct operationId, requestversion2 e receiptversion3/READY/repeatedfalse, stampa solo saved evidence. Poi riusa fixture cinema già versionata: activation receipt e pubblicazione ACTIVE/frozenchecksum exact; Ingestion e UDP scope publication/run, handoffIDset, intakes/jobs/decisions/issues/observations/revisions/bindings/activeobjects; più diagnostica UDP parametrizzata per source/run e tutti jobID/state/version/counters/flags ed eventi simbolici (incl MATERIALIZATION_RETRY_AUTHORIZED, REFERENCE_INTEGRITY_PASSED e RESOLUTION_COMPLETED se presenti). Nessun safe_detail/token/payload/ref/hash stampato. Cinque casi locali readerPASS (buono/unknown/wrongjob/version/privacy), bash-nPASS; helper runtime riusati senza modifiche. Protocollo readback rootprivate persistente, exit dei due reader separati; COMPLETE/exit0 non converte NOT_PROVEN in PASS.

Nota deploy: cinema_execution_readback è una fixture storica legata al deployment cinema corrente, non uno strumento di deploy generico; non introdotte nuove costanti lab nel codice applicativo/helper condiviso. La diagnostica UDP è parametrizzata CLI. Questa fase non chiude portabilità multi-host/domain/network/tenant né automatismi R-INSTALL. Se8materializationPASS, seguiranno search e byte/hash Lake indipendenti; letture cross-DB non atomiche, singolo snapshot non è consenso distribuito. Se pending/failure, analizzare originale senza nuovo retry cieco. Tutti altri gate ereditati restano aperti.


### R4A — readback completo: 7/8 materializzati, un originale nuovamente quarantinato (2026-10-01 18:28 Europe/Rome)

Operatore ha prima segnalato NOT_PROVEN, poi allegato output completo Testo incollato.txt, letto nel workspace. Il recupero del log salvato preparato nel frattempo è ora superfluo e non va richiesto. Protocollo reale privato `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/readback-after-retry.FUnWAL`. Receipt retry salvata PASS/3accepted/exactoriginaljobset; sourceACTIVE/frozenhash/publicationmatch. Ingestion run86809c17 SUCCEEDED/control2,10attempts/8lineages/0quarantines,8ACKED e UDP handoffIDset match; delivery8 PASS. Trigger_once consumed/DISABLED. Due failstorici404/403 restanoRESOLVEDv2. Output di entrambi reader exit0, non equivalenti a materializationPASS.

UDP:7PROCESSED/SUCCEEDED/NEW_OBJECT,7observations/revisions/bindings/activeobjects;1DURABLE/QUARANTINED,0open resolution issues. Materialization8 NOT_PROVEN e searchnonverificata. Dei tre retry, job7793566d/handoff8869a6d6 e jobe5b6ca24/handoffe58faf8c sonoSUCCEEDEDv5, attempts2/integrityAttempts1/baselinepresente, eventi originali+1MATERIALIZATION_RETRY_AUTHORIZED+REFERENCE_INTEGRITY_PASSED+RESOLUTION_COMPLETED. Ultimo job `e7572836-f8af-4c58-b5fc-12d7aff5db1d` / handoff `aed8ef93-6d00-4cf0-868d-d2d82d79b524` è tornatoQUARANTINEDv5/attempts2/integrityAttempts2,baselineassente,missingRefCount0,nextcheckassente,safeFailureCodeUDP_REFERENCE_INTEGRITY_CONTRACT_INVALID. Eventi:1retryAUTHORIZED e2REFERENCE_INTEGRITY_QUARANTINED (storico+nuovo), nessunREFERENCE_PASSED/RESOLUTION_COMPLETED per questo handoff. Questo è fallimento tecnico nel worker, non semplice job pendente; non ripetere alcun retry dei tre.

Tutte3review fresche avevanoREADY e POSTacceptedv3; il terzo tentativo asincrono contraddice readiness osservata prima in una diversa chiamata/istante. Causa specifica non dimostrata: non attribuire a token/Gateway/policy/mapper/payload senza nuova evidence. ACTIVEpolicy36 HTTP200 nel bundle generale; logruntimeUDP/Apisixsenza marker simbolici, accesslogTimeoutExpired. ING_ACTIVATION_DISCOVERY_UNAVAILABLE12da finestraprepubblicazione è diagnostica storica e non spiega da sola il nuovoUDPfailure. UDP_FAILURE_CODES=[] è proiezione intake, non assenza di safeFailureCode nel job. Zero resolutionissues non elimina questa quarantena tecnica. Owner authorization HUMAN è giàprovata dai3GET/POST; flagOWNER_AUTHORIZATION_NOT_PROVEN del bundlegenerale non revoca quella prova scoped.

Lettura sorgenti live83249a: MaterializationReferenceGate quarantina IllegalArgumentException con UDP_REFERENCE_INTEGRITY_CONTRACT_INVALID, e passa ReferenceFailureEvidence.detail alla append-only event. Nuova strumentazione deve contenere diagnosticCode allowlisted/category e max4 Javaapplicationframes, senza exceptionmessage/payload. ResolutionRepository inserisce questi campi direttamente nel safe_detail della nuovaREFERENCE_INTEGRITY_QUARANTINED; V1handoff_event.created_at è verificato da schema. Prossimo gate READ_ONLY mirato al solo originale rimasto: proietta esclusivamente jobstate/version/counters/safecode e recenti eventi quarantena con diagnosticCode/category/frames, ordinati percreated_at. Nessuna lettura/stampa integrale safe_detail o ref/hash/token/payload. Storico privo di campi ->NOT_RECORDED, simboli sconosciuti redatti; framesvalidati. Binding container/database/user/job/handoff/source/run solo CLI/runbook. SQL READ_ONLY/timeout15s/lock2s, processo25s, protocollo root0600. Proiezione sanitizer locale PASS (simboli/frame/valori arbitrari redatti/legacyabsent), bash-nPASS. È documentazione diagnostica, nessun cambio applicativo/deploy/policy/IAM/route/DB.

PET UDP109.6–109.7/Authorization36.10 consultati: conservare originali e audit, fermarsi sul nuovo failure, verificare referencegate senza fallback. Dopo code/frames usare prova per diagnosi/fix reviewable; niente retrycieco/replay/reactivation. Ultimo live83249a/5e048a/Flyway34, due originali recuperati con effetti canonici, uno ancora bloccato. Tutti gate ereditati, storage/search indipendente, causalità storica e industrializzazione R-INSTALL restano aperti.


### R4A — anche nuova quarantena senza diagnostica: verificare codice runtime (2026-10-01 18:35 Europe/Rome)

Operatore ha eseguito sola lettura mirata, protocollo privato `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/remaining-reference-failure.6rMnAL`. Job e7572836/handoff aed8ef93 restaQUARANTINEDv5/attempts2/integrityAttempts2/safeFailureCodeUDP_REFERENCE_INTEGRITY_CONTRACT_INVALID. Entrambi eventi hanno diagnosticCode/categoryNOT_RECORDED,frames[]: nuovo `2026-10-01T16:14:25.674269+00:00` (18:14locale dopo retry) e storico `2026-10-01T06:52:29.339869+00:00`. ReaderCOMPLETE,nessunretry/replay/payload/secrets. Non dire che nuovaevidencecontieneframes né inventare causa;7/8materializzati rimaneultimo readback.

Rilette sorgenti UDP pin83249a: MaterializationReferenceGate catchIllegalArgumentException chiama ReferenceFailureEvidence.detail, che restituisce sempre diagnosticCode (ancheUNCLASSIFIED),diagnosticCategory e diagnosticFrames (anchelista vuota). ResolutionRepository.quarantine(claim,code,Map) copiaMap e aggiunge safeFailureCode prima delwriteJSON/eventappend. ResolutionWorker esegue gate prima della propria try; il catch successivo usa jobs.fail, distinto dal referencequarantine. Dockerfile copia src e compila jar; nessun checkoutalternativo dichiarato. La mancanza dei tre campi nel nuovoevento è incompatibile con quel percorso sorgente se quello stesso bytecode ha scritto l'evento; non prova quale immagine/writer sia stato attivo. Non attribuire a vecchio container, serializzazione,token o trigger senza prova. JAR etichettato atteso e dichiarazione di release non sostituiscono osservazione del file effettivo/mount/writer.

Nextgate READ_ONLY runtime inventory: dockerinspectlive image/OCIrevision rispetto5e048a/83249a, inventario container con nome contenenteudp (running/restartpolicy/image/revision), dockerCP della sola /app/app.jar nei soli container running selezionati in directory0700/root; nessun dockercreate/start/restart/deploy. Zipfile legge classi BOOT-INF e verifica strutturalmente ReferenceFailureEvidence.class, marker/chiamataGate, signatureoverloadRepository conMap, campi diagnostici e recoveryAPIcandidates; controlla duplicateentry/limiti, mount che coprejar, identitàcontainer prima/dopo. Jarhash e copie rimangono privati, stdout solo strutture/identità giàpubbliche. Receipt/log root0600 e artifactdirectory persistenti; Configenv,mountsources,arguments/credentials mai stampati né salvati. JAR_COPY_ONLY e BUSINESS_STATE_UNCHANGED riferiti al probe, non assenza di attività autonoma del worker. Nomefilterudp non provaassenza di ogni altroprocesso/host; bytecodemarkers non provano da soli writer dell'evento precedente né gli oggetti giàcaricati inJVM, soprattutto conjarbindmount. Un changedidentity rende l'osservazione concorrente e richiede riconciliazione.

Test locale structuralprojection PASS per jar sintetico instrumentato e legacy, bash-nPASS. Nessun cambio condiviso/applicativo e nessun nuovo deploy/retry. PET UDP109.7 readiness/point-of-use consultato. Dopo inventario basare fix/diagnostica sui risultati; seJARcoerente e singolo writer visibile, indagare altro writer/trigger/serializzazione senza stampare safe_detailintegrale. Conservare originali e tutti3retryaudit. Status materializzazione7/8, search/storageindipendente/causalitàstorica/R-INSTALL e altri gate ereditati restanoaperti.


### R4A — due container UDP attivi rilevati, confronto binding ancora aperto (2026-10-01)

L'inventario runtime ricevuto dall'operatore prova che `ouf-udp` usa l'immagine attesa `sha256:5e048a859716d6674355e72238f03f899abd705a943ceadbdc5c8863d28f4e9f`, revision label `83249a897eb4add4289b5181b3299f48ea4c0f99`. Il JAR non è coperto da mount e contiene ReferenceFailureEvidence, le tre chiavi diagnostiche e l'overload diagnostico della quarantena. Identità invariata durante la copia.

È contemporaneamente RUNNING `ouf-udp-r4a-smoke`, immagine `sha256:707fe8ca7b1a795f8ff359f9fdb6c968734c0cf66e5b8f7bd9757f4104466f80`, revision label non provata, restart policy `no`. Il suo JAR contiene il gate ma non ReferenceFailureEvidence né l'overload diagnostico. Gli altri container censiti sono STOPPED; alcuni conservano restart policy `unless-stopped`. Non è stata eseguita alcuna modifica ai container.

Ricevuta privata: `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/runtime-reference-code-z145sybh/receipt.json`; protocollo omonimo `protocol.log`. La presenza di due processi non prova da sola un worker concorrente sullo stesso DB né chi abbia scritto l'evento delle 16:14:25Z. Nel codice corrente PublishedResolutionLoop è condizionato da `ouf.udp.execution.enabled=true`; ResolutionWorker presente nel JAR non prova l'attivazione del loop.

Stato business confermato precedente invariato: 7/8 materializzazioni; il job `e7572836-f8af-4c58-b5fc-12d7aff5db1d`, handoff `aed8ef93-6d00-4cf0-868d-d2d82d79b524`, resta QUARANTINED v5, attempts=2/integrityAttempts=2, CONTRACT_INVALID. Nessun ulteriore retry. Policy 36 e autorizzazione HUMAN nominale già provate; non ripubblicare e non ampliare grant.

Prossimo passo: confronto READ_ONLY delle configurazioni dichiarate dei soli due container, delle classi del loop nei rispettivi JAR e dei possibili override. Valori DB, credenziali, comandi e nomi delle reti non sono stampati né inclusi nelle ricevute. Uguaglianza dichiarata non equivale a binding effettivo Spring. Nessun arresto automatico in questa fase. Se emerge concorrenza sul DB, predisporre arresto circoscritto e reversibile del solo legacy preservato, con guard d'identità e ricevuta; successivamente nuova review HUMAN del solo job restante a v5 prima di proporne il retry.

PET consultato: UDP v1.3 §§109.6–109.7, ciclo dei claim/lease e reference-integrity senza fallback. Gate deploy da industrializzare: inventario di tutti i processi che possono acquisire job sul DB di destinazione, controllo versione/configurazione e trattamento esplicito di container legacy e restart policy; supportare più worker soltanto se compatibili e governati. Parametri di installazione in manifest/configurazione, mai endpoint/credenziali/tenant incorporati nel codice. Restano aperti 8/8, search, verifiche storage e installazione automatizzata multi-host/reti/Enti.


### R4A — confronto due worker completato; isolamento legacy predisposto (2026-10-01, 19:01 Europe/Rome)

Ricevuta operatore privata: `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/worker-binding-comparison-azz0955w/receipt.json`.
I due container RUNNING hanno URL/utente/credenziali DB dichiarati uguali, una rete Docker condivisa, `OUF_UDP_EXECUTION_ENABLED=true`, classi del loop schedulato e relativo gate presenti, binding datasource OUF e schema UDP dichiarati nel JAR. Nessun possibile override rilevato dalla verifica; entrambe le identità invariate. Questo è un rischio concreto di concorrenza con codice legacy incompatibile con la diagnostica corrente. Binding effettivo Spring e autore storico dell'evento NON provati; non attribuire l'evento del job restante al legacy come fatto accertato.

Decisione operativa: preservare e arrestare in modo circoscritto `ouf-udp-r4a-smoke` con immagine attesa `sha256:707fe8ca7b1a795f8ff359f9fdb6c968734c0cf66e5b8f7bd9757f4104466f80`, già restart=no. Non modificare né riavviare `ouf-udp` (immagine 5e048a, revision 83249a); non rimuovere altri container. Arresto predisposto, NON ancora eseguito/verificato.

Runbook con guard: immagini e revision live esatte; flag/binding/rate condivise riconfermati; assenza di override; main raggiungibile attraverso la rete del gateway; nessun job non terminale nell'intero DB interrogato; esattamente sette originali SUCCEEDED/PROCESSED e il restante job e7572836 QUARANTINED/DURABLE a v5. Prima della mutazione salva e fsync la ricevuta privata STOP_INTENT_OUTCOME_UNKNOWN. Lo stop usa l'ID immutabile del solo legacy e 60 secondi per shutdown; un timeout non provoca né restart automatico né retry. Dopo lo stop verifica exit code 0/143 e assenza OOM, restart=no, identità del main invariata, salute backend gateway e confronto completo degli originali prima/dopo.

Verifica locale: sintassi Bash/Python e sei scenari simulati (successo, immagine diversa, override, salute assente, worker non idle, timeout/esito sconosciuto), senza Docker reale. Nessuna chiamata di stop del main in tutti gli scenari. Ricevuta STOP privata con stati e identificativi, senza env/credenziali/URL DB/comandi. Nessun backup aggiuntivo: questa procedura non modifica schema o dati business. Le query sono READ ONLY; l'unica mutazione prevista è lo stop del container legacy.

PET UDP v1.3 §§109.6–109.7 riconsultato: niente arresto con claim pendenti, shutdown controllato e nessun silent fallback. Il gate deploy deve inventariare tutti i processi worker collegabili al DB target e verificare che le loro versioni siano ammesse; non assumere che un rilascio del container principale escluda worker di smoke residui. Conservare parametri host/reti/domain/tenant/moduli nei manifest di installazione e supportare worker concorrenti soltanto con contratti compatibili. Altri container STOPPED con restart unless-stopped restano censiti, senza cleanup indiscriminato.

Stato recovery: 7/8 confermati; nessun nuovo retry eseguito. Dopo PASS dell'isolamento, predisporre una nuova review HUMAN del solo originale restante a v5 e un nuovo retry esplicitamente confermato, usando la policy nominale 36 esistente senza ripubblicazione né ampliamento. Non riutilizzare lo script precedente dei tre job a v2. 8/8, search, storage e industrializzazione deploy restano aperti.


### R4A — isolamento legacy PASS; recovery del solo originale restante predisposta (2026-10-01, 19:10 Europe/Rome)

L'operatore ha restituito PASS dell'arresto circoscritto. Ricevuta privata `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/legacy-worker-stop-asbhqris/receipt.json`: legacy STOPPED, preservato, restart disabilitato; identità live invariata, salute backend gateway PASS, originali invariati. Guard prima dello stop: worker idle. Nessun retry/replay eseguito in questa fase. Autore storico dell'evento di quarantena ancora NON provato.

Ultimo stato business provato: 7 originali SUCCEEDED/PROCESSED e il job `e7572836-f8af-4c58-b5fc-12d7aff5db1d` / handoff `aed8ef93-6d00-4cf0-868d-d2d82d79b524` QUARANTINED/DURABLE a v5. La procedura nuova seleziona soltanto questo job. Verifica comunque resources.json completo, hash della ricevuta di pubblicazione, descriptor e tutti e tre i grant nominali; non produce una policy ristretta diversa e non ripubblica la versione 36. Gli altri due job già recuperati non vengono riesaminati come quarantene né rilanciati.

Codice helper pubblicato e congelato a `9ff81375422399bd1a259414dbe9932cb8fdcd1a`: `--select-job` restringe GET/POST al sottoinsieme del resource set completo verificato; ID fuori insieme o duplicati sono bloccati. `--prior-expected-version 2` valida soltanto la review storica di tutti e tre i job. La nuova review owner HUMAN deve avere stato QUARANTINED/DURABLE, versione esatta 5, contratto READY e snapshot verificato; è l'unica origine di snapshot e versione del nuovo POST. Il fresh receipt deve contenere l'esatto sottoinsieme selezionato. Mai utilizzare lo snapshot della review storica per il nuovo comando.

Il blocco operatore ricontrolla la ricevuta di isolamento PASS e gli ID/immagini corrente principale/legacy, legacy fermo con restart=no e revision live attesa prima del login. Poi Device Grant THS nominale `ouf-admin` con scope già configurato; GET anonima e fuori ambito devono essere negate, GET owner fresca del solo restante deve passare. Piano JOBS=1, expectedVersion=5, READY acceptedVersion=6. Solo dopo la conferma esplicita nel terminale viene trasmesso un POST /retry dell'originale; operationId e richiesta persistiti prima della trasmissione, token con oltre 60 secondi residui, nessuna ripetizione automatica.

La conferma richiesta resta `CONFERMO RETRY ORIGINALE 86809c17-3354-45ca-a7e6-57e903944b24`: verificare prima che il piano stampato abbia JOBS=1 e il solo ID e7572836. Receipt/protocol nuovi con prefisso human-retry-remaining, separati da quelli precedenti. Se BLOCKED o risposta incerta, riconciliare le ricevute senza rilanciare automaticamente. PASS di retry significa requeue accettato, NON materializzazione riuscita; servirà readback business successivo. La procedura non crea intake/handoff o replay, non riattiva la source/schedule.

Verifiche: 50 test locali policy/recovery, incluse regressioni selezione singola v5->6, altri due già SUCCEEDED, selezione fuori scope/duplicata, drift v6 e contratto non READY. Preflight isolamento: cinque scenari simulati. CI sul pin helper: 113 test recovery PASS (job 110488957023, run PR 36897761180), Java/container PASS, tutti e sette i workflow push/PR SUCCESS inclusi Authorization, Shared SDK e Gateway pairwise. Checksum dei tre file modificati aggiornati. Nessun nuovo deploy UDP necessario.

PET riconsultati: UDP v1.3 §§109.6–109.7 e Authorization v1.5 §36.10, owner enforcement e reference gate senza fallback. Installazione portabile continua a separare argomenti/configurazione da codice helper; blocco seguente è una riconciliazione lab con binding espliciti, non un default per Enti diversi. Handoff/deploy/roadmap conservano aperti 8/8, search, verifiche storage e automatizzazione install/upgrade/restore. Esito live della recovery singola ancora NON eseguito.


### R4A — retry del solo originale restante accettato; verifica 8/8 pendente (2026-10-01, 19:22 Europe/Rome)

Output operatore ricevuto: nuova GET owner HUMAN HTTP 200 sul solo job `e7572836-f8af-4c58-b5fc-12d7aff5db1d`, handoff `aed8ef93-6d00-4cf0-868d-d2d82d79b524`, QUARANTINED/DURABLE v5, retryEligible=true, contractReady=true, contractCheck=READY. Anonimo e fuori ambito negati; owner authorization e reference gate Spring PASS. Piano JOBS=1 per run `86809c17-3354-45ca-a7e6-57e903944b24` e source `managed-cinema-8ec8ae90`. Conferma esplicita nel terminale seguita da POST HTTP 200, original job match, acceptedVersion=6, READY, repeated=false. ACCEPTED_COUNT=1. Nessun replay/new intake POST.

Ricevuta fresca privata: `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/human-retry-remaining-20261001T172023-3532794-fresh-review.json`. Ricevuta primaria prevista dal blocco eseguito: stesso stem senza `-fresh-review`, cioè `human-retry-remaining-20261001T172023-3532794.json`; da verificare nel readback, non ricostruire o sovrascrivere. Protocollo privato `human-retry-protocol.edu1pk`. L'output riportato prova il comando accettato; non contiene ancora il readback di materializzazione né gli exit code finali del wrapper.

Ultimo stato materializzato provato ancora 7/8. Non promuovere a 8/8 dal solo READY acceptedVersion=6. Legacy isolato e conservato con restart=no nella ricevuta precedente `legacy-worker-stop-asbhqris/receipt.json`; causalità storica dell'evento senza diagnostica tuttora non provata.

Prossimo blocco READ_ONLY: valida la ricevuta primaria privata (PASS_AUTHORIZED_REQUEUE, humanConfirmed, un solo job/handoff, selectedJobIds esatto, versione richiesta 5 e accettata 6, operationId UUID corrispondente, repeated=false). Poi esegue il readback Cinema della source frozen e la diagnostica UDP parametrizzata per run/source; acquisisce entrambe le uscite in un nuovo protocollo privato anche se il primo controllo non prova il risultato completo. Nessun login THS, retry, replay, riattivazione o intake POST. Helpers congelati al pin CI verde `9ff81375422399bd1a259414dbe9932cb8fdcd1a`; wrapper guarda ricevuta verificato su sei scenari locali, senza query live.

Il readback Cinema resta una fixture lab esplicita, non un manifest portabile: in una nuova installazione utilizzare parametri frozen/source/run e binding di deployment locali. Le query dei diversi DB non sono uno snapshot atomico. Criterio di completamento: otto originali consegnati e otto job SUCCEEDED/PROCESSED con reference gate passato e risoluzione completata, nessun job originale in quarantena. Distinguere questo risultato dalla verifica serving/Search, dai controlli storage e dal deploy industrializzato, ancora aperti.

PET UDP v1.3 §§109.6–109.7 riconsultato: recovery governata e verifica reference-integrity prima della materializzazione. Nessun nuovo deploy, policy publish o ampliamento di autorizzazione. Handoff, manuale installazione, roadmap e runbook aggiornati; acquisire il prossimo output prima di dichiarare il gate 8/8 chiuso.


### R4A — consegna e materializzazione 8/8 PROVATE; vincolo PET e hardening generale (2026-10-01, 19:28 Europe/Rome)

**Checkpoint corrente: ING_DELIVERY_EIGHT_ROWS=PASS; UDP_MATERIALIZATION_EIGHT_ROWS=PASS.** Questo checkpoint supera gli stati storici 5/8 e 7/8, senza cancellare le relative evidenze. Search/serving, verifica byte/hash storage indipendente e industrializzazione deploy R-INSTALL restano APERTI.

Readback operatore privato: `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/readback-after-retry.sUa4nQ`. Exit readback=0 e diagnostica UDP=0. Source ACTIVE, hash frozen/publication corrispondenti; run `86809c17-3354-45ca-a7e6-57e903944b24` SUCCEEDED, 8 handoff ACKED, 8 lineages, 0 quarantene Ingestion. Schedule trigger_once consumata/DISABLED. Dieci attempt ING conservano la storia degli errori risolti, senza nuove ingestion/replay.

UDP: 8 intake PROCESSED, 8 job SUCCEEDED, 8 decisioni NEW_OBJECT, 8 observations/revisions/bindings/active objects; nessun failure code o issue di risoluzione aperta. Set handoff ING/UDP corrispondenti. Ogni handoff ha esattamente un HANDOFF_DURABLE, REFERENCE_INTEGRITY_PASSED e RESOLUTION_COMPLETED. I tre originali recuperati conservano gli eventi di quarantena e comando autorizzato: due job hanno un MATERIALIZATION_RETRY_AUTHORIZED e una quarantena storica; l'ultimo ha due di ciascuno. Nessun audit cancellato per far apparire il run riuscito.

Ultimo originale `e7572836-f8af-4c58-b5fc-12d7aff5db1d` / handoff `aed8ef93-6d00-4cf0-868d-d2d82d79b524`: SUCCEEDED/PROCESSED v8, attempts=3, integrityAttempts=2, baseline presente, missingRefCount=0, nextCheck assente, safeFailureCode nullo. Il precedente retry nominale HUMAN a v5->READY v6 è ora seguito da effettivo completamento. Non serve altro retry né riattivazione di source/schedule.

Limiti espliciti: letture cross-DB non atomiche; SEARCH_NOT_VERIFIED=true. I marker recenti ING_ACTIVATION_DISCOVERY_UNAVAILABLE sono 13; dispatch/publication/delivery/execution failure marker sono 0. Il run riuscito non risolve automaticamente i marker discovery: restano da correlare con finestra/worker e dipendenze, senza dedurne da soli un nuovo blocco del run. L'autore storico dell'evento privo di diagnostica NON è provato dal successo dopo isolamento del legacy.

**Istruzione di governo confermata dall'utente:** consultare i PET a ogni sprint; evitare deriva; se una regola del PET è ambigua o manca, presentare il punto preciso all'utente e decidere insieme prima di implementare quella scelta. Non introdurre una nuova norma in PET, codice o runbook tramite deduzione dal singolo caso. Gli incidenti sono evidenze e fixture di regressione; le regole operative derivano dagli invarianti generali. Container/UUID/source/tenant/domain/host/reti sono binding di installazione/test, non costanti di dominio.

PET riconsultato: UDP v1.3 §36.1 (search e access label, nessun side channel da count non autorizzati), §§109.2 (API/schema compatibili e rollout N/N+1), 109.6–109.7 (recovery e reference gate), 109.9 (runbook, retry bounded/transient e quarantena integrity, nessun repair business non auditato). Authorization v1.5 §36.10 è il vincolo owner già applicato alla recovery. Il PET consente workload/runtime distinti e N/N+1; non generalizzare l'incidente a “un solo worker” o “tutte le revisioni differenti vietate”.

| Evidenza del caso | Invariante generale collegato al PET | Stato |
| --- | --- | --- |
| Worker legacy attivo sul medesimo binding DB | Tutti i workload di una release devono avere contratti/schema compatibili; concorrenza e N/N+1 restano ammessi (§109.2). | Legacy isolato; inventario e gate automatico compatibilità da industrializzare. |
| Reference gate in quarantena | Verificare i riferimenti prima della materializzazione, senza fallback a ACTIVE (§109.7/109.9). | Otto originali hanno ora reference gate PASS; hardening diagnostico e regressioni da consolidare. |
| Owner HTTP403 e grant scoped | Applicare authn/capability/resource/data-label nell'owner prima di accesso/serializzazione (§36.1 e Authorization §36.10). | Fix owner e test già implementati; GET/POST HUMAN nominali provati. |
| Perdita shell/output o risposta incerta | Recovery idempotente/auditabile da stato verificato, senza ripetizioni ambigue (§109.6/109.9). | Ricevute persistenti, intent prima POST, riconciliazione e logger verificati; integrazione stabile THS/deploy da consolidare. |
| Retry di tre originali, poi uno solo | Comando governato con precondizioni correnti per ciascuna risorsa (§109.6). | Selezione parametrica nel set pubblicato, snapshot/versione freschi, test regressione e CI 113 PASS. |
| ACK riusciti ma materializzazione parziale | Durable ACK e serving non attestano la medesima fase (PET semantica durable ACK e serving). | Due gate delivery/materialization chiusi separatamente; serving/Search aperto. |

Le colonne “da industrializzare/consolidare” sono backlog generale tracciato, non nuove norme architetturali già approvate. Nessuna scelta di nuovi tipi di quarantena, TTL, topology policy o automatismi di mutazione viene applicata se non coperta dal PET o da decisione utente registrata. I test devono includere casi generali (worker compatibili multipli/N+1, versioni stale, accesso negato, timeout, retry idempotente), oltre alla fixture lab.

Prossimo gate autorizzato: verifica Search/serving attraverso il canale e le API previste, con principal e access label autorizzati; contare record in PostgreSQL non prova Search. Pinned ServingApi offre GET /api/udp/v1/objects?type=... e POST /objects/search per MCP con medesimo owner enforcement; nessuna chiamata runtime serving eseguita in questo checkpoint e nessun grant/routes/scope ampliato per ottenerla. Verificare prima i binding effettivi ed i contratti macchina della release.


### Nuovo CSV Teatri — upload/profilazione MCP riusciti; riferimenti semantici non ancora selezionati (2026-10-01, 19:50 Europe/Rome)

Nuovo test del percorso effettivo via MCP, distinto dalla precedente fixture Cinema con materializzazione 8/8 PASS. Account scelto dalla sessione: ouf-admin, subject b93d8cf6-cd14-4ee6-91d7-84cd76c4f500. Nessun SSH usato per upload/profilazione.

source.file.upload ha restituito il picker HUMAN governato con handoff `b6de7b63-4a1a-47d8-858e-3cc5f0adad51`. Widget ha segnalato asset `6609b245-86ed-4315-8ce0-73f2a8555bf3`; il successivo source.file.profile con controllo owner ha accettato la richiesta (QUEUED job `2f49ea03-b715-493b-ba25-a3f82007cd3d`). source.file.preview sul job ha restituito SUCCEEDED/resultRef `7984c39c-7396-4248-ab0a-f2efc390b49c`; la preview di quel profilo conferma asset/profile binding, versione 1. La verifica separata source.file.upload.status ha ricevuto errore host `tool selection stalled`, retryable=false: non è un errore di ingestione/quarantena OUF provato, non ripetuta. La successiva profilazione/preview costituisce evidenza del managed asset accessibile al principal.

Profilo metadata: CSV UTF-8, separatore ;, headerRow=1, 13 righe/20 colonne, recordModel ONE_ROW_ONE_SOURCE_OBJECT, proposalStatus PENDING_HUMAN_REVIEW. Campi: nome_teatro, tipologia, toponimo, nome_indirizzo, civico, cap, citta, provincia, latitudine, longitudine, sistema_riferimento, precisione_coordinate, capienza_posti, spettacoli_stagione, stagione_riferimento, note, fonte_indirizzo, fonte_coordinate, fonte_altri_dati, data_verifica. Non copiare sample o dati raw nei documenti. Coordinate/capienza e altri campi nullable; CAP inferito LONG dal profiler, ma inferenza non decide datatype semantico (codice postale va valutato come codice, preservando eventuali zeri iniziali).

Candidate keys osservate: nome_teatro, nome_indirizzo, fonte_indirizzo; uniqueness osservata su 13 righe non prova stabilità nel tempo. Identity proposal: NATIVE_KEY nome_teatro, normalization managed-file/native-key-v1, esplicito limite “stabile finché la chiave non cambia”. Non approvata. Non scegliere identità/classe/label/INCLUDE o EXCLUDE soltanto dall'inferenza; richiedono proposta e review dei dati/classificazioni.

PET Source Onboarding v1.6 §§92,92.1–92.2 consultato: profiler propone struttura/statistiche ma non decide classi semantiche o mapping autoritativi; ManagedFileAsset non è ancora Urban Object; DRAFT/review/approvazione precedono runtime ingestion. App source.onboarding.create richiede profilo reviewed, targetClassIri, semanticRefs pinned, field access decisions e chiave source object. Non invocata: nessuna DRAFT/approvazione/pubblicazione/ingestione Teatri prodotta in questo checkpoint.

Gap osservato nel catalogo degli strumenti OUF attualmente esposti in questa chat: presenti upload/status/profile/preview/onboarding.create, operations/authorization e urban.object search, ma nessuna capability per leggere classi/proprietà/publication semantiche. Non dedurre che Semantic Registry backend sia vuoto o indisponibile. Serve verificare la superficie MCP e il contratto PET Semantic prima di predisporre la consultazione governata; non inventare IRIs, semanticRefs, versioni o riusare i riferimenti Cinema sul nuovo tipo. Nessun fallback via route non autorizzata o modifica a grants/policy da questo checkpoint.

Prossimo passo: consultazione dei contratti/PET Semantic per disporre di riferimenti versionati governati e proposta mapping Teatri; review utente di profilo, identità e classificazioni prima di source.onboarding.create. Qualunque ambiguità/lacuna PET va portata all'utente per decisione, non colmata autonomamente. Registrare l'assenza della capability come gap generale del percorso MCP, non come regola specifica ai Teatri/13 record. Restano invariati il gate precedente Cinema 8/8 e gli open gates Search/storage/R-INSTALL.


### Percorso managed file — proposta di automazione utente confrontata ai PET (2026-10-01, 19:58 Europe/Rome)

L'utente richiede un percorso guidato dopo upload: Onboarding consulta semantica/vocabolari esistenti, ricerca esterna quando necessaria, propone mapping, governa duplicati/ambiguità e conduce il dato alla UDP. Confermato il fine generale; non introdurre un flusso legato al CSV Teatri né fare dipendere il prodotto dalla fornitura manuale di IRI da parte dell'utente.

Riferimenti PET letti in questa verifica: Semantic Model/Registry v1.3 §§11,11.1,17,18–18.1; Source Onboarding v1.6 §§92–92.2 e confini control-plane; UDP v1.3 §§21–22. Sequenza autoritativa prevista:
1. File HUMAN governato -> ManagedFileAsset/staging -> profiling deterministico.
2. Onboarding/esperienza assistita cerca semantica interna adeguata nel Registry; se assente, SemanticGap e Semantic Discovery on demand tramite provider adapter autorizzati e Gateway.
3. Candidate esterno -> confronto/proposta -> decisione HUMAN -> adozione DRAFT/review/publication ACTIVE. Un candidateRef esterno non può essere usato come semanticId ufficiale da Onboarding/runtime. Mapping, identità e classificazioni della source confluiscono nella DRAFT; review e approvazione HUMAN precedono il bundle ACTIVE.
4. Ingestion consuma bundle/ref pinned, esegue parsing/normalizzazione/mapping, persiste input RAW secondo durabilità e consegna HandoffPayload/CandidateObject idempotente alla UDP.
5. UDP esegue Object Resolution e policy: MATCH, NEW_OBJECT, REVIEW_REQUIRED o REJECTED; soltanto contributi ammessi sono materializzati. Duplicati/matching autoritativi sono responsabilità UDP successiva all'handoff, non ETL dell'Onboarding. Eventuali preflight non sostituiscono la decisione al punto d'uso.
6. Ambiguità apre ResolutionIssue e percorso HUMAN governato; merge autoritativo segue plan/impact/THS/audit, non una scelta AI automatica. Non equiparare ogni MATCH deterministico a un merge di identità canoniche.

Correzione alla diagnosi del checkpoint precedente: mancanza di tool Semantic esposto nella chat è un fatto osservato del catalogo, ma non dimostra che sia necessario un tool separato né che il backend Onboarding non possa già consultare Semantic. Il gap da verificare è l'orchestrazione e la consultazione governata nel percorso di onboarding, inclusa presentazione di candidati/mapping e ripresa dopo decisioni HUMAN. Non proporre l'ampliamento del catalogo MCP come unica soluzione senza verificare contratti e implementazione owner.

Ontopia/SPARQL: desiderio utente di una fonte di discovery; nei PET esaminati la regola è provider-based/configurabile e on demand. Nessun endpoint Ontopia o SPARQL specifico è stato verificato/configurato in questa sessione. Non introdurre URL/provider nel dominio né accettare query SPARQL arbitrarie dal chatbot. Un adapter concreto deve rispettare il contratto provider, Gateway/egress, timeout/TTL e provenienza del candidato. Il PET non prescrive “Ontopia sempre” né l'adozione automatica di risultati esterni.

Automazione attesa: concatenare passi tecnici, monitorare esiti e mantenere stato/receipt per riprendere il percorso; fermarsi e presentare THS quando è richiesta una decisione HUMAN autoritativa. Non automatizzare approvazione semantica/source o merge autoritativo aggirando THS. Prima di implementare una politica di scelta o classificazione non specificata dal PET, esporre la lacuna all'utente per decisione congiunta.

Checkpoint Teatri invariato: asset 6609b245-86ed-4315-8ce0-73f2a8555bf3, profilo 7984c39c-7396-4248-ab0a-f2efc390b49c v1 SUCCEEDED, 13 righe/20 colonne; nessuna DRAFT/ACTIVE/run UDP prodotta. Prossimo lavoro: gap analysis dei contratti e owner Onboarding/Semantic/MCP per ripristinare un percorso guidato realmente generale. Nessun nuovo deploy, provider, scope, grant o modifica PET applicato da questa registrazione.


### Piano di completamento file -> UDP: chatbot propone mapping, riuso dei passi già corretti (2026-10-01, 20:09–20:10 Europe/Rome)

Chiarimento utente: il chatbot svolge analisi/ricerca/proposta del mapping; Onboarding governa e persiste il mapping della source, Semantic governa gli artefatti/versioni, backend owner valida e THS raccoglie decisioni HUMAN autoritative. Non introdurre un agente AI interno al servizio Onboarding: MCP resta il client dell'AI esterna. L'utente ribadisce che i singoli passi sono stati testati/corretti a mano in molte ore; conservarne fix, test, pin e ricevute, NON riavviare il lavoro manuale da zero.

PET riletti: Source Onboarding v1.6 §§92–92.2 e THS-03/04/07; Semantic v1.3 §§9.2,10–11,17–18; UDP v1.3 §§21–22,109.2,109.6–109.9. Backend Semantic ispezionato al pin 48a652e0: ArtifactApi implementa search/read/propose; ValidationApi implementa references:resolve/validation/impact; DiscoveryApi request/candidates/adoption DRAFT/providers; GovernanceApi approval-challenge. Queste sono evidenze sorgente, NON verifica live di route/scopes/policy o del provider esterno. DiscoveryApi corrente espone status schemaGov; Ontopia adapter effettivo non provato. Catalogo MCP disponibile in questa chat non espone Semantic, submit/review/status source lifecycle o resolution plan/THS recovery; distinguere mancanza esposizione da assenza backend.

Piano di lavoro:
| Passo | Riuso e vincoli PET | Collegamento/gate da completare |
| --- | --- | --- |
| 1. Baseline dei passi già corretti | Pin per modulo/immagine/schema, test esistenti, receipt manuali; Cinema 8/8 PASS e upload/profile Teatri MCP PASS conservati. | Matrice passo -> contratto/API -> revisione -> evidenza -> ingresso MCP/THS; evitare codice stale dei branch/base e regressioni delle fix owner/intake/recovery. |
| 2. Consultazione semantica del chatbot | API ricerca/lettura/riferimenti/discovery esistenti; candidati esterni non ufficiali. | Proiezioni MCP tipizzate/bounded, Gateway/SDK owner authorization e metadata di versione/provenance sufficienti a formulare mapping; verifica live dei binding necessari. |
| 3. Proposta completa Onboarding | Managed asset/profile esistenti, SemanticMapping v1, source identity, classificazioni, transform whitelist, CRS/temporal/authority/representation richiesti dai contratti. | Il chatbot prepara mapping motivato, copertura campi/dubbi e richiesta DRAFT completa; owner verifica refs ACTIVE/pinned e configurazione consumabile dal runtime. Non chiedere IRI manuali né convertire statistiche in policy approvata. |
| 4. Review/approvazione e ripresa | THS/owner approvazione già implementati e provati dove registrato; no tools/call MCP di conferma. | Preparazione challenge, link THS, lettura esito e ripresa idempotente del percorso dopo decisione/timeout; separare source approval da eventuale adozione di nuova semantica. |
| 5. Activation/ingestion e risoluzione | Consumo di bundle pubblicato, durabilità RAW, handoff e UDP reference gate/identity/materializer già corretti; MERGE autoritativo/REVIEW_REQUIRED HUMAN. | Collegare trigger previsto dall'attivazione e monitorare run/handoff/job; proiezioni di dubbio/issue e THS owner, senza nuove ingestion o replay in caso di esito incerto. |
| 6. Esito verificabile e deploy portabile | API Search presente, owner filtering, evidenze job/lineage/history; fixture precedente preservata. | Check end-to-end nuovo file via MCP/THS fino a UDP e serving autorizzato; install/reconcile automatizzati di catalogo/scopes/policy/routes/provider/config per host/reti/domain/tenant parametrizzati. |

Ordine: baseline/evidence -> collegamento Semantic al chatbot -> proposta/versione e THS -> ripresa/run/risoluzione -> collaudo completo. Non rifare un modulo o ricopiare la sua logica nel chatbot/MCP. Automatismo = avanzamento delle operazioni tecniche autorizzate e ripresa da stato owner persistito; adozione/publication/approval/merge/retry HUMAN mantengono THS e precondizioni correnti. La classificazione dei nuovi passaggi e dei provider deve seguire i PET; per lacune normative presentare il punto preciso all'utente prima di scegliere.

Strategia verifiche richiesta: riusare le suite già presenti come regressione e le receipt come prova storica; nuove prove sui collegamenti modificati, authorization/channel boundaries e nuova E2E Teatri. Nessuna ripetizione indiscriminata dei comandi SSH e delle verifiche manuali già passate. Riaprire un gate già superato solo se una nuova modifica/rollout lo coinvolge, se la prova non copre il collegamento nuovo o emerge drift/incompatibilità. Test del flusso deve coprire ripresa dopo perdita chat/shell, decisione stale, transient vs integrity, scope/tenant negati e nessun duplicato da retry.

Questa registrazione è piano operativo, non dichiarazione di capacità end-to-end già funzionante né modifica ai PET. Nessun nuovo deploy/API/permission mutato. Nuovo CSV Teatri ancora soltanto asset/profile SUCCEEDED; nuova semantica/mapping/DRAFT da predisporre con capability governate. Primo deliverable concreto: esposizione semantica e proposta mapping dello stesso asset già caricato, senza nuovo upload o replay Cinema.

## 2026-10-02 — percorso comune file/API e timing acquisizione

[Sprint completo](sprints/OUF_ACQUISITION_TO_UDP_2026-10-02.md). File: trigger automatico una tantum dopo onboarding approvato/ACTIVE. Verticale: THS endpoint/credenziali → THS scelta profilo estrazione → scheduler governato; Ingestion alle scadenze del bundle. Mapping/review/UDP comuni e chatbot-neutral. Incremento Semantic search/exact-read candidato, non deployed e non acceptance finale. Preservare tutte le prove/gate già tracciati.

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

## Checkpoint correttivo successivo — pin sorgenti definitivi e staging proposto

MCP e64cb3938efb95c4f83cd9ca9cb0aa4874c7d215: entrambe le CI complete SUCCESS (protocol/lifecycle include i due nuovi tests tools/call, build/staticcheck/govulncheck; conformance Java/Go). Gateway2cdeb194028a2e5ba8cac859bd8814665969deaf: CI completa SUCCESS. Semantic pin definitivo1568b07acc1ba77a190a549d7a3ee6e1fdc1ef63 sostituisce12133: aggiornato anche checksum del workflow pairwise che punta al nuovo Gateway. I tre file cambiati congelati sono API, test e workflow; nessuna migration modificata. Ultimo esito completo Semantic da rileggere sul pin1568; i test pairwise/SDK/Auth sono PASS sullo stesso codice del parent. Le precedenti failure module erano nel gate checksum, prima dell'esecuzione Java.

Comando di staging proposto: scaricare r4a_stage_semantic_consultation.py da questo branch docs a commit immutabile; import in Python -B; leggere config della private runtime-snapshot.json di /etc/ouf/deploy-snapshots/consultation-20261002-0850, cambiare stageRoot=/etc/ouf/deploy-snapshots/consultation-read-fix-20261002-1049, commit Semantic1568/MCPe64c e liveRevision Semantic8985/MCP8476; invocare stage.main(config). Nessuna sostituzione live, nessuna nuova pubblicazione/grant, nessuna source/run. Operatore deve restituire STAGE receipt; non usare ancora il prepare/release originario add-only perché le due route sono già presenti. Rollback precedenti conservati.

## Checkpoint 2026-10-02 11:05 Europe/Rome — staging hotfix PASS; tutte le CI owner GREEN; preparazione sostituzione pronta

Operatore VPS: CONSULTATION_STAGE=PASS LIVE_UNCHANGED=true ROUTES_UNCHANGED=true NO_SWITCH=true NO_SOURCE_RUN=true nella nuova root /etc/ouf/deploy-snapshots/consultation-read-fix-20261002-1049.
Semantic1568b07acc1ba77a190a549d7a3ee6e1fdc1ef63 image sha256:d7bf997d258ae54609b2675778014a4db797407dd4ea4e67f82f3179525511ed.
MCPe64cb3938efb95c4f83cd9ca9cb0aa4874c7d215 image sha256:31ac648ad8327a0658c81d11ffa6a69f7d9dc47f73e3ce5298f3ad762bf1dd2a.
Route semantiche mcp-semantic-search/get già presenti, chiave Gateway OUF_SEMANTIC_READ_OWNER_KEY già configurata. Container live ancora Semantic8985/MCP8476 e Gateway della prima release; non confondere immagini staged con release.

Readback GitHub: tutte le quattro CI Semantic1568 SUCCESS, comprese Java21/Postgres17/container e Gateway Lua→Java; entrambe le CI MCPe64c SUCCESS; CI Gateway2cdeb SUCCESS. Il blocco checksum precedente superato (API/test/workflow aggiornati). Nessuna CI owner pendiente a questo checkpoint.

Estesi gli helper esistenti per prepare --replace-existing --previous-gateway-revision. Vecchi percorsi add-only preservati. Rigenerazione vecchie route da pin Gatewaye8ef e nuove da2cdeb in processi separati per evitare cache dei moduli. Verifica esatta dell'ownership delle sole due route precedenti; nessun altro pattern attivo può reclamarne gli URI. Chiave e whitelist nginx esistenti mantenute, niente rotazione: verifica key file400 UID/GID owner, binding owner/workload e uguaglianza Gateway; copia privata del medesimo valore. Tre candidati STOPPED con launch/mount/env/alias invarianti; Gateway resta stessa immagine, env e contenuto config. Rilascio mantiene i backup/readiness/deny/migration checks esistenti; aggiorna i due ID invece di crearli; rollback ripristina i corpi precedenti senza DELETE delle route esistenti e si arresta su drift di ownership. Funzionalità NON ancora eseguita sul VPS.

25 test locali PASS: 22 stage/prepare/release/preflight e 3 policy inventory. Copertura nuova di aggiornamento/rollback esatto delle route, risposta PUT persa anche durante ripristino, drift terzo proprietario, mode READ dei probe, ownership incompleta.

Prima dello switch occorre verificare il descriptor LIVE di read: il manifest storico catalogue/r4a-udp-published-execution.json registrava ouf.semantic.read READ con allowedActors=[SERVICE]. I preflight precedenti provavano esistenza/attivazione, non HUMAN allowed; grant37 non ne prova l'efficacia. Non assumere che il descriptor LIVE sia uguale allo storico. Predisposto r4a_semantic_consultation_policy_inventory.py: READ ONLY transaction, deriva DB Authorization dall'Onboarding binding e PG locale, stampa SOLO operation/scope/allowedActors/owner dei due descriptor registrati e pubblicati e policyRef. Nessun bearer, grant o segreto in output; niente registrazioni/publicazioni. Eseguire questa lettura prima di prepare/switch. Se read è ancora SERVICE-only, definire il contratto HUMAN coerente col PET tramite owner, senza allargare le identità SERVICE o modificare direttamente il DB/capability_registration immutabile. Dati/source/run invariati, search/get positivi ancora NON PROVATI.


### 2026-10-02 — Contratto HUMAN distinto per la lettura semantica MCP

L'inventario live dell'operatore conferma policy `ouf-lab-authorization:37`: `ouf.semantic.search` è READ/HUMAN; `ouf.semantic.read` è READ/SERVICE sia nel registro sia nel bundle pubblicato. Il grant nominale `grant-semantic-read-human-admin` pubblicato nella policy 37 non può autorizzare HUMAN su questo descriptor. Il precedente controllo del descriptor prima della proposta è stato omesso: errore della procedura di coordinamento, ora corretto senza ampliare o sostituire il contratto SERVICE immutabile.

La capability HUMAN separata è `ouf.semantic.consultation.read`, owner semantic, operation READ, requiredScope `ouf.semantic.read`, allowedActors [HUMAN]. Lo scope OAuth già configurato viene riutilizzato: il PET Authorization consente scope Gateway più grossolani delle capability applicative. Il tool utente resta `semantic.get`, con lo stesso schema e lo stesso riferimento esatto semanticId/revisionId/publicationSetId. La ricerca resta `semantic.search` con operation READ. Le API native SERVICE, i descriptor e i grant SERVICE non vengono modificati.

Sorgenti corretti: MCP `98e0c7a03d3be38458282250c71f678b9619ae62`, Gateway `c14d3f230684e3cb42c283b52f4210d5bfff3dc7`, Semantic `025a542bfe6c76d8c45ee5af668b7cb7bb0de0d6`. MCP e Gateway CI SUCCESS verificati; Semantic CI sul pin finale da verificare prima di staging/rilascio. Due errori nelle fixture Java della nuova prova (scope uguale al capabilityId e cambio lineage su runtime già popolato) sono corretti con descriptor reale e snapshot isolato; nessuna modifica al SDK di produzione.

Procedura diretta trusted HUMAN: `scripts/r4a_semantic_human_read_policy.py`, riusa il device client esistente e `r4a_authorization_lifecycle.py`. Plan è read only. Apply verifica identità/tenant/actor/audience/scope/validità, registra soltanto il nuovo descriptor se assente, crea un draft dal bundle ACTIVE preservando tutti gli altri dati, verifica il preview owner con ETag e pubblica soltanto dopo la frase digitata dall'operatore `PUBBLICA LETTURA SEMANTICA HUMAN`. Delta previsto: un descriptor aggiunto, rimozione del solo grant nominale inefficace `grant-semantic-read-human-admin`, aggiunta di `grant-semantic-consultation-read-human-admin` con subject/tenant/finestra di validità copiati dal grant nominale di ricerca. Non è una conferma MCP delegata: il bearer HUMAN resta esclusivamente nel processo locale del terminale e nelle richieste alle API trusted HUMAN. Registro SERVICE immutabile e tutti gli altri grant, inclusi quelli compilati dai ruoli, preservati. Nessuna pubblicazione eseguita dal coordinatore.

Stato privato 0600 in directory root 0700, checkpoint prima delle mutazioni, divieto di ripetere apply con stato esistente, preview esatto e lettura strutturale del bundle ACTIVE dopo publish; risposta persa riconciliata tramite readback senza seconda pubblicazione. Test locali: 15 HUMAN probe/policy PASS e 25 staging/preparazione/rilascio/inventario PASS. I probe di denial del release usano capability e operation dal nuovo schema della route, evitando payload del vecchio contratto.

Staging già ricevuto dall'operatore in `/etc/ouf/deploy-snapshots/consultation-read-fix-20261002-1049`: Semantic `1568b07acc1ba77a190a549d7a3ee6e1fdc1ef63`, MCP `e64cb3938efb95c4f83cd9ca9cb0aa4874c7d215`, LIVE_UNCHANGED e ROUTES_UNCHANGED. Queste immagini precedono il nuovo contratto HUMAN get e sono superate per il prossimo rilascio: NON prepararle né applicarle. Occorre staging dei nuovi pin in directory distinta, dopo CI verificata. Il rilascio live iniziale resta Semantic 8985d0d7 / MCP 8476a689; i container con nome rollback sono copie conservate, non un rollback eseguito.

Nessun onboarding, upload, ingestion, matching, approvazione o source run ripetuto. Cinema e Teatri storici restano congelati. Consultazione HUMAN positiva e tutti i gate end-to-end/PET ancora aperti: questa correzione non equivale ad accettazione completa del percorso acquisizione → UDP.


**Verifica successiva CI:** Semantic `025a542bfe6c76d8c45ee5af668b7cb7bb0de0d6` ha tutti e sei i check SUCCESS, inclusi java21-postgresql17, actual-lua-java-postgresql e container-smoke. MCP `98e0c7a03d3be38458282250c71f678b9619ae62` ha due check SUCCESS; Gateway `c14d3f230684e3cb42c283b52f4210d5bfff3dc7` ha cinque check SUCCESS. Helper HUMAN e documentazione sono pubblicati al pin `9dec9601cb22a941495ed17f232692abdaca2324`: check probe e preparation SUCCESS; le pipeline Java generali della branch di coordinamento sono ancora in corso al momento della lettura. Questa evidenza riguarda il codice e la procedura, non la policy live né il positivo HUMAN ancora da eseguire.

**Prossimo passo operatore:** scaricare dal pin 9dec9601 i quattro helper `r4a_semantic_human_read_policy.py`, `r4a_authorization_lifecycle.py`, `r4a_probe_semantic_human_mcp.py`, `r4a_admin_permission_proposal.py` e invocare il primo in modo apply, issuer `https://auth.ouf-lab.it/realms/ouf`, base-url `https://api.ouf-lab.it/api/trusted-human/v1/authorization`, client `ouf-human-admin`, subject `b93d8cf6-cd14-4ee6-91d7-84cd76c4f500`, tenant `ouf-lab`, audience `ouf-api-gateway`, stato `/etc/ouf/deploy-snapshots/consultation-read-fix-20261002-1049/human-read-policy-state.json`. Usare Python -B; nessun bearer da copiare in chat. Login HUMAN e frase di conferma solo dopo preview del delta preciso sopra descritto. Se stato già presente o apply interrotto, riconciliare prima di ripetere; publish/verify riusano il draftId privato. Ricevuta attesa `SEMANTIC_HUMAN_READ_POLICY=PASS` con policyRef effettiva. Pubblicazione ancora non ricevuta.


### 2026-10-02 11:52 Europe/Rome — Policy HUMAN read pubblicata, staging successivo

Ricevuta dell'operatore: `SEMANTIC_HUMAN_READ_POLICY=PASS POLICY_REF=ouf-lab-authorization:38 NO_SOURCE_RUN=true NO_SECRETS_PRINTED=true`. È concluso il passo di pubblicazione trusted HUMAN del nuovo descriptor `ouf.semantic.consultation.read` e della sostituzione del grant nominale inefficace. Il PASS dello script include il readback strutturale del bundle ACTIVE previsto. Non ripetere apply; lo stato privato rimane `/etc/ouf/deploy-snapshots/consultation-read-fix-20261002-1049/human-read-policy-state.json`. Nessun nuovo container/rilascio o test positivo MCP è dimostrato da questa ricevuta.

CI riletta dopo la ricevuta: Semantic `025a542bfe6c76d8c45ee5af668b7cb7bb0de0d6` 6/6 SUCCESS; MCP `98e0c7a03d3be38458282250c71f678b9619ae62` 2/2 SUCCESS; Gateway `c14d3f230684e3cb42c283b52f4210d5bfff3dc7` 5/5 SUCCESS. Sul pin helper `9dec9601cb22a941495ed17f232692abdaca2324` probe, preparation, live-pairwise, Java e SDK SUCCESS; due container-smoke di quella branch sono CANCELLED, non PASS, dopo aggiornamento successivo dei soli documenti. Le immagini da rilasciare si basano sui tre pin feature sopra, non sulla branch di coordinamento.

Prossimo comando operatore: riutilizzare `r4a_stage_semantic_consultation.py` al pin helper 9dec9601, derivando configurazione Gateway e binding container dallo snapshot privato esistente `/etc/ouf/deploy-snapshots/consultation-read-fix-20261002-1049/runtime-snapshot.json`. Verificare che i due liveRevision attesi siano Semantic `8985d0d7f772dc7a7fd3deb3d5a569b1406d5d6c` e MCP `8476a689fc6e59055001f59fc79a024bd14aca4a`; sostituire soltanto i commit delle immagini con i nuovi pin feature. Nuova directory esclusiva `/etc/ouf/deploy-snapshots/consultation-human-read-20261002-1153`. Lo staging costruisce due immagini e salva ricevute private; nessun container nuovo, switch, cambio route o source run. Lo script confronta lo stato live e le route prima/dopo. In caso di directory già presente o esito incerto, riconciliare le ricevute prima di ripetere.

Dopo STAGE PASS: preparare tre candidati STOPPED con Gateway c14d3f e `--replace-existing`, precedente pin Gateway `e8ef4b72093f4138d0efe78e9947ddfc4b471e27`, preservando esattamente ownership delle sole due route di consultazione e riusando la chiave owner esistente. Quindi piano/rilascio con backup verificati e denial/readiness; infine prova positiva HUMAN search/get con riferimento esatto tramite MCP pubblico. Nessun rilascio di Onboarding/Ingestion/UDP. Le vecchie immagini staged1568/e64 non sono le candidate per questo contratto; conservarle senza applicarle.

Restano aperti consultazione HUMAN positiva e gli altri gate PET/end-to-end già elencati. Cinema/Teatri e test manuali acquisiti rimangono congelati; nessun replay del percorso business.


### 2026-10-02 11:56 Europe/Rome — Immagini HUMAN consultation staged, preparazione prossima

Ricevuta operatore: `CONSULTATION_STAGE=PASS LIVE_UNCHANGED=true ROUTES_UNCHANGED=true NO_SWITCH=true NO_SOURCE_RUN=true PRIVATE_ROOT=/etc/ouf/deploy-snapshots/consultation-human-read-20261002-1153`.
- Semantic commit `025a542bfe6c76d8c45ee5af668b7cb7bb0de0d6`, image `sha256:809462b5abf7ce94e045061c1d104995ad5dfb866cbfbaef8ab105c0e443451f`, tag `ouf-semantic:consultation-025a542bfe6c`.
- MCP commit `98e0c7a03d3be38458282250c71f678b9619ae62`, image `sha256:7a8d7f8652a24055f3b92f1e75a8089bceb35318a0dfe5aa3e26b9c45fe2a4b3`, tag `ouf-mcp:consultation-98e0c7a03d3b`.

L'inventario Gateway mostra ancora le due route iniziali `mcp-semantic-search` e `mcp-semantic-get`, attive, e la chiave owner in environment; il PASS dello staging certifica confronto invariato dello snapshot completo prima/dopo. La policy 38 già pubblicata resta il riferimento corrente. Questo step non ha creato candidati né modificato il runtime live.

Prossimo comando: i due helper `r4a_prepare_semantic_consultation.py` e `r4a_stage_semantic_consultation.py` al pin `9dec9601cb22a941495ed17f232692abdaca2324`, Python -B, stage-root sopra, Gateway revision `c14d3f230684e3cb42c283b52f4210d5bfff3dc7`, `--replace-existing --previous-gateway-revision e8ef4b72093f4138d0efe78e9947ddfc4b471e27`, key-env `OUF_SEMANTIC_READ_OWNER_KEY`, key-target `/run/secrets/semantic-read-owner.key`, search-id `mcp-semantic-search`, get-id `mcp-semantic-get`. La preparazione verifica ownership esatta delle due vecchie route contro il pin precedente, genera le nuove route senza applicarle e riusa la chiave esistente. Crea esclusivamente tre candidati STOPPED (Semantic/MCP dalle immagini staged, APISIX dalla stessa immagine live) con snapshot/configurazione privati.

Ricevuta attesa `CONSULTATION_PREPARE=PASS CANDIDATES=3 STOPPED=true LIVE_UNCHANGED=true ROUTES_UNCHANGED=true POLICY_UNCHANGED=true` in `.../prepared`; non ancora ricevuta. Se preparazione si interrompe, non ripetere: riconciliare prepare-receipt.json e candidati eventualmente creati. Solo dopo PASS proseguire con piano/rilascio, backup e denial/readiness, poi positivo HUMAN MCP. Nessuna approvazione o source run business, nessuna modifica Onboarding/Ingestion/UDP. Restano congelati Cinema/Teatri e aperti i gate end-to-end/PET.


### 2026-10-02 11:59 Europe/Rome — Tre candidati HUMAN consultation pronti e spenti

Ricevuta operatore: `CONSULTATION_PREPARE=PASS CANDIDATES=3 STOPPED=true LIVE_UNCHANGED=true ROUTES_UNCHANGED=true POLICY_UNCHANGED=true NO_SOURCE_RUN=true PRIVATE_ROOT=/etc/ouf/deploy-snapshots/consultation-human-read-20261002-1153/prepared`.
- `ouf-semantic-consultation-candidate`: ID `35e2ade8427d10567b8ea3cbd3be0f3ea1dc31c700017c4dbfe5b296a67e8766`; image `sha256:809462b5abf7ce94e045061c1d104995ad5dfb866cbfbaef8ab105c0e443451f`.
- `ouf-mcp-consultation-candidate`: ID `75065eef6aaa18bf27d35f4f587110f4e5317d4b4adab9965b9aaa38486c88ff`; image `sha256:7a8d7f8652a24055f3b92f1e75a8089bceb35318a0dfe5aa3e26b9c45fe2a4b3`.
- `ouf-apisix-consultation-candidate`: ID `dcbe26bed97dd5c7ac8a131ec2badf77b0291c2ef32907be639bfa09c36596d9`; image `sha256:84e6b5e787e9f889ebff88161cb9a16599bafcffa236c6b54c7f779a0655940d`, stessa immagine APISIX live.

Questo PASS conclude la preparazione con verifica ownership delle sole due route esistenti e riuso della chiave owner. I tre candidati restano STOPPED; il live è ancora la release iniziale Semantic8985/MCP8476. La policy 38 non è modificata. Non ripetere prepare.

Prossimo comando operatore: scaricare i tre helper stage/prepare/release al pin `9dec9601cb22a941495ed17f232692abdaca2324`; eseguire `r4a_release_semantic_consultation.py plan` e, soltanto se exit status 0, `apply`, Python -B. Parametri: stage-root `/etc/ouf/deploy-snapshots/consultation-human-read-20261002-1153`, postgres-container `ouf-postgres`, semantic-origin `http://127.0.0.1:8080`, mcp-origin `http://127.0.0.1:8080`, gateway-origin `http://127.0.0.1:9080`; le origini sono raggiunte nei namespace dei rispettivi container.

Il piano ricontrolla live/candidati/route/chiave/config, readiness e migration history. Apply comporta una breve interruzione di MCP/Semantic/Gateway per switch e dump privati dei DB Semantic/MCP, con TOC verificata; non è una prova di restore. Conserva i container correnti per recupero, aggiorna soltanto `mcp-semantic-search` e `mcp-semantic-get` e verifica readiness, denial e history invariata. Nessun nuovo software APISIX, nessuna policy publication né source run; Onboarding/Ingestion/UDP invariati. Recupero automatico previsto solo se il rilascio fallisce; i nomi rollback, su PASS, indicano container conservati e non un rollback eseguito.

Esito richiesto: `CONSULTATION_RELEASE=PASS CONTAINERS=3 UPDATED_ROUTES=2 NEW_ROUTES=0 MIGRATION_HISTORY_UNCHANGED=true POLICY_PUBLICATION_NOT_CALLED=true NO_SOURCE_RUN=true POSITIVE_HUMAN_NOT_PROVEN=true`, con ricevuta privata `.../prepared/release-receipt.json`. Non ancora ricevuto. Interruzioni/esiti incerti richiedono riconciliazione, non nuova apply cieca. Dopo release PASS va eseguita la prova positiva HUMAN MCP search/get sul riferimento esatto già pubblicato. Restano congelati i test Cinema/Teatri e aperti tutti gli altri gate PET/end-to-end.


### 2026-10-02 12:01 Europe/Rome — Rilascio HUMAN consultation PASS; positivo MCP prossimo

Ricevuta operatore: plan PASS, apply PASS, backup Semantic e MCP PASS con TOC_VERIFIED=true/PRIVATE=true; readiness e denial PASS. Release `PASS CONTAINERS=3 UPDATED_ROUTES=2 NEW_ROUTES=0 MIGRATION_HISTORY_UNCHANGED=true POLICY_PUBLICATION_NOT_CALLED=true NO_SOURCE_RUN=true POSITIVE_HUMAN_NOT_PROVEN=true`. Ricevuta privata `/etc/ouf/deploy-snapshots/consultation-human-read-20261002-1153/prepared/release-receipt.json`.

Questo checkpoint supera lo stato cronologico «candidati spenti / release non ricevuta». Sono attivi i candidati preparati: Semantic `025a542bfe6c76d8c45ee5af668b7cb7bb0de0d6` (image809462b5), MCP `98e0c7a03d3be38458282250c71f678b9619ae62` (image7a8d7f86), APISIX stessa image84e6b5e7, due route di consultazione compilate da Gateway `c14d3f230684e3cb42c283b52f4210d5bfff3dc7`. Le route estranee alla consultazione sono preservate; nessuna migration nuova e nessun software Onboarding/Ingestion/UDP modificato. La policy corrente resta `ouf-lab-authorization:38`.

Container della release precedente conservati:
- `ouf-apisix-consultation-rollback-a076e563ab55`
- `ouf-mcp-consultation-rollback-e3e4d3e5ec5e`
- `ouf-semantic-consultation-rollback-e32dd8c43b7b`

Non è stato eseguito un rollback su questo PASS. Restano conservati anche i container originari della prima release, senza cancellazione. TOC del backup verificata non equivale a prova di restore.

Prossimo passo: prova positiva READ ONLY via MCP pubblico con `r4a_probe_semantic_human_mcp.py` e dipendenza `r4a_admin_permission_proposal.py`, entrambi pinned `9dec9601cb22a941495ed17f232692abdaca2324`. Esecuzione Python -B senza sudo, issuer `https://auth.ouf-lab.it/realms/ouf`, mcp-url `https://api.ouf-lab.it/mcp`, client `ouf-human-admin`, subject `b93d8cf6-cd14-4ee6-91d7-84cd76c4f500`, tenant `ouf-lab`, audience `ouf-api-gateway`, query `Cinema` sui dati già esistenti. Un login Device Flow HUMAN; tools/list, search limit1, get sul riferimento semanticId/revisionId/publicationSetId esatto restituito dalla ricerca. Token solo in memoria, nessun bearer o payload semantico stampato. Nessuna nuova source, onboarding, mapping, pubblicazione, ingestion, retry o materializzazione. Scope richiesti rimangono mcp.connect/ouf.semantic.search/ouf.semantic.read; tool semantic.get usa capability HUMAN distinta già pubblicata.

Esito richiesto `SEMANTIC_HUMAN_MCP=PASS READ_ONLY=true NO_SOURCE_RUN=true NO_SECRETS_PRINTED=true`, preceduto da discovery entrambe true, SEARCH PASS e GET PASS EXACT_REFERENCE_MATCH=true. Non ancora dimostrato. Ricerca vuota prova search ma lascia get non provato; non creare fixture di produzione per far passare il probe. Il tool registry di questa chat continua a non esporre semantic.search/get alla rilettura dei metadati: distinguere cache del chatbot e discovery effettiva del server. Aggiornamento/riconnessione del connector e prova tramite chatbot restano successivi alla verifica del MCP pubblico.

Consultazione HUMAN positiva, disponibilità per i chatbot e tutti gli altri gate PET/end-to-end restano aperti nel rispettivo ambito. Cinema/Teatri storici preservati senza replay.


### 2026-10-02 12:06 Europe/Rome — Positivo HUMAN ancora bloccato; diagnosi senza modifica live

Ricevuta operatore: token context PASS; discovery semantic.search=true / semantic.get=true; `SEMANTIC_HUMAN_MCP=BLOCKED REASON=MCP_TOOL_DENIED`. Il probe si arresta al primo tools/call (search) e non prova get. Policy 38 e release appena applicata restano invariati; nessun rollback o nuovo rilascio richiesto da questo esito.

Il probe precedente traduceva ogni isError in MCP_TOOL_DENIED: questo testo non dimostra da solo un diniego di autorizzazione. Il probe diagnostico conserva il comportamento READ ONLY, aggiunge tool e correlationId generato alle richieste e mostra soltanto codice appartenente a una allowlist fissa e stato HTTP numerico, supportando campi Go Code/Status e JSON code/status. Mai stampa detail/title/message arbitrari, token o payload completi. Test HUMAN aggiornati 18 PASS, inclusi redazione di contenuto ostile, stato HTTP e correlazione/restauro del builder header. Un ulteriore login Device Flow serve solo a osservare il fallimento corrente senza cambi runtime.

Audit del sorgente live MCP98e0: il ramo governed semantic.* invoca con MaxResultBytes=1048576, mentre entrambi gli schemi Gateway c14d3f ammettono massimo262144. Questa incoerenza di contratto è verificata nel codice e può produrre HTTP400 di request-validation; la causa dell'ultimo rifiuto live resta da confermare col probe diagnostico. La CI precedente aveva mock Gateway senza validazione completa degli envelope semantici.

Correzione MCP preparata sul solo ramo semantic.*: budget massimo100 oggetti /262144 byte; gli altri tool conservano i propri limiti. Commit `394b4b1540b575564f0ba58541df9d7efc59fb87` su `codex/file-to-udp-semantic-mcp`, NON LIVE. I due test reali di sessione MCP search/get ora verificano il budget dell'envelope e una nuova CI pinned Gateway c14d3f valida l'intero envelope effettivamente emesso contro i veri schemi JSON, oltre alle pipeline preesistenti. CI ancora da leggere prima di qualunque proposta di staging. Nessuna modifica Semantic/Gateway/Authorization/Onboarding/Ingestion/UDP necessaria per correggere questo limite.

Prossimo comando operatore: eseguire il probe diagnostico aggiornato e la dipendenza device client allo stesso pin documentale della presente modifica, stessi endpoint/client/subject/tenant/audience/query Cinema già usati. Richiesta evidenza SEMANTIC_PROBE_REQUEST e SEMANTIC_TOOL_ERROR oltre all'esito finale. Non ripubblicare policy, non ripetere onboarding/ingestion e non distribuire immagini prima di aver letto il codice/stato del rifiuto e la CI della correzione. Tutti i gate restano aperti come prima; i test business acquisiti rimangono congelati.


### 2026-10-02 12:34 Europe/Rome — HTTP400 osservato; byte fix MCP pronto, solo staging prossimo

Ricevuta operatore del probe diagnostico: token context PASS, discovery search/get true; richiesta `semantic.search` correlationId `097c211a-1b66-41bc-993f-fde56f1625c0`; `SEMANTIC_TOOL_ERROR={"code":"UNCLASSIFIED_TOOL_ERROR","httpStatus":400,"tool":"semantic.search"}`; finale BLOCKED/MCP_TOOL_DENIED. Get non invocato. HTTP400 è coerente con envelope fuori schema, non prova da solo un diniego di policy né individua univocamente quale validatore lo abbia emesso.

Correzione MCP `394b4b1540b575564f0ba58541df9d7efc59fb87`: CI riletta 3/3 SUCCESS (common-vectors, semantic-envelope e protocol-and-lifecycle). La prova semantic-envelope valida gli envelope effettivamente prodotti da sessioni MCP search/get contro gli schemi Gateway c14d3f. Budget ridotto da1048576 a262144 byte per semantic.*; altri tool invariati. Il codice dei soli kernel.go e semantic_dispatch_test.go è stato confrontato col genitore98e0: soltanto delta intenzionale. Nessuna nuova modifica a Semantic/Gateway/Authorization, nessun motivo di ripubblicare policy38.

Nuovo helper di coordinamento `scripts/r4a_stage_semantic_mcp_byte_fix.py` riusa i preesistenti helper MCP snapshot/preflight/prepare/rollout e managed_upload_mode dal source pin394b. Non introduce un altro launcher: preserva esattamente la modalità upload corrente e confronta l'intero environment, mount, alias/configurazione tramite gli helper collaudati. Costruisce unicamente l'immagine MCP, snapshot privato e file di candidato avvio; non crea/ferma container. Tre test locali PASS per preservazione dei quattro modi, rifiuto di modalità/duplicati e guard prima delle mutazioni. Workflow staging dedicato con helper MCP pinned394b; CI del nuovo wrapper ancora da leggere.

Prossimo passo operatore: stage-root esclusiva `/etc/ouf/deploy-snapshots/semantic-mcp-byte-fix-20261002-1234`, commit394b, expected-live-revision `98e0c7a03d3be38458282250c71f678b9619ae62`, Python -B come root. Helper richiede e confronta prima/dopo anche Semantic/APISIX/Onboarding/Ingestion/UDP. Registra stage-receipt.json con pin, imageID, snapshot, directory candidato, opzioni upload esatte e nome di conservazione previsto; nessun valore sensibile stampato. Build log e snapshot restano privati. Directory già presente o errore richiede riconciliazione, non ripetizione cieca.

Esito richiesto `MCP_BYTE_FIX_STAGE=PASS LIVE_UNCHANGED=true ENVIRONMENT_UNCHANGED=true NO_CONTAINERS_CREATED=true NO_SOURCE_RUN=true`, non ancora ricevuto. Dopo staging verrà predisposto il piano di switch del solo MCP, mantenendo i servizi restanti e le route già rilasciate. Consultazione HUMAN positiva rimane OPEN; nessun business replay Cinema/Teatri e tutti gli altri gate PET/end-to-end preservati.


### 2026-10-02 12:47 Europe/Rome — MCP byte fix staged, piano/switch MCP successivo

Ricevuta operatore: `MCP_BYTE_FIX_STAGE=PASS LIVE_UNCHANGED=true ENVIRONMENT_UNCHANGED=true NO_CONTAINERS_CREATED=true NO_SOURCE_RUN=true PRIVATE_ROOT=/etc/ouf/deploy-snapshots/semantic-mcp-byte-fix-20261002-1234`. Nuova image `sha256:99a158f780243b3fa05199bed9db01197be8ae60ae1e75ad5432964509422872`, tag `ouf-mcp:semantic-byte-fix-394b4b1540b5`, commit `394b4b1540b575564f0ba58541df9d7efc59fb87`. Preflight MCP PASS: live98e0/image7a8d7f86, utente10005:10005, networkouf-backend, restartunless-stopped, mount secret read-only2, Binds0, nessuna porta/resource limit/healthcheck inattesa. Tutte le variabili, compresa modalità upload/picker, preservate. Non ripetere stage.

CI correzione MCP 3/3 SUCCESS; nuovo staging wrapper 4ce10d56 ha check staging SUCCESS (anche sulla PR) e test locali di preservazione dei modi PASS. Questo PASS non ha distribuito la nuova immagine: Semantic025a/MCP98e0 e Gatewayc14d3f restano live con policy38.

Nuovo coordinatore `r4a_rollout_semantic_mcp_byte_fix.py`, modes plan/apply, delega il launcher al preesistente `scripts/r4a_rollout_mcp_runtime.py` del source MCP394b già staged. Carica dal receipt privato snapshot, opzioni upload e directory candidato senza chiedere né stampare valori sensibili. Verifica clean source/pin, image label, oldId e fingerprint dei sei servizi, environment esatto e bindings tramite native original_and_args. Legge le route complete APISIX e history MCP prima/dopo. Plan richiama native dry-run; apply crea checkpoint esclusivo, backup logico MCP privato con TOC verificata, chiama native apply e verifica image/revision/readiness204, history e altri servizi/route invariati. Usa i helper backup/readiness/database/history collaudati della release consultation. Nessun nuovo launcher né rigenerazione route/policy.

Parametri prossimo comando: stage-root sopra, consultation-stage-root `/etc/ouf/deploy-snapshots/consultation-human-read-20261002-1153`, postgres-containerouf-postgres, Python-B root, plan e apply soltanto dopo exitstatus0 del piano. Prevista breve interruzione del solo MCP; container originale conservato sotto `ouf-mcp-r4a-rollback-75065eef6aaa`. Lo script native provvede al recupero del container se il suo switch/readiness fallisce. Il coordinatore registra qualsiasi errore post-switch come RECONCILIATION_REQUIRED; non tenta restore automatico del DB, non ripete apply, non considera un esito incerto PASS. Nuova ricevuta `rollout-byte-fix-receipt.json`; backup `mcp-before-byte-fix.dump`, privati nella stage-root.

Test del coordinatore 3 PASS: piano senza apply/rollback, stesse opzioni fra plan/apply, assenza di picker/origin inventati per altri modi; workflow staging esteso ai nuovi path/test e alle dipendenze. Esito richiesto `MCP_BYTE_FIX_RELEASE=PASS CONTAINERS=1 ENVIRONMENT_UNCHANGED=true OTHER_SERVICES_UNCHANGED=true ROUTES_UNCHANGED=true MIGRATION_HISTORY_UNCHANGED=true NO_POLICY_PUBLICATION=true NO_SOURCE_RUN=true POSITIVE_HUMAN_NOT_PROVEN=true`; non ancora ricevuto. Dopo PASS ripetere la sola consultazione HUMAN diagnostica. Nessun business replay, gli altri gate end-to-end/PET restano aperti.


### 2026-10-02 13:04 Europe/Rome — MCP-only byte fix live e consultazione positiva dal chatbot

Ricevuta operatore: piano native e coordinatore PASS; backup MCP PASS TOC_VERIFIED=true/PRIVATE=true; native apply STAGED=true con originale conservato `ouf-mcp-r4a-rollback-75065eef6aaa`. Finale `MCP_BYTE_FIX_RELEASE=PASS CONTAINERS=1 ENVIRONMENT_UNCHANGED=true OTHER_SERVICES_UNCHANGED=true ROUTES_UNCHANGED=true MIGRATION_HISTORY_UNCHANGED=true NO_POLICY_PUBLICATION=true NO_SOURCE_RUN=true POSITIVE_HUMAN_NOT_PROVEN=true`. Ricevuta privata `/etc/ouf/deploy-snapshots/semantic-mcp-byte-fix-20261002-1234/rollout-byte-fix-receipt.json`. MCP ora commit `394b4b1540b575564f0ba58541df9d7efc59fb87`, image `sha256:99a158f780243b3fa05199bed9db01197be8ae60ae1e75ad5432964509422872`; altri servizi, route e policy38 invariati. La dicitura NOT_PROVEN è corretta per il solo script di rilascio; l'evidenza positiva successiva è qui sotto.

Tool registry della chat aggiornato: semantic.search/get entrambi disponibili. Il coordinatore ha eseguito direttamente attraverso il connector OUF di ChatGPT, account esplicito `ouf-admin` / link `link_6aafef96b4148191b767e9af7b756a07`:
1. semantic.search(q=Cinema,limit=1) SUCCESS/isError=false, una ontologia ACTIVE esistente.
2. semantic.get sul riferimento esatto restituito dalla ricerca SUCCESS/isError=false e corrispondenza verificata di semanticId/revisionId/publicationSetId.

Riferimento letto, senza nuove pubblicazioni: semanticId `https://api.ouf-lab.it/semantic/cinema`, artifactId `5ae731cc-e4c5-43a3-aa5e-a7576adbd3a1`, revisionId `51706bed-81e4-4306-aca1-70119821727d`, publicationSetId `f92a2e17-30c9-456f-bb12-63afa84f41e6`, version1.0.0, contentHash `78a39fc30dab8bf221bc9eb8c2567bb2abef57e72ba1e4e29a87a23db4142391`, publicationChecksum `a711d0428f1cbe24c73cbf0fa5cabfcb52f85df774e7238d884e7f83f41b84e9`. dependencies=[] / dependencies_partial=false. Non è stato necessario chiedere un altro login terminale. È ora dimostrata la consultazione positiva sul percorso chatbot ChatGPT → MCP → Gateway → Semantic con quell'account e quel riferimento. La causa del precedente HTTP400 è coerente col limite corretto e il risultato dopo correzione; nessuna modifica di autorizzazione intervenuta fra questi due probe.

Limite distinto: l'artefatto Cinema restituisce label={},description={},definition={}. Non inventare definizioni o considerare metadata semanticamente completi solo perché il trasporto passa. Rimangono aperti generalizzazione del contenuto semantico/discovery, secondo chatbot e uso per mapping. Questo positivo non accetta l'intera filiera acquisizione → UDP.

Avviato il prossimo gate soltanto in lettura: source.file.preview sul Teatri già congelato, asset `6609b245-86ed-4315-8ce0-73f2a8555bf3`, profile `7984c39c-7396-4248-ab0a-f2efc390b49c`, version1, PASS via lo stesso connector/account; CSV13righe20colonne, UTF8, delimitatore; e headerRow1. Profilo esistente letto, nessun nuovo profiling/job. Colonne: nome_teatro,tipologia,toponimo,nome_indirizzo,civico,cap,citta,provincia,latitudine,longitudine,sistema_riferimento,precisione_coordinate,capienza_posti,spettacoli_stagione,stagione_riferimento,note,fonte_indirizzo,fonte_coordinate,fonte_altri_dati,data_verifica. Sample redatto, proposalStatus=PENDING_HUMAN_REVIEW. IdentityProposal esistente propone NATIVE_KEY/nome_teatro: rimane una proposta statistica, NON adozione di identità canonica/durevole. RecordModel ONE_ROW_ONE_SOURCE_OBJECT non risolve il matching UDP fra fonti.

semantic.search(q=Teatro,limit=5) SUCCESS con []: questa query non restituisce riferimenti, non dimostra che tutti i concetti pertinenti siano assenti nel registro. Prossimo lavoro: verificare catalogo/definizioni e strumenti di discovery esistenti/PR aperte prima di predisporre mapping Teatri e review THS. Non usare l'ontologia Cinema come mapping Teatro per sola somiglianza e non creare nuove source/DRAFT/run fino alla proposta semanticamente verificabile. Sono preservati i gate e le fixture business ereditate; nessun replay Cinema/Teatri/ingestion/UDP eseguito.


## Checkpoint 2026-10-02 — RDF evidence for assisted mapping (candidate, not deployed)

- Direct ouf-admin MCP CLASS searches for Cinema, Teatro and Theatre returned empty arrays. This is query evidence, not a complete catalogue census.
- Source audit: `InterchangeService.importDraft` persists imported bytes/hash/statement count in `revision_interchange_snapshot` and creates an artifact revision without populating label/description/definition JSON. Exact consultation previously read only those JSON fields. The published Cinema Turtle already includes Cinema → schema:MovieTheater, nome → schema:name, indirizzo → schema:address, labels and domain/range. Do not recreate the ontology, rewrite immutable revisions, or replay Cinema/Teatri ingestion to recover this existing content.
- Semantic candidate `e7bc5190f9e6afbbc4cf3c90d5d4970afbfad14b` adds optional `rdf_snapshot` to exact published reads. Typed asserted RDF subject/predicate/object nodes preserve language/datatype, named terms and blank-node restrictions. Stored byte hash and statement count must match. Up to 1000 statements with explicit partial flag; existing entire response byte budget remains fail-closed. No inference, remote JSON-LD context/import retrieval, lifecycle write, migration or policy change. Existing JSON fields remain separate and unchanged; contained terms share the parent revision/publication scope and are not independently registered CLASS artifacts.
- CI at this exact commit: all 6 checks SUCCESS, including Java21/PostgreSQL17, actual Lua→Java→PostgreSQL, pinned SDK consumer, authorization contract, recovery scripts and container smoke. Added RDF tests cover labels/inheritance/domain/range/restrictions, RDF/XML, local/remote JSON-LD, hash/count mismatch, bounded partial graphs, native metadata preservation and historical pin isolation. Local Java runtime unavailable; Java execution evidence is CI.
- PR reconciliation: Onboarding #39 at `6340d5bf120e09b47c32177656e2c377a4c03640` is OPEN and already installed; #38 is its earlier identity gate work. Reuse that integration. MCP #48 identity review package remains OPEN and is distinct from semantic mapping. Native Semantic discovery/import/adoption APIs already exist; their governed channel-neutral MCP projections and provider acceptance remain OPEN. Do not replace them with chatbot web scraping or invent ontology terms from field names.
- New operator helper `scripts/r4a_stage_semantic_rdf_read.py` stages ONLY the exact Semantic candidate; clones pinned source, private build log/runtime snapshot, preserves all six live owners and all Gateway routes, retains exact environment/mount launch contract through existing helpers. No containers created or switched. Five local staging tests PASS (success, MCP drift, Semantic drift, route drift, private build failure). Run with Python -B. Staging helper is not release acceptance and does not claim RDF positive live proof.
- Live baseline remains Semantic 025a542b, MCP 394b4b15, Gateway c14d3f23 routes, policy ouf-lab-authorization:38. MCP transport consultation and Teatri existing-profile preview remain positively proven; candidate RDF projection is NOT live yet.
- Next operator step: stage one Semantic image, then prepare/review the one-container release with exact runtime/secret mounts, packaged migration equality, private DB backup/history, readiness/denial and preserved routes/other owners. Old review-card rollout assumes one mount and MUST NOT be reused unmodified against the current two-mount Semantic runtime. No publication, privileged actor broadening, fixture replay or new source job is part of this step.
- Teatri mapping remains OPEN: obtain adequate official class/properties/vocabularies through internal graph evidence or governed discovery; review inheritance/generalization and constraints, field inclusion/access labels, source identity versus canonical identity and per-field transformations in THS. Do not adopt Cinema for Teatri merely by similarity, and do not promote the statistical nome_teatro key proposal to canonical identity.
- File path retains immediate ingestion/dedup after approved onboarding; API path retains endpoint/credentials THS → extraction-profile THS → common mapping/review → scheduler configuration → ingestion/dedup at scheduled times. Overall pipeline acceptance, second chatbot, semantic discovery/generalization, THS activation and remaining PET gates stay OPEN.

Review checkpoint: RDF delta is draft PR #27, based on the exact live 025a542b baseline: one commit, six changed files. No merge into main or release-history reconciliation has occurred. Operator staging helpers are pinned at fa63c6bc72850a416b7f95ba172b8aca54a3f571.


## Checkpoint 2026-10-02 — Semantic RDF image staged; one-container release prepared

Operator staging PASS at `/etc/ouf/deploy-snapshots/semantic-rdf-read-20261002-1130`: candidate Semantic commit `e7bc5190f9e6afbbc4cf3c90d5d4970afbfad14b`, image `sha256:f6525f2512c72a600ebcbc7060d55355d86e0627487b655e7c5c6288a0be7fc6`, tag `ouf-semantic:rdf-read-e7bc5190f9e6`. Live containers/routes unchanged, no containers created, no switch/source run. This is staging evidence, not positive live RDF consultation acceptance.

New `scripts/r4a_release_semantic_rdf_read.py` reuses existing consultation launch/match, private checkpoint, migration history/backup, switch/restore and readiness/denial helpers. Modes: prepare (one stopped Semantic candidate; preserves exact mounts/environment/network aliases; compares packaged Flyway bytes), plan (rechecks runtime/source/image/candidate/migrations/history/routes), apply (private DB dump + TOC verification, exclusive lock and receipt, Semantic-only switch, readiness and forged/anonymous denial probes, history equality and all other owner/route equality, restart policy restoration). Original Semantic container is retained stopped on success; no rollback is executed on PASS. Post-switch failure restores that predecessor without restoring a database, then leaves explicit reconciliation-required state. Do not blindly rerun after a failed/incomplete attempt. No policy publication, new key, route mutation, ingestion replay or source job occurs.

Eight new local release tests PASS: backup-before-switch ordering, successful original retention, readiness failure/restoration, backup failure without switch, migration history drift before/after switch, packaged migration byte comparison, other-owner/route drift, existing multi-mount launch verification and four denial probes. Ten existing coordinated-release tests also PASS. The consultation-deploy CI workflow now includes both RDF stage/release test modules (13 tests). The candidate software's six CI checks remain green at its unchanged pinned commit. Release script evidence does not prove RDF HUMAN positive; after operator release PASS use the connected ouf-admin exact Cinema semantic.get to verify the newly returned snapshot/hash/statements, then resume Teatri semantic mapping/discovery. Existing file immediate-ingestion and API scheduler distinctions and all broader PET acceptance gates remain unchanged.


## Checkpoint 2026-10-02 — RDF release rolled back; operator probe corrected

Operator evidence: prepare PASS (one stopped candidate, two mounts, environment and packaged migrations identical), plan PASS twice, private Semantic DB backup/TOC PASS, then `FORGED_DIRECT_REQUEST_NOT_DENIED` and `SEMANTIC_RDF_READ_ORIGINAL_RESTORED=PASS`. The RDF release is BLOCKED, not accepted. Failed attempt receipt remains at `/etc/ouf/deploy-snapshots/semantic-rdf-read-20261002-1130/rdf-release-receipt.json`. Do not reapply or overwrite that attempt.

Root cause in the new operator script: the direct-owner negative probe used the Gateway public URI `/internal/capabilities/v1/execute/semantic/{search,get}` against the Semantic container, instead of the existing owner URI `/api/internal/v1/semantic/consultation/{search,get}`. It also omitted the explicitly forged receipt and JSON header used by the proven coordinated-release helper. The first mocked test checked the number of HTTP calls but failed to assert their route/header. This is an operator-script error; the unexpected status was not printed in that attempt and must not be invented or interpreted as evidence that an unauthenticated request executed. No change to software image/policy/security acceptance status set is warranted on this evidence.

Correction: use the established owner URI plus Content-Type application/json and X-OUF-Semantic-Read-Receipt invalid; retain strict 401/403 acceptance for both owner and Gateway. Print only boundary/tool/numeric status for future probes. Tests now assert exact owner and Gateway paths/headers and reject HTTP404 as an authorization denial. Added controlled `reconcile` mode: verify predecessor ID/name/config/restart policy/running state, failed candidate retained stopped under its expected failure name, PostgreSQL ID/migration-history equality, all other live owners/routes unchanged, readiness and corrected denial probes. Preserve the entire failed attempt and create an exclusive new retry root with a verified current predecessor snapshot; reuse the same clean pinned source and image without rebuilding. The only baseline adjustment is the predecessor restart timestamp established during automatic restoration. Existing state/receipt and failed container are never erased.

Direct ChatGPT ouf-admin semantic.get after restoration SUCCESS: same Cinema exact semantic/revision/publication pins, existing metadata and no rdf_snapshot, consistent with predecessor functionality restored. This is positive baseline consultation evidence, not positive RDF acceptance. Candidate remains e7bc5190f9e6afbbc4cf3c90d5d4970afbfad14b / sha256:f6525f2512c72a600ebcbc7060d55355d86e0627487b655e7c5c6288a0be7fc6; original Semantic 025a542b remains live as reported by rollback helper, pending exact operator reconciliation. MCP/Gateway/policy38 untouched by this release operation.

Local verification: 17 combined RDF stage/release tests PASS, plus 10 existing coordinated-release tests PASS. New reconciliation tests cover preservation of failed receipt, permitted restart baseline refresh and blocks on original image/config or migration drift. The next operator invocation must reconcile first into `/etc/ouf/deploy-snapshots/semantic-rdf-read-20261002-1130-retry1`; only a reconciliation PASS permits prepare/plan/apply there. After release PASS, verify live RDF statements/hash through connected ouf-admin exact semantic.get. Mapping/THS/discovery/scheduler and all full-pipeline acceptance gates remain OPEN.


## Checkpoint 2026-10-02 — Semantic RDF live release and positive HUMAN MCP acceptance

Operator reconciliation PASS into `/etc/ouf/deploy-snapshots/semantic-rdf-read-20261002-1130-retry1`: exact original ID/config verified, PostgreSQL migration history unchanged, failed-attempt artifacts retained, no rebuild/no switch in reconciliation. Prepare PASS: one stopped candidate, two mounts, same environment and packaged migrations. Plan PASS twice; private Semantic DB backup and TOC verification PASS (not a restore-to-database test). Release PASS: exactly one Semantic container switched, environment and all other services/routes unchanged, migration history unchanged, no policy publication or source run. Retained predecessor: `ouf-semantic-rdf-read-rollback-35e2ade8427d`. Private release receipt: retry root `rdf-release-receipt.json`. Corrected negative probes PASS both before/after switch: owner search/get HTTP403; Gateway search/get HTTP401.

Live Semantic is now `e7bc5190f9e6afbbc4cf3c90d5d4970afbfad14b`, image `sha256:f6525f2512c72a600ebcbc7060d55355d86e0627487b655e7c5c6288a0be7fc6`. MCP remains 394b4b1540b575564f0ba58541df9d7efc59fb87; Gateway routes remain c14d3f23-derived; policy remains ouf-lab-authorization:38. Neither the original failed attempt receipt nor its stopped failed candidate was deleted. No fixture was replayed.

Positive direct ChatGPT MCP evidence after release: connected `ouf-admin` semantic.get SUCCESS for semanticId `https://api.ouf-lab.it/semantic/cinema`, revision `51706bed-81e4-4306-aca1-70119821727d`, publication set `f92a2e17-30c9-456f-bb12-63afa84f41e6`. Exact returned pins verified. New rdf_snapshot contains 17 typed asserted triples, statement_count=17, partial=false, text/turtle, raw RDF SHA256 `4340986102db6e47345dd8157734d9db83b928edd94485f1b9a5b9e81c497a2e`; matches the tracked imported Cinema Turtle bytes. JSON metadata content_hash remains separately `78a39fc30dab8bf221bc9eb8c2567bb2abef57e72ba1e4e29a87a23db4142391`: do not confuse revision metadata hash with raw RDF bytes hash.

Returned asserted facts include Cinema owl:Class with Italian label and rdfs:subClassOf schema:MovieTheater; nome/indirizzo owl:DatatypeProperty with Italian labels, domain Cinema, range xsd:string, subPropertyOf schema:name/schema:address; original ontology label/comment and source profile provenance. Existing JSON label/description/definition remain empty and unchanged. This closes the positive HUMAN consultation gate for existing imported RDF via this ChatGPT→MCP→Gateway→Semantic path, superseding the operator-script-only RDF_POSITIVE_HUMAN_NOT_PROVEN flag. It does not establish a second chatbot, complete effective imported-ontology closure, inference, external MovieTheater parent definitions, or adequate Teatri mapping semantics. partial=false applies only to all 17 statements in this exact stored snapshot.

Next work resumes Teatri mapping without replay/reprofile/new ingestion job: internal artifact search plus graph content inspection, then reuse the existing governed Semantic discovery/provider/adoption APIs when no adequate official class/properties/vocabularies exist. The Cinema→MovieTheater relationship must not classify a theatre by analogy. Review/generalization, source versus canonical identity, field inclusion/access classifications, transforms, THS mapping approval/activation, immediate file ingestion and scheduled API ingestion/dedup remain OPEN along with all previously recorded PET gates. PR27 remains a six-file draft delta against the prior deployed Semantic baseline; PR26 holds operator/procedural coordination. No main merge or release-history reconciliation is implied.


## Checkpoint 2026-10-02 — Discovery readiness audit and Teatri mapping continuation

User authorizes autonomous continuation until a concrete human/server dependency arises. Existing native discovery/provider/adoption functions are present and must be reused. Current open-PR inventory confirms Semantic PR27 (RDF live delta) and PR26 (coordination/operators); no separate open Semantic discovery implementation PR was found in that inventory. This is not proof that every historical branch is reconciled.

Pinned source audit (live e7bc5190): application.yml defaults schema-gov provider disabled, gateway base https://gateway.invalid, southbound search /semantic-providers/schema-gov/sparql and fetch /semantic-providers/schema-gov/fetch; discovery worker enabled by default. These are source defaults, not an observed effective runtime configuration. SchemaGovProvider already emits bounded structured SPARQL and routes every search/fetch through the configured same-origin Gateway client. Do not substitute direct chatbot SPARQL/web acquisition or invent an upstream endpoint. Official catalogue documentation https://schema.gov.it/en/sparql-tool/ describes classes/properties/vocabularies in the national semantic graph; it does not establish the OUF Gateway binding or effective installed provider connectivity.

Further implementation gaps found before exposing discovery to MCP: disabled SchemaGovProvider returns an empty candidate list; DiscoveryService.executeOne counts that call as successful and even treats an empty provider list as success. Consequently SUCCEEDED with no candidates is not sufficient proof a real external provider was consulted. Candidate normalized_payload is currently stored as {}; native candidates projection supplies metadata/reasons/gaps but not full candidate definitions. Formal adoption stores RDF in immutable_semantic_snapshot/external_semantic_origin, whereas the new exact imported RDF projection reads revision_interchange_snapshot: do not substitute latest origin snapshot for an exact adopted revision. Existing governed adoption tests explicitly patch/version/validate/publish a draft and remain relevant; future changes must preserve those tested semantics and add exact snapshot/definition coverage. Discovery request/status/candidate MCP envelopes need dedicated operation/purpose authorization and caller ownership, idempotency, bounds and async status; the read-only consultation receipt must not be broadened into write/adoption authority. Descriptor actors/operation must be inventoried before any OAuth grant, registration or policy proposal. No approval/activation/publish tool is allowed.

New scripts/r4a_semantic_discovery_preflight.py performs a single read-only inventory of current Semantic/MCP pinned runtimes, safe effective-config indicators, actual Gateway route matching, exact registered/published ouf.semantic.discovery descriptors and grouped discovery queue/candidate counts. It prints no endpoint/credential/env values, host mount paths, raw candidates or user intent; makes no external provider request and creates no discovery/source job. Unknown Spring/JVM/command/mount overrides yield UNPROVEN rather than assuming defaults. Local 7 tests PASS covering default disabled provider, redaction, ambiguous overrides, relaxed property precedence, active route/method selection, read-only SQL and safe Gateway origin validation. ConfigurationReady is preliminary configuration evidence only: provider connectivity, HUMAN authorization and MCP binding remain explicitly unproven. Workflow adds the targeted CI test. User must run the pinned inventory on the VPS because no server execution access exists in this chat; do not make deployment/configuration choices while that evidence is absent.

Teatri proposal preparation remains source-specific and unapproved: map discovered fields into venue name/type; structured address; geometry/CRS/precision; seating capacity and seasonal activity; per-field provenance and verification date. Do not interpret data_verifica as business validFrom, declared CRS as validated geometry, seating as number of independent canonical venues, or unique source labels as a stable canonical key. Multi-hall note means row/source-object/canonical-object granularity requires explicit review. tipologia and coordinate precision require official vocabulary/value-map inspection rather than invented controlled terms. Internal searches for Teatro/Theatre CLASS currently returned empty arrays; published Cinema only establishes a MovieTheater specialization, not a generic theatre classification. Start governed lexical discovery of a theatre venue class and required properties only after provider/path/auth readiness is proved, compare appropriate generalization/constraints, then present decisions in THS. Existing asset/profile/job stay frozen, no reupload/reprofile/new ingestion job. File immediate ingestion/dedup and API scheduler-before-ingestion distinctions remain unchanged. Broader acceptance remains OPEN.


### 2026-10-02 — Discovery availability and live configuration inventory

Operator `SEMANTIC_DISCOVERY_INVENTORY=PASS` is a read-only inventory, **not discovery acceptance**. Under active policy `ouf-lab-authorization:38`, the native `ouf.semantic.discovery` descriptor is absent from registration and publication. Provider disabled, Gateway origin missing, worker enabled; queue and adopted/unexpired candidate counts are zero. No external provider call, source job, database write or policy publication occurred.

The route counts refer only to the inspected `ouf-apisix` Gateway. They do not prove that a separate southbound deployment does not exist. Before preparing provider routes, inspect the running container inventory and reconcile the PET northbound/southbound separation with the real topology. Missing configured origin currently prevents proving the binding; do not enable the provider or install routes on the northbound deployment by assumption.

Reviewable backend correction: [Semantic PR #28](https://github.com/GioNob/ouf-semantic-registry/pull/28), commit `bf35e930fb239c61ea8ceebb41e187d653a3d96a`, based exactly on deployed RDF-read commit `e7bc5190f9e6afbbc4cf3c90d5d4970afbfad14b`. New requests with no enabled provider return HTTP 503 / `SEM_DISCOVERY_NO_ENABLED_PROVIDER` before creating a job; previously queued requests fail explicitly. A real enabled provider returning no candidates still succeeds. Six availability regression cases passed on Java 21/PostgreSQL 17 (full suite 71 tests, zero failures/errors, one pre-existing skipped test). All 12 reported checks passed, including pairwise, actual Lua/Java/PostgreSQL and both container smoke checks. No live rollout is claimed.

Existing native provider/adoption implementation is being reused. Open-PR inventory found no additional dedicated external-discovery wiring PR in Semantic, Gateway or MCP; this is limited to the currently open PRs and is not a census of every historical branch. Remaining work includes owner-side request idempotency and caller-scoped asynchronous status; governed service authentication and bounded southbound search/fetch; channel-neutral MCP bindings; temporary candidate inspection; direct HUMAN adoption/review/publication; revision-pinned adopted RDF. Existing READ-only delegation must not authorize discovery commands or adoption. Internal consultation and exact published RDF remain available independently.

Live software, policy 38, Cinema/Teatri fixtures, migrations and source jobs remain unchanged. File ingestion follows approved onboarding immediately; API ingestion follows scheduler configuration and runs at scheduled times. No identity/mapping decision or ingestion replay is authorized by this discovery checkpoint.


### 2026-10-02 — Docker topology and native asynchronous discovery prerequisites

Operator running-container inventory lists exactly one APISIX (`ouf-apisix`, image prefix `84e6b5e787e9`), plus Caddy, etcd and existing owners. No separate running southbound gateway appears in that output; stopped containers and non-Docker services were not inventoried. PET distinguishes northbound/southbound deployments and requires governed service identity, TLS and default-deny egress. This is a configuration/integration gap, not a reason to rebuild already proven file ingestion or change consultation routes.

[Semantic PR #29](https://github.com/GioNob/ouf-semantic-registry/pull/29), commit `dc0980a250e5e96e6d10d791a7db78801e2c1cd6`, is stacked on availability PR #28. It adds an optional caller-scoped idempotency key, atomic unique-index protection for concurrent retries, payload-conflict rejection, actual-state replay, native GET job status and caller ownership checks for status/candidate listing. Status excludes raw provider error text and query/key/fingerprint details. Seven new regression tests passed; Java 21/PostgreSQL 17 suite: 78 tests, zero failures/errors, one existing skipped test. All 12 reported CI checks are green, including container smoke, pairwise and actual Lua/Java/PostgreSQL.

Candidate V10 is additive (nullable key hash/fingerprint and consistency/index constraints); historical migrations and rows are untouched. **Not deployed.** The migration-identical RDF rollout helper cannot release it. A migration-aware release/restore procedure remains required. Native unkeyed clients retain compatibility; the future MCP command must supply a stable key for transport retries. Caller checks currently use the native trusted subject within the configured IAM issuer; tenant/issuer-aware persistence and receipts are still required for broader delegated contexts.

New `scripts/r4a_semantic_southbound_topology.py` performs Docker reads only and prints selected owner/Gateway image IDs, revision labels, environment names, mount targets/read-only flags, port-binding counts and network names/driver/internal flags. It redacts environment values, host mount paths, addresses and credentials, detects runtime changes, and never calls a provider or writes routes. Four focused tests passed locally. Its evidence does **not** prove TLS, service authentication or host firewall/default-deny enforcement. Operator execution is the next step needed to prepare the real isolated southbound binding; no blind northbound route installation or provider enablement.

The full MCP/file/API pipeline remains open: provider service authentication/bounded search+fetch; command/read capability and owner-receipt separation; candidate RDF inspection; direct human THS adoption/review/publication; adopted revision pinning; chatbot mapping/identity review; automatic file ingestion after approved onboarding; vertical scheduler configuration followed by scheduled ingestion. Existing Cinema/Teatri fixtures, live service revisions, policy 38 and source jobs remain unchanged.


### 2026-10-02 — Installation portability requirement reaffirmed

User requires network data, endpoints, ports and domains to be installation parameters, supporting freely chosen compatible network configurations and domain names. Treat the laboratory values as explicit operator inputs/examples only. No generic installer, provider adapter, route compiler or acceptance helper may infer an installation binding from the laboratory domain, port, subnet or container name. Resolve bindings from the governed installation configuration; validate them against PET security/identity requirements; propagate them consistently across owner, Gateway, MCP, IAM and scheduler. Trusted provider destinations and fetch paths must be explicit governed allowlist bindings rather than client-selected arbitrary URLs. Installation-origin validation must not hard-code `ouf-lab.it`.

The new southbound topology helper now requires explicit `--semantic-container` and `--gateway-container` arguments; proxy, Gateway state and dedicated southbound container references are optional explicit arguments. It derives network memberships from the selected runtime and has no lab role-name defaults. Six tests passed locally, including arbitrary container/network names and invalid/ambiguous binding rejection. The helper is a Docker diagnostic, not the generic installation implementation or acceptance of TLS/egress enforcement. This portability requirement applies to the remaining release/configuration and end-to-end work; historical lab-only evidence is not a portable installation claim.


### 2026-10-02 — Proven lab topology and bounded provider request candidate

Operator `SEMANTIC_SOUTHBOUND_TOPOLOGY_INVENTORY=PASS`: Semantic `e7bc5190f9e6afbbc4cf3c90d5d4970afbfad14b` is attached to `ouf-backend`; APISIX image `84e6b5e787e9` to `ouf-backend` + `ouf-gateway-control`; both networks have Docker `internal=true`. Caddy is also attached to `ouf-edge` (`internal=false`) and publishes two bindings. No dedicated southbound container was observed. TLS, workload authentication and full default-deny egress are unproven; network flags alone do not close those acceptance gates. No container, route or provider call changed. These observed lab names are evidence only; installation names, domains, endpoint URLs, ports and networks remain explicit parameters.

[Gateway PR #56](https://github.com/GioNob/ouf-api-gateway/pull/56), commit `0dee24f1d01949b7f32281c525d74e047adab98e`, is based exactly on deployed consultation Gateway commit `c14d3f230684e3cb42c283b52f4210d5bfff3dc7`. It adds technical request validation for the six existing owner-generated bounded read-query patterns and mandatory candidate namespace bindings. Arbitrary SPARQL/update/SERVICE injection, duplicate fields, endpoint substitution, malformed encoding and oversized requests are rejected; escaped text remains data. Ten focused tests and all 12 reported CI checks passed, including existing configuration/network/owner regressions. **Not yet connected to a transport adapter or deployed.** No claim of owner-to-provider acceptance.

No candidate IRI may become an HTTP destination or implicit parser fetch. Provider endpoint host/port/path and namespace allowlists come from trusted installation bindings. The remaining adapter must send admitted reads to the registered provider, enforce DNS/TLS/redirect/media/response bounds and preserve snapshot completeness/provenance evidence. Separate isolated southbound APISIX/configuration, governed egress, service authentication, tenant-aware MCP command/read receipts and human THS adoption still need implementation and acceptance.

New `scripts/r4a_semantic_provider_iam_inventory.py` uses an existing authenticated kcadm session for GET-only, paginated workload-client and selected-scope inventory. Container, CLI path, realm and scope names are required parameters. It prints only client IDs and flags plus selected scope-existence booleans; no client secrets, credentials, token claims or session data. It does not login, alter IAM, register capabilities or publish policy. Five focused tests passed locally. Binding/credential/token-claim proof remains false. Keycloak CLI reference: https://github.com/keycloak/keycloak/blob/main/docs/documentation/server_admin/topics/admin-cli.adoc

Next operator assistance: run the IAM inventory to identify reusable service clients and existing scope definitions before proposing M2M bindings. Existing live software, policy 38, file fixtures and source jobs remain unchanged. Availability PR #28 and native job PR #29 are still candidates; V10 migration is not deployed. Full file/API-to-UDP closure is still open and the established immediate-file versus scheduled-vertical distinction remains mandatory.


### 2026-10-02 — Reuse Semantic workload identity; prepare additive IAM changes

Operator `SEMANTIC_PROVIDER_IAM_INVENTORY=PASS` in realm `ouf`: both `gateway.southbound.invoke` and `ouf.semantic.discovery` scope definitions are absent. Existing `ouf-semantic` client is enabled, confidential (`publicClient=false`) and service-account enabled. Five other workload clients are present: `ouf-ingestion`, `ouf-mcp-server`, `ouf-onboarding`, `ouf-source-onboarding`, `ouf-udp`. Do not recreate, merge, rename or rotate these clients. Mapper, audience, tenant, scope-binding and actual token-claim acceptance are not established by that inventory. Expired kcadm session was renewed by the human operator; no credentials were provided to the model.

New `scripts/r4a_prepare_semantic_provider_iam.py` composes the existing tested scope-definition, client-binding and workload-profile helpers (their bytes are unchanged and verified against the canonical GitHub parent). All IAM container/path/realm/client/audience/tenant/scope inputs are explicit parameters. Modes: plan (read-only exact actions/profile drift), apply (additive scope creation and only the provider scope DEFAULT binding to the selected existing client), verify (read-only). Discovery scope definition is prepared without assigning it to any client. No client creation, flag/mapper edits, secret retrieval, credential rotation or application-policy publication is implemented.

Apply fails before any write for an unexpected existing workload profile or an existing scope definition requiring review. Existing unrelated DEFAULT/OPTIONAL scopes are preserved. Legacy base-scope recommendations are excluded from the mutation gate because this procedure does not rewrite existing base scopes; actual SERVICE/client/mapper/account requirements are retained. The composer is retryable after partial REST failures through its underlying idempotent reconcilers; it is not a multi-resource IAM transaction. Six focused tests passed locally. Operator plan is the next required evidence before applying these prepared changes; a correct plan is not live token/authorization proof.

Requested laboratory plan parameters: client `ouf-semantic`, audience `ouf-api-gateway`, tenant `ouf-lab`, provider scope `gateway.southbound.invoke`, discovery scope `ouf.semantic.discovery`. They are CLI inputs, not installation defaults. OAuth scope preparation/binding does not substitute for capability registration, active grants, Gateway route enforcement or owner authorization. Policy remains `ouf-lab-authorization:38`; no new discovery grant or descriptor is published by this step.

Still open: actual provider service token acquisition and secure credential mount; southbound adapter wiring/configuration/egress/DNS/TLS/response acceptance; tenant-aware MCP discovery command/read receipts; native V10 migration-aware release; exact candidate RDF inspection and adopted revision pinning; human-only adoption/review/publication; chatbot semantic/identity mapping; immediate approved-file ingestion and configured scheduled vertical ingestion. Live owners, historical migration bytes, Cinema/Teatri fixtures and source jobs remain unchanged.

### 2026-10-02 — Provider IAM plan accepted; additive apply pending

Operator plan from pinned helper `208df1fdea874d608ebcf9d7b0829d6180b3eaef` returned `profileDrift=[]`, `EXISTING_PROFILE_READY=true`, `providerScopeDefault=false`; both scope definitions are missing. Planned writes are exactly: create `gateway.southbound.invoke`, create `ouf.semantic.discovery`, add only `gateway.southbound.invoke` as DEFAULT to existing `ouf-semantic`. No discovery client binding, mapper/flag/credential edits, secret reads or policy publication. The helper's preparation CI is green (job 110859198264); six focused tests passed.

Next operator step is apply then verify with the same pinned helper and explicit installation parameters. Apply rereads and guards the current client profile/scope definitions before writing. This plan is sufficient to proceed within the already authorized integration work; it is not applied-state or live token/provider acceptance. Policy 38, live software, fixtures, source jobs and scheduler remain unchanged at this checkpoint. All previously open southbound transport/egress/TLS, tenant-aware MCP, migration-aware V10, human semantic governance and full file/API-to-UDP gates remain open.

### 2026-10-02 — Provider IAM applied and verified; workload OAuth candidate

Operator apply and verify using helper `208df1fdea874d608ebcf9d7b0829d6180b3eaef` passed: definitions `gateway.southbound.invoke` and `ouf.semantic.discovery` exist with no drift; provider scope is now DEFAULT on existing `ouf-semantic`. No discovery client scope binding was requested. Existing client flags, mappers, credentials and policy `ouf-lab-authorization:38` were preserved. This closes the additive IAM preparation step; do not repeat it. Actual token claims and Gateway admission remain unproven.

Semantic draft PR #30 (`codex/semantic-provider-workload-auth`, candidate `c2b4ae5abed1236378c7060b3eb3dac126672cbc`, based on native jobs PR #29) adds bounded client-credentials OAuth with explicit endpoint/client/scope/private mounted credential parameters, synchronized in-memory renewal, no expired-token fallback and same-origin checks before token acquisition/disclosure. Disabled/incomplete authentication fails closed. Token responses have media/type/scope/lifetime checks; token and Gateway bodies have allocation and elapsed-time bounds. Production token endpoints require HTTPS. No installation domain/port/network/client/credential-path defaults were added; the previous Gateway sentinel default was removed.

The first candidate's Java21/PostgreSQL17 suite passed (86 tests, zero failures/errors, one existing skip), but its legacy live pairwise fixture failed because it still supplied anonymous HTTP. The follow-up candidate uses an ephemeral HTTPS fixture issuer, trusted fixture certificate, private read-only client credential and protected Gateway routes. Fixture tests, native suite and actual Lua–Java–PostgreSQL checks have passed; final container/live pairwise results are pending at this checkpoint. This is test-fixture transport acceptance, not installed Keycloak/Gateway/provider acceptance. Existing live images remain unchanged.

New `scripts/r4a_semantic_provider_runtime_bindings.py` reads only explicitly selected Semantic/MCP container metadata, exposes selected safe endpoint bindings, numeric user and credential-mount presence, and never reads credentials/requests tokens/calls providers. Six focused tests pass locally. No container name defaults; no environment-value dump or host mount sources. Next operator evidence is this inventory to resolve real TLS/endpoint/credential bindings before any rollout.

All prior gates remain open: isolated southbound adapter and fixed provider boundary wiring, egress/DNS/TLS, actual workload token/Gateway admission, tenant-aware MCP discovery command/read receipts, native V10 migration-aware release, exact candidate RDF inspection/adopted revision pinning, human-only adoption/review/publication, chatbot mapping/identity decisions, immediate approved-file ingestion and configured scheduled vertical ingestion. Cinema/Teatri fixtures and source jobs were not replayed. The migration-identical RDF release helper must not deploy the V10 discovery branch.

### 2026-10-02 — Workload OAuth candidate validation completed

Semantic PR #30 candidate `c2b4ae5abed1236378c7060b3eb3dac126672cbc` now has all 14 reported CI checks green. Java21/PostgreSQL17: 86 tests, zero failures/errors, one pre-existing skip. Container smoke, fixture Java21, actual Lua–Java–PostgreSQL and HTTPS workload-authenticated live pairwise passed; job 110869592967 reports `PAIRWISE PASS: Semantic Registry <-> Gateway fixture <-> live schema.gov.it`. This closes candidate validation pending in the preceding checkpoint, not production IAM/Gateway acceptance.

Read-only runtime bindings inventory is pinned at `ae535739ce45b76da39e74a4a5a53147526507af`; its six focused tests and complete preparation job 110870691474 passed. Operator must supply actual container bindings. It prints only selected sanitized issuer/provider/token/requester endpoint values plus configuration/mount proof flags, never environment secrets or credential contents. No token request, provider call, route/container/policy mutation. Next required external evidence is its server output; no SSH capability is available in the assistant environment.

All preceding installation, southbound isolation, actual token admission, semantic governance, V10-aware release, tenant-aware MCP and end-to-end file/vertical ingestion gates remain open. No successful IAM preparation, frozen business fixture or source acquisition job is to be repeated for this inventory.

### 2026-10-02 — Runtime bindings received; existing credential staging helper

Operator inventory from `ae535739ce45b76da39e74a4a5a53147526507af` passed read-only with no token request/provider call. Selected Semantic container is `7ae83be8c1fe9fe25774b7d748e35153652b29b2501886f89daeabb83bd1a147`, running as `10001:10001`. Issuer `https://auth.ouf-lab.it/realms/ouf` and MCP execution endpoint `https://api.ouf-lab.it/internal/capabilities/v1/execute` are configured HTTPS bindings. Provider/auth are disabled; provider Gateway/token/client/scope/credential mount bindings are absent. These are observed lab inputs, not defaults. HTTPS URL syntax does not establish network/TLS connectivity or workload admission.

New `scripts/r4a_prepare_semantic_provider_credentials.py` composes the unchanged proven `provision-keycloak-workload.py` profile inspector through a GET-only wrapper. Plan checks pinned running Semantic ID/numeric non-root user/issuer, existing confidential SERVICE client/scope/mappers and exact explicit token/introspection endpoint equality against TLS OIDC metadata. It does not read a secret, request a token or create a directory/file. Apply reads the existing IAM secret without rotation, obtains a fresh service token with explicit scope, validates issuer/audience/client/SERVICE/tenant/subject/acr/lifetime, then requires active IAM introspection with matching context over TLS. Only after acceptance and repeat profile/container/credential race checks does it create a private copy. Existing different copies are blocked, never overwritten. Verify repeats authority acceptance and preserves the file.

The operator chooses the absolute credential path and all container/IAM/network/domain bindings. A single new directory may be created below existing root-owned, non-writable ancestors; directory root:0700, credential derived Semantic uid/gid:0600. Regular non-symlink single-link files only. Copy creation is atomic and does not replace an existing/racing file; tokens stay in memory, never persist or print. Redirects, non-JSON/oversize/duplicate-key bodies and elapsed-time overrun are rejected. Optional CA file supports an installation-specific trust anchor without disabling TLS validation. No credential in process arguments or URLs. Standard-library implementation; no new Python package dependency. Official endpoint semantics: https://www.keycloak.org/securing-apps/oidc-layers (confidential-client introspection) and Keycloak 26.7.4 server admin guide (GET current client secret).

Seventeen focused tests cover token/introspection context, inactivity, TLS trust/redirects, bounded JSON/deadline, no-write preflight failure, no secret read in plan, profile/pointer/rotation/container drift, replay preservation, real file ownership/permissions/symlink/hardlink/atomic create race and GET-only/redacted kcadm. Local scratch passes fourteen with three numeric ownership checks unsupported by the scratch filesystem; CI must run all seventeen as root with ownership support required. CI pending at this checkpoint. No helper apply or token acceptance has run on the server yet.

Next operator step is plan, apply, verify of this credential helper after its CI passes. It prepares a host file only: no mount installation, enabled provider, container switch, route change, IAM configuration update, policy publication or provider call. Active policy remains 38. Actual Gateway admission, TLS/egress southbound wiring, fixed provider boundary, V10-aware release, exact candidate inspection/adopted revision pinning, tenant-aware MCP and human semantic governance/file immediate ingestion/API scheduled ingestion gates remain open. Do not repeat already successful IAM scope preparation or frozen Cinema/Teatri source jobs.

### 2026-10-02 — Existing credential helper CI acceptance

Pinned helper `d49a10157ba25f8cbf4026be188802848d0e053b` passed its complete preparation job 110882214001. All seventeen new tests executed successfully as root, with no skips, including real numeric file ownership and private/atomic no-overwrite behavior. This closes the helper validation pending above. The existing workload helper bytes were checked unchanged against parent `4e66f34409a1344154a2677a346072ea30be1202` before publication. Module Java/PostgreSQL, authorization/SDK, staging/probe and live pairwise checks also passed; container checks were still running at this exact documentation checkpoint.

Prepared operator execution uses selected lab bindings as CLI arguments, not defaults: IAM container `ouf-keycloak`, kcadm `/opt/keycloak/bin/kcadm.sh`, realm `ouf`, client `ouf-semantic`, audience `ouf-api-gateway`, tenant `ouf-lab`, scope `gateway.southbound.invoke`; selected Semantic container `ouf-semantic` pinned to `7ae83be8c1fe9fe25774b7d748e35153652b29b2501886f89daeabb83bd1a147`. Issuer/token/introspection endpoints are explicit HTTPS installation values. The proposed private credential path is `/etc/ouf/semantic-provider-auth/client-secret`; no preexisting different file or unsafe directory is replaced. UID/GID are derived from the pinned container (`10001:10001` at observed runtime). Plan/apply/verify are prepared for operator execution; no server credential or token acceptance result has been received yet.

Expected successful next evidence: `SEMANTIC_PROVIDER_TOKEN_CONTEXT=PASS AUTHORITY_INTROSPECTION_ACTIVE=true` and credential apply/verify PASS, with no secret printed. This proves authority-side acceptance from the host, not installed container egress/TLS, credential mount, enabled provider or actual Gateway admission. Those, fixed southbound route/adapter/egress wiring, active discovery authorization, native V10-aware release, tenant-aware MCP, exact candidate adoption pinning, human semantic decisions and the full file/API-to-UDP gates remain open. Software, routes, policy 38, fixtures and source jobs remain as last proven on the server.

### 2026-10-02 — Issuing-client introspection blocked; correct JWT preparation proof

Operator ran pinned credential helper `d49a10157ba25f8cbf4026be188802848d0e053b`: plan PASS with no existing credential, numeric user/group 10001 and TLS metadata proven; apply blocked `TOKEN_INTROSPECTION_INACTIVE`. No credential copy/directory was created by that failed apply, since its write occurs only after token acceptance. Earlier expired kcadm session was renewed by the human; no IAM configuration mutation occurred.

The helper incorrectly used the issuing workload client for introspection of a token intended for the Gateway audience. Keycloak 26.7.4's upgrading guide states introspection returns active=false when the introspecting client is absent from token audience (https://www.keycloak.org/docs/26.7.4/upgrading/, section Token introspection now validates audience claim). The observed response is consistent with that rule; the old output does not enumerate all audiences and is not a token revocation diagnosis. Do not add a self-audience, disable audience checks, rotate credentials or change IAM simply to make this preparation probe pass.

Corrected helper verifies the fresh RS256 JWT signature with the issuer's explicitly bound TLS JWKS endpoint and then validates issuer, required Gateway audience, scope, client, SERVICE actor, tenant, subject/acr and time bounds. Plan requires exact jwks_uri match in TLS OIDC metadata. Signature verification uses installed OpenSSL with a validated single matching RSA kid/key, bounded key sizes, no private/encryption keys, no token-header key URLs, no redirects and no new Python dependency. ASN.1 code only serializes the public JWK for OpenSSL; it does not implement cryptographic verification. Public key/signature transient files are in a private temporary directory; token and secret remain unprinted, no token persistence. CLI now requires --jwks-endpoint instead of --introspection-endpoint; --openssl-path is optional and otherwise resolved from the operator environment. No installation network/domain defaults.

Acceptance output now states SIGNATURE_VERIFIED=true, INTROSPECTION_NOT_CALLED=true, REVOCATION_NOT_PROVEN=true and GATEWAY_ADMISSION_NOT_PROVEN=true. This supersedes the preceding expected introspection PASS marker: a signed fresh workload token is preparation evidence, not resource admission/revocation acceptance. Actual Gateway validation remains mandatory before enabling the provider. Existing scope/profile guards, pinned container/numeric owner checks, private atomic no-overwrite copy and read-only verify are retained. All nineteen tests pass locally except three numeric ownership cases unsupported by scratch; root CI requires those cases too. Added real TLS/JWKS/OpenSSL valid-signature, tampered-token, wrong-key, duplicate-kid and rejected-key cases. CI pending here; operator must use the corrected immutable pin after it passes.

Live Semantic/MCP/Gateway software, routes, policy 38 and successful IAM scope bindings remain unchanged. Provider remains disabled/unconfigured. Southbound isolation/route wiring/egress/TLS, actual Gateway admission, V10-aware discovery release, candidate RDF inspection/adopted revision pinning, tenant-aware MCP, human semantic governance, immediate approved-file ingestion and scheduled vertical ingestion remain open. Frozen Cinema/Teatri fixtures/source jobs remain untouched.

### 2026-10-02 — Corrected JWT/JWKS helper CI passed

Corrected immutable pin `bad1e7f44d440389332bc90720591909a1662cb3` passed complete preparation job 110888180818. All nineteen credential tests executed as root with no skips, including real trusted TLS JWKS retrieval and OpenSSL verification against valid/tampered signatures, wrong key, ambiguous kid and private atomic copy ownership cases. This closes helper CI pending above. Operator retry must use this pin and --jwks-endpoint https://auth.ouf-lab.it/realms/ouf/protocol/openid-connect/certs as an explicit lab installation argument; the old --introspection-endpoint is no longer accepted. Do not rerun the old out-of-audience introspection helper.

Server token signature acceptance and credential copy are still pending: only old plan PASS/introspection BLOCKED have been reported. Scope definitions/bindings and policy 38 are preserved; no server container, route, provider activation or source job changed. Signature-based preparation does not establish revocation status, actual resource admission or container egress/TLS. The previously listed southbound configuration/isolation, fixed provider boundary, V10-aware release, tenant-aware MCP, candidate/adopted revision inspection/pinning, human semantic governance and end-to-end file/API-to-UDP gates remain open.

### 2026-10-02 — Credential staging accepted; fixed provider transport candidate

Operator completed corrected helper `bad1e7f44d440389332bc90720591909a1662cb3`: plan PASS; apply PASS PRIVATE_COPY_CREATED=true; verify PASS PRIVATE_COPY_CREATED=false. Both fresh token contexts report SIGNATURE_VERIFIED=true, SERVICE actor and TTL_SECONDS=299. Existing secret was copied without rotation to the chosen private file `/etc/ouf/semantic-provider-auth/client-secret`, owner/group derived from pinned Semantic (10001:10001), mode 0600 under root:0700 directory. IAM config, containers, routes and policy stayed unchanged. No provider call. This closes host credential staging and fresh signed token context, not mount/container connectivity/resource admission/revocation. Provider remains disabled and mount uninstalled.

Gateway PR #56 was expanded in place, not duplicated, with candidate `58d8b575a8be50c904c48df8402e6396a1966753`. New `tools/semantic_provider_relay.py` wires the existing exact six search forms and installed namespace IRI validation to a fixed registered HTTPS endpoint. Candidate URI remains subject-only CONSTRUCT data and never an HTTP destination. DNS answers are checked before a numeric socket connect (no second DNS lookup), while SNI/hostname validation stays bound to the registered host. Public/non-global/private/CIDR controls, elapsed time (DNS/TCP/TLS/headers/body), media/body/framing/compression/redirect/incomplete bounds and no caller credential forwarding are enforced. Fetch exposes outgoing asserted subject-triple scope, not ontology closure or full artifact completeness. No silent LIMIT truncation. Ten existing grammar tests plus ten new relay tests pass locally, including real controlled TLS numeric pin/SNI/trust checks. CI pending at this checkpoint. The core has no listener and must not be exposed directly; HTTP adapter/trusted Gateway admission and production wiring remain open. POSIX main-process deadlines reject threaded invocation; concurrency requires bounded worker processes.

Before selecting the actual isolated southbound install/egress mechanism, the host's Docker/rootless and firewall capabilities must be known; previous network inventory only showed Docker networks, not the host packet-filter implementation. New read-only `scripts/r4a_semantic_southbound_host_inventory.py` accepts explicit Gateway binding, reads Docker metadata plus available nftables/filter iptables metadata, and emits only version/rootless observation, selected role/network names, counts/fixed policy classes. It never prints rule expressions, IPs/interfaces/custom chain/table labels/comments, environment/credential values or raw command failures. Six focused tests pass locally; preparation CI pending. Default-deny, FQDN policy and TLS client identity remain explicitly unproven even if a global DROP chain is observed. No rule write, token request or provider call.

Next external evidence is the operator's host capability inventory; assistant has no SSH/server execution. After that, the install must provide explicit network/domain/port/endpoint/namespace/CA/credential bindings, separate the technical southbound boundary, enforce trusted Gateway/owner bypass protection and verify OS egress default-deny/FQDN/TLS before enabling provider traffic. Native discovery release inherits V10, so migration-identical RDF helper remains inapplicable. All active discovery authorization/tenant-aware MCP, exact candidate inspection/adopted revision pinning, human-only governance, chatbot mapping, immediate approved-file ingestion, scheduled vertical ingestion and full file/API-to-UDP gates remain open. Frozen Cinema/Teatri fixtures and source jobs were not replayed.


### CI confirmation — 2026-10-02, host credential preparation complete

Gateway PR #56 relay candidate `58d8b575a8be50c904c48df8402e6396a1966753`: all 12 reported checks completed successfully, including the 20 request-grammar/relay tests. Semantic host inventory candidate `82253dc696b10fd27b35cf937538ae2788f65743`: all 14 reported checks completed successfully, including preparation and both container-smoke runs. This supersedes the pending CI statements in the preceding checkpoint. The operator helper remains pinned to that tested inventory commit. Successful host credential apply/verify does not prove mounted credentials, revocation, Gateway resource admission, runtime provider connectivity or egress isolation. Next action is read-only host capability inventory; no live release, policy change or provider call is authorized by these CI results alone.


## 2026-10-02 — host southbound capabilities observed; authenticated TLS adapter candidate

Operator `SEMANTIC_SOUTHBOUND_HOST_INVENTORY=PASS`: Docker29.8.1, rootlessObserved=false; nft and iptables available/readable. iptables21 filter rules with FORWARD=DROP, INPUT/OUTPUT=ACCEPT and DOCKER-USER present. nft35 rules across ip/ip6, mixed forward/drop/accept and output/accept classes. Gateway ID `dcbe26bed97dd5c7ac8a131ec2badf77b0291c2ef32907be639bfa09c36596d9`, image `sha256:84e6b5e787e9f889ebff88161cb9a16599bafcffa236c6b54c7f779a0655940d`, networks unchanged (backend/control internal). Read-only: no rule/container/route/token/provider change. Counts/global chain policies do NOT prove workload default-deny, FQDN controls or TLS identity; all three remain false/unproven. These are new host packet-filter capability facts, not replay of the successful IAM/credential or source tests.

Gateway PR#56 now adds purpose-separated short-lived HMAC provider receipts, TLS-only bounded Linux fork workers and additive exact POST-search/GET-fetch route materialization. Gateway checks OIDC/JWKS/audience/scope + SERVICE/issuer/workload/tenant, signs exact method/target/body, strips incoming proof/identity headers and bearer/cookie before backend transport. Adapter denies absent/duplicate/altered/expired/wrong-context receipts and forwarded bearer before provider calls. New provider receipt key must be separately provisioned, never reused from OAuth/delegation/semantic-READ keys. Non-root/private key files, TLS1.2+, complete elapsed incoming deadline incl handshake/slow headers, finite workers/backlog, input framing and bounded response enforced. Fetch scope remains outgoing asserted subject triples, not complete ontology/closure/adopted artifact inspection.

Candidate head `a8292a7f9f6003b6a9408b5ed73c32086ea2bb94`; local40 focused tests PASS, one Docker APISIX fixture skipped locally. A mandatory real APISIX3.18.0 CI job exercises signed JWT -> actual Lua receipt -> TLS adapter, wrong identity/scope/direct bypass and wrong TLS hostname, with controlled provider exchange only. Initial candidate CI failed on unread ambiguous-body TLS reset handling in the test and incorrect fixture IAM trust parameter; corrected tests use the permitted safe connection close and correct APISIX trust path. Pinned APISIX3.18 source inspection shows upstream.tls.verify is Kafka-only. Candidate therefore requires an explicit DEDICATED_SOUTHBOUND NGINX TLS profile (proxy_ssl_verify on + finite verification depth + installed CA bundle), emits providerTLSRequirement installed=false, and does not rely on an ineffective HTTPS route flag. Do not apply global NGINX changes silently to the shared existing northbound role. Exact source: https://github.com/apache/apisix/blob/3.18.0/apisix/schema_def.lua and https://github.com/apache/apisix/blob/3.18.0/apisix/cli/ngx_tpl.lua. Controlled TLS fixture trust mounts/SAN bindings were corrected while keeping certificate verification enabled. Current pinned candidate CI: all14 reported checks completed successfully; none pending. Mandatory provider-apisix-tls completed successfully on both push/PR (jobs110921132533 and110921115668), exercising real signed JWT/OIDC, exact Lua-to-adapter request receipt, validated TLS, wrong upstream hostname rejection, direct owner and wrong identity/scope denial. Focused request-boundary jobs both PASS (40 executable tests plus one opt-in live fixture skipped there and run by the separate mandatory job). No live acceptance inferred; no live rollout command is ready yet. Implementation/docs: `tools/semantic_provider_admission.py`, `semantic_provider_adapter.py`, `materialize_semantic_provider.py`, `tools/lua/admit_semantic_provider.lua`, `docs/SEMANTIC_PROVIDER_ADAPTER.md`.

Next gates: exact live APISIX version/TLS feature enforcement and installed trust; governed provider endpoint/namespace; approved packaging/Technology Economy for Gateway transport process; isolated southbound zone; independent kernel default-deny and FQDN-aware/equivalent control with explicitly governed DNS/identity/telemetry exceptions; direct workload bypass negatives; receipt key/certificate provisioning; release plan/snapshot/rollback/readback. Parameterize all domain/endpoint/port/container/network/trust bindings. Current host Semantic OAuth copy is already verified, remains unmounted, no rotation/recreation. Provider not enabled; no external provider calls. Semantic PR#30 inherits V10 and cannot use migration-identical RDF release helper. Discovery policy/MCP tenant-aware commands, candidate RDF/adopted exact revision pinning, human governance, chatbot mapping, immediate approved-file ingestion and scheduled vertical ingestion/file-to-UDP acceptance remain open. Frozen Cinema/Teatri jobs are preserved and never replayed.


Next operator input is the version of the actual already-running Gateway binary (`docker exec <explicit-gateway-container> apisix version`), a read-only command with no credential, route, token, provider or container configuration mutation. Do not stage/apply new software before live-version/trust/role/egress bindings and reversible plan are prepared.


## 2026-10-02 — live APISIX version confirmed; provider image-only staging prepared

Operator read-only binary output: `3.18.0` (apisix version). This closes the live-version uncertainty and matches the real APISIX3.18.0 OIDC/receipt/TLS CI fixture. It does not prove installed CA/NGINX configuration, isolated southbound role or kernel/FQDN policy. Current live images/credentials/routes/source jobs remain unchanged by this work.

Gateway PR#56 candidate `52c0dcf11654a4d3d0f17a6902ed095975466fb9` adds `Dockerfile.semantic-provider`, `scripts/stage_semantic_provider_adapter.py`, staging tests and mandatory actual-container packaging CI. The image uses an explicitly resolved Python3.13 digest and only five reviewed stdlib modules. No configuration, certificate, secret, tests or repository credentials enter the minimal build context. Non-root UID/GID and revision/payload labels are explicit build inputs. Stage plan is read-only; apply checks all pinned SHA-256 payloads, uses offline `--network=none --pull=false` build, refuses reused snapshot roots/image tags, hashes sensitive Gateway inspect fields without printing/persisting values and requires Gateway ID/configuration/version stable before/after. Verify is read-only; failed/interrupted apply retains intent and requires reconciliation, not blind retry. No runtime container creation/start/switch, credential read/mount, route/IAM/database write, policy publication or provider call is implemented. Docker build workers/cache and image are build artifacts, not deployed OUF services.

Local13 staging tests PASS. Mandatory root CI staging jobs110950003316 and110949985400 PASS with13 tests/no skips; real root receipt/ancestor guards run there. Actual container jobs110950003240 and110949985450 PASS: native non-root entrypoint, read-only root/private mounts, dropped capabilities, no-new-privileges, bounded PIDs, actual TLS/direct denial, valid receipt + invalid grammar blocked before DNS/provider I/O. The controlled fixture calls no external provider and does not prove kernel egress. Native APISIX and focused grammar/relay CI are also PASS. Final candidate CI: all18 reported checks completed successfully; none pending. Operator staging command is pinned to this tested candidate.

CI acquired and actually tested immutable base `python@sha256:bb2988715db2cf7ace7b53f38f3cffbef7c7046a656bee66245eb0ed386e2e81`. CI code revision `52c0dcf11654a4d3d0f17a6902ed095975466fb9`, built image `sha256:e1c1903139dfa0b0ce5036edab37b249810440d388c7c15227c72e7b386d5a3f`, fixture UID/GID10006:10006. Production staging will use the exact pinned source commit and selected base digest and records its own resulting image ID (do not assume it equals the CI artifact). Digest integrity is not publisher signature/provenance acceptance. Fixture UID/GID is an explicit candidate build binding, not an IAM identity/default or automatic runtime permission. All image/source/registry/container/UID/GID/snapshot, future network/domain/endpoint/port/CA/credential bindings remain installation parameters; no shared northbound NGINX change is silently applied.

Next operator step: acquire this exact base digest, download only the pinned helper and run plan/apply/verify to stage the image. That step requires server execution unavailable to the assistant; it creates no OUF runtime container and activates no provider. The operator output is needed before preparing container/config/network install bindings. Do not use a mutable base tag in FROM. Do not recreate/rotate the already verified Semantic OAuth host copy, rerun IAM setup or replay frozen source fixtures.

Still open: governed provider endpoint/namespace/registry binding; packaging/Technology Economy acceptance for Gateway transport process; dedicated southbound APISIX role with explicit NGINX certificate verification/CA; independent OS default-deny and FQDN-aware/equivalent control, scoped DNS/identity/telemetry and direct Semantic/Ingestion bypass negatives; receipt key/certificate provisioning, reversible snapshots/readback and real provider proof. Semantic PR#30 includes V10 and requires a migration-aware release. Discovery application capability/policy/HUMAN scopes and tenant-aware MCP commands, exact candidate RDF inspection/adopted revision pinning, human-only governance, chatbot mapping, immediately-onboarded approved-file ingestion/dedup and scheduled API vertical ingestion/UDP acceptance remain open. Cinema8/8 and frozen Teatri fixtures are retained; no source job/upload/profile replay. See Gateway `docs/SEMANTIC_PROVIDER_IMAGE_STAGE.md` for packaging/staging contract.


## Operator adapter image stage evidence — 2026-10-02 19:34 Europe/Rome

Operator plan/apply/verify all PASS. Exact staged Gateway transport source `52c0dcf11654a4d3d0f17a6902ed095975466fb9`; image `sha256:a697bf75bf7d51afadadfaccd3d80537e9a5fb2a08f0d194c6dfd9462e812468`, tag `ouf-semantic-provider:stage-52c0dcf11654`, runtime UID/GID `10006:10006`, base `python@sha256:bb2988715db2cf7ace7b53f38f3cffbef7c7046a656bee66245eb0ed386e2e81`. Private stage receipt: `/etc/ouf/deploy-snapshots/semantic-provider-adapter-20261002-173408/stage-receipt.json`. This is the resulting server image ID, intentionally distinct from the CI-built image ID. No OUF runtime container created, no route/IAM/policy writes and no provider call; NOT_RELEASE_ACCEPTANCE remains true. Do not rebuild or rerun apply; retain this image/receipt for the subsequent reversible installation.

Next: read-only selected Docker network/bridge/IPAM inventory before constructing isolated southbound installation bindings. The existing host inventory proves available firewall tools only, not workload default-deny. Select container roles and expected Gateway ID explicitly; derive observed network facts without assuming subnet/interface/domain/port. No firewall changes or provider connectivity test are part of this inventory. Separate southbound APISIX TLS trust, independent kernel default-deny with governed destination/DNS/identity openings, workload bypass negatives and the real provider remain unproven. The prepared Semantic credential copy stays unmounted; no IAM replay/rotation. Frozen Cinema/Teatri source jobs stay untouched.

### Network inventory candidate ready — 2026-10-02

Gateway PR#56 latest helper-only head `1a0dd214e5db871664959771ca7c7be845f36b64` adds standalone `scripts/inventory_semantic_provider_network.py`. It does not change any of the six adapter build-payload files; the staged 52c0dcf image/receipt remains valid and must not be rebuilt for this inventory addition. All18 reported CI checks on 1a0dd214 completed successfully. Local focused suite:54 tests,51 PASS,3 opt-in skips; mandatory CI executes APISIX/TLS, OCI packaging and real network fixtures separately. Network inventory CI:12 tests with no skips, actual internal Docker bridge and three harmless sleeping fixture containers; push job110956522504 and PR job110956549675 each print SEMANTIC_PROVIDER_NETWORK_CI=PASS REAL_DOCKER_BRIDGE=true PROVIDER_CALLS=0 NOT_RELEASE_ACCEPTANCE=true. Fixtures are removed afterwards; no OUF source job is invoked.

Next operator command downloads the immutable 1a0dd214 standalone helper and runs only selected container/network inspect plus host link metadata, using explicit Gateway/Semantic/Ingestion roles and expected Gateway ID. The helper reports bridge interfaces, IPv4/IPv6 IPAM/subnets/gateways and selected workload attachments; it excludes env/mounts/credential-bearing fields, rejects role/driver/address/identity ambiguity and redacts failures. Repeated matching reads detect drift without claiming an atomic snapshot. It issues no firewall command, Docker exec/create/start/switch, DNS/provider/token request or write. The server output is required to construct installation-specific isolation rules. Kernel default-deny, FQDN enforcement, TLS trust and actual installation acceptance remain false/unproven in this metadata report. No provider enablement or application-policy publication is included.


## Observed network bindings and kernel candidate — 2026-10-02

Operator network inventory PASS at 19:51 Europe/Rome: selected topology stable across two reads, bridgeBindingsReady=true, snapshotHash `8b0eb1c691a5010f98f22e34bb3de8de0b65cf8f9bab3079fc6c193778b857d4`; atomicSnapshotProven=false. Both observed networks are internal bridge networks with IPv6 disabled. Existing shared interface/IPAM bindings (facts only, never installation defaults):

| Role/network | Observed binding |
| --- | --- |
| backend | `ouf-backend`, networkID `113b5f0a3c53059b087a2ce997d2670cc057e88c0c17d4291b3b41a51ce26ba3`, bridge `br-113b5f0a3c53`, ifindex36, subnet `172.18.0.0/16`, gateway `172.18.0.1` |
| Gateway control | `ouf-gateway-control`, networkID `1209d67944755d95601b96719c0a5b1860ac2a6f137c10077da7b4e9967637aa`, bridge `br-1209d6794475`, ifindex41, subnet `172.20.0.0/16`, gateway `172.20.0.1` |
| live Gateway | ID `dcbe26bed97dd5c7ac8a131ec2badf77b0291c2ef32907be639bfa09c36596d9`, backend `172.18.0.10`, control `172.20.0.3` |
| live Semantic | ID `7ae83be8c1fe9fe25774b7d748e35153652b29b2501886f89daeabb83bd1a147`, backend `172.18.0.6` |
| live Ingestion | ID `1fa5450574e72ef15ebb2c74e0f421f04d24c842975e324ac958f071672fbb7e`, backend `172.18.0.9` |

No firewall/container/provider changes. Kernel default-deny, FQDN policy and TLS trust remain unproven. These existing shared bridges must not receive a whole-interface deny policy for the new southbound candidate.

Repository reuse audit: all9 open Gateway PRs checked; no pre-existing Docker kernel-policy installer found. Existing `southbound_security.py` and Kubernetes NetworkPolicy contracts are retained. APISIX CI already uses the separate data-plane YAML role without etcd, so that transport role does not require adding another etcd service. The observed Docker deployment still needs separate installed topology/bindings and lifecycle proof; this audit is not production architecture acceptance.

Gateway PR#56 head `fdbd32fcf5291139c981530ea3faece434afb7db` adds pure `tools/materialize_southbound_kernel.py` and `docs/SOUTHBOUND_KERNEL_PLAN.md`. It compiles only explicit isolated interface and exact source/destination/port flows into a scoped nftables table; no DNS, subprocess, source/provider I/O or installation. Existing-interface exclusions, bounded expiring provider-address sets, exact private exceptions, IPv4/IPv6 and injection/port/class guards are validated. Exact reverse established traffic checks the expiring provider set too; no blanket conntrack grandfathering or broad Internet CIDR. Host input/output and forwarded hooks are emitted, without flushing/global modification. Output installed/default-deny/FQDN/release acceptance remains false. A declared resolution evidence ref is not DNS provenance; governed bounded/fail-closed refresh, all-answer/TTL validation, Docker embedded DNS host boundary and persistence are still implementation/installation gates.

All20 reported CI checks on fdbd32fc completed successfully. Mandatory root nft/netns jobs110962929384 and110962948695 each pass all9 tests without skips, including actual kernel packet exchange and lease expiry for new and already-established sockets. The test uses a local veth pair in two temporary Linux namespaces, not external providers or OUF source jobs; baseline443/8443 reachable, deny-only blocks both, timed exact443 permits443/denies8443, expiry denies fresh443 and the previously opened socket. Readback is checked and processes/namespaces removed. Proof: SOUTHBOUND_KERNEL_CI=PASS REAL_NFT_NETNS=true DEFAULT_DENY=true LEASE_EXPIRY_NEW_AND_ESTABLISHED_DENIED=true DOCKER_HOOK_NOT_PROVEN=true PROVIDER_CALLS=0 NOT_RELEASE_ACCEPTANCE=true. This proves CI input/output semantics, not installed VPS/Docker bridge forwarding behavior or release acceptance.

Next operator step: execute the exact fdbd32fc isolated nft/netns fixture on the VPS (nft/ip already observed available), using only its two pinned Python files and Python -B. It temporarily creates unique network namespaces/veths and local test servers, installs the candidate table only inside the new test namespace, then cleans up. It does not change global host rules, containers, source jobs, IAM, routes, credentials or policy and invokes no provider. Needed output is target-kernel evidence; do not activate the provider from a metadata/CI PASS. Actual Docker path/bypass negatives, FQDN refresh, reboot/restart ordering, scoped DNS/identity, TLS/receipt-key provisioning, isolated configuration/container installation and real provider gates remain open. Adapter build payload is unchanged; keep the already verified 52c0dcf image and stage receipt, with no rebuild. Semantic PR#30 V10 requires its migration-aware release; discovery authorization/tenant-aware MCP/adopted RDF/HUMAN governance and complete file/vertical-to-UDP gates remain open. No frozen Cinema/Teatri replay.


## Target kernel PASS and native Docker bridge correction — 2026-10-02

Operator executed pinned fdbd32fc nft/netns fixture on the VPS at20:11 Europe/Rome: all9 tests PASS (9.234s), SOUTHBOUND_KERNEL_CI=PASS REAL_NFT_NETNS=true DEFAULT_DENY=true LEASE_EXPIRY_NEW_AND_ESTABLISHED_DENIED=true DOCKER_HOOK_NOT_PROVEN=true PROVIDER_CALLS=0 NOT_RELEASE_ACCEPTANCE=true. This is now target-kernel evidence, not only CI; temporary namespaces/local servers were used, with no OUF source replay. Docker forwarding remained explicitly unproven at that point.

The next actual Docker CI fixture at96cb74af initially failed DOCKER_BRIDGE_HOOK_NOT_PROVEN: inet hooks alone did not intercept intra-bridge traffic on the runner. Fixtures were cleaned up, no VPS candidate was installed, and the denial test was retained. Fixed Gateway PR#56 head `5570b63bee5d57217c7b75ae279fe22b90bbbb98` adds native nft bridge forward filtering, scoped by meta ibrname/obrname, alongside inet host/routed guards. The compiler returns tableFamilies=[inet,bridge]; both owned families must be applied/refreshed/read back/deleted atomically. Link ARP and hop-limit255 neighbor solicitation/advertisement remain allowed for address resolution, while unregistered IP transports drop. No shared br_netfilter sysctl or existing interface/table/chain is changed. Kernel bridge conntrack compatibility/target proof is required. These compiler/test changes do not alter the six-file adapter build payload; retain the verified 52c0dcf image/receipt with no rebuild.

Latest CI all20 checks PASS. Mandatory root jobs110969972772 and110969989708 each pass the updated9-test nft/netns suite and the actual Docker fixture (one scenario,15.417s/15.312s). Actual Docker uses an explicitly pre-acquired digest image, a uniquely named new internal bridge, three harmless non-root/read-only/capability-free/restart-disabled test containers without mounts/ports and numeric local peer traffic. Subnet/addresses are read from Docker, not lab defaults. The two temporary host tables match only this new bridge; deny-only blocks real packets with a DROP counter, exact timed source/port allows only its client, other port/client are denied, expiry blocks new/established sockets. Removing the tables restores baseline reachability and pre-existing nft rule structure (ignoring counters/remaining leases) is checked. Cleanup removes fixture containers/network/tables; on failure a guard is retained if workload/network removal is unproven, with unique suffix/types printed for reconciliation. Fixture performs no image pull, provider/DNS/token/credential/source-job/policy operation. Host scoped tables are temporary firewall mutations, so this Docker fixture must not be described as read-only or as having no host firewall writes.

Proof in both CI logs: SOUTHBOUND_DOCKER_KERNEL=PASS REAL_DOCKER_BRIDGE=true NATIVE_BRIDGE_HOOK=true SCOPED_HOST_FORWARD_HOOK=true DEFAULT_DENY=true UNREGISTERED_WORKLOAD_DENIED=true LEASE_EXPIRY_NEW_AND_ESTABLISHED_DENIED=true SHARED_RULE_STRUCTURE_UNCHANGED=true PROVIDER_CALLS=0 NOT_RELEASE_ACCEPTANCE=true; SOUTHBOUND_DOCKER_KERNEL_CLEANUP=PASS TEST_CONTAINERS_NETWORK_AND_TABLE_REMOVED=true.

Next operator step: run only `tests/test_southbound_docker_kernel.py` plus its pinned `tools/materialize_southbound_kernel.py` dependency from5570b63b on the VPS, opt-in root with OUF_SOUTHBOUND_DOCKER_KERNEL_TEST=1 and the already-local explicit Python base digest. No pull/rebuild. Expected one test OK, SOUTHBOUND_DOCKER_KERNEL=PASS and cleanup PASS. It creates only unique disposable resources, attaches to no existing OUF network and changes no existing OUF container/configuration/route/IAM/policy/source job. Target Docker packet proof is needed before an isolated production installation. FQDN resolution provenance/all-answer/TTL/fail-closed refresh, host embedded DNS boundary, registered endpoints/trust/receipt keys, lifecycle persistence/reboot, IPv6 packet paths/forwarding offload, actual production workload bypass and real provider/complete MCP-to-UDP acceptance remain open. The new fixture client's denial is not yet a Semantic/Ingestion production-bypass proof. See Gateway docs/SOUTHBOUND_KERNEL_PLAN.md; upstream native bridge reference https://wiki.nftables.org/wiki-nftables/index.php/Bridge_filtering.


## Target Docker kernel PASS and private trust preparation — 2026-10-02

Operator ran the5570b63b actual Docker bridge fixture on the VPS at22:54 Europe/Rome: one test PASS (17.521s), SOUTHBOUND_DOCKER_KERNEL=PASS REAL_DOCKER_BRIDGE=true NATIVE_BRIDGE_HOOK=true SCOPED_HOST_FORWARD_HOOK=true DEFAULT_DENY=true UNREGISTERED_WORKLOAD_DENIED=true LEASE_EXPIRY_NEW_AND_ESTABLISHED_DENIED=true SHARED_RULE_STRUCTURE_UNCHANGED=true PROVIDER_CALLS=0 NOT_RELEASE_ACCEPTANCE=true. Cleanup PASS: test containers/network/tables removed. This upgrades the isolated Docker/kernel fixture from CI-only to target-host proof, including exact scoped bridge admission, source/port bypass denial and new/established lease expiry. It remains a fixture, not installed southbound/provider or production Semantic/Ingestion bypass acceptance; no source replay/provider call or OUF runtime switch occurred.

Gateway PR#56 latest head `397ca4e4f691b0cb0f7f6a9591c8a7a7dc171809` adds standalone `scripts/prepare_semantic_provider_trust.py` and docs/SEMANTIC_PROVIDER_TRUST_PREPARE.md. It generates only unmounted installation-private TLS/receipt artifacts with plan/apply/verify: fresh EC P-256 offline CA, distinct exact parameterized DNS-SAN serverAuth leaves for adapter/southbound, public trust bundle preserving selected public roots, fresh cryptographic256-bit purpose-separated receipt key copied privately to the two roles. No old read/delegation/OAuth key is reused/rotated; existing prepared Semantic OAuth copy is not read or mounted. Root snapshot/role directories0700; intent/receipt/offline CA key root0600; server keys/certs/MAC files0600 with explicit adapter UID/GID or current Gateway UID/GID derived only via readonly id commands. Public CA/trust bundle root0644. CA private key must never enter a runtime mount. Future mount layout must bind individual readonly leaf files into traversable runtime target directories, not the root0700 role directories wholesale.

All installation ID/hostnames/source-image/UID/GID/validity/public-CA/snapshot/executable bindings are explicit parameters. The helper selects only scalar Gateway metadata (ID/image/user/running) and readonly id -u/-g, never env/mount/command/credential fields. Pinned staged adapter image/native entrypoint/source/component/payload/user contract is checked. Safe root-owned no-symlink ancestors and bounded no-follow single-link files are enforced. Existing roots refuse apply; partial failures retain private intent/artifacts and no success receipt, with no blind retry. Verify checks exact bindings, private ownership, hashes, TLS key/certificate signature/purpose/hostname and wrong-name denial, plus receipt-key equality, without regenerating keys. Output contains no key/cert bytes or private checksums. Preparation performs no image pull/build, runtime container create/start/switch, route/IAM/policy/database/source/provider/network operation; mountsInstalled=false and notReleaseAcceptance=true.

All22 reported CI checks on397ca4e4 completed successfully. Mandatory root trust jobs111031127307 and111031149565 pass all8 tests with no skips (0.378s/0.390s), including real OpenSSL signing, runtime UID/GID10006/10004 ownership, actual local TLS positive/wrong-hostname handshake, plan/no-write/no-secret inspection, identity/image/hostname/validity/public-CA/private-key guards, symlink/mode/pair/content drift, partial failure/no-overwrite and CLI redaction. Local restricted workspace cannot map chown10006;5 cases pass locally/3 ownership integrations intentionally skipped, but all8 run mandatory in CI. Mandatory kernel/Docker, APISIX OIDC/receipt/TLS, OCI packaging/staging/inventory and broader regressions remain green. No external provider or frozen source fixture is called by any added test.

Next operator step: pinned397ca4e4 helper plan/apply/verify on an unused private `/etc/ouf/deploy-snapshots/semantic-provider-trust-<UTC timestamp>` root. Explicit lab bindings in the command are installation IDouf-lab-netcup-01, proposed private DNS aliasesouf-semantic-provider/ouf-semantic-southbound (certificate names only, no DNS/container/route installed), selected public roots/etc/ssl/certs/ca-certificates.crt, CA365d/server30d, existing pinned Gateway IDdcbe26bed97d..., existing staged adapter image sha256:a697bf75bf7d51afadadfaccd3d80537e9a5fb2a08f0d194c6dfd9462e812468 and its52c0dcf source/UID-GID10006:10006. These are operator parameters/lab examples, not product defaults. The helper derives current Gateway numeric ownership rather than assuming it. Expected private receipt and verify output are required before configuring future mounts. Retain existing staged image/receipt; helper changes do not alter the6-file build payload or require a rebuild. Do not rotate/recreate the already verified Semantic OAuth host copy.

Still open: registered provider endpoint/namespace and governance; all-answer DNS provenance/TTL/fail-closed bounded FQDN lease refresh and persistence; Docker host DNS proxy boundary; IPv6/flowtable-offload/reboot/restart and actual production bypass; dedicated southbound TLS/configuration/readonly leaf mounts/operational lifecycle and Technology Economy acceptance; Java native client truststore; real authenticated Gateway/provider exchange. CA/server expiry/renewal/revocation remain lifecycle gates, not covered by a prepare PASS. Native Semantic PR#30 V10 needs migration-aware release; discovery application authorization/HUMAN scopes/tenant-aware MCP commands, exact candidate/adopted RDF revision inspection and HUMAN-only governance, chatbot mapping, immediate approved-file ingestion/dedup and scheduled API vertical ingestion-to-UDP acceptance remain open. Frozen Cinema/Teatri are untouched. No provider enablement or complete release acceptance is claimed.

## Target trust preparation verified; runtime remains uninstalled — 2026-10-02

Operator supplied plan/apply/verify PASS for the pinned397ca4e4 trust helper. Private receipt: `/etc/ouf/deploy-snapshots/semantic-provider-trust-20261002-212033/trust-receipt.json`. Adapter DNS SAN `ouf-semantic-provider`, separate southbound DNS SAN `ouf-semantic-southbound`; these remain installation parameters/certificate identities, not proof of installed DNS aliases. Apply created the artifacts and verified them; subsequent verify reported created=false, verified=true. Actual target Gateway runtime ownership derived by the helper is **UID/GID636:636**. Use this detected ownership for its private TLS/receipt files; do not substitute CI fixture ownership10004:10004. Adapter ownership remains the explicitly bound10006:10006.

Reported invariants: no container/IAM/route/policy/provider change, mounts not installed, no secrets printed, NOT_RELEASE_ACCEPTANCE=true. Reuse the existing staged adapter image a697bf75bf7d... / source52c0dcf11654... and both existing stage/trust receipts. No image rebuild, certificate regeneration, OAuth secret rotation or frozen Cinema/Teatri source/job replay is required by this checkpoint. Individual readonly leaf mounts remain required; offline CA private key stays outside all runtime mounts.

Next installation configuration must bind the separate southbound TLS role, adapter provider endpoint/namespace, explicit listener/upstream ports, runtime mounts, Java client trust and controlled DNS/egress. A usable upstream DNS resolver address has not been established by the prior Docker network metadata. Obtain only resolver metadata from the target host before selecting a parameterized exact DNS flow; host stub/loopback addresses are not automatically usable from an isolated Docker role, and Docker embedded DNS is not proof that forwarding traverses the guard. Do not infer a broad allow rule, reuse guarded shared OUF bridges, start a provider runtime, or publish discovery policy from a trust-prepare PASS.

Previous native bridge/default-deny/lease-expiry fixture PASS remains sufficient evidence for that fixture; no repeat is requested. Actual installation FQDN all-answer/TTL provenance, bounded fail-closed refresh/persistence, embedded DNS path, registered provider governance and lifecycle/production bypass acceptance remain open. File ingestion/dedup must follow approved onboarding immediately; API vertical onboarding must instead complete scheduler configuration before timed automatic ingestion.

## Explicit resolver binding and paired runtime compiler — 2026-10-02

Operator supplied resolver metadata `46.38.252.230`, `46.38.225.230` and `2a03:4000:0:1::e1e6`. Existing observed OUF networks are IPv4-only; the IPv4 resolver addresses are compatible candidate bindings, while the IPv6 resolver is retained as deferred metadata. None of these values is a product default or proof of DNS connectivity/forwarding. No DNS query/provider call or host/container/network/rule change has been made in this compiler step.

Gateway PR#56 head `1b9def82c5ed563e1838a637f03619b5f034fd15` adds `tools/materialize_semantic_provider_runtime.py`, documentation `docs/SEMANTIC_PROVIDER_RUNTIME_PLAN.md` and seven tests. The pure compiler accepts exactly explicit route/adapter/TLS-identity/DNS objects. It reuses native adapter and route validators, rejects admission/path/request-bound mismatch, mismatched adapter hostname/port/TLS identity, duplicate or unsafe namespace boundaries, non-separated credential references, unsafe or repeated runtime file paths, invalid worker/intent/body/deadline bounds, broad destination CIDRs and unsafe addresses. Private installations can declare exact /32 or /128 destination exemptions; declaration is not publication/authorization. Arbitrary lab domains, ports, listener family, namespaces and resolver addresses remain caller inputs. Resolver port is explicit; the existing kernel DNS flow profile currently supports53 and a different port requires a matching reviewed profile before installation.

The output contains native adapter JSON, additive southbound routes and declared DNS/TLS bindings with `installed=false`, `providerCalls=0`, `notReleaseAcceptance=true`. It is **not an APISIX startup configuration**. Separate-role TLS listener/SSL resource, Java truststore, verified trust receipt/readonly individual leaf mounts, controlled DNS forwarding/all-answer/TTL fail-closed refresh, isolated kernel readback, governance/admission and lifecycle/production bypass remain installation gates. Compiler input accepts no inline key/PEM/OAuth values. Only the named bounded JSON input and existing Lua template are read; no private runtime artifact is opened. Duplicate JSON keys, unknown fields and oversized input/output fail closed with redacted CLI errors.

Local targeted compiler/native route/adapter regression PASS:27 tests,0 failures (6.544s). Request-boundary CI jobs111041218561 and111041202002 discover61 tests and PASS (8.579s/7.405s); their3 opt-in integration skips belong to the separate mandatory APISIX/OCI/network jobs. All22 reported CI checks on1b9def82 completed successfully, including real APISIX OIDC/receipt/TLS, OCI container packaging, private trust preparation and actual Docker/native bridge/default-deny/lease-expiry gates.

This addition is outside the frozen six-file adapter image payload; retain staged image sha256:a697bf75bf7d... and its existing receipt. The target trust preparation at `/etc/ouf/deploy-snapshots/semantic-provider-trust-20261002-212033/trust-receipt.json` remains verified and unmounted, with actual Gateway UID/GID636:636 and explicit adapter10006:10006. Do not regenerate those artifacts, rotate the existing Semantic OAuth copy, rebuild the image or replay Cinema/Teatri. No complete release acceptance is claimed.

Next concrete laboratory binding requires the exact tenant identifier previously passed to the provider IAM/credential preparation `--tenant`; it is not recoverable from the redacted PASS output and must not be guessed from realm or installation name. Only the identifier is needed, never a token/password/secret. Continue preparing the explicit provider endpoint/namespace/role configuration with that admission binding before requesting host installation. Preserve all unresolved gates from preceding checkpoints and the file-immediate-ingestion versus vertical-scheduler distinction.

## Confirmed tenant and private runtime plan staging — operator confirmation 2026-10-02

Operator confirmed provider workload tenant identifier `ouf-lab`. Admission must bind that exact value; do not derive tenant from realm `ouf` or installation ID. Resolver metadata remains `46.38.252.230`, `46.38.225.230`, `2a03:4000:0:1::e1e6`, with the IPv6 resolver deferred for the observed IPv4-only profile. These are explicit laboratory parameters, never product defaults.

Gateway PR#56 head `bea029b4da49256d0f226359f7e84a053874841d` adds `examples/semantic-provider-runtime.ouf-lab.json`, `scripts/stage_semantic_provider_runtime_plan.sh` and three root staging tests. The profile combines the confirmed installation/tenant/issuer/audience/workload/scope, editable proposed Schema.gov.it/OntoPiA endpoint `https://schema.gov.it:443/sparql`, ontology/controlled-vocabulary prefixes, exact provider search/fetch paths, adapter9443, TLS runtime file references, explicit time/body/worker/rate bounds and DNS port53. It is a proposed parameter file, not provider governance publication, connectivity proof, catalogue census or source acquisition. Existing paired compiler validates the profile; its two readonly southbound routes remain uninstalled.

The staging helper takes explicit repository, immutable commit, profile path, new root-private snapshot and existing private trust receipt reference. It downloads only bounded pinned compiler/native/template/profile files via verified HTTPS with HTTP200/no-redirect requirements. Downloaded Python executes without sudo. The only elevated program is fixed stdlib code creating new metadata: snapshot0700 and root-owned0600 binding.json/runtime-plan.json/stage-receipt.json; source/profile/plan hashes and input/plan readback are recorded. Existing snapshots/symlink/unsafe writable parent chains are refused, partial snapshots retained on failure with no blind retry. Temporary source is cleaned. No existing runtime config, container/image/network/rule/route/IAM/policy/token/database/provider/source job operation occurs. The root-owned metadata is not yet worker-mounted configuration.

The existing trust receipt `/etc/ouf/deploy-snapshots/semantic-provider-trust-20261002-212033/trust-receipt.json` is only referenced, not opened or copied. No CA/private leaf/receipt/OAuth key is read, regenerated or rotated. Receipt flags explicitly retain trustArtifactsRevalidated=false, liveConfigurationRevalidated=false, runtimeFilesMounted=false, providerCalls=0, notReleaseAcceptance=true. Current trust/role drift checks and actual nonroot config ownership/readonly individual leaf mounts remain installer gates. Actual previously observed Gateway UID/GID636:636 and adapter10006:10006 remain the role bindings to revalidate then. Offline ca.key must never enter a runtime mount.

Local targeted stage/compiler/native route/adapter PASS:30 tests,0 failures (8.740s). The three stage cases use fixture-only curl/no network and validate concrete lab compilation/private modes/source+plan hash readback, no downloaded-code invocation through sudo, no-overwrite, redirect/invalid binding/symlink/unsafe-parent refusal. New root cases run mandatory in the existing trust CI job; generic unprivileged request discovery may skip them only because that separate root gate runs them. All22 reported CI checks onbea029b4 completed successfully. Mandatory root jobs111050192318 and111050174692 run the3 staging cases with no skips (1.736s/1.935s) plus all8 existing trust tests; separate real APISIX OIDC/receipt/TLS, OCI packaging/network and native Docker/kernel lease-expiry gates remain green.

Next operator action: run the pinnedbea029b4 metadata-stage helper on a fresh `/etc/ouf/deploy-snapshots/semantic-provider-runtime-<UTC timestamp>` root with the explicit laboratory profile and the existing trust receipt reference. Expected RUNTIME_STAGE=PASS and private stage receipt, still NOT_RELEASE_ACCEPTANCE=true. Do not rebuild the staged adapter image a697bf75bf7d... / source52c0dcf11654..., repeat previous manual bridge/kernel fixtures, rotate OAuth/TLS artifacts, or replay frozen Cinema/Teatri. This stage is additive private configuration preparation only.

Next development/installation gates remain: dedicated-role APISIX TLS listener and SSL-resource matching (current route plan is not startup YAML), Java custom-CA truststore; governed registered provider endpoint/namespace, controlled DNS forwarding/all-answer TTL provenance/fail-closed lease refresh and persistence; isolated guarded networks/kernel readback, IPv6/offload/reboot/renewal/revocation and actual production workload bypass; real OIDC/receipt/provider exchange. Semantic PR#30 still inherits V10 and needs migration-aware release. Discovery authorization/HUMAN scopes/tenant-aware MCP, candidate/adopted exact RDF revision inspection, HUMAN-only governance, chatbot mapping, immediate approved-file ingestion/dedup and scheduler-first API vertical ingestion-to-UDP acceptance remain open. No complete release acceptance is claimed.

## 2026-10-02 — runtime stage observed; private TLS startup preparation

Operator receipt: SEMANTIC_PROVIDER_RUNTIME_STAGE=PASS, CONFIGURATION_COMPILED=true, PRIVATE=true at /etc/ouf/deploy-snapshots/semantic-provider-runtime-20261002-222530/stage-receipt.json. No container, network/rule, route/IAM/policy or provider call occurred. This closes only metadata staging; NOT_RELEASE_ACCEPTANCE=true remains. Reuse the existing trust receipt /etc/ouf/deploy-snapshots/semantic-provider-trust-20261002-212033/trust-receipt.json, adapter image sha256:a697bf75bf7d51afadadfaccd3d80537e9a5fb2a08f0d194c6dfd9462e812468 and source52c0dcf11654a4d3d0f17a6902ed095975466fb9.

Gateway PR#56 commit97654545436476ee8087c0952ee9ba170b3b8480 adds private scripts/prepare_semantic_provider_tls_runtime.py and documents its boundary in docs/SEMANTIC_PROVIDER_TLS_RUNTIME_PREPARE.md. It revalidates prior input/source/plan hashes, current immutable Gateway role and adapter image identity, detected UID/GID and existing trust artifacts; verifies both leaf/key pairs and exact hostname/signature/purpose/expiry. It never reads offline ca.key or requests/rotates OAuth. The existing southbound leaf is represented by an exact-SNI APISIX SSL resource; APISIX3.18 overwrites static certificate paths with placeholders, so leaf-path configuration alone is insufficient.

The dedicated role has one explicit TLS listener, HTTP/admin/control disabled, TLS1.2/1.3 and no fallback SNI. JSON-as-YAML config.yaml/apisix.yaml and adapter.json are written exclusively to a new private root0700 snapshot. Files are0600 and owned by detected runtime identities. apisix.yaml embeds the existing private leaf key; never print, publish or commit it. Individual readonly file mounts only; do not mount private snapshot directories wholesale or mount ca.key. Readback and full input revalidation precede the success receipt; verify checks exact bytes/bindings. Partial failures retain private artifacts without a success receipt; DO_NOT_RERUN_BLINDLY.

Mandatory root CI job111062967183 ran all4 new ownership/private-preparer cases without skips (0.399s), plus8 trust and3 metadata-stage cases. Actual APISIX job111062978798 passed the exact JSON-as-YAML startup encoding, single listener inventory, exact SNI and client hostname verification, OIDC→receipt→adapter TLS, upstream hostname mismatch rejection and fixture cleanup; only local fixtures, zero external provider calls. Earlier de3bb35d TLS increment also had all22 checks green; its APISIX jobs111058487265/111058467954 passed. Current complete CI result is recorded below.

Next operator step: download the original8 compiler/native/template files, TLS factory and trust/TLS helpers from immutable Gateway commit97654545436476ee8087c0952ee9ba170b3b8480; run python3 -B -m scripts.prepare_semantic_provider_tls_runtime in plan/apply/verify. Select the existing stage/trust roots above and a fresh /etc/ouf/deploy-snapshots/semantic-provider-tls-runtime-<UTC timestamp>. Explicit lab parameters: gateway-container ouf-apisix; expected ID dcbe26bed97dd5c7ac8a131ec2badf77b0291c2ef32907be639bfa09c36596d9; adapter image/source above; listen-address0.0.0.0, listen-port10443, ssl-resource-id semantic-provider-southbound-tls. These are installation data/CLI parameters, never software defaults or fixed deployment requirements. No listener or host port is activated at this step.

Expected SEMANTIC_PROVIDER_TLS_RUNTIME_PREPARE=PASS and private tls-runtime-receipt.json, still mountsInstalled=false, containersCreated=0, providerCalls=0, NOT_RELEASE_ACCEPTANCE=true. Do not rebuild existing images, regenerate certificates, rotate secrets, repeat prior manual kernel tests or replay Cinema/Teatri.

Remaining gates: individual trust/leaf mounts and private OIDC/provider-receipt env provisioning, Java custom-CA truststore; isolated guarded role networks/kernel readback and production bypass; governed provider endpoint/namespace, controlled DNS all-answer/TTL provenance and fail-closed leases/persistence; IPv6/offload/reboot/renewal/revocation, actual workload OIDC/Gateway/provider exchange. Semantic PR#30 includes V10 and needs migration-aware release. Discovery authorization/HUMAN scopes/tenant-aware MCP, exact adopted RDF revision inspection and HUMAN-only governance, chatbot mapping, immediate approved-file ingestion/UDP dedup, API endpoint/credentials→extraction profile→scheduler→timed ingestion remain unaccepted.

Complete CI readback on commit97654545436476ee8087c0952ee9ba170b3b8480: all33 reported checks completed successfully (11 named gates across three workflow contexts), no pending/failing checks. Fixture proof and staging remain separate from live release acceptance.

## 2026-10-03 Europe/Rome — private TLS prepared; Java trust gate

Operator completed TLS plan/apply/verify: SEMANTIC_PROVIDER_TLS_RUNTIME_PREPARE=PASS. Snapshot /etc/ouf/deploy-snapshots/semantic-provider-tls-runtime-20261002-230418; private receipt tls-runtime-receipt.json. Detected Gateway UID/GID636:636, proposed listener10443; files contain the existing southbound leaf key. No container/mount/network/rule/route/IAM/policy/provider activation occurred. Keep the files private; do not print apisix.yaml. This replaces the prior pending TLS-preparation action with observed completion only, NOT_RELEASE_ACCEPTANCE=true.

Gateway PR#56 commitd64ffc5117d476cbec3596c28ff7e74831549886 adds scripts/prepare_semantic_provider_java_trust.py, tests/test_prepare_semantic_provider_java_trust.py and docs/SEMANTIC_PROVIDER_JAVA_TRUST_PREPARE.md. It adds no application-code/image-payload change. Java HttpClients use the default SSLContext; the proposed private PKCS12 store preserves all public certificates from selected Semantic image cacerts and adds the existing internal CA, preserving public-IAM trust as well. The store contains no private key or credential; its changeit password is a public certificate-store format value, not an OAuth/TLS/MAC secret. No artifacts are regenerated or credentials rotated.

Explicit bindings: existing trust snapshot212033 and TLS snapshot230418; current Semantic ID7ae83be8c1fe9fe25774b7d748e35153652b29b2501886f89daeabb83bd1a147, image sha256:f6525f2512c72a600ebcbc7060d55355d86e0627487b655e7c5c6288a0be7fc6, sourcee7bc5190f9e6afbbc4cf3c90d5d4970afbfad14b. Proposed image Java home /opt/java/openjdk and future store target /run/ouf-semantic-provider/java-truststore.p12 are explicit CLI parameters, not product defaults. Numeric Semantic UID/GID are detected, not assumed. All role/path/network data remain parameterized.

Plan reads only bounded protected metadata and existing public CA/southbound leaf; verifies receipt cross-binding, artifact hashes, exact hostname/signature/purpose/expiry and selected immutable Semantic role/image/source. No private .key, apisix.yaml, MAC or OAuth file is read or mounted. Plan writes nothing and creates no helper. Apply creates an exclusive root0700 snapshot and runs one ephemeral keytool-only process from the already-local immutable Semantic image (--pull=never), network=none, readonly root, cap-dropALL/no-new-privileges and bounded CPU/memory/PIDs/tmpfs; the application entrypoint is overridden. Only the public CA readonly and new public-store output directory are mounted. Existing live containers are unchanged. Cleanup/readback, exact preservation of baseline certificate set plus one existing CA, safe ownership and unchanged input/role proof precede the success receipt.

Files: java-truststore.p12 and java-trust-options.json are0600 and owned by detected Semantic UID/GID; baseline.pem/merged.pem and intent/receipt are root0600. Verify checks exact output bytes/hash, certificate sets, permissions and bindings without another keytool container. Failed partial snapshots are retained without a success receipt; DO_NOT_RERUN_BLINDLY. Future installer must bind the individual store readonly into a traversable target and merge proposed JVM properties with existing Java options; never mount private root0700 snapshots wholesale. Future PR#30 candidate must prove equal baseline roots or explicitly prepare its selected-image truststore. Existing custom Java trust/options, if configured in another installation, require explicit reconciliation before activation.

Mandatory root CI job111067895411 ran all6 cases without skips (19.781s): real selected-image keytool conversion/import, all public roots preserved, real10001 ownership, current role/CA/output drift, no-overwrite/partial failure, redacted CLI and helper cleanup. Real Java21 HttpClient using the generated store accepted the controlled localhost leaf; wrong hostname and missing CA both failed. No external provider/token call. Fixture image retained exactly the pulled Temurin21 JRE layers; fixture keys are isolated CI only. Actual APISIX/kernel/OCI and older private staging gates remain separate.

Next operator action: download just the trust and Java helpers from immutable commitd64ffc5117d476cbec3596c28ff7e74831549886; python3 -B -m scripts.prepare_semantic_provider_java_trust plan/apply/verify with the explicit current bindings above and a fresh /etc/ouf/deploy-snapshots/semantic-provider-java-trust-<UTC timestamp>. Expected private java-trust-receipt.json; no runtime/mount/network/route/IAM/policy/provider activation. The only new server container is the temporary networkless keytool helper, removed before success; no Semantic application or source/job runs, no image rebuild or pull.

Still open: actual readonly trust/leaf mounts and private OIDC/provider-receipt env provisioning; Semantic PR#30 V10-aware backup/migration/rollback and candidate baseline reconciliation; isolated role networks/kernel readback and actual production bypass; governed endpoint/namespace, controlled DNS all-answer/TTL/fail-closed leases and persistence, IPv6/offload/reboot/renewal/revocation; actual workload OIDC/Gateway/provider exchange. Discovery authorization/HUMAN scopes/tenant-aware MCP, exact adopted RDF revision and HUMAN-only governance, chatbot mapping, immediate approved-file ingestion/UDP dedup, API endpoint/credentials→extraction profile→scheduler→timed ingestion acceptance remain open. No Cinema/Teatri or prior manual kernel fixture is replayed.

Complete CI readback on d64ffc5117d476cbec3596c28ff7e74831549886: all24 reported checks succeeded (12 named gates across push/PR contexts). Second mandatory Java job111067884636 also ran all6 cases without skips (58.523s) with the same real-keytool/Java21 positive and denial proof. Current fixture evidence is green; live release acceptance remains unproven.

## 2026-10-03 08:18 Europe/Rome — Java trust completed; DNS observation next

Operator JAVA_TRUST plan/apply/verify all PASS. Private receipt /etc/ouf/deploy-snapshots/semantic-provider-java-trust-20261003-061729/java-trust-receipt.json. Detected Semantic UID/GID10001:10001, containsPrivateKeys=false; publicRootsPreserved=true on apply and verify (plan intentionally did not perform keytool work). Current live containers unchanged, no runtime container/mount/network/rule/route/IAM/policy/provider activation. This closes private Java preparation only; NOT_RELEASE_ACCEPTANCE=true remains. Reuse prior trust212033, runtime222530 and TLS230418 snapshots. Do not regenerate keys/credentials, rebuild the adapter, repeat earlier manual fixtures or replay Cinema/Teatri.

Repository readback: Semantic PR#30 remains c2b4ae5abed1236378c7060b3eb3dac126672cbc with workload OAuth and inherited V10. The frozen RDF-read stage/release scripts pin e7bc5190 and cannot be reused blindly for that candidate or migration. No application/image change or release is requested by this increment.

Gateway PR#56 commit004a3855c7ee345fabce2cc1e1c0db0eb5dddae5 adds tools/semantic_provider_dns.py, scripts/inventory_semantic_provider_dns.py, tests/test_semantic_provider_dns.py and docs/SEMANTIC_PROVIDER_DNS_OBSERVATION.md. The frozen52c0dcf adapter build payload is unchanged. This is explicit resolver evidence only, not endpoint authorization, DNSSEC, provider connectivity, FQDN enforcement or kernel lease installation.

DNS queries go only to numeric resolvers/port from the selected private runtime binding: both A and AAAA through every resolver in the selected network family, recording other-family resolvers as deferred. Connected UDP verifies transaction/question/type/class; truncation uses bounded TCP framing on the same selected resolver, under a shared deadline. DNS message/record/name/compression/count limits, CNAME cycles/conflicts/8-hop limit and SOA-backed negative answers are enforced. All reachable queried addresses across both families/all selected resolvers are validated together; one forbidden/non-global-unregistered/CIDR-mismatched answer denies the entire observation. CNAME/address/negative TTL minimum is retained, observation time deducted and remaining lifetime capped explicitly. No provider HTTP/SPARQL/token call.

Snapshots are historical evidence only. Ordinary UDP/TCP DNS does not authenticate the resolver channel or validate DNSSEC; AD is metadata only. Re-reading a receipt never refreshes its TTL and must never authorize a static/permanent IP rule. The future isolated namespace needs fresh resolution, governed registration and a controlled DNS path/atomic fail-closed lease controller. This host observation does not prove those production gates.

Plan validates private stage binding/hash and source metadata without DNS or file writes. Apply creates a fresh root0700 snapshot and root0600 intent/observation/receipt after complete DNS/input/readback success. Verify checks historical byte/binding integrity without any query/lease refresh; leaseStillCurrentAtReadback may be false while historical verify passes. Failure retains private intent, no success receipt, and rejects blind reuse. No TLS key, receipt key or OAuth credential is read. CLI prints counts/currentness/private path only.

Local six pure/wire tests PASS, including actual local UDP truncation→TCP for A/AAAA and socket cleanup. Three private-root cases are mandatory in the CI ownership job; normal non-root discovery may skip them only because that separate root gate executes them. Current complete CI evidence is recorded below.

Next operator action after green CI: download the DNS tool, DNS inventory and unchanged trust helper from immutable Gateway commit004a3855c7ee345fabce2cc1e1c0db0eb5dddae5; python3 -B -m scripts.inventory_semantic_provider_dns plan/apply/verify with runtime-stage-root /etc/ouf/deploy-snapshots/semantic-provider-runtime-20261002-222530, fresh /etc/ouf/deploy-snapshots/semantic-provider-dns-<UTC timestamp>, source-commit004a3855c7ee345fabce2cc1e1c0db0eb5dddae5, timeout-seconds20/max-lease-seconds300. Endpoint/port/resolvers/CIDRs/family remain parameterized private installation data; no lab names/network defaults are embedded in product code. Expected DNS_INVENTORY=PASS with private dns-receipt.json, no container/network/rule/route/IAM/policy changes, providerCalls=0/kernelLeaseInstalled=false/NOT_RELEASE_ACCEPTANCE=true.

Still open: governed provider endpoint/namespace registration; controlled DNS forwarding/authenticatable policy, fresh all-answer TTL provenance inside isolated namespaces, atomic fail-closed expiring leases/refresh/persistence/readback; isolated role topology and real production workload bypass; IPv6/offload/reboot/renewal/revocation. Individual TLS/Java mounts, private OIDC/receipt env provisioning and selected-image baseline reconciliation are not installed; Semantic PR#30 needs migration-aware backup/history/rollback and real OIDC/Gateway/provider exchange. Discovery authorization/HUMAN scopes/tenant-aware MCP, exact candidate/adopted RDF inspection, HUMAN-only governance, chatbot mapping, immediate approved-file ingestion/UDP dedup and API endpoint/credentials→extraction profile→scheduler→timed ingestion acceptance remain open.

Complete CI readback on004a3855c7ee345fabce2cc1e1c0db0eb5dddae5: all24 reported checks succeeded (12 named gates across push/PR contexts). Mandatory root jobs111146671666/111146664310 each ran all9 DNS cases with no skips (0.022s/0.018s), including actual UDP/TCP peers, alongside prior8 trust/3 metadata/4 TLS tests. Actual APISIX, Java trust, OCI and native Docker/kernel gates remained green. Fixture evidence is not production release acceptance.

## 2026-10-03 08:38 Europe/Rome — DNS observation completed; atomic lease refresh gate

Operator DNS plan/apply/verify all PASS, private receipt /etc/ouf/deploy-snapshots/semantic-provider-dns-20261003-063746/dns-receipt.json. allAddressCount=1 and usableAddressCount=1; the lease was current at apply/verify readback. This is explicitly historicalEvidenceOnly=true/kernelLeaseInstalled=false. No container, network/rule, route/IAM/policy or provider HTTP/SPARQL/source operation changed. Never reuse this expiring snapshot to authorize a permanent/static address rule or extend admission later. Its address/TTL evidence closes host DNS inventory only; no governed registration, isolated resolver path, DNSSEC, authenticated resolver transport or runtime FQDN acceptance is claimed.

Reuse completed private trust212033, runtime222530, TLS230418, Java061729 and DNS063746 snapshots. The frozen52c0dcf adapter image/payload, current Semantice7bc5190 live software and prior Cinema/Teatri jobs remain unchanged. No key/secret rotation, image rebuild or previous manual packet/ingestion fixture replay is requested.

Gateway PR#56 commit52916801abb1b1e4914c5dd723df60a36b62f3c9 adds tools/materialize_southbound_lease_refresh.py and docs/SOUTHBOUND_LEASE_REFRESH.md. It compiles a single native nft batch replacing provider sets in both owned inet and bridge tables; it never executes nft, changes chains/static flows/shared tables, or consumes a saved DNS snapshot. All endpoint/ref/source/family/private-exception/table/interface limits remain explicit existing kernel bindings. Finite fresh monotonic resolution lifetime is rounded down, capped by configured lease limit and reduced by an explicit apply budget; output carries mustApplyByMonotonic. Missing/failed/stale/historical/invalid resolution empties every provider set, with no partial admission. Malformed ownership is rejected rather than naming an uncertain table; existing finite leases must expire.

This pure compiler does not authenticate evidence or implement the refresh worker. historicalEvidenceOnly=false dictionary metadata is not provenance. A future trusted owner must obtain fresh governed resolution inside the controlled namespace, compile immediately before execution, enforce the apply deadline, atomically install/read back both tables and revoke on late/failed readback. It must not retry old relative-timeout plans, restore stale wall-clock/monotonic evidence on reboot or infer full success from one family. Session/lifecycle/persistence/production ownership enforcement remains open.

Five pure refresh tests PASS locally. Existing mandatory actual nft/netns and Docker/native bridge packet tests now also refresh both owned sets, deliberately fail the last bridge statement to prove whole-batch rollback and clear admission on missing resolution. Existing new/established-socket lease expiry, unregistered-workload/port denial, shared rule structure and cleanup requirements remain. These controlled CI proofs do not request another target-VPS manual fixture.

PET recheck: Gatewayv1.5 requires distinct north/south deployments, no public southbound Service, default-deny networking, explicit necessary flow openings and approved source/route bindings. This increment preserves that separation and adds no generic Internet permission. The next host input is current parameterized Docker bridge/workload binding readback before compiling/creating new isolated roles. Reuse scripts/inventory_semantic_provider_network.py at immutable52916801 commit; readonly parameters gateway-containerouf-apisix, expectedGatewayIDdcbe26bed97dd5c7ac8a131ec2badf77b0291c2ef32907be639bfa09c36596d9, semantic-containerouf-semantic, ingestion-containerouf-ingestion are lab CLI data, not product defaults. No network or rule creation is requested yet.

Remaining gates: controlled DNS forwarding/authenticatable policy and fresh resolution provenance inside isolated namespaces; governed endpoint/namespace registry; trusted refresh worker, atomic deadline/readback and fail-closed reboot/persistence; isolated role topology and actual production workload bypass, IPv6/offload and CA renewal/revocation. Individual TLS/Java mounts/private OIDC/receipt provisioning and candidate baseline reconciliation are not installed. Semantic PR#30 c2b4ae5abed1236378c7060b3eb3dac126672cbc needs V10-aware backup/history/rollback and real workload OIDC/Gateway/provider exchange. Discovery authorization/HUMAN scopes/tenant-aware MCP, exact adopted RDF inspection/HUMAN-only governance, chatbot mapping, immediate approved-file ingestion/UDP dedup and API endpoint/credentials→extraction profile→scheduler→timed ingestion acceptance remain open.

Complete CI readback on52916801abb1b1e4914c5dd723df60a36b62f3c9: all24 reported checks succeeded. Mandatory kernel job111149565426 ran9 netns tests (10.163s) and the actual Docker bridge packet test (17.040s), emitting ATOMIC_INET_BRIDGE_REFRESH=true, FAILED_BATCH_ROLLBACK=true and MISSING_RESOLUTION_REVOKED=true in both environments; actual Docker cleanup PASS. Prior DNS/private ownership, TLS/APISIX, Java trust, OCI and pairwise regressions remain green. This closes controlled atomic-refresh fixture proof only, not a deployed worker or production release.

### 2026-10-03 — topologia invariata e preparazione reti dedicate vuote

L'operatore ha ripetuto l'inventario read-only: snapshotHash `8b0eb1c691a5010f98f22e34bb3de8de0b65cf8f9bab3079fc6c193778b857d4` identico. Gateway `dcbe26bed97dd5c7ac8a131ec2badf77b0291c2ef32907be639bfa09c36596d9`, Semantic `7ae83be8c1fe9fe25774b7d748e35153652b29b2501886f89daeabb83bd1a147` e Ingestion `1fa5450574e72ef15ebb2c74e0f421f04d24c842975e324ac958f071672fbb7e` conservano i collegamenti osservati. Bridge condivisi backend/control osservati; nessuna regola o container modificato da questo inventario. Non è una prova atomica né default-deny installato.

Gateway PR56, commit `796476521ad5d43047680775ad54aaee7b0ed278`, aggiunge `scripts/prepare_semantic_provider_networks.py`: plan/apply/verify con identificativi di installazione, nomi delle reti/bridge/tabella, snapshot e strumenti espliciti. Il profilo seleziona esplicitamente IPAM IPv4 automatico Docker; nessuna subnet, rete, porta o dominio diventa un default di prodotto. Apply installa in una sola transazione due tabelle nft esclusive inet/native bridge, con catene di negazione verificate, PRIMA di creare due reti vuote (trasporto interno ed egress). Controlla sovrapposizioni rispetto a tutte le reti Docker, route e indirizzi locali preesistenti. Nessun workload attuale viene collegato. Nessun container runtime, accesso provider/DNS, modifica IAM, route applicativa, policy, credenziale o job sorgente.

La preservazione delle regole condivise riguarda l'installazione delle nostre tabelle: Docker crea le proprie regole di rete/NAT per le nuove reti, esplicitamente riportate nella ricevuta. Intent, regole, readback, journal degli ID e ricevuta sono privati root. Gli ID/configurazioni delle nuove reti, assenza di endpoint, collegamenti esistenti e struttura delle regole vengono verificati; contatori non fanno drift. Un errore conserva risorse parziali protette e journal per riconciliazione: `DO_NOT_RERUN_BLINDLY`, nessuna cancellazione di risorse non identificate.

Gate reale Docker/nft job `111152287070`: 2 test senza skip, 3.520s, plan/apply/verify, blocco effettivo sullo stesso bridge, rifiuto endpoint inattesi e alterazioni, cleanup completo. Nello stesso job passano anche 9 test netns (10.147s) e 1 test packet Docker (17.005s), incluse scadenza connessioni nuove/aperte e refresh atomico/rollback/revoca. Provider calls=0. Il primo tentativo CI ha individuato la creazione di tabelle prive delle catene: corretto prima di qualunque esecuzione sul VPS, con readback esplicito e test packet. Le verifiche locali non sostituiscono questi gate reali.

Prossimo intervento operatore: preparare SOLO le due reti vuote/protette contro lo snapshot corrente. Non ricostruire adapter, non rigenerare PKI/TLS/Java trust/OAuth, non ripetere Cinema/Teatri. I materiali già preparati restano validi da riconciliare al momento delle future mount. La ricevuta DNS 063746 resta storica e non viene trasformata in una regola permanente. Rimangono da completare worker DNS fresco e lease/lifecycle/reboot, mount e autenticazione runtime, registrazione governata, ammissione provider e rollout Semantic con migrazioni V10; nessuna accettazione release/end-to-end implicita. File: ingestion/dedup immediati dopo onboarding approvato. Verticali: THS endpoint/credenziali → THS profilo → mapping/governance → scheduler → ingestion automatica nei tempi configurati.

CI sul commit indicato: 24/24 check riportati verdi, readback GitHub; staging/CI non equivalgono ad accettazione di release.

### 2026-10-03 09:20 Europe/Rome — reti dedicate preparate sul VPS

L'operatore ha eseguito il blocco Gateway `796476521ad5d43047680775ad54aaee7b0ed278`: `SEMANTIC_PROVIDER_COLD_NETWORKS=PASS` nei tre modi plan/apply/verify. Plan riporta EMPTY_NETWORKS=0 (nessuna creazione); apply e verify EMPTY_NETWORKS=2. Ricevuta privata: `/etc/ouf/deploy-snapshots/semantic-provider-networks-20261003-072023/prepared/network-receipt.json`. Non ripetere apply, creazione reti o preparazioni TLS/Java/OAuth/adapter già riuscite.

Installati i due bridge dedicati dietro le tabelle di blocco iniziale; nessun container collegato, nessuna chiamata provider, nessuna modifica IAM/route applicative. Il controllo dei pacchetti in produzione resta NON provato e NOT_RELEASE_ACCEPTANCE=true: reti vuote e readback strutturale non equivalgono a runtime operativo, egress governato, DNS refresh, TLS o ammissione workload. Reti/IPAM/bridge sono parametri della specifica installazione; nessuna subnet del laboratorio può entrare come costante di prodotto.

Prossimo dato necessario: readback read-only degli ID e IPAM assegnati automaticamente alle due nuove reti `ouf-semantic-provider-internal` e `ouf-semantic-provider-egress`, inclusi bridge e assenza di endpoint. L'output PASS fornito non contiene subnet/gateway; non inferirli dalle reti condivise o dai nomi Docker. Servono per vincolare indirizzi riservati e flussi esatti del futuro runtime. Si riusano i gate packet reali CI già verdi; nessun replay Cinema/Teatri o sorgenti. Proseguono i gate aperti per owner DNS fresco e lease monotonic, lifecycle/readback/revoca/reboot, infrastruttura/DNS proxy, mount individuali, autenticazione, registrazione governata e release Semantic migration-aware. Nessuna policy pubblicata né provider abilitato da questo passo.

### 2026-10-03 09:26 Europe/Rome — readback IPAM e owner lease DNS/nft

Readback operatore: rete interna `ouf-semantic-provider-internal`, ID `2a6652422b45db6f359d94d779ab8625b1ad99b1750bb54582b4b8c4e8aa9307`, bridge `oufsp-int`, internal=true, IPv6=false, subnet `172.21.0.0/16`, gateway `172.21.0.1`, endpoints=0. Rete egress `ouf-semantic-provider-egress`, ID `db8bc9f8feccc3c14f2818a5c843f5c08e5eb2e192530858d88a70ce1cc0a86d`, bridge `oufsp-egress`, internal=false, IPv6=false, subnet `172.22.0.0/16`, gateway `172.22.0.1`, endpoints=0. Sono fatti di questa installazione, non default o costanti software. Riutilizzare la ricevuta reti 072023/prepared già verificata, non ricreare risorse.

Gateway PR56 commit `00e7b750b8b90878eaa7f8657accdd5e4d9feca6`: aggiunti `tools/semantic_provider_lease_owner.py` e `tools/semantic_provider_lease_nft.py`. Il nucleo lifecycle non accetta snapshot DNS: effettua una nuova osservazione ad ogni ciclo, usa deadline monotonic conservative, verifica struttura installata attesa, applica una volta un batch atomico alle due famiglie e legge indirizzi/TTL rimanenti. DNS fallito, deadline superata, differenza indirizzi o estensione TTL causano revoca di tutti i set; revoca non dimostrata NON produce PASS. Nessun retry della stessa TTL relativa. Backend nft con comandi/deadline espliciti, hash strutturale atteso proveniente dall'installer fidato; non crea/adotta tabelle o autorità.

Sei test avversariali del lifecycle e cinque del compilatore passano. Gate CI reale job `111156948070`: 9 test netns in 11.388s (owner nft reale con DNS stub esplicitamente marcato), 1 test Docker in 18.833s con DNS UDP locale reale A + AAAA/negative SOA, owner, refresh/readback inet+bridge e rifiuto packet dopo DNS indisponibile. Rimangono verdi scadenza socket aperti, rollback atomico e bypass workload non registrato. 2 test cold networks in 3.901s e cleanup completo. Check GitHub sul commit: 24/24 verdi. Nessun provider pubblico chiamato o sorgente/job OUF ripetuto. Payload e immagine adapter staged restano invariati.

Questa è implementazione del nucleo e backend, NON daemon installato o accettazione production. Installer deve vincolare configurazione governata/hash struttura, supervisore/cadence, avvio deny-only, arresto/revoca e riavvio senza lease storiche. Prossimo dato host necessario: init/supervisore e percorsi/versioni Python, nft, ip, Docker, systemctl per compilare l'installazione parametrizzata senza presumere percorsi o servizio disponibili. Non modificare regole/reti/runtime durante questo inventario. Restano aperti mount individuali/credenziali, proof DNS-proxy/bypass e lifecycle production, registrazione provider, ammissione e Semantic migration-aware. Policy 38 e preparazioni TLS/Java/OAuth/Cinema/Teatri restano da riutilizzare; nessuna nuova pubblicazione o release implicita.

### 2026-10-03 09:39 Europe/Rome — daemon lease, systemd e pacchetto privato

Inventario operatore: init=systemd; Python `/usr/bin/python3` 3.13.5; Docker `/usr/bin/docker` 29.8.1; ip `/usr/sbin/ip` iproute2-6.15.0/libbpf1.5.0; nft `/usr/sbin/nft` v1.1.3; systemctl `/usr/bin/systemctl` systemd257. Questi percorsi/versioni sono dati del VPS, non default installativi.

Gateway PR56 commit `7a81cc344b513d04fd276cd1923a9c23197aceee`: daemon `scripts/run_semantic_provider_lease_owner.py`, compilatore `tools/materialize_semantic_lease_service.py`, staging `scripts/stage_semantic_lease_package.py`. Configurazione JSON root-private sigillata tramite SHA, duplicate key negate, lock esclusivo root0600, rilettura della configurazione a ogni ciclo. Avvio e arresto revocano i set; ogni refresh interroga DNS nuovo. Configurazione alterata, proprietà sconosciuta o revoca non provata non producono PASS; lease kernel finite restano fallback. Processo senza API e senza dump di configurazioni/errori arbitrari. Compilazione unità con percorsi/dependency/timing espliciti, sola CAP_NET_ADMIN, NoNewPrivileges e filesystem/address families limitati. Nessuna installazione/enable/start implicita.

Factory kernel con opzione esplicita `empty_provider_sets=True`: crea set a timeout vuoti e i relativi vincoli, senza seed DNS né indirizzi inizialmente ammessi. LeaseOwner/backend/refresh accettano configurazioni con addresses=[] usando questa validazione; il refresh valido deve comunque ottenere indirizzi nuovi dal DNS e validarli normalmente. Il normale factory senza questa opzione conserva la validazione precedente. Il pacchetto staged comprende 9 file root-private e ricevuta SHA; plan/apply/verify non installano unità, non avviano daemon, non cambiano regole, non fanno DNS/provider né toccano credenziali o sorgenti.

Gate reale systemd/nft/DNS job `111159948330`: 3 test senza skip in 2.168s, configurazione sigillata/tamper, lock esclusivo, package staging/tamper, servizio reale con DNS locale A/AAAA, revoca all'arresto, DNS fresco dopo restart e negazione dopo DNS indisponibile; cleanup servizio/file/tabelle completo. Un errore iniziale nella prova confondeva lease seed del fixture con quelle del servizio: corretto aspettando anche nuove query DNS, poi il fixture è passato con scaffold inizialmente vuoto. Check GitHub sul commit: 26/26 verdi. Le prove packet native/Docker, OIDC/TLS e trust restano verdi; nessun job/sorgente OUF o provider pubblico eseguito.

Prossimo passo operatore: preparare SOLO il pacchetto privato source/receipt sul VPS, con commit pinned indicato; poi riusarlo nel bootstrap. Nessun daemon/unit installato dal passo. Rimangono aperti configurazione governata e hash struttura/custodia, ricostruzione guard prima di Docker al boot e ordine arresto/start, prova lifecycle reale sul VPS, DNS-proxy/bypass production, mount individuali/credenziali, registrazione provider, ammissione workload e Semantic migration-aware. Unit systemd da sola NON dimostra reboot sicuro: nft perde regole al reboot, quindi le nuove reti non devono ricevere workload prima della ricostruzione guard. Non abilitare runtime/uscite prima dei gate pertinenti; riusare reti 072023, trust/TLS/Java/OAuth/adapter, Cinema/Teatri e policy38 senza ripetizioni. Domain name, indirizzi, reti e porte continuano a essere parametri.

### 2026-10-03 09:59 Europe/Rome — pacchetto lease verificato e bootstrap deny-only

Operatore: `SEMANTIC_LEASE_PACKAGE=PASS` plan/apply/verify, FILES=9 ROOT_PRIVATE=true, nessun daemon/unit/regola/provider. Ricevuta privata `/etc/ouf/deploy-snapshots/semantic-lease-package-20261003-075940/source-package-receipt.json`, source commit `7a81cc344b513d04fd276cd1923a9c23197aceee`. Riutilizzare questo cohort immutabile: nessuna ristaging/ripreparazione dei 9 file.

Gateway PR56 commit `d7f65fc73a6beb0a36e77972301a4c823fe21c5d` aggiunge due script isolati: `restore_semantic_boot_guard.py` e `stage_semantic_boot_guard.py`. Stage verifica ricevuta/codice del pacchetto lease, le due reti ancora vuote con ID attesi e la struttura nft contro la ricevuta cold 072023/prepared. Il factory sealed deve rigenerare ESATTAMENTE il deny-only.nft originale. Produce privata configurazione hash-sealed, unità guard, drop-in Docker e ricevuta; non installa/pubblica file systemd, non chiama daemon-reload, non cambia regole, non avvia/riavvia Docker.

Restorer prima di Docker: se entrambe le tabelle dedicate sono assenti, le crea e popola in una singola transazione esclusiva e ne controlla footprint/logical structure + regole condivise preservate. Se entrambe sono già presenti e identiche, verifica senza riscriverle. Proprietà parziale o struttura diversa vengono negate, senza delete/adoption di regole estranee. Normalizzazione esclude handles/contatori/tempo residuo/metainfo, conserva significato di catene/hook/rule. Profilo root0600 con SHA in ExecStart, lock esclusivo root; nessun seed DNS/set provider/uscita. Unit guard ordinata Before del servizio Docker scelto; drop-in Requires/After più ExecStartPre revalida AD OGNI avvio Docker anche se guard oneshot rimane active.

Gate reale systemd/nft job `111163684935`: 3 test boot in 1.710s senza skip, ricostruzione dopo rimozione simulata delle tabelle, avvio di un servizio sostitutivo isolato dopo guard, rifiuto dopo alterazione su successivo start, ownership parziale negata, stage privato/tamper usando reti Docker reali vuote e pacchetto sealed, struttura condivisa preservata, cleanup completo. Nello stesso job 3 test lease/systemd/DNS in 2.248s passano. GitHub commit indicato: 26/26 check verdi. Il test NON riavvia Docker reale né host, quindi REAL_REBOOT_NOT_PROVEN=true; non confondere simulazione table-loss con reboot o accettazione production. Il primo tentativo aveva un errore nel filename chmod del fixture, corretto prima di fornire comandi VPS.

Prossimo intervento operatore: preparare SOLO artefatti bootstrap privati, leggendo cold-root `/etc/ouf/deploy-snapshots/semantic-provider-networks-20261003-072023/prepared` e lease package 075940. Percorsi python/nft/docker/unit/runtime directory espliciti; nomi rete/bridge derivati dalla ricevuta installativa, nessuna costante di prodotto. Successivo installer deve verificare grafo systemd reale/collisioni, preservare unit/drop-in preesistenti e backup, installare in modo riconciliabile senza restart Docker, verificare start guard nonmutante contro le tabelle presenti e ordine boot. Il futuro profilo runtime richiederà una transizione di custodia dal bootstrap deny-all agli scaffold/flussi governati: la presente configurazione zero-flow non è un'autorizzazione a sostituire tabelle live.

Restano aperti reboot/lifecycle target, DNS proxy/bypass production, configurazione governata e hash struttura del runtime, mount/credenziali, provider registration/admission, Semantic V10 migration-aware, HUMAN mapping/review/ACTIVE, file ingestion immediata e vertical scheduler nei tempi configurati, UDP identità/dedup e altri gate PET già registrati. Riusare Cinema/Teatri e preparazioni precedenti senza replay; policy38 e container attuali invariati. Nessuna release/end-to-end acceptance implicita.


### 2026-10-03 — Boot guard private staging verified on installation

Operator plan/apply/verify passed for source `d7f65fc73a6beb0a36e77972301a4c823fe21c5d`. Private receipt: `/etc/ouf/deploy-snapshots/semantic-boot-guard-20261003-083310/boot-stage-receipt.json`. The sealed lease package at `/etc/ouf/deploy-snapshots/semantic-lease-package-20261003-075940` and cold networks receipt at `/etc/ouf/deploy-snapshots/semantic-provider-networks-20261003-072023/prepared/network-receipt.json` were reused; no restaging of their source cohorts.

No systemd unit or Docker drop-in is installed, no daemon reload or rule change occurred, and no provider call was made. This receipt is preparation evidence, not release acceptance. Next gate: read-only inventory of the actual systemd Docker unit, dependency graph, command fingerprints, drop-in paths and proposed target collisions, together with sealed boot artifact hashes. Do not print unit contents, command lines, environment values, keys or tokens. Only after reconciling that inventory prepare the concrete installer and its rollback journal; preserve existing Docker settings and pre-start commands. Do not restart Docker or the VPS as part of this inventory.

Boot lifecycle CI proves reconstruction of lost owned tables before an isolated dependent service, and rejection of changed/partial ownership at each dependent start. A real VPS reboot and a production Docker restart remain unproven. The current boot configuration is deny-only with no provider leases; later runtime profile custody and empty-set bootstrap must be explicit. Network names, endpoints, paths, ports and service identities remain installation parameters. Cinema/Teatri and their source/ingestion runs remain frozen. HUMAN governance, file ingestion after onboarding, vertical scheduler activation, Semantic Discovery and UDP acceptance gates remain open.


### 2026-10-03 — Systemd inventory reconciled; boot installer prepared

The read-only VPS inventory passed. Selected Docker unit is `docker.service`, enabled/active/running with observed MainPID `1740`, fragment `/usr/lib/systemd/system/docker.service`, no existing drop-ins, no ExecStartPre and no daemon reload pending. Raw ExecStart fingerprint reported by the operator: `82a2a5c6dafa5db18f2080ca15a24d8147d56f6886b88c0450bf5079f3ce4d5f`. `nftables.service` is loaded but inactive/disabled. The proposed unit `/etc/systemd/system/ouf-semantic-boot-guard.service` and drop-in `/etc/systemd/system/docker.service.d/90-ouf-semantic-boot-guard.conf` are absent. Sealed staged artifacts were verified. No restart or rule change occurred.

Gateway PR56 now includes `scripts/install_semantic_boot_guard.py` at `39923852d93a3b0907edce91cf87e9386b11621b`. It reuses private stage `/etc/ouf/deploy-snapshots/semantic-boot-guard-20261003-083310`, pinned to original stage source `d7f65fc73a6beb0a36e77972301a4c823fe21c5d`, without changing the sealed lease package or adapter image. Required installation inputs are `--stage-root`, `--stage-commit`, `--snapshot-root`, `--unit-root`, `--systemctl-path`, `--analyze-path` and `--mode plan|apply|verify|rollback`; no deployment domain/network/port defaults are introduced. Operator must use Python `-B`.

Plan reads only and rejects collisions, existing pre-start commands/drop-ins, non-private staging/journal roots and deny-table drift. Apply records a root-private journal before creating only the new guard unit and dedicated drop-in; there are no pre-existing files to overwrite or restore. It verifies the installed dependency graph, calls daemon-reload, starts only the guard against already-present deny tables, and verifies Docker's PID, fragment, unit-file state and executable/argument definition remain unchanged. Runtime execution timestamps in systemd ExecStart are not command authority and may change on reload. Docker gains only Requires/After guard and one non-ignored ExecStartPre. The selected Docker unit already being enabled pulls the guard on future starts; no independent guard enable symlink or Docker restart is necessary.

Verify checks sealed artifacts, owned files, loaded graph and unchanged dependent process. A failed apply retains its private journal and partial artifacts; do not rerun apply blindly. Explicit rollback validates ownership/content first, removes only this installation's unit/drop-in, reloads systemd and stops only the guard, leaving Docker and deny tables intact. It rejects modified/foreign files. Interrupted installation before daemon-reload is covered. The initial install verify proves the running-process-preservation gate; it is not a post-reboot acceptance probe and its recorded PID must not be reused as permanent runtime identity.

Real native CI job `111168951151` passed 4 boot tests (no skip), including installing against an already-running isolated dependent, unchanged PID, loaded graph, artifact tampering refusal, rollback of owned files and recovery from failure after file creation/before daemon-reload. The existing 3 native lease lifecycle tests also passed. CI never restarts production Docker and does not perform a real reboot. Next operator action is plan/apply/verify installation with a fresh root-private journal directory. The VPS installation has NOT yet been executed or accepted; real reboot/production Docker lifecycle proof remains open. Provider calls remain zero; current boot custody is deny-only/no leases. Future runtime custody transition, governed authority, DNS-proxy/bypass/IPv6 lifecycle, candidate runtime mounts, PR30 migration-aware Semantic rollout, Discovery, HUMAN approvals, chatbot mapping, approved file ingestion, vertical scheduler and UDP acceptance remain open. Cinema/Teatri stay frozen.


### 2026-10-03 — VPS boot installation verified; embedded Docker DNS gate added

Operator plan/apply/verify passed using installer `39923852d93a3b0907edce91cf87e9386b11621b`, journal `/etc/ouf/deploy-snapshots/semantic-boot-install-20261003-103547/install-journal.json` (private). The sealed original boot stage `/etc/ouf/deploy-snapshots/semantic-boot-guard-20261003-083310` was reused. Unit and dedicated Docker drop-in are installed; loaded graph and guard were verified. Docker was not restarted, deny rules were unchanged, provider calls were zero. A real reboot/production Docker restart remains unproven; this is not release acceptance. No container image was rebuilt and no Cinema/Teatri source or ingestion job was replayed.

Gateway PR56 adds an independent opt-in real Docker embedded-DNS fixture at `b4c2faefb7a526c3455632212275633c60d826e7`: `tests/test_southbound_docker_dns.py`, invoking the unchanged `tools/materialize_southbound_kernel.py`. It uses one new egress-capable bridge, unique owned inet/bridge tables and four temporary containers from the already-selected digest-pinned Python image. Default deny is installed before fixture containers start. Only numeric local DNS peers are used; no external resolver, provider, OIDC/token, source acquisition or ingestion call is made.

Native CI job `111186656897` passed the new test (1 test, no skip, 12.617s). It demonstrates UDP/TCP queries and A/AAAA answers through Docker's embedded resolver, observed source IP equal to the authorized container, denial with no DNS flow, denial to a non-selected peer, denial for an unregistered container, renewed denial after flow removal, unchanged shared rule structure and cleanup of owned temporary resources. This is CI proof for its explicitly configured numeric non-loopback resolver profile, not target-host proof or permission to accept Docker host/loopback resolver forwarding. Runtime binding must retain the explicit resolver list and reject loopback/unsafe resolver inputs. Production networks remain cold/deny-only with no provider leases.

Next operator action: run ONLY this new fixture on the VPS Docker 29.8.1, from the pinned test/compiler source cohort with Python `-B` and the already-cached digest-pinned Python image. It must not attach to the two prepared production provider networks or modify the installed boot guard, shared firewall rules, live container configurations or production Docker service. It creates and cleans up its own fixture network, four containers and unique two-family table; Docker creates/removes the corresponding fixture networking rules. A failed run requires retaining the private source root/output and scoped reconciliation, not blind repeated execution.

After target DNS evidence, remaining production gates include actual boot/restart acceptance, explicit runtime profile/empty-provider-set bootstrap custody transition, governed source/provider authority, distinct southbound deployment/configuration/IAM role bindings (do not silently copy a northbound credential), selected addresses/mounts/stopped candidates, IPv6/spoofing/bypass lifecycle, native Semantic image and migration-aware PR30 rollout, truststore/public roots consistency, provider workload admission, Discovery HUMAN/MCP bindings, chatbot mapping/HUMAN ACTIVE, approved-file ingestion, vertical scheduler and UDP identity/materialization. All installation network/domain/port/identity/path data remain parameters; original manual source-run evidence stays frozen.


### 2026-10-03 — Target embedded-DNS fixture passed; candidate input inventory next

On target Docker 29.8.1, operator root `/etc/ouf/deploy-snapshots/semantic-docker-dns-20261003-105129` ran the pinned `b4c2faefb7a526c3455632212275633c60d826e7` test/compiler cohort. `SOUTHBOUND_DOCKER_DNS=PASS` and cleanup passed; 1 test ran in 15.661s, no skip. UDP/TCP A/AAAA, proxy source equal to the registered container, default deny, refusal of unselected resolvers and unregistered clients, denial after rule removal, shared rule structure preservation and removal of own temporary containers/network/table are proven for this fixture profile. Provider and external DNS calls were zero. The prepared production provider networks and installed boot guard were not activated or changed by this fixture. This does not prove IPv6, host/loopback DNS forwarding, production candidate connectivity or reboot/restart acceptance.

Next: `scripts/inventory_semantic_provider_candidate_inputs.py` on Gateway PR56 at `39d471b80b527f0f2356dd2f594cfb52124817a7`. This read-only helper links existing runtime-plan, trust and TLS receipts; verifies sealed adapter configuration, public CA/trust/certificate hashes, selected certificate hostname/purpose/remaining validity, current gateway ID/image/user/running state and the already-staged adapter image revision/payload/entrypoint. Private-key and receipt-key files are checked only for owner/mode/path metadata; their contents are not read. This is a partial pre-mount input inventory: key-pair/content integrity must be rechecked before mounting, and it explicitly reports candidateCreationReady=false and southboundCredentialProvisioningProven=false.

The selected OIDC client ID comes from the two sealed southbound route definitions rather than a new hardcoded account. The helper uses the existing kcadm session to read only clientId/enabled/publicClient/serviceAccountsEnabled/clientAuthenticatorType, never any client-secret or token endpoint. It does not create clients, alter mappers/scopes, retrieve credentials, rotate keys, mount files, create/start containers, reload systemd, alter rules/routes/policy, rebuild images or invoke source/ingestion/provider jobs. Any profile/credential decision remains based on that actual inventory and PET northbound/southbound separation; no new IAM client or copied northbound credential is silently required or provisioned. `KCADM_SESSION_EXPIRED` requires the operator's normal session renewal, without printing login/session credentials.

Operator inputs remain explicit: TLS root `/etc/ouf/deploy-snapshots/semantic-provider-tls-runtime-20261002-230418`, trust root `/etc/ouf/deploy-snapshots/semantic-provider-trust-20261002-212033`, runtime root `/etc/ouf/deploy-snapshots/semantic-provider-runtime-20261002-222530`, selected gateway `ouf-apisix`, IAM container `ouf-keycloak`, kcadm `/opt/keycloak/bin/kcadm.sh`, realm `ouf`, Docker `/usr/bin/docker`, OpenSSL `/usr/bin/openssl`, minimum certificate validity 600 seconds for this inventory. These are lab invocation data, not product defaults. The adapter image remains `sha256:a697bf75bf7d51afadadfaccd3d80537e9a5fb2a08f0d194c6dfd9462e812468` from `52c0dcf11654a4d3d0f17a6902ed095975466fb9`; no software/container rollout is performed.

Retain the boot install journal `/etc/ouf/deploy-snapshots/semantic-boot-install-20261003-103547/install-journal.json`, cold network/lease/trust/TLS/Java receipts and all prior source/job freeze evidence. Remaining gates include staged runtime candidates and exact addresses/mounts, guarded runtime profile/empty-provider-set custody transition, IPv6/spoofing/bypass lifecycle, actual reboot/production Docker lifecycle, governed provider/source authority and workload admission, migration-aware PR30/native Semantic image and Java public-roots verification, Discovery HUMAN/MCP bindings, chatbot semantic mapping with HUMAN ACTIVE governance, immediate approved-file ingestion/UDP identity, and vertical scheduler configuration then timed ingestion. Cinema/Teatri and their existing manual run evidence remain frozen.


### 2026-10-03 — Candidate inventory metadata block retained for diagnosis

Admin kcadm session was renewed successfully before the candidate input inventory. Root `/etc/ouf/deploy-snapshots/semantic-candidate-inputs-20261003-111502` returned `BLOCKED CODE=ARTIFACT_METADATA_DRIFT NO_CHANGES=true NO_SECRETS_PRINTED=true` from source `39d471b80b527f0f2356dd2f594cfb52124817a7`. This does not establish a bad IAM session or modified credentials: the block is in local artifact metadata validation, before the IAM client query completes. No mounts, candidates or runtime changes occurred.

Source review found the new inventory applies a generic 131072-byte limit to all files, including the public trust bundle. The earlier trust preparator permits public artifacts up to 1048576 bytes and intentionally preserves system public roots. An oversized valid public bundle is a possible false positive, not yet confirmed on the target. Next operator action is scoped stat-only readback of receipt/config/public-trust/leaf artifact UID/GID/mode/size/link/type metadata; never cat keys, print raw unit/config/environment contents, chmod artifacts, rotate credentials, regenerate trust, rebuild images or repeat source runs to clear this block. Correct only the inventory contract after evidence establishes the cause; retain all original prepared receipts and the blocked source root.

Login correction: interactive shell read prompts must be run one line at a time, waiting for input, because pasting subsequent commands may feed them into read. `oufadmin` is the VPS user and must not be assumed to be the Keycloak admin. Use the operator's known admin identity/realm and kcadm interactive password; do not place passwords in command arguments or output. The actual renewed admin session is retained.


### 2026-10-03 — Confirmed oversized public-bundle false positive; inventory-only correction

Target stat readback confirmed every listed artifact is a regular single-link file with the expected owner/group/mode. The public `trust-bundle.pem` is 225117 bytes, root:root 0644; CA is 668 bytes/root:root 0644. Receipts/configuration and both role leaf/receipt-key metadata match the original preparation contract. The candidate inventory's generic 131072-byte cap was the cause of the metadata block; stat alone does not replace content hash/key-pair checks.

Gateway PR56 source `840abe970bde4ab1edc1c6aeecd84eee9d1fc5a8` raises ONLY the public CA/trust-bundle metadata limit to 1048576 bytes, matching the existing trust preparator. Private files and JSON keep the 131072-byte default and all original owner/group/mode/type/link/ancestor checks. No existing server artifact, credential, image, container, route, rule, policy or database is changed. The original 225117-byte bundle and original prepared receipts are reused; no certificate regeneration/credential rotation/rebuild/source replay is needed.

Three real-filesystem regression tests pass locally and in root CI job `111192199824` (3 tests, no skip, 0.003s): the exact target-sized public bundle is accepted; the same-sized private file/JSON is rejected; public files above 1 MiB, wrong owners/modes, hardlinks and symlinks remain rejected. The workflow now explicitly tracks the candidate inventory and runs this regression under the root-owned fixture profile.

Next operator action: download the pinned corrected script into the existing private source root `/etc/ouf/deploy-snapshots/semantic-candidate-inputs-20261003-111502` under a NEW filename `inventory-public-trust-fix.py`, preserving the blocked `inventory.py`; verify SHA256 `7bbf6a50722f475323b33568e3bc875b57d7f3e3de78d62c8f7410442c48c6c9`, then repeat the same read-only CLI invocation and all original explicit root/role/realm/tool/certificate-window parameters. This retry is scoped to the diagnosed false positive, not an apply rerun. Candidate creation, credential provisioning, private-key content/pair checks before mounts and all previously enumerated production/pipeline gates remain open. kcadm admin session has been renewed; renew again only if an actual expiry blocks its metadata query.


### 2026-10-03 — Candidate inputs verified; private OIDC validator preparation

Operator read-only candidate inventory now PASS: preserved receipts/configuration, reused adapter image/user and leaf validity proven; zero candidates, no credential retrieved, no runtime/route/IAM writes. Existing validator client `ouf-api-gateway` is enabled, confidential, `client-secret`, with serviceAccountsEnabled=false. This passive bearer-token validator is distinct from calling SERVICE workload `ouf-semantic`; no service-account enablement or grant is requested.

Gateway PR56 commit `faaf43748648207f51edee890be4b3dc6592cfc5` adds `scripts/prepare_semantic_southbound_validator_credentials.py`, invoked as a Python -B module with its pinned inventory dependency. Plan repeats sealed input/role checks and IAM metadata reads only. Apply GETs only the selected existing client secret into a new root0700 private directory, with role-owned0600 `client-secret` and root0600 intent/receipt; verify compares current client profile/secret and local sealed intent/hash without overwriting drift. No secret rotation, IAM configuration writes, token grant, provider call, mounts, container switch, route or policy changes. Source/realm/tool paths/prepared roots/certificate window are explicit parameters. A preexisting or partial target requires reconciliation, never blind apply rerun.

Native root CI job `111194749526` passed the credential regression, including real636:636 ownership and private permissions, plan metadata-only, false service-account flag accepted, IAM-secret drift refuses overwrite, target collision/tampered intent rejected, invalid secret/public client denied. Local mapped-root environment cannot assign636:636: three ownership cases skip locally and are mandatory with OUF_VALIDATOR_FULL_OWNER_TEST=1 in CI; metadata tests remain local PASS. Credential preparation has NOT been executed on the VPS yet. Before mounts, private-key content integrity/pair checks remain mandatory. Candidate creation, live workload admission/leases/DNS/TLS tests, Discovery HUMAN/MCP gates and full acquisition-to-UDP acceptance remain open. Historical DNS is not a live kernel lease. Cinema/Teatri stay frozen; no source/job replay.


### 2026-10-03 — Validator credential copied and verified on target; launch-input gate

Operator at 13:40 Europe/Rome confirmed pinned source checksums and plan/apply/verify PASS for Gateway source `faaf43748648207f51edee890be4b3dc6592cfc5`. Target `/etc/ouf/deploy-snapshots/semantic-southbound-validator-20261003-114001/prepared/credential-receipt.json` is private. Apply created a dedicated636:6360600 copy of the existing validator secret; verify matched current IAM/profile/receipt. No secret rotation, IAM writes, token grant, container/route changes or provider call occurred. This is preparation, not runtime/token-admission or release acceptance. Do not recreate the credential root or replace its sealed two-file source cohort.

Next Gateway PR56 source `732d65a8bcebb1545086702da54ee01c01c3b823` adds module `scripts.prepare_semantic_provider_launch_inputs`. It reuses the unchanged inventory/validator dependency contents and explicitly verifies the original validator source commit faaf437..., current credential profile/secret, prepared TLS/runtime bindings and live role/image. It reads only role leaf keys/receipt keys, hashes against BOTH original trust and TLS-runtime seals, locally loads each certificate/key pair with SSL, compares receipt-key pair, and hashes private APISIX config.yaml/apisix.yaml. Offline ca.key is never read. Plan reads these private inputs but creates no file. Apply prepares root0700 snapshot containing root0600 southbound.env with ONLY the two secret variable names selected by the sealed binding and a private launch-input receipt; verify compares without overwriting drift. No container, mount, network/rule, IAM, route, policy, source/job replay or provider call is authorized by this helper. No hardcoded installation identity, name, endpoint, port or domain is added to product code.

The helper's source and both immutable dependencies must be fetched from pinned commits and SHA256 checked; original credential-source contents remain unchanged. CLI requires explicit mode/source and validator-source commits, snapshot/credential/trust/TLS/runtime roots, gateway/IAM container/realm/tool paths and certificate window. A preexisting/partial snapshot or changed private input blocks and is retained for reconciliation. After successful private launch-input preparation, stopped-candidate manifest/mount validation and kernel-flow/boot-profile transition still need implementation and host evidence before start; candidateCreationReady must not be inferred from this preparation. The historical DNS receipt remains non-authoritative for live leases. Source Cinema/Teatri and live northbound gateway remain frozen.


### 2026-10-03 — Launch-input native evidence and deterministic signature test

Launch-input preparator source remains pinned `732d65a8bcebb1545086702da54ee01c01c3b823`, SHA256 `4a5483d5ff54bdc79ef26e4ae436ac41ebd12363be0640005d1d6f695df93e8d`. Native root job111195899535 passed all5 launch-input cases in0.098s without skip: real private env ownership, plan/apply/verify, altered leaf hash, mismatched leaf/key despite matching receipt hashes, altered private APISIX config, environment-name collision and existing-root denial. In the local mapped-root workspace, these5 role-owner fixtures must skip; native CI enforces OUF_LAUNCH_FULL_OWNER_TEST=1 and fails rather than skip if636:636 cannot be assigned.

One general config-contract job on source732... failed the preexisting delegation signature-tamper test. The test replaced Base64 tail characters, which can change only unused padding bits and preserve the decoded MAC. Pure Base64 reproduction confirmed the false-positive case. Gateway test-only commit `8b1fadb31060cce4deaf3962691aa0aaf17f5865` decodes the MAC, flips one actual byte, asserts inequality and encodes it back. It changes no production software, staged payload, sealed validator dependency or prepared artifact. Config-contract native tests on that head have passed; the launch helper and its dependencies remain identical to their pinned cohorts. The full18 general head checks are tracked separately from the prior provider-workflow evidence. No host launch-input operation has been executed yet; next operator action prepares only private files and repeats all original checks before any future mount.


### 2026-10-03 — Launch inputs verified on VPS; stopped-candidate manifest preparation

Operator at14:52 Europe/Rome confirmed plan/apply/verify PASS for launch source732d65a8bcebb1545086702da54ee01c01c3b823. Private receipt `/etc/ouf/deploy-snapshots/semantic-provider-launch-inputs-20261003-124906/prepared/launch-input-receipt.json`: both leaf/private-key pairs and purpose receipt-key pair verified; offline CA private key not read; private southbound.env created and reverified. No container/mount/network/rule/route/IAM changes, grant or provider call. Initial14:49 plan blocked only on KCADM_SESSION_EXPIRED, before snapshot creation; after interactive admin renewal, the same staged source root was reused successfully. Do not regenerate credentials/TLS, replay sources or recreate these successful snapshots.

Gateway PR56 source `9596f450ccb2ee38730b147e22e58ceaafd52841` adds `scripts.stage_semantic_provider_candidates`, SHA256 cb04a31e4d13e182b08de2df75fa13a4ec01a7c0671239339451523f2dfc9f84. This step produces ONLY a private root0700/root0600 stopped-manifest.json, not Docker candidates. It reuses and verifies the exact launch/validator source cohorts and private inputs, original cold-network receipt IDs/bridge/owner/empty endpoint profile, original deny-only nft table hash, live gateway backend binding and gateway image/user. It reads image startup metadata only into a fingerprint; raw live environment/secret/mount inspection is never serialized or printed.

The manifest plans separate southbound and adapter roles with verified existing image IDs, explicit nonroot users, restart=no, no published ports, capDrop=ALL, bounded caller-selected memory/pids, exact read-only file mounts, selected numeric IPv4 DNS and TLS-bound container identities. Southbound is planned on the original backend plus the dedicated internal/egress networks; adapter only on dedicated internal/egress. Free IPv4 choices derive from observed IPAM/gateway/endpoints, not hardcoded installation addresses; addresses are NOT reserved and must be rechecked at a future creation transaction. Backend prefix/domain/name/target paths are explicit installation parameters. Caller-selected targets remain subject to image startup compatibility at creation/readiness. Current deployment profile remains IPv4; unsupported custom IPAM allocation requires an explicit profile rather than guessed addressing.

Plan creates no snapshot. Apply creates the private manifest and repeats input checks; verify compares without overwrite. Existing candidate name, occupied cold networks, altered network ID/config, changed deny table, changed launch seals or changed private receipt blocks and preserves evidence. startAuthorized=false and containersCreated=0 are explicit; this manifest is not release acceptance. Five real private-filesystem tests pass locally (no skip), covering plan/apply/verify, stopped/no-public-port/read-only-mount structure, secret non-serialization, cold-network/name/guard/ID collision denial, avoiding backend gateway/occupied addresses, manifest tampering and existing-root refusal. Root CI runs the same five; native runtime creation/start has not occurred.

Next operator action is plan/apply/verify of this private manifest using the existing launch root, validator root, TLS/trust/runtime roots and cold-network root `/etc/ouf/deploy-snapshots/semantic-provider-networks-20261003-072023/prepared`. Afterwards implement a reviewed stopped-create journal/readback/cleanup protocol before actual Docker creation, then a distinct guarded empty-set/static-flow/boot-profile custody transition before any start, lease daemon/admission/provider request or Semantic migration-aware rollout. Production Docker restart/reboot, workload/TLS/DNS/kernel gates, provider governance/Discovery HUMAN-MCP and full file/API scheduler to UDP gates remain open. Cinema/Teatri frozen and northbound gateway unchanged.


### 2026-10-03 — Stopped manifest target PASS; real Docker exposed automatic-IPAM blocker

Operator at15:05 Europe/Rome confirmed Gateway source9596f450ccb2ee38730b147e22e58ceaafd52841 checksums and stopped-manifest plan/apply/verify PASS. Private manifest `/etc/ouf/deploy-snapshots/semantic-provider-candidate-manifest-20261003-130410/prepared/stopped-manifest.json`; images reused, private mounts read-only, dedicated networks empty, original deny guard matched, no container created/address reserved/network-rule-route-IAM writes/provider call. START_AUTHORIZED=false. Source9596... full26CI checks were green. This proves a sealed plan, not that Docker accepts its static addressing.

Actual stopped-create development under PR56 found a necessary deployment correction BEFORE any VPS candidate creation. Real Docker rejects an explicit --ip on a network whose subnet was allocated automatically: DOCKER_EXPLICIT_IPAM_SUBNET_REQUIRED. The cold-network source796476521ad5d43047680775ad54aaee7b0ed278 created the two dedicated empty networks without --subnet; observing allocated IPAM/Subnet/Gateway does not establish user-configured-subnet support. Therefore the existing static-address manifest is NOT creation-ready despite its earlier PASS. No source/job/provider replay, image rebuild, credential rotation or certificate regeneration resolves this; keep all successful original artifacts and evidence intact.

Gateway source8c04d8fb6dd251407e8c86c583d40b53a66f1179 now contains `scripts/create_semantic_provider_stopped_candidates.py`: root-private transaction journal, immutable source/manifest custody, fixed create/connect/inspect verbs, ownership+ID+label+never-started checks, private mounts/env/image/command/DNS/resource readback, no ports/restart, no start/run/force-removal operation. Partial create/connect evidence is retained; cleanup discovers only transaction-labelled/recorded IDs, refuses foreign/running/previously-started containers, preserves the journal and removes no network/table/shared service. Original cold receipt lacks binding.explicit_subnets=true, so production plan/apply intentionally BLOCKS COLD_IPAM_PROFILE_NOT_EXPLICIT_NO_CONTAINER_CREATED before any creation. DO NOT execute it against the current cold profile. A future explicit/dynamic addressing profile requires a new sealed manifest and guarded network/boot custody reconciliation, never editing historical receipts in place.

Docker also defers NetworkID/endpoint activation on CREATED containers. Readback now checks configured network name/current immutable ID, static IPAM request and aliases separately and records liveNetworkNamespaceProven=false/liveAddressAllocationProven=false/kernelLeaseInstalled=false. No stopped-create result is a live packet/lease/address proof. Native root job111212525183 passed4 real Docker cases in4.754s without skip: exact stopped creation/readback and owned cleanup; interrupted network connection/partial journal recovery; config drift and foreign-transaction cleanup rejection; automatically allocated subnet denies static IP whereas explicitly configured subnet accepts it. Fixture network subnets are daemon-selected then explicitly configured for the positive case, so no installation subnet is hardcoded. Only synthetic env/config are used; trusted IAM/TLS/manifest preflight composition remains covered by prior separate tests. No real provider/source or production process runs; fixture containers never start and owned resources are cleaned.

Next target action is `scripts.inventory_semantic_provider_static_ipam` from the same source8c04d8..., SHA256426d3aab4c05bb24a46b2c41279a6f6fc847b85d3fc6c2954d236200a4cc68a3. Explicit Docker path, cached immutable adapter image, inert /bin/false probe entrypoint, three expected network name=ID bindings and private snapshot root; no IAM session needed. Plan reads metadata only; apply tests static create on each selected existing network with an unguessable owned disposable container, never starts it, confirms CREATED/zero StartedAt/ownership and removes it. Expected Docker automatic-subnet rejection is recorded as staticIpSupported=false, not hidden or treated as runtime acceptance. Unknown failures block with no raw command/stderr/env/secret output and private probe intents retain ownership information. Apply/verify bind network ID/subnet/gateway/current free-address facts and private receipt; addresses remain unreserved. The cached adapter entrypoint is overridden with the explicit inert executable and never invoked; no adapter software/source job/provider call occurs. No shared container or network configuration is modified. This native auto-versus-explicit probe case already passed in the above4-case fixture.

Probe backend plus both dedicated network IDs. Dedicated network support is already disproven by source/CI; backend support is not assumed from visible subnet metadata. Do not recreate or normalize the shared backend network or restart Docker/active services. Use target findings to prepare a guarded correction confined to empty dedicated networks and a separately reviewed backend addressing profile; preserve deny-only protection and reconcile installed boot guard/manifest/lease bindings with any changed dedicated network ID/bridge ifindex before start. All runtime provider/workload/TLS/DNS/lease/HUMAN-MCP/Discovery, Java/semantic migration-aware rollout and complete file/API scheduler to UDP gates remain open. Cinema/Teatri frozen; no source/job replay.


### 2026-10-03 — Target static-IPAM accepted on all three networks; supersedes inferred normalization requirement

Operator at15:35 Europe/Rome confirmed static-IPAM source8c04d8fb6dd251407e8c86c583d40b53a66f1179 plan/apply/verify PASS. Private receipt `/etc/ouf/deploy-snapshots/semantic-provider-static-ipam-20261003-133526/prepared/ipam-receipt.json`: STATIC_IP_READY=true; backend113b5f0a3c53059b087a2ce997d2670cc057e88c0c17d4291b3b41a51ce26ba3, internal2a6652422b45db6f359d94d779ab8625b1ad99b1750bb54582b4b8c4e8aa9307, egressdb8bc9f8feccc3c14f2818a5c843f5c08e5eb2e192530858d88a70ce1cc0a86d each STATIC_CREATE_ACCEPTED_NOT_PACKET_PROOF with an owned probe created, never started and removed. Network configuration/shared services/provider/source jobs unchanged.

CORRECTION to the preceding entry: real CI rejected static addressing on its automatically allocated subnet, but that behavior must not be generalized to this installation. The target Docker accepts static create on all three existing networks, including the dedicated pair created without an explicit --subnet in the cold preparator. Source history plus visible allocated subnet alone establishes neither support nor rejection across daemons. No target network normalization/recreation, bridge-ID/ifindex change or boot-guard rebinding is currently required by IPAM. Keep the original cold/boot/manifest/trust/credential/launch artifacts unchanged. This supersedes the previously inferred cold-IPAM block and planned dedicated-network normalization requirement; it does not close runtime packet/lease/start gates.

Gateway PR56 source93e861fe8c8a43912f0cb78a74adceb2db509dd9 replaces the conservative explicit_subnets-history gate with actual verified target proof admission. New CLI --ipam-root and --ipam-source-commit bind the private source8c04d8... receipt. verify_ipam checks schema/source/hash/image, staticIpReady=true, no started containers/provider calls, all probes created+removed, exact manifest network name/ID sets and current driver/family/IPAM/subnet/gateway/internal metadata. Negative/incomplete/other-network/changed-network evidence blocks before Docker creation. The next-free probe address is not interpreted as a reservation or live endpoint; independent initial sealed-manifest preflight still rechecks planned availability. The proof hash is bound into the stopped-create journal and checked again after creation/verify. No cold receipt is rewritten or given a fabricated explicit-subnet flag.

Four real private-filesystem admission tests pass locally without skip, then in native root CI: positive target evidence accepted independent of subnet-history flag; false/started/provider-called/wrong-source/incomplete results denied; unrelated or changed current networks denied; changed next-free address does not become a claimed reservation. Native Docker fixture continues proving created/stopped configuration/ownership/recovery/cleanup with4 cases; its auto-allocation discovery assertion now records the daemon's actual result, while explicit allocation must be accepted, rather than assuming all daemons reject automatic subnet history. Trusted production IAM/TLS/manifest gates remain separately verified; synthetic Docker fixture never starts real or fixture processes/provider/source jobs.

Stopped-create helper source SHA2564babe7ebfdffe6ef1ab4f81bacad52c86eabbbe991d30bf3c41de65d7f47ffdd. Next operator action: stage this helper with the EXACT unchanged original stage/launch/validator/inventory source cohorts and static-IPAM helper426d3aab4c05bb24a46b2c41279a6f6fc847b85d3fc6c2954d236200a4cc68a3 into a fresh private source root; execute plan/apply/verify with all explicit receipt roots/source pins/tool/role/realm/certificate-window bindings. Only apply creates2 new containers and their approved network configurations; no start/run/restart, shared container switch, mount changes to live roles, policy publication, source replay or provider call. Existing image IDs are reused; private mount/env/package/config/resource/DNS/state/ID/transaction readback remains mandatory. On any block retain root/journal and do not rerun apply; IAM expiry in plan precedes mutation, expiry after creation requires journal-aware reconciliation or owned cleanup. Real live namespace/address allocation/flow/lease/start admission and all complete acquisition-to-UDP gates remain open. Cinema/Teatri frozen, northbound/shared roles untouched.


### 2026-10-03 — Target stopped candidates created; boot custody transition pending

Host evidence: `/etc/ouf/deploy-snapshots/semantic-provider-stopped-create-20261003-135106/prepared/creation-journal.json`. Plan reported `PLANNED`, apply and verify reported `CREATED_STOPPED`, two containers, `NEVER_STARTED=true`, `START_AUTHORIZED=false`. Candidate configuration attaches the reused APISIX and adapter images to the existing selected networks; it does not prove a live namespace, allocated endpoint, packets, TLS admission or a provider lease. No shared container, network rules, routes, IAM configuration or authorization policy changed; provider calls remain zero. The successful interactive Keycloak login used administrative user `oufadmin` in `master`.

Do not replay stopped-create apply, normalize/recreate the existing networks, rebuild either image or invoke `docker start`. The target static-IPAM positive receipt remains authoritative. Earlier empty-network manifest/cold verifiers describe the pre-creation state and must not be blindly rerun after candidate creation.

Next boundary: coordinate the installed deny-only boot guard with the future empty-set/runtime rule structure before changing owned nft tables. `scripts/inventory_semantic_provider_guard_custody.py` is a read-only custody inventory, not full configuration acceptance: it binds the completed creation journal, manifest, cold receipt, installed boot artifacts, loaded Docker pre-start fingerprint/PID and current two-family guard. It permits only transaction-owned configured endpoints on dedicated networks and rejects started/foreign candidates, partial journals, foreign endpoints and changed guard/boot files. It neither invokes Keycloak nor requests tokens, DNS or providers, and does not authorize candidate startup. All roots, executable paths and creation revision are explicit inputs. Seven fixture admission tests cover these denials; target systemd/nft readback remains required. Real reboot and the full file/API-to-UDP release remain unproven; Cinema/Teatri evidence is preserved.


Custody helper pinned revision: Gateway `85914e39bd0aa9f8e7a0a0a9d3b9db6007633ff8`; SHA-256 `fabd47c6ce8919bc7a910cbaf63f66f1fb786b00c239ae41757c1fd0df829b8d`. All 28 check runs on this revision completed successfully (push and PR); config-contract recorded 454 passed / 64 opt-in skips, with native Docker/kernel/TLS/systemd jobs green separately. This proves CI behavior, not target custody or startup acceptance. Next user action is read-only target invocation with the five exact receipt/journal roots, creation revision `93e861fe8c8a43912f0cb78a74adceb2db509dd9`, and explicit Docker/nft/systemctl paths; no Keycloak renewal is needed for this helper.
