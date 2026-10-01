# R4A — build isolata della candidata UDP e sonda GET-only

Questa procedura prepara un'immagine candidata senza installarla. Consultare UDP PET1.3 §§109.6/109.7/109.9 e Ingestion PET1.3 §45.2 a ogni sprint: durable ACK e materializzazione completata sono evidenze distinte. Il caso corrente conserva otto handoff originali ACKED, cinque materializzati e tre quarantene tecniche; una build o un resolver PASS non cambia questo stato.

## Contratto operativo

Script `scripts/r4a_prepare_udp_recovery_image.py`, root richiesto, tutti i binding espliciti:

| Argomento | Significato |
|---|---|
| repository | URL HTTPS pubblico senza credenziali del repository sorgente |
| revision | SHA40 esatto della candidata verificata in CI |
| baseline-revision | SHA40 esatto della versione installata, per confronto completo delle migrazioni |
| container | Nome del container UDP live da ispezionare |
| expected-live-image | Image ID sha256 osservato e atteso per quel container |
| image-repository | Repository locale per tag univoco candidata; non usare il tag live |
| work-parent | Directory assoluta esistente, root-owned, non scrivibile da gruppo/altri |

Lo script crea una sottodirectory privata univoca, fetch dei due commit in un repository separato, checkout detached esatto, confronto path+SHA256 dei blob migration, build dal Dockerfile versionato con label OCI revision e tag univoco. Non prende env/token/DB/segreti del live come build arguments o secret mounts. Ispeziona UID/GID e image ID finali, controlla identità/StartedAt/restart count live prima/dopo, conserva source/build.log/receipt.json root-only. Su errore conserva receipt BLOCKED con solo tipo sicuro; niente messaggi arbitrari in output. Non crea o avvia un container applicativo, non cambia tag/config/mount/network del live, non esegue migrazioni o retry. Le immagini intermedie/cache e la candidata restano presenti.

Il Dockerfile contiene ancora base image tags; SHA sorgente+label non rendono la build riproducibile bit per bit. Registrare e usare l'image ID risultante. Pin dei digest e distribuzione di artefatti firmati restano gate R-INSTALL; questo helper non chiude industrializzazione, multi-host o upgrade/restore.

Poi chiamare `r4a_udp_java_reference_probe.py --resolver-image IMAGE_ID --expected-revision REVISION` oltre ai binding esistenti espliciti run/source/container/postgres-container/database/db-user/network/jdk-image/jar-path. Il JDK deve essere già presente; nessun pull implicito nella sonda. L'helper copia il JAR da container fermo networknone e lo rimuove. JVM candidata separata usa classi/librerie reali, UID/GID live, token directory bind read-only, nessun credential DB/env applicativo e nessun Spring/worker. SELECT read-only e GET Gateway degli esatti riferimenti; stampa solo protocollo sicuro. Un PASS resta limitato: mapper live Spring, causa storica, materializzazione, auth HUMAN e deploy non provati.

## Binding del checkpoint corrente — valori operatore, non default nel codice

- UDP candidata `c0b6c98c5029682a51e5ed82717092f86bfbb318`, PR38; baseline installata `edaba2bff18a2aaf52d1180f21f0e68984cc3437`.
- Ultimo image ID live osservato `sha256:a47c8607c53451f7d0affba5994ec20dc6c09272ace68808daa9e63c33bc572e`; se diverso lo script blocca, non aggiornarlo senza inventario.
- Run `86809c17-3354-45ca-a7e6-57e903944b24`, source `managed-cinema-8ec8ae90`.
- Installazione laboratorio: checkout coordinamento `/opt/ouf/semantic`, live `ouf-udp`, PostgreSQL `ouf-postgres`, database/user `ouf_udp`, network `ouf-backend`, JAR `/app/app.jar`, JDK `maven:3.9.11-eclipse-temurin-21`.
- Nuova directory privata per candidata `/opt/ouf/udp-recovery-candidates`, repository immagine locale `ouf-udp-recovery-candidate`. Fonte HTTPS `https://github.com/GioNob/ouf-udp-object-resolution.git`.
- Estrarre i tre script (build, Java probe e token inventory importato) da un commit coordinamento esatto con CI verificata; il comando consegnato nell'handoff fissa quello SHA. Non eseguire script da branch mobile.

La build è bounded a30min e scrive dettagli solo in build.log privato; può richiedere download Maven/base images. Output START e receipt sono immediati, i dettagli build non passano in chat. Non inoltrare build.log, token, payload o receipt completo. Copiare le sole righe protocollo prodotte da build/sonda.

## Gate successivi

Dopo PASS operatore conservare receipt/image ID e aggiornare insieme handoff/manuale/roadmap. Nessuna sostituzione live autorizzata dal PASS. Restano preparazione privata backup/rollback/config/network, release controllata, nuova capability `udp.materialization.retry` HUMAN e scope/grant/route governati con fresh ACTIVE policy e prove deny/allow; poi GET live delle tre quarantene, conferma HUMAN e retry idempotenti dei job originali. Non usare SQL repair, replay nuovo handoff, riattivazione source/schedule o re-invio ACK. Ricontrollare tutti gli otto ID e la materializzazione canonica, quindi search e altri gate aperti.

## Verifica dello helper

Sette nuovi test mocked: build e receipt senza live mutation, checkout errato prima build, migration drift prima build, restart concorrente, failure redaction, hash byte esatti e rifiuto URL con credenziali/parent scrivibile. Suite combinata39 PASS localmente; non equivale a build/sonda sul VPS. CI recovery-cycle-scripts include ora questo modulo.


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

#### Esecuzione unica del fix verificato — installazione corrente

I valori seguenti sono binding espliciti dell'installazione corrente, da sostituire per altri Enti/host/reti. Nessun valore viene introdotto nel codice applicativo. Il blocco richiede sudo sul server; interrompe brevemente UDP per backup e switch. Non esegue retry/replay o pubblicazione policy. Non ripetere una fase release con esito incerto: riconciliare il receipt privato prima.

```bash
(
set -euo pipefail
umask 077
# Valori dell'installazione corrente; gli helper richiedono parametri espliciti.
ouf_coordination=/opt/ouf/semantic
ouf_work_parent=/opt/ouf/udp-recovery-candidates
ouf_udp_container=ouf-udp
ouf_candidate_container=ouf-udp-materialization-candidate
ouf_revision=afa5c4c4cf03bff4e39b02e27f898256c3776cbc
ouf_baseline=c0b6c98c5029682a51e5ed82717092f86bfbb318
ouf_expected_image=sha256:e15fb3493992d67b065ecb3035beb36fd36b139a590544bd9fb55879bc782229
ouf_helpers=53ee0c69d6ecabc5d8bdbfdaa838beb476b06537
ouf_run=86809c17-3354-45ca-a7e6-57e903944b24
ouf_source=managed-cinema-8ec8ae90
cd "$ouf_coordination"
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
ouf_fix_dir=$(mktemp -d /tmp/ouf-r4a-udp-label-fix.XXXXXX)
trap 'rm -rf -- "$ouf_fix_dir"' EXIT
for script in r4a_prepare_udp_recovery_image.py r4a_udp_java_reference_probe.py r4a_udp_token_transport_inventory.py r4a_stage_udp_recovery.py r4a_release_udp_recovery.py; do
  git show "$ouf_helpers:scripts/$script" > "$ouf_fix_dir/$script"
done
sudo docker image inspect maven:3.9.11-eclipse-temurin-21 >/dev/null
sudo docker image inspect curlimages/curl:8.16.0 >/dev/null
sudo install -d -m 0700 "$ouf_work_parent"
sudo python3 -B "$ouf_fix_dir/r4a_prepare_udp_recovery_image.py" \
  --repository https://github.com/GioNob/ouf-udp-object-resolution.git \
  --revision "$ouf_revision" --baseline-revision "$ouf_baseline" \
  --container "$ouf_udp_container" --expected-live-image "$ouf_expected_image" \
  --image-repository ouf-udp-recovery-candidate --work-parent "$ouf_work_parent" \
  | tee "$ouf_fix_dir/build-protocol.txt"
ouf_candidate_id=$(sed -n 's/^UDP_RECOVERY_CANDIDATE_IMAGE_ID=//p' "$ouf_fix_dir/build-protocol.txt")
ouf_build_receipt=$(sed -n 's/^R4A_UDP_RECOVERY_IMAGE_RECEIPT=\([^ ]*\) PRIVATE=true$/\1/p' "$ouf_fix_dir/build-protocol.txt")
test -n "$ouf_candidate_id"
test -n "$ouf_build_receipt"
sudo python3 -B "$ouf_fix_dir/r4a_udp_java_reference_probe.py" \
  --resolver-image "$ouf_candidate_id" --expected-revision "$ouf_revision" \
  --container "$ouf_udp_container" --jar-path /app/app.jar \
  --run "$ouf_run" --source "$ouf_source" \
  --postgres-container ouf-postgres --database ouf_udp --db-user ouf_udp \
  --network ouf-backend --jdk-image maven:3.9.11-eclipse-temurin-21
sudo python3 -B "$ouf_fix_dir/r4a_stage_udp_recovery.py" \
  --container "$ouf_udp_container" --candidate-container "$ouf_candidate_container" \
  --build-receipt "$ouf_build_receipt" --work-parent "$ouf_work_parent" \
  | tee "$ouf_fix_dir/stage-protocol.txt"
ouf_stage_receipt=$(sed -n 's/^R4A_UDP_RECOVERY_STAGE_RECEIPT=\([^ ]*\) PRIVATE=true$/\1/p' "$ouf_fix_dir/stage-protocol.txt")
test -n "$ouf_stage_receipt"
sudo python3 -B "$ouf_fix_dir/r4a_release_udp_recovery.py" \
  --stage-receipt "$ouf_stage_receipt" \
  --postgres-container ouf-postgres --database ouf_udp --db-user ouf_udp \
  --gateway-container ouf-apisix --curl-image curlimages/curl:8.16.0 \
  --health-origin http://127.0.0.1:8080 --health-path /actuator/health \
  --gateway-health-url http://ouf-udp:8080/actuator/health \
  --expected-flyway 34 --stop-seconds 60 --health-attempts 45 \
  --source "$ouf_source" --run "$ouf_run" \
  --probe-job 7793566d-b9d4-4402-8cda-c09b8f135c04 \
  --expected-job-count 8 --expected-succeeded 5 --expected-quarantined 3
)
```


### Checkpoint 2026-10-01 — fix image costruita, stage bloccato prima di ogni deploy

Evidenze operatore: build UDP afa5c4c4cf03bff4e39b02e27f898256c3776cbc PASS, immagine sha256:024c6691888855ef4d5574cadacf060e0dfbf7ff891dbc9a747628f5b5c8a519; receipt privato /opt/ouf/udp-recovery-candidates/udp-recovery-image-ckrhncjk/receipt.json. Migrazioni identiche e live invariato durante build. Probe Java candidata GET-only PASS; mapper Spring e causalità storica non provati. Stage BLOCKED ValueError, senza stage receipt riportato, DEPLOY=false e RETRY=false; release non eseguito.

Revisione helper: lo stage richiedeva feature recovery false sul live, incompatibile con un successivo upgrade del runtime c0b6 già recovery-enabled. Questo è un difetto del percorso upgrade; il messaggio generico non prova ancora il codice effettivo sul server. Lo stage ora richiede --allow-enabled-live per quell'upgrade, rifiuta valori diversi da true/false, conserva gli altri guard e aggiunge --check-only per preflight in sola lettura. StageError riporta esclusivamente codici statici senza valori privati. Receipt distingue prima abilitazione da upgrade. Test per enabled-live negato senza opzione, upgrade consentito, flag invalido, preflight senza receipt/container e release con ambiente invariato. Non disabilitare la feature sul live per aggirare il guard. Riutilizzare la build già validata; nuovo blocco preflight → stage → release, senza rebuild/replay/retry. Se emerge un altro guard, bloccare e riconciliare dal codice simbolico.


### Checkpoint 2026-10-01 — helper upgrade verificato; ripresa senza ricostruire immagine

Fix helper deploy `b71a964b663e47bb23a93f7c46c62d3ecaa84e0b`: 22 test locali stage/release PASS, suite helper completa 63 test PASS. CI Semantic Registry run36849541342 job recovery-cycle-scripts SUCCESS (63 test); gli altri job del modulo sono ancora in corso. Il codice applicativo UDP resta afa5c4c4cf03bff4e39b02e27f898256c3776cbc, già verde in tutte le sue CI; si riusa esattamente immagine 024c6691… e receipt build ckrhncjk. Nessun stage/release del fix è provato finché non arriva il nuovo protocollo operatore. Live atteso resta e15fb349… / Flyway34. La prima verifica del blocco seguente è --check-only, GET/inspect soltanto: se non PASS, set -e interrompe senza stage o release. Se PASS, stage fermo e release guardato. Non inviare file privati o messaggi raw di errore; usare CODE statico. Con esito incerto non ripetere release, riconciliare receipt.

#### Ripresa dello stage bloccato — build ckrhncjk

Questo blocco sostituisce quello precedente per il receipt già costruito. Binding dell'installazione corrente espliciti; nuovo preflight in sola lettura, poi stage e release controllato con backup. Nessun rebuild/replay/retry. --allow-enabled-live non modifica la feature sul live.

```bash
(
set -euo pipefail
umask 077
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
ouf_resume_dir=$(mktemp -d /tmp/ouf-r4a-udp-stage-resume.XXXXXX)
trap 'rm -rf -- "$ouf_resume_dir"' EXIT
for script in r4a_stage_udp_recovery.py r4a_release_udp_recovery.py; do
  git show b71a964b663e47bb23a93f7c46c62d3ecaa84e0b:scripts/"$script" > "$ouf_resume_dir/$script"
done
ouf_stage_args=(
  --container ouf-udp --candidate-container ouf-udp-materialization-candidate
  --build-receipt /opt/ouf/udp-recovery-candidates/udp-recovery-image-ckrhncjk/receipt.json
  --work-parent /opt/ouf/udp-recovery-candidates --allow-enabled-live
)
sudo python3 -B "$ouf_resume_dir/r4a_stage_udp_recovery.py" "${ouf_stage_args[@]}" --check-only
sudo python3 -B "$ouf_resume_dir/r4a_stage_udp_recovery.py" "${ouf_stage_args[@]}" \
  | tee "$ouf_resume_dir/stage-protocol.txt"
ouf_stage_receipt=$(sed -n 's/^R4A_UDP_RECOVERY_STAGE_RECEIPT=\([^ ]*\) PRIVATE=true$/\1/p' "$ouf_resume_dir/stage-protocol.txt")
test -n "$ouf_stage_receipt"
sudo python3 -B "$ouf_resume_dir/r4a_release_udp_recovery.py" \
  --stage-receipt "$ouf_stage_receipt" \
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


CI finale helper upgrade: Semantic Registry run36849692475 su 71c84cebf5a91a3d8d879019ff7eed4f36bf44f6 SUCCESS nei tre job recovery-cycle-scripts (63 test), java21-postgresql17 e container-smoke. Codice helper pinnato b71a964b663e47bb23a93f7c46c62d3ecaa84e0b invariato. Il successivo aggiornamento è solo documentale. Rilascio sul server ancora NON eseguito/provato.


### Checkpoint 2026-10-01 12:37 Europe/Rome — fix DataAccessLabel distribuito

Preflight READ_ONLY PASS (LIVE_RECOVERY_ENABLED=true, CANDIDATE_ABSENT=true); stage receipt privato /opt/ouf/udp-recovery-candidates/udp-recovery-stage-8oc0p5t1/receipt.json PASS. Release receipt privato nello stesso directory release-receipt.json: PASS, immagine live sha256:024c6691888855ef4d5574cadacf060e0dfbf7ff891dbc9a747628f5b5c8a519, codice afa5c4c4cf03bff4e39b02e27f898256c3776cbc, Flyway34, backup restore-list PASS, original jobs unchanged, health Gateway PASS, anonymous/spoof denied. Rollback ouf-udp-rollback-2f9a72e60975 fermo/restart disabilitato; conservare anche i rollback precedenti finché non riconciliati. Nessun retry. HUMAN authorization non ancora provata. Stato precedente 5 SUCCEEDED + 3 QUARANTINED resta invariato nel guard del release; full8/search non acquisito. Prossimo passo: registrazione batch parametrizzata e policy DRAFT HUMAN, tre grant a resourceId esatto/source/run/tenant e DataAccessLabel RAW effettivo, conservando interamente fresh ACTIVE. Nessuna pubblicazione implicita o modifica IAM/route. Il login admin HUMAN sarà necessario per le API amministrative; non usare token SERVICE.


### Checkpoint 2026-10-01 — batch scoped HUMAN policy preparation

Nuovi helper parametrizzati: r4a_materialization_recovery_scope.py legge soltanto metadata dei job originali/RAW, richiede stato tecnico recuperabile e nessun effetto canonico, scrive scope privato exact-job/source/run/type + DataAccessLabel effettivo. r4a_prepare_scoped_human_policy.py accetta manifest batch HUMAN e scope privati, issuer/client/audience/admin scope/API base/tenant/subject/expiry/state-file obbligatori. Registra soltanto descrittori mancanti semanticamente compatibili e crea un DRAFT add-only: ACTIVE fresco e tutte le entry esistenti preservate; baseline/revision/readback/diff preview ricontrollati, nessuna pubblicazione. State file esclusivo 0600 con intent fsync prima di ogni POST; esito incerto obbliga riconciliazione, nessun repost automatico. Token solo in memoria, no redirect e nessuna modifica IAM/route/job. La preview non è prova di autorizzazione runtime. Test di perdita risposta registration/draft, conflitti pre-write, ACTIVE drift, preview scoped-grant drift, deny tenant/canonical effects/labels assenti/SERVICE/duplicati/expiry/redirect; test locali PASS, CI avviata. Per l'esecuzione admin serve fresh Device Grant HUMAN del soggetto esplicito; mantenere il codice fuori dalla chat. Dopo DRAFT: simulazioni deny/allow governate, IAM scope client binding e Gateway exact routes, pubblicazione esplicita HUMAN e poi lettura Spring dei tre job; retry soltanto dopo review/confirm nello stesso contesto umano. Full8/search e gli altri gate precedenti restano aperti.


### Checkpoint 2026-10-01 — scoped batch operatore pronto, nessuna activation

CI helper run36851261430 recovery-cycle-scripts SUCCESS, 73 test; modulo fermato prima di Maven perché checksum workflow non aggiornato insieme al nuovo test. Registro source-checksums corretto in 7a163de5bb0351f5bf332f7ad9f42d0cdf4240ea, includendo anche i tre nuovi file helper/test; gate invariato. Nuova CI avviata, completamento non ancora acquisito. Il codice dei due helper resta quello del commit 4c8600c45510ae451dd8385bbb66b3903eb3d080. Operator binding: soggetto HUMAN b93d8cf6-cd14-4ee6-91d7-84cd76c4f500, tenant ouf-lab, admin scope authorization.policy.admin, IAM client ouf-human-admin; validUntil esplicito 2026-10-02T10:00:00Z (12:00 Europe/Rome), da sostituire se la ripresa avviene dopo scadenza. State directory privato /etc/ouf/deploy-snapshots/udp-materialization-recovery-policy; resources.json e draft-receipt.json non stampare. Non rieseguire il blocco se uno di questi file esiste: riconciliare prima lo stato privato; zero repost automatici. DRAFT e preview non provano capability runtime allow. Nessuna publication/IAM/Gateway/retry implicita. Il blocco richiede login Device Grant HUMAN nel browser e non deve essere autenticato con identità SERVICE o altro subject.

#### Preparazione batch della policy HUMAN — tre job originali

Binding dell'installazione corrente espliciti. Il primo helper legge solo metadata DB e scrive scope privato; il secondo valida input, richiede fresh Device Grant HUMAN, registra il manifest batch e crea un DRAFT senza pubblicarlo. Il token resta solo in memoria. Non condividere device user code, token, JSON scope/receipt o payload. Al termine incollare soltanto protocollo simbolico. Una POST con esito incerto richiede riconciliazione del receipt privato, mai riesecuzione alla cieca.

```bash
(
set -euo pipefail
umask 077
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
ouf_policy_code=4c8600c45510ae451dd8385bbb66b3903eb3d080
ouf_policy_tmp=$(mktemp -d /tmp/ouf-r4a-scoped-policy.XXXXXX)
trap 'rm -rf -- "$ouf_policy_tmp"' EXIT
for script in r4a_prepare_scoped_human_policy.py r4a_materialization_recovery_scope.py; do
  git show "$ouf_policy_code:scripts/$script" > "$ouf_policy_tmp/$script"
done
# Binding espliciti dell'installazione corrente.
ouf_policy_dir=/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy
ouf_policy_tenant=ouf-lab
ouf_policy_subject=b93d8cf6-cd14-4ee6-91d7-84cd76c4f500
sudo install -d -m 0700 "$ouf_policy_dir"
cat > "$ouf_policy_tmp/manifest.json" <<'JSON'
[{"ownerRef":"udp","descriptor":{"capabilityId":"udp.materialization.retry","operation":"COMMAND","requiredScope":"udp.materialization.retry","allowedActors":["HUMAN"]}}]
JSON
sudo python3 -B "$ouf_policy_tmp/r4a_materialization_recovery_scope.py" \
  --postgres-container ouf-postgres --database ouf_udp --db-user ouf_udp \
  --source managed-cinema-8ec8ae90 --tenant "$ouf_policy_tenant" \
  --run 86809c17-3354-45ca-a7e6-57e903944b24 --capability udp.materialization.retry \
  --job 7793566d-b9d4-4402-8cda-c09b8f135c04 \
  --job e7572836-f8af-4c58-b5fc-12d7aff5db1d \
  --job e5b6ca24-6143-4ae5-8907-5dce398abfa3 \
  --output "$ouf_policy_dir/resources.json"
ouf_policy_args=(
  --issuer https://auth.ouf-lab.it/realms/ouf --client ouf-human-admin
  --audience ouf-api-gateway --admin-scope authorization.policy.admin
  --base-url https://api.ouf-lab.it/api/trusted-human/v1/authorization
  --tenant "$ouf_policy_tenant" --subject "$ouf_policy_subject"
  --valid-until 2026-10-02T10:00:00Z
  --manifest "$ouf_policy_tmp/manifest.json" --resources "$ouf_policy_dir/resources.json"
  --state-file "$ouf_policy_dir/draft-receipt.json"
)
sudo python3 -B "$ouf_policy_tmp/r4a_prepare_scoped_human_policy.py" "${ouf_policy_args[@]}" --validate-only
sudo python3 -B "$ouf_policy_tmp/r4a_prepare_scoped_human_policy.py" "${ouf_policy_args[@]}"
)
```


### Checkpoint finale 2026-10-01 — scoped HUMAN batch verificato, in attesa login operatore

Semantic Registry CI push run36851593724 su 88b5b1802eeac5538f8e2205ed86a46d52d55cde SUCCESS: recovery-cycle-scripts (73 test), Java21/PostgreSQL17, container-smoke. Pairwise Shared SDK run36851598351, Authorization Semantic run36851598357 e Gateway live run36851598405 SUCCESS. Source checksum gate ripristinato e verificato. Helper code 4c8600c45510ae451dd8385bbb66b3903eb3d080 immutato. Aggiornamento seguente solo documentale. Il blocco è pronto ma NON ancora eseguito: catalogue/DRAFT/ACTIVE/IAM/Gateway/job invariati da questa sessione; prossimo intervento richiesto è l'esecuzione operatore con fresh Device Grant HUMAN amministratore. Nessun retry eseguito o provato. Conservare tutte le limitazioni e gate indicati sopra.


### Checkpoint 2026-10-01 12:54 Europe/Rome — scoped HUMAN DRAFT creato

Operatore: R4A_SCOPED_HUMAN_POLICY_DRAFT PASS, base ouf-lab-authorization:35, draft b305bcae-a03f-4f0d-8b81-81508bcddb24 revision0; una capability e tre grant scoped, entry esistenti preservate, ACTIVE invariato. Receipt privato /etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/draft-receipt.json. POLICY_UNPUBLISHED=true; preview non è prova di autorizzazione; IAM/route invariati; RETRY=false. Non rieseguire prepare o rigenerare resources/receipt: bozza registrata, da riprendere per ID/revision esatti. Target atteso :36 da confermare dal receipt/API. Prossimi gate: simulazioni SDK del DRAFT con scope RAW effettivi (allow dei tre job e deny actor/tenant/subject/source/run/job/label/scope), binding opzionale IAM della nuova scope al client HUMAN e route Gateway esatte senza modificare OIDC/limiti; pubblicazione con revisione e conferma HUMAN esplicita; poi GET della recovery sul runtime Spring reale e soltanto dopo conferma eventuale retry originale. Tutte le evidenze e limitazioni precedenti preservate.


### Checkpoint 2026-10-01 — inventario binding parametrizzato prima di apply/publish

Nuovo r4a_recovery_binding_inventory.py: tutti i binding IAM/Gateway/realm/client/scope/config destination/admin origin/curl image/backend/path/snapshot espliciti. Riusa soltanto parser pure del precedente inventory, senza i suoi default runtime. Legge route con APISIX Admin GET e chiave solo via stdin; legge client/scope/binding con kcadm GET esistente, nessuna ricerca o stampa credenziali. Controlla Gateway identity/config invariati; scrive snapshot esclusivo root0600 sotto parent0700, contenente configurazione tecnica privata, da non condividere. Output pubblico solo fatti/ID/path sanitizzati. URI candidates sono conservativi: priority/vars/radixtree parity non provata. Un accesso IAM bloccato non impedisce acquisire l'inventario Gateway; stato PARTIAL non equivale a PASS. Non cambia scope, route, policy o job e non fa retry. Quattro test locali PASS (secret/stdin-only + GET, IAM binding, mount/clear HTTP fail closed, snapshot parziale privato). Nuovo test aggiunto alla CI; checksum workflow e nuovi file aggiornati nello stesso commit. DRAFT b305bcae-a03f-4f0d-8b81-81508bcddb24 revision0 resta in attesa simulazioni/binding/pubblicazione HUMAN. Necessario l'output inventario del server per preparare un apply che preservi la configurazione effettiva; non ricreare bozza o scope resource file.


### Prossima esecuzione — binding inventory read-only

Blocco nel runbook R4A_UDP_RECOVERY_CANDIDATE per inventario IAM/Gateway, codice c353542fb687b23147d10e76e478d8286e840a2a. Snapshot /etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/binding-inventory.json PRIVATE: include route complete e segreti tecnici OIDC; non incollare o esportare. Solo output simbolico. Non richiede nuovo Device Grant HUMAN, riusa soltanto la sessione amministrativa kcadm già configurata e legge APISIX tramite root/mount esistente. Se accesso IAM fallisce, PARTIAL riporta comunque Gateway; nessuna ricerca/stampa delle credenziali e nessun cambiamento applicativo. CI del nuovo commit avviata, risultato non ancora acquisito. Il DRAFT e ACTIVE restano invariati, nessun retry, le simulazioni e i binding apply/pubblicazione restano gate successivi.

#### Inventario IAM e Gateway — DRAFT recovery UDP

Binding dell'installazione corrente espliciti. Solo letture amministrative e snapshot tecnico privato. Non condividere il file snapshot: contiene la configurazione completa delle route. Nessuna pubblicazione o retry. L'inventario non prova autorizzazione HUMAN runtime o routing parity; acquisisce i fatti necessari al prossimo apply governato.

```bash
(
set -euo pipefail
umask 077
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
ouf_binding_tmp=$(mktemp -d /tmp/ouf-r4a-binding-inventory.XXXXXX)
trap 'rm -rf -- "$ouf_binding_tmp"' EXIT
for script in r4a_recovery_binding_inventory.py r4a_prepare_scoped_human_policy.py r4a_execution_route_inventory.py r4a_prepare_frozen_compatibility_probe.py; do
  git show c353542fb687b23147d10e76e478d8286e840a2a:scripts/"$script" > "$ouf_binding_tmp/$script"
done
sudo python3 -B "$ouf_binding_tmp/r4a_recovery_binding_inventory.py" \
  --gateway-container ouf-apisix --config-destination /usr/local/apisix/conf/config.yaml \
  --admin-origin http://127.0.0.1:9180 --curl-image curlimages/curl:8.16.0 \
  --udp-node ouf-udp:8080 --template-node ouf-udp:8080 \
  --template-node ouf-ingestion:8080 --template-node ouf-onboarding:8080 \
  --review-path /api/udp/v1/governance/materialization/jobs/7793566d-b9d4-4402-8cda-c09b8f135c04 \
  --retry-path /api/udp/v1/governance/materialization/jobs/7793566d-b9d4-4402-8cda-c09b8f135c04/retry \
  --keycloak-container ouf-keycloak --kcadm /opt/keycloak/bin/kcadm.sh \
  --realm ouf --client ouf-human-admin --scope udp.materialization.retry \
  --snapshot /etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/binding-inventory.json
)
```


### Checkpoint 2026-10-01 13:30 Europe/Rome — Gateway acquisito, IAM inventory parziale

Operatore: review GET URI candidates0, retry POST URI candidates0; 42 template inline nei backend selezionati. Esistono template HUMAN Ingestion r4a-ingestion-human-quarantine-read/retry/run-read/resume e UDP ths-identity-preflight-read/create, con OIDC bearer-only e limit-count. Questo non prova routing parity, né la correttezza completa di un template da clonare: i body completi sono nel private snapshot /etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/binding-inventory.json. IAM inventory BLOCKED UNCLASSIFIED CalledProcessError, causa/sessione scaduta NON provata; overall PARTIAL READ_ONLY, nessun cambio IAM/route/policy/retry. Scope existence/assignment non acquisiti. Non rieseguire l'inventory con stesso filename esclusivo.

CI completa inventory f961fb1c4c8409418af1c78b430a14333f36855a SUCCESS: run36853251203 modulo (77 test helper, Java/PostgreSQL e container), Shared SDK36853251233, Authorization Semantic36853251113, Gateway36853251194. DRAFT b305bcae-a03f-4f0d-8b81-81508bcddb24 revision0 ancora non pubblicato nell'ultima evidenza, ACTIVE:35 nell'ultima lettura; UDP immagine024c6691…/afa5c4c4…/Flyway34,5SUCCEEDED+3QUARANTINED invariati nell'ultimo guard. Target:36 da riconfermare fresh prima di publish. Handoff e gate precedenti preservati.

Prossimo blocco: rinnovo interattivo kcadm realm master, administrator configurato oufadmin nel runbook, password esclusivamente nel terminale (non argv/env/chat); login distinto dal Device Grant HUMAN ouf-admin. Con lettura client esatto riuscita, helper Keycloak immutati Onboarding6340d5bf120e09b47c32177656e2c377a4c03640, tutti gli argomenti container/realm/client/scope/binding espliciti: catalogue plan; se scope esiste binding plan prima delle mutazioni per negare DEFAULT confliggente; catalogue apply/verify; binding plan/apply/verify OPTIONAL solo udp.materialization.retry su ouf-human-admin. Nessun altro scope/binding modificato; nessuna modifica del DRAFT/pubblicazione/route/job. Software path kcadm resta il percorso canonico dei helper esistenti, limite di portabilità da parametrizzare nel successivo consolidamento R-INSTALL. Bash syntax verificata; la riconciliazione effettiva IAM resta da provare sul server. Se login/plan fallisce, stop; non stampare credenziali o raw kcadm output e non reiterare una create incerta senza readback.

#### Rinnovo kcadm e scope OPTIONAL — recovery UDP

Binding del laboratorio espliciti nelle variabili del blocco. Per il login realm master usare l'amministratore Keycloak configurato (qui oufadmin); la password viene chiesta direttamente da kcadm. Il login e l'apply riguardano soltanto la configurazione IAM, non la pubblicazione della bozza né il retry. Modificare i binding dichiarati per altre installazioni; non condividere la password. Gli helper immutati riconciliano un singolo scope e preservano gli altri binding.

```bash
(
set -euo pipefail
umask 077
cd /opt/ouf/semantic
git fetch --no-tags https://github.com/GioNob/ouf-source-onboarding.git 6340d5bf120e09b47c32177656e2c377a4c03640
ouf_iam_tmp=$(mktemp -d /tmp/ouf-r4a-recovery-iam.XXXXXX)
trap 'rm -rf -- "$ouf_iam_tmp"' EXIT
for script in r4a_keycloak_client_scope_catalogue.py r4a_keycloak_client_scope_binding.py; do
  git show 6340d5bf120e09b47c32177656e2c377a4c03640:scripts/"$script" > "$ouf_iam_tmp/$script"
done
# Binding dell'installazione corrente; password solo nel prompt kcadm.
ouf_kc_container=ouf-keycloak
ouf_kc_server=https://auth.ouf-lab.it
ouf_kc_admin=oufadmin
ouf_kc_realm=ouf
ouf_kc_client=ouf-human-admin
ouf_kc_scope=udp.materialization.retry
sudo docker exec -it "$ouf_kc_container" /opt/keycloak/bin/kcadm.sh config credentials \
  --server "$ouf_kc_server" --realm master --user "$ouf_kc_admin"
sudo python3 -B - "$ouf_iam_tmp" "$ouf_kc_container" "$ouf_kc_realm" "$ouf_kc_client" <<'PY'
import sys
sys.path.insert(0,sys.argv[1])
import r4a_keycloak_client_scope_binding as binding
try:
    binding.exact_client(sys.argv[2],sys.argv[3],sys.argv[4])
except binding.ScopeError as error:
    print('R4A_IAM_CLIENT_PREFLIGHT=BLOCKED CODE='+str(error))
    raise SystemExit(1)
print('R4A_IAM_CLIENT_PREFLIGHT=PASS READ_ONLY=true')
PY
ouf_catalogue_args=(--container "$ouf_kc_container" --realm "$ouf_kc_realm" --scope "$ouf_kc_scope")
ouf_binding_args=(--container "$ouf_kc_container" --realm "$ouf_kc_realm" --client "$ouf_kc_client" --scope "$ouf_kc_scope" --binding optional)
sudo python3 -B "$ouf_iam_tmp/r4a_keycloak_client_scope_catalogue.py" plan "${ouf_catalogue_args[@]}" \
  | tee "$ouf_iam_tmp/catalogue-plan.txt"
# Rifiuta un binding DEFAULT confliggente prima di cambiare uno scope esistente.
if test "$(sed -n 's/^EXISTS=//p' "$ouf_iam_tmp/catalogue-plan.txt")" = true; then
  sudo python3 -B "$ouf_iam_tmp/r4a_keycloak_client_scope_binding.py" plan "${ouf_binding_args[@]}"
fi
sudo python3 -B "$ouf_iam_tmp/r4a_keycloak_client_scope_catalogue.py" apply "${ouf_catalogue_args[@]}"
sudo python3 -B "$ouf_iam_tmp/r4a_keycloak_client_scope_catalogue.py" verify "${ouf_catalogue_args[@]}"
sudo python3 -B "$ouf_iam_tmp/r4a_keycloak_client_scope_binding.py" plan "${ouf_binding_args[@]}"
sudo python3 -B "$ouf_iam_tmp/r4a_keycloak_client_scope_binding.py" apply "${ouf_binding_args[@]}"
sudo python3 -B "$ouf_iam_tmp/r4a_keycloak_client_scope_binding.py" verify "${ouf_binding_args[@]}"
printf '%s\n' 'R4A_UDP_RECOVERY_IAM_BINDING=PASS OPTIONAL=true POLICY_PUBLISH_NOT_CALLED=true ROUTE_WRITES=false RETRY=false SECRETS_NOT_PRINTED=true'
)
```


### Checkpoint 2026-10-01 13:44 Europe/Rome — output SSH IAM perso, esito da riconciliare

L'operatore riferisce di aver eseguito il blocco di rinnovo kcadm e scope OPTIONAL, ma di aver perso l'output SSH. Non assumere PASS o FAIL, né ripetere login/apply/create. Prossima azione: due soli verify read-only dei helper Keycloak immutati6340d5bf120e09b47c32177656e2c377a4c03640, scope udp.materialization.retry e binding OPTIONAL a ouf-human-admin nel realm ouf. Si riusa la sessione kcadm già configurata. Catalogue verify prova protocollo/attributi attuali; binding verify prova l'assegnazione attuale e nega un DEFAULT confliggente. Se sessione scaduta o scope/binding mancante, acquisire il codice simbolico prima di ulteriori azioni; non usare apply per diagnostica. La verifica non ricostruisce il log storico perduto. DRAFT b305bcae-a03f-4f0d-8b81-81508bcddb24 revision0 e ACTIVE:35 nell'ultima evidenza, nuove route recovery ancora assenti nell'ultimo inventory, nessuna pubblicazione/retry provati. Handoff e gate precedenti preservati.


### Checkpoint 2026-10-01 13:48 Europe/Rome — IAM scope OPTIONAL verificato

Readback operatore in sola lettura: scope udp.materialization.retry EXISTS=true, DRIFT=NONE, catalogue VERIFY PASS; client ouf-human-admin, OPTIONAL STATE=BOUND, binding VERIFY PASS. R4A_IAM_RECONCILIATION PASS READ_ONLY=true RETRY=false. Protocollo privato /etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/iam-verify.22IAo3. Questa verifica recupera stato attuale; non ricostruisce il log SSH storico perduto. Nuovo token HUMAN con scope esplicito non ancora acquisito. DRAFT b305bcae-a03f-4f0d-8b81-81508bcddb24 revision0, ACTIVE:35 nell'ultima evidenza; pubblicazione/retry non eseguiti/provati. Route review/retry ancora assenti nell'ultimo inventory; prossimo passo preparazione di due route HUMAN UUID esatte, riusando template protetto e preservando OIDC/limiti/route esistenti, con snapshot/intent/readback/rollback. Seguono simulazioni della bozza, conferma/pubblicazione HUMAN, GET reale Spring dei tre job e solo poi eventuale conferma retry. Gate full8/search/causalità storica/industrializzazione e tutti i precedenti invariati.


### R4A — Gateway recovery parameterizzato, preparazione dopo IAM verificato (2026-10-01)

IAM verify dell'operatore: `udp.materialization.retry` esiste, DRIFT=NONE; client `ouf-human-admin` OPTIONAL/BOUND. Log privato `iam-verify.22IAo3`, nessun retry. Consultati PET Authorization v1.5 §36.10 e UDP v1.3 §§109.6–109.7: coarse Gateway, fine-grained owner, reference integrity nel punto d'uso; nessun silent fallback.

Nuovo helper `scripts/r4a_install_materialization_recovery_routes.py`: ogni binding obbligatorio da CLI, due route condivise GET review/POST retry con UUID/action ancorati, OIDC bearer-only e limit-count preservati da template validato, guard HUMAN access e rimozione header x-ouf nel rewrite, token preservato per verifica owner indipendente. Non copia Lua di altre capability. Snapshot Gateway privato precedente deve combaciare con lettura fresca; collisione/drift bloccano prima di PUT. Ricevuta esclusiva root 0600 con intent fsync prima di ogni PUT; rollback elimina soltanto route create che combaciano ancora con il desiderato. Se output perso, `verify` legge senza PUT; stato incerto richiede riconciliazione e mai blind retry. Nessun POST owner, nessuna pubblicazione policy, nessun replay/source activation. Test locali 20 PASS (6 nuovi +14 preesistenti); CI aggiunta a 83 test e checksum aggiornati nello stesso commit. Deploy effettivo e HUMAN authorization rimangono da verificare dall'operatore. Bozza b305bcae-a03f-4f0d-8b81-81508bcddb24 non pubblicata; ultimo ACTIVE osservato :35; invariato obiettivo materializzazione 8/8 e search non provata. Limiti: snapshot+readback non sono transazione APISIX distribuita; evitare writer concorrenti nella finestra.


#### R4A UDP recovery Gateway — installazione due route dopo IAM verify

Eseguire sul nodo Gateway, finestra senza altri writer APISIX. Binding di esempio dell'ambiente lab nel runbook; helper senza default installativi. Usa snapshot privato Gateway PASS_READ_ONLY anche quando IAM nello stesso inventario era PARTIAL, ora verificato separatamente. Plan/apply/verify salvano protocollo privato; se ricevuta già esiste esegue solo verify. Non pubblica policy e non invoca retry owner. In caso BLOCKED copiare soltanto output simbolico; non stampare snapshot o receipt che contengono configurazione OIDC privata.

```bash
set -euo pipefail
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
REVISION=2011743b06f685004f74ccef045d1b34b273192b
WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT
for SCRIPT in r4a_install_materialization_recovery_routes.py r4a_recovery_binding_inventory.py r4a_execution_route_inventory.py r4a_prepare_frozen_compatibility_probe.py r4a_prepare_scoped_human_policy.py; do
  git show "$REVISION:scripts/$SCRIPT" > "$WORK_DIR/$SCRIPT"
done
sudo bash -s -- "$WORK_DIR" <<'ROOT'
set -euo pipefail
umask 077
WORK_DIR=$1
STATE_DIR=/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy
LOG=$(mktemp "$STATE_DIR/gateway-routes.XXXXXX")
printf 'RECOVERY_GATEWAY_LOG=%s PRIVATE=true\n' "$LOG"
COMMON=(
  --gateway-container ouf-apisix
  --config-destination /usr/local/apisix/conf/config.yaml
  --admin-origin http://127.0.0.1:9180
  --curl-image curlimages/curl:8.16.0
  --template-id r4a-onboarding-runtime-publications-list
  --template-uri /api/onboarding/v1/runtime/publications
  --template-node ouf-onboarding:8080
  --template-scope ouf.onboarding.configuration.read
  --public-host api.ouf-lab.it
  --udp-node ouf-udp:8080
  --base-path /api/udp/v1/governance/materialization/jobs
  --scope udp.materialization.retry
  --review-id r4a-udp-human-materialization-review
  --retry-id r4a-udp-human-materialization-retry
  --snapshot "$STATE_DIR/binding-inventory.json"
  --receipt "$STATE_DIR/gateway-routes-receipt.json"
)
if test -e "$STATE_DIR/gateway-routes-receipt.json"; then
  python3 -B "$WORK_DIR/r4a_install_materialization_recovery_routes.py" verify "${COMMON[@]}" 2>&1 | tee -a "$LOG"
else
  python3 -B "$WORK_DIR/r4a_install_materialization_recovery_routes.py" plan "${COMMON[@]}" 2>&1 | tee -a "$LOG"
  python3 -B "$WORK_DIR/r4a_install_materialization_recovery_routes.py" apply "${COMMON[@]}" 2>&1 | tee -a "$LOG"
  python3 -B "$WORK_DIR/r4a_install_materialization_recovery_routes.py" verify "${COMMON[@]}" 2>&1 | tee -a "$LOG"
fi
ROOT
```


R4A CI aggiornamento: 83/83 recovery-cycle test PASS. Primo check checksum ha rilevato newline finale divergente nelle copie locali di workflow/helper; correggere hash ai byte Git pubblicati (codice invariato). La procedura operatore rimane pinnata a 2011743b06f685004f74ccef045d1b34b273192b; nessun deploy/retry effettuato da questo controllo. Attendere CI sul commit checksum prima dell'esecuzione operatore.


R4A Gateway recovery — CI verificata su `9b029beaec1f5419ff3820a1f038597bb4e8dcbf`: module run 36859068962, recovery-cycle 83/83 PASS, Java 51/51 PASS, source checksums PASS, container-smoke/non-root PASS. Pairwise Authorization 36859069018, Shared SDK 36859068821 e Gateway 36859068774 SUCCESS. Codice operativo pinnato 2011743b06f685004f74ccef045d1b34b273192b identico al codice verificato; successiva correzione riguarda soltanto hash dei byte Git e documentazione. Pronto blocco SSH; prossimo gate: apply/readback due route Gateway dall'operatore. Nessun deploy Gateway dichiarato eseguito prima del suo output; DRAFT ancora non pubblicata, HUMAN owner authorization e materializzazione 8/8 da provare.


### R4A — Gateway recovery installato/verificato dall'operatore (2026-10-01 14:15 Europe/Rome)

Output operatore: plan/apply/verify PASS, 2 route GET review/POST retry con UUID/action esatti, tutte le route esistenti preservate. Ricevuta privata `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/gateway-routes-receipt.json`; protocollo privato `gateway-routes.xG4lR0`. Non stampare receipt/snapshot OIDC. IAM precedentemente verificato: scope `udp.materialization.retry` senza drift, OPTIONAL/BOUND sul client `ouf-human-admin`. Nessuna pubblicazione policy chiamata, nessun retry/replay/reactivation. Owner HUMAN authorization ancora NOT_PROVEN. Prossimo gate: leggere bozza b305bcae-a03f-4f0d-8b81-81508bcddb24 rev0 e ACTIVE da sessione HUMAN fresca, preview esatta e simulazioni positive/negative; pubblicazione separata governata. Target invariato: recuperare soltanto i 3 job UDP originali, poi provare 8/8 materializzazione e search. PET Authorization §36.10 e UDP §§109.6–109.7 obbligatori; parametro environment esplicito e doc/deploy automation sempre aggiornati.
