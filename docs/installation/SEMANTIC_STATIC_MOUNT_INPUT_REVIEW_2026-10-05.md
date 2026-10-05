## §44 AUTORIZZATO — comando operatore da eseguire, output non ancora ricevuto

Conferimento esplicito utente5 ottobre2026 12:52:29 Europe/Rome: lettura18input fissi incluse2TLS private keys+2MACkeys, compiler replay/OpenSSL e output redatto. Esclusi ca.key/deployment keys/Env/Docker/provider/firma/avvio. Wrapper eseguibile immutabile `7b084e207f882168b11137f27d9647fa0d35525e`, SHA256 `d3aa10849587f3c46c6724764b86d2810eae0e01dbb22a245a8947d0b3e98b83`; header PREPARED nel pin è storico, questo conferimento lo autorizza senza modificarne i bytes. Receipt `docs/handoffs/receipts/SEMANTIC_MOUNT_INPUTS_SCOPE_44_AUTHORIZATION_2026-10-05.json`. **NON ANCORA ESEGUITO/nessun output VPS ricevuto**, ultimo VPS43PASS. Eseguire una volta nella sessione oufadmin del server, preservare l'output redatto; non ripetere43 o i precedenti. Codice7b084e e checkpoint96080f:7workflow PR returned tutti completed/success;59root+2Docker tests/0skip già verificati sui log codice. Acceptance/start restano false; PET vincolanti. Stato corrente prevale sulle cronologie sottostanti.

# §44 — controllo statico degli input delle mount

**PREPARATO, NON AUTORIZZATO, NON ESEGUITO sul VPS.** Ultimo VPS §43 PASS; non ripetere i controlli completati. Sorgente wrapper immutabile `7b084e207f882168b11137f27d9647fa0d35525e`, SHA256 `d3aa10849587f3c46c6724764b86d2810eae0e01dbb22a245a8947d0b3e98b83`; percorso `docs/handoffs/commands/OUF_VERIFY_MOUNT_INPUTS_2026-10-05.sh`. Revisionabile: https://github.com/GioNob/ouf-semantic-registry/blob/7b084e207f882168b11137f27d9647fa0d35525e/docs/handoffs/commands/OUF_VERIFY_MOUNT_INPUTS_2026-10-05.sh

## Scope privato concreto da conferire

Legge esattamente 18 file, due volte per rilevare cambiamenti: i 10 input §40 (manifest, launch receipt, TLS receipt, trust receipt, stage receipt, binding, runtime plan, adapter.json, config.yaml, apisix.yaml) e 8 artefatti trust (ca.crt, trust-bundle.pem, adapter/server.crt, adapter/server.key, adapter/provider-receipt.key, southbound/server.crt, southbound/server.key, southbound/provider-receipt.key). Paths lab, UID/GID e manifest hash sono espliciti nel wrapper; nessun percorso aggiuntivo aperto da JSON privato.

**Nuova lettura privata: 2 chiavi TLS e 2 chiavi MAC.** apisix.yaml contiene inoltre la chiave TLS inline già letta nel §40. Esclude ca.key, chiavi deployment/node signing, Env, credenziali registry, Docker/container/live rootfs. Chiavi/configurazioni restano in memoria e stdin OpenSSL; niente private spool. Output solo hash, contatori e esiti, senza contenuti o percorsi privati.

Usa sudo /usr/bin/python3 -I -B e /usr/bin/openssl verificato root-owned e hash-stabile. Scrive/elimina un proprio temporaneo contenente **soltanto CA pubblica** e output pubblico DER/stato in /tmp; non scrive target/configurazioni o chiavi. Nessuna rete/provider/firma, modifica policy, consumer link, registrazione runtime, creazione o avvio. Deadline60s; ciascun OpenSSL≤3s; receipt/config≤128KiB, artefatti role≤64KiB, CA/bundle≤1MiB; nofollow/regular/nlink1/owner/mode/ancestor e doppia rilettura stabile.

## Cosa prova

Catena receipt e hash; corrispondenza crittografica delle due leaf/key, catena verso CA esplicita, purpose sslserver, hostname esatto, validità temporale e rifiuto hostname errato; nessuna CA predefinita o revocation download. Pairing MAC64hex, corrispondenza di tutti8artefatti alle receipt. Ricompila binding→plan e tre configurazioni byte-per-byte da9 sorgenti Gateway pubblici congelati al pin516133e59be869012d3003758e545a5b5aa0060a. Otto hash compiler devono corrispondere allo stage; materializerTLS è sorgente aggiuntivo revisionato. Il solo read della Lua è sostituito dal medesimo testo embedded; nessun source privato eseguito.

Mappa le8 mount dichiarate nel manifest già pinned (5adapter+3southbound) agli8file effettivamente montati: source esatto, destinazione sicura e TLS/MAC/CA coerenti con binding, readOnly, nessun extra/missing/duplicato. I target dei3file configurazione sono quelli del manifest sigillato; non è una ricostruzione della full OCI/mount view. Legge anche gli artefatti TLS/MAC southbound non montati separatamente per verificare la relazione con la chiave inline.

## Limiti vincolanti PET

PET Semantic§159.2 e Gateway supply-chain richiedono provenance/SBOM oltre ai checksum: questo controllo non li chiude. Authorization§36.10 mantiene scope/authority separati e fail-closed. Nessuna acceptance autoapprovata. Non prova snapshot atomico, generation reale, full OCI/mount view, rootfs corrente, revocation o publisher provenance; input host/receipt non firmati non proteggono contro host root compromesso. acceptanceGranted/startAuthorized/runtimeRegistered=false sempre. Issuer esterno e acceptance al punto shadow OCI rimangono lavoro distinto; §43 riusato senza Docker save ripetuto.

## Verifica e intervento richiesto

11 test nativi locali PASS,0skip: OpenSSL reale con fixture TLS, mismatch key/host/expiry, compiler replay e drift reseal, mount drift, byte/metadata/IO/redaction e CLI embedded isolata. Il filesystem locale non consente chown verso gli UID target; test separato **obbligatorio in CI root**, nessun mock/skip, esercita10006 e636. CI al pin7b084e207f882168b11137f27d9647fa0d35525e: run37270448875/job111636119122, log letto:59test root PASS/0skip (11+7+8+21+11+1), inclusi ownership10006/636;5wrapper bash-n/parity PASS. Docker reale e Docker29.8.1/containerd:1+1 PASS/0skip, job111636119006/111636119218. Al checkpoint5dei7workflow PR returned completed/success,2in corso; nessuna failure osservata. Non attribuire queste prove a commit documentali successivi.

Handoff§7.4: «Se serve lettura privata/conferimento nuovo, chiedere scope concreto dopo preparazione.» Il conferimento §43 autorizzava bytes immagini e non queste2TLS+2MAC. Pertanto chiedere solo lo scope §44 quando codice e CI sono pronti; nessun comando VPS consegnato/eseguito prima. Nessun rollback target necessario per lettura. Su BLOCKED preservare output redatto e diagnosticare senza replay automatico o ampliamento dello scope.

Documentazione OpenSSL ufficiale: https://docs.openssl.org/master/man1/openssl-verify/
