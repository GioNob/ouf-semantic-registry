# Ricerca UDP503: verifica e correzione condizionale della sola route

Test/reload APISIX eseguiti dall'operatore7ottobre08:23:30Europe/Rome; chiamata ChatGPT successiva ancoraHTTP503. Non ripetere reload o alterare il file snapshot consultation-human-read-20261002-1153/prepared/apisix-config.yaml.

Sorgente ef414117af30a65d36807b36c8eb1dcef9d7178d; SHA256 3e16a8e9242fa2a1d231acddbf9a08a186d3f616189368010eac0ade117872a1. Cinque test localiPASS per deltaunico, bindingesistente/estraneonegato, routeestranea, readback/ripristinosuscritturaambigua, driftconcorrentenegato. Nessuna prova target/CI positiva concessa.

## Operazione concreta

Lo script legge privatamente la chiave Admin già esistente /opt/ouf/secrets/apisix-admin-key e la usa soltanto per GET/PUT dell'ID execute-urban-object-search sull'IPprivato gatewaycontrol del containercorrente. Nessun valore di chiave viene stampato, copiato negli argomenti Docker o rigenerato.

Legge inspect e nginx.conf in memoria. Procede solo se GatewayèRUNNING, chiaveSEARCHgiàpresente/64hex e direttivagenerata envSEARCHrilevata. Verifica URI/metodoPOST, headerfunzione, declarationdelegation e contrattoreceipt. Se OWNER_KEY_ENV è già dichiarata non modifica nulla; bindingdiverso/formatoignoto blocca. Se manca soltanto la declaration attesa, aggiunge local OWNER_KEY_ENV = "OUF_UDP_SEARCH_OWNER_KEY" subito dentro la funzione. Il confronto integrale dopo rimozione della sola riga deve coincidere con la route originale; nessun OIDC/scope/schema/policy/upstream viene cambiato.

Prima della PUT salva previous-route.json in una nuova directory root700/file600 sotto /etc/ouf/deploy-snapshots. Lo snapshot route può incorporare configurazioneprivata: non aprirlo/stamparlo/caricarlo su GitHub. Rilegge currentrouteprima e dopo PUT. In errore ripristina soltanto se currentroute è ancora il nostro esatto nuovostato; non sovrascrive stati concorrenti/ignoti. Questi casi riportano REVIEW_REQUIRED, conservano snapshot e richiedono diagnosi, senza nuovoapply/restart.

Nessun container/provider/sourcejob/oggettoUDP viene creato o avviato, nessun fileconfigAPISIXstorico viene modificato. Questa correzione non aggiunge grant né conferisce provider acceptance/start. Il successo del readback non è servingpositivo: la chiamata ChatGPT successiva lo verifica.

## Tre righe nella shell VPS

```bash
umask 077; oufRepairDir=$(mktemp -d /tmp/ouf-search-repair.XXXXXX)
```

```bash
curl -fsSL "https://raw.githubusercontent.com/GioNob/ouf-semantic-registry/ef414117af30a65d36807b36c8eb1dcef9d7178d/scripts/repair_search_owner_binding.py" -o "$oufRepairDir/repair.py"
```

```bash
printf '%s  %s\n' 3e16a8e9242fa2a1d231acddbf9a08a186d3f616189368010eac0ade117872a1 "$oufRepairDir/repair.py" | sha256sum -c - && sudo /usr/bin/python3 -I -B "$oufRepairDir/repair.py" --apply --docker /usr/bin/docker --gateway ouf-apisix --network ouf-gateway-control --admin-key-file /opt/ouf/secrets/apisix-admin-key --backup-root /etc/ouf/deploy-snapshots
```

Restituire solo marker SEARCH_OWNER_BINDING oppure erroredownload/checksum. Se ALREADY_DECLARED o GENERATED_SEARCH_ENV_DIRECTIVE_ABSENT non c'è stata alcuna scrittura e la causa503restaaperta. Se REPAIRED_AND_READBACK_VERIFIED, l'assistente ricerca subito Cinema via stesso account ouf-admin e prosegue con paginazione/mappingTeatri.
