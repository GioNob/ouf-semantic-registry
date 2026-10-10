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
