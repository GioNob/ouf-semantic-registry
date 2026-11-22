# Ritorno al predecessore Semantic (D-080)

Il job `predecessor-return` di `module-ci.yml` verifica il ritorno del Semantic 32 sui dati del candidato. Su pull request, l'artefatto governato diventa disponibile solo dopo il superamento del job. Il risultato vale per la coppia di image ID registrata nel riepilogo della run.

## Identità delle immagini

| Riferimento | Origine |
|---|---|
| Commit del predecessore | `528881d59a018d5fd3ad4ff62b2b3b95a2b62cd3` di default. Per cambiare baseline usare la variabile di repository `SEMANTIC_PREDECESSOR_COMMIT` oppure l'input manuale `predecessor`. |
| `SEMANTIC_PREDECESSOR_RUN` | ID della run che ha prodotto l'archivio di rilascio `semantic-registry-governed-image-<run>`. Variabile di repository o input manuale `predecessor_run`. |
| `SEMANTIC_PREDECESSOR_IMAGE_ID` | Docker image ID completo (`sha256:…`) registrato per il container in esercizio. Variabile di repository o input manuale `predecessor_image_id`. |
| Candidato | Archivio trasferito da `container-smoke` nella stessa run. La revisione OCI deve corrispondere al checkout testato, incluso il merge di prova per le PR. |

Quando cambia il predecessore, aggiornare insieme commit, run e image ID con i riferimenti del rilascio. Il job verifica repository, commit revisionato, albero Git, SHA-256 dell'archivio e revisione OCI. Avvia le immagini per ID. L'assenza di un pin, un archivio scaduto o una discordanza d'identità fa fallire il gate prima delle prove applicative. La disponibilità dell'archivio va verificata per tutta la permanenza del predecessore in esercizio. La retention corrente dell'artefatto governato è di 14 giorni.

## Sequenza della prova

| Fase | Operazioni ed evidenza richiesta |
|---|---|
| Predecessore su V19 | Flyway applica le migrazioni del JAR a PostgreSQL 17 vuoto. Il worker scopre `MultiplePointOfInterest`. Seguono adozione, validazione, review, approvazione HUMAN tramite THS e pubblicazione. |
| Candidato su V20 | L’agente propone il DATATYPE `Recapito`. Il driver verifica la scheda italiana, pubblica con l’identità HUMAN e confronta lo SHA-256 della definizione con un digest calcolato in Node. La successiva pubblicazione della classe OntoPiA `PointOfInterest` verifica ancora le virgolette nelle descrizioni e crea un set cumulativo. |
| Ritorno su V20 | Riparte lo stesso container del predecessore sullo stesso database. Il driver confronta definizione e hash RDF del DATATYPE nei due set. Verifica le letture RDF e la ricerca delle due classi. |
| Scritture e retry dopo il ritorno | Il predecessore ripete l’adozione del candidato, ritrova la pubblicazione attiva, scopre `POIState` e ripete adozione e review. I retry devono ritrovare la revisione e la challenge originarie. Il conteggio finale richiede tre ricevute di adozione e quattro challenge. |

L'esecutore usa Flyway e il driver JDBC estratti da ciascuna immagine. Ogni migrazione e la rispettiva riga di storia sono scritte in una transazione. La prova confronta le righe versionate di `ouf_sem.flyway_schema_history` prima e dopo le fasi applicative e verifica V19 e V20 con checksum ed esito positivo. Un solo container PostgreSQL conserva i dati per tutte le fasi.

## Readiness e isolamento

Ogni avvio dell'applicazione usa `SPRING_FLYWAY_ENABLED=false`. Il driver richiede HTTP 200 e `status=UP` sia da `/actuator/health/readiness` sia da `/actuator/health/cutover`. Il gruppo di cutover comprende `livenessState,readinessState,db`. Se la readiness del predecessore fallisce al ritorno, il job si ferma prima delle letture e delle nuove scritture. Registrare in **Domande aperte** la fase, le versioni, lo stato osservato e l'eventuale rifiuto di migrazioni future.

Dopo l'acquisizione degli artefatti e delle immagini di supporto sul runner GitHub, i processi della prova condividono soltanto il loopback di un namespace Docker con rete `none`. Il provider serve i file OntoPiA versionati usati da `OntopiaPublicationRuntimeTest`. Le immagini Semantic eseguono il worker e le API di produzione. Il driver usa ricevute HMAC, un issuer TLS e un'identità HUMAN distinta per il reviewer, con chiavi e grant temporanei della fixture. L'accesso a VPS, IAM e provider operativi è escluso.

## Evidenza per la review

Il riepilogo del job registra image ID, identità PostgreSQL, ultime migrazioni e fasi superate. Il log dello scenario riporta gli ID delle revisioni pubblicate. Per qualificare il ritorno occorre una run verde con entrambi i pin del rilascio e l'ultima fase completata. Questo documento descrive la prova da eseguire in CI.
