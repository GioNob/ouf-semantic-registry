# Contratto dei producer locali e custodia del tentativo

## Collegamento operativo successivo

Gateway `86ceb70591762319b3003c4163990451a5c6cca1`: il broker operativo usa questo contratto e la custodia per emettere attestation e approval, validare completamente la creazione prima della seconda emissione, pubblicare READY e sigillare il driver v5. [Profilo, fasi, precondizioni e recupero](SEMANTIC_LOCAL_DEPLOYMENT_BROKER.md). Il broker crea O_EXCL i claim UNUSED soltanto dentro la propria fase PREPARING già persistita; l'installer provisiona in anticipo i journal STAGED del deployment/broker e le directory di risultato vuote. Nessun reset o replay implicito. Il vecchio package v6 sul VPS resta immutabile e non include il broker.

## Scopo e stato

Sorgenti `93e1c845d26d339af6a07acb0e588b2532d2a4a7`: `tools/semantic_provider_deployment_producer.py`, API `DetachedAuthenticator.verify_detached` e17 test nuovi. 99 test locali PASS; [CI del commit](https://github.com/GioNob/ouf-api-gateway/commit/93e1c845d26d339af6a07acb0e588b2532d2a4a7/checks). Il modulo è un trasporto/custodia per componenti con mandato locale esplicito, non un signer, un issuer di mandati, un verifier di immagini o un orchestratore di avvio. Non genera né legge chiavi private. Nei test si usano esclusivamente chiavi effimere e un producer echo del risultato già firmato.

Ogni Ente ha la propria installazione. Un producer resta un processo locale configurato; nessun nuovo microservizio o authority centrale multitenant è imposto. Issuer/attestor/policy/chiavi reali devono essere provisionati attraverso il mandato infrastrutturale esplicito.

## Binding ed esecuzione

`LocalEvidenceProducer(configured, authorities, verifier, budget)` richiede configured esatto: python/source/configuration, ciascuno path assoluto +sha256. Interpreter root-owned executable, gid0, non scrivibile da gruppo/altri, max64MB/hash streaming; script e configurazione root-owned0600 senza symlink/hardlink, max128KiB e ancestor fidati. Tutti i binding sono riletti/hash-verificati dopo la chiamata.

La chiamata è fissa: Python pinned -I -B source --configuration configuration, cwd=/, env minimale, nessuna shell/argv arbitraria. Request <=4096bytes; stdout è letto incrementalmente via selector/pipe, max196608bytes, senza communicate() illimitato o spool su disco; stderr DEVNULL. Budget è esattamente lo stesso oggetto del verifier, deadline monotonic cumulativa; un producer in hang/output flood viene terminato insieme al process group e raccolto. Non ci sono retry automatici.

Prima dell'invocazione si verifica una policy privata pinned e almeno un mandato attivo per l'issuer/ruolo configurato. Al ritorno entrambi i keyRef firmanti e la policy devono essere ancora validi, con clock non regressivo e budget residuo. Il codice non desume un mandato da root ownership, hash o semplice esito zero del processo.

## Request e risposta

Request schema `ouf.semantic-local-producer-request.v1`: role, issuerRef, installationRef, entityRef sono scelti dalle authorities configurate. Ruoli ammessi solo CREATION_ATTESTATION e FINAL_DEPLOYMENT_APPROVAL. Facts esatti: containerId, transactionId, intentHash, artifactHash, deploymentConstraintsHash, applicationHash, transportHash, runtimeExecutableHash (SHA256 lowercase), generation(pid/startTicks/namespaceInode positivi, pid>1). Per approval sono obbligatori anche attestationHash e creationAcceptanceHash. Nessun campo comando/tool/URL arbitrario.

Result schema `ouf.semantic-local-producer-result.v1`: recordBase64 canonico di esatti bytes <=128KiB, recordSignature, bindingSignature. Le due signature sono envelope Ed25519 v1 già definiti dall'autenticatore (max4096bytes), issuer/ruolo/installazione/Ente configurati.

La bindingSignature firma, con lo stesso frame/domain del ruolo, il manifest canonico:
`{schema: ouf.semantic-local-producer-binding.v1, requestHash, recordHash, recordSignatureHash}`.
recordSignatureHash è SHA256 del JSON ASCII sorted keys/separators compatti dell'envelope recordSignature. Il manifest è ricostruito dal caller; non si considera autentico un requestHash semplicemente dichiarato dall'output. recordSignature firma i bytes del record. Sono richieste entrambe le firme autentiche; la risposta non può essere riusata su facts differenti.

Il record deve avere schema/issuer/scope matching; attestation lega anche intent/artefatto/constraints/runtime/generation. Il broker deve poi eseguire la validazione completa del protocollo e della creation acceptance prima dell'approval e prima di READY. Autenticità non prova veridicità dell'ispezione, stato ACTIVE/full authorization o readiness.

## Emissione una sola volta

`ProducerEmission` richiede journal esplicitamente staged schema `ouf.semantic-local-producer-emission.v1`, binding(role/issuer/installazione/Ente/containerId/transactionId/requestHash/producerHash), state UNUSED, resultHash null. producerHash copre i tre binding completi del producer. L'installer deve provisionare journal e directory risultati root-owned0700; nessuna creazione implicita di un mandato.

emit_once usa il lock comune guard/lease già esistente. emit_locked è il punto interno quando il caller lo possiede già; non va chiamato senza quel lock. Il wrapper persiste ISSUING prima di chiamare il producer. Un risultato estraneo preesistente blocca prima dell'emissione.

Risultato pubblicato con O_EXCL/0600 nel file <requestHash>.json, schema `ouf.semantic-local-producer-result-custody.v1`: binding +record/recordSignature/binding/bindingSignature in base64, max256KiB. fsync file/directory e readback precedono journal ISSUED/resultHash. Esito sconosciuto, pubblicazione fallita o timeout dopo il claim preservano ISSUING per recupero esplicito; mai azzerare o ricreare il journal per ritentare. ISSUED non può essere riemesso. Due processi concorrenti sullo stesso claim sono testati con flock/journal reali.

Il broker deve conservare e legare questa custody, le evidenze e la receipt READY prima di generare/sigillare il driver. Il consumo del consumer resta distinto dall'emissione: questi stati non autorizzano alcun processo o FIFO.

## Limiti e prosecuzione

Non è ancora un broker CLI deployabile, né un vero attestatore di immagine/OCI/rootfs. Non è nel package v6 già eseguito. Lo step successivo è comporre i due role producer e la loro custody con validazione completa del protocollo, journal consumer e preparer/adapter. Writers cooperanti usano lo stesso lock; non è provato snapshot atomico o protezione contro root non cooperante, e pin dell'interprete non attesta la sua intera closure OS. Eventuali blocchi OS di I/O non sono garanzie realtime, ma non vanno convertiti in autorizzazione.

§28 ESEGUITO/PASS in /etc/ouf/deploy-snapshots/semantic-authenticated-runtime-package-20261004-094455; nessun replay o nuovo staging richiesto ora. Nessuna key/policy/firma/producer/runtime è stata creata/installata sul target. Gli altri gate e il ciclo end-to-end ingestion restano aperti nel handoff.
