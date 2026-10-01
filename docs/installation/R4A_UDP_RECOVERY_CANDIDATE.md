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
