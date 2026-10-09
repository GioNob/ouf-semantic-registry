# Diagnosi corrente della ricerca UDP da ChatGPT

La chiamata urban.object.search tramite ouf-admin restituisce HTTP503. Scopo: distinguere indisponibilità owner UDP, configurazione assente e problemi Gateway usando la ricerca Cinema già materializzata. Non ripetere ingestion/upload/profile né riavviare componenti.

## Operazioni

Legge in memoria il Docker inspect dei soli ouf-apisix e ouf-udp e la configurazione Nginx corrente del Gateway. Stampa soltanto booleani/conteggi sui binding; il valore della chiave Gateway viene controllato per forma in memoria e non divulgato. Nessun file chiave letto, nessun Env/config completo stampato, nessuna scrittura di configurazione/container lifecycle/route/IAM/policy. I file del solo script sono temporanei privati in /tmp.

Invia una richiesta di ricerca anonima al solo IP IPv4 privato di ouf-udp sulla rete ouf-backend, porta8080, endpoint /api/udp/v1/objects/search. Non invia bearer o receipt, non legge body/oggetti, non segue redirect o proxy. Il filtro UDP verificato al commit 83249a897eb4add4289b5181b3299f48ea4c0f99 verifica prima la configurazione di identità e poi il receipt. Questo probe diagnostico non sostituisce il percorso Gateway autorizzato né la prova positiva di serving.

Questi sono binding del lab, non default per altre installazioni.

## Esecuzione operatore

Usare la shell Bash sul VPS come oufadmin, non PowerShell. Copiare una riga alla volta, senza prompt. Source immutabile f63ba286058276f1a3e6a7393c015a5b89ed476d; SHA256 ec80aba8e835781a2fa3b909c1799cc21d95c03ced2cf801dd3b37634682c114. Lo script richiede sudo soltanto per leggere Docker.

```bash
umask 077; oufDiagDir=$(mktemp -d /tmp/ouf-product-search.XXXXXX)
```

```bash
curl -fsSL "https://raw.githubusercontent.com/GioNob/ouf-semantic-registry/f63ba286058276f1a3e6a7393c015a5b89ed476d/scripts/diagnose_product_search.py" -o "$oufDiagDir/diagnose.py"
```

```bash
printf '%s  %s\n' ec80aba8e835781a2fa3b909c1799cc21d95c03ced2cf801dd3b37634682c114 "$oufDiagDir/diagnose.py" | sha256sum -c - && sudo /usr/bin/python3 -I -B "$oufDiagDir/diagnose.py" --docker /usr/bin/docker --gateway ouf-apisix --udp ouf-udp --network ouf-backend
```

Restituire la sola riga OUF_PRODUCT_SEARCH_DIAGNOSIS oppure PRODUCT_SEARCH_DIAGNOSIS=BLOCKED STAGE=..., oltre ad eventuali errori di download/checksum. Non fare apply/restart o leggere file privati per tentare una riparazione dopo BLOCKED.

## Interpretazione e limiti

- Owner503: il servizio UDP interrogato è indisponibile prima di un receipt valido; con binding assenti si individua una lacuna concreta, altrimenti formato/leggibilità file o diversa configurazione devono essere verificati nella correzione mirata. Non conferma da solo la causa della risposta503 del Gateway.
- Owner403: la richiesta priva di receipt è rifiutata come atteso; dimostra un diniego corrente owner, non l'uguaglianza delle chiavi, la policy positiva o il serving. Se Gateway key/inheritance sono assenti, la lacuna è visibile; se presenti servono binding route e correlazione precisa.
- Owner404 o connectionfailed: endpoint/versione/upstream non provati; non rigenerare chiavi per deduzione.
- Ogni altro status richiede review; non è PASS della ricerca positiva.

Quattro test locali PASS: nessun valore segreto nell'output, binding mancanti/inheritance distinti,403/503/404 senza lettura body/receipt, rifiuto indirizzi pubblici/loopback. Probe VPS NON eseguito dall'assistente, nessuna CI o acceptance target dichiarata.
