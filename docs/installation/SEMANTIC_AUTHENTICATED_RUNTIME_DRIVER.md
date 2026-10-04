# Runtime autenticato per installazione indipendente

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

## Prossimo passo VPS — §28 NON ESEGUITO

[Comando source-only v6](../handoffs/commands/OUF_STAGE_AUTHENTICATED_RUNTIME_PACKAGE_V6_2026-10-04.sh), 22 file, source `f1996cca60e66f1807b88f126793a8edc1aed15f`. Nuovo root privato, checksum e plan/apply/verify, receipt schema `ouf.semantic-authenticated-runtime-source-package.v6`. OpenSSL in trustedToolsAvailable è metadata d'inventario, non una prova di firma o mandato sul target. Nessun test/fixture/private key viene copiato.

Staging non installa adapter/preparer/verifier/broker/policy, non genera chiavi/firme, non registra runtime, non cambia regole/unit/container e non fa IAM/DNS/provider calls. §27v5 resta ESEGUITO/PASS e immutato. Dopo la ricevuta §28 aggiornare handoff/roadmap/manuale/sprint e proseguire gli elementi produttivi; fermarsi per i binding di autorità indispensabili senza inventarli.

Ogni Ente ha installazione e autorità indipendenti; i servizi possono essere distribuiti o co-locati. Discovery esterna resta responsabilità Semantic/Registry tramite Gateway (default schema.gov.it, parametrizzabile per installazione); chatbot/MCP propone attraverso capability tipizzate, THS approva adozione/attivazione. Restano aperte la prova completa file→mapping→ingestion→UDP e le altre questioni del handoff.
