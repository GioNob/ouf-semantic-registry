# OUF — Manuale di installazione e bootstrap

Versione iniziale: 2026-09-18  
Stato: WORKING DRAFT  
Ambito: installazione multi-Ente / environment binding / bootstrap piattaforma

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

## 22. Provisioning standardizzato dei workload IAM

I client workload OUF devono essere creati e verificati con una procedura idempotente, non con modifiche manuali della console IAM.

Il repository fornisce `scripts/provision-keycloak-workload.py` con tre modalità:
- `plan`: confronto read-only fra stato desiderato e stato Keycloak;
- `apply`: creazione/aggiornamento del client, binding dello scope richiesto, mapper canonici e materializzazione atomica della credenziale nel percorso runtime fornito dall'installazione;
- `verify`: acceptance read-only e fail-closed su qualsiasi drift.

Il contratto minimo di un workload SERVICE che legge la PolicyBundle ACTIVE è:
- OIDC confidential client;
- service account abilitato;
- Standard Flow disabilitato;
- Direct Access Grants disabilitati;
- default scope `authorization.bundle.read`;
- audience access-token uguale alla Gateway audience della InstallationConfiguration;
- claim `ouf_actor_type=SERVICE`;
- claim `tenant_id` uguale al tenant della InstallationConfiguration.

La procedura non stampa client secret o access token. La credenziale runtime resta fuori da Git e viene scritta atomicamente con ownership/mode verificati.

Per R4a, UDP deve avere una propria workload identity distinta da MCP e Ingestion. Il runtime UDP usa poi un token short-lived rinnovato automaticamente per leggere `/internal/capabilities/v1/authorization/policy-bundle/active`. Non è ammesso riusare il client MCP come identità UDP.

Acceptance obbligatoria:
1. `plan` mostra solo il drift atteso prima del primo provisioning;
2. `apply` termina con `VERIFY=PASS`;
3. un successivo `verify` termina con `VERIFY=PASS` senza modifiche;
4. il token SERVICE contiene audience, tenant, actor type e scope richiesti;
5. il Gateway accetta il workload sulla route PolicyBundle;
6. il consumer carica la PolicyBundle ACTIVE e continua a rinfrescarla entro il limite di staleness.



## 23. R4a — ripresa automatizzata e stato del lab (27 settembre 2026)

**Aggiornamento operativo 29 settembre:** usare il nuovo
[handoff dopo il preflight](../handoffs/OUF_HANDOFF_2026-09-29_R4A_PREFLIGHT_TO_INGESTION.md)
prima di eseguire i passi storici sotto. La policy attiva è
`ouf-lab-authorization:31`, UDP live è `edaba2bff18a2aaf52d1180f21f0e68984cc3437`
con Flyway 34, Onboarding live è `f74c3a9f377b5ce93b5cab298fa24372de1602bc`
con Flyway 31. La versione cinema è `IN_REVIEW`, lock 2, hash congelato
`sha256:2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891`.
Il preflight HUMAN e la lettura SERVICE della stessa attestazione UDP
`57499699-dbc5-419d-a14b-27cd3604ec6f` sono PASS con zero oggetti.
**Ingestion compatibility ABSENT** e immagine staged diversa dal live;
non procedere ad attivazione o prima run finché non esiste un'attestazione
SERVICE di compatibilità della configurazione congelata. Il prossimo
inventario read-only `scripts/r4a_ingestion_compatibility_inventory.py`
(commit `438e3fbfc00e742cbe55a376bda6626ba5f3a807`) è preparato ma
**non eseguito**. Non ripetere submit/preflight e non cancellare backup o
container rollback elencati nel nuovo handoff.

Il grant admin per `urban.identity.preflight` nella policy :30 richiedeva
cinque etichette e quattro livelli su una risorsa `capability` che non li
espone. La proposta `REPLACE_ROLES` `86086d30-1f2d-4432-af09-fb45bf8189bd`
è stata confermata HUMAN in THS e pubblicata come :31: soltanto i due insiemi
di quel permesso sono vuoti, gli altri 28 permessi admin e le assegnazioni
restano invariati. Keycloak ha già gli scope HUMAN preflight e SERVICE lettura
attestazione; prima di introdurre `ouf.ingestion.configuration.attest`,
verificare descriptor, grant SERVICE, client scope e route con l'inventario.
Non trasformare il login IAM in approvazione automatica e non inserire
attestazioni direttamente in DB. La compatibilità va valutata dal runtime
Ingestion sul contratto esatto; Onboarding richiede identità SERVICE
autorizzata e hash della versione congelata.

**Snapshot storico al 27 settembre:** [handoff PET 1.7](../handoffs/OUF_HANDOFF_2026-09-27_R4A.md) e [audit con evidenze e difformità](../audits/OUF_R4A_FINAL_AUDIT_2026-09-27.md). I rollout picker Onboarding/MCP/Gateway, la riparazione owner-key e l'upload HUMAN tramite Gateway avevano prodotto l'asset `8ec8ae90-808a-4d9e-907c-d56de119e376`; Semantic aveva pubblicato la revisione `51706bed-81e4-4306-aca1-70119821727d`. La versione Onboarding allora era DRAFT e l'ultimo PolicyBundle attestato era `ouf-lab-authorization:28`. Oggi valgono lo stato `IN_REVIEW` e la policy :31 sopra; il ciclo Ingestion → UDP → search non è ancora provato.

### Procedura di modifica

Per fotografare i soli container, eseguire lo script read-only [r4a_handoff_snapshot.py](../../scripts/r4a_handoff_snapshot.py) dal commit fissato. Esempio: dalla directory del repository sul VPS, `git show <COMMIT_VERIFICATO>:scripts/r4a_handoff_snapshot.py | sudo python3 -`. Lo script non interroga policy, route, DB o stato della filiera e non sostituisce le acceptance.

Per preparare le immagini del motore d'identità senza modificare i container,
usare [r4a_stage_identity_images.py](../../scripts/r4a_stage_identity_images.py)
dal commit Semantic fissato. `--plan` verifica gli HEAD remoti e le immagini
attive; `--stage` crea worktree separati in `/opt/ouf/r4a-stage`, costruisce
UDP, Onboarding e Ingestion dai commit con CI verde e registra gli ID delle
vecchie e nuove immagini in `identity-images.json` (0600). Non cambia branch,
container, DB, route, policy o segreti. Un HEAD divergente blocca lo staging.
Questo manifest è un input per il rollout con backup e rollback; non attesta
il deployment. Prima di attivare la fonte servono le route Gateway, il grant
HUMAN `urban.identity.preflight`, il grant SERVICE
`ouf.udp.identity.attestation.read`, il token workload rinnovabile per
Onboarding, il preflight della configurazione congelata e la prova live del
percorso fino a UDP. Il matching attuale è limitato alla classe canonica.
Decisione HUMAN del 28 settembre: cinema e teatro restano oggetti canonici
distinti; un eventuale luogo fisico condiviso si rappresenta con un legame
governato, senza fare merge fra le due classi. L'indirizzo o un nome simile
propongono una relazione da verificare, non autorizzano da soli il link.

**Stato lab 29 settembre:** UDP è live con Flyway 34 e il dump e container
precedenti sono conservati. Onboarding live è a Flyway 31, con immagine staged
`f74c3a9f…`, cinque mount read-only e UID/GID 10003; lo smoke SERVICE della
route UDP ha dato 401 senza bearer e 400 con bearer e parametro mancante.
Per Onboarding, usare prima l'inventario read-only
[r4a_onboarding_rollout_inventory.py](../../scripts/r4a_onboarding_rollout_inventory.py).
Il rinnovo del bearer SERVICE è implementato in
[r4a_onboarding_token_runtime.py](../../scripts/r4a_onboarding_token_runtime.py):
`install` verifica il secret root-only già esistente, installa servizio e
timer systemd e scrive il token solo in
`/run/ouf-onboarding-identity/token` (root:10003, 0640). La directory è
root:10003 (0750) e viene ricreata da tmpfiles al boot. Il container UID/GID
10003 deve montare **l'intera directory** in sola lettura e usare
`OUF_ONB_UDP_IDENTITY_GATEWAY_URL=https://api.ouf-lab.it` e
`OUF_ONB_UDP_IDENTITY_TOKEN_FILE=/run/ouf-onboarding-identity/token`.
Il timer rinnova ogni minuto; controllare il TTL prima di avviare il nuovo
container e verificare la rotazione dopo il deploy. Nessun valore di bearer
o client secret va inserito in env Docker, unità systemd o log. La lettura
positiva dell'attestazione richiede un preflight HUMAN valido sulla
configurazione congelata, come documentato in
[R4A_IDENTITY_LAB_ACTIVATION.md](../R4A_IDENTITY_LAB_ACTIVATION.md).

#### Policy Authorization R4a: preparazione senza pubblicazione

La policy ACTIVE `ouf-lab-authorization:28` non dichiara ancora
`urban.identity.preflight`, `ouf.udp.identity.attestation.read`,
`resolution.issue.read` e `resolution.match.approve`. Il percorso MCP di
`authorization.permissions.propose` cambia un grant per volta e non registra
descriptor: per questa prima introduzione usare l'API amministrativa
`/api/trusted-human/v1/authorization`, con identità HUMAN autenticata e
trusted write proof. Il backend rimane privato; non pubblicare queste API in
MCP né creare grant con SQL. L'installazione Gateway attuale non espone route
amministrative dedicate: verificare un canale autenticato appropriato prima
di tentare POST, senza aprire la porta backend a Internet.

Lo script [r4a_prepare_identity_policy.py](../../scripts/r4a_prepare_identity_policy.py)
accetta due esportazioni **locali al server**: il JSON `bundle_payload`
dell'ACTIVE, e un array JSON di `capability_id, descriptor` delle quattro
registrazioni (può essere `[]`). Le istruzioni seguenti sono **SQL per psql**,
non comandi della shell. Sul VPS usare `sudo docker exec -i ouf-postgres psql
-X -qAt -v ON_ERROR_STOP=1 -U ouf_onboarding -d ouf_onboarding -c 'SQL'`
e redirigere l'output in file locali con `umask 077`; se il ruolo DB
dell'installazione è diverso, usare quello già verificato per Onboarding.

```sql
select p.bundle_payload::text
from ouf_authorization.active_policy_bundle a
join ouf_authorization.policy_bundle p using (bundle_id, version);

select coalesce(jsonb_agg(jsonb_build_object(
  'capability_id', capability_id, 'descriptor', descriptor)), '[]'::jsonb)::text
from ouf_authorization.capability_registration
where capability_id in ('urban.identity.preflight',
  'ouf.udp.identity.attestation.read', 'resolution.issue.read',
  'resolution.match.approve');
```

```sh
python3 scripts/r4a_prepare_identity_policy.py \
  --active /opt/ouf/r4a-stage/active-policy.json \
  --registrations /opt/ouf/r4a-stage/registered-identity-capabilities.json \
  --valid-until 2027-09-28T00:00:00Z \
  --output-dir /opt/ouf/r4a-stage/policy-29-review
```

La scadenza è un parametro esplicito da approvare. Il generatore blocca una
ACTIVE diversa da :28 e descriptor incompatibili. Produce
`capability-registrations.json` per i soli descriptor assenti e
`policy-draft.json` per la nuova versione. Mantiene tutti i grant esistenti,
inclusi quelli governati dal catalogo ruoli, e aggiunge il solo grant SERVICE
`ouf-source-onboarding`. Rivedere il diff e i file sul server; registrare i
descriptor mancanti con `POST /capabilities`, creare la bozza con
`POST /policies`, poi confermare la pubblicazione con
`POST /policies/{id}:publish` e l'ETag reale. La pubblicazione è una decisione
HUMAN esplicita; se ACTIVE cambia, rigenerare dal nuovo bundle e riesaminare.

Per il profilo lab, lo script
[r4a_create_identity_policy_draft.py](../../scripts/r4a_create_identity_policy_draft.py)
verifica il diff e ACTIVE in sola lettura. Con `--apply` avvia il Device Flow
del client HUMAN `ouf-human-admin`, mostra URL/codice da approvare nel browser,
mantiene il bearer soltanto in memoria e usa l'API Onboarding attraverso
l'indirizzo privato Docker. Registra i descriptor e crea la bozza; non
pubblica ACTIVE né inoltra credenziali al chatbot. Richiede un login HUMAN
effettivo e un grant corrente `authorization.policy.admin`. Se una
registrazione riesce e il passo successivo fallisce, conservarla: il registro
è immutabile e la successiva revisione deve partire dallo stato aggiornato.
Per la bozza lab `fb931b4e-46bb-4aee-8f0e-434b8aeda10b`, revisione 0,
[r4a_publish_identity_policy.py](../../scripts/r4a_publish_identity_policy.py)
rilegge il draft tramite API HUMAN, confronta l'intero payload col file
revisionato, verifica ACTIVE `:28`, mostra la scadenza del grant e richiede di
digitare l'identificativo esatto prima del `POST :publish` con `If-Match: "0"`.
Il Device Flow è ripetuto perché il token precedente è effimero. La risposta
e il puntatore ACTIVE devono entrambi attestare `:29`; un esito incerto richiede
una lettura di stato, mai una ripetizione cieca della pubblicazione.

Dopo la pubblicazione, aggiornare `ouf-admin` attraverso
`authorization.permissions.read` (`view: CAPABILITIES`), proposta
`REPLACE_ROLES` e conferma THS: includere ogni capability HUMAN del bundle,
con i vincoli massimi previsti dal modello ruoli Onboarding. La capability
SERVICE resta al workload, non al ruolo umano. Il manifest MCP in produzione
deve esporre `view: CAPABILITIES`; se la validazione dello strumento la rifiuta,
aggiornare manifest/Gateway prima della proposta. Anche dopo la policy servono
scope IAM, route Gateway, token workload Onboarding e deployment delle immagini
staged. Nessuna fonte si attiva sulla sola base del draft o della pubblicazione
della policy.


1. Identificare branch/commit e immagine/container live del solo modulo interessato; non dedurre deployment da PR, CI o body di issue. Registrare lo snapshot di route, container, config e DB richiesto dallo script di rollout versionato.
2. Usare la modalità `plan`/dry run dello script e poi `apply` idempotente con verifiche e rollback automatico. Riportare all'operatore **un** esito sintetico PASS/BLOCKED, il riferimento di rollback e il gate successivo. Evitare lunghe sequenze manuali di controlli indipendenti. Non ripetere una prova già attestata se l'immagine e la configurazione pertinenti non sono cambiate.
3. Comandi copiabili completi: `cd` esplicito, commit fissato, shell non interattiva salvo login HUMAN, `set -o pipefail` dove si usa `git show | sudo python3 -`; non interrompere un comando in modo che il pipe invii uno script parziale. Le credenziali vanno in secret file/runtime e non nei log o nella chat. Snapshot e dump restano finché il rollback è verificato.
4. Dopo un blocco, conservare il motivo e correggere il solo contratto fallito, poi rieseguire la fase idempotente. Non trattare `KCADM_SESSION_EXPIRED`, route mancanti o un PASS del probe APISIX come prove di risultato E2E.

### Binding del lab e gate ancora aperti

Il bootstrap Keycloak dei cinque scope managed-file e dei client `ouf-onboarding`, `ouf-ingestion`, `ouf-human-admin` e `ouf-chatgpt` è stato applicato/verificato nei passaggi documentati in Onboarding; la sessione `kcadm` può scadere e richiede nuova autenticazione interattiva prima di mutazioni. Gli scope HUMAN legati come OPTIONAL a un client non compaiono automaticamente nel token di un altro. Gateway controlla route e capability, Onboarding/UDP fanno enforcement fine e il THS resta owner delle decisioni HUMAN.

Il probe APISIX isolato ha mostrato early bytes/204/cleanup; per la route prodotto restano 413 senza asset parziale, media/checksum/auth negativi e rollback. L'upload live ha avuto successo ma non prova tutti quei casi. Le immagini e le route attive vanno osservate appena prima di un ulteriore rollout. Il profilo `resolution.weighted` è accettato come struttura opzionale da Onboarding ma UDP non ne esegue la semantica: la PR #34 lo rifiuta esplicitamente; non attivare una fonte che ne dipende finché il motore generale e il test di contratto versionato non sono attivi. La MinIO CI della PR usa un binario ufficiale con SHA fissato; nessun cambiamento al MinIO live del VPS.


## 24. Stato R-INSTALL e confine del laboratorio

**R-INSTALL OPEN.** La raccolta di script versionati di bootstrap e rollout ha
ridotto errori del lab, ma non è un orchestrator d'installazione su nuova
macchina. Per chiudere il gate servono manifest di installazione e secret refs,
bootstrap idempotente IAM/Authorization e route, build/deploy dei sei moduli,
clean install, upgrade N/N+1, backup/restore, rollback e CI d'installabilità.
Il contratto deve supportare Gateway e owner su reti/host distinti con upstream
versionato e trasporto verificato; il binding Docker `ouf-onboarding:8080` è
soltanto il profilo lab. L'[audit R4a](../audits/OUF_R4A_FINAL_AUDIT_2026-09-27.md)
registra i regressi che l'orchestrator deve prevenire: payload anonimo valido
per il probe delle route, dichiarazione owner-key preservata, picker URL
proiettato dall'installazione, snapshot/rollback e sessione IAM gestita
senza inviare secret alla chat. Un output PASS dell'inventario container o
del rollout picker non chiude R-INSTALL né R-SMOKE.

## Ripresa R4a — 30 settembre: inventario Ingestion e sonda candidata

L’operatore ha eseguito l’inventario rimasto sospeso: **PASS**. Flyway live/staged
è 14/14; lo staged `e3f04f1…` differisce dal live. Policy
`ouf-lab-authorization:31`: un descriptor SERVICE e un grant SERVICE per
`ouf.ingestion.configuration.attest`, zero altri grant. I conteggi non provano
che il bearer effettivo sia il principal destinatario del grant né che la route
risponda; la compatibilità della versione resta non attestata.

La [PR Ingestion #33](https://github.com/GioNob/ouf-ingestion-runtime/pull/33),
commit `da941666643d83f9f417da85be91fb3b10d4db01`, aggiunge una sonda nel jar
che usa mapper, adapter e validator dei contratti CDE/lineage/handoff di
produzione. Verifica hash/stato congelato, riferimenti Semantic esatti, integrità
dell’asset, identità sorgente e tutte le righe. Lo script versionato costruisce
una candidata isolata, senza avviare Spring/Flyway/worker o scrivere run,
materializzazioni e attestazioni. Il PASS della sonda avrà
`candidateDeployed=false` e `attestationSubmitted=false`.

La prima revisione passa i sei test Python, i 23 test consumer/regressione Java,
la suite funzionale con PostgreSQL e il restore drill. Trivy ha rilevato
CVE-2026-68497 nella dipendenza Jackson Databind 2.21.4 ereditata dal ramo: la BOM
è stata aggiornata a 2.21.6, senza abbassare il gate HIGH/CRITICAL. Sul commit aggiornato sono PASS la CI dedicata, la suite completa Ingestion
con PostgreSQL, il restore drill e il gate supply-chain (Trivy e chart).
Il risultato VPS rimane da acquisire, distinto dalle prove CI. Il prossimo
intervento dell’operatore è la preparazione/prova candidata; seguono backup
verificato, switch/rollback, prova contro l’immagine effettivamente live e POST
SERVICE governata. Poi approvazione HUMAN in THS, attivazione e filiera fino
alla ricerca UDP. **R-SMOKE e R-INSTALL restano OPEN**.

Contratto, parametri, limiti e procedura:
[R4A_FROZEN_CONFIGURATION_COMPATIBILITY.md](https://github.com/GioNob/ouf-ingestion-runtime/blob/da941666643d83f9f417da85be91fb3b10d4db01/docs/R4A_FROZEN_CONFIGURATION_COMPATIBILITY.md).

### Configurazione e IAM di questo incremento

La sonda usa i mount esistenti `/run/ouf-ingestion-auth` e
`/run/secrets/ingestion-summary.properties` in sola lettura. Le proprietà
`ouf.ingestion.activation.gateway-url`, `token-file` e `tenant-id` devono essere
esplicite e risolvibili. Il token deve poter leggere l’asset e le pubblicazioni
Semantic esatte attraverso Gateway; un 401/403 o una proprietà mancante blocca
la prova. Non viene creato un nuovo client, scope, grant o route Keycloak/APISIX.
Il descriptor/grant di attestazione già censito non implica scope presente nel
bearer: verificarlo con il percorso SERVICE prima del futuro POST. Qualsiasi
variazione IAM/policy resta governata e documentata nel runbook, con decisione
HUMAN per pubblicazione policy. Il build log resta privato nel percorso di stage;
non inviare contenuti delle proprietà o credenziali in chat.

La preparazione non richiede restore: non effettua switch o DDL. Conservare gli
snapshot e i rollback esistenti. Lo switch successivo richiede backup verificato
e rollback applicativo; niente restore DB automatico.

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
