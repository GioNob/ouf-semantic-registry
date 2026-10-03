# OUF · handoff operativo R4a (27 settembre 2026)

**Aggiornamento 29 settembre:** questo è uno snapshot storico. Per lo stato live
dopo il preflight, il comando Ingestion esplicitamente non eseguito e tutti i
gate residui, leggere l'[handoff aggiornato](OUF_HANDOFF_2026-09-29_R4A_PREFLIGHT_TO_INGESTION.md).

Questo documento è destinato a una nuova chat senza contesto. Leggere prima il **Reality Baseline Package / PET 1.7** allegato alla nuova chat, poi questo handoff. Se una frase qui confligge con Blueprint L0 v0.3, Cross-Module Alignment Matrix v1.7 o PET L1 vigenti, prevale la baseline. Nessun output sotto costituisce da solo un'attestazione di release.

## Obiettivo del prodotto

L'utente chiede in qualsiasi chatbot compatibile con MCP di importare **un file**. Il picker OUF acquisisce il file attraverso il Gateway, Onboarding determina formato e profilo (CSV, XLSX, GeoPackage o errore per formato non supportato), Semantic/Registry propone semantica e vocabolari, l'utente rivede e approva le decisioni nel THS, Onboarding attiva la configurazione, Ingestion esegue e consegna alla UDP, UDP risolve l'identità canonica e serve la ricerca governata. La capability è neutrale rispetto al canale; widget/picker e handoff alla chat sono adattatori UX. Non costruire un recuperatore di allegati specifico per ChatGPT, né chiedere di copiare l'Asset ID come UX ordinaria. Operazioni HUMAN protette rimangono nel THS e l'owner riconvalida le decisioni; MCP non approva autonomamente.

L'utente è stato sovraccaricato da molti comandi SSH e regressioni. Continuare con script idempotenti e versionati, verifica compatta PASS/BLOCKED e rollback automatico dove possibile. Non ripetere ricognizioni già documentate senza un rischio concreto. Ogni comando VPS deve essere un blocco completo copiabile, con directory corretta, revisione fissata, protezione dei segreti e output atteso. Mai chiedere token, credenziali o CSV in chat. Il lavoro manuale attuale prova la filiera: deve diventare capability e flusso automatico.

## Autorità e divisione dei moduli

| Responsabilità | Owner | Vincolo |
| --- | --- | --- |
| Identità, policy, grant | Authorization, co-locata con Onboarding | Gateway controlla capability, owner applica autorizzazione fine |
| Confine di rete, routing, streaming | Gateway | Nessun accesso diretto del chatbot a DB/MinIO/owner |
| Intake, profilo, mapping e configurazione fonte | Source Onboarding / THS | Nessuna approvazione implicita dal tool MCP |
| Ontologia, vocabolari e pubblicazione semantica | Semantic Registry / THS | Riferimenti versionati e approvazione HUMAN |
| Esecuzione, CDE, handoff e watermark | Ingestion Runtime | ACK durevole downstream separato dalla materializzazione |
| Identità canonica, object resolution, merge e serving | UDP | La chiave tecnica della riga sorgente non è l'identità canonica |
| Interfaccia agente | MCP | Tool tipizzati e bounded, capability neutrale, nessuna autorità HUMAN autonoma |

## Evidenza live ricevuta dall'operatore

Le righe seguenti sono output VPS forniti in chat, non una nuova interrogazione del server. Data dell'ultima evidenza: 27 settembre 2026. Riconfermare l'immagine, la policy e le route soltanto prima di un nuovo rollout.

| Area | Ultima evidenza | Limite |
| --- | --- | --- |
| APISIX-Runtime | Probe isolato: `FIRST_BYTE_BEFORE_CLIENT_FINISH=true`, HTTP 204, route temporanea rimossa | Non dimostra 413/no asset parziale sulla route prodotto; digest precedente `sha256:84e6b5e787e9f889ebff88161cb9a16599bafcffa236c6b54c7f779a0655940d` |
| IAM / Authorization | Quattro scope HUMAN managed-file e uno scope SERVICE di lettura object-storage creati e verificati; grant SERVICE e HUMAN aggiunti; `ouf-admin` HUMAN token PASS; ultimo `ACTIVE_POLICY_REF=ouf-lab-authorization:28`, capability semantiche 7 aggiunte | Dopo cambi live verificare il ref; sessione `kcadm` era scaduta e fu recuperata |
| Object storage | Bucket `ouf-managed-files`, policy limitata al prefisso e credenziali app verificate; MinIO live immutato | La modifica del download binario MinIO in CI UDP non riguarda il VPS |
| Onboarding / picker / MCP | Rollout picker e chat handoff PASS; upload reale di un CSV ha registrato l'asset sotto; route Gateway e owner-key repair PASS; Semantic human routes e search via Gateway PASS | Handoff UX tra host diversi richiede acceptance; non confondere PASS di rollout con R-SMOKE |
| Semantic | Proposta RDF validata, approvata da HUMAN e pubblicata; dettagli sotto | Il solo Semantic non crea oggetti UDP |
| Ingestion / UDP | Nessuna evidenza che **questo** file sia stato elaborato fino a UDP e ricerca | R-SMOKE rimane **OPEN** |

Il CSV dell'esercizio (`cinema_trieste(1).csv`) aveva 509 byte, BOM UTF-8, colonne `cinema`, `indirizzo`, otto righe, SHA-256 `a07c2dcdc21aa9a23fb5585a69d52031dc08010d251bf39bfa67c8e0962c6e1a`. Non pubblicare il contenuto o URL temporanei. Asset live `8ec8ae90-808a-4d9e-907c-d56de119e376`; profilo `4462692b-9c85-446b-b6fd-779f01eab64d`. Le **proprietà** sono mappate a IRI semantici governati; i **valori** sono testo libero, senza code list controllata, e richiedono normalizzatori approvati per essere confrontati. Non sono chiavi univoche. Il nome del cinema **non** è chiave del record.

Semantic ID `https://api.ouf-lab.it/semantic/cinema`, classe allineata a `schema:MovieTheater`, proprietà nome/indirizzo allineate a `schema:name` e `schema:address`; revisione `51706bed-81e4-4306-aca1-70119821727d`, set pubblicato `f92a2e17-30c9-456f-bb12-63afa84f41e6`, manifest `a711d0428f1cbe24c73cbf0fa5cabfcb52f85df774e7238d884e7f83f41b84e9`, RDF SHA-256 `4340986102db6e47345dd8157734d9db83b928edd94485f1b9a5b9e81c497a2e`. Output: `SEMANTIC_HUMAN_PUBLICATION=PASS`.

Onboarding DRAFT `managed-cinema-8ec8ae90`, versione `68394f42-5c82-4127-a1f3-126516665749`, **non submitted né activated**. La source-row identity `MANAGED_DETERMINISTIC` è derivata da asset e ordinale, quindi un riordino del file può cambiare quella identità tecnica. La UDP deve risolvere l'identità canonica separatamente. Ultimo preflight live: `REVIEWED_DRAFT_MATCH=true`, `UDP_RESOLUTION_CONFIGURED=false`, validazione zero errori/avvisi su quel runtime. Una correzione successiva del validatore Onboarding che rifiuta profili execution/UDP mancanti è in codice CI, non attestata su VPS: non usare il vecchio PASS come permesso di attivazione.

## Punto esatto di arresto e prossima unità di lavoro

**Non attivare il DRAFT cinema né avviare Ingestion** con una regola UDP basata su un solo `matchProperty` o su `resolution.weighted` non eseguita. Il prossimo lavoro è il contratto e motore di identità canonica **generale** in UDP, poi il suo allineamento con il contratto pubblicabile di Onboarding e i profili di Semantic/Ingestion. La PR UDP [#34](https://github.com/GioNob/ouf-udp-object-resolution/pull/34), branch `codex/r4a-ambiguous-review-resume`, implementa il prerequisito di quarantena/riavvio e rifiuta un profilo weighted con `UDP_WEIGHTED_RUNTIME_UNAVAILABLE`; non implementa il motore generale e non risulta distribuita. L'issue [#35](https://github.com/GioNob/ouf-udp-object-resolution/issues/35) traccia il lavoro generale. La vecchia PR #33, chiusa, codificava campi/esempi specifici: non riprenderla.

La decisione concordata con l'utente vale per **ogni** classe e fonte:

1. Un mapping verso vocabolario controllato o proprietà semantica condivisa dice *che cosa significa* un dato; non dimostra che quel valore identifichi da solo un oggetto. Confrontare proprietà e relazioni condivise, con normalizzatori tipizzati e versionati; la mancanza di un campo è neutra. Conservare versione, provenienza, copertura ed evidenza positiva/negativa.
2. La policy d'identità pubblicata dichiara ruolo probatorio, comparatore, scope, cardinalità, unicità giustificata e semantica temporale/spaziale pertinente. Una relazione molti-a-uno non rende identici i figli. Frequenza o selettività di un valore serve al recupero di candidati e alla spiegazione, **mai** a conferirgli automaticamente autorità identificante mediante soglia.
3. Mantenere una binding sorgente conosciuta per continuità e provenienza, distinta dall'identità canonica. Generare candidati con predicati indicizzati e bounded; overflow `RESOLUTION_TOO_BROAD`, nessuna scelta del primo risultato.
4. Auto MATCH solo se una regola sufficiente approvata soddisfa le premesse ed esclude concorrenti. Un punteggio weighted ordina/spiega candidati, non autorizza da solo un merge. Auto NEW solo secondo policy esplicita limitata alla fonte, con possibilità di merge governato successivo. Ambiguità reale o conflitti irrisolti -> `REVIEW_REQUIRED`, audit e decisione HUMAN.
5. Due oggetti con 5 e 12 proprietà confrontano anche solo le quattro semanticamente comuni; il match confermato unisce i contributi non conflittuali (13 proprietà nell'esempio). Su valori condivisi incompatibili scegliere per authority di proprietà governata oppure chiedere all'umano quali tenere, preservando lineage. Per upload interattivo mostrare la revisione subito; per acquisizione SUO schedulata quarantena durevole fino al ritorno dell'umano, senza bloccare gli altri job.
6. Prima di schedulare una fonte esercitare **lo stesso motore eseguibile** su osservazioni rappresentative/adversariali, invarianti all'ordine e ai nomi dei campi, e misurare ampiezza candidati e volume review. Adeguare la policy se produce troppe ambiguità. `semaforo`, indirizzi ripetuti, controller condivisi e classi diverse sono soltanto fixture di regressione, mai rami speciali nel codice.

Il durable ACK UDP precede la risoluzione; la review per record non annulla l'ACK né il watermark Ingestion. La revisione HUMAN approva una binding e riaccoda il job con contratti storici fissati; decisione originaria append-only. Non mantenere una transazione aperta mentre attende una persona. Una decisione dismiss lascia il record in quarantena. La quarantena contrattuale Ingestion antecedente all'handoff è diversa.

## Repository e documenti da aprire per primi

| Repository / branch di lavoro | Documenti o riferimento |
| --- | --- |
| [Semantic Registry](https://github.com/GioNob/ouf-semantic-registry/tree/codex/r4a-smoke-semantic-inventory) | `docs/OUF_ROADMAP_PET_1_7.md`, `docs/installation/OUF_INSTALLATION_MANUAL.md`, `docs/R4A_CINEMA_SEMANTIC_PROPOSAL.md` |
| [Source Onboarding](https://github.com/GioNob/ouf-source-onboarding/tree/codex/r4a-authorization-catalogue) | `docs/R4A_MANAGED_CSV_INTAKE.md`; configurazione, picker, rollout automatizzato e validatore del DRAFT |
| [Gateway](https://github.com/GioNob/ouf-api-gateway/tree/codex/r4a-object-search) | `docs/R4A_MANAGED_FILE_STREAMING_GATE.md`; route esatte, snapshot e prove negative |
| [MCP picker](https://github.com/GioNob/ouf-mcp-server/tree/codex/r4a-managed-file-rollout) | PR #46, `internal/kernel/picker_handoff.html`, `scripts/r4a_attachment_rollout.py`; il vecchio adapter attachment in PR #45/#46 non va abilitato |
| [UDP](https://github.com/GioNob/ouf-udp-object-resolution/tree/codex/r4a-ambiguous-review-resume) | `docs/R4A_RESOLUTION_REVIEW_GATE.md`, PR #34, issue #35 |
| [Ingestion](https://github.com/GioNob/ouf-ingestion-runtime) | PET Ingestion v1.3 e contratti handoff/version pinning; nessun esito per questo asset |

I nomi delle branch non attestano merge né deployment. Confrontare HEAD, CI e immagini live prima di attribuire una modifica al VPS. Lo script read-only [`r4a_handoff_snapshot.py`](https://github.com/GioNob/ouf-semantic-registry/blob/codex/r4a-smoke-semantic-inventory/scripts/r4a_handoff_snapshot.py) comprime l'inventario Docker senza esporre secret: dal checkout Semantic eseguire `git show <COMMIT_VERIFICATO>:scripts/r4a_handoff_snapshot.py | sudo python3 -`. L'inventario non verifica policy, route o DB. Lo script di rollout è la fonte operativa per la configurazione del relativo modulo; non replicare una lunga serie di comandi imperativi in chat. I backup di route, container e DB sono stati mantenuti durante i rollout precedenti; non cancellarli per “pulizia” durante R4a.

## Gate residui per dire R-SMOKE PASS

- Contratto d'identità class-neutral governato e implementato nella UDP, accettazione DB/Gateway/HUMAN di ambiguità e resume; allineamento Onboarding/UDP e attivazione solo di profili eseguibili. PR #34 è un prerequisito, non chiusura del gate.
- Profilo/mapping proposti per l'asset esistente, revisione HUMAN, configurazione Onboarding approvata e ACTIVE con riferimenti semantici fissati. Eseguire Ingestion su quella versione, osservare ACK durevole e materializzazione UDP, verifica del numero di oggetti, provenienza e search attraverso Gateway e MCP/altro canale autorizzato.
- Probe sulla route prodotto per primi byte prima della fine del client, richiesta oversized 413 senza asset parziale e risorse bounded, tipo supportato/non supportato, checksum mismatch, anonimato 401/403, idempotenza e rollback. Il probe isolato APISIX non sostituisce queste prove.
- Acceptance del picker/handoff in un chatbot MCP compatibile e in un secondo canale, senza richiedere copia manuale dell'Asset ID, nessuna regressione del login OUF. Rispettare audit, authority HUMAN e segreti. Documentare limiti host-specific solo come adattatori, non come contratto OUF.
- Collaudi recovery, backup di oggetti, trasporto verificato fra reti separate e gli altri gate PET rimangono distinti dal percorso lab. Non chiamare “release” un test isolato o una PR verde.

## Evidenze e cautela sullo stato del codice

La PR UDP #34 ha avuto tre workflow GitHub Actions conclusi con successo sia sul commit eseguibile `af28582819417f1bc66c4877e236fa3b8a4810f5` sia sul successivo commit documentale `1c31c4ba0969a11b6fff872467e6bb3aabd877b6` (UDP module CI, Authorization SDK pairwise, CRS); verificare comunque lo stato del nuovo HEAD prima di un merge. Il percorso CI usa il binario MinIO ufficiale verificato con SHA-256 fissato (`RELEASE.2025-09-07T16-13-09Z`, `7c5bd8512c6e966455b1d198209358b2d191c77a83ab377c4073281065fb855f`) per evitare rate limit registry; non cambia il MinIO live. Le evidenze di test non provano il flusso HUMAN reale fino a search.

Le PR/issue storiche spesso riportano uno stato live precedente: non sovrascrivere gli output VPS recenti con i loro body. Al contrario, un output `PASS` di deploy non dimostra che una modifica non ancora distribuita sia attiva. Se una informazione manca, annotare **non verificato** e fare un controllo mirato una sola volta.

## Continuità con l'handoff iniziale e R-INSTALL

L'[handoff del 25 settembre](https://github.com/GioNob/ouf-semantic-registry/blob/docs/r4a-2026-09-25-handoff/docs/handoffs/OUF_HANDOFF_R4A_2026-09-25_SCOPE_BOOTSTRAP_NEXT.md) contiene cronologia dettagliata, InstallationConfiguration r5, scope Keycloak, precedenti container/rollback, acceptance di ricerca e supply chain. I suoi punti operativi `plan/apply` e i riferimenti policy `:22` sono **superati** dagli output 26–27 settembre in questa chat; non eseguirli come prossimi comandi. Conservare i vecchi backup elencati là, oltre agli snapshot di route/container/DB stampati dai rollout successivi. La lettura del 25 settembre è utile per motivare le decisioni, non per dedurre lo stato live.

R-INSTALL resta **OPEN**. Il percorso di installazione deve diventare un orchestrator riproducibile da manifest d'installazione: riferimenti ai secret, IAM/capability/grant, Gateway route materialization, build e deploy dei sei moduli, clean install, upgrade, backup/restore, rollback e CI d'installabilità. Gli script R4a già creati sono componenti di tale percorso e non provano una nuova installazione autonoma. Le vulnerabilità di processo viste qui (route anonima provata con payload invalido, regressione owner-key, origin picker fissata al lab, comandi spezzati e sessione `kcadm` scaduta) sono regressioni da impedire con automazione, non check manuali da ripetere per sempre.

L'acceptance R-SMOKE originaria include almeno tre Urban Object reali dello stesso tipo, ricerca autorizzata con un oggetto da minimizzare, due pagine, cursor, partial, invalid cursor, authorization di proprietà e audit. L'asset cinema ha otto righe, ma nessun oggetto UDP attestato. Dopo il motore d'identità generale, verificare questi risultati tramite il Gateway e il client MCP, mantenendo i pin storici e le evidenze del file.

## Revisione metodologica del 27 settembre, sera

Il PET ZIP allegato aveva 323 checksum validi su 323. I branch R4a di Gateway, Onboarding, Semantic, UDP e MCP sono avanti a `main` e le PR principali sono ancora aperte; Ingestion non ha un branch R4a. I workflow osservati dei cinque branch R4a e del branch R2f Ingestion risultavano `success` sui rispettivi HEAD **prima** degli ultimi edit documentali/codice: controllare i nuovi commit dopo la modifica. I PASS live restano output dell'operatore e non sono stati ricampionati sul VPS.

Sono state aggiornate le note delle PR #37 Onboarding, #51/#53/#54 Gateway, #24/#25/#26 Semantic, #27 Ingestion, #45/#46 MCP, #33/#34 UDP e gli issue MCP #43/Gateway #52. Gateway #51 non contiene ancora tutte le correzioni dell'installer #53; #54 deriva dalla linea picker/owner-key. Semantic #25 sovrappone roadmap/manuale a #26; il provisioner di #24 è già presente identico in #26. Non mergiare separatamente queste linee senza riconciliare il delta. PR MCP #46 resta draft con conflitto di merge: contiene codice storico di fetch diretto host, bloccato dal PET, oltre al picker. Il widget del branch è stato corretto per derivare il picker prefix dall'URL d'installazione; test simulati MCP Apps e ChatGPT passano anche con un'origine diversa dal lab. Questo **non** prova un secondo chatbot live e non è un deploy. Sul nuovo HEAD MCP #46 la CI PR non era ancora attestata. Il documento [audit finale](https://github.com/GioNob/ouf-semantic-registry/blob/codex/r4a-smoke-semantic-inventory/docs/audits/OUF_R4A_FINAL_AUDIT_2026-09-27.md) registra fonti, difformità, correzioni e gate.

### Correzione CI emersa nell'audit finale

Il commit Semantic `b46bb276409c102b5fc0609ef56c614cd2e856d3` ha avuto tre workflow SUCCESS ma **Semantic Registry module CI FAILURE**: il checksum congelato di `.github/workflows/module-ci.yml` non era stato aggiornato dopo l'aggiunta del test read-only. Il job si è fermato prima dei test. Il commit `65ce2bfddb7c820a44aeced8fa66d95d3c8ace5f` ha corretto `evidence/source-checksums.txt`; verificare la CI di quel nuovo HEAD prima di considerarla verde. Per MCP #46 resta non attestata la CI del nuovo codice widget.
