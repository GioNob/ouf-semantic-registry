# OUF — ripartenza dopo creazione dei candidati provider fermi

## Checkpoint corrente — provisioning progettato; §32 inventario target NON ESEGUITO

Gateway `a6d4e0ce0b9d66013370184a64103e0922a2e6fe`, PR56 draft non mergiata, **CI38/38 SUCCESS**:168 test pertinenti,2 native preparer e nuova prova Docker dell’inventario (2 candidati reali fixture mai avviati), oltre alle6 prove Docker adapter già verdi. Log root111444592858 e111444583801 verificati:168+2+1, nessuno skip. Locale169 test,168PASS/1 nuovo Docker skip. Prima revisione33e820f aveva3 failure in config-contract perché le fixture private root erano eseguite dal runner non root; corretto soltanto il gating fixture, non i vincoli di produzione, nuova CI verde senza rerun.

Preparato progetto per policy e configurazioni per-Ente e nuovo helper standalone `scripts/inventory_semantic_target_acceptance.py` (SHA256 `959be951c87824a0949872c64c8582da3bc64571d8103032f44834ff0d98451e`). Verifica manifest/journal/package v8 e26 hash, confronta due letture selected Docker inspect di immagini/candidati/network e stat dei mount senza aprirne contenuti o chiavi. Nessuna lettura env. Evidenze private bounded/durable, receipt per ultima, no-overwrite; nessun import/esecuzione dei producer. La bozza authority usa schema diverso dalla policy e stato DRAFT_NOT_AUTHORIZED, identità/chiavi non assegnate: non conferisce trust.

**Prossimo intervento VPS: §32 NON ESEGUITO**, [wrapper completo](commands/OUF_INVENTORY_TARGET_ACCEPTANCE_2026-10-04.sh), SHA256 `25023bef6501cfeec533d795619812ef6e3c79e44398e902979a1b24e51343b5`. Nuovo snapshot `semantic-target-acceptance-inventory-TIMESTAMP/prepared`; input restano i root sigillati candidati20261003 e package v8 `/etc/ouf/deploy-snapshots/semantic-local-producers-package-20261004-121542`, source7ded9df. Output stdout solo hash/conteggi/booleani; dossier/piano/receipt root0600. [Modello di fiducia, matrice configurazioni e limiti](../installation/SEMANTIC_DEPLOYMENT_AUTHORITY_PROVISIONING.md). Il wrapper crea esplicitamente root/source/prepared root:root0700; download helper pinned e hash installato verificati; bash-n PASS.

§31 **ESEGUITO/PASS**, source0755→0700 e plan/apply/verify sullo stesso package121542 completati; non ripetere recovery o staging. §30 originario resta storico BLOCKED. Il bootstrap canonico corretto resta completo per installazioni nuove; nessuna sua esecuzione VPS è inventata. §29 v7 preservato. Dopo output §32 registrare autonomamente root/hash/esito e stato comando nei4 documenti. Quindi preparare provisioning reviewable per soggetti/chiavi/policy e accettazione immagini/volumi prima del conferimento. Generazione chiavi/firma/applicazione policy e registrazione runtime/start restano espliciti, senza merge/replay impliciti.

Limiti: dossier selected inspect/layer descriptor non è full OCI, rootfs seal o provenance; stat mount non ne accetta contenuti/mutabilità; runc configurato Docker created non prova bundle/generazione live. Authority reale, namespace/lease/revoca/start, snapshot atomico, reboot e release acceptance restano aperti. Installazioni indipendenti per Ente, stessa rete/host o servizi distribuiti. Il ramo provider esterno non è prerequisito universale dell’ingestion interna MCP/THS/ACTIVE/Ingestion/UDP, ancora aperta. Semantic/Registry cerca tramite Gateway, default schema.gov.it configurabile; chatbot/MCP propone e THS governa.

## Checkpoint storico — §31 ESEGUITO/PASS; staging v8 completato

Output operatore allegato: recovery root `/etc/ouf/deploy-snapshots/semantic-local-producers-directory-recovery-20261004-123655`; package originale `/etc/ouf/deploy-snapshots/semantic-local-producers-package-20261004-121542`. inspect/repair PASS, source root:root **0755→0700**, proprietari/dev/inode e26 sorgenti preservati; **plan/apply/verify PASS**. Custodia sorgenti verificata, sourceCommit `7ded9df0c74c6db919c7a68d4c75ab2c132dea53`, manifest `a1b11fbfb9d701101f2efa1048c7f99a54f123ed1f1b71f480ffcd883c0e560b`. [Evidenza strutturata](receipts/SEMANTIC_LOCAL_PRODUCERS_V8_RECOVERY_PASS_2026-10-04_OPERATOR.json) e [output operatore](receipts/SEMANTIC_LOCAL_PRODUCERS_V8_RECOVERY_2026-10-04_OPERATOR.txt); nessuna ispezione indipendente del VPS, hash della receipt target non fornito. §30 originario resta ESEGUITO/BLOCKED; §31 è ESEGUITO/PASS e non va ripetuto.

**Procedura canonica per nuovi package:** [unico wrapper completo corretto](commands/OUF_STAGE_LOCAL_PRODUCERS_PACKAGE_V8_2026-10-04.sh), SHA256 `f7f3b96a1a0f6f32971a6d8c973ceb88339630eddff76f02df983bd36177739d`. Scarica e verifica tutti26 sorgenti, crea esplicitamente root/source/scripts/tools root:root0700 e completa plan/apply/verify: non richiede il vecchio comando difettoso né la recovery. Questa revisione canonica è **NON ESEGUITA sul VPS**; il PASS target deriva dalla recovery documentata, non da una prova di bootstrap nuovo. Il wrapper difettoso resta soltanto storico nel commit immutabile `f6280b6275963af3b41b2426d8c75ec6a033cee3`, checksum f1c2e775; non usarlo per installazioni future. Variante FIXED equivalente resta disponibile per compatibilità.

Verifiche codice Gateway `7941098e4253a50916542471328f556d979436fe`: CI38/38 SUCCESS,159 test pertinenti+2 native+6 Docker; nuovi8 test comprendono il bootstrap corretto con umask022/077 e la recovery reale. Contatori target chiavi/firme/provider/esecuzione producer tutti0; trustPolicyProvisioned/runtimeRegistered/startAuthorized=false, componenti non installati, regole/unit/container invariati. Nessuna authority o release acceptance provata.

**Prossimo lavoro:** preparare provisioning esplicito per-Ente di authority e mandati di accettazione delle immagini/volumi target. Generazione chiavi, firma mandati, registrazione runtime e avvio richiedono authority esplicita; nessun merge/replay/reboot implicito. Atomicità e reboot reale restano aperti. Installazioni indipendenti per ogni Ente, host/rete condivisi o distribuiti; ingestion interna MCP→profilo→mapping DRAFT→THS→ACTIVE→Ingestion→UDP resta aperta.

## Checkpoint storico — §30 bloccato; §31 allora pendente

Output operatore: root `/etc/ouf/deploy-snapshots/semantic-local-producers-package-20261004-121542`, source `7ded9df0c74c6db919c7a68d4c75ab2c132dea53`;28 checksum OK (wrapper/manifest/26 sorgenti), poi **BLOCKED MODE=plan REASON=PRIVATE_PACKAGE_DIRECTORY_REQUIRED**. apply/verify non raggiunti nel wrapper set-e; nessuna receipt PASS fornita. §30 è **ESEGUITO/BLOCKED**, non più NON ESEGUITO e non PASS. [Evidenza operatore](receipts/SEMANTIC_LOCAL_PRODUCERS_V8_BLOCKED_2026-10-04_OPERATOR.json), senza attribuire un’ispezione indipendente del VPS o inventare un hash di receipt target.

Difetto riprodotto con GNU install reale: le leaf source/scripts e source/tools ricevono0700, ma source intermedia viene creata0755. Il wrapper ometteva source dall’elenco esplicito. Il validatore resta rigoroso; non si accetta0755. La metadata concreta target sarà letta prima di qualsiasi riparazione, e stati inattesi sono rifiutati.

Correzione Gateway `7941098e4253a50916542471328f556d979436fe`, PR56 draft non mergiata, **CI38/38 SUCCESS senza rerun**:159 test pertinenti +2 native preparer +6 Docker. Locale165 test,162PASS e3Docker skip. 8 nuovi test riproducono il caso GNU, il completamento originale dopo recovery, umask022/077, receipt incerta, hash/mode/owner/symlink/hardlink inattesi, no-op e fsync fallito. Nessuno dei26 sorgenti del package target è cambiato.

**Prossimo intervento dell’operatore: §31 NON ESEGUITO**, [wrapper recovery](commands/OUF_RECOVER_LOCAL_PRODUCERS_PACKAGE_V8_DIRECTORY_2026-10-04.sh), SHA256 `2d770d268cf5a9e164d6559b60c3246500009d80ab076838f9fab4387df94a5d`. [Procedura e limiti](../installation/SEMANTIC_PACKAGE_V8_DIRECTORY_RECOVERY.md). Helper pinned Gateway sopra, SHA256 `116efd276852fc184479017ab853fb5ccce5c30667489771f097da4f505dbac4`. Verifica root/scripts/tools0700, source0755 o0700, root:root,26 hash originali e receipt assente; corregge soltanto source0755→0700, fsync e rilegge. Sullo stesso root completa per la prima volta plan/apply/verify dello stager7ded9df. Receipt presente o metadati inattesi bloccano: non cancellare o normalizzare altro. Non ripetere il wrapper originario e non creare un package sostitutivo per nascondere questo tentativo.

Il [wrapper futuro corretto](commands/OUF_STAGE_LOCAL_PRODUCERS_PACKAGE_V8_FIXED_2026-10-04.sh) crea esplicitamente tutte le quattro directory con mode/owner/group richiesti; **NON ESEGUITO**, non destinato al root121542. Il comando originario è deprecato e marcato ESEGUITO/BLOCKED; il commit eseguito f6280b6 rimane immutabile con checksum wrapper f1c2e775. La sua sezione storica non è uno stato corrente.

La recovery non esegue producer e non crea authority, chiavi o firme; non registra runtime, non modifica regole/unit/container e non autorizza avvii. §29 v7 ESEGUITO/PASS è preservato. Dopo output §31 registrare autonomamente receipt, stato comando e tutti i documenti; poi provisioning esplicito authority e mandati per immagini/volumi target, ancora aperto. Restano snapshot atomico, runtime registration e avvio eventuali espliciti, reboot e release acceptance.

Ogni Ente conserva un’installazione indipendente, stessa macchina/subnet o servizi su nodi/reti differenti; nessun tenant o authority centrale. Questo ramo riguarda il provider esterno: ingestion interna MCP→profilo→mapping DRAFT→THS→bundle ACTIVE→Ingestion→UDP resta aperta. Semantic/Registry ricerca via Gateway, schema.gov.it predefinito e provider configurabile; chatbot/MCP propone e THS autorizza adozione/pubblicazione/attivazione.

## Checkpoint storico — attestor e issuer reali verificati; staging v8 allora NON ESEGUITO

Gateway `7ded9df0c74c6db919c7a68d4c75ab2c132dea53`, PR56 draft non mergiata: **CI38/38 SUCCESS**, senza rerun, con151 test pertinenti +2 prove native preparer +6 Docker. Locale157 test,154PASS e3 Docker skip. Nuovi12 test attestor e8 test staging v8. Il percorso autenticato usa entrambi i producer di produzione; il rootfs alterato dopo l’accettazione è respinto prima di claim del firmatario, approval e driver, senza processo applicativo. Mandati, chiavi e immagine Busybox della prova restano di CI.

L’attestor verifica un mandato di accettazione esplicito e firmato, l’intero OCI, il sigillo dell’intero rootfs senza esclusioni, runtime created, generazione live, MAC/IP e peer/bridge. Rilegge prima/dopo la firma e conserva un claim non ripetibile. Il contenuto dei bind mount esterni non è sigillato dal rootfs: l’autorità deve approvarne esplicitamente mutabilità e vincoli del documento OCI. Questo non prova snapshot atomico, provenance publisher o accettazione delle immagini/volumi reali del VPS.

**Prossimo intervento necessario dell’operatore: §30 staging privato v8, NON ESEGUITO.** [Comando completo](commands/OUF_STAGE_LOCAL_PRODUCERS_PACKAGE_V8_2026-10-04.sh), wrapper SHA256 `f1c2e775d4882916e0840fe5ab9965fdf4477d984dd4dd5b1e0f5a7a2ea9d5bb`; manifest26 sorgenti SHA256 `a1b11fbfb9d701101f2efa1048c7f99a54f123ed1f1b71f480ffcd883c0e560b`. Fonte immutabile Gateway sopra. Nuovo root privato timestamped; plan/apply/verify compilano e custodiscono sorgenti/ricevuta senza invocare i producer. Nessuna chiave, firma o authority target, registrazione runtime, modifica regole/unit/container o avvio. **Non ripetere §29.**

§29 v7 resta ESEGUITO/PASS secondo ricevuta operatore, root `/etc/ouf/deploy-snapshots/semantic-local-broker-package-20261004-110947`, source `04d775e892cd42e42d34de02959b9c7ba6483f3b`. Non contiene i nuovi producer. Il nuovo package v8 li rende disponibili per configurazione successiva: non è accettazione operativa. La sua esecuzione va registrata soltanto quando arriva l’output reale dell’utente; aggiornare autonomamente ricevuta, stato comando e tutti i documenti.

Decisione: ogni Ente ha installazione e authority indipendenti; attestor locale al nodo runtime, senza tenant o authority centrale. Stesso host/subnet e nodi/reti differenti restano supportati dal contratto. Protocollo, configurazione, limiti, responsabilità dei mandati e provisioning aperto: [attestor/package v8](../installation/SEMANTIC_NODE_ATTESTOR_AND_PRODUCERS_PACKAGE_V8.md). L’issuer installer già completato rimane separato dall’attestor e dall’IAM applicativo.

Dopo l’output v8: chiudere custodia sorgenti target e preparare **provisioning esplicito delle authority e dei mandati di accettazione target**, con binding reali delle immagini/volumi. Restano inoltre registrazione runtime esplicita, eventuale autorizzazione all’avvio, reboot reale e release acceptance. Nessun merge, replay, start o reboot implicito.

Il ramo ingestion interno MCP→profilo→mapping DRAFT→THS→bundle ACTIVE→Ingestion→UDP resta aperto nel suo sprint. Semantic/Registry esegue la ricerca esterna via Gateway, schema.gov.it predefinito e provider configurabile per installazione; chatbot/MCP propone, THS autorizza adozione/pubblicazione/attivazione. Questo gate riguarda il deployment provider esterno, non un prerequisito universale dell’ingestion interna.

## Checkpoint storico — issuer reale dell’approval completato; §29 VPS ESEGUITO/PASS

Gateway: `1f8693cacc296c0b7b521ec6822ad5a032378a3d`, ramo `codex/semantic-provider-request-boundary`, PR56 draft e non mergiata. CI **38/38 SUCCESS**, senza rerun: **131 test pertinenti**, **2 prove native del preparer** e **6 test Docker**, compreso il percorso autenticato che usa broker operativo e **issuer installer di produzione**. In locale:137 test eseguiti,134 passati e3 prove Docker saltate perché l’ambiente non le supporta. 16 nuovi test issuer includono due processi concorrenti, fsync fallito, claim incerto, mandato/chiave/input non validi e regressione temporale.

L’issuer verifica un mandato finale **distinto, esplicito e firmato**, riferito a quello specifico intento; un intento creation-only non autorizza l’approval. Verifica l’attestazione completa del nodo prima di leggere la chiave privata esistente e pinned. Claim O_EXCL e fsync precedono le due firme Ed25519. Il claim issuer resta ISSUING anche dopo il risultato: soltanto il broker conferma custodia e ISSUED. Nessun retry/reset automatico dopo un esito incerto.

Decisione tecnica: issuer locale dell’installer, distinto dall’attestor e dall’IAM applicativo, per ogni installazione indipendente di ciascun Ente. Nessun servizio centrale o multitenant. Stesso host/subnet e servizi distribuiti restano casi supportati. Per contratto, provisioning e limiti: [producer installer reale](../installation/SEMANTIC_INSTALLER_APPROVAL_PRODUCER.md).

**VPS: invariato rispetto alla ricevuta §29.** Package v7 `/etc/ouf/deploy-snapshots/semantic-local-broker-package-20261004-110947`, source `04d775e892cd42e42d34de02959b9c7ba6483f3b`, plan/apply/verify ESEGUITI/PASS. La ricevuta operatore e la sezione del comando restano registrate; non effettuare replay. Il nuovo issuer non è installato nel package v7. Nessuna nuova esecuzione VPS è dichiarata. Nessuna generazione chiavi, firma target, concessione authority, registrazione runtime, avvio, merge o reboot.

**Questione aperta e prossimo passo preciso:** completare il producer reale dell’attestazione del nodo, con verifica dell’immagine/rootfs e dei vincoli completi di creazione, generazione live e binding del trasporto; poi provisioning esplicito delle authority target. La CI usa ancora un attestor e mandati/chiavi sintetici dedicati, quindi non prova accettazione delle immagini reali, authority target, snapshot atomico, reboot o release acceptance. Non produrre un altro staging source-only per dichiarare chiusi questi gate.

Il percorso ingestion via MCP resta aperto nel suo sprint: file → profilo → mapping DRAFT → THS → bundle ACTIVE → Ingestion → UDP. L’enforcement esterno non è una dipendenza universale dell’ingestion interna. La ricerca esterna appartiene a Semantic/Registry tramite Gateway, provider predefinito schema.gov.it configurabile per installazione; chatbot/MCP propone, THS autorizza adozione/pubblicazione/attivazione. Queste responsabilità non cambiano con l’issuer.

## Checkpoint storico — §29 ESEGUITO/PASS; sorgenti broker v7 custodite sul VPS

Ricevuta operatore del2026-10-04: `/etc/ouf/deploy-snapshots/semantic-local-broker-package-20261004-110947`, schema `ouf.semantic-local-broker-source-package.v7`, source `04d775e892cd42e42d34de02959b9c7ba6483f3b`. Checksum wrapper +manifest +20 sorgenti OK; plan/apply/verify PASS, tre receipt JSON concordanti; Python3.13.5. Tutti20 hash confrontati con il manifest del comando immutabile `bcae7ff130846a28e98579556790efdeee495d10`. Wrapper SHA256 `430694376a5b745a35ad2efaf46c2ceede5df9542f62edceacf95c1d47680072`; manifest SHA256 `e258b94090319124cbdf9520fa5b179e772836f3d6477e3824809741e08a5035`.

[Evidenza strutturata dell'operatore](receipts/SEMANTIC_LOCAL_BROKER_PACKAGE_V7_2026-10-04_OPERATOR.json), SHA256 dell'allegato terminale `40809a684b7543e7531b35f8be8f3d4b6260e907690999afe2e7f89971faa8bd`. Fonte: Testo incollato(3).txt. Questa è evidenza fornita dall'operatore, non ispezione indipendente del VPS; nessun digest della receipt target è stato fornito e non viene inventato. trustedToolsAvailable=true per tutti10 tool è metadata filesystem, non prova di integrazione runtime o authority.

Confermati false: brokerInstalled, runtimeAdapterInstalled, admissionPreparerInstalled, externalProducerInstalled, signatureVerifierInstalled, trustPolicyProvisioned, runtimeRegistered, rulesChanged, unitsChanged, containersChanged, startAuthorized. Confermati0: sourceBodiesExecuted, keysGenerated, privateKeysRead, signaturesIssued, providerCalls. sourceCustodyVerified/noSecretsPrinted/notReleaseAcceptance=true. sourceBodiesExecuted riguarda i componenti operativi, escluso lo stager. Lo staging non ha eseguito il broker o gli issuer/attestor reali.

**§29 non va rieseguito.** [Comando storico aggiornato a ESEGUITO/PASS](commands/OUF_STAGE_LOCAL_BROKER_PACKAGE_V7_2026-10-04.sh); il commit immutabile offerto all'operatore conserva il testo precedente NON ESEGUITO. Il package v6 §28 resta immutabile, root /etc/ouf/deploy-snapshots/semantic-authenticated-runtime-package-20261004-094455, source f1996cca60e66f1807b88f126793a8edc1aed15f.

**Validazione software già conclusa:** [Gateway04d775e8](https://github.com/GioNob/ouf-api-gateway/commit/04d775e892cd42e42d34de02959b9c7ba6483f3b/checks) CI38/38 SUCCESS,115 test pertinenti,2 native preparer,6 Docker PASS; locale121 eseguiti,118 PASS e3 Docker saltati. Otto test dello stager, verifica esatta dei byte receipt per respingere false/0, wrapper integrale offline con root/curl/sudo shim e stager reale. [Guida del package](../installation/SEMANTIC_LOCAL_BROKER_PACKAGE_V7.md).

**Prossimo gate:** predisposizione esplicita dei producer installer/attestor reali e del mandato/trust policy pubblica dell'Ente; accettazione completa dell'immagine reale; profilo broker/template e journal STAGED legati ai dati del VPS. Le chiavi e il verifier Busybox della CI non sono authority target. Senza queste evidenze non si invoca il percorso operativo e non si considera il target startup-ready. Nessun nuovo comando di attivazione è autorizzato da questo receipt.

Restano aperti gli altri gate di infrastruttura/namespace/revoca/lease/reboot e il ciclo file→mapping→ingestion→UDP; nessun PASS viene trasferito dal package alla release. Ogni Ente ha installazione indipendente; co-locazione o reti differenti non conferiscono permessi impliciti. Semantic/Registry mantiene la discovery esterna attraverso Gateway, default schema.gov.it configurabile, e THS governa adozione/attivazione secondo PET. Nessun merge, start, registration, replay o reboot implicito.

## Checkpoint storico — §29 pronto/NON ESEGUITO; package broker v7 privato

Il broker operativo è collegato e verificato nel commit `86ceb70591762319b3003c4163990451a5c6cca1` (CI38/38 SUCCESS). Nuovo Gateway `04d775e892cd42e42d34de02959b9c7ba6483f3b`: stager source-only v7 con manifest esatto pinned,20 sorgenti della chiusura operativa, zero esecuzione dei corpi hook/broker/producer. Nuovo codice stager/test e workflow; broker operativo, adapter, preparer e driver restano quelli già collegati.

**§29 NON ESEGUITO:** prossimo intervento operatore è soltanto staging privato in nuovo root /etc/ouf/deploy-snapshots/semantic-local-broker-package-TIMESTAMP. [Comando immutabile](commands/OUF_STAGE_LOCAL_BROKER_PACKAGE_V7_2026-10-04.sh), wrapper SHA256 `430694376a5b745a35ad2efaf46c2ceede5df9542f62edceacf95c1d47680072`; manifest SHA256 `e258b94090319124cbdf9520fa5b179e772836f3d6477e3824809741e08a5035`; sorgenti pinned `04d775e892cd42e42d34de02959b9c7ba6483f3b`. Non eseguire il comando storico §28 sul vecchio root. [Guida e valori attesi](../installation/SEMANTIC_LOCAL_BROKER_PACKAGE_V7.md).

Plan non scrive; apply scrive soltanto receipt privata O_EXCL/0600/fsync; verify confronta i byte esatti della receipt e sorgenti e non ripara drift. Manifest esatto20 file, hash verificati prima di compilare, nessun import/exec delle sorgenti; letture limitate e fstat/readback. Non vengono eseguiti broker, producer, runc, Docker, nft, OpenSSL, IAM o DNS. Capability tool è solo metadata filesystem.

**Verifiche:** otto nuovi test dello stager; locale121 eseguiti,118 PASS e3 Docker native saltati. Wrapper bash -n PASS, tutti20 contenuti/hash confrontati con il commit GitHub. [CI Gateway](https://github.com/GioNob/ouf-api-gateway/commit/04d775e892cd42e42d34de02959b9c7ba6483f3b/checks): 38/38 check SUCCESS sull'esatto commit corrente. Il predecessore1717967947b1fa5b0b3dd11b2c42e7a7f3bdf4fb ha richiesto un singolo rerun del job Docker legacy dopo un errore docker create senza dettagli diagnostici; il percorso autenticato era PASS già allora. Il commit corrente è verificato separatamente. 115 test pertinenti PASS,2 native preparer PASS,6 Docker test PASS; Docker corrente concluso con SUCCESS. Wrapper completo provato anche offline con curl/sudo shim, root locale e stager reale: tre receipt uguali, VPS non toccato. Test aggiunto per false→0 nella receipt, respinto dal confronto esatto dei byte..

**Ultimo VPS confermato:** §28 ESEGUITO/PASS, root /etc/ouf/deploy-snapshots/semantic-authenticated-runtime-package-20261004-094455, source f1996cca60e66f1807b88f126793a8edc1aed15f, ricevuta operatore2a8a0bc82e93bd09a6f65e7645381e1951b6bff1. V6 immutabile; nuovo v7 non lo modifica né lo riapplica. Root/receipt §29 saranno noti solo dopo output operatore.

**Gate successivo aperto:** producer installer/attestor reali, mandato infrastrutturale, policy pubblica e accettazione completa dell'immagine; profilo broker/template/journal STAGED della singola installazione. Package source-only non li provisiona e non costituisce startup readiness. Nessun avvio, registration, key generation/read, firma, provider call, replay, reboot o merge implicito. Ogni Ente ha piattaforma indipendente; conservata la responsabilità PET Semantic/Registry→Gateway per discovery esterna e THS per adozione/attivazione. Il ciclo file→ingestion→UDP resta distinto e aperto.

## Checkpoint storico — broker operativo collegato ai producer e al driver

Gateway `86ceb70591762319b3003c4163990451a5c6cca1`: `scripts/semantic_provider_deployment_broker.py` compone le quattro fasi dell'adapter v4 con `LocalEvidenceProducer`, `ProducerEmission`, Consumption, preparer v3 e driver v5. Il collegamento è implementato; il broker sintetico precedente non è più necessario per comporre il percorso autenticato. Guida completa: [SEMANTIC_LOCAL_DEPLOYMENT_BROKER.md](../installation/SEMANTIC_LOCAL_DEPLOYMENT_BROKER.md).

Ordine effettivo: intento creation-only autenticato → processo OCI created verificato → claim PREPARING persistente → attestazione firmata e validazione completa prima di chiedere approval → approval firmata legata alla richiesta/attestationHash/creationAcceptanceHash → READY → preparer → sigillo del driver sotto lock comune → start protetto soltanto dove autorizzato. Le chiamate ready_locked/seal_driver_locked evitano flock annidati; il subprocess preparer acquisisce il lock dopo che il broker lo ha rilasciato. Ogni emissione conserva ISSUING/ISSUED e file O_EXCL. Interruzioni, custodia o generazione cambiate e claim estranei impediscono replay o sigillo.

**Verifiche:** 113 test locali eseguiti,110 PASS e3 Docker nativi saltati per ambiente privo di Docker/runc/netns. Otto nuovi test del broker usano subprocess producer e firme Ed25519 reali; native runtime/preparer sostituiti soltanto nei test unitari. [CI Gateway del commit](https://github.com/GioNob/ouf-api-gateway/commit/86ceb70591762319b3003c4163990451a5c6cca1/checks):107 test pertinenti PASS,2 prove native preparer PASS,6 test Docker PASS, compresa la catena broker operativo → due producer distinti → preparer v3 → driver v5, blocchi per deriva lease/firma e cleanup reale. Chiavi/mandati/verifier Busybox restano fixture CI, esclusi dai pacchetti di deployment. Tutti i38 check Gateway del commit sono SUCCESS, inclusi i due job summary-stack.

**VPS invariato:** §28 ESEGUITO/PASS in `/etc/ouf/deploy-snapshots/semantic-authenticated-runtime-package-20261004-094455`, source `f1996cca60e66f1807b88f126793a8edc1aed15f`. Ricevuta operatore in `2a8a0bc82e93bd09a6f65e7645381e1951b6bff1`. Il package v6 non contiene i nuovi producer/broker; è immutabile e non va rieseguito. Nessun nuovo comando VPS, chiave, firma reale, policy, runtime registration o avvio è stato eseguito da questa sessione. Nessun merge.

**Prossimo passo preciso:** predisporre per la singola installazione i binding dei producer installer/attestor reali e della trust policy pubblica, sotto mandato infrastrutturale esplicito. L'attestor deve provare l'immagine e l'accettazione completa reali; il risultato CI non lo sostituisce. Il profilo broker, il template e i journal STAGED devono essere provisionati con i dati effettivi del VPS prima di invocare il percorso operativo. Non generare implicitamente chiavi, mandati, avvii, replay o reboot. L'integrazione software è completata; l'accettazione del deployment target resta aperta.

Conservati i vincoli PET: installazioni indipendenti per Ente, topologie su host/reti differenti o stessa subnet; ricerca esterna di Semantic/Registry attraverso Gateway, default schema.gov.it configurabile per installazione. Chatbot/MCP propone discovery/mapping tipizzato; THS decide adozione/pubblicazione/attivazione. Questo gate riguarda la discovery esterna e non sostituisce né dichiara completato il ciclo interno file → ingestion → UDP.

## Checkpoint storico — §28 ESEGUITO/PASS; contratto e custodia producer implementati

§28: `/etc/ouf/deploy-snapshots/semantic-authenticated-runtime-package-20261004-094455`, source `f1996cca60e66f1807b88f126793a8edc1aed15f`; checksum wrapper +22 sorgenti e plan/apply/verify PASS concordanti, Python3.13.5. Ricevuta operatore in `2a8a0bc82e93bd09a6f65e7645381e1951b6bff1`, CI documentale13/13. Nessun accesso VPS indipendente o digest della receipt target. Nessun replay del §28.

Nuovo codice Gateway `93e1c845d26d339af6a07acb0e588b2532d2a4a7`: `LocalEvidenceProducer` invoca soltanto un producer Python locale con interprete/source/configurazione esplicitamente pinned; richieste esatte CREATION_ATTESTATION/FINAL_DEPLOYMENT_APPROVAL, preflight mandato attivo, I/O limitati, stderr soppresso, deadline condivisa con la verifica. Due firme reali: record e manifest che lega requestHash/recordHash/hash dell'envelope canonico. Un hash di richiesta non firmato non è accettato come legame. L'autenticatore espone anche verifica detached in memoria, conservando le verifiche file legacy.

`ProducerEmission` richiede un journal UNUSED esplicitamente provisionato e il lock comune già esistente: claim fsync ISSUING prima dell'invocazione, risultato firmato salvato O_EXCL/0600 con readback e fsync directory, poi ISSUED con resultHash. Timeout/esito sconosciuto resta ISSUING; nessun retry/reset automatico. File risultato estraneo è preservato e blocca prima dell'emissione. Due processi concorrenti non emettono due volte sullo stesso claim.

**Validazione:** 99 test locali PASS, di cui17 nuovi producer test: processo reale +Ed25519, catena a tre ruoli del protocollo esistente, replay di risposta su richiesta differente, firma/mandato/scope/source drift, modifica configurazione durante processo, limiti/output flood/hang e diagnostica redatta, deadline unica, fsync/custodia/claim incerto e concorrenza con due processi. Chiavi effimere solo fixture. [CI sull'esatto commit](https://github.com/GioNob/ouf-api-gateway/commit/93e1c845d26d339af6a07acb0e588b2532d2a4a7/checks): verificare i check di questo head, senza trasferire il PASS di un commit precedente.

**Limite e prossimo passo preciso:** trasporto e custodia del producer sono implementati/testati, ma il broker produttivo e il collegamento di questi componenti al bootstrap operativo non sono dichiarati completi. Comporre il broker con claim per i ruoli, full attestation valida prima della richiesta di approval, pubblicazione/custodia del request-binding e delle tre evidenze, quindi READY del consumer esistente e preparer3/driver5. Nessun approver o attestor reale è provisionato; non confondere il fixture echo/signature CI con full image/OCI/rootfs acceptance. Profilo e mandato dell'Ente, keys/policy/producer reali e gli altri gate rimangono aperti.

**Nessun nuovo intervento VPS in questo checkpoint:** v6 resta immutato; il nuovo modulo e la nuova API detached non sono copiati/installati sul target. Regole/unit/container/runtime e start non cambiano. Nessun merge/replay/emissione/keygen target. Installazioni indipendenti per Ente; servizi co-locati o distribuiti; Semantic/Registry discovery esterna tramite Gateway (default schema.gov.it parametrizzabile), MCP/chatbot propone e THS governa adozione/attivazione. La prova file→mapping→ingestion→UDP resta aperta.


## Checkpoint storico — ricevuta §28, prima del contratto producer

Output operatore del 4 ottobre 2026: `/etc/ouf/deploy-snapshots/semantic-authenticated-runtime-package-20261004-094455`, schema `ouf.semantic-authenticated-runtime-source-package.v6`, source `f1996cca60e66f1807b88f126793a8edc1aed15f`, Python3.13.5. Checksum wrapper +22 sorgenti OK; plan/apply/verify PASS con tre receipt concordanti. [Ricevuta operatore](https://github.com/GioNob/ouf-semantic-registry/blob/codex/r4a-smoke-semantic-inventory/docs/handoffs/receipts/SEMANTIC_AUTHENTICATED_RUNTIME_PACKAGE_V6_2026-10-04_OPERATOR.json). Evidenza allegata, non accesso VPS indipendente; digest del file receipt sul VPS non fornito.

adapter/preparer/verifier/producer/runtime non installati o registrati; trustPolicyProvisioned/startAuthorized=false, keysGenerated/signaturesIssued/providerCalls=0; regole/unità/container invariati. trustedToolsAvailable, incluso OpenSSL, è metadata, non prova di verifica crypto o autorità sul target. §28 completato: nessun replay. I commit precedenti e i package v5/v6 restano immutabili.

**Prossimo lavoro indipendente:** definire e implementare il contratto del producer locale per richieste tipizzate di CREATION_ATTESTATION e FINAL_DEPLOYMENT_APPROVAL, con eseguibile/configurazione pinned, limiti/deadline e verifica delle firme restituite; collegarlo poi al broker senza generare mandati, chiavi o approval implicite. La firma autentica il mandato provisionato, non dimostra da sola la veridicità della full image/OCI/rootfs acceptance. Il mandato reale della singola installazione e gli altri gate del handoff restano aperti.


## Checkpoint storico — driver collegato, prima dell'esecuzione §28

Gateway `f1996cca60e66f1807b88f126793a8edc1aed15f`: **adapter v4 → preparer v3 → driver v5** richiedono esplicitamente riverifica Ed25519 dei tre ruoli. Le nuove closure sigillate contengono 16 file per il preparer e 15 per il driver; nessun fallback al driver precedente nel percorso adapter v4. I vecchi schemi rimangono compatibili per gli snapshot già creati, senza migrazione implicita.

**Budget condiviso:** nel driver firme, hash/riletture e backend nativo condividono la stessa deadline monotonic `budgetSeconds` (1–5s), senza reset tra riverifiche prima/dopo fsync. Nel preparer il verificatore condivide la deadline complessiva di preparazione (18s), oltre ai budget dei worker nativi. Timeout/scadenza/revoca prima del claim conserva READY; dopo il claim conserva STARTING senza FIFO/replay automatico. Rollback di risorse possedute e generazione morta non richiede una firma ancora valida.

**Verifiche sull'esatto commit:** 82 test locali PASS; CI Gateway **38/38 completed/success**. Log push e PR: **82 test +2 native admission**, Docker **6 test PASS**, inclusa prova reale adapter4/preparer3/driver5 con chiavi Ed25519 distinte e temporanee solo CI. Lease drift e firma alterata negano l'applicazione; firme valide consentono il marker del solo fixture. Nel negativo della firma Docker elimina il candidato fallito e il rollback porta preexec a ROLLED_BACK/admission CLEANED, mentre consumption resta READY; questo esito è verificato, non un reset. Sorgenti di tutti i 22 file del prossimo package riletti dal commit e hash confrontati.

**Ultima evidenza VPS resta §27 ESEGUITO/PASS**, package v5 `/etc/ouf/deploy-snapshots/semantic-authenticated-deployment-package-20261004-083518`, source `6697029e3efa03f9090bd7be13aab86784749731`. Nuovo codice provato in CI; non ancora copiato o installato sul target.

**Intervento §28 ESEGUITO/PASS, registro storico**, soltanto nuovo source package `ouf.semantic-authenticated-runtime-source-package.v6`: 22 sorgenti privati, checksum +plan/apply/verify. [Comando §28](https://github.com/GioNob/ouf-semantic-registry/blob/codex/r4a-smoke-semantic-inventory/docs/handoffs/commands/OUF_STAGE_AUTHENTICATED_RUNTIME_PACKAGE_V6_2026-10-04.sh) e [contratto operativo](https://github.com/GioNob/ouf-semantic-registry/blob/codex/r4a-smoke-semantic-inventory/docs/installation/SEMANTIC_AUTHENTICATED_RUNTIME_DRIVER.md). Nessuna chiave/policy/mandato generato, nessuna firma emessa, nessun runtime registrato, nessun container o regola/unità cambiato. Questo staging non è readiness o release acceptance. Dopo l'output §28 registrare ricevuta e root esatti, senza replay, poi completare gli elementi produttivi indipendenti prima di richiedere i binding di autorità indispensabili.

**Restano aperti:** broker/issuer/attestor produttivi con mandato esplicito della singola installazione; full image/OCI/rootfs creation acceptance; provisioning trust/policy/chiavi reali; snapshot atomico, enforcement/binding IPv6/spoof, OIDC/purpose/TLS/revocation admission, ciclo lease attivo/guard e reboot reale. Le prove CI di questo percorso non chiudono questi gate né autorizzano start/merge/replay. Ogni Ente è un'installazione indipendente, con servizi co-locati o distribuiti. Semantic/Registry governa discovery esterna tramite Gateway (default schema.gov.it parametrizzabile); MCP/chatbot propone, THS governa adozione/attivazione. Il ramo provider non sostituisce la prova file→mapping→ingestion→UDP.


## Checkpoint storico — riverifica autenticata, prima del collegamento al driver

Il §27 resta **ESEGUITO/PASS**: package privato `/etc/ouf/deploy-snapshots/semantic-authenticated-deployment-package-20261004-083518`, source `6697029e3efa03f9090bd7be13aab86784749731`. Nessun replay, avvio o installazione richiesto.

Il Gateway aggiunge in `aa18a7b09a8bb55a193a5bdbc9b382aed2467663` il callback `LateAuthenticatedEvidence`: rilegge tre evidenze private con hash vincolati, verifica realmente le tre firme e i mandati locali, confronta evidenceHash e scope con il driver sigillato, ricontrolla tutti i file/firme/policy e la scadenza anche dopo le riletture. Il consumer esistente lo può invocare sotto il lock comune prima e dopo il claim persistente STARTING. Revoca prima del claim mantiene READY; revoca dopo claim mantiene STARTING senza processo né replay implicito.

Validazione locale: **72 test PASS**, inclusi **8 nuovi test** con OpenSSL Ed25519 reale e PrivateJournal/flock; coperti consumo singolo, revoca prima/dopo fsync, modifica di una firma precedente durante verifica successiva, scope/hash estranei, deriva sorgente, scadenza approval e mandato dopo rilettura. Chiavi effimere solo nei fixture dei test. CI Gateway sul commit `aa18a7b09a8bb55a193a5bdbc9b382aed2467663`: **38/38 completed/success**; log push e PR: **72 test +2 native**, Docker **5 test PASS**. Il primo job summary-stack PR è fallito per porta effimera già occupata (Ingestion non avviato); rilancio mirato dello stesso job PASS. Questa instabilità del fixture resta da correggere separatamente. CI documentale del checkpoint `ac037bcaf58fff9f4a87ca04233b638f108a621e`: **13/13 PASS**; la revisione che registra questi esiti avrà propria CI, da verificare sul relativo commit.

**Limite e prossimo passo preciso:** callback composto/testato con il consumer, ma **non ancora collegato al bootstrap driver/preparer/adapter**; package v5 sul VPS rimane immutato e non contiene questo modulo. Integrare il percorso sigillato e il budget totale di verifica sotto lock, provarlo in CI con fixture indipendenti, prima di preparare un ulteriore intervento VPS. Le riletture non dimostrano snapshot atomico né impediscono un amministratore privilegiato non cooperante. Mandato reale, producer/attestor, chiavi/policy di produzione e readiness restano non provati.

Restano confermate le installazioni indipendenti per Ente e le responsabilità PET: Semantic/Registry esegue discovery esterna tramite Gateway; provider predefinito schema.gov.it parametrizzabile per installazione; chatbot/MCP propone attraverso capability tipizzate, THS governa adozione/attivazione. Questa infrastruttura serve il ramo provider esterno; non costituisce prerequisito universale del ciclo ingestion interno.


## Checkpoint storico — ricevuta §27 ESEGUITO/PASS

**Ultimo esito VPS, 4 ottobre 2026:** `/etc/ouf/deploy-snapshots/semantic-authenticated-deployment-package-20261004-083518`; checksum comando +20 sorgenti OK, plan/apply/verify PASS concordanti, Python3.13.5, source `6697029e3efa03f9090bd7be13aab86784749731`, schema `ouf.semantic-authenticated-deployment-source-package.v5`. Evidenza allegata dall'operatore, non accesso indipendente al VPS.

signatureVerifierInstalled/trustPolicyProvisioned/externalProducerInstalled/runtimeAdapterInstalled/admissionPreparerInstalled/runtimeRegistered/startAuthorized=false; keysGenerated/signaturesIssued/providerCalls=0; regole/unità/container invariati. Questo PASS sigilla sorgenti, non verifica un deployment reale e non conferisce authority. §27 e i vecchi snapshot sono immutabili; nessun replay richiesto.

**Prossimo lavoro repository:** collegare firme/custody e revoca delle tre evidenze alla reauthorization subito prima del consumo, sotto common guard/lease lock; testare diniego prima del claim e revoca dopo STARTING senza release del processo o replay. Il driver v4 attuale ricontrolla il solo approval binding hash/tempo; non dichiararlo già collegato al nuovo verificatore.

**Gate reali aperti:** broker/issuer/attestor produttivi, mandate/public trust keys per-Ente provisionati esplicitamente, full immagine/OCI/rootfs acceptance, closure source-sealed di integrazione e acceptance target. Nessun signing, key generation, runtime registration o startup implicito.

**Percorso conservato:** Semantic/Registry esegue discovery tramite adapter e Gateway southbound; chatbot/MCP invoca capability tipizzate e propone, THS governa decisioni HUMAN. Gap interno o richiesta esplicita autorizzata; default provider modificabile schema.gov.it. Ramo provider non è prerequisito universale di ogni ingestion. [Traccia PET](../sprints/OUF_FILE_TO_UDP_PROVIDER_DEPENDENCY_2026-10-04.md).

## Checkpoint precedente — §26 ESEGUITO/PASS; §27 allora NON ESEGUITO

§26 attestato dall'operatore in `/etc/ouf/deploy-snapshots/semantic-deployment-trust-backend-inventory-20261004-080455`: source custody 18 e stableAcrossReads PASS, receipt hash `1b5a340a11fa3a157fe83be7bddc2a4af5dd755eb78a003b7a3640e117647d0a`; OpenSSL 3.5.7, hash `f4aa15f2822f670af7b5c1043d7aa6ebbbc64229fd2fae382edfc6a4524749c1`, firma valida e due negative PASS. Authority/atomicità/runtime/start restano false; key generation/private-key reads/signature issuance/provider/DNS/IAM calls zero. Receipt operatore conservata; nessun replay §25/§26.

**Codice completato:** gateway `6697029e3efa03f9090bd7be13aab86784749731`, verificatore detached Ed25519 con scope key/role/issuer/installazione/Ente, policy esplicita hash-pinned, revoca/scadenza rilette dopo native verify bounded; nessun issuer/default/grant, signing o keygen di produzione. Nuovo source package v5 di 20 file. Locale 64 test pertinenti PASS, 14 auth nuovi + 2 package. [Contratto e limiti](../installation/SEMANTIC_DEPLOYMENT_AUTHENTICATION.md).

**CI codice finale:** gateway `6697029e3efa03f9090bd7be13aab86784749731`, 38/38 completed/success; log push/PR verificati: 64 unit/contract/package, 2 native admission, 5 Docker. Documento ricevuta §26 `e796a09c08b0c1a55e2e903cd83b12bebc03fa33`: 13/13 success dopo rerun del solo job fallito per download Maven Central HTTP403, senza modifica al codice.

**Percorso confermato sui PET:** Semantic v1.3 §§10–11,17–18,25–26 e74; Onboarding v1.6 §§9.3,12–13,92; MCP v1.4 confini/catalogo. Il chatbot può richiedere discovery tipizzata e proporre mapping; Semantic/Registry governa provider adapter e candidati; egress via Gateway southbound. Trigger: match interno inadeguato **o richiesta esplicita autorizzata**. Niente SPARQL arbitrario dall'Agent, né adozione/pubblicazione/activation HUMAN via MCP. Candidato esterno non è riferimento ACTIVE finché il workflow governato non lo rende tale.

**Decisione utente 4 ottobre:** provider predefinito `schema.gov.it`, modificabile per installazione (`schema.maggioli.it` è un esempio). SPARQL è il canale configurato quando disponibile, secondo Semantic §26.3; dominio non determina URL endpoint completo. Un Ente, un'installazione indipendente, servizi distribuiti o co-localizzati. [Traccia del ramo deploy rispetto a file → MCP → UDP](../sprints/OUF_FILE_TO_UDP_PROVIDER_DEPENDENCY_2026-10-04.md): non è una dipendenza universale di ogni ingestion. Guard/lease/OCI/firme sono scelte implementative per i confini PET; collaudo end-to-end resta aperto.

**Prossimo intervento necessario sul VPS:** §27 **NON ESEGUITO**, [staging privato v5](commands/OUF_STAGE_AUTHENTICATED_DEPLOYMENT_PACKAGE_V5_2026-10-04.sh), soltanto compile/hash/receipt di sorgenti nuovi. Verificatore/policy/producer non installati, nessuna key/firma emessa, regole/unit/container invariati; runtimeRegistration/start false. Non applicare policy o avviare componenti. Broker/issuer/attestor reali, acceptance completa, wiring signature prima del consumo sotto common lock e provisioning per-Ente restano il lavoro successivo; nessun gate target viene chiuso da CI/package PASS.

## Checkpoint precedente — §26 ESEGUITO/PASS; autenticazione allora in lavorazione

**Ultimo esito VPS, 4 ottobre 2026:** `/etc/ouf/deploy-snapshots/semantic-deployment-trust-backend-inventory-20261004-080455`. Custody dei 18 sorgenti v4 e stabilità fra letture PASS; receipt hash `1b5a340a11fa3a157fe83be7bddc2a4af5dd755eb78a003b7a3640e117647d0a`. OpenSSL `3.5.7`, hash `f4aa15f2822f670af7b5c1043d7aa6ebbbc64229fd2fae382edfc6a4524749c1`: firma pubblica valida accettata, messaggio e firma alterati respinti. Evidenza operatore, non accesso indipendente al VPS.

Authority/atomicSnapshot/runtimeRegistration/start restano false; chiavi generate/lette private, firme emesse, chiamate IAM/DNS/provider zero. §26 è storico: nessun replay richiesto. §25 e gli snapshot precedenti restano immutabili.

**Collegamento all'obiettivo:** file → MCP/chatbot → ricerca semantica interna → eventuale discovery esterna se il match interno è insufficiente → mapping Onboarding e THS → bundle ACTIVE → Ingestion/handoff → UDP e serving autorizzato. Il ramo esterno era disabled/non connesso: il percorso di deploy corrente chiude i suoi gate di rete/shared faces, guard/lease e admission. Il provider esterno non è un prerequisito universale del percorso interno o di ogni ingestion. Nessun gate end-to-end chiuso dalla disponibilità OpenSSL.

**Prossimo lavoro indipendente:** verificatore bounded di firme detached per intent, attestation e approval della singola installazione; niente emissione firme, chiavi di produzione, installazione, avvio o nuova authority. Esito CI/codice sarà registrato al successivo checkpoint. Il mandato e le trust key reali devono essere conferiti/provisionati esplicitamente; il broker sintetico CI resta escluso.

**Criterio di uscita dal ramo:** evidenze autentiche per la singola installazione; creazione reale/OCI/rootfs e namespace accettati; guard/lease coordinati; runtime e startup autorizzati esplicitamente; provider southbound con OIDC/purpose/TLS/revoca e least privilege verificati sul target. Poi ricongiungere il ramo allo sprint MCP/mapping, riusando il file e le prove esistenti. Le automazioni coprono queste configurazioni necessarie, senza introdurre nuovi moduli o ampliare il deployment generale. Reboot/atomic snapshot e gate ereditati restano tracciati; non inventare scorciatoie per il lab.

## Checkpoint precedente — §25 ESEGUITO/PASS; §26 allora NON ESEGUITO, inventario read-only

**Vincolo permanente:** un Ente, una installazione OUF indipendente; servizi distribuiti o co-localizzati anche nella stessa rete/sottorete. Nessuna authority centrale multitenant.

§25 registrato con ricevuta operatore e root `/etc/ouf/deploy-snapshots/semantic-deployment-package-20261004-072744`: 18 checksum OK, plan/apply/verify PASS, schema v4, source `cc161b94c1af014403dabd113200d3180f02089d`. Solo sorgenti privati; producer/preparer/adapter non installati, runtime non registrato, nessuna regola/unità/container cambiati, providerCalls=0, startAuthorized=false. Questo è l'ultimo esito VPS ricevuto.

**Lavoro completato:** inventario di custody v4 e prova pubblica OpenSSL/Ed25519, gateway `3c62e7a98957545623e3d3183e067d9c1bd4a6c8`. 48 test pertinenti locali PASS, 8 nuovi casi; confronto reale dei 18 hash dell'output operatore e CLI isolata PASS; verifica positiva e due negative reali. Nessuna generazione/accesso a chiavi private o emissione di firme. Il backend candidato è locale alla singola installazione; non attribuisce authority. [Dettagli e limiti](../installation/SEMANTIC_DEPLOYMENT_TRUST_BACKEND.md).

**CI gateway finale:** commit `3c62e7a98957545623e3d3183e067d9c1bd4a6c8`, 38/38 controlli completed/success; log verificati: 48 unit test + 2 native admission e 5 Docker, sia push sia PR. CI della ricevuta §25 `d033b0b8a3bfafaa405ea8f9745ac7c0c6e99f90`: 13/13 completed/success.

**Prossimo intervento VPS necessario:** §26 **NON ESEGUITO**, [comando immutabile](commands/OUF_INVENTORY_DEPLOYMENT_TRUST_BACKEND_2026-10-04.sh). Legge il pacchetto v4, verifica i suoi 18 hash contro la ricevuta operatore e misura il backend effettivo. PASS dell'inventario non equivale a backend funzionante: verificare tutti i booleani di verifica firma. Atomicità, authority reale, provisioning delle chiavi, runtime e startup restano non provati/non autorizzati. Non ripetere §25. Nessun merge/avvio/replay implicito.

## Checkpoint precedente — §25 ESEGUITO PASS; package v4 solo sorgenti privati

**Vincolo permanente approvato:** un Ente, una installazione OUF autonoma. Nessuna installazione centrale multitenant o authority condivisa tra Enti. Ogni installazione possiede identità, policy, configurazioni, dati e mandato infrastrutturale propri; i suoi microservizi possono essere distribuiti o co-localizzati nello stesso server/rete/sottorete.

**Codice completato:** gateway `cc161b94c1af014403dabd113200d3180f02089d` (PR56 draft). Nuovo `tools/semantic_provider_deployment_consumption.py`, adapter v3, preparer v2 e driver v4; schemi legacy restano accettati. Journal per candidato `ouf.semantic-deployment-consumption.v1`: STAGED → CREATING → CREATED → READY → STARTING → STARTED. Scope installation/Ente/CID/transaction, intent/config hash, OCI/generazione, evidence/approval e driver hash sono legati. Il broker source-sealed riceve tre fasi esplicite: authorize-create, record-created e prepare. La creazione parte dall'intento creation-only; attestazione e approval finali arrivano dopo il created-state indipendente. Il preparer v2 controlla READY/custody prima delle modifiche, verifica la stessa generazione reale e produce driver v4; il broker sigilla il driver una sola volta.

**Consumo e recovery:** il driver v4 invoca il consumer dentro la sezione critica common guard/lease lock di Preexec, dopo i controlli live. STARTING viene compare-and-replace/fsync prima della release FIFO; authority viene ricontrollata dopo il claim, immediatamente prima dello starter. Successo registra STARTED come tentativo native completato, non application readiness. Failure/crash/revoca tardiva/fsync non provato lasciano lo stato durevole per recovery esplicito; nessun reset, nuova adozione o replay automatico. Un diniego prima del claim non consuma READY. Il lock per CID dell'adapter resta distinto: ordine per-CID → common, senza acquisizione inversa. Autorità mutate da root fuori dal protocollo cooperante non sono escluse.

**Verifiche eseguite:** locale 82 test, **78 PASS e 4 native/Docker opt-in skip**. Nuovi: 11 consumer test, inclusi due processi reali sullo stesso PrivateJournal/flock con un solo consumo, failure di pubblicazione, revoca tardiva, cambio generazione/hash, fasi corrotte, doppio create/final/seal/start e callback sotto lock; 3 source-package v4 test; nuovo caso Docker opt-in. Head corrente **38/38 CI completed/success**, push e PR. Log di quattro job pertinenti letti: ciascun admission-preparer passa 40 unit/contract/package test e 2 native preparer/runc/nft senza skip; ciascun Docker job passa 5 test senza skip, legacy preservato e nuovo adapter v3 → preparer v2 → driver v4 reale, candidate created prima di approval finale, lease drift nega l'applicazione, positivo con marker reale e consumption STARTED, cleanup owned e default runtime preservato. I produttori sono sintetici esclusivamente nei test; nessuna acceptance VPS o authority target viene dichiarata.

**Package privato nuovo:** `scripts/stage_semantic_deployment_package.py`, schema `ouf.semantic-deployment-source-package.v4`, **18 sorgenti**. Compila in memoria senza eseguire i body dei tool, sigilla hash/receipt root-private e nega replay o drift. Nessun broker/issuer/attestor/authenticator di test incluso. runtimeAdapterInstalled/admissionPreparerInstalled/externalProducerInstalled/runtimeRegistered/startAuthorized=false, regole/unità/container invariati e providerCalls=0. Metadata trustedToolsAvailable non prova compatibilità runtime.

**VPS §25 ESEGUITO — attestazione operatore del 4 ottobre 2026:** checksum comando OK e 18 sorgenti OK, plan/apply/verify **PASS** concordanti in `/etc/ouf/deploy-snapshots/semantic-deployment-package-20261004-072744`, schema `ouf.semantic-deployment-source-package.v4`, source `cc161b94c1af014403dabd113200d3180f02089d`, Python 3.13.5. Attestazione `docs/handoffs/receipts/SEMANTIC_DEPLOYMENT_PACKAGE_V4_2026-10-04_OPERATOR.json`; nessuna lettura indipendente del VPS né digest del receipt dichiarati. externalProducerInstalled/runtimeAdapterInstalled/admissionPreparerInstalled/runtimeRegistered/startAuthorized=false; rulesChanged/unitsChanged/containersChanged=false, providerCalls=0, notReleaseAcceptance/noSecretsPrinted=true. Nove trustedToolsAvailable=true sono metadata, non compatibilità funzionale. Questo nuovo snapshot e i precedenti sono immutabili; §25 è storico e non va rieseguito automaticamente.

**Prossimo passo preciso:** predisporre il collegamento a produttori realmente autorizzati della singola installazione, con autenticazione delle evidenze distinta dal semplice hash/root ownership. Prima della selezione del backend crittografico sul target, verificarne disponibilità/versione/supporto senza generare chiavi, concessioni o approval. Mandati, identity binding M2M quando applicabile, full image/rootfs acceptance e configurazione del broker reale restano gate espliciti; nessun avvio o runtime registration autorizzato.

**Gate dopo staging:** individuare e configurare nella singola installazione i produttori realmente autorizzati e l'autenticatore bounded, implementare/validare il broker di produzione secondo l'interfaccia source-sealed (la fixture Docker non è deployable), verificare immagine/rootfs completa e custody target. Binding authority M2M A/B/C non è implicitamente scelto. Restano atomic snapshot, IPv6/spoof, OIDC/purpose/TLS/revoca applicativa, lease attiva, reboot e acceptance sul backend VPS. Migrazione/cohort/runtime registration e qualsiasi start richiedono passaggi espliciti successivi.

## Checkpoint precedente — installazioni autonome; contratto a due fasi approvato

**Decisione esplicita approvata dall'utente il 4 ottobre 2026:** ogni Ente installa e amministra il proprio OUF. Mille Enti significano mille installazioni indipendenti; nessuna installazione centrale multitenant, collegamento tra tenant o authority condivisa è implicita. Codice, contratti e strumenti di release sono comuni; identità, policy, configurazioni, dati e mandati infrastrutturali appartengono alla singola installazione. Dentro un'installazione i microservizi possono essere distribuiti su server/reti differenti o sullo stesso server nella stessa rete/sottorete. La scalabilità riguarda replicabilità, aggiornamenti/manutenzione automatizzati e carico locale.

**Responsabilità approvate:** installer/orchestratore con mandato infrastrutturale esplicito per intento e approval finale; verificatore sul nodo di destinazione per full creation acceptance. Due ruoli logici implementabili negli strumenti di installazione esistenti, nessun nuovo microservizio obbligatorio. IAM autentica gli attori, Authorization conserva le capability applicative secondo i PET; il mandato infrastrutturale non deriva da entityRef o dalla rete interna. Authority M2M A/B/C resta binding esplicito della singola installazione.

**Contratto implementato:** gateway `d0784285dc98651a732d1328ec2aef5cc0eb8955`, `tools/semantic_provider_deployment_protocol.py`, 18 test pertinenti in `tests/test_semantic_deployment_protocol.py` e workflow admission-preparer aggiornato. Sequenza: intento autentico creation-only → candidato creato fermo → attestazione autentica della creazione reale sul nodo → approval finale breve sugli hash OCI/transport/acceptance → successivi controlli live guard/lease prima di un eventuale avvio esplicitamente autorizzato. L'intento iniziale non contiene hash OCI non ancora disponibile e applicationStartAuthorized deve essere false. Approval finale non può precedere l'osservazione o superare la scadenza dell'intento. Intento e approval durano al massimo 300s; staging delle immagini precede l'emissione.

**Verifiche locali eseguite:** 18/18 nuovi test PASS; selezione regressioni 67 test, 64 PASS e 3 native/Docker opt-in skip, senza fallimenti. Dinieghi per altra installazione/autorità, ruolo errato, evidenze alterate, scope/hash/image/transport/runtime/constraints drift, acceptance falsa, generazione invalida, approval prematura, scadenza durante autenticazione, JSON duplicato/unbounded/nonfinite/nesting e revoca. Quattro file gateway riletti da GitHub e confrontati. **CI del nuovo head: 38/38 completed/success**, verificati push e PR. Log dei due job admission-preparer letti: ciascuno 26 test unitari/contratto/package (18 nuovi + 8 esistenti) PASS e 2 test native preparer/runc/nft PASS senza skip. Queste prove native restano sul preparer v3 esistente; non dimostrano la futura migrazione Docker a due fasi.

**Confini dell'implementazione:** validatore puro senza I/O, emissione/firma, image inspection, journal consumption o start. Autenticatore obbligatorio fornito dalla trusted integration, autorizzato per ruolo/issuer/installazione/Ente; solo True booleano accettato, nessun default permissivo né endpoint IAM hardcoded. Hash root-private da solo non prova identità. L'attestor reale deve ispezionare immagine/rootfs, OCI, vincoli e runtime; questi test usano produttori sintetici soltanto in CI. Output senza start flag, generazione e hash conservati per futura verifica live. Snapshot bounded non è atomic snapshot. Freshness ricontrollata dopo autenticazione; timeout del produttore resta responsabilità dell'integrazione.

**VPS attestato invariato dal lavoro repository:** §23 ESEGUITO plan/apply/verify PASS, `/etc/ouf/deploy-snapshots/semantic-admission-package-20261004-055825`, source ed6fab81acc17591a1087761266701f877233799, 15 checksum OK e schema source-package v3. Adapter/preparer non installati, runtime non registrato, start non autorizzato, providerCalls=0, nessuna modifica attestata a regole/unità/container. Il nuovo modulo non è in quel package immutabile. Comandi §20–§23 restano storici; nessun nuovo comando VPS e nessun merge/start/replay accompagnano questa decisione.

**Prossimo passo preciso:** integrare la sequenza nei contratti installer/adapter con journal durevole e consumo unico sotto common lock. L'adapter v2 esistente lega già approval/config finali prima di create: non è stato migrato e non può essere dichiarato compatibile con la nuova sequenza. Occorre congelare l'intento, ricevere evidenze finali dopo created-state indipendente, legarle alla stessa generazione e consumarle una sola volta; vietato ribindare un journal v2 esistente. Prove Docker complete, produttori/autenticazione concreti, acceptance immagine reale, atomicità, IPv6/spoof, OIDC/purpose/TLS/revoca applicativa, lease attiva e reboot restano aperti. L'approvazione architetturale non autorizza avvii o registrazioni runtime sul VPS.

Decisione e confini completi: `docs/architecture/OUF_INDEPENDENT_INSTALLATIONS_DEPLOYMENT_ADMISSION_2026-10-04.md`. Contratto gateway: https://github.com/GioNob/ouf-api-gateway/blob/d0784285dc98651a732d1328ec2aef5cc0eb8955/docs/SEMANTIC_DEPLOYMENT_PROTOCOL.md

## Checkpoint precedente — §23 ESEGUITO PASS; admission v3 solo sorgenti privati

Gateway PR56 commit `ed6fab81acc17591a1087761266701f877233799`, **38/38 CI check completed/success** (push e PR), log delle sei esecuzioni pertinenti letti. Locale: 51 test, 46 PASS e 5 native/Docker opt-in skip. Nuovo job preparer: 8 test unitari/source-package e 2 native senza skip; namespace PREPARED e OCI_CREATED, template isolato con host rules invariati, sorgente alterato negato, preparer sigillato, runc/nft reali, revoca prima del start negata, rollback live negato e cleanup owned. Shared job: 40 regressioni/inventari + 3 native rete/lease + 1 OCI reale senza skip. Docker job: 4 test, named runtime legacy positivo/negative/cleanup/default preservato. Queste sono prove sintetiche CI, non release acceptance VPS.

**Implementazione:** `scripts/semantic_provider_admission_preparer.py`, `tools/semantic_provider_deployment_admission.py`, `scripts/stage_semantic_admission_package.py`. Preparer source-sealed a dodici sorgenti e comandi con hash; intent per CID con intero documento OCI, receipt esterno di creation acceptance, approval esterna per issuer/Ente/installazione/CID/transaction/application/transport/creation hash, ACTIVE e validità massima 300s. Riutilizza soltanto lease custody/journal/common lock esistenti, QUIESCED e provider sets vuoti. Rifiuta NIC non approvate, MAC/IP/bridge/peer/runtime/PID drift. Non emette approval, non interroga IAM/DNS/provider, non è authorization applicativa. Driver v3 ricontrolla approval hash/scopo/expiry sotto common lock prima della release FIFO; v1/v2 restano compatibili. Revoca cooperante deve usare lo stesso lock; mutazioni privilegiate esterne non sono escluse.

**Footprint indipendente:** compilato in un namespace network nuovo con mirror bounded di nomi/indici approvati, non ricavato calibrando regole host. Worker rifiuta namespace del chiamante prima di ogni write. Configurazione lega anche hostNetworkNamespace: prepare/cleanup richiedono la custody host esatta, worker richiede parentNamespace uguale al valore sigillato e namespace corrente diverso. CI prova diniego dell'invocazione diretta host e parent falsificato, con host rules invariati. Binding live usa query ai soli indici selezionati, evitando inventari globali di migliaia di NIC. Adapter schema v2 effettua dispatch del preparer/config hash per CID e richiede grant v3/approval SHA corrispondente; un solo runtime/cohort nominato può servire candidati diversi. Dispatch v2 coperto dai contract test; la prova Docker completa resta sul percorso legacy e le prove v3 complete sono runc native. L'integrazione Docker v2/v3 target non è dichiarata provata.

**Recovery:** journal STAGED → PREPARING → PREPARED → PROTECTED → CLEANED; PREPARING/PREPARED interrotti non vengono adottati o ripetuti automaticamente. Cleanup richiede rollback indipendente e morte della generazione registrata anche se non ha raggiunto il hook. Recovery operativo delle fasi incomplete resta esplicito; nessun reset/rebind implicito. La CI ha corretto il confronto atime e una collisione del nome helper; l'esistente provider `tools/semantic_provider_admission.py` è ripristinato byte-per-byte, SHA256 `dca670d1f0ced678db6af9810199da07419901a21523385e0ebea623b608bbfc`. I fallimenti delle revisioni precedenti non sono PASS retroattivi.

**VPS §23 ESEGUITO — attestazione operatore del 4 ottobre 2026:** quindici checksum iniziali OK; plan/apply/verify **PASS** concordanti in `/etc/ouf/deploy-snapshots/semantic-admission-package-20261004-055825`, schema `ouf.semantic-admission-source-package.v3`, source commit `ed6fab81acc17591a1087761266701f877233799`, Python 3.13.5. Attestazione salvata in `docs/handoffs/receipts/SEMANTIC_ADMISSION_PACKAGE_V3_2026-10-04_OPERATOR.json`; nessuna lettura indipendente del VPS o digest del receipt dichiarati. admissionPreparerInstalled/runtimeAdapterInstalled/runtimeRegistered/startAuthorized=false; rulesChanged/unitsChanged/containersChanged=false, providerCalls=0, notReleaseAcceptance=true e noSecretsPrinted=true. Nove trustedToolsAvailable=true indicano disponibilità metadata, non compatibilità funzionale. §20/§21/§22 e snapshot precedenti restano storici e immutabili; l'ultimo guard attestato era RUNTIME_EMPTY/EMPTY_ONLY, non nuovamente verificato da questo receipt.

**Prossimo passo preciso:** chiudere la prova Docker adapter v2/driver v3 con preparer reale in CI isolata, senza assumere acceptance VPS. Prima di qualsiasi profilo/installazione/registrazione/start sul target occorrono produttori realmente approvati di deployment approval e full creation acceptance e custody target verificata. Nessun comando VPS aggiuntivo è autorizzato da questo receipt; §23 è storico, non da rieseguire automaticamente.

**Gate successivi:** issuer/attestor di deployment realmente approvati, creation acceptance completa e authority infrastructure target, profili e journal/common lock sigillati, compatibilità template/backend VPS, integrazione Docker v2/v3, atomic snapshot, OIDC/purpose/TLS/revoca applicativa, lease attiva e reboot restano aperti. Approval JSON root-private con hash è un artefatto trusted del deployer, non verifica una firma IAM o autentica da solo issuerRef; il produttore approvato deve essere identificato prima dell'uso reale. Migliaia di Enti, host/reti distribuiti e co-localizzazione nella stessa rete/sottorete restano vincoli permanenti; backend bridge IPv4 è una realizzazione, non un default della piattaforma.

## Checkpoint VPS attestato — §22 ESEGUITO; nuovo source package v2 PASS

Output operatore ricevuto il 3 ottobre 2026 alle 23:31 Europe/Rome: **§22 ESEGUITO, plan/apply/verify PASS**. Nuovo package `/etc/ouf/deploy-snapshots/semantic-preexec-adapter-package-20261003-213033`, schema `ouf.semantic-preexec-source-package.v2`, source commit `b5260260fff1adf798626f12e24323c20ae1bb2e`; dodici checksum iniziali OK e dodici sourceHashes attestati, Python 3.13.5. Receipt e flag concordanti nei tre output. Attestazione operatore registrata in `docs/handoffs/receipts/SEMANTIC_PREEXEC_PACKAGE_V2_2026-10-03_OPERATOR.json`; nessuna lettura indipendente del VPS né digest del receipt dichiarati.

**Effetto attestato limitato ai sorgenti privati:** runtimeAdapterInstalled=false, admissionPreparerInstalled=false, runtimeRegistered=false, startAuthorized=false; rulesChanged/unitsChanged/containersChanged=false, providerCalls=0, notReleaseAcceptance=true, noSecretsPrinted=true. trustedToolsAvailable è true per busybox/ip/nft/nsenter/python/runc/unshare e indica solo metadata, non compatibilità funzionale. Package v1 e snapshot precedenti restano immutabili. Il comando §22 è ora storico: non rieseguirlo automaticamente.

**Validazione codice già completata:** gateway `b5260260fff1adf798626f12e24323c20ae1bb2e`, 36/36 CI check success, riconfermati dopo il receipt; Docker adapter positivo/negative/owned cleanup, 38 regressioni/inventari + 3 native rete/lease + 1 OCI reale senza skip nelle rispettive esecuzioni. Locale 36 PASS e 3 Docker opt-in skip. Docker prepara la rete fra NewTask e Task.Start: admission al proprio start verifica CID/bundle/PID/generazione/owned tables/lease prima del rilascio dell'applicazione, mantenendo il common guard/lease lock fino a runc start. Default/cohort invariati; CI sintetica non è acceptance VPS. Ultima documentazione precedente `215e63dfd6e284f0f5be29937f28fe372b71adaa`, CI 13/13 success.

**Custody target:** §20 e §21 restano ESEGUITI PASS; due candidati runc mai avviati e nessun binding namespace live provato da quegli inventari. Ultimo guard attestato RUNTIME_EMPTY/EMPTY_ONLY: questo staging non lo verifica nuovamente né conferisce readiness/authority. Nessuna registrazione runtime, reload/restart, ricreazione, avvio, merge o replay implicito.

**Prossimo lavoro tecnico preciso:** preparer di admission di produzione e compilazione indipendente del footprint, con contratto di approval/authority, binding live e recovery espliciti; la fixture sintetica CI non può essere installata o riusata come preparer di produzione. Usare il nuovo package v2 come radice source-only attestata, senza alterarlo. Prima di qualunque piano di registrazione/start target restano infrastructure authority reale, full creation acceptance, atomic snapshot, OIDC/purpose/TLS/revoca, lease attiva e reboot. Migliaia di Enti, host/reti distribuiti e co-localizzazione sulla stessa rete/sottorete restano vincoli permanenti. Nessun nuovo comando VPS di registrazione/start è autorizzato o presentato da questo receipt.

## Checkpoint precedente — inventario candidati VPS ESEGUITO; adapter Docker da implementare

Gateway PR56 head `6e84e5ca1134cd8e26b603380a0adcb06a15fb0c`. Helper nuovo `scripts/inventory_semantic_preexec_candidates.py`, SHA256 `63fb3da6682861cd033c236a2830668bb4648b27ddc139799a05a8c62652f0bb`. Readback di helper, test, workflow e protocollo su GitHub verificato. Locale: **32 PASS + 2 Docker opt-in skip**, Docker assente nel workspace. **Job dedicati 111284288072 e 111284295941 completed/success**, log letti: ciascuno **34 test (32 regressioni + 2 Docker reali), 3 prove native di rete e 1 prova OCI reale senza skip**; runc 1.5.1. **CI complessiva verificata sull'esatto head: 34/34 completed/success, nessun pending/failure.**

Ultimo intervento VPS §20 **ESEGUITO plan/apply/verify PASS**, undici hash OK; package root `/etc/ouf/deploy-snapshots/semantic-preexec-package-20261003-195926`, source `1a020edea42cdf60a38298bec2ffebc97b3fad02`, Python 3.13.5, strumenti metadata tutti presenti. Il package sigillato resta immutabile, runtimeRegistered/startAuthorized=false e nessuna modifica di rule/unit/container.

**Ultimo intervento operatore: handoff §21 ESEGUITO, inventario candidati PASS; source root `semantic-preexec-candidate-inventory-20261003-203221`.** Il comando pubblica un nuovo snapshot privato del solo helper e legge candidati/reti tramite socket Docker locale, CLI config privata vuota, ambiente minimale e proiezioni allowlist. Lega manifest/creation journal agli hash attestati e network receipt al manifest; controlla custody CREATED/PID zero/mai avviato/restart no, runtime assegnato, network/IPAM/alias configurati, owner/bridge e assenza di membri estranei sulle sole reti dedicate. Due letture concordanti e rilettura dei file attestano stabilità osservata, mai atomicità. Output ridotto a hash/runtime/conteggi, niente Env/mount/comandi/indirizzi o namespace path. Non usa il vecchio inventario DENY_ONLY per accettare il nuovo guard RUNTIME_EMPTY.

**Rischi e decisione documentati prima dell'implementazione:** (1) endpoint configurati differiti non sono namespace live: NetworkID vuoto ammesso con verifica separata del network ID e liveNamespaceBindingProven=false; (2) letture Docker multiple non sono atomiche: drift blocca ma atomicSnapshotProven=false; (3) inspect integrale/ambiente ereditato/output illimitato potrebbero esporre segreti, selezionare host remoto o consumare memoria: proiezioni allowlist, socket locale, configurazione privata vuota, output 128 KiB e deadline totale 30 s. Test negativi coprono start/drift/ownership/IPAM, duplicati JSON, output e deadline; Docker reale prova il helper CLI con due nuovi candidati sintetici mai avviati, ripuliti dopo la prova.

La documentazione ufficiale Docker richiede registrazione esplicita per runtime drop-in runc o integrazione shim containerd: [Alternative runtimes](https://docs.docker.com/engine/daemon/alternative-runtimes/). Decisione ordinaria: progettare un'integrazione nominata e scoped, preservando default/cohort; nessun cambio globale per aggirare binding non provati. Runtime osservato non prova che il gate sia invocato. Il wrapper/shim di integrazione Docker **non è ancora implementato né provato**. Authority reale, binding namespace/PID/veth live, admission OIDC/purpose/TLS/revoca, lease attiva e reboot rimangono aperti. Nessuna registrazione/reload/restart/ricreazione/start/merge/replay impliciti. Topologie distribuite e co-localizzate, migliaia di Enti e assenza di default IP/bridge fixture restano requisiti permanenti.

## Inventario candidati VPS — ESEGUITO, PASS (3 ottobre 2026)

Output operatore ricevuto alle 22:32 Europe/Rome: source root `/etc/ouf/deploy-snapshots/semantic-preexec-candidate-inventory-20261003-203221`. SHA256 del helper OK; schema `ouf.semantic-preexec-candidate-inventory.v1`, **PASS READ_ONLY=true**. Due candidati, candidateRuntimes=[runc], candidatesNeverStarted=true, configuredBindingsMatchManifest=true, configuredNetworkCount=3, sandboxKeyPresentCount=0 e stableAcrossReads=true. Tre reti configurate non implicano tre interfacce live; l'assenza di SandboxKey nell'inspect non prova l'assenza di ogni namespace sul sistema.

| Binding verificato dall'inventario | SHA256 |
| --- | --- |
| bindingHash | `0337655a5c3d6d80653aca363d8479ce10e6d27cde024518060a6c628e542aeb` |
| manifestHash | `052b46a56ea666971f135c75af48b3342dbeb68e2f17f1f16263a99351df88bd` |
| creationJournalHash | `a1c2acd9924fc0f924ded7c2d59f128ef2d8b8dd11c62484a901f628022aaae7` |

atomicSnapshotProven=false, fullCreationAcceptanceProven=false, liveNamespaceBindingProven=false, ociHookIntegrationProven=false, runtimeRegistrationAuthorized=false, startAuthorized=false; providerCalls=0, notReleaseAcceptance=true, noSecretsPrinted=true. Nessuna modifica rule/unit/container attestata dall'operatore. Questa è evidenza del comando di inventario sul target, non una nuova verifica del guard runtime o acceptance di avvio.

**Handoff §21 ESEGUITO: conservarne il comando come registro, non rieseguirlo automaticamente.** §20 resta ESEGUITO PASS, package e vecchi cohort immutabili. Ultimo guard runtime attestato RUNTIME_EMPTY/EMPTY_ONLY; questo inventario non lo aggiorna né lo riconferma atomicamente.

**Prossimo passo autonomo preciso:** implementare e provare in CI un adapter Docker nominato e scoped che colleghi la preparazione del bundle/namespace al gate OCI prima del processo applicativo, con binding indipendente al manifest approvato, common lock e journal di guard/lease. Le prove positive/negative devono usare cohort sintetici separati, coprire create/start/delete e crash/rollback, dimostrare che gli errori del gate impediscano il processo e preservare default runtime/cohort esistenti. Solo dopo codice e CI verificati preparare un nuovo package privato e il relativo piano target reviewable. Non c'è un nuovo comando VPS pronto in questo checkpoint.

**Decisione derivata dall'evidenza:** non costruire un profilo prepared-namespace target da indirizzi soltanto configurati o da un SandboxKey assente, e non assumere che i candidati assegnati a runc invochino il driver standalone sigillato. L'eventuale registrazione runtime, reload e gestione del nuovo cohort saranno azioni target esplicite e separate; nessun avvio, ricreazione, replay o merge implicito. Authority di infrastruttura e admission reale non sono conferite da questo PASS e restano gate aperti insieme a coordinazione lease attiva e reboot. Distribuzione su reti/host differenti e co-localizzazione nella stessa rete/sottorete per migliaia di Enti restano vincoli permanenti.


## Checkpoint precedente — source package VPS ESEGUITO; integrazione Docker da verificare

Gateway PR56 head `1a020edea42cdf60a38298bec2ffebc97b3fad02`. **Job dedicati 111273368756 e 111273359644 completed/success**: ciascuno **29 test (28 regressioni + 1 Docker reale), 3 prove native di rete e 1 prova OCI reale senza skip**; log letti. Entrambi riportano **runc version 1.5.1**, la stessa versione standalone rilevata sul VPS. **CI complessiva verificata sull'esatto head: 34/34 completed/success, nessun pending/failure.** Localmente 28 PASS + 1 Docker opt-in skip, con dipendenze riallineate all'esatto source remoto. Undici sorgenti del package letti da GitHub e confrontati esattamente; comando staging controllato con bash -n.

La nuova prova esegue il driver source-sealed con runc, nft, namespace/veth, lock e journal privati reali. Source tamper, start authority assente, lease non quiescente, MAC/bundle drift impediscono l'applicazione; create valido lascia assente il marker fino allo start esplicito; rollback con generazione viva e nuova creazione con handle estranei sono rifiutati. Fixture con sola shell statica e authority sintetica, nessun provider chiamato. Corrette le dipendenze CI senza rimpiazzare il runtime Docker del runner e l'isolamento stdio/dev della fixture. I fallimenti delle revisioni precedenti sono storici, non PASS retroattivi.

| Componente nuovo | SHA256 |
| --- | --- |
| `scripts/stage_semantic_preexec_package.py` | `bf86bc438c39a1f8f7752797110bcfcf18b9e7deb23a662f850fffb900df2fd8` |
| `scripts/semantic_provider_preexec_hook.py` | `e904774d50626e3ce93d6bcd187571b03d0698ad6a7472a7b6a862b4816eb850` |
| `tools/semantic_provider_preexec_native.py` | `c45d343308a311790bcd5c9ed9687925d4af0fec59f96fc79f4af7a685b8c70f` |

Decisione: prepared-namespace/static IPv4 come primo backend sincrono, separato dal contratto di identity/authority/flow e lifecycle. Il driver root/Python -I -B verifica dieci sorgenti prima degli import, bundle privato, namespace inode, veth peer/ifindex, bridge, MAC/IP e PID/start ticks; rifiuta hook successivi capaci di modificare la rete. Nessuna assunzione Docker/IP/bridge fixture diventa default di piattaforma. Migliaia di Enti e distribuzione/co-localizzazione rimangono invarianti permanenti.

**Ultimo intervento operatore: §20 ESEGUITO, plan/apply/verify PASS; package `semantic-preexec-package-20261003-195926`.** Undici file pin/hash, receipt esclusiva/fsynced e tool availability/Python version rilevati via metadata. Non crea profilo driver, namespace, coordination journal, hook OCI installato, tabelle, unità, runtime registration o container. Non avvia processi applicativi/owner; source staging non abilita lease. Il source receipt non è acceptance, tool presence non prova static busybox né backend target utilizzabile.

**Limiti aperti:** la prova è standalone runc in CI, non Docker del VPS né startup/admission target. Occorrono profilo/binding/authority reali, template indipendente, integration/wrapper o shim con registrazione esplicita, gestione cohort e lifecycle servizi/reboot. Default runtime e vecchi candidati restano invariati; nessun reload/restart, merge o replay impliciti. Target resta RUNTIME_EMPTY/EMPTY_ONLY, due candidati mai avviati, providerCalls=0/startAuthorized=false. Inventario VPS §19 **ESEGUITO PASS**, source `semantic-preexec-runtime-inventory-20261003-183915`, Docker 29.8.1/default runc e runc standalone 1.5.1; il percorso invocato da Docker non è dimostrato dal numero di versione.

## Source package VPS — ESEGUITO, PASS (3 ottobre 2026)

Output operatore ricevuto e registrato: **plan/apply/verify PASS**, tutti gli undici SHA256 OK. Package root `/etc/ouf/deploy-snapshots/semantic-preexec-package-20261003-195926`; receipt `source-package-receipt.json`, schema `ouf.semantic-preexec-source-package.v1`, source commit Gateway `1a020edea42cdf60a38298bec2ffebc97b3fad02`. Python **3.13.5**; busybox/ip/nft/nsenter/python/runc/unshare risultano tutti disponibili secondo il controllo metadata dello stager.

**Comando handoff §20 ESEGUITO: conservarlo come registro, non ripetere apply.** PRIVATE_SOURCE_ONLY=true; runtimeRegistered=false, startAuthorized=false, rulesChanged=false, unitsChanged=false, containersChanged=false, providerCalls=0, notReleaseAcceptance=true, noSecretsPrinted=true in tutti i modi. Evidenza ricevuta dall'operatore, distinta dalle prove CI: nessuna verifica dell'integrazione Docker o dell'admission target può essere dichiarata superata da questa receipt.

**Prossimo passo preciso:** preparare e verificare il contratto di integrazione Docker e un inventario privato dei binding dei candidati fermi e delle reti, vincolato ai manifest/journal già sigillati. Il successivo comando VPS dovrà essere di sola lettura e pubblicazione di evidenza privata, senza registrazione runtime, reload/restart, modifica cohort o avvio. Namespace live, authority di infrastruttura, admission OIDC/purpose/TLS/revoca, coordinazione lease attiva e reboot restano gate aperti. Nessun indirizzo o bridge osservato diventa default di piattaforma; restano obbligatorie topologie distribuite e co-localizzate per migliaia di Enti.


## Inventario runtime VPS — ESEGUITO, PASS (3 ottobre 2026)

Output operatore ricevuto: source root `/etc/ouf/deploy-snapshots/semantic-preexec-runtime-inventory-20261003-183915`. Schema `ouf.semantic-preexec-runtime-inventory.v1`, Docker serverVersion **29.8.1**, defaultRuntime **runc**, runtimeNames **io.containerd.runc.v2, runc**, runcBinaryVersion **1.5.1**. READ_ONLY=true, stableAcrossReads=true, atomicSnapshotProven=false, ociHookIntegrationProven=false, runtimeRegistrationAuthorized=false, startAuthorized=false, providerCalls=0, notReleaseAcceptance=true, noSecretsPrinted=true. Righe JSON e PASS attestate dall'operatore; nessuna modifica rule/unit/container.

**Comando §19 ESEGUITO: conservarlo come registro, non ripeterlo.** Il binario runc locale non è prova che Docker utilizzi quel percorso; l'inventario non autorizza registrazione runtime, avvio o restart. Prossimo lavoro autonomo: backend con binding live e verifica sincrona OCI prima del processo, prove positive/negative reali e nuovo staging sealed; Docker target e authority rimangono gate separati.

## Checkpoint precedente — core install/recovery e inventario runtime (82d1db7)

Core Gateway `a0473e397d90d46cda2ca33404670c514dd435c9`: **34/34 check completed/success**, nessun pending/failure; job 111261718405 e 111261707562 ciascuno **19 regressioni + 3 prove native PASS senza skip**. Head corrente Gateway PR56 `82d1db716b1015dac52feca217af1c5ed600a520`: job dedicato 111264097837 **PASS, 24 test (23 regressioni + 1 Docker reale) e 3 prove native senza skip**, log controllato. È PASS anche il job 111263877173 del precedente d0fa3d1. **Verifica successiva sull'esatto head: CI complessiva 34/34 completed/success, nessun pending/failure.** Validazione locale: 23 PASS e 1 Docker reale skip perché assente nel workspace. Readback dei file pubblicati e dei quattro documenti verificato.

Il nuovo core `tools/semantic_provider_preexec.py` (SHA256 `5086f893ac22e962816e76709883c9c7f341989919339c579a4f28bfbd403804`) implementa STAGED/INSTALLING/PROTECTED/REMOVING/ROLLED_BACK, installazione esclusiva atomica delle due tabelle, ownership/readback, journal fsynced e lock comune con coordination, recupero esplicito dopo crash e rollback solo con generazione provata morta. Liveness sconosciuta non equivale a morte. Rifiuta replay apply, tabelle/handle estranei, footprint/binding/generazione alterati e lease non quiescenti. Footprint indipendente e commento transaction univoco sono prerequisiti del driver.

Il helper `scripts/inventory_semantic_preexec_runtime.py` è ora verificato con Docker reale in CI. Legge soltanto serverVersion/defaultRuntime/runtimeNames e versione runc locale, da socket locale root-owned e CLI configuration privato vuoto. Non eredita DOCKER_HOST/proxy/credential helper e non stampa daemon config/argomenti/credenziali. Corrette e testate due incompatibilità emerse in CI: newline finale aggiuntivo del formatter Docker e timestamp di accesso del socket; resta controllata l'identità device/inode/mode/uid/gid/nlink. SHA256 helper `5caf118353fbb49457ad083bdcf26e778413ba9ea699978ce52465a8480860e1`.

**Limite esplicito:** core con backend/driver iniettati, non hook OCI distribuito né registrazione Docker. La prova nativa del lifecycle usa un processo fixture già vivo e verifica namespace/PID/start ticks; **non prova protezione prima dell'esecuzione dell'applicazione**. Restano source-sealed driver/staging, aggancio OCI reale, integrazione runtime target e migrazione servizi guard/owner. Una versione runc locale non prova che Docker usi quel binario; letture stabili non provano snapshot atomico o compatibilità OCI.

**Inventario read-only del §19 ESEGUITO, PASS:** output e source root nel nuovo checkpoint sopra. Il comando è registro storico e pinna source/hash verificati; non ripeterlo. Conservare output e nuovo source root, fermarsi su BLOCKED senza replay di runtime apply. Runtime rilevato: Docker 29.8.1/default runc, versione standalone 1.5.1. Integrare e provare il driver; l'inventario non dimostra il percorso binario usato da Docker. Nessuna registrazione/avvio/restart autorizzati dall'inventario.

Restano attestati i comandi VPS già **ESEGUITI** ai §§11–16: intent privato, staging, runtime plan/apply/verify RUNTIME_EMPTY e readiness read-only PASS. Stage `semantic-runtime-transition-stage-20261003-160211/prepared`, readiness source `semantic-runtime-readiness-20261003-165430`; **EMPTY_ONLY**, due candidati mai avviati, zero provider call, start non autorizzato. Nessun merge, avvio/replay, Docker restart, mutazione target o riattivazione lease eseguiti da questo lavoro. Scala di migliaia di Enti e topologie distribuite/co-localizzate rimangono vincoli permanenti; backend Linux non diventa default universale. PET e business acceptance conservati.

## Checkpoint precedente — shared-face compiler e core guard/lease verificati (d382891)

Dopo la richiesta dell'operatore «Proseguiamo con enforcement sulle interfacce condivise e coordinazione guard/lease», Gateway PR56 contiene il commit `d38289132e49c9e9be4cb6245bb70a63cfaa82dc` (precedente `2a4499fb17e174f57c5f557d1fdaace793e8ec06`). **CI sull'esatto head: 34/34 completed/success**, nessun pending/failure. I job `shared-face-lease-coordination` 111254451253 e 111254440087 hanno eseguito ciascuno **9 regressioni + 2 prove native PASS senza skip**. Readback esatto dei sei file nuovi/modificati. Nuovi test locali: 9 eseguiti PASS, 2 native skip perché questo workspace non ha nft/ip/netns; la prova nativa è CI, non VPS. Nessun merge.

| Componente software nuovo | SHA256 / risultato |
| --- | --- |
| `tools/materialize_semantic_shared_faces.py` | `b97f31cc17c22abbb7a021c274be73816f649196762f9c6dfcc54a58d8382e8a` |
| `tools/semantic_provider_lease_coordination.py` | `25c6df90d33e39fe83321df6ab9e5c38d4c33bcd290ad57c7a85c03b1bb8ba78` |
| Fixture shared faces | Same-subnet, routed-network e host-local positivi; porte/peer non governati, spoof IP/MAC e peer port negati; altri peer IPv4/IPv6 conservati; rinomina conserva binding ifindex |
| Fixture coordination | DNS locale fresco A+AAAA, nft timeout sets, flock comune e journal root privato/fsynced reali; quiesce/revoke, nuova risoluzione dopo riattivazione esplicita, gate incompleto e handle ricreati negati |

Decisione architetturale coerente con scala di qualche migliaio di Enti e topologie distribuite/co-localizzate: contratti identity/authority/flow e lifecycle separati dal backend di enforcement. Il backend Linux seleziona port ifindex+bridge+MAC+IPv4 dei workload e ingress kind/index del peer, senza applicare default-deny all'intero bridge shared. Ogni flow dichiara authorityRef e coppia/protocollo/porta esatti; un ref dichiarato non prova approval. IPv6/VLAN/data non governati sono negati sulle porte selezionate in questo backend iniziale IPv4, preservati sugli altri peer. Fixture routed non prova multi-server/tenant acceptance né SLO a migliaia di Enti.

Il core `Coordinator` usa il medesimo boot lock durante DNS fresco/apply/readback/pubblicazione. Fasi LEASE_READY → LEASE_UPDATING → LEASE_READY; QUIESCING prima della revoca e QUIESCED soltanto dopo empty readback; BLOCKED su failure. `PrivateJournal` compare-and-replace/fsync sotto lock, root:root0600/nofollow/single-link/bounds/duplicate checks; lock inode esistente riusato, non creato. Config/DNS/hash handle dell'owner congelati e ricontrollati; membership autorizzata dal receipt dell'ultimo ciclo, TTL finita, niente cached TTL replay, auto-reactivation o ricreazione/rebinding automatico. startAuthorized resta sempre false. Il journal attuale EMPTY_ONLY non è adottato da questo protocollo nuovo.

**Questi componenti non sono installati sul VPS e non costituiscono ancora un nuovo profilo deploy completo.** Il target resta al §16 PASS: RUNTIME_EMPTY, guard EMPTY_ONLY, 2 candidati mai avviati, provider sets vuoti, zero DNS/provider calls, avvio non autorizzato; source cohort target `ef2270a57446da1f23a58548aa4d44920e578fe0` e hash config/journal/lease attestati invariati. Nessun comando VPS, restart, reboot, start o lease activation eseguito in questa fase.

Gate di integrazione concreto: il binding namespace/ifindex/iflink/parent/MAC/IP/generazione deve essere verificato e protetto **prima dell'esecuzione applicativa**. Un listener Docker post-start sarebbe una finestra di bypass e non viene scelto. I candidati mai avviati attuali non forniscono tale prova o il lifecycle di ricreazione delle porte. Occorre integrare un meccanismo runtime sincrono network-before-process e un nuovo installer sealed con recovery/rollback, owner/guard service lifecycle e migrazione dall'EMPTY_ONLY; non cambiare cohort/manifests/reti produttive per comodità. Nessun nuovo apply target è predisposto.

Protocollo e limiti: [documento Gateway fissato](https://github.com/GioNob/ouf-api-gateway/blob/d38289132e49c9e9be4cb6245bb70a63cfaa82dc/docs/SEMANTIC_PROVIDER_SHARED_FACE_LEASE_PROTOCOL.md). Rischi verificati: spoof da porta distinta anche con IP+MAC falsificati; port rename/reparent; race restore vs writer (lock denial), incomplete gate e revoca fallita; source/authority injection, journal/config/DNS/handle drift; foreign journal preservato. Restano authority/shared-face live binding, bootstrap pre-process, real IPv6 dove richiesto, OIDC/purpose/TLS/revocation admission, real reboot, tenant/distributed/load acceptance e gate Semantic/Discovery/THS/file/API→UDP/Search. PET e business evidence conservati.

## Requisito architetturale permanente e vincolante — scala Enti e topologie indipendenti

**Istruzione esplicita dell'operatore, 3 ottobre 2026: OUF sarà ragionevolmente adottata da qualche migliaio di Enti. Deve supportare microservizi su reti e server differenti e installazioni su un unico server nella stessa rete/sottorete. Questo requisito governa ogni scelta architetturale, implementazione, test e procedura di installazione futura.**

- La posizione di rete non conferisce identità, fiducia, tenant authority o autorizzazione. I medesimi contratti di autenticazione/autorizzazione, segregazione e transito obbligatorio attraverso Gateway devono valere anche fra servizi sullo stesso host o nella stessa sottorete.
- Endpoint, porte, service identity, trust/secret reference, tenant binding e policy devono essere parametri espliciti e governati per installazione. Nessuna dipendenza obbligatoria da IP, nomi Docker, bridge, subnet, percorsi host o domini del laboratorio.
- Gli adapter di deployment/enforcement possono differire fra topologie, ma devono preservare invarianti di default-deny, protezione SSRF/DNS/redirect, prevenzione del bypass e isolamento applicabile fra Enti. Non assumere che firewall inter-subnet o bridge dedicati siano presenti o sufficienti.
- Installazione, registrazione delle capability, configurazione, upgrade, riconciliazione e verifica devono essere automatizzabili e idempotenti; niente procedure manuali ripetute per ogni Ente/capability. Parametri e ownership devono permettere convivenza senza collisioni e deployment separati.
- Validare sia topologia distribuita su host/reti distinti sia topologia co-localizzata su singolo host e stessa sottorete, includendo negative-path di accesso diretto/bypass e isolamento fra Enti dove condividono risorse. Non dedurre scalabilità o performance a migliaia di Enti da fixture del laboratorio: servono profili di carico e SLO rappresentativi.
- Il profilo Docker/nft di ouf-lab è una realizzazione di deployment, non il contratto generale della piattaforma. Conservare le evidenze già ottenute, senza universalizzare dettagli locali né riscrivere il lavoro validato per convenienza.

La previsione di qualche migliaio di Enti non impone automaticamente migliaia di tenant nella stessa istanza: cardinalità, deployment condivisi/separati, isolamento e capacità vanno dichiarati nei profili. Ogni proposta futura deve spiegare come funziona nelle due topologie, senza ampliamenti impliciti di authority o bypass dei confini PET. Se una soluzione copre soltanto il laboratorio, dichiarare il limite e mantenere il gate portabilità aperto. Non chiudere R-INSTALL o scalabilità sulla sola CI.

Questo requisito si aggiunge alle regole permanenti di validazione/autonomia/checkpoint e va conservato in ogni nuovo handoff. Registrazione documentale: nessuna modifica al runtime VPS e nessuna nuova prova di scala/topologia dichiarata.

## Checkpoint target attestato — inventario readiness VPS ESEGUITO, PASS; gate startup aperti

Il 3 ottobre 2026 alle 16:54 UTC (18:54 Europe/Rome) l'operatore ha eseguito il comando §16 e restituito `SEMANTIC_RUNTIME_READINESS_INVENTORY=PASS READ_ONLY=true STARTUP_READY=false START_AUTHORIZED=false NO_IAM_OR_DNS_CALL=true NO_RULE_UNIT_CONTAINER_CHANGED=true NO_SECRETS_PRINTED=true`. Source snapshot attestato: `/etc/ouf/deploy-snapshots/semantic-runtime-readiness-20261003-165430`. Helper Gateway `4daad06b71695ad839d1865e55d5aeaf765df861`, checksum `ecb0326b9f97f76598d9bad56aa241b01802bf0a601f4eda38fef41fb15c655a`; runtime cohort originale resta `ef2270a57446da1f23a58548aa4d44920e578fe0`.

| Binding runtime attestato | Valore |
| --- | --- |
| Stage root | `/etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/prepared` |
| configurationHash | `24968cf990a32b87f3169b9226fe63d224c93a403540afec197011fbd670b0bb` |
| journalHash | `4ccb05b0a28b6e7e823de3d9af81f29255d60b38271d0a74a00f64e2e5828a74` |
| leaseStructureHash | `26f6f80af9d1e4898c1a6fe6dc8721cd6f67f1ceed05c7eea35e3b9f4a040e54` |
| Custody / stato / guard | runtimeCustodyVerified=true, RUNTIME_EMPTY, EMPTY_ONLY |
| Candidati | 2, candidatesNeverStarted=true |
| Regole statiche | 9; purpose DNS e GATEWAY_ADAPTER |
| Provider / interfacce | 1 provider flow, insiemi vuoti; 2 guarded interfaces, 4 shared interfaces escluse |
| Limiti | stableAcrossReads=true, atomicSnapshotProven=false; startupReady=false, activeLeaseLifecycleReady=false; DNS/provider calls 0; notReleaseAcceptance=true |

**Custody, intent, staging, runtime plan/apply/verify e readiness sono completati nel proprio scope. Non ripetere §§6,11–16.** L'inventario ha verificato binding e stato corrente senza promuoverli ad authority/startup/packet acceptance. In particolare le 9 staticFlows non contengono WORKLOAD_GATEWAY o IDENTITY; l'assenza di tali purpose non prova da sola l'assenza di ogni percorso host, ma richiede un piano autoritativo per i percorsi necessari e l'enforcement sulle shared faces. Nessuna regola shared o permesso è stato inventato.

Restano sette gate esplicitamente non provati: INFRASTRUCTURE_AUTHORITY, SHARED_FACE_SOURCE_ENFORCEMENT, LIVE_NAMESPACE_ADDRESS_BINDING, PACKET_SPOOF_BYPASS_IPV6, OIDC_PURPOSE_TLS_REVOCATION_ADMISSION, ACTIVE_LEASE_GUARD_COORDINATION, REAL_REBOOT. Il prossimo lavoro indipendente è il piano di enforcement source-specific sulle shared faces e il protocollo guard/lease attivo, da validare con fixture native prima di un nuovo staging/apply target. Il lease owner isolato esistente non può essere attivato sotto EMPTY_ONLY: quando popola gli insiemi il guard attuale lo rifiuta; inoltre ricreazione tabelle e handle rebinding devono essere serializzati contro i writer, senza replay TTL.

Ciò non cambia i gate Semantic rollout migration-aware, Discovery governata/THS, mapping Teatri e file immediate ingestion o API scheduler-before-ingestion → UDP/Search. Main/live software, run business e cohort storici preservati; niente merge/restart/reboot/provider start/lease activation. CI sul software readiness già verificata 32/32 success, job root 16 test senza skip; questa nuova prova VPS è distinta dalla CI. Aggiornamento documentale del presente esito: nessun nuovo codice o nuovo comando VPS eseguito dopo l'inventario.

## Cronologia — readiness software PASS, prima dell'inventario VPS

Dopo il comando `prosegui`, è stato implementato `scripts/inventory_semantic_runtime_readiness.py` in Gateway PR56, commit `4daad06b71695ad839d1865e55d5aeaf765df861`, SHA256 `ecb0326b9f97f76598d9bad56aa241b01802bf0a601f4eda38fef41fb15c655a`. **CI sull'esatto head: 32/32 completed/success**, nessun pending/failure. Il job root nativo 111247226355 ha eseguito **16 test PASS senza skip**, con `RUNTIME_READINESS_NATIVE=PASS READ_ONLY=true STARTUP_READY=false DNS_CALLS=0`. Locale: 13 test eseguiti PASS, 3 fixture native saltate perché Docker/nft/systemd assenti. Readback esatto dei cinque file modificati, sintassi shell del comando target verificata. PR56 descrizione riallineata alla transizione target; nessun merge.

Il target resta al risultato già attestato: apply/verify PASS RUNTIME_EMPTY sul root `/etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/prepared`; due candidati mai avviati, avvio non autorizzato, zero chiamate provider, Docker non riavviato. **Il nuovo inventario readiness sul VPS NON È ESEGUITO.** Prossimo intervento: soltanto il comando read-only §16 dell'handoff. La preparazione salva un nuovo source snapshot root privato, senza modificare il cohort runtime esistente; l'inventario non scrive regole/unità/container/journal e non chiama DNS/IAM/provider.

Decisione tecnica: riusare l'installer sealed del cohort originale attraverso SHA256 esplicito `a3818878086a40377125816b776606f936ad02496d891f4bc72477c4c731ecf4` e source commit target `ef2270a57446da1f23a58548aa4d44920e578fe0`. Il nuovo commit dell'inventario non sostituisce i source installati. Evitare il vecchio custody deny-only/intent verifier dopo la transizione, perché attendono tabelle originali. Il nuovo helper valida receipt/source/config/artifact, journal completo, footprint e hash lease con handle, unità installate/caricate, shared structure/PID Docker/candidati/input immutabili e ripete i readback sotto lo stesso boot lock. Stable read non è snapshot host globalmente atomico.

Rischi affrontati e verificati: import di source alterato o non privato (hash/mode/owner/nofollow/nlink/bounds), promozione di journal incompleto o lease/handle estranei (blocco senza flush), drift tra letture e divulgazione di config/errori (blocco redatto). La fixture nativa attesta inventario dopo transizione reale con entrambi i readback nft, journal e PID invariati. L'output espone soltanto hash/count/purpose e gate non provati; `staticPurposes` non è prova di authority e `startupReady=false` resta obbligatorio.

Vincolo verificato nel codice: guard installato EMPTY_ONLY, mentre lease owner isolato popola insiemi con DNS fresco. **Lifecycle attivo ancora da implementare/integrare col guard, non attivare il lease owner attuale.** La futura transizione deve coordinare gate persistente, owner writer e ricreazione/handle rebinding, pre-start Docker, revoca stop/failure/restart, expiry finita e nessun replay TTL. Restano inoltre authority/shared-face enforcement, live namespace/IP e pacchetti/spoof/bypass/IPv6, OIDC/purpose/TLS/revocation, reboot reale, rollout Semantic migration-aware, Discovery/THS e acceptance file/API→UDP/Search. PET Gateway v1.5 T11/T11.3 GW-NET-01..05 e Semantic v1.3 §§9.2/10–11 riletti; nessuna modifica ai confini dominio/THS e al requisito di egress cumulativo. Nessun provider start/restart/reboot, upload/job replay o alterazione business evidence eseguito.

## Regole permanenti di esecuzione — adottate dall'operatore il 3 ottobre 2026

**Validazione obbligatoria.** Prima dell’implementazione, verifica il flusso, le dipendenze e i principali rischi logici, di concorrenza, memoria e compatibilità. Correggi autonomamente i problemi individuati e valida il risultato con test pertinenti e CI. Presenta il codice completato insieme alle verifiche eseguite e agli eventuali limiti residui. Non dichiarare superata una verifica basandoti soltanto sull’auto-revisione.

**Autonomia e completamento.** Procedi autonomamente entro l’obiettivo concordato. Risolvi le scelte tecniche privilegiando coerenza con PET e repository, semplicità, reversibilità e scalabilità necessaria; documenta le decisioni nell’handoff senza fermarti per scelte ordinarie. Mantieni aggiornati handoff, roadmap, manuale e sprint, comprese le sezioni dei comandi eseguiti. Fermati soltanto quando serve un’azione sul VPS, un’informazione indispensabile o una decisione di autorità non già conferita. Niente merge, avvii o replay impliciti.

**Checkpoint.** Lascia sempre un risultato verificabile: commit, stato dei test/CI, lavoro completato, questioni aperte e prossimo passo preciso. Se un blocco impedisce una parte, completa comunque le attività indipendenti.

**Autonomia rafforzata — nuova regola dell'operatore, 3 ottobre 2026.** «procedi e vai avanti “a manetta” fermandoti solo quando devo intervenire io». Proseguire senza pause o richieste di conferma per scelte tecniche ordinarie, completando le attività autonome e quelle indipendenti da eventuali blocchi. Fermarsi soltanto quando l'intervento dell'operatore è indispensabile: azione VPS, informazione necessaria o autorità non già conferita. Usare checkpoint frequenti, salvati su GitHub, per conservare continuità anche in caso di disconnessione della chat; un checkpoint non costituisce motivo per interrompere il lavoro autonomo. Restano obbligatorie validazione con test/CI, coerenza PET e aggiornamento dei quattro documenti/comandi. Nessun merge, avvio, replay o restart implicito.

Queste regole si applicano alla continuazione del progetto e alle nuove chat. Il prossimo lavoro tecnico rimane la preparazione dei gate rete/authority e del lifecycle lease dopo RUNTIME_EMPTY (§15 dell'handoff). La loro adozione non attesta verifiche aggiuntive e non conferisce autorizzazione startup, merge, replay o restart. Stato target confermato: apply/verify PASS RUNTIME_EMPTY, startAuthorized=false. Nessun nuovo codice, test/CI o comando VPS eseguito in questo checkpoint di regole.

## Checkpoint target attestato — runtime VPS ESEGUITO, PASS apply/verify, RUNTIME_EMPTY

Il 3 ottobre 2026 l'operatore ha restituito entrambi gli esiti del §14: `SEMANTIC_RUNTIME_TRANSITION=PASS MODE=apply STATE=RUNTIME_EMPTY` e `SEMANTIC_RUNTIME_TRANSITION=PASS MODE=verify STATE=RUNTIME_EMPTY`. Entrambi attestano `START_AUTHORIZED=false PROVIDER_CALLS=0 DOCKER_RESTARTED=false NOT_RELEASE_ACCEPTANCE=true NO_SECRETS_PRINTED=true`. Il messaggio successivo ripete gli stessi esiti; è duplicato della stessa attestazione, non evidenza di un secondo apply.

Stage/transaction root: `/etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/prepared`; journal `transition-journal.json` sotto tale root; source Gateway `ef2270a57446da1f23a58548aa4d44920e578fe0`. Intent precedente `/etc/ouf/deploy-snapshots/semantic-provider-transition-intent-20261003-151036/prepared` conservato. Custody, intent, staging, plan e apply/verify sono completati nel loro scope. **Non ripetere i comandi §§6,11–14.**

Stato host corrente: guard/drop-in runtime installati e caricati tramite daemon-reload; le due tabelle possedute sono nel profilo runtime con insiemi provider vuoti, footprint e binding leaseStructureHash verificati e journal completato RUNTIME_EMPTY. Il precedente DENY_ONLY è baseline storica conservata, non il profilo host attuale. Docker non riavviato, due candidati mai avviati, nessuna chiamata provider, avvio non autorizzato. Gli insiemi timeout vuoti non attestano installazione/attivazione del lease owner o lease attive.

Prossimo lavoro: chiudere i gate residui di authority infrastrutturale, namespace/source/live IP e pacchetti/spoof/direct bypass/IPv6, admission OIDC/purpose/TLS/revocation e lifecycle lease prima di proporre startup. Il guard attuale è empty-only e rifiuta elementi lease attivi: non installare/attivare una lease owner sotto questo profilo senza transizione coordinata e prove. Reboot reale, rollout Semantic migration-aware, Discovery/THS, mapping Teatri e percorso file/API→UDP/Search restano aperti. Il comando read-only readiness §16 è ora predisposto e pendente; nessun comando start/restart/reboot. Main/live software e run business conservati; nessun merge.

L'apply host è una prova target della transizione vuota, non release acceptance né prova di provider operativo/reboot. Conservare gli originali sealed e questo journal. In caso di drift/interruzione futura usare diagnosi e reconcile/rollback espliciti, mai replay apply. Una ricreazione delle tabelle cambia gli handle e richiede riconciliazione del binding lease; il rollback logico non fabbrica un nuovo PASS custody legacy.

## Cronologia — runtime plan PASS, prima di apply/verify

Il 3 ottobre 2026 l'operatore ha restituito `SEMANTIC_RUNTIME_TRANSITION=PASS MODE=plan STATE=PREPARING START_AUTHORIZED=false PROVIDER_CALLS=0 DOCKER_RESTARTED=false NOT_RELEASE_ACCEPTANCE=true NO_SECRETS_PRINTED=true` per il §13 dell'handoff, sullo stage `/etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/prepared`, source Gateway `ef2270a57446da1f23a58548aa4d44920e578fe0`. **Plan eseguito; non ripeterlo come passo autonomo.** `PREPARING` è il record restituito dal plan: il codice ritorna prima di scrivere il journal e prima di qualsiasi installazione; non prova una transizione apply iniziata.

Custody, intent e staging privato già PASS; nessuna regola/unità/container host modificata da questo plan. Host ancora DENY_ONLY, kernel lease assente, due candidati mai avviati, avvio non autorizzato. Prossimo comando pendente: transizione runtime `apply` seguita da `verify`, §14 dell'handoff. Questo successivo apply sostituisce soltanto le due tabelle possedute con il profilo runtime a provider set vuoti e gli artefatti guard/drop-in posseduti, con journal persistente e `systemctl daemon-reload`; non riavvia Docker/container e non autorizza start né installa/attiva lease. Non è release acceptance.

Runtime apply/verify target **NON ESEGUITI**. Se BLOCKED o interruzione, conservare snapshot/journal e non rieseguire apply: diagnosticare per reconcile/rollback espliciti. Tutti i gate PET, authority, namespace/pacchetti/IPv6, admission/lease lifecycle/reboot e business acceptance restano aperti; main/live e run Cinema/Teatri invariati. CI software già verificata 32/32 e job runtime 11 test senza skip.

## Cronologia — staging privato PASS, prima del runtime plan

Il 3 ottobre 2026 alle 16:02 UTC (18:02 Europe/Rome) l'operatore ha eseguito il blocco staging del §12 dell'handoff. I tre checksum source sono OK; `SEMANTIC_RUNTIME_TRANSITION_STAGE=PASS` nei modi `plan/apply/verify`. Root del tentativo: `/etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211`; root preparato privato: `/etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/prepared`.

Output attestato: `ISOLATED_NATIVE_TEMPLATE=true`, `HOST_RULES_UNCHANGED=true`, `UNITS_UNCHANGED=true`, `CONTAINERS_UNCHANGED=true`, `EMPTY_PROVIDER_SETS=true`, `START_AUTHORIZED=false`, `PROVIDER_CALLS=0`, `NOT_RELEASE_ACCEPTANCE=true`, `NO_SECRETS_PRINTED=true`. Il template vuoto è compilato in namespace isolato; non prova regole runtime host installate. Intent precedente PASS al root `semantic-provider-transition-intent-20261003-151036/prepared` conservato. Non ripetere custody, intent o staging come passi autonomi.

Source Gateway fissato: `ef2270a57446da1f23a58548aa4d44920e578fe0`; CI software già verificata 32/32 PASS, job runtime 11 test senza skip. Main/live e business evidence Cinema/Teatri invariati. Boot host DENY_ONLY, nessuna kernel lease installata, due candidati mai avviati; avvio non autorizzato. Rimangono tutti i gate PET/admission/authority/live namespace/packets/IPv6/lease lifecycle/reboot e acceptance già elencati.

**Prossimo intervento pendente: solo runtime transition `--mode plan`**, read-only sulle regole/unità/container, sullo stage attestato; comando nel §13 dell'handoff. Runtime `apply/verify/reconcile/rollback` host NON ESEGUITI. Non avviare container, non fare restart Docker/reboot e non presumere che PASS stage sia release acceptance.

## Cronologia — intent PASS e software verificato, prima dello staging target

Il 3 ottobre 2026 l'operatore ha restituito PASS per `prepare_semantic_provider_transition_intent.py` nei tre modi `plan/apply/verify`. Root privato attestato: `/etc/ouf/deploy-snapshots/semantic-provider-transition-intent-20261003-151036/prepared`. Il boot lock è stato riusato; sono stati scritti soltanto artefatti privati. Nessuna regola runtime, unità o container modificata; `startAuthorized=false`, `providerCalls=0`, `notReleaseAcceptance=true`. Questa prova supera le diciture intent pendente sotto, conservate come cronologia; non ripetere l'intent come passo autonomo.

Gateway PR56, ancora aperta/draft: commit `ef2270a57446da1f23a58548aa4d44920e578fe0`, **32/32 check run completed/success**, nessun pending/failure. Il log del job `provider-runtime-transition` 111236177469 attesta **11 test PASS senza skip**: 8 prove di file privati/lock e 3 fixture native con Docker/nft/systemd. Le fixture provano staging, apply/verify, ripristino delle sole tabelle vuote, blocco di tabelle estranee/parziali, riconciliazione esplicita degli handle, gate persistente dopo crash/reload fallita, rollback degli artefatti posseduti e rifiuto atomico nft con conservazione delle due tabelle precedenti. Queste sono prove CI, non prove sul VPS.

| Source fissato nel commit Gateway | SHA256 |
| --- | --- |
| `scripts/restore_semantic_runtime_boot_guard.py` | `cceab662620d1abf97c09be1147c79e4e43022298cb0560dc604ed4bdeb6a606` |
| `scripts/stage_semantic_runtime_transition.py` | `f88740a293d78906b0a4c8915cc6b760a2dc3f9ab97f110cbb4308e950e519dd` |
| `scripts/transition_semantic_runtime_guard.py` | `a3818878086a40377125816b776606f936ad02496d891f4bc72477c4c731ecf4` |

Lo staging prepara esclusivamente file root privati e compila il template nft in un namespace di rete isolato tramite `unshare`; non installa unità/regole host e non avvia container. L'installer runtime è implementato con journal persistente e recovery/rollback, ma **né staging né transizione runtime sono stati eseguiti sul VPS**. Il target resta DENY_ONLY, senza kernel lease, con due candidati mai avviati e avvio non autorizzato.

Prossimo passo target: solo staging privato `plan/apply/verify`, dopo ripresa esplicita della sessione, con i pin sopra e l'intent attestato. Parametri espliciti: `--source-commit ef2270a57446da1f23a58548aa4d44920e578fe0`, `--intent-source-commit 392234edc50c6e8cd19a3028b3e9e19d6f1955b4`, `--intent-source-sha256 f1cc60568118387cad11a8546f3b0c2c64941c6a51a28611e4c62a009db57422`, `--runtime-guard-sha256 cceab662620d1abf97c09be1147c79e4e43022298cb0560dc604ed4bdeb6a606`, nuovo `--snapshot-root /etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-<UTC>/prepared` esclusivo, `--docker-path /usr/bin/docker`, `--nft-path /usr/sbin/nft`, `--systemctl-path /usr/bin/systemctl`, `--unshare-path /usr/bin/unshare`, `--python-path /usr/bin/python3`, `--provider-endpoint-ref schema-gov`, `--resolution-evidence-ref fresh-lease-owner`, `--lease-seconds 30`. Conservare i tre source verificati sotto il nuovo parent `source/scripts` (directory root 0700, file root 0600). Procedura software: [runbook Gateway fissato](https://github.com/GioNob/ouf-api-gateway/blob/ef2270a57446da1f23a58548aa4d44920e578fe0/docs/SEMANTIC_PROVIDER_BOOT_RUNTIME_TRANSITION.md). Nessun runtime apply host è il passo corrente.

Restano aperti prima dell'avvio: prova target, autorità infrastrutturale/live namespace e pacchetti, profilo IPv6, admission/start, lifecycle lease attiva, riconciliazione lease degli handle ricreati e reboot reale. Il profilo vuoto rifiuta lease attive; non le adotta né le svuota. I gate PET Gateway v1.5 T11/T11.3 GW-NET01..05 e Semantic v1.3 §§9.2/10–11 restano invariati: chatbot propone, THS adotta con autorità prevista. Non modificare main/live, non eseguire merge, replay dei run Cinema/Teatri, upload/job o ricreazione delle reti di produzione.

L'operatore ha interrotto la sessione per apparente loop/problema dell'interfaccia. Dopo l'interruzione sono stati verificati soltanto la CI e questo checkpoint documentale; nessun nuovo sviluppo o comando VPS è stato avviato.

## Cronologia — custody PASS, prima dell'esecuzione dell'intent

Il 3 ottobre 2026 l'operatore ha eseguito il blocco custody del §6 dell'handoff e restituito `SEMANTIC_PROVIDER_GUARD_CUSTODY_INVENTORY=PASS`. Questa prova **supera le precedenti diciture NON ESEGUITO/custody pending**, mantenute sotto come cronologia. Nessun replay del comando custody è richiesto come passo autonomo.

| Evidenza target | Valore |
| --- | --- |
| Schema | `ouf.semantic-provider-guard-custody.v1` |
| Manifest hash | `052b46a56ea666971f135c75af48b3342dbeb68e2f17f1f16263a99351df88bd` |
| Creation journal hash | `a1c2acd9924fc0f924ded7c2d59f128ef2d8b8dd11c62484a901f628022aaae7` |
| Boot install journal hash | `44dfac2145f509c8fb0b66983630616d25958b40f3ffc811074ebb9b3c1edda5` |
| Candidati / start | 2, neverStarted=true, startAuthorized=false |
| Boot / lease | DENY_ONLY, kernelLeaseInstalled=false, bootTransitionRequiredBeforeRuntimeRules=true |
| Effetti | Read-only; no IAM/DNS/provider calls; nessun container/regola modificato; nessun segreto stampato |

Non è release acceptance né snapshot atomico: l'helper custody non prende lock. Il path timestamped del suo source snapshot non compare nell'output fornito e non viene inventato. Gli hash sopra e i journal originali sono sufficienti a vincolare il nuovo preflight.

Gateway PR56 ora contiene `392234edc50c6e8cd19a3028b3e9e19d6f1955b4`: helper `prepare_semantic_provider_transition_intent.py`, SHA256 `f1cc60568118387cad11a8546f3b0c2c64941c6a51a28611e4c62a009db57422`. Readback esatto dei quattro file modificati; 8 test locali PASS senza skip, con file privati/flock reali e readback host simulati. CI Gateway sul nuovo head: **30/30 check run completed/success** (push e PR); i due job root intent hanno eseguito 8/8 test senza skip (0.079s/0.078s). Semantic PR30 resta `c2b4ae5abed1236378c7060b3eb3dac126672cbc`, OPEN DRAFT, 14/14 completed/success. CI non equivale a target transition acceptance. Nessun software live sostituito, merge o cambio main.

[Protocollo completo e limiti](https://github.com/GioNob/ouf-api-gateway/blob/392234edc50c6e8cd19a3028b3e9e19d6f1955b4/docs/SEMANTIC_PROVIDER_BOOT_RUNTIME_TRANSITION.md). Il restore deny-only installato rifiuta i set: non basta sostituire le regole nft. Il prossimo passo prende lo **stesso lock inode del boot guard**, revalida gli hash custody, il runtime sealed e il cohort lease9, poi registra due readback bounded di struttura propria/condivisa in un nuovo intent root-private. Plan non crea intent; apply scrive **soltanto tre file privati**; verify ricontrolla tutto. Nessuna modifica nft/unit/Docker, nessun login KC, DNS, lease o provider call. Il lock boot non serializza scrittori esterni: globalAtomicSnapshotProven=false. Collisioni, lock conteso/assente/symlink, drift e parziali bloccano; conservare la prova senza retry apply cieco.

**NON ESEGUITO sul VPS:** transition intent plan/apply/verify. **Non implementato:** nuovo runtime restore guard e apply coordinato. Il protocollo richiede gate persistente nel Docker pre-start prima delle mutazioni, intent/journal fsynced e lock comune, sostituzione atomica delle sole due tabelle con empty provider sets, confronto readback con struttura compilata attendibile, verifica shared/PID/pre-start, rollback per fase e nuova attestazione hash lease dopo ricreazione. Native failure/recovery tests prima di host apply; niente seed storico DNS né adozione cieca di hash osservati. Start/daemon/provider admission/reboot restano distinti.

Il primo head di questa sessione `844ebb1979196e847061f82ebb6cdab66948ea19` ha passato il job root intent (8/8 senza skip), ma request-boundary/config-contract non privilegiati hanno raccolto gli stessi fixture root e fallito. Head `392234edc50c6e8cd19a3028b3e9e19d6f1955b4` corregge esclusivamente test/workflow: opt-in/skip nel discovery generale e OUF_TRANSITION_FULL_OWNER_TEST=1 nel job root, che deve fallire se non è davvero root. Helper e SHA256 restano identici; nessuna attenuazione del controllo root in produzione.

Il pacchetto PET autorizzato è presente nel workspace: SHA256 `e63df67e8817eec38a9d4b3eb736b020f693b932f3360dc02f4555330f2201ce`, 323 checksum interni riletti, zero mismatch. Consultati i testi Gateway v1.5 T11/T11.3/GW-NET-01..05 e Semantic v1.3 §§9.2/10–11: default-deny cumulativo, endpoint governati, confini north/south, discovery on-demand, mapping proposto dal chatbot e autorità THS invariati. Nessuna nuova API/identity authority introdotta.

Cinema/Teatri, reti/immagini/trust/credenziali, policy38, receipt/backup e tutti i gate ereditati restano preservati. File: ingestion immediata dopo onboarding/ACTIVE; API: endpoint/credenziali/extraction profile/onboarding/scheduler prima dell'ingestion automatica. Nessun gate di startup, rete runtime o filiera completa chiuso da questo PASS.

## Cronologia — ripresa verificata precedente

Letto integralmente questo handoff al commit `381fc2ae00c52f1952e941edbc43d7fda7fa01be` attraverso il connector GitHub; acquisiti roadmap, manuale, sprint, registro ereditato del 1 ottobre e riferimenti storici 25/27/29/30 settembre e audit 27 settembre. La cronologia resta preservata: nessun gate chiuso per omissione.

Baseline allegata `OUF_Reality_Baseline_Package_v1_7(20261003-142932).zip`: SHA256 `e63df67e8817eec38a9d4b3eb736b020f693b932f3360dc02f4555330f2201ce`; tutti i 323 checksum interni coincidono. Il contenuto dell'archivio coincide con la baseline citata al §3 anche se il nome di upload differisce. Consultati Matrix L0 v1.7, Onboarding v1.6 §§92–92.2, Semantic v1.3 §§9.2/10–11/17–18, UDP v1.3 §§21–22/109.2/109.6–109.9, Authorization v1.5 §36.10 e confini MCP v1.4/Gateway v1.5. Mapping assistito esterno, autorità THS, ingestion file dopo ACTIVE e scheduler governato per API rimangono il percorso concordato.

### Pin riletti dal connector

| Repository / PR | HEAD verificato | Stato |
| --- | --- | --- |
| Gateway PR56 | `85914e39bd0aa9f8e7a0a0a9d3b9db6007633ff8` | OPEN DRAFT, 28/28 check run completed/success |
| Semantic PR30 | `c2b4ae5abed1236378c7060b3eb3dac126672cbc` | OPEN DRAFT, 14/14 check run completed/success |
| Semantic PR26 | `381fc2ae00c52f1952e941edbc43d7fda7fa01be` | OPEN DRAFT; pin di ingresso prima di questo aggiornamento documentale |
| Semantic PR27 | `e7bc5190f9e6afbbc4cf3c90d5d4970afbfad14b` | OPEN DRAFT; coincide con ultima revisione live riferita, senza nuova prova target |
| Semantic PR28 | `bf35e930fb239c61ea8ceebb41e187d653a3d96a` | OPEN DRAFT |
| MCP PR48 | `d7d5330d2b2588b3f896ea23e2c47e19b7b905a1` | OPEN DRAFT |
| Gateway PR55 | `b368284b3f6a7675863f85eeafc42d67bf9187dc` | OPEN DRAFT |

Main riletti separatamente: Semantic `d188e5e727eca7a22f414f43f164f85c31411bcf`, Gateway `dbdc24b5481dc9473b21b360ab1142c9aef0194b`, MCP `5615fdcad8cbcad9ff41ec3d0ad2ccbf9423c042`. Nessun merge o spostamento di main. Compare PR28→PR30: ahead 3, behind 0, merge-base uguale al pin PR28; la correzione disponibilità Discovery è ereditata. Il delta include V10 e rimane candidato software, non rollout. Gli stati live al §5 sono ultima evidenza operatore, non una nuova interrogazione VPS.

### Primo intervento e dipendenza target

Scaricato e letto l'helper custody dal pin Gateway sopra; byte UTF-8 verificati SHA256 `fabd47c6ce8919bc7a910cbaf63f66f1fb786b00c239ae41757c1fd0df829b8d`. Il blocco §6 è riproposto invariato come primo intervento VPS; controllo sintattico shell riuscito. **NON ESEGUITO sul target; nessun PASS custody, nuovo snapshot host o autorizzazione start è attestato.** Nessun accesso SSH è disponibile in questa sessione: l'operatore esegue il blocco e restituisce solo output redatto.

Dopo l'esito target: se BLOCKED, isolare read-only la differenza senza replay create/apply; se PASS, usare i journal/hash restituiti come precondizioni di un nuovo piano boot/runtime. La transizione richiede profilo nuovo sealed, intent/journal e lock comune con la custodia boot, stato fail-closed ad ogni fase, provider sets inizialmente vuoti, verifica della struttura condivisa e del Docker pre-start, rollback/reconciliation dei parziali. Conservare separati footprint boot e hash struttura lease; non riusare una vecchia osservazione DNS come lease. Nessun helper di transizione è dichiarato implementato o target-verified da questa ripresa. Start/daemon/provider admission e reboot restano gate distinti successivi, con binding d'installazione espliciti.

Cinema/Teatri, asset/profile/job, reti, immagini, credenziali, policy38, receipt originali e backup restano preservati; nessuna mutazione VPS, nuova ingestion o chiamata provider eseguita in questa sessione.


Checkpoint: **2026-10-03, 16:14 Europe/Rome**. L'utente interrompe la chat per lentezza, non interrompe il progetto. Questo è il punto di ingresso della nuova chat. Conserva e integra il registro storico del [1 ottobre](OUF_HANDOFF_2026-10-01_FILE_TO_UDP_NEXT_SPRINT.md), senza chiudere gate per omissione.

## 1. Checkpoint storico 16:14 — il custody allora non era eseguito

Ultima azione sul VPS provata dall'output dell'utente: `create_semantic_provider_stopped_candidates.py`, plan/apply/verify PASS. Journal:

`/etc/ouf/deploy-snapshots/semantic-provider-stopped-create-20261003-135106/prepared/creation-journal.json`

- Plan: `PLANNED`, 0 container; apply e verify: `CREATED_STOPPED`, **2 container**.
- `NEVER_STARTED=true`, `START_AUTHORIZED=false`, `NETWORK_CONFIGURATION_ONLY=true`.
- Nessun container condiviso modificato, nessuna scrittura di regole/route/IAM, zero provider call, nessuna release acceptance.
- Nomi/TLS alias: **ouf-semantic-southbound** (APISIX) e **ouf-semantic-provider** (adapter). Gli ID sono nel journal privato, non sono stati stampati né ricostruiti dalla chat.
- Le immagini sono riusate, non ricompilate. Configurazione Docker delle reti/IP non prova namespace o allocazione live, pacchetti, TLS o lease.

**NON ESEGUITO:** download/installazione/invocazione di `inventory_semantic_provider_guard_custody.py`, proposto nel messaggio successivo. Non esiste alcun output target `SEMANTIC_PROVIDER_GUARD_CUSTODY_INVENTORY=PASS` in questa chat. Non assumere nemmeno la creazione del suo snapshot timestamped. Non avviare i candidati. Primo passo operativo rimasto è il comando completo al §6.

La parte software/documentale è invece pubblicata: Gateway helper `85914e39bd0aa9f8e7a0a0a9d3b9db6007633ff8`, SHA256 `fabd47c6ce8919bc7a910cbaf63f66f1fb786b00c239ae41757c1fd0df829b8d`, sette test di admission con readback fixture. CI Gateway **28/28 SUCCESS**, verificata nuovamente durante questo handoff. Le fixture non provano lo stato del VPS.

## 2. Obiettivo e regole di collaborazione

Completare acquisizione → onboarding → mapping semantico → ingestion → UDP, utilizzabile in modo semplice tramite MCP con chatbot compatibili. Il chatbot consulta, confronta e propone il mapping; **nessun agente AI aggiunto dentro Onboarding**. Onboarding valida/persiste il mapping della source; Semantic governa artefatti/versioni; UDP decide l'identità canonica. Le decisioni autoritative HUMAN restano in THS; nessun tool MCP di approvazione/pubblicazione/merge privilegiato.

| Ingresso | Avvio del percorso | Dopo mapping e decisioni governate |
| --- | --- | --- |
| File gestito | THS scelta file → upload/staging → profiling | Onboarding/review/ACTIVE compatibile → ingestion automatica una tantum immediata → handoff/UDP/dedup; nessuna attesa di cadence periodica. |
| Verticale API | THS endpoint e credenziali → THS scelta extraction profile | Stesso percorso di mapping/governance; configurazione scheduler e pubblicazione parametri → ingestion automatica alle scadenze. Onboarding non fa polling. |

La verifica autoritativa di doppioni/identità è UDP dopo l'handoff; non spostarla nel profiler. Credenziali mediante THS/secret manager, MCP riceve riferimenti opachi e stati redatti. Il sistema deve gestire dubbi/quarantene e ripresa idempotente da stato persistito.

Regole persistenti:

1. Riusare centinaia di ore di prove/correzioni backend. Nessun replay Cinema/Teatri, nuovo upload/profile/job, riattivazione schedule o retry per comodità. Nuovi test sui collegamenti cambiati e regressioni appropriate, non ripetizione integrale manuale.
2. L'utente autorizza a proseguire autonomamente finché serve realmente il suo aiuto. Preparare codice, test/CI, piani e readback prima di chiedere login/decisione o esecuzione VPS. Non presumere accesso SSH: qui il VPS è operato dall'utente con comandi pinned.
3. Aggiornare a ogni checkpoint handoff, roadmap, manuale installazione/configurazione e sprint. Non cambiare main/mergiare automaticamente PR o trasformare CI/staging in release acceptance.
4. Tutti domini, indirizzi, porte, reti, subnet, bridge, nomi, UID/GID, path, trust, issuer/client/scope, tenant, timeout e scheduler sono parametri espliciti. I valori lab sotto sono binding di questa installazione, non default del prodotto.
5. Non stampare token, secret, env completi, private key, payload raw o log integrali. Ricevute/journal restano privati sul VPS. Usare Python **-B** nelle procedure host. Conservare backup, originali/rollback e tentativi falliti; cleanup solo proprio e verificato, mai force su container avviati/estranei.
6. Revisioni live, branch, main e candidato non sono equivalenti. Prima di modificare inventariare diff/PR per evitare doppioni. Nel workspace vecchio il repo Gateway è dirty: pubblicare soltanto file mirati su tree GitHub fresco, mai l'intero checkout.
7. Nella chat conclusa niente Docker/nft/systemd/Java runtime native locali disponibili; test native in CI e sul target. UID0 mappato non permette chown636/10006: skip locali non sono acceptance. Non generare nuove prove host fittizie.

## 3. PET e documentazione da leggere

[Roadmap](../OUF_ROADMAP_PET_1_7.md), [manuale installazione](../installation/OUF_INSTALLATION_MANUAL.md), [sprint](../sprints/OUF_ACQUISITION_TO_UDP_2026-10-02.md), storico [1 ottobre](OUF_HANDOFF_2026-10-01_FILE_TO_UDP_NEXT_SPRINT.md), con registro gate ereditati e collegamenti agli handoff 25/27/29/30 settembre e audit 27 settembre. Le sezioni cronologiche vecchie non sostituiscono questo checkpoint attuale.

Normativa: L0 Alignment Matrix v1.7; Source Onboarding v1.6 §§92–92.2 e THS; Semantic v1.3 §§9.2,10–11,17–18; UDP v1.3 §§21–22,109.2,109.6–109.9; Authorization v1.5 §36.10; MCP v1.4; Gateway v1.5. Gateway prescrive confini northbound/southbound distinguibili per route, policy, credenziali, log e zone; il proxy non fa ETL né decisioni di dominio.

Pacchetto letto nella chat: `OUF_Reality_Baseline_Package_v1_7(20261001-185201).zip`, SHA256 `e63df67e8817eec38a9d4b3eb736b020f693b932f3360dc02f4555330f2201ce`; 323 checksum interni verificati senza mismatch. Nel vecchio workspace esistono `baseline/OUF_Reality_Baseline_Package_v1_7/` e `pet-text/`. Possono non sopravvivere alla nuova chat. Verificare disponibilità autorizzata; se mancano, richiedere il pacchetto normativo. Non accedere alla Library di altre chat e non trattare questa sintesi come sostituto PET. Si può proseguire il readback già preparato senza reinterpretare una norma assente.

## 4. Repository, PR, revisioni e CI verificate

Owner GitHub **GioNob**. Pin verificati durante preparazione del presente handoff:

| Repository / PR | Branch / pin | Stato |
| --- | --- | --- |
| ouf-api-gateway [PR56](https://github.com/GioNob/ouf-api-gateway/pull/56) | `codex/semantic-provider-request-boundary`, HEAD `85914e39bd0aa9f8e7a0a0a9d3b9db6007633ff8`, base `codex/consultation-live-c14d3f23` | OPEN DRAFT; 28/28 check runs SUCCESS, push+PR. config-contract 454 passed/64 opt-in skips; native Docker/kernel/TLS/systemd separatamente verdi. |
| ouf-semantic-registry [PR30](https://github.com/GioNob/ouf-semantic-registry/pull/30) | `codex/semantic-provider-workload-auth`, HEAD `c2b4ae5abed1236378c7060b3eb3dac126672cbc`, base `codex/semantic-discovery-jobs` | OPEN DRAFT; 14/14 check runs SUCCESS. Workload OAuth/HTTPS testato; **nessuna immagine staged/built/live provata** per questo incremento. |
| ouf-semantic-registry [PR26](https://github.com/GioNob/ouf-semantic-registry/pull/26) | `codex/r4a-smoke-semantic-inventory`, base main; prima di questo handoff HEAD `ade6315eda1020efe37dbfa0ec6586ed75a720cc` | OPEN DRAFT; coordinamento e procedure. Il commit che contiene questo file aggiorna HEAD; il pin precedente non è l'HEAD finale. |

Riferimenti storici da riconciliare prima di usare/modificare: Semantic PR27 delta RDF già live, PR28 disponibilità Discovery, MCP PR48/Gateway PR55 pacchetto identità. Il tentativo di rilettura di queste quattro PR durante l'handoff ha avuto timeout connector: il loro stato corrente non è attestato qui. Non inferire merge/chiusura/assenza da timeout. Non ricostruire un nuovo motore identità o nuove API Discovery perché la PR non è stata riletta.

Correzioni già sviluppate:

- Source read/search/exact refs Semantic, proiezione MCP `semantic.search`/`semantic.get`, contratto HUMAN consultation distinto da SERVICE read, byte-body fix MCP e RDF asserted snapshot: rollout e positivo HUMAN già provati.
- Discovery già ha API request/status/candidates/providers/adoption governata; riusare, non creare un secondo percorso.
- PR28 corregge provider disabled/nessun provider: nuove richieste 503 `SEM_DISCOVERY_NO_ENABLED_PROVIDER`, queued jobs fail esplicito; un provider realmente consultato senza risultati può invece riuscire. Verificare eredità nel branch PR30 e rollout futuro; il live è ancora e7bc5190.
- Adoption formalizzata scrive `immutable_semantic_snapshot`/`external_semantic_origin`; projection RDF imported legge `revision_interchange_snapshot`. Restano da verificare definizioni e snapshot esatti dell'adozione, niente fallback latest. normalized_payload candidato `{}` e projection metadata insufficiente non diventano mapping completo per sola connettività.
- Test-only Gateway `8b1fadb31060cce4deaf3962691aa0aaf17f5865`: tamper MAC deve decodificare, flip byte e ricodificare; cambiare solo padding Base64 non garantiva alterazione MAC. Non revertire né ricompilare container per questo test.

## 5. Baseline live e preparazioni target da riusare

### 5.1 Container produttivi e policy

| Ruolo | Revisione live / digest |
| --- | --- |
| Semantic `ouf-semantic` | `e7bc5190f9e6afbbc4cf3c90d5d4970afbfad14b`, `sha256:f6525f2512c72a600ebcbc7060d55355d86e0627487b655e7c5c6288a0be7fc6` |
| MCP `ouf-mcp` | `394b4b1540b575564f0ba58541df9d7efc59fb87`, `sha256:99a158f780243b3fa05199bed9db01197be8ae60ae1e75ad5432964509422872` |
| Gateway `ouf-apisix` | APISIX **3.18.0**, image `sha256:84e6b5e787e9f889ebff88161cb9a16599bafcffa236c6b54c7f779a0655940d`, c14d3f23-derived routes |
| Onboarding | `6340d5bf120e09b47c32177656e2c377a4c03640`, `sha256:ec6f2a962261a8433bfe103347afa2202837fcec90d210d9b5232711b854ee8a` |
| Ingestion | `163c167d09b8371ff7a62ce7068e9d485b6969b7`, `sha256:b07a4a786ca48335feae887e18dc7c4c6cdd9bd0a3a255f83d18c7c1616eec48` |
| UDP | `83249a897eb4add4289b5181b3299f48ea4c0f99`, `sha256:5e048a859716d6674355e72238f03f899abd705a943ceadbdc5c8863d28f4e9f`, Flyway34 |

Last observed IDs: live Gateway `dcbe26bed97dd5c7ac8a131ec2badf77b0291c2ef32907be639bfa09c36596d9`; Semantic `7ae83be8c1fe9fe25774b7d748e35153652b29b2501886f89daeabb83bd1a147`; Ingestion `1fa5450574e72ef15ebb2c74e0f421f04d24c842975e324ac958f071672fbb7e`. These are readback bindings, not permanent role defaults. Other shared infrastructure (Caddy, etcd, Keycloak, MinIO, Postgres, operational owner) was not switched in the provider preparation.

Authorization remains **ouf-lab-authorization:38**. Historical :36 recovery grants expired; don't reuse them. `gateway.southbound.invoke` and `ouf.semantic.discovery` scopes exist/no drift; only `gateway.southbound.invoke` DEFAULT-bound to **ouf-semantic** SERVICE. Discovery scope not client-bound/descriptor not registered or published at last inventory. Provider disabled, live workload/provider OAuth configuration uninstalled, worker enabled, queue/adopted/unexpired counts zero at inventory. HUMAN discovery/MCP binding and live provider connectivity unproven.

Calling workload: `ouf-semantic` existing confidential service account. Private credential `/etc/ouf/semantic-provider-auth/client-secret`, UID/GID10001,0600; prepared/verified, no rotation. RS256/JWKS signature, SERVICE claims/tenant/audience/TTL299 verified; introspection inactive was corrected by signature verification. Revocation and Gateway admission not proven; no mount on live Semantic.

Passive OIDC validator: **ouf-api-gateway**, enabled/confidential/client-secret, **serviceAccountsEnabled=false**. It validates bearer/JWKS; do not enable service accounts or invent a second M2M identity. Validator credential is distinct from caller credential. Successful master login administrative user **oufadmin** was explicitly observed; SSH user alone is not evidence of KC identity. Session may expire; the §6 inventory does not use kcadm.

Issuer `https://auth.ouf-lab.it/realms/ouf`, token endpoint `/protocol/openid-connect/token` under issuer; MCP execution `https://api.ouf-lab.it/internal/capabilities/v1/execute`. These are explicit lab configuration only.

### 5.2 Receipt roots — absolute paths are host bindings, not defaults

All roots below are under `/etc/ouf/deploy-snapshots/`; keep private root ownership/modes and referenced cohorts. Preparation flags describe time of receipt, not current mounts after creation.

| Preparation | Exact receipt relative to parent | Proven / residual |
| --- | --- | --- |
| Adapter image | `semantic-provider-adapter-20261002-173408/stage-receipt.json` | image `sha256:a697bf75bf7d51afadadfaccd3d80537e9a5fb2a08f0d194c6dfd9462e812468`, source `52c0dcf11654a4d3d0f17a6902ed095975466fb9`, UID10006; now created stopped, no rebuild. Base `python@sha256:bb2988715db2cf7ace7b53f38f3cffbef7c7046a656bee66245eb0ed386e2e81`. |
| Trust PKI/MAC | `semantic-provider-trust-20261002-212033/trust-receipt.json` | CA/public-root merged bundle/role leaves/purpose MAC pair verified. Offline ca.key never mounted/read by launch; role files individually RO mounted on stopped candidates. |
| Runtime plan | `semantic-provider-runtime-20261002-222530/stage-receipt.json` | root-private binding.json/runtime-plan.json compiled; native runtime activation not proved. |
| TLS startup | `semantic-provider-tls-runtime-20261002-230418/tls-runtime-receipt.json` | config.yaml/apisix.yaml/adapter.json prepared, now mounted RO on stopped candidates. apisix.yaml includes private leaf key: never cat. |
| Java trust | `semantic-provider-java-trust-20261003-061729/java-trust-receipt.json` | merged public roots preserved for selected old Semantic image; private PKCS12/JVM options UID10001, no private keys. Not mounted on live Semantic. Recheck public roots for future selected PR30 image. |
| DNS observation | `semantic-provider-dns-20261003-063746/dns-receipt.json` | Historical only, one address observed, **no kernel lease**. Expired observation must never seed runtime sets. |
| Cold networks/guards | `semantic-provider-networks-20261003-072023/prepared/network-receipt.json` | Two dedicated networks + owned inet/bridge deny-only tables installed. Candidate configuration now exists: old EMPTY predicates are historical. |
| Lease source package | `semantic-lease-package-20261003-075940/source-package-receipt.json` | Nine sealed files staged, no daemon/unit installed or started. Reuse frozen cohort. |
| Boot stage | `semantic-boot-guard-20261003-083310/boot-stage-receipt.json` | Sealed deny-only restore profile, unit and Docker drop-in. |
| Boot installation | `semantic-boot-install-20261003-103547/install-journal.json` | Plan/apply/verify PASS, loaded guard/drop-in, Docker PID1740 preserved, no restart/rule/provider call. Real reboot unproven. |
| Candidate-input inventory | `semantic-candidate-inputs-20261003-111502` | Original false block retained; corrected inventory-public-trust-fix.py PASS. Do not reuse bad original inventory.py. |
| Validator credential | `semantic-southbound-validator-20261003-114001/prepared/credential-receipt.json` | Existing secret private copy636:6360600, current profile/secret verified; no rotate/config/grant. |
| Launch inputs | `semantic-provider-launch-inputs-20261003-124906/prepared/launch-input-receipt.json` | Leaf key pairs/receipt MAC pair verified, root0600 southbound.env created; no offline CA key read; no grants/providers. |
| Stopped manifest | `semantic-provider-candidate-manifest-20261003-130410/prepared/stopped-manifest.json` | Sealed exact images/mounts/network/IP/resource specs; initial no-container/no-reservation state historical. |
| Static IPAM | `semantic-provider-static-ipam-20261003-133526/prepared/ipam-receipt.json` | Target accepted never-started disposable static create on all THREE existing networks; probes removed; no address reservation/packet proof. |
| Actual stopped creation | `semantic-provider-stopped-create-20261003-135106/prepared/creation-journal.json` | Two actual candidates, owned transaction/manifest labels, never started, checked strict config/env/RO mounts/net IDs/static IP config. This is latest target PASS. |

Metadata pitfall resolved: public trust-bundle.pem225117 bytes/root644 was incorrectly subjected to 131072 private-JSON cap. Only public CA/trust bundle cap raised to1MiB; private JSON/ownership/mode/link/ancestor checks preserved. Correct inventory source840abe...; no chmod/chown of valid artifacts needed.

IPAM pitfall resolved: one CI daemon rejected static IP on an auto-allocated subnet. This did NOT prove the target incapable. Target Docker29.8.1 positively accepted static create on backend/internal/egress. **Do not recreate/normalize these networks, rebind boot guard or restage all artifacts for that old inference.** Do not infer causality from daemon version alone; evidence is the target probe.

### 5.3 Source pins for frozen helpers

| Helper | Source commit | SHA256 |
| --- | --- | --- |
| create_semantic_provider_stopped_candidates.py | `93e861fe8c8a43912f0cb78a74adceb2db509dd9` | `4babe7ebfdffe6ef1ab4f81bacad52c86eabbbe991d30bf3c41de65d7f47ffdd` |
| stage_semantic_provider_candidates.py | `9596f450ccb2ee38730b147e22e58ceaafd52841` | `cb04a31e4d13e182b08de2df75fa13a4ec01a7c0671239339451523f2dfc9f84` |
| prepare_semantic_provider_launch_inputs.py | `732d65a8bcebb1545086702da54ee01c01c3b823` | `4a5483d5ff54bdc79ef26e4ae436ac41ebd12363be0640005d1d6f695df93e8d` |
| prepare_semantic_southbound_validator_credentials.py | `faaf43748648207f51edee890be4b3dc6592cfc5` | `3d349fd816c1c04091daada0c20eefae7b41396230e89fb7dcc46cb427aace31` |
| inventory_semantic_provider_candidate_inputs.py | `840abe970bde4ab1edc1c6aeecd84eee9d1fc5a8` | `7bbf6a50722f475323b33568e3bc875b57d7f3e3de78d62c8f7410442c48c6c9` |
| inventory_semantic_provider_static_ipam.py | `8c04d8fb6dd251407e8c86c583d40b53a66f1179` | `426d3aab4c05bb24a46b2c41279a6f6fc847b85d3fc6c2954d236200a4cc68a3` |
| inventory_semantic_provider_guard_custody.py — target PASS | `85914e39bd0aa9f8e7a0a0a9d3b9db6007633ff8` | `fabd47c6ce8919bc7a910cbaf63f66f1fb786b00c239ae41757c1fd0df829b8d` |

Frozen lease cohort source `7a81cc344b513d04fd276cd1923a9c23197aceee`: scripts stage_semantic_lease_package.py/run_semantic_provider_lease_owner.py/prepare_semantic_provider_trust.py; tools materialize_semantic_lease_service.py/materialize_southbound_kernel.py/materialize_southbound_lease_refresh.py/semantic_provider_dns.py/semantic_provider_lease_owner.py/semantic_provider_lease_nft.py. Nine root0600 files in source/scripts and source/tools; no daemon/API started.

Boot stage source `d7f65fc73a6beb0a36e77972301a4c823fe21c5d`; installer `39923852d93a3b0907edce91cf87e9386b11621b`. Host source files and artifact hashes are bound by receipts. Do not mutate frozen cohorts in place.

### 5.4 Network/trust/runtime facts

Host rootful Docker29.8.1, systemd257, Python3.13.5, nftables1.1.3. Paths `/usr/bin/docker`, `/usr/bin/python3`, `/usr/sbin/nft`, `/usr/sbin/ip`, `/usr/bin/systemctl`, `/usr/bin/openssl`; Keycloak `/opt/keycloak/bin/kcadm.sh` in ouf-keycloak.

| Network | ID | Binding |
| --- | --- | --- |
| ouf-backend | `113b5f0a3c53059b087a2ce997d2670cc057e88c0c17d4291b3b41a51ce26ba3` | internal, br-113b5f0a3c53,172.18.0.0/16,gateway172.18.0.1,v4 |
| ouf-gateway-control | `1209d67944755d95601b96719c0a5b1860ac2a6f137c10077da7b4e9967637aa` | internal,br-1209d6794475,172.20/16,v4; shared |
| ouf-semantic-provider-internal | `2a6652422b45db6f359d94d779ab8625b1ad99b1750bb54582b4b8c4e8aa9307` | bridge oufsp-int,internal,v4,172.21.0.0/16,gateway172.21.0.1 |
| ouf-semantic-provider-egress | `db8bc9f8feccc3c14f2818a5c843f5c08e5eb2e192530858d88a70ce1cc0a86d` | bridge oufsp-egress,non-internal,v4,172.22.0.0/16,gateway172.22.0.1 |

Owned **inet + bridge table ouf_sem_provider**, currently **deny-only**, no provider sets/flows/lease installed. Never DROP the entire shared backend/control network. Original topology snapshot hash `8b0eb1c691a5010f98f22e34bb3de8de0b65cf8f9bab3079fc6c193778b857d4` is historical, not an atomic current state proof.

Southbound candidate primary backend, secondary provider-internal + provider-egress; adapter primary provider-internal + provider-egress. Planned static addresses in private manifest/journal, not inferred as allocated while stopped. Both restart=no/capDropALL/no published ports/512MiB memory and same swap limit/pids128/no healthcheck; adapter read-only root, APISIX root writable; exact individual RO mounts. Created Docker endpoints can defer NetworkID until start: helper binds current network name→ID separately and checks IPAMConfig rather than claiming packet proof.

Selected lab DNS resolvers `46.38.252.230`, `46.38.225.230`, UDP/TCP53. Supplied IPv6 `2a03:4000:0:1::e1e6` deferred; current profileIPv4 only. Provider `https://schema.gov.it:443/sparql`; namespaces https://w3id.org/italia/ont/ and controlled-vocabulary/. No arbitrary chatbot SPARQL/provider URL.

Southbound TLS-only10443/SNIouf-semantic-southbound, no HTTP/admin/control/extra-metrics listeners. Adapter9443/SNIouf-semantic-provider; POST `/internal/providers/schema-gov/search`, GET `/internal/providers/schema-gov/fetch`. Adapter worker4/deadline20/providerTimeout10/maxRequest65536/maxResponse8388608/maxIntent2000. TLS cert/key/purpose MAC paths under `/run/ouf-semantic-provider/`, upstream CA/trust-bundle.pem. Separate purpose-bound receipt MAC, not OAuth/delegation key. Issuer/audience/service workload/tenant/scopes bound by private plan. Northbound Gateway env must not be copied wholesale into southbound.

Boot guard installed targets `/etc/systemd/system/ouf-semantic-boot-guard.service` and `/etc/systemd/system/docker.service.d/90-ouf-semantic-boot-guard.conf`. DefaultDependencies=no, after local-fs/nftables, before Docker; Docker Requires/After guard and **ExecStartPre validates every start**. Existing tables must match; both absent can restore strict-create; partial/foreign tables block. Original installer verifies Docker PID preservation, not a permanent verifier after a legitimate restart/reboot. Current expected PID1740 is intentional custody binding; any later change requires reconciliation, not silent adoption.

### 5.5 Already proven native tests — don't rerun indiscriminately

- Real nft/netns default-deny and expiry rejecting new **and established** packets,9 host tests PASS.
- Real Docker bridge native hook + scoped host forward, default-deny/unregistered workload/expired leases, own cleanup,1 host test17.521s PASS.
- Real APISIX3.18 CI OIDC → purpose receipt → adapter TLS, forged/direct/incomplete TLS+HTTP and wrong-hostname/SNI/plaintext denials.
- Boot/systemd native CI restore/dependency/foreign/partial recovery, no Docker restart/PID change. Actual host boot install PASS; **real reboot not proven**.
- Target embedded DockerDNS fixture at `semantic-docker-dns-20261003-105129`: source `b4c2faefb7a526c3455632212275633c60d826e7`; UDP/TCPA+AAAA, forwarded source bound to container, selected resolver/default deny/unregistered denial/flow removal, shared structure unchanged, own cleanup,15.661s. **provider0/externalDNS0**; isolated fixture, not production packet acceptance.
- Real Docker stopped-create tests4 and target static-IPAM admission tests4, plus root role-owned launch/trust/credential fixtures in CI. Target creation itself now PASS.
- Current custody helper7 fixture tests pass; native jobs inherited unchanged are green. **Custody inventory target PASS ora registrato nel checkpoint corrente; intent target ancora pendente**.

## 6. Comando custody storico — ora eseguito con PASS

Questa è la riproduzione completa dell'ultimo comando proposto. Fa download checksum-pinned e installa un nuovo helper root0600 in snapshot privato, poi legge stato Docker/reti/nft/systemd e ricevute. **Nessuna IAM/DNS/provider call, nessuno start o cambiamento container/regole/route. Non necessita refresh kcadm.** L'utente ha esplicitamente rinviato l'intero blocco alla nuova chat.

```bash
(
set -euo pipefail

OUF_CUSTODY_DOWNLOAD=$(mktemp)
trap 'rm -f "$OUF_CUSTODY_DOWNLOAD"' EXIT

curl --fail --silent --show-error \
  https://raw.githubusercontent.com/GioNob/ouf-api-gateway/85914e39bd0aa9f8e7a0a0a9d3b9db6007633ff8/scripts/inventory_semantic_provider_guard_custody.py \
  -o "$OUF_CUSTODY_DOWNLOAD"

printf '%s  %s\n' \
  fabd47c6ce8919bc7a910cbaf63f66f1fb786b00c239ae41757c1fd0df829b8d \
  "$OUF_CUSTODY_DOWNLOAD" | sha256sum -c -

OUF_CUSTODY_ROOT="/etc/ouf/deploy-snapshots/semantic-provider-guard-custody-$(date -u +%Y%m%d-%H%M%S)"
sudo install -d -m 0700 -o root -g root "$OUF_CUSTODY_ROOT"
sudo install -m 0600 -o root -g root \
  "$OUF_CUSTODY_DOWNLOAD" "$OUF_CUSTODY_ROOT/inventory.py"

sudo /usr/bin/python3 -B "$OUF_CUSTODY_ROOT/inventory.py" \
  --manifest-root /etc/ouf/deploy-snapshots/semantic-provider-candidate-manifest-20261003-130410/prepared \
  --creation-root /etc/ouf/deploy-snapshots/semantic-provider-stopped-create-20261003-135106/prepared \
  --network-root /etc/ouf/deploy-snapshots/semantic-provider-networks-20261003-072023/prepared \
  --boot-stage-root /etc/ouf/deploy-snapshots/semantic-boot-guard-20261003-083310 \
  --boot-install-root /etc/ouf/deploy-snapshots/semantic-boot-install-20261003-103547 \
  --creation-source-commit 93e861fe8c8a43912f0cb78a74adceb2db509dd9 \
  --docker-path /usr/bin/docker \
  --nft-path /usr/sbin/nft \
  --systemctl-path /usr/bin/systemctl
)
```

Atteso (non ancora osservato sul target): JSON schema `ouf.semantic-provider-guard-custody.v1`, candidateCount2/neverStartedtrue/bootProfileDENY_ONLY/startAuthorizedfalse/kernelLeaseInstalledfalse/bootTransitionRequiredBeforeRuntimeRulestrue, quindi `SEMANTIC_PROVIDER_GUARD_CUSTODY_INVENTORY=PASS`.

Il helper è **custody inventory**, non sostituisce il readback completo config/env/mounts effettuato dal creator. Verifica binding journal/manifest/cold/boot, ID/image/labels/never-started/restart=no, assenza endpoint estranei dedicati, boot files/sorgenti hash, stato systemd/PID/pre-start fingerprint e footprint guard inet+bridge. Non prende lock e non certifica uno snapshot atomico. Se BLOCKED, stampato solo codice generico redatto: diagnosi puntuale read-only, non replay della create né correzione live alla cieca.

## 7. Cosa fare dopo il readback, senza rifare lavoro precedente

1. **Custody e transition intent PASS riconciliati** nel checkpoint corrente: apply/verify runtime §14 sono PASS RUNTIME_EMPTY; readiness §16 PASS; componenti §17 verificati; proseguire dall'integrazione §18 e dai gate §15. I comandi §6, §11 e §12 sono già eseguiti con PASS; non ripeterli come passi autonomi. Non chiamare i vecchi stage/cold verifiers che pretendono nomi assenti/reti vuote. Se drift nel preflight, isolare la differenza conservando journal e container.
2. **Preparare una transizione coordinata** dalle tabelle deny-only al profilo statico/empty provider sets, insieme alla custodia boot/systemd. La precedente incompatibilità del boot guard deny-only è stata risolta dalla transizione coordinata §14; il nuovo guard verifica il profilo runtime vuoto e il journal completo, senza autorizzare startup. Gli helper di staging, guard e transizione sono implementati nel commit Gateway `ef2270a57446da1f23a58548aa4d44920e578fe0`, con journal persistente, fail-closed, recovery/rollback e CI 32/32 PASS. Staging sul VPS PASS al root `semantic-runtime-transition-stage-20261003-160211/prepared`; runtime apply/verify sul VPS PASS RUNTIME_EMPTY; il guard runtime vuoto è installato; compatibilità target/reboot e gate di avvio non sono provati dalla CI. Non alterare gli originali sealed in place.
3. Riusare kernel compiler/lease9cohort. `materialize(..., empty_provider_sets=True)` emette insiemi timeout **vuoti** in inet+bridge; static exact flows per gateway→adapter, DNS e infrastruttura autorizzata. `guardedInterfaces` soltanto dedicate; mai aprire broad egress né scambiare eccezione indirizzo privato per authority. Governare distintamente identity/JWKS e provider esterno. Resolver/endpoint/source/IP/port e private exception espliciti, nessun seed dai vecchi DNS. LeaseOwner query fresh A+AAAA a tutti i resolver selezionati, TTL bounded/tempo sottratto, apply atomico entrambe famiglie/readback, revoca su failure/stop/start. Finite expiry nega anche established.
4. Prima di start/daemon: provare namespace/IP/bridge source binding e confini/pacchetti/DNS/direct bypass/spoof/IPv6 nel perimetro effettivamente scelto. Valutare con attenzione due funzioni diverse di hash: boot footprint elimina handles/metainfo; NftBackend structure hash mantiene metadata/handles e rimuove set elem. Ricreazione tabelle e leases attivi richiedono binding coerenti, non riutilizzo cieco di un expected hash né accettazione automatica di struttura estranea. Non dichiarare supporto reboot sulla sola CI.
5. Quando il piano è concreto e verificato, installare/avviare solo i componenti necessari con procedure governate. La creazione non è autorizzazione startup, la connettività TLS non è IAM admission, il JWT verificato non prova revocation. Provare OIDC/purpose receipt/TLS adapter/hostname, owner diretti negati e workload gateway admission prima di chiamate provider.
6. PR30 Semantic: future build/stage/release con backup/migration-aware history delta. Il branch eredita **V10**, quindi NON usare alla cieca il vecchio helper RDF «migrations identical». Confrontare il truststore pubblico dell'immagine selezionata con il Java trust preparato; se diverso, preparare solo trust appropriato alla nuova immagine. Coordinare config provider/gateway/workload token+mounts; live attuale resta disabled.
7. Attivare Discovery governata solo dopo provider e autorizzazioni pronte: inventariare descriptor actors/operation/purpose; scopes≠capability registration≠policy grant≠route≠MCP discovery. Riutilizzare API asynchronous native con ownership/idempotency/bounds/status/candidate expiry/adozione THS e exact snapshot. `SUCCEEDED` vuoto non prova provider consultato se disabled. Non allargare read receipt in write/adoption authority.
8. Riprendere il mapping Teatri con artefatti adeguati, proposta source/field/identity/classifications/transformazioni/version pins, THS e bundle ACTIVE; collegare file immediate ingestion e API scheduler-before-ingestion, UDP resolution/THS/resume/recovery e Search autorizzato. Poi acceptance per nuovo percorso e secondo chatbot, preservando il resto del backlog.

Reboot/Docker restart del VPS hanno impatto condiviso: non farli per comodità. Se un gate li richiede realmente, predisporre verifica/backup/restore/rollback e finestra concreta prima della coordinazione con l'utente. Nessun reboot/restart è stato eseguito né pianificato come prossimo comando.

## 8. Business evidence congelata e decisioni mapping ancora aperte

### Cinema

Source `managed-cinema-8ec8ae90`, run `86809c17-3354-45ca-a7e6-57e903944b24` SUCCEEDED; otto handoff ACKED/lineage e otto UDP intake PROCESSED/jobsSUCCEEDED/NEW_OBJECT/observations/revisions/bindings/active objects; quarantene recuperate governatamente, audit conservato. Schedule trigger_once consumed/DISABLED. Vecchio `ouf-udp-r4a-smoke` con JAR incompatibile è stato fermato/retained/restart=no; non riavviare. Historical owner causa non provata integralmente.

Semantic artifact `5ae731cc-e4c5-43a3-aa5e-a7576adbd3a1`, semanticId `https://api.ouf-lab.it/semantic/cinema`, revision `51706bed-81e4-4306-aca1-70119821727d`, publication set `f92a2e17-30c9-456f-bb12-63afa84f41e6`, ACTIVEv1. Positivo HUMAN ChatGPT/MCP semantic.get pinned dopo RDF rollout:17 asserted triples,partialfalse,text/turtle,RDF SHA256 `4340986102db6e47345dd8157734d9db83b928edd94485f1b9a5b9e81c497a2e`. JSON metadata hash distinto `78a39fc30dab8bf221bc9eb8c2567bb2abef57e72ba1e4e29a87a23db4142391`. Cinema subClassOf schema:MovieTheater, nome/indirizzo labels/domain/range. Non prova ontology closure/inference o class Teatro; JSON definitions restano vuote. R-SMOKE Search completo rimane aperto.

### Teatri

Account MCP precedente `ouf-admin`, subject `b93d8cf6-cd14-4ee6-91d7-84cd76c4f500`; non confonderlo con master admin/SSH oufadmin. Nuova chat deve seguire account routing connector corrente, non ricostruire link_id. Connector storico `6aafef96b4148191b767e9af7b756a07` è un riferimento, non autorizzazione a presumere sessione o tool attivi.

Picker `b6de7b63-4a1a-47d8-858e-3cc5f0adad51`; asset `6609b245-86ed-4315-8ce0-73f2a8555bf3`; profile job `2f49ea03-b715-493b-ba25-a3f82007cd3d` SUCCEEDED; profile `7984c39c-7396-4248-ab0a-f2efc390b49c`v1. CSVUTF8/semicolon/header1,13rows20cols/ONE_ROW_ONE_SOURCE_OBJECT, proposta PENDING_HUMAN_REVIEW. Nessuna nuova DRAFT/ACTIVE/run/UDP Teatri provata.

Fields: nome_teatro,tipologia,toponimo,nome_indirizzo,civico,cap,citta,provincia,latitudine,longitudine,sistema_riferimento,precisione_coordinate,capienza_posti,spettacoli_stagione,stagione_riferimento,note,fonte_indirizzo,fonte_coordinate,fonte_altri_dati,data_verifica. Non riportare sample raw. CAP inferitoLONG non è tipo semantico/codice preservato; CRS dichiarato non valida geometria. data_verifica≠businessvalidFrom. Multi-hall granularity e provenance per-field da governare. Proposta NATIVE_KEY nome_teatro ancora unapproved: unicità su13righe non prova stabilità e non è chiave canonica. CLASS Teatro/Theatre search[] osservato non è censimento completo. Cinema/MovieTheater non autorizza analogia Theatre. Official vocabulary tipologia/precisione e transformations whitelist da valutare.

Identità: source-row key distinta da canonical UDP identity. Motore class-neutral già nel branch corretto; non riscrivere weighted legacy. Policy proprietà/comparatori/candidate coverage; subset sufficiente concorde anche in entrambe direzioni può MATCH con premesse/unicità; tutti comuni confrontabili diversi→distinct; partial/conflict/missing→incerto. NEW solo allowAutoNew + coverage completa; overflow REVIEW_REQUIRED/RESOLUTION_TOO_BROAD. Score/frequenza/selettività non conferiscono autorità. MATCH non equivale a merge canonico automatico. Review HUMAN/THS non blocca durable ACK/watermark né tiene transazione DB aperta; append-only audit/lineage.

## 9. Backlog ereditato: nessuna chiusura per omissione

| Gate | Residuo / limite della prova |
| --- | --- |
| R-SMOKE completo | Cinema8/8 non basta: Search Gateway/MCP almeno3oggetti, minimizzazione proprietà/oggetto,2pagine,cursor invalid/partial,label/authority/audit. |
| Seconda fonte sovrapposta/identity review | Source distinta con class/candidate overlap, subset entrambe direzioni, concorde/differente/conflicts/missing/authority, disjoint forms,boundedness/overflow/coverage/backfill, THS atomic/resume. Teatri non prova automaticamente questo gate. |
| Gateway managed upload acceptance | Streaming/primi byte,413 oversized senza assetparziale,415,media-type/digest,anonimi,limiti/idempotenza/rollback. Upload/profile reale è solo una parte. |
| MCP/channel neutrality | Secondo host/client senza copia manuale AssetID,login continuity e limiti/adattatori; niente bridge hostfiles arbitrario. |
| Semantic generalità | Exact refs/provenance/DTO/schema/consumer compatibilità, external discovery/adoption snapshot/definitions, class/property/vocab sufficienti, mapping completo. HUMAN read positivo provato soltanto per il path attuale. |
| Data Lake indipendente | Byte/hash/S3 e DB-objectstore reconciliation, backup/restore oggetti. ACK/materializzazione non sono lettura indipendente byte. |
| Replay RAW/SPI | Trasporto/esecutore e RAW durevole. UDP REPRODUCE non sostituisce retry originale/source replay. Nessun replay per chiudere formalmente questo handoff. |
| Lake policy | Retention/access per source/type/zone,enforcement/cancellazione effettiva; no defaults lab universalizzati. |
| R-INSTALL/portabilità | Manifest/secretrefs,bootstrap idempotente capabilities/IAM/Authorization/routes,cleaninstall,upgradeN/N+1,rollback/restore/PITR/reconciliation,macchine/reti/domain/Enti diversi. Le oltre100capabilities devono avere procedura batch/reconcile automatizzabile, non una lunga sequenza manuale ciascuna. |
| Network/TLS/egress | Native fixture/CI PASS nel proprio scope; target provider deployment/boot custody e runtime packets/admission ancora da provare. Real reboot/IPv6/FQDN leases non attestati dal cold stage. |
| Performance/concurrency | Profili/SLO rappresentativi,race lease/rollout/governor multi-replica; fixture vuote non acceptance. |
| Awareness/collectors | Cross-owner raccolta/proiezioni/alert e13marker ING_ACTIVATION_DISCOVERY_UNAVAILABLE da correlare; non dichiarare run riuscito fallito né healthy dalla mancanza log. |
| Latenza ChatGPT–MCP | Correlare host/tool/Gateway/owner; la lentezza chat percepita non prova latenza backend. |
| Cross-module release/branch/PR | Reconcile main/stalebase/live/pin,SBOM/checksum/security/compatibility/consumer schema; workercompatibility generale non divieto arbitrario N/N+1. CI/build/tag/deploy/live acceptance distinti. |
| Causalità storica403/reference | Non integralmente provata; conservare evidenze, niente mutazioni aggiuntive solo per una spiegazione. |

## 10. Checklist di ingresso della nuova chat

- Leggere questo file e il registro ereditato; verificare PET realmente disponibili. Riassumere brevemente obiettivo e ultimoPASS, senza rifare inventario completo manuale.
- Rileggere pin GitHub/PR/CI correnti con connector, senza assumere che HEAD/main/live coincidano. Timeout non è assenza. Niente merge automatico.
- I comandi custody §6 e transition intent §11 sono eseguiti con PASS. Staging §12 eseguito con PASS. Il plan §13 è PASS; apply/verify §14 sono PASS RUNTIME_EMPTY. Non riproporre custody, intent, staging, plan o apply; readiness §16 PASS; componenti §17 verificati; riprendere dall'integrazione §18 e dai gate §15.
- Custody e intent PASS registrati; helper boot/runtime/emptysets con native tests PASS. Staging privato target PASS: apply/verify runtime §14 PASS: riprendere dai gate §15, conservando i gate lease/admission/start prima di attivazione.
- Se serve HUMAN decision/login o SSH reale, preparare prima il risultato verificabile. Non chiedere permessi già conferiti per codice/test/read-only/aggiornamento docs.
- Conservare e aggiornare questo handoff come punto di ingresso insieme ai quattro documenti canonici. Questa chat ha eseguito solo aggiornamenti GitHub nella fase di handoff, non azioni VPS.


## 11. Transition intent privato — ESEGUITO, PASS plan/apply/verify

**ESEGUITO il 3 ottobre 2026 dall'operatore su VPS/sessione SSH oufadmin: PASS in tutti i modi `plan/apply/verify`.** Entrambi i checksum source sono risultati OK. Root attestato: `/etc/ouf/deploy-snapshots/semantic-provider-transition-intent-20261003-151036/prepared`, privato. Boot lock riusato; nessuna regola runtime, unità o container modificata; `START_AUTHORIZED=false`, `PROVIDER_CALLS=0`, `NOT_RELEASE_ACCEPTANCE=true`, `NO_SECRETS_PRINTED=true`.

Il comando sotto è conservato **solo come registro del comando eseguito: non rieseguirlo**. Il prossimo passo pendente è lo staging runtime privato del §12.

```bash
(
set -euo pipefail
OUF_TRANSITION_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_TRANSITION_TMP"' EXIT

curl --fail --silent --show-error --proto '=https' --max-time 30 \
  https://raw.githubusercontent.com/GioNob/ouf-api-gateway/392234edc50c6e8cd19a3028b3e9e19d6f1955b4/scripts/prepare_semantic_provider_transition_intent.py \
  -o "$OUF_TRANSITION_TMP/prepare_semantic_provider_transition_intent.py"
curl --fail --silent --show-error --proto '=https' --max-time 30 \
  https://raw.githubusercontent.com/GioNob/ouf-api-gateway/85914e39bd0aa9f8e7a0a0a9d3b9db6007633ff8/scripts/inventory_semantic_provider_guard_custody.py \
  -o "$OUF_TRANSITION_TMP/inventory_semantic_provider_guard_custody.py"

printf '%s  %s\n' \
  f1cc60568118387cad11a8546f3b0c2c64941c6a51a28611e4c62a009db57422 \
  "$OUF_TRANSITION_TMP/prepare_semantic_provider_transition_intent.py" \
  fabd47c6ce8919bc7a910cbaf63f66f1fb786b00c239ae41757c1fd0df829b8d \
  "$OUF_TRANSITION_TMP/inventory_semantic_provider_guard_custody.py" | sha256sum -c -

OUF_TRANSITION_ROOT="/etc/ouf/deploy-snapshots/semantic-provider-transition-intent-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_TRANSITION_ROOT"
sudo install -d -m 0700 -o root -g root "$OUF_TRANSITION_ROOT/source/scripts"
sudo install -m 0600 -o root -g root \
  "$OUF_TRANSITION_TMP/"*.py "$OUF_TRANSITION_ROOT/source/scripts/"

OUF_TRANSITION_LOCK=$(sudo /usr/bin/python3 -B - <<'PY'
import json
from pathlib import Path
import re
p=Path('/etc/ouf/deploy-snapshots/semantic-boot-guard-20261003-083310/boot-stage-receipt.json')
v=json.loads(p.read_bytes())['profile']['runtimeDirectory']
if not isinstance(v,str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,63}',v):
    raise SystemExit('BOOT_LOCK_BINDING_BLOCKED')
print('/run/'+v+'/guard.lock')
PY
)

for OUF_TRANSITION_MODE in plan apply verify; do
  sudo /usr/bin/python3 -B "$OUF_TRANSITION_ROOT/source/scripts/prepare_semantic_provider_transition_intent.py" \
    --mode "$OUF_TRANSITION_MODE" \
    --source-commit 392234edc50c6e8cd19a3028b3e9e19d6f1955b4 \
    --custody-source-sha256 fabd47c6ce8919bc7a910cbaf63f66f1fb786b00c239ae41757c1fd0df829b8d \
    --manifest-root /etc/ouf/deploy-snapshots/semantic-provider-candidate-manifest-20261003-130410/prepared \
    --creation-root /etc/ouf/deploy-snapshots/semantic-provider-stopped-create-20261003-135106/prepared \
    --network-root /etc/ouf/deploy-snapshots/semantic-provider-networks-20261003-072023/prepared \
    --boot-stage-root /etc/ouf/deploy-snapshots/semantic-boot-guard-20261003-083310 \
    --boot-install-root /etc/ouf/deploy-snapshots/semantic-boot-install-20261003-103547 \
    --runtime-root /etc/ouf/deploy-snapshots/semantic-provider-runtime-20261002-222530 \
    --lease-package-root /etc/ouf/deploy-snapshots/semantic-lease-package-20261003-075940 \
    --snapshot-root "$OUF_TRANSITION_ROOT/prepared" \
    --boot-lock-file "$OUF_TRANSITION_LOCK" \
    --lease-source-commit 7a81cc344b513d04fd276cd1923a9c23197aceee \
    --creation-source-commit 93e861fe8c8a43912f0cb78a74adceb2db509dd9 \
    --expected-manifest-hash 052b46a56ea666971f135c75af48b3342dbeb68e2f17f1f16263a99351df88bd \
    --expected-creation-journal-hash a1c2acd9924fc0f924ded7c2d59f128ef2d8b8dd11c62484a901f628022aaae7 \
    --expected-boot-install-journal-hash 44dfac2145f509c8fb0b66983630616d25958b40f3ffc811074ebb9b3c1edda5 \
    --docker-path /usr/bin/docker \
    --nft-path /usr/sbin/nft \
    --systemctl-path /usr/bin/systemctl
done
)
```

## 12. Staging runtime privato — ESEGUITO, PASS plan/apply/verify

**ESEGUITO il 3 ottobre 2026: PASS plan/apply/verify.** Root privato attestato: `/etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/prepared`. I tre checksum sono OK. Il blocco sotto è registro storico: non rieseguirlo. Il plan §13 e apply/verify §14 sono ora PASS; readiness §16 PASS; prossimo lavoro piano §17, gate §15 aperti. Usare gli helper e i parametri fissati nel checkpoint corrente iniziale e nel runbook Gateway al commit `ef2270a57446da1f23a58548aa4d44920e578fe0`; preparare un nuovo snapshot esclusivo root privato e verificare i tre checksum prima dell'esecuzione. Modi `plan/apply/verify` dello staging: scrittura di soli artefatti privati e compilazione nft in namespace isolato tramite `unshare`; nessuna installazione di regole/unità host o avvio container. Restituire solo output redatto, conservare root/parziali in caso di BLOCKED, non ripetere apply alla cieca. Nessuna transizione runtime host o autorizzazione startup è inclusa in questo passo.

Regola permanente di documentazione: dopo ogni risultato comunicato dall'operatore, aggiornare autonomamente checkpoint, sezione del comando, checklist e prossimo passo nei documenti canonici applicabili. Le procedure superate vanno marcate come cronologia/comandi già eseguiti; un PASS nel checkpoint non basta a lasciare pendente la relativa sezione operativa.

### Blocco staging privato eseguito — PASS

Richiesto dall'operatore il 3 ottobre 2026 dopo l'intent PASS. Eseguire in SSH come oufadmin; non richiede Keycloak. Il root del tentativo viene stampato prima della preparazione per conservare il binding anche in caso di BLOCKED. Nessun installer runtime è invocato. Esito ricevuto: PASS in plan/apply/verify, root `/etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/prepared`, nessuna regola/unità/container host modificata, start non autorizzato, provider calls 0.

```bash
(
set -euo pipefail
OUF_RUNTIME_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_RUNTIME_TMP"' EXIT

for OUF_RUNTIME_SCRIPT in \
  restore_semantic_runtime_boot_guard.py \
  stage_semantic_runtime_transition.py \
  transition_semantic_runtime_guard.py; do
  curl --fail --silent --show-error --proto '=https' --max-time 30 \
    "https://raw.githubusercontent.com/GioNob/ouf-api-gateway/ef2270a57446da1f23a58548aa4d44920e578fe0/scripts/$OUF_RUNTIME_SCRIPT" \
    -o "$OUF_RUNTIME_TMP/$OUF_RUNTIME_SCRIPT"
done

printf '%s  %s\n' \
  cceab662620d1abf97c09be1147c79e4e43022298cb0560dc604ed4bdeb6a606 \
  "$OUF_RUNTIME_TMP/restore_semantic_runtime_boot_guard.py" \
  f88740a293d78906b0a4c8915cc6b760a2dc3f9ab97f110cbb4308e950e519dd \
  "$OUF_RUNTIME_TMP/stage_semantic_runtime_transition.py" \
  a3818878086a40377125816b776606f936ad02496d891f4bc72477c4c731ecf4 \
  "$OUF_RUNTIME_TMP/transition_semantic_runtime_guard.py" | sha256sum -c -

OUF_RUNTIME_ROOT="/etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_RUNTIME_ROOT"
printf 'SEMANTIC_RUNTIME_STAGE_ATTEMPT_ROOT=%s\n' "$OUF_RUNTIME_ROOT"
sudo install -d -m 0700 -o root -g root "$OUF_RUNTIME_ROOT/source/scripts"
sudo install -m 0600 -o root -g root \
  "$OUF_RUNTIME_TMP/"*.py "$OUF_RUNTIME_ROOT/source/scripts/"

for OUF_RUNTIME_MODE in plan apply verify; do
  sudo /usr/bin/python3 -B "$OUF_RUNTIME_ROOT/source/scripts/stage_semantic_runtime_transition.py" \
    --mode "$OUF_RUNTIME_MODE" \
    --source-commit ef2270a57446da1f23a58548aa4d44920e578fe0 \
    --intent-root /etc/ouf/deploy-snapshots/semantic-provider-transition-intent-20261003-151036/prepared \
    --intent-source-commit 392234edc50c6e8cd19a3028b3e9e19d6f1955b4 \
    --intent-source-sha256 f1cc60568118387cad11a8546f3b0c2c64941c6a51a28611e4c62a009db57422 \
    --runtime-guard-sha256 cceab662620d1abf97c09be1147c79e4e43022298cb0560dc604ed4bdeb6a606 \
    --snapshot-root "$OUF_RUNTIME_ROOT/prepared" \
    --docker-path /usr/bin/docker \
    --nft-path /usr/sbin/nft \
    --systemctl-path /usr/bin/systemctl \
    --unshare-path /usr/bin/unshare \
    --python-path /usr/bin/python3 \
    --provider-endpoint-ref schema-gov \
    --resolution-evidence-ref fresh-lease-owner \
    --lease-seconds 30
done
)
```

## 13. Plan transizione runtime — ESEGUITO, PASS

**ESEGUITO il 3 ottobre 2026: PASS MODE=plan STATE=PREPARING.** Start non autorizzato, provider calls 0, Docker non riavviato, non release acceptance, nessun segreto stampato. Il plan ritorna prima della scrittura del journal; PREPARING non attesta apply iniziato. Comando sotto conservato come registro storico, non rieseguirlo. Apply/verify §14 sono ora PASS RUNTIME_EMPTY; prossimo lavoro ai gate §15. Ha invocato soltanto `--mode plan` sullo stage privato già verificato. Rilegge binding, custodia, unità, container e tabelle sotto il boot lock; non applica regole/unità e non riavvia Docker o candidati. Non eseguire apply prima del readback plan. In caso di BLOCKED conservare tutti gli artefatti e diagnosticare, senza replay apply.

```bash
sudo /usr/bin/python3 -B \
  /etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/source/scripts/transition_semantic_runtime_guard.py \
  --mode plan \
  --stage-root /etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/prepared \
  --stage-source-commit ef2270a57446da1f23a58548aa4d44920e578fe0 \
  --analyze-path /usr/bin/systemd-analyze
```

## 14. Apply/verify runtime vuoto — ESEGUITO, PASS RUNTIME_EMPTY

**ESEGUITO il 3 ottobre 2026: PASS MODE=apply e PASS MODE=verify, entrambi STATE=RUNTIME_EMPTY.** Start non autorizzato, provider calls 0, Docker non riavviato, non release acceptance, nessun segreto stampato. Root `/etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/prepared`. Il blocco sotto è conservato come registro del comando eseguito: non ripeterlo. Prerequisiti attestati: intent, staging e runtime plan PASS sullo stesso stage e source. Questo blocco invoca l'installer e cambia le sole tabelle e unità possedute, con journal e daemon-reload, mantenendo Docker/candidati senza restart/start. Il profilo resta vuoto e startAuthorized=false. `set -e` ferma il blocco al primo errore. Non cancellare journal o snapshot; se BLOCKED/interrotto non ripetere apply e riportare output per diagnosi/reconcile/rollback. Esito atteso in entrambi i modi: PASS STATE=RUNTIME_EMPTY; non equivale ad avvio autorizzato o acceptance.

```bash
(
set -euo pipefail
for OUF_RUNTIME_MODE in apply verify; do
  sudo /usr/bin/python3 -B \
    /etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/source/scripts/transition_semantic_runtime_guard.py \
    --mode "$OUF_RUNTIME_MODE" \
    --stage-root /etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/prepared \
    --stage-source-commit ef2270a57446da1f23a58548aa4d44920e578fe0 \
    --analyze-path /usr/bin/systemd-analyze
done
)
```

## 15. Gate successivi dopo RUNTIME_EMPTY — startup non autorizzato

Apply/verify §14 completati. Non ci sono comandi da ripetere. Inventario read-only §16 eseguito PASS. Preparare e verificare il piano per authority infrastrutturale e source-specific shared faces, namespace/live binding, pacchetti/DNS/spoof/bypass/IPv6, admission/TLS/purpose/revocation e transizione del guard empty-only verso lifecycle lease governata. Il template e la transizione vuota non chiudono questi gate. Nessun Docker restart/reboot/provider start/lease activation autorizzato dal PASS RUNTIME_EMPTY. Preservare business evidence, journal e vecchi cohort; aggiornare autonomamente checkpoint e sezioni operative dopo ogni nuovo esito.

## 16. Inventario readiness runtime read-only — ESEGUITO, PASS

**ESEGUITO il 3 ottobre 2026: PASS READ_ONLY=true STARTUP_READY=false START_AUTHORIZED=false.** Source root `/etc/ouf/deploy-snapshots/semantic-runtime-readiness-20261003-165430`. Hash e quantità nel checkpoint corrente. Nessuna chiamata DNS/IAM/provider o modifica rule/unit/container. Il blocco sotto è registro storico, non rieseguirlo. Helper nuovo, source commit `4daad06b71695ad839d1865e55d5aeaf765df861`, hash `ecb0326b9f97f76598d9bad56aa241b01802bf0a601f4eda38fef41fb15c655a`. Il source runtime installato resta al vecchio commit `ef2270a57446da1f23a58548aa4d44920e578fe0`; non confondere i due pin. Non richiede login Keycloak. La preparazione scrive solo un nuovo source snapshot privato; il helper esegue read-only sulle evidenze e sullo stato host, sotto lock già esistente. Non applica nft, non crea journal, non chiama DNS/IAM, non esegue Docker start/exec/restart. Il risultato atteso è inventory PASS con startupReady=false, non startup/admission acceptance. In caso di BLOCKED conservare output/source root e cohort; niente replay runtime apply o reconcile/rollback alla cieca.

```bash
(
set -euo pipefail
OUF_READINESS_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_READINESS_TMP"' EXIT

curl --fail --silent --show-error --proto '=https' --max-time 30 \
  https://raw.githubusercontent.com/GioNob/ouf-api-gateway/4daad06b71695ad839d1865e55d5aeaf765df861/scripts/inventory_semantic_runtime_readiness.py \
  -o "$OUF_READINESS_TMP/inventory_semantic_runtime_readiness.py"

printf '%s  %s\n' \
  ecb0326b9f97f76598d9bad56aa241b01802bf0a601f4eda38fef41fb15c655a \
  "$OUF_READINESS_TMP/inventory_semantic_runtime_readiness.py" | sha256sum -c -

OUF_READINESS_ROOT="/etc/ouf/deploy-snapshots/semantic-runtime-readiness-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_READINESS_ROOT"
printf 'SEMANTIC_RUNTIME_READINESS_SOURCE_ROOT=%s\n' "$OUF_READINESS_ROOT"
sudo install -d -m 0700 -o root -g root "$OUF_READINESS_ROOT/source/scripts"
sudo install -m 0600 -o root -g root \
  "$OUF_READINESS_TMP/inventory_semantic_runtime_readiness.py" "$OUF_READINESS_ROOT/source/scripts/"

sudo /usr/bin/python3 -B "$OUF_READINESS_ROOT/source/scripts/inventory_semantic_runtime_readiness.py" \
  --stage-root /etc/ouf/deploy-snapshots/semantic-runtime-transition-stage-20261003-160211/prepared \
  --stage-source-commit ef2270a57446da1f23a58548aa4d44920e578fe0 \
  --installer-sha256 a3818878086a40377125816b776606f936ad02496d891f4bc72477c4c731ecf4
)
```

Output JSON e riga finale ricevuti con PASS e conservati nel checkpoint corrente; sezione del comando, checklist e quattro documenti canonici aggiornati. Il prossimo lavoro è il piano del §17. Le quantità e i purpose stampati aiutano a vincolare il piano successivo; non inventare indirizzi/namespace o authority dalla configurazione pianificata.

## 17. Piano shared faces e lifecycle — componenti software verificati, integrazione aperta

Non c'è un nuovo comando VPS da eseguire in questo checkpoint. Compiler, core di coordinazione e fixture native sono ora implementati e verificati nel commit Gateway `d38289132e49c9e9be4cb6245bb70a63cfaa82dc`, come riportato nel checkpoint corrente. L'integrazione target rimane aperta al §18. Il piano originario richiedeva enforcement del candidato southbound sulle interfacce shared (senza trasformare intere reti condivise in default-deny), anti-spoof/source binding e percorsi workload/identity autorizzati; usare porte e endpoint governati da configurazione, non inferire authority da IP osservati o route. I container mai avviati non forniscono prova di namespace/veth live; le prove isolate devono precedere una procedura target esplicita.

Per il lifecycle attivo servono coordinamento gate persistente/guard/owner con lo stesso lock, fresh DNS A+AAAA bounded per tutti i resolver selezionati, apply/readback atomico inet+bridge, stop/failure/restart revoke e expiry anche su established, binding handle riconciliato esplicitamente e niente auto-adoption di tabelle estranee. Il guard EMPTY_ONLY corrente e il package lease9 restano sealed; non modificarli in place né avviare il vecchio owner per convenienza. Anche un futuro profilo lease-aware non conferisce startup authority. Conservare gate admission/reboot e business acceptance, aggiornare documentazione dopo ogni esito.

## 18. Integrazione prima dell'esecuzione — core install/recovery PASS, hook runtime ancora aperto

I componenti e le fixture §17 sono PASS; nessun comando host da eseguire è ancora predisposto. Il nuovo backend richiede binding di porta/generazione verificato prima che il processo applicativo possa emettere pacchetti. Non fare attach delle regole in risposta a un evento Docker già avvenuto. Il runtime deve fornire un ordinamento sincrono network-before-process con fail-closed su creazione/ricreazione, rifiuto di ifindex riusati o binding incompleto e verifica prima di start. Integrare questo meccanismo e fixture di crash/recovery/port recreation prima del nuovo staging target.

Completare poi nuovo installer sealed/profile migrator, journal e artefatti guard/owner con lo stesso lock, bounded contention, service stop/restart/quiesce, readback/rollback e autorità infrastrutturale. Nessuna auto-adoption del vecchio journal o binding lease; il journal di coordination ha schema nuovo e startAuthorized=false. Non attivare il package lease9 sotto il guard EMPTY_ONLY attuale. Conservare tutti i cohort originali; le prove native nuove sono isolate, non prove di startup/admission del VPS. Aggiornare autonomamente handoff/roadmap/manuale/sprint/PR dopo ogni esito.

## 19. Inventario runtime preexec — ESEGUITO, PASS

Helper verificato nel job CI 111264097837 dell'esatto head Gateway `82d1db716b1015dac52feca217af1c5ed600a520`: 24 test e 3 native PASS senza skip. Suite complessiva verificata sull'esatto head: 34/34 completed/success, nessun pending/failure; prova distinta dalla precedente revisione core. Nessuna prova target inventata.

Questo blocco prepara soltanto un nuovo source snapshot root privato e legge informazioni pubbliche/sanitizzate del runtime locale. **Non cambia nft/unit/container, non registra runtime e non esegue inspect/start/exec/restart/DNS/IAM/provider.** Non richiede rinnovo Keycloak. Se /usr/bin/runc non è il binario disponibile o un dato/metadata non è provato, il helper restituisce BLOCKED con motivo non sensibile: conservare output e source root, non cambiare il daemon e non ripetere vecchi apply. La versione standalone non prova il binario usato da Docker.

```bash
(
set -euo pipefail
OUF_PREEXEC_INV_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_PREEXEC_INV_TMP"' EXIT

curl --fail --silent --show-error --proto '=https' --max-time 30 \
  https://raw.githubusercontent.com/GioNob/ouf-api-gateway/82d1db716b1015dac52feca217af1c5ed600a520/scripts/inventory_semantic_preexec_runtime.py \
  -o "$OUF_PREEXEC_INV_TMP/inventory_semantic_preexec_runtime.py"

printf '%s  %s\n' \
  5caf118353fbb49457ad083bdcf26e778413ba9ea699978ce52465a8480860e1 \
  "$OUF_PREEXEC_INV_TMP/inventory_semantic_preexec_runtime.py" | sha256sum -c -

OUF_PREEXEC_INV_ROOT="/etc/ouf/deploy-snapshots/semantic-preexec-runtime-inventory-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_PREEXEC_INV_ROOT"
sudo install -d -m 0700 -o root -g root "$OUF_PREEXEC_INV_ROOT/source/scripts"
sudo install -m 0600 -o root -g root \
  "$OUF_PREEXEC_INV_TMP/inventory_semantic_preexec_runtime.py" "$OUF_PREEXEC_INV_ROOT/source/scripts/"
printf 'SEMANTIC_PREEXEC_RUNTIME_SOURCE_ROOT=%s\n' "$OUF_PREEXEC_INV_ROOT"

sudo /usr/bin/python3 -I -B \
  "$OUF_PREEXEC_INV_ROOT/source/scripts/inventory_semantic_preexec_runtime.py" \
  --docker-path /usr/bin/docker \
  --runc-path /usr/bin/runc
)
```

Esito atteso: JSON schema ouf.semantic-preexec-runtime-inventory.v1 seguito da PASS READ_ONLY=true OCI_HOOK_INTEGRATION_PROVEN=false START_AUTHORIZED=false. **ESEGUITO, PASS:** output operatore e source root riportati sopra; quattro documenti aggiornati. Non ripetere il blocco storico. Nessuna successiva installazione o applicazione implicita.

## 20. Source package preexec privato — ESEGUITO; plan/apply/verify PASS

Il comando seguente prepara soltanto un nuovo source snapshot. L'apply è **pubblicazione della receipt privata**, non installazione di regole/hook/unit/runtime o start. Non modifica il package lease9, cohort runtime, reti, candidati, daemon Docker o journal già esistenti. Pinna undici file del commit Gateway `1a020edea42cdf60a38298bec2ffebc97b3fad02` e verifica ciascun SHA256 prima di copiarlo in root:root 0600. Il nuovo stager è provato con plan/apply/verify, rifiuto replay e source drift; la prova OCI con runc 1.5.1 è PASS nei due job del checkpoint. Non trasferire questa prova CI al VPS.

Atteso PASS per tutti e tre i modi con PRIVATE_SOURCE_ONLY=true RUNTIME_REGISTERED=false START_AUTHORIZED=false. JSON contiene Python version e disponibilità di strumenti root-owned: può essere PASS anche se busybox/tool opzionali sono assenti, perché il source staging non prova la readiness del runtime. Riportare l'intero output e PACKAGE_ROOT. Su BLOCKED conservare snapshot/output; niente replay apply, rimozione dei cohort o apt/restart per convenienza. Non richiede login Keycloak.

```bash
(
set -euo pipefail
OUF_PREEXEC_PKG_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_PREEXEC_PKG_TMP"' EXIT

cat > "$OUF_PREEXEC_PKG_TMP/sources.sha256" <<'OUF_PREEXEC_SHA'
bf86bc438c39a1f8f7752797110bcfcf18b9e7deb23a662f850fffb900df2fd8  scripts/stage_semantic_preexec_package.py
e904774d50626e3ce93d6bcd187571b03d0698ad6a7472a7b6a862b4816eb850  scripts/semantic_provider_preexec_hook.py
98e3004300226fecd509a46c009585df14021927f20d4e5c82d8ff7a8a8180de  tools/materialize_southbound_kernel.py
1c0d7f1243752fe216ef62eefbc2e3253b8f2503b518fafe11277e4d7721a084  tools/materialize_southbound_lease_refresh.py
c466172113d1ffe850bf2c69762113b55fbc65d9091c96dca98a74548fddf930  tools/semantic_provider_dns.py
7a5f2b21c096228a3e4d298674e380f667c3004dd6d8ec19934a2302844c0f93  tools/semantic_provider_lease_nft.py
92736eebeccf344e565186bce94d29c65ffe1d50638d57eae81486e7b26e884d  tools/semantic_provider_lease_owner.py
b97f31cc17c22abbb7a021c274be73816f649196762f9c6dfcc54a58d8382e8a  tools/materialize_semantic_shared_faces.py
25c6df90d33e39fe83321df6ab9e5c38d4c33bcd290ad57c7a85c03b1bb8ba78  tools/semantic_provider_lease_coordination.py
5086f893ac22e962816e76709883c9c7f341989919339c579a4f28bfbd403804  tools/semantic_provider_preexec.py
c45d343308a311790bcd5c9ed9687925d4af0fec59f96fc79f4af7a685b8c70f  tools/semantic_provider_preexec_native.py
OUF_PREEXEC_SHA

while read -r OUF_PREEXEC_HASH OUF_PREEXEC_FILE; do
  mkdir -p -- "$OUF_PREEXEC_PKG_TMP/$(dirname -- "$OUF_PREEXEC_FILE")"
  curl --fail --silent --show-error --proto '=https' --max-time 30 \
    "https://raw.githubusercontent.com/GioNob/ouf-api-gateway/1a020edea42cdf60a38298bec2ffebc97b3fad02/$OUF_PREEXEC_FILE" \
    -o "$OUF_PREEXEC_PKG_TMP/$OUF_PREEXEC_FILE"
done < "$OUF_PREEXEC_PKG_TMP/sources.sha256"

(cd "$OUF_PREEXEC_PKG_TMP"; sha256sum -c sources.sha256)

OUF_PREEXEC_PKG_ROOT="/etc/ouf/deploy-snapshots/semantic-preexec-package-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_PREEXEC_PKG_ROOT"
sudo install -d -m 0700 -o root -g root \
  "$OUF_PREEXEC_PKG_ROOT/source/scripts" "$OUF_PREEXEC_PKG_ROOT/source/tools"
while read -r OUF_PREEXEC_HASH OUF_PREEXEC_FILE; do
  sudo install -m 0600 -o root -g root \
    "$OUF_PREEXEC_PKG_TMP/$OUF_PREEXEC_FILE" "$OUF_PREEXEC_PKG_ROOT/source/$OUF_PREEXEC_FILE"
done < "$OUF_PREEXEC_PKG_TMP/sources.sha256"
printf 'SEMANTIC_PREEXEC_PACKAGE_ROOT=%s\n' "$OUF_PREEXEC_PKG_ROOT"

for OUF_PREEXEC_PKG_MODE in plan apply verify; do
  sudo /usr/bin/python3 -I -B \
    "$OUF_PREEXEC_PKG_ROOT/source/scripts/stage_semantic_preexec_package.py" \
    --mode "$OUF_PREEXEC_PKG_MODE" \
    --package-root "$OUF_PREEXEC_PKG_ROOT" \
    --source-commit 1a020edea42cdf60a38298bec2ffebc97b3fad02 \
    --hook-source-sha256 e904774d50626e3ce93d6bcd187571b03d0698ad6a7472a7b6a862b4816eb850
done
)
```

**ESEGUITO:** output operatore plan/apply/verify PASS ricevuto; handoff/roadmap/manuale/sprint aggiornati con package root e receipt. Il comando sopra è storico, non da rieseguire. Per il passo successivo restano authority e profilo target/generazione/runtime integration, senza avvii o registrazioni impliciti.

## 21. Inventario runtime/binding dei candidati fermi — ESEGUITO, PASS; comando storico di sola lettura

Prerequisiti attestati: §20 ESEGUITO PASS e candidati mai avviati; manifest/creation journal pin agli hash seguenti. Lo snapshot del helper è nuovo e privato, separato dal package preexec sigillato. Il helper non scrive receipt/journal o regole e non interroga IAM/DNS/provider. Nessun login Keycloak necessario. Non verifica l'intera configurazione della creazione né il guard runtime attuale.

Atteso: due righe JSON/PASS con READ_ONLY=true, configuredBindingsMatchManifest=true, candidatesNeverStarted=true, liveNamespaceBindingProven=false, atomicSnapshotProven=false, ociHookIntegrationProven=false e startAuthorized=false. CandidateRuntimes e sandboxKeyPresentCount sono risultati da raccogliere, **non predetti né acceptance**. Su BLOCKED conservare source root/output; niente avvio, registrazione runtime, ricreazione o replay automatico. Riportare source root e intero output redatto.

```bash
(
set -euo pipefail
OUF_CANDIDATE_INV_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_CANDIDATE_INV_TMP"' EXIT
curl --fail --silent --show-error --proto '=https' --max-time 30 \
  https://raw.githubusercontent.com/GioNob/ouf-api-gateway/6e84e5ca1134cd8e26b603380a0adcb06a15fb0c/scripts/inventory_semantic_preexec_candidates.py \
  -o "$OUF_CANDIDATE_INV_TMP/inventory_semantic_preexec_candidates.py"
printf '%s  %s\n' \
  63fb3da6682861cd033c236a2830668bb4648b27ddc139799a05a8c62652f0bb \
  "$OUF_CANDIDATE_INV_TMP/inventory_semantic_preexec_candidates.py" | sha256sum -c -
OUF_CANDIDATE_INV_ROOT="/etc/ouf/deploy-snapshots/semantic-preexec-candidate-inventory-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_CANDIDATE_INV_ROOT"
sudo install -d -m 0700 -o root -g root "$OUF_CANDIDATE_INV_ROOT/source"
sudo install -m 0600 -o root -g root \
  "$OUF_CANDIDATE_INV_TMP/inventory_semantic_preexec_candidates.py" "$OUF_CANDIDATE_INV_ROOT/source/"
printf 'SEMANTIC_PREEXEC_CANDIDATE_SOURCE_ROOT=%s\n' "$OUF_CANDIDATE_INV_ROOT"
sudo /usr/bin/python3 -I -B "$OUF_CANDIDATE_INV_ROOT/source/inventory_semantic_preexec_candidates.py" \
  --manifest-root /etc/ouf/deploy-snapshots/semantic-provider-candidate-manifest-20261003-130410/prepared \
  --creation-root /etc/ouf/deploy-snapshots/semantic-provider-stopped-create-20261003-135106/prepared \
  --network-root /etc/ouf/deploy-snapshots/semantic-provider-networks-20261003-072023/prepared \
  --expected-manifest-hash 052b46a56ea666971f135c75af48b3342dbeb68e2f17f1f16263a99351df88bd \
  --expected-creation-journal-hash a1c2acd9924fc0f924ded7c2d59f128ef2d8b8dd11c62484a901f628022aaae7 \
  --creation-source-commit 93e861fe8c8a43912f0cb78a74adceb2db509dd9 \
  --docker-path /usr/bin/docker
)
```

**ESEGUITO sul VPS:** output operatore PASS ricevuto e registrato in handoff/roadmap/manuale/sprint. Runtime runc, due candidati mai avviati, tre reti configurate, SandboxKey presenti zero; bindingHash `0337655a5c3d6d80653aca363d8479ce10e6d27cde024518060a6c628e542aeb`. Il comando sopra è storico e non da rieseguire. Prossimo lavoro: adapter Docker e prove CI, mantenendo separata l'authority di infrastruttura dal semplice inventario.


## 22. Nuovo source package adapter v2 privato — ESEGUITO; plan/apply/verify PASS

Prerequisito CI sul commit `b5260260fff1adf798626f12e24323c20ae1bb2e`: 36/36 success, Docker adapter positivo/negative/cleanup e regressioni native senza skip; dodici contenuti e SHA256 verificati contro GitHub. Sintassi del comando verificata con bash -n. Questa è preparazione dei soli sorgenti: non registra né installa un runtime, broker o profilo, non modifica regole/unità/container e non avvia candidati. Il precedente package v1 resta immutabile. Non include il preparer sintetico CI. Docker integration su runner non autorizza l'integrazione target.

Il comando crea una radice esclusiva nuova con directory root 0700 e file root 0600. Esegue plan/apply/verify e salva il receipt v2 privato; trustedToolsAvailable è solo metadata, non prova funzionale. Atteso runtimeAdapterInstalled=false, admissionPreparerInstalled=false, runtimeRegistered=false, startAuthorized=false, providerCalls=0 e notReleaseAcceptance=true. Su BLOCKED conservare radice/output, niente replay o riparazione automatica. Riportare package root e intero output redatto.

```bash
(
set -euo pipefail
OUF_PREEXEC_PKG_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_PREEXEC_PKG_TMP"' EXIT

cat > "$OUF_PREEXEC_PKG_TMP/sources.sha256" <<'OUF_PREEXEC_SHA'
3fb04519de05131087a5bd12095b42f97026e7c5826d5f8f3845608404008f95  scripts/stage_semantic_preexec_package.py
f4185658a7a9a1190cd9ee85ed6f6397de5344bad15a6d3078d765f88c914093  scripts/semantic_provider_docker_runtime.py
2da64dc68707fb694a49656562800d733184a21845293fee172a6f99167534b3  scripts/semantic_provider_preexec_hook.py
98e3004300226fecd509a46c009585df14021927f20d4e5c82d8ff7a8a8180de  tools/materialize_southbound_kernel.py
1c0d7f1243752fe216ef62eefbc2e3253b8f2503b518fafe11277e4d7721a084  tools/materialize_southbound_lease_refresh.py
c466172113d1ffe850bf2c69762113b55fbc65d9091c96dca98a74548fddf930  tools/semantic_provider_dns.py
7a5f2b21c096228a3e4d298674e380f667c3004dd6d8ec19934a2302844c0f93  tools/semantic_provider_lease_nft.py
92736eebeccf344e565186bce94d29c65ffe1d50638d57eae81486e7b26e884d  tools/semantic_provider_lease_owner.py
b97f31cc17c22abbb7a021c274be73816f649196762f9c6dfcc54a58d8382e8a  tools/materialize_semantic_shared_faces.py
25c6df90d33e39fe83321df6ab9e5c38d4c33bcd290ad57c7a85c03b1bb8ba78  tools/semantic_provider_lease_coordination.py
f541eca6bee47a68a08d06ad7b577a3a7894ca02d8674d97e36d6cb2bafe0fcd  tools/semantic_provider_preexec.py
b6b09ef5209d92405d85ef4161b671ade10c300b797569362c301ae9293b6ac0  tools/semantic_provider_preexec_native.py
OUF_PREEXEC_SHA

while read -r OUF_PREEXEC_HASH OUF_PREEXEC_FILE; do
  mkdir -p -- "$OUF_PREEXEC_PKG_TMP/$(dirname -- "$OUF_PREEXEC_FILE")"
  curl --fail --silent --show-error --proto '=https' --max-time 30 \
    "https://raw.githubusercontent.com/GioNob/ouf-api-gateway/b5260260fff1adf798626f12e24323c20ae1bb2e/$OUF_PREEXEC_FILE" \
    -o "$OUF_PREEXEC_PKG_TMP/$OUF_PREEXEC_FILE"
done < "$OUF_PREEXEC_PKG_TMP/sources.sha256"

(cd "$OUF_PREEXEC_PKG_TMP"; sha256sum -c sources.sha256)

OUF_PREEXEC_PKG_ROOT="/etc/ouf/deploy-snapshots/semantic-preexec-adapter-package-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_PREEXEC_PKG_ROOT"
sudo install -d -m 0700 -o root -g root \
  "$OUF_PREEXEC_PKG_ROOT/source/scripts" "$OUF_PREEXEC_PKG_ROOT/source/tools"
while read -r OUF_PREEXEC_HASH OUF_PREEXEC_FILE; do
  sudo install -m 0600 -o root -g root \
    "$OUF_PREEXEC_PKG_TMP/$OUF_PREEXEC_FILE" "$OUF_PREEXEC_PKG_ROOT/source/$OUF_PREEXEC_FILE"
done < "$OUF_PREEXEC_PKG_TMP/sources.sha256"
printf 'SEMANTIC_PREEXEC_PACKAGE_ROOT=%s\n' "$OUF_PREEXEC_PKG_ROOT"

for OUF_PREEXEC_PKG_MODE in plan apply verify; do
  sudo /usr/bin/python3 -I -B \
    "$OUF_PREEXEC_PKG_ROOT/source/scripts/stage_semantic_preexec_package.py" \
    --mode "$OUF_PREEXEC_PKG_MODE" \
    --package-root "$OUF_PREEXEC_PKG_ROOT" \
    --source-commit b5260260fff1adf798626f12e24323c20ae1bb2e \
    --hook-source-sha256 2da64dc68707fb694a49656562800d733184a21845293fee172a6f99167534b3
done
)
```

**ESEGUITO sul VPS:** output operatore ricevuto, dodici checksum OK e plan/apply/verify PASS. Package root `/etc/ouf/deploy-snapshots/semantic-preexec-adapter-package-20261003-213033`, source commit `b5260260fff1adf798626f12e24323c20ae1bb2e`, schema v2, Python 3.13.5. runtimeAdapterInstalled/admissionPreparerInstalled/runtimeRegistered/startAuthorized=false; rulesChanged/unitsChanged/containersChanged=false, providerCalls=0. Il comando sopra è storico e non da rieseguire automaticamente. Handoff, roadmap, manuale e sprint aggiornati con l'attestazione effettiva; preparer/authority/footprint indipendente e registrazione/cohort/recovery restano separati e non autorizzati dal receipt.

## 23. Source package admission v3 privato — ESEGUITO PASS; comando storico

Prerequisito verificato: gateway `ed6fab81acc17591a1087761266701f877233799`, CI 38/38 success e prove native senza skip. Questa operazione prepara soltanto quindici sorgenti root-private, sigilla un receipt v3 e verifica il package. Non esegue il preparer, non crea namespace o template nativi, approval, profili, journal di runtime, lease o regole, non registra runtime né modifica unità/container e non avvia applicazioni. Package v1 e v2 restano immutabili. I dodici sorgenti che il preparer verifica e gli undici del driver v3 sono sottoinsiemi espliciti del source package a quindici file.

Hash/contenuti verificati 15/15 contro GitHub; sintassi bash verificata. trustedToolsAvailable è metadata, non prova funzionale. Atteso schema `ouf.semantic-admission-source-package.v3`, quindici sourceHashes, plan/apply/verify PASS, runtimeAdapterInstalled/admissionPreparerInstalled/runtimeRegistered/startAuthorized/rulesChanged/unitsChanged/containersChanged=false, providerCalls=0 e notReleaseAcceptance=true. Su BLOCKED conservare root/output; non riscrivere i package vecchi, non fare replay automatico. Riportare la nuova root e tutto l'output redatto.

```bash
(
set -euo pipefail
OUF_PREEXEC_PKG_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_PREEXEC_PKG_TMP"' EXIT

cat > "$OUF_PREEXEC_PKG_TMP/sources.sha256" <<'OUF_PREEXEC_SHA'
84f6b1fec995b9675284253321930efee0056e4546168058bae6a3667a2ff7d7  scripts/stage_semantic_admission_package.py
3fb04519de05131087a5bd12095b42f97026e7c5826d5f8f3845608404008f95  scripts/stage_semantic_preexec_package.py
3106ade7c32e5d37ce7aa0214726907a3422c2850741168b7ee7d273b98b00fb  scripts/semantic_provider_docker_runtime.py
5f38532f73f620cbbc9980b02a2e29cd8a4cdabafce370aba5a8a50e330065a5  scripts/semantic_provider_preexec_hook.py
5b31650fddb0d47dad99f128d0d8775bde56a2f7489b0f5476956e17eaba125d  scripts/semantic_provider_admission_preparer.py
98e3004300226fecd509a46c009585df14021927f20d4e5c82d8ff7a8a8180de  tools/materialize_southbound_kernel.py
1c0d7f1243752fe216ef62eefbc2e3253b8f2503b518fafe11277e4d7721a084  tools/materialize_southbound_lease_refresh.py
c466172113d1ffe850bf2c69762113b55fbc65d9091c96dca98a74548fddf930  tools/semantic_provider_dns.py
7a5f2b21c096228a3e4d298674e380f667c3004dd6d8ec19934a2302844c0f93  tools/semantic_provider_lease_nft.py
92736eebeccf344e565186bce94d29c65ffe1d50638d57eae81486e7b26e884d  tools/semantic_provider_lease_owner.py
b97f31cc17c22abbb7a021c274be73816f649196762f9c6dfcc54a58d8382e8a  tools/materialize_semantic_shared_faces.py
25c6df90d33e39fe83321df6ab9e5c38d4c33bcd290ad57c7a85c03b1bb8ba78  tools/semantic_provider_lease_coordination.py
b0fc54f39ec1b650a1e51a721127cca2cda1c2cd6bd9c2179919929a1cb50bc7  tools/semantic_provider_preexec.py
ef0b98c96879933480a26418edc2b971b21a116509ac87cbc39e3b2062e7a528  tools/semantic_provider_preexec_native.py
4bd0051fad23acd91fc42eb9b6cd2f2dac6e8d9d960fefd391add261a3646499  tools/semantic_provider_deployment_admission.py
OUF_PREEXEC_SHA

while read -r OUF_PREEXEC_HASH OUF_PREEXEC_FILE; do
  mkdir -p -- "$OUF_PREEXEC_PKG_TMP/$(dirname -- "$OUF_PREEXEC_FILE")"
  curl --fail --silent --show-error --proto '=https' --max-time 30 \
    "https://raw.githubusercontent.com/GioNob/ouf-api-gateway/ed6fab81acc17591a1087761266701f877233799/$OUF_PREEXEC_FILE" \
    -o "$OUF_PREEXEC_PKG_TMP/$OUF_PREEXEC_FILE"
done < "$OUF_PREEXEC_PKG_TMP/sources.sha256"

(cd "$OUF_PREEXEC_PKG_TMP"; sha256sum -c sources.sha256)

OUF_PREEXEC_PKG_ROOT="/etc/ouf/deploy-snapshots/semantic-admission-package-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_PREEXEC_PKG_ROOT"
sudo install -d -m 0700 -o root -g root \
  "$OUF_PREEXEC_PKG_ROOT/source/scripts" "$OUF_PREEXEC_PKG_ROOT/source/tools"
while read -r OUF_PREEXEC_HASH OUF_PREEXEC_FILE; do
  sudo install -m 0600 -o root -g root \
    "$OUF_PREEXEC_PKG_TMP/$OUF_PREEXEC_FILE" "$OUF_PREEXEC_PKG_ROOT/source/$OUF_PREEXEC_FILE"
done < "$OUF_PREEXEC_PKG_TMP/sources.sha256"
printf 'SEMANTIC_ADMISSION_PACKAGE_ROOT=%s\n' "$OUF_PREEXEC_PKG_ROOT"

for OUF_PREEXEC_PKG_MODE in plan apply verify; do
  sudo /usr/bin/python3 -I -B \
    "$OUF_PREEXEC_PKG_ROOT/source/scripts/stage_semantic_admission_package.py" \
    --mode "$OUF_PREEXEC_PKG_MODE" \
    --package-root "$OUF_PREEXEC_PKG_ROOT" \
    --source-commit ed6fab81acc17591a1087761266701f877233799 \
    --hook-source-sha256 5f38532f73f620cbbc9980b02a2e29cd8a4cdabafce370aba5a8a50e330065a5
done
)
```

**VPS §23 ESEGUITO — attestazione operatore del 4 ottobre 2026:** quindici checksum iniziali OK; plan/apply/verify **PASS** concordanti in `/etc/ouf/deploy-snapshots/semantic-admission-package-20261004-055825`, schema `ouf.semantic-admission-source-package.v3`, source commit `ed6fab81acc17591a1087761266701f877233799`, Python 3.13.5. Attestazione salvata in `docs/handoffs/receipts/SEMANTIC_ADMISSION_PACKAGE_V3_2026-10-04_OPERATOR.json`; nessuna lettura indipendente del VPS o digest del receipt dichiarati. admissionPreparerInstalled/runtimeAdapterInstalled/runtimeRegistered/startAuthorized=false; rulesChanged/unitsChanged/containersChanged=false, providerCalls=0, notReleaseAcceptance=true e noSecretsPrinted=true. Nove trustedToolsAvailable=true indicano disponibilità metadata, non compatibilità funzionale. §20/§21/§22 e snapshot precedenti restano storici e immutabili; l'ultimo guard attestato era RUNTIME_EMPTY/EMPTY_ONLY, non nuovamente verificato da questo receipt.

**Prossimo passo preciso:** chiudere la prova Docker adapter v2/driver v3 con preparer reale in CI isolata, senza assumere acceptance VPS. Prima di qualsiasi profilo/installazione/registrazione/start sul target occorrono produttori realmente approvati di deployment approval e full creation acceptance e custody target verificata. Nessun comando VPS aggiuntivo è autorizzato da questo receipt; §23 è storico, non da rieseguire automaticamente.


## 24. Installazioni autonome e admission a due fasi — approvato; contratto repository ESEGUITO

Decisione approvata dall'utente il 4 ottobre 2026: un Ente, una installazione autonoma. Contratto gateway `d0784285dc98651a732d1328ec2aef5cc0eb8955`, 18 nuovi test PASS e CI 38/38 completed/success; dettagli nel checkpoint corrente e in `docs/architecture/OUF_INDEPENDENT_INSTALLATIONS_DEPLOYMENT_ADMISSION_2026-10-04.md`. Nessun nuovo comando VPS, installazione, registrazione, avvio o replay eseguito. Il prossimo lavoro è la migrazione installer/adapter con journal durevole e consumo unico sotto common lock; gate concreti di authority e acceptance restano aperti.


## 25. Package deployment v4 privato — ESEGUITO PASS; comando storico

Prerequisiti: operatore oufadmin con sudo, accesso HTTPS ai sorgenti pinned. La radice deve essere nuova; conservare i package precedenti. Questa operazione copia e sigilla soltanto 18 sorgenti con schema source-package v4. Non installa adapter/preparer/broker, non registra runtime, non cambia unità/regole/container e non autorizza avvio o lease. Il modulo consumer supporta journal iniziali provisionati dall'installer, ma questo comando non ne crea né popola alcuno; non produce intent, attestazioni o approval.

Source commit: `cc161b94c1af014403dabd113200d3180f02089d`. Comando standalone: `docs/handoffs/commands/OUF_STAGE_DEPLOYMENT_PACKAGE_V4_2026-10-04.sh`; SHA256 `b6ad57b07b4b28cb8791fb64d7df39c915d48dc2022e1db163b24235e57f5dd5`. Bash syntax PASS e source pin/hash readback 18/18. Fixture e chiavi sintetiche escluse.

```bash
(
set -euo pipefail
OUF_DEPLOYMENT_PKG_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_DEPLOYMENT_PKG_TMP"' EXIT

cat > "$OUF_DEPLOYMENT_PKG_TMP/sources.sha256" <<'OUF_DEPLOYMENT_SHA'
e2ee1c81de0cf9004538adc0393833453d826a9e1a2533fa9baba95aab50e8b0  scripts/stage_semantic_deployment_package.py
84f6b1fec995b9675284253321930efee0056e4546168058bae6a3667a2ff7d7  scripts/stage_semantic_admission_package.py
3fb04519de05131087a5bd12095b42f97026e7c5826d5f8f3845608404008f95  scripts/stage_semantic_preexec_package.py
c05c0216c0cec774f13ab27b193ab92599dd191314a157dc76b26ad978bc215c  scripts/semantic_provider_docker_runtime.py
a4ca047fc76dda6378e81834cac421d5d829b55d63ac62dde29a3178245aaabc  scripts/semantic_provider_preexec_hook.py
e8f6670029e6e3bf7a74e79dadd710b5a62bf31a23abd4c2785a71f36245a03c  scripts/semantic_provider_admission_preparer.py
98e3004300226fecd509a46c009585df14021927f20d4e5c82d8ff7a8a8180de  tools/materialize_southbound_kernel.py
1c0d7f1243752fe216ef62eefbc2e3253b8f2503b518fafe11277e4d7721a084  tools/materialize_southbound_lease_refresh.py
c466172113d1ffe850bf2c69762113b55fbc65d9091c96dca98a74548fddf930  tools/semantic_provider_dns.py
7a5f2b21c096228a3e4d298674e380f667c3004dd6d8ec19934a2302844c0f93  tools/semantic_provider_lease_nft.py
92736eebeccf344e565186bce94d29c65ffe1d50638d57eae81486e7b26e884d  tools/semantic_provider_lease_owner.py
b97f31cc17c22abbb7a021c274be73816f649196762f9c6dfcc54a58d8382e8a  tools/materialize_semantic_shared_faces.py
25c6df90d33e39fe83321df6ab9e5c38d4c33bcd290ad57c7a85c03b1bb8ba78  tools/semantic_provider_lease_coordination.py
1ade8d45a7387bd3b22464a34401ab6b4358f76e5c025ac84d80951542eb1fad  tools/semantic_provider_preexec.py
ef0b98c96879933480a26418edc2b971b21a116509ac87cbc39e3b2062e7a528  tools/semantic_provider_preexec_native.py
4bd0051fad23acd91fc42eb9b6cd2f2dac6e8d9d960fefd391add261a3646499  tools/semantic_provider_deployment_admission.py
87e4eed4485cee0736bb7031827ee773efde6f4fb97d6289c885fc5cf2049592  tools/semantic_provider_deployment_protocol.py
88b848be497607a71a9fc8def9164119d8bcf74d095d906fd56e6f91b7cb642a  tools/semantic_provider_deployment_consumption.py
OUF_DEPLOYMENT_SHA

while read -r OUF_DEPLOYMENT_HASH OUF_DEPLOYMENT_FILE; do
  mkdir -p -- "$OUF_DEPLOYMENT_PKG_TMP/$(dirname -- "$OUF_DEPLOYMENT_FILE")"
  curl --fail --silent --show-error --proto '=https' --max-time 30 \
    "https://raw.githubusercontent.com/GioNob/ouf-api-gateway/cc161b94c1af014403dabd113200d3180f02089d/$OUF_DEPLOYMENT_FILE" \
    -o "$OUF_DEPLOYMENT_PKG_TMP/$OUF_DEPLOYMENT_FILE"
done < "$OUF_DEPLOYMENT_PKG_TMP/sources.sha256"

(cd "$OUF_DEPLOYMENT_PKG_TMP"; sha256sum -c sources.sha256)

OUF_DEPLOYMENT_PKG_ROOT="/etc/ouf/deploy-snapshots/semantic-deployment-package-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_DEPLOYMENT_PKG_ROOT"
sudo install -d -m 0700 -o root -g root \
  "$OUF_DEPLOYMENT_PKG_ROOT/source/scripts" "$OUF_DEPLOYMENT_PKG_ROOT/source/tools"
while read -r OUF_DEPLOYMENT_HASH OUF_DEPLOYMENT_FILE; do
  sudo install -m 0600 -o root -g root \
    "$OUF_DEPLOYMENT_PKG_TMP/$OUF_DEPLOYMENT_FILE" "$OUF_DEPLOYMENT_PKG_ROOT/source/$OUF_DEPLOYMENT_FILE"
done < "$OUF_DEPLOYMENT_PKG_TMP/sources.sha256"
printf 'SEMANTIC_DEPLOYMENT_PACKAGE_ROOT=%s\n' "$OUF_DEPLOYMENT_PKG_ROOT"

for OUF_DEPLOYMENT_PKG_MODE in plan apply verify; do
  sudo /usr/bin/python3 -I -B \
    "$OUF_DEPLOYMENT_PKG_ROOT/source/scripts/stage_semantic_deployment_package.py" \
    --mode "$OUF_DEPLOYMENT_PKG_MODE" \
    --package-root "$OUF_DEPLOYMENT_PKG_ROOT" \
    --source-commit cc161b94c1af014403dabd113200d3180f02089d \
    --hook-source-sha256 a4ca047fc76dda6378e81834cac421d5d829b55d63ac62dde29a3178245aaabc
done
)
```

**VPS §25 ESEGUITO — attestazione operatore del 4 ottobre 2026:** checksum comando OK e 18 sorgenti OK, plan/apply/verify **PASS** concordanti in `/etc/ouf/deploy-snapshots/semantic-deployment-package-20261004-072744`, schema `ouf.semantic-deployment-source-package.v4`, source `cc161b94c1af014403dabd113200d3180f02089d`, Python 3.13.5. Attestazione `docs/handoffs/receipts/SEMANTIC_DEPLOYMENT_PACKAGE_V4_2026-10-04_OPERATOR.json`; nessuna lettura indipendente del VPS né digest del receipt dichiarati. externalProducerInstalled/runtimeAdapterInstalled/admissionPreparerInstalled/runtimeRegistered/startAuthorized=false; rulesChanged/unitsChanged/containersChanged=false, providerCalls=0, notReleaseAcceptance/noSecretsPrinted=true. Nove trustedToolsAvailable=true sono metadata, non compatibilità funzionale. Questo nuovo snapshot e i precedenti sono immutabili; §25 è storico e non va rieseguito automaticamente.

**Prossimo passo preciso:** predisporre il collegamento a produttori realmente autorizzati della singola installazione, con autenticazione delle evidenze distinta dal semplice hash/root ownership. Prima della selezione del backend crittografico sul target, verificarne disponibilità/versione/supporto senza generare chiavi, concessioni o approval. Mandati, identity binding M2M quando applicabile, full image/rootfs acceptance e configurazione del broker reale restano gate espliciti; nessun avvio o runtime registration autorizzato.

## 26. Inventario backend pubblico — ESEGUITO/PASS, comando storico

Nessuna installazione di producer né nuova authority. Comando read-only pinning helper e ricevuta operatore; restituisce la custody sorgenti e il risultato reale della verifica pubblica.

```bash
#!/usr/bin/env bash
# §26 ESEGUITO/PASS — comando storico, non ripetere.
set -euo pipefail
OUF_TRUST_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_TRUST_TMP"' EXIT
curl --fail --silent --show-error --proto '=https' --max-time 30 \
  https://raw.githubusercontent.com/GioNob/ouf-api-gateway/3c62e7a98957545623e3d3183e067d9c1bd4a6c8/scripts/inventory_semantic_deployment_trust_backend.py \
  -o "$OUF_TRUST_TMP/inventory.py"
curl --fail --silent --show-error --proto '=https' --max-time 30 \
  https://raw.githubusercontent.com/GioNob/ouf-semantic-registry/d033b0b8a3bfafaa405ea8f9745ac7c0c6e99f90/docs/handoffs/receipts/SEMANTIC_DEPLOYMENT_PACKAGE_V4_2026-10-04_OPERATOR.json \
  -o "$OUF_TRUST_TMP/operator.json"
printf '%s  %s\n' \
  9a948314f7d16820a6f4a4a0d71027f2307d5f080bf69377eaeb8bba05b48a79 "$OUF_TRUST_TMP/inventory.py" \
  315cf438aa8dec194958e61a99a8364526531b72472cdb9f74bee930a5e15146 "$OUF_TRUST_TMP/operator.json" | sha256sum -c -
OUF_TRUST_ROOT="/etc/ouf/deploy-snapshots/semantic-deployment-trust-backend-inventory-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_TRUST_ROOT"
sudo install -d -m 0700 -o root -g root "$OUF_TRUST_ROOT/source"
sudo install -m 0600 -o root -g root "$OUF_TRUST_TMP/inventory.py" "$OUF_TRUST_TMP/operator.json" "$OUF_TRUST_ROOT/source/"
printf 'SEMANTIC_DEPLOYMENT_TRUST_BACKEND_SOURCE_ROOT=%s\n' "$OUF_TRUST_ROOT"
sudo /usr/bin/python3 -I -B "$OUF_TRUST_ROOT/source/inventory.py" \
  --package-root /etc/ouf/deploy-snapshots/semantic-deployment-package-20261004-072744 \
  --operator-attestation "$OUF_TRUST_ROOT/source/operator.json" \
  --openssl-path /usr/bin/openssl
```

## 27. Package v5 soltanto sorgenti — ESEGUITO/PASS, registro storico

**ESEGUITO/PASS il 4 ottobre 2026. Non ripetere.** Nessuna authority, chiave o runtime installato. Nuovo snapshot, nessun replay dei vecchi package.

```bash
#!/usr/bin/env bash
# §27 ESEGUITO/PASS — comando storico, non ripetere. Solo sorgenti privati.
set -euo pipefail
OUF_AUTH_PKG_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_AUTH_PKG_TMP"' EXIT
cat > "$OUF_AUTH_PKG_TMP/sources.sha256" <<'OUF_AUTH_SHA'
e8f6670029e6e3bf7a74e79dadd710b5a62bf31a23abd4c2785a71f36245a03c  scripts/semantic_provider_admission_preparer.py
c05c0216c0cec774f13ab27b193ab92599dd191314a157dc76b26ad978bc215c  scripts/semantic_provider_docker_runtime.py
a4ca047fc76dda6378e81834cac421d5d829b55d63ac62dde29a3178245aaabc  scripts/semantic_provider_preexec_hook.py
84f6b1fec995b9675284253321930efee0056e4546168058bae6a3667a2ff7d7  scripts/stage_semantic_admission_package.py
2be2d851db0ae5f5189c0b4c5aed27a74a7e91a58f080e5ef16d1a0bba181d9a  scripts/stage_semantic_authenticated_deployment_package.py
e2ee1c81de0cf9004538adc0393833453d826a9e1a2533fa9baba95aab50e8b0  scripts/stage_semantic_deployment_package.py
3fb04519de05131087a5bd12095b42f97026e7c5826d5f8f3845608404008f95  scripts/stage_semantic_preexec_package.py
b97f31cc17c22abbb7a021c274be73816f649196762f9c6dfcc54a58d8382e8a  tools/materialize_semantic_shared_faces.py
98e3004300226fecd509a46c009585df14021927f20d4e5c82d8ff7a8a8180de  tools/materialize_southbound_kernel.py
1c0d7f1243752fe216ef62eefbc2e3253b8f2503b518fafe11277e4d7721a084  tools/materialize_southbound_lease_refresh.py
4bd0051fad23acd91fc42eb9b6cd2f2dac6e8d9d960fefd391add261a3646499  tools/semantic_provider_deployment_admission.py
f81bdead000bde095ddcd7ab3841edf765513deb8512e20115e0054d08dcff53  tools/semantic_provider_deployment_authentication.py
88b848be497607a71a9fc8def9164119d8bcf74d095d906fd56e6f91b7cb642a  tools/semantic_provider_deployment_consumption.py
87e4eed4485cee0736bb7031827ee773efde6f4fb97d6289c885fc5cf2049592  tools/semantic_provider_deployment_protocol.py
c466172113d1ffe850bf2c69762113b55fbc65d9091c96dca98a74548fddf930  tools/semantic_provider_dns.py
25c6df90d33e39fe83321df6ab9e5c38d4c33bcd290ad57c7a85c03b1bb8ba78  tools/semantic_provider_lease_coordination.py
7a5f2b21c096228a3e4d298674e380f667c3004dd6d8ec19934a2302844c0f93  tools/semantic_provider_lease_nft.py
92736eebeccf344e565186bce94d29c65ffe1d50638d57eae81486e7b26e884d  tools/semantic_provider_lease_owner.py
1ade8d45a7387bd3b22464a34401ab6b4358f76e5c025ac84d80951542eb1fad  tools/semantic_provider_preexec.py
ef0b98c96879933480a26418edc2b971b21a116509ac87cbc39e3b2062e7a528  tools/semantic_provider_preexec_native.py
OUF_AUTH_SHA
while read -r OUF_AUTH_HASH OUF_AUTH_FILE; do
  mkdir -p -- "$OUF_AUTH_PKG_TMP/$(dirname -- "$OUF_AUTH_FILE")"
  curl --fail --silent --show-error --proto '=https' --max-time 30 \
    "https://raw.githubusercontent.com/GioNob/ouf-api-gateway/6697029e3efa03f9090bd7be13aab86784749731/$OUF_AUTH_FILE" \
    -o "$OUF_AUTH_PKG_TMP/$OUF_AUTH_FILE"
done < "$OUF_AUTH_PKG_TMP/sources.sha256"
(cd "$OUF_AUTH_PKG_TMP"; sha256sum -c sources.sha256)
OUF_AUTH_PKG_ROOT="/etc/ouf/deploy-snapshots/semantic-authenticated-deployment-package-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_AUTH_PKG_ROOT"
sudo install -d -m 0700 -o root -g root "$OUF_AUTH_PKG_ROOT/source/scripts" "$OUF_AUTH_PKG_ROOT/source/tools"
while read -r OUF_AUTH_HASH OUF_AUTH_FILE; do
  sudo install -m 0600 -o root -g root "$OUF_AUTH_PKG_TMP/$OUF_AUTH_FILE" "$OUF_AUTH_PKG_ROOT/source/$OUF_AUTH_FILE"
done < "$OUF_AUTH_PKG_TMP/sources.sha256"
printf 'SEMANTIC_AUTHENTICATED_DEPLOYMENT_PACKAGE_ROOT=%s\n' "$OUF_AUTH_PKG_ROOT"
for OUF_AUTH_MODE in plan apply verify; do
  sudo /usr/bin/python3 -I -B "$OUF_AUTH_PKG_ROOT/source/scripts/stage_semantic_authenticated_deployment_package.py" \
    --mode "$OUF_AUTH_MODE" --package-root "$OUF_AUTH_PKG_ROOT" \
    --source-commit 6697029e3efa03f9090bd7be13aab86784749731 \
    --hook-source-sha256 a4ca047fc76dda6378e81834cac421d5d829b55d63ac62dde29a3178245aaabc
done
```

## 28. Package runtime autenticato v6 — ESEGUITO/PASS

Comando operativo versionato: [OUF_STAGE_AUTHENTICATED_RUNTIME_PACKAGE_V6_2026-10-04.sh](commands/OUF_STAGE_AUTHENTICATED_RUNTIME_PACKAGE_V6_2026-10-04.sh). Source Gateway `f1996cca60e66f1807b88f126793a8edc1aed15f`, 22 hash esatti; script SHA256 `92b746dc33db98da5580ea64d8994887a9c9ba1c85ca67569155ef9dddae1e05`. Crea un nuovo snapshot privato e una receipt source-only. Non aggiorna il package v5 già eseguito. Plan/apply/verify non installano configurazioni o producer, non eseguono i body dei nuovi moduli e non autorizzano start. Output operatore ricevuto: plan/apply/verify PASS, root `/etc/ouf/deploy-snapshots/semantic-authenticated-runtime-package-20261004-094455`; ricevuta conservata. Non ripetere.


## 30. Intervento VPS eseguito — package v8 BLOCKED in plan

**ESEGUITO/BLOCKED**, root121542, PRIVATE_PACKAGE_DIRECTORY_REQUIRED; apply/verify non raggiunti. Il [wrapper originario](commands/OUF_STAGE_LOCAL_PRODUCERS_PACKAGE_V8_2026-10-04.sh) è deprecato e non va ripetuto. Per continuare usare soltanto §31 dopo i controlli descritti. Nessun replay del v7. Entrambi i producer restano non installati/invocati; authority e start non vengono conferiti. Nessun nuovo login Keycloak. Prima di qualunque configurazione operativa, servono authority e accettazione target esplicite.


## 31. Primo intervento VPS pendente — recovery directory del package v8

**NON ESEGUITO.** Eseguire una volta il [wrapper recovery pinned](commands/OUF_RECOVER_LOCAL_PRODUCERS_PACKAGE_V8_DIRECTORY_2026-10-04.sh) sul root121542 e riportare l’output. Nessuna cancellazione di receipt, chmod ricorsivo o sostituzione del package. Receipt presente/metadati diversi bloccano; source0755 può diventare0700 soltanto dopo hash e owner verificati. Completa il primo apply/verify mai raggiunto di §30, senza start, chiavi o runtime registration. §29 non va ripetuto.

## 32. Primo intervento VPS pendente — dossier target e piano authority inerte

**NON ESEGUITO.** Eseguire soltanto il wrapper completo [OUF_INVENTORY_TARGET_ACCEPTANCE_2026-10-04.sh](commands/OUF_INVENTORY_TARGET_ACCEPTANCE_2026-10-04.sh). Hash e input sono nel checkpoint corrente. Riportare stdout sintetico; non incollare target-dossier.json, comandi, percorsi mount o chiavi. PASS è inventario, non accettazione né authority. Nessun apply/staging/recovery precedente va ripetuto.
