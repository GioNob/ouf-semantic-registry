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

### Gate storico: 403 alla risoluzione Semantic

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

### Inventario Semantic acquisito dall'operatore — 30 settembre

`SEM_TOKEN_SCOPE_PRESENT=false`, TTL 259 secondi alla lettura. Descriptor unico,
scope corretto e SERVICE ammesso. Un solo grant, SERVICE, zero corrispondenze con
client/sub di Ingestion e zero subject-grant corrispondenti, nessun constraint
nel grant esistente. Il bridge Semantic versionato risolve servicePrincipalId da
client_id/azp: il selector esistente non copre il client Ingestion. Non sostituire
il grant preesistente, aggiungere la nuova autorizzazione con il percorso HUMAN
THS preservando il resto del bundle quando la proposta sarà pronta.

Keycloak: `KCADM_SESSION_EXPIRED`; nessuna evidenza ancora su esistenza e binding
DEFAULT/OPTIONAL dello scope. Il runbook già dispone di
`scripts/r4a_refresh_kcadm_session.py`, che usa le variabili bootstrap soltanto
nel container Keycloak senza stamparle. Prossimo intervento: refresh della
sessione amministrativa e ripetizione dell'inventario esistente; nessuna modifica
a scope/client/grant/route, nessun build o POST compatibilità. Seguiranno piano
IAM additivo per lo scope read e proposta di grant SERVICE governata. R-SMOKE e
R-INSTALL OPEN; versione e hash congelati preservati.

### Prossimo comando — sessione kcadm e inventario completo

```bash
(
set -e
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
git show 8cd9a67a5a6f084b12b7005216817b4303feafe5:scripts/r4a_refresh_kcadm_session.py > /tmp/ouf-r4a-refresh-kcadm.py
sudo python3 /tmp/ouf-r4a-refresh-kcadm.py
sudo python3 /tmp/r4a_semantic_access_inventory.py --tenant-id ouf-lab --realm ouf
)
```

Il file inventory in /tmp è quello fissato a e4e1f095c53b7ec4819b8d99fcd79769027330bb ed eseguito dall'operatore nel passo precedente.

### Sessione kcadm ripristinata e piano scope Ingestion

Output operatore: refresh PASS e inventario Keycloak PASS; un solo scope
`ouf.semantic.read`, un solo client `ouf-ingestion`, assegnazioni DEFAULT e
OPTIONAL entrambe false. Token senza scope, TTL 254 secondi all'osservazione;
descriptor SERVICE valido, grant con selector non corrispondente come sopra.
Nessun cambio IAM/policy è stato eseguito da questo inventario.

Prossimo intervento: reconciler scope esistente in sequenza plan/apply/verify,
solo `ouf.semantic.read` come DEFAULT di Ingestion. Preserva le assegnazioni
agli altri scope; non ricrea scope/client, mapper o secret. Nel lab il client
credentials usa gli scope default e il token esistente rimane invariato fino
al normale rinnovo: DEFAULT=true non implica immediatamente token scope=true.
Ripetere l'inventario senza build; non inviare attestazioni o attivare la fonte.

Il grant va aggiunto separatamente, preservando quello esistente: capability
`ouf.semantic.read`, tenant `ouf-lab`, servicePrincipalId `ouf-ingestion`.
La API PermissionProposal supporta UPSERT di un grant e conserva il resto del
PolicyBundle; nessuna proposta è ancora creata. Verificare scadenza, hash,
base ACTIVE e accesso Gateway/delegation prima di proporla; pubblicazione
richiede conferma HUMAN THS, mai SQL o script storico di publish diretto.
R-SMOKE/R-INSTALL OPEN.

### Prossimo comando — assegnazione DEFAULT Semantic a Ingestion

```bash
(
set -e
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
git show 5e60be53aa50a76e48bfe39c870102ad67a07bcb:scripts/reconcile-keycloak-client-scope.py > /tmp/ouf-reconcile-ingestion-semantic-scope.py
for mode in plan apply verify; do
  sudo python3 /tmp/ouf-reconcile-ingestion-semantic-scope.py "$mode" \
    --realm ouf \
    --client-id ouf-ingestion \
    --scope ouf.semantic.read \
    --assignment default
done
sudo python3 /tmp/r4a_semantic_access_inventory.py --tenant-id ouf-lab --realm ouf
)
```

Risultato apply/verify ancora da acquisire. Il file inventory è quello già fissato a e4e1f095…; la sessione kcadm deve essere ancora valida.

### Scope Semantic applicato e proposta grant PENDING — 30 settembre

Operatore: reconciler plan/apply/verify PASS, `ouf.semantic.read` DEFAULT=true e
OPTIONAL=false su `ouf-ingestion`; nessuna drift al verify. Subito dopo il bearer
esistente aveva scope assente e TTL 269 secondi: verifica del token rinnovato
ancora da acquisire, non diagnosticare fallimento del binding da quel solo output.
Inventario policy invariato: descriptor SERVICE valido, un grant non corrispondente.

L'assistente ha usato il plugin OUF MCP con il collegamento `ouf-admin`, prima
ROLES (catalogo preservato), poi GRANTS filtrato `subjectId=ouf-ingestion`:
policyRef :31, hash `sha256:3c043bf01564b1fc0647d8114220b8cd114d0d6d701371e2fd9cb44ff4ec3bc7`,
proiezione vuota; una proiezione configurata non è prova di permessi effettivi.
Creata via `authorization.permissions.propose` una UPSERT di un solo grant:
`grant-r4a-semantic-read-ingestion-20260930`, capability `ouf.semantic.read`,
tenant `ouf-lab`, servicePrincipalId `ouf-ingestion`, subject/organization null,
constraints null, validFrom 2026-09-30T00:00:00Z, validUntil 2027-09-30T00:00:00Z.
Il resto del PolicyBundle e il ruolo admin restano preservati. Nessun publish.

Ricevuta: proposta `44817d9d-e66c-4c02-8ef5-53ca2b2548e9`, revision 0, PENDING,
expiresAt **2026-09-30T08:28:55.717003Z** (10:28:55 Europe/Rome).
[Conferma HUMAN nel THS](https://api.ouf-lab.it/trusted-human/authorization/?proposal=44817d9d-e66c-4c02-8ef5-53ca2b2548e9).
La scadenza della proposta è distinta dalla validUntil del grant. Il chatbot non
conferma; dopo la decisione leggere la ricevuta con `authorization.proposal.read`
(same account), verificare finalPolicyRef e rinnovo token. Se la proposta è scaduta,
non usare il link come conferma valida: preparare una nuova proposta sullo stato
ACTIVE corrente. Compatibilità, prova Semantic/asset e rollout ancora aperti;
R-SMOKE/R-INSTALL OPEN. Nessuna attestazione o attivazione della fonte.

### Conferma HUMAN verificata: policy :32 pubblicata

L'utente ha confermato la proposta nel THS. L'assistente ha letto la ricevuta
attraverso OUF MCP (account ouf-admin): proposta
`44817d9d-e66c-4c02-8ef5-53ca2b2548e9`, revision **1**, **PUBLISHED**,
finalPolicyRef **ouf-lab-authorization:32**. Non ricreare o riconfermare la proposta.
Lo scope DEFAULT resta quello applicato/verificato dall'operatore. Questo chiude
la pubblicazione governata del grant Semantic Ingestion, non la prova consumer.

La candidata corrente PR #33 è `e4e1f095c53b7ec4819b8d99fcd79769027330bb`: tutte le 14 run CI
push/PR risultano completed/success alla verifica, comprese suite consumer,
module/security/recovery e pairwise. Nessun deploy live né attestazione positiva.
Prossimo passo VPS: rileggere inventario, richiedere scope Semantic presente nel
bearer ruotato prima del build e rieseguire la sonda sulla revisione corrente.
L'inventario non equivale a decisione ALLOW: la sonda deve risolvere riferimenti,
leggere l'asset e validare tutte le righe. La sessione amministrativa kcadm non
serve a quelle letture; un suo eventuale expiry nell'inventario resta separato
quando il token e il grant sono già verificati. Conservare versione/hash congelati,
backup e rollback. R-SMOKE/R-INSTALL OPEN.

### Prossimo comando — controllo bearer e prova candidata, non rollout

```bash
(
set -e
cd /opt/ouf/ingestion
git fetch --no-tags origin codex/r4a-ingestion-frozen-compatibility-probe
git show e4e1f095c53b7ec4819b8d99fcd79769027330bb:scripts/r4a_prepare_frozen_compatibility_probe.py > /tmp/r4a_prepare_frozen_compatibility_probe.py
git show e4e1f095c53b7ec4819b8d99fcd79769027330bb:scripts/r4a_semantic_access_inventory.py > /tmp/r4a_semantic_access_inventory.py
ouf_sem_inventory="$(sudo python3 /tmp/r4a_semantic_access_inventory.py --tenant-id ouf-lab --realm ouf)"
printf '%s\n' "$ouf_sem_inventory"
case "$ouf_sem_inventory" in
  *SEM_TOKEN_SCOPE_PRESENT=true*) ;;
  *) echo 'R4A_ING_COMPAT_RESUME=BLOCKED CODE=SEMANTIC_SCOPE_NOT_IN_ROTATED_TOKEN'; exit 1 ;;
esac
sudo python3 /tmp/r4a_prepare_frozen_compatibility_probe.py \
  --revision e4e1f095c53b7ec4819b8d99fcd79769027330bb \
  --source managed-cinema-8ec8ae90 \
  --version 68394f42-5c82-4127-a1f3-126516665749 \
  --expected-hash sha256:2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891 \
  --tenant-id ouf-lab
)
```

Risultato VPS ancora da acquisire. Lo switch controllato e la prova sull'immagine live precederanno la POST attestazione; approval/activation della fonte restano HUMAN.

### Stato corrente — Semantic superato, lettura asset bloccata da 404

Ultimo output VPS: scope Semantic presente nel token ruotato (TTL 296s),
DEFAULT=true, OPTIONAL=false; due grant SERVICE e un selector client corrispondente.
Policy :32 già pubblicata via conferma HUMAN. Sonda e4e1f095…: trasporto PASS,
preflight Semantic superato, poi **ING_EXECUTION_GATEWAY_404** alla lettura
Gateway dell'asset. Nessuna validazione completa delle otto righe, attestazione,
attivazione o switch. R-SMOKE/R-INSTALL restano OPEN; versione/hash congelati
e backup/rollback restano preservati.

Riscontro statico, da confrontare con il runtime: ExecutionGatewayClient legge
GET `/internal/object-storage/v1/content?ref=…`; il binding Gateway
`onboarding-managed-file-read` a 3014f3c… punta a
`/api/internal/v1/onboarding/managed-files/content` su Onboarding. Quel controller
non è nel tree della baseline Onboarding f74c3a9…. La capability owner
`ouf.object-storage.content.read` richiede lo scope `ouf.internal.object-storage.read` del bearer.
Questo non dimostra che la route live coincida con quel binding, né che
l'asset manchi. Non ricaricare il file, cambiare hash o introdurre accesso diretto
allo storage per aggirare il 404.

PR #33 aggiornata a **0dfab1e7b2253fd939088259ea61754d6e56706c**: aggiunto
`scripts/r4a_execution_route_inventory.py`, solo Docker inspect e GET
dell'Admin API APISIX; nessun GET del contenuto asset, build, cambio IAM/route,
deploy o POST attestazione. Stampa conteggi/booleani su route esatta, rewrite,
upstream, scope e revisione owner. Chiave Admin letta dal bind config.yaml
(oppure file esplicito), passata al curl via stdin, mai argv/output o file temporanei.
Layout chiave non letterale/ambiguo blocca senza stampare il valore.
Diciannove test Python locali PASS, inclusi parser fail-closed, GET esatto,
formati Admin API e assenza chiave da argv/output. CI nuova revisione avviata,
non ancora acquisita. Prossimo passo: inventario live, poi correzione governata
del binding/owner effettivamente osservato.

### Comando storico — inventario route live completato

```bash
(
set -e
cd /opt/ouf/ingestion
git fetch --no-tags origin codex/r4a-ingestion-frozen-compatibility-probe
git show 0dfab1e7b2253fd939088259ea61754d6e56706c:scripts/r4a_prepare_frozen_compatibility_probe.py > /tmp/r4a_prepare_frozen_compatibility_probe.py
git show 0dfab1e7b2253fd939088259ea61754d6e56706c:scripts/r4a_execution_route_inventory.py > /tmp/r4a_execution_route_inventory.py
sudo python3 /tmp/r4a_execution_route_inventory.py --admin-key /opt/ouf/secrets/apisix-admin-key
)
```

Acquisire solo l'output sintetico. I comandi precedenti sono storici; non
rieseguire ancora build/switch/attestazione.

### Inventario route: chiave esplicita nel comando

Output VPS acquisito: `EXEC_READ_OWNER_BASELINE_REVISION_MATCH=true`, poi
`APISIX_ADMIN_KEY_LAYOUT_UNSUPPORTED`. La lettura dell'Admin API non è stata
eseguita: non sono ancora disponibili evidenze sulle route attive. La baseline
Onboarding f74c3a9… è invece confermata dall'immagine live.

Il parser ristretto del bind config.yaml non accetta il layout osservato.
Usare l'opzione già disponibile `--admin-key /opt/ouf/secrets/apisix-admin-key`:
è lo stesso riferimento del rollout Gateway versionato
`scripts/r4a_semantic_rdf_route_rollout.py` a 3014f3c….
La presenza del file sul VPS sarà verificata dalla lettura, non è stata dedotta
dalla sola fonte GitHub. La chiave resta in memoria/stdin, non in argv/output;
il layout YAML non viene interpretato. Nessuna modifica a configurazione, token,
route, policy, asset, immagini live o attestazioni.

Revisione inventario invariata: `0dfab1e7b2253fd939088259ea61754d6e56706c`.
Tutte le 14 run CI push/PR ora completed/success. I 19 test Python locali erano
già PASS. Il blocco consumer resta `ING_EXECUTION_GATEWAY_404`; compatibilità,
R-SMOKE e R-INSTALL restano aperti.

### Gate corrente confermato — endpoint owner assente nella release live

Output VPS: baseline owner=true, una route GET esatta, rewrite al vecchio
endpoint content=true, upstream Onboarding=true, nessun upstream_id,
OIDC=true, required scope match=true, rewrite=true; inventario completo
in sola lettura. La route invia la richiesta al controller assente nel tree
f74c3a9…. Non vi è evidenza che l'asset sia perso. Il preflight Semantic
è già superato; otto righe, compatibilità live, attestazione Ingestion e
filiera Ingestion → UDP → search rimangono aperti.

Correzione della precedente nota sullo scope: `ouf.object-storage.content.read`
è il nome della capability owner, mentre il descriptor richiede proprio
`ouf.internal.object-storage.read`, già presente nel token. Questa distinzione
non richiede un cambio IAM. Il backend dovrà comunque effettuare la sua
decisione effettiva di autorizzazione dopo il ripristino dell'endpoint.

I rami intake (5d770df…) e identity live (f74c3a9…) divergono dal parent
21de5f2…; il rollout identity ha lasciato fuori l'implementazione intake.
Preparata **Onboarding PR #39**, branch
`codex/r4a-onboarding-managed-identity-integration`, commit
**6340d5bf120e09b47c32177656e2c377a4c03640**, con entrambi i parent nella storia. Ripristina
intake/picker/delegation e conserva gate UDP e PermissionProposal publication.
Cinque file modificati da entrambi i rami integrati con merge a tre vie;
conflitti risolti sulle tre superfici sessione HUMAN e sulle due validazioni,
entrambe mantenute. Il test storico che attivava un managed DRAFT incompleto
resta sostituito dalla regressione fail-closed già introdotta nell'intake.

Tutte le **quattro CI push/PR completed/success** alla verifica: module e
browser. La CI del container verifica GET owner anonimo 403 con
ONB_AUTHORIZATION_DENIED oltre alla readiness, quindi rileva anche una
release priva del controller. Nessun deploy VPS effettuato.
Procedura specifica nel repo Onboarding:
`docs/R4A_MANAGED_IDENTITY_INTEGRATION.md`. Non eseguire il vecchio rollout
picker: riguarda un'altra fase e il suo controllo git non risolve questo caso.

Il DB live è già V31, ma V30/V31 mancano nel tree identity f74c3a9….
La candidata conserva i file originali intake: occorre confrontare ogni
script/checksum con la storia Flyway effettiva, non dichiarare migrazioni
invariate dal solo confronto con quel tree. Preflight Semantic versionato a
**721d81a25c194615eb0ddf48fca8b9bd0a281ef9**, quattro test locali PASS e test aggiunto alla CI:
`scripts/r4a_managed_identity_release_inventory.py`. Solo git read/ancestor,
Docker inspect e SQL BEGIN READ ONLY/ROLLBACK; verifica entrambe le storie,
baseline, env/mount read-only, metadati file per UID/GID 10003 e migrazioni
esatte già applicate. Stampa conteggi/booleani; nessun valore o identità.
Un mismatch blocca i prerequisiti della release. La CI Semantic nuova è in
corso; CI della candidata Onboarding già verde.

Acquisire questo inventario prima di build/candidato fermo e switch con
backup recuperabile. Conservare i rollback e i dump già registrati,
versione/hash congelati e attestazione UDP esistente. La prova isolata e
il gate d'identità devono restare insieme alla lettura managed. Nessun
restore automatico del DB, reupload, cambio hash o aggiramento diretto
dello storage. R-SMOKE/R-INSTALL OPEN.

### Comando storico — preflight release combinata PASS

```bash
(
set -e
cd /opt/ouf/onboarding
git fetch --no-tags origin codex/r4a-onboarding-managed-identity-integration
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
git show 721d81a25c194615eb0ddf48fca8b9bd0a281ef9:scripts/r4a_managed_identity_release_inventory.py > /tmp/r4a_managed_identity_release_inventory.py
sudo python3 /tmp/r4a_managed_identity_release_inventory.py \
  --revision 6340d5bf120e09b47c32177656e2c377a4c03640
)
```

Solo inventario: nessun build, candidato Docker, backup, stop, switch,
rinnovo token, modifica IAM/route, caricamento o attestazione.
Se i prerequisiti risultano BLOCKED, acquisire i booleani senza stampare
env, file chiavi/token o contenuto delle route.

### Preflight release acquisito PASS — candidata da costruire e lasciare ferma

L'operatore ha eseguito il preflight sulla candidata Onboarding
6340d5bf120e09b47c32177656e2c377a4c03640: entrambe le storie preservate,
31 migrazioni tutte corrispondenti al DB, baseline live attiva, quattro env
staging presenti, mount credenziali read-only e file privati leggibili,
gateway/token managed presenti, gateway/token identity presenti e leggibili.
RELEASE_PREREQUISITES=PASS, LIVE_UNCHANGED=true. Nessun nuovo prerequisito
IAM/configurazione va introdotto per riparare l'endpoint mancante.

Automazione Semantic aggiornata a **6fc4ed9b4e74cb038250c609f3688b4276aadb31**:
`scripts/r4a_prepare_managed_identity_candidate.py`. Fissa la candidata
Onboarding alla revisione verde; ripete l'inventario prima e dopo la build da
git archive, verifica label immagine e contratto di avvio, e blocca se live,
env, mount, migrazioni o impostazioni Docker cambiano. Crea solo il container
`ouf-onboarding-r4a-managed-identity-candidate`, in stato created,
restart=no, alias ouf-onboarding, UID/GID 10003, con env/mount/log del live.
Non lo avvia, non cambia il live, non accede al bucket e non invia attestazioni.

Un candidato già presente è riutilizzato solo se fermo e identico; eventuale
drift blocca senza sostituzione. Il readback deve confermare l'ID creato,
immagine, env, mount, rete e stato. In caso d'errore ripulisce solo il proprio
container ancora fermo e non tocca container sostituiti da altri operatori.
Il file env temporaneo è privato e rimosso nel finally.

Manifest privato root 0600:
`/etc/ouf/deploy-snapshots/onboarding-managed-identity-release.json`;
contiene lo snapshot Docker live (anche env segreti), candidate ID e image ID.
Non stamparlo, condividerlo o committarlo. Le build log sono in una directory
root 0700 sotto /etc/ouf/deploy-snapshots, il solo percorso viene stampato; conservate su errore.
Lo stato esistente non viene sovrascritto; deve corrispondere al live/candidato.
Non modificare `identity-images.json` e non eliminare i rollback precedenti.

Otto test Python locali PASS e discovery CI estesa a entrambi gli script:
checksum/migrazioni, mount privati, preparazione completa, drift durante build,
cleanup per ID e candidati preesistenti. CI preparatore avviata, non ancora
acquisita; le quattro CI della candidata Onboarding restano completed/success.
Prossimo passo: acquisire BUILDING → CANDIDATE PASS/STOPPED; poi backup
recuperabile e switch con verifica di readiness, endpoint e Flyway invariata.
Il preparatore non crea backup e non esegue lo switch. Compatibilità consumer,
attestazione e HUMAN approval/activation restano gate successivi.
Versione/hash congelati, attestazione UDP e backup/rollback preservati;
R-SMOKE/R-INSTALL OPEN.

### Comando storico — preparazione candidato fermo completata

```bash
(
set -e
cd /opt/ouf/onboarding
git fetch --no-tags origin codex/r4a-onboarding-managed-identity-integration
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
git show 6eb09c963b39cfc67401d15e39397df4663f456a:scripts/r4a_managed_identity_release_inventory.py > /tmp/r4a_managed_identity_release_inventory.py
git show 6eb09c963b39cfc67401d15e39397df4663f456a:scripts/r4a_prepare_managed_identity_candidate.py > /tmp/r4a_prepare_managed_identity_candidate.py
sudo python3 /tmp/r4a_prepare_managed_identity_candidate.py
)
```

### Correzione percorso privato del preparatore — stop prima del build

Tentativo VPS su 6fc4ed9…: OWNER_STAGE_DIRECTORY_UNSAFE, prima di git archive,
build, candidato o file di stato. Il preflight precedente resta PASS; non
dedurre drift del runtime, IAM o migrazioni da questo blocco.

Il preparatore aveva usato /opt/ouf/r4a-stage come parent per stato contenente
env segreti: quel percorso di staging condiviso non soddisfa il requisito
root-only. Correzione **76073d25ceff9f8a54684fee214071c564423b83**: usa la directory già prevista dai rollout
Onboarding `/etc/ouf/deploy-snapshots`, richiede directory reale (non symlink),
owner root e modo esatto 0700. Non modifica permessi/owner del vecchio staging.
Stato ora `/etc/ouf/deploy-snapshots/onboarding-managed-identity-release.json`,
root 0600; log ed env temporanei nelle sottodirectory private della stessa root.
Non esiste uno stato precedente creato dal tentativo bloccato da spostare.

Nove test locali PASS, inclusa regressione che blocca directory user-owned,
accessibile ad altri o symlink prima di inspect/build. CI della correzione
avviata; candidata Onboarding invariata 6340d5bf… con CI già verde.
Il comando corrente è aggiornato alla correzione. Ancora nessun build o
candidato fermo attestato dall'operatore, nessuno switch/POST. Versione/hash,
live, IAM, route, asset e rollback precedenti restano invariati.
R-SMOKE/R-INSTALL OPEN.

### Build eseguita, stop nel lookup candidato — correzione indipendente dagli errori Docker

Output operatore su 76073d2…: preflight PASS prima e dopo la build, poi
OWNER_DOCKER_INSPECT_FAILED nel lookup opzionale del candidato. La build è
terminata e il controllo di provenance/contratto di avvio è superato;
nessuna nuova creazione candidato attestata, nessun avvio/switch o POST.
Log privato conservato:
`/etc/ouf/deploy-snapshots/onboarding-managed-identity-bmvgzvr2/build.log`.
Non stampare lo stato/env privato. Il live e il DB restano invariati.

Il vecchio helper distingueva assenza da guasto leggendo due stringhe d'errore
di docker inspect; l'output redatto non permette di confermare quale errore
Docker specifico si sia presentato. Correzione Semantic **6eb09c963b39cfc67401d15e39397df4663f456a**:
docker container ls --all con formato Names, confronto per nome esatto,
poi inspect solo quando il candidato esiste. Il risultato vuoto è assenza;
un errore del daemon o un race dell'inspect blocca, senza trattarlo come
assenza e senza mostrarne i dettagli. Nessuna dipendenza dalla lingua/forma
del messaggio No such object/container/image.

Dieci test Python locali PASS, inclusi assenza/nome simile/nome esatto,
errore daemon fail-closed, main completo, drift e cleanup per ID.
Candidata Onboarding invariata 6340d5bf…, stessa immagine/tag: la build ripetuta
può riusare la cache, i due preflight restano obbligatori. Comando corrente
aggiornato alla nuova revisione. CI helper avviata, non ancora acquisita;
le quattro CI Onboarding erano già verdi.
Nessuna modifica IAM/route/asset/versione congelata o ai rollback;
R-SMOKE/R-INSTALL OPEN. Prossimo risultato richiesto: CANDIDATE PASS STOPPED=true,
prima di preparare il backup/switch.

### Candidato combinato preparato PASS — switch ancora da eseguire

Output VPS acquisito: inventario PASS prima/dopo build, CANDIDATE=PASS
STOPPED=true ENV_AND_MOUNTS_PRESERVED=true; PREPARE=PASS LIVE_UNCHANGED=true
DB_UNCHANGED=true. Il candidato fermo è
`ouf-onboarding-r4a-managed-identity-candidate`, revisione Onboarding
6340d5bf120e09b47c32177656e2c377a4c03640. Stato privato root 0600:
`/etc/ouf/deploy-snapshots/onboarding-managed-identity-release.json`.
Build log del tentativo riuscito:
`/etc/ouf/deploy-snapshots/onboarding-managed-identity-h4pcqei_/build.log`.
Non stampare i contenuti; i log precedenti restano conservati.

Automazione switch Semantic a **13feb098621f3c08889f875e92c0d381905a7b7a**:
`scripts/r4a_switch_managed_identity_candidate.py`, modalità plan/apply.
Verifica manifest/ID, snapshot live, env/mount/rete, label/contratto immagine,
31 checksum, token managed e identity freschi con client/scopo/tenant/issuer/
audience corretti, readiness live e versione/hash congelati.
Plan è di sola lettura e non crea receipt/backup. Apply ferma il live,
crea un dump custom dell'intero DB Onboarding e prova pg_restore in un
database temporaneo, rimosso nel finally; exige 31 migrazioni ripristinate.
Rilegge storia Flyway e versione congelata dopo backup e dopo avvio.

Conserva il vecchio container come
`ouf-onboarding-managed-identity-rollback-<old-id-prefix>`; rinomina e avvia
solo il candidato verificato, richiede readiness, stesso ID/immagine/env/mount,
storia Flyway identica e versione congelata invariata. Verifica diniego anonimo
401/403 sul port owner content e freshness dei due token, poi imposta
restart=unless-stopped. Il diniego anonimo non è lettura positiva dell'asset:
la sonda consumer resta il gate seguente, prima di attestazioni.

Receipt privato root 0600:
`/etc/ouf/deploy-snapshots/onboarding-managed-identity-switch.json`;
conserva fase, ID, nome rollback/failed, dump e storia migration. Un receipt
preesistente blocca per evitare doppio switch. In caso di errore tenta ritorno
al vecchio runtime per ID, conserva il nuovo failed e fino a 120 righe di log
in file privato. Se il backup fallisce prima dello swap, riavvia l'originale.
Non rimuove il vecchio rollback e non ripristina automaticamente il DB;
un ID live estraneo blocca il recupero senza toccare quel container.
Ogni fallimento va analizzato dal suo output redatto e stato privato,
senza rilanciare alla cieca un receipt già esistente.

Sedici test Python locali PASS (aggiunti plan senza scritture, apply completo,
backup-before-swap, rollback su backup/start fallito, ID estraneo e cleanup
scratch con dump privato conservato); discovery CI già comprende la suite.
CI nuova helper avviata, non ancora acquisita. Le quattro CI Onboarding
della revisione candidata sono completed/success alla verifica.
Nessuno switch effettivo ancora attestato, nessun cambio route/IAM/asset,
nessun POST compatibilità/approval/activation. Prossimo passo: plan/apply
sulla versione e hash congelati; poi prova Ingestion, mai attivare la fonte
in base alla sola readiness. R-SMOKE/R-INSTALL OPEN.

### Comando storico eseguito — switch con backup e rollback, nessuna attestazione

```bash
(
set -e
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
git show 13feb098621f3c08889f875e92c0d381905a7b7a:scripts/r4a_managed_identity_release_inventory.py > /tmp/r4a_managed_identity_release_inventory.py
git show 13feb098621f3c08889f875e92c0d381905a7b7a:scripts/r4a_prepare_managed_identity_candidate.py > /tmp/r4a_prepare_managed_identity_candidate.py
git show 13feb098621f3c08889f875e92c0d381905a7b7a:scripts/r4a_switch_managed_identity_candidate.py > /tmp/r4a_switch_managed_identity_candidate.py
for mode in plan apply; do
  sudo python3 /tmp/r4a_switch_managed_identity_candidate.py "$mode" \
    --source managed-cinema-8ec8ae90 \
    --version 68394f42-5c82-4127-a1f3-126516665749 \
    --expected-hash sha256:2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891
done
)
```

L'apply sostituisce il runtime Onboarding e conserva il precedente per ritorno;
non deploya Ingestion e non attesta/approva/attiva la fonte.

## 2026-09-30 — switch managed intake + identity eseguito: PASS

L'output VPS di plan/apply conferma Onboarding live a
**6340d5bf120e09b47c32177656e2c377a4c03640**, Flyway **31**,
versione congelata e hash invariati. Backup completo ripristinato con successo
nel database temporaneo e conservato:
`/etc/ouf/deploy-snapshots/onboarding-before-managed-identity-_6czsruy.dump`.
Container precedente conservato:
`ouf-onboarding-managed-identity-rollback-260c56287584`.
Receipt privato:
`/etc/ouf/deploy-snapshots/onboarding-managed-identity-switch.json`.
Non stampare dump, receipt, token, env o snapshot privati.

Il GET anonimo owner content restituisce **401**: il controllo di accesso
nega l'accesso anonimo. La lettura autenticata dell'asset da Ingestion e la
validazione delle otto righe restano da verificare. Nessun POST attestazione
è stato eseguito, nessuna approval/activation della fonte.

Il precedente blocco switch è storico ed eseguito: non rilanciarlo.
Prossimo gate: sonda Ingestion isolata alla revisione
**0dfab1e7b2253fd939088259ea61754d6e56706c** (14 CI completed/success
verificate), con Semantic storico esatto e lettura via Execution Gateway.
Policy pubblicata ouf-lab-authorization:32 e scope ouf.semantic.read nel
token restano le evidenze IAM precedenti. La sonda non cambia il live
Ingestion, non migra DB e non invia attestazioni.

Solo dopo PASS della sonda: rilascio controllato Ingestion e prova positiva
del consumer live prima dell'attestazione; approval/activation restano HUMAN THS.
R-SMOKE/R-INSTALL **OPEN**.

### Comando storico eseguito — sonda Ingestion, nessuna attestazione

```bash
(
set -e
cd /opt/ouf/ingestion
git fetch --no-tags origin codex/r4a-ingestion-frozen-compatibility-probe
git show 0dfab1e7b2253fd939088259ea61754d6e56706c:scripts/r4a_prepare_frozen_compatibility_probe.py > /tmp/r4a_prepare_frozen_compatibility_probe.py
sudo python3 /tmp/r4a_prepare_frozen_compatibility_probe.py \
  --revision 0dfab1e7b2253fd939088259ea61754d6e56706c \
  --source managed-cinema-8ec8ae90 \
  --version 68394f42-5c82-4127-a1f3-126516665749 \
  --expected-hash sha256:2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891 \
  --tenant-id ouf-lab
)
```

## 2026-09-30 — sonda frozen Ingestion PASS, otto righe validate

Output VPS acquisito: R4A_ING_COMPAT_TRANSPORT=PASS; sonda reale
R4A_ING_COMPAT_PROBE=PASS VALIDATED_ROWS=8, candidato
**0dfab1e7b2253fd939088259ea61754d6e56706c**.
La lettura via Gateway e la validazione del consumer isolato hanno superato
il gate sulla versione congelata. Il candidato **non è deployato**:
LIVE_CONTAINER_UNCHANGED=true, ATTESTATION_POST=false.
Proof locale privato: `/opt/ouf/r4a-stage/ingestion-compatibility-probe.json`;
non stamparne contenuti o altri snapshot privati.

Il precedente blocco sonda è storico ed eseguito. Prossimo passo:
inventario read-only del contratto live/candidato Ingestion e delle sole
presenze delle proprietà/env activation; la sonda ha usato proprietà
temporanee senza modificare il live. L'inventario serve alla preparazione
del rilascio controllato, con backup e rollback, e non è uno switch.
Prima dell'attestazione occorre prova positiva del consumer deployato.
Approval/activation della fonte restano HUMAN THS; R-SMOKE/R-INSTALL OPEN.

### Comando storico eseguito — inventario rilascio Ingestion

```bash
sudo python3 - <<'PY'
import json, re, subprocess
from pathlib import Path

def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=30).stdout.strip()
def inspect(name, kind="container"):
    return json.loads(run(["docker", "inspect", "--type", kind, name]))[0]
def flag(key, value):
    print(key + "=" + str(bool(value)).lower())

print("R4A_ING_RELEASE_INVENTORY=READ_ONLY", flush=True)
try:
    proof = json.loads(Path("/opt/ouf/r4a-stage/ingestion-compatibility-probe.json").read_text())
    live = inspect("ouf-ingestion")
    image = inspect(proof["candidateImageId"], "image")
    old = inspect(live["Image"], "image")
    flag("ING_PROOF_REVISION_MATCH", proof.get("candidateCommit") == "0dfab1e7b2253fd939088259ea61754d6e56706c")
    flag("ING_PROOF_EIGHT_ROWS_PASS", proof.get("status") == "PASS" and proof.get("validatedRows") == 8 and proof.get("attestationSubmitted") is False)
    flag("ING_LIVE_BASELINE_MATCH", live["Image"] == proof.get("liveImageId"))
    flag("ING_LIVE_RUNNING", live["State"]["Running"])
    flag("ING_CANDIDATE_LABEL_MATCH", image["Config"].get("Labels", {}).get("org.opencontainers.image.revision") == proof.get("candidateCommit"))
    flag("ING_IMAGE_LAUNCH_CONTRACT_MATCH", all(image["Config"].get(k) == old["Config"].get(k) for k in ("User", "Entrypoint", "Cmd", "WorkingDir", "ExposedPorts")))
    flag("ING_RUNTIME_NETWORK_MATCH", live["HostConfig"]["NetworkMode"] == "ouf-backend" and set(live["NetworkSettings"]["Networks"]) == {"ouf-backend"})
    mounts = {m["Destination"]: m for m in live["Mounts"]}
    flag("ING_TRANSPORT_MOUNTS_READ_ONLY", all(mounts.get(k, {}).get("Type") == "bind" and mounts[k].get("RW") is False for k in ("/run/ouf-ingestion-auth", "/run/secrets/ingestion-summary.properties")))
    text = Path(mounts["/run/secrets/ingestion-summary.properties"]["Source"]).read_text()
    env = {v.split("=", 1)[0]: v.split("=", 1)[1] for v in live["Config"].get("Env", []) if "=" in v}
    for suffix in ("gateway-url", "token-file", "tenant-id"):
        key = "ouf.ingestion.activation." + suffix
        flag("ING_ACTIVATION_" + suffix.upper().replace("-", "_") + "_PROPERTY_PRESENT", bool(re.search(r"^[ \t]*" + re.escape(key) + r"[ \t]*[=:][ \t]*\S", text, re.MULTILINE)))
        flag("ING_ACTIVATION_" + suffix.upper().replace("-", "_") + "_ENV_PRESENT", bool(env.get(key.upper().replace(".", "_").replace("-", "_"))))
    version = run(["docker", "exec", "ouf-postgres", "psql", "-X", "-qAt", "-v", "ON_ERROR_STOP=1", "-U", "ouf_ingestion", "-d", "ouf_ingestion", "-c", "begin read only; select version from ouf_ingestion.flyway_schema_history order by installed_rank desc limit 1; rollback;"])
    flag("ING_FLYWAY_14", version == "14")
    print("R4A_ING_RELEASE_INVENTORY=COMPLETE LIVE_UNCHANGED=true VALUES_NOT_PRINTED=true")
except Exception as error:
    print("R4A_ING_RELEASE_INVENTORY=BLOCKED CODE=" + type(error).__name__ + " SECRETS_NOT_PRINTED=true")
    raise SystemExit(1)
PY
```

## 2026-09-30 — inventario rilascio Ingestion acquisito; preparatore candidato fermo

Inventario VPS COMPLETE read-only: proof revisione/otto righe PASS, baseline live,
runtime running, provenance immagine, contratto di avvio, rete e mount read-only
tutti true; Flyway **14**. Le tre proprietà activation gateway-url/token-file/
tenant-id sono assenti sia nel file sia nell'ambiente del live.

Helper Semantic **f763a5b7949f26298d9dde11a470528bdead096f**:
`scripts/r4a_prepare_ingestion_candidate.py`. Riusa l'immagine immutabile
della proof candidata **0dfab1e7b2253fd939088259ea61754d6e56706c**;
non ricostruisce e non modifica il branch/revisione prodotto Ingestion.
La dipendenza `scripts/r4a_prepare_frozen_compatibility_probe.py` è copia
esatta del helper Ingestion a 0dfab1e7… (per import/tests autonomi del repo
Semantic); nel preparatore sono usati solo inspect, GET/SQL read-only e
validazione trasporto/proof, non il main di build/sonda.

Richiede directory root 0700 `/etc/ouf/deploy-snapshots`, proof PASS esatta,
baseline/image label/launch contract, rete, mount, env univoci, Flyway14,
versione/hash congelati e token trasporto fresco. Copia tutte le properties
live in file privato root:10002 mode0440, aggiungendo esclusivamente le tre
chiavi activation derivate dal trasporto verificato. Nessun valore/token/env
è stampato; il file properties live rimane identico.

Crea solo `ouf-ingestion-r4a-compatibility-candidate` con restart=no, env
identici, mount read-only identici salvo la copia properties e alias
ouf-ingestion; non lo avvia. Verifica readback e snapshot live, conserva
stato privato root0600:
`/etc/ouf/deploy-snapshots/ingestion-compatibility-release.json`.
Riuso consentito solo per candidato/state posseduti e coincidenti;
drift blocca. Un fallimento dopo creazione rimuove soltanto il proprio ID
ancora fermo; il file temporaneo env viene sempre rimosso.
Cinque nuovi test PASS, 17 test locali dei preparatori PASS; CI nuova revisione
non ancora acquisita. Nessun candidato preparato attestato dal VPS finora.

Il blocco inventario precedente è storico ed eseguito. Prossimo gate:
CANDIDATE PASS STOPPED=true, prima di predisporre backup/switch Ingestion.
Nessun live switch, migrazione, attestazione, approval/activation in questo
blocco. R-SMOKE/R-INSTALL OPEN.

### Comando storico tentato e bloccato — preparazione candidato Ingestion fermo

```bash
(
set -e
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
git show f763a5b7949f26298d9dde11a470528bdead096f:scripts/r4a_prepare_frozen_compatibility_probe.py > /tmp/r4a_prepare_frozen_compatibility_probe.py
git show f763a5b7949f26298d9dde11a470528bdead096f:scripts/r4a_prepare_ingestion_candidate.py > /tmp/r4a_prepare_ingestion_candidate.py
sudo python3 /tmp/r4a_prepare_ingestion_candidate.py \
  --source managed-cinema-8ec8ae90 \
  --version 68394f42-5c82-4127-a1f3-126516665749 \
  --expected-hash sha256:2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891 \
  --tenant-id ouf-lab
)
```

## 2026-09-30 — preparazione Ingestion bloccata dal contratto runtime

Output VPS acquisito:
R4A_ING_COMPAT_RELEASE_PREPARE=BLOCKED CODE=ING_RUNTIME_SETTINGS_UNSUPPORTED.
Il guard precede la creazione di directory/file del candidato e docker create:
questo tentativo non ha creato o avviato il candidato né modificato live/DB.
La proof isolata otto righe PASS a 0dfab1e7… resta valida come evidenza del
consumer isolato; nessun POST attestazione.

Il codice aggrega campi HostConfig non supportati, Healthcheck, restart/log
driver e tipo/readonly/formato dei mount. L'output non identifica quale
condizione abbia bloccato: causa specifica ancora da acquisire.
Nessun allentamento del guard e nessuna copia indiscriminata di HostConfig.
Il blocco preparazione precedente è storico (tentativo bloccato);
prossimo passo inventario read-only dei soli nomi dei campi non vuoti e flag
di conformità, senza stampare valori, env o mount path.
La correzione deve preservare il contratto reale rilevato; poi ripetere
preparazione fermo, backup/switch e prova consumer deployato prima del POST.
R-SMOKE/R-INSTALL OPEN.

### Comando storico eseguito — diagnosi contratto runtime Ingestion

```bash
sudo python3 - <<'PY'
import json, subprocess
print("R4A_ING_RUNTIME_CONTRACT_INVENTORY=READ_ONLY", flush=True)
try:
    result = subprocess.run(
        ["docker", "inspect", "--type", "container", "ouf-ingestion"],
        check=True, capture_output=True, text=True, timeout=30)
    live = json.loads(result.stdout)[0]
    host, config = live["HostConfig"], live["Config"]
    keys = ("PortBindings", "Binds", "VolumesFrom", "Privileged", "ReadonlyRootfs",
            "ExtraHosts", "Dns", "DnsSearch", "CapAdd", "SecurityOpt", "Devices",
            "Tmpfs", "AutoRemove", "GroupAdd", "UsernsMode", "Init", "Ulimits",
            "CapDrop", "Memory", "MemorySwap", "NanoCpus", "CpuShares", "PidsLimit",
            "OomKillDisable", "CpusetCpus", "CpusetMems", "PidMode", "Sysctls")
    active = [key for key in keys if host.get(key)]
    print("ING_RUNTIME_UNSUPPORTED_FIELD_COUNT=" + str(len(active)))
    for key in active:
        print("ING_RUNTIME_FIELD=" + key + " NONEMPTY=true")
    def flag(key, value):
        print(key + "=" + str(bool(value)).lower())
    flag("ING_RUNTIME_HEALTHCHECK_PRESENT", config.get("Healthcheck"))
    flag("ING_RUNTIME_RESTART_POLICY_MATCH",
         host.get("RestartPolicy", {}).get("Name") == "unless-stopped")
    flag("ING_RUNTIME_LOG_DRIVER_MATCH",
         host.get("LogConfig", {}).get("Type") == "json-file")
    flag("ING_RUNTIME_ALL_MOUNTS_BIND", all(m["Type"] == "bind" for m in live["Mounts"]))
    flag("ING_RUNTIME_ALL_MOUNTS_READ_ONLY", all(m["RW"] is False for m in live["Mounts"]))
    flag("ING_RUNTIME_MOUNT_PATH_FORMAT_MATCH",
         all(not any(c in m["Source"] + m["Destination"] for c in ",\n\r")
             for m in live["Mounts"]))
    print("R4A_ING_RUNTIME_CONTRACT_INVENTORY=COMPLETE LIVE_UNCHANGED=true VALUES_NOT_PRINTED=true")
except Exception as error:
    print("R4A_ING_RUNTIME_CONTRACT_INVENTORY=BLOCKED CODE="
          + type(error).__name__ + " SECRETS_NOT_PRINTED=true")
    raise SystemExit(1)
PY
```

## 2026-09-30 — contratto runtime identificato: bind e limiti memoria preservati

Inventario read-only VPS: tre campi non vuoti **Binds, Memory, MemorySwap**;
Healthcheck assente; restart/log driver conformi; tutti i mount bind read-only
e formato path conforme. Live invariato; valori e identità non stampati.

Correzione helper Semantic **c1bbb31d81ee067008f264ad0f8c662aa1c014e2**: valida ogni bind ro rispetto al mount
risolto (nessun bind extra/duplicato, niente opzioni sconosciute); accetta solo
propagazione rprivate e ricrea i mount via --mount readonly.
Non ricopia ciecamente HostConfig.Binds. Mantiene sostituzione della sola copia
properties del candidato, mentre tutti gli altri source/target restano uguali.

Valida Memory/MemorySwap come interi coerenti, conserva i valori via
--memory/--memory-swap (incluso swap -1) e richiede uguaglianza nel readback.
Gli altri campi non supportati restano bloccanti; MemoryReservation è
esplicitamente bloccante. Nessun numero/valore di configurazione è stampato.
20 test locali dei preparatori PASS, di cui 8 per il preparatore Ingestion:
flusso completo con bind/memoria, candidato fermo, riuso, cleanup, drift,
swap illimitato e rifiuto bind/limiti incoerenti. CI nuova revisione non
ancora acquisita; revisione prodotto candidata rimane 0dfab1e7… con prova
isolata otto righe PASS. Nessun candidato preparato attestato dal VPS finora.

Il blocco diagnostico precedente è storico ed eseguito. Prossimo comando:
ripetere la preparazione con il helper corretto, senza build/avvio/switch,
migrazioni o POST. Risultato richiesto CANDIDATE PASS STOPPED=true; poi backup
e switch controllato, prova positiva consumer deployato prima dell'attestazione.
Approval/activation HUMAN THS; R-SMOKE/R-INSTALL OPEN.

### Comando storico eseguito — preparazione corretta del candidato Ingestion fermo

```bash
(
set -e
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
git show c1bbb31d81ee067008f264ad0f8c662aa1c014e2:scripts/r4a_prepare_frozen_compatibility_probe.py > /tmp/r4a_prepare_frozen_compatibility_probe.py
git show c1bbb31d81ee067008f264ad0f8c662aa1c014e2:scripts/r4a_prepare_ingestion_candidate.py > /tmp/r4a_prepare_ingestion_candidate.py
sudo python3 /tmp/r4a_prepare_ingestion_candidate.py \
  --source managed-cinema-8ec8ae90 \
  --version 68394f42-5c82-4127-a1f3-126516665749 \
  --expected-hash sha256:2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891 \
  --tenant-id ouf-lab
)
```

## 2026-09-30 — candidato Ingestion preparato PASS; switch plan/apply pronto

Output VPS acquisito: CANDIDATE=PASS STOPPED=true ENV_PRESERVED=true
TRANSPORT_CONFIG_PREPARED=true; RELEASE_PREPARE=PASS LIVE_UNCHANGED=true
DB_UNCHANGED=true ATTESTATION_POST=false. Candidato fermo:
`ouf-ingestion-r4a-compatibility-candidate`; stato privato root0600:
`/etc/ouf/deploy-snapshots/ingestion-compatibility-release.json`.
Prodotto candidato **0dfab1e7b2253fd939088259ea61754d6e56706c**, immagine
immutabile della proof con otto righe PASS. Non ancora live.

Helper Semantic **ca5d44a76b3b8ed6592e3aedb61ad2d386e58507**:
`scripts/r4a_switch_ingestion_candidate.py`, plan/apply.
Plan è read-only: richiede stato/ID/revisione/context esatti, immagine/label,
env/mount/rete/launch contract/limiti memoria coerenti, properties private
0440 e hash/content identici a copia baseline più trasporto, token fresco
SERVICE/client/tenant/issuer/audience/scopi Semantic/object-storage/attest,
storia Flyway 14 tutta successful, versione/hash congelati e readiness.

Apply crea receipt privato, ferma live con restart=no; dump custom completo
del DB Ingestion, pg_restore in DB temporaneo e confronto dell'intera storia
Flyway (version/script/checksum/success/type), poi drop scratch con dump
conservato. Nessun DDL/migrazione previsto nel DB live: stessa storia richiesta
prima/dopo. Rilegge candidato e properties prima dello swap per ID.
Conserva vecchio runtime come `ouf-ingestion-compatibility-rollback-<id>`;
rinomina/avvia solo il candidato verificato, richiede readiness e stesso
image/env/mount/Memory/MemorySwap, storia Flyway/versione congelata identiche,
properties baseline intatte e token fresco; poi restart=unless-stopped.

Receipt privato root0600:
`/etc/ouf/deploy-snapshots/ingestion-compatibility-switch.json`.
Receipt preesistente blocca doppi switch. In caso di errore, recupero per ID
del vecchio runtime, nuovo failed e fino a 120 righe di log conservati in file
privati; nessun DB restore automatico. Un ID estraneo live blocca recupero.
Non rilanciare alla cieca uno switch con receipt già creato, anche rolled-back.

28 test locali dei preparatori/switch PASS, inclusi 8 nuovi dello switch
Ingestion: plan senza scritture, sequenza stop/backup/swap, recupero su
backup/start fallito, drift properties, ID estraneo, cleanup scratch e
claims/freshness token. CI nuova helper non ancora acquisita.
Il precedente blocco preparazione è storico ed eseguito. Prossimo gate:
plan/apply dello switch; dopo PASS occorre sonda della revisione deployata
con i mount/properties effettivi, distinta dalla sola readiness.
Nessun POST attestazione/approval/activation nel blocco switch; HUMAN THS
resta il gate fonte. R-SMOKE/R-INSTALL OPEN.

### Comando storico eseguito — switch Ingestion con backup, nessuna attestazione

```bash
(
set -e
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
git show ca5d44a76b3b8ed6592e3aedb61ad2d386e58507:scripts/r4a_prepare_frozen_compatibility_probe.py > /tmp/r4a_prepare_frozen_compatibility_probe.py
git show ca5d44a76b3b8ed6592e3aedb61ad2d386e58507:scripts/r4a_prepare_ingestion_candidate.py > /tmp/r4a_prepare_ingestion_candidate.py
git show ca5d44a76b3b8ed6592e3aedb61ad2d386e58507:scripts/r4a_switch_ingestion_candidate.py > /tmp/r4a_switch_ingestion_candidate.py
for mode in plan apply; do
  sudo python3 /tmp/r4a_switch_ingestion_candidate.py "$mode" \
    --source managed-cinema-8ec8ae90 \
    --version 68394f42-5c82-4127-a1f3-126516665749 \
    --expected-hash sha256:2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891 \
    --tenant-id ouf-lab
done
)
```

## 2026-09-30 — switch Ingestion eseguito PASS; sonda deployata pronta

Output VPS plan/apply acquisito: SWITCH=PASS live
**0dfab1e7b2253fd939088259ea61754d6e56706c**, Flyway **14**,
versione e hash congelati invariati. Dump completo verificato tramite restore
in DB temporaneo e conservato:
`/etc/ouf/deploy-snapshots/ingestion-before-compatibility-2weff4yv.dump`.
Vecchio runtime conservato:
`ouf-ingestion-compatibility-rollback-f55cbf453460`.
Receipt privato `/etc/ouf/deploy-snapshots/ingestion-compatibility-switch.json`.
Onboarding resta live 6340d5bf… Flyway31, UDP edaba2bf… Flyway34.
ATTESTATION_POST=false; DEPLOYED_CONSUMER_PROBE_PENDING=true.
Non stampare stato/receipt/dump/env/token; non rilanciare il blocco switch
già eseguito, perché il receipt blocca doppi switch.

Helper Semantic **974f5eff2e80fa1224cd5581b89fb312e9b4ceef**:
`scripts/r4a_probe_deployed_ingestion.py`.
Richiede receipt PASS, ID/image/revisione/label/context esatti, contratto
runtime/env/mount/memoria e properties hash invariati, trasporto conforme
alle tre properties effettivamente montate, token SERVICE fresco con issuer/
audience/scopi e Flyway identico al receipt; verifica readiness.

Esegue il consumer reale **in una JVM separata**, immagine ID del container
live e stessi mount AUTH/properties read-only, rete ouf-backend. Nessuna copia
temporanea del trasporto: le properties sono quelle effettivamente deployate.
Nessun endpoint del processo applicativo live viene invocato per la
compatibilità: questa è prova del consumer della revisione deployata con
configurazione effettiva, distinta dalla sola readiness. Non avvia Spring,
Flyway/scheduler/worker, non fornisce DB o persistenza, non POSTa attestazioni.

Richiede otto righe, stesso hash asset/adapter/runtime/binding della proof
predeploy, versione/hash congelati e snapshot live/Flyway/properties
invariati dopo lettura e validazione. Cleanup del solo probe disposable
anche in timeout/diniego. Salva solo dopo PASS proof privata root0600:
`/etc/ouf/deploy-snapshots/ingestion-deployed-compatibility-probe.json`,
con timestamp, image/container ID, candidateDeployed=true e modalità
SEPARATE_JVM_DEPLOYED_IMAGE_AND_LIVE_MOUNTS; attestationSubmitted=false.

Quattro nuovi test locali PASS (flusso completo immagine/mount reali,
diniego, timeout, drift); 28 test preparatori/switch già PASS. CI nuova helper
non ancora acquisita. Prossimo risultato richiesto DEPLOYED_COMPAT_PROBE PASS;
solo dopo questa evidenza predisporre attestazione vincolata a proof/context
e consumer deployato. Approval/activation restano HUMAN THS; fonte congelata
e R-SMOKE/R-INSTALL OPEN. Nessuna attestazione inviata dal blocco corrente.

### Comando storico eseguito — sonda immagine deployata e mount effettivi

```bash
(
set -e
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
for script in r4a_prepare_frozen_compatibility_probe r4a_prepare_ingestion_candidate r4a_switch_ingestion_candidate r4a_probe_deployed_ingestion; do
  git show 974f5eff2e80fa1224cd5581b89fb312e9b4ceef:scripts/"$script".py > /tmp/"$script".py
done
sudo python3 /tmp/r4a_probe_deployed_ingestion.py \
  --source managed-cinema-8ec8ae90 \
  --version 68394f42-5c82-4127-a1f3-126516665749 \
  --expected-hash sha256:2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891 \
  --tenant-id ouf-lab
)
```

## 2026-09-30 — consumer deployato PASS su otto righe, nessuna attestazione

Output VPS acquisito: DEPLOYED_COMPAT_PROBE=PASS VALIDATED_ROWS=8,
revisione live **0dfab1e7b2253fd939088259ea61754d6e56706c**;
COMPLETE=PASS SEPARATE_JVM=true LIVE_CONFIG_CHANGED=false ATTESTATION_POST=false.
Proof privata:
`/etc/ouf/deploy-snapshots/ingestion-deployed-compatibility-probe.json`.
Consumer reale eseguito in JVM separata con immagine deployata e mount/properties
live; nessuna invocation dell'endpoint applicativo live per la compatibilità,
nessun avvio Spring/scheduler/persistenza nella sonda. Otto righe validate,
immagine/configurazione/Flyway/versione/hash vincolati e ricontrollati.

Contratto owner alla revisione Onboarding 6340d5bf… verificato:
POST `/api/internal/v1/onboarding/compatibility/ingestion-runtime`;
body sourceId/onboardingVersionId/compatible/detail; autorità SERVICE con
capability ouf.ingestion.configuration.attest. L'owner accetta solo
IN_REVIEW/APPROVED e registra l'hash corrente della versione nel proprio
consumer_compatibility_attestation; non approva/attiva. Il futuro submitter
deve vincolare detail alla proof, image ID/revisione/versione/hash esatti e
verificare response/readback owner; nessuna scrittura SQL diretta.

Il blocco sonda precedente è storico ed eseguito. Prossimo passo ancora
read-only: inventario route APISIX per POST attestation (owner path, upstream,
OIDC e required scope); non assumere esistenza o mapping dal solo contratto
Java/repository. Nessun nuovo scope/grant/proposal o cambio route autorizzato
da questa evidenza; eventuali blocchi vanno risolti nel rispettivo owner.
Solo dopo verifica route e autorità token/capability preparare POST attestazione;
HUMAN THS mantiene approval/activation. R-SMOKE/R-INSTALL OPEN.

### Comando storico tentato e bloccato — inventario route attestazione, sola lettura

```bash
(
set -e
cd /opt/ouf/ingestion
git fetch --no-tags origin codex/r4a-ingestion-frozen-compatibility-probe
for script in r4a_prepare_frozen_compatibility_probe r4a_execution_route_inventory; do
  git show 0dfab1e7b2253fd939088259ea61754d6e56706c:scripts/"$script".py > /tmp/"$script".py
done
sudo python3 - <<'PY'
import json, sys
from pathlib import Path
sys.path.insert(0, "/tmp")
import r4a_execution_route_inventory as routes

print("R4A_ING_ATTESTATION_ROUTE_INVENTORY=READ_ONLY", flush=True)
try:
    helper = routes.helper
    owner = helper.inspect("ouf-onboarding")
    image = helper.inspect(owner["Image"], "image")
    print("ING_ATTESTATION_OWNER_REVISION_MATCH=" + str(
        image["Config"].get("Labels", {}).get("org.opencontainers.image.revision")
        == "6340d5bf120e09b47c32177656e2c377a4c03640").lower())
    apisix = helper.inspect("ouf-apisix")
    if not apisix["State"]["Running"]:
        raise RuntimeError("APISIX_NOT_RUNNING")
    key = routes.admin_key(routes.mounted_config(apisix).read_text())
    config = ('silent\nshow-error\nfail\nmax-time = 15\nmax-filesize = 10485760\n'
              'header = "X-API-KEY: ' + key + '"\n'
              'url = "http://127.0.0.1:9180/apisix/admin/routes"\n')
    raw = helper.run(["docker", "run", "--rm", "-i", "--read-only",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--network", "container:ouf-apisix", "curlimages/curl:8.16.0",
        "--config", "-"], input=config, timeout=30)
    target = "/api/internal/v1/onboarding/compatibility/ingestion-runtime"
    matching = []
    for route in routes.route_values(json.loads(raw)):
        uris = [route.get("uri")] + (route.get("uris") or [])
        rewrite = route.get("plugins", {}).get("proxy-rewrite", {}).get("uri")
        relevant = rewrite == target or any(
            isinstance(uri, str) and (uri.endswith("/compatibility/ingestion-runtime")
            or (uri.endswith("/*") and target.startswith(uri[:-1]) and not rewrite))
            for uri in uris)
        if relevant and (not route.get("methods") or "POST" in route["methods"]):
            matching.append(route)
    print("ING_ATTESTATION_ROUTE_COUNT=" + str(len(matching)))
    if len(matching) == 1:
        route = matching[0]
        plugins = route.get("plugins", {})
        oidc = plugins.get("openid-connect", {})
        rewrite = plugins.get("proxy-rewrite", {}).get("uri")
        uris = [route.get("uri")] + (route.get("uris") or [])
        facts = {
            "ING_ATTESTATION_ROUTE_ENABLED": route.get("status", 1) == 1,
            "ING_ATTESTATION_OWNER_PATH_MATCH": rewrite == target or
                (not rewrite and any(isinstance(uri, str) and
                (uri == target or (uri.endswith("/*") and target.startswith(uri[:-1])))
                for uri in uris)),
            "ING_ATTESTATION_UPSTREAM_ONBOARDING":
                route.get("upstream", {}).get("nodes") == {"ouf-onboarding:8080": 1},
            "ING_ATTESTATION_UPSTREAM_REFERENCE": "upstream_id" in route,
            "ING_ATTESTATION_OIDC_PRESENT": bool(oidc),
            "ING_ATTESTATION_REQUIRED_SCOPE_MATCH":
                "ouf.ingestion.configuration.attest" in (oidc.get("required_scopes") or []),
            "ING_ATTESTATION_OIDC_ENABLED": not oidc.get("_meta", {}).get("disable", False),
        }
        for name, value in facts.items():
            print(name + "=" + str(bool(value)).lower())
    print("R4A_ING_ATTESTATION_ROUTE_INVENTORY=COMPLETE LIVE_UNCHANGED=true ATTESTATION_POST=false VALUES_NOT_PRINTED=true")
except Exception as error:
    code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
    print("R4A_ING_ATTESTATION_ROUTE_INVENTORY=BLOCKED CODE="
          + code + " ATTESTATION_POST=false SECRETS_NOT_PRINTED=true")
    raise SystemExit(1)
PY
)
```

## 2026-09-30 — route attestazione non ancora acquisita; parser APISIX corretto

Output VPS: owner revision match=true, poi BLOCKED
APISIX_ADMIN_KEY_LAYOUT_UNSUPPORTED prima del GET admin/routes.
Nessuna evidenza su conteggio/mapping/scopo route da questo tentativo,
nessun POST o cambio live/IAM/route. La proof consumer deployato otto righe
PASS resta acquisita; R-SMOKE/R-INSTALL OPEN.

Il parser precedente fermava la lettura quando una lista YAML admin_key era
allineata alla chiave proprietaria (indentless sequence). Correzione Semantic
**ea588d84cb7a848fe3bc3e6867b22e4f24043428**: ammette questa forma standard oltre alla lista indentata e
commenti inline su scalari letterali quotati/non quotati. Arresta il parsing
alla successiva mapping sibling; richiede sempre una sola key di role=admin
con formato ristretto. Ambiguità, riferimenti a env e forme non supportate
restano bloccanti. Nessuna chiave stampata o inserita nell'argv:
curl config viene passato solo su stdin.

La forma effettiva della configurazione live non è stata stampata/acquisita:
la correzione copre un limite certo del codice, senza attribuire ancora una
causa specifica al file live. Sei test locali PASS (incluse indentless,
commenti, confine sibling, ambiguità/ref, trasmissione privata su stdin e
formati response Admin API). CI nuova helper non ancora acquisita.

Il helper read-only route attestazione è ora
`scripts/r4a_ingestion_attestation_route_inventory.py`, con dipendenza
`scripts/r4a_execution_route_inventory.py` corretta nel repo Semantic;
il main storico di execution inventory non viene invocato. Il branch prodotto
Ingestion resta invariato a 0dfab1e7… già deployato. Il blocco precedente è
storico e bloccato. Prossimo passo: ripetere solo inventario route; eventuale
nuovo BLOCKED richiede diagnosi del layout senza stampare valori. Ancora nessun
submit attestation; approval/activation HUMAN THS.

### Comando storico eseguito — inventario route con parser YAML corretto

```bash
(
set -e
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
for script in r4a_prepare_frozen_compatibility_probe r4a_execution_route_inventory r4a_ingestion_attestation_route_inventory; do
  git show ea588d84cb7a848fe3bc3e6867b22e4f24043428:scripts/"$script".py > /tmp/"$script".py
done
sudo python3 /tmp/r4a_ingestion_attestation_route_inventory.py
)
```

## 2026-09-30 — route attestazione PASS; submitter SERVICE pronto, POST non ancora eseguito

Output VPS read-only acquisito: owner revision match=true; route count=1,
enabled=true, owner path match=true, upstream Onboarding inline=true,
upstream reference=false, OIDC presente/abilitato e scope
ouf.ingestion.configuration.attest conforme. Inventario COMPLETE live invariato,
ATTESTATION_POST=false. Parser corretto ha permesso la lettura admin/routes;
nessuna chiave/identità/valore stampato.

Helper Semantic **26366fbdf5ad1c212ccd146888fbaa098b99766f**:
`scripts/r4a_attest_ingestion_compatibility.py`, plan/apply.
Ogni modalità rigenera la sonda consumer deployato (JVM separata, immagine e
mount/properties live) prima di valutare il payload: non usa una proof stantia.
Plan esegue GET/SQL read-only e salva la proof locale aggiornata, ma non crea
receipt attestazione e non POSTa. Richiede proof/context/revisione/otto righe,
live ID/image, token SERVICE fresco, route owner revision/upstream/scope/host/
path univoci e abilitati e fonte ancora IN_REVIEW/hash congelato.
Verifica in sola lettura assenza di attestazione INGESTION_RUNTIME già presente
per versione/hash; se presente richiede riconciliazione, senza duplicare.

Apply ricontrolla runtime/properties/fonte/token e assenza di attestazione;
riserva atomicamente receipt locale privato root0600:
`/etc/ouf/deploy-snapshots/ingestion-compatibility-attestation.json`.
La creazione esclusiva impedisce POST concorrenti di questi submitter.
Invia una sola richiesta via Gateway con token Ingestion; nessun HUMAN token,
nessuna scrittura SQL diretta, niente retry/redirect automatici.
Credenziale e body sono solo su stdin del curl disposable, mai nell'argv/output.

Payload owner sourceId/onboardingVersionId/compatible=true/detail; detail
contiene schema evidence v1 e proof della revisione deployata: image/container ID,
versione/hash, hash asset, adapter/versione, binding count/otto righe, hash
properties, timestamp e modalità separate JVM. L'owner resta autoritativo su
capability/resource enforcement e hash corrente della versione; plan non
sostituisce il suo ALLOW. Richiede HTTP201, risposta con ID UUID, consumer,
versione/hash/compatible/detail esatti e readback SQL read-only del record owner.
Fonte/hash congelati devono restare identici dopo POST. Stampa solo ID
attestazione e flag; risposta con eventuale actor_subject resta privata.

Receipt preesistente blocca ogni nuovo POST. Errori dopo riserva conservano
UNVERIFIED_DO_NOT_REPOST e flag post_attempted; timeout può aver committato
nell'owner, quindi mai rilanciare/rimuovere receipt alla cieca. Prima di un
eventuale recupero, riconciliare il record owner e il receipt senza stamparli.
Sette nuovi test locali PASS: route/context negativi, evidence vincolata,
plan senza POST/receipt, singolo POST+readback, timeout/no-repost, stdin privato
e riserva esclusiva. CI nuova helper non ancora acquisita.

Il blocco inventario route precedente è storico ed eseguito. Prossimo comando:
plan/apply dell'attestazione. **POST ancora non eseguito** dall'operatore.
Non approva o attiva la fonte, non cambia policy/IAM/route, non ingesta/persiste
righe/ACK. Dopo PASS attestazione occorre rileggere l'activation gate UDP
corrente e presentare review HUMAN THS della versione/hash congelati;
R-SMOKE/R-INSTALL OPEN fino alla catena reale Ingestion→UDP→search e installazione.

### Comando storico eseguito — attestazione SERVICE plan/apply, nessuna approval/activation

```bash
(
set -e
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
for script in r4a_prepare_frozen_compatibility_probe r4a_prepare_ingestion_candidate r4a_switch_ingestion_candidate r4a_probe_deployed_ingestion r4a_execution_route_inventory r4a_attest_ingestion_compatibility; do
  git show 26366fbdf5ad1c212ccd146888fbaa098b99766f:scripts/"$script".py > /tmp/"$script".py
done
for mode in plan apply; do
  sudo python3 /tmp/r4a_attest_ingestion_compatibility.py "$mode" \
    --source managed-cinema-8ec8ae90 \
    --version 68394f42-5c82-4127-a1f3-126516665749 \
    --expected-hash sha256:2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891 \
    --tenant-id ouf-lab
done
)
```

## 2026-09-30 — attestazione Ingestion owner PASS; UDP corrente da verificare

Output VPS acquisito: plan PASS senza POST, nuova sonda deployata PASS otto
righe in apply, ATTESTATION=PASS, READBACK=PASS, fonte/hash congelati invariati.
**Attestazione Ingestion acquisita: 00006776-5970-4f5c-acf0-145171a6f944**,
consumer INGESTION_RUNTIME, revisione deployata 0dfab1e7b2253fd939088259ea61754d6e56706c.
ATTESTATION_POST=true, SOURCE_APPROVAL=false, SOURCE_ACTIVATION=false.
Receipt privato conservato:
`/etc/ouf/deploy-snapshots/ingestion-compatibility-attestation.json`.
Il blocco attestazione è storico ed eseguito: non rilanciarlo o rimuovere il
receipt. Nessuna duplicazione dell'attestazione, nessun nuovo cambio live/DB
schema/route/IAM; backup e rollback restano conservati.

Prossimo gate prima della review HUMAN: rileggere coverage UDP corrente per
fonte/hash esatti. Helper Semantic **0a8ebe92d0f8628f9c2f5458cbb5647b58fcb210**:
`scripts/r4a_current_udp_activation_gate.py`, solo GET/SQL read-only.
Legge configurazione congelata e governedIdentity, verifica source/tenant/
policyRef/strategyVersion e Onboarding live 6340d5bf…; usa solo il binding
live OUF_ONB_UDP_IDENTITY_GATEWAY_URL/TOKEN_FILE e token SERVICE
ouf-source-onboarding fresco con scope ouf.udp.identity.attestation.read,
issuer/audience/tenant esatti. Token privato root:10003 e montato read-only;
non stampato, trasmesso al curl disposable esclusivamente su stdin.

GET dello stesso endpoint usato da UdpIdentityActivationVerifier:
`/api/udp/v1/governance/internal/identity/preflight`, sourceId e
configurationHash esatti. Richiede HTTP200, valid=true, source/hash/tenant/
canonicalClass/policyRef/policyVersion corrispondenti e coverageRef coverage://,
poi owner runtime e versione congelata invariati. Stampa solo status/booleani.
Due test locali PASS con tutte le corrispondenze/negativi/attestazione assente;
CI nuova helper non ancora acquisita. Un PASS resta una lettura puntuale:
Onboarding ricontrolla comunque il gate all'attivazione; mutazioni UDP possono
invalidarlo. Non rigenera copertura/backfill e non POSTa alcun preflight.

UDP preflight storico 57499699-dbc5-419d-a14b-27cd3604ec6f non sostituisce questa
verifica corrente. Fonte resta congelata IN_REVIEW, versione
68394f42-5c82-4127-a1f3-126516665749/hash invariati.
Dopo UDP corrente PASS predisporre card/challenge di review nella THS,
con decisione approval/activation esclusivamente HUMAN. Catena reale
Ingestion→UDP→search ancora da eseguire; R-SMOKE/R-INSTALL OPEN.

### Comando storico eseguito PASS — verifica UDP corrente, sola lettura

```bash
(
set -e
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
for script in r4a_prepare_frozen_compatibility_probe r4a_managed_identity_release_inventory r4a_current_udp_activation_gate; do
  git show 0a8ebe92d0f8628f9c2f5458cbb5647b58fcb210:scripts/"$script".py > /tmp/"$script".py
done
sudo python3 /tmp/r4a_current_udp_activation_gate.py \
  --source managed-cinema-8ec8ae90 \
  --version 68394f42-5c82-4127-a1f3-126516665749 \
  --expected-hash sha256:2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891 \
  --tenant-id ouf-lab
)
```

## 2026-09-30 — UDP corrente PASS; versione IN_REVIEW senza challenge

Evidenza VPS incollata dall'operatore: UDP gate HTTP200/valid=true,
source/hash/tenant/classe/policyRef/policyVersion corrispondenti, coverageRef
presente, live invariato. L'attestazione Ingestion
00006776-5970-4f5c-acf0-145171a6f944 e la prova del consumer deployato su otto
righe restano acquisite. Versione cinema
68394f42-5c82-4127-a1f3-126516665749, fonte managed-cinema-8ec8ae90:
IN_REVIEW, hash congelato invariato, zero approval_challenge per la versione.
Non è stata acquisita l'approvazione finale di questo pacchetto; non dedurre
che siano assenti o invalide precedenti decisioni su schema/mapping semantici.
Nessuna nuova approvazione, attivazione o materializzazione effettuata.

Prossimo comando: scripts/r4a_approval_route_inventory.py (Semantic
66a78a99b6167605934c4f9936666612be784483), con dipendenze
r4a_execution_route_inventory.py e r4a_prepare_frozen_compatibility_probe.py.
Inventaria CREATE/CARD/CONFIRM/ACTIVATE e scope inline; controlla owner/versione
invariati; nessun POST. Quattro test locali PASS, CI non ancora acquisita.
Non certifica ALLOW owner, sessione HUMAN, browser THS o enforcement; riferimenti
service/plugin/upstream, rewrite e condizioni ulteriori richiedono verifica.
Non crea challenge prima della verifica del percorso; non conferma o attiva.

Distinguere il gate HUMAN della configurazione/attivazione della fonte dalla
risoluzione UDP per record: NEW_OBJECT e MATCH non ambiguo procedono secondo
policy governata senza THS per ogni riga; REVIEW_REQUIRED apre review umana.
Identità della pratica, tipo NUOVA_LICENZA/RINNOVO e identità dehor/concessione
sono distinti, con chiavi/relazioni approvate in onboarding. Il flag non decide
l'identità; nuove pratiche possono collegarsi allo stesso dehor, mentre stesso
ID pratica può produrre revisioni/evidenze senza duplicazione dell'oggetto.
Questa è una regola di modellazione concordata, non prova di un deploy aggiuntivo.
Dopo approvazione e attivazione seguono run managed reale, CDE/handoff/ACK,
materializzazione e ricerca. R-SMOKE e R-INSTALL restano OPEN.

## 2026-09-30 — route review acquisite; preparatore challenge pronto

Output VPS: CREATE/CARD/CONFIRM/ACTIVATE hanno ciascuna una route, enabled=true,
upstream Onboarding inline, OIDC abilitato, owner path preservato, nessun rewrite,
riferimento upstream/service/plugin config o ulteriore condizione di match.
Host pubblico ammesso e required scope inline ouf.onboarding.configuration.write.
Fonte ancora IN_REVIEW; inventory COMPLETE senza POST/approval/activation.
Questo inventario non prova ALLOW owner né sessione/assurance HUMAN o browser THS.

Helper scripts/r4a_prepare_cinema_approval.py, commit Semantic
ba99054c1652cd7648f44962086d2077b17f8447 (include sei nuovi test locali PASS;
CI non ancora acquisita). Riutilizza il device flow già versionato, con solo
scope ouf.onboarding.configuration.write, stessa identità amministrativa attesa;
token soltanto in memoria e su stdin curl, niente redirect automatici.
Ricontrolla route dopo login, runtime owner e versione/hash congelati.
Non usa credenziali SERVICE per simulare l'approvazione umana.

Crea esclusivamente POST /api/onboarding/v1/sources/managed-cinema-8ec8ae90/
onboarding-versions/68394f42-5c82-4127-a1f3-126516665749/approval-challenges.
Riserva prima del POST un receipt root0600 in directory root0700:
`/etc/ouf/deploy-snapshots/cinema-approval-challenge.json`.
Richiede HTTP201, challenge UUID, CREATED, contesto/hash/ref ed expiry coerenti;
poi GET card /api/trusted-human/v1/approval-challenges/{id}, HTTP200,
configurazione esattamente uguale alla versione congelata.
Card/risposta salvate privatamente, token mai persistito. Stampa solo ID/ref/
expiry e flag, non la configurazione integrale o actor_subject.

Receipt PASS riutilizzabile: nuovo login e GET della stessa card, nessun POST.
Receipt incerto, challenge preesistente senza receipt o challenge scaduta
richiedono riconciliazione; non cancellare il receipt e non rilanciare per
creare doppioni. Un timeout può avere già creato la challenge nell'owner.
Il receipt conservato impedisce un secondo POST automatico di questo helper.

Nessuna challenge è ancora dichiarata creata: attendere output VPS.
Il preparatore non chiama confirm/reject/activate; fonte non approvata/non attiva.
Dopo card verificata occorre review effettiva del contenuto e decisione HUMAN
attraverso il percorso fiduciario; il login device da solo non approva.
La challenge ha TTL: se scade prima della review, recuperare in modo esplicito.
Seguono attivazione e prima run reale; R-SMOKE e R-INSTALL rimangono OPEN.

## 2026-09-30 — challenge cinema e card create PASS; review ancora da completare

Output VPS: challenge **d56c8e00-de2b-4f47-a940-38b453facf2f**,
card PASS con configurazione congelata corrispondente, receipt privato
`/etc/ouf/deploy-snapshots/cinema-approval-challenge.json`.
Scadenza **2026-09-30T13:13:21.263Z** (15:13:21 Europe/Rome).
PREPARE=PASS, SOURCE_APPROVAL=false, SOURCE_ACTIVATION=false.
Non interpretare il device login come decisione di approvazione.
Il blocco preparazione è ora storico/eseguito: non ricreare la challenge.

Prossimo passo: review effettiva prima della decisione HUMAN.
Helper `scripts/r4a_review_cinema_approval.py`, Semantic
**87d8eb17d97b934ee8e9c162a70e5a531fcc4987**, compilazione Python verificata.
Non fa login, HTTP POST, confirm o activate. Verifica receipt root0600,
contesto/hash, configurazione della card esattamente uguale all'owner,
challenge CREATED/non scaduta nel DB in transazione read-only e versione
IN_REVIEW invariata. Mostra soltanto sezioni decisionali della configurazione:
mapping/binding semantici, identità sorgente, access labels, modello di record,
execution e policy UDP resolution/materialization; niente righe CSV/token.
Non è il collaudo di una UI browser THS; il browser shell resta un gate distinto.
Se la challenge scade, richiedere recupero esplicito, conservando il receipt;
non modificare DB/status/expiry per aggirare il TTL. Dopo review segue la
conferma HUMAN sul backend THS verificato, poi attivazione distinta.
R-SMOKE e R-INSTALL restano OPEN.

## 2026-09-30 — review card acquisita PASS; conferma HUMAN pronta, non eseguita

Operatore: REVIEW=PASS CARD_AND_OWNER_MATCH=true, hash invariato,
challenge d56c8e00-de2b-4f47-a940-38b453facf2f CREATED/non scaduta al controllo.
Mapping cinema→nome e indirizzo→indirizzo IDENTITY, classe Cinema, proprietà
OPEN, ontology 1.0.0 e binding revision/publication set esatti; CSV managed
509 byte, otto righe validate, identità sorgente asset+ordinal.
La limitazione al riordino delle righe riguarda l'identità sorgente;
la risoluzione canonica UDP usa la policy governed separata.
La review PASS certifica corrispondenza tecnica, non consenso HUMAN.
Scadenza challenge 2026-09-30T13:13:21.263Z; non estenderla via SQL.

Helper `scripts/r4a_confirm_cinema_approval.py`, commit
**58a561a94d31d3a69e2ee0c3aaa9922fd30ebf27**: quattro test locali PASS
(cancel senza POST, consenso esplicito e readback, timeout/no-repost,
token privato e solo endpoint confirm); CI non acquisita.
Solo operatore umano nel terminale: nuova login Device Flow, GET card THS
corrente, sezioni decisionali stampate direttamente dalla card e richiesta
di digitare APPROVO seguito dall'UUID challenge. Una risposta differente
annulla senza POST o receipt. Controlla expiry/hash/config prima del consenso
e di nuovo dopo, route/runtime/versione invariati. Riserva receipt root0600
`/etc/ouf/deploy-snapshots/cinema-approval-confirmation.json`, poi singolo
POST /api/trusted-human/v1/approval-challenges/{id}/confirm.
Richiede HTTP200/APPROVED/config e hash invariati, readback versione APPROVED
e una approval_decision APPROVE sullo stesso challenge/versione/hash.
Esito incerto conserva receipt e blocca ogni secondo POST automatico.
Non invia activate, non esegue ingestion; conferma non ancora eseguita
finché l'operatore non fornisce output PASS. È prova diretta del backend THS
con consenso HUMAN locale, non completamento della superficie browser THS.
Dopo PASS: attivazione separata, gate corrente e prima run managed reale.
Se expiry precede conferma, recupero esplicito conservando receipt/challenge.
R-SMOKE/R-INSTALL OPEN.

## 2026-09-30 — conferma bloccata per expiry; rinnovo esplicito pronto

Operatore alle 15:14 Europe/Rome: HUMAN_APPROVAL=BLOCKED
APPROVAL_CHALLENGE_EXPIRED_OR_TOO_SHORT, SOURCE_ACTIVATION=false.
Il codice si è arrestato in review.main prima di login/riserva receipt di
conferma/POST confirm. Non dedurre APPROVED: versione attesa ancora IN_REVIEW,
da ricontrollare nel rinnovo. Challenge d56c8e00-de2b-4f47-a940-38b453facf2f
scaduta alle 15:13:21 italiane; non modificare status/expiry via SQL.

Helper scripts/r4a_renew_cinema_approval.py, Semantic
**1bea4f9d68a3062f2d0ea002cf11144496bc024e**, quattro test locali PASS,
CI non acquisita. Rinnovo esplicito con --expired-challenge; verifica vecchio
receipt PASS root0600, card/config/hash esatti, versione IN_REVIEW, challenge
expired e CREATED/EXPIRED, zero decisioni sulla versione, zero altre challenge
CREATED non scadute e assenza receipt di conferma. Ripete i controlli dopo
Device Flow e verifica route/runtime/hash invariati.
Riserva file renewal-{expiredId}.json root0600 prima del POST; archivia senza
sovrascrittura il vecchio receipt in cinema-approval-challenge-expired-{id}.json.
Salva nel receipt corrente UNVERIFIED_DO_NOT_REPOST, poi singolo POST create,
GET card e proof di nuova challenge/config/hash/expiry. A PASS aggiorna anche
il receipt di rinnovo con nuovo ID. Vecchia challenge nel DB rimane immutata.
Timeout o receipt incerto richiedono riconciliazione, niente secondo POST.

Con --review-and-confirm prosegue nella stessa sessione HUMAN (token solo in
memoria) al preparatore di conferma già testato: card riletta, sezioni
decisionali mostrate, richiesta di digitare APPROVO seguito dal NUOVO UUID.
Nessuna conferma automatica dal rinnovo/device login; rifiuto annulla.
Riduce i passaggi fra creazione e decisione senza cambiare TTL o policy.
Non chiama activate e non avvia ingestion. Rinnovo/conferma ancora da eseguire
sul VPS fino a output PASS; R-SMOKE/R-INSTALL OPEN.

## 2026-09-30 — approvazione HUMAN acquisita PASS; attivazione ancora da eseguire

Output VPS: HUMAN_APPROVAL=PASS challenge **4f7a8248-ef40-4dc4-8a64-8a6101c98511**,
owner readback PASS **STATE=APPROVED**, hash congelato invariato.
Receipt privato `/etc/ouf/deploy-snapshots/cinema-approval-confirmation.json`.
SOURCE_ACTIVATION=false. Non rilanciare conferma/rinnovo; conservare receipt
corrente, archive della challenge scaduta e receipt renewal.
La nuova challenge sostituisce quella scaduta nel workflow locale; nessun
cambio retroattivo del record storico scaduto. Compatibilità SERVICE e UDP
corrente restano evidenze acquisite; Onboarding ricontrolla i gate all'activation.

Contratto owner 6340d5bf… verificato: activate richiede HUMAN e versione APPROVED,
latest INGESTION_RUNTIME compatible=true sullo stesso hash, surveillance e gate
UDP; compila/persistisce bundle ACTIVE e proiezioni atomiche e porta versione
ACTIVE. La THS activate legge la challenge e delega all'owner; il TTL della
challenge già CONFIRMED non viene usato come nuovo gate di conferma.
Non confondere publication ACTIVE con run Ingestion o materializzazione PASS.

Prima del POST activate: controllare anche abilitazione worker live. La prova
precedente era JVM separata e non certifica ActivationLoop/RunCoordinator.
Helper `scripts/r4a_activation_worker_inventory.py`, Semantic
**9c65cddf8f563b0413d11b883a03ed8202989aef**, compilazione Python verificata.
READ_ONLY: verifica stato APPROVED/hash, container/revisione Ingestion, mount
properties, hash corrispondente al release receipt; mostra esclusivamente
TRUE/FALSE/ABSENT/UNSUPPORTED per activation.enabled property/env e flag su
Spring JSON/command/JVM override. Non dichiara valore effettivo quando potrebbe
esserci precedenza di altri property source; COMPLETE non equivale a worker
abilitato o ALLOW. Nessun cambio properties/runtime/DB o POST.
Acquisire inventario worker, poi preparare decisione HUMAN di activation e
osservazione run→CDE→handoff→ACK→materializzazione→ricerca. R-SMOKE/R-INSTALL OPEN.

## 2026-09-30 — worker activation live disabilitato; preflight prima dell'abilitazione

Inventario VPS COMPLETE: fonte APPROVED, Ingestion running su revisione attesa,
properties corrispondenti al release; activation.enabled PROPERTY_COUNT=0,
PROPERTY=ABSENT, ENV=ABSENT, nessun Spring JSON/command/JVM override.
application.yml della revisione prodotto 0dfab1e7… verificato via GitHub:
nessun default activation.enabled. ActivationLoop, PublicationGatewayClient e
RunCoordinator richiedono ConditionalOnProperty havingValue=true senza
matchIfMissing. Il worker non è abilitato nella configurazione verificata.
Questo non invalida il PASS consumer in JVM separata né l'approvazione della
fonte, ma impedisce di assumere l'avvio automatico della run dopo publication.

Prima di aggiungere activation.enabled=true e riavviare/sostituire il runtime,
inventariare catalogo ACTIVE e schedule/run preesistenti: il loop scopre e
riconcilia pubblicazioni visibili, non soltanto la fonte cinema.
Helper scripts/r4a_worker_enablement_preflight.py, Semantic
**9e53089f089631a0a1689e5347878671f0638ca5**, compilazione Python verificata.
READ_ONLY: conteggi SQL pubblicazioni ACTIVE (globale e cinema), schedule ACTIVE/
publication_enabled/non blocked e run non finite. GET reale con token SERVICE
Ingestion e trasporto live verso /api/onboarding/v1/runtime/publications?limit=20&after=,
lo stesso endpoint del consumer. Token su stdin curl, nessun redirect/retry o
stampa bundle/credenziali; solo HTTP/count/next-page flag.
COMPLETE non equivale a accesso autorizzato se HTTP diverso da 200 né a inventario
completo del catalogo visibile se nextAfter non vuoto. Conteggi SQL globali e
pagina Gateway autorizzata sono evidenze distinte. Nessun worker abilitato,
nessuna property modificata, fonte ancora non attiva.
Dopo output: risolvere eventuale route/capability/blocker, preparare candidato
con copia privata delle properties e flag esplicito, preservare env/mount/
memoria, prova e switch controllato; poi decisione HUMAN activate e smoke reale.
Conservare tutti i dump/rollback/receipt; R-SMOKE/R-INSTALL OPEN.

## 2026-09-30 — code worker vuote; discovery runtime HTTP404

Output VPS: catalogo ACTIVE=0, cinema ACTIVE=0, schedule ACTIVE=0, run non finite=0.
GET SERVICE /api/onboarding/v1/runtime/publications?limit=20&after= restituisce
HTTP404. AUTHORIZED=false del helper significa accesso non dimostrato, NON
diagnosi di diniego IAM/capability. Nessun worker abilitato o fonte attivata.
Fonte resta APPROVED/hash invariato. Non assumere che worker abilitato possa
scoprire la fonte finché questo percorso non risponde correttamente.

RuntimePublicationApi del prodotto Onboarding live 6340d5bf… verificato:
GET root/list, /{sourceId}/active e /resolve sono presenti; page restituisce
items=[]/nextAfter="" quando non ci sono publication ACTIVE (non 404).
Owner richiede SERVICE, tenant configurato tramite
ouf.runtime-publications.tenant-id (default vuoto) e capability
ouf.onboarding.configuration.read sul ResourceContext published-configuration.
Per page/resolve controlla anche accesso module-level prima dei singoli source.
Il 404 può provenire da route assente o instradamento/path errato: prima
verificare APISIX, senza attribuirlo alla policy né aggiungere grant alla cieca.

Helper scripts/r4a_runtime_publication_route_inventory.py, Semantic
**54d3889c8ab3a8566d97bed23245b4ee062791a2**, compilazione Python verificata:
riusa parser admin e matcher route già testati, enumera LIST/ACTIVE/RESOLVE
con conteggio e flag upstream/OIDC/scope/rewrite/references/host/conditions.
Nessuna stampa chiave/bearer/policy/bundle; scope names e flag solamente.
Aggiunge flag espliciti di tenant ENV owner e scope config-read nel bearer
Ingestion. Questi non sostituiscono GET reale/ALLOW owner e non escludono
altri property source per il tenant; niente POST o mutazione IAM/route/env.
Prossimo output richiesto: inventario route; poi correggere il layer realmente
mancante, riprovare discovery e preparare worker candidate/switch controllato.
R-SMOKE/R-INSTALL OPEN; approvazione HUMAN non va ripetuta.

## 2026-09-30 — LIST runtime assente; correzione route pronta

Output VPS: LIST_ROUTE_COUNT=0; ACTIVE/RESOLVE ciascuna una route enabled,
upstream Onboarding inline, OIDC abilitato, owner path preservato, nessun
rewrite/reference/extra condition; required scope ouf.onboarding.configuration.read.
Bearer Ingestion CONFIG_READ_SCOPE_PRESENT=false. Owner TENANT_ENV_PRESENT=false
ma SPRING_APPLICATION_JSON_PRESENT=true: tenant effettivo NON ancora diagnosticato.
Questi sono layer distinti; il 404 LIST è coerente con route mancante, non prova
di policy deny. Fonte resta APPROVED, worker disabilitato, nessuna fonte ACTIVE.

Helper scripts/r4a_install_runtime_publication_list_route.py, Semantic
**78b41071beae7c613e8eedc856865f68a3a6124b**, plan/apply; sei test locali PASS,
CI non acquisita. Plan GET admin solamente, nessun snapshot/receipt/PUT.
Richiede owner live 6340d5bf…/APPROVED/hash, template ACTIVE univoco/upstream/
OIDC/scope esatti, assenza route GET root e assenza del nuovo ID.
La nuova route è GET esatta /api/onboarding/v1/runtime/publications, ID
r4a-onboarding-runtime-publications-list, clone di upstream/plugins/host/
security del template ACTIVE; non modifica ACTIVE/RESOLVE né IAM/grant.
Legge solo il tenant mirato da Spring JSON (flat/nested) e stampa presence/match
bool; nessuna stampa JSON/env/credenziale.

Apply conserva admin route snapshot completo privato root0600 in directory
privata /etc/ouf/deploy-snapshots/publication-list-route-*/routes-before.json,
riserva receipt runtime-publication-list-route.json root0600
UNVERIFIED_DO_NOT_REPUT, singolo PUT nuovo ID e GET readback univoco/contenuto
esatto; fonte/hash devono restare invariati. Admin key/body sono su stdin curl,
niente redirect/retry e nessuna stampa route body o secret. Receipt PASS o
incerto blocca un secondo PUT automatico: riconciliare, non cancellare alla cieca.
Nessuna modifica worker/Onboarding env/DB, nessuna approval/activation.

Blocchi successivi: token Ingestion deve acquisire lo scope configuration.read
tramite configurazione IAM/refresher corretta e owner policy SERVICE adeguata;
verificare GET effettiva (non inventario scope soltanto), incluso module-level
per list e source-level quando esisterà la pubblicazione. Se JSON tenant non
corrisponde, correggere binding owner con rollout governato, non inferire da
assenza ENV. Solo dopo discovery HTTP200 e scope/tenant/owner ALLOW: candidato
worker enabled=true, switch/prova, HUMAN activate e prima run fino a UDP/search.
Route correction ancora non eseguita sul VPS fino a output PASS.
R-SMOKE/R-INSTALL OPEN; approvazione acquisita non va ripetuta.
