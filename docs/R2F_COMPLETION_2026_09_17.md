# R2f — completamento del percorso di revisione

Stato: implementazione disponibile nelle cinque PR R2f; CI finale verificata, **43 controlli integrati PASS**. L’accettazione operativa resta distinta dalla CI. Questo rapporto aggiorna, senza cancellarle, le lacune registrate in `R2F_REVIEW_2026_09_17.md`.

## PET consultati

Restano vincolanti Reality Baseline v1.7, Blueprint L0, Matrix, Supersession Notice e tutti i sette PET identificati in `OUF_REALITY_BASELINE_V1_7_REFERENCES.json`. Consultazione mirata in questo incremento: UDP §§15–24, 29–31; Onboarding §§92–94 e THS; Ingestion §§143.2–144; Semantic Registry: proposte, TBox e pubblicazioni versionate; Authorization: default deny, resource/data-label e HUMAN; Gateway: owner e profilo OPEN/ANONYMOUS; MCP: proposta e handoff senza conferma umana. Non si attesta la chiusura integrale dei PET.

## Comportamento consegnato

| Area | Comportamento e prova |
|---|---|
| Proprietà non geometriche | Confronto autorizzato di tutti i contributi; scelta umana su evidenza e regola esatte, motivazione, audit append-only, nuova revisione canonica. Retry idempotente; revisione, contributi o policy superati impediscono la decisione. Le altre proprietà rimangono leggibili nella nuova revisione. |
| Ruoli geometrici | `PRIMARY` mantiene la geometria predefinita; ruoli nominati hanno puntatori distinti e sono esposti come `geometries`, ciascuno con la propria autorizzazione e provenienza. Il profilo pubblicato descrive un ruolo per contributo; contributi diversi possono popolare ruoli diversi sullo stesso oggetto. |
| Validità e ordine | Intervalli non validi sono rifiutati. Contributi scaduti o tardivi sono conservati senza avanzare la vista corrente; contributi futuri sono pianificati alla propria validFrom. Query spaziali e identità escludono geometrie scadute. Le osservazioni della stessa forma conservano il timestamp più recente senza perdere lo storico. Timestamp pari/assenti con forme discordanti richiedono revisione. |
| Decisione geometrica | Scelta della revisione, ripresa del job e allineamento fra proprietà canonica e geometria di serving. Anche una nuova forma della fonte precedentemente scelta riapre il conflitto: la scelta non diventa priorità permanente. |
| THS | Superficie in Onboarding: `/trusted-human/r2f`. Code dei conflitti visibili, confronto di proprietà, sovrapposizione geometrica con zoom/inquadratura, distanza minima, aree, equivalenza topologica e provenienza. Scelta esplicita con motivazione; errori di autorizzazione e stale evidence mostrati senza conferme fittizie. |
| Sicurezza della revisione | Gateway verso UDP; comandi HUMAN e non tool MCP. Cookie Secure/HttpOnly/SameSite=Strict, token CSRF legato a subject/tenant, controllo dell’origine e risposte no-store. I caller automatici autorizzati possono leggere evidenze ma non ricevono il token di sessione umano. |
| Proposte Access | Dal FileProfile immutabile nascono gap idempotenti con hash/provenienza, chiavi composite, colonne FK e direzione strutturale. Candidato adottato non equivale a pubblicato. Solo il risultato autorizzato del Registry può attestare PUBLISHED. Il riferimento selezionato conserva predicate/domain/range/direction e publication binding; il mapping richiede comunque la normale approvazione Onboarding. |
| Formati equivalenti | La prova integrata ricarica gli stessi attributi/geometria in Shapefile e GeoPackage, riusa l’identità canonica e conserva le relazioni. Access MDB/ACCDB mantiene chiavi composite e identità anche riordinando le righe. La prova riguarda le fixture descritte, non ogni possibile conversione GIS. |

Le API nuove sono specificate nei repository owner. Gateway espone namespace limitati per code/confronti/decisioni e il comando di proposta `/api/onboarding/v1/access-semantic-proposals`. Il Gateway non decide identità, authority o semantica.

## Persona, superficie e risultato

Persona: operatore autorizzato alla revisione. Obiettivo: riconoscere un conflitto, confrontare contributi e conservare quello verificato senza introdurre duplicati né regole implicite. Superficie: THS ospitata in Onboarding, con owner API UDP attraverso Gateway. Risultato osservabile: riferimento di decisione immutabile, revisione coerente e persistente, nessuna modifica degli altri valori per una scelta scalare.

Il test browser Chromium esegue rendering geometrico, zoom, invio della scelta esatta con token CSRF, blocco dei dati non autorizzati, gestione di revisione superata e rendering testuale di valori potenzialmente ostili. Le risposte API del test browser sono fixture dichiarate. La prova fra quattro JVM esegue invece servizi, approvazioni, materializzazione, API HTTP, PostgreSQL/PostGIS e MinIO reali; identità, Gateway HTTP e decisioni degli attori sono fixture esplicite escluse dai JAR di produzione.

## Collaudo finale ed evidenze

I riferimenti definitivi ai commit e alle workflow sono riportati in `evidence/r2f-human-review-integration.json`. Tutte le workflow elencate sotto hanno esito SUCCESS letto da GitHub. Le vecchie prove verdi non vengono attribuite ai nuovi commit. I test owner coprono entrambe le scelte geometriche, ruoli, validità, ordini temporali, policy obsolete, riimportazioni, label, attori automatici e immutabilità.

| Repository / prova | Head verificato | Workflow |
|---|---|---|
| Onboarding: modulo e Chromium THS | `7f051e69dadf54814293158ea480375d3e90580f` | [modulo](https://github.com/GioNob/ouf-source-onboarding/actions/runs/35233121749), [browser](https://github.com/GioNob/ouf-source-onboarding/actions/runs/35233121754) |
| UDP: modulo, CRS, SDK | `862a975e28dc681faa6482dba1feef0acd2a3988` | [modulo](https://github.com/GioNob/ouf-udp-object-resolution/actions/runs/35233383718), [CRS](https://github.com/GioNob/ouf-udp-object-resolution/actions/runs/35233383788), [SDK](https://github.com/GioNob/ouf-udp-object-resolution/actions/runs/35233383819) |
| Gateway: compilazione e policy | `a75a932d6c6f43025a963f7e7f8da8cec9e7aa0b` | [CI](https://github.com/GioNob/ouf-api-gateway/actions/runs/35233140373) |
| Ingestion: modulo e R2f integrata | `1b912bd58b851f6c4275d293d413293f86a948a6` | [modulo](https://github.com/GioNob/ouf-ingestion-runtime/actions/runs/35233389153), [43 controlli R2f](https://github.com/GioNob/ouf-ingestion-runtime/actions/runs/35233389465) |

Le regressioni Ingestion SDK/R2a/R2b/R2c/R2e sono anch’esse SUCCESS sullo stesso head: 35233389160, 35233389195, 35233389379, 35233389089, 35233389168. Il runtime Semantic della prova è fissato a `04cca9fa1194d6c20dbbaf2ab8149322eb49b923`. `runtimeCommit` nell’evidenza identifica il merge temporaneo del job PR, non un merge in main. Le cinque PR restano draft in attesa del gate operativo.

## Gate di accettazione residuo

Manca il collaudo dell’operatore in un ambiente con IdP, adapter della sessione browser, HTTPS e APISIX effettivamente configurati. Il browser di produzione deve usare lo stesso origin del Gateway; UDP deve avere `ouf.ths.origin` corrispondente e sessioni aderenti alla topologia di deployment. La fixture HTTP inoltra esplicitamente il cookie Secure per provare il comando owner: non attesta una sessione browser TLS reale.

Questo non rinvia l’implementazione della revisione R2f a R4a: la superficie e i comandi sono ora presenti. Non si attestano invece identità esterna, grigliati IGM reali, precisione territoriale o accettazione dell’operatore. La roadmap mantiene R3 dopo l’accettazione di R2f; queste prove non autorizzano a cancellare tale gate.
