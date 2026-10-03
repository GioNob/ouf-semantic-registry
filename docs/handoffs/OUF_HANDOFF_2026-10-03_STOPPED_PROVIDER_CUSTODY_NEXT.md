# OUF — ripartenza dopo creazione dei candidati provider fermi

## Checkpoint corrente — custody PASS, transition intent pendente

Il 3 ottobre 2026 l'operatore ha eseguito il blocco custody del §6 dell'handoff e restituito `SEMANTIC_PROVIDER_GUARD_CUSTODY_INVENTORY=PASS`. Questa prova **supera le precedenti diciture NON ESEGUITO/custody pending**, mantenute sotto come cronologia. Nessun replay del comando custody è richiesto come passo autonomo.

| Evidenza target | Valore |
| --- | --- |
| Schema | `ouf.semantic-provider-guard-custody.v1` |
| Manifest hash | `052b46a56ea666971f135c75af48b3342dbeb68e2f17f1f16263a99351df88bd` |
| Creation journal hash | `a1c2acd9924fc0f924ded7c2d59f128ef2d8b8dd11c62484a901f628022aaae7` |
| Boot install journal hash | `44dfac2145f509c8fb0b66983630616d25958b40f3ffc811074ebb9b3c1edda5` |
| Candidati / start | 2, neverStarted=true, startAuthorized=false |
| Boot / lease | DENY_ONLY, kernelLeaseInstalled=false, bootTransitionRequiredBeforeRuntimeRules=true |
| Effetti | Read-only; no IAM/DNS/provider calls; nessun container/regola modificato; nessun segreto stampato |

Non è release acceptance né snapshot atomico: l'helper custody non prende lock. Il path timestamped del suo source snapshot non compare nell'output fornito e non viene inventato. Gli hash sopra e i journal originali sono sufficienti a vincolare il nuovo preflight.

Gateway PR56 ora contiene `392234edc50c6e8cd19a3028b3e9e19d6f1955b4`: helper `prepare_semantic_provider_transition_intent.py`, SHA256 `f1cc60568118387cad11a8546f3b0c2c64941c6a51a28611e4c62a009db57422`. Readback esatto dei quattro file modificati; 8 test locali PASS senza skip, con file privati/flock reali e readback host simulati. CI Gateway sul nuovo head: **30/30 check run completed/success** (push e PR); i due job root intent hanno eseguito 8/8 test senza skip (0.079s/0.078s). Semantic PR30 resta `c2b4ae5abed1236378c7060b3eb3dac126672cbc`, OPEN DRAFT, 14/14 completed/success. CI non equivale a target transition acceptance. Nessun software live sostituito, merge o cambio main.

[Protocollo completo e limiti](https://github.com/GioNob/ouf-api-gateway/blob/392234edc50c6e8cd19a3028b3e9e19d6f1955b4/docs/SEMANTIC_PROVIDER_BOOT_RUNTIME_TRANSITION.md). Il restore deny-only installato rifiuta i set: non basta sostituire le regole nft. Il prossimo passo prende lo **stesso lock inode del boot guard**, revalida gli hash custody, il runtime sealed e il cohort lease9, poi registra due readback bounded di struttura propria/condivisa in un nuovo intent root-private. Plan non crea intent; apply scrive **soltanto tre file privati**; verify ricontrolla tutto. Nessuna modifica nft/unit/Docker, nessun login KC, DNS, lease o provider call. Il lock boot non serializza scrittori esterni: globalAtomicSnapshotProven=false. Collisioni, lock conteso/assente/symlink, drift e parziali bloccano; conservare la prova senza retry apply cieco.

**NON ESEGUITO sul VPS:** transition intent plan/apply/verify. **Non implementato:** nuovo runtime restore guard e apply coordinato. Il protocollo richiede gate persistente nel Docker pre-start prima delle mutazioni, intent/journal fsynced e lock comune, sostituzione atomica delle sole due tabelle con empty provider sets, confronto readback con struttura compilata attendibile, verifica shared/PID/pre-start, rollback per fase e nuova attestazione hash lease dopo ricreazione. Native failure/recovery tests prima di host apply; niente seed storico DNS né adozione cieca di hash osservati. Start/daemon/provider admission/reboot restano distinti.

Il primo head di questa sessione `844ebb1979196e847061f82ebb6cdab66948ea19` ha passato il job root intent (8/8 senza skip), ma request-boundary/config-contract non privilegiati hanno raccolto gli stessi fixture root e fallito. Head `392234edc50c6e8cd19a3028b3e9e19d6f1955b4` corregge esclusivamente test/workflow: opt-in/skip nel discovery generale e OUF_TRANSITION_FULL_OWNER_TEST=1 nel job root, che deve fallire se non è davvero root. Helper e SHA256 restano identici; nessuna attenuazione del controllo root in produzione.

Il pacchetto PET autorizzato è presente nel workspace: SHA256 `e63df67e8817eec38a9d4b3eb736b020f693b932f3360dc02f4555330f2201ce`, 323 checksum interni riletti, zero mismatch. Consultati i testi Gateway v1.5 T11/T11.3/GW-NET-01..05 e Semantic v1.3 §§9.2/10–11: default-deny cumulativo, endpoint governati, confini north/south, discovery on-demand, mapping proposto dal chatbot e autorità THS invariati. Nessuna nuova API/identity authority introdotta.

Cinema/Teatri, reti/immagini/trust/credenziali, policy38, receipt/backup e tutti i gate ereditati restano preservati. File: ingestion immediata dopo onboarding/ACTIVE; API: endpoint/credenziali/extraction profile/onboarding/scheduler prima dell'ingestion automatica. Nessun gate di startup, rete runtime o filiera completa chiuso da questo PASS.

## Cronologia — ripresa verificata precedente

Letto integralmente questo handoff al commit `381fc2ae00c52f1952e941edbc43d7fda7fa01be` attraverso il connector GitHub; acquisiti roadmap, manuale, sprint, registro ereditato del 1 ottobre e riferimenti storici 25/27/29/30 settembre e audit 27 settembre. La cronologia resta preservata: nessun gate chiuso per omissione.

Baseline allegata `OUF_Reality_Baseline_Package_v1_7(20261003-142932).zip`: SHA256 `e63df67e8817eec38a9d4b3eb736b020f693b932f3360dc02f4555330f2201ce`; tutti i 323 checksum interni coincidono. Il contenuto dell'archivio coincide con la baseline citata al §3 anche se il nome di upload differisce. Consultati Matrix L0 v1.7, Onboarding v1.6 §§92–92.2, Semantic v1.3 §§9.2/10–11/17–18, UDP v1.3 §§21–22/109.2/109.6–109.9, Authorization v1.5 §36.10 e confini MCP v1.4/Gateway v1.5. Mapping assistito esterno, autorità THS, ingestion file dopo ACTIVE e scheduler governato per API rimangono il percorso concordato.

### Pin riletti dal connector

| Repository / PR | HEAD verificato | Stato |
| --- | --- | --- |
| Gateway PR56 | `85914e39bd0aa9f8e7a0a0a9d3b9db6007633ff8` | OPEN DRAFT, 28/28 check run completed/success |
| Semantic PR30 | `c2b4ae5abed1236378c7060b3eb3dac126672cbc` | OPEN DRAFT, 14/14 check run completed/success |
| Semantic PR26 | `381fc2ae00c52f1952e941edbc43d7fda7fa01be` | OPEN DRAFT; pin di ingresso prima di questo aggiornamento documentale |
| Semantic PR27 | `e7bc5190f9e6afbbc4cf3c90d5d4970afbfad14b` | OPEN DRAFT; coincide con ultima revisione live riferita, senza nuova prova target |
| Semantic PR28 | `bf35e930fb239c61ea8ceebb41e187d653a3d96a` | OPEN DRAFT |
| MCP PR48 | `d7d5330d2b2588b3f896ea23e2c47e19b7b905a1` | OPEN DRAFT |
| Gateway PR55 | `b368284b3f6a7675863f85eeafc42d67bf9187dc` | OPEN DRAFT |

Main riletti separatamente: Semantic `d188e5e727eca7a22f414f43f164f85c31411bcf`, Gateway `dbdc24b5481dc9473b21b360ab1142c9aef0194b`, MCP `5615fdcad8cbcad9ff41ec3d0ad2ccbf9423c042`. Nessun merge o spostamento di main. Compare PR28→PR30: ahead 3, behind 0, merge-base uguale al pin PR28; la correzione disponibilità Discovery è ereditata. Il delta include V10 e rimane candidato software, non rollout. Gli stati live al §5 sono ultima evidenza operatore, non una nuova interrogazione VPS.

### Primo intervento e dipendenza target

Scaricato e letto l'helper custody dal pin Gateway sopra; byte UTF-8 verificati SHA256 `fabd47c6ce8919bc7a910cbaf63f66f1fb786b00c239ae41757c1fd0df829b8d`. Il blocco §6 è riproposto invariato come primo intervento VPS; controllo sintattico shell riuscito. **NON ESEGUITO sul target; nessun PASS custody, nuovo snapshot host o autorizzazione start è attestato.** Nessun accesso SSH è disponibile in questa sessione: l'operatore esegue il blocco e restituisce solo output redatto.

Dopo l'esito target: se BLOCKED, isolare read-only la differenza senza replay create/apply; se PASS, usare i journal/hash restituiti come precondizioni di un nuovo piano boot/runtime. La transizione richiede profilo nuovo sealed, intent/journal e lock comune con la custodia boot, stato fail-closed ad ogni fase, provider sets inizialmente vuoti, verifica della struttura condivisa e del Docker pre-start, rollback/reconciliation dei parziali. Conservare separati footprint boot e hash struttura lease; non riusare una vecchia osservazione DNS come lease. Nessun helper di transizione è dichiarato implementato o target-verified da questa ripresa. Start/daemon/provider admission e reboot restano gate distinti successivi, con binding d'installazione espliciti.

Cinema/Teatri, asset/profile/job, reti, immagini, credenziali, policy38, receipt originali e backup restano preservati; nessuna mutazione VPS, nuova ingestion o chiamata provider eseguita in questa sessione.


Checkpoint: **2026-10-03, 16:14 Europe/Rome**. L'utente interrompe la chat per lentezza, non interrompe il progetto. Questo è il punto di ingresso della nuova chat. Conserva e integra il registro storico del [1 ottobre](OUF_HANDOFF_2026-10-01_FILE_TO_UDP_NEXT_SPRINT.md), senza chiudere gate per omissione.

## 1. Checkpoint storico 16:14 — il custody allora non era eseguito

Ultima azione sul VPS provata dall'output dell'utente: `create_semantic_provider_stopped_candidates.py`, plan/apply/verify PASS. Journal:

`/etc/ouf/deploy-snapshots/semantic-provider-stopped-create-20261003-135106/prepared/creation-journal.json`

- Plan: `PLANNED`, 0 container; apply e verify: `CREATED_STOPPED`, **2 container**.
- `NEVER_STARTED=true`, `START_AUTHORIZED=false`, `NETWORK_CONFIGURATION_ONLY=true`.
- Nessun container condiviso modificato, nessuna scrittura di regole/route/IAM, zero provider call, nessuna release acceptance.
- Nomi/TLS alias: **ouf-semantic-southbound** (APISIX) e **ouf-semantic-provider** (adapter). Gli ID sono nel journal privato, non sono stati stampati né ricostruiti dalla chat.
- Le immagini sono riusate, non ricompilate. Configurazione Docker delle reti/IP non prova namespace o allocazione live, pacchetti, TLS o lease.

**NON ESEGUITO:** download/installazione/invocazione di `inventory_semantic_provider_guard_custody.py`, proposto nel messaggio successivo. Non esiste alcun output target `SEMANTIC_PROVIDER_GUARD_CUSTODY_INVENTORY=PASS` in questa chat. Non assumere nemmeno la creazione del suo snapshot timestamped. Non avviare i candidati. Primo passo operativo rimasto è il comando completo al §6.

La parte software/documentale è invece pubblicata: Gateway helper `85914e39bd0aa9f8e7a0a0a9d3b9db6007633ff8`, SHA256 `fabd47c6ce8919bc7a910cbaf63f66f1fb786b00c239ae41757c1fd0df829b8d`, sette test di admission con readback fixture. CI Gateway **28/28 SUCCESS**, verificata nuovamente durante questo handoff. Le fixture non provano lo stato del VPS.

## 2. Obiettivo e regole di collaborazione

Completare acquisizione → onboarding → mapping semantico → ingestion → UDP, utilizzabile in modo semplice tramite MCP con chatbot compatibili. Il chatbot consulta, confronta e propone il mapping; **nessun agente AI aggiunto dentro Onboarding**. Onboarding valida/persiste il mapping della source; Semantic governa artefatti/versioni; UDP decide l'identità canonica. Le decisioni autoritative HUMAN restano in THS; nessun tool MCP di approvazione/pubblicazione/merge privilegiato.

| Ingresso | Avvio del percorso | Dopo mapping e decisioni governate |
| --- | --- | --- |
| File gestito | THS scelta file → upload/staging → profiling | Onboarding/review/ACTIVE compatibile → ingestion automatica una tantum immediata → handoff/UDP/dedup; nessuna attesa di cadence periodica. |
| Verticale API | THS endpoint e credenziali → THS scelta extraction profile | Stesso percorso di mapping/governance; configurazione scheduler e pubblicazione parametri → ingestion automatica alle scadenze. Onboarding non fa polling. |

La verifica autoritativa di doppioni/identità è UDP dopo l'handoff; non spostarla nel profiler. Credenziali mediante THS/secret manager, MCP riceve riferimenti opachi e stati redatti. Il sistema deve gestire dubbi/quarantene e ripresa idempotente da stato persistito.

Regole persistenti:

1. Riusare centinaia di ore di prove/correzioni backend. Nessun replay Cinema/Teatri, nuovo upload/profile/job, riattivazione schedule o retry per comodità. Nuovi test sui collegamenti cambiati e regressioni appropriate, non ripetizione integrale manuale.
2. L'utente autorizza a proseguire autonomamente finché serve realmente il suo aiuto. Preparare codice, test/CI, piani e readback prima di chiedere login/decisione o esecuzione VPS. Non presumere accesso SSH: qui il VPS è operato dall'utente con comandi pinned.
3. Aggiornare a ogni checkpoint handoff, roadmap, manuale installazione/configurazione e sprint. Non cambiare main/mergiare automaticamente PR o trasformare CI/staging in release acceptance.
4. Tutti domini, indirizzi, porte, reti, subnet, bridge, nomi, UID/GID, path, trust, issuer/client/scope, tenant, timeout e scheduler sono parametri espliciti. I valori lab sotto sono binding di questa installazione, non default del prodotto.
5. Non stampare token, secret, env completi, private key, payload raw o log integrali. Ricevute/journal restano privati sul VPS. Usare Python **-B** nelle procedure host. Conservare backup, originali/rollback e tentativi falliti; cleanup solo proprio e verificato, mai force su container avviati/estranei.
6. Revisioni live, branch, main e candidato non sono equivalenti. Prima di modificare inventariare diff/PR per evitare doppioni. Nel workspace vecchio il repo Gateway è dirty: pubblicare soltanto file mirati su tree GitHub fresco, mai l'intero checkout.
7. Nella chat conclusa niente Docker/nft/systemd/Java runtime native locali disponibili; test native in CI e sul target. UID0 mappato non permette chown636/10006: skip locali non sono acceptance. Non generare nuove prove host fittizie.

## 3. PET e documentazione da leggere

[Roadmap](../OUF_ROADMAP_PET_1_7.md), [manuale installazione](../installation/OUF_INSTALLATION_MANUAL.md), [sprint](../sprints/OUF_ACQUISITION_TO_UDP_2026-10-02.md), storico [1 ottobre](OUF_HANDOFF_2026-10-01_FILE_TO_UDP_NEXT_SPRINT.md), con registro gate ereditati e collegamenti agli handoff 25/27/29/30 settembre e audit 27 settembre. Le sezioni cronologiche vecchie non sostituiscono questo checkpoint attuale.

Normativa: L0 Alignment Matrix v1.7; Source Onboarding v1.6 §§92–92.2 e THS; Semantic v1.3 §§9.2,10–11,17–18; UDP v1.3 §§21–22,109.2,109.6–109.9; Authorization v1.5 §36.10; MCP v1.4; Gateway v1.5. Gateway prescrive confini northbound/southbound distinguibili per route, policy, credenziali, log e zone; il proxy non fa ETL né decisioni di dominio.

Pacchetto letto nella chat: `OUF_Reality_Baseline_Package_v1_7(20261001-185201).zip`, SHA256 `e63df67e8817eec38a9d4b3eb736b020f693b932f3360dc02f4555330f2201ce`; 323 checksum interni verificati senza mismatch. Nel vecchio workspace esistono `baseline/OUF_Reality_Baseline_Package_v1_7/` e `pet-text/`. Possono non sopravvivere alla nuova chat. Verificare disponibilità autorizzata; se mancano, richiedere il pacchetto normativo. Non accedere alla Library di altre chat e non trattare questa sintesi come sostituto PET. Si può proseguire il readback già preparato senza reinterpretare una norma assente.

## 4. Repository, PR, revisioni e CI verificate

Owner GitHub **GioNob**. Pin verificati durante preparazione del presente handoff:

| Repository / PR | Branch / pin | Stato |
| --- | --- | --- |
| ouf-api-gateway [PR56](https://github.com/GioNob/ouf-api-gateway/pull/56) | `codex/semantic-provider-request-boundary`, HEAD `85914e39bd0aa9f8e7a0a0a9d3b9db6007633ff8`, base `codex/consultation-live-c14d3f23` | OPEN DRAFT; 28/28 check runs SUCCESS, push+PR. config-contract 454 passed/64 opt-in skips; native Docker/kernel/TLS/systemd separatamente verdi. |
| ouf-semantic-registry [PR30](https://github.com/GioNob/ouf-semantic-registry/pull/30) | `codex/semantic-provider-workload-auth`, HEAD `c2b4ae5abed1236378c7060b3eb3dac126672cbc`, base `codex/semantic-discovery-jobs` | OPEN DRAFT; 14/14 check runs SUCCESS. Workload OAuth/HTTPS testato; **nessuna immagine staged/built/live provata** per questo incremento. |
| ouf-semantic-registry [PR26](https://github.com/GioNob/ouf-semantic-registry/pull/26) | `codex/r4a-smoke-semantic-inventory`, base main; prima di questo handoff HEAD `ade6315eda1020efe37dbfa0ec6586ed75a720cc` | OPEN DRAFT; coordinamento e procedure. Il commit che contiene questo file aggiorna HEAD; il pin precedente non è l'HEAD finale. |

Riferimenti storici da riconciliare prima di usare/modificare: Semantic PR27 delta RDF già live, PR28 disponibilità Discovery, MCP PR48/Gateway PR55 pacchetto identità. Il tentativo di rilettura di queste quattro PR durante l'handoff ha avuto timeout connector: il loro stato corrente non è attestato qui. Non inferire merge/chiusura/assenza da timeout. Non ricostruire un nuovo motore identità o nuove API Discovery perché la PR non è stata riletta.

Correzioni già sviluppate:

- Source read/search/exact refs Semantic, proiezione MCP `semantic.search`/`semantic.get`, contratto HUMAN consultation distinto da SERVICE read, byte-body fix MCP e RDF asserted snapshot: rollout e positivo HUMAN già provati.
- Discovery già ha API request/status/candidates/providers/adoption governata; riusare, non creare un secondo percorso.
- PR28 corregge provider disabled/nessun provider: nuove richieste 503 `SEM_DISCOVERY_NO_ENABLED_PROVIDER`, queued jobs fail esplicito; un provider realmente consultato senza risultati può invece riuscire. Verificare eredità nel branch PR30 e rollout futuro; il live è ancora e7bc5190.
- Adoption formalizzata scrive `immutable_semantic_snapshot`/`external_semantic_origin`; projection RDF imported legge `revision_interchange_snapshot`. Restano da verificare definizioni e snapshot esatti dell'adozione, niente fallback latest. normalized_payload candidato `{}` e projection metadata insufficiente non diventano mapping completo per sola connettività.
- Test-only Gateway `8b1fadb31060cce4deaf3962691aa0aaf17f5865`: tamper MAC deve decodificare, flip byte e ricodificare; cambiare solo padding Base64 non garantiva alterazione MAC. Non revertire né ricompilare container per questo test.

## 5. Baseline live e preparazioni target da riusare

### 5.1 Container produttivi e policy

| Ruolo | Revisione live / digest |
| --- | --- |
| Semantic `ouf-semantic` | `e7bc5190f9e6afbbc4cf3c90d5d4970afbfad14b`, `sha256:f6525f2512c72a600ebcbc7060d55355d86e0627487b655e7c5c6288a0be7fc6` |
| MCP `ouf-mcp` | `394b4b1540b575564f0ba58541df9d7efc59fb87`, `sha256:99a158f780243b3fa05199bed9db01197be8ae60ae1e75ad5432964509422872` |
| Gateway `ouf-apisix` | APISIX **3.18.0**, image `sha256:84e6b5e787e9f889ebff88161cb9a16599bafcffa236c6b54c7f779a0655940d`, c14d3f23-derived routes |
| Onboarding | `6340d5bf120e09b47c32177656e2c377a4c03640`, `sha256:ec6f2a962261a8433bfe103347afa2202837fcec90d210d9b5232711b854ee8a` |
| Ingestion | `163c167d09b8371ff7a62ce7068e9d485b6969b7`, `sha256:b07a4a786ca48335feae887e18dc7c4c6cdd9bd0a3a255f83d18c7c1616eec48` |
| UDP | `83249a897eb4add4289b5181b3299f48ea4c0f99`, `sha256:5e048a859716d6674355e72238f03f899abd705a943ceadbdc5c8863d28f4e9f`, Flyway34 |

Last observed IDs: live Gateway `dcbe26bed97dd5c7ac8a131ec2badf77b0291c2ef32907be639bfa09c36596d9`; Semantic `7ae83be8c1fe9fe25774b7d748e35153652b29b2501886f89daeabb83bd1a147`; Ingestion `1fa5450574e72ef15ebb2c74e0f421f04d24c842975e324ac958f071672fbb7e`. These are readback bindings, not permanent role defaults. Other shared infrastructure (Caddy, etcd, Keycloak, MinIO, Postgres, operational owner) was not switched in the provider preparation.

Authorization remains **ouf-lab-authorization:38**. Historical :36 recovery grants expired; don't reuse them. `gateway.southbound.invoke` and `ouf.semantic.discovery` scopes exist/no drift; only `gateway.southbound.invoke` DEFAULT-bound to **ouf-semantic** SERVICE. Discovery scope not client-bound/descriptor not registered or published at last inventory. Provider disabled, live workload/provider OAuth configuration uninstalled, worker enabled, queue/adopted/unexpired counts zero at inventory. HUMAN discovery/MCP binding and live provider connectivity unproven.

Calling workload: `ouf-semantic` existing confidential service account. Private credential `/etc/ouf/semantic-provider-auth/client-secret`, UID/GID10001,0600; prepared/verified, no rotation. RS256/JWKS signature, SERVICE claims/tenant/audience/TTL299 verified; introspection inactive was corrected by signature verification. Revocation and Gateway admission not proven; no mount on live Semantic.

Passive OIDC validator: **ouf-api-gateway**, enabled/confidential/client-secret, **serviceAccountsEnabled=false**. It validates bearer/JWKS; do not enable service accounts or invent a second M2M identity. Validator credential is distinct from caller credential. Successful master login administrative user **oufadmin** was explicitly observed; SSH user alone is not evidence of KC identity. Session may expire; the §6 inventory does not use kcadm.

Issuer `https://auth.ouf-lab.it/realms/ouf`, token endpoint `/protocol/openid-connect/token` under issuer; MCP execution `https://api.ouf-lab.it/internal/capabilities/v1/execute`. These are explicit lab configuration only.

### 5.2 Receipt roots — absolute paths are host bindings, not defaults

All roots below are under `/etc/ouf/deploy-snapshots/`; keep private root ownership/modes and referenced cohorts. Preparation flags describe time of receipt, not current mounts after creation.

| Preparation | Exact receipt relative to parent | Proven / residual |
| --- | --- | --- |
| Adapter image | `semantic-provider-adapter-20261002-173408/stage-receipt.json` | image `sha256:a697bf75bf7d51afadadfaccd3d80537e9a5fb2a08f0d194c6dfd9462e812468`, source `52c0dcf11654a4d3d0f17a6902ed095975466fb9`, UID10006; now created stopped, no rebuild. Base `python@sha256:bb2988715db2cf7ace7b53f38f3cffbef7c7046a656bee66245eb0ed386e2e81`. |
| Trust PKI/MAC | `semantic-provider-trust-20261002-212033/trust-receipt.json` | CA/public-root merged bundle/role leaves/purpose MAC pair verified. Offline ca.key never mounted/read by launch; role files individually RO mounted on stopped candidates. |
| Runtime plan | `semantic-provider-runtime-20261002-222530/stage-receipt.json` | root-private binding.json/runtime-plan.json compiled; native runtime activation not proved. |
| TLS startup | `semantic-provider-tls-runtime-20261002-230418/tls-runtime-receipt.json` | config.yaml/apisix.yaml/adapter.json prepared, now mounted RO on stopped candidates. apisix.yaml includes private leaf key: never cat. |
| Java trust | `semantic-provider-java-trust-20261003-061729/java-trust-receipt.json` | merged public roots preserved for selected old Semantic image; private PKCS12/JVM options UID10001, no private keys. Not mounted on live Semantic. Recheck public roots for future selected PR30 image. |
| DNS observation | `semantic-provider-dns-20261003-063746/dns-receipt.json` | Historical only, one address observed, **no kernel lease**. Expired observation must never seed runtime sets. |
| Cold networks/guards | `semantic-provider-networks-20261003-072023/prepared/network-receipt.json` | Two dedicated networks + owned inet/bridge deny-only tables installed. Candidate configuration now exists: old EMPTY predicates are historical. |
| Lease source package | `semantic-lease-package-20261003-075940/source-package-receipt.json` | Nine sealed files staged, no daemon/unit installed or started. Reuse frozen cohort. |
| Boot stage | `semantic-boot-guard-20261003-083310/boot-stage-receipt.json` | Sealed deny-only restore profile, unit and Docker drop-in. |
| Boot installation | `semantic-boot-install-20261003-103547/install-journal.json` | Plan/apply/verify PASS, loaded guard/drop-in, Docker PID1740 preserved, no restart/rule/provider call. Real reboot unproven. |
| Candidate-input inventory | `semantic-candidate-inputs-20261003-111502` | Original false block retained; corrected inventory-public-trust-fix.py PASS. Do not reuse bad original inventory.py. |
| Validator credential | `semantic-southbound-validator-20261003-114001/prepared/credential-receipt.json` | Existing secret private copy636:6360600, current profile/secret verified; no rotate/config/grant. |
| Launch inputs | `semantic-provider-launch-inputs-20261003-124906/prepared/launch-input-receipt.json` | Leaf key pairs/receipt MAC pair verified, root0600 southbound.env created; no offline CA key read; no grants/providers. |
| Stopped manifest | `semantic-provider-candidate-manifest-20261003-130410/prepared/stopped-manifest.json` | Sealed exact images/mounts/network/IP/resource specs; initial no-container/no-reservation state historical. |
| Static IPAM | `semantic-provider-static-ipam-20261003-133526/prepared/ipam-receipt.json` | Target accepted never-started disposable static create on all THREE existing networks; probes removed; no address reservation/packet proof. |
| Actual stopped creation | `semantic-provider-stopped-create-20261003-135106/prepared/creation-journal.json` | Two actual candidates, owned transaction/manifest labels, never started, checked strict config/env/RO mounts/net IDs/static IP config. This is latest target PASS. |

Metadata pitfall resolved: public trust-bundle.pem225117 bytes/root644 was incorrectly subjected to 131072 private-JSON cap. Only public CA/trust bundle cap raised to1MiB; private JSON/ownership/mode/link/ancestor checks preserved. Correct inventory source840abe...; no chmod/chown of valid artifacts needed.

IPAM pitfall resolved: one CI daemon rejected static IP on an auto-allocated subnet. This did NOT prove the target incapable. Target Docker29.8.1 positively accepted static create on backend/internal/egress. **Do not recreate/normalize these networks, rebind boot guard or restage all artifacts for that old inference.** Do not infer causality from daemon version alone; evidence is the target probe.

### 5.3 Source pins for frozen helpers

| Helper | Source commit | SHA256 |
| --- | --- | --- |
| create_semantic_provider_stopped_candidates.py | `93e861fe8c8a43912f0cb78a74adceb2db509dd9` | `4babe7ebfdffe6ef1ab4f81bacad52c86eabbbe991d30bf3c41de65d7f47ffdd` |
| stage_semantic_provider_candidates.py | `9596f450ccb2ee38730b147e22e58ceaafd52841` | `cb04a31e4d13e182b08de2df75fa13a4ec01a7c0671239339451523f2dfc9f84` |
| prepare_semantic_provider_launch_inputs.py | `732d65a8bcebb1545086702da54ee01c01c3b823` | `4a5483d5ff54bdc79ef26e4ae436ac41ebd12363be0640005d1d6f695df93e8d` |
| prepare_semantic_southbound_validator_credentials.py | `faaf43748648207f51edee890be4b3dc6592cfc5` | `3d349fd816c1c04091daada0c20eefae7b41396230e89fb7dcc46cb427aace31` |
| inventory_semantic_provider_candidate_inputs.py | `840abe970bde4ab1edc1c6aeecd84eee9d1fc5a8` | `7bbf6a50722f475323b33568e3bc875b57d7f3e3de78d62c8f7410442c48c6c9` |
| inventory_semantic_provider_static_ipam.py | `8c04d8fb6dd251407e8c86c583d40b53a66f1179` | `426d3aab4c05bb24a46b2c41279a6f6fc847b85d3fc6c2954d236200a4cc68a3` |
| inventory_semantic_provider_guard_custody.py — target PASS | `85914e39bd0aa9f8e7a0a0a9d3b9db6007633ff8` | `fabd47c6ce8919bc7a910cbaf63f66f1fb786b00c239ae41757c1fd0df829b8d` |

Frozen lease cohort source `7a81cc344b513d04fd276cd1923a9c23197aceee`: scripts stage_semantic_lease_package.py/run_semantic_provider_lease_owner.py/prepare_semantic_provider_trust.py; tools materialize_semantic_lease_service.py/materialize_southbound_kernel.py/materialize_southbound_lease_refresh.py/semantic_provider_dns.py/semantic_provider_lease_owner.py/semantic_provider_lease_nft.py. Nine root0600 files in source/scripts and source/tools; no daemon/API started.

Boot stage source `d7f65fc73a6beb0a36e77972301a4c823fe21c5d`; installer `39923852d93a3b0907edce91cf87e9386b11621b`. Host source files and artifact hashes are bound by receipts. Do not mutate frozen cohorts in place.

### 5.4 Network/trust/runtime facts

Host rootful Docker29.8.1, systemd257, Python3.13.5, nftables1.1.3. Paths `/usr/bin/docker`, `/usr/bin/python3`, `/usr/sbin/nft`, `/usr/sbin/ip`, `/usr/bin/systemctl`, `/usr/bin/openssl`; Keycloak `/opt/keycloak/bin/kcadm.sh` in ouf-keycloak.

| Network | ID | Binding |
| --- | --- | --- |
| ouf-backend | `113b5f0a3c53059b087a2ce997d2670cc057e88c0c17d4291b3b41a51ce26ba3` | internal, br-113b5f0a3c53,172.18.0.0/16,gateway172.18.0.1,v4 |
| ouf-gateway-control | `1209d67944755d95601b96719c0a5b1860ac2a6f137c10077da7b4e9967637aa` | internal,br-1209d6794475,172.20/16,v4; shared |
| ouf-semantic-provider-internal | `2a6652422b45db6f359d94d779ab8625b1ad99b1750bb54582b4b8c4e8aa9307` | bridge oufsp-int,internal,v4,172.21.0.0/16,gateway172.21.0.1 |
| ouf-semantic-provider-egress | `db8bc9f8feccc3c14f2818a5c843f5c08e5eb2e192530858d88a70ce1cc0a86d` | bridge oufsp-egress,non-internal,v4,172.22.0.0/16,gateway172.22.0.1 |

Owned **inet + bridge table ouf_sem_provider**, currently **deny-only**, no provider sets/flows/lease installed. Never DROP the entire shared backend/control network. Original topology snapshot hash `8b0eb1c691a5010f98f22e34bb3de8de0b65cf8f9bab3079fc6c193778b857d4` is historical, not an atomic current state proof.

Southbound candidate primary backend, secondary provider-internal + provider-egress; adapter primary provider-internal + provider-egress. Planned static addresses in private manifest/journal, not inferred as allocated while stopped. Both restart=no/capDropALL/no published ports/512MiB memory and same swap limit/pids128/no healthcheck; adapter read-only root, APISIX root writable; exact individual RO mounts. Created Docker endpoints can defer NetworkID until start: helper binds current network name→ID separately and checks IPAMConfig rather than claiming packet proof.

Selected lab DNS resolvers `46.38.252.230`, `46.38.225.230`, UDP/TCP53. Supplied IPv6 `2a03:4000:0:1::e1e6` deferred; current profileIPv4 only. Provider `https://schema.gov.it:443/sparql`; namespaces https://w3id.org/italia/ont/ and controlled-vocabulary/. No arbitrary chatbot SPARQL/provider URL.

Southbound TLS-only10443/SNIouf-semantic-southbound, no HTTP/admin/control/extra-metrics listeners. Adapter9443/SNIouf-semantic-provider; POST `/internal/providers/schema-gov/search`, GET `/internal/providers/schema-gov/fetch`. Adapter worker4/deadline20/providerTimeout10/maxRequest65536/maxResponse8388608/maxIntent2000. TLS cert/key/purpose MAC paths under `/run/ouf-semantic-provider/`, upstream CA/trust-bundle.pem. Separate purpose-bound receipt MAC, not OAuth/delegation key. Issuer/audience/service workload/tenant/scopes bound by private plan. Northbound Gateway env must not be copied wholesale into southbound.

Boot guard installed targets `/etc/systemd/system/ouf-semantic-boot-guard.service` and `/etc/systemd/system/docker.service.d/90-ouf-semantic-boot-guard.conf`. DefaultDependencies=no, after local-fs/nftables, before Docker; Docker Requires/After guard and **ExecStartPre validates every start**. Existing tables must match; both absent can restore strict-create; partial/foreign tables block. Original installer verifies Docker PID preservation, not a permanent verifier after a legitimate restart/reboot. Current expected PID1740 is intentional custody binding; any later change requires reconciliation, not silent adoption.

### 5.5 Already proven native tests — don't rerun indiscriminately

- Real nft/netns default-deny and expiry rejecting new **and established** packets,9 host tests PASS.
- Real Docker bridge native hook + scoped host forward, default-deny/unregistered workload/expired leases, own cleanup,1 host test17.521s PASS.
- Real APISIX3.18 CI OIDC → purpose receipt → adapter TLS, forged/direct/incomplete TLS+HTTP and wrong-hostname/SNI/plaintext denials.
- Boot/systemd native CI restore/dependency/foreign/partial recovery, no Docker restart/PID change. Actual host boot install PASS; **real reboot not proven**.
- Target embedded DockerDNS fixture at `semantic-docker-dns-20261003-105129`: source `b4c2faefb7a526c3455632212275633c60d826e7`; UDP/TCPA+AAAA, forwarded source bound to container, selected resolver/default deny/unregistered denial/flow removal, shared structure unchanged, own cleanup,15.661s. **provider0/externalDNS0**; isolated fixture, not production packet acceptance.
- Real Docker stopped-create tests4 and target static-IPAM admission tests4, plus root role-owned launch/trust/credential fixtures in CI. Target creation itself now PASS.
- Current custody helper7 fixture tests pass; native jobs inherited unchanged are green. **Custody inventory target PASS ora registrato nel checkpoint corrente; intent target ancora pendente**.

## 6. Comando custody storico — ora eseguito con PASS

Questa è la riproduzione completa dell'ultimo comando proposto. Fa download checksum-pinned e installa un nuovo helper root0600 in snapshot privato, poi legge stato Docker/reti/nft/systemd e ricevute. **Nessuna IAM/DNS/provider call, nessuno start o cambiamento container/regole/route. Non necessita refresh kcadm.** L'utente ha esplicitamente rinviato l'intero blocco alla nuova chat.

```bash
(
set -euo pipefail

OUF_CUSTODY_DOWNLOAD=$(mktemp)
trap 'rm -f "$OUF_CUSTODY_DOWNLOAD"' EXIT

curl --fail --silent --show-error \
  https://raw.githubusercontent.com/GioNob/ouf-api-gateway/85914e39bd0aa9f8e7a0a0a9d3b9db6007633ff8/scripts/inventory_semantic_provider_guard_custody.py \
  -o "$OUF_CUSTODY_DOWNLOAD"

printf '%s  %s\n' \
  fabd47c6ce8919bc7a910cbaf63f66f1fb786b00c239ae41757c1fd0df829b8d \
  "$OUF_CUSTODY_DOWNLOAD" | sha256sum -c -

OUF_CUSTODY_ROOT="/etc/ouf/deploy-snapshots/semantic-provider-guard-custody-$(date -u +%Y%m%d-%H%M%S)"
sudo install -d -m 0700 -o root -g root "$OUF_CUSTODY_ROOT"
sudo install -m 0600 -o root -g root \
  "$OUF_CUSTODY_DOWNLOAD" "$OUF_CUSTODY_ROOT/inventory.py"

sudo /usr/bin/python3 -B "$OUF_CUSTODY_ROOT/inventory.py" \
  --manifest-root /etc/ouf/deploy-snapshots/semantic-provider-candidate-manifest-20261003-130410/prepared \
  --creation-root /etc/ouf/deploy-snapshots/semantic-provider-stopped-create-20261003-135106/prepared \
  --network-root /etc/ouf/deploy-snapshots/semantic-provider-networks-20261003-072023/prepared \
  --boot-stage-root /etc/ouf/deploy-snapshots/semantic-boot-guard-20261003-083310 \
  --boot-install-root /etc/ouf/deploy-snapshots/semantic-boot-install-20261003-103547 \
  --creation-source-commit 93e861fe8c8a43912f0cb78a74adceb2db509dd9 \
  --docker-path /usr/bin/docker \
  --nft-path /usr/sbin/nft \
  --systemctl-path /usr/bin/systemctl
)
```

Atteso (non ancora osservato sul target): JSON schema `ouf.semantic-provider-guard-custody.v1`, candidateCount2/neverStartedtrue/bootProfileDENY_ONLY/startAuthorizedfalse/kernelLeaseInstalledfalse/bootTransitionRequiredBeforeRuntimeRulestrue, quindi `SEMANTIC_PROVIDER_GUARD_CUSTODY_INVENTORY=PASS`.

Il helper è **custody inventory**, non sostituisce il readback completo config/env/mounts effettuato dal creator. Verifica binding journal/manifest/cold/boot, ID/image/labels/never-started/restart=no, assenza endpoint estranei dedicati, boot files/sorgenti hash, stato systemd/PID/pre-start fingerprint e footprint guard inet+bridge. Non prende lock e non certifica uno snapshot atomico. Se BLOCKED, stampato solo codice generico redatto: diagnosi puntuale read-only, non replay della create né correzione live alla cieca.

## 7. Cosa fare dopo il readback, senza rifare lavoro precedente

1. **Custody PASS riconciliato** nel checkpoint corrente: prossimo intervento è il transition intent §11, non un replay autonomo del §6. Non chiamare i vecchi stage/cold verifiers che pretendono nomi assenti/reti vuote. Se drift nel preflight, isolare la differenza conservando journal e container.
2. **Preparare una transizione coordinata** dalle tabelle deny-only al profilo statico/empty provider sets, insieme alla custodia boot/systemd. Non basta applicare nft: il boot guard attuale verifica la vecchia struttura e bloccherebbe un futuro Docker start. Nessun helper di transizione è stato implementato o eseguito in questa chat: la frase «preparo regole/insiemi» era direzione di lavoro, non prova di completamento. Definire intent/journal, fail-closed tra ogni step, rollback/partial reconciliation, lettura shared structure, compatibilità daemon/reboot prima di host apply. Non alterare gli originali sealed in place.
3. Riusare kernel compiler/lease9cohort. `materialize(..., empty_provider_sets=True)` emette insiemi timeout **vuoti** in inet+bridge; static exact flows per gateway→adapter, DNS e infrastruttura autorizzata. `guardedInterfaces` soltanto dedicate; mai aprire broad egress né scambiare eccezione indirizzo privato per authority. Governare distintamente identity/JWKS e provider esterno. Resolver/endpoint/source/IP/port e private exception espliciti, nessun seed dai vecchi DNS. LeaseOwner query fresh A+AAAA a tutti i resolver selezionati, TTL bounded/tempo sottratto, apply atomico entrambe famiglie/readback, revoca su failure/stop/start. Finite expiry nega anche established.
4. Prima di start/daemon: provare namespace/IP/bridge source binding e confini/pacchetti/DNS/direct bypass/spoof/IPv6 nel perimetro effettivamente scelto. Valutare con attenzione due funzioni diverse di hash: boot footprint elimina handles/metainfo; NftBackend structure hash mantiene metadata/handles e rimuove set elem. Ricreazione tabelle e leases attivi richiedono binding coerenti, non riutilizzo cieco di un expected hash né accettazione automatica di struttura estranea. Non dichiarare supporto reboot sulla sola CI.
5. Quando il piano è concreto e verificato, installare/avviare solo i componenti necessari con procedure governate. La creazione non è autorizzazione startup, la connettività TLS non è IAM admission, il JWT verificato non prova revocation. Provare OIDC/purpose receipt/TLS adapter/hostname, owner diretti negati e workload gateway admission prima di chiamate provider.
6. PR30 Semantic: future build/stage/release con backup/migration-aware history delta. Il branch eredita **V10**, quindi NON usare alla cieca il vecchio helper RDF «migrations identical». Confrontare il truststore pubblico dell'immagine selezionata con il Java trust preparato; se diverso, preparare solo trust appropriato alla nuova immagine. Coordinare config provider/gateway/workload token+mounts; live attuale resta disabled.
7. Attivare Discovery governata solo dopo provider e autorizzazioni pronte: inventariare descriptor actors/operation/purpose; scopes≠capability registration≠policy grant≠route≠MCP discovery. Riutilizzare API asynchronous native con ownership/idempotency/bounds/status/candidate expiry/adozione THS e exact snapshot. `SUCCEEDED` vuoto non prova provider consultato se disabled. Non allargare read receipt in write/adoption authority.
8. Riprendere il mapping Teatri con artefatti adeguati, proposta source/field/identity/classifications/transformazioni/version pins, THS e bundle ACTIVE; collegare file immediate ingestion e API scheduler-before-ingestion, UDP resolution/THS/resume/recovery e Search autorizzato. Poi acceptance per nuovo percorso e secondo chatbot, preservando il resto del backlog.

Reboot/Docker restart del VPS hanno impatto condiviso: non farli per comodità. Se un gate li richiede realmente, predisporre verifica/backup/restore/rollback e finestra concreta prima della coordinazione con l'utente. Nessun reboot/restart è stato eseguito né pianificato come prossimo comando.

## 8. Business evidence congelata e decisioni mapping ancora aperte

### Cinema

Source `managed-cinema-8ec8ae90`, run `86809c17-3354-45ca-a7e6-57e903944b24` SUCCEEDED; otto handoff ACKED/lineage e otto UDP intake PROCESSED/jobsSUCCEEDED/NEW_OBJECT/observations/revisions/bindings/active objects; quarantene recuperate governatamente, audit conservato. Schedule trigger_once consumed/DISABLED. Vecchio `ouf-udp-r4a-smoke` con JAR incompatibile è stato fermato/retained/restart=no; non riavviare. Historical owner causa non provata integralmente.

Semantic artifact `5ae731cc-e4c5-43a3-aa5e-a7576adbd3a1`, semanticId `https://api.ouf-lab.it/semantic/cinema`, revision `51706bed-81e4-4306-aca1-70119821727d`, publication set `f92a2e17-30c9-456f-bb12-63afa84f41e6`, ACTIVEv1. Positivo HUMAN ChatGPT/MCP semantic.get pinned dopo RDF rollout:17 asserted triples,partialfalse,text/turtle,RDF SHA256 `4340986102db6e47345dd8157734d9db83b928edd94485f1b9a5b9e81c497a2e`. JSON metadata hash distinto `78a39fc30dab8bf221bc9eb8c2567bb2abef57e72ba1e4e29a87a23db4142391`. Cinema subClassOf schema:MovieTheater, nome/indirizzo labels/domain/range. Non prova ontology closure/inference o class Teatro; JSON definitions restano vuote. R-SMOKE Search completo rimane aperto.

### Teatri

Account MCP precedente `ouf-admin`, subject `b93d8cf6-cd14-4ee6-91d7-84cd76c4f500`; non confonderlo con master admin/SSH oufadmin. Nuova chat deve seguire account routing connector corrente, non ricostruire link_id. Connector storico `6aafef96b4148191b767e9af7b756a07` è un riferimento, non autorizzazione a presumere sessione o tool attivi.

Picker `b6de7b63-4a1a-47d8-858e-3cc5f0adad51`; asset `6609b245-86ed-4315-8ce0-73f2a8555bf3`; profile job `2f49ea03-b715-493b-ba25-a3f82007cd3d` SUCCEEDED; profile `7984c39c-7396-4248-ab0a-f2efc390b49c`v1. CSVUTF8/semicolon/header1,13rows20cols/ONE_ROW_ONE_SOURCE_OBJECT, proposta PENDING_HUMAN_REVIEW. Nessuna nuova DRAFT/ACTIVE/run/UDP Teatri provata.

Fields: nome_teatro,tipologia,toponimo,nome_indirizzo,civico,cap,citta,provincia,latitudine,longitudine,sistema_riferimento,precisione_coordinate,capienza_posti,spettacoli_stagione,stagione_riferimento,note,fonte_indirizzo,fonte_coordinate,fonte_altri_dati,data_verifica. Non riportare sample raw. CAP inferitoLONG non è tipo semantico/codice preservato; CRS dichiarato non valida geometria. data_verifica≠businessvalidFrom. Multi-hall granularity e provenance per-field da governare. Proposta NATIVE_KEY nome_teatro ancora unapproved: unicità su13righe non prova stabilità e non è chiave canonica. CLASS Teatro/Theatre search[] osservato non è censimento completo. Cinema/MovieTheater non autorizza analogia Theatre. Official vocabulary tipologia/precisione e transformations whitelist da valutare.

Identità: source-row key distinta da canonical UDP identity. Motore class-neutral già nel branch corretto; non riscrivere weighted legacy. Policy proprietà/comparatori/candidate coverage; subset sufficiente concorde anche in entrambe direzioni può MATCH con premesse/unicità; tutti comuni confrontabili diversi→distinct; partial/conflict/missing→incerto. NEW solo allowAutoNew + coverage completa; overflow REVIEW_REQUIRED/RESOLUTION_TOO_BROAD. Score/frequenza/selettività non conferiscono autorità. MATCH non equivale a merge canonico automatico. Review HUMAN/THS non blocca durable ACK/watermark né tiene transazione DB aperta; append-only audit/lineage.

## 9. Backlog ereditato: nessuna chiusura per omissione

| Gate | Residuo / limite della prova |
| --- | --- |
| R-SMOKE completo | Cinema8/8 non basta: Search Gateway/MCP almeno3oggetti, minimizzazione proprietà/oggetto,2pagine,cursor invalid/partial,label/authority/audit. |
| Seconda fonte sovrapposta/identity review | Source distinta con class/candidate overlap, subset entrambe direzioni, concorde/differente/conflicts/missing/authority, disjoint forms,boundedness/overflow/coverage/backfill, THS atomic/resume. Teatri non prova automaticamente questo gate. |
| Gateway managed upload acceptance | Streaming/primi byte,413 oversized senza assetparziale,415,media-type/digest,anonimi,limiti/idempotenza/rollback. Upload/profile reale è solo una parte. |
| MCP/channel neutrality | Secondo host/client senza copia manuale AssetID,login continuity e limiti/adattatori; niente bridge hostfiles arbitrario. |
| Semantic generalità | Exact refs/provenance/DTO/schema/consumer compatibilità, external discovery/adoption snapshot/definitions, class/property/vocab sufficienti, mapping completo. HUMAN read positivo provato soltanto per il path attuale. |
| Data Lake indipendente | Byte/hash/S3 e DB-objectstore reconciliation, backup/restore oggetti. ACK/materializzazione non sono lettura indipendente byte. |
| Replay RAW/SPI | Trasporto/esecutore e RAW durevole. UDP REPRODUCE non sostituisce retry originale/source replay. Nessun replay per chiudere formalmente questo handoff. |
| Lake policy | Retention/access per source/type/zone,enforcement/cancellazione effettiva; no defaults lab universalizzati. |
| R-INSTALL/portabilità | Manifest/secretrefs,bootstrap idempotente capabilities/IAM/Authorization/routes,cleaninstall,upgradeN/N+1,rollback/restore/PITR/reconciliation,macchine/reti/domain/Enti diversi. Le oltre100capabilities devono avere procedura batch/reconcile automatizzabile, non una lunga sequenza manuale ciascuna. |
| Network/TLS/egress | Native fixture/CI PASS nel proprio scope; target provider deployment/boot custody e runtime packets/admission ancora da provare. Real reboot/IPv6/FQDN leases non attestati dal cold stage. |
| Performance/concurrency | Profili/SLO rappresentativi,race lease/rollout/governor multi-replica; fixture vuote non acceptance. |
| Awareness/collectors | Cross-owner raccolta/proiezioni/alert e13marker ING_ACTIVATION_DISCOVERY_UNAVAILABLE da correlare; non dichiarare run riuscito fallito né healthy dalla mancanza log. |
| Latenza ChatGPT–MCP | Correlare host/tool/Gateway/owner; la lentezza chat percepita non prova latenza backend. |
| Cross-module release/branch/PR | Reconcile main/stalebase/live/pin,SBOM/checksum/security/compatibility/consumer schema; workercompatibility generale non divieto arbitrario N/N+1. CI/build/tag/deploy/live acceptance distinti. |
| Causalità storica403/reference | Non integralmente provata; conservare evidenze, niente mutazioni aggiuntive solo per una spiegazione. |

## 10. Checklist di ingresso della nuova chat

- Leggere questo file e il registro ereditato; verificare PET realmente disponibili. Riassumere brevemente obiettivo e ultimoPASS, senza rifare inventario completo manuale.
- Rileggere pin GitHub/PR/CI correnti con connector, senza assumere che HEAD/main/live coincidano. Timeout non è assenza. Niente merge automatico.
- Il comando custody §6 è stato eseguito con PASS; il primo intervento ora pendente è il transition intent §11. Non riproporre un replay custody autonomo né presumere un PASS intent.
- Custody PASS registrato: proseguire dal preflight intent e protocollo boot/runtime/emptysets/lease, con implementazione e native tests prima di attivazione.
- Se serve HUMAN decision/login o SSH reale, preparare prima il risultato verificabile. Non chiedere permessi già conferiti per codice/test/read-only/aggiornamento docs.
- Conservare e aggiornare questo handoff come punto di ingresso insieme ai quattro documenti canonici. Questa chat ha eseguito solo aggiornamenti GitHub nella fase di handoff, non azioni VPS.


## 11. Primo intervento VPS pendente — solo transition intent privato

NON ESEGUITO. Su VPS/sessione SSH oufadmin; non richiede login Keycloak. Incollare solo output redatto, senza leggere i tre file privati. Apply qui significa esclusivamente scrittura di nuovi file di evidenza; non modifica regole/unit/container. In caso di BLOCKED conservare root e parziali, non rieseguire apply.

```bash
(
set -euo pipefail
OUF_TRANSITION_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_TRANSITION_TMP"' EXIT

curl --fail --silent --show-error --proto '=https' --max-time 30 \
  https://raw.githubusercontent.com/GioNob/ouf-api-gateway/392234edc50c6e8cd19a3028b3e9e19d6f1955b4/scripts/prepare_semantic_provider_transition_intent.py \
  -o "$OUF_TRANSITION_TMP/prepare_semantic_provider_transition_intent.py"
curl --fail --silent --show-error --proto '=https' --max-time 30 \
  https://raw.githubusercontent.com/GioNob/ouf-api-gateway/85914e39bd0aa9f8e7a0a0a9d3b9db6007633ff8/scripts/inventory_semantic_provider_guard_custody.py \
  -o "$OUF_TRANSITION_TMP/inventory_semantic_provider_guard_custody.py"

printf '%s  %s\n' \
  f1cc60568118387cad11a8546f3b0c2c64941c6a51a28611e4c62a009db57422 \
  "$OUF_TRANSITION_TMP/prepare_semantic_provider_transition_intent.py" \
  fabd47c6ce8919bc7a910cbaf63f66f1fb786b00c239ae41757c1fd0df829b8d \
  "$OUF_TRANSITION_TMP/inventory_semantic_provider_guard_custody.py" | sha256sum -c -

OUF_TRANSITION_ROOT="/etc/ouf/deploy-snapshots/semantic-provider-transition-intent-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_TRANSITION_ROOT"
sudo install -d -m 0700 -o root -g root "$OUF_TRANSITION_ROOT/source/scripts"
sudo install -m 0600 -o root -g root \
  "$OUF_TRANSITION_TMP/"*.py "$OUF_TRANSITION_ROOT/source/scripts/"

OUF_TRANSITION_LOCK=$(sudo /usr/bin/python3 -B - <<'PY'
import json
from pathlib import Path
import re
p=Path('/etc/ouf/deploy-snapshots/semantic-boot-guard-20261003-083310/boot-stage-receipt.json')
v=json.loads(p.read_bytes())['profile']['runtimeDirectory']
if not isinstance(v,str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,63}',v):
    raise SystemExit('BOOT_LOCK_BINDING_BLOCKED')
print('/run/'+v+'/guard.lock')
PY
)

for OUF_TRANSITION_MODE in plan apply verify; do
  sudo /usr/bin/python3 -B "$OUF_TRANSITION_ROOT/source/scripts/prepare_semantic_provider_transition_intent.py" \
    --mode "$OUF_TRANSITION_MODE" \
    --source-commit 392234edc50c6e8cd19a3028b3e9e19d6f1955b4 \
    --custody-source-sha256 fabd47c6ce8919bc7a910cbaf63f66f1fb786b00c239ae41757c1fd0df829b8d \
    --manifest-root /etc/ouf/deploy-snapshots/semantic-provider-candidate-manifest-20261003-130410/prepared \
    --creation-root /etc/ouf/deploy-snapshots/semantic-provider-stopped-create-20261003-135106/prepared \
    --network-root /etc/ouf/deploy-snapshots/semantic-provider-networks-20261003-072023/prepared \
    --boot-stage-root /etc/ouf/deploy-snapshots/semantic-boot-guard-20261003-083310 \
    --boot-install-root /etc/ouf/deploy-snapshots/semantic-boot-install-20261003-103547 \
    --runtime-root /etc/ouf/deploy-snapshots/semantic-provider-runtime-20261002-222530 \
    --lease-package-root /etc/ouf/deploy-snapshots/semantic-lease-package-20261003-075940 \
    --snapshot-root "$OUF_TRANSITION_ROOT/prepared" \
    --boot-lock-file "$OUF_TRANSITION_LOCK" \
    --lease-source-commit 7a81cc344b513d04fd276cd1923a9c23197aceee \
    --creation-source-commit 93e861fe8c8a43912f0cb78a74adceb2db509dd9 \
    --expected-manifest-hash 052b46a56ea666971f135c75af48b3342dbeb68e2f17f1f16263a99351df88bd \
    --expected-creation-journal-hash a1c2acd9924fc0f924ded7c2d59f128ef2d8b8dd11c62484a901f628022aaae7 \
    --expected-boot-install-journal-hash 44dfac2145f509c8fb0b66983630616d25958b40f3ffc811074ebb9b3c1edda5 \
    --docker-path /usr/bin/docker \
    --nft-path /usr/sbin/nft \
    --systemctl-path /usr/bin/systemctl
done
)
```
