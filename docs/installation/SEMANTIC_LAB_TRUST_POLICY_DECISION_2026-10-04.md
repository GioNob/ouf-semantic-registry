# Proposta di policy locale di verifica per OUF lab

**STATO: PREPARAZIONE PRIVATA AUTORIZZATA, NON MATERIALIZZATA SUL VPS.** Utente autorizzo4ottobre18:58:29, [scope registrato](../handoffs/receipts/SEMANTIC_PRIVATE_TRUST_POLICY_AUTHORIZED_2026-10-04_OPERATOR.json), [implementazione/§38](SEMANTIC_PRIVATE_TRUST_POLICY_PREPARATION.md). Il conferimento35 riguardava soltanto le due chiavi private/bozza inattiva ed è completato al36. Questa è una nuova decisione circoscritta; non richiedere di nuovo la generazione delle chiavi.

## Binding reviewable

Installation `ouf-lab-netcup-01`, entity `ouf-lab`. Custody36 `/etc/ouf/deploy-snapshots/semantic-authority-provisioning-20261004-164654`, receiptHash `a134c4c8e8487860e6a8ed3a672520935a5de753d02507c4005a0475570b2d49`, draftHash `a9e5bdbef01c391c216e23e7b99c9e9ed3d6e3a92da56e8e1e9d7b2ca91b040c`. Queste coppie reali sono verificate sul VPS dal helper, non rigenerate o copiate; i valori publicKey vanno letti privatamente dal draft sigillato e confrontati con i DER. Non sono stati ricevuti nella chat e non vengono inventati. Date90giorni già proposte nel draft, da riusare esattamente senza rinnovarle al momento del provisioning; drift/scadenza/clock bloccano.

| Grant della policy proposta | issuerRef | keyRef | Ruoli esatti |
| --- | --- | --- | --- |
| Installer locale | `ouf-lab-infrastructure-installer` | `ouf-lab-installer-ed25519-1` | DEPLOYMENT_INTENT, FINAL_DEPLOYMENT_APPROVAL |
| Attestor locale al nodo | `ouf-lab-node-attestor` | `ouf-lab-attestor-ed25519-1` | CREATION_ATTESTATION |

Proposta: preparare in **nuovo snapshot privato** una policy con schema operativo `ouf.semantic-deployment-trust-policy.v1`, installationRef/entityRef esatti e due grant con keyRef/issuerRef/roles/publicKey/notBefore/expiresAt/state ACTIVE. ACTIVE indica chiavi ammesse per verificare i ruoli nella policy proposta, non approvazione di un deployment o start. Tutte le publicKey/date derivano dal draft verificato, non da nomi host, IAM, chiavi TLS o placeholder. Il parser operativo deve accettare la policy e rifiutare grant con ruolo/binding/validità alterati.

## Scope del conferimento ricevuto

Autorizzare **solo preparazione privata della policy dei tre ruoli sopra**, verificata con il contratto vigente e collegata per hash alla custody36 e al dossier34. Questo conferimento rende autorizzata la selezione delle chiavi/ruoli nella policy da preparare. Non autorizza emissione di firme operative o mandati, installation di producer/broker, collegamento della policy a processi/servizi/runtime, creazione/migrazione di container, modifica delle regole/unit, runtime registration, start, provider call o reboot. La policy privata è un artefatto di provisioning esplicito, non si attiva automaticamente in un consumer. Il grant finale non equivale a mandato finale per un candidato.

Prima del comando VPS: implementare builder/verify read-only delle chiavi, source e backend pinned, integrity/permission/custody checks, parser runtime reale, exclusive publication e receipt ultima, test pertinenti e CI. Non leggere o stampare PEM privati se per questo passo bastano draft/pubDER e receipt; non firmare evidenze reali o sintetiche aggiuntive senza necessità. No keygen, no overwrite/replay della custody36, nessun nuovo staging source-only.

## Accettazione e lavoro indipendente

§34 dà un dossier di due candidati e8 mount, non accettazione di immagini/contenuti/mutabilità, full OCI/rootfs/generazione live o namespace. Il mandato attestor deve essere costruito solo dopo revisione concreta del target e conferimento distinto; il Docker image ID o questo grant non sono provenance/full rootfs acceptance. Configurazione issuer intento, producer/broker e guard/lease rimangono lavori separati. Mandati transazionali massimi300s, quindi non emetterli ora per un avvio futuro.

Politica per-Ente autonoma, non multitenant centrale; chiave attestor sul nodo runtime anche per microservizi distribuiti. Su unico host ruoli e keypair sono separati, non si dichiara protezione da root amministratore. Ingestion interna MCP/THS/UDP resta aperta e distinta dai gate provider; ricerca esterna Semantic/Registry via Gateway, schema.gov.it default parametrizzato.

## Decisione ricevuta; istruzione storica

Approvare o negare il solo scope della policy privata dei tre ruoli. Nessun comando VPS fino a conferimento e implementazione/test/CI. La custodia35 non è stata estesa implicitamente: autorizzazione distinta37 ricevuta e registrata.
