# Ricerca UDP503: correzione condizionale owner binding, procedura corrente

Questa versione sostituisce i comandi ef414117, bloccati prima di qualsiasi GET/PUT perché richiedevano erroneamente ownerroot sulla chiave. Output operatore7ottobre08:32:36Europe/Rome: fileAdminregular,600,UID1000/GID1000. Non modificare proprietà/permessi o rigenerare la chiave.

Pin immutabile 7edde1826366a942e8f3e30bdca9c75826714534; SHA256 8df3b26571e98103663981fd9095cc515cfece109dccd05fa7fafdde1a4c2944. Otto testlocaliPASS; nuova esecuzione targetpendente. Nessuna nuova CI o servingpositivo dichiarato.

Il programma accetta il proprietario osservato solo con --admin-key-owner-uid1000 e accesso privato, rifiuta symlink/fileestraneo/permessi aperti. La chiaveAdmin è letta privatamente per la sola route execute-urban-object-search. L'Admin API viene raggiunta su127.0.0.1:9180 nel namespace rete del Gatewaycorrente: FDnamespacebloccato al processoosservato, nsenter, Pythonhost-I-B. Nessun container temporaneo/riavvio. Chiave e route sono trasferite al worker via stdin, mai argv/environment o output pubblico; il responsobackend è catturato in memoria.

Se la dichiarazioneOWNER_KEY_ENV esiste, non cambia nulla. Se manca, può aggiungere soltanto local OWNER_KEY_ENV = "OUF_UDP_SEARCH_OWNER_KEY" alla funzione, dopo aver verificato route/metodo/header/delega/receipt e direttiva env generata. Il confronto completo della route con rimozione della sola riga deve coincidere con l'originale; OIDC/scopes/schema/policy/upstream invariati. In caso di envgeneratoancoraassente non scrive.

Prima della PUT conserva previous-route.json in nuova root700/file600 sotto /etc/ouf/deploy-snapshots. Non aprire o pubblicare questo snapshotprivato. Verifica currentrouteprima/dopo. Ripristina su errore solo se vede ancora il proprio esattostatonuovo; driftconcorrente/ignoto richiede review, senza force. Nessun fileconfigAPISIXstorico modificato, nessuna fonte/run/UDPmutation/grant/providerstart.

Nella shell VPSoufadmin, tre righe separate:

```bash
umask 077; oufRepairDir2=$(mktemp -d /tmp/ouf-search-repair-v2.XXXXXX)
```

```bash
curl -fsSL "https://raw.githubusercontent.com/GioNob/ouf-semantic-registry/7edde1826366a942e8f3e30bdca9c75826714534/scripts/repair_search_owner_binding.py" -o "$oufRepairDir2/repair.py"
```

```bash
printf '%s  %s\n' 8df3b26571e98103663981fd9095cc515cfece109dccd05fa7fafdde1a4c2944 "$oufRepairDir2/repair.py" | sha256sum -c - && sudo /usr/bin/python3 -I -B "$oufRepairDir2/repair.py" --apply --docker /usr/bin/docker --gateway ouf-apisix --network ouf-gateway-control --admin-key-file /opt/ouf/secrets/apisix-admin-key --admin-key-owner-uid 1000 --nsenter /usr/bin/nsenter --backup-root /etc/ouf/deploy-snapshots
```

Restituire il markerSEARCH_OWNER_BINDING. Una causa nota è esposta soltanto come codice sicuro REASON, mai rawerror/secret. REPAIRED_AND_READBACK_VERIFIED è verifica della correzione route, non servingpositivo; l'assistente richiama subito la ricercaCinema da ChatGPT con accountouf-admin. ALREADY_DECLARED/envabsent non conferiscono alcuna correzione. Conservare snapshot e vecchio tentativo.
