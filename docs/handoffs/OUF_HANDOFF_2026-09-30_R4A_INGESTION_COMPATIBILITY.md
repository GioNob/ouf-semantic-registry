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

### Prossimo comando corrente — switch Ingestion con backup, nessuna attestazione

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
