# Ricerca UDP: anomalia inheritance Gateway,7 ottobre2026

Output operatore08:17:03Europe/Rome: script/checksumOK; probe UDP senza receipt403; tutti5bindingUDP presenti e mountchiaveRO; Gateway ownerkey presente/64hex, ma il diagnostic non trova la direttiva plain env nella configurazione Nginx generata. Nessuna modifica target. Questo restringe la diagnosi, non prova ancora il serving positivo o la causa esclusiva del503.

Prossimo passo circoscritto: leggere la dichiarazione env nella forma lista YAML corrente e il solo path del bind config.yaml. Nessun valore Env/file completo/chiave da stampare. La prima verifica cerca una voce non quotata su una riga di lista: absent non equivale da solo a YAMLsemanticamenteassente per formati inline/quotati. Il path serve a distinguere filecorrente da artefatto storico da preservare; non riscrivere snapshot sotto /etc/ouf/deploy-snapshots o /opt/ouf/backup.

Eseguire due righe separate nella shell VPS oufadmin, non PowerShell:

```bash
sudo docker exec ouf-apisix sh -c 'test -r /usr/local/apisix/conf/config.yaml || exit 1; if grep -Eq "^[[:space:]]*-[[:space:]]*OUF_UDP_SEARCH_OWNER_KEY[[:space:]]*(#.*)?$" /usr/local/apisix/conf/config.yaml; then echo SEARCH_ENV_CONFIG_LINE=present; else echo SEARCH_ENV_CONFIG_LINE=absent; fi'
```

```bash
sudo docker inspect --format '{{range .Mounts}}{{if eq .Destination "/usr/local/apisix/conf/config.yaml"}}CONFIG_SOURCE={{.Source}}{{end}}{{end}}' ouf-apisix
```

Confrontare col sorgente generatore Nginx prima di decidere la riparazione. Se sorgente già corretto: validazione e reload circoscritto da preparare. Se sorgente mancante: nuova configurazione conservando voceevaloriesistenti e snapshot originali; scegliere il percorso dopo osservazione mount. Nessun restart indiscriminato/rotazione chiavi/policy grant. Test locale positivo e negativo del linecheck PASS; non è parser YAML completo né test reload sul target. Dopo correzione rileggere via stesso account ChatGPT la ricerca Cinema; preservare8/8 eTeatri.
