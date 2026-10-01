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

## Letture obbligatorie per la nuova chat

Baseline PET v1.7 fornita dall'utente: Source Onboarding v1.6 §§92–92.2 e THS; Semantic Registry v1.3 §§9.2,10–11,17–18; UDP v1.3 §§21–22,109.2,109.6–109.9; Authorization v1.5 §36.10; MCP v1.4 e Gateway v1.5 per projection/delegation/channel boundary.

Nella sessione precedente i PET erano estratti dal pacchetto `OUF_Reality_Baseline_Package_v1_7(20261001-060705).zip`. Se non disponibili nella nuova chat/workspace o nei riferimenti autorizzati, richiedere il pacchetto necessario: questa sintesi non sostituisce la fonte normativa. Non accedere a Library di altre chat.

**Prima azione concreta:** leggere PET e baseline, verificare catalogo/contratti correnti e collegare la consultazione semantica governata per proporre il mapping dello stesso asset/profile. Non ri-uploadare, ri-profilare, riattivare Cinema o rilanciare recovery senza una necessità verificata.
