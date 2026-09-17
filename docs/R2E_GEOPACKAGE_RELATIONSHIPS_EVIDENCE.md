# R2e — GeoPackage, oggetti per feature e relazioni telecamere↔armadi

Autorità normativa: Reality Baseline Package v1.7 e integrazioni GIS concordate nella roadmap. Sono stati letti tutti i sette PET e i documenti L0; [regola di allineamento degli sprint](OUF_SPRINT_PET_ALIGNMENT.md) e [manifest delle fonti](OUF_REALITY_BASELINE_V1_7_REFERENCES.json). L'incremento mantiene la ripartizione Onboarding → Ingestion → UDP; non introduce un nuovo runtime o una nuova autorità semantica.

## Risultato e superficie umana

Persona: operatore comunale che configura una fonte GeoPackage e lettore autorizzato che consulta telecamere e armadi. Obiettivo: scegliere layer/chiavi/attributi/geometria, approvare il profilo e verificare gli oggetti e i collegamenti acquisiti, anche dopo un aggiornamento.

Onboarding restituisce l'inventario dei layer, CRS e geometrie, colonne, campione e candidati a chiave; richiede layer e chiavi espliciti. Il draft conserva le decisioni, completate dal profilo eseguibile e dalla scelta CRS R2d. Conferma umana, attestazione di compatibilità e pubblicazione congelano il bundle.

Ingestion verifica dimensione e checksum, legge il layer approvato in sola lettura e produce un record per feature. L'identità usa fonte, layer e chiavi approvate, senza dipendere da ordine del file, hash dell'asset o fid non scelto come chiave. Null e geometria CRS-tagged sono conservati. RAW per feature, NORMALIZED con provenienza e CURATED usano il percorso Lake esistente.

UDP materializza gli oggetti e le geometrie con i profili storici verificati. Telecamera→armadio usa la chiave target dichiarata; un target assente produce issue persistente e viene riconciliato al suo arrivo con la regola originale. Più target restano in revisione, senza scelta arbitraria. Cambiare riferimento ritira l'edge precedente; contributi/revisioni restano disponibili. Il retry della stessa evidenza non duplica revisioni.

La superficie attuale è costituita dalle API owner e dagli stati persistiti. `relationships?direction=OUTBOUND` e `direction=INBOUND` permettono la navigazione nei due sensi con gli stessi ID edge. Tenant, oggetto di partenza, relazione e altro oggetto sono autorizzati prima della serializzazione. L'originale è nella proprietà geometrica mappata, con controllo `urban.geometry.read` anche in current/history/search; `canonicalGeometry`, `geometry` e `geometryProvenance` conservano il contratto R2d. Il browser cartografico integrato rimane R4a, la remediation completa R3.

## Implementazione

| Owner | PR | Contratto operativo |
|---|---|---|
| Onboarding | [#16](https://github.com/GioNob/ouf-source-onboarding/pull/16) | [Profilazione e decisioni](https://github.com/GioNob/ouf-source-onboarding/blob/main/docs/R2E_GEOPACKAGE.md) |
| Ingestion | [#26](https://github.com/GioNob/ouf-ingestion-runtime/pull/26) | [Adapter, identità e limiti](https://github.com/GioNob/ouf-ingestion-runtime/blob/main/docs/R2E_GEOPACKAGE.md) |
| UDP | [#29](https://github.com/GioNob/ouf-udp-object-resolution/pull/29) | [Binding, riconciliazione e serving](https://github.com/GioNob/ouf-udp-object-resolution/blob/main/docs/R2E_GEOPACKAGE_RELATIONSHIPS.md) |

Le migrazioni ammettono formato/media type GeoPackage e aggiungono task di riconciliazione e supporti correnti. Handoff e profilo originale sono protetti da immutabilità; gli aggiornamenti riguardano scheduling e stato corrente. SQLite JDBC è fissato a 3.53.4.0 e incluso nel packaging e nei gate del modulo. La parità del reader fra profiler e adapter è verificata nella CI di integrazione.

## Prove riproducibili

La CI R2e di Ingestion avvia **quattro JVM owner reali** (Semantic, Onboarding, Ingestion, UDP), PostgreSQL/PostGIS e MinIO. La pubblicazione semantica e quella di Onboarding passano dai rispettivi servizi di governance. Instradamento Gateway, credenziali/identità e input sono fixture dichiarate; non vengono usati come prova di un deployment operativo completo.

Lo scenario contiene **25 verifiche PASS**: pubblicazione e referenze esatte; due feature→due telecamere; riferimento inizialmente mancante; armadio acquisito successivamente; navigazione reciproca; originale/canonico; ricaricamento con fid/ordine/coordinate/riferimento modificati senza duplicare gli oggetti; ritiro dell'edge precedente; storico geometrico, bundle storico e lineage; rifiuto di lettura anonima e del workload di scrittura; restart e cinque RAW per feature verificati. Il registro JSON conserva elenco esatto, SHA e run/artifact finali.

Le suite dei moduli aggiungono casi negativi per layer/chiavi/hash/CRS, header/WKB/dimensioni/limiti, binding di label/mapping/chiave/strategia, ambiguità, idempotenza, immutabilità e omissione delle relazioni riservate. Le suite R2a/b/c, SDK e CRS/grigliati R2d restano gate di regressione.

Sono stati corretti e conservati come evidenza diagnostica i failure intermedi: scheduler di riconciliazione attivo nei test senza runtime, vincolo database sul vecchio elenco di media type, aspettativa errata del test sul campo dell'originale geometrico e fixture di materializzazione priva della lista bitemporale obbligatoria. Gli esiti intermedi non vengono presentati come run finali verdi.

## Limiti residui

- Simple features 2D, CRS EPSG esplicito; file fino a 10 MiB, 64 layer, 256 colonne, 10.000 feature/layer; geometria binaria fino a 1 MiB. Vuoti, Z/M, curve e codifiche estese sono rigettati, senza conversioni o riparazioni implicite. I formati/casi ulteriori restano R4b.
- La stabilità della chiave nel sistema sorgente è una decisione di configurazione; l'unicità nel file non la garantisce. Il profilo richiede la scelta esplicita e controlla null/duplicati.
- Riconciliazione periodica limitata a 10 task per tick; il backlog può aumentare la latenza. Le ambiguità restano in revisione; UI e remediation complete sono R3/R4a.
- Lo scenario R2e usa EPSG:4326 senza trasformazione territoriale. I test 6708, assi, trasformazioni e grigliato sintetico restano quelli R2d. **Nessun grigliato IGM reale è stato reperito, licenziato o collaudato territorialmente in questo incremento.**
- IAM, Gateway/THS operativi e acceptance cross-module rappresentativa restano i gate già tracciati. Nessun gruppo PET generale è chiuso dalla sola CI R2e.

Prossimo incremento della roadmap: **R3 — Operational Awareness**, mantenendo i gate R4a/R4b e di ambiente.

## Commit e CI finali

| Owner | Head verificato | Merge su main |
|---|---|---|
| onboarding | `808b717ed4bddeb7e6b22ec42dfb32095464ed2c` | `5ebb9bc9a8fc9d4dbb9b9dd23dd3bacdeb47e85a` |
| ingestion | `64a7895471826f3e76de4a8cd5c0cb38827381e8` | `a8ba969a5a0e20e9c53977d2875094ce82802f9d` |
| udp | `933443ca5484cd4ca9b08d67227860938148ea1b` | `6285b733c49b89cb6d3382abe8dc469f8a0e8b1b` |

| CI sul commit finale | Esito |
|---|---|
| [ouf-source-onboarding / Source Onboarding module CI / 35207262543](https://github.com/GioNob/ouf-source-onboarding/actions/runs/35207262543) | PASS |
| [ouf-ingestion-runtime / Shared Authorization SDK pairwise / 35208061119](https://github.com/GioNob/ouf-ingestion-runtime/actions/runs/35208061119) | PASS |
| [ouf-ingestion-runtime / R2c governed publication to historical serving / 35208061289](https://github.com/GioNob/ouf-ingestion-runtime/actions/runs/35208061289) | PASS |
| [ouf-ingestion-runtime / R2b source to authorized serving / 35208061216](https://github.com/GioNob/ouf-ingestion-runtime/actions/runs/35208061216) | PASS |
| [ouf-ingestion-runtime / R2a Onboarding automatic activation / 35208061012](https://github.com/GioNob/ouf-ingestion-runtime/actions/runs/35208061012) | PASS |
| [ouf-ingestion-runtime / Ingestion Runtime module CI / 35208061084](https://github.com/GioNob/ouf-ingestion-runtime/actions/runs/35208061084) | PASS |
| [ouf-ingestion-runtime / R2e GeoPackage features and governed camera-cabinet relations / 35208061013](https://github.com/GioNob/ouf-ingestion-runtime/actions/runs/35208061013) | PASS |
| [ouf-udp-object-resolution / Shared Authorization SDK pairwise / 35207985143](https://github.com/GioNob/ouf-udp-object-resolution/actions/runs/35207985143) | PASS |
| [ouf-udp-object-resolution / R2d governed CRS and grid execution / 35207985156](https://github.com/GioNob/ouf-udp-object-resolution/actions/runs/35207985156) | PASS |
| [ouf-udp-object-resolution / UDP Object Resolution module CI / 35207985182](https://github.com/GioNob/ouf-udp-object-resolution/actions/runs/35207985182) | PASS |

Il processo della CI pull_request usa il merge commit sintetico GitHub: `6aa2124445403ab75b932225ef96695d00896508`; la head Ingestion è `64a7895471826f3e76de4a8cd5c0cb38827381e8`. Il registro mantiene entrambi. I digest degli artifact sono metadata GitHub, non checksum ricalcolati scaricando gli archivi.
