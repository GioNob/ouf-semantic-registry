# Stato della verticale file–search per il documento PA

Data: 10 ottobre 2026. Verifica documentale successiva alla roadmap F0–F11, a supporto del documento narrativo richiesto dall’owner. Non è una nuova verifica live del VPS, né una nuova esecuzione dei test. [Evidenza strutturata](../evidence/file-to-search-documentary-status-20261010.json).

## Esito

La verticale ha componenti e prove concrete, ma il giro completo sulla combinazione applicativa corrente non è concluso. Input runtime, trust Java e contratto applicativo sono preparati; la ricevuta più recente resta APPLICATION_INPUT_CONTRACT_PREPARED_NOT_APPLY_READY. Montaggi, cutover coordinato e salute applicativa non sono dimostrati da questa ricevuta. L’installazione riutilizzabile su host pulito resta una consegna futura.

Le CI rilevate sono verdi nei controlli citati di Semantic Registry, Onboarding e MCP. Ingestion module e R2b/R2c/R2e sono rossi; UDP module è rosso. Altri controlli degli stessi repository sono verdi. I precedenti rilievi su worker e fixture MinIO non vengono aggirati e non sono reinterpretati come una nuova diagnosi dei log in questa verifica.

## Stato F0–F11

| Passo | Stato e prossimo criterio |
| --- | --- |
| F0 | DEFINED_PARTIALLY_ENFORCED: Same-nature identity invariant adopted and acceptance cases defined; all resolver branches still need qualification. |
| F1 | PREPARATION_NOT_CUTOVER: Runtime inputs, candidate public trust and application contract prepared; no completed application cutover or target health proof. |
| F2 | PARTIAL_SCOPED_PROOFS: Onboarding module/browser CI green; current whole file path and accepted format profiles still need acceptance. |
| F3 | PARTIAL: Registry definitions/publication and green CI; current provider discovery/application adoption on target not accepted end to end. |
| F4 | PARTIAL: Relationship mapping and main typed candidate filter exist; source-binding reuse, reclassification, compatible classes and executable strategies need audit. |
| F5 | PARTIAL_SCOPED_PROOFS: Versioned bundles and automatic R2a proof; current target human/grant/publication closure pending. |
| F6 | PARTIAL_BLOCKING_CI: Ingestion foundation exists; module and R2b/R2c/R2e CI red. |
| F7 | PARTIAL: Typed candidate lookup and source contributions exist; all identity branches and authority behavior not fully qualified. |
| F8 | PARTIAL: Pinned-profile late relationship reconciliation and focused tests exist; inverse semantics/cardinality/load not generally certified. |
| F9 | PARTIAL: Bounded authorized inbound/outbound related search exists; complete target channels still need acceptance. |
| F10 | NOT_COMPLETED: Full current multi-file acceptance has not been demonstrated. |
| F11 | PLANNED_WITH_COMPONENTS: Industrialization plan and preparation components; no reusable installer or independent clean-host acceptance. |

## Coerenza semantica e PET

- Il confronto di identità richiede prima natura compatibile e ambito autorizzato. Per default stessa classe canonica; equivalenza tra vocabolari solo con corrispondenza esplicita approvata e versionata. Stesso indirizzo non basta neppure fra due cinema.
- Il filtro principale UDP per match_key usa tenant e canonical_type. Il ramo di riuso SourceObjectBinding deve essere qualificato per isolamento e riclassificazione: non si estende la prova del filtro principale a tutti i rami. La presenza di WeightedIdentityPolicy non dimostra scoring runtime end to end.
- Registry pubblica la semantica, Onboarding configura mapping/bundle, Ingestion applica le trasformazioni, UDP risolve identità e relazioni. MCP può proporre e interrogare nel perimetro autorizzato; non sostituisce la decisione HUMAN prevista dai PET.
- La riconciliazione tardiva conserva il profilo originario. Un target mancante resta osservabile; più target non autorizzano la scelta arbitraria del primo. La query inbound non coincide con l’adozione di una nuova proprietà inversa ontologica.
- Strada, indirizzo, edificio, sede, gestore, sala ed evento sono entità distinguibili. Un file con soli toponimi non è automaticamente una banca dati di indirizzi completi. Una strada può attraversare più quartieri.
- Nessuna modifica agli stati dei 23 gap PET deriva da questo documento. Le prove circoscritte e i workflow verdi non vengono promossi ad accettazione dell’intero prodotto.

## Servizi culturali e limiti della visione

Il Cinema Lumière di Bologna è un esempio reale, con ingresso documentato in via Azzo Gardino 65 dalla Cineteca. L’associazione a un quartiere resta da verificare su coordinate e confini ufficiali. Schema.org distingue MovieTheater, PostalAddress e address; containedInPlace riguarda il contenimento fra luoghi e non va applicato indistintamente a un indirizzo.

Lo scenario numerico del documento PA è dichiaratamente ipotetico: 40.000 residenti, obiettivo 0,20 visite al mese per residente, 4.500 visite iniziali; divario 3.500. Un’unità da 200 posti × 20 proiezioni × 40% utilizzo offre 1.600 visite teoriche: tre unità sotto queste ipotesi, non necessariamente tre nuovi cinema. Utilizzo al 20% o 60% cambia il risultato rispettivamente a cinque o due unità. Non sono dati locali, una previsione validata o una misura del livello culturale. Il programma reale SI GIRA del Comune di Bologna mostra un’alternativa itinerante alle sole sedi permanenti; non è una prova di efficacia nello scenario.

L’analisi di fabbisogno richiede dati e modelli ulteriori: offerta, accessibilità, partecipazione, qualità della copertura, costi, incertezza e alternative. Visite non equivalgono a persone uniche; visitatori non equivalgono a residenti; dati mancanti non equivalgono a zero. Questa estensione non va dichiarata già accettata nella verticale file–search.

## Fonti pubbliche del documento

- [Cineteca Bologna Cinema Lumière](https://cinetecadibologna.it/luogo/cinema-lumiere/)
- [Comune Bologna SI GIRA](https://www.comune.bologna.it/novita/comunicati-stampa/torna-si-gira-il-grande-schermo-arriva-nei-quartieri-di-bologna)
- [ISTAT Statistiche culturali 2024](https://www.istat.it/tavole-di-dati/statistiche-culturali-anno-2024/)
- [Schema.org MovieTheater](https://schema.org/MovieTheater), [PostalAddress](https://schema.org/PostalAddress), [address](https://schema.org/address), [containedInPlace](https://schema.org/containedInPlace)


## Aggiornamento esecutivo — file prima delle API, 10 ottobre

Questo seguito distingue la fotografia documentale precedente dalle correzioni eseguite oggi. [Checkpoint strutturato](../evidence/file-loop-execution-checkpoint-20261010.json); [sequenza e decisione tecnologica](https://github.com/GioNob/ouf-deploy/blob/4dbe94da861e11a883602ce0b29fdafbcbf64609/releases/FILE_FIRST_EXECUTION_CHECKPOINT_20261010.md).

Ingestion 3a33c6c… è integrato in main e qualificato nei sei workflow correnti: module CI, SDK e R2a/b/c/e sono PASS. Il worker di test è isolato dalle altre run; MinIO è confezionato dal binario dello stesso rilascio con checksum. La scansione delle nuove immagini ha richiesto un aggiornamento OSS delle dipendenze, qualificato senza abbassare i gate. F6 supera dunque il blocco CI citato nella fotografia iniziale; rimane una prova di componente, non l'accettazione file-to-search sul target.

UDP c7a158a… è integrato in main con module CI, CRS/grid e SDK PASS. Il module registra 127 test, zero errori/failure e un test fuori dal contesto ordinario; i 14 nuovi casi di identità non sono saltati. Il riuso di binding, i replay materializzanti e le approvazioni HUMAN verificano tenant, natura e stato del target. Una riclassificazione va a review; il merge viene rivalidato all'esecuzione. La decisione immutabile conserva lo scope della proposta. F0/F4/F7 avanzano su questi rami, ma scoring ponderato, equivalenze approvate, tutte le superfici di governance e combinazioni multi-file restano da qualificare.

La dichiarazione runtime e la consegna fissata superano otto test nella CI deploy 38065415701. Conservano l'intero frame host storico e dichiarano soltanto i tre bind read-only approvati nel contratto; non realizzano OCI, mount o peer e non rinnovano autorità. Serve esecuzione sudo sul VPS per verificare la composizione dei due snapshot privati. F1 resta PREPARATION_NOT_CUTOVER e F10/F11 non sono completati.

L'owner conferma l'ordine: giro file completo e consolidato, quindi API native dei verticali tramite pull secondo v2.3. Il verticale non conosce ontologie/UrbanObjectId/capability OUF; estrazione/proiezione sono governate prima del trasferimento. Nessuna prova CI attiva automaticamente capability, lease, route o grant. La ricevuta target più recente resta quella sopra riportata; nessuna nuova salute live viene inferita.

## Security refresh qualification — 2026-10-10

The retained Semantic candidate source `403531a9df1cbc877078f8126fd1fc4ff18acea9` remains a separate historical signed artifact. Branch `codex/discovery-security-refresh-20261010`, qualified source `622614b0040cf11be2f6c7e3568733a488ca4ca8`, updates Tomcat to 11.0.26 and adds a fresh image scan with HIGH, CRITICAL and UNKNOWN failures, including unfixed findings, without exceptions. No Java, SQL, API contracts or retained Dockerfile bytes changed.

Module run [38065957754](https://github.com/GioNob/ouf-semantic-registry/actions/runs/38065957754) passed functional PostgreSQL tests (90 tests, zero failures/errors, two existing skips), recovery scripts, non-root container smoke and image scanning. Authorization, SDK and Discovery Gateway pairwise runs 38065957664, 38065957691 and 38065957683 also passed. Artifact `semantic-current-image-scan-38065957754` (ID 11674238309) reports no vulnerabilities at the selected severities; scanned CI image ID is `sha256:a19ee71a3f976087f3f4f3b0ea3609a28bcf12a41464519fcbf6b8bc00ea5aa8`. This is a bounded scan result, not a universal absence-of-vulnerabilities claim.

First run 38065793902 failed because the historical checksum register did not describe the already retained Dockerfile. The follow-up corrects that metadata to the unchanged recipe hash `da4d4fb4b5b677dea4e3d15427412cf87ddb80e84b9c42e2346d416adea5216b`; failed evidence is retained.

The refresh is source/CI qualification only. It does not inherit the old signed archive, target image, Java trust preparation, installation authority or transport closure. A fresh reproducible package and complete attestation/extended inventory remain required before target staging or cutover. The runtime declaration launcher still composes only the historical candidate bindings; it does not deploy this refresh.

Ingestion and UDP main documentation heads 98a845b453362ec35a55fbebf9156204cc804e10 and c786dbae32ce77a6c4a858e3f85181e45020c480 have now also passed every triggered workflow. Full target file-to-search acceptance, industrialized clean-host installation and the vertical API phase remain open.


## Rettifica di continuità VPS — 10 ottobre 2026

Il giro Cinema già consegnato non va rifatto: l'handoff storico conserva source/run SUCCEEDED, 8 ACKED e 8 materializzazioni riuscite dopo recovery HUMAN. Teatri upload/profile tramite MCP sono già riusciti. [Ricognizione completa, pin e controllo eseguibile](https://github.com/GioNob/ouf-deploy/blob/beef7e37c7579a0daf743276f6d63d5174fab175/releases/FILE_LOOP_VPS_CONTINUITY_20261010.md).

La frase precedente «resta da completare il giro sul VPS» non distingueva queste prove dai collegamenti ancora aperti. Search Cinema via Gateway/MCP restava esplicitamente non verificato nell'handoff; non dedurre né piena acceptance né necessità di riacquisizione. Nessun replay/riattivazione/recovery dei gate superati.

UDP live ereditato 83249a897eb4add4289b5181b3299f48ea4c0f99 contiene schema V34, motore class-neutral governato, review e recovery; main c786dbae32ce77a6c4a858e3f85181e45020c480 manca V22–V34 e componenti rilevanti. Le nuove correzioni main non sono una release sostituibile direttamente: vanno riconciliate sul ramo avanzato, mantenendo la regola subset/coverage e i contratti live. Ingestion presenta analoga divergenza R4a/main. F0 include dunque riconciliazione esplicita dei branch, non solo ricognizione main. Nessuna regressione a weighted legacy o richiesta di nomi/indirizzi come chiavi canoniche.

Il nuovo output operatore REPLACEMENT_RUNTIME_DECLARED_NOT_REALIZED/exit0 completa la preparazione della dichiarazione runtime nel perimetro storico. Snapshot nfggulwg, hash privato b9ee536c6cb4fefa4e6357716599cfdb34a38b7e11789013cf69096e5932709c; nessun mount/lifecycle/cutover/R9. Questo supersede il precedente ultimo checkpoint applicativo, senza certificare OCI realizzato o salute.


## Consolidamento effettivo delle baseline avanzate — 10 ottobre 2026

Le correzioni runtime e di isolamento identità sono state riportate sui sorgenti avanzati, preservando IAM, recovery, configurazioni frozen e motore governato. UDP bc336208ce41876f2854c3a4d8623fb6698bdcdd: cinque workflow PASS, 208 test senza failure/error e due skip preesistenti; sedici nuovi test eseguiti. Ingestion 8b908554314617298242eb2ae8312f734f55e817: otto workflow PASS, 118 test senza failure/error/skip, prova SQLite nativa e XLSX nel container reale. Scansioni fresche HIGH/CRITICAL comprensive di unfixed: zero finding in entrambe le immagini; la precedente immagine distroless Ingestion con nove HIGH resta evidenza fallita.

I main sono riconciliati con entrambe le linee come genitori, conservando documentazione/evidenze: UDP 48a86459fdeed38403838c5a2076b40cb082fe58, Ingestion 6d6777e20e0368c830d1e01de0494d9fa0197dbf. Tutte le 34/14 migrazioni storiche sono inalterate, con gate automatico di continuità PASS sui nuovi main. I workflow di riconciliazione vanno distinti dalle qualifiche dei candidati; nessun deploy segue automaticamente.

[Report, workflow, image ID e limiti](https://github.com/GioNob/ouf-deploy/blob/1493bf6baca064bffca467cf6e8a4b7a97e9a1b9/releases/LIVE_BASELINE_QUALIFICATION_20261010.md). F0/F4/F7 avanzano sulle prove class-neutral/same-nature, binding/replay e revisione HUMAN senza promuovere il legacy weighted a default; F6 supera il blocco componente sulla baseline avanzata. F10/F11 rimangono aperti.

Letture correnti Gateway/MCP: status pubblico MCP HEALTHY; ricerca MovieTheater vuota su entrambi i profili disponibili, ricerca Semantic MovieTheater vuota, ingestion.status Cinema negato. Questo non cancella il PASS storico 8/8, non prova assenza dei cinema e non chiude Search. Non cambiare grant o tenant per aggirare i risultati, non riacquisire la fixture. Occorre una prova di visibilità/owner nel perimetro corretto. La dichiarazione runtime target nfggulwg è già acquisita, non richiede replica del vecchio comando.


## Prova corrente positiva Semantic e Search — 10 ottobre 2026

La lettura dell'approvazione storica chiarisce la natura: cinema#Cinema è subClassOf schema.org/MovieTheater, non il medesimo codice canonico. La ricerca di schema.org/MovieTheater vuota era corretta per la richiesta esatta e non indicava assenza/deny dei Cinema. Query Gateway/MCP di https://api.ouf-lab.it/semantic/cinema#Cinema: otto ACTIVE distinti su tre pagine 3/3/2, cursor finale null, partial=false e due proprietà pubblicate. Nessuna nuova ingestion, modifica di grant, replay o recovery. F9 avanza con prova positiva attuale; minimizzazione negativa, cursor invalido owner e audit restano aperti. Il tentativo invalid-cursor viene fermato dal budget MCP/retryable=false, non aggirato.

semantic.get sui pin conservati restituisce la stessa ontologia ACTIVE e 17 statement RDF con hash e publication checksum corrispondenti; semantic.search ONTOLOGY la trova. CLASS vuoto non certifica assenza dei termini contenuti nello snapshot RDF. [Ricevuta osservazionale e limiti](https://github.com/GioNob/ouf-deploy/blob/d4a9e3122a22179fe5f357924e80a174787e09cd/evidence/current-canonical-search-read-20261010.json).

Tutti i workflow sui main riconciliati sono PASS. I tre pacchetti Semantic/Ingestion/UDP sono costruiti nella pipeline 38069730894, con digest delle basi risolti, scan legato a immagine, sorgenti/JAR/Docker-save e checksum; Ingestion ripete la prova SQLite/XLSX nel nuovo container. [Pacchetti unsigned e passaggio operatore](https://github.com/GioNob/ouf-deploy/blob/d4a9e3122a22179fe5f357924e80a174787e09cd/releases/FILE_LOOP_OFFLINE_PACKAGES_20261010.md). Non sono ancora firmati/importati né autorizzano apply. Per proseguire verso custodia target serve output del nuovo launcher di staging e lettura nativa sudo; nessuna richiesta di ripetere i vecchi gate VPS.


## Custodia target e provenienza dei pacchetti — 10 ottobre 2026

L'operatore ha completato staging e lettura metadata: tre ZIP e checksum interni PASS, immagini non importate, nessun lifecycle/apply. Directory /home/oufadmin/ouf-file-loop-offline-stage.LMawhAuO. Le immagini effettivamente confezionate sono Semantic e826bd9769a72e930e356f72c1c244007f9a34d065db94ca8113b064d10d8b85, Ingestion 98af9d774e446ce621128a52bfa1f9faaa096052cdc185f17dc81f1ea76e9a05 e UDP 7a97979286113c4e3ef6bae87e1bf2d54d2f7195d447ce43b9329f3b90899d28. Non confonderle con gli image ID delle precedenti CI di componente.

I container storici restano running e le generazioni sono stabili nella lettura. R9 è invece failed, MainPID=0, stessa InvocationID ba95ba7239664789ac68430107ac6dc8, Restart=no: il precedente lease attivo non è una prova attuale. La causa non è ancora letta nei record protetti. Non riavviare né riapplicare il claim/consenso consumato; eventuale nuova autorità resta distinta.

La pipeline publisher [38071155443](https://github.com/GioNob/ouf-deploy/actions/runs/38071155443) verifica e firma gli stessi ZIP già sul VPS, senza rebuild: checksum, sorgenti, inventario, SQL nei JAR (10/14/34 migrazioni), SDK di produzione e scansioni sono coerenti. Le firme Cosign e i receipt sono sidecar separati: i record originari restano unsigned. L'API GitHub di conservazione attestation non è disponibile per questo repository privato personale; il tentativo fallito resta documentato, il repository rimane privato e la verifica Sigstore indipendente è qualificata. Provenienza publisher non significa autorità d'installazione o apply.

La pipeline [38071443267](https://github.com/GioNob/ouf-deploy/actions/runs/38071443267) estrae e firma soltanto i certificati pubblici dalla nuova immagine Semantic. Baseline SHA256 98d34a90fca2688ef5674862d2a484e09e5ca25d2f07c5d654aa28f1581f3419: identica alla baseline storica. Il riuso dei bytes del truststore preparato richiede ancora il confronto read-only sul target di baseline, CA, manifest e store; non eredita l'autorità storica.

Il launcher fissato a Deploy 8226af642d7f020bff4a345a0fa605c301d82443 accorpa verifica delle firme, confronto read-only dei sei file protetti e diagnosi R9. Scarica solo sidecar e client verificatore, non le immagini; non importa immagini, non acquisisce lock, non interroga DNS, non modifica firewall e non riavvia servizi. [CI di consegna 38072056620](https://github.com/GioNob/ouf-deploy/actions/runs/38072056620): PASS, dieci test e verifica checksum/sintassi. L'esecuzione sul target resta pendente e richiede l'operatore sudo. [Report ed evidenze](https://github.com/GioNob/ouf-deploy/blob/8226af642d7f020bff4a345a0fa605c301d82443/releases/FILE_LOOP_TARGET_PACKAGE_CONTINUITY_20261010.md).

F1 resta preparazione senza cutover; F9 conserva la prova corrente positiva 8 Cinema; F10/F11 restano aperti. Non ripetere il giro Cinema né il profiling Teatri. Prima consolidare file e installazione ripetibile, poi API native pull v2.3.
