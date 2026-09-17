# Roadmap OUF rispetto ai PET della baseline v1.7

Data di verifica: 16 settembre 2026. Stato: proposta esecutiva basata sui repository, non attestazione di conformità finale.

La priorità è completare la catena eseguibile e autorizzata tra i moduli. I repository contengono una parte consistente del dominio e dei test, ma rimangono codice di integrazione, capability, superfici umane e criteri di accettazione da realizzare. Non è corretto descrivere il lavoro residuo come sola configurazione IAM o collaudo di produzione.

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

Esaminati i sei repository OUF trovati sotto GioNob: alberi completi, codice e wiring delle aree critiche, workflow CI, test, contratti e documenti di tracciabilità. Authorization è correttamente co-locata in Onboarding: la mancanza di un repository autonomo non è un gap. Non sono stati modificati repository o PET durante questo audit, né rieseguite le suite: gli esiti CI sono quelli letti da GitHub sui commit indicati.

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

**SEM-01 — INTEGRAZIONE:** correggere il live pairwise e successivamente provarlo contro Gateway e identità conformi. Agganciare Onboarding/Ingestion/UDP agli exact SemanticReference; non basta il test Authorization basato su ispezione di schema e stringhe del resolver. PET §§133–136, 160.7, 160.15.

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
| R3 | Operational Awareness completa, priorità prodotto | R1 e R2a/b | OUF-OA-001…006 e OUF-OA-CN-001…005: fault offline, retry/dedup/recovery, misfire, retention, partial/deny, medesimo owner via MCP/API |
| R4a | Catalogo capability e THS comune | R1/R2; può procedere con R3 | Onboarding/file, serving e proposal esposti via Gateway/MCP; decisioni umane e protected logs confinati a THS browser |
| R4b | Residui di dominio | R2; per moduli indipendenti | UDP PARTIAL chiusi; GIS previsti; Semantic job/limits/upstream lifecycle e Onboarding discovery automatica completi |
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

R0 e R1a sono consegnati; R1b ha ora implementazione centrale e controlli owner nei percorsi descritti in `R1B_OWNER_ENFORCEMENT_EVIDENCE.md`. Il prossimo incremento verticale è **R2a: Onboarding→Ingestion reale**, con bundle ACTIVE, preflight esatto e avvio automatico file/PULL. I controlli owner implementati devono essere mantenuti nel percorso; l'accettazione completa dei restanti domini/proiezioni e dell'identità reale rimane tracciata in AUT-03/AUT-04, senza riaprire decisioni già risolte.


## Avanzamento R1b — 17 settembre 2026

Implementazione centrale Authorization e cache consegnata; evidenze in `R1B_AUTHORIZATION_EVIDENCE.md`. AUT-01 chiuso per l'API amministrativa verificata in laboratorio. AUT-02 e AUT-03 restano parziali per enforcement e proiezioni owner-specific, con audit esplicito in `R1B_ENDPOINT_COVERAGE_AUDIT.md`. AUT-04 resta il gate IAM/THS reale. Lo stato `IMPLEMENTED_WITH_INTEGRATION_GAPS` non equivale ad accettazione completa del PET o a chiusura di tutti i requisiti della fase.

## Follow-up R1b: enforcement owner — 17 settembre 2026

Corretti tutti i percorsi Semantic mediante matrice capability fail-closed, le proiezioni UDP incluse query graph/related/spatial, la Operational Awareness Ingestion e i protected log Onboarding/Ingestion. Evidenze immutabili e PR: `R1B_OWNER_ENFORCEMENT_EVIDENCE.md`. AUT-02 soddisfa il criterio SDK/adapter/conformità e backend deny; AUT-03 conserva l'accettazione completa delle proiezioni owner nei restanti domini e canali. AUT-04 resta il gate IAM/THS reale. I test di modulo non chiudono R2/R6.
