# OUF — Manuale di installazione e bootstrap

Versione iniziale: 2026-09-18  
Stato: WORKING DRAFT  
Ambito: installazione multi-Ente / environment binding / bootstrap piattaforma

**Audit di installabilità:** [verdetto e blocchi verificati il 23 settembre
2026](INSTALLABILITY_AUDIT_2026-09-23.md). La checklist iniziale
[`source_preflight.py`](../../scripts/installation/source_preflight.py)
controlla i sei checkout e il lock esatto senza installare nulla. Lo
[`script Keycloak per scope`](../../scripts/installation/keycloak_scopes.py)
copre solo la creazione e il binding degli scope su client già esistenti.
R-INSTALL nella roadmap rimane OPEN fino alla prova di installazione su ambiente
pulito con bootstrap, sei moduli, rotte, acceptance e restore completi.

## 1. Regola di governo

Questo manuale è la fonte operativa versionata per installare e avviare OUF su infrastrutture reali.

Ordine di autorità:
1. Reality Baseline Package / PET vigenti;
2. Cross-Module Alignment Matrix;
3. questo manuale di installazione;
4. runbook specifici di modulo.

Se questo manuale diverge dai PET, prevalgono i PET e il manuale deve essere aggiornato.

Il manuale deve essere aggiornato nello stesso incremento che modifica:
- DNS o hostname;
- IAM / realm / client / scope;
- TLS / CA / certificati;
- endpoint pubblici o interni;
- database, storage o object store;
- reti Docker/Kubernetes;
- secret layout;
- ordine di bootstrap;
- acceptance gates;
- rollback o disaster recovery.

## 2. Principi di industrializzazione

### 2.1 Lifecycle della configurazione di installazione

Le revisioni di InstallationConfiguration sono evidence immutabile: una revisione già persistita non si modifica in place.

Ogni tentativo di configurazione produce una nuova revision:
- `VALIDATED` se supera i controlli previsti per quella fase;
- `REJECTED` se fallisce, con findings persistiti.

I tentativi rifiutati non vengono cancellati: restano come evidence di bootstrap.

Activation, supersession, rollback e revocation sono eventi di lifecycle separati e append-only.

Il puntatore ACTIVE può cambiare, ma il payload della revision non cambia mai.

Il rollback non significa “riscrivere” una vecchia configurazione: significa riattivare una revision precedente già validata, registrando un evento `ROLLBACK_ACTIVATED`.



OUF non deve contenere hostname, domini, IP, realm, endpoint o coordinate infrastrutturali specifici di un Ente hardcoded nel codice.

Ogni installazione deve produrre una Installation Configuration versionata e validata.

La configurazione environment-specific deve:
- essere raccolta durante bootstrap;
- essere validata prima dell'attivazione;
- essere revisionabile;
- avere checksum/versione;
- supportare rollback;
- separare rigorosamente configurazione e segreti;
- essere proiettata ai moduli, senza ricostruzioni autonome da convenzioni implicite.

I segreti non devono comparire in:
- Git;
- log;
- output di comandi;
- documentazione;
- bundle di configurazione non protetti.

## 3. Bootstrap della piattaforma

Il bootstrap OUF deve diventare un Installation Bootstrap Wizard, non solo una creazione dell'amministratore.

### 3.1 Dati minimi da raccogliere

Identità installazione:
- organizationId / tenantId;
- nome Ente;
- environment: dev / test / staging / production;
- installationId;
- timezone;
- eventuale dominio base gestito dall'Ente.

IAM:
- issuer host;
- realm;
- admin HUMAN iniziale;
- policy per Device Flow / MFA;
- client workload richiesti;
- audience Gateway;
- scope bootstrap e scope permanenti;
- eventuale CA aziendale.

Gateway:
- hostname pubblico API;
- hostname pubblico IAM;
- endpoint amministrativi interni;
- policy di esposizione;
- timeout / request limits / rate limits.

Networking:
- backend network;
- edge network;
- control-plane network;
- service discovery strategy;
- policy che vieta esposizione diretta dei moduli interni.

Persistence:
- PostgreSQL host/service;
- database per modulo;
- object storage;
- filesystem persistente;
- backup target;
- retention.

Secrets:
- secret store strategy;
- file mount paths o secret references;
- ownership UID/GID;
- rotation policy.

Observability:
- metrics endpoint;
- log sink;
- alert destination;
- incident retention.

### 3.2 Output del bootstrap

Il bootstrap deve produrre:
- InstallationConfiguration revision;
- checksum;
- stato VALIDATED / ACTIVE;
- secret references separati;
- projection per Gateway/Caddy;
- projection per MCP;
- projection per Source Onboarding;
- projection per Ingestion;
- projection per Semantic Registry;
- projection per UDP;
- acceptance report;
- rollback reference.


### 3.3 Validazione dell'ambiente reale

Una configurazione sintatticamente valida non può essere attivata solo perché i campi sono presenti.

Prima dell'activation deve esistere evidence environment `PASS` prodotta dal contesto di rete del deployment.

Il validation engine deve verificare almeno:
- risoluzione DNS dell'issuer IAM;
- risoluzione DNS dell'API Gateway;
- HTTPS/TLS dell'issuer;
- OIDC discovery;
- corrispondenza esatta tra issuer configurato e campo `issuer` restituito dalla discovery;
- corrispondenza esatta tra token endpoint configurato e `token_endpoint` pubblicato dalla discovery;
- HTTPS/TLS del Gateway pubblico;
- reachability TCP di PostgreSQL;
- reachability dello storage quando applicabile.

Ogni esecuzione del validator è append-only e produce risultati strutturati.

La regola è **latest-result-wins**:
- nessuna environment validation -> activation vietata;
- ultimo risultato `FAIL` -> activation vietata anche se un controllo precedente era PASS;
- ultimo risultato `PASS` -> l'activation può proseguire agli altri gate.

Un HTTP `404` sulla root dell'API può essere un PASS di reachability/TLS quando la root non è una route applicativa: il validator deve distinguere reachability da semantica della singola capability.

### 3.4 Projection runtime

I moduli non devono ricostruire autonomamente gli endpoint a partire da nomi convenzionali.

Una revision VALIDATED deve poter produrre projection deterministiche.

**Caddy projection**
- backend network;
- edge network;
- issuer host;
- API host;
- OIDC discovery URL.

**Gateway projection**
- issuer URL;
- audience richiesta;
- API base URL;
- internal service reference.

**MCP projection**
- endpoint token OIDC;
- client id workload MCP;
- generic governed Gateway execution endpoint;
- endpoint PolicyBundle;
- endpoint recovery;
- reference al client secret;
- reference alla fingerprint key.

Le projection non devono contenere password, client secret, bearer token o key material.

## 4. Piano DNS

Il numero di record DNS deve derivare dalle superfici pubbliche effettivamente abilitate, non da domini hardcoded.

### 4.1 Record minimi obbligatori

Per l'installazione OUF attuale il minimo architetturale è di **2 record A/AAAA pubblici**:

| Funzione | Host logico | Tipo | Destinazione | Obbligatorio | Note |
|---|---|---|---|---|---|
| IAM / OIDC issuer | `<issuer-host>` | A/AAAA | IP/VIP edge OUF | sì | Deve coincidere esattamente con il claim OIDC `iss`; TLS obbligatorio |
| API Gateway / MCP northbound | `<api-host>` | A/AAAA | IP/VIP edge OUF | sì | Termina TLS su reverse proxy / ingress e inoltra verso Gateway |

Esempio di laboratorio, non normativo:
- `auth.ouf-lab.it`
- `api.ouf-lab.it`

Questi nomi non devono comparire come default nel software.

### 4.2 Record opzionali

Possono essere richiesti in base al deployment:
- `<staging-host>` per ambiente staging separato;
- hostname UI/THS;
- hostname observability;
- hostname object storage pubblico;
- hostname DR;
- record CNAME verso load balancer gestiti.

Ogni record opzionale deve avere:
- owner;
- finalità;
- esposizione;
- TLS policy;
- lifecycle;
- acceptance test.

### 4.3 Regole DNS

- Nessun modulo interno deve dipendere da hairpin NAT verso l'IP pubblico quando esiste un percorso interno governato.
- Se un workload deve usare lo stesso hostname pubblico per preservare TLS/SNI/issuer semantics, la rete interna deve risolvere quel nome verso il reverse proxy interno mediante DNS/service alias dichiarativo.
- Vietati workaround permanenti `--add-host` per singolo consumer.
- Ogni hostname deve essere verificato sia da rete esterna sia dalla rete backend.
- DNS TTL deve essere esplicito e documentato.
- DNSSEC è raccomandato quando supportato dall'Ente, ma non sostituisce TLS.

### 4.4 Acceptance DNS

Per ogni hostname pubblico:
- risoluzione autoritativa corretta;
- risoluzione da resolver pubblico;
- risoluzione da host;
- risoluzione da backend workload;
- TLS certificate valido;
- SNI corretto;
- reverse proxy verso il target previsto;
- nessuna esposizione diretta del modulo interno.

## 5. TLS e reverse proxy

Caddy/Ingress è il boundary TLS pubblico.

Regole:
- i moduli interni non devono pubblicare porte host salvo esplicita necessità governata;
- IAM e API Gateway devono essere raggiunti tramite hostname configurati dall'installazione;
- i certificati devono essere validi per gli hostname effettivi;
- il percorso interno deve preservare hostname e SNI dove richiesto;
- rollback del reverse proxy deve essere disponibile prima dello switch.

## 6. IAM

L'issuer OIDC è configurazione dell'installazione.

Il bootstrap deve:
- creare o validare il realm;
- creare l'admin HUMAN;
- creare i client workload;
- configurare audience;
- configurare tenant claim;
- configurare actor type;
- assegnare scope iniziali;
- pubblicare la prima PolicyBundle;
- chiudere il bootstrap latch;
- rimuovere scope bootstrap temporanei.

I token workload devono essere rinnovabili automaticamente; non si persistono access token short-lived in file env.

## 7. Secret management

I segreti devono essere conservati fuori dal repository.

Ogni secret deve avere:
- path/reference;
- owner UID/GID;
- mode;
- consumer;
- rotation policy;
- acceptance test di leggibilità dal solo consumer previsto.

Esempi di categorie:
- DB password;
- Keycloak client secret;
- fingerprint/HMAC key;
- object storage secret;
- APISIX admin key.

## 8. Database e migration

Prima di avviare un modulo:
- database presente;
- ruolo corretto;
- migration applicate;
- ownership e grant verificati;
- backup/restore policy definita.

Le application process non devono inventare schema o bypassare il ruolo di migration quando il PET prevede un migration role separato.

## 9. Ordine di bootstrap / avvio

Ordine iniziale di riferimento:
1. rete / storage persistente;
2. PostgreSQL;
3. Keycloak / IAM;
4. reverse proxy / TLS;
5. Source Onboarding / Authorization registry;
6. prima PolicyBundle;
7. Gateway control plane;
8. MCP Server;
9. Semantic Registry;
10. Ingestion Runtime;
11. UDP / Object Resolution;
12. UI / THS;
13. observability;
14. acceptance end-to-end.

L'ordine può essere raffinato, ma ogni deviazione deve essere documentata.

## 10. Acceptance minima installazione

Prima dell'attivazione devono inoltre essere verificati:
- revision persistita con checksum SHA-256;
- validation state `VALIDATED`;
- assenza di secret values nel payload;
- lifecycle event di activation registrato;
- possibilità di rollback a una revision precedente validata;
- impossibilità di attivare revision `REJECTED` o `REVOKED`.



Un'installazione non è ACTIVE finché non sono verdi almeno:
- DNS;
- TLS;
- issuer discovery;
- admin HUMAN login;
- workload token issuance;
- PolicyBundle fetch;
- Gateway reachability;
- MCP bootstrap;
- module health/readiness;
- database persistence;
- restart acceptance;
- rollback acceptance;
- test negativo senza token;
- test negativo con audience/scope errati;
- audit/correlation smoke.

## 11. Rollback

Ogni switch deve preservare:
- configurazione precedente;
- container/image precedente o deployment revision;
- DB migration compatibility;
- secret references precedenti quando consentito;
- procedura di restore documentata.

## 12. Stato corrente del laboratorio OUF

Questa sezione documenta il lab corrente senza trasformarlo in default di prodotto.

- VPS: Netcup
- edge IP lab: `62.83.33.202`
- IAM hostname lab: `auth.ouf-lab.it`
- API hostname lab: `api.ouf-lab.it`
- backend network: `ouf-backend`
- edge network: `ouf-edge`
- Gateway control network: `ouf-gateway-control`
- Caddy: TLS / reverse proxy boundary
- APISIX: Gateway runtime interno
- Keycloak realm lab: `ouf`

Questi valori sono evidence dell'installazione corrente e non devono diventare costanti applicative.

## 13. TBD — MUST BE RESOLVED

Prima di dichiarare il bootstrap industrializzato completo devono essere definiti:
- browser bootstrap wizard;
- secret reference model;
- CA enterprise handling;
- HA/LB topology;
- backup/restore contract;
- observability bootstrap;
- unattended/headless bootstrap mode;
- export/import install profile;
- upgrade workflow tra versioni OUF.

## 14. Change control

Ogni PR che cambia installazione o deployment deve verificare se questo manuale necessita aggiornamento.

Checklist obbligatoria:
- cambia DNS? aggiornare §4;
- cambia endpoint? aggiornare §3/§5;
- cambia IAM? aggiornare §6;
- cambia secret? aggiornare §7;
- cambia DB/migration? aggiornare §8;
- cambia ordine di avvio? aggiornare §9;
- cambia acceptance? aggiornare §10;
- cambia rollback? aggiornare §11.


## 15. Esempio laboratorio — lifecycle InstallationConfiguration

Nel laboratorio Netcup la futura revisione di installazione deve rappresentare, come esempio concreto e non come default di prodotto:
- installationId: `ouf-lab-netcup-01`;
- issuer: `https://auth.ouf-lab.it/realms/ouf`;
- API base: `https://api.ouf-lab.it`;
- backend network: `ouf-backend`;
- edge network: `ouf-edge`;
- Gateway control network: `ouf-gateway-control`;
- PostgreSQL service: `ouf-postgres:5432`;
- secret references sotto `/opt/ouf/secrets/`.

Durante il bootstrap reale:
1. una configurazione invalida deve essere persistita come `REJECTED` con findings;
2. una configurazione valida deve diventare una nuova revision `VALIDATED`;
3. l'attivazione deve produrre un lifecycle event;
4. un eventuale rollback deve riattivare una revision precedente senza modificarne il payload;
5. una revision revocata non deve essere riattivabile.


## 16. Esempio laboratorio — environment validation e projection

Per il laboratorio Netcup, una revision candidata deve produrre almeno:

**Caddy**
- issuer host: `auth.ouf-lab.it`;
- API host: `api.ouf-lab.it`;
- backend network: `ouf-backend`;
- edge network: `ouf-edge`.

**Gateway**
- issuer: `https://auth.ouf-lab.it/realms/ouf`;
- audience: `ouf-api-gateway`;
- API base: `https://api.ouf-lab.it`.

**MCP**
- token endpoint: `https://auth.ouf-lab.it/realms/ouf/protocol/openid-connect/token`;
- workload client: `ouf-mcp-server`;
- Gateway execution base: `https://api.ouf-lab.it/internal/capabilities/v1/execute`;
- PolicyBundle: `https://api.ouf-lab.it/internal/capabilities/v1/authorization/policy-bundle/active`;
- recovery: `https://api.ouf-lab.it/internal/capabilities/v1/recovery`;
- client-secret e fingerprint-key come reference a file protetti sotto `/opt/ouf/secrets/`.

Situazione osservata durante R3a:
- il record pubblico `api.ouf-lab.it -> 62.83.33.202` è stato pubblicato;
- HTTPS pubblico verso Caddy/APISIX ha restituito `404`, confermando TLS e proxy;
- da `ouf-backend`, il tentativo di hairpin verso l'IP pubblico non era raggiungibile;
- pertanto il lab richiede la projection Caddy con alias DNS interno dichiarativo per `api.ouf-lab.it`, analogo al già accettato issuer alias.

Questa evidence è specifica del laboratorio e non crea alcun default di prodotto.


## 17. Gateway e Caddy — applicazione della InstallationProjection

Il catalogo Gateway deve rimanere indipendente dai valori specifici dell'Ente.

Nel catalogo di prodotto, le coordinate installation-specific vengono rappresentate da reference logiche, ad esempio:

- `installation://iam.gatewayAudience`;
- `installation://iam.workloadClients.mcpServer`.

Prima della pubblicazione runtime, il compiled Gateway catalog deve essere risolto contro la InstallationProjection ACTIVE.

### 17.1 Endpoint interni MCP

Il Gateway espone tre superfici necessarie al runtime MCP.

**Generic execution**

`POST /internal/capabilities/v1/execute`

È un endpoint di mediazione Gateway, non una business capability. Il body contiene il `CapabilityID` e il Gateway seleziona esclusivamente un binding già pubblicato nel catalogo.

**Recovery**

`POST /internal/capabilities/v1/recovery`

È anch'esso mediazione Gateway e usa solo owner/service/path di recovery già pubblicati dal catalogo. Non accetta destinazioni dal client.

**Authorization PolicyBundle**

`GET /internal/capabilities/v1/authorization/policy-bundle/active`

Questa superficie corrisponde invece alla capability reale `authorization.bundle.read` e viene inoltrata dal Gateway al Source Onboarding/Authorization registry.

### 17.2 Caddy

Il deploy Caddy deve ricevere una InstallationProjection, non hostname/network impostati come default nel prodotto.

Forma canonica:

```sh
sudo env OUF_INSTALLATION_PROJECTION=/opt/ouf/installation/active-projection.json \
  sh ops/caddy/deploy.sh
```

Dalla projection vengono letti:
- backend network;
- edge network;
- issuer hostname;
- API hostname;
- OIDC discovery URL.

Il deploy deve assegnare issuer e API hostname come alias dichiarativi sul backend network quando la strategia dell'installazione è `REVERSE_PROXY_ALIAS`.

Il Caddyfile è un artefatto dell'installazione e deve contenere entrambi gli hostname proiettati. Il deploy fallisce se projection e Caddyfile non coincidono.

### 17.3 Esempio laboratorio Netcup

Per il laboratorio corrente, la projection deve risolvere:

- backend network: `ouf-backend`;
- edge network: `ouf-edge`;
- issuer host: `auth.ouf-lab.it`;
- API host: `api.ouf-lab.it`;
- audience Gateway: `ouf-api-gateway`;
- workload MCP: `ouf-mcp-server`.

Il risultato runtime atteso per MCP è:

- `MCP_GATEWAY_ENDPOINT=https://api.ouf-lab.it/internal/capabilities/v1/execute`;
- `MCP_AUTHORIZATION_BUNDLE_ENDPOINT=https://api.ouf-lab.it/internal/capabilities/v1/authorization/policy-bundle/active`;
- `MCP_GATEWAY_RECOVERY_ENDPOINT=https://api.ouf-lab.it/internal/capabilities/v1/recovery`.

Client secret e fingerprint key restano secret references e non entrano nel catalogo Gateway.

### 17.4 Acceptance prima del deploy MCP

Prima di avviare MCP devono risultare verdi:
1. projection ACTIVE esportata;
2. compiled Gateway catalog risolto contro la projection;
3. Caddy redeploy dalla stessa projection;
4. risoluzione interna issuer/API verso Caddy;
5. OIDC discovery interna 200;
6. PolicyBundle path protetto e raggiungibile tramite Gateway;
7. generic execution e recovery materializzati nel Gateway;
8. nessuna porta host diretta del MCP Server.


## 18. Export governato della InstallationProjection ACTIVE

La InstallationProjection consumata da Gateway/Caddy/MCP non deve essere ricostruita manualmente sul server.

Il Source Onboarding espone una Trusted Human operation:

`GET /api/trusted-human/v1/installations/{installationId}/projection`

Requisiti:
- actor HUMAN;
- capability `installation.configuration.export`;
- descriptor canonico registrato nel capability registry con owner `installation`, operation `READ`, actor `HUMAN`;
- grant/policy ACTIVE che assegna la capability all'installer HUMAN;
- header `X-Correlation-ID`;
- opzionale query `revision` usata come precondizione sulla revision ACTIVE.

Regole:
- viene esportata solo la revision ACTIVE;
- se non esiste una ACTIVE revision -> 404;
- se la revision richiesta non coincide con ACTIVE -> 409;
- SERVICE/AI_AGENT non possono usare questa surface;
- la risposta usa `Cache-Control: no-store`;
- response header `X-OUF-Installation-Revision` e `X-OUF-Installation-Checksum` devono coincidere con il payload esportato;
- l'export produce audit append-only con subject HUMAN, correlation id, revision e checksum.

L'export può contenere secret references, ad esempio:
- `MCP_OIDC_CLIENT_SECRET_FILE`;
- `MCP_FINGERPRINT_KEY_FILE`.

Non può contenere secret values, password, bearer/access token o private key material.

### 18.1 Materializzazione sul server

Dopo un export riuscito, il file operativo deve essere scritto atomicamente, non con modifica manuale in place.

Percorso canonico:

`/opt/ouf/installation/active-projection.json`

Sequenza operativa:
1. esportare la projection in un file temporaneo;
2. verificare revision e checksum restituiti dall'endpoint;
3. verificare che il JSON sia parsabile;
4. sostituire atomicamente `active-projection.json`;
5. usare lo stesso file per risolvere Gateway, Caddy e MCP;
6. conservare la projection precedente per rollback quando compatibile.

### 18.2 Esempio laboratorio Netcup

Per il laboratorio corrente:
- installationId atteso: `ouf-lab-netcup-01`;
- capability HUMAN richiesta: `installation.configuration.export`;
- prima dell'export il descriptor canonico deve essere registrato con owner `installation` e poi incluso in una nuova PolicyBundle ACTIVE;
- destinazione operativa: `/opt/ouf/installation/active-projection.json`.

Il file non deve essere costruito a mano usando i valori di questa sezione: deve provenire dall'endpoint governato della revision ACTIVE.


## 19. Trusted Human Installation Bootstrap API

La lifecycle della InstallationConfiguration è governata dalla Trusted Human Surface.

Capability canoniche con owner `installation`:
- `installation.configuration.read` — READ — HUMAN;
- `installation.configuration.write` — EXECUTE — HUMAN;
- `installation.configuration.activate` — EXECUTE — HUMAN;
- `installation.configuration.export` — READ — HUMAN.

Endpoint:
- `GET /api/trusted-human/v1/installations/{installationId}/active`;
- `GET /api/trusted-human/v1/installations/{installationId}/revisions/{revision}`;
- `POST /api/trusted-human/v1/installations/{installationId}/revisions`;
- `POST /api/trusted-human/v1/installations/{installationId}/revisions/{revision}:validate-environment`;
- `POST /api/trusted-human/v1/installations/{installationId}/revisions/{revision}:activate`;
- `POST /api/trusted-human/v1/installations/{installationId}/revisions/{revision}:rollback`;
- `POST /api/trusted-human/v1/installations/{installationId}/revisions/{revision}:revoke`.

Le operazioni mutanti richiedono HUMAN, capability dedicata, trusted-write proof e `X-Correlation-ID`.

L'activation richiede revision VALIDATED, non REVOKED e ultima environment validation PASS. Il rollback può puntare solo a una revision più vecchia dell'ACTIVE e produce `ROLLBACK_ACTIVATED`.

Da V24 la correlation viene persistita anche per ogni tentativo di creazione revision e per ogni environment validation.

### 19.1 Sequenza laboratorio Netcup

1. registrare le capability read/write/activate con owner `installation`;
2. pubblicare una nuova PolicyBundle con grant a `ouf-admin`;
3. creare la revision `ouf-lab-netcup-01`;
4. eseguire environment validation;
5. attivare con PASS;
6. esportare la projection ACTIVE;
7. materializzare atomicamente `/opt/ouf/installation/active-projection.json`;
8. proseguire con Gateway/Caddy/MCP dalla stessa projection.


## 20. Bootstrap IAM — procedura normativa per i client scope

Questa sezione è obbligatoria per il bootstrap IAM su Keycloak.

### 20.1 Regola di creazione e binding

Ogni client scope OUF deve essere creato esplicitamente e il binding al client deve usare l'ID restituito dalla stessa operazione di create.

Forma operativa:

`kcadm.sh create client-scopes -r <realm> -s name=<scope> -s protocol=openid-connect -i`

L'output `-i` è il client-scope ID canonico da usare immediatamente nel binding:

`kcadm.sh update clients/<client-id>/default-client-scopes/<scope-id> -r <realm> -n`

Regole:
- non riutilizzare un scope ID tra scope differenti;
- non dedurre il client-scope ID tramite query non validate;
- nel laboratorio Keycloak 26.7.4, la forma `get client-scopes -q name=<scope>` non è accettata come procedura normativa perché ha prodotto risultati non filtrati e può quindi restituire un ID non corrispondente al nome richiesto;
- il runbook deve usare l'ID restituito direttamente da `create ... -i` oppure, per scope già esistenti, una lettura completa seguita da matching esatto lato client sul campo `name`;
- ogni scope deve avere un ID distinto salvo esplicita evidenza contraria del provider.

### 20.2 Acceptance del binding

Dopo aver creato/bindato nuovi scope:
1. emettere un nuovo token;
2. verificare una sola volta il claim `scope`;
3. il claim deve contenere tutti gli scope appena configurati prima di usare endpoint THS che li richiedono.

Il controllo del token è acceptance del binding IAM, non un controllo ripetitivo da eseguire a ogni chiamata applicativa.

### 20.3 Esempio laboratorio Netcup

Per `ouf-human-admin` devono risultare emessi almeno:
- `authorization.policy.admin`;
- `installation.configuration.read`;
- `installation.configuration.write`;
- `installation.configuration.activate`;
- `installation.configuration.export`.

Il bootstrap non deve procedere alla Trusted Human Installation API se il token non contiene gli scope richiesti.

### 20.4 Primo script idempotente: soli client scope

Su una macchina amministrativa Linux con Python 3.12+, preparare una copia
privata di `scripts/installation/keycloak-scopes.example.json` usando
l'issuer effettivo e i nomi esatti dei client **già creati**. Il file di
esempio non è il profilo di produzione.

```bash
python3 scripts/installation/keycloak_scopes.py --desired /path/desired-scopes.json --mode plan
python3 scripts/installation/keycloak_scopes.py --desired /path/desired-scopes.json --mode check --token-file /path/admin-token-0600
python3 scripts/installation/keycloak_scopes.py --desired /path/desired-scopes.json --mode apply --token-file /path/admin-token-0600
```

`plan` è offline e non legge token; `check` fallisce in caso di drift, senza
scritture; `apply` crea soltanto scope mancanti e binding Default mancanti,
senza cancellare o alterare scope esistenti. La creazione usa l'ID dalla
risposta Keycloak, il riuso usa matching esatto dell'intera lista, seguito da
readback. Eseguire `apply` soltanto dopo aver verificato realm, client,
profilo e autorizzazione dell'operatore. Script e test non configurano
realm/client/secret/utente/mapper/ruoli, non pubblicano policy e non attestano
l'emissione dei nuovi scope nel JWT: quest'ultima resta l'acceptance §20.2.

## 21. Bootstrap a due fasi della InstallationProjection

La prima activation non può dipendere da una projection ACTIVE già materializzata, perché l'environment validation deve risultare PASS prima dell'activation.

Quando il networking interno richiede alias derivati dalla InstallationConfiguration, il bootstrap deve usare due fasi distinte.

### 21.1 Candidate projection

Una revision `VALIDATED` deve poter produrre una projection candidata deterministica e bound a:
- installationId;
- revision;
- checksum.

La candidate projection:
- è usata solo per predisporre l'ambiente necessario alla validation;
- non equivale a una revision ACTIVE;
- non può essere consumata come stato runtime canonico da moduli applicativi;
- deve essere auditata e correlata;
- deve derivare esclusivamente dalla revision immutabile richiesta.

### 21.2 Sequenza obbligatoria

Per il primo bootstrap o quando la validation dipende da coordinate di rete proiettate:
1. creare revision `VALIDATED`;
2. esportare la candidate projection della stessa revision;
3. applicare solo i prerequisiti di bootstrap/validation, ad esempio alias DNS interni su Caddy/reverse proxy;
4. eseguire environment validation;
5. se l'ultima validation è PASS, attivare la revision;
6. esportare la projection ACTIVE;
7. verificare che ACTIVE revision/checksum coincidano con quelli della candidate projection;
8. materializzare la projection ACTIVE canonica e proseguire con i moduli runtime.

### 21.3 Divieti

Non sono ammessi:
- `--add-host` permanenti per singolo consumer;
- modifica SQL dell'InstallationConfiguration;
- creazione manuale di una projection non derivata dal servizio;
- considerare una candidate projection come ACTIVE;
- bypassare la regola latest-result-wins della environment validation.

### 21.4 Evidence laboratorio Netcup

La validation della revision 1 di `ouf-lab-netcup-01` ha prodotto:
- IAM DNS PASS;
- OIDC discovery PASS;
- issuer match PASS;
- token endpoint match PASS;
- PostgreSQL PASS;
- object storage PASS;
- Gateway DNS FAIL per `api.ouf-lab.it` dalla rete backend;
- Gateway HTTPS FAIL conseguente.

Questa evidence conferma che, nel laboratorio corrente, la candidate projection deve predisporre anche l'alias interno di `api.ouf-lab.it` verso Caddy prima di rieseguire la validation.
