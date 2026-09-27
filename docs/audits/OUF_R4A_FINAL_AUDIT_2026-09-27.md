# OUF R4a · audit finale metodologico (27 settembre 2026)

Questo rapporto fotografa le evidenze disponibili nella chat e su GitHub; **non**
è una nuova interrogazione del VPS. È parte dell'[handoff
operativo](../handoffs/OUF_HANDOFF_2026-09-27_R4A.md). R-SMOKE e R-INSTALL
rimangono **OPEN**.

## Metodo e fonti

1. Verificato il pacchetto `OUF_Reality_Baseline_Package_v1_7` allegato:
   323 voci SHA-256, 0 errori. Consultati Blueprint L0 v0.3, Cross-Module
   Alignment Matrix v1.7 e i sette PET L1: Authorization 1.5, Gateway 1.5,
   Onboarding/THS 1.6, Semantic 1.3, Ingestion 1.3, UDP 1.3, MCP 1.4.
2. Confrontati l'[handoff iniziale 25/09](https://github.com/GioNob/ouf-semantic-registry/blob/docs/r4a-2026-09-25-handoff/docs/handoffs/OUF_HANDOFF_R4A_2026-09-25_SCOPE_BOOTSTRAP_NEXT.md),
   gli output operatore 26–27/09, il nuovo handoff e i documenti dei sei
   repository. Lo stato cronologico del 25/09 (PolicyBundle :22, nessun asset)
   è superato dai successivi output, ma conserva rollback e razionale.
3. Letti metadata/head/mergeability delle PR R4a, confronto dei branch con
   `main`, manifest delle route/capability, contratti e porzioni eseguibili
   decisive; interrogati i workflow GitHub Actions per gli HEAD osservati.
   CI, repository, VPS e UX restano quattro piani probatori distinti.
4. Nessun token, password, file CSV, URL allegato temporaneo o dump privato
   è stato letto o copiato. Nessun `apply` sul VPS è stato eseguito.

## Registro per modulo

| Modulo | PET e prova esaminata | Stato verificabile | Limite/gate |
| --- | --- | --- | --- |
| Authorization | PET 1.5; manifest capability/scope, grant e output PolicyBundle | Ultimo ref live riferito `ouf-lab-authorization:28`; scope/grant managed-file e Semantic applicati; token SERVICE/HUMAN acceptance PASS | Nessuna lettura live dopo l'output; R-INSTALL non chiuso |
| Gateway | PET 1.5 T25/T28 e T11.3; route upload HUMAN/MCP e probe APISIX | Probe **isolato** early-byte/204/cleanup PASS; picker HUMAN ha prodotto l'asset via Gateway; route Semantic installate secondo output | Mancano timing/413/no asset parziale della route prodotto, media/checksum/auth negativi, rollback esercitato e TLS verificato cross-network; issue #52 |
| Onboarding/THS | PET 1.6 tabella capability managed-file, ONB-33/34; codice validator/picker e rollout | Asset `8ec8ae90-808a-4d9e-907c-d56de119e376`, profilo `4462692b-9c85-446b-b6fd-779f01eab64d`; DRAFT `managed-cinema-8ec8ae90` non ACTIVE | Il validator allora-live disse PASS con `UDP_RESOLUTION_CONFIGURED=false`; correzione in branch non attestata live; formati oltre CSV non provati sul picker |
| Semantic | PET 1.3 e review HUMAN; RDF/proposta/hash | Revisione `51706bed-81e4-4306-aca1-70119821727d` pubblicata nel set `f92a2e17-30c9-456f-bb12-63afa84f41e6`; zero-set precedente è storico | Nessuna approval/activation della Source Onboarding dedotta dalla sola pubblicazione |
| Ingestion | PET 1.3: bundle storico pin, CDE, handoff e watermark | PR R2f #27 open, 7 workflow osservati SUCCESS; nessuna branch R4a | Nessuna run di **questo asset** attestata; nessun ACK/watermark/materializzazione deducibile |
| UDP | PET 1.3 §4.1, §24–25; PR #34 e issue #35 | PR #34 open, CI osservata SUCCESS, review per record e `UDP_WEIGHTED_RUNTIME_UNAVAILABLE` nel branch | PR non distribuita; motore class-neutral non implementato; nessun oggetto cinema servito |
| MCP | PET 1.4 §34 (channel-neutral), §21 file, THS boundary; PR #45/#46 e picker widget | Picker tool e status/handoff nel branch; test simulato MCP Apps/ChatGPT; upload via picker riferito dall'operatore | PR #46 draft con conflitto; adapter `hostfiles` diretto resta PET-blocked; nessun secondo host live |

## Errori e correzioni della revisione

| Priorità | Difformità | Correzione | Prova residua |
| --- | --- | --- | --- |
| Alta | Il widget MCP aveva `api.ouf-lab.it` fisso in JavaScript nonostante `MCP_MANAGED_FILE_PICKER_URL` configurabile | In PR #46 prefix iniettato dal picker URL già validato dal server; test Node su origine lab e altro Ente | CI sul nuovo HEAD; secondo host MCP reale |
| Alta | PR #45/#46 e vecchi documenti proponevano fetch diretto di URL allegato o parlavano di route non distribuite | PR e documento #46 marcati storici/PET-blocked; picker Gateway come percorso attuale | Escludere adapter storico dal candidato merge/deploy, risolvere conflitto PR #46 |
| Alta | Inventario Semantic diceva ancora `published_sets=0` come se fosse attuale | Cronologia riscritta con pubblicazione HUMAN, hash e set; DRAFT inattivo distinto | Nessuna run Ingestion/UDP attestata |
| Media | Manuale picker chiedeva copia dell'Asset ID, negava chat handoff e mostrava un 403 precedente come corrente | I comandi pin restano documentati come storici; registrato asset/profile successivo e limite UX | Chat handoff live su secondo client |
| Media | PR #33 chiusa diceva che solo concept ID controllati sono confrontabili, in tensione con proprietà schema.org a testo libero | Body chiarito: proprietà governate e valori liberi sono cose diverse; comparazione come evidenza, mai prova automatica senza policy | Contratto generale issue #35 |
| Media | Lo script read-only di inventario Docker confondeva errore daemon con container assente e poteva attendere indefinitamente | Elenco container prima di inspect, fail closed e timeout; test locale missing/failure/no secret/timeout | Prova reale su VPS solo se necessaria a prossimo rollout |
| Media | PR #37/#51/#54/#26 e issue #43/#52 mantenevano descrizioni pre-rollout come stato corrente | Annotate con cronologia supersedente, senza dichiarare R-SMOKE PASS o merge | Verificare HEAD/CI dopo ogni nuova modifica |

## Regola d'identità approvata e distinzione semantica

Il PET UDP distingue source-object binding, canonical Urban Object e
materializzazione. Blocking indicizzato e limitato recupera candidati e non
decide MATCH; overflow produce review/`RESOLUTION_TOO_BROAD`. Le proprietà
sono confrontabili solo quando i mapping IRI/versione e i normalizzatori
tipizzati governati sono compatibili. Il CSV cinema ha proprietà allineate
a schema.org, ma **non** concept ID controllati per i valori testuali. Il
mapping non autorizza identità: un'uguaglianza di nome o indirizzo può essere
evidenza da spiegare, mai MATCH per sé.

La policy pubblicata deve dichiarare vincoli giustificati (unicità/scope,
cardinalità, temporalità, geometria, authority), condizioni sufficienti e
competitori da escludere. Frequenza/selectivity aiuta retrieval e review,
non conferisce autorità per soglia. Auto NEW richiede policy esplicita;
ambiguità e conflitti richiedono HUMAN review durevole. Una conferma unisce
contributi non conflittuali e conserva lineage, authority per proprietà e
history. Gli esempi «semaforo», «cinema», indirizzi e controller condivisi
sono fixture del motore generale, non rami di produzione.

L'ACK UDP è emesso solo dopo persistenza durevole dell'input/recovery metadata;
non attende object resolution. Una review su un record non invalida l'ACK,
non riporta indietro il watermark e non blocca gli altri job. PR #34 copre
quarantena e resume, non la policy generale. Un `resolution.weighted`
validato da Onboarding non deve essere attivato finché UDP non lo esegue.

## Stato PR e dipendenze

- Gateway PR #51, #53, #54: open/draft; i rispettivi branch hanno contenuto
  diverso dal loro deployment storico. Il branch #51 non include ancora
  le correzioni dell'installer #53 (blob diversi per deployer M2M/MCP);
  #53 risultava anche non mergeable con la base al controllo; #54 deriva
  da un ulteriore branch picker/owner-key. Queste dipendenze
  vanno integrate e ricollaudate insieme prima di promuovere `main`.
  Non inferire merge da route installate.
- Onboarding PR #37: open/draft; Semantic PR #26: open/draft; Semantic docs
  PR #25 e workload PR #24 restano separate. #25 modifica gli stessi
  roadmap/manuale di #26 e il vecchio handoff è storico; il provisioner
  Keycloak di #24 è già presente con blob identico in #26. Evitare merge
  indipendenti che sovrascrivano la documentazione corrente o duplicano
  il bootstrap.
- Ingestion PR #27 R2f: open/draft; nessuna PR R4a per questo asset.
- UDP PR #34: open/ready for review, non deployed; issue #35 aperta;
  PR #33 chiusa senza merge. UDP PR #31 search open/draft e PR #32 già
  mergiata nella branch R4a, non necessariamente in `main`.
- MCP PR #45 e #46: open/draft; #46 attualmente non mergeable con la sua
  base. Il codice del picker è nel branch #46; il contratto precedente #45
  non sostituisce l'integrazione del branch #46.

Gli HEAD osservati prima degli ultimi cambi avevano workflow SUCCESS:
Gateway #51 (1), Onboarding #37 (2), Semantic #26 (4), Ingestion #27 (7),
UDP #34 (3), MCP #45/#46 (2 ciascuna). Dopo la correzione del widget,
il commit MCP #46 `ab553578095c5236b62612160f4fd8fdd77da2f8`
non aveva run PR restituiti dal connettore; la sua CI finale è **non
attestata**. Su Semantic il commit `b46bb276409c102b5fc0609ef56c614cd2e856d3`
aveva due workflow SUCCESS, uno in progress e uno pending. Su
Onboarding `5d770df635f8328a1e901b2d47bf8cd5bacab6c5`
entrambi i workflow erano SUCCESS. Ricontrollare la CI su ogni nuovo
HEAD; un esito verde non è prova live.

## Gate di uscita

1. Implementare issue UDP #35 come motore generale, allineare contratto
   Onboarding/UDP e verificarlo su dataset multi-classe senza eccezioni.
   Rieseguire lo **stesso** motore sulle osservazioni prima di schedulare
   la fonte; misurare candidate overflow e review volume.
2. Approve/activate il DRAFT cinema via THS solo con execution, Semantic
   refs e UDP policy/materialization profile realmente compatibili.
3. Eseguire Ingestion sull'asset esistente, osservare RAW/handoff/ACK,
   materializzazione/lineage UDP e search via Gateway, MCP e altro client
   autorizzato. Provare almeno tre oggetti reali, due pagine/cursor,
   minimizzazione, partial, invalid cursor e audit, come nell'handoff 25/09.
4. Eseguire sulla route upload di prodotto i negativi 413/415, hash,
   anonimo, idempotenza, asset parziale, early bytes e rollback. Il probe
   APISIX isolato resta solo un prerequisito.
5. R-INSTALL: orchestrator da manifest, secret refs, bootstrap IAM/route e
   moduli, clean install, upgrade, backup/restore, rollback e CI. Il lab
   Docker singola rete non attesta TLS su reti separate né produzione.

Non ripetere upload o pubblicazione già attestati per riempire un report.
Conservare asset, snapshot, container rollback e dump secondo retention
governata. Un controllo live nuovo va scelto per risolvere un rischio preciso,
con output minimo e senza segreti.
