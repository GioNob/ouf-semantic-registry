# OUF · handoff R4a, 30 settembre 2026: Ingestion compatibility probe

Questo documento prosegue l'[handoff del 29 settembre](OUF_HANDOFF_2026-09-29_R4A_PREFLIGHT_TO_INGESTION.md). I suoi vincoli e gli altri gate aperti restano validi. Non ripetere upload, submit, pubblicazione Semantic, policy o preflight UDP.

## Evidenza acquisita dall’operatore

L’inventario sospeso è stato eseguito con PASS. Staged Ingestion `e3f04f1d8ed47a62cde8b9c7831882c9cea17169` differisce dal live, che è running su `ouf-backend`, UID/GID 10002:10002. Flyway live 14, staged massimo 14. Policy `ouf-lab-authorization:31`: un descriptor SERVICE e un grant SERVICE di `ouf.ingestion.configuration.attest`, zero altri grant. I conteggi non attestano corrispondenza tra il principal del bearer e il destinatario del grant; non dimostrano scope IAM, route o accesso owner effettivi.

L’assistente non ha SSH e questi sono output incollati dall’operatore. Compatibilità della fonte ancora non attestata; nessun deploy, approvazione o attivazione è stato eseguito in questa ripresa. Stato atteso della versione cinema: IN_REVIEW, lock 2, hash `sha256:2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891`.

## Incremento preparato

[Ingestion PR #33](https://github.com/GioNob/ouf-ingestion-runtime/pull/33), draft, branch `codex/r4a-ingestion-frozen-compatibility-probe`, commit `da941666643d83f9f417da85be91fb3b10d4db01`. Base: il branch CSV già staged, PR #32; riconciliare la catena prima del merge a main.

La sonda è una JVM separata nel jar consegnabile; usa mapper, trasporto Gateway, adapter managed e validator CDE/lineage/handoff reali. Non avvia Spring/Flyway/worker e non scrive run, lake, ACK, watermark, oggetti UDP o attestazioni. Verifica stato/hash congelati, riferimenti Semantic esatti, file immutabile, adapter/runtime version, source identity, campi attesi e tutte le righe. Nessuna decisione di identità canonica appartiene alla sonda.

Lo script prepara una candidata in un worktree isolato e confronta esattamente i file migration con la precedente baseline, non solo il massimo Flyway. La JVM legge soltanto mount di auth/proprietà, con tmpfs parser bounded, senza credenziali DB né chiave receipt. GET Gateway e SELECT in transazione read-only sono gli unici accessi di dominio. Immagine/worktree/log privato/evidence vengono conservati, il container della sonda viene rimosso; i container live e gli snapshot preesistenti sono preservati.

[Procedura Ingestion e limiti](https://github.com/GioNob/ouf-ingestion-runtime/blob/da941666643d83f9f417da85be91fb3b10d4db01/docs/R4A_FROZEN_CONFIGURATION_COMPATIBILITY.md).

## Normativa consultata per lo sprint

Pacchetto allegato v1.7: 323 checksum validi; L0 Blueprint v0.3, Matrix v1.7 e Supersession Notice v1.1. Consultati i sette PET con vincoli pertinenti:

| Owner | Vincolo/prova di questo incremento |
|---|---|
| Ingestion v1.3 | Consumer compatibility e riferimenti pin (§§104–106); sonda con adapter e output validator reali, senza run/persistenza |
| Onboarding/THS v1.6 | Configurazione congelata e hash; nessun ACTIVE sintetico o sostituzione della decisione HUMAN |
| Semantic v1.3 | Risoluzione Gateway di revision/publication set esatti; nessun lookup che sostituisca il pin con latest |
| UDP v1.3 | Nessuna materializzazione, identità canonica o ACK; il PASS non certifica serving o R-SMOKE |
| Authorization v1.5 | Default deny conservato; inventory non prova principal effettivo; nessuna modifica globale SDK, grant o policy |
| Gateway v1.5 | Asset e semantic refs letti attraverso route governate; nessun bypass diretto object-store/owner |
| MCP v1.4 | Nessun privilegio o approvazione mediata dall’AI; source data e token non vengono proiettati in chat |

## CI ed evidence

Sei test Python PASS localmente. CI dedicata: 12 test della sonda, 11 regressioni adapter/mapper/contracts, sei test Python e prova del main nel jar confezionato. Sul commit aggiornato sono PASS la CI dedicata, la suite completa Ingestion con PostgreSQL, il restore drill e supply-chain/deployment con Trivy e Helm. La prima revisione era bloccata dalla CVE-2026-68497 nella dipendenza ereditata jackson-databind 2.21.4: BOM aggiornata a 2.21.6, mantenendo il gate HIGH/CRITICAL. Run modulo aggiornata: [36680659183](https://github.com/GioNob/ouf-ingestion-runtime/actions/runs/36680659183). Le suite pairwise/cross-module e l’evidence operatore rimangono evidenze distinte.

## Primo tentativo operatore — eseguito e BLOCKED; superato dal comando aggiornato sotto

```bash
(
set -e
cd /opt/ouf/ingestion
git fetch --no-tags origin codex/r4a-ingestion-frozen-compatibility-probe
git show da941666643d83f9f417da85be91fb3b10d4db01:scripts/r4a_prepare_frozen_compatibility_probe.py > /tmp/ouf-r4a-ingestion-frozen-probe.py
sudo python3 /tmp/ouf-r4a-ingestion-frozen-probe.py \\
  --revision da941666643d83f9f417da85be91fb3b10d4db01 \\
  --source managed-cinema-8ec8ae90 \\
  --version 68394f42-5c82-4127-a1f3-126516665749 \\
  --expected-hash sha256:2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891
)
```

Il build può richiedere vari minuti; lo script stampa solo marker sicuri. Con PASS produce `/opt/ouf/r4a-stage/ingestion-compatibility-probe.json` con `candidateDeployed=false` e `attestationSubmitted=false`. Non dichiarare un PASS del VPS prima dell’output. Un BLOCKED va trattato con una sola causa specifica; non stampare configurazione, file sorgente o bearer.

Le proprietà Gateway/token-file/tenant-id del mount esistente devono essere esplicite; gli accessi effettivi SERVICE alle letture devono funzionare. Se mancano, preparare la correzione governata; non leggere direttamente lo storage come fallback.

## Sequenza dopo il risultato VPS

1. Confrontare la prova candidata con hash/configurazione congelati e supporto effettivo; non trasformare un PASS dei validator in accettazione generale dei PET.
2. Preparare backup DB verificato, retained old container, switch/rollback controllato e readiness smoke. Nessun DDL viene aggiunto qui.
3. Ripetere la prova contro l’immagine realmente deployed, verificare route, principal/capability SERVICE e scope prima del POST compatibilità. L’attestazione deve legare versione/hash, immagine live ed evidence tecnica; niente POST da inventory sola e niente scrittura SQL diretta dell’attestazione.
4. Solo dopo compatibilità positiva e UDP gate corrente: card/challenge e decisione HUMAN nel THS, poi activation e prima run managed, CDE/handoff/ACK/materializzazione/search. Poi seconda fonte e matching/review reali.

**R-SMOKE e R-INSTALL OPEN.** Conservare tutti i backup, rollback container e route snapshot del 29/09. Nessun restore DB automatico, nessuna pulizia indiscriminata. Roadmap, procedura e manuale sono aggiornati insieme; IAM/policy non sono stati modificati.


## Aggiornamento operatore — 30 settembre: trasporto della sonda

Il primo tentativo su `da941666…` è arrivato al build e poi si è fermato con
`ING_COMPAT_TRANSPORT_CONFIG_REQUIRED`: tutte le tre proprietà activation erano
assenti dal file summary live. Nessuno switch o POST attestazione. Il successivo
`docker exec cat` è una diagnostica non adatta all'immagine distroless, non prova
assenza del token. La lettura del bind mount sul VPS ha confermato file presente,
SERVICE/client Ingestion/tenant/issuer/audience corrispondenti, TTL 277 secondi
all'osservazione e scope `authorization.bundle.read`,
`ouf.ingestion.configuration.attest`, `ouf.internal.object-storage.read`,
`email`, `profile`. Claim decodificati: diagnostica, non autenticazione.

La correzione Ingestion è `160e3391862083bd8779aed69493484f5d2b086d` sulla PR #33. Dieci test Python locali PASS;
CI sulla nuova revisione avviata, risultato non ancora acquisito in questo aggiornamento.
Nessuna modifica Java, DB, IAM/policy o configurazione live.
Il preparatore legge i riferimenti registry HTTPS/token già presenti, controlla
le dipendenze prima del build e crea un file temporaneo solo per la sonda con
Gateway origin, token-file e tenant esplicito (`--tenant-id ouf-lab`). File root:10002,
0440, montato read-only al posto delle proprietà solo nel container usa-e-getta;
nessun token copiato, file rimosso anche in caso di errore della sonda. Directory
auth esistente in sola lettura, rinnovo token conservato. Non aggiungere le
proprietà al summary live né abilitare activation/execution durante questa prova.

L'accesso Semantic esatto resta da provare: nessuno scope Semantic esplicito è
presente nell'output. Il consumer deve attraversare Gateway con owner enforcement;
un 401/403/404 richiede correzione governata di IAM/grant/route/owner, mai accesso
diretto allo storage o attestazione sintetica. La versione resta congelata e
compatibilità non attestata. **R-SMOKE e R-INSTALL OPEN.**

### Sonda successivamente eseguita e BLOCKED — usare ora l'inventario in fondo

```bash
(
set -e
cd /opt/ouf/ingestion
git fetch --no-tags origin codex/r4a-ingestion-frozen-compatibility-probe
git show dae05e6d4e8aa5dcd2f1ff2b6642b1ff4356dd37:scripts/r4a_prepare_frozen_compatibility_probe.py > /tmp/ouf-r4a-ingestion-frozen-probe.py
sudo python3 /tmp/ouf-r4a-ingestion-frozen-probe.py \
  --revision dae05e6d4e8aa5dcd2f1ff2b6642b1ff4356dd37 \
  --source managed-cinema-8ec8ae90 \
  --version 68394f42-5c82-4127-a1f3-126516665749 \
  --expected-hash sha256:2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891 \
  --tenant-id ouf-lab
)
```

Il comando è una prova candidata isolata, non un rollout. I gate successivi restano quelli indicati sopra.

### Correzione dell'ordine di preparazione — 30 settembre

Il tentativo operatore su `160e339…` ha superato il controllo trasporto iniziale,
poi si è fermato con `UnboundLocalError`: la creazione del file temporaneo usava
`current` prima della sua assegnazione. Stop prima del build, del file trasporto
e dei GET consumer; nessuno switch/POST. Le CI precedenti erano tutte verdi,
ma non esercitavano il main del preparatore.

Correzione attuale Ingestion `1eb70c4c3aa6de7e3c3f1ffc4f78ca7b63331872`: il file temporaneo viene creato
solo dopo build, snapshot live verificato e rilettura della versione congelata.
Dodici test Python locali PASS, inclusi due nuovi test del main completo con
operazioni VPS simulate (successo/proof e diniego/cleanup). CI nuova revisione
avviata; il risultato VPS resta da acquisire. Il comando aggiornato, dove presente,
fissa questa revisione e mantiene `--tenant-id ouf-lab`. Non rieseguire i comandi
storici su `160e339…`. R-SMOKE/R-INSTALL restano OPEN e nessuna attestazione positiva.

### Sonda VPS — correzione del contratto d'identità sorgente

Tentativo su `1eb70c4…`: trasporto PASS, build raggiunto, poi
`ING_COMPAT_IDENTITY_POLICY_UNSUPPORTED`. Nessun switch/attestazione;
stop prima dei GET Semantic/asset. Il probe confondeva
`extractionProfile.runtime.rowIdentityBasis=ASSET_AND_ROW_ORDINAL` con
`sourceObjectIdentityPolicy.strategy`, il cui valore normativo è
`MANAGED_DETERMINISTIC` per questa policy. Contratto owner e
`ManagedFileService` Onboarding confermano campi `[$managedRowOrdinal]` e
normalizzazione `normalization://managed-file/asset-row-ordinal-v1`.

Correzione Ingestion `dae05e6d4e8aa5dcd2f1ff2b6642b1ff4356dd37` (PR #33): verifica quella combinazione
esatta, supporta anche NATIVE_KEY/COMPOSITE_NATIVE_KEY con cardinalità/campi
validi; non modifica la configurazione congelata o l'hash. Quattro regressioni
Java aggiunte e fixture managed corretta; dodici test Python PASS, CI Java 21
nuova revisione in corso al momento dell'aggiornamento. Il comando aggiornato,
dove presente, punta alla nuova revisione. Compatibilità live non attestata;
accesso Gateway/Semantic ancora non provato. R-SMOKE/R-INSTALL OPEN.

### Gate aperto corrente: 403 alla risoluzione Semantic

L'operatore ha eseguito la sonda `dae05e6…`: trasporto PASS, build raggiunto,
identità superata, `ING_ACTIVATION_GATEWAY_403` durante Semantic preflight,
prima di lettura asset e validazione righe. Nessuno switch/POST compatibilità.
La route versionata `r2b-semantic-reference` usa `ouf.semantic.read`; lo scope
richiesto manca nel token osservato. Assegnazione Keycloak, descriptor SERVICE,
grant effettivo e route live rimangono evidenze distinte, non dedurre ALLOW.

Inventario read-only in PR #33, commit `e4e1f095c53b7ec4819b8d99fcd79769027330bb`: scope corrente,
descriptor/grant del PolicyBundle ACTIVE e scope DEFAULT/OPTIONAL del client
Ingestion nel realm tramite la sessione kcadm esistente. Nessun build, rinnovo
credenziali, GET dei dati, modifica IAM/policy o attestazione. Una sessione scaduta
stampa `KCADM_SESSION_EXPIRED`, non i dettagli/credenziali. Tre test locali PASS
su conteggi senza identità, sessione scaduta e Keycloak solo GET. Prossimo passo:
acquisire questo inventario e preparare correzione governata del prerequisito
mancante; eventuale nuova policy si pubblica solo con conferma HUMAN THS.
R-SMOKE/R-INSTALL OPEN, compatibilità ancora non attestata.

### Prossimo comando operatore — inventario Semantic, nessun build

```bash
(
set -e
cd /opt/ouf/ingestion
git fetch --no-tags origin codex/r4a-ingestion-frozen-compatibility-probe
git show e4e1f095c53b7ec4819b8d99fcd79769027330bb:scripts/r4a_prepare_frozen_compatibility_probe.py > /tmp/r4a_prepare_frozen_compatibility_probe.py
git show e4e1f095c53b7ec4819b8d99fcd79769027330bb:scripts/r4a_semantic_access_inventory.py > /tmp/r4a_semantic_access_inventory.py
sudo python3 /tmp/r4a_semantic_access_inventory.py --tenant-id ouf-lab --realm ouf
)
```
