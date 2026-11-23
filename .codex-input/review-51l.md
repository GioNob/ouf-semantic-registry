# Review sprint-03 / task-51l — Consultazione a lotti del pubblicato e zero attestato

**Esito: APPROVATO con due note da chiudere prima dell'attivazione T1.** Branch `sprint-03/task-51l-published-batch`, base `f6ed9f1`, PR Semantic #62 (stacked su #60).

## Verifiche
- **`POST /api/internal/v1/semantic/consultation/search-batch`:**
  - forme chiuse, JSON rigoroso (chiavi duplicate e token residui rifiutati);
  - limiti `max-intents` ≤ 64, `max-hits` ≤ 8, 64 KiB in ingresso e 256 KiB in uscita, validati all'avvio;
  - bean **condizionale** su `ouf.semantic.published-batch.enabled`: in produzione resta spento finché l'installazione non lo configura, nessun rischio di avvio senza parametri.
- **Una sola `SELECT` per lotto** (`jsonb_array_elements` degli intenti): filtri condivisi con la ricerca singola (`SEARCH_JOINS`, `CURRENT_PUBLISHED`, filtri di dominio e range), tipo e contesto applicati in SQL.
- **Ranking 100/95/60:** unicità verificata prima del limite (`strong`), ordine stabile; `MATCH` solo con una forte, `AMBIGUOUS` altrimenti, `NONE` senza riscontri.
- **Verificatore della ricevuta condiviso** con la ricerca singola (`SemanticReadDelegation`), byte inoltrati verificati e policy owner per artefatto.
- **`completedCandidateCount`:** scritto nella stessa istruzione che conclude il job, esposto da status e candidates; nessuna migrazione.
- **ICU4J 75.1** fissata per `norm-v1`: stessa versione Unicode per NFC, case folding e White_Space.
- **CI:** 11/11 verdi. `container-smoke` è stato rieseguito dopo un 429 di Maven Central.

## Note da chiudere prima dell'attivazione T1 (condizioni, non backlog)
1. **Costo con cataloghi grandi.** La `SELECT` combina ogni intento con tutti gli artefatti pubblicati del tipo, e il ranking avviene in Java. Oggi il pubblicato contiene decine di termini; con OntoPiA importata saranno migliaia (righe = intenti × artefatti). Prima di attivare T1 su un catalogo grande serve un indice delle etichette normalizzate (`norm-v1`) che restringa i candidati in SQL, con la misura nel PET.
2. **Una revisione presente in più set pubblicati** non deve contare due volte fra le forti. Il contratto lo richiede («ogni revisione compare una volta»). Va verificato che `CURRENT_PUBLISHED` restituisca un solo set per revisione, altrimenti aggiungere la deduplicazione per `revisionId` prima di `strong`, con un test.

## Rilascio
Dopo la coppia di giri (D-090), con il cutover Semantic/R3; attivazione da profilo d'installazione.
