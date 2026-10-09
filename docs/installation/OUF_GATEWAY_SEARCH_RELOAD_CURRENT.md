# APISIX: validazione e reload della configurazione esistente

Output operatore7ottobre08:21:53Europe/Rome: SEARCH_ENV_CONFIG_LINE=present. Source bind: /etc/ouf/deploy-snapshots/consultation-human-read-20261002-1153/prepared/apisix-config.yaml. Il file storico non va modificato. Il diagnostic precedente non trovava la direttiva env plain nel Nginx generato; UDP rispondeva403 alla richiesta senza receipt.

Prossima operazione nella shell VPS oufadmin:

```bash
sudo docker exec ouf-apisix apisix test && sudo docker exec ouf-apisix apisix reload
```

Il secondo comando viene eseguito solo se il test termina con successo. È reload del Gateway corrente, non aggiornamento immagine/container o avvio dei provider; nessun file sorgente/snapshot,route,IAM,policy,chiave,fonte,run o oggettoUDP viene modificato dal piano. Nginx generato e worker vengono aggiornati secondo il CLI APISIX. Non eseguire stop/start/restart o rigenerare segreti se il test/reload fallisce: conservare l'errore e diagnosticare quello specifico.

Target reload ancora NON eseguito. Dopo output positivo l'assistente richiama urban.object.search tramite lo stesso account ouf-admin e verifica il risultato reale. Nessuna clearance/acceptance del provider esterno è concessa da questo passo. https://apisix.apache.org/docs/apisix/installation-guide/ descrive test prima di reload nella stessa installazione.
