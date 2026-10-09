# Proposta di policy locale di verifica per OUF lab

## Checkpoint corrente — §38 ESEGUITO/PASS, non ripetere

Output operatore ricevuto il4 ottobre2026: plan/apply/verify PASS. Root privato `/etc/ouf/deploy-snapshots/semantic-trust-policy-preparation-20261004-172336`; policyHash `21122630e52cb63c3744fee89f5c81ed926dad55231190243ca11be6d481bd42` identico nei tre modi; receiptHash `42d27903c65e6a1334fff5647a817e393a661e27f5c4fbf69c8d7910a6abb7ab` identico in apply/verify. Checksum wrapper e helper scaricati/installati OK. Evidenza basata sull'output fornito, senza ispezione VPS indipendente. Wrapper eseguito dal commit immutabile dad24714ca572ab45667313b8cc7ec748c851ce3, SHA2561b3927170ba06722402050a25eb12d50bf3d5886ea443b5a1e5866770a573857. Il nuovo header documentale non sostituisce quei bytes eseguiti.

Policy privata materializzata con2chiavi/3ruoli, grant ACTIVE nell'artefatto, parser reale/public binding/custodyReceipt verificati e validità originale preservata. consumerLinked/policyActiveInConsumer/trustPolicyInstalled/roleSigningAuthorized/startAuthorized/runtimeRegistered/deploymentAuthorityProven/atomicSnapshotProven=false. Nessuna nuova chiave, lettura privata, firma selftest/operativa, mandato o chiamata provider/DNS/IAM; regole/unit/container invariati. currentPrivateKeyBindingsReverified=false: non è una nuova verifica delle private key.

§38 completato; §37 conferimento soddisfatto; §36/§34/§31 preservati. **Non ripetere preparazione, custodia o staging.** Prossimo lavoro: acceptance concreta dei2candidati/8mount, con classificazione contenuti/mutabilità/provenance e binding fullOCI/rootfs/generazione; poi intento e configurazione broker/producer. Metadata/hash già inventariati non equivalgono ad accettazione dei contenuti. Emissione di mandati/firme, collegamento consumer, registrazione runtime, start e reboot richiedono scope distinto ancora non conferito. Nessuna accettazione o attivazione implicita da questo PASS. CI codice3bdedad38/38 SUCCESS già verificata,46 test locali PASS e201unit+2nativepreparer+2targetnative PASS senza skip; questa modifica registra evidenza e documentazione, CI documentale separata da verificare.

Installazioni indipendenti per Ente, servizi colocati o distribuiti; nessun multitenant centrale. Semantic/Registry ricerca esterna via Gateway, endpoint schema.gov.it predefinito e parametrizzabile; chatbot/MCP propone, THS governa. Ciclo ingestion interno e prove residue di lease/revoca/reboot/release restano aperti. PR56/26 draft, nessun merge. Le sezioni precedenti che riportano §38 NON ESEGUITO descrivono il checkpoint storico prima di questo output.

### Chiarimento di disegno — installer e approvazione finale nel lab

La scelta di usare la stessa chiave installer per DEPLOYMENT_INTENT e FINAL_DEPLOYMENT_APPROVAL è deliberata per il laboratorio a operatore singolo, già esplicita nella tabella dei grant approvata al37. Non costituisce separazione tra proponente e approvatore finale né approvazione a due persone. La chiave attestor resta distinta: il protocollo richiede comunque CREATION_ATTESTATION autenticata e legata a intentHash/container/transazione/OCI/trasporto/runtime/generazione; il node attestor richiede inoltre mandato di accettazione autenticato sotto CREATION_ATTESTATION. Compromettere soltanto la chiave installer non permette di falsificare quelle evidenze. Permette di firmare intento e approval nei rispettivi ruoli: può abusare di evidenze attestor compatibili ancora valide, quindi non si dichiara immunità dopo compromissione.

I300secondi limitano la validità delle evidenze/mandati transazionali, non la vita della private key: una chiave compromessa può firmare altri payload nei ruoli concessi finché il grant è ammesso e non revocato/scaduto. I90giorni qui proposti sono la diversa finestra del grant, riusata dal draft; nessun rinnovo implicito. Due keypair sullo stesso root host separano ruoli e verifiche, non proteggono da root né forniscono indipendenza amministrativa. Il current scope non attiva consumer o emette evidenze; startup e acceptance target non sono provati.

Il numero di nodi non impone da solo un approvatore distinto: separazione intento/approval è una scelta di responsabilità/governance dell'Ente e del suo modello di minaccia. Il formato policy supporta grant/keyRef/issuerRef diversi per questi due ruoli (1..32keys); nuova custodia/conferimento/configurazioni e prove sono comunque necessari, non basta generare una terza chiave sullo stesso root host per avere approvatori indipendenti. Nessuna separazione aggiuntiva è introdotta implicitamente da questa revisione.

Per più nodi della stessa installazione, target future: attestor locale con propria chiave/issuerRef per nodo e selezione esplicita dell'attestor atteso nella configurazione del deployment per quel nodo. Non fidarsi di qualunque attestor solo perché ammesso a CREATION_ATTESTATION; verificare anche scope/generazione/runtime del target. Binding esplicito nodo, selezione e prove su secondo nodo reale restano aperti: il lab a nodo singolo non li dimostra. Nessuna authority centrale tra Enti e nessun cambio al modello di installazioni indipendenti.

Riferimenti verificati al commit Gateway3bdedad3108112ee4c36e7cb8387aaf60912e97c: tools/semantic_provider_deployment_protocol.py (validate_intent/_validate_creation/validate_final), tools/semantic_provider_node_attestor.py (acceptance), tools/semantic_provider_deployment_reauthorization.py (LateAuthenticatedEvidence), tools/semantic_provider_deployment_authentication.py (policy). Revisione documentale: stessi grant, stessi hash e stessi scope37. **§38 resta NON ESEGUITO**, wrapper già offerto pinned al commit documentale dad24714ca572ab45667313b8cc7ec748c851ce3 invariato e utilizzabile; nessuna nuova autorizzazione richiesta da questa precisazione.

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
