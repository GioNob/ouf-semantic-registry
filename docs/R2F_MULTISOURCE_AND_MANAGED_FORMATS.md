# R2f — Identità multi-fonte, conflitti e formati gestiti

Stato: **IN CORSO — non accettato, non equivalente alla chiusura dei requisiti PET**.

Il committente ha approvato il completamento della risoluzione di identità e dei conflitti per **qualunque classe di oggetto**, il supporto Shapefile ZIP e l'importazione Access di tabelle e dati. Chiavi e relazioni Access costituiscono evidenza per proposte semantiche, mai pubblicazioni automatiche. I dehor sono un caso di collaudo, non una specializzazione del motore.

## Fonti normative e responsabilità

Fonti: Reality Baseline Package v1.7, riferimenti identificati in `OUF_REALITY_BASELINE_V1_7_REFERENCES.json`. Applicare L0, Matrix v1.7 e Supersession Notice; il codice non sostituisce il PET.

| Owner / PET | Requisito applicabile | Intervento / evidenza richiesta |
|---|---|---|
| UDP v1.3 §§21–24 | ATTRIBUTE_WEIGHTED, SPATIAL e COMPOSITE; candidate generation bounded; soglie/evidence versionate | Policy pubblicata, score riproducibile, blocco delle ambiguità, test su classi diverse |
| UDP v1.3 §§15–20 | Authority per proprietà/geometria/periodo; nessuna prevalenza per ordine di arrivo non approvata | Contributi conservati, current coerente, decisione umana persistente |
| UDP v1.3 §§25,31 | Identità distinta dall'authority; merge/override protetti | Impatto e revisione; nessuna approvazione tramite service identity |
| UDP v1.3 §29 | CRS/tolerance/ranking/margin espliciti; prossimità non sufficiente salvo policy | Metriche spaziali verificabili; equivalenza distinta dal conflitto |
| Onboarding/THS v1.6 §§92–94 | Profiling deterministico, draft, classificazioni e mapping approvati | FileProfile multi-layer/multi-tabella; preview e scelte immutabili |
| Ingestion v1.3 §§143.2,144 | Shapefile ZIP; sorgenti tabellari gestite; identità per record | Adapter selezionato dal bundle; integrità, limiti, replay e source identity |
| Semantic Registry v1.3 | TBox e pubblicazioni versionate, proposte non autoritative | Riutilizzo di classi/relazioni esistenti; gap sottoposti al workflow owner |
| Authorization v1.5 | Default deny; prove umane, policy e label server-side | Deny test, nessun dato protetto nelle spiegazioni non autorizzate |
| Gateway v1.5 | Accesso governato ai backend owner | Binding delle nuove superfici; nessun accesso diretto a storage/database |
| MCP v1.4 | Proposte e spiegazioni tipizzate; THS separata | Nessun tool di conferma umana; nessun nuovo runtime LLM interno |

Access è un'estensione richiesta dal committente nel percorso INTERNAL_MANAGED, non un formato esplicitamente nominato nei paragrafi GIS. La compatibilità di ciascun formato/versione deve essere provata, non dedotta dalla presenza della libreria.

## Accettazione richiesta

- Identificativi diversi ma attributi/geometrie compatibili producono MATCH solo secondo policy approvata.
- Candidati vicini nel punteggio, evidenza insufficiente o insieme troppo ampio producono REVIEW_REQUIRED; nessuna selezione arbitraria.
- I valori mancanti non fanno rinormalizzare verso l'alto il punteggio.
- Policy, normalizzazione, evidenze, soglie e decisione sono riproducibili dai riferimenti storici.
- Chiavi certe e binding noti mantengono continuità; le strategie non dipendono da nomi di dominio hard-coded.
- Geometrie con ruoli/validità diversi sono modellate distintamente; quelle realmente discordanti aprono un conflitto.
- Importazioni in ordine inverso non annullano le decisioni umane; originale, revisioni e lineage restano disponibili secondo autorizzazione.
- Il confronto umano presenta soltanto i casi che richiedono decisione, con metriche e rappresentazione cartografica.
- La decisione sul singolo caso non diventa implicitamente una regola per le importazioni future.
- Shapefile ZIP verifica componenti coerenti, encoding, CRS, geometrie e limiti prima dell'emissione dei record.
- Dataset equivalenti in GeoPackage e Shapefile producono gli stessi oggetti/relazioni canonici tramite mapping approvato; la provenance delle fonti resta distinta.
- Access consente selezione delle tabelle, lettura di tipi e dati, chiavi composite e relazioni dichiarate come proposte.
- Access non esegue VBA, macro, query salvate, espressioni o risoluzione di tabelle collegate verso file/reti esterni.
- File corrotti, protetti o non supportati producono errore esplicito; niente inferenze di contenuto o conversioni silenziose.
- Contratti, migrazioni e test di integrazione owner devono passare; CI tecnica e accettazione umana restano distinte.

## Rettifica del limite R2e

R2e certifica GeoPackage e relazioni dichiarate per chiave. Non certifica ATTRIBUTE_WEIGHTED/COMPOSITE né la riconciliazione governata di geometrie tra fonti. Il percorso geometrico di quella baseline aggiorna la geometria corrente all'ultima materializzazione valida: questo è uno scostamento da UDP §15.1 quando manca una policy che autorizzi tale prevalenza. Le precedenti CI verdi non chiudono tale requisito.

## Registro di avanzamento

| Area | Stato |
|---|---|
| Score pesato e integrazione nella risoluzione UDP | Score puro e integrazione PostgreSQL/PostGIS verificati in CI; validazione prima dell’approvazione e replay della decisione umana aggiunti |
| Authority geometrica, ruoli e workflow umano | Da completare |
| Shapefile ZIP | Lettore, profiler, adapter e controlli di integrità implementati; fixture punti/poligoni con buchi; percorso completo fra owner aperto |
| Access, chiavi e relazioni | Lettore/profiler/adapter, chiavi composite e metadata/suggerimenti semantici implementati; pubblicazione semantica governata integrata ancora aperta |
| Tracciabilità e collaudo integrato | Aperto |

Nessun grigliato IGM reale, collaudo territoriale o accettazione operativa è attestato da questo documento.


## Implementazione verificabile e limiti puntuali

- UDP: segnali EXACT/TEXT/NUMBER/DISTANCE/OVERLAP, pesi normalizzati, soglie HIGH/review, margine, blocco per attributi e/o raggio, massimo 100 candidati. Evidenze mancanti pesano zero. Oltre il limite si apre revisione, senza selezione parziale. Lo score è evidenza, non authority.
- Le metriche spaziali usano la geometria trasformata secondo R2d. I candidati senza geometria possono concorrere sugli attributi quando non è richiesto un filtro geografico. Il confronto testuale usa NFKC, case folding e distanza di modifica; gli attributi di blocking richiedono invece uguaglianza JSON, da configurare su valori normalizzati.
- Il percorso pubblicato conserva la geometria corrente davanti a contributi discordanti di pari autorità e mette il job in revisione. Il confronto è topologico nel CRS di serving, non una tolleranza territoriale configurabile. La via legacy di materializzazione diretta non è certificata come corretta per il caso multi-fonte.
- L’approvazione di un match riprende la lavorazione attraverso il binding umano e conserva la decisione automatica append-only. La policy di authority viene rivalutata sui contributi storici, senza riscriverne il rank originale.
- Sono ancora aperti: decisioni su conflitti di proprietà/geometria e relativa persistenza, ruoli/validità geometrica, controllo degli aggiornamenti fuori ordine della stessa fonte, superfici umane autorizzate e cartografia. Nessuno di questi requisiti è dichiarato completo.
- Access conserva `metadata.semanticHints` e `sourceSchemaEvidence` nella bozza: classi/proprietà da cercare, chiavi dichiarate e coppie di colonne delle relazioni, senza inventare IRI o direzioni ontologiche. Il workflow di selezione/pubblicazione del Semantic Registry resta da collegare e collaudare.
- I nuovi lettori sono identici tra Onboarding e Ingestion. Limiti e formati effettivamente collaudati sono descritti in `docs/R2F_MANAGED_FORMATS.md` nei due repository.
- Nessuna nuova prova source-to-serving Access/Shapefile è attestata dalle vecchie pairwise: esse fissano i commit e i profili dello scenario storico. Prima del merge occorre una prova che usi le nuove pubblicazioni e tutti gli owner interessati.
