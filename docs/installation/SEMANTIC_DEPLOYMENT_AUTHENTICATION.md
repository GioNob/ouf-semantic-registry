# Verifica detached delle evidenze deployment e package sorgenti v5

## Stato

§26 ESEGUITO/PASS secondo l'output operatore: OpenSSL 3.5.7 target, vettore pubblico positivo e due negativi PASS, custody 18 sorgenti v4 PASS. Il nuovo verificatore non è installato sul VPS e non fa parte del package v4 immutabile. Il §27 porta soltanto 20 sorgenti in un nuovo package privato v5; **NON ESEGUITO**. Nessuna key/policy, firma, authority o startup di produzione è stata creata.

Gateway sorgenti `d27bf59f72470828c961d1df25d7588878b477ca`: `tools/semantic_provider_deployment_authentication.py`, `scripts/stage_semantic_authenticated_deployment_package.py`, due nuovi moduli test e workflow pertinente. I sorgenti legacy, i loro schemi/closure e i vecchi snapshot restano invariati. [Comando §27](../handoffs/commands/OUF_STAGE_AUTHENTICATED_DEPLOYMENT_PACKAGE_V5_2026-10-04.sh).

## Contratto del verificatore

`DetachedAuthenticator(policy_binding, signature_directory, openssl_binding, clock)` implementa il callback richiesto da `validate_intent/validate_final`. Non emette firme, non genera chiavi, non fa chiamate IAM/DNS/provider, non ispeziona immagini e non esegue container. Non esiste una policy/key/issuer predefinita.

I binding richiedono path assoluto e SHA256 esatto. La policy root-owned 0600, senza symlink/hardlink, è limitata a 64KiB; la directory firme è root-owned 0700 e i file 0600. Policy e signature sono rilette dopo la verifica e confrontate; modifiche, revoca, scadenza o clock regressivo negano l'autenticazione. Il binario OpenSSL è root-owned, eseguibile, non scrivibile da gruppo/altri e hash-pinned prima/dopo la chiamata. Non si passa alcuna configurazione OpenSSL d'ambiente del chiamante; stdout/stderr sono soppressi e timeout native 2s.

Policy schema `ouf.semantic-deployment-trust-policy.v1`: installationRef/entityRef e 1–32 key mandate espliciti. Ogni key contiene keyRef, issuerRef, roles, publicKey Ed25519 raw 32 bytes in hex, notBefore/expiresAt interi e state ACTIVE/REVOKED. I ruoli ammessi sono DEPLOYMENT_INTENT, CREATION_ATTESTATION e FINAL_DEPLOYMENT_APPROVAL. L'integrazione autorizzata deve provisionare questi trust anchor; root ownership/hash **da soli** non attestano chi abbia conferito il mandato. Chiavi scadute/revocate/estranee o senza quel ruolo non vengono usate. Un cambio di policy/hash richiede riconfigurazione esplicita, non auto-adoption.

Signature file: `<sha256(payload)>.<ROLE>.json`, massimo 4096 bytes. Campi esatti: schema=`ouf.semantic-deployment-detached-signature.v1`, algorithm=Ed25519, keyRef, role, issuerRef, installationRef, entityRef, payloadHash, signature (64 bytes hex). Nessuna selezione di algoritmo/issuer non provisionato e nessun percorso fornito dal payload.

La firma copre il frame:

`b'OUF-DEPLOYMENT-EVIDENCE\\x00V1\\x00' + uint32be(len(header)) + header + uint32be(len(payload)) + payload`

Header è il record senza signature, JSON ASCII sorted keys/separators compatti; payload sono gli **esatti bytes** esistenti, max128KiB. Header lega algoritmo, key, ruolo, issuer, installazione/Ente e payload hash. Il ruolo non può essere cambiato anche se l'issuer usa la stessa key per intent e approval. JSON duplicato/nonfinite, ruoli non ammessi, tipi e binding non validi sono negati. `signing_bytes` descrive il frame pubblico; non firma.

La verifica native usa [OpenSSL pkeyutl](https://docs.openssl.org/3.5/man1/openssl-pkeyutl/), Ed25519 pure, `-verify -pubin -rawin`, con input piccoli di dimensione nota e file temporanei privati rimossi alla fine. L'hash del binario non attesta tutta la closure delle librerie/provider OS. Readback bounded non è snapshot atomico e non esclude un root esterno al protocollo. Writers cooperanti di revoca e consumo devono usare il common lock nell'integrazione; questo modulo non acquisisce un nuovo lock né sostituisce il journal consumer.

## Verifiche e limiti

CI sull'esatto head: 38/38 completed/success, con log push/PR verificati (63 unit/contract/package, 2 native admission e 5 Docker).

63 test pertinenti locali PASS: 13 nuovi authentication test e 2 source-package v5 test. Le firme positive/negative sono verificate realmente da OpenSSL, con chiavi temporanee **esclusivamente nelle fixture CI/locali**. Test dell'intero `validate_final` per i tre ruoli; scope/role relabelling, altered payload/signature, policy drift/revoca durante verifica, scadenza tardiva, signature drift, policy assente/ruolo non concesso, limiti/permessi/symlink, algorithm/hash sconosciuti, timeout e backend drift. I test v5 provano 20 sorgenti, plan/apply/verify, diniego replay/drift/missing source e compilation senza eseguire il body del verificatore. Nessuna fixture/private key viene inclusa nei 20 file del package.

Una verifica positiva autentica i bytes rispetto a una key/mandato provisionati: non prova la veridicità di full creation acceptance, non dà authority applicativa IAM, non supera i controlli live guard/lease e non autorizza avvio. Restano da implementare/provisionare broker, issuer e attestor reali, acceptance completa dell'immagine/OCI/rootfs, source-sealing delle nuove closure e late verification nel driver/common lock. Il callback reale è integrato con il protocollo nei test; **adapter/preparer/driver di produzione non sono stati dichiarati migrati a questo verificatore**.

## Next step VPS

§27 solo nuovo package `ouf.semantic-authenticated-deployment-source-package.v5`; compile/hash/receipt. signatureVerifierInstalled/trustPolicyProvisioned/externalProducerInstalled/runtimeRegistered/startAuthorized=false, keysGenerated/signaturesIssued/providerCalls=0, regole/unit/container invariati. Le source v4 originali vengono copiate, non cambiate. PASS dello staging non è autenticazione del deployment reale.

Dopo il §27, implementare il broker produttivo e il collegamento all'attestazione reale; mandato/key provisioning richiedono binding espliciti della singola installazione. Nessun merge, reset/replay dei journal o registrazione/start impliciti. [Collegamento verificato alla filiera MCP → UDP e PET](../sprints/OUF_FILE_TO_UDP_PROVIDER_DEPENDENCY_2026-10-04.md).
