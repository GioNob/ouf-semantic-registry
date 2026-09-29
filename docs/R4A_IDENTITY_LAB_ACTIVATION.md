# R4a: attivazione controllata dell'identità nel laboratorio

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

Le route di review `resolution.issue.read` e
`resolution.match.approve`, la card THS e la proiezione chatbot richiedono
verifica separata prima di dichiarare completa la review end-to-end.
Non registrare un risultato R-SMOKE o R-INSTALL prima della prova live.
