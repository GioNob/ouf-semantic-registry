# Audit di installabilità OUF — 23 settembre 2026

**Verdetto: NO.** Consegnando oggi i sei URL GitHub e questo manuale a un
installatore nuovo, l'installazione da zero non è riproducibile senza informazioni
esterne o una sessione con chi ha configurato il laboratorio. Questa è una
verifica delle sorgenti e dei runbook; non è stato creato un ambiente pulito né
sono stati letti i secret o modificato il server Netcup.

Autorità: Reality Baseline Package v1.7 (Blueprint L0, Matrix v1.7, PET dei
sei moduli), [manuale](OUF_INSTALLATION_MANUAL.md) §§3, 6–13, 19–21 e
[roadmap](../OUF_ROADMAP_PET_1_7.md). Authorization è nel repository
Onboarding; non è un settimo repository da installare.

## Sorgenti consegnabili: il primo blocco

| Modulo | Repository | `main` il 23/09/2026 | Stato per una nuova installazione |
|---|---|---|---|
| Onboarding/Authorization | [ouf-source-onboarding](https://github.com/GioNob/ouf-source-onboarding) | `21de5f21e903e6e99f4ef4d6617a446d60a54792` | Main disponibile, binding ambiente incompleti |
| Semantic | [ouf-semantic-registry](https://github.com/GioNob/ouf-semantic-registry) | `d188e5e727eca7a22f414f43f164f85c31411bcf` | Main disponibile, installazione integrata assente |
| Ingestion | [ouf-ingestion-runtime](https://github.com/GioNob/ouf-ingestion-runtime) | `a8ba969a5a0e20e9c53977d2875094ce82802f9d` | Il merge #31 è su `codex/r3-summary-governed`, non su main |
| UDP | [ouf-udp-object-resolution](https://github.com/GioNob/ouf-udp-object-resolution) | `6285b733c49b89cb6d3382abe8dc469f8a0e8b1b` | Main disponibile, binding ambiente incompleti |
| Gateway | [ouf-api-gateway](https://github.com/GioNob/ouf-api-gateway) | `dbdc24b5481dc9473b21b360ab1142c9aef0194b` | Il merge #50 è su `codex/r3-summary-governed`, non su main |
| MCP | [ouf-mcp-server](https://github.com/GioNob/ouf-mcp-server) | `5615fdcad8cbcad9ff41ec3d0ad2ccbf9423c042` | Il merge #40 è su `codex/retry-budget-release-candidate`, non su main |

I tre merge di integrazione non sono un rilascio coordinato. Il lock
[`source-lock.example.json`](../../scripts/installation/source-lock.example.json)
fotografa solo questi **main**: serve a mostrare il blocco, non è un insieme di
versioni approvato per il deploy. Prima di installare occorrono un unico
release manifest con commit per tutti e sei, compatibilità verificata e
provenienza degli artefatti.

## Percorso installatore nuovo: dove si ferma

| Passaggio | Evidenza nei repository | Esito / informazione ancora necessaria |
|---|---|---|
| Clonare sei commit compatibili | Sei repository e lock di esempio; nessun release manifest coordinato | **BLOCCATO**: main non include tutte le tranche; non dedurre il release da branch di lavoro |
| Provisionare rete, DNS, TLS, etcd, PostgreSQL, object store, backup | Manuale §§3–5, 7–8, 12–13; topologia lab descritta | **BLOCCATO**: definizioni complete di provisioning e segreti/owner, restore e CA non versionati |
| Avviare realm e client IAM | Guida Keycloak in MCP; manuale §20; `keycloak_scopes.py` per subset idempotente | **PARZIALE**: manca bootstrap riproducibile di realm, utenti HUMAN, workload, secret, profile, audience, redirect, ruoli e verifica token |
| Migrare e avviare sei servizi | Dockerfile Java in quattro repo; `ouf-mcp migrate`; Helm Ingestion/UDP | **BLOCCATO**: no orchestratore con DB/ruolo migration, image digest, ConfigMap/Secret, readiness, restart e rollback per tutti e sei |
| Creare InstallationConfiguration e prima policy | Onboarding API e manuale §§19–21 | **PARZIALE**: sequenza due fasi candidata → validation PASS → ACTIVE va eseguita con identità reali; no script completo, no policy iniziale portabile |
| Compilare e attivare rotte APISIX | Gateway compiler/materializer e script `ops/apisix/deploy_*.{sh,py}` con snapshot per alcune route | **PARZIALE**: nessuna pubblicazione transazionale e verificata dell'intero catalogo; chiave Admin, OIDC env, APISIX config/etcd e rollback reboot-safe sono environment bindings |
| Avviare MCP / worker | README MCP e runbook; Gateway e policy necessari prima dello start | **BLOCCATO** se bundle, proof/key, secret workload o DB migration mancano; un tool elencato non è prova di dispatch |
| Verificare negativo/positivo, restart e restore | CI di modulo e test mirati; manuale §10 | **BLOCCATO**: manca acceptance su installazione nuova e prova di rebuild senza aiuto del precedente operatore |

## Conoscenza nascosta o non recuperabile da Git

- La definizione esatta degli avvii Docker/Compose/Systemd **attuali** sul
  server, incluse reti, mount, alias DNS interni e utenti dei file: i runbook
  indicano in alcuni casi di ricreare il container *preservando* inspect
  originale. Quell'inspect sanitizzato e una definizione dichiarativa non sono
  nel release package. Non si può ricostruire fedelmente da comandi raccontati.
- Password e chiavi (correttamente fuori Git), loro riferimenti/owner UID/GID,
  rotazione e procedura di creazione iniziale completa. Il valore non va
  trascritto; vanno trascritti *come si genera e si monta* e i controlli.
- I binding Keycloak effettivi per ogni client, scope e mapper; il manuale
  contiene un incidente preciso: query `client-scopes?name=` non affidabile nel
  lab, quindi occorre ID da create o confronto esatto di tutta la lista.
- L'ordine concreto di migrazione, deploy e verifica per tutte le immagini,
  l'identità del primo HUMAN e le decisioni di approvazione della policy.
  Sono azioni governate che uno script non può inventare.
- La prova di come vengono materializzate **tutte** le route APISIX ed etcd
  partendo dalla projection ACTIVE, non solo le route coperte da script
  specifici. I backup in `/run` non bastano come rollback dopo un reboot.

Una sessione SSH passata **non è una specifica di installazione**. Non affermo
che ogni passaggio sia stato solo orale: le guide conservano molti comandi e
incidenti. L'elenco sopra indica ciò che non è verificabile con un checkout
pulito, senza accesso alla macchina o a un export dichiarativo sanitizzato.

## Primo incremento committato e gate di uscita

`scripts/installation/source_preflight.py` blocca commit imprevisti,
repository mancanti/origin diversi e working tree sporchi. È read-only.
`keycloak_scopes.py` riconcilia soltanto scope OIDC **di client già
esistenti**: default `--mode plan` offline, `check` read-only, `apply`
esplicito con token da file 0600, esatta verifica degli ID restituiti da
Keycloak. Non crea utenti, secret, policy né avvia servizi. I suoi esempi
sono segnaposto, non il profilo Netcup.

Gate **R-INSTALL**: un operatore nuovo prende un release manifest dei sei
commit e un InstallationConfiguration di prova privo di secret; esegue
provisioning dichiarativo, IAM/Keycloak, DB/ruoli/migrazioni, sei servizi e
Gateway/Caddy con script idempotenti e rollback; completa bootstrap a due
fasi, test positivi/negativi, restart e restore; deposita log sanitizzati e
tempi misurati. Nessun accesso a una sessione SSH precedente, nessuna
ricostruzione da valori hardcoded del lab. Il gate rimane **OPEN**.
