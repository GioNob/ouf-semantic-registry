# Inventario read-only del backend di verifica deployment (§26)

Stato VPS: **ESEGUITO/PASS il 4 ottobre 2026**. Backend reale OpenSSL 3.5.7, verifica positiva e negative PASS; custody 18 sorgenti PASS. Root `semantic-deployment-trust-backend-inventory-20261004-080455`. Nessuna authority/start/atomicità dimostrata. Il §25 è ESEGUITO/PASS secondo l'output dell'operatore: `/etc/ouf/deploy-snapshots/semantic-deployment-package-20261004-072744`, source commit `cc161b94c1af014403dabd113200d3180f02089d`, 18 checksum OK, plan/apply/verify PASS. La ricevuta è conservata in [operator attestation](../handoffs/receipts/SEMANTIC_DEPLOYMENT_PACKAGE_V4_2026-10-04_OPERATOR.json); non è un'attestazione indipendente del VPS.

Il registro storico è [il comando §26](../handoffs/commands/OUF_INVENTORY_DEPLOYMENT_TRUST_BACKEND_2026-10-04.sh). Scarica due file immutabili, verifica entrambi i SHA256 e li conserva in una nuova directory privata. Legge la ricevuta v4 e ricalcola i 18 hash senza importare/eseguire i moduli del pacchetto. Confronta i contenuti esatti con l'attestazione dell'operatore. Input symlink, permessi non privati, hash divergenti o metadati variati bloccano il controllo.

Il probe usa esclusivamente chiave **pubblica**, messaggio e firma del TEST 2 di [RFC 8032 §7.1](https://www.rfc-editor.org/rfc/rfc8032.html#section-7.1). Invoca `/usr/bin/openssl version` e `pkeyutl -verify -pubin -rawin`: verifica la firma valida e due casi negativi (messaggio modificato, firma modificata). Usa piccoli file pubblici temporanei rimossi alla fine, perché [OpenSSL Ed25519 richiede input di dimensione nota](https://docs.openssl.org/3.0/man1/openssl-pkeyutl/). Nessun accesso a chiavi private, generazione di chiavi o emissione di firme. Il binario risolto deve essere di root, eseguibile, non scrivibile da gruppo/altri; hash, versione e risultati sono confrontati su due letture.

La configurazione riguarda **una installazione autonoma per Ente**, con servizi distribuiti o co-localizzati. OpenSSL/Ed25519 è un candidato verificato per questa installazione, non un'autorità centrale, un nuovo servizio obbligatorio o una scelta globale imposta alle altre installazioni. L'inventario non concede mandato di firma e non modifica IAM/M2M A/B/C.

## Interpretazione e limiti

- `PASS` indica inventario completato. Se OpenSSL manca o non verifica il vettore, `ed25519VerificationProven=false`; non basta il PASS della raccolta.
- Per considerare disponibile questo backend servono `opensslAvailable=true`, `ed25519VerificationProven=true`, `alteredMessageRejected=true` e `alteredSignatureRejected=true`, oltre a custody e stabilità.
- `sourceCustodyVerified=true` riguarda il pacchetto v4. Non rivalida il guard host, non prova atomicità (`atomicSnapshotProven=false`), live namespace, immagine del candidato o accettazione creazione.
- L'hash riguarda il binario OpenSSL, non l'intera chiusura delle librerie/provider del sistema. Le prove dimostrano soltanto queste tre operazioni pubbliche sul backend effettivamente eseguito.
- `deploymentAuthorityProven=false`, `keyGenerationAuthorized=false`, `runtimeRegistrationAuthorized=false`, `startAuthorized=false`; provider/DNS/IAM calls zero. Nessuna regola, unità o container modificati.
- Restano da implementare produttori/autenticatore reali, provisioning di mandato e chiavi per Ente, attestazione completa della creazione e integrazione autorizzata sul VPS. Il broker sintetico di CI resta escluso dal pacchetto.
- Nessun merge, registrazione runtime, avvio, reboot o replay implicito. Ripetere il §25 non è necessario.

## Validazione del codice

Gateway `3c62e7a98957545623e3d3183e067d9c1bd4a6c8`: 48 test pertinenti passati localmente, inclusi 8 nuovi casi e un comando Python isolato reale con OpenSSL 3.0.13. I casi coprono verifica positiva/negativa, custody invariata, drift, permessi/symlink, JSON duplicato o booleani sostituiti da numeri, backend assente e binding della root. CI verifica la stessa suite con Python 3.13 e mantiene i 2 test native admission e i test Docker esistenti; esito sul commit finale: 38/38 controlli completed/success. Log push e PR riletti: 48 unit test, 2 native admission, 5 Docker. È passato anche un controllo locale con i 18 sorgenti effettivi: ciascun hash coincide con l'output VPS e il probe isolato completa verifica positiva e negative. Il comando §26 supera `bash -n`; i sorgenti pubblicati sono stati riletti e confrontati byte per byte.

L'output operatore del §26 è registrato nella ricevuta `SEMANTIC_DEPLOYMENT_TRUST_BACKEND_2026-10-04_OPERATOR.json`. Verificatore delle evidenze detached completato come sorgente; prossimo intervento §27 package privato v5. [Contratto aggiornato](SEMANTIC_DEPLOYMENT_AUTHENTICATION.md). Nessun replay del §26. L'esito CI locale/remote non viene esteso al VPS.
