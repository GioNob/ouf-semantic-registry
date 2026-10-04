# Staging privato del broker locale — package v7

Stato: **§29 NON ESEGUITO sul VPS**. Sorgenti Gateway `04d775e892cd42e42d34de02959b9c7ba6483f3b`; sorgenti operative collegate nel predecessore `86ceb70591762319b3003c4163990451a5c6cca1`. Il package v6 §28 già eseguito resta immutabile. Questo nuovo staging è necessario perché il v6 non contiene producer transport e broker operativo.

Il nuovo script `scripts/stage_semantic_local_broker_package.py` copia/valida soltanto la custodia delle sorgenti. Il wrapper [OUF_STAGE_LOCAL_BROKER_PACKAGE_V7_2026-10-04.sh](../handoffs/commands/OUF_STAGE_LOCAL_BROKER_PACKAGE_V7_2026-10-04.sh) scarica20 sorgenti dal commit immutabile e controlla tutti gli hash prima del primo sudo. Crea una directory nuova root-owned0700 sotto /etc/ouf/deploy-snapshots/semantic-local-broker-package-TIMESTAMP, installa sorgenti0600 e manifest0600, quindi esegue plan/apply/verify. Apply scrive esclusivamente la receipt privata del package; non esegue broker, hook o producer.

| Binding | Valore |
| --- | --- |
| sourceCommit | `04d775e892cd42e42d34de02959b9c7ba6483f3b` |
| SHA256 sources.sha256 | `e258b94090319124cbdf9520fa5b179e772836f3d6477e3824809741e08a5035` |
| SHA256 wrapper | `430694376a5b745a35ad2efaf46c2ceede5df9542f62edceacf95c1d47680072` |
| receipt schema | `ouf.semantic-local-broker-source-package.v7` |
| sourceCount | 20 |
| sourceBodiesExecuted | 0 |
| Nuovo root target | Stampato come SEMANTIC_LOCAL_BROKER_PACKAGE_ROOT; non ancora noto |

## Differenze rispetto al package v6

Si include la chiusura operativa, non la catena storica degli stager: stager v7, broker, adapter v4, preparer v3, hook/driver v5 e15 moduli tool. Il profilo broker selezionerà poi la sua chiusura esatta18 dall'insieme20; preparer e driver mantengono le rispettive chiusure16 e15. Nessuna fixture tests o chiave CI è nel package.

sourceBodiesExecuted conta i componenti operativi, escludendo lo stager che viene eseguito per validare/pubblicare la receipt. Il nuovo stager usa soltanto standard library: nessun import/exec delle sorgenti, nemmeno dell'hook di bootstrap. Il manifest esatto è pinned con hash esterno e comprende tutti20 file, incluso lo stager. Sono vietati nomi extra, mancanti o duplicati. I file root-owned0600 devono essere regolari, senza symlink/hardlink, max128KiB e ancestor fidati; quattro directory del package devono essere root-owned0700. Le letture controllano fstat prima/dopo e rileggono tutti i byte dopo la compilazione. Le riletture non provano uno snapshot atomico contro modifiche root non cooperative.

Plan non scrive receipt. Apply usa O_EXCL, fsync file/directory e readback; un file receipt esistente è preservato e blocca un nuovo apply/plan. Verify confronta i byte esatti della receipt canonica attesa, hash dei sorgenti, manifest, Python e metadati tool; non ripara drift. Un valore false sostituito con0 viene respinto e coperto da test; il confronto Python dei soli valori non viene usato. I metadati trustedToolsAvailable verificano proprietà del filesystem, non integrazione o autorizzazione dei tool.

Receipt attesa: brokerInstalled/runtimeAdapterInstalled/admissionPreparerInstalled/externalProducerInstalled/signatureVerifierInstalled/trustPolicyProvisioned/runtimeRegistered/rulesChanged/unitsChanged/containersChanged/startAuthorized=false; sourceBodiesExecuted/keysGenerated/privateKeysRead/signaturesIssued/providerCalls=0; sourceCustodyVerified=true, noSecretsPrinted=true, notReleaseAcceptance=true.

## Verifiche e consegna

Otto nuovi test:20 sorgenti e receipt immutabile; corpi hook/broker/producer con sentinel non eseguita; source drift prima di apply; manifest modificato senza nuovo pin; set incompleto/duplicato/estraneo; symlink/hardlink/permissi pubblici; receipt alterata senza riparazione e sostituzione di un boolean con integer0. Locale121 test eseguiti,118 PASS e3 Docker native saltati. Tutti20 contenuti e SHA256 sono stati confrontati con i file del commit GitHub immutabile; wrapper controllato con bash -n e provato integralmente offline: curl e sudo sostituiti da shim, root target ridiretto in scratch, stager reale plan/apply/verify e tre receipt uguali. La prova offline non ha toccato il VPS. [CI dell'esatto commit](https://github.com/GioNob/ouf-api-gateway/commit/04d775e892cd42e42d34de02959b9c7ba6483f3b/checks):38/38 SUCCESS,115 test pertinenti,2 native preparer e6 Docker test PASS. Nel predecessore1717967947b1fa5b0b3dd11b2c42e7a7f3bdf4fb un job Docker legacy è fallito in docker create senza dettaglio diagnostico; un solo rerun mirato ha completato6 test con SUCCESS, e il percorso autenticato era PASS già al primo tentativo. Il commit corrente viene validato separatamente, senza trasferire il PASS precedente.

Conservare l'output completo plan/apply/verify e il root stampato; non stampare file di configurazione, credenziali, token o chiavi. Dopo il receipt operatore si aggiorneranno autonomamente §29, handoff, roadmap, manuale e sprint a ESEGUITO/PASS soltanto per lo staging effettivamente attestato. Se un tentativo fallisce non rieseguire apply sullo stesso root e non rimuovere custodia o journal per tentare di farlo passare.

## Gate successivo

Staging delle sorgenti non provisiona producer installer/attestor reali, mandate/policy/key né il profilo broker/template/journal STAGED. Occorrono binding dell'Ente e prova completa dell'immagine reale. Il [broker operativo](SEMANTIC_LOCAL_DEPLOYMENT_BROKER.md) usa soltanto tali componenti autorizzati; non inventa authority o firme. Gli avvii, registration, replay, reboot e accettazione release rimangono chiusi. Nessuna autorità centrale multitenant: ogni Ente ha installazione propria, con servizi co-locati o distribuiti.
