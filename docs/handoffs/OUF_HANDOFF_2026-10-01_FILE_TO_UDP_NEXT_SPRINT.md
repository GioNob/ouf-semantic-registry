# OUF — handoff per nuova chat: prossimo sprint file → UDP
Data checkpoint: 2026-10-01, 20:24 Europe/Rome.

## Ripartenza e vincoli dell'utente

**Obiettivo del prossimo sprint:** completare un percorso generale guidato dal chatbot, dal caricamento di un file alla registrazione/materializzazione UDP, usando lo stesso CSV Teatri già caricato. Riusare i passi corretti e verificati; non ripartire da zero né far ripetere ore di prove manuali.

PET obbligatori a ogni sprint. Se qualcosa è ambiguo o non trattato, esplicitare il punto e decidere con l'utente prima di implementare quella scelta. Nessuna regola di dominio dedotta soltanto dalla fixture Cinema o Teatri. Tutto deve restare parametrizzato per Enti, tenant, domini, host, reti e moduli differenti. Handoff, roadmap e documentazione install/config/deploy vanno mantenuti aggiornati. Fine ultimo: sistema robusto, quarantene appropriate, risoluzione governata THS e deploy industrializzato.

**Il chatbot fa il mapping assistito:** analizza, consulta semantica, compara candidati, propone corrispondenze/trasformazioni e spiega i dubbi. Non chiedere all'utente IRI manuali. Onboarding valida/persiste il mapping specifico della fonte; Semantic governa artefatti/versioni; owner e THS governano decisioni autoritative. Nessun agente AI interno ad Onboarding. Le approvazioni, adozioni/pubblicazioni semantiche e merge autoritativi previsti HUMAN non diventano tools/call di conferma MCP.

Non chiedere nuova autorizzazione per analisi, codice/test/documentazione necessari al piano già concordato. Quando una fase necessita realmente di login/decisione HUMAN o di esecuzione SSH, preparare prima un risultato concreto, pinned e verificato. In questa chat non c'è accesso SSH diretto: l'operatore ha eseguito blocchi pinned via shell. Dopo la nuova chat verificare le capacità effettivamente disponibili, senza presumere accessi.

## Risultati provati di questa chat

### Fixture precedente Cinema: delivery e materializzazione 8/8 PASS

Source `managed-cinema-8ec8ae90`; run `86809c17-3354-45ca-a7e6-57e903944b24` SUCCEEDED. Source ACTIVE, frozen hash/publication corrispondenti; schedule trigger_once consumata/DISABLED. Otto handoff ACKED, otto lineage, zero quarantene Ingestion.

UDP: otto intake PROCESSED, otto job SUCCEEDED, otto NEW_OBJECT e otto observations/revisions/bindings/active objects; zero failure code/issue di risoluzione aperta. Tutti gli otto handoff hanno HANDOFF_DURABLE, REFERENCE_INTEGRITY_PASSED e RESOLUTION_COMPLETED. Set handoff ING/UDP corrispondenti. Non eseguire ulteriori retry/replay/intake o riattivare questa fixture.

Recupero governato: tre originali erano QUARANTINED. Policy nominale e route owner/SDK sono state corrette e provate; tre retry HUMAN hanno recuperato due job. Il restante è stato poi riesaminato a v5 e ritentato da HUMAN a READY v6; ora SUCCEEDED/PROCESSED v8, attempts=3, integrityAttempts=2, baseline presente, failure nullo. Audit storico delle quarantene e delle autorizzazioni conservato.

Si è scoperto `ouf-udp-r4a-smoke` ancora RUNNING con vecchio JAR senza diagnostica, execution.enabled=true e binding DB dichiarati uguali al main. Arrestato con guard, idle verification e shutdown controllato; conservato e restart=no. Main invariato/sano, originali invariati durante stop. Autore storico dell'evento senza diagnostica NON provato. Regola generale: compatibilità di tutti i worker/consumer/schema, non “un solo worker” né divieto indiscriminato N/N+1.

Ricevute private lato server:
- readback finale: `/etc/ouf/deploy-snapshots/udp-materialization-recovery-policy/readback-after-retry.sUa4nQ`, exit readback=0/diagnostica=0;
- isolamento: `legacy-worker-stop-asbhqris/receipt.json` nello stesso parent, PASS;
- retry singolo: `human-retry-remaining-20261001T172023-3532794.json` e relativo `-fresh-review.json`;
- protocollo retry: `human-retry-protocol.edu1pk`.

Search/serving della fixture Cinema NON verificato; letture cross-DB non atomiche; verifica indipendente byte/hash storage e R-INSTALL aperti. Tredici marker recenti ING_ACTIVATION_DISCOVERY_UNAVAILABLE restano da correlare/diagnosticare, senza dichiarare fallito il run riuscito.

### Nuovo CSV Teatri: upload/profile reali via MCP PASS

Account utilizzato: **ouf-admin** (subject `b93d8cf6-cd14-4ee6-91d7-84cd76c4f500`). Non confondere con SSH oufadmin o Keycloak master admin. Nella nuova chat selezionare l'account dalle indicazioni correnti del connector, non ricostruire link_id.

- Picker handoff: `b6de7b63-4a1a-47d8-858e-3cc5f0adad51`.
- Asset: `6609b245-86ed-4315-8ce0-73f2a8555bf3`.
- Profile job: `2f49ea03-b715-493b-ba25-a3f82007cd3d`, SUCCEEDED.
- Profile/resultRef: `7984c39c-7396-4248-ab0a-f2efc390b49c`, versione 1.
- CSV UTF-8, separatore `;`, header row 1, 13 righe e 20 colonne, ONE_ROW_ONE_SOURCE_OBJECT; proposta PENDING_HUMAN_REVIEW.

Campi: nome_teatro, tipologia, toponimo, nome_indirizzo, civico, cap, citta, provincia, latitudine, longitudine, sistema_riferimento, precisione_coordinate, capienza_posti, spettacoli_stagione, stagione_riferimento, note, fonte_indirizzo, fonte_coordinate, fonte_altri_dati, data_verifica.

Preview ricevuta già redatta dall'owner; non copiare sample/raw nei documenti. Coordinate e diversi dati sono nullable. CAP inferito LONG: non confondere inferenza col tipo semantico, valutare preservazione di codici/zeri iniziali. Candidate keys osservate: nome_teatro/nome_indirizzo/fonte_indirizzo. Proposal NATIVE_KEY nome_teatro: identità stabile solo mentre il nome resta stabile; unicità in 13 righe non è prova di chiave durevole. Chiave e classificazioni non approvate.

Un tentativo upload.status ha restituito errore host `tool selection stalled`, retryable=false; successiva profilazione e preview owner hanno confermato l'asset. Non è una quarantena OUF provata. Nessuna DRAFT, ACTIVE, nuova run o materiale UDP Teatri creati.

## Baseline tecnica da preservare

| Componente | Pin/evidenza |
|---|---|
| Repo di coordinamento | `GioNob/ouf-semantic-registry`, branch `codex/r4a-smoke-semantic-inventory`; aggiornamenti di questa chat sul branch, non merge automatico in main. |
| UDP live | Repo `GioNob/ouf-udp-object-resolution`, branch `codex/r4a-materialization-recovery`, revision `83249a897eb4add4289b5181b3299f48ea4c0f99`, image `sha256:5e048a859716d6674355e72238f03f899abd705a943ceadbdc5c8863d28f4e9f`, Flyway 34. |
| Helper recovery | Pin `9ff81375422399bd1a259414dbe9932cb8fdcd1a`: select-job, review fresca/v5 distinta dalla prior/v2, intent prima POST, niente repost ambiguo, logger unbuffered; CI sette workflow SUCCESS, 113 test recovery. |
| Policy recovery lab | `ouf-lab-authorization:36`, tre grant HUMAN nominali/esatti/source-run/data label; expiry 2026-10-02T10:00:00Z. Non assumere validità dopo scadenza e non ampliarla per il nuovo CSV. |
| Documentazione dettagliata | [Handoff storico](OUF_HANDOFF_2026-09-30_R4A_INGESTION_COMPATIBILITY.md), [roadmap](../OUF_ROADMAP_PET_1_7.md), [installazione](../installation/OUF_INSTALLATION_MANUAL.md), [runbook recovery](../installation/R4A_UDP_RECOVERY_CANDIDATE.md). |

Preservare fix ammissione owner scoped, access label RAW, identity/service-principal, intake routes, reference-integrity e recovery. I branch/base/main non sono automaticamente equivalenti al codice live corretto: verificare diff/pin prima del lavoro o rollout. Ricevute private restano sul server; non importare segreti, token, env o log integrali nella chat/GitHub.

## Prossimo sprint concordato: percorso completo guidato dal chatbot

### Sequenza PET

File/staging → profiling → chatbot ricerca semantica interna → eventuale discovery esterna e adozione governata → proposta mapping/identità/classificazioni e DRAFT Onboarding → review/approvazione THS → bundle ACTIVE → Ingestion/RAW/handoff → UDP Object Resolution → materializzazione → verifica serving autorizzato.

Il matching autoritativo è UDP dopo l'handoff; un preflight non lo sostituisce. MATCH deterministico non equivale sempre a merge canonico. REVIEW_REQUIRED/merge autoritativo seguono owner/THS e audit.

### Deliverable, nell'ordine

1. **Inventario dei passi già corretti:** matrice contratto/API, owner, revision/immagine, receipt/test e collegamento MCP/THS. Riusare il lavoro precedente; distinguere prova backend manuale da prova del nuovo collegamento.
2. **Semantic consultabile dal chatbot:** capability MCP tipizzate/bounded e route/policy/SDK owner per ricerca, lettura, riferimenti pinned; discovery/proposte quando necessarie. Nel sorgente Semantic esistono già ArtifactApi search/read/propose, ValidationApi references:resolve/validation/impact, DiscoveryApi requests/candidates/adoption DRAFT/providers e GovernanceApi approval-challenge. Verificare deployment/binding prima di implementare doppioni.
3. **Mapping assistito completo del Teatri già caricato:** classe/proprietà/dizionari, trasformazioni whitelist, chiave stabile, INCLUDE/EXCLUDE e access label, CRS/temporal/authority/representation richiesti dai contratti. Chatbot propone e motiva; Onboarding valida/persiste riferimenti ACTIVE/versionati. Presentare dubbi all'utente, non inventare IRI o riciclare Cinema.
4. **THS e ripresa:** preparare challenge/link fiduciario, leggere esito e riprendere idempotentemente da stato owner persistito; semantica/source hanno decisioni proprie. Nessun token privilegiato HUMAN o comando di conferma tramite MCP.
5. **Activation → ingestion → UDP e recovery:** usare trigger governato previsto e servizi corretti; monitorare source/run/handoff/job; presentare quarantene/ResolutionIssue e azioni THS. Timeout/esito sconosciuto richiede readback/riconciliazione, non nuova run/replay automatico.
6. **Collaudo end-to-end e deploy:** stesso nuovo CSV fino a durabilità, job/materializzazione, linkage e Search autorizzato; catalogo/scopes/policy/routes/provider/config installabili e riconciliabili automaticamente per deployment parametrizzati.

Catalogo MCP osservato in questa chat: upload/status/profile/preview/onboarding.create, operations/authorization e object search; **Semantic e diversi passaggi lifecycle/risoluzione non esposti**. Questo non prova assenza backend e non impone un tool separato come unica soluzione. Il gap è il collegamento governato necessario al chatbot e alla continuità del percorso.

Ontopia/SPARQL: l'utente desidera discovery esterna; PET prescrive provider adapter autorizzati, configurabili e on demand solo senza match interno adeguato. DiscoveryApi corrente mostra status schemaGov; adapter/endpoint Ontopia effettivi non verificati. Nessuna query SPARQL arbitraria dal chatbot. Candidato esterno effimero non è un riferimento OUF ufficiale finché non adottato. Le scelte mancanti nei PET vanno discusse.

### Verifiche e criterio di chiusura

Non ripetere tutte le prove manuali già superate. Eseguire regressioni automatiche già disponibili e prove nuove sui collegamenti modificati. Riaprire un gate precedente solo se toccato da cambiamento/rollout o se emerge drift/incompatibilità.

Lo sprint si chiude quando il chatbot può condurre **il nuovo file** attraverso ricerca/proposta, decisioni THS, pubblicazione/ingestion e risultato UDP verificato, usando solo canali governati, senza SSH ordinario o IRI forniti manualmente. Verificare anche pause/ripresa, denial di scope/tenant, snapshot/versioni stale, transient vs integrity e assenza duplicazioni da retry. Nessuna nuova norma scelta senza PET o decisione utente.


## Registro esplicito dei gate ereditati — verifica 2026-10-01 20:33 Europe/Rome

**Il prossimo sprint non sostituisce il backlog precedente. Nessuna questione si chiude perché omessa da questa sintesi.** Verificati in questa ripresa: [handoff iniziale del 29/09](OUF_HANDOFF_2026-09-29_R4A_PREFLIGHT_TO_INGESTION.md), [handoff del 30/09 e cronologia di questa chat](OUF_HANDOFF_2026-09-30_R4A_INGESTION_COMPATIBILITY.md), [handoff 27/09](OUF_HANDOFF_2026-09-27_R4A.md), [audit 27/09](../audits/OUF_R4A_FINAL_AUDIT_2026-09-27.md), [handoff 25/09](https://github.com/GioNob/ouf-semantic-registry/blob/docs/r4a-2026-09-25-handoff/docs/handoffs/OUF_HANDOFF_R4A_2026-09-25_SCOPE_BOOTSTRAP_NEXT.md) e roadmap corrente. Gli stati live vecchi sono storici; vincoli e gate aperti restano validi salvo nuova prova esplicita.

| Gate ereditato | Stato dopo questa chat / prova mancante |
|---|---|
| Approval/activation e compatibilità della fixture Cinema; primo run/handoff/materializzazione | Superati per la fixture già pubblicata; run e otto handoff/materializzazioni PASS nella ricevuta finale. Non ripetere approval/activation/recovery. Questo non certifica una nuova source o un rollout diverso. |
| **R-SMOKE completo** | **OPEN**: 8/8 è una parte, non tutto il gate. Search via Gateway/MCP con almeno tre oggetti, un oggetto/proprietà da minimizzare, due pagine, cursor/invalid cursor/partial, label/authority enforcement e audit da verificare. |
| Seconda fonte sovrapposta e matching/review reali | **OPEN**: source diversa ma classe/candidati sovrapposti; subset nelle due direzioni, campi concordi/diversi, conflitti/missing, autorità, forme disgiunte, ampiezza bounded senza m×n, overflow/coverage, backfill e pacchetto THS atomico/resume. Il nuovo Teatri non prova da solo questo gate, né è automaticamente il file sovrapposto menzionato nel vecchio handoff. |
| Gateway/upload di prodotto | **OPEN per acceptance residua**: streaming/primi byte prima del completamento client, oversized 413 senza asset parziale, 415/media-type, digest mismatch, anonimo, limiti/idempotenza/rollback. Upload/profile reali PASS non sostituiscono tutte le prove negative e il trasporto streaming end-to-end. |
| MCP/UX e channel neutrality | Questo host: upload/picker, callback con Asset ID e profile/preview PASS. **OPEN** secondo host/client MCP compatibile senza copia manuale Asset ID, limiti host/adattatori e continuità login; bridge hostfiles diretto non è un fallback autorizzato. |
| Semantic exact refs e contratti storici | Prove puntuali della fixture conservate. **OPEN per integrazione/generalità**: chatbot search/read/pinned references, discovery/adozione governata, bundle/provenance/consumer compatibility e contratto DTO/schema non vanno dichiarati tutti conformi da un GET o validator PASS. |
| Data Lake: verifica indipendente | **OPEN** byte/hash/S3 e riconciliazione DB-object store; persistenza/ACK/materializzazione non equivalgono a lettura indipendente dei byte. Backup di oggetti e restore storage da provare nel perimetro previsto. |
| Replay RAW originario / SPI | **OPEN** esecutore/trasporto e prova di sorgente RAW durevole. UDP REPRODUCE genera un nuovo handoff/job: non sostituisce il retry dell'originale né prova il replay source Ingestion. Non inferire durabilità dal solo payload_ref. |
| Policy Lake per source/type/zone | **OPEN** retention/access e enforcement per ambito, senza default lab trasformati in regola generale. Il profilo esplicito già adottato non prova policy dinamiche né cancellazione effettiva degli oggetti esistenti. |
| Portabilità e **R-INSTALL** | **OPEN** manifest/secret refs, bootstrap idempotente IAM/Authorization/routes, installazione automatica dei moduli, clean install, upgrade N/N+1, rollback/restore/PITR/reconciliation e CI d'installabilità su macchine/reti/domain/Enti diversi. Preservare backup/snapshot/container, nessun restore o cleanup indiscriminato. |
| Reti separate e trust TLS | **OPEN** verifica comportamentale del trust upstream/trasporto remoto; semplice scheme=https non è attestazione di verifica certificati. Conservare i vincoli già tracciati su Gateway/runtime/streaming. |
| Capacity/concurrency/performance | **OPEN** profili rappresentativi, lease race/rollout compatibile/governor multi-replica e SLO; non usare fixture vuote come acceptance. |
| Operational awareness / collectors | **OPEN** raccolta/proiezioni/gate e alert cross-owner. Tredici marker discovery unavailable da correlare; log mancanti non equivalgono a healthy. |
| Latenza ChatGPT–MCP | **OPEN** misure e correlazione dei tempi host/tool/Gateway/owner; evitare attribuzioni speculative dal solo tempo percepito. |
| Cross-module release / PR / branch reconciliation | **OPEN** riconciliare branch reali corretti e main/stale base, pin/SBOM/checksum/security/cross-module acceptance. Successo CI, presenza sorgente, deploy e risultato live sono evidenze distinte; base-image tag non digest-pinned non prova build bit-for-bit. |
| Causalità storica degli errori 403/reference | Non provata integralmente dalla risoluzione corrente. Conservare eventi/receipt; nessuna nuova mutazione necessaria soltanto per ottenere una spiegazione. |

### Regola d'identità già concordata: non regredire

L'handoff 29/09 §4 contiene la scelta utente, successiva alla discussione weighted del 27/09. **Identità tecnica della riga sorgente distinta dall'identità canonica UDP.** Coordinate/indirizzi/nomi non sono automaticamente chiavi canoniche stabili.

La policy pubblicata governa proprietà/comparatori/candidati: subset sufficiente concorde anche nelle due direzioni può dare MATCH se le premesse e l'unicità sono soddisfatte; campi comuni confrontabili tutti diversi indicano distinto; concordanze parziali/conflitti/assenza di confrontabilità restano incerti. NEW richiede policy allowAutoNew e coverage completa; overflow è REVIEW_REQUIRED/RESOLUTION_TOO_BROAD. Score/frequenza/selettività non conferiscono autorità identificante da soli. Il motore class-neutral è implementato nel branch corretto: non rifarlo né ripristinare weighted legacy perché un documento storico lo descriveva come ancora mancante.

Il chatbot mostra evidenze/proposte, l'utente accetta/modifica e conferma il pacchetto nel THS. Review non trattiene durable ACK/watermark; nessuna transazione DB aperta in attesa umana. Binding/riaccodamento e lineage/audit restano governati e append-only. Per il nuovo CSV non scegliere nome_teatro come identità canonica soltanto perché unico nel campione.

### Come usare questo registro nel prossimo sprint

Portare tutti i gate nella matrice evidenze; associare ogni chiusura a prova/versione/ambito specifici. Integrare il percorso file → UDP con questi vincoli, senza trasformare ogni gate ereditato in una nuova prova manuale preventiva. Riusare test/receipt; chiedere intervento soltanto dove effettivamente necessario. I gate fuori dal perimetro dello sprint restano OPEN e tracciati, non cancellati.

## Letture obbligatorie per la nuova chat

Baseline PET v1.7 fornita dall'utente: Source Onboarding v1.6 §§92–92.2 e THS; Semantic Registry v1.3 §§9.2,10–11,17–18; UDP v1.3 §§21–22,109.2,109.6–109.9; Authorization v1.5 §36.10; MCP v1.4 e Gateway v1.5 per projection/delegation/channel boundary.

Nella sessione precedente i PET erano estratti dal pacchetto `OUF_Reality_Baseline_Package_v1_7(20261001-060705).zip`. Se non disponibili nella nuova chat/workspace o nei riferimenti autorizzati, richiedere il pacchetto necessario: questa sintesi non sostituisce la fonte normativa. Non accedere a Library di altre chat.

**Prima azione concreta:** leggere PET e baseline, verificare catalogo/contratti correnti e collegare la consultazione semantica governata per proporre il mapping dello stesso asset/profile. Non ri-uploadare, ri-profilare, riattivare Cinema o rilanciare recovery senza una necessità verificata.

## Ripresa della nuova chat — 2026-10-01 20:54 Europe/Rome

PET ricevuti: `OUF_Reality_Baseline_Package_v1_7(20261001-185201).zip`; archivio SHA256 `e63df67e8817eec38a9d4b3eb736b020f693b932f3360dc02f4555330f2201ce`. 323 checksum interni verificati, zero mismatch. Consultati L0 Matrix v1.7 e i PET pertinenti indicati sopra. Autorizzazione utente alla lettura/scrittura dei repository OUF per la durata della chat riconfermata; mantenere parametrizzazione e handoff/deploy aggiornati.

Primo deliverable: [inventario PET/contratti/evidenze e gap del collegamento](../audits/OUF_FILE_TO_UDP_INITIAL_INVENTORY_2026-10-01.md), commit documento `6258cfc751ef13ece85696c080a1ab653581e250`. GitHub read/write riusciti. Nessun nuovo rollout, upload/profile, DRAFT/approval/run/retry eseguito; stati live precedenti rimangono evidenze ereditate.

Verifica sorgente Semantic al checkpoint be76527e: search esiste ma usa soltanto similarity di semantic_id; risultato senza label/definition/publication set. get artefatto sceglie l'ultima revisione; references:resolve invece verifica membership exact e ritorna label/metadata, senza definition/domain/range. Prima della proiezione MCP completare/verificare la lettura sufficiente al mapping e la scoperta del riferimento pinned; non equiparare presenza endpoint alla conformità PET §10.

Catalogo di questa chat ancora privo di semantic.search/get. Manifest MCP main, attachment e object-search esaminati mostrano superfici differenti: nessuno dei singoli manifest esaminati riproduce da solo upload+search disponibili qui. Riconciliare loader/overlay/receipt e pin effettivo prima di scegliere la base, preservando managed-file, owner auth e search già corretti. Gateway main dichiara ouf.semantic.read ACTIVE/toolEligible=false: configurazione sorgente, non readback live.

Prossimo passo: verificare contratti di lettura semantica completa e baseline MCP, implementare collegamento governato con deploy parametrico, poi proporre il mapping dello stesso asset/profile Teatri. Nessun IRI inventato/manuale, nessun AI interno a Onboarding e nessuna conferma HUMAN MCP. Tutti i gate della tabella ereditata restano tracciati, con stati invariati.

## Sprint acquisizione comune — decisione 2026-10-02

L'utente conferma l'obiettivo completo MCP/channel-neutral e distingue il trigger: file → dopo onboarding approvato/bundle ACTIVE acquisizione automatica una tantum e poi resolution UDP; verticale → THS endpoint/credenziali, THS profilo di estrazione, configurazione scheduler, ingestion automatica alle scadenze pubblicate. Il resto del percorso e le ownership restano comuni. Credenziali esclusivamente THS/secret manager; nessun materiale sensibile nel chatbot.

[Piano concreto e incremento Semantic](../sprints/OUF_ACQUISITION_TO_UDP_2026-10-02.md): branch candidato `codex/file-to-udp-semantic-read` dalla baseline b50f3d88…, ricerca label/alias/definizione con pin della revisione ACTIVE corrente e risoluzione storica exact arricchita. Test nuovi Java/PostgreSQL/HTTP predisposti, esecuzione CI da verificare sul pin risultante. Check locali Python inventory (2 test), registro PET e checksum PASS. Nessun rollout, nuova source/run/approval o materializzazione.

MCP live non ancora riconciliato: prima del suo rilascio richiedere un readback limitato di revision/image/running dei container, senza env/mount/log/segreti. Non scegliere il branch deployed-baseline-8599843 soltanto dal nome: il manifest embedded sorgente non contiene managed upload. Mancano SSH diretto e tool amministrativo di deploy in questa sessione; GitHub write disponibile tramite connector. Tutti i gate ereditati e la prova Cinema rimangono invariati.

Pin sorgente candidato Semantic: `527fe074a7f6fb9c2990aac2fc9a7a98b8e97e4f` (CI da verificare; nessun deploy).

### Verifica candidato Semantic — 2026-10-02

Commit sorgente `527fe074a7f6fb9c2990aac2fc9a7a98b8e97e4f`: job Java21/PostgreSQL17 PASS (nuovi test SemanticReadRuntimeTest inclusi nel verify), recovery-cycle-scripts PASS e i due workflow Authorization pairwise SUCCESS. [CI runtime](https://github.com/GioNob/ouf-semantic-registry/actions/runs/36972327013): container-smoke SUCCESS, workflow completo SUCCESS. Nessun rollout. Lettura live necessaria di running/image/revision dei cinque container MCP/Semantic/Onboarding/Ingestion/UDP prima del deploy MCP: usare docker inspect con template limitato; non esporre env, mount sources, token o log.


## Checkpoint consultazione MCP e baseline live — 2026-10-02

Questo checkpoint aggiorna l'inventario dei paragrafi precedenti. Readback operatore: tutti e cinque i container sono running=true.

| Container | Revisione live | Image digest |
| --- | --- | --- |
| ouf-mcp | 04e871601e393672a1d62759dfdee09e2e66dc6d | sha256:b25c282882a858e8192d69170bc769e3c79f43e04330fc19ccd538b56c41716c |
| ouf-semantic | 12dc4bcad788bfdf96e15af716c8fa39ea0d12ef | sha256:9e7ec63f1a69195bd2e0688de9d491d30fe50024220b7a9f79dd991fc2113a3b |
| ouf-onboarding | 6340d5bf120e09b47c32177656e2c377a4c03640 | sha256:ec6f2a962261a8433bfe103347afa2202837fcec90d210d9b5232711b854ee8a |
| ouf-ingestion | 163c167d09b8371ff7a62ce7068e9d485b6969b7 | sha256:b07a4a786ca48335feae887e18dc7c4c6cdd9bd0a3a255f83d18c7c1616eec48 |
| ouf-udp | 83249a897eb4add4289b5181b3299f48ea4c0f99 | sha256:5e048a859716d6674355e72238f03f899abd705a943ceadbdc5c8863d28f4e9f |

Il sorgente MCP alla revisione live contiene sia managed upload/picker sia Search. Il candidato deriva da questa revisione e preserva le voci precedenti del manifest. Il confronto Semantic con il sorgente live conferma che SDK, pom e migrations non sono modificati dall'incremento.

| Repository / branch candidato | Commit sorgente |
| --- | --- |
| ouf-mcp-server / codex/file-to-udp-semantic-mcp | 8476a689fc6e59055001f59fc79a024bd14aca4a |
| ouf-api-gateway / codex/file-to-udp-semantic-mediation | e8ef4b72093f4138d0efe78e9947ddfc4b471e27 |
| ouf-semantic-registry / codex/file-to-udp-semantic-delegation | 8985d0d7f772dc7a7fd3deb3d5a569b1406d5d6c |

MCP espone semantic.search e semantic.get con input chiusi. Gateway verifica OIDC workload e delega HUMAN/tenant tramite ricevuta purpose/body/path/capability-bound di massimo 30 secondi. Semantic verifica la ricevuta e rivaluta la policy owner corrente con lo stesso SDK/resource type delle letture esistenti. Search consente soltanto ACTIVE; get richiede semanticId/revisionId/publicationSetId exact. Nessuna authority di approvazione, adozione o pubblicazione passa al chatbot.

CI MCP SUCCESS ([conformance](https://github.com/GioNob/ouf-mcp-server/actions/runs/36974180113), [evidence](https://github.com/GioNob/ouf-mcp-server/actions/runs/36974180119)). CI Gateway SUCCESS ([run](https://github.com/GioNob/ouf-api-gateway/actions/runs/36974491284)); suite locale completa 341 PASS / 4 SKIP. Il test cross-repository esegue il Lua Gateway reale e verifica la ricevuta nel Java owner; non equivale alla prova live di APISIX/OIDC/JWKS/TLS. CI Semantic sul pin sopra: tutti e quattro i workflow SUCCESS: [Java/PostgreSQL/container](https://github.com/GioNob/ouf-semantic-registry/actions/runs/36975096810), [Lua Gateway→Java owner](https://github.com/GioNob/ouf-semantic-registry/actions/runs/36975096768), Authorization Semantic e Shared Authorization SDK pairwise.

### Installazione: passo disponibile e limiti concreti

Script read-only scripts/r4a_consultation_runtime_preflight.py e due test PASS: controlla revisioni esatte/stato/privileged di Semantic e MCP e restituisce solo nomi delle variabili, destinazioni dei mount, nomi reti e metadati. Non restituisce valori env, mount host source o comandi container. Usare nomi container e revisioni espliciti; drift blocca senza mutazioni.

Configurazione nuova owner: ouf.semantic.delegation.key-file, ouf.semantic.delegation.workload e binding esistenti ouf.iam.issuer/audience. Chiave dedicata di 64 caratteri hex come bytes ASCII, distinta dalla chiave delegazione; soltanto Gateway e secret-file owner. Assenza chiave nega queste letture; configurazione incompleta/invalida blocca startup. Nessun segreto in MCP o chatbot.

Il materializer Gateway aggiunge soltanto le due route a un runtime già materializzato, con route IDs/upstream/issuer/audience/workload/key env names espliciti. Non è ancora un installer live plan/apply: prima del rollout completare readback scopes/catalog/policy/routes, snapshot privato, riconciliazione parametrica idempotente, key mount e rollback coordinato owner/MCP. Non sostituire l'intero runtime Gateway con una baseline sorgente presunta. Poi verificare discovery tool, letture positive/denial/exact storico e regressione picker/Search esistenti.

Nessun deploy, nuova source, upload, profiling, DRAFT, approvazione, run ingestion, retry UDP o materializzazione è stato eseguito in questo checkpoint. Cinema e Teatri rimangono invariati. Tutti i gate ereditati restano OPEN nei rispettivi ambiti. Il percorso intero non è ancora accettato: dopo la consultazione occorrono mapping/review/activation THS, trigger file una tantum, scheduler verticale, esiti UDP/Search e secondo chatbot. Deduplication autoritativa rimane in UDP.


## Checkpoint operatore e preparazione immagini — 2026-10-02 08:49 Europe/Rome

Preflight live ricevuto PASS: Semantic e MCP alle revisioni attese, entrambi su ouf-backend, senza porte pubblicate o privileged. Semantic user 10001:10001, mount bind read-only /run/ouf-semantic-auth; env IAM/Authorization presenti, nessuna configurazione della ricevuta semantica ancora presente. MCP user 10005:10005, mount read-only dei due secret-file client/fingerprint, managed upload e picker configurati; restart unless-stopped. Nessun healthcheck Docker configurato: il futuro switch richiede readiness applicativa esplicita, non sola verifica Running. Questi fatti non dimostrano la salute delle API o l'accesso autorizzato.

Script nuovo scripts/r4a_stage_semantic_consultation.py: configurazione JSON con stageRoot, due immagini (repository, commit exact, nome container, liveRevision), container/configDestination/adminOrigin Gateway. Nessun binding installazione implicito nello script. Crea una directory nuova privata 0700, legge le route APISIX via Admin loopback nel network namespace Gateway; chiave letta dal bind config, passata via stdin, mai argomento o output. Snapshot completo di inspect/config/routes soltanto in file privato 0600; output solo metadati route/plugin/scopes e nomi env. Checkout detached dei commit exact, build log privato e label OCI controllata; conserva immagini staged, senza creare/avviare candidati. Verifica live config/stato e route invariati alla fine. Non scrive a owner, IAM, Gateway o policy; nessuna nuova source/run. Directory già esistente blocca e richiede lettura dello stato, senza sovrascrivere snapshot o rilanciare build implicitamente.

Tre test locali PASS: percorso due immagini con snapshot/receipt privati e nessuna operazione live, drift pin bloccato prima della build, endpoint Admin remoto/pin simbolico rifiutati. Le build VPS restano da eseguire; Dockerfile Semantic/MCP produce immagini applicative, i test Java/Go sono quelli della CI già verde sui pin sorgente, non eseguiti di nuovo dalla build.

Parametri espliciti per questa installazione nel comando operatore: ouf-semantic, ouf-mcp, ouf-apisix; config APISIX /usr/local/apisix/conf/config.yaml, Admin http://127.0.0.1:9180; directory nuova sotto /etc/ouf/deploy-snapshots. Se config bind non corrisponde, lo script blocca senza switch e senza stampare segreti. L'output e lo snapshot preparano il successivo piano add-only per route, key binding, scopes/catalog/policy e switch con readiness/rollback. Non equivalgono a rilascio, nuova capability autorizzata o percorso file/API→UDP completato. Tutti i gate precedenti rimangono tracciati.


## Checkpoint immagini VPS e candidati fermi — 2026-10-02 08:58 Europe/Rome

Operatore: CONSULTATION_STAGE=PASS, LIVE_UNCHANGED=true, ROUTES_UNCHANGED=true, NO_SWITCH=true, NO_SOURCE_RUN=true. Directory privata /etc/ouf/deploy-snapshots/consultation-20261002-0850. Non ripetere le build:
- Semantic source 8985d0d7f772dc7a7fd3deb3d5a569b1406d5d6c → sha256:6a13b3fe2febad93d23e8c699f1139cfd616a29598b406f0a46a6534631a9555.
- MCP source 8476a689fc6e59055001f59fc79a024bd14aca4a → sha256:eb6169e33d6d50ba25ea100a11898dee26a0eb1f993ec8ce8ea33e32b8c40808.

Gateway readback: route mcp-generic-execution, managed-file create/handoff/preview/profile/upload, permissions e urban-object-search presenti; letture Semantic GET search e references:resolve già attive su ouf-semantic:8080 con i rispettivi scope. Le nuove route execute semantic/search|get sono assenti. Gateway possiede env per delegazione/Authorization/Search, non la chiave nuova OUF_SEMANTIC_READ_OWNER_KEY. Related-search risulta disabilitato nelle due route mostrate: stato ereditato, non attivato da questo sprint.

Nuovo preparatore scripts/r4a_prepare_semantic_consultation.py (dipendenza sibling r4a_stage_semantic_consultation.py): consuma snapshot/receipt dello staging già PASS, verifica live/image/routes freschi e concordanza issuer/audience/workload fra Lua execute e env Semantic/MCP. Checkout Gateway exact e8ef4b72093f4138d0efe78e9947ddfc4b471e27 e materializer già verificato generano soltanto due route private. Chiave casuale dedicata 32 bytes resa hex ASCII, semantic-owner.key UID/GID owner e mode0400, Gateway env privato0600; APISIX config nuovo conserva tutto tranne una nuova voce nginx_config.envs. Bind originali e file live non modificati.

Crea tre candidati con restart=no, mai start/stop/rename: ouf-semantic-consultation-candidate, ouf-mcp-consultation-candidate e ouf-apisix-consultation-candidate. Gateway riusa la stessa immagine live. Conserva launch contract, env precedenti, bind RO, resource limits e reti/alias dai dati reali; impostazioni non supportate bloccano prima dei create. Receipt salva intent prima di ogni create e ID verificati; directory prepared esistente blocca una ripetizione cieca. Candidato parziale/errore richiede readback degli intent/ID senza cancellare o riavviare i live.

Test locali cumulativi stage+prepare: 8 PASS; preflight 2 PASS. Nuovo workflow Consultation deploy scripts esegue questi test; esito CI sul commit da verificare prima di dichiararlo PASS. Questo preparatore non esegue switch, PUT route, grant/catalog/IAM/policy publication, approvazioni, attivazione source o run. Prossimo passo operatore: preparare tre candidati fermi dalla directory sopra; successivamente verificare receipt, predisporre backup/health/rollback e installer add-only con gestione esiti incerti prima del rilascio coordinato. Scope/catalog/policy Semantic correnti e HUMAN autorizzata rimangono da verificare. Non equiparare candidatura tecnica a filiera completa accettata; gate ereditati invariati.

### CI preparazione verificata — 2026-10-02

[Consultation deploy scripts](https://github.com/GioNob/ouf-semantic-registry/actions/runs/36977385047) SUCCESS sul commit 72ab11dee9b670c58cc04dd06c82e244dbb188df: otto test stage/prepare e due preflight eseguiti. Corretto il test di reentry per runner non-root; nessun cambiamento alle immagini applicative già staged. Comando operatore di preparazione deve usare i due helper pinned a questo commit; risultato VPS dei tre candidati ancora da acquisire. Non dichiara PASS il futuro switch o la filiera complessiva.
