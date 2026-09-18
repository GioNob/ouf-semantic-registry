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
- API/THS bootstrap;
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
