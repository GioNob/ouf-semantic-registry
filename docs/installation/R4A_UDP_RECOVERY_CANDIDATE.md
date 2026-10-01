# R4A — build isolata della candidata UDP e sonda GET-only

> **Stato corrente — 2026-10-01 19:28 Europe/Rome:** consegna e materializzazione **8/8 PASS**; Search/serving, storage indipendente e R-INSTALL **aperti**. PET obbligatori a ogni sprint; ambiguità o lacune normative da decidere con l’utente. Dettaglio nell’ultimo checkpoint R4A.


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


### R4A — Review/publicazione HUMAN della bozza esistente, helper governato (2026-10-01)

Nuovo helper parametrizzato `scripts/r4a_review_publish_scoped_human_policy.py` con modi review/publish/verify. Usa soltanto draft-receipt/resources esistenti, nessuna ricreazione del draft, registrazione o modifica di grant. Confronta identità, hash baseline, diff esatta, resourceType/ID/attrs/DataAccessLabel e scadenza; mantiene ogni entry preesistente. Legge ACTIVE e draft/ETag, verifica catalogue owner/descriptor, preview e simulazioni lato owner Authorization: ALLOW per ogni risorsa/label; DENY per SERVICE, AI_AGENT, scope assente, soggetto/ID/type/attrs/label diversi o label assente; contesti tenant esterni respinti HTTP403 dal boundary (non confondere con decisione SDK). Response deve essere HYPOTHETICAL_NOT_IAM_VERIFIED/authoritative=false, hash e revisioni coerenti. Le POST preview/simulate scrivono audit amministrativo, non mutano policy ACTIVE/draft o business UDP: non dichiararle globalmente read-only. Tre risorse lab con quattro attrs e una label ciascuna producono 41 scenari. Nessuna prova HUMAN owner UDP ottenuta dalle simulazioni.

Pubblicazione: login Device Grant HUMAN fresco sul client configurato, account OUF corretto verificato per sub/tenant/issuer/audience/adminscope; conferma locale esatta `PUBBLICO <bundle:version>` dopo review. La bozza lab è b305bcae-a03f-4f0d-8b81-81508bcddb24 rev0/base:35, target:36, grant scadono 2026-10-02T10:00:00Z. Recheck dopo conferma di expiry/draft/ACTIVE; durable intent root 0600 prima di POST publish; response + GET draft PUBLISHED rev1 e ACTIVE esatto (publishedAt stabilito dall'owner). Receipt privata impedisce repost; verify legge soltanto policy/draft con sessione HUMAN fresca, anche dopo expiry per diagnosticare una pubblicazione storica, senza ripubblicare. Per state senza publish intent serve riconciliazione, non forzare receipt né blind retry. Nessuna chiamata UDP retry/intake/replay/source activation. Runbook esegue fresh GET Gateway verify prima del login. Test locali 26 PASS, 6 nuovi; CI recovery passa da83 a89 con checksum esatti sui byte pubblicati. Attendere CI e output operatore prima di dichiarare pubblicato :36. Dopo pubblicazione, next gate sessione HUMAN col nuovo scope + reale GET review dei tre job e controlli Spring/reference, poi eventuale retry HUMAN originale, poi readback8/8/search. Restano tutti i blocker ereditati e R-INSTALL/portabilità/autodeploy non chiusi.


#### R4A UDP recovery policy — review simulazioni e pubblicazione HUMAN

Prerequisiti: ricevute draft/resources già presenti e IAM OPTIONAL verificato; fresh Gateway GET verify eseguito dal blocco. Questo ciclo non ricrea draft né grant. Usa account OUF `ouf-admin` per Device Grant (`ouf-human-admin` è client OIDC; `oufadmin` nel master Keycloak non è questo login). Non incollare browser code o token in chat. Receipt root 0600 conserva intent, preview/simulazioni e readback; se output SSH perso rieseguire il blocco: receipt esistente -> soltanto verify, mai POST publish automatico.

Review invoca POST amministrative preview/simulate: scrivono audit, non policy/business. Dopo PASS propone :35 -> :36 con tre grant nominali esatti e bounded, e richiede nel terminale `PUBBLICO ouf-lab-authorization:36`; confermare soltanto se riepilogo è coerente. Se risposta persa o mismatch, non eliminare la receipt: riconciliare con GET. Pubblicazione fallisce su drift, expiry vicina, scenario inatteso, identità non conforme o conferma diversa. Lo script non invoca retry/materializzazione. Prossimo gate è GET reale UDP con HUMAN e nuovo scope, non la simulazione ipotetica.

```bash
set -euo pipefail
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
REVISION=190e3f052e5a0612109da3145534e73ae519dae7
WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT
for SCRIPT in r4a_review_publish_scoped_human_policy.py r4a_prepare_scoped_human_policy.py r4a_install_materialization_recovery_routes.py r4a_recovery_binding_inventory.py r4a_execution_route_inventory.py r4a_prepare_frozen_compatibility_probe.py; do
  git show "$REVISION:scripts/$SCRIPT" > "$WORK_DIR/$SCRIPT"
done
STATE_DIR=/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy
# Fresh GET-only Gateway readback before policy publication; private credentials never printed.
sudo python3 -B "$WORK_DIR/r4a_install_materialization_recovery_routes.py" verify \
  --gateway-container ouf-apisix --config-destination /usr/local/apisix/conf/config.yaml \
  --admin-origin http://127.0.0.1:9180 --curl-image curlimages/curl:8.16.0 \
  --template-id r4a-onboarding-runtime-publications-list \
  --template-uri /api/onboarding/v1/runtime/publications \
  --template-node ouf-onboarding:8080 --template-scope ouf.onboarding.configuration.read \
  --public-host api.ouf-lab.it --udp-node ouf-udp:8080 \
  --base-path /api/udp/v1/governance/materialization/jobs --scope udp.materialization.retry \
  --review-id r4a-udp-human-materialization-review --retry-id r4a-udp-human-materialization-retry \
  --snapshot "$STATE_DIR/binding-inventory.json" --receipt "$STATE_DIR/gateway-routes-receipt.json"
COMMON=(
  --issuer https://auth.ouf-lab.it/realms/ouf
  --client ouf-human-admin
  --audience ouf-api-gateway
  --admin-scope authorization.policy.admin
  --base-url https://api.ouf-lab.it/api/trusted-human/v1/authorization
  --tenant ouf-lab
  --subject b93d8cf6-cd14-4ee6-91d7-84cd76c4f500
  --capability udp.materialization.retry
  --operation COMMAND
  --required-scope udp.materialization.retry
  --owner udp
  --expected-resources 3
  --min-remaining-seconds 120
  --draft-receipt "$STATE_DIR/draft-receipt.json"
  --resources "$STATE_DIR/resources.json"
  --receipt "$STATE_DIR/publication-receipt.json"
)
# Login Device Grant fresco: browser/codice solo in terminale, account OUF ouf-admin.
# Non copiare codice/token in chat. Conferma finale esplicita nel terminale.
if sudo test -e "$STATE_DIR/publication-receipt.json"; then
  sudo python3 -B "$WORK_DIR/r4a_review_publish_scoped_human_policy.py" verify "${COMMON[@]}"
else
  sudo python3 -B "$WORK_DIR/r4a_review_publish_scoped_human_policy.py" publish "${COMMON[@]}"
fi
```


R4A policy review/publish CI finale verificata su `66ac8b1db36e83a8558aa4a8ab3fa9366f1205a8`: module run 36861896858 SUCCESS, recovery-cycle 89/89 PASS, Java 51/51 PASS, checksum/build/non-root container PASS; Authorization pairwise36861896871, Shared SDK36861896859, Gateway36861896946 SUCCESS. Codice pinnato190e3f052e5a0612109da3145534e73ae519dae7; runbook pronto. Stato al passaggio operatore: IAM/Gateway PASS già ricevuti, bozza ancora non pubblicata secondo ultima prova, nessun retry eseguito; richiede login OUF ouf-admin e conferma HUMAN terminale dopo review41scenari. Ricevuta publication-receipt.json root privata, output perso -> verify senza repost. Nessuna prova owner UDP/materializzazione8/8/search anticipata.


### R4A — Conferma terminale fallita prima della pubblicazione, fix e ripresa (2026-10-01 14:32 Europe/Rome)

Operatore: REVIEW PASS 3 risorse/41 scenari, ACTIVE_UNCHANGED=true, SIMULATION_AUTHORITATIVE=false. Receipt privata publication-receipt.json scritta. La proposta :35->:36 è stata mostrata ma `confirm()` ha sollevato UnsupportedOperation prima del durable publish intent e prima del POST. Causa riprodotta: Python open('/dev/tty','r+') tenta buffered random I/O su terminale non seekable. Nessun publish/retry UDP eseguito in questa invocazione; non eliminare/ricreare la receipt né bozza. Owner HUMAN authorization resta NOT_PROVEN.

Fix: prompt su stdout flush e terminale aperto solo lettura 'r'. Test reali pty.fork con /dev/tty non seekable: frase corretta PASS, frase errata DENY. Nuovo modo resume accetta esclusivamente receipt root0600 REVIEWED_NOT_PUBLISHED con mode originario publish e hash draft/resources identici; fresh HUMAN login + preview/simulazioni completo + ACTIVE/draft/ETag/expiry recheck + nuova conferma terminale. Non utilizza vecchie simulazioni come autorizzazione. Publish intent/PASS_PUBLISHED/altre receipt bloccano resume prima del login, richiedono verify senza repost. Lost response originaria e scope/expiry/drift restano fail-closed. Test locali10 helper PASS (4 nuovi); totale CI93 previsto. Consultati PET Authorization§36.10 e UDP§109.6. Nessun binding installativo nuovo hardcoded e nessuna modifica Gateway/IAM/UDPbusiness/migrazione. Next gate rimane pubblicazione HUMAN :36 verificata, poi GET reale UDP nuovo scope, reference readiness e recovery originale3job; 8/8/search ancora NOT_PROVEN e blocker ereditati invariati.


#### R4A UDP recovery policy — ripresa dopo errore terminale non seekable

Eseguire dopo riconnessione SSH. Usa ricevuta esistente REVIEWED_NOT_PUBLISHED/mode publish, non eliminare alcun file e non ricreare bozza/grant. Login fresco account OUF ouf-admin, 41 simulazioni ripetute, nuova conferma nel terminale con apertura /dev/tty solo lettura. Prima esegue verify Gateway GET. Pubblicazione con durable intent e readback; nessun retry UDP. Se receipt indica già publish intent o PASS_PUBLISHED, resume rifiuta senza POST: usare verify sullo stesso helper/argomenti per riconciliare, mai cambiare stato manualmente.

```bash
set -euo pipefail
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
REVISION=dcd6703e7bb5d8a1f7e29b6a9c15f4c8be0e58d4
WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT
for SCRIPT in r4a_review_publish_scoped_human_policy.py r4a_prepare_scoped_human_policy.py r4a_install_materialization_recovery_routes.py r4a_recovery_binding_inventory.py r4a_execution_route_inventory.py r4a_prepare_frozen_compatibility_probe.py; do
  git show "$REVISION:scripts/$SCRIPT" > "$WORK_DIR/$SCRIPT"
done
STATE_DIR=/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy
# Fresh GET-only Gateway readback before policy publication; private credentials never printed.
sudo python3 -B "$WORK_DIR/r4a_install_materialization_recovery_routes.py" verify \
  --gateway-container ouf-apisix --config-destination /usr/local/apisix/conf/config.yaml \
  --admin-origin http://127.0.0.1:9180 --curl-image curlimages/curl:8.16.0 \
  --template-id r4a-onboarding-runtime-publications-list \
  --template-uri /api/onboarding/v1/runtime/publications \
  --template-node ouf-onboarding:8080 --template-scope ouf.onboarding.configuration.read \
  --public-host api.ouf-lab.it --udp-node ouf-udp:8080 \
  --base-path /api/udp/v1/governance/materialization/jobs --scope udp.materialization.retry \
  --review-id r4a-udp-human-materialization-review --retry-id r4a-udp-human-materialization-retry \
  --snapshot "$STATE_DIR/binding-inventory.json" --receipt "$STATE_DIR/gateway-routes-receipt.json"
COMMON=(
  --issuer https://auth.ouf-lab.it/realms/ouf
  --client ouf-human-admin
  --audience ouf-api-gateway
  --admin-scope authorization.policy.admin
  --base-url https://api.ouf-lab.it/api/trusted-human/v1/authorization
  --tenant ouf-lab
  --subject b93d8cf6-cd14-4ee6-91d7-84cd76c4f500
  --capability udp.materialization.retry
  --operation COMMAND
  --required-scope udp.materialization.retry
  --owner udp
  --expected-resources 3
  --min-remaining-seconds 120
  --draft-receipt "$STATE_DIR/draft-receipt.json"
  --resources "$STATE_DIR/resources.json"
  --receipt "$STATE_DIR/publication-receipt.json"
)
# Ripresa della receipt REVIEWED_NOT_PUBLISHED; nessuna cancellazione o nuova bozza.
# Fresh login OUF ouf-admin; dopo la review digitare la frase richiesta nel terminale.
sudo python3 -B "$WORK_DIR/r4a_review_publish_scoped_human_policy.py" resume "${COMMON[@]}"
```


R4A terminal fix CI finale su `303758a89ebe4d00c4ee3056774b421bfb38fd9d`: module run36863065590 tutti job SUCCESS (Java, recovery93/93, checksum, container-smoke); SharedSDK36863065702, Authorization36863065777 e Gateway36863065591 SUCCESS. Fix operativo pinnato dcd6703e7bb5d8a1f7e29b6a9c15f4c8be0e58d4, test includono tty reale non seekable e resume dopo UnsupportedOperation con una sola pubblicazione. Pronto ripartire in SSH interattiva usando receipt originale REVIEWED_NOT_PUBLISHED. Nessun POST policy da questo agente; ultimo output operatore è reviewPASS/pubbloccata prima di intent, retryUDP=false. Dopo ripresa verificare ACTIVE:36 prima del prossimo gate ownerHUMAN/3job/8materializzazione/search.


### R4A — Pubblicazione scoped HUMAN confermata (2026-10-01 15:28 Europe/Rome)

Operatore ha ripetuto review PASS (3 risorse,41scenari, ACTIVE invariata durante review) e inserito conferma terminale esatta. PUBLISH PASS ACTIVE=ouf-lab-authorization:36, draft PUBLISHED revision1, exact scoped diff/readback verificati. Receipt privata publication-receipt.json; non stampare. La precedente conferma non seekable è superata. Grant nominali HUMAN per soltanto tre job originali, attrs/type/DataAccessLabel esatti, expiry2026-10-02T10:00Z, altre entry preservate. Nessun retry UDP ancora eseguito; simulation authoritative=false; HUMAN owner authorization ancora NOT_PROVEN. Next gate: login HUMAN fresco richiedendo udp.materialization.retry, GET reali Gateway->UDP review dei tre job; verificare authz owner, QUARANTINED/DURABLE/v2 e reference contractReady nel profilo Spring effettivo. Solo dopo PASS preparare eventuale retry HUMAN per originale job con expectedVersion/snapshotHash/operationId, poi readback8/8/search. Non replay/reactivation/resend, nessun repair DB. Restano tutti i blocker ereditati e industrializzazione R-INSTALL/multi-host/network/domain/tenant.


### R4A — Reale HUMAN GET review UDP, prossimo gate dopo ACTIVE:36 (2026-10-01)

Helper `scripts/r4a_read_human_materialization_review.py` parametrizzato: root receipt nuova/esclusiva privata, verifica publication PASS_PUBLISHED/resourcesHash/descriptor COMMAND HUMAN, set esatto3job/handoff ed expectedstate. Nuovo Device Grant richiede solo scope OPTIONAL udp.materialization.retry; verifica sub/tenant/issuer/client/audience/scope. UDP owner riceve solo GET (nessun business POST): anonimo deve401/403, job esistente fuori scope deve403, quindi GET3job originali200 con binding source/run/handoff esatto, QUARANTINED/DURABLE/v2 e failure tecnica attesa. Legge retryEligible/contractReady/contractCheck/snapshotHash/verifiedBaselineHash nella vera applicazione Spring; valori dei ref/hash solo receipt privata. PASS_AUTHORIZATION_REFERENCE_BLOCKED distingue auth riuscita da reference gate non-ready e vieta retry. Anche PASS non esegue materializzazione. Le normali decisioni di autorizzazione possono produrre audit; OWNER_GET_ONLY non implica assenza globale di audit. Sessione login OIDC utilizza POST token endpoints, nessun owner UDP POST. ReviewGET corrente non prova causalità dei3failurestorici né materializzazione8/8/search.

Se99testCI PASS, consegnare runbook per login ouf-admin e GET reale. Scope fine-grained/HUMAN prova dalla risposta reale owner, non simulazione. Expected policy:36 è confronto con ricevuta di pubblicazione verificata, non ulteriore prova della versione globale ACTIVE corrente o contenuto in-memory del resolver. Test6 nuovi coprono soleGET/deny, receipt drift prelogin, scope anon/outside erroneamenteallow, source/handoff/version mismatch, payloadextra respinto, contract blocked. Corretto soltanto test pty precedente: hangup può anticipare visibilità waitpid, ora attende exit entro timeout senza falsa failure; nessuna modifica runtime di quella conferma. PET UDP§109.7 reference readiness e Authorization§36.10 owner enforcement consultati; binding installativi solo CLI/runbook, altri gate ereditati invariati.


#### R4A UDP recovery — GET reali HUMAN dopo policy36

Sessione HUMAN fresca account OUF ouf-admin; Device Grant richiede scope OPTIONAL udp.materialization.retry. Questo blocco non ripubblica policy, non cambia IAM/Gateway, non invoca POST UDP/retry/replay/intake né source activation. OIDC login usa POST ai soli endpoint IAM. Fa GET anonimo e GET job esistente fuori scope (attesi401/403 e403), poi GET3job originali. Receipt distinta root0600 per ogni lettura, conserva snapshot/hash privati; incollare soltanto output simbolico, mai codici login/token/hash/ref/payload. PASS_AUTHORIZATION_REFERENCE_GATE_BLOCKED permette distinguere owner auth da contract readiness e resta blocker per retry. PASS pieno prova soltanto review runtime Spring e accesso corrente, non8materializzazioni o causalitàstorica. L'expectedpolicy36 viene dalla receipt pubblicazione, non da una nuova lettura globale ACTIVE né prova generica di policyinmemory. Grant scadono2026-10-02T10:00Z; owner enforcement fail-closed se non più validi. Se output perso si può rifare il blocco GET-only con nuova receipt; conservare tutte le precedenti.

```bash
set -euo pipefail
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
REVISION=d06a5ca48d2cfc058f04ce73e4ba0703fdce5566
WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT
for SCRIPT in r4a_read_human_materialization_review.py r4a_prepare_scoped_human_policy.py; do
  git show "$REVISION:scripts/$SCRIPT" > "$WORK_DIR/$SCRIPT"
done
STATE_DIR=/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy
RECEIPT="$STATE_DIR/human-review-$(date -u +%Y%m%dT%H%M%S)-$$.json"
sudo python3 -B "$WORK_DIR/r4a_read_human_materialization_review.py" \
  --issuer https://auth.ouf-lab.it/realms/ouf --client ouf-human-admin \
  --audience ouf-api-gateway --tenant ouf-lab \
  --subject b93d8cf6-cd14-4ee6-91d7-84cd76c4f500 \
  --scope udp.materialization.retry --expected-policy ouf-lab-authorization:36 \
  --base-url https://api.ouf-lab.it/api/udp/v1/governance/materialization/jobs \
  --publication-receipt "$STATE_DIR/publication-receipt.json" \
  --resources "$STATE_DIR/resources.json" --receipt "$RECEIPT" \
  --expected-version 2 --expected-resources 3 \
  --expected-failure UDP_REFERENCE_INTEGRITY_CONTRACT_INVALID \
  --binding 7793566d-b9d4-4402-8cda-c09b8f135c04:8869a6d6-3d82-4514-a63a-d23f9b26d48f \
  --binding e7572836-f8af-4c58-b5fc-12d7aff5db1d:aed8ef93-6d00-4cf0-868d-d2d82d79b524 \
  --binding e5b6ca24-6143-4ae5-8907-5dce398abfa3:e58faf8c-c35a-4106-b4b6-67e58dec9774 \
  --outside-job f84de729-c245-4e34-80cf-764c4eb0f160
```


R4A HUMAN GET review CI finale su `0bd124c2fdc9554d784273fb3aad14fe4dedbb8c`: module run36870489064 Java/checksum/container SUCCESS, recovery99/99 PASS; Authorization36870489030, SharedSDK36870489031 e Gateway36870489124 SUCCESS. Codice operativo pinnato d06a5ca48d2cfc058f04ce73e4ba0703fdce5566. Pronto gate operatore: sessione HUMAN scopeudp.materialization.retry e soleGET reali. Receipt interna in caso reference nonready è AUTHORIZATION_PASS_REFERENCE_GATE_BLOCKED, output R4A_UDP_HUMAN_REVIEW=BLOCKED/HUMAN_OWNER_AUTHORIZATION_PROVEN=true. Non confondere con PASS della materializzazione: nessun retry finora,8/8/search ancora da provare. Pubblicazione:36 giàPASS ricevuta da operatore, GETowner proof non ancora ricevuta.


### R4A — Output GET HUMAN perso / shell chiusa dopo THS (2026-10-01 16:35 Europe/Rome)

Operatore segnala shell chiusa dopo conferma THS, output finale non disponibile. Non assumere review PASS né owner authz/reference ready; ultima prova certa resta pubblicazione ACTIVE:36 PASS, retryUDP mai chiamato dal blocco GET-only consegnato. Recuperare esclusivamente receipt human-review-*.json rootprivate, soli metadata/stati, senza nuovo login/GET/POST/retry. Receipt può essere RESERVED/LOGIN_PENDING/partial oppure PASS_READY o AUTHORIZATION_PASS_REFERENCE_GATE_BLOCKED; stati incompleti non provano esito positivo e il vecchio helper non persiste l'exception finale, quindi la causa remota può restare ignota dopo lettura. Le receipt sono evidenza salvata, non query live né snapshot fresco per futuro retry.

Difetto certo individuato nel bootstrap incollato in SSH: `set -euo pipefail` impostava opzioni della shell interattiva chiamante. Qualsiasi exit nonzero (incluso gate reference bloccato previsto, exit2) può chiudere tale shell/sessione. Non attribuire automaticamente la chiusura a nuovo bug applicativo né escluderlo senza evidence. Da ora bootstrap in processo bash separato, status gestito con OR nel chiamante; non alterare opzioni interattive. I runbook interni possono usare set-e dentro il processo isolato. Recovery metadata testato localmente con fixture LOGIN_PENDING/PASS_READY/REFERENCE_BLOCKED e private-mode unsafe: nessun ref/hash/payload/token stampato, nessuna falsa prova completa da partial. Nessun deploy/cambioIAM/Gateway/policy/UDPbusiness e nessun nuovo retry. Handoff/manuale/roadmap/runbook aggiornati; nextgate invariato fino a recupero output reale.


#### R4A UDP recovery — recupero output perso dalle ricevute HUMAN

Questo blocco legge al massimo le tre receipt più recenti, verifica rootownership/0600 e directory0700, stampa solo stati/counter/boolean e codici contract whitelisted. Non stampa payload/ref/hash/token o contenuto della receipt. Nessun login né accesso live API/DB; nessun replay/retry. Se stato LOGIN_PENDING con zero/partial review, successo completo NOT_PROVEN. È normale che il vecchio helper non distingua tutte le fasi dalla sola status; non dedurre che login sia ancora in corso né eliminare file. Il bootstrap da chat deve avviare bash separato con status gestito nel chiamante, mai applicare set-e alla shell interattiva.

```bash
set -euo pipefail
sudo python3 - /etc/ouf/deploy-snapshots/udp-materialization-recovery-policy <<'PY'
import json, os, re, stat, sys
from pathlib import Path
root=Path(sys.argv[1])
def require(value):
    if not value:raise RuntimeError('PRIVATE_EVIDENCE_UNSAFE')
def private(path,directory=False):
    info=path.lstat()
    require(info.st_uid==0 and stat.S_IMODE(info.st_mode)==(0o700 if directory else 0o600)
        and (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)))
def load(path):
    private(path);require(path.stat().st_size<=8000000)
    return json.loads(path.read_text())
def boolean(value):return str(value).lower() if type(value) is bool else 'NOT_RECORDED'
try:
    require(os.geteuid()==0);private(root,True)
    rows=[p for p in root.glob('human-review-*.json')
          if re.fullmatch(r'human-review-[0-9]{8}T[0-9]{6}-[0-9]+\.json',p.name)]
    for p in rows:private(p)
    rows=sorted(rows,key=lambda p:p.stat().st_mtime_ns,reverse=True)[:3]
    print('HUMAN_REVIEW_RECEIPTS_FOUND='+str(len(rows)))
    for receipt_index,path in enumerate(rows,1):
        value=load(path)
        allowed=('RESERVED_NO_POST','LOGIN_PENDING_NO_BUSINESS_POST','PASS_READY',
                 'AUTHORIZATION_PASS_REFERENCE_GATE_BLOCKED','BLOCKED')
        status=value.get('status')
        require(status in allowed)
        reviews=value.get('reviews',[]);require(isinstance(reviews,list) and len(reviews)<=3)
        print('RECEIPT_'+str(receipt_index)+'_PATH='+str(path)+' PRIVATE=true')
        print('RECEIPT_'+str(receipt_index)+'_SAVED_STATUS='+status)
        print('RECEIPT_'+str(receipt_index)+'_VALIDATED_REVIEWS='+str(len(reviews)))
        for field,label in (('anonymousHttp','ANONYMOUS_HTTP'),('outsideScopeHttp','OUTSIDE_SCOPE_HTTP')):
            number=value.get(field)
            require(number is None or type(number) is int and number in (401,403))
            print('RECEIPT_'+str(receipt_index)+'_'+label+'='+('NOT_RECORDED' if number is None else str(number)))
        for index,row in enumerate(reviews,1):
            review=row['review'];check=review.get('contractCheck')
            require(check in ('READY','MISSING','CONTRACT_INVALID','CATALOG_UNAVAILABLE','NOT_ELIGIBLE'))
            version=review.get('stateVersion');require(type(version) is int and 0<=version<=1000000)
            require(review.get('state')=='QUARANTINED' and review.get('intakeState')=='DURABLE')
            print('RECEIPT_'+str(receipt_index)+'_REVIEW_'+str(index)
                +' STATE=QUARANTINED INTAKE=DURABLE VERSION='+str(version)
                +' RETRY_ELIGIBLE='+boolean(review.get('retryEligible'))
                +' CONTRACT_READY='+boolean(review.get('contractReady'))+' CONTRACT_CHECK='+check)
        if status in ('PASS_READY','AUTHORIZATION_PASS_REFERENCE_GATE_BLOCKED'):
            require(len(reviews)==3 and value.get('anonymousHttp') in (401,403)
                    and value.get('outsideScopeHttp')==403)
            print('RECEIPT_'+str(receipt_index)+'_HUMAN_OWNER_AUTHORIZATION_SAVED_PROOF=true')
        else:print('RECEIPT_'+str(receipt_index)+'_COMPLETE_SUCCESS_NOT_PROVEN=true')
    print('R4A_HUMAN_REVIEW_OUTPUT_RECOVERY=COMPLETE READ_ONLY=true SAVED_EVIDENCE_ONLY=true'
          +' LIVE_STATE_NOT_QUERIED=true LOGIN=false RETRY=false REPLAY=false SECRETS_NOT_PRINTED=true')
except Exception as error:
    print('R4A_HUMAN_REVIEW_OUTPUT_RECOVERY=BLOCKED TYPE='+type(error).__name__
          +' READ_ONLY=true RETRY=false SECRETS_NOT_PRINTED=true')
    raise SystemExit(1)
PY
```


### R4A — Receipt reale recuperata: negativi PASS, zero review validate (2026-10-01 16:46 Europe/Rome)

Operatore: una receipt human-review-20261001T143329-3493421.json, status LOGIN_PENDING_NO_BUSINESS_POST, anonymousHttp401, outsideScopeHttp403, reviews0. Questo prova login concluso e due negativi osservati/salvati, non successo delle tre review autorizzate. Non reinterpretare il vecchio status come login ancora pendente; il marker non veniva aggiornato dopo il login. Errore/stato HTTP della successiva richiesta non registrati dal vecchio helper, causa corrente ignota: possibileHTTPdeny/trasporto/parser, non dichiarare guastoIAM/mapper. Nessun retryUDP. Ultima policy provata:36, vecchie3QUARANTINED non riverificatelive.

Fix osservabilità helper: phase persistita prima di login/anon/outside/ogniGET e validation, negativi salvati progressivamente; ownerHTTP e responseShape solo tipologie/campi, nessun valore inatteso/payload, salvati prima di check. Main persiste BLOCKED/safeFailureCode/type/phase solo su receipt esclusivamente creata da quella invocazione; errori estranei ->UNCLASSIFIED, mai exception-message arbitrario, mai overwrite di receipt precedente. SystemExit2 referencegate atteso preserva AUTHORIZATION_PASS_REFERENCE_GATE_BLOCKED. Tre test nuovi provano denial/transport/schema salvati, negativi preservati e receiptnonowned intatta; 9 testhelperPASS, CI102previsto. Runbook nuovo: nuova receipt GET-only, protocollo root0600 che filtra solo righe UDP_HUMAN/R4A_UDP (nessun devicecode/token), loginouf-admin, shell bootstrap in bash separato con status gestito; nessun POSTUDP/publish/replay. Conservare receipt precedente. PET UDP109.7 consultato; ownerpositive/referenceSpring/8materializzazioni/search ancoraNOTPROVEN.


#### R4A UDP recovery — nuove GET HUMAN con errore e protocollo persistiti

La receipt precedente del 20261001T143329 ha soli negativi401/403 e review0; causa successiva ignota, non cancellarla. Helper corretto salva phase/safeFailureCode/failureType e HTTP strutturali prima di validation, solo nella nuova receipt da esso creata. Questo blocco rifà solo login Device Grant e GET reali, mai retry o POST UDP/policy. Protocollo root0600 contiene soltanto righe simboliche UDP_HUMAN/R4A_UDP, filtra browser-devicecode/token; il devicecode necessario resta sul terminale e non va incollato in chat. Il bootstrap incollato deve essere `bash <<'SH' || ...` in processo separato, non applicare set-e alla shell interattiva. La pipeline mantiene distinto exit Python da exit del capture. Se errore, riportare ultimo R4A...CODE/PHASE/ERROR_SAVED e exit; se output perso, receipt/protocollo privati restano disponibili. Accesso owner positivo/referenceSpring non ancora provati; niente retry basato su negativi.

```bash
set -euo pipefail
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
REVISION=d6c32cbf062618f0b255c51f8a7a8d6fb521e839
WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT
for SCRIPT in r4a_read_human_materialization_review.py r4a_prepare_scoped_human_policy.py; do
  git show "$REVISION:scripts/$SCRIPT" > "$WORK_DIR/$SCRIPT"
done
sudo bash -s -- "$WORK_DIR" <<'ROOT'
set -euo pipefail
umask 077
WORK_DIR=$1
STATE_DIR=/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy
LOG=$(mktemp "$STATE_DIR/human-review-protocol.XXXXXX")
printf 'HUMAN_REVIEW_PROTOCOL_LOG=%s PRIVATE=true\n' "$LOG"
RECEIPT="$STATE_DIR/human-review-$(date -u +%Y%m%dT%H%M%S)-$$.json"
set +e
python3 -B "$WORK_DIR/r4a_read_human_materialization_review.py" \
  --issuer https://auth.ouf-lab.it/realms/ouf --client ouf-human-admin \
  --audience ouf-api-gateway --tenant ouf-lab \
  --subject b93d8cf6-cd14-4ee6-91d7-84cd76c4f500 \
  --scope udp.materialization.retry --expected-policy ouf-lab-authorization:36 \
  --base-url https://api.ouf-lab.it/api/udp/v1/governance/materialization/jobs \
  --publication-receipt "$STATE_DIR/publication-receipt.json" \
  --resources "$STATE_DIR/resources.json" --receipt "$RECEIPT" \
  --expected-version 2 --expected-resources 3 \
  --expected-failure UDP_REFERENCE_INTEGRITY_CONTRACT_INVALID \
  --binding 7793566d-b9d4-4402-8cda-c09b8f135c04:8869a6d6-3d82-4514-a63a-d23f9b26d48f \
  --binding e7572836-f8af-4c58-b5fc-12d7aff5db1d:aed8ef93-6d00-4cf0-868d-d2d82d79b524 \
  --binding e5b6ca24-6143-4ae5-8907-5dce398abfa3:e58faf8c-c35a-4106-b4b6-67e58dec9774 \
  --outside-job f84de729-c245-4e34-80cf-764c4eb0f160 2>&1 |
  awk -v logfile="$LOG" '{ print; fflush(); if ($0 ~ /^(UDP_HUMAN_REVIEW_|R4A_UDP_HUMAN_REVIEW)/) { print >> logfile; fflush(logfile) } }'
RESULT=("${PIPESTATUS[@]}")
set -e
printf 'HUMAN_REVIEW_PROTOCOL_LOG=%s PRIVATE=true\n' "$LOG"
printf 'HUMAN_REVIEW_PROCESS_EXIT=%s OUTPUT_CAPTURE_EXIT=%s RETRY=false\n' "${RESULT[0]}" "${RESULT[1]}"
test "${RESULT[1]}" -eq 0
exit "${RESULT[0]}"
ROOT
```


R4A safe GET error capture CI finale su f89e9983b39759d8a45fc470dc2b14deca971904: module36880091805 Java/checksum/container SUCCESS, recovery102/102 PASS; Authorization36880092062, SDK36880092071 e Gateway36880091803 SUCCESS. Codice operativo d6c32cbf062618f0b255c51f8a7a8d6fb521e839. Protocol-filter testPASS: codice Device Grant visibile al terminale ma escluso dal fileprivato. Nuovo blocco pronto, bootstrap externalbash con ORhandler protegge shell; nessun retrybusiness. Attesa nuovaGET per classificare errore successivo ai due negativi, ownerpositivo/refgate non ancora provati; conservata receipt143329.


### R4A — Attesa dopo LOG causata dal filtro interattivo, correzione (2026-10-01 17:05 Europe/Rome)

Operatore segnala attesa prolungata subito dopo HUMAN_REVIEW_PROTOCOL_LOG=...TwWflM, prima del codice THS. Raccomandato Ctrl+C, nessun inserimento credenziali alla cieca. Riprodotto localmente con mawk1.3.4: producer stampa DeviceCode flush e attende input, filtro awk precedente non consegna la linea prima di EOF (fflush agiva solo sull'output). Deadlock di presentazione: login attende conferma che non può essere effettuata perché il codice è trattenuto. Difetto del runbook/logger, il precedente test di filtraggio controllava solo processo terminato, non interattività. Non usare quel filtro e non attribuire questa attesa a nuova prova di failureowner.

Sostituito awk con python3-u logger stdin line-by-line, stdout write+flush immediato; scrive sul protocollo root0600 solo prefixUDP_HUMAN/R4A_UDP, nessun devicecode/token. Producer helper avviato anche -u. Test interattivo PASS: codice visibile entro2sec prima della conferma, producer ancora in attesa, poi esito salvato e codice escluso dal protocollo; filtrovecchio WITHHELD=true riprodotto. bash-nPASS. Solo documentazione/runbook modificati, Pythonhelperresta codice d6c32cbf062618f0b255c51f8a7a8d6fb521e839 giàCI102PASS; nessun cambio owner/Docker/IAM/Gateway/policy o retry. Nuovo loginGET-only dopo interruzione, nuova receipt/protocollo; conservare TwWflM e receiptprecedenti, sono evidencepotenzialmenteparziali. Sempre bootstrap externalbash con ORhandler, mai set-einterattivo. Ultime prove owner: negativi401/403 salvati, reviewpositive0 nella receiptprima; nuovaownerpositive/refgate/8materializzazioni/search ancoraNOTPROVEN. Aggiornati handoff/manuale/roadmap/runbook.


#### R4A UDP recovery — GET HUMAN con protocollo immediato senza awk

Interrompere il precedente blocco con Ctrl+C e attendere il ritorno del prompt. Il nuovo logger Python rende immediatamente visibili browser/code THS, mantenendo fuori dal protocollo DeviceCode/token. Non usare il runbook con awk per logininterattivo. Account OUF ouf-admin; solo login IAM e GET UDP, niente retry/publish/replay. Protocollo e receipt nuove e private; non cancellare le precedenti. Il bootstrap deve usare bash separato con ORhandler per mantenere la shell aperta. Se codice non compare entro circa60sec, non aspettare indefinitamente: riportare le righe simboliche o assenza di nuove righe, senza token/devicecode; i timeout HTTPsono30sec per chiamata e precedono il codice con due chiamate IAM. Dopo login, ultima riga CODE/PHASE/ERROR_SAVED indica la failure effettiva, oppure PASS/referencegateBLOCKED. Nessuna prova materiale8/8 anticipata.

```bash
set -euo pipefail
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
REVISION=d6c32cbf062618f0b255c51f8a7a8d6fb521e839
WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT
for SCRIPT in r4a_read_human_materialization_review.py r4a_prepare_scoped_human_policy.py; do
  git show "$REVISION:scripts/$SCRIPT" > "$WORK_DIR/$SCRIPT"
done
sudo bash -s -- "$WORK_DIR" <<'ROOT'
set -euo pipefail
umask 077
WORK_DIR=$1
STATE_DIR=/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy
LOG=$(mktemp "$STATE_DIR/human-review-protocol.XXXXXX")
printf 'HUMAN_REVIEW_PROTOCOL_LOG=%s PRIVATE=true\n' "$LOG"
RECEIPT="$STATE_DIR/human-review-$(date -u +%Y%m%dT%H%M%S)-$$.json"
set +e
python3 -u -B "$WORK_DIR/r4a_read_human_materialization_review.py" \
  --issuer https://auth.ouf-lab.it/realms/ouf --client ouf-human-admin \
  --audience ouf-api-gateway --tenant ouf-lab \
  --subject b93d8cf6-cd14-4ee6-91d7-84cd76c4f500 \
  --scope udp.materialization.retry --expected-policy ouf-lab-authorization:36 \
  --base-url https://api.ouf-lab.it/api/udp/v1/governance/materialization/jobs \
  --publication-receipt "$STATE_DIR/publication-receipt.json" \
  --resources "$STATE_DIR/resources.json" --receipt "$RECEIPT" \
  --expected-version 2 --expected-resources 3 \
  --expected-failure UDP_REFERENCE_INTEGRITY_CONTRACT_INVALID \
  --binding 7793566d-b9d4-4402-8cda-c09b8f135c04:8869a6d6-3d82-4514-a63a-d23f9b26d48f \
  --binding e7572836-f8af-4c58-b5fc-12d7aff5db1d:aed8ef93-6d00-4cf0-868d-d2d82d79b524 \
  --binding e5b6ca24-6143-4ae5-8907-5dce398abfa3:e58faf8c-c35a-4106-b4b6-67e58dec9774 \
  --outside-job f84de729-c245-4e34-80cf-764c4eb0f160 2>&1 |
  python3 -u -c '
import sys
with open(sys.argv[1], "a", buffering=1) as log:
    for line in sys.stdin:
        sys.stdout.write(line); sys.stdout.flush()
        if line.startswith(("UDP_HUMAN_REVIEW_", "R4A_UDP_HUMAN_REVIEW")):
            log.write(line); log.flush()
' "$LOG"
RESULT=("${PIPESTATUS[@]}")
set -e
printf 'HUMAN_REVIEW_PROTOCOL_LOG=%s PRIVATE=true\n' "$LOG"
printf 'HUMAN_REVIEW_PROCESS_EXIT=%s OUTPUT_CAPTURE_EXIT=%s RETRY=false\n' "${RESULT[0]}" "${RESULT[1]}"
test "${RESULT[1]}" -eq 0
exit "${RESULT[0]}"
ROOT
```


### R4A — 2026-10-01: HTTP 403 HUMAN e difetto di ammissione scoped identificato

Ultimo output operatore: `R4A_UDP_HUMAN_REVIEW=BLOCKED CODE=HTTP_403 PHASE=OWNER_REVIEW_GET_1`, errore persistito; protocollo privato `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/human-review-protocol.79bSK5`. Processo review exit 1, capture exit 0, shell mantenuta aperta. Solo GET, nessun retry/replay. Policy attiva rimane `ouf-lab-authorization:36`, tre grant HUMAN nominali su job/label esatti, expiry 2026-10-02T10:00:00Z. Live rimane revisione afa5c4c4cf03bff4e39b02e27f898256c3776cbc / immagine sha256:024c6691888855ef4d5574cadacf060e0dfbf7ff891dbc9a747628f5b5c8a519 / Flyway 34. Ultimo business readback: cinque materializzati, tre QUARANTINED; otto consegne ACKED. Nessun nuovo business readback dopo questo GET negato.

Consultati PET Authorization v1.5 §36.10 e UDP v1.3 §§109.6–109.7: Gateway coarse, enforcement owner sul contesto autorevole, reference gate fail-closed e originali durable conservati. Difetto sorgente certo: MaterializationRecoveryApi ricava le capability da ServletAuthorization.resolve sul resourceContext generico capability; i grant esatti materialization-job non autorizzano quel contesto. Il servizio poi actor.require nega prima di poter chiamare owner.require sul job. Test precedenti di dominio non attraversavano il servlet/SDK endpoint.

Correzione candidate commit UDP `1aaa1f6b6a27281ea2d97106ec2033748bab1aee` su codex/r4a-materialization-recovery: solo API recovery usa OwnerAuthorization.candidates per ammissione descriptor/actor/scope fresca, mantenendo identità autenticata e snapshot SDK pinned; servizio continua obbligatoriamente owner.require prima della risoluzione contratti/serializzazione o transizione. Nessuna modifica SDK globale, IAM, grant, route, DB/migrazioni. Nuovi test HTTP MockMvc con SDK LocalAuthorization reale, grant nominale job/source/run/type/RAW label, PostgreSQL: GET e POST ammessi senza grant generico; altri job/soggetti/label/sorgenti, actor SERVICE/AI_AGENT, scope assente, anonimo/spoof negati senza catalog/eventi. Filtri JWT disabilitati in questi test per esercitare il server SPI autenticato; firma token/Gateway hanno verifiche separate. CI in corso, fix non ancora rilasciata. Causalità del 403 live compatibile con difetto, non ancora dimostrata end-to-end; possibili ulteriori problemi Gateway/cache/subject non esclusi.

Prossimo gate: completare CI candidate, build parametrizzata/pinned con migrazioni identiche, stage con live invariato, backup e release verificata senza retry; poi nuova GET HUMAN per prova owner/runtime e readiness storica. Non ripubblicare policy, non aggiungere grant generici, non ripetere intake/replay. Restano aperti materializzazione 8/8, verifica search/storage indipendente e industrializzazione R-INSTALL multi-host/network/domain/Ente.


### R4A — fix ammissione scoped verificata, pronta al rilascio (2026-10-01)

Codice candidate definitivo `83249a897eb4add4289b5181b3299f48ea4c0f99` (correzione API nel parent 1aaa1f6b, seconda commit corregge solo fixture SERVICE con servicePrincipalId obbligatorio). Primo run ha rilevato quella fixture invalida, non un fallo nel caso HTTP positivo; conservare traccia e non dichiarare verde quel run. Run definitivo recovery push36884410381 e PR36884416179 SUCCESS: 18/18 test, zero failures/errors/skipped (recovery13, referencegate3, evidence2); dipendenza SDK10/10 PASS. Module push36884410102/PR36884416158 SUCCESS in tutti e quattro job Java21/PostgreSQL17/image, DR, performance, supply-chain/deployment (vulnerability gate e Helm inclusi). SDK pairwise36884410299/36884416285 e CRS/grid36884410315/36884416242 SUCCESS. PR38 aggiornata sul comportamento finale; niente merge a main.

Il test HTTP autorizzato dimostra GET200 e POST200/v3 sul job originale senza grant generico; denied GET/POST non raggiungono catalogo né appendono eventi; input originale preservato. Sono verifiche CI con fixture, non prova della corrente identità/route/cache/policy live. Fix non ancora deployata, HUMAN owner positivo e mapper storico runtime ancora da provare. Ultimo output operatore resta HTTP403 OWNER_REVIEW_GET_1/no retry e live024c/afa5/Flyway34. Nuovo runbook usa helper già testati al pin3c0e5ef7, feature-enabled upgrade esplicito, preflight check-only, backup prima dello switch, readback originali e rollback fermo. Binding host/DB/rete/source/run/image/percorsi soltanto nel runbook, tutti helper parametrizzati; nessuna nuova migrazione/config hardcoded applicativa. Base image tag non digest-pinned: riproducibilità bit-for-bit non provata, gate industrializzazione resta aperto.

Prossima azione operatore: blocco unico build/probe/preflight/stage/backup/release nella sezione “fix ammissione scoped e release controllata” del runbook R4A_UDP_RECOVERY_CANDIDATE. Breve indisponibilità UDP durante backup/switch; nessun retry/intake/replay/publish policy. Build stampa START e salva output esteso nel build.log privato, timeout1800sec; non confondere silenzio del build con attesa THS. Dopo PASS release, nuova login/GET HUMAN attraverso Gateway e owner; se401/403 persiste, diagnosticare layer e subject/cache senza allargare grant. Non rieseguire release con stato incerto: riconciliare receipt privato. Grant scadono 2026-10-02T10:00Z. Materializzazione8/8 e search non provate; tutti gate ereditati e R-INSTALL invariati.


#### R4A UDP recovery — fix ammissione scoped e release controllata

Eseguire dal bootstrap esterno `bash <<'SH' || printf ...`, mantenendo la shell interattiva aperta anche se il gate fallisce. Codice UDP83249a8 verificato in tutte le CI. Il blocco prepara immagine isolata, esegue probe Java GET-only, preflight in sola lettura, stage fermo, poi backup e release con controlli. Preflight e stage consentono esplicitamente upgrade da recovery-enabled senza cambiare ambiente oltre al flag ammesso. Migrazioni identiche al liveafa5, originali job preservati (8,5SUCCEEDED,3QUARANTINED), Flyway34, negativi anon/spoof e backend health. Nessun retry/policy publish/IAM/route edit/replay. La release200/health non prova owner HUMAN né materializzazione. Tutti valori lab sono binding installativi dichiarati qui, da sostituire per altri Enti/host/reti; gli helper non hanno default lab.

Conservare path receipt build/stage/release e rollback stampati. In caso shell/output perso durante release, non ripetere il blocco: riconciliare quelle ricevute e live in sola lettura. Il build può restare senza nuove righe dopo START mentre scrive log privato (timeout30min); non stampare log integrali. Dopo release PASS attendere nuova review HUMAN GET-only prima di qualsiasi retry.

```bash
set -euo pipefail
umask 077
# Binding espliciti dell'installazione corrente.
ouf_coordination=/opt/ouf/semantic
ouf_work_parent=/opt/ouf/udp-recovery-candidates
ouf_udp_container=ouf-udp
ouf_candidate_container=ouf-udp-materialization-candidate
ouf_revision=83249a897eb4add4289b5181b3299f48ea4c0f99
ouf_baseline=afa5c4c4cf03bff4e39b02e27f898256c3776cbc
ouf_expected_image=sha256:024c6691888855ef4d5574cadacf060e0dfbf7ff891dbc9a747628f5b5c8a519
ouf_helpers=3c0e5ef7ace9e2a9bcf91a885080846f2191948e
ouf_run=86809c17-3354-45ca-a7e6-57e903944b24
ouf_source=managed-cinema-8ec8ae90
cd "$ouf_coordination"
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
ouf_fix_dir=$(mktemp -d /tmp/ouf-r4a-udp-admission-fix.XXXXXX)
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
ouf_stage_args=(
  --container "$ouf_udp_container" --candidate-container "$ouf_candidate_container"
  --build-receipt "$ouf_build_receipt" --work-parent "$ouf_work_parent" --allow-enabled-live
)
sudo python3 -B "$ouf_fix_dir/r4a_stage_udp_recovery.py" "${ouf_stage_args[@]}" --check-only
sudo python3 -B "$ouf_fix_dir/r4a_stage_udp_recovery.py" "${ouf_stage_args[@]}" \
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
```


### R4A — release fix ammissione scoped confermata dall’operatore (2026-10-01 17:37 Europe/Rome)

Output operatore: build revisione UDP `83249a897eb4add4289b5181b3299f48ea4c0f99` PASS, candidate/live finale `sha256:5e048a859716d6674355e72238f03f899abd705a943ceadbdc5c8863d28f4e9f`, tag `ouf-udp-recovery-candidate:r4a-83249a897eb4-3fdecb4873a0`. Receipt build privata `/opt/ouf/udp-recovery-candidates/udp-recovery-image-ijxpujl8/receipt.json`. Migrazioni identiche e live precedente024c invariato durante build. Probe compilato/shipped Java resolve PASS GET_ONLY/candidate, senza Spring: non prova mapper runtime o causalità storica.

Preflight PASS READ_ONLY/live recovery-enabled/candidate assente; stage PASS candidate fermo/no restart, mounts uguali, ambiente conservato salvo flag recovery, live invariato. Receipt stage privata `/opt/ouf/udp-recovery-candidates/udp-recovery-stage-5gvo9w_0/receipt.json`. Release PASS dopo stop live e backup PASS con restore-list; receipt privata `/opt/ouf/udp-recovery-candidates/udp-recovery-stage-5gvo9w_0/release-receipt.json`. Live finale5e048a/Flyway34, ORIGINAL_JOBS_UNCHANGED, Gateway backend health, anon/spoof negati. Rollback `ouf-udp-rollback-d2450009a153` fermo/restart-disabled; conservare backup e rollback precedenti. Non ripetere build/release né rimuovere ricevute. Queste sono evidenze operatore, non ispezione SSH diretta dell’agente.

HUMAN_AUTHORIZATION_NOT_PROVEN=true, RETRY=false. Ultimo business stato noto resta 8handoff ACKED, 5PROCESSED/SUCCEEDED e 3DURABLE/QUARANTINED; release dichiara originali invariati, non materializzazione8/8 o search. La fix sorgente è ora rilasciata, ma causalità del precedenteHTTP403 e prova owner positiva richiedono GET reale. PET Authorization§36.10 e UDP§109.7 consultati: health/negativi non sostituiscono AUTHZ-READY e reference gate al punto d’uso. Policy ultima pubblicata:36, grant3 nominali/scoped, expiry2026-10-02T10:00Z; nessuna nuova pubblicazione, route o IAM change richiesta.

Prossimo intervento operatore: nuova sessione HUMAN ouf-admin/clientouf-human-admin con scope OPTIONAL udp.materialization.retry; GET anonimo, fuori scope e tre job originali tramite Gateway->UDP, utilizzando helper giàCI102PASS d6c32cbf e logger Python unbuffered verificato interattivamente. Nuove receipt/protocollo root-private, phase/HTTP/error persistiti. Se GET3PASS e contractReady/retryEligible confermati, preparare soltanto allora retry originale con expectedVersion/snapshotHash/operationId e conferma HUMAN. Se403 persiste diagnosticare Gateway/owner/subject/policycache, senza grant generici o nuovi tentativi di business. Block reference gate con ownerpositive resta esito incompleto e vieta retry. Restano tutti i gate ereditati, storage/search indipendenti e industrializzazione R-INSTALL.


#### R4A UDP recovery — review HUMAN dopo release 83249a8

La release5e048a è confermata. Questo blocco usa lo stesso helper GET-only già verificato e il logger Python immediato; nuova receipt/protocollo esclusivi, nessun retry/replay/intake/policy publish. Effettuare la conferma THS con account OUF `ouf-admin`; non incollare in chat devicecode/token o file privati. Il bootstrap deve avviare bash separato e gestire exit nel chiamante per mantenere la shell SSH aperta. Scope richiesto udp.materialization.retry; grant esatti scadono2026-10-02T10:00Z.

Dopo login: anonimo401/403, fuori scope403, poi tre GET owner200; verificare binding originali QUARANTINED/DURABLE/v2, readiness contratti e retryEligible. PASS_READY prova review corrente, non8materializzazioni; AUTHORIZATION_PASS_REFERENCE_GATE_BLOCKED distingue ownerpositive dalla readiness mancante e impedisce retry. In casoHTTP403 riporterà phase/safeFailureCode senza payload; conservare ricevute. Runtime policy globale/in-memory non è provata dal confronto con receipt publication36; non usare simulazione come prova owner.

```bash
set -euo pipefail
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
REVISION=d6c32cbf062618f0b255c51f8a7a8d6fb521e839
WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT
for SCRIPT in r4a_read_human_materialization_review.py r4a_prepare_scoped_human_policy.py; do
  git show "$REVISION:scripts/$SCRIPT" > "$WORK_DIR/$SCRIPT"
done
sudo bash -s -- "$WORK_DIR" <<'ROOT'
set -euo pipefail
umask 077
WORK_DIR=$1
STATE_DIR=/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy
LOG=$(mktemp "$STATE_DIR/human-review-protocol.XXXXXX")
printf 'HUMAN_REVIEW_PROTOCOL_LOG=%s PRIVATE=true\n' "$LOG"
RECEIPT="$STATE_DIR/human-review-$(date -u +%Y%m%dT%H%M%S)-$$.json"
set +e
python3 -u -B "$WORK_DIR/r4a_read_human_materialization_review.py" \
  --issuer https://auth.ouf-lab.it/realms/ouf --client ouf-human-admin \
  --audience ouf-api-gateway --tenant ouf-lab \
  --subject b93d8cf6-cd14-4ee6-91d7-84cd76c4f500 \
  --scope udp.materialization.retry --expected-policy ouf-lab-authorization:36 \
  --base-url https://api.ouf-lab.it/api/udp/v1/governance/materialization/jobs \
  --publication-receipt "$STATE_DIR/publication-receipt.json" \
  --resources "$STATE_DIR/resources.json" --receipt "$RECEIPT" \
  --expected-version 2 --expected-resources 3 \
  --expected-failure UDP_REFERENCE_INTEGRITY_CONTRACT_INVALID \
  --binding 7793566d-b9d4-4402-8cda-c09b8f135c04:8869a6d6-3d82-4514-a63a-d23f9b26d48f \
  --binding e7572836-f8af-4c58-b5fc-12d7aff5db1d:aed8ef93-6d00-4cf0-868d-d2d82d79b524 \
  --binding e5b6ca24-6143-4ae5-8907-5dce398abfa3:e58faf8c-c35a-4106-b4b6-67e58dec9774 \
  --outside-job f84de729-c245-4e34-80cf-764c4eb0f160 2>&1 |
  python3 -u -c '
import sys
with open(sys.argv[1], "a", buffering=1) as log:
    for line in sys.stdin:
        sys.stdout.write(line); sys.stdout.flush()
        if line.startswith(("UDP_HUMAN_REVIEW_", "R4A_UDP_HUMAN_REVIEW")):
            log.write(line); log.flush()
' "$LOG"
RESULT=("${PIPESTATUS[@]}")
set -e
printf 'HUMAN_REVIEW_PROTOCOL_LOG=%s PRIVATE=true\n' "$LOG"
printf 'HUMAN_REVIEW_PROCESS_EXIT=%s OUTPUT_CAPTURE_EXIT=%s RETRY=false\n' "${RESULT[0]}" "${RESULT[1]}"
test "${RESULT[1]}" -eq 0
exit "${RESULT[0]}"
ROOT
```


### R4A — prova owner HUMAN e reference gate Spring completa (2026-10-01 17:55 Europe/Rome)

Operatore: tre review HTTP200 PASS, JOB_BINDING_MATCH=true, QUARANTINED/DURABLE/version2, retryEligible=true, contractReady=true, contractCheck=READY per tutti e tre job originali. R4A_UDP_HUMAN_REVIEW=PASS, HUMAN_OWNER_AUTHORIZATION_PROVEN=true, ANONYMOUS_DENIED=true, OUTSIDE_JOB_DENIED=true, SPRING_REVIEW_REFERENCE_GATE=PASS. Receipt privata `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/human-review-20261001T155349-3513740.json`; protocollo privato `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/human-review-protocol.MIvo9G`; process/capture exit0. Solo owner GET: RETRY=false, REPLAY=false, INTAKE_POST=false, materializzazione non triggerata. Causalità storica resta NOT_PROVEN; la sequenza prima403/poi200 dopofix non è ricostruzione dell'errore storico di reference integrity. Live83249a/5e048a/Flyway34, originali preservati.

Gate owner positivo e risoluzione attuale nel mapper Spring superati per i tre job sotto questa sessione; non dichiarare materializzazione8/8/search/storage indipendente. Policy36 nominale HUMAN, soli3job/type/source/run/RAWlabel esatti, expiry2026-10-02T10:00Z. Non ripubblicare policy o modificare IAM/routes. PET Authorization36.10/UDP109.6–109.7 consultati: retry originale governato, version/snapshot e reference gate al punto d'uso, nessun replay/repair DB/silent fallback.

Preparato helper parametrizzato scripts/r4a_retry_human_materialization.py: richiede receipt review precedente PASS_READY e hash/set esatti, risorse/private publication, binding originali e motivo bounded; nuova sessione HUMAN e nuove GET owner per i tre job. Il helper GET riutilizzabile restituisce token soltanto in-process, mai lo salva. Dopo tutte le review READY persiste tre operationId e richieste esatte, mostra job/handoff/source/run e transizioneQUARANTINEDv2->READYv3, richiede frase sul /dev/tty read-only. Conferma non pubblica policy. Prima di ogni POST verifica TTL>60sec e fsync dell'intento/operationId/body nella receipt esclusiva0600. Solo un POST per originale, nessun loop/repost. HTTP200 verificato con operation/job/handoff/version3/READY/repeatedfalse, append progressivo; successo è PASS_AUTHORIZED_REQUEUE, non prova materializzazione. Qualsiasi failure ferma il batch; timeout/response invalida conserva POST_INTENT_OUTCOME_UNKNOWN e precedenti successi, vieta repost fino a riconciliazione. Nessun messaggio eccezione arbitrario, payload/token/hash sul terminale.

Otto test nuovi coprono tre review fresche prima della conferma/POST, drift input/prior/source, reference/version gate, conferma/TTL, intent durevole, partial timeout/409/schema error e nessun overwrite/repost, token non persistito, terminale reale corretto/negato. 17 test retry+review locali PASS, 47 policy/Gateway/helper locali PASS. CI helper/package da completare prima del blocco operativo. Nessun retry remoto ancora effettuato; prossimo intervento umano sarà login THS e conferma batch mostrato, poi readback8handoff/job originali ed effetti canonici/search. Tutti i gate ereditati/industrializzazione R-INSTALL restano aperti.


### R4A — retry HUMAN originale verificato e pronto alla conferma operatore (2026-10-01)

Helper operativo pin `fe8b957907106925acbca95fe8e63595c88f806c`: recovery scripts CI PR36889604556 job110461624123 SUCCESS, 110/110 test PASS. PR module completo Java21/PostgreSQL17/checksum e production container SUCCESS; Authorization pairwise36889604582, Shared SDK36889604497 e Gateway live pairwise36889604635 SUCCESS. Push Authorization36889598494 e SDK36889598423 SUCCESS; pushmodule36889598409 SUCCESS, inclusi checksum/Java,110testhelper e production container. Prompt conferma emesso con newline/flush per il logger a righe: test locale reale producer->logger->PTY PASS, prompt visibile prima di input, codice login escluso dal protocollo. bash-n e published-code readback PASS. Nessun deploy aggiuntivo richiesto: UDP live resta83249a/5e048a/Flyway34. Non confondere CI helper con autorizzazione remota POST; quest'ultima non ancora esercitata.

Blocco operativo nel runbook “retry HUMAN dei tre job originali dopo review PASS”: nuova receipt human-retry-* root0600 e fresh-review separata; sessione HUMAN dedicata, tre nuove GET READY e negativi, piano con tutti job/handoff/run/source, frase esatta da digitare su tty, poi tre POST originali uno per volta. Scope/grant già governati:36, nessuna ripubblicazione, replay/intake/reactivation. Snapshot fresh e version2 da owner, operationId stabili persistiti prima dell'intento; version3/READY è ammissione, non materializzazione. Logger filtra sole righe simboliche, non devicecode/token/hash/payload. Con exitnonzero o connessione persa dopo intent, fermarsi e riconciliare receipt: non rieseguire il batch, non inventare nuova operation né sommare automaticamente una risposta persa ai successi. Conserva pass già registrati e unknown separati, mai claimfalseRETRY=false dopo POST.

Ultima prova remota certa: receipt human-review-20261001T155349-3513740.json PASS_READY,3reviewHTTP200/QUARANTINED/DURABLE/v2/eligible/READY e anon/outside denied. Nessun retry al momento di questo checkpoint. Dopo receipt3POST200 PASS_AUTHORIZED_REQUEUE, nextgate è readback sugli otto originali Ingestion/UDP, stati ed eventi di retry/resolution, effetti canonici e search; non fare nuove ingestion/replay. Restano storage/hash indipendente, causalità storica NOT_PROVEN e tutti gate R-INSTALL/industrializzazione ereditati. Grant expiry2026-10-02T10:00Z, owner enforcement deve continuare fail-closed.


#### R4A UDP recovery — retry HUMAN dei tre job originali dopo review PASS

Questo blocco esegue una nuova login HUMAN ouf-admin e sole GET di review/negativi prima della conferma. Se tutti i gate sono PASS, mostra sorgente/run/job/handoff e transizione prevista, poi attende la frase su terminale. Solo dopo conferma invia un POST/retry per ciascun job originale, preservando input e versioni con i guard owner. Nessun replay/intake/source reactivation/policy publish. Binding installativi espliciti qui, helper parametrizzati senza default lab. Il bootstrap deve essere processo bash separato con ORhandler per mantenere la shell SSH aperta; logger Python unbuffered mostra anche prompt completo, salva solo righe simboliche su protocollo privato.

Conferma richiesta (dopo nuove review e piano): `CONFERMO RETRY ORIGINALE 86809c17-3354-45ca-a7e6-57e903944b24`. Prima di digitare controllare i tre job mostrati, source managed-cinema-8ec8ae90, run originale e VERSION2->3. Grant scadono2026-10-02T10:00Z; il helper verifica TTLtoken>60sec dopo conferma e prima di ogni POST. Se si attende troppo e il token non è più sufficiente, si ferma senza quel POST. Non incollare devicecode/token, snapshot o receipt private in chat. Dopo3PASS il worker prosegue in modo asincrono; la risposta non prova ancora materializzazione8/8.

Se il batch si interrompe o output/connessione vengono persi, non ripetere il blocco: conservare il percorso R4A_UDP_HUMAN_RETRY_RECEIPT e protocollo, riconciliare receipt con stati/eventi originali in sola lettura. L'intento è durabile prima del POST e una risposta persa è OUTCOME_UNKNOWN, non negazione o successo dimostrato. Nessun recovery automatico/repost incluso in questo script. Richieste UUID/hash/reason nella receipt privata consentono riconciliazione precisa. La receipt originale di review e tutte le precedenti restano conservate.

```bash
set -euo pipefail
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
REVISION=fe8b957907106925acbca95fe8e63595c88f806c
WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT
for SCRIPT in r4a_retry_human_materialization.py r4a_read_human_materialization_review.py r4a_prepare_scoped_human_policy.py; do
  git show "$REVISION:scripts/$SCRIPT" > "$WORK_DIR/$SCRIPT"
done
sudo bash -s -- "$WORK_DIR" <<'ROOT'
set -euo pipefail
umask 077
WORK_DIR=$1
STATE_DIR=/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy
LOG=$(mktemp "$STATE_DIR/human-retry-protocol.XXXXXX")
printf 'HUMAN_RETRY_PROTOCOL_LOG=%s PRIVATE=true\n' "$LOG"
RECEIPT="$STATE_DIR/human-retry-$(date -u +%Y%m%dT%H%M%S)-$$.json"
set +e
python3 -u -B "$WORK_DIR/r4a_retry_human_materialization.py" \
  --issuer https://auth.ouf-lab.it/realms/ouf --client ouf-human-admin \
  --audience ouf-api-gateway --tenant ouf-lab \
  --subject b93d8cf6-cd14-4ee6-91d7-84cd76c4f500 \
  --scope udp.materialization.retry --expected-policy ouf-lab-authorization:36 \
  --base-url https://api.ouf-lab.it/api/udp/v1/governance/materialization/jobs \
  --publication-receipt "$STATE_DIR/publication-receipt.json" \
  --resources "$STATE_DIR/resources.json" --receipt "$RECEIPT" \
  --prior-review-receipt "$STATE_DIR/human-review-20261001T155349-3513740.json" \
  --run 86809c17-3354-45ca-a7e6-57e903944b24 --source managed-cinema-8ec8ae90 \
  --reason "Ripresa governata dei job originali dopo review HUMAN e reference gate READY" \
  --expected-version 2 --expected-resources 3 \
  --expected-failure UDP_REFERENCE_INTEGRITY_CONTRACT_INVALID \
  --binding 7793566d-b9d4-4402-8cda-c09b8f135c04:8869a6d6-3d82-4514-a63a-d23f9b26d48f \
  --binding e7572836-f8af-4c58-b5fc-12d7aff5db1d:aed8ef93-6d00-4cf0-868d-d2d82d79b524 \
  --binding e5b6ca24-6143-4ae5-8907-5dce398abfa3:e58faf8c-c35a-4106-b4b6-67e58dec9774 \
  --outside-job f84de729-c245-4e34-80cf-764c4eb0f160 2>&1 |
  python3 -u -c '
import sys
with open(sys.argv[1], "a", buffering=1) as log:
    for line in sys.stdin:
        sys.stdout.write(line); sys.stdout.flush()
        if line.startswith(("UDP_HUMAN_REVIEW_", "UDP_HUMAN_RETRY_", "R4A_UDP_")):
            log.write(line); log.flush()
' "$LOG"
RESULT=("${PIPESTATUS[@]}")
set -e
printf 'HUMAN_RETRY_PROTOCOL_LOG=%s PRIVATE=true\n' "$LOG"
printf 'HUMAN_RETRY_PROCESS_EXIT=%s OUTPUT_CAPTURE_EXIT=%s\n' "${RESULT[0]}" "${RESULT[1]}"
test "${RESULT[1]}" -eq 0
exit "${RESULT[0]}"
ROOT
```


### R4A — retry HUMAN dei tre job originali accettato (2026-10-01 18:14 Europe/Rome)

Operatore ha effettuato nuova sessione HUMAN, tre GET owner200 con job binding esatto, QUARANTINED/DURABLE/v2, retryEligible=true e contractReady=true/READY; anonimo e job fuori scope negati. Fresh review privata `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/human-retry-20261001T161313-3517748-fresh-review.json`. Piano source managed-cinema-8ec8ae90/run86809c17-3354-45ca-a7e6-57e903944b24, tre originali e transizionev2->v3 mostrati. Operatore ha digitato frase esatta CONFERMO RETRY ORIGINALE con runID, quindi tutti e tre POST/retry HTTP200 PASS/ORIGINAL_JOB_MATCH/acceptedVersion3/READY/repeatedfalse.

Ordine confermato: job7793566d-b9d4-4402-8cda-c09b8f135c04/handoff8869a6d6-3d82-4514-a63a-d23f9b26d48f; jobe5b6ca24-6143-4ae5-8907-5dce398abfa3/handoffe58faf8c-c35a-4106-b4b6-67e58dec9774; jobe7572836-f8af-4c58-b5fc-12d7aff5db1d/handoffaed8ef93-6d00-4cf0-868d-d2d82d79b524. R4A_UDP_HUMAN_RETRY=PASS/ACCEPTED_COUNT3/HUMAN_OWNER_AUTHORIZATION_PROVEN/ORIGINAL_JOBS_REQUEUED. REPLAY=false, INTAKE_POST=false, MATERIALIZATION_NOT_YET_VERIFIED=true. Protocollo privato `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/human-retry-protocol.edA735`; process e capture exit0. Receipt retry principale derivabile senza ambiguità dal nome fresh-review del helper: `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/human-retry-20261001T161313-3517748.json`; contiene operationId/body/snapshot e risposta per ciascun POST, non stampare. Il prossimo reader ne verifica presenza/privacy/schema/set prima dei readback live.

Non ripetere i retry: ammissione originale completata, il worker procede asincrono. Non riattivare sorgente/schedule trigger_once, non replay/reintake/repair DB. Version3/READY è accettazione, non SUCCEEDED o effetto canonico. Ultimo stato Ingestion noto resta SUCCEEDED/control2/8ACKED, lineages8, attempts10 con due failstorici risolti; cinque materializzazioni UDP precedenti più tre ora in coda, totale effettivo corrente da leggere. Live83249a/5e048a/Flyway34, policy36 nominale3scope, nessun cambio deploy/IAM/Gateway/policy. Causalità storica reference failures NOT_PROVEN.

PET UDP109.6–109.7 e Authorization36.10 consultati: re-run da evidence/version/snapshot e durable originals, owner fine-grained, reference gate senza fallback. Preparato blocco READ_ONLY: valida ricevuta retry originale0600/root e parent0700, set3job/handoff, distinct operationId, requestversion2 e receiptversion3/READY/repeatedfalse, stampa solo saved evidence. Poi riusa fixture cinema già versionata: activation receipt e pubblicazione ACTIVE/frozenchecksum exact; Ingestion e UDP scope publication/run, handoffIDset, intakes/jobs/decisions/issues/observations/revisions/bindings/activeobjects; più diagnostica UDP parametrizzata per source/run e tutti jobID/state/version/counters/flags ed eventi simbolici (incl MATERIALIZATION_RETRY_AUTHORIZED, REFERENCE_INTEGRITY_PASSED e RESOLUTION_COMPLETED se presenti). Nessun safe_detail/token/payload/ref/hash stampato. Cinque casi locali readerPASS (buono/unknown/wrongjob/version/privacy), bash-nPASS; helper runtime riusati senza modifiche. Protocollo readback rootprivate persistente, exit dei due reader separati; COMPLETE/exit0 non converte NOT_PROVEN in PASS.

Nota deploy: cinema_execution_readback è una fixture storica legata al deployment cinema corrente, non uno strumento di deploy generico; non introdotte nuove costanti lab nel codice applicativo/helper condiviso. La diagnostica UDP è parametrizzata CLI. Questa fase non chiude portabilità multi-host/domain/network/tenant né automatismi R-INSTALL. Se8materializationPASS, seguiranno search e byte/hash Lake indipendenti; letture cross-DB non atomiche, singolo snapshot non è consenso distribuito. Se pending/failure, analizzare originale senza nuovo retry cieco. Tutti altri gate ereditati restano aperti.


#### R4A UDP recovery — readback dopo tre retry HUMAN accettati

I tre POST originali sono PASS HTTP200/version3/READY. Questo blocco non effettua login, retry, intake, replay, resume, source activation o deploy; legge receipt salvata e DB/log simbolici con transazioni READ_ONLY e timeout. Il path retry è quello corrispondente alla fresh review161313 ricevuta, verificato prima delle query. Il readback cinema è la fixture storica per questa sorgente/installazione, valida publication/frozen activation ricevuta e distingue delivery8ACKED da materializzazione8PROCESSED/SUCCEEDED/observation/binding/noopenissues; non forzare otto urbanobjects se la resolution governata li unifica. Non è una prova portabile R-INSTALL. La seconda diagnostica richiede binding CLI espliciti run/source/container/database/user e mostra i job originali/eventi, senza payload/safe_detail/hash/ref.

Il protocollo root0600 persiste soltanto questo output simbolico; nessun devicecode o token perché non c'è login. I dati vengono letti in istanti diversi, non atomicamente tra DB. `UDP_MATERIALIZATION_EIGHT_ROWS=NOT_PROVEN` con processo exit0 è comunque un gate incompleto. Conservare ricevute/retry audit e rollback. Se output perso si può ripetere questa sola lettura; non rieseguire il blocco POST. Search e verifica S3byte/hash non inclusi.

```bash
set -euo pipefail
umask 077
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
ouf_helpers=b9108fa360a11bb5be745e187e278ecbc7814229
ouf_readback_dir=$(mktemp -d /tmp/ouf-r4a-after-retry.XXXXXX)
trap 'rm -rf -- "$ouf_readback_dir"' EXIT
for script in r4a_cinema_execution_readback.py r4a_execution_failure_bundle.py r4a_execution_route_inventory.py r4a_prepare_frozen_compatibility_probe.py r4a_udp_materialization_diagnostic.py; do
  git show "$ouf_helpers:scripts/$script" > "$ouf_readback_dir/$script"
done
sudo bash -s -- "$ouf_readback_dir" <<'ROOT'
set -euo pipefail
umask 077
ouf_readback_dir=$1
ouf_state_dir=/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy
ouf_retry_receipt="$ouf_state_dir/human-retry-20261001T161313-3517748.json"
ouf_run=86809c17-3354-45ca-a7e6-57e903944b24
ouf_source=managed-cinema-8ec8ae90
ouf_bindings=(
  7793566d-b9d4-4402-8cda-c09b8f135c04:8869a6d6-3d82-4514-a63a-d23f9b26d48f
  e5b6ca24-6143-4ae5-8907-5dce398abfa3:e58faf8c-c35a-4106-b4b6-67e58dec9774
  e7572836-f8af-4c58-b5fc-12d7aff5db1d:aed8ef93-6d00-4cf0-868d-d2d82d79b524
)
LOG=$(mktemp "$ouf_state_dir/readback-after-retry.XXXXXX")
printf 'R4A_POST_RETRY_READBACK_LOG=%s PRIVATE=true\n' "$LOG"
python3 -B - "$ouf_retry_receipt" "$ouf_run" "$ouf_source" "${ouf_bindings[@]}" <<'PY' | tee "$LOG"
import json, os, re, stat, sys, uuid
from pathlib import Path
def require(value):
    if not value:raise RuntimeError('RECEIPT_MISMATCH')
try:
    path=Path(sys.argv[1]);meta=path.lstat();parent=path.parent.lstat()
    require(os.geteuid()==0 and stat.S_ISREG(meta.st_mode) and meta.st_uid==0 and stat.S_IMODE(meta.st_mode)==0o600)
    require(stat.S_ISDIR(parent.st_mode) and parent.st_uid==0 and stat.S_IMODE(parent.st_mode)==0o700)
    require(meta.st_size<=8000000)
    value=json.loads(path.read_text());expected=dict(pair.split(':',1) for pair in sys.argv[4:])
    require(all(str(uuid.UUID(j))==j and str(uuid.UUID(h))==h for j,h in expected.items()))
    require(value['status']=='PASS_AUTHORIZED_REQUEUE' and value['runId']==sys.argv[2] and value['sourceId']==sys.argv[3])
    require(value['humanConfirmed'] is True and len(value['rows'])==len(expected)==3)
    require({row['jobId'] for row in value['rows']}==set(expected))
    operations=set()
    for row in value['rows']:
        request=row['request'];receipt=row['receipt'];job=row['jobId'];handoff=expected[job]
        require(row['status']=='PASS_ACCEPTED' and row['handoffId']==handoff)
        require(request['expectedVersion']==2 and re.fullmatch('sha256:[a-f0-9]{64}',request['expectedSnapshotHash']))
        operation=request['operationId'];require(str(uuid.UUID(operation))==operation and operation not in operations)
        operations.add(operation)
        require(receipt['operationId']==operation and receipt['jobId']==job and receipt['handoffId']==handoff)
        require(receipt['acceptedVersion']==3 and receipt['state']=='READY' and receipt['repeated'] is False)
    print('R4A_HUMAN_RETRY_SAVED_RECEIPT=PASS ACCEPTED_COUNT=3 EXACT_ORIGINAL_JOB_SET=true SAVED_EVIDENCE_ONLY=true LIVE_MATERIALIZATION_NOT_YET_QUERIED=true SECRETS_NOT_PRINTED=true')
except Exception as error:
    print('R4A_HUMAN_RETRY_SAVED_RECEIPT=BLOCKED TYPE='+type(error).__name__+' READ_ONLY=true SECRETS_NOT_PRINTED=true')
    raise SystemExit(1)
PY
set +e
python3 -u -B "$ouf_readback_dir/r4a_cinema_execution_readback.py" 2>&1 | tee -a "$LOG"
ouf_cinema_result=("${PIPESTATUS[@]}")
python3 -u -B "$ouf_readback_dir/r4a_udp_materialization_diagnostic.py" \
  --run "$ouf_run" --source "$ouf_source" \
  --postgres-container ouf-postgres --database ouf_udp --db-user ouf_udp 2>&1 | tee -a "$LOG"
ouf_udp_result=("${PIPESTATUS[@]}")
set -e
printf 'R4A_POST_RETRY_READBACK_LOG=%s PRIVATE=true\n' "$LOG"
printf 'R4A_POST_RETRY_READBACK_EXIT=%s UDP_DIAGNOSTIC_EXIT=%s READ_ONLY=true RETRY=false REPLAY=false\n' "${ouf_cinema_result[0]}" "${ouf_udp_result[0]}"
test "${ouf_cinema_result[0]}" -eq 0
test "${ouf_cinema_result[1]}" -eq 0
test "${ouf_udp_result[0]}" -eq 0
test "${ouf_udp_result[1]}" -eq 0
ROOT
```


### R4A — readback completo: 7/8 materializzati, un originale nuovamente quarantinato (2026-10-01 18:28 Europe/Rome)

Operatore ha prima segnalato NOT_PROVEN, poi allegato output completo Testo incollato.txt, letto nel workspace. Il recupero del log salvato preparato nel frattempo è ora superfluo e non va richiesto. Protocollo reale privato `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/readback-after-retry.FUnWAL`. Receipt retry salvata PASS/3accepted/exactoriginaljobset; sourceACTIVE/frozenhash/publicationmatch. Ingestion run86809c17 SUCCEEDED/control2,10attempts/8lineages/0quarantines,8ACKED e UDP handoffIDset match; delivery8 PASS. Trigger_once consumed/DISABLED. Due failstorici404/403 restanoRESOLVEDv2. Output di entrambi reader exit0, non equivalenti a materializationPASS.

UDP:7PROCESSED/SUCCEEDED/NEW_OBJECT,7observations/revisions/bindings/activeobjects;1DURABLE/QUARANTINED,0open resolution issues. Materialization8 NOT_PROVEN e searchnonverificata. Dei tre retry, job7793566d/handoff8869a6d6 e jobe5b6ca24/handoffe58faf8c sonoSUCCEEDEDv5, attempts2/integrityAttempts1/baselinepresente, eventi originali+1MATERIALIZATION_RETRY_AUTHORIZED+REFERENCE_INTEGRITY_PASSED+RESOLUTION_COMPLETED. Ultimo job `e7572836-f8af-4c58-b5fc-12d7aff5db1d` / handoff `aed8ef93-6d00-4cf0-868d-d2d82d79b524` è tornatoQUARANTINEDv5/attempts2/integrityAttempts2,baselineassente,missingRefCount0,nextcheckassente,safeFailureCodeUDP_REFERENCE_INTEGRITY_CONTRACT_INVALID. Eventi:1retryAUTHORIZED e2REFERENCE_INTEGRITY_QUARANTINED (storico+nuovo), nessunREFERENCE_PASSED/RESOLUTION_COMPLETED per questo handoff. Questo è fallimento tecnico nel worker, non semplice job pendente; non ripetere alcun retry dei tre.

Tutte3review fresche avevanoREADY e POSTacceptedv3; il terzo tentativo asincrono contraddice readiness osservata prima in una diversa chiamata/istante. Causa specifica non dimostrata: non attribuire a token/Gateway/policy/mapper/payload senza nuova evidence. ACTIVEpolicy36 HTTP200 nel bundle generale; logruntimeUDP/Apisixsenza marker simbolici, accesslogTimeoutExpired. ING_ACTIVATION_DISCOVERY_UNAVAILABLE12da finestraprepubblicazione è diagnostica storica e non spiega da sola il nuovoUDPfailure. UDP_FAILURE_CODES=[] è proiezione intake, non assenza di safeFailureCode nel job. Zero resolutionissues non elimina questa quarantena tecnica. Owner authorization HUMAN è giàprovata dai3GET/POST; flagOWNER_AUTHORIZATION_NOT_PROVEN del bundlegenerale non revoca quella prova scoped.

Lettura sorgenti live83249a: MaterializationReferenceGate quarantina IllegalArgumentException con UDP_REFERENCE_INTEGRITY_CONTRACT_INVALID, e passa ReferenceFailureEvidence.detail alla append-only event. Nuova strumentazione deve contenere diagnosticCode allowlisted/category e max4 Javaapplicationframes, senza exceptionmessage/payload. ResolutionRepository inserisce questi campi direttamente nel safe_detail della nuovaREFERENCE_INTEGRITY_QUARANTINED; V1handoff_event.created_at è verificato da schema. Prossimo gate READ_ONLY mirato al solo originale rimasto: proietta esclusivamente jobstate/version/counters/safecode e recenti eventi quarantena con diagnosticCode/category/frames, ordinati percreated_at. Nessuna lettura/stampa integrale safe_detail o ref/hash/token/payload. Storico privo di campi ->NOT_RECORDED, simboli sconosciuti redatti; framesvalidati. Binding container/database/user/job/handoff/source/run solo CLI/runbook. SQL READ_ONLY/timeout15s/lock2s, processo25s, protocollo root0600. Proiezione sanitizer locale PASS (simboli/frame/valori arbitrari redatti/legacyabsent), bash-nPASS. È documentazione diagnostica, nessun cambio applicativo/deploy/policy/IAM/route/DB.

PET UDP109.6–109.7/Authorization36.10 consultati: conservare originali e audit, fermarsi sul nuovo failure, verificare referencegate senza fallback. Dopo code/frames usare prova per diagnosi/fix reviewable; niente retrycieco/replay/reactivation. Ultimo live83249a/5e048a/Flyway34, due originali recuperati con effetti canonici, uno ancora bloccato. Tutti gate ereditati, storage/search indipendente, causalità storica e industrializzazione R-INSTALL restano aperti.


#### R4A UDP recovery — evidenza sicura del solo job rimasto in quarantena

ReadbackFUnWAL dimostra7/8, con jobe7572836 tornatoQUARANTINEDv5/CONTRACT_INVALID. Questo blocco legge soltanto eventi e stato di quell'originale; nessun login/GETHTTP/retry/replay/intake/deploy o modifica DB. La strumentazione già rilasciata dovrebbe aver salvato codice simbolico/category/max4frames nella nuova event; quella storica può mancare di diagnostica e verrà NOT_RECORDED. Le query proiettano soltanto queste tre chiavi del safe_detail, mai il JSON intero, e il sanitizer redige valori fuoriallowlist. Non stampare loggrezzi o eccezioni integrali. Config installativa/source/run/job/handoff è passata esplicitamente alla Pythoninline nel runbook.

Protocollo privato persistente remaining-reference-failure.*, transazione READ_ONLY con timeout, output simbolico utile per distinguere il punto di errore. Nessun retry autorizzato da questo blocco; una nuova reviewREADY da sola non spiegherebbe la discrepanza con il worker. Conservare entrambeeventi quarantena e le tre receipt di retry. Shell bootstrap esterna con ORhandler, outputincollare solo simbolico.

```bash
set -euo pipefail
sudo bash <<'ROOT'
set -euo pipefail
umask 077
LOG=$(mktemp /etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/remaining-reference-failure.XXXXXX)
printf 'R4A_REMAINING_REFERENCE_FAILURE_LOG=%s PRIVATE=true\n' "$LOG"
# Binding espliciti dell'installazione e dell'originale rimasto in quarantena.
python3 -u -B - ouf-postgres ouf_udp ouf_udp \
  e7572836-f8af-4c58-b5fc-12d7aff5db1d aed8ef93-6d00-4cf0-868d-d2d82d79b524 \
  managed-cinema-8ec8ae90 86809c17-3354-45ca-a7e6-57e903944b24 <<'PY' | tee "$LOG"
import json, re, subprocess, sys, uuid
from datetime import datetime
def require(value):
    if not value:raise RuntimeError('DIAGNOSTIC_SHAPE_OR_BINDING_INVALID')
def clean(document):
    job=document.get('job');require(isinstance(job,dict))
    result={'job':{},'events':[]}
    for key in ('state_version','attempts','integrity_attempts'):
        require(type(job.get(key)) is int and job[key]>=0);result['job'][key]=job[key]
    for key in ('job_state','safe_failure_code'):
        value=job.get(key);require(value is None or isinstance(value,str) and re.fullmatch('[A-Z0-9_]{1,120}',value))
        result['job'][key]=value
    allowed={'UDP_PINNED_PROFILE_INVALID','UDP_GOVERNED_IDENTITY_PROFILE_INVALID','UDP_RESOLUTION_PROFILE_UNSUPPORTED',
        'UDP_GATEWAY_INVALID','UDP_CONTRACT_REFS_REQUIRED','UDP_CONTRACT_REF_REQUIRED','UDP_CONTRACT_REF_INVALID',
        'UDP_HISTORICAL_CATALOG_INVALID','UDP_HISTORICAL_CATALOG_DUPLICATE','UDP_HISTORICAL_BASELINE_INVALID',
        'UDP_PUBLICATION_UNAVAILABLE','UDP_PUBLICATION_INTERRUPTED','UNCLASSIFIED'}
    events=document.get('events');require(isinstance(events,list) and len(events)<=8)
    for event in events:
        at=event['created_at'];require(isinstance(at,str));datetime.fromisoformat(at.replace('Z','+00:00'))
        code=event.get('diagnostic_code');category=event.get('diagnostic_category');frames=event.get('diagnostic_frames')
        if code is None:code='NOT_RECORDED'
        elif code not in allowed:code='NON_SYMBOLIC_REDACTED'
        if category is None:category='NOT_RECORDED'
        elif category not in ('IllegalArgumentException','IllegalStateException'):category='REDACTED'
        if frames is None:frames=[]
        require(isinstance(frames,list) and len(frames)<=4)
        safe_frames=[f for f in frames if isinstance(f,str) and re.fullmatch(
            r'it\.comune\.trieste\.ouf\.udp\.[A-Za-z0-9_.$]{1,240}#[A-Za-z0-9_$<>]{1,160}:-?[0-9]{1,10}',f)]
        result['events'].append({'created_at':at,'diagnostic_code':code,'diagnostic_category':category,
            'diagnostic_frames':safe_frames,'frames_redacted':len(safe_frames)!=len(frames)})
    return result
try:
    container,database,user,job,handoff,source,run=sys.argv[1:]
    for value in (container,database,user,source):require(re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,159}',value))
    job=str(uuid.UUID(job));handoff=str(uuid.UUID(handoff));run=str(uuid.UUID(run))
    sql=("begin read only; set local statement_timeout='15s'; set local lock_timeout='2s'; "
        "with target as (select j.handoff_id,j.state job_state,j.state_version,j.attempts,j.integrity_attempts,j.safe_failure_code "
        "from ouf_udp.materialization_job j join ouf_udp.handoff_intake h using(handoff_id) "
        "where j.job_id='"+job+"' and j.handoff_id='"+handoff+"' and h.source_id='"+source+"' and h.ingestion_run_id='"+run+"'), "
        "e as (select e.created_at,e.safe_detail->>'diagnosticCode' diagnostic_code,"
        "e.safe_detail->>'diagnosticCategory' diagnostic_category,e.safe_detail->'diagnosticFrames' diagnostic_frames "
        "from ouf_udp.handoff_event e join target t using(handoff_id) where e.event_type='REFERENCE_INTEGRITY_QUARANTINED' "
        "order by e.created_at desc,e.event_id desc limit 8) "
        "select json_build_object('job',(select row_to_json(t) from target t),"
        "'events',coalesce((select json_agg(e order by created_at desc) from e),'[]'::json)); rollback;")
    raw=subprocess.run(['docker','exec',container,'psql','-X','-qAt','-v','ON_ERROR_STOP=1',
        '-U',user,'-d',database,'-c',sql],check=True,capture_output=True,text=True,timeout=25).stdout.strip()
    value=clean(json.loads(raw))
    print('UDP_REMAINING_REFERENCE_FAILURE_EVIDENCE='+json.dumps(value,sort_keys=True))
    print('R4A_UDP_REFERENCE_FAILURE_EVIDENCE=COMPLETE READ_ONLY=true RETRY=false REPLAY=false PAYLOADS_NOT_PRINTED=true SECRETS_NOT_PRINTED=true')
except Exception as error:
    print('R4A_UDP_REFERENCE_FAILURE_EVIDENCE=BLOCKED TYPE='+type(error).__name__+' READ_ONLY=true RETRY=false SECRETS_NOT_PRINTED=true')
    raise SystemExit(1)
PY
printf 'R4A_REMAINING_REFERENCE_FAILURE_LOG=%s PRIVATE=true\n' "$LOG"
ROOT
```


### R4A — anche nuova quarantena senza diagnostica: verificare codice runtime (2026-10-01 18:35 Europe/Rome)

Operatore ha eseguito sola lettura mirata, protocollo privato `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/remaining-reference-failure.6rMnAL`. Job e7572836/handoff aed8ef93 restaQUARANTINEDv5/attempts2/integrityAttempts2/safeFailureCodeUDP_REFERENCE_INTEGRITY_CONTRACT_INVALID. Entrambi eventi hanno diagnosticCode/categoryNOT_RECORDED,frames[]: nuovo `2026-10-01T16:14:25.674269+00:00` (18:14locale dopo retry) e storico `2026-10-01T06:52:29.339869+00:00`. ReaderCOMPLETE,nessunretry/replay/payload/secrets. Non dire che nuovaevidencecontieneframes né inventare causa;7/8materializzati rimaneultimo readback.

Rilette sorgenti UDP pin83249a: MaterializationReferenceGate catchIllegalArgumentException chiama ReferenceFailureEvidence.detail, che restituisce sempre diagnosticCode (ancheUNCLASSIFIED),diagnosticCategory e diagnosticFrames (anchelista vuota). ResolutionRepository.quarantine(claim,code,Map) copiaMap e aggiunge safeFailureCode prima delwriteJSON/eventappend. ResolutionWorker esegue gate prima della propria try; il catch successivo usa jobs.fail, distinto dal referencequarantine. Dockerfile copia src e compila jar; nessun checkoutalternativo dichiarato. La mancanza dei tre campi nel nuovoevento è incompatibile con quel percorso sorgente se quello stesso bytecode ha scritto l'evento; non prova quale immagine/writer sia stato attivo. Non attribuire a vecchio container, serializzazione,token o trigger senza prova. JAR etichettato atteso e dichiarazione di release non sostituiscono osservazione del file effettivo/mount/writer.

Nextgate READ_ONLY runtime inventory: dockerinspectlive image/OCIrevision rispetto5e048a/83249a, inventario container con nome contenenteudp (running/restartpolicy/image/revision), dockerCP della sola /app/app.jar nei soli container running selezionati in directory0700/root; nessun dockercreate/start/restart/deploy. Zipfile legge classi BOOT-INF e verifica strutturalmente ReferenceFailureEvidence.class, marker/chiamataGate, signatureoverloadRepository conMap, campi diagnostici e recoveryAPIcandidates; controlla duplicateentry/limiti, mount che coprejar, identitàcontainer prima/dopo. Jarhash e copie rimangono privati, stdout solo strutture/identità giàpubbliche. Receipt/log root0600 e artifactdirectory persistenti; Configenv,mountsources,arguments/credentials mai stampati né salvati. JAR_COPY_ONLY e BUSINESS_STATE_UNCHANGED riferiti al probe, non assenza di attività autonoma del worker. Nomefilterudp non provaassenza di ogni altroprocesso/host; bytecodemarkers non provano da soli writer dell'evento precedente né gli oggetti giàcaricati inJVM, soprattutto conjarbindmount. Un changedidentity rende l'osservazione concorrente e richiede riconciliazione.

Test locale structuralprojection PASS per jar sintetico instrumentato e legacy, bash-nPASS. Nessun cambio condiviso/applicativo e nessun nuovo deploy/retry. PET UDP109.7 readiness/point-of-use consultato. Dopo inventario basare fix/diagnostica sui risultati; seJARcoerente e singolo writer visibile, indagare altro writer/trigger/serializzazione senza stampare safe_detailintegrale. Conservare originali e tutti3retryaudit. Status materializzazione7/8, search/storageindipendente/causalitàstorica/R-INSTALL e altri gate ereditati restanoaperti.


#### R4A UDP recovery — inventario JAR runtime dopo diagnostica assente

Entrambi eventi dell'originale rimasto sono NOT_RECORDED anche dopo release83249a. Verificarefile/classi/identità prima di dedurre una causa o rilasciare altro codice. Il blocco fa soltanto dockerinspect/ps/cp e lettura ziplocale, nessun avvioSpring/container o modifica del DB/job, nessun retry. Copia gli JAR dei container running selezionati nel directoryprivato nuovo, salva digest in receiptprivate e mostra soltanto fatti strutturali. Include container stopped nella lista senza copiarli/avviarli. Se una copia non-live non è unJAR/èinaccessibile, la marcaUNAVAILABLE; sul live richiesto il probe si blocca. I nomi contenentiudp sono filtroesplicito, non inventario globalehost/processi.

Controllare liveexpectedimage/revisionmatch, gateReferencesFailureEvidence, gateReferencesDiagnosticQuarantineOverload, failureEvidenceHasAllDiagnosticKeys e APIcandidates; mount/identitychanged rendono più debole l'inferenza sul bytecode giàcaricato. Non stampare receipt/jar/env/configurazioni. Nessun hashJar sul terminale. Structuralmarkers sono prova di presenza nel file letto, non prova di quale processo abbia scritto il vecchioevento. Bootstrap esterno con ORhandler per mantenereSSHaperta; path log/receiptstampati e persistenti.

```bash
set -euo pipefail
sudo python3 -u -B - ouf-udp /app/app.jar \
  sha256:5e048a859716d6674355e72238f03f899abd705a943ceadbdc5c8863d28f4e9f \
  83249a897eb4add4289b5181b3299f48ea4c0f99 \
  /etc/ouf/deploy-snapshots/udp-materialization-recovery-policy <<'PY'
import hashlib, json, os, re, stat, subprocess, sys, tempfile, zipfile
from pathlib import Path
def require(value):
    if not value:raise RuntimeError('RUNTIME_INVENTORY_BINDING_OR_SHAPE_INVALID')
def docker(*args):
    return subprocess.run(['docker',*args],check=True,capture_output=True,text=True,timeout=30).stdout.strip()
def inspect(name):return json.loads(docker('inspect',name))[0]
def identity(row):
    return (row['Id'],row['Image'],row['State']['Running'],row['State']['StartedAt'],row['RestartCount'])
def classes(path):
    base='BOOT-INF/classes/it/comune/trieste/ouf/udp/'
    with zipfile.ZipFile(path) as archive:
        def read(name):
            entries=[e for e in archive.infolist() if e.filename==base+name+'.class']
            require(len(entries)<=1)
            if not entries:return b''
            require(entries[0].file_size<=2000000);return archive.read(entries[0])
        gate=read('MaterializationReferenceGate');failure=read('ReferenceFailureEvidence')
        repo=read('ResolutionRepository');api=read('MaterializationRecoveryApi')
        signature=b'(Lit/comune/trieste/ouf/udp/ResolutionRepository$Claim;Ljava/lang/String;Ljava/util/Map;)V'
        return {'gateClassPresent':bool(gate),'failureEvidenceClassPresent':bool(failure),
            'gateReferencesFailureEvidence':b'it/comune/trieste/ouf/udp/ReferenceFailureEvidence' in gate,
            'gateReferencesDiagnosticQuarantineOverload':signature in gate,
            'repositoryHasDiagnosticQuarantineOverload':signature in repo,
            'failureEvidenceHasAllDiagnosticKeys':all(k in failure for k in (b'diagnosticCode',b'diagnosticCategory',b'diagnosticFrames')),
            'recoveryApiUsesAdmissionCandidates':b'candidates' in api}
try:
    live,jar_path,expected_image,expected_revision,parent=sys.argv[1:]
    require(os.geteuid()==0 and re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,159}',live))
    require(re.fullmatch('sha256:[a-f0-9]{64}',expected_image) and re.fullmatch('[a-f0-9]{40}',expected_revision))
    require(jar_path.startswith('/') and ':' not in jar_path and not any(c.isspace() for c in jar_path))
    parent=Path(parent);meta=parent.lstat()
    require(stat.S_ISDIR(meta.st_mode) and meta.st_uid==0 and stat.S_IMODE(meta.st_mode)==0o700)
    root=Path(tempfile.mkdtemp(prefix='runtime-reference-code-',dir=parent))
    receipt=root/'receipt.json';protocol=root/'protocol.log';rows=[]
    before=inspect(live);require(before['State']['Running'])
    with protocol.open('x') as log:
        def emit(line):print(line,flush=True);log.write(line+'\n');log.flush()
        emit('R4A_UDP_RUNTIME_CODE_RECEIPT='+str(receipt)+' PRIVATE=true')
        emit('R4A_UDP_RUNTIME_CODE_LOG='+str(protocol)+' PRIVATE=true')
        emit('UDP_LIVE_EXPECTED_IMAGE_MATCH='+str(before['Image']==expected_image).lower())
        label=(before['Config'].get('Labels') or {}).get('org.opencontainers.image.revision')
        emit('UDP_LIVE_EXPECTED_REVISION_LABEL_MATCH='+str(label==expected_revision).lower())
        names=docker('ps','-a','--format','{{.Names}}').splitlines()
        names=sorted(set([live]+[name for name in names if 'udp' in name.lower()]))
        require(len(names)<=100)
        for index,name in enumerate(names,1):
            require(re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,159}',name))
            row=inspect(name);require(re.fullmatch('sha256:[a-f0-9]{64}',row['Image']))
            restart=row['HostConfig']['RestartPolicy']['Name'];require(restart in ('no','always','unless-stopped','on-failure',''))
            revision=(row['Config'].get('Labels') or {}).get('org.opencontainers.image.revision')
            if not isinstance(revision,str) or not re.fullmatch('[a-f0-9]{40}',revision):revision='NOT_PROVEN'
            item={'name':name,'running':bool(row['State']['Running']),'imageId':row['Image'],'revisionLabel':revision,'restartPolicy':restart}
            if item['running']:
                copied=root/('app-'+str(index)+'.jar')
                try:
                    docker('cp',name+':'+jar_path,str(copied));copied.chmod(0o600)
                    require(copied.stat().st_size<=200000000)
                    item.update(classes(copied));item['jarSha256']=hashlib.sha256(copied.read_bytes()).hexdigest()
                    item['jarCopy']='PASS'
                except Exception as error:
                    if name==live:raise
                    item['jarCopy']='UNAVAILABLE';item['jarCopyFailureType']=type(error).__name__
                item['jarCoveredByMount']=any(jar_path==m['Destination'] or jar_path.startswith(m['Destination'].rstrip('/')+'/')
                    for m in row.get('Mounts',[]))
                item['identityUnchangedDuringCopy']=identity(row)==identity(inspect(name))
            rows.append(item)
            # jar digest remains private; print only identity and structural facts.
            safe={k:v for k,v in item.items() if k!='jarSha256'}
            emit('UDP_RUNTIME_CONTAINER_'+str(index)+'='+json.dumps(safe,sort_keys=True))
        unchanged=identity(before)==identity(inspect(live))
        receipt.write_text(json.dumps({'containers':rows,'liveIdentityUnchanged':unchanged},sort_keys=True));receipt.chmod(0o600)
        emit('R4A_UDP_RUNTIME_CODE_INVENTORY=COMPLETE READ_ONLY=true LIVE_IDENTITY_UNCHANGED='+str(unchanged).lower()
            +' NAME_FILTER=udp SPRING_NOT_STARTED=true RETRY=false REPLAY=false BUSINESS_STATE_UNCHANGED=true'
            +' JAR_COPY_ONLY=true SECRETS_NOT_PRINTED=true')
except Exception as error:
    print('R4A_UDP_RUNTIME_CODE_INVENTORY=BLOCKED TYPE='+type(error).__name__+' READ_ONLY=true RETRY=false SECRETS_NOT_PRINTED=true',flush=True)
    raise SystemExit(1)
PY
```


### R4A — due container UDP attivi rilevati, confronto binding ancora aperto (2026-10-01)

L'inventario runtime ricevuto dall'operatore prova che `ouf-udp` usa l'immagine attesa `sha256:5e048a859716d6674355e72238f03f899abd705a943ceadbdc5c8863d28f4e9f`, revision label `83249a897eb4add4289b5181b3299f48ea4c0f99`. Il JAR non è coperto da mount e contiene ReferenceFailureEvidence, le tre chiavi diagnostiche e l'overload diagnostico della quarantena. Identità invariata durante la copia.

È contemporaneamente RUNNING `ouf-udp-r4a-smoke`, immagine `sha256:707fe8ca7b1a795f8ff359f9fdb6c968734c0cf66e5b8f7bd9757f4104466f80`, revision label non provata, restart policy `no`. Il suo JAR contiene il gate ma non ReferenceFailureEvidence né l'overload diagnostico. Gli altri container censiti sono STOPPED; alcuni conservano restart policy `unless-stopped`. Non è stata eseguita alcuna modifica ai container.

Ricevuta privata: `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/runtime-reference-code-z145sybh/receipt.json`; protocollo omonimo `protocol.log`. La presenza di due processi non prova da sola un worker concorrente sullo stesso DB né chi abbia scritto l'evento delle 16:14:25Z. Nel codice corrente PublishedResolutionLoop è condizionato da `ouf.udp.execution.enabled=true`; ResolutionWorker presente nel JAR non prova l'attivazione del loop.

Stato business confermato precedente invariato: 7/8 materializzazioni; il job `e7572836-f8af-4c58-b5fc-12d7aff5db1d`, handoff `aed8ef93-6d00-4cf0-868d-d2d82d79b524`, resta QUARANTINED v5, attempts=2/integrityAttempts=2, CONTRACT_INVALID. Nessun ulteriore retry. Policy 36 e autorizzazione HUMAN nominale già provate; non ripubblicare e non ampliare grant.

Prossimo passo: confronto READ_ONLY delle configurazioni dichiarate dei soli due container, delle classi del loop nei rispettivi JAR e dei possibili override. Valori DB, credenziali, comandi e nomi delle reti non sono stampati né inclusi nelle ricevute. Uguaglianza dichiarata non equivale a binding effettivo Spring. Nessun arresto automatico in questa fase. Se emerge concorrenza sul DB, predisporre arresto circoscritto e reversibile del solo legacy preservato, con guard d'identità e ricevuta; successivamente nuova review HUMAN del solo job restante a v5 prima di proporne il retry.

PET consultato: UDP v1.3 §§109.6–109.7, ciclo dei claim/lease e reference-integrity senza fallback. Gate deploy da industrializzare: inventario di tutti i processi che possono acquisire job sul DB di destinazione, controllo versione/configurazione e trattamento esplicito di container legacy e restart policy; supportare più worker soltanto se compatibili e governati. Parametri di installazione in manifest/configurazione, mai endpoint/credenziali/tenant incorporati nel codice. Restano aperti 8/8, search, verifiche storage e installazione automatizzata multi-host/reti/Enti.

#### R4A UDP recovery — confronto dichiarato dei due worker UDP attivi

Questo blocco è una verifica circoscritta all'installazione lab già censita; nomi, immagini attese e destinazione ricevute sono argomenti della procedura. Non è un manifest di deploy portabile. Docker inspect/cp soltanto; nessun docker exec/start/stop/update, nessuna connessione JDBC o API business. L'esito COMPLETE significa raccolta riuscita, non prova di causalità o di binding effettivo. Guard di sintassi e configurazioni alternative verificati localmente, senza eseguire Docker.

```bash
set -euo pipefail
sudo python3 -u -B - ouf-udp ouf-udp-r4a-smoke \
  sha256:5e048a859716d6674355e72238f03f899abd705a943ceadbdc5c8863d28f4e9f \
  sha256:707fe8ca7b1a795f8ff359f9fdb6c968734c0cf66e5b8f7bd9757f4104466f80 \
  /etc/ouf/deploy-snapshots/udp-materialization-recovery-policy <<'PY'
import json, os, re, stat, subprocess, sys, tempfile, zipfile
from pathlib import Path
def require(ok):
    if not ok:raise RuntimeError('WORKER_COMPARISON_PRECONDITION_INVALID')
def docker(*args):
    return subprocess.run(['docker',*args],check=True,capture_output=True,text=True,timeout=30).stdout.strip()
def inspect(name):return json.loads(docker('inspect',name))[0]
def identity(row):return (row['Id'],row['Image'],row['State']['Running'],row['State']['StartedAt'],row['RestartCount'])
def environment(row):
    env={}
    for value in row['Config'].get('Env') or []:
        key,sep,item=value.partition('=');require(sep and key not in env);env[key]=item
    return env
def configuration(row,env):
    # Compare declared configuration only. Never infer effective Spring values from env alone.
    command=[row.get('Path','')]+(row.get('Args') or [])
    override=any(x.startswith(('--spring.','--ouf.','-Dspring.','-Douf.')) for x in command)
    dynamic=any(env.get(k,'').strip() for k in ('SPRING_APPLICATION_JSON','SPRING_CONFIG_LOCATION',
        'SPRING_CONFIG_ADDITIONAL_LOCATION','SPRING_CONFIG_IMPORT','SPRING_PROFILES_ACTIVE',
        'SPRING_PROFILES_INCLUDE','JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','JAVA_OPTS','_JAVA_OPTIONS'))
    config_mount=any(m['Destination'].rstrip('/') in ('/','/app','/app/config','/config','/workspace','/workspace/config')
        for m in row.get('Mounts',[]))
    execution_args=[x.split('=',1)[1].strip().lower() for x in command
        if x.startswith(('--ouf.udp.execution.enabled=','-Douf.udp.execution.enabled='))]
    def value(primary,secondary):
        return env.get(primary,env.get(secondary,''))
    return {'url':value('SPRING_DATASOURCE_URL','OUF_UDP_DB_URL'),
        'user':value('SPRING_DATASOURCE_USERNAME','OUF_UDP_DB_USER'),
        'password':value('SPRING_DATASOURCE_PASSWORD','OUF_UDP_DB_PASSWORD'),
        'execution':env.get('OUF_UDP_EXECUTION_ENABLED','').strip().lower(),
        'executionArgs':execution_args,
        'overrides':override or dynamic or config_mount}
def jar_facts(path):
    with zipfile.ZipFile(path) as archive:
        def read(name):
            found=[e for e in archive.infolist() if e.filename==name];require(len(found)<=1)
            if not found:return b''
            require(found[0].file_size<2000000);return archive.read(found[0])
        base='BOOT-INF/classes/'
        loop=read(base+'it/comune/trieste/ouf/udp/PublishedResolutionLoop.class')
        config=read(base+'application.yml')+read(base+'application.properties')
        return {'scheduledPublishedLoopPresent':b'org/springframework/scheduling/annotation/Scheduled' in loop,
            'executionPropertyGatePresent':b'ouf.udp.execution.enabled' in loop,
            'oufDatasourceBindingsPresent':all(k in config for k in (b'OUF_UDP_DB_URL',b'OUF_UDP_DB_USER',b'OUF_UDP_DB_PASSWORD')),
            'udpSchemaDeclared':b'ouf_udp' in config}
try:
    live,legacy,live_image,legacy_image,parent=sys.argv[1:]
    require(os.geteuid()==0 and live!=legacy)
    for name in (live,legacy):require(re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,159}',name))
    for image in (live_image,legacy_image):require(re.fullmatch('sha256:[a-f0-9]{64}',image))
    parent=Path(parent);meta=parent.lstat()
    require(stat.S_ISDIR(meta.st_mode) and meta.st_uid==0 and stat.S_IMODE(meta.st_mode)==0o700)
    os.umask(0o077);root=Path(tempfile.mkdtemp(prefix='worker-binding-comparison-',dir=parent))
    receipt=root/'receipt.json';protocol=root/'protocol.log'
    before=[inspect(live),inspect(legacy)]
    require(all(r['State']['Running'] for r in before))
    require([r['Image'] for r in before]==[live_image,legacy_image])
    envs=[environment(r) for r in before];configs=[configuration(r,e) for r,e in zip(before,envs)]
    facts=[]
    for index,name in enumerate((live,legacy)):
        copied=root/('app-'+str(index)+'.jar');docker('cp',name+':/app/app.jar',str(copied));copied.chmod(0o600)
        require(copied.stat().st_size<200000000);facts.append(jar_facts(copied))
    def same(key):return bool(configs[0][key]) and configs[0][key]==configs[1][key]
    shared=set(before[0]['NetworkSettings']['Networks'])&set(before[1]['NetworkSettings']['Networks'])
    result={'declaredDatasourceUrlEqual':same('url'),'declaredDatasourceUserEqual':same('user'),
        'declaredDatasourceCredentialsEqual':same('password'),'sharedDockerNetworkPresent':bool(shared),
        'liveExecutionEnabledDeclared':configs[0]['execution']=='true',
        'legacyExecutionEnabledDeclared':configs[1]['execution']=='true',
        'liveExecutionEnabledCommandDeclared':'true' in configs[0]['executionArgs'],
        'legacyExecutionEnabledCommandDeclared':'true' in configs[1]['executionArgs'],
        'livePotentialConfigurationOverrides':configs[0]['overrides'],
        'legacyPotentialConfigurationOverrides':configs[1]['overrides'],
        'liveJarFacts':facts[0],'legacyJarFacts':facts[1],
        'liveIdentityUnchanged':identity(before[0])==identity(inspect(live)),
        'legacyIdentityUnchanged':identity(before[1])==identity(inspect(legacy))}
    # No raw environment, URLs, credentials, command lines or network names in receipts either.
    receipt.write_text(json.dumps(result,sort_keys=True));receipt.chmod(0o600)
    with protocol.open('x') as log:
        lines=['R4A_UDP_WORKER_COMPARISON_RECEIPT='+str(receipt)+' PRIVATE=true',
            'UDP_WORKER_BINDING_FACTS='+json.dumps(result,sort_keys=True),
            'R4A_UDP_WORKER_COMPARISON=COMPLETE READ_ONLY=true EFFECTIVE_DATABASE_BINDING_NOT_PROVEN=true'
            ' HISTORICAL_WRITER_NOT_PROVEN=true STOP=false RETRY=false REPLAY=false SECRETS_NOT_PRINTED=true']
        for line in lines:print(line,flush=True);log.write(line+'\n')
except Exception as error:
    print('R4A_UDP_WORKER_COMPARISON=BLOCKED TYPE='+type(error).__name__+' READ_ONLY=true STOP=false RETRY=false SECRETS_NOT_PRINTED=true',flush=True)
    raise SystemExit(1)
PY
```


### R4A — confronto due worker completato; isolamento legacy predisposto (2026-10-01, 19:01 Europe/Rome)

Ricevuta operatore privata: `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/worker-binding-comparison-azz0955w/receipt.json`.
I due container RUNNING hanno URL/utente/credenziali DB dichiarati uguali, una rete Docker condivisa, `OUF_UDP_EXECUTION_ENABLED=true`, classi del loop schedulato e relativo gate presenti, binding datasource OUF e schema UDP dichiarati nel JAR. Nessun possibile override rilevato dalla verifica; entrambe le identità invariate. Questo è un rischio concreto di concorrenza con codice legacy incompatibile con la diagnostica corrente. Binding effettivo Spring e autore storico dell'evento NON provati; non attribuire l'evento del job restante al legacy come fatto accertato.

Decisione operativa: preservare e arrestare in modo circoscritto `ouf-udp-r4a-smoke` con immagine attesa `sha256:707fe8ca7b1a795f8ff359f9fdb6c968734c0cf66e5b8f7bd9757f4104466f80`, già restart=no. Non modificare né riavviare `ouf-udp` (immagine 5e048a, revision 83249a); non rimuovere altri container. Arresto predisposto, NON ancora eseguito/verificato.

Runbook con guard: immagini e revision live esatte; flag/binding/rate condivise riconfermati; assenza di override; main raggiungibile attraverso la rete del gateway; nessun job non terminale nell'intero DB interrogato; esattamente sette originali SUCCEEDED/PROCESSED e il restante job e7572836 QUARANTINED/DURABLE a v5. Prima della mutazione salva e fsync la ricevuta privata STOP_INTENT_OUTCOME_UNKNOWN. Lo stop usa l'ID immutabile del solo legacy e 60 secondi per shutdown; un timeout non provoca né restart automatico né retry. Dopo lo stop verifica exit code 0/143 e assenza OOM, restart=no, identità del main invariata, salute backend gateway e confronto completo degli originali prima/dopo.

Verifica locale: sintassi Bash/Python e sei scenari simulati (successo, immagine diversa, override, salute assente, worker non idle, timeout/esito sconosciuto), senza Docker reale. Nessuna chiamata di stop del main in tutti gli scenari. Ricevuta STOP privata con stati e identificativi, senza env/credenziali/URL DB/comandi. Nessun backup aggiuntivo: questa procedura non modifica schema o dati business. Le query sono READ ONLY; l'unica mutazione prevista è lo stop del container legacy.

PET UDP v1.3 §§109.6–109.7 riconsultato: niente arresto con claim pendenti, shutdown controllato e nessun silent fallback. Il gate deploy deve inventariare tutti i processi worker collegabili al DB target e verificare che le loro versioni siano ammesse; non assumere che un rilascio del container principale escluda worker di smoke residui. Conservare parametri host/reti/domain/tenant/moduli nei manifest di installazione e supportare worker concorrenti soltanto con contratti compatibili. Altri container STOPPED con restart unless-stopped restano censiti, senza cleanup indiscriminato.

Stato recovery: 7/8 confermati; nessun nuovo retry eseguito. Dopo PASS dell'isolamento, predisporre una nuova review HUMAN del solo originale restante a v5 e un nuovo retry esplicitamente confermato, usando la policy nominale 36 esistente senza ripubblicazione né ampliamento. Non riutilizzare lo script precedente dei tre job a v2. 8/8, search, storage e industrializzazione deploy restano aperti.

#### R4A UDP recovery — arresto circoscritto del worker legacy con guard

Eseguire una sola volta dopo il confronto ricevuto sopra. Parametri espliciti dell'installazione lab, non configurazione incorporata nell'applicazione. Non ripetere automaticamente se BLOCKED dopo STOP_INTENT: riconciliare la ricevuta e lo stato corrente. Nessun replay/intake POST/retry/materializzazione avviata. La salute usa un container curl temporaneo sul namespace di rete del gateway con immagine già locale e pull=never.

```bash
set -euo pipefail
sudo python3 -u -B - ouf-udp ouf-udp-r4a-smoke \
  sha256:5e048a859716d6674355e72238f03f899abd705a943ceadbdc5c8863d28f4e9f \
  sha256:707fe8ca7b1a795f8ff359f9fdb6c968734c0cf66e5b8f7bd9757f4104466f80 \
  83249a897eb4add4289b5181b3299f48ea4c0f99 \
  ouf-postgres ouf_udp ouf_udp ouf-apisix curlimages/curl:8.16.0 \
  http://ouf-udp:8080/actuator/health managed-cinema-8ec8ae90 \
  86809c17-3354-45ca-a7e6-57e903944b24 e7572836-f8af-4c58-b5fc-12d7aff5db1d \
  /etc/ouf/deploy-snapshots/udp-materialization-recovery-policy <<'PY'
import json, os, re, stat, subprocess, sys, tempfile, uuid
from pathlib import Path
def require(ok,code):
    if not ok:raise ValueError(code)
def docker(*args,timeout=30):
    return subprocess.run(['docker',*args],check=True,capture_output=True,text=True,timeout=timeout).stdout.strip()
def inspect(name):return json.loads(docker('inspect',name))[0]
def identity(row):return (row['Id'],row['Image'],row['State']['Running'],row['State']['StartedAt'],row['RestartCount'])
def env(row):
    values={}
    for entry in row['Config'].get('Env') or []:
        key,sep,value=entry.partition('=');require(sep and key not in values,'ENV_SHAPE_INVALID');values[key]=value
    return values
def bindings(rows):
    values=[env(r) for r in rows]
    for key in ('OUF_UDP_DB_URL','OUF_UDP_DB_USER','OUF_UDP_DB_PASSWORD'):
        require(bool(values[0].get(key)) and values[0][key]==values[1].get(key),'DECLARED_DB_BINDINGS_CHANGED')
    for row,v in zip(rows,values):
        require(v.get('OUF_UDP_EXECUTION_ENABLED','').lower()=='true','WORKER_FLAG_CHANGED')
        forbidden=('SPRING_APPLICATION_JSON','SPRING_CONFIG_LOCATION','SPRING_CONFIG_ADDITIONAL_LOCATION',
            'SPRING_CONFIG_IMPORT','SPRING_PROFILES_ACTIVE','SPRING_PROFILES_INCLUDE','JAVA_TOOL_OPTIONS',
            'JDK_JAVA_OPTIONS','JAVA_OPTS','_JAVA_OPTIONS','SPRING_DATASOURCE_URL','SPRING_DATASOURCE_USERNAME','SPRING_DATASOURCE_PASSWORD')
        require(not any(v.get(k,'').strip() for k in forbidden),'CONFIG_OVERRIDE_PRESENT')
        require(not any(x.startswith(('--spring.','--ouf.','-Dspring.','-Douf.'))
            for x in [row.get('Path','')]+(row.get('Args') or [])),'COMMAND_OVERRIDE_PRESENT')
        require(not any(m['Destination'].rstrip('/') in ('','/app','/app/config','/config','/workspace','/workspace/config')
            for m in row.get('Mounts',[])),'CONFIG_MOUNT_PRESENT')
    require(bool(set(rows[0]['NetworkSettings']['Networks'])&set(rows[1]['NetworkSettings']['Networks'])),'NETWORK_BINDING_CHANGED')
def health(gateway,curl_image,url):
    return docker('run','--rm','--pull','never','--network','container:'+gateway,'--read-only',
        '--cap-drop','ALL','--security-opt','no-new-privileges',curl_image,'--max-time','5','-sS',
        '-o','/dev/null','-w','%{http_code}',url)=='200'
def database_state(pg,database,user,source,run,job):
    sql=("begin read only; set local statement_timeout='15s'; set local lock_timeout='2s'; "
        "select json_build_object('pending', (select count(*) from ouf_udp.materialization_job "
        "where state not in ('SUCCEEDED','QUARANTINED','FAILED')), 'jobs', "
        "(select json_agg(q order by job_id) from (select j.job_id,j.handoff_id,j.state,j.state_version,"
        "j.attempts,j.integrity_attempts,j.safe_failure_code,h.state intake_state "
        "from ouf_udp.materialization_job j join ouf_udp.handoff_intake h using(handoff_id) "
        "where h.source_id='"+source+"' and h.ingestion_run_id='"+run+"') q)); rollback;")
    state=json.loads(docker('exec',pg,'psql','-X','-qAt','-v','ON_ERROR_STOP=1','-U',user,'-d',database,'-c',sql))
    require(state['pending']==0,'WORKERS_NOT_IDLE')
    rows=state['jobs'];require(isinstance(rows,list) and len(rows)==8,'RUN_JOB_SET_CHANGED')
    require(sum(r['state']=='SUCCEEDED' and r['intake_state']=='PROCESSED' for r in rows)==7,'RUN_JOB_STATES_CHANGED')
    target=[r for r in rows if r['job_id']==job]
    require(len(target)==1 and target[0]['state']=='QUARANTINED' and target[0]['state_version']==5
        and target[0]['intake_state']=='DURABLE','REMAINING_JOB_CHANGED')
    return state
receipt=None;data={}
try:
    live,legacy,live_image,legacy_image,revision,pg,database,user,gateway,curl_image,url,source,run,job,parent=sys.argv[1:]
    require(os.geteuid()==0 and live!=legacy,'OPERATOR_BINDING_INVALID')
    for name in (live,legacy,pg,database,user,gateway,source):require(re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,159}',name),'ARGUMENT_INVALID')
    for image in (live_image,legacy_image):require(re.fullmatch('sha256:[a-f0-9]{64}',image),'IMAGE_ARGUMENT_INVALID')
    require(re.fullmatch('[a-f0-9]{40}',revision) and url.startswith('http://') and not any(c.isspace() for c in url),'ARGUMENT_INVALID')
    run=str(uuid.UUID(run));job=str(uuid.UUID(job));parent=Path(parent);meta=parent.lstat()
    require(stat.S_ISDIR(meta.st_mode) and meta.st_uid==0 and stat.S_IMODE(meta.st_mode)==0o700,'PRIVATE_DIRECTORY_INVALID')
    os.umask(0o077);root=Path(tempfile.mkdtemp(prefix='legacy-worker-stop-',dir=parent));receipt=root/'receipt.json'
    def save():
        temporary=root/'receipt.tmp'
        with temporary.open('w') as stream:json.dump(data,stream,sort_keys=True);stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,receipt)
        fd=os.open(root,os.O_RDONLY);os.fsync(fd);os.close(fd)
    print('R4A_UDP_LEGACY_STOP_RECEIPT='+str(receipt)+' PRIVATE=true',flush=True)
    before=[inspect(live),inspect(legacy)]
    require(all(r['State']['Running'] for r in before),'RUNTIME_STATE_CHANGED')
    require([r['Image'] for r in before]==[live_image,legacy_image],'IMAGE_ID_CHANGED')
    require((before[0]['Config'].get('Labels') or {}).get('org.opencontainers.image.revision')==revision,'LIVE_REVISION_CHANGED')
    require(before[1]['HostConfig']['RestartPolicy']['Name']=='no','LEGACY_RESTART_POLICY_CHANGED')
    bindings(before)
    require(health(gateway,curl_image,url),'LIVE_GATEWAY_HEALTH_UNAVAILABLE')
    state=database_state(pg,database,user,source,run,job)
    require(all(identity(r)==identity(inspect(r['Id'])) for r in before),'RUNTIME_IDENTITY_CHANGED')
    data.update(status='STOP_INTENT_OUTCOME_UNKNOWN',liveId=before[0]['Id'],legacyId=before[1]['Id'],
        legacyName=legacy,legacyImage=legacy_image,originalJobs=state['jobs'],retry=False)
    save()
    print('R4A_UDP_LEGACY_STOP=START IDENTITY_GUARDS=PASS WORKERS_IDLE=true TARGET='+legacy+' RETRY=false',flush=True)
    docker('stop','--time','60',before[1]['Id'],timeout=75)
    after=inspect(before[1]['Id'])
    data['legacyStopped']=not after['State']['Running'];data['legacyExitCode']=after['State']['ExitCode'];save()
    require(not after['State']['Running'] and not after['State'].get('OOMKilled')
        and after['State']['ExitCode'] in (0,143),'GRACEFUL_STOP_NOT_PROVEN')
    require(after['Image']==legacy_image and after['HostConfig']['RestartPolicy']['Name']=='no','LEGACY_FINAL_STATE_CHANGED')
    require(identity(before[0])==identity(inspect(before[0]['Id'])),'LIVE_IDENTITY_CHANGED')
    require(health(gateway,curl_image,url),'POST_STOP_GATEWAY_HEALTH_FAILED')
    require(database_state(pg,database,user,source,run,job)==state,'BUSINESS_STATE_CHANGED')
    data.update(status='PASS_LEGACY_STOPPED',liveIdentityUnchanged=True,gatewayBackendHealth=True,
        originalJobsUnchanged=True,legacyRestartDisabled=True,historicalWriterProven=False);save()
    print('R4A_UDP_LEGACY_STOP=PASS LEGACY_STOPPED=true LEGACY_PRESERVED=true LEGACY_RESTART_DISABLED=true'
        ' LIVE_IDENTITY_UNCHANGED=true GATEWAY_BACKEND_HEALTH=true ORIGINAL_JOBS_UNCHANGED=true'
        ' RETRY=false REPLAY=false HISTORICAL_WRITER_NOT_PROVEN=true SECRETS_NOT_PRINTED=true',flush=True)
except Exception as error:
    if receipt is not None:
        data['failureType']=type(error).__name__
        if 'status' not in data:data['status']='BLOCKED_BEFORE_STOP'
        save()
    print('R4A_UDP_LEGACY_STOP=BLOCKED TYPE='+type(error).__name__+
        ' RECONCILE_RECEIPT=true NO_AUTOMATIC_RESTART=true RETRY=false SECRETS_NOT_PRINTED=true',flush=True)
    raise SystemExit(1)
PY
```


### R4A — isolamento legacy PASS; recovery del solo originale restante predisposta (2026-10-01, 19:10 Europe/Rome)

L'operatore ha restituito PASS dell'arresto circoscritto. Ricevuta privata `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/legacy-worker-stop-asbhqris/receipt.json`: legacy STOPPED, preservato, restart disabilitato; identità live invariata, salute backend gateway PASS, originali invariati. Guard prima dello stop: worker idle. Nessun retry/replay eseguito in questa fase. Autore storico dell'evento di quarantena ancora NON provato.

Ultimo stato business provato: 7 originali SUCCEEDED/PROCESSED e il job `e7572836-f8af-4c58-b5fc-12d7aff5db1d` / handoff `aed8ef93-6d00-4cf0-868d-d2d82d79b524` QUARANTINED/DURABLE a v5. La procedura nuova seleziona soltanto questo job. Verifica comunque resources.json completo, hash della ricevuta di pubblicazione, descriptor e tutti e tre i grant nominali; non produce una policy ristretta diversa e non ripubblica la versione 36. Gli altri due job già recuperati non vengono riesaminati come quarantene né rilanciati.

Codice helper pubblicato e congelato a `9ff81375422399bd1a259414dbe9932cb8fdcd1a`: `--select-job` restringe GET/POST al sottoinsieme del resource set completo verificato; ID fuori insieme o duplicati sono bloccati. `--prior-expected-version 2` valida soltanto la review storica di tutti e tre i job. La nuova review owner HUMAN deve avere stato QUARANTINED/DURABLE, versione esatta 5, contratto READY e snapshot verificato; è l'unica origine di snapshot e versione del nuovo POST. Il fresh receipt deve contenere l'esatto sottoinsieme selezionato. Mai utilizzare lo snapshot della review storica per il nuovo comando.

Il blocco operatore ricontrolla la ricevuta di isolamento PASS e gli ID/immagini corrente principale/legacy, legacy fermo con restart=no e revision live attesa prima del login. Poi Device Grant THS nominale `ouf-admin` con scope già configurato; GET anonima e fuori ambito devono essere negate, GET owner fresca del solo restante deve passare. Piano JOBS=1, expectedVersion=5, READY acceptedVersion=6. Solo dopo la conferma esplicita nel terminale viene trasmesso un POST /retry dell'originale; operationId e richiesta persistiti prima della trasmissione, token con oltre 60 secondi residui, nessuna ripetizione automatica.

La conferma richiesta resta `CONFERMO RETRY ORIGINALE 86809c17-3354-45ca-a7e6-57e903944b24`: verificare prima che il piano stampato abbia JOBS=1 e il solo ID e7572836. Receipt/protocol nuovi con prefisso human-retry-remaining, separati da quelli precedenti. Se BLOCKED o risposta incerta, riconciliare le ricevute senza rilanciare automaticamente. PASS di retry significa requeue accettato, NON materializzazione riuscita; servirà readback business successivo. La procedura non crea intake/handoff o replay, non riattiva la source/schedule.

Verifiche: 50 test locali policy/recovery, incluse regressioni selezione singola v5->6, altri due già SUCCEEDED, selezione fuori scope/duplicata, drift v6 e contratto non READY. Preflight isolamento: cinque scenari simulati. CI sul pin helper: 113 test recovery PASS (job 110488957023, run PR 36897761180), Java/container PASS, tutti e sette i workflow push/PR SUCCESS inclusi Authorization, Shared SDK e Gateway pairwise. Checksum dei tre file modificati aggiornati. Nessun nuovo deploy UDP necessario.

PET riconsultati: UDP v1.3 §§109.6–109.7 e Authorization v1.5 §36.10, owner enforcement e reference gate senza fallback. Installazione portabile continua a separare argomenti/configurazione da codice helper; blocco seguente è una riconciliazione lab con binding espliciti, non un default per Enti diversi. Handoff/deploy/roadmap conservano aperti 8/8, search, verifiche storage e automatizzazione install/upgrade/restore. Esito live della recovery singola ancora NON eseguito.

#### R4A UDP recovery — review fresca e retry HUMAN del solo originale restante a v5

Serve login THS nominale e conferma del piano di UN SOLO job. L'isolamento legacy è ricontrollato prima del login. Si verifica l'intero insieme pubblicato di tre risorse ma si seleziona soltanto e7572836 per nuove GET owner e POST. Nessuna richiesta business viene trasmessa prima della nuova review READY e della conferma. Non ripetere il blocco dopo un esito incerto: riconciliare la ricevuta indicata.

```bash
set -euo pipefail
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
REVISION=9ff81375422399bd1a259414dbe9932cb8fdcd1a
WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT
for SCRIPT in r4a_retry_human_materialization.py r4a_read_human_materialization_review.py r4a_prepare_scoped_human_policy.py; do
  git show "$REVISION:scripts/$SCRIPT" > "$WORK_DIR/$SCRIPT"
done
sudo bash -s -- "$WORK_DIR" <<'ROOT'
set -euo pipefail
umask 077
WORK_DIR=$1
STATE_DIR=/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy
python3 -u -B - "$STATE_DIR/legacy-worker-stop-asbhqris/receipt.json" \
  ouf-udp ouf-udp-r4a-smoke \
  sha256:5e048a859716d6674355e72238f03f899abd705a943ceadbdc5c8863d28f4e9f \
  sha256:707fe8ca7b1a795f8ff359f9fdb6c968734c0cf66e5b8f7bd9757f4104466f80 \
  83249a897eb4add4289b5181b3299f48ea4c0f99 <<'PY'
import json, os, stat, subprocess, sys
from pathlib import Path
def require(ok):
    if not ok:raise ValueError('LEGACY_ISOLATION_BINDING_INVALID')
try:
    receipt,live,legacy,live_image,legacy_image,revision=sys.argv[1:]
    path=Path(receipt);meta=path.lstat()
    require(stat.S_ISREG(meta.st_mode) and meta.st_uid==0 and stat.S_IMODE(meta.st_mode)==0o600)
    saved=json.loads(path.read_text())
    require(saved['status']=='PASS_LEGACY_STOPPED' and saved['originalJobsUnchanged'] is True)
    require(saved['liveIdentityUnchanged'] is True and saved['legacyRestartDisabled'] is True)
    def inspect(name):
        return json.loads(subprocess.run(['docker','inspect',name],check=True,
            capture_output=True,text=True,timeout=15).stdout)[0]
    main=inspect(live);old=inspect(legacy)
    require(main['Id']==saved['liveId'] and main['Image']==live_image and main['State']['Running'])
    require((main['Config'].get('Labels') or {}).get('org.opencontainers.image.revision')==revision)
    require(old['Id']==saved['legacyId'] and old['Image']==legacy_image and not old['State']['Running'])
    require(old['HostConfig']['RestartPolicy']['Name']=='no')
    print('R4A_UDP_REMAINING_RETRY_PREFLIGHT=PASS READ_ONLY=true LEGACY_STOPPED=true LIVE_BINDING_MATCH=true RETRY=false',flush=True)
except Exception as error:
    print('R4A_UDP_REMAINING_RETRY_PREFLIGHT=BLOCKED TYPE='+type(error).__name__+' READ_ONLY=true RETRY=false SECRETS_NOT_PRINTED=true',flush=True)
    raise SystemExit(1)
PY
LOG=$(mktemp "$STATE_DIR/human-retry-protocol.XXXXXX")
printf 'HUMAN_RETRY_PROTOCOL_LOG=%s PRIVATE=true\n' "$LOG"
RECEIPT="$STATE_DIR/human-retry-remaining-$(date -u +%Y%m%dT%H%M%S)-$$.json"
set +e
python3 -u -B "$WORK_DIR/r4a_retry_human_materialization.py" \
  --issuer https://auth.ouf-lab.it/realms/ouf --client ouf-human-admin \
  --audience ouf-api-gateway --tenant ouf-lab \
  --subject b93d8cf6-cd14-4ee6-91d7-84cd76c4f500 \
  --scope udp.materialization.retry --expected-policy ouf-lab-authorization:36 \
  --base-url https://api.ouf-lab.it/api/udp/v1/governance/materialization/jobs \
  --publication-receipt "$STATE_DIR/publication-receipt.json" \
  --resources "$STATE_DIR/resources.json" --receipt "$RECEIPT" \
  --prior-review-receipt "$STATE_DIR/human-review-20261001T155349-3513740.json" \
  --run 86809c17-3354-45ca-a7e6-57e903944b24 --source managed-cinema-8ec8ae90 \
  --reason "Ripresa del solo job originale restante dopo isolamento worker legacy e nuova review HUMAN READY" \
  --expected-version 5 --prior-expected-version 2 --expected-resources 3 \
  --select-job e7572836-f8af-4c58-b5fc-12d7aff5db1d \
  --expected-failure UDP_REFERENCE_INTEGRITY_CONTRACT_INVALID \
  --binding 7793566d-b9d4-4402-8cda-c09b8f135c04:8869a6d6-3d82-4514-a63a-d23f9b26d48f \
  --binding e7572836-f8af-4c58-b5fc-12d7aff5db1d:aed8ef93-6d00-4cf0-868d-d2d82d79b524 \
  --binding e5b6ca24-6143-4ae5-8907-5dce398abfa3:e58faf8c-c35a-4106-b4b6-67e58dec9774 \
  --outside-job f84de729-c245-4e34-80cf-764c4eb0f160 2>&1 |
  python3 -u -c '
import sys
with open(sys.argv[1], "a", buffering=1) as log:
    for line in sys.stdin:
        sys.stdout.write(line); sys.stdout.flush()
        if line.startswith(("UDP_HUMAN_REVIEW_", "UDP_HUMAN_RETRY_", "R4A_UDP_")):
            log.write(line); log.flush()
' "$LOG"
RESULT=("${PIPESTATUS[@]}")
set -e
printf 'HUMAN_RETRY_PROTOCOL_LOG=%s PRIVATE=true\n' "$LOG"
printf 'HUMAN_RETRY_PROCESS_EXIT=%s OUTPUT_CAPTURE_EXIT=%s\n' "${RESULT[0]}" "${RESULT[1]}"
test "${RESULT[1]}" -eq 0
exit "${RESULT[0]}"
ROOT
```


### R4A — retry del solo originale restante accettato; verifica 8/8 pendente (2026-10-01, 19:22 Europe/Rome)

Output operatore ricevuto: nuova GET owner HUMAN HTTP 200 sul solo job `e7572836-f8af-4c58-b5fc-12d7aff5db1d`, handoff `aed8ef93-6d00-4cf0-868d-d2d82d79b524`, QUARANTINED/DURABLE v5, retryEligible=true, contractReady=true, contractCheck=READY. Anonimo e fuori ambito negati; owner authorization e reference gate Spring PASS. Piano JOBS=1 per run `86809c17-3354-45ca-a7e6-57e903944b24` e source `managed-cinema-8ec8ae90`. Conferma esplicita nel terminale seguita da POST HTTP 200, original job match, acceptedVersion=6, READY, repeated=false. ACCEPTED_COUNT=1. Nessun replay/new intake POST.

Ricevuta fresca privata: `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/human-retry-remaining-20261001T172023-3532794-fresh-review.json`. Ricevuta primaria prevista dal blocco eseguito: stesso stem senza `-fresh-review`, cioè `human-retry-remaining-20261001T172023-3532794.json`; da verificare nel readback, non ricostruire o sovrascrivere. Protocollo privato `human-retry-protocol.edu1pk`. L'output riportato prova il comando accettato; non contiene ancora il readback di materializzazione né gli exit code finali del wrapper.

Ultimo stato materializzato provato ancora 7/8. Non promuovere a 8/8 dal solo READY acceptedVersion=6. Legacy isolato e conservato con restart=no nella ricevuta precedente `legacy-worker-stop-asbhqris/receipt.json`; causalità storica dell'evento senza diagnostica tuttora non provata.

Prossimo blocco READ_ONLY: valida la ricevuta primaria privata (PASS_AUTHORIZED_REQUEUE, humanConfirmed, un solo job/handoff, selectedJobIds esatto, versione richiesta 5 e accettata 6, operationId UUID corrispondente, repeated=false). Poi esegue il readback Cinema della source frozen e la diagnostica UDP parametrizzata per run/source; acquisisce entrambe le uscite in un nuovo protocollo privato anche se il primo controllo non prova il risultato completo. Nessun login THS, retry, replay, riattivazione o intake POST. Helpers congelati al pin CI verde `9ff81375422399bd1a259414dbe9932cb8fdcd1a`; wrapper guarda ricevuta verificato su sei scenari locali, senza query live.

Il readback Cinema resta una fixture lab esplicita, non un manifest portabile: in una nuova installazione utilizzare parametri frozen/source/run e binding di deployment locali. Le query dei diversi DB non sono uno snapshot atomico. Criterio di completamento: otto originali consegnati e otto job SUCCEEDED/PROCESSED con reference gate passato e risoluzione completata, nessun job originale in quarantena. Distinguere questo risultato dalla verifica serving/Search, dai controlli storage e dal deploy industrializzato, ancora aperti.

PET UDP v1.3 §§109.6–109.7 riconsultato: recovery governata e verifica reference-integrity prima della materializzazione. Nessun nuovo deploy, policy publish o ampliamento di autorizzazione. Handoff, manuale installazione, roadmap e runbook aggiornati; acquisire il prossimo output prima di dichiarare il gate 8/8 chiuso.

#### R4A UDP recovery — readback dopo retry HUMAN del solo restante accettato a v6

Sola lettura: prima verifica della ricevuta privata, poi readback business ed eventi degli otto originali. Non necessita di login. Il readback Cinema è la fixture frozen dell'installazione lab documentata; la diagnostica UDP riceve esplicitamente i binding del deployment. Se l'esito non è provato, conservare l'output completo senza rilanciare retry.

```bash
set -euo pipefail
umask 077
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
ouf_helpers=9ff81375422399bd1a259414dbe9932cb8fdcd1a
ouf_readback_dir=$(mktemp -d /tmp/ouf-r4a-after-retry.XXXXXX)
trap 'rm -rf -- "$ouf_readback_dir"' EXIT
for script in r4a_cinema_execution_readback.py r4a_execution_failure_bundle.py r4a_execution_route_inventory.py r4a_prepare_frozen_compatibility_probe.py r4a_udp_materialization_diagnostic.py; do
  git show "$ouf_helpers:scripts/$script" > "$ouf_readback_dir/$script"
done
sudo bash -s -- "$ouf_readback_dir" <<'ROOT'
set -euo pipefail
umask 077
ouf_readback_dir=$1
ouf_state_dir=/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy
ouf_retry_receipt="$ouf_state_dir/human-retry-remaining-20261001T172023-3532794.json"
ouf_run=86809c17-3354-45ca-a7e6-57e903944b24
ouf_source=managed-cinema-8ec8ae90
ouf_bindings=(
  e7572836-f8af-4c58-b5fc-12d7aff5db1d:aed8ef93-6d00-4cf0-868d-d2d82d79b524
)
LOG=$(mktemp "$ouf_state_dir/readback-after-retry.XXXXXX")
printf 'R4A_POST_RETRY_READBACK_LOG=%s PRIVATE=true\n' "$LOG"
python3 -B - "$ouf_retry_receipt" "$ouf_run" "$ouf_source" "${ouf_bindings[@]}" <<'PY' | tee "$LOG"
import json, os, re, stat, sys, uuid
from pathlib import Path
def require(value):
    if not value:raise RuntimeError('RECEIPT_MISMATCH')
try:
    path=Path(sys.argv[1]);meta=path.lstat();parent=path.parent.lstat()
    require(os.geteuid()==0 and stat.S_ISREG(meta.st_mode) and meta.st_uid==0 and stat.S_IMODE(meta.st_mode)==0o600)
    require(stat.S_ISDIR(parent.st_mode) and parent.st_uid==0 and stat.S_IMODE(parent.st_mode)==0o700)
    require(meta.st_size<=8000000)
    value=json.loads(path.read_text());expected=dict(pair.split(':',1) for pair in sys.argv[4:])
    require(all(str(uuid.UUID(j))==j and str(uuid.UUID(h))==h for j,h in expected.items()))
    require(value['status']=='PASS_AUTHORIZED_REQUEUE' and value['runId']==sys.argv[2] and value['sourceId']==sys.argv[3])
    require(value['humanConfirmed'] is True and len(value['rows'])==len(expected)==1)
    require(value['selectedJobIds']==sorted(expected))
    require({row['jobId'] for row in value['rows']}==set(expected))
    operations=set()
    for row in value['rows']:
        request=row['request'];receipt=row['receipt'];job=row['jobId'];handoff=expected[job]
        require(row['status']=='PASS_ACCEPTED' and row['handoffId']==handoff)
        require(type(request['expectedVersion']) is int and request['expectedVersion']==5
            and re.fullmatch('sha256:[a-f0-9]{64}',request['expectedSnapshotHash']))
        operation=request['operationId'];require(str(uuid.UUID(operation))==operation and operation not in operations)
        operations.add(operation)
        require(receipt['operationId']==operation and receipt['jobId']==job and receipt['handoffId']==handoff)
        require(type(receipt['acceptedVersion']) is int and receipt['acceptedVersion']==6
            and receipt['state']=='READY' and receipt['repeated'] is False)
    print('R4A_HUMAN_RETRY_SAVED_RECEIPT=PASS ACCEPTED_COUNT=1 EXACT_REMAINING_ORIGINAL_JOB=true SAVED_EVIDENCE_ONLY=true LIVE_MATERIALIZATION_NOT_YET_QUERIED=true SECRETS_NOT_PRINTED=true')
except Exception as error:
    print('R4A_HUMAN_RETRY_SAVED_RECEIPT=BLOCKED TYPE='+type(error).__name__+' READ_ONLY=true SECRETS_NOT_PRINTED=true')
    raise SystemExit(1)
PY
set +e
python3 -u -B "$ouf_readback_dir/r4a_cinema_execution_readback.py" 2>&1 | tee -a "$LOG"
ouf_cinema_result=("${PIPESTATUS[@]}")
python3 -u -B "$ouf_readback_dir/r4a_udp_materialization_diagnostic.py" \
  --run "$ouf_run" --source "$ouf_source" \
  --postgres-container ouf-postgres --database ouf_udp --db-user ouf_udp 2>&1 | tee -a "$LOG"
ouf_udp_result=("${PIPESTATUS[@]}")
set -e
printf 'R4A_POST_RETRY_READBACK_LOG=%s PRIVATE=true\n' "$LOG"
printf 'R4A_POST_RETRY_READBACK_EXIT=%s UDP_DIAGNOSTIC_EXIT=%s READ_ONLY=true RETRY=false REPLAY=false\n' "${ouf_cinema_result[0]}" "${ouf_udp_result[0]}"
test "${ouf_cinema_result[0]}" -eq 0
test "${ouf_cinema_result[1]}" -eq 0
test "${ouf_udp_result[0]}" -eq 0
test "${ouf_udp_result[1]}" -eq 0
ROOT
```


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
