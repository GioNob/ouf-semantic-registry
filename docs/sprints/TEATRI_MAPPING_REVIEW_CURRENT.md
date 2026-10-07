# Teatri: proposta di mapping per il file già caricato

Stato: granularità confermata dall'utente il7ottobre2026 alle11:08:21Europe/Rome: una riga rappresenta un teatro, capienza di singola sala qualificata separatamente. La conferma riguarda soltanto questa scelta. Altri mapping/accesslabel/identità/pin e pubblicazione restano da completare; nessuna DRAFT o ACTIVE creata.

L'utente ha autorizzato la rilettura del profilo il 7 ottobre 2026 alle 07:52:40 Europe/Rome. La chiamata source.file.preview tramite ouf-admin ha restituito il profilo esistente: asset 6609b245-86ed-4315-8ce0-73f2a8555bf3, profile 7984c39c-7396-4248-ab0a-f2efc390b49c v1, CSV UTF-8, separatore punto e virgola, 13 righe e 20 colonne. Nessun nuovo upload o profiling. Non conservare sample/valori privati in questo documento.

## Mappatura proposta

| Campo | Significato proposto | Trattamento/decisione |
| --- | --- | --- |
| nome_teatro | Nome del teatro | Testo; candidato per il confronto, non chiave canonica |
| tipologia | Tipo di teatro dichiarato | Preservare testo; dizionario/versione e corrispondenze da approvare |
| toponimo | Tipo di strada nella fonte | Componente indirizzo; non nome geografico del teatro |
| nome_indirizzo | Nome della strada | Componente indirizzo |
| civico | Numero civico | Testo nullable; preservare suffissi |
| cap | Codice postale | Testo; non quantità LONG; nessuna ricostruzione di zeri non osservati |
| citta | Località dell'indirizzo | Testo; riferimento territoriale da risolvere |
| provincia | Provincia dichiarata | Codice/testo; non ID territoriale inferito |
| latitudine | Latitudine dichiarata | Decimale nullable; coppia con longitudine |
| longitudine | Longitudine dichiarata | Decimale nullable; nessuna inversione implicita |
| sistema_riferimento | CRS dichiarato | Validare prima di costruire geometria; non certifica accuratezza |
| precisione_coordinate | Precisione/metodo delle coordinate | Preservare testo; non convertirlo in precisione numerica senza regola approvata |
| capienza_posti | Capienza dichiarata | Intero nullable; qualificare teatro/sala prima di attribuzione canonica |
| spettacoli_stagione | Numero di spettacoli riferito alla stagione | Intero nullable; associato al periodo |
| stagione_riferimento | Periodo della misura spettacoli | Testo nullable; intervallo soltanto dopo interpretazione approvata |
| note | Annotazioni della fonte | Testo nullable; review di classificazione prima di pubblicazione |
| fonte_indirizzo | Provenienza dell'indirizzo | Metadato per-field; mai usare come identità del teatro |
| fonte_coordinate | Provenienza delle coordinate | Metadato per-field nullable |
| fonte_altri_dati | Provenienza degli altri dati | Metadato nullable; non autorità automatica |
| data_verifica | Data di verifica della fonte | Data; non validFrom e non data di acquisizione |

## Classe e riferimenti

Le ricerche bounded nel Registry corrente per Theatre, Teatro, teatr e Cultural non hanno restituito candidati. Questo non è un censimento completo. Non usare Cinema/MovieTheater per analogia.

La documentazione ufficiale [Cultural-ON](https://dati.cultura.gov.it/cultural-ON/ITA.html) include una classe Teatro e tratta sedi, indirizzi e geometrie tramite entità collegate. È un candidato per la review nazionale; non è stato importato, adottato o pubblicato in OUF. [Schema.org PerformingArtsTheater](https://schema.org/PerformingArtsTheater) è un ulteriore candidato documentato. La consultazione web prepara la review: non sostituisce la Discovery/adoption governata OUF né conferisce un pin ACTIVE al mapping. Le schede web consultate non sono un artefatto immutabile accettato.

[postalCode](https://schema.org/postalCode) prevede un valore testuale e viene usato sull'indirizzo; le proprietà delle entità collegate non devono essere appiattite sul teatro senza un modello approvato. Non inserire IRI placeholder come se fossero riferimenti pubblicati. Nessuna equivalenza tra Cultural-ON e Schema.org è dichiarata.

## Scelte concrete da presentare nella review

- Proposta per questa prova: una riga descrive il teatro registrato dalla fonte; la capienza riferita alla singola sala rimane qualificata e non diventa la capienza dell'intero teatro. Granularità confermata dall'utente il7ottobre11:08:21Europe/Rome.
- Per un unico asset immutabile è disponibile l'identità source ASSET_AND_ROW_ORDINAL, già implementata. Evita di dichiarare durevole nome_teatro; non è identità canonica UDP e non fornisce continuità tra upload distinti. Nome e indirizzo restano candidati di confronto canonico da governare nel profilo UDP.
- Le 20 colonne vengono considerate esplicitamente. Nessuna esclusione o label OPEN automatica è stata applicata; INCLUDE/EXCLUDE e classificazione per campo saranno presentati con il mapping eseguibile.
- Coordinate mancanti, precisazioni sulle sale e discrepanze dell'indirizzo devono rimanere visibili; non normalizzare silenziosamente i dubbi.

## Collegamento mancante al giro completo

Il tool corrente source.onboarding.create crea un DRAFT base. Nel codice Onboarding 6340d5bf120e09b47c32177656e2c377a4c03640 il validator richiede anche contratti managed di esecuzione e publication binding prima della pubblicazione. Il DRAFT base non è configurazione pronta all'attivazione. Riutilizzare il percorso di completamento già usato per Cinema, con la nuova semantica e profilo identità; non simulare attestazioni positive.

Aggiornamento7ottobre: CinemaUDP letto davvero da ChatGPT,8oggetti su4pagine,zero duplicati,partial=false; vecchio503 risolto con sola correzione hostname. Passi successivi: decisione HUMAN sulla granularità teatro/sala → riferimenti semantici adottati/pubblicati e pin esatti per Teatri → configurazione completa/review HUMAN/compatibilità Ingestion e UDP → un run e lettura finale. Il diniego ingestion.status resta un blocco distinto di osservabilità del percorso; nessuna modifica IAM/policy eseguita.

## Richiesta discovery preparata e collegamento verificato

[Intent strutturato](TEATRI_DISCOVERY_INTENT_CURRENT.json) preparato, non inviato, senza valori dei file. Fonte codiceRegistry02b266538895eb952de02db28aa493948df7079d: DiscoveryApi esiste su /api/semantic/v1/discovery-requests; inputeffettivo requestedArtifactType/intent/preferredLanguages. OpenAPI riporta erroneamente /discovery e il contrattojson contiene campi ulteriori non accettati dal DTO. Il manifestMCP394b4b1540b575564f0ba58541df9d7efc59fb87 espone search/get, non discovery.request. Non attribuire questa assenza soltanto a IAM senza prova. CAPABILITIES attraverso il connector corrente ha fallito validazione argomenti: nessun catalogo ottenuto, non prova diniego owner.

DiscoveryService può completare positivamente anche con providers.isEmpty(): un job concluso vuoto non prova discoveryfunzionante. Leggere configurazione attuale provider/worker e override sul VPS prima di predisporre richiesta; collegare la capabilityMCP e la mediazioneGateway senza inviare querySPARQL/URL liberi. Adozione/pubblicazione THS resta HUMAN; nessun pin o successo inventato. Providerdefaultschema.gov.it rimane scelta installazione giàapprovata, non prova del runtime corrente; candidati e firme/scan restano nei rispettivi scope, nessun nuovo avvio.
