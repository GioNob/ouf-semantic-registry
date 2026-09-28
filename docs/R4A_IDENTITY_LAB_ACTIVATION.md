# R4a: attivazione controllata dell'identità nel laboratorio

## Stato e confini

La policy `ouf-lab-authorization:30` contiene le nuove capability e il ruolo
HUMAN `admin`. Le immagini UDP, Onboarding e Ingestion sono preparate in
`/opt/ouf/r4a-stage/identity-images.json`; lo staging non sostituisce i
container live. Il branch Gateway `codex/r4a-resolution-review-routes` al
commit `d946a1f73be7db415ea38e5daf9b2cf434dae299` contiene la
materializzazione delle tre route di preflight e il deploy con snapshot e
rollback. Il commit Gateway `b368284b3f6a7675863f85eeafc42d67bf9187dc`
aggiunge il piano di sola lettura per la proiezione live e la raggiungibilità
dell'upstream. La CI Gateway e la CI UDP del commit
`d9626a91b3252b6bc0380f81e4f7a141bda4f3e7` sono verdi.

Questi fatti non equivalgono a una prova end-to-end: servono ancora il
workload IAM Onboarding con scope
`ouf.udp.identity.attestation.read`, gli scope HUMAN del preflight/review,
le route APISIX, la configurazione IAM UDP e il token ruotabile accessibile
al solo container Onboarding.

Il piano live di sola lettura del 28 settembre ha restituito `PASS`,
installazione `ouf-lab-netcup-01`, audience `ouf-api-gateway`, e raggiungibilità
di `ouf-udp:8080` dalla namespace APISIX. Il file preparato è
`/opt/ouf/r4a-stage/r4a-identity-routes-gdcn1xv5.json`. Prima del deploy,
l'inventario aveva restituito 404 per tutte e tre le route, e mancavano le
variabili IAM UDP e il collegamento all'attestazione in Onboarding. Nessuna
route APISIX è stata scritta dal piano.

Il deploy delle tre route ha poi restituito
`R4A_IDENTITY_ROUTES_INSTALLED=3 AUTHENTICATED_SMOKE_PENDING=true`.
Lo snapshot durevole delle route precedenti è
`/opt/ouf/r4a-stage/identity-routes-before-gdcn1xv5.json` (root-only).
Il test senza bearer ha restituito 401 per i tre percorsi. Questo non
attesta ancora token HUMAN/SERVICE né disponibilità del nuovo UDP.

L'inventario IAM successivo ha rilevato `PRESENT=false` per tutti e quattro
gli scope R4a nella discovery Keycloak (`urban.identity.preflight`,
`ouf.udp.identity.attestation.read`, `resolution.issue.read`,
`resolution.match.approve`) e `KCADM_SESSION_EXPIRED`. Le variabili bootstrap
amministrative sono presenti nel container Keycloak, senza mount aggiuntivi.
Prima di riconciliare scope e client, rinnovare la sessione kcadm tramite
`scripts/r4a_refresh_kcadm_session.py` e ripetere l'inventario amministrativo;
lo script usa le variabili soltanto nel container e non le stampa.

`scripts/r4a_reconcile_identity_iam.py` usa i reconciler Keycloak esistenti
in modalità `plan`, `apply`, `verify`. Crea gli scope mancanti, assegna i tre
scope HUMAN a `ouf-human-admin` come **optional** e crea
`ouf-source-onboarding` con scope SERVICE default, audience Gateway,
`ouf_actor_type=SERVICE` e `tenant_id=ouf-lab`. Il client secret rimane in
`/var/lib/ouf-r4a-identity/onboarding-client-secret` (directory root 0700,
file root 0600); non montarlo nel container Onboarding. Il token a breve
durata dovrà essere rinnovato da un workload distinto e letto da Onboarding
attraverso un file di sola lettura. Gli scope HUMAN opzionali vanno richiesti
nel Device Flow/sessione THS pertinente. Un PASS del reconciler non prova
ancora i claim del token, da verificare nell'acceptance autenticata.
Il primo `plan` IAM ha confermato quattro scope assenti; il primo `apply`
si è fermato prima di ogni mutazione Keycloak con
`IAM_SECRET_PARENT_INVALID` per `/opt/ouf/secrets`. Il percorso privato
dedicato sopra indicato risolve il prerequisito senza allentare i permessi
del parent esistente.
L'`apply` IAM successivo ha riportato PASS per le quattro definizioni, le tre
assegnazioni OPTIONAL, il nuovo client SERVICE e i permessi root 0600 del
secret. Il `verify` separato ha riportato PASS per le quattro definizioni,
mentre il controllo successivo era ancora in corso al momento dell'output:
il controllo è poi terminato con `R4A_IAM_RECONCILE=PASS MODE=VERIFY`.
Lo script
`r4a_service_token_smoke.py` controlla issuer, audience, scope, attore,
tenant, identità SERVICE, subject, ACR e scadenza con un token reale in
memoria, poi registra il solo status HTTP della route Gateway. Con UDP live
ancora vecchio, un 404 dopo l'autenticazione non prova il nuovo owner.
La prova reale ha restituito PASS per tutti e nove i claim, HTTP 404 dal
Gateway e `R4A_SERVICE_TOKEN_SMOKE=PASS`, senza stampa o persistenza del
bearer. Prima di sostituire UDP, usare
`scripts/r4a_udp_rollout_inventory.py` per confrontare immagine staged,
container, mount, rete e default dell'immagine senza divulgare env o sorgenti
dei mount; fermare UDP e fare il backup PostgreSQL immediatamente prima delle
migrazioni, conservando una via di ripristino del database.

## Inventario prima delle modifiche

Nel server, dal checkout Semantic, scaricare lo script revisionato senza
modificare il branch in uso e avviarlo con privilegi sufficienti a leggere
Docker e la chiave Admin APISIX:

```bash
cd /opt/ouf/semantic
git fetch --no-tags origin codex/r4a-smoke-semantic-inventory
git show a73ad73b6707bab18493ada5f4b5c7b2c0e78c53:scripts/r4a_identity_activation_inventory.py > /tmp/ouf-r4a-inventory.py
sudo python3 /tmp/ouf-r4a-inventory.py
```

Lo script legge la proiezione, `docker inspect`, la configurazione Nginx di
APISIX e gli ID delle sole tre route via Admin API nella namespace di rete
del container. Non stampa valori degli environment, chiavi o corpi delle
route. Ogni `R4A_INVENTORY_BLOCKED` è un gate da risolvere prima del deploy.

## Ordine di attivazione

1. Conservare inspect, definizione di avvio, immagine precedente e backup
   database dei servizi interessati. Verificare proiezione IAM corrente,
   audience `ouf-api-gateway`, issuer e DNS privato UDP. Stabilire il token
   SERVICE ruotabile e i nuovi scope nel client IAM; non mettere bearer o
   client secret nella configurazione pubblicata.
2. Compilare il catalogo Gateway dal branch revisionato e applicare la
   proiezione **attiva** dell'installazione. Il materializzatore
   `tools/materialize_r4a_identity_preflight.py` accetta soltanto tre binding
   esatti e un host upstream esplicito `ouf-udp` sulla rete privata. Lo script
   `ops.apisix.plan_r4a_identity_preflight` fa entrambe le operazioni,
   verifica la connessione dalla namespace APISIX e prepara il file di route
   privato in `/opt/ouf/r4a-stage`, senza scrivere nell'Admin API.
3. Il deploy `ops.apisix.deploy_r4a_identity_preflight` esige un percorso
   nuovo per la snapshot durevole `--backup-output`, modalità `0600`, la
   chiave Admin in file e il segreto OIDC ereditato da Nginx. Scrive soltanto
   le tre route, legge ciascuna route dopo il PUT e verifica 401 senza bearer;
   se fallisce ripristina quelle toccate. Conservare la snapshot per
   `--restore`. La risposta 401 non prova ancora il flusso autenticato.
4. Ricreare UDP con la nuova immagine, la stessa definizione di rete/mount/
   database e `OUF_UDP_IAM_ENABLED=true`, issuer e audience verificati.
   Controllare avvio, policy Authorization aggiornata e accesso dell'owner
   con bearer HUMAN e SERVICE. Un 403 o un 401 richiede diagnosi di scope,
   issuer, audience, actor e principal; non allargare la route per aggirarlo.
5. Ricreare Onboarding soltanto dopo un'attestazione UDP valida, aggiungendo
   `OUF_ONB_UDP_IDENTITY_GATEWAY_URL` e
   `OUF_ONB_UDP_IDENTITY_TOKEN_FILE` con mount privato per UID 10003.
   L'attivazione del DRAFT deve leggere l'attestazione corrente e fallire
   chiusa se hash/configurazione, tenant, classe o copertura non coincidono.
6. Eseguire lo smoke con fonte generica e oggetti canonici: preflight,
   pubblicazione, ingestion, handoff UDP, indice dei candidati, casi certi e
   incerti, proposta e approvazione atomica HUMAN del pacchetto THS. Un
   CSV o verticale API cambia l'adapter Ingestion, non la regola UDP.

Le route di review `resolution.issue.read` e
`resolution.match.approve`, la card THS e la proiezione chatbot richiedono
verifica separata prima di dichiarare completa la review end-to-end.
Non registrare un risultato R-SMOKE o R-INSTALL prima della prova live.
