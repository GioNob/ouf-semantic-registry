# Contratto sprint-03 — Analisi semantica v2

**Versione 2.0.0 · 23 novembre 2026 · Sequenza di attivazione T0 → T1 → T2.**

L’unità di completezza è l’**ordinale del profilo**. L’unità di ricerca è l’**intento distinto**. Il MCP conserva la relazione fra le due. Semantic decide quale evidenza esiste. Il Gateway autorizza e media ogni dispatch. Il chatbot segue il `next` del piano.

| Parte | Versione di interfaccia | Owner e responsabilità |
|---|---|---|
| B · tranche 0 | `ouf.analysis.summary.v2` | MCP possiede esiti, contatori, pagine e binario. Semantic attesta lo zero quando la lettura esistente non basta. |
| A · tranche 1 | `ouf.semantic.published-batch.v1` | Semantic possiede ricerca e classificazione. Gateway possiede rotta e schema di dispatch. MCP raggruppa gli ordinali e pianifica i residui. |
| C · tranche 2 | `ouf.analysis.run.v2`, `ouf.analysis.mandate.v1` | MCP possiede piano, coda e consumo. Gateway possiede mandato, revoca e mediazione con prova fresca. Gli owner conservano l’ultima decisione sulla propria risorsa. |

Si applicano D-071, D-080, D-085, D-087, D-088, D-089, D-090, la policy di resilienza v3 e i PET dei moduli. I nomi v2 e le nuove rotte qui definite sono specifiche da implementare. Le prove di accettazione sono condizioni di rilascio.

## Convenzioni comuni

- JSON UTF-8. Gli oggetti nuovi sono chiusi. Campi obbligatori salvo indicazione `?`. Vietati chiavi duplicate, `null` impliciti, coercizioni e troncamenti silenziosi. I byte si misurano sul corpo serializzato, dopo eventuale decompressione.
- `uuid` è una stringa UUID canonica. `commandKey` è UUIDv4 minuscolo. `digest` è una stringa di 64 cifre esadecimali minuscole. `analysisId` conserva la forma `digest` e l’identità logica di `analysis.AnalysisID`. `instant` è un timestamp RFC 3339 UTC. `seq` è una stringa decimale canonica fra `"0"` e `"9223372036854775807"`.
- `Profile` ha esattamente `assetId:uuid`, `profileId:uuid`, `profileVersion:int≥1`, `schemaHash:"sha256:"+digest`, `columnCount:int[1,1024]`. Gli ordinali iniziano da zero. Gli esempi sono fixture sintetiche.
- Ogni risposta MCP di workflow, inclusi errori, dinieghi e ammissione rifiutata, contiene `next` conforme a `ouf.next-step.v1`. Negli errori v2 il corpo applicativo è `{"code":"ANALYSIS_INPUT_INVALID","next":…}`. I tre puntini nella notazione indicano il blocco v1 completo. L’owner HTTP restituisce almeno `{"code":"CODICE_STABILE"}`. Un 429 o 503 transitorio comunica anche `Retry-After` se noto.
- Ogni `next.tool` e ogni alternativa devono appartenere al catalogo attivo. Gli argomenti devono superare lo schema del destinatario. `userMessage` viene da un modello italiano controllato. Per `BLOCKED` servono `actor` e `alternatives`, anche vuote. Unica alternativa identica alla chiamata corrente → `BLOCKED/OPERATOR` senza ciclo.
- Limiti operativi, quote, lingue, capacità, scadenze, riferimenti ai servizi e trust sono parametri versionati e validati. I massimi di protocollo delimitano i valori configurabili. Il rilascio verifica la compatibilità dei limiti effettivi attraverso MCP, Gateway e owner.

## Parte A — Consultazione a lotti del pubblicato · T1

### A.1 — Richiesta e risposta Semantic

`POST /api/internal/v1/semantic/consultation/search-batch`. Capability interna `ouf.semantic.search.batch`, `Owner=semantic`, `OperationClass=READ`, `GatewayBindingRef=capability://ouf.semantic.search.batch`. Si usa la busta di dispatch esistente. Il JSON seguente è il suo campo `Arguments`.

```json
{
  "contract": "ouf.semantic.published-batch.v1",
  "limitPerIntent": 3,
  "intents": [
    {"intentId":"i0","intent":"codice pratica","preferredLanguages":["it","en"],"requestedArtifactType":"PROPERTY","context":{}},
    {"intentId":"i1","intent":"quantità","preferredLanguages":["it"],"requestedArtifactType":"DATATYPE","context":{}}
  ]
}
```

```json
{
  "contract":"ouf.semantic.published-batch.v1",
  "results":[
    {"intentId":"i0","state":"MATCH","hasMore":false,"hits":[
      {"semanticId":"urn:fixture:codice-pratica","semanticVersion":"1.0.0","revisionId":"11111111-1111-4111-8111-111111111111","publicationSetId":"22222222-2222-4222-8222-222222222222","score":100,"reasons":["EXACT_LABEL","PREFERRED_LANGUAGE"]}
    ]},
    {"intentId":"i1","state":"NONE","hasMore":false,"hits":[]}
  ]
}
```

| Campo o limite | Regola v1 |
|---|---|
| `intents` | Da 1 a `batchMaxIntents`, default e massimo 64. `intentId` univoco nel lotto, stringa `^[A-Za-z0-9_-]{1,64}$`. |
| `intent` | Stringa da 1 a 256 punti di codice prima e dopo la normalizzazione. Una stringa vuota dopo la normalizzazione è invalida. |
| `preferredLanguages` | Da 1 a 5 stringhe ordinate per preferenza. Forma `^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8}){0,3}$`. Uniche dopo la conversione ASCII in minuscolo. |
| `requestedArtifactType` | Enum chiuso `PROPERTY`, `CLASS`, `DATATYPE` in tutti e tre i repository. |
| `context` | Oggetto obbligatorio. Campi facoltativi `namespace:string[1,512]`, `domain:string[1,2048]`, `range:string[1,2048]`. Identificatori confrontati esattamente. Ogni filtro presente è vincolante. |
| `limitPerIntent`, `hits` | Intero da 1 a `batchMaxHits`, default operativo 3, massimo 8. `hits` contiene al massimo `limitPerIntent` elementi. `hasMore:boolean` indica ulteriori riscontri ammissibili. |
| Riscontro | `semanticId:string[1,2048]`, `semanticVersion:string[1,128]` nella forma emessa dall’owner, `revisionId:uuid`, `publicationSetId:uuid`, `score:int[0,100]`, `reasons` array ordinato di 1–4 codici distinti della tabella seguente. |
| Byte | `batchMaxRequestBytes` default/massimo 65.536 sull’intera busta owner. `batchMaxResponseBytes` default/massimo 262.144. Vale anche il minore `MaxResultBytes` negoziato. Il MCP compone i lotti per numero **e** byte. |

Semantic legge in un solo snapshot per lotto. Riusa i filtri di `SemanticReadService.search`: artefatto visibile e non ritirato, puntatore alla revisione corrente, revisione `ACTIVE`, membership della stessa revisione e dello stesso `semanticId` in un set `PUBLISHED`. Fra più set sceglie `publication_no` maggiore, poi `publicationSetId` crescente. Applica tipo, contesto e autorizzazione prima del ranking. L’indice può fornire candidati alla ricerca. Ogni riscontro restituito deve superare i filtri owner.

| Evidenza sul termine normalizzato | `score` | `reasons` in ordine |
|---|---:|---|
| Etichetta esatta in una lingua preferita | 100 | `EXACT_LABEL`, `PREFERRED_LANGUAGE` |
| Nome locale esatto con almeno un’etichetta nella lingua preferita | 95 | `EXACT_LOCAL_NAME`, `PREFERRED_LANGUAGE` |
| Prefisso non vuoto dell’etichetta in lingua preferita | 60 | `LABEL_PREFIX`, `PREFERRED_LANGUAGE` |
| Filtri di contesto presenti e soddisfatti | invariato | Aggiungere `CONTEXT_MATCH` in coda. |

Ogni revisione compare una volta con la sua migliore prova. La revisione con punteggio 95 o 100 è una corrispondenza forte. **Una sola forte** → `MATCH` e `hits[0]` è il pin prescelto. Più forti oppure solo deboli → `AMBIGUOUS`. Nessun riscontro → `NONE`. Si verifica l’unicità **prima** di applicare `limitPerIntent`. L’ordine è punteggio decrescente, prima lingua pertinente nell’ordine richiesto, `semanticId` in ordine di byte UTF-8, `revisionId` crescente. I risultati seguono l’ordine degli intenti in ingresso.

La lettura è idempotente e senza effetti di dominio. Stesso input, stessa visibilità, stesso catalogo e versione di ranking producono gli stessi risultati. Una nuova pubblicazione può cambiare una successiva consultazione. Il MCP conserva atomicamente la risposta accettata e i pin con il lotto del piano. Un replay del piano usa quell’evidenza. Un lotto incompleto, duplicato, fuori ordine o sconosciuto fallisce per intero.

### A.2 — Identità dell’intento e residui

1. `norm-v1` applica NFC, Unicode Default Case Folding non dipendente dalla lingua, poi NFC. Sostituisce ogni sequenza Unicode `White_Space` con uno spazio ASCII e rimuove gli spazi estremi. Conserva accenti, punteggiatura, cifre e separatori di parola. Le implementazioni fissano le stesse tabelle Unicode nella fixture di contratto. Le lingue passano in minuscolo mantenendo l’ordine. I riferimenti di contesto restano opachi.
2. La chiave è SHA-256 del JSON canonico RFC 8785 di `["norm-v1",testoNormalizzato,lingueOrdinate,tipo,context]`. Il raggruppamento è circoscritto a identità, tenant, profilo immutabile, visibilità e versione della policy del piano. Conservare `intentKey → ordinali distinti ordinati`. Un gruppo può attraversare più pagine. Lingue invertite, dominio diverso o tipo diverso formano gruppi distinti.
3. Il MCP cerca prima nel pubblicato. `MATCH` produce un `MATCHED_PUBLISHED` per ogni ordinale del gruppo. Per `NONE` o `AMBIGUOUS` prepara al massimo **una discovery iniziale per gruppo**. Conserva l’evidenza dell’ambiguità. Nessun fallback remoto per un lotto fallito, un diniego o un `MATCH`.
4. Il comando esistente usa `requestedArtifactType`, `intent`, `preferredLanguages`, `idempotencyKey`. La chiave owner `analysis:` più digest è generata dal MCP e persistita prima del primo invio. Include piano e intento distinto, anche quando due contesti avrebbero lo stesso testo remoto. Il job cerca candidati per il successivo esame del contesto.
5. La discovery corrente ammette `PROPERTY` e `CLASS` ma il suo enum esclude `DATATYPE`. Un residuo `DATATYPE` dà `BLOCKED / DISCOVERY_TYPE_UNSUPPORTED`. Vietata la conversione in `PROPERTY`. Per abilitarlo servono supporto owner/provider qualificato, aggiornamento dello schema discovery e successiva attivazione Gateway → MCP.
6. In T1 il lotto è una capability **interna**, `toolEligible=false`. Il passaggio pubblico di piano già autorizzato esegue lavoro finito con le quote interattive applicabili. Il chatbot segue `next` e non sceglie lotti, lingue di fallback o chiavi. D-085 governa la continuazione. D-088 continua a governare le chiamate del chatbot. Il lavoro autonomo si attiva in T2.

### A.3 — Gateway, autorizzazione ed errori

Rotta governata `mcp-semantic-search-batch`, `POST /internal/capabilities/v1/execute/semantic/consultation/search-batch` → endpoint A.1. Si applica il modello 51j: `RouteBinding`, binding del backend da installazione, risorsa nel bundle di rilascio, snapshot con provenienza in `contracts/`, generazione dello schema APISIX e prova del corpo realmente inoltrato.

Il manifest MCP è la fonte dello schema `Arguments`. La CI confronta ricorsivamente `required`, proprietà, enum, tipi, limiti, pattern e chiusura degli oggetti. Proietta via solo i campi dichiarati locali, per esempio `analysisId` nella ricerca singola. La CI esercita **anche `semantic.search` singola** con `type=DATATYPE` attraverso la rotta materializzata. D-087 richiede adozione dell’ID reale al plan, confronto campo per campo, rimozione governata dei duplicati, revisione di installazione coerente e restore provato.

Il Gateway esige workload MCP autenticato e autorità HUMAN corrente per il pubblicato. T1 usa la delega interattiva. T2 usa C. Semantic estende il verificatore `SemanticReadDelegation` al binding batch, verifica `X-OUF-Semantic-Read-Receipt` sui byte effettivamente inoltrati e applica la policy owner su `semantic.artifact` nel tenant. Il permesso di consultazione del lotto richiede il diritto di ricerca pubblicata. Audit minimo: decisione, capability, scope, versione di ranking, digest del lotto, cardinalità e conteggi per stato.

| HTTP | Codice | Trattamento |
|---|---|---|
| 400 | `SEM_BATCH_ARGUMENTS_INVALID` | Forma, enum, duplicati o limite di cardinalità invalidi. Nessun risultato parziale. |
| 413 | `SEM_BATCH_REQUEST_TOO_LARGE` | Ripartire il lotto in ordine. Un singolo intento fuori limite viene bloccato. |
| 422 | `SEM_BATCH_RESULT_TOO_LARGE` | Dividere il lotto, poi ridurre `limitPerIntent` fino a 1. L’unicità resta calcolata sull’insieme ammissibile. Se ancora insufficiente, bloccare il gruppo. |
| 403 | `SEM_READ_RECEIPT_OR_POLICY_DENIED` | Fermare lo scope interessato. Nessuna discovery sostitutiva. |
| 429 / 503 | `SEM_BATCH_RATE_LIMITED` / `SEM_BATCH_UNAVAILABLE` | Pausa durevole solo per transitorio esplicito, con budget residuo. |
| 502 al MCP | `ANALYSIS_OWNER_RESPONSE_INVALID` | Risposta incoerente o prova mancante. Bloccare e conservare la correlazione. |

## Parte B — Esito per ordinale e riepilogo · T0

Il MCP legge `source.file.preview` in vista `COLUMNS` per il profilo fissato. Verifica identità, versione, hash, totale, offset e continuità di ogni pagina. Prealloca una riga `PENDING` per ogni ordinale di `0..columnCount-1`. Una pagina assente, ripetuta o incoerente impedisce di dichiarare completo il piano. Un’intestazione non utilizzabile blocca il solo ordinale identificato. Il nome duplicato conserva entrambi gli ordinali.

### B.1 — Unione discriminata degli esiti

Campi comuni esatti: `ordinal:int[0,columnCount-1]`, `state:enum` della tabella, `changedSeq:seq`. I soli campi aggiuntivi ammessi dipendono dallo stato.

| `state` | Campi aggiuntivi | Prova richiesta |
|---|---|---|
| `MATCHED_PUBLISHED` | `match` con la forma del riscontro A.1 | `MATCH` accettato e pin conservato. |
| `CANDIDATES_READY` | `requestId:uuid`, `candidateCount:int≥1`, `observedAt:instant` | Job owner `SUCCEEDED` e lista del job letta con stato coerente, candidati validi alla lettura. I riferimenti restano vincolati al job. |
| `NO_CANDIDATES` | `requestId:uuid`, `candidateCount:0`, `observedAt:instant` | Job `SUCCEEDED` e zero attestato al completamento. Vale per la ricerca e la policy effettivamente applicate. |
| `BLOCKED` | `reasonCode:codice`, `requestId?:uuid` | Motivo specifico e persistito. Conta come rendicontato e come bloccato. |
| `PENDING` | `requestId?:uuid` | Lavoro da fare, ricevuta di invio, osservazione transitoria o riconciliazione ancora in corso. |

`step.state=SUCCEEDED` con `result.state=PENDING` salva il `requestId` e lascia la colonna `PENDING`. Anche `NONE` nel pubblicato da solo lascia la colonna aperta. Timeout, lista scaduta, diniego, coda occupata e provider indisponibile non provano uno zero.

`DiscoveryJobService.status` conta i candidati **ancora validi**. Per distinguere uno zero originario da una scadenza, Semantic aggiunge a status/candidates `completedCandidateCount?:int≥0`, fissato nella transazione di successo e immutabile. Un equivalente storico è accettabile solo se ricostruibile da evidenza owner integra. Con dato assente o candidati positivi ormai scaduti, il MCP conserva l’evidenza già verificata oppure rende `BLOCKED / DISCOVERY_EVIDENCE_UNAVAILABLE`. L’uso successivo di un candidato richiede una lettura autorizzata corrente.

### B.2 — Forma di `source.analysis.read`

La forma legacy `{analysisId,offset?,limit?}` conserva il proprio significato. V2 aggiunge due rami distinti. `STATUS` serve alla sola osservazione aggregata. `SUMMARY` consegna contatori ed esiti paginati.

```json
{"analysisId":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","view":"STATUS"}
```

```json
{"analysisId":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","view":"SUMMARY","limit":32}
```

Risposta `SUMMARY` completa per un profilo di due colonne:

```json
{
  "contract":"ouf.analysis.summary.v2",
  "analysisId":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "state":"PARTIAL","changeSeq":"4",
  "counts":{"total":2,"matchedPublished":0,"candidatesReady":0,"noCandidates":1,"blocked":1,"pending":0},
  "items":[
    {"ordinal":0,"changedSeq":"3","state":"NO_CANDIDATES","requestId":"33333333-3333-4333-8333-333333333333","candidateCount":0,"observedAt":"2030-01-01T10:00:00Z"},
    {"ordinal":1,"changedSeq":"4","state":"BLOCKED","reasonCode":"DISCOVERY_TYPE_UNSUPPORTED"}
  ],
  "next":{"contract":"ouf.next-step.v1","action":"BLOCKED","reasonCode":"ANALYSIS_PARTIAL","actor":"OPERATOR","alternatives":[],"userMessage":"Una colonna richiede un tipo che la discovery non supporta. Il riepilogo conserva entrambi gli esiti."}
}
```

- La risposta `STATUS` contiene solo `contract`, `analysisId`, `state`, `changeSeq`, `counts`, `next`. `SUMMARY` aggiunge `items` e `nextCursor?:string`. `limit` facoltativo, default 32, massimo 128. Continuazione esatta `{analysisId,view:"SUMMARY",cursor}`. Il cursore base64url autenticato, lungo 32–1024 caratteri, lega scope, piano, snapshot, ultimo ordinale, limite e scadenza.
- I cinque contatori di stato sono interi non negativi. La somma è `total=columnCount`. Esiti conclusi con evidenza = `matchedPublished+candidatesReady+noCandidates`. Rendicontati con esito definitivo della sessione = `total-pending`. Almeno un blocco impedisce il successo integrale.
- Un’unica transazione con fence aggiorna esiti, contatori, stato aggregato e sequenza. `changeSeq` cresce a ogni commit che cambia un esito osservabile o lo stato aggregato. Tutte le righe modificate nello stesso commit ricevono quel valore. Replay identico e semplice poll lasciano la sequenza invariata. `revision` del piano conserva la semantica v1.
- La prima pagina fissa uno snapshot durevole con contatori e sequenza. Le successive leggono a quella sequenza, per chiave `ordinal > ultimo`, usando un indice e versioni conservate entro la retention. Nessun lock fra pagine. Nessuna scansione dei task o ricarica del piano completo per `STATUS`, contatori o pagina. La risposta rispetta un limite di byte parametrico, massimo 1 MiB. Una pagina può contenere meno di `limit` righe.
- Il cursore scaduto dà `410 ANALYSIS_CURSOR_EXPIRED` e `CALL_TOOL` alla prima `SUMMARY` corrente. Cursore alterato → `400 ANALYSIS_CURSOR_INVALID`. Scope estraneo e piano inesistente → identico `404 ANALYSIS_NOT_FOUND_OR_SCOPE_CHANGED`. Riautorizzare anche le pagine storiche. Registrare scope, decisione, snapshot e intervallo servito.
- Altri errori MCP: `400 ANALYSIS_INPUT_INVALID`, `409 ANALYSIS_REVISION_CONFLICT`, `409 ANALYSIS_PROFILE_CHANGED`, `503 ANALYSIS_STORE_UNAVAILABLE`. Drift di profilo o di integrità richiede intervento. I motivi di colonna includono inoltre `ANALYSIS_COLUMN_INVALID`, `DISCOVERY_FAILED`, `DISCOVERY_CANCELLED` e i motivi governati delle parti A e C.

### B.3 — Stato aggregato e `next`

| Stato | Condizione nell’ordine di valutazione | Passo sul binario |
|---|---|---|
| `BLOCKED` | Stop dell’intero piano oppure tutti gli ordinali bloccati | Da `STATUS`, consegnare `SUMMARY` se la lettura è ancora autorizzata. Nel riepilogo, `BLOCKED` con motivo e attore effettivi. Dopo revoca del diritto di lettura, diniego immediato senza dati. |
| `RUNNING` | Esiste lavoro pendente con prosecuzione ammessa, anche con blocchi indipendenti | T0/T1 indicano il prossimo `step` o la lettura owner consentita. T2 emette il `POLL` aggregato di C. |
| `PARTIAL` | Nessun pendente, almeno un esito con evidenza e almeno un blocco | `STATUS → CALL_TOOL SUMMARY`. Nel riepilogo `BLOCKED / ANALYSIS_PARTIAL`, motivi per ordinale, sole uscite autorizzate. |
| `COMPLETE` | Tutti gli ordinali hanno evidenza, compresi gli zeri verificati | `STATUS → CALL_TOOL SUMMARY`. Per l’obiettivo di sola analisi, `DONE / SUCCEEDED`. Nel workflow di onboarding si conserva `BLOCKED / MAPPING_DECISION_REQUIRED` con le alternative del manifest applicabili ai pin o job osservati. |

L’obiettivo di workflow è fissato dal binario all’avvio. La fine della raccolta non conclude la pipeline CSV. Per una lettura integrale richiesta, `nextCursor` conduce alla pagina successiva prima della transizione finale. La lettura ordinaria del riepilogo consegna subito i contatori globali.

## Parte C — Un piano durevole lato server · T2

### C.1 — Avvio e attesa di macchina

`source.analysis.plan` aggiunge il ramo chiuso seguente. Il ramo con `work` ed `expectedRevision` resta disponibile per il predecessore. La preview CSV v2 indica il ramo `ALL_COLUMNS` appena possiede i riferimenti immutabili del profilo.

```json
{"mode":"ALL_COLUMNS","commandKey":"44444444-4444-4444-8444-444444444444","assetId":"55555555-5555-4555-8555-555555555555","profileId":"66666666-6666-4666-8666-666666666666"}
```

Il risultato di avvio ha esattamente `contract:"ouf.analysis.run.v2"`, `analysisId:digest`, `profile:Profile`, `state` come in B, `changeSeq:seq`, `deadline:instant`, `next`. Il server acquisisce tutte le pagine, registra i gruppi, esegue A, invia i residui ammessi e raccoglie B. Il chatbot non invia `work`, ordinali, policy, budget o deleghe per singola colonna.

Stesso soggetto, chiave e contenuto → stessa ammissione e stesso piano osservabile. Stessa chiave e contenuto diverso → `409 ANALYSIS_COMMAND_CONFLICT`. Una nuova chiave per lo stesso profilo e intento operativo ritrova il piano e il consumo esistenti. Fissare profilo, manifest, versione del contratto e della policy; un cambio richiede riconciliazione o riprocessamento governato.

```json
{
  "contract":"ouf.next-step.v1","action":"POLL","reasonCode":"ANALYSIS_RUNNING",
  "tool":"source.analysis.read",
  "arguments":{"analysisId":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","view":"STATUS"},
  "pollAfterSeconds":5,"terminalStates":["COMPLETE","PARTIAL","BLOCKED"],
  "deadline":"2030-01-01T11:00:00Z",
  "userMessage":"L’analisi è in corso. Attendi il riepilogo del profilo."
}
```

D-089 impone **`POLL` per la macchina**. Il MCP, owner del piano, persiste alla prima ammissione `deadline=min(avvio+waitMaxSeconds,scadenzaMandato,scadenzaBudget)`. `waitMaxSeconds` ha default e massimo 3600 s. Il poll segue la cadenza aggregata dell’owner, normalmente 5 s, rispettando `notBefore`, `Retry-After` e il tempo residuo. Alla deadline si osserva prima l’eventuale esito già registrato. Altrimenti `BLOCKED / WAIT_DEADLINE_EXPIRED`, con lettura successiva solo se autorizzata. Nessun rinnovo implicito.

Il connettore segue **una continuazione logica per piano**. Ogni poll legge solo `STATUS` locale. Il cambio terminale produce una lettura `SUMMARY`. D-088 si applica a start e letture del chatbot: default 15/min per utente, letture `POLL` equivalenti ammesse alla cadenza consentita entro finestra, guardia al terzo comando equivalente e profili dedicati vigenti. `ouf.wait`, con tranche fino a 45 s, resta sul percorso delle attese umane. Il numero di turni effettivi del modello si misura sul connettore.

### C.2 — Mandato e mediazione Gateway

Il Gateway espone nel bundle tre operazioni interne `POST /internal/analysis/v1/mandates/{issue,dispatch,revoke}`. Identità di workload verificabile anche fra host distinti. L’emissione e la revoca umana richiedono delega HUMAN corrente. La revoca amministrativa richiede la corrispondente autorità IAM. Per `dispatch` il worker si autentica con la propria identità di servizio. Il solo possesso di `mandateId` non autorizza l’invio.

| Operazione | Corpo JSON esatto | Risultato |
|---|---|---|
| `issue` | `{contract:"ouf.analysis.mandate.v1",analysisId:digest,profile:Profile,manifestChecksum:digest,commandKey:uuidv4}` | `{mandateId:uuid,generation:seq,decisionRef:string[1,256],issuedAt:instant,expiresAt:instant,allowedOperations:string[]}` |
| `dispatch` | `{mandateId:uuid,generation:seq,analysisId:digest,intentKey:digest,attemptId:uuid,fence:seq,operation:string,arguments:object}` | Corpo e stato della normale operazione owner; `decisionRef` e correlazione tornano come metadati autenticati al MCP. |
| `revoke` | `{mandateId:uuid,expectedGeneration:seq,commandKey:uuidv4}` | `{mandateId:uuid,generation:seq,state:"REVOKED",decisionRef:string[1,256]}` |

- Il Gateway deriva da prove affidabili issuer, workload, principal HUMAN, tenant, risorsa, grant, scadenza e decisione. Persiste il legame con piano, profilo, manifest, operazioni, policy e generazione. Emissione idempotente e revoca con confronto di versione. Il MCP persiste il riferimento e lo stato del mandato. Nessun bearer umano durevole.
- Allowlist massima di `operation`: `source.file.preview` limitata a `COLUMNS` del profilo fissato, `ouf.semantic.search.batch`, `semantic.discovery.request`, `semantic.discovery.status`, `semantic.discovery.candidates`. `allowedOperations` è il sottoinsieme autorizzato. I nomi tool vengono risolti nelle capability e nei binding esatti del manifest fissato. Nessun percorso arbitrario. Adozione, mapping, proposte, pubblicazione, decisioni THS e rinnovo di budget richiedono i propri flussi.
- `intentKey` identifica il gruppo, oppure il digest canonico della pagina o del lotto ordinato. Il MCP registra **prima** del dispatch una prenotazione immutabile con scope, operazione, hash degli argomenti, generazione e fence. Il Gateway verifica tale prenotazione tramite interfaccia autenticata del MCP, anche su host separati. I riferimenti `requestId` devono appartenere al piano e allo stesso soggetto owner. Il chiamante non può sostituire profilo, operazione o argomenti.
- Per ogni tentativo il Gateway verifica workload, prenotazione corrente, mandato attivo, scadenza, generazione, diritto IAM corrente sul soggetto e sulla risorsa, catalogo e policy. Registra una nuova decisione. Il punto di ammissione all’inoltro è serializzato con la revoca. Un invio già ammesso che attraversa la revoca viene riconciliato come effetto in volo.
- Il Gateway costruisce la busta standard, rimuove header di prova forniti dal chiamante e firma **i byte che inoltra**, mediante la mediazione specifica della rotta. Per Semantic lega almeno purpose, metodo, path owner, capability, body hash, issuer, audience, workload, soggetto, tenant, scope, `iat`, `exp`. `exp ≤ min(iat+30 s,expiresAt)`. La prova fresca raggiunge direttamente Semantic. Ogni retry comporta nuova decisione e nuova prova. Semantic verifica di nuovo prova e policy owner. La preview conserva la sua mediazione specifica.
- Se l’IAM dell’installazione non permette di verificare l’autorità corrente a distanza, il Gateway blocca il dispatch. Un IAM OUF e un IAM preesistente devono superare lo stesso PET. Vietati rinnovo per semplice attività, riuso di ricevute scadute e deduzione di autorità dalla sola rete.

### C.3 — Budget, riconciliazione e `next`

Il profilo interno `analysis-run-v2` si seleziona esclusivamente lato server. Il ledger durevole conta chiamate, tentativi, oggetti, byte, tempo di esecuzione, tempo assoluto e concorrenza. Prenotazione atomica **prima** dell’invio, consuntivo una sola volta per `attemptId`. Una prenotazione con effetto incerto resta contabilizzata. I poll pubblici sul riepilogo consumano D-088. Il worker consuma il budget interno e rispetta anche i limiti effettivi di Gateway, Semantic e provider.

| Livello | Vincolo persistente |
|---|---|
| Piano/incidente | Massimi cumulativi di chiamate, oggetti, byte, tentativi e durata, inclusa l’esecuzione dei tentativi. Chiave logica stabile per scope e profilo. Job, replica, conversazione, nuova chiave e cambio di versione non azzerano il consumo. |
| Tenant/sorgente | Finestre condivise fra repliche, concorrenza finita, limite di coda e dei byte trattenuti. Ammissione con backpressure prima della saturazione. |
| Dipendenza/provider | Limiti di frequenza, raffica e concorrenza sul vero scope condiviso. Rispettare la lease owner soggetto-provider, lo stato di pausa e la capacità riservata a controllo, revoca e riconciliazione. |

Per i soli transitori espliciti: checkpoint durevole, backoff 5/15/60/300/900 s, jitter fino al 20%, `Retry-After` come minimo, fino a 128 tentativi e 24 ore per incidente o al limite inferiore del piano. Nessun lock, transazione o slot di esecuzione durante l’attesa. Stato di liveness osservabile. Isolare il minimo scope indipendente e riprendere gradualmente.

| Evento | Stato durevole e azione owner | `next` pubblico |
|---|---|---|
| Pressione temporanea o servizio transitoriamente indisponibile | Salvare `notBefore`, prenotazioni e budget residuo. Le altre dipendenze possono avanzare. | `POLL / ANALYSIS_BACKOFF` su `STATUS`, entro deadline. |
| Riavvio o nuova replica | Ritrovare piano, mandato, sessione, spese e checkpoint. Claim atomico con nuova fence. Rivalidare prima del dispatch. | `POLL / ANALYSIS_RUNNING` oppure il terminale già registrato. |
| Crash dopo l’invio, prima della ricevuta | Persistito lo stato di effetto incerto. Con `requestId` leggere lo status. Senza ID, riconciliare con **la stessa `Arguments.idempotencyKey`**, stesso soggetto owner e identico fingerprint, attraverso la deduplica atomica Semantic. Nuovo tentativo e prova, stesso effetto logico. | `POLL / ANALYSIS_RECONCILING` mentre è lecito osservare. Con conflitto o deduplica non dimostrabile, `BLOCKED / ANALYSIS_EFFECT_UNCERTAIN`, `OPERATOR`. |
| Revoca, cancellazione, grant ritirato | Invalidare generazione e claim. Fermare nuovi invii. Conservare effetti in volo, evidenze e consumo. Il worker tardivo non pubblica esiti. | `BLOCKED / ANALYSIS_MANDATE_REVOKED` oppure `ANALYSIS_CANCELLED`. `OPERATOR` o `HUMAN_THS` solo se esiste un’uscita owner pertinente. Nessun dato dopo revoca della lettura. |
| Mandato scaduto | Stop al dispatch e alle ripetizioni con effetti. Conservare il piano. | `BLOCKED / ANALYSIS_MANDATE_EXPIRED`. Una nuova autorizzazione esplicita può riprendere lo stesso scope entro il budget residuo. |
| Budget cumulativo esaurito | Quarantena del minimo scope, un incidente durevole aperto, contatori cumulativi e nessuna ripartenza automatica. Se coinvolge solo alcuni gruppi, completare gli indipendenti. | `BLOCKED / ANALYSIS_BUDGET_EXHAUSTED` sullo scope fermo; riepilogo `PARTIAL` quando applicabile. Uscita HUMAN solo tramite meccanismo governato disponibile. |
| Drift di identità, profilo, manifest o policy incompatibile; errore permanente o ignoto | Fermare lo scope. Conservare input e ultima evidenza valida. | `BLOCKED / ANALYSIS_SCOPE_DRIFT` o `ANALYSIS_OWNER_FAILURE`, `OPERATOR`. |

Errori Gateway del mandato: `400 ANALYSIS_INPUT_INVALID`, `403 ANALYSIS_AUTHORITY_DENIED`, `404 ANALYSIS_MANDATE_UNKNOWN` anche per riferimenti altrui, `409 ANALYSIS_STALE_EXECUTION`, `409 ANALYSIS_COMMAND_CONFLICT`, `410 ANALYSIS_MANDATE_EXPIRED`, `429 ANALYSIS_BACKOFF`, `503 ANALYSIS_AUTHORITY_UNAVAILABLE`. Un worker con fence obsoleta termina. Il MCP deriva il `next` dallo stato corrente del piano, senza arretrarlo.

Solo un HUMAN autorizzato può concedere **una nuova sessione finita** dopo esaurimento. Persistire attore, motivo, `decisionRef`, limiti, versione attesa e stessa identità d’incidente. Conservare storia, consumo cumulativo e chiavi owner. Una sola recovery attiva per scope. La nuova sessione verifica revoca e altre precondizioni.

L’audit collega `analysisId`, mandato, `decisionRef`, tenant e identità protette, digest profilo e manifest, `intentKey`, ordinali o loro riferimento durevole, operazione, hash della chiave owner, `attemptId`, generazione, fence, prenotazione, `requestId`, esito e `changeSeq`. Un incidente di dipendenza conserva il numero di piani, gruppi e ordinali colpiti. D-058 si applica a contratto, log, fixture e rapporti pubblici. Usare riferimenti opachi, codici e conteggi; escludere token, ricevute, dati CSV, segreti e coordinate di installazione.

## Rilascio, compatibilità e PET comuni

Lo sviluppo sui tre branch può procedere in parallelo contro le stesse fixture. D-090 colloca i rilasci **dopo i due giri E2E ripetibili sullo stesso candidato**.

| Passaggio | Ordine e condizione di attivazione |
|---|---|
| T0 + T1 | Semantic espande consultazione e attestazione dello zero. Nello stesso primo rilascio D-090 anticipa filtro di namespace prima dei GET e diagnostica del 429 con origine attestata oppure sconosciuta. Gateway adotta e qualifica le rotte governate. MCP attiva B, poi A. La baseline T0 può essere misurata in parallelo. |
| T2 | Verificatori owner e deduplica qualificati → Gateway con mandato e revoca → MCP con esecutore, contatori e budget attivati insieme. Prima dell’ultimo gate nessun dispatch autonomo. |
| D-080 per A/B/C | Migrazioni additive. Conservare endpoint singolo, buste 51j, rami `plan/read/step`, stati e vincoli SQL leggibili dal predecessore. Stato v2 in strutture separate o compatibili. I task v1 restano osservabili; importare soltanto esiti con prova sufficiente. Al rollback fermare e recintare i worker v2, conservare ledger e lavori sospesi. |
| D-071 e D-087 | Pipeline `ouf-deploy`, descrittori registrati al rilascio, attivazione e permessi mediante diff completo e conferma THS. Plan/apply/restore governati con digest. Ogni modulo dichiara predecessore esatto, dipendenze SQL, nuovi dati e punto di attivazione. Il plan rifiuta salti non supportati. |

| PET condiviso | Criterio di accettazione |
|---|---|
| A · pubblicato e schema | Per tutti e tre i tipi eseguire manifest → rotta materializzata → owner. Verificare anche la ricerca singola `DATATYPE`. Escludere draft, revisioni superate, set non pubblicati e risorse invisibili. Due forti con limite 1 restano `AMBIGUOUS`. Provare parità, ordine, lingue, contesto, duplicati, limiti byte e input alterato. |
| A/B · deduplica e completezza | Fixture con Unicode equivalente, accenti distinti, lingue invertite, dominio diverso e intestazioni duplicate su pagine lontane. Verificare 18/18, 1.000/1.000 e confine 1.024 ordinali. Zero discovery per `MATCH`, un solo job owner per residuo supportato. Pagina mancante, ricevuta `PENDING`, evidenza scaduta, vero zero e residuo `DATATYPE` danno esiti distinti. |
| B · consistenza e costo | PostgreSQL reale, lettori e writer concorrenti. Somma dei contatori esatta a ogni snapshot. Pagine senza salti né duplicati durante gli aggiornamenti. Replay senza incremento di sequenza. Provare cursor expiry, cambio tenant, revoca fra pagine e piano SQL indicizzato. Misurare byte e righe lette per `STATUS` e per pagina a 1.000 colonne. |
| C · autorità ed effetti | Orologio controllato. Provare scadenza a 30 s, body/path alterati, decisione negata, revoca in pausa e corsa revoca/inoltro. Interrompere prima e dopo l’inserimento owner e prima del commit MCP. Due repliche e un worker tardivo producono un solo job owner e un solo esito corrente. |
| C · resilienza | Outage di ore, restart, pressione su un tenant, quota di dipendenza satura, cancellazione, finestra rinnovata, esaurimento e due richieste HUMAN concorrenti. Verificare la stessa spesa, un incidente aperto, una nuova sessione ammessa, nessun reset e capacità di controllo disponibile. |
| Contratti e rollback | Validare ed eseguire ogni `next`, comprese alternative ed errori, contro destinatari reali di test. Provare soglia dei comandi, 15ª/16ª chiamata, deadline e anti-ciclo. Per ogni migrazione: PostgreSQL popolato → scritture candidato → immagine predecessore esatta con configurazione prevista → letture, scritture, retry → ritorno al candidato con checkpoint integri. |
| E2E e prestazioni | Chatbot senza istruzioni OUF, soli MCP e THS. Misurare da avvio a riepilogo su 18 e 1.000 colonne, a caldo, a freddo e con 1.000 intenti unici. Registrare p95 con e senza coda, turni modello, poll logici/fisici, locali, residui, GET utili/esclusi/ripetuti, attese e blocchi. Qualificare R-043 con 100 utenti e 3.000 processi. CI sorgente e fixture non sostituiscono prove client, connettore ed E2E. |

## Decisioni umane aperte e default raccomandati

| Domanda | Default raccomandato |
|---|---|
| Quanta capacità interna può concedere l’installazione? | Attivazione T2 dopo approvazione del profilo misurato. Partire con un piano attivo per soggetto, una richiesta attiva per soggetto-provider e capacità separata per controllo. Dimensionare chiamate, oggetti, byte e tempi sui PET a 1.000 colonne. Esplicitare per ogni quota tetto cumulativo, finestra condivisa e margine. |
| Il traguardo di 10–15 minuti vale anche per 1.000 intenti tutti remoti? | Usare come obiettivi condizionati 10 minuti con fino a 50 residui e 15 con fino a 80, da verificare al p95. Pubblicare separatamente il caso tutto remoto. Decidere cache tra fonti, ripresa per GET e regolazione del ritmo dopo la misura D-090. |
| Serve discovery remota per `DATATYPE` nella prima attivazione? | Abilitare subito la consultazione del pubblicato per `DATATYPE`. Mantenere il blocco motivato sui residui fino a qualificazione esplicita della discovery owner per quel tipo. |