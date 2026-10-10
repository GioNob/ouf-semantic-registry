# Roadmap: dal file alla ricerca, con identità tipizzata e relazioni governate

Checkpoint documentale per il documento PA: [stato F0–F11 e limiti delle evidenze al 10 ottobre](FILE_TO_SEARCH_STATUS_20261010.md). Nessuna nuova prova live del VPS e nessuna chiusura automatica dei gap PET.

Data: 10 ottobre 2026. Obiettivo dell'owner: usare il percorso completo file → onboarding → semantica → ingestion → UDP → search, poi installarlo e aggiornarlo senza interventi manuali ordinari sul VPS. Questa roadmap dettaglia una verticale della roadmap PET v1.7; non sostituisce R0–R6 e non chiude gap sulla sola base del piano.

## 1. Risultato osservabile richiesto

Un utente autorizzato carica un file, vede anteprima e problemi, configura e approva significato e regole, attiva un bundle, segue l'acquisizione, ricerca gli oggetti risultanti e ne comprende provenienza e collegamenti. Un secondo file può arricchire gli stessi oggetti o introdurre oggetti di altre nature da collegare. Replay, aggiornamenti e diverso ordine di arrivo non devono creare doppioni o collegamenti arbitrari.

Tre livelli di consegna:

1. **Giro semplice utilizzabile:** un file di natura nota, mapping approvato, ingestion reale, oggetti UDP e ricerca autorizzata attraverso Gateway e interfaccia/MCP disponibili.
2. **Giro multi-fonte completo:** identità per natura, authority per proprietà, relazioni tra nature diverse, target tardivi, ambiguità e aggiornamenti con storico. È il risultato funzionale richiesto in questa conversazione.
3. **Installazione industrializzata:** stesso comportamento su host pulito indipendente, pacchetto/profilo documentati, upgrade e recovery qualificati. Una demo sul VPS non soddisfa questo livello.

Nessuna data di completamento è promessa prima di ripristinare i gate rossi e qualificare l'applicatore target. L'ordine sotto è eseguibile e le uscite sono verificabili; lo stato viene aggiornato con evidenze, non percentuali stimate.

## 2. Stato verificato di partenza

- VPS: input runtime, truststore pubblico Java e contratto applicativo sono preparati. Il contratto del10 ottobre15:29 corrisponde ai path e al workload del provider originale; tre file hanno proprietà/permesse verificate. Nessun cutover applicativo effettuato; complete OCI, nuovo peer/transport firmato, migrazione/applicatore coordinato e readiness restano aperti. I bytes dei segreti devono essere verificati privatamente all'apply.
- Il codice Onboarding include THS di review, publication e contratti relazionali; esistono prove R2a–R2f circoscritte. Non equivalgono all'intero percorso corrente installato.
- UDP ObjectResolutionService limita la ricerca per match_key a tenant e canonical_type. Il percorso di riuso di SourceObjectBinding deve essere incluso nell'audit di riclassificazione/isolamento: non si estende la prova del filtro principale a ogni ramo.
- RelationshipMaterializer risolve target tipizzati per chiave, registra contributi/evidenze e non sceglie arbitrariamente tra più candidati. PublishedRuntimeConfiguration ammette nel percorso ispezionato CANONICAL_KEY, QUARANTINE_RELATION e REVIEW_REQUIRED: il contratto generale non prova che tutte le strategie dichiarabili siano eseguibili.
- RelationshipReconciliation conserva il profilo originario e rivaluta anche target arrivati dopo. Sono presenti test per target tardivo, successiva ambiguità e riferimento cambiato; RelatedSearchService offre traversal inbound/outbound limitato. Inverse ontologiche, compatibilità generale tra classi e tutte le cardinalità non sono dichiarate complete da questa ispezione.
- WeightedIdentityPolicy esiste nel control plane; il resolver ispezionato usa il percorso esatto match_key. La presenza del modello pesato non prova il funzionamento end-to-end dello scoring.
- Latest CI sugli SHA riletti: Onboarding module/browser verdi; MCP module/conformance verdi; Ingestion module e R2b/c/e rossi, UDP module rosso. I precedenti rilievi del worker e della fixture MinIO restano da risolvere, non da aggirare.
- Cinema e asset/profilo Teatri già acquisiti sono regressioni da preservare; non si richiede un nuovo upload per continuare dati già custoditi.

Queste sono evidenze di sorgente/CI e ricevute operatore, non una nuova ispezione live dell'intera piattaforma.

## 3. Regola generale di identità

**Una somiglianza tra campi non autorizza l'identità tra oggetti di natura diversa.** La proposta dell'owner è adottata come invariante funzionale; i dettagli di profilo/versione qui sotto sono il disegno di attuazione da qualificare.

Ogni candidato deve avere un tipo canonico, riferimenti semantici pubblicati/versionati, identità della riga sorgente, contesto di isolamento e un profilo di risoluzione approvato. La selezione dei candidati applica prima il perimetro semantico e di sicurezza, poi chiavi e altri indizi. Il commit della decisione ripete i controlli: non basta filtrare l'indice.

Per default sono confrontabili per identità solo oggetti della stessa classe canonica. Classi di vocabolari differenti possono condividere un perimetro di identità soltanto attraverso una corrispondenza esplicita, approvata e versionata. Etichette uguali, antenati generici come Thing/Place, semplice sottoclasse o vicinanza vettoriale non bastano. Organizzazione, sede fisica, edificio, evento e ruolo devono restare distinguibili anche quando descrivono la stessa situazione. Cambi di classificazione o mapping di una sorgente richiedono verifica di continuità; non causano automaticamente nuova identità né riuso cieco del vecchio binding.

All'interno della natura corretta si usano, in ordine configurato: binding sorgente valido, identificatore canonico/master data, attributi normalizzati, regole composte e, dove supportato e approvato, scoring/spazio. La stessa natura è necessaria, non sufficiente: due cinema allo stesso civico possono restare distinti. Il solo indirizzo o la sola geometria non sono chiavi universali.

Ogni esito è MATCH, NEW_OBJECT, REVIEW_REQUIRED o REJECTED, con regola/versione, evidenze e motivazione. Un match non comporta sovrascrivere tutti i dati: l'authority per proprietà/geometria/relazione determina il current view. Un merge di due oggetti canonici già creati è una distinta operazione governata, con impatto, decisione HUMAN ove richiesta, alias e storico; non coincide col binding di una nuova osservazione.

Deduplica del file, idempotenza della run/handoff, identità della riga sorgente, identità dell'oggetto canonico e deduplica degli edge sono cinque controlli distinti.

## 4. Regola generale delle relazioni

La condivisione di un attributo può fornire evidenza per una relazione tra oggetti diversi; non determina da sola né l'esistenza né il significato della relazione. Il Registry deve pubblicare la relazione; l'Onboarding deve configurare il suo uso; UDP deve risolvere le istanze e conservarne evidenza e validità.

Un mapping relazionale deve fissare almeno:

- relationIri e versione/publication set; classi ammesse a origine e destinazione;
- campo o regola di estrazione, target class e chiave/strategia di lookup;
- normalizzazione, contesto territoriale, ambito tenant e validità temporale;
- cardinalità, eventuale auto-relazione consentita, regole per zero o più target;
- relazione obbligatoria/opzionale e conseguenze sull'attivazione/materializzazione;
- authority, classificazione di accesso e provenance degli edge;
- politica di aggiornamento, rivalutazione e fine validità;
- eventuale inversa o altra inferenza esplicitamente pubblicata e supportata.

Comportamento richiesto per entrambi gli ordini di arrivo:

1. Se il target esiste, è ammissibile e unico, materializzare un edge idempotente.
2. Se manca, conservare l'intento di relazione con profilo e chiave originali. Non creare un oggetto autorevole inventato. La policy decide se lasciare l'oggetto visibile con relazione pendente oppure bloccarne/quarantinarne la materializzazione; la relazione assente deve essere osservabile.
3. All'arrivo o modifica di un target, riconciliare gli intenti pertinenti in modo durevole e limitato. Il polling esistente costituisce una base; selezione per tipo/chiave, budget e backoff vanno qualificati per il carico atteso.
4. Se più target sono plausibili, aprire una issue. Il caso ambiguo non si sblocca automaticamente scegliendo il primo o il più vicino senza policy sufficiente.
5. Se cambia la sorgente, il target diventa inattivo o una nuova evidenza contraddice il link, aggiornare/supersedere la vista corrente conservando lo storico e le evidenze delle diverse fonti.

Per navigare da B verso gli A collegati non serve sempre duplicare l'edge A→B: la query inbound è già un meccanismo valido. Se il modello dichiara una proprietà inversa, la sua proiezione deve essere coerente e deduplicata. Non si inventano contains/belongsTo come inverse di qualsiasi relazione; simmetria e transitività non sono automatiche.

### Esempio solo illustrativo

Nel vocabolario Schema.org il tipo è MovieTheater; PostalAddress è un tipo e address è una proprietà che può riferirlo. containedInPlace/containsPlace rappresentano invece contenimento tra Place. Non si forza quindi un PostalAddress a essere il contenitore spaziale di un cinema.

Un file con i soli toponimi e qualificatori via/viale/piazza può descrivere strade o aree di circolazione, non indirizzi completi. Un indirizzo può richiedere comune, codice strada, civico, esponente ed eventuale unità; un edificio e un'attività in esso restano altre entità. Il modello esatto va scelto dai dati e dal catalogo pubblicato. I collegamenti illustrativi cinema→indirizzo, indirizzo→strada, cinema→edificio possono diventare regole concrete solo dopo l'adozione della semantica appropriata.

La regola vale anche per sensore→impianto, concessione→attività, edificio→particella, evento→luogo e dispositivo→organizzazione: la relazione fra entità diverse non le fonde.

## 5. Roadmap operativa

Le sigle F0–F11 sono passi di questa verticale; non nuovi stati normativi dei PET.

| Passo | Lavoro e deliverable | Owner principali | Dipendenze e uscita verificabile |
| --- | --- | --- | --- |
| F0 — Contratti e casi di accettazione | Fissare natura/IRI, identità, authority, relazioni e casi negativi; censire capability realmente installate e candidate | Semantic, Onboarding, UDP | Ora. Specifica versionata e fixture multi-fonte con risultati attesi, senza cambiare retroattivamente i mapping attivi |
| F1 — Baseline eseguibile | Correggere CI worker/storage; completare applicatore, backup/fencing, nuovo peer/transport, migrazione e readiness; preservare Cinema | Deploy, Gateway, Ingestion, UDP, Semantic/MCP | Gate attuale. Pacchetto identificato e installato, test positivi/negativi delle route e recupero; niente PASS copiati da scansioni scadute |
| F2 — File e profilazione | Upload governato, hash/raw immutabile, formato/encoding/separatori, schema e anteprima; null/tipi/duplicati tecnici, source ID e source-object key; selezione campi/classificazione | Onboarding/THS, Gateway, storage | F1 per prova target. CSV iniziale; XLSX e formati gestiti in tranche qualificate. Utente vede righe valide/errori e può correggere prima dell'attivazione |
| F3 — Semantica utilizzabile | Cercare classi/proprietà/relazioni già adottate; per un gap avviare discovery, proporre adozione/pubblicazione governata; pin di versioni e validazione di domain/range | Semantic, THS, Gateway | F0/F2. Ogni tipo/campo necessario ha un riferimento valido; gap obbligatori bloccano. Provider esterno solo quando necessario, senza riscoprire quanto già approvato |
| F4 — Mapping e profili | Costruire mapping campi/vocabolari/normalizzazioni, chiavi per natura, policy MATCH/NEW/REVIEW, authority e regole relazionali; anteprima su campione | Onboarding con Semantic e UDP | F3. Eseguibile supportato e coerente: nessuna strategia soltanto dichiarata. Campione dimostra cinema≠indirizzo e due attività co-localizzate distinte |
| F5 — Approvazione e pubblicazione | Review comprensibile, challenge/ETag/attore; pubblicare PublishedConfigurationBundle ACTIVE con refs/checksum e readiness | Onboarding/THS, Authorization, Gateway | F4. Bundle accettato dagli owner runtime; vecchie versioni ancora risolvibili. Nessuna attivazione implicita per semplice proposta AI |
| F6 — Acquisizione e handoff | Eseguire extraction/normalizzazione dal bundle pinned, preservare raw, emettere canonical payload, lineage e stato durevole; retry/idempotenza/quarantena | Ingestion, Gateway, lake | F5. Conteggi ricevuti/processati/scartati verificabili; nessuna perdita o duplicazione al replay e nessuna decisione di identità canonica in Ingestion |
| F7 — Identità e arricchimento | Applicare filtro semantico a ogni percorso, risolvere source binding e match, materializzare revisioni/authority; issue e merge governato; audit di riclassificazione e concorrenza | UDP; profili Onboarding | F6. Più fonti della stessa entità convergono sullo stesso ID dove provato; nature incompatibili e omonimi restano distinti; lineage fino alla riga/raw |
| F8 — Relazioni e arrivi tardivi | Materializzare edge tipizzati, riconciliare target successivi, gestire zero/N target, cardinalità, letture inverse, aggiornamento/tombstone e provenienza multi-fonte | UDP con contratti Semantic/Onboarding | F7. Entrambi gli ordini di caricamento producono lo stesso grafo valido; edge duplicati e collegamenti arbitrari assenti; obbligatorietà e pending visibili |
| F9 — Search di oggetti e relazioni | Esporre ricerca per tipo/attributi/testo e spazio dove qualificato; dettaglio/provenienza; ricerca con anchor e relazioni, inbound/outbound, limiti/cursor e autorizzazione | UDP, Gateway, MCP/UI | F7 per ricerca semplice, F8 per correlata. Query reali dal canale utente; output filtrato e nessuna fuga attraverso conteggi, edge o cache |
| F10 — Collaudo del giro completo | Eseguire scenari multi-file, review, update/delete, riavvio/retry e replay storico; verificare OA e recupero; regressione Cinema/Teatri | Tutti gli owner | F2–F9. Evidenza unica correlata file→bundle→run→urbanObjectId→edge→risposta, con negativi e problemi espliciti |
| F11 — Installazione ripetibile | Convergere in pacchetto firmato, profilo parametrizzato, ingresso ristretto e macchina di stato; host pulito, seconda installazione, N→N+1 e fault/recovery | Deploy con tutti gli owner | Disegno da F1, sviluppo durante le fasi; accettazione dopo F10. Nessuna modifica manuale ordinaria sul VPS, nessun hardcode di PID/ifindex/snapshot del laboratorio |

F0 e ripristino CI possono avanzare insieme al completamento di F1; contratti/test di F3–F4 non richiedono mutazioni del VPS. Per il primo giro semplice si usa una classe già disponibile e matching deterministico; si attraversano F2–F7 e F9. F8 e F10 chiudono il risultato multi-fonte richiesto, senza fermarsi alla demo iniziale. F11 viene progettato subito e non ridotto a un confezionamento finale di script ad hoc.

La search del catalogo semantico in F3 cerca classi/proprietà; la search in F9 cerca istanze urbane. Gli eventuali sinonimi, gerarchie o ranking semantici devono usare riferimenti governati; un motore vettoriale non è un requisito per il primo giro e non decide l'identità.

## 6. Collaudo minimo della verticale

| ID | Scenario | Atteso |
| --- | --- | --- |
| FILE-01 | Stesso file/richiesta ripetuti | Idempotenza documentata; nessun doppio effetto canonico |
| ID-01 | Due fonti della stessa natura con identificatore forte della stessa entità | Stesso urbanObjectId, due binding e lineage distinti |
| ID-02 | Cinema e indirizzo con tutti i campi indirizzo uguali | Due oggetti distinti; mai MATCH d'identità fra loro |
| ID-03 | Due cinema allo stesso civico ma identificatori/evidenze di entità distinte | Due oggetti; indirizzo da solo insufficiente |
| ID-04 | Stesso nome/chiave locale in comuni o tenant diversi | Nessuna fusione fuori dal perimetro approvato |
| ID-05 | Classi di vocabolari differenti o generiche | Nessun allargamento implicito; solo corrispondenza esplicita e testata |
| ID-06 | Cambio mapping/type con SourceObjectBinding già noto | Continuità verificata o review; nessun bypass del controllo semantico |
| REL-01 | Target caricato prima dell'oggetto sorgente | Edge corretto una sola volta |
| REL-02 | Oggetto sorgente prima del target, con riavvio intermedio | Intento conservato e risolto dopo senza reupload della fonte |
| REL-03 | Due target con la stessa chiave nel perimetro | Issue visibile; nessun primo match arbitrario |
| REL-04 | Target inattivo, relazione incompatibile o cardinalità violata | Rifiuto/pending/quarantena secondo policy, con motivo |
| REL-05 | Lookup inverso e retry di più contributi allo stesso edge | Risultato coerente, nessun doppio edge; provenance mantenuta |
| REL-06 | Riferimento sorgente cambia, target scompare o merge/split interviene | Vista corrente riconciliata; storico conservato e nessun link replicato arbitrariamente |
| AUTH-01 | Valori discordanti da due fonti | Authority per proprietà, conflitto/evidenza visibili; niente ultimo-writer-vince implicito |
| SEARCH-01 | Filtri tipo/attributi e query attraverso relazioni | Solo oggetti attesi; paginazione e budget applicati |
| SEC-01 | Utente senza permessi su oggetto/proprietà/edge | Nessuna restituzione o inferenza tramite conteggi; identica policy sui canali |
| GOV-01 | Proposta AI e tentativo service di decisione HUMAN protetta | Proposta consentita; commit protetto negato e handoff THS corretto |
| OPS-01 | Crash/retry, messaggio vecchio dopo il nuovo e replay bundle storico | Esiti durevoli, idempotenza e pinning; nessuna regressione silenziosa |
| INST-01 | Pacchetto su host pulito e upgrade con guasto | Stesso esito funzionale e recupero governato senza correzioni manuali |

## 7. Confini di ownership e coerenza normativa

Semantic Registry possiede classi/proprietà/relazioni e pubblicazioni; Onboarding possiede mapping, profili e bundle; Ingestion esegue acquisizione/normalizzazione/handoff; UDP possiede identità, authority, revisioni ed edge; Gateway media; Authorization valuta e gli owner applicano; MCP propone/interroga; THS esegue le decisioni HUMAN presso il backend owner. L'automazione usa regole già approvate: non richiede un click per ogni riga, e non approva autonomamente ontologie, mapping o merge protetti.

Riferimenti della baseline allegata: UDP1.3 §§11–12,18–24,25–31 e serving/governance; Onboarding1.6 §§33,36 e PublishedConfigurationBundle; Semantic1.3 publication/reference integrity e §160; Matrix1.7 e Blueprint0.3 per ownership; Authorization1.5, Gateway1.5 e MCP1.4 per confini dei canali/decisioni. L'invariante di natura esplicitato dall'owner precisa i guard della risoluzione e va tracciato nel contratto; non riscrive tacitamente i PET.

R2a–f rimangono verticali circoscritte; questa consegna attraversa R2c/R4a/R4b e i gate R5/R6. HA, tutti i formati/GIS, OA completa, capacity e DR dell'intera piattaforma restano nel programma generale. Non sono attestati dal giro CSV né dimenticati dalla nuova roadmap.

## 8. Fonti della ricognizione

Snapshot main letti il10 ottobre2026:

- [UDP](https://github.com/GioNob/ouf-udp-object-resolution/tree/6285b733c49b89cb6d3382abe8dc469f8a0e8b1b): 6285b733c… — ObjectResolutionService, PublishedResolutionLoop/Configuration, RelationshipMaterializer/Reconciliation, RelatedSearchService e test relazionali.
- [Onboarding](https://github.com/GioNob/ouf-source-onboarding/tree/21de5f21e903e6e99f4ef4d6617a446d60a54792): 21de5f21e… — RelationshipMapping, WeightedIdentityPolicy, THS/CI e roadmap.
- [Semantic](https://github.com/GioNob/ouf-semantic-registry/tree/416e9c484ea3737ec773471f4505069061080558): 416e9c484… — roadmap e registro gap; candidato firmato di deploy resta distinto da main.
- Ingestion: a8ba969a5a0e20e9c53977d2875094ce82802f9d — latest CI module36423996284, R2b36423996047, R2c36423996317, R2e36423996231 in failure.
- UDP latest module36334165297 failure; Onboarding module36388267487/browser36388267535 success; MCP5615fdc… module36410481211/conformance36410481075 success. Queste CI sono state rilette, non rieseguite per scrivere il piano.
- [Deploy](https://github.com/GioNob/ouf-deploy/tree/735c3c9fa3066df21811ca8b4f6e2a6df1754145):735c3c9f…; receipt application-input-contract-prepared-target-20261010 e INSTALLATION_INDUSTRIALIZATION_PLAN.
- Vocabolario esterno consultato come esempio, non adozione: https://schema.org/MovieTheater, https://schema.org/PostalAddress, https://schema.org/address, https://schema.org/containedInPlace. L'installazione deve usare la versione effettivamente adottata e pubblicata.


## Ordine confermato dall'owner e seguito esecutivo

Dopo il completamento e consolidamento del giro con i file, si affronta il giro tramite PULL sulle API native dei verticali secondo le Linee di indirizzo v2.3. Le interfacce verticali non incorporano semantica o identità UDP; il profilo di estrazione approvato guida proiezione, normalizzazione e handoff durevole. [Progressi eseguiti e prove correnti](FILE_TO_SEARCH_STATUS_20261010.md#aggiornamento-esecutivo--file-prima-delle-api-10-ottobre). Le CI bloccanti di Ingestion/UDP sono state corrette; F1, F10 e F11 rimangono aperti finché non esistono le rispettive prove target e su host pulito.
