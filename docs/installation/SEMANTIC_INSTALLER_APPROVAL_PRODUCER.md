# Producer reale dell’approval finale dell’installer

## Stato

Implementazione: `scripts/semantic_provider_installer_approval.py`, `tools/semantic_provider_installer_approval.py` e `tools/semantic_provider_deployment_signing.py`, commit Gateway `1f8693cacc296c0b7b521ec6822ad5a032378a3d`. Il broker usa questa CLI nel percorso Docker/runc autenticato di CI. L’attestor del nodo resta una fixture: non è dimostrata l’accettazione delle immagini reali del VPS.

Il package v7 già custodito in `/etc/ouf/deploy-snapshots/semantic-local-broker-package-20261004-110947` proviene da `04d775e892cd42e42d34de02959b9c7ba6483f3b` e non contiene questo nuovo issuer. §29 resta ESEGUITO/PASS. Nessun replay, installazione, mandato target, firma target, registrazione runtime o avvio è implicito in questo lavoro.

## Autorità e flusso

Ogni Ente possiede la propria installazione indipendente. Installer infrastrutturale e attestor del nodo hanno ruoli espliciti; l’IAM applicativo non conferisce da solo l’autorità di deployment. Il modello resta applicabile a servizi sulla stessa macchina/subnet e a servizi distribuiti. L’issuer non deduce autorità dalla topologia.

1. Il broker registra e rende persistente la propria emissione ISSUING, con hash della richiesta e del producer configurato.
2. La CLI verifica la source closure, l’interprete, la trust policy, l’intento firmato e un mandato finale distinto e firmato.
3. Verifica la firma dell’attestazione completa e confronta generazione, accettazione, artefatto, vincoli, applicazione, trasporto e runtime con la richiesta esatta.
4. Registra un proprio claim con O_EXCL e fsync di file e directory. Un claim già presente o un esito incerto impediscono una seconda emissione.
5. Usa una chiave Ed25519 esistente e pinned, verifica che la sua chiave pubblica coincida con il grant ACTIVE della policy e firma approval e binding della richiesta.
6. Verifica entrambe le firme, rilegge input, policy, sorgenti, claim e binding, controlla le finestre temporali e restituisce soltanto il risultato JSON al broker.

Il claim dell’issuer resta ISSUING: l’issuer non può dimostrare che il padre abbia ricevuto stdout. Solo il broker pubblica la custodia del risultato e ISSUED. Non cancellare il claim per ritentare, anche dopo cleanup o errore.

## Mandato finale dedicato

Schema esatto `ouf.semantic-final-approval-mandate.v1`:

| Campi | Vincolo |
| --- | --- |
| issuerRef, installationRef, entityRef | Authority approver e installazione/Ente configurati |
| intentHash, containerId, transactionId | Uno specifico intento e una specifica creazione |
| artifactHash, deploymentConstraintsHash, transportHash, runtimeExecutableHash | Uguaglianza con i binding dell’intento |
| approvalRef | Riferimento esplicito dell’approvazione |
| issuedAt, expiresAt | Finestra valida, massimo 300 secondi, contenuta in quella dell’intento |
| state, issuanceAuthorized, applicationStartAuthorized | ACTIVE e booleani esattamente true |

Il mandato viene autenticato con una firma detached sotto il ruolo FINAL_DEPLOYMENT_APPROVAL della policy. Deve essere già provisionato da un’autorità legittima: la CLI non lo genera, non sceglie authority o chiavi e non trasforma un intento creation-only in mandato di avvio. Nessun mandato reale è stato conferito sul VPS.

## Configurazione e invocazione

Schema esatto `ouf.semantic-installer-approval-producer.v1`, con i seguenti campi obbligatori:

| Campo | Uso |
| --- | --- |
| sourceRoot, sourceHashes | Root privato e closure esatta di 18 sorgenti: CLI e 17 moduli tool elencati in MODULES |
| pythonBinding | Interprete assoluto, hash pinned |
| authorities | installationRef, entityRef, intentIssuerRef, attestorRef, approvalIssuerRef |
| intentBinding, approvalMandateBinding | File già esistenti, path assoluto e SHA256 |
| attestationPath | Path fisso del record pubblicato dal broker; l’hash è vincolato dalla richiesta |
| policyBinding, signatureDirectory, opensslBinding | Policy pubblica e firme; OpenSSL pinned per path/hash/versione |
| signingKeyBinding, keyRef | Chiave privata già esistente, path/hash e grant pubblico corrispondente |
| brokerEmissionJournal | Journal dell’emissione approval del broker, esattamente ISSUING |
| issuanceClaimPath | Claim privato dedicato dell’issuer, inizialmente assente |
| budgetSeconds | Intero da 1 a 12, entro il budget complessivo del broker |

File privati root:root0600, sourceRoot e directory del claim0700, ancestor fidati, nessun symlink/hardlink ammesso per i file privati. La binding producer del broker punta a Python, alla CLI e alla configurazione con i rispettivi hash. Il contratto stdin/stdout è quello di LocalEvidenceProducer.

Invocazione da parte del broker: Python pinned con `-I -B`, CLI pinned e `--configuration` esplicita; richiesta canonica su stdin. Errori: nessun risultato, exit1 e diagnostica costante senza contenuti sensibili. La CLI non esegue start, Docker, nft, IAM o DNS.

## Verifiche e limiti

16 nuovi test con OpenSSL reale: CLI positiva e protocollo finale; mandato assente/falso, creation-only, altro Ente, scaduto o eccedente l’intento; attestazione incompleta e generazione diversa; claim broker mancante; claim precedente/incerto; chiave errata o modificata; fsync fallito; sorgente mutata e richiesta non canonica; regressione dell’orologio; due processi reali in concorrenza. Il percorso Docker autenticato usa ora l’issuer di produzione, un mandato firmato di CI e due chiavi distinte di CI; l’attestor resta sintetico.

La simulazione e l’auto-revisione non sostituiscono i test. Verifiche osservate sul commit sopra: locale137 test,134 PASS e3 Docker skip; CI38/38 SUCCESS senza rerun,131 test pertinenti +2 preparer nativi +6 Docker. I log del percorso autenticato riportano REAL_INSTALLER_ISSUER=true e CI_NODE_ATTESTOR_ONLY=true.

La CLI legge la chiave privata configurata per verificare il pin e chiede a OpenSSL di firmare: non affermare privateKeysRead=0 o signaturesIssued=0 per una sua esecuzione reale. Non genera, copia su file o esporta la chiave nei risultati. Il materiale letto è limitato a4096 byte; Python non garantisce azzeramento dei buffer. Hash/reletture e verifica crittografica prima/dopo non provano uno snapshot atomico contro root non cooperativo.

Restano da realizzare e validare il producer reale dell’attestazione del nodo e l’accettazione completa delle immagini target, oltre al provisioning esplicito delle authority target. Restano aperti reboot reale e release acceptance. Non introdurre nuovi staging source-only per simulare il superamento di questi gate.
