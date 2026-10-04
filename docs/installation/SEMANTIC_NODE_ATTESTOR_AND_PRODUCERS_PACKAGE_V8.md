# Attestor reale del nodo e package privato v8

## Stato verificato

Gateway `7ded9df0c74c6db919c7a68d4c75ab2c132dea53` (attestor introdotto in `b87f16bdde66c67137b356b411c09fe651d15f85`): CI38/38 SUCCESS senza rerun;151 test pertinenti,2 prove native del preparer e6 test Docker. Locale157 test,154PASS e3 prove Docker saltate. Il percorso Docker autenticato usa ora **attestor e issuer di produzione**: i log riportano REAL_NODE_ATTESTOR=true, REAL_INSTALLER_ISSUER=true, ROOTFS_DRIFT_NO_APPLICATION=true e CI_ACCEPTANCE_AUTHORITY_ONLY=true. Una modifica dell’immagine dopo il mandato viene respinta prima del claim del firmatario, senza approval o driver e senza processo applicativo.

Queste sono prove di CI, con immagine Busybox, due chiavi e mandati dedicati di CI. Non dimostrano authority, accettazione o avvio delle immagini reali sul VPS. Il comando di staging v8 descritto sotto è **NON ESEGUITO**. Lo staging §29 v7 resta ESEGUITO/PASS nella sua ricevuta operatore, senza replay.

## Responsabilità e autorità

`scripts/semantic_provider_node_attestor.py` carica una closure esatta di20 sorgenti prima di eseguire moduli. Riusa i helper privati di lettura/rilettura e claim dell’issuer; non ne invoca l’emissione di approval. `tools/semantic_provider_node_observation.py` legge immagine, OCI, stato runc e interfacce. `tools/semantic_provider_node_attestor.py` verifica mandato e osservazioni prima di firmare.

Ogni Ente ha un’installazione indipendente e le proprie authority esplicite. L’attestor opera sul nodo che possiede il runtime, anche se altri microservizi sono su reti/server diversi. Nessuna fiducia derivata dalla condivisione di host/subnet e nessun tenant centrale. Installer infrastrutturale, autorità di accettazione e IAM applicativo restano ruoli espliciti; non nasce un servizio centrale obbligatorio.

Il mandato `ouf.semantic-node-creation-acceptance-mandate.v1` deve essere già emesso da un’autorità di accettazione legittima e autenticato sotto CREATION_ATTESTATION della policy locale. La CLI non genera mandati o chiavi e non certifica autonomamente la provenienza commerciale dell’immagine. **Il provisioning e l’emissione del mandato di accettazione per le immagini target restano da realizzare/autorizzare.** La fixture che li crea in CI vive soltanto sotto tests/fixtures; non è inclusa nel package target.

## Mandato e osservazioni

| Mandato firmato | Verifica indipendente |
| --- | --- |
| issuerRef, installationRef, entityRef | Authority attestor e installazione/Ente configurati |
| intentHash, CID, transactionId, artifactHash, deploymentConstraintsHash | Uguaglianza con intento firmato e richiesta canonica |
| applicationHash | Hash canonico dell’intero documento OCI osservato, compresi process, root, mounts, linux, hooks e annotations |
| runtimeExecutableHash | Hash dell’eseguibile runc configurato, controllato prima/dopo la query |
| generation | PID, startTicks e inode del namespace osservati da /proc, coerenti con runtime created e richiesta |
| transportHash | Binding esatti di networkBindings/transport/tableName; MAC/IP, interfacce, veth peer e bridge verificati live |
| rootfsSeal | Sigillo dell’intero rootfs osservato, senza esclusioni implicite |
| issuedAt, expiresAt | Finestra valida, massimo300 secondi e contenuta nell’intento |
| state, attestationAuthorized, completeCreationAccepted | ACTIVE e booleani esattamente true |

Il sigillo `ouf.semantic-rootfs-seal.v1` riporta SHA256, numero di entry e byte di file letti. Include nomi e tipo di ogni entry, permessi, UID/GID, numero di hardlink, contenuto dei file regolari, xattrs di file/directory e destinazione dei symlink. I symlink sono sigillati come link e non seguiti; symlink con xattrs e file speciali vengono rifiutati. I timestamp non entrano nel sigillo, mentre vengono usati nei controlli di stabilità durante la lettura. Non accettare un sottoinsieme di file o un hash di argv come prova dell’immagine completa.

Traversal con dirfd/O_NOFOLLOW, lettura a blocchi e verifica fstat prima/dopo. Limiti espliciti: maxEntries1..100000, maxBytes1..8GiB, maxDepth1..64 e budget totale producer1..12 secondi. La somma delle entry enumerate ancora in coda è limitata: non si accumulano liste illimitate nelle directory annidate. Limiti o tempo insufficienti causano denial, senza approvazione parziale.

L’intero OCI vincola anche i descrittori dei mount esterni; il sigillo dell’immagine **non sigilla il contenuto delle sorgenti bind mount esterne**. L’autorità di accettazione deve approvare esplicitamente la loro mutabilità e i vincoli completi del documento OCI. Non presentare questa prova come immutabilità di tutti i volumi o verifica del contenuto di volumi dati.

## Ordine e concorrenza

La CLI richiede il journal broker PREPARING per la stessa transazione e il journal emissione attestation ISSUING con hash esatti della richiesta e del producer. Osserva runc esclusivamente con state; pretende created, verifica il bundle sotto parent approvati, il root runtime sotto parent approvati e la generazione live. Query ip/nsenter sono read-only e mirate ai peer del candidato; non scandiscono migliaia di porte host estranee.

Dopo mandato e osservazioni valide, claim O_EXCL root0600 e fsync di file/directory precedono l’uso della chiave esistente. Firma il record protocollo di attestazione completa e il binding della richiesta. Prima di restituire i dati ripete osservazioni rootfs/OCI/generazione/trasporto, verifica firme, policy, input, source closure, claim e finestre temporali. Il broker conserva il risultato ed emette successivamente l’approval finale con l’issuer separato.

Il claim `ouf.semantic-node-attestation-issuance-claim.v1` resta ISSUING; soltanto il broker conferma ISSUED dopo la custodia. Nessuna cancellazione, recovery o firma ripetuta automatica dopo errore/esito incerto. Il producer non registra runtime, modifica nft, crea namespace, esegue start, consulta IAM/DNS o chiama provider.

## Profilo

Schema esatto `ouf.semantic-node-attestor.v1`: sourceRoot/sourceHashes/pythonBinding; authorities; intentBinding; acceptanceMandatePath; policyBinding/signatureDirectory/opensslBinding; signingKeyBinding/keyRef; brokerEmissionJournal/brokerStateJournal/issuanceClaimPath; budgetSeconds; runtimeBinding/runtimeRootParents/bundleParents; commands(ip/nsenter con path/hash); candidate(networkBindings/transport/tableName); rootfsLimits. Tutti path e binding sono espliciti e privati, senza valori di lab incorporati nel prodotto.

La CLI isolata `-I -B --configuration` usa il contratto LocalEvidenceProducer. Gli errori restituiscono exit1 con diagnostica costante e nessun record. Il signer condiviso accetta soltanto CREATION_ATTESTATION o FINAL_DEPLOYMENT_APPROVAL e verifica il grant pubblico del ruolo. Nessuna authority è dedotta da una chiave privata presente.

## Prossimo intervento VPS: staging v8, NON ESEGUITO

[Comando completo](../handoffs/commands/OUF_STAGE_LOCAL_PRODUCERS_PACKAGE_V8_2026-10-04.sh). SHA256 wrapper `f1c2e775d4882916e0840fe5ab9965fdf4477d984dd4dd5b1e0f5a7a2ea9d5bb`; [manifest di26 sorgenti](../handoffs/commands/OUF_LOCAL_PRODUCERS_PACKAGE_V8_SOURCES_2026-10-04.sha256), SHA256 `a1b11fbfb9d701101f2efa1048c7f99a54f123ed1f1b71f480ffcd883c0e560b`. Sorgenti fissate al commit Gateway sopra.

Nuovo root privato timestamped `/etc/ouf/deploy-snapshots/semantic-local-producers-package-<UTC>`. plan/apply/verify compilano le26 sorgenti senza importarne/eseguirne i corpi e custodiscono una ricevuta immutabile `ouf.semantic-local-producers-source-package.v8`. I due producer non vengono invocati: nessuna chiave privata letta, firma emessa o mandato conferito. Restano false installerApprovalInstalled/nodeAttestorInstalled/brokerInstalled/runtimeRegistered/startAuthorized, senza regole/unit/container modificati.

Il package rende disponibili per configurazione successiva i due producer reali già provati in CI; non chiude il provisioning dell’autorità di accettazione o l’accettazione target. A output ricevuto, aggiornare autonomamente ricevuta, stato comando, handoff, roadmap, manuale e sprint.

## Limiti residui e collegamento al PET

Riletture e prove native non attestano snapshot atomico contro root non cooperativo. Python non garantisce azzeramento dei buffer della chiave letta per verificare il pin; nessuna chiave viene generata/copiata su file/esportata nel risultato. Il producer legge la propria chiave e firma quando realmente invocato: non estendere i contatori zero dello staging a una sua esecuzione operativa.

Restano provisioning reale delle authority e dei mandati, accettazione immagini/volumi target, registrazione esplicita del runtime, autorizzazione eventuale all’avvio, reboot reale e release acceptance. Nessun merge, replay, start o reboot implicito.

L’ingestion interna file→profilo→mapping DRAFT→THS→bundle ACTIVE→Ingestion→UDP resta aperta nel proprio sprint. La ricerca esterna è responsabilità di Semantic/Registry via Gateway, schema.gov.it predefinito e configurabile per installazione; chatbot/MCP propone e THS autorizza adozione/pubblicazione/attivazione. Questo producer è un gate infrastrutturale del ramo provider esterno, non un nuovo prerequisito universale dell’ingestion interna.
