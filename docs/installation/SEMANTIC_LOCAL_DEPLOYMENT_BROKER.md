# Broker locale operativo di deployment

## Producer installer ora disponibile

Commit Gateway `1f8693cacc296c0b7b521ec6822ad5a032378a3d`: l’approval finale può essere emessa dalla [CLI installer di produzione](SEMANTIC_INSTALLER_APPROVAL_PRODUCER.md), previa policy, mandato finale firmato e chiave già esistenti. La CI38/38 passa con questo issuer nel percorso Docker autenticato:131 test pertinenti,2 preparer nativi e6 Docker. L’attestor del nodo resta una fixture di CI e deve essere completato per le immagini reali. Il package v7 §29 ESEGUITO/PASS sul VPS non contiene il nuovo issuer; nessuna installazione, firma, registrazione o avvio target è avvenuta con questo checkpoint.

## Stato e confini

Il broker `scripts/semantic_provider_deployment_broker.py` è collegato a `LocalEvidenceProducer`, `ProducerEmission`, `Consumption`, al preparer v3 e al driver v5 tramite l'adapter v4. Non è più necessario un broker sintetico per comporre queste fasi. Le authority e gli attestor reali restano componenti locali configurati con mandato esplicito; il broker non firma, non legge chiavi private e non certifica immagini.

Ogni Ente installa la propria piattaforma indipendente. Nessuna authority condivisa fra Enti, tenant centrale o nuovo microservizio obbligatorio. Stessa macchina/subnet e nodi/reti differenti restano casi supportati dal contratto: il broker non deduce il permesso di comunicare dalla sola appartenenza alla subnet e usa i binding trasporto e il guard/lease della singola installazione.

## Interfaccia realmente collegata

| Fase dell'adapter | Azione del broker | Custodia |
| --- | --- | --- |
| authorize-create | Verifica intento Ed25519 valido e autorizzato esclusivamente alla creazione | Consumption STAGED → CREATING; broker STAGED → CREATING |
| record-created | Interroga il runc pinned e confronta stato created, CID, bundle, PID, hash OCI e generazione | Consumption CREATING → CREATED; broker CREATING → CREATED |
| prepare | Attestor → validazione completa → installer approver → READY → preparer v3 → driver v5 | Claim PREPARING; due emissioni ISSUING/ISSUED; driverHash sigillato una volta; broker PROTECTED |
| cleanup | Invoca il cleanup già esistente dopo rollback indipendente e generazione morta | Broker PROTECTED → CLEANED; nessun reset di Consumption o delle emissioni |

Il broker non chiama `runc create` o `runc start`: l'adapter gestisce la creazione, il driver gestisce il rilascio protetto del processo. `READY` e `PROTECTED` non attestano salute applicativa o release acceptance.

## Profilo e precondizioni dell'installer

Profilo esatto `ouf.semantic-deployment-broker.v1`: sourceRoot, sourceHashes, authorities, intentBinding, policyBinding, signatureDirectory, opensslBinding, producers, preparerTemplate, candidateRoot e runtimeRootParent. `authorities` contiene installationRef/entityRef/intentIssuerRef/attestorRef/approvalIssuerRef. I binding dei file hanno path assoluto +sha256; OpenSSL aggiunge la versione. `producers` contiene soltanto attestation e approval, ciascuno con python/source/configuration pinned. Nessun issuer, tool o chiave di default.

Source closure esatta: broker, preparer, hook e15 moduli tool =18 sorgenti, tutti root-owned0600, sourceRoot0700 e ancestor fidati. Le sorgenti sono verificate prima di eseguirne i moduli; nessun import dal repository ambiente durante la CLI isolata `-I -B`.

Il preparerTemplate pinned ha schema `ouf.semantic-admission-preparer-template.v1` e i campi pythonPath/pythonHash, commands/commandHashes, candidate, kernel, dns, coordinationBinding/coordinationJournal, lockFile, budgetSeconds e hostNetworkNamespace. Candidate iniziale contiene containerId, transactionId, networkBindings, transport, tableName e runtimeBinding(path/sha256). Bundle, hash OCI, root runtime, ricevuta di accettazione e approval sono aggiunti soltanto dopo le verifiche della creazione. Nessuna regola nft o unit è inizializzata dal broker: deve esistere già la custodia guard/lease vuota richiesta dal preparer.

L'installer provisiona candidateRoot0700, directory attestation-results/approval-results0700, lock comune esistente, `deployment.json` STAGED e `broker-state.json` STAGED, con lo stesso binding installationRef/entityRef/containerId/transactionId/intentHash/configurationHash. configurationHash è SHA256 dei byte del profilo broker esatto. Il journal broker aggiunge state/runtimeRoot/bundleHash/driverHash; i tre valori iniziali sono null. Il journal Consumption conserva il suo schema v1 e le precondizioni già documentate. Il broker non inventa intenti, trust policy, mandati o chiavi mancanti.

## Ordine, firme e concorrenza

La fase prepare verifica nuovamente intento, processo created, generazione e trasporto. Acquisisce il lock guard/lease esistente e pubblica PREPARING con fsync prima di allocare O_EXCL i due claim di prima emissione. Ciascuna emissione mantiene il contratto request/record/binding firmato e la custodia persistente già implementati. Un file estraneo viene preservato; una fase incerta non viene ripresa.

`validate_creation` verifica l'intero schema dell'attestazione, intentHash, osservazione temporale, generazione e accettazione completa prima di invocare l'approval producer. L'approvazione riceve anche attestationHash e creationAcceptanceHash. Record e manifest della richiesta sono verificati con Ed25519. I byte firmati dei record sono conservati esattamente, senza normalizzazione che ne cambierebbe la firma.

Consumption.ready_locked e seal_driver_locked compongono le pubblicazioni nella sezione critica già posseduta, evitando un secondo flock. Il broker rilascia il lock prima del subprocess preparer, che acquisisce autonomamente lo stesso lock; lo riprende per verificare custodia, runtime e firme e sigillare il driver. Il lock dell'adapter per candidato resta distinto e non viene riacquisito dal subprocess broker.

Il budget del broker è cumulativo18s. Producer e verifier condividono lo stesso oggetto deadline; il subprocess preparer riceve soltanto il tempo residuo. I/O e bytecode/sorgenti restano limitati, argv fissi, stderr soppresso. La custodia dei due risultati, journal, payload e firme è riletta fino al sigillo del driver. Successivamente il driver esegue i fence delle tre evidenze, policy, scadenza e generazione immediatamente attorno al claim STARTING e al rilascio del FIFO. Nessuna pretesa di snapshot atomico.

## Interruzioni e recupero

Un fallimento dell'attestazione completa lascia broker PREPARING e Consumption CREATED, senza chiedere approval. Un esito incerto del producer conserva ISSUING. Se la preparazione fallisce dopo READY, driverHash resta null e la fase PREPARING resta custodita. Un cambio di generazione, sorgenti, configurazione o risultato durante la preparazione impedisce il sigillo. Nessun retry, replay, reset o riconciliazione implicita.

Il cleanup non dipende da una firma ancora valida: dipende dal driver posseduto, dal rollback indipendente e dalla prova di generazione morta già imposta dal preparer. Non cancella la storia del tentativo.

## Validazione e stato VPS

Sorgenti Gateway `86ceb70591762319b3003c4163990451a5c6cca1`, [CI38/38 SUCCESS](https://github.com/GioNob/ouf-api-gateway/commit/86ceb70591762319b3003c4163990451a5c6cca1/checks):107 test pertinenti,2 native preparer,6 Docker test PASS. Locale:113 test eseguiti,110 PASS e3 Docker native saltati.

Otto nuovi test del broker esercitano processi producer reali e firme Ed25519, ordine attestor/approver, sigillo, mancato replay, claim estraneo, deriva configurazione/intento/generazione/custodia e preparer fallito. Le verifiche native runc/netns/preparer sono sostituite in questi test e coperte dalla prova Docker opt-in in CI.

La prova Docker autenticata usa il broker operativo con due producer distinti, preparer v3 e driver v5. La fixture attestor verifica esclusivamente l'immagine Busybox sintetica approvata, comando e mount di prova; la fixture installer firma sotto mandato sintetico della CI. Wrapper di test introduce deriva lease o firma soltanto dopo l'esecuzione del broker operativo. Queste fixture, le loro chiavi e i loro mandati non appartengono ai pacchetti della piattaforma.

Il VPS ha soltanto il package v6 §28 già eseguito/PASS, source f1996cca60e66f1807b88f126793a8edc1aed15f. Esso non contiene producer o broker nuovi; resta immutabile e non va rieseguito. Nessun nuovo comando VPS è stato eseguito o autorizza un avvio. Collegamento del codice e accettazione del deployment reale sono stati distinti.

Prima di predisporre un deployment reale servono i producer installer/attestor e la trust policy pubblica dell'Ente con mandato esplicito; l'attestor deve provare l'immagine reale e l'accettazione completa. La CI sintetica non li sostituisce. Runtime registration, avvio, replay, reboot e accettazione release restano chiusi finché i rispettivi gate non sono dimostrati e autorizzati.
