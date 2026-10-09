# Verifica detached delle evidenze deployment e package sorgenti v5/v6

## Checkpoint corrente — §28 ESEGUITO/PASS; contratto e custodia producer implementati

§28: `/etc/ouf/deploy-snapshots/semantic-authenticated-runtime-package-20261004-094455`, source `f1996cca60e66f1807b88f126793a8edc1aed15f`; checksum wrapper +22 sorgenti e plan/apply/verify PASS concordanti, Python3.13.5. Ricevuta operatore in `2a8a0bc82e93bd09a6f65e7645381e1951b6bff1`, CI documentale13/13. Nessun accesso VPS indipendente o digest della receipt target. Nessun replay del §28.

Nuovo codice Gateway `93e1c845d26d339af6a07acb0e588b2532d2a4a7`: `LocalEvidenceProducer` invoca soltanto un producer Python locale con interprete/source/configurazione esplicitamente pinned; richieste esatte CREATION_ATTESTATION/FINAL_DEPLOYMENT_APPROVAL, preflight mandato attivo, I/O limitati, stderr soppresso, deadline condivisa con la verifica. Due firme reali: record e manifest che lega requestHash/recordHash/hash dell'envelope canonico. Un hash di richiesta non firmato non è accettato come legame. L'autenticatore espone anche verifica detached in memoria, conservando le verifiche file legacy.

`ProducerEmission` richiede un journal UNUSED esplicitamente provisionato e il lock comune già esistente: claim fsync ISSUING prima dell'invocazione, risultato firmato salvato O_EXCL/0600 con readback e fsync directory, poi ISSUED con resultHash. Timeout/esito sconosciuto resta ISSUING; nessun retry/reset automatico. File risultato estraneo è preservato e blocca prima dell'emissione. Due processi concorrenti non emettono due volte sullo stesso claim.

**Validazione:** 99 test locali PASS, di cui17 nuovi producer test: processo reale +Ed25519, catena a tre ruoli del protocollo esistente, replay di risposta su richiesta differente, firma/mandato/scope/source drift, modifica configurazione durante processo, limiti/output flood/hang e diagnostica redatta, deadline unica, fsync/custodia/claim incerto e concorrenza con due processi. Chiavi effimere solo fixture. [CI sull'esatto commit](https://github.com/GioNob/ouf-api-gateway/commit/93e1c845d26d339af6a07acb0e588b2532d2a4a7/checks): verificare i check di questo head, senza trasferire il PASS di un commit precedente.

**Limite e prossimo passo preciso:** trasporto e custodia del producer sono implementati/testati, ma il broker produttivo e il collegamento di questi componenti al bootstrap operativo non sono dichiarati completi. Comporre il broker con claim per i ruoli, full attestation valida prima della richiesta di approval, pubblicazione/custodia del request-binding e delle tre evidenze, quindi READY del consumer esistente e preparer3/driver5. Nessun approver o attestor reale è provisionato; non confondere il fixture echo/signature CI con full image/OCI/rootfs acceptance. Profilo e mandato dell'Ente, keys/policy/producer reali e gli altri gate rimangono aperti.

**Nessun nuovo intervento VPS in questo checkpoint:** v6 resta immutato; il nuovo modulo e la nuova API detached non sono copiati/installati sul target. Regole/unit/container/runtime e start non cambiano. Nessun merge/replay/emissione/keygen target. Installazioni indipendenti per Ente; servizi co-locati o distribuiti; Semantic/Registry discovery esterna tramite Gateway (default schema.gov.it parametrizzabile), MCP/chatbot propone e THS governa adozione/attivazione. La prova file→mapping→ingestion→UDP resta aperta.


## Checkpoint storico — ricevuta §28, prima del contratto producer

Output operatore del 4 ottobre 2026: `/etc/ouf/deploy-snapshots/semantic-authenticated-runtime-package-20261004-094455`, schema `ouf.semantic-authenticated-runtime-source-package.v6`, source `f1996cca60e66f1807b88f126793a8edc1aed15f`, Python3.13.5. Checksum wrapper +22 sorgenti OK; plan/apply/verify PASS con tre receipt concordanti. [Ricevuta operatore](https://github.com/GioNob/ouf-semantic-registry/blob/codex/r4a-smoke-semantic-inventory/docs/handoffs/receipts/SEMANTIC_AUTHENTICATED_RUNTIME_PACKAGE_V6_2026-10-04_OPERATOR.json). Evidenza allegata, non accesso VPS indipendente; digest del file receipt sul VPS non fornito.

adapter/preparer/verifier/producer/runtime non installati o registrati; trustPolicyProvisioned/startAuthorized=false, keysGenerated/signaturesIssued/providerCalls=0; regole/unità/container invariati. trustedToolsAvailable, incluso OpenSSL, è metadata, non prova di verifica crypto o autorità sul target. §28 completato: nessun replay. I commit precedenti e i package v5/v6 restano immutabili.

**Prossimo lavoro indipendente:** definire e implementare il contratto del producer locale per richieste tipizzate di CREATION_ATTESTATION e FINAL_DEPLOYMENT_APPROVAL, con eseguibile/configurazione pinned, limiti/deadline e verifica delle firme restituite; collegarlo poi al broker senza generare mandati, chiavi o approval implicite. La firma autentica il mandato provisionato, non dimostra da sola la veridicità della full image/OCI/rootfs acceptance. Il mandato reale della singola installazione e gli altri gate del handoff restano aperti.


## Checkpoint storico — driver collegato, prima dell'esecuzione §28

Gateway `f1996cca60e66f1807b88f126793a8edc1aed15f`: **adapter v4 → preparer v3 → driver v5** richiedono esplicitamente riverifica Ed25519 dei tre ruoli. Le nuove closure sigillate contengono 16 file per il preparer e 15 per il driver; nessun fallback al driver precedente nel percorso adapter v4. I vecchi schemi rimangono compatibili per gli snapshot già creati, senza migrazione implicita.

**Budget condiviso:** nel driver firme, hash/riletture e backend nativo condividono la stessa deadline monotonic `budgetSeconds` (1–5s), senza reset tra riverifiche prima/dopo fsync. Nel preparer il verificatore condivide la deadline complessiva di preparazione (18s), oltre ai budget dei worker nativi. Timeout/scadenza/revoca prima del claim conserva READY; dopo il claim conserva STARTING senza FIFO/replay automatico. Rollback di risorse possedute e generazione morta non richiede una firma ancora valida.

**Verifiche sull'esatto commit:** 82 test locali PASS; CI Gateway **38/38 completed/success**. Log push e PR: **82 test +2 native admission**, Docker **6 test PASS**, inclusa prova reale adapter4/preparer3/driver5 con chiavi Ed25519 distinte e temporanee solo CI. Lease drift e firma alterata negano l'applicazione; firme valide consentono il marker del solo fixture. Nel negativo della firma Docker elimina il candidato fallito e il rollback porta preexec a ROLLED_BACK/admission CLEANED, mentre consumption resta READY; questo esito è verificato, non un reset. Sorgenti di tutti i 22 file del prossimo package riletti dal commit e hash confrontati.

**Ultima evidenza VPS resta §27 ESEGUITO/PASS**, package v5 `/etc/ouf/deploy-snapshots/semantic-authenticated-deployment-package-20261004-083518`, source `6697029e3efa03f9090bd7be13aab86784749731`. Nuovo codice provato in CI; non ancora copiato o installato sul target.

**Intervento §28 ESEGUITO/PASS, registro storico**, soltanto nuovo source package `ouf.semantic-authenticated-runtime-source-package.v6`: 22 sorgenti privati, checksum +plan/apply/verify. [Comando §28](https://github.com/GioNob/ouf-semantic-registry/blob/codex/r4a-smoke-semantic-inventory/docs/handoffs/commands/OUF_STAGE_AUTHENTICATED_RUNTIME_PACKAGE_V6_2026-10-04.sh) e [contratto operativo](https://github.com/GioNob/ouf-semantic-registry/blob/codex/r4a-smoke-semantic-inventory/docs/installation/SEMANTIC_AUTHENTICATED_RUNTIME_DRIVER.md). Nessuna chiave/policy/mandato generato, nessuna firma emessa, nessun runtime registrato, nessun container o regola/unità cambiato. Questo staging non è readiness o release acceptance. Dopo l'output §28 registrare ricevuta e root esatti, senza replay, poi completare gli elementi produttivi indipendenti prima di richiedere i binding di autorità indispensabili.

**Restano aperti:** broker/issuer/attestor produttivi con mandato esplicito della singola installazione; full image/OCI/rootfs creation acceptance; provisioning trust/policy/chiavi reali; snapshot atomico, enforcement/binding IPv6/spoof, OIDC/purpose/TLS/revocation admission, ciclo lease attivo/guard e reboot reale. Le prove CI di questo percorso non chiudono questi gate né autorizzano start/merge/replay. Ogni Ente è un'installazione indipendente, con servizi co-locati o distribuiti. Semantic/Registry governa discovery esterna tramite Gateway (default schema.gov.it parametrizzabile); MCP/chatbot propone, THS governa adozione/attivazione. Il ramo provider non sostituisce la prova file→mapping→ingestion→UDP.


## Stato

§26 ESEGUITO/PASS secondo l'output operatore: OpenSSL 3.5.7 target, vettore pubblico positivo e due negativi PASS, custody 18 sorgenti v4 PASS. Il nuovo verificatore non è installato sul VPS e non fa parte del package v4 immutabile. Il §27 porta soltanto 20 sorgenti in un nuovo package privato v5; **ESEGUITO/PASS il 4 ottobre 2026** in `/etc/ouf/deploy-snapshots/semantic-authenticated-deployment-package-20261004-083518`, 20 checksum OK e plan/apply/verify PASS. Nessuna key/policy, firma, authority o startup di produzione è stata creata.

Gateway sorgenti `6697029e3efa03f9090bd7be13aab86784749731`: `tools/semantic_provider_deployment_authentication.py`, `scripts/stage_semantic_authenticated_deployment_package.py`, due nuovi moduli test e workflow pertinente. I sorgenti legacy, i loro schemi/closure e i vecchi snapshot restano invariati. [Comando §27](../handoffs/commands/OUF_STAGE_AUTHENTICATED_DEPLOYMENT_PACKAGE_V5_2026-10-04.sh).

## Contratto del verificatore

`DetachedAuthenticator(policy_binding, signature_directory, openssl_binding, clock)` implementa il callback richiesto da `validate_intent/validate_final`. Non emette firme, non genera chiavi, non fa chiamate IAM/DNS/provider, non ispeziona immagini e non esegue container. Non esiste una policy/key/issuer predefinita.

I binding policy richiedono path assoluto e SHA256 esatto; il binding OpenSSL richiede anche la versione attesa (`path`, `sha256`, `version`), misurata dal §26. Hash e risposta `openssl version` devono coincidere; un eseguibile root-owned che restituisce solo zero o una versione diversa è negato. La policy root-owned 0600, senza symlink/hardlink, è limitata a 64KiB; la directory firme è root-owned 0700 e i file 0600. Policy e signature sono rilette dopo la verifica e confrontate; modifiche, revoca, scadenza o clock regressivo negano l'autenticazione. Il binario OpenSSL è root-owned, eseguibile, non scrivibile da gruppo/altri e hash-pinned prima/dopo la chiamata. Non si passa alcuna configurazione OpenSSL d'ambiente del chiamante; stdout/stderr sono soppressi e timeout di 2s per comando native (versione e verifica).

Policy schema `ouf.semantic-deployment-trust-policy.v1`: installationRef/entityRef e 1–32 key mandate espliciti. Ogni key contiene keyRef, issuerRef, roles, publicKey Ed25519 raw 32 bytes in hex, notBefore/expiresAt interi e state ACTIVE/REVOKED. I ruoli ammessi sono DEPLOYMENT_INTENT, CREATION_ATTESTATION e FINAL_DEPLOYMENT_APPROVAL. L'integrazione autorizzata deve provisionare questi trust anchor; root ownership/hash **da soli** non attestano chi abbia conferito il mandato. Chiavi scadute/revocate/estranee o senza quel ruolo non vengono usate. Un cambio di policy/hash richiede riconfigurazione esplicita, non auto-adoption.

Signature file: `<sha256(payload)>.<ROLE>.json`, massimo 4096 bytes. Campi esatti: schema=`ouf.semantic-deployment-detached-signature.v1`, algorithm=Ed25519, keyRef, role, issuerRef, installationRef, entityRef, payloadHash, signature (64 bytes hex). Nessuna selezione di algoritmo/issuer non provisionato e nessun percorso fornito dal payload.

La firma copre il frame:

`b'OUF-DEPLOYMENT-EVIDENCE\\x00V1\\x00' + uint32be(len(header)) + header + uint32be(len(payload)) + payload`

Header è il record senza signature, JSON ASCII sorted keys/separators compatti; payload sono gli **esatti bytes** esistenti, max128KiB. Header lega algoritmo, key, ruolo, issuer, installazione/Ente e payload hash. Il ruolo non può essere cambiato anche se l'issuer usa la stessa key per intent e approval. JSON duplicato/nonfinite, ruoli non ammessi, tipi e binding non validi sono negati. `signing_bytes` descrive il frame pubblico; non firma.

La verifica native usa [OpenSSL pkeyutl](https://docs.openssl.org/3.5/man1/openssl-pkeyutl/), Ed25519 pure, `-verify -pubin -rawin`, con input piccoli di dimensione nota e file temporanei privati rimossi alla fine. L'hash del binario non attesta tutta la closure delle librerie/provider OS. Readback bounded non è snapshot atomico e non esclude un root esterno al protocollo. Writers cooperanti di revoca e consumo devono usare il common lock nell'integrazione; questo modulo non acquisisce un nuovo lock né sostituisce il journal consumer.

## Verifiche storiche del package v5 e limiti

CI sull'esatto head: 38/38 completed/success, con log push/PR verificati (64 unit/contract/package, 2 native admission e 5 Docker).

64 test pertinenti locali PASS: 14 nuovi authentication test e 2 source-package v5 test. Le firme positive/negative sono verificate realmente da OpenSSL, con chiavi temporanee **esclusivamente nelle fixture CI/locali**. Test dell'intero `validate_final` per i tre ruoli; scope/role relabelling, altered payload/signature, policy drift/revoca durante verifica, scadenza tardiva, signature drift, policy assente/ruolo non concesso, limiti/permessi/symlink, algorithm/hash sconosciuti, timeout, backend drift, eseguibile no-op e versione divergente. I test v5 provano 20 sorgenti, plan/apply/verify, diniego replay/drift/missing source e compilation senza eseguire il body del verificatore. Nessuna fixture/private key viene inclusa nei 20 file del package.

Una verifica positiva autentica i bytes rispetto a una key/mandato provisionati: non prova la veridicità di full creation acceptance, non dà authority applicativa IAM, non supera i controlli live guard/lease e non autorizza avvio. Restano da implementare/provisionare broker, issuer e attestor reali, acceptance completa dell'immagine/OCI/rootfs, source-sealing delle nuove closure e late verification nel driver/common lock. Il callback reale è integrato con il protocollo nei test; **adapter/preparer/driver di produzione non sono stati dichiarati migrati a questo verificatore**.

## Registro storico §27

§27 solo nuovo package `ouf.semantic-authenticated-deployment-source-package.v5`; compile/hash/receipt. signatureVerifierInstalled/trustPolicyProvisioned/externalProducerInstalled/runtimeRegistered/startAuthorized=false, keysGenerated/signaturesIssued/providerCalls=0, regole/unit/container invariati. Le source v4 originali vengono copiate, non cambiate. PASS dello staging non è autenticazione del deployment reale.

§27 completato; non ripetere. Ora implementare il broker produttivo e il collegamento all'attestazione reale; mandato/key provisioning richiedono binding espliciti della singola installazione. Nessun merge, reset/replay dei journal o registrazione/start impliciti. [Collegamento verificato alla filiera MCP → UDP e PET](../sprints/OUF_FILE_TO_UDP_PROVIDER_DEPENDENCY_2026-10-04.md).
