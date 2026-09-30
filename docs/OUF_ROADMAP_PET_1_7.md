# Roadmap OUF rispetto ai PET della baseline v1.7

Data della baseline: 16 settembre 2026. Snapshot operativo R4a: 27 settembre 2026. Stato: proposta esecutiva basata sui repository, non attestazione di conformità finale.

La priorità è completare la catena eseguibile e autorizzata tra i moduli. I repository contengono una parte consistente del dominio e dei test, ma rimangono codice di integrazione, capability, superfici umane e criteri di accettazione da realizzare. Non è corretto descrivere il lavoro residuo come sola configurazione IAM o collaudo di produzione.

## Avanzamento live al 29 settembre 2026

Lo [stato corrente e il punto esatto di ripresa](handoffs/OUF_HANDOFF_2026-09-29_R4A_PREFLIGHT_TO_INGESTION.md)
superano lo snapshot del 27 settembre qui sotto. UDP live usa l'immagine
`edaba2bff18a2aaf52d1180f21f0e68984cc3437`, Flyway 34, con backup e
container rollback conservati. Policy `ouf-lab-authorization:31`; scope/client
IAM e tre route APISIX di preflight sono attivi. Onboarding live ha token
SERVICE rinnovabile e la versione cinema è `IN_REVIEW`, lock 2, hash
congelato; il preflight HUMAN e la lettura dell'attestazione SERVICE sono
`PASS`, attestazione `57499699-dbc5-419d-a14b-27cd3604ec6f` con **zero**
oggetti ancora indicizzati. **Compatibilità Ingestion ABSENT**, immagine
Ingestion staged diversa dal live; nessuna approval/activation Onboarding o
run Ingestion → UDP → search attestata. L'inventario Ingestion read-only
preparato sul branch Semantic non è stato eseguito per scelta dell'utente.
**R-SMOKE OPEN; R-INSTALL OPEN.** Procedura e backup:
[attivazione R4a](R4A_IDENTITY_LAB_ACTIVATION.md). PR UDP
[#37](https://github.com/GioNob/ouf-udp-object-resolution/pull/37) open;
rollout live e merge sono fatti diversi.

## Snapshot R4a al 27 settembre 2026

[Handoff cross-module per nuova chat](https://github.com/GioNob/ouf-semantic-registry/blob/codex/r4a-smoke-semantic-inventory/docs/handoffs/OUF_HANDOFF_2026-09-27_R4A.md). L'upload HUMAN attraverso picker/Gateway ha prodotto l'asset `8ec8ae90-808a-4d9e-907c-d56de119e376`; il profilo è `4462692b-9c85-446b-b6fd-779f01eab64d`. Semantic ha pubblicato con conferma HUMAN la revisione `51706bed-81e4-4306-aca1-70119821727d` nel set `f92a2e17-30c9-456f-bb12-63afa84f41e6`. Il DRAFT Onboarding `managed-cinema-8ec8ae90` non è submitted/ACTIVE e non c'è evidenza di Ingestion → UDP → search per questo asset. **R-SMOKE OPEN**.

Prerequisito in review: [UDP PR #34](https://github.com/GioNob/ouf-udp-object-resolution/pull/34) rende durevole la review per record e rifiuta weighted non eseguito; [issue #35](https://github.com/GioNob/ouf-udp-object-resolution/issues/35) definisce il **prossimo incremento**, il motore di identità canonica generale. La regola usa proprietà semantiche condivise e vincoli governati, non nomi o frequenza dei valori; uno score non autorizza da solo MATCH. Allineare Onboarding/UDP prima di attivare il DRAFT. Distinguere CI, PR e rollout live. L'ordine e i gate sono dettagliati nell'handoff e nell'[audit PET R4a](audits/OUF_R4A_FINAL_AUDIT_2026-09-27.md). **R-INSTALL OPEN**: gli script lab non sostituiscono clean install, upgrade, restore e CI d'installabilità.

## 1. Autorità e metodo

Fonte normativa: `OUF_Reality_Baseline_Package_v1_7.zip` allegato. Verificati tutti i 323 checksum del pacchetto: nessuna difformità. Gerarchia applicata: Blueprint L0 v0.3 e Cross-Module Alignment Matrix v1.7, PET L1 applicabili, contratti macchina secondo la gerarchia del pacchetto, implementazione ed evidenze. La Terminology Supersession Notice v1.1 governa la terminologia; non sostituisce la semantica dei campi contrattuali.

| Documento L1 | Versione applicabile |
|---|---|
| Source Onboarding, Configuration e THS | 1.6 |
| Authorization e Access Control | 1.5 |
| Urban API Gateway | 1.5 |
| Ingestion Runtime | 1.3 |
| Data Lake, UDP e Urban Object Registry | 1.3 |
| Semantic Model Registry | 1.3 |
| MCP Server | 1.4, Go |

Esaminati i sei repository OUF trovati sotto GioNob: alberi completi, codice e wiring delle aree critiche, workflow CI, test, contratti e documenti di tracciabilità. Authorization è correttamente co-locata in Onboarding: la mancanza di un repository autonomo non è un gap. Nel primo audit del 16 settembre non furono modificati repository/PET né rieseguite suite: gli esiti CI di quella sezione sono storici. La revisione R4a del 27 settembre ha aggiornato documenti, un widget MCP e uno script di inventario su branch di lavoro; i workflow vanno riletti sui rispettivi nuovi HEAD.

La roadmap copre i principali ambiti dei sette PET e le dipendenze cross-module. Non equivale a una verifica esecutiva riga per riga di tutte le acceptance suite. Un'assenza è riferita ai sei repository ispezionati; eventuali componenti esterni non forniti richiedono evidenza nominata. I limiti non diventano implicitamente deroghe.

Classificazione: **CODICE** = implementazione/wiring mancante o incompleto osservato; **INTEGRAZIONE** = componenti presenti ma percorso tra processi non dimostrato; **EVIDENZA** = criterio da provare con test mirati; **AMBIENTE** = infrastruttura/binding e collaudo rappresentativo; **TRACCIABILITÀ** = documentazione/evidence da riconciliare.

## 2. Snapshot autorevole dei repository

| Repository | Commit main esaminato | CI sul commit |
|---|---|---|
| ouf-source-onboarding | `fb2dd51dfc204577a47c1e702f17531dd0709b3c` | Module CI verde, run 35121897270 |
| ouf-ingestion-runtime | `e732d3b17b6a75c35a2b52eedc2d0c586d2d2cf2` | Module CI verde, run 35129774169 |
| ouf-udp-object-resolution | `a18e1c1d1f6add41bb11c975e5f2487f352d1bdb` | Module CI verde, run 34886224933 |
| ouf-api-gateway | `8a1757e5879f73ee60c2786a7f5e2b325741c940` | Control-plane CI verde, run 35123350078 |
| ouf-mcp-server | `6980aac2e113ebbbe5f7b7329f58854d60dd6846` | MCP CI verde, run 35122560464 |
| ouf-semantic-registry | `353d2fc821035c5c3db1c2b142aeb9e3800ec0e3` | Module CI e Authorization pairwise verdi; Semantic Gateway live pairwise rosso |

Fonti CI: [Onboarding](https://github.com/GioNob/ouf-source-onboarding/actions/runs/35121897270), [Ingestion](https://github.com/GioNob/ouf-ingestion-runtime/actions/runs/35129774169), [UDP](https://github.com/GioNob/ouf-udp-object-resolution/actions/runs/34886224933), [Gateway](https://github.com/GioNob/ouf-api-gateway/actions/runs/35123350078), [MCP](https://github.com/GioNob/ouf-mcp-server/actions/runs/35122560464), [Semantic module](https://github.com/GioNob/ouf-semantic-registry/actions/runs/35142826809), [Authorization Semantic](https://github.com/GioNob/ouf-semantic-registry/actions/runs/35142826747), [Semantic Gateway live](https://github.com/GioNob/ouf-semantic-registry/actions/runs/35142826742).

### Primo blocco osservato

Il workflow Semantic Gateway live fallisce con HTTP 403 dopo l'avvio dei container. Lo script invia `X-OUF-Subject` come identità; il `TrustedActorResolver` corrente richiede invece un principal autenticato. Questa incoerenza offre una spiegazione concreta del fallimento, da chiudere con una nuova esecuzione dopo la correzione della fixture. Il vecchio header non deve essere reintrodotto come autorità.

Il workflow usa una **fixture Gateway Java**, non il Gateway APISIX completo, e dipende da schema.gov.it live. Anche una sua futura run verde non proverà automaticamente l'integrazione con il Gateway reale. Fonti: [script live](https://github.com/GioNob/ouf-semantic-registry/blob/353d2fc821035c5c3db1c2b142aeb9e3800ec0e3/pairwise/run-semantic-gateway-live.sh), [resolver](https://github.com/GioNob/ouf-semantic-registry/blob/353d2fc821035c5c3db1c2b142aeb9e3800ec0e3/src/main/java/it/comune/trieste/ouf/semantic/api/TrustedActorResolver.java).

La V9 duplicata è stata rimossa e la CI di modulo è verde: questo problema resta chiuso. Il 403 è un'evidenza nuova e distinta.

## 3. Gap verificati per modulo

### Authorization — priorità trasversale

Presenti: evaluator scenario-neutral, bundle immutabili, active pointer, decision evidence nel Registry, endpoint di distribuzione e cache locale MCP. È preservata l'architettura senza servizio Authorization sincrono sul percorso di ogni richiesta.

**AUT-01 — CODICE: completare il piano amministrativo.** Il controller Authorization esposto distribuisce il bundle ACTIVE; non costituisce il CRUD governato di policy/grant, registrazione capability, authoring con ETag e workflow amministrativo human-only richiesti da §§4.3, 109.1–109.4. I metodi Java di publish/activate non sostituiscono l'API amministrativa e i suoi controlli. Uscita: OpenAPI admin versionata, lifecycle e revoca con audit, stale ETag e actor negativi testati.

**AUT-02 — CODICE/INTEGRAZIONE: shared SDK e enforcement nei servizi.** Il contratto JSON esiste, ma la valutazione Java è nel package Onboarding e MCP ne ha un evaluator Go. Semantic e Ingestion consumano attributi trusted e capability; questo non dimostra lo SDK locale sui bundle previsto da Authorization §§109.1–109.3 e Semantic §160.7. Occorre artifact Java versionato, implementazione Go semanticamente conforme, loader/cache e security adapter nei servizi, con test comuni. Per UDP serve anche il pairwise Authorization e l'adattamento esplicito dei vocaboli legacy: `TrustedHumanContext` richiede ancora `HUMAN_USER`, mentre il contratto consumer recente usa `HUMAN/SERVICE/AI_AGENT`. Non rinominare alla cieca i dati storici.

**AUT-03 — CODICE: completare policy e freshness.** Il motore attuale verifica tenant, capability, actor, scope, soggetto/service principal, organizzazione e validità temporale del grant. Non realizza da solo tutti i vincoli di risorsa, DataAccessLabel, assurance/step-up e permitted detail level/visibility OA previsti da §§36.10, 109.2 e 34.2. La cache MCP conserva il last-known-good in caso di errore ma non applica `max-staleness` al momento della decisione (§109.6); la validità dei grant è un controllo diverso. Uscita: policy di freschezza governata, fail-closed oltre soglia, hash/integrità bundle verificabili, medesimi fixture allow/deny tra linguaggi, coarse allow/backend deny e revoca dimostrati.

**AUT-04 — AMBIENTE:** selezionare/configurare scenario A/B/C, issuer/JWKS, audience, claim mapping, rotazione/revoca e identità workload (§109.5). Avviare questa dipendenza subito, senza bloccare lo sviluppo scenario-neutral.

Fonti: [API distribuzione](https://github.com/GioNob/ouf-source-onboarding/blob/fb2dd51dfc204577a47c1e702f17531dd0709b3c/src/main/java/it/comune/trieste/ouf/onboarding/api/AuthorizationBundleApi.java), [evaluator Java](https://github.com/GioNob/ouf-source-onboarding/blob/fb2dd51dfc204577a47c1e702f17531dd0709b3c/src/main/java/it/comune/trieste/ouf/onboarding/authorization/AuthorizationPolicy.java), [cache MCP](https://github.com/GioNob/ouf-mcp-server/blob/6980aac2e113ebbbe5f7b7329f58854d60dd6846/internal/authorization/cache.go), [guard UDP](https://github.com/GioNob/ouf-udp-object-resolution/blob/a18e1c1d1f6add41bb11c975e5f2487f352d1bdb/src/main/java/it/comune/trieste/ouf/udp/TrustedHumanContext.java).

### Onboarding e THS

Presenti: registry/versioni, mapping, validazione, bundle, challenge umani, CSV/XLSX, quarantena intake, proiezioni runtime, semantic gap, backend protected logs/export.

**ONB-01 — CODICE/INTEGRAZIONE:** completare discovery tecnica automatica attraverso Gateway. `DiscoveryService` gestisce start/claim/complete e snapshot, ma non è presente un worker di discovery sorgenti equivalente ai worker schedulati file-profile ed export. Collegare fetch schema/type/state, retry/recovery e callback Semantic, senza confondere registrazione di uno snapshot con acquisizione automatica. PET §§109.4–109.5, 109.9 e gate §109.17.

**ONB-02 — INTEGRAZIONE:** ACTIVE bundle → proiezione Gateway → compatibilità Ingestion → prima ingestione file o PULL. Verificare exact references, acknowledgement e riattivazione dopo schema drift; la policy operativa va realmente consumata dall'Ingestion, non soltanto serializzata. PET §37 e §109.17; OUF-E2E-001/017/019/020.

**THS-01 — CODICE/INTEGRAZIONE:** realizzare la superficie browser fiduciaria comune e i relativi adapter ai backend owner. Il repository dichiara il browser shell delegato; nessun frontend THS è stato trovato nei sei repository. Completare card cross-module, sessione umana, assurance/freshness, stale challenge e handoff di approvazione; collegare il log store condiviso oltre l'adapter audit Onboarding. Il frontend amministrativo generico resta opzionale, la THS prevista dal PET no. Riferimenti §§101–106, 109.1 e OUF-E2E-014/016.

**ONB-03 — CODICE/EVIDENZA/AMBIENTE:** configuration catalog completo, packaging Helm/NetworkPolicy, upgrade N/N+1, capacity fixture e restore THS con challenge scadute non riattivate. Mancano nel repository gli artefatti operativi completi richiesti da §§109.10–109.16; non sono tutte semplici coordinate esterne. Profilo normativo: 1.000 source, 10.000 type, 500.000 field, concorrenza amministrativa/job dichiarata dal PET.

Fonti: [tracciabilità](https://github.com/GioNob/ouf-source-onboarding/blob/fb2dd51dfc204577a47c1e702f17531dd0709b3c/docs/PET_TRACEABILITY.md), [discovery](https://github.com/GioNob/ouf-source-onboarding/blob/fb2dd51dfc204577a47c1e702f17531dd0709b3c/src/main/java/it/comune/trieste/ouf/onboarding/application/DiscoveryService.java), [OA](https://github.com/GioNob/ouf-source-onboarding/blob/fb2dd51dfc204577a47c1e702f17531dd0709b3c/docs/OPERATIONAL_AWARENESS_TRACEABILITY.md).

### Ingestion Runtime

Presenti: stato run/checkpoint/watermark, outbox/durable ACK, lease/fairness/retry, pipeline, CSV/XLSX e REST/WFS, replay, quarantena e controllo umano. Questa implementazione va riusata.

**ING-01 — CODICE/INTEGRAZIONE, blocco della catena:** collegare gli adapter di produzione per bundle ACTIVE, Semantic preflight, Data Lake, durable handoff UDP, replay e ritorno Onboarding. `RunCoordinator`, `RunExecutionWorker`, `OutboxDispatcher` e `ReplayWorker` sono condizionati alla presenza di port; non risultano bean di produzione per l'intera composizione né un loop schedulato che invochi questi metodi. `@EnableScheduling` da solo non avvia l'ingestion. I test costruiscono percorsi eseguibili ma non dimostrano che il container confezionato li avvii. Uscita: una source ACTIVE viene acquisita senza chiamate manuali ai metodi Java, ACK e watermark rispettano i vincoli, restart e lease recovery provati. PET §§21, 32–37, 80–89, 128 e 139.

**ING-02 — CODICE/INTEGRAZIONE: chiudere il producer Operational Awareness.** La proiezione corrente legge `runtime_issue` e traduce OPEN/altri stati in OPEN/RESOLVED. Non implementa l'intera timeline RETRY_WAIT/RECOVERING/RESOLVED, dedup correlato, misfire, attempt count/nextRetryAt e retention governata ≥30 giorni. Inoltre `summary` conta gli OPEN nella lista limitata: occorre impedire HEALTHY quando incidenti aperti sono fuori dalla pagina/finestra. Query e riepilogo devono avere semantiche distinte e complete. Riferimenti §46.1–46.5, OA-ING-01…06, Matrix §6.

**ING-03 — CODICE/EVIDENZA:** coprire i profili GIS richiesti dal §143.2 oltre REST/WFS e managed CSV/XLSX: OGC API Features, GeoPackage, GeoJSON/JSON-FG e Shapefile ZIP, con layer/CRS e limiti di parser espliciti. Un adapter JSON generico non dimostra automaticamente conformità a questi formati. Procedere per fixture verticali, senza introdurre un nuovo runtime non richiesto.

Fonti: [coordinatore](https://github.com/GioNob/ouf-ingestion-runtime/blob/e732d3b17b6a75c35a2b52eedc2d0c586d2d2cf2/src/main/java/it/comune/trieste/ouf/ingestion/RunCoordinator.java), [worker](https://github.com/GioNob/ouf-ingestion-runtime/blob/e732d3b17b6a75c35a2b52eedc2d0c586d2d2cf2/src/main/java/it/comune/trieste/ouf/ingestion/RunExecutionWorker.java), [runtime ports](https://github.com/GioNob/ouf-ingestion-runtime/blob/e732d3b17b6a75c35a2b52eedc2d0c586d2d2cf2/src/main/java/it/comune/trieste/ouf/ingestion/RuntimePorts.java), [OA service](https://github.com/GioNob/ouf-ingestion-runtime/blob/e732d3b17b6a75c35a2b52eedc2d0c586d2d2cf2/src/main/java/it/comune/trieste/ouf/ingestion/OperationalAwarenessService.java).

### UDP, Object Resolution e Data Lake

Presenti: durable intake, resolution, authority/provenance, materializzazione temporale/delta, graph/spatial/related search, budget condiviso, human merge/split, lake retention/rebuild, replay e prove DR di laboratorio.

**UDP-01 — CODICE/INTEGRAZIONE:** collegare configuration ports ai bundle storici esatti e avviare il resolution worker nel runtime. `ResolutionWorker` è condizionato a due port di configurazione, senza adapter bean/loop di produzione individuati. Dimostrare poi nel medesimo percorso resolution, proprietà, relazioni e spatial: test separati dei materializer non bastano. PET §§95–97, 109.6–109.7.

**UDP-02 — CODICE/EVIDENZA:** chiudere i residui espliciti del registro attuale: cleanup globale query_budget e prova bloat/lock (A42); progressive pruning e protezione ingestion/current read sotto carico agentico (A29/A35); history/asOf/lineage da cold storage (A23); limiti graph completi (A15/E2E-10); N/N+1 (A19); concorrenza materializzazione/merge (A21 v1.0); validTo e non-triplicazione (A06/A02).

**UDP-03 — INTEGRAZIONE/EVIDENZA:** breaking drift senza perdita dello storico, preflight contro registry reali, WFS conversazionale/GIS statico, source-to-serving correlation e capacity gate per nuove fonti (E2E-04/13/15, A07/08/09/10/20).

Il JSON corrente contiene **48 VERIFIED, 16 PARTIAL, 3 VERIFIED-LAB, 2 EXTERNAL-OPEN** su 69 righe. Sono classificazioni del repository, non 48 certificazioni indipendenti di questo audit. Il Markdown riporta ancora conteggi e blocchi precedenti. Non riaprire analytical rejection, delta/bitemporal, retry guard e resilienza replica già implementati; rimangono le prove realmente mancanti.

Fonti: [registro puntuale](https://github.com/GioNob/ouf-udp-object-resolution/blob/a18e1c1d1f6add41bb11c975e5f2487f352d1bdb/docs/pet-traceability-v1.3.json), [resolution worker](https://github.com/GioNob/ouf-udp-object-resolution/blob/a18e1c1d1f6add41bb11c975e5f2487f352d1bdb/src/main/java/it/comune/trieste/ouf/udp/ResolutionWorker.java), [resilienza governor](https://github.com/GioNob/ouf-udp-object-resolution/blob/a18e1c1d1f6add41bb11c975e5f2487f352d1bdb/docs/QUERY_BUDGET_GOVERNOR_RESILIENCE.md).

### Semantic Registry

Presenti: artefatti/revisioni, parser Jena locale, discovery provider, adozione/snapshot, validation/impact, approval/publication atomica, deprecate/retire e risoluzione storica. La V9 è chiusa.

**SEM-01 — INTEGRAZIONE (PARTIAL, evidenza R2c):** correggere il live pairwise e successivamente provarlo contro Gateway e identità conformi. Agganciare Onboarding/Ingestion/UDP agli exact SemanticReference; non basta il test Authorization basato su ispezione di schema e stringhe del resolver. PET §§133–136, 160.7, 160.15.

**SEM-02 — CODICE/EVIDENZA:** chiudere pause/cancel e partial-result semantics dei job; admission per classe/per-provider, fan-out, parser/time/size e publication limits nel configuration catalog; startup/reference-integrity e restore reconciliation. L'API discovery attuale espone creazione, candidates, adoption e providers, senza coprire tutto §160.4. Verificare separatamente la completezza dell'upstream lifecycle §§61/134, distinguendo notice/proposal già presenti dalle operazioni di check/recovery ancora da completare.

**SEM-03 — CODICE/EVIDENZA/AMBIENTE:** Helm/GitOps, dashboard/alert, runbook e configuration reference, capability/job schema e release package; upgrade N/N+1, security scans/SBOM/provenance, restore e profilo 100k artefatti/1M concept con isolamento provider failure. Sono deliverable obbligatori §§160.1, 160.8–160.14 e DoD §160.17 non coperti dalla sola build Maven/container attuale.

Fonti: [API discovery](https://github.com/GioNob/ouf-semantic-registry/blob/353d2fc821035c5c3db1c2b142aeb9e3800ec0e3/src/main/java/it/comune/trieste/ouf/semantic/api/DiscoveryApi.java), [config](https://github.com/GioNob/ouf-semantic-registry/blob/353d2fc821035c5c3db1c2b142aeb9e3800ec0e3/src/main/resources/application.yml), [CI modulo](https://github.com/GioNob/ouf-semantic-registry/blob/353d2fc821035c5c3db1c2b142aeb9e3800ec0e3/.github/workflows/module-ci.yml), [pairwise Authorization](https://github.com/GioNob/ouf-semantic-registry/blob/353d2fc821035c5c3db1c2b142aeb9e3800ec0e3/.github/workflows/authorization-pairwise.yml).

### Gateway

Presenti: config compiler, manifest e route, publication/LKG, adapter Admin API, activation gates, controlli anti-SSRF/identità, manifest HA/network, incident store e route OA channel-neutral.

**GW-01 — INTEGRAZIONE/CODICE:** esercitare compiler/publication/controller con APISIX ed etcd reali, con entrypoint e scheduling/deployment operativo del control plane. Oggi la CI principale esegue Python/pytest e compile config; non avvia la topologia APISIX/etcd. Implementazioni dei port e manifest non sono prova del dataplane. Collegare anche i binding business mancanti man mano che si espande il catalogo.

**GW-02 — CODICE/AMBIENTE:** portare la persistenza incidenti dal riferimento SQLite a un backend di produzione coerente con HA, backup e retention, oppure produrre una soluzione governata che dimostri tali requisiti. Verificare fault reali APISIX/etcd/trust e recovery stesso incidente. Riferimenti PET §34 e T33.9–T33.10; Matrix §6.

**GW-03 — AMBIENTE/EVIDENZA:** prove packet-level default deny e bypass southbound, FQDN/DNS rebinding sul CNI scelto, mTLS/JWKS, etcd quorum/partition/member-loss/restore, rolling N/N+1, drain/HPA/PDB, upload/realtime e capacity. T33.4–T33.16 e OUF-E2E-023/024. Non introdurre un bypass per rendere verde un test.

Fonti: [CI](https://github.com/GioNob/ouf-api-gateway/blob/8a1757e5879f73ee60c2786a7f5e2b325741c940/.github/workflows/ci.yml), [producer OA](https://github.com/GioNob/ouf-api-gateway/blob/8a1757e5879f73ee60c2786a7f5e2b325741c940/docs/GATEWAY_OPERATIONAL_AWARENESS_PRODUCER_TRACEABILITY.md), [etcd acceptance](https://github.com/GioNob/ouf-api-gateway/blob/8a1757e5879f73ee60c2786a7f5e2b325741c940/docs/GATEWAY_1H_BC_TRACEABILITY.md).

### MCP

Presenti: SDK Go, kernel/protocollo, budget/admission, reconciliation/recovery, evidence, retention parziale, maintenance, cache Authorization locale, owner API separate e aggregazione OA Ingestion/Gateway/MCP.

**MCP-01 — CODICE/INTEGRAZIONE:** completare la proiezione del catalogo owner. Il manifest attuale registra **sette tool**, di cui sei OA e `urban.object.related_search`, più un descriptor human-only non esposto. Non copre ancora l'intero serving UDP, onboarding/file/discovery/semantic e proposal/handoff prescritti. Pubblicare per tranche complete owner→Gateway→MCP, con schemi input/output, versioni e classificazione; non annunciare tool senza backend. Protected Operations non diventa un tool. Riferimenti PET §§91–96, 114, 122 e OUF-E2E-022.

**MCP-02 — CODICE/INTEGRAZIONE:** completare OA con finestra since/until, cursor pagination, timeline, durata/attempt/retry, distinguendo denial, redaction e producer unavailable. `ouf.system.status` descrive oggi il solo stato MCP, mentre §33.2 richiede lo snapshot dei moduli visibili; `operations.summary` aggrega già tre producer. Chiarire e coprire il requisito senza cancellare l'owner API channel-neutral. `operations.explain` è ancora legato all'Ingestion: aggiungere dispatch owner-aware per gli incidenti degli altri producer previsti. Gate OA-MCP-01…08 e OA-CN.

**MCP-03 — EVIDENZA/CODICE:** aggiungere gate di conformance ufficiale della versione MCP normativa e interoperabilità con client SDK indipendente; non individuati nella CI corrente. Non basta la dipendenza dall'SDK ufficiale. Completare retention invariant-preserving dei manifest snapshot dove dovuta (esplicitamente pending nel registro), mantenendo le prove già ottenute per audit/attempt/evidence. Packaging OCI/SBOM/provenance e collaudo HA/DR restano parte della chiusura.

Fonti: [manifest attuale](https://github.com/GioNob/ouf-mcp-server/blob/6980aac2e113ebbbe5f7b7329f58854d60dd6846/internal/manifest/capabilities.json), [CI](https://github.com/GioNob/ouf-mcp-server/blob/6980aac2e113ebbbe5f7b7329f58854d60dd6846/.github/workflows/ci.yml), [OA aggregazione](https://github.com/GioNob/ouf-mcp-server/blob/6980aac2e113ebbbe5f7b7329f58854d60dd6846/docs/MCP_OPERATIONAL_AWARENESS_AGGREGATION_TRACEABILITY.md), [retention](https://github.com/GioNob/ouf-mcp-server/blob/6980aac2e113ebbbe5f7b7329f58854d60dd6846/docs/MCP_1G_RETENTION_CHAIN_TRACEABILITY.md).

## 4. Roadmap ordinata e criteri di uscita

Le tranche seguenti sono una proposta di sequenza, non nuove prescrizioni dei PET. Non assegno date o percentuali complessive senza capacità del team, ambiente e consuntivi: darebbero una precisione ingannevole.

| Ordine | Tranche e obiettivo | Dipendenze | Criterio di uscita verificabile |
|---|---|---|---|
| R0, immediata | Ripristinare Semantic live pairwise; registro unico requisiti/evidenze | Nessuna | Fixture autenticata senza header spoofing; workflow verde; baseline v1.7 e commit/CI associati a ogni claim |
| R1a | Authorization↔UDP e shared SDK/security adapter Java | R0 | HUMAN/legacy boundary esplicito; deny backend con coarse allow; bundle pinning e contesto trusted su tutti i servizi |
| R1b | Authorization amministrativa, policy completa e cache freshness | R1a, sviluppabile in parte insieme | Admin human-only/ETag/audit, resource/DataAccessLabel/assurance/detail policy, max-staleness, rotazione bundle e fixture comuni |
| R2a | Onboarding→Ingestion reale | R1; Gateway di integrazione | ACTIVE bundle genera prima run file e PULL senza invocazioni manuali dei worker; preflight exact e schedule versionato |
| R2b | Ingestion→Lake/UDP→serving reale | R2a | Persistenza raw, ACK, watermark, resolution/materialization e lettura autorizzata nello stesso percorso; crash/retry senza perdita/duplicazione |
| R2c | Semantic↔Onboarding↔runtime | R1, R2 | Discovery/adoption/publication governate; cambio ACTIVE non cambia la run pinned; historical replay esatto |
| R2d | Fondazioni geografiche e decisione CRS | R2c | CRS configurabile per Comune; trasformazioni effettive e ordine assi; grigliati verificati/versionati; scelta umana converti/rigetta registrata nel profilo |
| R2e | GeoPackage → oggetti e relazioni | R2d | Telecamere e armadi acquisiti come oggetti con identità stabile; relazione per identificativo, navigabile nei due sensi; riferimenti mancanti/ambigui espliciti |
| R3 | Operational Awareness completa, priorità prodotto | R1 e R2a/b | OUF-OA-001…006 e OUF-OA-CN-001…005: fault offline, retry/dedup/recovery, misfire, retention, partial/deny, medesimo owner via MCP/API |
| R4a | Catalogo capability e THS comune | R1/R2; può procedere con R3 | Onboarding/file, serving e proposal esposti via Gateway/MCP; decisioni umane e protected logs confinati a THS browser |
| R4b | Residui di dominio | R2; per moduli indipendenti | UDP PARTIAL chiusi; altri formati/casi GIS previsti oltre GeoPackage; Semantic job/limits/upstream lifecycle e Onboarding discovery automatica completi |
| R5 | Gate riproducibili di release | Avvio già in R0, chiusura dopo R4 | Upgrade N/N+1, contract diff, protocol/interoperability, negative security, supply chain e package operativo conformi per ciascun modulo |
| R6 | Acceptance cross-module e rappresentativa | R1–R5; IAM/CNI/storage pronti | 25 scenari E2E, suite locali PET, HA/fault/load/restore, RPO/RTO misurati e sign-off delle evidenze |

Il lavoro di piattaforma va avviato **subito in parallelo alla pianificazione**: scelta IAM A/B/C, ambiente APISIX/etcd, PostgreSQL/object storage, CNI/NetworkPolicy, log/metrics e client THS. Il PET consente fixture conformi nello sviluppo; la vera integrazione e l'accettazione richiedono binding effettivi. Questa è una dipendenza da governare, non un motivo per fermare ogni sviluppo.

Ogni tranche deve produrre PR limitate, riferimenti PET/Matrix, test negativi e criterio di uscita. Nessun nuovo microservizio Authorization, incident hub o Agent Host interno è necessario per questa roadmap.

## 5. Piano delle evidenze cross-module

Il catalogo normativo è E2E v0.3 incluso nel pacchetto. Nei sei repository non è stato trovato un runner comune tracciato ai 25 ID canonici. Alcuni scenari hanno prove locali o pairwise; non vanno contati come full-path senza un report che colleghi versioni, risultati ed evidenze.

| Gruppo | ID canonici | Quando chiudere |
|---|---|---|
| Attivazione, acquisizione, identità oggetto e storico | 001, 002, 003, 004, 006, 015, 017, 019, 020 | R2, poi regressione R6 |
| WFS conversazionale e dati personali | 005, 007 | R4a/b + R1 |
| Tool routing, retry, budget e confine analitico | 008, 009, 010, 011, 012, 013 | R4a/b, multi-Pod rappresentativo R6 |
| Decisione umana e protected logs | 014, 016 | R4a |
| Coarse/fine deny, M2M e capability projection | 018, 021, 022 | R1/R4a |
| Egress, LKG e error/correlation full-path | 023, 024, 025 | R2/R5, CNI/etcd reali R6 |
| Operational Awareness e channel neutrality | OUF-OA-001…006, OUF-OA-CN-001…005 | R3, validazione ambiente R6 |

R6 deve includere anche i target dei PET, non solo happy path: isolamento sotto carico, multi-worker/multi-Pod, revoca credenziali/policy, producer outage, failover, restore e continuità dei riferimenti storici. Per UDP esistono già restore/PITR e performance di laboratorio: si riusano, senza spacciare il laboratorio per accettazione dei target di produzione.

## 6. Correzioni necessarie alla tracciabilità

1. Il documento UDP `PET_TRACEABILITY.md` mantiene conteggi vecchi e richiama un pacchetto precedente; il JSON attuale ha esiti più avanzati. Riconciliare il riepilogo conservando lo storico.
2. Semantic `evidence/acceptance-traceability.json` indica "Semantic Model Registry v1.4", mentre il PET nel pacchetto v1.7 è v1.3. Correggere il riferimento documentale, senza attribuire una nuova versione al PET.
3. Le note iniziali MCP/Gateway marcano pending funzioni poi realizzate. Ogni gap va chiuso con link al commit/test successivo, non lasciato come falso arretrato.
4. Le CI pairwise pin-nano revisioni precise dei peer, talvolta precedenti ai main qui esaminati. È corretto per riproducibilità, ma serve anche una matrice della combinazione candidata al rilascio: un vecchio pin verde non dimostra compatibilità con tutti i main correnti.
5. Distinguere test su stringhe/config, test di modulo con stub, integrazione tra processi reali e prova nell'ambiente rappresentativo. Il nome "pairwise" da solo non determina il livello di evidenza.

Registro minimo per ogni requisito: documento/versione/sezione/ID, owner, stato, codice e commit, test e livello, CI/artifact/hash, gap residuo, dipendenze, criterio di chiusura. Gli ID della presente roadmap sono locali al report e non rinumerano i PET. La Matrix L0 resta normativa: si aggiorna con change control se cambia il contratto/ownership; il registro di implementazione registra l'avanzamento.

Regola operativa permanente per il seguito: **una decisione risolta non viene riaperta senza nuova evidenza da repository o CI**. Una build verde non modifica i requisiti dei PET; una voce "CHIUSO" nel gap register del documento di progetto indica completezza della specifica, non implementazione avvenuta.

## 7. Prossimo passo raccomandato

R0 e R1a sono consegnati; R1b ha ora implementazione centrale e controlli owner nei percorsi descritti in `R1B_OWNER_ENFORCEMENT_EVIDENCE.md`. R2a ora consegna admission automatica file/PULL, bundle ACTIVE verificato, preflight esatto e schedule versionato. R2b ora dimostra il percorso CSV/REST fino alla lettura autorizzata e al lineage, con ACK e watermark verificati fra processi. R2d consegna ora le fondazioni CRS governate descritte in `R2D_GOVERNED_CRS_EVIDENCE.md`. R2e aggiunge ora GeoPackage, identità stabile per feature e relazioni telecamere↔armadi; evidenze in `R2E_GEOPACKAGE_RELATIONSHIPS_EVIDENCE.md`. Il prossimo incremento è **R3**, mantenendo separati i gate di ambiente e le superfici umane ancora mancanti. I controlli owner implementati devono essere mantenuti nel percorso; l'accettazione completa dei restanti domini/proiezioni e dell'identità reale rimane tracciata in AUT-03/AUT-04, senza riaprire decisioni già risolte.


## Avanzamento R1b — 17 settembre 2026

Implementazione centrale Authorization e cache consegnata; evidenze in `R1B_AUTHORIZATION_EVIDENCE.md`. AUT-01 chiuso per l'API amministrativa verificata in laboratorio. AUT-02 e AUT-03 restano parziali per enforcement e proiezioni owner-specific, con audit esplicito in `R1B_ENDPOINT_COVERAGE_AUDIT.md`. AUT-04 resta il gate IAM/THS reale. Lo stato `IMPLEMENTED_WITH_INTEGRATION_GAPS` non equivale ad accettazione completa del PET o a chiusura di tutti i requisiti della fase.

## Follow-up R1b: enforcement owner — 17 settembre 2026

Corretti tutti i percorsi Semantic mediante matrice capability fail-closed, le proiezioni UDP incluse query graph/related/spatial, la Operational Awareness Ingestion e i protected log Onboarding/Ingestion. Evidenze immutabili e PR: `R1B_OWNER_ENFORCEMENT_EVIDENCE.md`. AUT-02 soddisfa il criterio SDK/adapter/conformità e backend deny; AUT-03 conserva l'accettazione completa delle proiezioni owner nei restanti domini e canali. AUT-04 resta il gate IAM/THS reale. I test di modulo non chiudono R2/R6.

## Avanzamento R2a — 17 settembre 2026

Admission automatica e preflight file/PULL implementati; evidenze in `R2A_ACTIVATION_EVIDENCE.md`. Il test tra processi usa Onboarding reale e il JAR di produzione Ingestion, con Gateway/Semantic/identità di laboratorio dichiarati. ONB-02 e ING-01 avanzano a PARTIAL: ACK, acquisizione completa, watermark, replay e ritorno Onboarding restano da verificare in R2b/c. La successiva evidenza R2b è descritta sotto; RUNNING mantiene il solo significato di admission.

## Aggiornamento R2b — 17 settembre 2026

Scenario CSV/REST implementato, verificato e mergiato: il lettore autorizzato trova i valori acquisiti, il campo riservato è omesso e il lineage è consultabile. La prova completa usa Onboarding, JAR Ingestion, UDP, PostgreSQL/PostGIS e MinIO reali; verifica perdita ACK, HTTP 202 senza watermark, kill/restart e assenza di duplicati. Evidenze e commit in `R2B_SERVING_EVIDENCE.md` e `r2b` del registro JSON.

**Limite del risultato:** Gateway HTTP, sorgenti, Semantic e identità/approvazione sono fixture dichiarate. APISIX, adapter di invocazione southbound e managed storage reali restano GW-01; IAM/THS, profili estesi e ambiente rappresentativo restano gate aperti. La superficie utilizzabile verificata è l’API; browser/MCP e presentazione integrata dello stato restano R4/R3. ONB-02, ING-01 e UDP-01 rimangono PARTIAL rispetto ai criteri PET completi.

Per ogni incremento, accanto a commit e CI, dichiarare persona, obiettivo, superficie, risultato osservabile e verifica. Prossimo passo della sequenza: R3; questa regola umana resta vincolante anche nei blocchi infrastrutturali.


## R2c — pubblicazioni governate e riferimenti storici

L'incremento collega il processo Semantic reale ai processi Onboarding, Ingestion e UDP. Il provider esterno, Gateway e identità/decisioni umane restano fixture dichiarate. Le correzioni permettono di assegnare una versione a una bozza adottata, vincolano il candidato alla richiesta di discovery e impediscono di risolvere un gap Onboarding prima della pubblicazione.

Il cambio ACTIVE è verificato durante consegne non ancora confermate: snapshot precedenti immutati, nuova pubblicazione distinta, recupero outbox al riavvio, lookup storico esatto senza fallback. L'accesso storico distingue revisioni pubblicate poi deprecate/ritirate da bozze mai pubblicate. I riferimenti contrattuali sono visibili anche negli snapshot nel formato R2.

**Prova di replay R2c:** oltre alla riconsegna outbox, il piano umano UDP REPRODUCE deve verificare i byte Lake del vecchio handoff, risolvere i suoi riferimenti storici e completare la materializzazione mentre la nuova configurazione è ACTIVE. Il confronto deve usare il checksum del file di evidenza, distinto dal contentHash canonico. L’esecuzione deve essere idempotente e conservare il riferimento al raw sorgente. **Gate generale ancora aperto:** questo non certifica REPRODUCE/REPROCESS dei raw in quarantena Ingestion; ReplayExecutionPort e la conservazione dei metadati di riproduzione restano nel completamento operativo R3/ING-01.

**Verifica umana:** il lettore autorizzato consulta gli oggetti e la provenienza dei dati; una nuova configurazione non riscrive la configurazione delle elaborazioni precedenti. Superficie verificata: API. La superficie THS e il percorso operatore completo restano R4a.

## Requisiti GIS concordati per R2d/R2e/R3/R4a

- Ogni feature (geometria e riga attributi) alimenta un oggetto canonico secondo mapping e identità approvati. Riacquisire aggiorna senza duplicare. Telecamera→armadio usa l'identificativo dell'armadio; target assenti restano irrisolti e si riconciliano al successivo caricamento, target ambigui richiedono revisione.
- CRS sorgente per layer conservato; CRS comunale configurabile (Trieste EPSG:6708), distinto dal CRS di esposizione. Ordine assi, area d'uso, precisione e trasformazione sono espliciti; nessuna semplice rietichettatura SRID.
- CRS diverso: l'umano sceglie conversione o rigetto dopo aver visto operazione proposta, accuratezza dichiarata o non nota e limitazioni. La scelta vale nel profilo versionato anche per fonti dinamiche; cambi di CRS/operazione/condizioni richiedono nuova decisione. CRS ignoto non viene indovinato.
- Grigliati: inventario per coppia CRS e territorio, verifica condizioni d'uso, versione/checksum fissati, conservazione dell'originale e test su punti noti. Nessun ripiego silenzioso verso trasformazioni meno accurate se manca una risorsa richiesta. Disponibilità dei grigliati IGM/locali non ancora attestata.
- R3 espone progressi, errori geometrici/CRS e collegamenti irrisolti. R4a fornisce anteprima cartografica, importazione guidata, schede e relazioni navigabili. La geocodifica conserva fonte/precisione e converte nel CRS comunale; punto del civico e perimetro effettivo del dehor devono restare distinguibili.
- R4b conserva i restanti formati e casi GIS prescritti dai PET. La CI tecnica di R2e non equivale alla completa accettazione umana, che richiede R4a.

R2c: **36 verifiche PASS** nello scenario tra quattro owner, incluso REPRODUCE UDP. Evidenze, SHA dei consumer e limiti in `R2C_GOVERNED_PUBLICATION_EVIDENCE.md` e nel registro JSON. R2d è implementato e verificato nel perimetro delle fondazioni CRS; R2e verifica ora GeoPackage e relazioni con 25 controlli fra quattro owner; R3 è il prossimo incremento; i gate generali elencati restano aperti.

SEM-01 e UDP-03 passano a PARTIAL per le prove R2c; i residui sono esplicitati nel registro. Il live pairwise già ripristinato in R0 non viene riaperto.


## Stato R2d — fondazioni CRS governate

R2d implementa CRS comunale configurabile (test EPSG:6708 e altro Comune), ordine assi esplicito, operazioni PROJ effettive approvate, originale e provenance, verifiche di area/punti/grigliati e scelta CONVERT/REJECT congelata nel profilo. Il loop automatico rifiuta geometrie incompatibili prima di creare oggetti vuoti. La scheda owner THS espone la decisione; il serving owner espone canonico e CRS/provenance con omissione autorizzata.

Evidenze e limiti: `R2D_GOVERNED_CRS_EVIDENCE.md` e sezione `r2d` del registro. I grigliati sono stati collaudati con una risorsa sintetica: **la disponibilità/licenza/precisione dei grigliati IGM per Trieste resta un gate di ambiente**. La fixture 6708 non certifica equivalenza geodetica RDN2008/WGS84. I gruppi PET generali restano aperti dove mancano formati, percorsi e acceptance.

R2e è ora descritto nella sezione seguente. R3 e R4a completano osservabilità, remediation e superfici umane cartografiche.

## Stato R2e — GeoPackage e relazioni governate

R2e consegna profilazione dei layer, scelta esplicita di layer/chiavi, acquisizione bounded in sola lettura, identità per feature stabile nel ricaricamento, geometria originale/canonica e riferimenti storici. Le relazioni telecamere↔armadi sono navigabili nei due sensi; i target tardivi vengono riconciliati con la regola originale, quelli ambigui restano in revisione e i riferimenti cambiati ritirano gli edge precedenti.

La CI fra quattro owner, PostGIS e MinIO contiene **25 verifiche PASS**. Fixture Gateway/identità dichiarate, commit, run, limiti e stato dei merge sono riportati in [R2E_GEOPACKAGE_RELATIONSHIPS_EVIDENCE.md](R2E_GEOPACKAGE_RELATIONSHIPS_EVIDENCE.md) e nella sezione `r2e` del registro JSON. La geometria sorgente mappata richiede il permesso geometrico anche in current, history e search.

Restano 2D simple features e limiti di parser espliciti; altri formati/casi sono R4b. Nessun grigliato IGM reale o collaudo territoriale è attestato. La UI cartografica resta R4a; prossimo incremento **R3 — Operational Awareness**.

Ogni sprint deve consultare tutti i sette PET e L0: [regola obbligatoria e manifest delle fonti](OUF_SPRINT_PET_ALIGNMENT.md).

## Ripresa R4a — 30 settembre: inventario Ingestion e sonda candidata

L’operatore ha eseguito l’inventario rimasto sospeso: **PASS**. Flyway live/staged
è 14/14; lo staged `e3f04f1…` differisce dal live. Policy
`ouf-lab-authorization:31`: un descriptor SERVICE e un grant SERVICE per
`ouf.ingestion.configuration.attest`, zero altri grant. I conteggi non provano
che il bearer effettivo sia il principal destinatario del grant né che la route
risponda; la compatibilità della versione resta non attestata.

La [PR Ingestion #33](https://github.com/GioNob/ouf-ingestion-runtime/pull/33),
commit `da941666643d83f9f417da85be91fb3b10d4db01`, aggiunge una sonda nel jar
che usa mapper, adapter e validator dei contratti CDE/lineage/handoff di
produzione. Verifica hash/stato congelato, riferimenti Semantic esatti, integrità
dell’asset, identità sorgente e tutte le righe. Lo script versionato costruisce
una candidata isolata, senza avviare Spring/Flyway/worker o scrivere run,
materializzazioni e attestazioni. Il PASS della sonda avrà
`candidateDeployed=false` e `attestationSubmitted=false`.

La prima revisione passa i sei test Python, i 23 test consumer/regressione Java,
la suite funzionale con PostgreSQL e il restore drill. Trivy ha rilevato
CVE-2026-68497 nella dipendenza Jackson Databind 2.21.4 ereditata dal ramo: la BOM
è stata aggiornata a 2.21.6, senza abbassare il gate HIGH/CRITICAL. Sul commit aggiornato sono PASS la CI dedicata, la suite completa Ingestion
con PostgreSQL, il restore drill e il gate supply-chain (Trivy e chart).
Il risultato VPS rimane da acquisire, distinto dalle prove CI. Il prossimo
intervento dell’operatore è la preparazione/prova candidata; seguono backup
verificato, switch/rollback, prova contro l’immagine effettivamente live e POST
SERVICE governata. Poi approvazione HUMAN in THS, attivazione e filiera fino
alla ricerca UDP. **R-SMOKE e R-INSTALL restano OPEN**.

Contratto, parametri, limiti e procedura:
[R4A_FROZEN_CONFIGURATION_COMPATIBILITY.md](https://github.com/GioNob/ouf-ingestion-runtime/blob/da941666643d83f9f417da85be91fb3b10d4db01/docs/R4A_FROZEN_CONFIGURATION_COMPATIBILITY.md).

## Aggiornamento operatore — 30 settembre: trasporto della sonda

Il primo tentativo su `da941666…` è arrivato al build e poi si è fermato con
`ING_COMPAT_TRANSPORT_CONFIG_REQUIRED`: tutte le tre proprietà activation erano
assenti dal file summary live. Nessuno switch o POST attestazione. Il successivo
`docker exec cat` è una diagnostica non adatta all'immagine distroless, non prova
assenza del token. La lettura del bind mount sul VPS ha confermato file presente,
SERVICE/client Ingestion/tenant/issuer/audience corrispondenti, TTL 277 secondi
all'osservazione e scope `authorization.bundle.read`,
`ouf.ingestion.configuration.attest`, `ouf.internal.object-storage.read`,
`email`, `profile`. Claim decodificati: diagnostica, non autenticazione.

La correzione Ingestion è `160e3391862083bd8779aed69493484f5d2b086d` sulla PR #33. Dieci test Python locali PASS;
CI sulla nuova revisione avviata, risultato non ancora acquisito in questo aggiornamento.
Nessuna modifica Java, DB, IAM/policy o configurazione live.
Il preparatore legge i riferimenti registry HTTPS/token già presenti, controlla
le dipendenze prima del build e crea un file temporaneo solo per la sonda con
Gateway origin, token-file e tenant esplicito (`--tenant-id ouf-lab`). File root:10002,
0440, montato read-only al posto delle proprietà solo nel container usa-e-getta;
nessun token copiato, file rimosso anche in caso di errore della sonda. Directory
auth esistente in sola lettura, rinnovo token conservato. Non aggiungere le
proprietà al summary live né abilitare activation/execution durante questa prova.

L'accesso Semantic esatto resta da provare: nessuno scope Semantic esplicito è
presente nell'output. Il consumer deve attraversare Gateway con owner enforcement;
un 401/403/404 richiede correzione governata di IAM/grant/route/owner, mai accesso
diretto allo storage o attestazione sintetica. La versione resta congelata e
compatibilità non attestata. **R-SMOKE e R-INSTALL OPEN.**

### Correzione dell'ordine di preparazione — 30 settembre

Il tentativo operatore su `160e339…` ha superato il controllo trasporto iniziale,
poi si è fermato con `UnboundLocalError`: la creazione del file temporaneo usava
`current` prima della sua assegnazione. Stop prima del build, del file trasporto
e dei GET consumer; nessuno switch/POST. Le CI precedenti erano tutte verdi,
ma non esercitavano il main del preparatore.

Correzione attuale Ingestion `1eb70c4c3aa6de7e3c3f1ffc4f78ca7b63331872`: il file temporaneo viene creato
solo dopo build, snapshot live verificato e rilettura della versione congelata.
Dodici test Python locali PASS, inclusi due nuovi test del main completo con
operazioni VPS simulate (successo/proof e diniego/cleanup). CI nuova revisione
avviata; il risultato VPS resta da acquisire. Il comando aggiornato, dove presente,
fissa questa revisione e mantiene `--tenant-id ouf-lab`. Non rieseguire i comandi
storici su `160e339…`. R-SMOKE/R-INSTALL restano OPEN e nessuna attestazione positiva.

### Sonda VPS — correzione del contratto d'identità sorgente

Tentativo su `1eb70c4…`: trasporto PASS, build raggiunto, poi
`ING_COMPAT_IDENTITY_POLICY_UNSUPPORTED`. Nessun switch/attestazione;
stop prima dei GET Semantic/asset. Il probe confondeva
`extractionProfile.runtime.rowIdentityBasis=ASSET_AND_ROW_ORDINAL` con
`sourceObjectIdentityPolicy.strategy`, il cui valore normativo è
`MANAGED_DETERMINISTIC` per questa policy. Contratto owner e
`ManagedFileService` Onboarding confermano campi `[$managedRowOrdinal]` e
normalizzazione `normalization://managed-file/asset-row-ordinal-v1`.

Correzione Ingestion `dae05e6d4e8aa5dcd2f1ff2b6642b1ff4356dd37` (PR #33): verifica quella combinazione
esatta, supporta anche NATIVE_KEY/COMPOSITE_NATIVE_KEY con cardinalità/campi
validi; non modifica la configurazione congelata o l'hash. Quattro regressioni
Java aggiunte e fixture managed corretta; dodici test Python PASS, CI Java 21
nuova revisione in corso al momento dell'aggiornamento. Il comando aggiornato,
dove presente, punta alla nuova revisione. Compatibilità live non attestata;
accesso Gateway/Semantic ancora non provato. R-SMOKE/R-INSTALL OPEN.

### Gate storico: 403 alla risoluzione Semantic

L'operatore ha eseguito la sonda `dae05e6…`: trasporto PASS, build raggiunto,
identità superata, `ING_ACTIVATION_GATEWAY_403` durante Semantic preflight,
prima di lettura asset e validazione righe. Nessuno switch/POST compatibilità.
La route versionata `r2b-semantic-reference` usa `ouf.semantic.read`; lo scope
richiesto manca nel token osservato. Assegnazione Keycloak, descriptor SERVICE,
grant effettivo e route live rimangono evidenze distinte, non dedurre ALLOW.

Inventario read-only in PR #33, commit `e4e1f095c53b7ec4819b8d99fcd79769027330bb`: scope corrente,
descriptor/grant del PolicyBundle ACTIVE e scope DEFAULT/OPTIONAL del client
Ingestion nel realm tramite la sessione kcadm esistente. Nessun build, rinnovo
credenziali, GET dei dati, modifica IAM/policy o attestazione. Una sessione scaduta
stampa `KCADM_SESSION_EXPIRED`, non i dettagli/credenziali. Tre test locali PASS
su conteggi senza identità, sessione scaduta e Keycloak solo GET. Prossimo passo:
acquisire questo inventario e preparare correzione governata del prerequisito
mancante; eventuale nuova policy si pubblica solo con conferma HUMAN THS.
R-SMOKE/R-INSTALL OPEN, compatibilità ancora non attestata.

### Inventario Semantic acquisito dall'operatore — 30 settembre

`SEM_TOKEN_SCOPE_PRESENT=false`, TTL 259 secondi alla lettura. Descriptor unico,
scope corretto e SERVICE ammesso. Un solo grant, SERVICE, zero corrispondenze con
client/sub di Ingestion e zero subject-grant corrispondenti, nessun constraint
nel grant esistente. Il bridge Semantic versionato risolve servicePrincipalId da
client_id/azp: il selector esistente non copre il client Ingestion. Non sostituire
il grant preesistente, aggiungere la nuova autorizzazione con il percorso HUMAN
THS preservando il resto del bundle quando la proposta sarà pronta.

Keycloak: `KCADM_SESSION_EXPIRED`; nessuna evidenza ancora su esistenza e binding
DEFAULT/OPTIONAL dello scope. Il runbook già dispone di
`scripts/r4a_refresh_kcadm_session.py`, che usa le variabili bootstrap soltanto
nel container Keycloak senza stamparle. Prossimo intervento: refresh della
sessione amministrativa e ripetizione dell'inventario esistente; nessuna modifica
a scope/client/grant/route, nessun build o POST compatibilità. Seguiranno piano
IAM additivo per lo scope read e proposta di grant SERVICE governata. R-SMOKE e
R-INSTALL OPEN; versione e hash congelati preservati.

### Sessione kcadm ripristinata e piano scope Ingestion

Output operatore: refresh PASS e inventario Keycloak PASS; un solo scope
`ouf.semantic.read`, un solo client `ouf-ingestion`, assegnazioni DEFAULT e
OPTIONAL entrambe false. Token senza scope, TTL 254 secondi all'osservazione;
descriptor SERVICE valido, grant con selector non corrispondente come sopra.
Nessun cambio IAM/policy è stato eseguito da questo inventario.

Prossimo intervento: reconciler scope esistente in sequenza plan/apply/verify,
solo `ouf.semantic.read` come DEFAULT di Ingestion. Preserva le assegnazioni
agli altri scope; non ricrea scope/client, mapper o secret. Nel lab il client
credentials usa gli scope default e il token esistente rimane invariato fino
al normale rinnovo: DEFAULT=true non implica immediatamente token scope=true.
Ripetere l'inventario senza build; non inviare attestazioni o attivare la fonte.

Il grant va aggiunto separatamente, preservando quello esistente: capability
`ouf.semantic.read`, tenant `ouf-lab`, servicePrincipalId `ouf-ingestion`.
La API PermissionProposal supporta UPSERT di un grant e conserva il resto del
PolicyBundle; nessuna proposta è ancora creata. Verificare scadenza, hash,
base ACTIVE e accesso Gateway/delegation prima di proporla; pubblicazione
richiede conferma HUMAN THS, mai SQL o script storico di publish diretto.
R-SMOKE/R-INSTALL OPEN.

### Scope Semantic applicato e proposta grant PENDING — 30 settembre

Operatore: reconciler plan/apply/verify PASS, `ouf.semantic.read` DEFAULT=true e
OPTIONAL=false su `ouf-ingestion`; nessuna drift al verify. Subito dopo il bearer
esistente aveva scope assente e TTL 269 secondi: verifica del token rinnovato
ancora da acquisire, non diagnosticare fallimento del binding da quel solo output.
Inventario policy invariato: descriptor SERVICE valido, un grant non corrispondente.

L'assistente ha usato il plugin OUF MCP con il collegamento `ouf-admin`, prima
ROLES (catalogo preservato), poi GRANTS filtrato `subjectId=ouf-ingestion`:
policyRef :31, hash `sha256:3c043bf01564b1fc0647d8114220b8cd114d0d6d701371e2fd9cb44ff4ec3bc7`,
proiezione vuota; una proiezione configurata non è prova di permessi effettivi.
Creata via `authorization.permissions.propose` una UPSERT di un solo grant:
`grant-r4a-semantic-read-ingestion-20260930`, capability `ouf.semantic.read`,
tenant `ouf-lab`, servicePrincipalId `ouf-ingestion`, subject/organization null,
constraints null, validFrom 2026-09-30T00:00:00Z, validUntil 2027-09-30T00:00:00Z.
Il resto del PolicyBundle e il ruolo admin restano preservati. Nessun publish.

Ricevuta: proposta `44817d9d-e66c-4c02-8ef5-53ca2b2548e9`, revision 0, PENDING,
expiresAt **2026-09-30T08:28:55.717003Z** (10:28:55 Europe/Rome).
[Conferma HUMAN nel THS](https://api.ouf-lab.it/trusted-human/authorization/?proposal=44817d9d-e66c-4c02-8ef5-53ca2b2548e9).
La scadenza della proposta è distinta dalla validUntil del grant. Il chatbot non
conferma; dopo la decisione leggere la ricevuta con `authorization.proposal.read`
(same account), verificare finalPolicyRef e rinnovo token. Se la proposta è scaduta,
non usare il link come conferma valida: preparare una nuova proposta sullo stato
ACTIVE corrente. Compatibilità, prova Semantic/asset e rollout ancora aperti;
R-SMOKE/R-INSTALL OPEN. Nessuna attestazione o attivazione della fonte.

### Conferma HUMAN verificata: policy :32 pubblicata

L'utente ha confermato la proposta nel THS. L'assistente ha letto la ricevuta
attraverso OUF MCP (account ouf-admin): proposta
`44817d9d-e66c-4c02-8ef5-53ca2b2548e9`, revision **1**, **PUBLISHED**,
finalPolicyRef **ouf-lab-authorization:32**. Non ricreare o riconfermare la proposta.
Lo scope DEFAULT resta quello applicato/verificato dall'operatore. Questo chiude
la pubblicazione governata del grant Semantic Ingestion, non la prova consumer.

La candidata corrente PR #33 è `e4e1f095c53b7ec4819b8d99fcd79769027330bb`: tutte le 14 run CI
push/PR risultano completed/success alla verifica, comprese suite consumer,
module/security/recovery e pairwise. Nessun deploy live né attestazione positiva.
Prossimo passo VPS: rileggere inventario, richiedere scope Semantic presente nel
bearer ruotato prima del build e rieseguire la sonda sulla revisione corrente.
L'inventario non equivale a decisione ALLOW: la sonda deve risolvere riferimenti,
leggere l'asset e validare tutte le righe. La sessione amministrativa kcadm non
serve a quelle letture; un suo eventuale expiry nell'inventario resta separato
quando il token e il grant sono già verificati. Conservare versione/hash congelati,
backup e rollback. R-SMOKE/R-INSTALL OPEN.

### Stato corrente — Semantic superato, lettura asset bloccata da 404

Ultimo output VPS: scope Semantic presente nel token ruotato (TTL 296s),
DEFAULT=true, OPTIONAL=false; due grant SERVICE e un selector client corrispondente.
Policy :32 già pubblicata via conferma HUMAN. Sonda e4e1f095…: trasporto PASS,
preflight Semantic superato, poi **ING_EXECUTION_GATEWAY_404** alla lettura
Gateway dell'asset. Nessuna validazione completa delle otto righe, attestazione,
attivazione o switch. R-SMOKE/R-INSTALL restano OPEN; versione/hash congelati
e backup/rollback restano preservati.

Riscontro statico, da confrontare con il runtime: ExecutionGatewayClient legge
GET `/internal/object-storage/v1/content?ref=…`; il binding Gateway
`onboarding-managed-file-read` a 3014f3c… punta a
`/api/internal/v1/onboarding/managed-files/content` su Onboarding. Quel controller
non è nel tree della baseline Onboarding f74c3a9…. La capability owner
`ouf.object-storage.content.read` richiede lo scope `ouf.internal.object-storage.read` del bearer.
Questo non dimostra che la route live coincida con quel binding, né che
l'asset manchi. Non ricaricare il file, cambiare hash o introdurre accesso diretto
allo storage per aggirare il 404.

PR #33 aggiornata a **0dfab1e7b2253fd939088259ea61754d6e56706c**: aggiunto
`scripts/r4a_execution_route_inventory.py`, solo Docker inspect e GET
dell'Admin API APISIX; nessun GET del contenuto asset, build, cambio IAM/route,
deploy o POST attestazione. Stampa conteggi/booleani su route esatta, rewrite,
upstream, scope e revisione owner. Chiave Admin letta dal bind config.yaml
(oppure file esplicito), passata al curl via stdin, mai argv/output o file temporanei.
Layout chiave non letterale/ambiguo blocca senza stampare il valore.
Diciannove test Python locali PASS, inclusi parser fail-closed, GET esatto,
formati Admin API e assenza chiave da argv/output. CI nuova revisione avviata,
non ancora acquisita. Prossimo passo: inventario live, poi correzione governata
del binding/owner effettivamente osservato.

### Inventario route: chiave esplicita nel comando

Output VPS acquisito: `EXEC_READ_OWNER_BASELINE_REVISION_MATCH=true`, poi
`APISIX_ADMIN_KEY_LAYOUT_UNSUPPORTED`. La lettura dell'Admin API non è stata
eseguita: non sono ancora disponibili evidenze sulle route attive. La baseline
Onboarding f74c3a9… è invece confermata dall'immagine live.

Il parser ristretto del bind config.yaml non accetta il layout osservato.
Usare l'opzione già disponibile `--admin-key /opt/ouf/secrets/apisix-admin-key`:
è lo stesso riferimento del rollout Gateway versionato
`scripts/r4a_semantic_rdf_route_rollout.py` a 3014f3c….
La presenza del file sul VPS sarà verificata dalla lettura, non è stata dedotta
dalla sola fonte GitHub. La chiave resta in memoria/stdin, non in argv/output;
il layout YAML non viene interpretato. Nessuna modifica a configurazione, token,
route, policy, asset, immagini live o attestazioni.

Revisione inventario invariata: `0dfab1e7b2253fd939088259ea61754d6e56706c`.
Tutte le 14 run CI push/PR ora completed/success. I 19 test Python locali erano
già PASS. Il blocco consumer resta `ING_EXECUTION_GATEWAY_404`; compatibilità,
R-SMOKE e R-INSTALL restano aperti.

### Gate corrente confermato — endpoint owner assente nella release live

Output VPS: baseline owner=true, una route GET esatta, rewrite al vecchio
endpoint content=true, upstream Onboarding=true, nessun upstream_id,
OIDC=true, required scope match=true, rewrite=true; inventario completo
in sola lettura. La route invia la richiesta al controller assente nel tree
f74c3a9…. Non vi è evidenza che l'asset sia perso. Il preflight Semantic
è già superato; otto righe, compatibilità live, attestazione Ingestion e
filiera Ingestion → UDP → search rimangono aperti.

Correzione della precedente nota sullo scope: `ouf.object-storage.content.read`
è il nome della capability owner, mentre il descriptor richiede proprio
`ouf.internal.object-storage.read`, già presente nel token. Questa distinzione
non richiede un cambio IAM. Il backend dovrà comunque effettuare la sua
decisione effettiva di autorizzazione dopo il ripristino dell'endpoint.

I rami intake (5d770df…) e identity live (f74c3a9…) divergono dal parent
21de5f2…; il rollout identity ha lasciato fuori l'implementazione intake.
Preparata **Onboarding PR #39**, branch
`codex/r4a-onboarding-managed-identity-integration`, commit
**6340d5bf120e09b47c32177656e2c377a4c03640**, con entrambi i parent nella storia. Ripristina
intake/picker/delegation e conserva gate UDP e PermissionProposal publication.
Cinque file modificati da entrambi i rami integrati con merge a tre vie;
conflitti risolti sulle tre superfici sessione HUMAN e sulle due validazioni,
entrambe mantenute. Il test storico che attivava un managed DRAFT incompleto
resta sostituito dalla regressione fail-closed già introdotta nell'intake.

Tutte le **quattro CI push/PR completed/success** alla verifica: module e
browser. La CI del container verifica GET owner anonimo 403 con
ONB_AUTHORIZATION_DENIED oltre alla readiness, quindi rileva anche una
release priva del controller. Nessun deploy VPS effettuato.
Procedura specifica nel repo Onboarding:
`docs/R4A_MANAGED_IDENTITY_INTEGRATION.md`. Non eseguire il vecchio rollout
picker: riguarda un'altra fase e il suo controllo git non risolve questo caso.

Il DB live è già V31, ma V30/V31 mancano nel tree identity f74c3a9….
La candidata conserva i file originali intake: occorre confrontare ogni
script/checksum con la storia Flyway effettiva, non dichiarare migrazioni
invariate dal solo confronto con quel tree. Preflight Semantic versionato a
**721d81a25c194615eb0ddf48fca8b9bd0a281ef9**, quattro test locali PASS e test aggiunto alla CI:
`scripts/r4a_managed_identity_release_inventory.py`. Solo git read/ancestor,
Docker inspect e SQL BEGIN READ ONLY/ROLLBACK; verifica entrambe le storie,
baseline, env/mount read-only, metadati file per UID/GID 10003 e migrazioni
esatte già applicate. Stampa conteggi/booleani; nessun valore o identità.
Un mismatch blocca i prerequisiti della release. La CI Semantic nuova è in
corso; CI della candidata Onboarding già verde.

Acquisire questo inventario prima di build/candidato fermo e switch con
backup recuperabile. Conservare i rollback e i dump già registrati,
versione/hash congelati e attestazione UDP esistente. La prova isolata e
il gate d'identità devono restare insieme alla lettura managed. Nessun
restore automatico del DB, reupload, cambio hash o aggiramento diretto
dello storage. R-SMOKE/R-INSTALL OPEN.

### Preflight release acquisito PASS — candidata da costruire e lasciare ferma

L'operatore ha eseguito il preflight sulla candidata Onboarding
6340d5bf120e09b47c32177656e2c377a4c03640: entrambe le storie preservate,
31 migrazioni tutte corrispondenti al DB, baseline live attiva, quattro env
staging presenti, mount credenziali read-only e file privati leggibili,
gateway/token managed presenti, gateway/token identity presenti e leggibili.
RELEASE_PREREQUISITES=PASS, LIVE_UNCHANGED=true. Nessun nuovo prerequisito
IAM/configurazione va introdotto per riparare l'endpoint mancante.

Automazione Semantic aggiornata a **6fc4ed9b4e74cb038250c609f3688b4276aadb31**:
`scripts/r4a_prepare_managed_identity_candidate.py`. Fissa la candidata
Onboarding alla revisione verde; ripete l'inventario prima e dopo la build da
git archive, verifica label immagine e contratto di avvio, e blocca se live,
env, mount, migrazioni o impostazioni Docker cambiano. Crea solo il container
`ouf-onboarding-r4a-managed-identity-candidate`, in stato created,
restart=no, alias ouf-onboarding, UID/GID 10003, con env/mount/log del live.
Non lo avvia, non cambia il live, non accede al bucket e non invia attestazioni.

Un candidato già presente è riutilizzato solo se fermo e identico; eventuale
drift blocca senza sostituzione. Il readback deve confermare l'ID creato,
immagine, env, mount, rete e stato. In caso d'errore ripulisce solo il proprio
container ancora fermo e non tocca container sostituiti da altri operatori.
Il file env temporaneo è privato e rimosso nel finally.

Manifest privato root 0600:
`/etc/ouf/deploy-snapshots/onboarding-managed-identity-release.json`;
contiene lo snapshot Docker live (anche env segreti), candidate ID e image ID.
Non stamparlo, condividerlo o committarlo. Le build log sono in una directory
root 0700 sotto /etc/ouf/deploy-snapshots, il solo percorso viene stampato; conservate su errore.
Lo stato esistente non viene sovrascritto; deve corrispondere al live/candidato.
Non modificare `identity-images.json` e non eliminare i rollback precedenti.

Otto test Python locali PASS e discovery CI estesa a entrambi gli script:
checksum/migrazioni, mount privati, preparazione completa, drift durante build,
cleanup per ID e candidati preesistenti. CI preparatore avviata, non ancora
acquisita; le quattro CI della candidata Onboarding restano completed/success.
Prossimo passo: acquisire BUILDING → CANDIDATE PASS/STOPPED; poi backup
recuperabile e switch con verifica di readiness, endpoint e Flyway invariata.
Il preparatore non crea backup e non esegue lo switch. Compatibilità consumer,
attestazione e HUMAN approval/activation restano gate successivi.
Versione/hash congelati, attestazione UDP e backup/rollback preservati;
R-SMOKE/R-INSTALL OPEN.

### Correzione percorso privato del preparatore — stop prima del build

Tentativo VPS su 6fc4ed9…: OWNER_STAGE_DIRECTORY_UNSAFE, prima di git archive,
build, candidato o file di stato. Il preflight precedente resta PASS; non
dedurre drift del runtime, IAM o migrazioni da questo blocco.

Il preparatore aveva usato /opt/ouf/r4a-stage come parent per stato contenente
env segreti: quel percorso di staging condiviso non soddisfa il requisito
root-only. Correzione **76073d25ceff9f8a54684fee214071c564423b83**: usa la directory già prevista dai rollout
Onboarding `/etc/ouf/deploy-snapshots`, richiede directory reale (non symlink),
owner root e modo esatto 0700. Non modifica permessi/owner del vecchio staging.
Stato ora `/etc/ouf/deploy-snapshots/onboarding-managed-identity-release.json`,
root 0600; log ed env temporanei nelle sottodirectory private della stessa root.
Non esiste uno stato precedente creato dal tentativo bloccato da spostare.

Nove test locali PASS, inclusa regressione che blocca directory user-owned,
accessibile ad altri o symlink prima di inspect/build. CI della correzione
avviata; candidata Onboarding invariata 6340d5bf… con CI già verde.
Il comando corrente è aggiornato alla correzione. Ancora nessun build o
candidato fermo attestato dall'operatore, nessuno switch/POST. Versione/hash,
live, IAM, route, asset e rollback precedenti restano invariati.
R-SMOKE/R-INSTALL OPEN.
