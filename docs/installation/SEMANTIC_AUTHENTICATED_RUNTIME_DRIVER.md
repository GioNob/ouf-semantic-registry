# Runtime autenticato per installazione indipendente

## Checkpoint corrente — §28 ESEGUITO/PASS; contratto e custodia producer implementati

§28: `/etc/ouf/deploy-snapshots/semantic-authenticated-runtime-package-20261004-094455`, source `f1996cca60e66f1807b88f126793a8edc1aed15f`; checksum wrapper +22 sorgenti e plan/apply/verify PASS concordanti, Python3.13.5. Ricevuta operatore in `2a8a0bc82e93bd09a6f65e7645381e1951b6bff1`, CI documentale13/13. Nessun accesso VPS indipendente o digest della receipt target. Nessun replay del §28.

Nuovo codice Gateway `93e1c845d26d339af6a07acb0e588b2532d2a4a7`: `LocalEvidenceProducer` invoca soltanto un producer Python locale con interprete/source/configurazione esplicitamente pinned; richieste esatte CREATION_ATTESTATION/FINAL_DEPLOYMENT_APPROVAL, preflight mandato attivo, I/O limitati, stderr soppresso, deadline condivisa con la verifica. Due firme reali: record e manifest che lega requestHash/recordHash/hash dell'envelope canonico. Un hash di richiesta non firmato non è accettato come legame. L'autenticatore espone anche verifica detached in memoria, conservando le verifiche file legacy.

`ProducerEmission` richiede un journal UNUSED esplicitamente provisionato e il lock comune già esistente: claim fsync ISSUING prima dell'invocazione, risultato firmato salvato O_EXCL/0600 con readback e fsync directory, poi ISSUED con resultHash. Timeout/esito sconosciuto resta ISSUING; nessun retry/reset automatico. File risultato estraneo è preservato e blocca prima dell'emissione. Due processi concorrenti non emettono due volte sullo stesso claim.

**Validazione:** 99 test locali PASS, di cui17 nuovi producer test: processo reale +Ed25519, catena a tre ruoli del protocollo esistente, replay di risposta su richiesta differente, firma/mandato/scope/source drift, modifica configurazione durante processo, limiti/output flood/hang e diagnostica redatta, deadline unica, fsync/custodia/claim incerto e concorrenza con due processi. Chiavi effimere solo fixture. [CI sull'esatto commit](https://github.com/GioNob/ouf-api-gateway/commit/93e1c845d26d339af6a07acb0e588b2532d2a4a7/checks): verificare i check di questo head, senza trasferire il PASS di un commit precedente.

**Limite e prossimo passo preciso:** trasporto e custodia del producer sono implementati/testati, ma il broker produttivo e il collegamento di questi componenti al bootstrap operativo non sono dichiarati completi. Comporre il broker con claim per i ruoli, full attestation valida prima della richiesta di approval, pubblicazione/custodia del request-binding e delle tre evidenze, quindi READY del consumer esistente e preparer3/driver5. Nessun approver o attestor reale è provisionato; non confondere il fixture echo/signature CI con full image/OCI/rootfs acceptance. Profilo e mandato dell'Ente, keys/policy/producer reali e gli altri gate rimangono aperti.

**Nessun nuovo intervento VPS in questo checkpoint:** v6 resta immutato; il nuovo modulo e la nuova API detached non sono copiati/installati sul target. Regole/unit/container/runtime e start non cambiano. Nessun merge/replay/emissione/keygen target. Installazioni indipendenti per Ente; servizi co-locati o distribuiti; Semantic/Registry discovery esterna tramite Gateway (default schema.gov.it parametrizzabile), MCP/chatbot propone e THS governa adozione/attivazione. La prova file→mapping→ingestion→UDP resta aperta.


## Checkpoint storico — ricevuta §28, prima del contratto producer

Output operatore del 4 ottobre 2026: `/etc/ouf/deploy-snapshots/semantic-authenticated-runtime-package-20261004-094455`, schema `ouf.semantic-authenticated-runtime-source-package.v6`, source `f1996cca60e66f1807b88f126793a8edc1aed15f`, Python3.13.5. Checksum wrapper +22 sorgenti OK; plan/apply/verify PASS con tre receipt concordanti. [Ricevuta operatore](https://github.com/GioNob/ouf-semantic-registry/blob/codex/r4a-smoke-semantic-inventory/docs/handoffs/receipts/SEMANTIC_AUTHENTICATED_RUNTIME_PACKAGE_V6_2026-10-04_OPERATOR.json). Evidenza allegata, non accesso VPS indipendente; digest del file receipt sul VPS non fornito.

adapter/preparer/verifier/producer/runtime non installati o registrati; trustPolicyProvisioned/startAuthorized=false, keysGenerated/signaturesIssued/providerCalls=0; regole/unità/container invariati. trustedToolsAvailable, incluso OpenSSL, è metadata, non prova di verifica crypto o autorità sul target. §28 completato: nessun replay. I commit precedenti e i package v5/v6 restano immutabili.

**Prossimo lavoro indipendente:** definire e implementare il contratto del producer locale per richieste tipizzate di CREATION_ATTESTATION e FINAL_DEPLOYMENT_APPROVAL, con eseguibile/configurazione pinned, limiti/deadline e verifica delle firme restituite; collegarlo poi al broker senza generare mandati, chiavi o approval implicite. La firma autentica il mandato provisionato, non dimostra da sola la veridicità della full image/OCI/rootfs acceptance. Il mandato reale della singola installazione e gli altri gate del handoff restano aperti.


## Stato verificato

Gateway `f1996cca60e66f1807b88f126793a8edc1aed15f`, CI38/38 PASS. 82 test pertinenti +2 native admission e6 test Docker. Il percorso adapter4/preparer3/driver5 è stato esercitato realmente in Docker/runc/nft con due chiavi Ed25519 distinte, temporanee e confinate al fixture. Negativi lease-drift e firma alterata, positivo marker applicativo, runtime Docker di default preservato, cleanup posseduto verificato. Questo non è l'autorizzazione o la readiness del VPS.

| Componente opt-in | Schema | Closure sigillata | Vincolo |
| --- | --- | --- | --- |
| Adapter | ouf.semantic-docker-runtime-adapter.v4 | eseguibile adapter, driver e broker hash-pinned | richiede driver5; nessun downgrade automatico |
| Preparer | ouf.semantic-admission-preparer.v3 | 16 sorgenti | consumptionBinding e authenticationBinding obbligatori |
| Driver | ouf.semantic-preexec-driver.v5 | 15 sorgenti | tre firme autentiche e scope/evidenceHash sigillati |

Gli schemi precedenti restano leggibili per le configurazioni già esistenti; passare alla nuova versione richiede configurazione esplicita e nuova closure. Nessun modificatore del runtime o script di migrazione viene eseguito dal package source-only.

## Binding esatto

`authenticationBinding` ha esattamente `records`, `authorities`, `policyBinding`, `signatureDirectory`, `opensslBinding`.

- records: intent/attestation/approval, ciascuno path assoluto +sha256; approval coincide esattamente con path/hash dell'authorityBinding del candidato/driver.
- authorities: installationRef, entityRef, intentIssuerRef, attestorRef, approvalIssuerRef; validati dal protocollo esistente, senza default.
- policyBinding: path/hash della policy privata con mandate/key/ruoli locali espliciti.
- signatureDirectory: directory root-owned 0700; tre envelope privati nominati con payload hash e ruolo.
- opensslBinding: path/hash/versione esatti; versione/binario sono verificati prima dell'uso.

`consumptionBinding` conserva journalPath/binding/evidenceHash; il broker esterno deve già aver pubblicato READY per la generazione attestata e poi sigillare il driverHash una sola volta. Il preparer verifica quei legami prima delle modifiche e prima di pubblicare il driver. Non emette intent, acceptance, attestation, approval o firme e non provisiona key/policy. Il producer/broker reale resta da completare con mandato conferito; il fixture CI non è incluso nel package.

## Lock e scadenza

Il caller usa il lock comune già impiegato da guard/lease; il callback non acquisisce un secondo lock. Nel driver il budget del verificatore ha la stessa deadline monotonic del NativeBackend: budgetSeconds intero 1–5s, cumulativo tra controlli live e tutte le riverifiche di quell'operazione, senza reset. Ogni comando OpenSSL usa min(2s, tempo residuo); hash del binario, riletture e ritorno controllano la deadline. Nel preparer il verificatore condivide la deadline complessiva di18s successiva alla lettura della configurazione, oltre ai budget più stretti dei backend/worker nativi.

Il callback verifica prima l'approval privata legacy, poi le tre firme reali, i ruoli/mandati, lo scope/evidenceHash, tutte le riletture e le scadenze finali. Il consumer lo richiama prima e dopo la pubblicazione fsync di STARTING. Budget esaurito/revoca/scadenza prima del claim: READY, nessun processo. Dopo il claim: STARTING, nessun rilascio FIFO, recupero esplicito. STARTED registra il tentativo native completato; non certifica salute applicativa. Nessun reset/replay automatico.

Le revoche cooperative devono usare lo stesso lock. Le riletture non provano snapshot atomico e non proteggono da un amministratore privilegiato estraneo al protocollo; hash/versione OpenSSL non attestano le librerie/provider dell'OS. I file/input/output sono limitati; la deadline può causare un diniego sicuro su host molto lento e dovrà essere misurata sul target senza autorizzare avvii impliciti.

## Rollback e comportamento Docker verificati

Rollback/cleanup restano vincolati a risorse possedute, tag/footprint, journal e generazione morta; non richiedono firme ancora valide. Docker può chiedere delete dopo un'ammissione negata: il fixture della firma alterata verifica ROLLED_BACK del preexec, CLEANED dell'admission, DELETED dell'adapter, namespace rimosso e consumption ancora READY. Questo è cleanup, non una nuova autorizzazione o un reset della receipt. Lease-drift preserva il candidato protetto per recupero esplicito. Il consumer non consente una seconda consumazione.

## Registro VPS — §28 ESEGUITO/PASS

[Comando source-only v6](../handoffs/commands/OUF_STAGE_AUTHENTICATED_RUNTIME_PACKAGE_V6_2026-10-04.sh), 22 file, source `f1996cca60e66f1807b88f126793a8edc1aed15f`. Nuovo root privato, checksum e plan/apply/verify, receipt schema `ouf.semantic-authenticated-runtime-source-package.v6`. OpenSSL in trustedToolsAvailable è metadata d'inventario, non una prova di firma o mandato sul target. Nessun test/fixture/private key viene copiato.

Staging non installa adapter/preparer/verifier/broker/policy, non genera chiavi/firme, non registra runtime, non cambia regole/unit/container e non fa IAM/DNS/provider calls. §27v5 resta ESEGUITO/PASS e immutato. Dopo la ricevuta §28 aggiornare handoff/roadmap/manuale/sprint e proseguire gli elementi produttivi; fermarsi per i binding di autorità indispensabili senza inventarli.

Ogni Ente ha installazione e autorità indipendenti; i servizi possono essere distribuiti o co-locati. Discovery esterna resta responsabilità Semantic/Registry tramite Gateway (default schema.gov.it, parametrizzabile per installazione); chatbot/MCP propone attraverso capability tipizzate, THS approva adozione/attivazione. Restano aperte la prova completa file→mapping→ingestion→UDP e le altre questioni del handoff.
