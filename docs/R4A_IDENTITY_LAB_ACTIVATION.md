# R4a: attivazione controllata dell'identità nel laboratorio

## Esito del preflight HUMAN e prossimo gate (29 settembre, sera)

Il diagnostic SDK nel clone UDP ha identificato il vincolo effettivo:
`NO_APPLICABLE_GRANT` sul bundle `ouf-lab-authorization:30`. Il grant
`urban.identity.preflight` del ruolo `admin` conteneva cinque
`allowedDataLabels` e quattro `allowedDetailLevels`; la risorsa `capability`
del preflight non ha né etichetta né livello. La proposta governata
`86086d30-1f2d-4432-af09-fb45bf8189bd` ha cambiato **soltanto** i due
insiemi di quel permesso nel catalogo ruoli. Il titolare ha confermato in THS:
stato `PUBLISHED`, policy `ouf-lab-authorization:31`. La lettura del catalogo
mostra ancora 29 permessi admin e due assegnazioni; i due insiemi del preflight
sono vuoti. Il contratto SDK continua a negare una richiesta di dati etichettati
quando manca l'etichetta richiesta; non modificarlo per questo caso.

Il clone isolato dell'immagine UDP corretta ha poi restituito `ALLOW` con bundle
31, scope HUMAN presente e un grant corrispondente. Sul vecchio UDP live il
POST restituiva ancora 403; lo switch controllato ha portato live l'immagine
`edaba2bff18a2aaf52d1180f21f0e68984cc3437` con Flyway 34 e preflight
autenticato `PASS`. L'attestazione è
`57499699-dbc5-419d-a14b-27cd3604ec6f`, `INDEXED_OBJECTS=0`: la fonte
non è ancora stata ingerita. Backup verificato
`/opt/ouf/r4a-stage/udp-before-principal-fix-g1580k75.dump`; precedente
container `ouf-udp-principal-rollback-a4fb36e8ce32`. Conservare entrambi.

`scripts/r4a_verify_cinema_attestation.py` ha letto senza nuova scrittura
l'attestazione esistente dalla route SERVICE usata da Onboarding: versione e
hash congelati `PASS`, `INDEXED_OBJECTS=0`, compatibilità Ingestion `ABSENT`,
Ingestion live running ma immagine staged diversa dal live. Il successivo
inventario read-only `scripts/r4a_ingestion_compatibility_inventory.py` del
commit Semantic `438e3fbfc00e742cbe55a376bda6626ba5f3a807` è stato
preparato e **non eseguito** su richiesta dell'utente. Il [nuovo handoff](handoffs/OUF_HANDOFF_2026-09-29_R4A_PREFLIGHT_TO_INGESTION.md)
registra comando e gate. La successiva attivazione Onboarding richiede
approvazione HUMAN, attestazione di compatibilità da Ingestion Runtime SERVICE
e verifica della stessa attestazione UDP; nessuno dei tre gate è implicito nel
solo preflight. Non ripetere il submit della versione già `IN_REVIEW`.

## Preflight HUMAN: diagnosi storica del 403 (prima della policy :31)

La versione cinema è `IN_REVIEW`, congelata con hash
`sha256:2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891`.
Il preflight HUMAN ha restituito 403. L'inventario di sola lettura conferma
policy attiva `ouf-lab-authorization:30`, un grant applicabile, scope e tipo
attore HUMAN corretti nel bearer. La stessa GET autenticata con ID assente
restituisce 403 generico sia tramite Gateway sia direttamente verso UDP:
la route non è la causa. La forma della risposta colloca il rifiuto durante
la risoluzione del contesto di autorizzazione, prima della decisione del
preflight.

Il bridge IAM di UDP era ordinato prima di
`SecurityContextHolderAwareRequestFilter`, che ricopre la richiesta e può
mascherare il principal verificato dal bridge. Il commit UDP
`edaba2bff18a2aaf52d1180f21f0e68984cc3437` colloca il bridge dopo
l'adattatore servlet e fa eseguire il test della sequenza durante la build
dell'immagine. La causa runtime resta da confermare con lo smoke autenticato
dopo la build. `scripts/r4a_stage_udp_principal_fix.py` accetta solo quel
commit, controlla che le modifiche siano limitate a bridge, test e Dockerfile,
esegue la build con il test e registra l'immagine senza toccare il live o DB.
Non ripetere la submit della versione già congelata; riprendere il preflight
solo dopo la verifica del runtime aggiornato.

Lo staging ha restituito `PASS`, con immagine
`edaba2bff18a2aaf52d1180f21f0e68984cc3437`, tre soli percorsi di diff e
test del bridge eseguito nella build; il live e il DB sono invariati.
`scripts/r4a_switch_udp_principal_fix.py` ottiene prima del fermo un bearer
HUMAN tramite Device Flow e verifica la configurazione cinema congelata.
Controlla immagine e configurazione live, crea un candidato spento con gli
stessi env/mount, conserva un dump PostgreSQL verificato, sostituisce UDP,
richiede health e Flyway 34 e prova il POST preflight reale seguito dalla
lettura dell'attestazione. Se un controllo fallisce dopo lo swap, ripristina
il container precedente; non ripristina automaticamente il DB. Una prova
positiva crea l'attestazione desiderata e lascia la versione Onboarding
`IN_REVIEW` per i successivi gate di approvazione.

**Esito dello switch di prova:** il candidato e il backup verificato
`/opt/ouf/r4a-stage/udp-before-principal-fix-9pruwm49.dump` sono stati
preparati; il POST autenticato ha ancora restituito 403. Il rollback runtime
è `PASS`, il dump rimane conservato e il database non è stato ripristinato
automaticamente. La sequenza dei filtri era una causa possibile nel codice,
ma la prova live mostra che la diagnosi non era sufficiente. Prima di ogni
altro switch, `scripts/r4a_udp_authorization_runtime_inventory.py` controlla
in sola lettura endpoint del registry, stato del bearer workload e risposta
del bundle senza stampare token o policy. Proseguire in base a questo esito.
L'inventario ha confermato bearer SERVICE fresco, registry HTTP 200, bundle
versione 30 e hash corrispondente. Una copia isolata del dump con l'immagine
corretta ha poi restituito, a una GET SERVICE autenticata con identificativo
assente, `UDP_IDENTITY_PREFLIGHT_NOT_FOUND`: la richiesta raggiunge la logica
di dominio dopo autenticazione e autorizzazione. Clone e container temporaneo
sono stati eliminati e il live è invariato. Il successivo script
`r4a_probe_udp_human_route.py` confronta una GET HUMAN senza scritture,
con lo stesso bearer, direttamente verso la copia isolata e tramite Gateway
verso il live. Questa prova separa il percorso HUMAN interno dal route layer.
La GET HUMAN sul clone corretto ha restituito un 403 `Owner authorization
denied`, quindi il principal arriva al controller ma la capability non è
concessa nella decisione locale. La GET Gateway verso il live precedente ha
restituito il 403 generico già noto. `scripts/r4a_human_policy_decision_inventory.py`
ricostruisce ora, con un bearer HUMAN fresco e il bundle attivo, ogni vincolo
del grant esattamente come l'SDK (incluso subject effettivo `ouf_subject` e
organizationId omessi dall'inventario iniziale), senza stampare identità,
bearer o policy. Non modificare la policy finché il vincolo fallito non è
identificato.
L'inventario con un bearer fresco ha dato `PASS` per ogni vincolo del grant
versione 30; `ouf_subject` è assente, il subject IAM coincide con quello del
grant e `organizationId` è assente. La valutazione ricostruita è `ALLOW`,
mentre UDP nel clone nega: occorre osservare la versione del bundle e il
`decisionCode` effettivi. Il commit UDP
`9574fefbd864d7de88f287c2481cf843e7d65a37` aggiunge un endpoint
diagnostico abilitabile solo con `OUF_UDP_AUTHORIZATION_DIAGNOSTIC_ENABLED=true`;
resta disabilitato per default e restituisce soltanto metadati della decisione.
`r4a_stage_udp_auth_diagnostic.py` compila e testa l'immagine senza cambiare il
live; `r4a_probe_udp_effective_decision.py` abilita l'endpoint solo in un clone
temporaneo, legge il risultato con bearer HUMAN e ripulisce database/container.

## Stato e confini

**Aggiornamento live 29 settembre 2026:** lo switch UDP è passato con immagine
`3402050b36ee28758e5255a57b0d32bc3983a34f` e Flyway 34. Il dump
precedente `/opt/ouf/r4a-stage/udp-before-r4a-bx9w8isg.dump` è stato
validato e conservato; il vecchio container è
`ouf-udp-rollback-247d81294764`. L'isolated probe aveva prima migrato a
Flyway 34 un clone del dump senza alterare il live. Restano la prova Gateway
autenticata HUMAN/SERVICE, il token rinnovabile e l'attivazione Onboarding,
poi Ingestion e lo smoke end-to-end. Non eliminare il dump o il rollback
container prima di chiudere questi gate.

Lo smoke SERVICE prima di un'attestazione usa
`scripts/r4a_service_token_smoke.py`: richiede 401 sulla route senza bearer e
400 con il bearer SERVICE quando manca intenzionalmente il parametro
`configurationHash`. Questa coppia verifica Gateway e binding della richiesta
nel nuovo owner UDP; **non** verifica ancora la lettura positiva di
un'attestazione valida. Un 404 o 500 non è PASS.
La verifica live del 29 settembre ha restituito tutti i claim SERVICE `PASS`,
401 senza bearer e 400 con bearer sulla route; la lettura di un'attestazione
reale resta aperta. L'inventario Onboarding live ha confermato immagine staged
`f74c3a9f…`, rete `ouf-backend`, UID/GID `10003:10003`, cinque mount read-only,
restart `unless-stopped`, Flyway **31** e secret client root 0600. La directory
del token non era ancora presente. L'immagine staged e il live hanno lo
stesso insieme di migrazioni SQL; lo switch deve quindi richiedere 31 prima e
dopo, senza affidarsi a una versione supposta.

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

La policy, gli scope/client IAM, le tre route APISIX e UDP live sono stati
attivati nei passaggi sotto registrati. Questi fatti non equivalgono a una
prova end-to-end: restano l'accettazione autenticata delle route, il token
workload ruotabile accessibile solo a Onboarding, il preflight HUMAN della
configurazione congelata e la filiera di acquisizione fino a UDP.

Per il token SERVICE di Onboarding, `scripts/r4a_onboarding_token_runtime.py`
installa un servizio oneshot e un timer che rinnova ogni minuto. Il client
secret resta in `/var/lib/ouf-r4a-identity/onboarding-client-secret` (0600);
lo script eseguito dal servizio viene copiato nella stessa directory privata
(root:root, 0600), senza richiedere permessi particolari alla directory di staging;
il servizio usa l'utente root senza la direttiva systemd `Group=10003`
(l'host non espone quel GID come gruppo NSS). Il file bearer è assegnato al
GID numerico 10003 dallo script dopo il rinnovo;
il bearer viene sostituito atomicamente in
`/run/ouf-onboarding-identity/token` (root:10003, 0640). Montare **la
directory** `/run/ouf-onboarding-identity` in sola lettura nel container,
così il file sostituito diventa visibile senza riavviare Onboarding. La
regola tmpfiles dedicata ricrea la directory root:10003 (0750) al boot.
Prima del rollout eseguire `scripts/r4a_onboarding_rollout_inventory.py`:
legge solo identificativo immagine, impostazioni e nomi delle variabili,
destinazioni dei mount, versione Flyway e metadati dei file, senza valori
dei secret o sorgenti dei mount.
`scripts/r4a_prepare_onboarding_candidate.py` confronta immagine, rete,
UID/GID, cinque mount live, env e impostazioni Docker, verifica il token
rinnovato e crea **spento** `ouf-onboarding-r4a-candidate` con la directory
del token in bind read-only e le sole due variabili UDP identity. Il readback
del candidato è obbligatorio. Riutilizza un candidato già presente solo se
spento e identico alla configurazione prevista; altrimenti si ferma senza
rimuoverlo. Non esegue migrazioni né cambia il live.
Nel caso osservato in lab (differenze `IMAGE,RESTART,MOUNTS,ENV`, con
`STOPPED,USER,NETWORK,LOG_DRIVER` corretti), l'opzione `--replace-stale`
ricontrolla ID, stato e differenze, rinomina il candidato precedente con
suffisso basato sul suo ID e crea quello nuovo. Il vecchio container resta
conservato; se la creazione fallisce, lo script tenta di ripristinare il nome.
`scripts/r4a_switch_onboarding.py --expected-flyway <versione verificata>`
richiede che il timer sia attivo, che il bearer abbia claim corretti,
scadenza sufficiente e mtime recente, e che il candidato sia spento; controlla
health e Flyway live, ferma Onboarding, crea e valida un dump custom,
conserva il vecchio container rinominato e avvia il candidato. Dopo l'avvio
richiede health e la stessa versione Flyway (nessuna migrazione Onboarding
aggiunta nell'immagine staged). Se il backup fallisce riavvia il vecchio
container; dopo uno swap fallito tenta rollback del runtime ma conserva il
dump per il recupero del DB. Non lanciare lo switch prima di esaminare
l'inventario e il candidato.

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
L'inventario live ha confermato la nuova immagine `d9626a91…`, rete unica
`ouf-backend`, UID/GID `10004:10004`, due mount bind read-only, nessuna porta
host, restart `unless-stopped`, entrypoint/cmd/workdir di default, ambiente
monoriga, PostgreSQL `pg_dump` 17.11, issuer e audience attesi. I bind sono
nel campo Docker `HostConfig.Mounts`, non in `HostConfig.Binds`.
`scripts/r4a_prepare_udp_candidate.py` crea un container candidato **non
avviato** con gli stessi mount e env live più le tre variabili IAM; confronta
il readback e cancella il file temporaneo degli env. Non ferma UDP, non
esegue migrazioni e non tocca il DB. Il backup va eseguito solo nella fase
successiva, dopo aver fermato il live e prima di avviare il candidato.
Il candidato attuale è stato creato spento con commit `3402050b…`, due mount
identici e ambiente live più le tre variabili IAM; UDP e DB risultavano
invariati. `scripts/r4a_switch_udp.py` esige che il vecchio container sia
healthy, legge la versione Flyway precedente, lo ferma, produce un dump
custom completo del DB `ouf_udp` in `/opt/ouf/r4a-stage` (root 0600),
valida il dump con `pg_restore -l`, conserva il container vecchio rinominato,
avvia il candidato e controlla health, raggiungibilità da APISIX e la versione
Flyway attesa (34 nella versione aggiornata).
Se il backup fallisce riavvia il vecchio UDP; se l'avvio nuovo fallisce prova
il rollback del **runtime** senza ripristinare automaticamente il DB. Non
eliminare il dump né il container vecchio. In caso di vecchio runtime non
avviabile dopo una migrazione parziale, fermare UDP e usare solo allora
`scripts/r4a_restore_udp_backup.py --backup <dump> --old-version <versione>`;
questo è un ripristino distruttivo del DB alla snapshot e richiede verificare
che non siano state accettate nuove scritture dopo il dump.

### Esito del primo switch UDP (29 settembre 2026)

Il candidato `d9626a91…` non si è avviato: Flyway ha rifiutato la validazione
per checksum diversi nelle migrazioni V22–V26. L'immagine live
`944c2f5…` e il ramo R4a avevano assegnato gli stessi numeri a migrazioni
diverse. Il rollback automatico del runtime è passato; il vecchio UDP è
operativo e nessuna nuova migrazione risulta applicata. Il dump verificato è
`/opt/ouf/r4a-stage/udp-before-r4a-j5k8rens.dump` ed è conservato.

**Non rilanciare `r4a_switch_udp.py` con il candidato `d9626a91…`.** La
correzione locale integra le migrazioni live V22–V26, conferma i checksum
Flyway live V23–V26 e rinumera quelle R4a V27–V34. Occorrono CI verde,
immagine nuova, nuovo inventario e script di switch aggiornato con commit e
versione 34 prima di un altro tentativo. Le API di geometria e proprietà
già presenti nel runtime live vanno preservate e verificate nel merge.

La PR di integrazione in bozza è `GioNob/ouf-udp-object-resolution#37`.
Il commit `3402050b36ee28758e5255a57b0d32bc3983a34f` ha superato tutti
i job CI (Java/PostgreSQL, SDK, CRS, prestazioni, ripristino e supply chain).
Gli script di staging, inventario, preparazione e switch sono ora fissati a
questo commit; lo switch richiede esattamente Flyway 26 prima e 34 dopo.
Prima dello switch, `scripts/r4a_probe_udp_migration.py` ripristina il dump
in un database temporaneo, avvia un container temporaneo senza esecuzione
worker, verifica health e Flyway 34, controlla che il database live rimanga
a V26 e rimuove le risorse temporanee. La prova richiede che il nuovo
candidato sia già stato preparato, ma non avviato.
Il primo tentativo della prova si è fermato nella creazione del clone: il
ruolo applicativo `ouf_udp` non ha `CREATEDB`. La versione successiva dello
script legge il ruolo amministrativo dal container PostgreSQL, ne verifica
la facoltà di creare il database temporaneo e lo usa soltanto per creazione
e rimozione. Non concede nuovi privilegi al ruolo applicativo.
Il tentativo seguente ha creato il clone, ma il ripristino si è fermato sui
privilegi richiesti per creare un'estensione PostgreSQL. La prova ora rileva
nomi e versioni delle estensioni presenti nel database live, le prepara nel
solo clone con il ruolo amministrativo, verifica le versioni, quindi ripristina
lo schema e i dati con `ouf_udp` omettendo i commenti. Il clone viene rimosso
anche in caso di errore; il database e il container live restano invariati.
Il ripristino successivo ha superato la preparazione di due estensioni, ma
`pg_restore` ha ancora segnalato un permesso insufficiente. La prova ora
riporta soltanto la categoria SQL e il tipo di oggetto TOC coinvolto, senza
mostrare query, nomi di oggetti, dati o credenziali; prima di cambiare
ulteriormente il ripristino serve questa diagnosi circoscritta.
La diagnosi ha indicato `PERMISSION_FOR_TABLE`. Un tentativo di concedere
privilegi alle tabelle di configurazione delle estensioni si è fermato prima
del ripristino; non è quindi prova che fossero le sole tabelle interessate.
La prova ora usa il ruolo amministrativo per **l'intero restore nel clone**,
lascia attiva la ricostruzione dei proprietari registrati nel dump, confronta
proprietario dello schema e di ogni relazione applicativa con il live, e solo
allora avvia il candidato come `ouf_udp`. Non modifica i privilegi nel live.
Il tentativo con restore amministrativo ha superato `pg_restore`, ma un comando
di verifica prima del marcatore dei proprietari ha fallito. Il log non distingue
la lettura della versione Flyway dalla query sui proprietari: la precedente
attribuzione alla sola lettura Flyway era troppo precisa. L'inventario di sola
lettura `scripts/r4a_restore_access_inventory.py` ha confermato che nel dump
schema e tabella Flyway appartengono a `ouf_udp`; il ruolo può leggere la
tabella nel live. L'ipotesi che `--no-acl` spieghi da sola questo errore non è
supportata dai dati. La prova ora marca separatamente ciascuna verifica,
classifica il codice SQLSTATE e, in caso di errore nel clone, interroga con il
ruolo amministrativo presenza, proprietà e permessi senza stampare dati o SQL.
Il primo output classificato ha mostrato `CLONE_FLYWAY` riuscito e
`CLONE_OWNERSHIP` fallito con SQLSTATE 42725, mentre presenza, proprietà e
permessi della tabella Flyway nel clone risultavano tutti validi. L'errore è
quindi nella query di confronto scritta per la prova: la concatenazione
implicita del tipo catalogo `pg_class.relkind` è ambigua. I valori della query
vengono ora convertiti esplicitamente a `text`. Il tentativo successivo ha
superato il restore e la verifica dei proprietari, avviato l'immagine
`3402050b…` sul clone e migrato fino a Flyway 34. Pulizia del clone riuscita;
il container e il database live sono rimasti a Flyway 26. Lo switch live e lo
smoke con bearer autenticato sono i prossimi gate. I due test dello script di
switch (ordine stop/backup/swap e recupero dopo errore backup) passano.

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

**Evidenza live 29 settembre:** lo switch Onboarding è riuscito con immagine
`f74c3a9f377b5ce93b5cab298fa24372de1602bc` e Flyway 31. Il backup
`/opt/ouf/r4a-stage/onboarding-before-r4a-0yqagqb4.dump` ha superato
`pg_restore -l`; il precedente container è conservato come
`ouf-onboarding-rollback-e8c73d52f85e`. Il timer del bearer è attivo.
L'attestazione positiva per una versione congelata e la filiera Ingestion →
UDP restano da provare. L'inventario read-only
`scripts/r4a_onboarding_post_switch_inventory.py` verifica il nuovo runtime e
legge solo classe, proprietà, riferimenti semantici e presenza dei profili del
DRAFT, senza mostrare configurazione completa o credenziali.
L'inventario live ha confermato DRAFT, classe `cinema#Cinema` e le proprietà
`#indirizzo` e `#nome`; non sono ancora presenti `semanticReferenceBindings`,
il profilo `runtime.execution` né `runtime.udp`. Il piano di sola lettura
`scripts/r4a_cinema_governed_proposal_plan.py` usa il set semantico pubblicato
già registrato, controlla asset e lock 0, e propone i profili Ingestion e UDP
senza scrivere nel database. Il piano non è una validazione, un submit o una
decisione HUMAN.
Il piano live ha prodotto hash SHA-256
`2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891`.
`scripts/r4a_apply_cinema_governed_proposal.py` ricostruisce la stessa proposta,
verifica l'hash, ottiene un bearer HUMAN tramite device flow, aggiorna solo
il DRAFT con ETag `ov:0`, legge il risultato e chiama `/validate`. Se un
precedente tentativo ha già scritto esattamente la proposta con lock 1, riprende
la validazione. Non effettua submit, approvazione o attivazione.
La proposta è stata applicata nel DRAFT con lock 1 e `/validate` ha restituito
PASS, zero errori e zero warning. `scripts/r4a_freeze_and_preflight_cinema.py`
ricontrolla l'hash, verifica la validazione server prima del submit, congela
la versione con ETag `ov:1` e chiama il preflight UDP con bearer HUMAN. Legge
poi l'attestazione sia dalla route HUMAN sia dalla route SERVICE usata da
Onboarding. Questo passaggio non approva né attiva la versione; se interrotto
dopo il submit riconosce `IN_REVIEW` con lock 2 e hash identico.
Il submit live ha congelato la versione con lock 2 e hash atteso, ma il primo
POST HUMAN al preflight UDP ha risposto 403. L'inventario read-only
`scripts/r4a_human_preflight_denial_inventory.py` confronta scope e ruolo del
bearer con descriptor e grant nel PolicyBundle ACTIVE, ed esegue solo un GET
su un ID inesistente per distinguere la denial di route/owner. Non ristampa il
bearer, la policy completa né la configurazione congelata; nessuna
attestazione è stata ancora prodotta.

Le route di review `resolution.issue.read` e
`resolution.match.approve`, la card THS e la proiezione chatbot richiedono
verifica separata prima di dichiarare completa la review end-to-end.
Non registrare un risultato R-SMOKE o R-INSTALL prima della prova live.

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
