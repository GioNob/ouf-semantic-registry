# Decisione di authority per il laboratorio OUF — custodia chiavi approvata

**Stato: CUSTODIA CHIAVI/BOZZA INATTIVA APPROVATA; GENERAZIONE VPS NON ESEGUITA.** Conferma utente confermo4ottobre2026 17:57:37 Europe/Rome, limitata alla proposta nel commit a8e6caf. Nessuna firma deployment, policy ACTIVE, registrazione runtime o start conferiti. [Registrazione del conferimento](../handoffs/receipts/SEMANTIC_AUTHORITY_KEY_CUSTODY_AUTHORIZED_2026-10-04_OPERATOR.json). [Implementazione e prossimo comando §36](SEMANTIC_AUTHORITY_KEY_CUSTODY.md). Non è trust policy, mandato firmato o configurazione operativa. Questo documento rende reviewable la sola scelta di identità e custodia chiavi per la prossima fase. Nessuna nuova chiave è stata generata.

## Evidenza disponibile

§34 ESEGUITO/PASS, root `/etc/ouf/deploy-snapshots/semantic-target-acceptance-inventory-20261004-151023/prepared`. Dossier `a37f22635035ab8543a4654def5cd6a6f4fe45fd1affc0ff10ccc3c19f03085c`, piano inerte `31492d13db05b46252215bb4bde815712bd55a1e245aff25408350328fcb7093`, receipt package v8 `f06c4b6ea2a7c05e008db3e615e35f475d44824b2073ff2d5f451c55dbce2850`. Due candidati mai avviati, otto mount, zero provider/DNS/IAM/chiavi/firme; dati Env e contenuti mount non letti. Output operatore, non ispezione indipendente. Non è accettazione completa di immagini/volumi, full OCI/rootfs/live-generation, authority o start.

## Proposta approvata per questa installazione

| Binding | Valore proposto | Stato |
| --- | --- | --- |
| installationRef | `ouf-lab-netcup-01` | Identificatore del laboratorio già documentato; il futuro helper dovrà confrontarlo con il dossier e bloccare drift. |
| entityRef | `ouf-lab` | Identificatore di laboratorio proposto, confermato dal titolare per il laboratorio; non è dedotto da host, IAM o installationRef. |
| Installer issuerRef | `ouf-lab-infrastructure-installer` | Soggetto proposto per intento e approvazione finale; mandato da conferire esplicitamente. |
| Attestor issuerRef | `ouf-lab-node-attestor` | Soggetto locale al nodo runtime, separato dall'installer; non authority centrale. |
| Installer keyRef | `ouf-lab-installer-ed25519-1` | Nuova coppia Ed25519 proposta; non riutilizza chiavi TLS/IAM/receipt. |
| Attestor keyRef | `ouf-lab-attestor-ed25519-1` | Seconda coppia distinta, locale al nodo; non condivisa con altri Enti. |
| Custodia | Nuovo root sotto `/etc/ouf/deploy-snapshots/semantic-authority-provisioning-TIMESTAMP` | Directory root:root0700, chiavi root:root0600, no symlink/hardlink/overwrite, nessuna stampa/esportazione di private key. |
| Durata proposta dei futuri grant | 90 giorni da UTC della futura generazione | Intervallo concreto da registrare; non crea grant ACTIVE adesso. Finestra dei mandati transazionali resta al massimo300s. |

Un Ente, una installazione indipendente. La separazione dei due ruoli è funzionale e crittografica; su un unico host root può accedere a entrambe le chiavi, quindi non viene dichiarata segregazione amministrativa forte. Su nodi distinti la chiave attestor deve restare sul rispettivo nodo runtime; non copiare la chiave di questo laboratorio come default di prodotto. Valori della tabella sono lab-specific e non default delle installazioni future.

## Conferimento ricevuto e limiti

La decisione ricevuta riguarda **soltanto** approvazione delle identità proposte e autorizzazione alla futura generazione/custodia privata delle due coppie Ed25519 e alla preparazione di una bozza di policy non attivata. Il passo VPS verrà fornito soltanto dopo conferimento e implementazione verificata. Niente firma di intenti/attestazioni/approval, emissione mandati, policy ACTIVE, installer/attestor installati, configurazione Docker, registrazione runtime, modifica container/regole/unit, start o reboot sono inclusi.

La preparazione delle chiavi non equivale a conferimento del ruolo di firma. La bozza rimane in schema distinto DRAFT_NOT_AUTHORIZED, non una policy operativa popolata da null o default permissivi. Una policy futura dovrà avere publicKey reale64hex, keyRef/issuerRef/ruoli esatti, intervalli verificati e stato conferito esplicitamente. Non trasformare la risposta su queste chiavi in un mandato finale di avvio.

## Lavoro successivo dopo il conferimento

Implementare e validare helper di provisioning privato: plan senza generazione; apply genera le sole due coppie autorizzate in nuovo root esclusivo, verifica corrispondenza public/private con OpenSSL pinned e roundtrip sintetico senza emettere evidenze di deployment; verify confronta custodia/hash/receipt e non rigenera. Privati mai su stdout/GitHub, input/output bounded, timeout, cleanup dei processi e no-overwrite dopo crash. Test reali di filesystem/Ed25519 e casi negativi, quindi CI verde e unico wrapper completo reviewable. Il test sintetico va distinto da qualunque firma di intento o attestation.

Restano indipendenti: revisione privata delle due immagini e otto mount e loro mutabilità; full OCI/rootfs/generazione; implementazione/configurazione effettiva dei producer e dell'intento; trust policy conferita; mandato di acceptance e poi mandato finale; registrazione/migrazione runtime; startup esplicito; active lease/revoca; snapshot atomico e reboot reale. Le CLI di signing custodite non conferiscono authority e non rappresentano da sole un issuer completo per tutti i tre ruoli.

## Istruzione storica per esprimere la decisione

Confermare `entityRef=ouf-lab` oppure fornire l'identificatore corretto. Confermare o sostituire i due issuerRef. Autorizzare esplicitamente oppure negare la sola futura generazione privata delle due coppie secondo questa proposta. Approvare il modello architetturale per-Ente già concordato non viene interpretato come questa autorizzazione.

Il prossimo passo non richiede un altro inventario o staging source-only: §34 e §31 non vanno ripetuti. Ingestion interna MCP→profilo→mapping DRAFT→THS→ACTIVE→Ingestion→UDP resta aperta; questo ramo serve la ricerca semantica esterna Semantic/Registry via Gateway, default schema.gov.it parametrizzabile. Nessun gate provider viene imposto come prerequisito universale dell'ingestion interna.
