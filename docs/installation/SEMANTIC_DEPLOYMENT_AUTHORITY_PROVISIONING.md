# Provisioning delle authority e dossier target per installazione indipendente

## Stato corrente —37 preparazione privata conferita,38 NON ESEGUITO

Utente autorizzo per sola policy privata di verifica sui keypair esistenti. [Procedura](SEMANTIC_PRIVATE_TRUST_POLICY_PREPARATION.md), [wrapper38](../handoffs/commands/OUF_PREPARE_TRUST_POLICY_2026-10-04.sh), SHA256 `1b3927170ba06722402050a25eb12d50bf3d5886ea443b5a1e5866770a573857`, Gateway `3bdedad3108112ee4c36e7cb8387aaf60912e97c` CI38/38SUCCESS/201unit+2native+2targetnative PASS. Grant ACTIVE nel file, consumerLinked/installed/roleSigning/start=false. Originali36/34/v8 preservati; noPEM read/keygen/signing. Date90giorni non rinnovate. Dopo output38 aggiornare tutti i checkpoint. Nessun altro conferimento per questa preparazione richiesto; emissione/consumer/runtime/start ancora esclusi.

## Checkpoint storico —36 PASS,37 allora pendente

Root `/etc/ouf/deploy-snapshots/semantic-authority-provisioning-20261004-164654`, draftHash `a9e5bdbef01c391c216e23e7b99c9e9ed3d6e3a92da56e8e1e9d7b2ca91b040c`, receiptHash `a134c4c8e8487860e6a8ed3a672520935a5de753d02507c4005a0475570b2d49`. [Evidenza operatore](../handoffs/receipts/SEMANTIC_AUTHORITY_KEY_CUSTODY_PASS_2026-10-04_OPERATOR.json), plan/apply/verify PASS,2chiavi presenti, verify keysGenerated/selfTestSignaturesIssued=0. Nessun ruolo firma/policy/start attivo. Non ripetere36 o rigenerare; la fonte dei byte eseguiti e hash è la receipt operatore. [Prossimo conferimento distinto](SEMANTIC_LAB_TRUST_POLICY_DECISION_2026-10-04.md): preparazione privata policy di verifica due grant/tre ruoli, senza firme/mandati o collegamento a consumer/runtime. Il35 è soddisfatto e non deve essere richiesto di nuovo.

## Stato storico — custodia approvata;36 allora NON ESEGUITO

Utente confermo approva identità lab e sola futura generazione di2 keypair/bozza inattiva. [Scope e implementazione](SEMANTIC_AUTHORITY_KEY_CUSTODY.md), [wrapper36 completo](../handoffs/commands/OUF_PROVISION_AUTHORITY_KEYS_2026-10-04.sh), SHA256 `14c506fc2468e0b6f40470d6b074aab318b0120813be4795172d4715bdaa4795`, Gateway `509a011cd920d9a9e9ece83a07e5b99ce05806a5`. plan/apply/verify nuovi, no-overwrite;2 firme selftest sintetiche,0 deployment signatures. Policy ACTIVE/ruolo firma/runtime/start non conferiti. §34 PASS e §31 v8 PASS preservati, non ripetere. Conferimento non è generazione eseguita né accettazione immagini/mount.

## Stato storico — §34 PASS; §35 allora pendente

Diagnostica e inventario PASS, `/etc/ouf/deploy-snapshots/semantic-target-acceptance-inventory-20261004-151023/prepared`,2 candidati mai avviati e8 mount. DossierHash `a37f22635035ab8543a4654def5cd6a6f4fe45fd1affc0ff10ccc3c19f03085c`, pianoHash `31492d13db05b46252215bb4bde815712bd55a1e245aff25408350328fcb7093`, packageReceiptHash `f06c4b6ea2a7c05e008db3e615e35f475d44824b2073ff2d5f451c55dbce2850`. Nessuna accettazione completa/authority/start, nessuna chiave o firma. [Receipt operatore](../handoffs/receipts/SEMANTIC_TARGET_ACCEPTANCE_PASS_2026-10-04_OPERATOR.json), non ispezione indipendente; hash inventory-receipt non fornito. Non ripetere §34/staging/recovery.

[Proposta concreta di conferimento](SEMANTIC_LAB_AUTHORITY_DECISION_2026-10-04.md): identità per laboratorio e futura generazione privata di2 chiavi Ed25519/bozza non attivata. Il modello per-Ente già approvato non conferisce questa authority. Nessun comando VPS nuovo fino alla decisione e alla verifica del provisioning. No firma deployment, policy ACTIVE, runtime registration o start inclusi. Gatewayd42a8 CI38/38 SUCCESS; wrapper eseguito documentif4eb446 CI13/13 SUCCESS.

## Stato storico — §33 BLOCKED; §34 allora NON ESEGUITO

Diagnostico operatore root20261004-145230: IMAGE_INSPECT / TARGET_ACCEPTANCE_INVENTORY_UNPROVEN. Nessuna receipt PASS o authority target. Gateway `d42a8c563a58ed041bf7b7a2921be975e93becf5` CI38/38 verde,169 unit+2 preparer native+2 target native PASS; nuovo [wrapper completo §34](../handoffs/commands/OUF_INVENTORY_TARGET_ACCEPTANCE_2026-10-04.sh) SHA256 `1fa92459ae358f3811ba234c837a0c3e8cffcde92b575372f5d073ae78f8833d`: diagnosi prima, inventario solo se PASS su nuovo root senza overwrite. §31 PASS preservato; non ripetere staging/recovery/§32/§33.

[Docker documenta l'omissione dei campi Config vuoti](https://docs.docker.com/engine/deprecated/#empty-nil-fields-in-image-config) e [la CLI usa fallback su mappa](https://github.com/docker/cli/blob/master/cli/command/inspect/inspector.go). Corretto accesso ai soli campi opzionali con regressione Go missingkey=error e Docker reale; obbligatori e vincoli volumi/startup preservati. Questo difetto è provato nei test; la causa del blocco sul VPS resta da confermare con §34. Locale10 PASS/2 native skip. Authority, accettazione effettiva di immagini/mount, runtime e start restano distinti e non conferiti.

## Stato storico — §32 BLOCKED; §33 allora pendente

Fotografia operatore conferma BLOCKED, non la causa né receipt PASS. L’inventario NON ESEGUITO descritto sotto è storico. Non ripetere il wrapper32 o cancellare output parziali. [§33 diagnostica](../handoffs/commands/OUF_DIAGNOSE_TARGET_ACCEPTANCE_2026-10-04.sh) usa --diagnose: stessi input target, nessuna pubblicazione di dossier/piano/receipt e codici CHECK/REASON costanti senza valori privati. Nuovo snapshot custodisce soltanto il helper; non modifica package/candidati. Anche PASS diagnostico non completa §32 o conferisce authority.

## Stato e obiettivo

Staging v8 completato sul root121542 tramite recovery §31 ESEGUITO/PASS. Le26 sorgenti restano al commit7ded9df; non ripetere staging o recovery. §32 originale ESEGUITO/BLOCKED; §34 corretto ESEGUITO/PASS misura i due candidati target e genera una bozza di provisioning locale. Non conferisce authority, genera chiavi/firme, registra runtime o avvia processi. [Comando completo](../handoffs/commands/OUF_INVENTORY_TARGET_ACCEPTANCE_2026-10-04.sh).

Ogni Ente ha un'installazione indipendente. Il riferimento entityRef non si deduce dall'host, dal nome dell'installazione o dall'utente Keycloak. La condivisione di host/subnet non conferisce fiducia: l'attestor resta locale al nodo runtime anche quando altri servizi sono su server/reti differenti. Non occorre una authority centrale o un servizio multitenant.

## Dossier privato e piano inerte

`inventory_semantic_target_acceptance.py` è standalone stdlib: non importa né esegue i producer custoditi. Verifica hash del manifest candidate, journal creation, manifest26 sorgenti e receipt v8; rilegge tutte26 sorgenti. Legge soltanto inspect Docker container/image/network con template selettivi. Verifica identità e never-started, etichette journal, startup selezionato, user, restrizioni host, DNS configurato, mount bind readonly/rprivate e indirizzi IPv4 configurati. Il runtime deve avere un nome valido; il dossier registra quello osservato, senza sostituirlo o registrarlo.

Due letture confrontate devono coincidere. Mount source: soltanto lstat e metadati degli antenati, senza aprire file/chiavi/env né enumerare contenuti di directory. Tipo file/directory, mode, owner, dev/inode, nlink, size, mtime/ctime vengono custoditi; symlink, file speciali e scrittura group/world bloccano. I proprietari dei file montati possono essere UID applicativi: gli antenati devono essere root-owned e non scrivibili group/world. Nessun permesso viene corretto.

Output privati root0600 nel nuovo snapshot700:

| File | Contenuto e uso |
| --- | --- |
| target-dossier.json | Identità candidate/immagini, layer digest dichiarati da Docker, configurazione selezionata, percorsi mount e loro metadati. Da consultare privatamente; command/paths non vengono pubblicati su stdout o GitHub. |
| authority-plan.json | Schema `ouf.semantic-deployment-authority-provisioning-plan.v1`, stato DRAFT_NOT_AUTHORIZED, tre ruoli con identità e chiavi non assegnate. **Non è una trust policy né configurazione operativa**. |
| inventory-receipt.json | Hash dei due file e della receipt v8, contatori/esito. Pubblicata per ultima dopo fsync/readback; unico marker di completamento. |

Il report pubblico stampa soltanto hash, conteggi e booleani, senza percorsi mount, command, configurazioni o credenziali. Nessuna lettura `.Config.Env` o contenuti di mount. Le risposte Docker sono limitate a128KiB/call e30s complessivi; due candidati, massimo32 mount/network ciascuno,256 layer/image; dossier aggregato massimo128KiB. stdout drenato con selector, stderr scartato e processo ucciso/raccolto su timeout/overflow. File privati readback128KiB e antisymlink/hardlink/metadata drift. Pubblicazione esclusiva, mai overwrite: evidenza parziale richiede riconciliazione, non reset o replay.

## Modello di fiducia da approvare

| Ruolo | Responsabilità | Evidenza necessaria |
| --- | --- | --- |
| DEPLOYMENT_INTENT | Autorità infrastrutturale installer: autorizza creazione per installation/entity/candidato/transazione specifici. | Intento firmato creation-only, vincoli deployment e binding trasporto/runtime. Non autorizza start. |
| CREATION_ATTESTATION | Attestor locale al nodo; verifica il mandato di accettazione e l'osservazione reale di OCI/rootfs/generazione/link prima di firmare. | Mandato di accettazione esplicito, completo OCI, rootfs seal osservato, gestione bind mount esterni. Nessuna auto-accettazione derivata dal Docker image ID. |
| FINAL_DEPLOYMENT_APPROVAL | Installer emette approval dopo attestazione valida e mandato finale distinto. | Mandato finale firmato e limitato a singola generazione/OCI/trasporto/runtime, start esplicito. |

Coerenza con contratto vigente: installer può detenere ruoli intento/finale; chiave e ruolo dell'attestor restano separati. La scelta di soggetti, publicKey/keyRef/issuerRef, validità, custodia, revoca e scope richiede autorità esplicita. Nessuna chiave esistente è promossa a authority perché presente sul disco. IAM applicativo non diventa authority infrastrutturale. Non leggere/riutilizzare chiavi TLS o di receipt come chiavi di deploy.

Policy operativa futura: schema `ouf.semantic-deployment-trust-policy.v1`; installationRef/entityRef esatti;1..32 grant con keyRef,issuerRef,roles,publicKey Ed25519 lowercasehex64,notBefore,expiresAt,state ACTIVE/REVOKED. La bozza nulla non è convertibile in policy ACTIVE senza conferimento esplicito. I mandati operativi sono validi al massimo300s e dentro la finestra dell'intento; non emetterli ora per un avvio futuro.

## Binding delle configurazioni da materializzare dopo l'inventario e il conferimento

| Componente | Schema operativo | Binding da risolvere |
| --- | --- | --- |
| Broker | ouf.semantic-deployment-broker.v1 | sourceRoot e closure esatta18 sorgenti, authorities5 identità, intento/policy/signatureDirectory/OpenSSL; producer attestor/approval pinned, preparerTemplate, candidateRoot e runtimeRootParent. |
| Attestor nodo | ouf.semantic-node-attestor.v1 | closure20 sorgenti, Python, authorities, intento, acceptanceMandatePath, policy/firme/OpenSSL, propria signingKeyBinding/keyRef; journal broker/emissione/claim, budget1..12s, runtime, antenati runtime/bundle, ip/nsenter, candidate network/transport/table e limiti rootfs. |
| Issuer installer | ouf.semantic-installer-approval-producer.v1 | closure18 sorgenti, Python, authorities, intento, attestationPath e approvalMandateBinding; policy/firme/OpenSSL, propria signingKeyBinding/keyRef, journal emissione/claim e budget1..12s. |
| Preparer | ouf.semantic-admission-preparer.v3 | Comandi e hash, candidate/kernel/DNS, common guard/lease lock e percorsi privati, namespace/rootfs osservati e protocollo autenticato. Produce il driver v5 soltanto dopo ammissione reale. |
| Adapter Docker | ouf.semantic-docker-runtime-adapter.v4 | Driver/broker e configurazioni pinned, registry/CID e runtime nativo. Registrazione e migrazione dei candidati esistenti richiedono intervento esplicito; runtime runc esistente non viene sostituito da questo inventario. |

La matrice è un progetto di configurazione, non JSON operativo con default permissivi. Gli hash delle closure derivano dalla receipt v8 verificata e vanno selezionati esattamente secondo i MODULES delle CLI; non includere indiscriminatamente tutti26 file. Le chiavi e i journal sono per installazione/nodo e transazione; il broker conserva lock comune guard/lease, oltre al lock per CID, evitando firma/start concorrenti e replay dopo crash. Nessun claim va cancellato per ritentare.

## Cosa resta da provare

PASS §34 è inventario per costruire un dossier di revisione. Non prova ambiente completo, provenance publisher, contenuto immutabile dei layer o dei volumi, full OCI, namespace/generazione live, rootfs seal, hook OCI, active lease lifecycle, snapshot atomico, reboot o release acceptance. I layer sono descriptor Docker, **non** sigillo dell'intero rootfs estratto. I bind mount possono contenere chiavi e dati mutabili: questo comando non li apre o sigilla. L'autorità deve approvare contenuti e mutabilità con vincoli espliciti. I candidati Docker created con runtime runc non danno da soli un bundle/generazione runc created; i mandati non vanno sintetizzati da metadati incompleti.

Output §34 registrato nei4 documenti e stato comando aggiornato: dossier privato disponibile, prossimo gate identità e conferimento circoscritto; non ripetere inventario. Preparare il provisioning reviewable prima di chiedere conferimento per generazione/firma/applicazione. Nessun nuovo staging source-only per simulare gates chiusi. Ingestion interna MCP→profilo→mapping DRAFT→THS→bundle ACTIVE→Ingestion→UDP resta aperta; Semantic/Registry ricerca via Gateway, schema.gov.it predefinito configurabile, chatbot/MCP propone e THS governa adozione/pubblicazione/attivazione.

## Validazione

9 test unit root con filesystem reale: nessun open dei mount, piano inerte, configurazioni unsafe, network/image/mount drift, letture diverse, symlink/FIFO/worldwrite, budget/overflow/exit, O_EXCL/fsync/readback e source/receipt drift. Prova Docker root dedicata:2 immagini/candidati fixture mai avviati, mount con segreto non letto, CLI reale con package v8 e ricevuta verificata, dossier/hash e no-overwrite del tentativo successivo. Nessun pull o provider; immagine fixture importata localmente. La suite generale non root salta le fixture root; il job root le esegue effettivamente. Stato CI e commit esatti nel checkpoint corrente.
