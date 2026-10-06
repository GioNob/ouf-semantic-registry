> Stato corrente 6 ottobre 2026 — versione effettiva LuaJIT `2.1.1787558776`, tag sorgente conservato `v2.1-20260824`. Build e scansioni [37448782226](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37448782226) PASS: **0 Critical / 0 High / 0 Unknown**, anche nel supplemento nativo. Verifica indipendente dello ZIP pubblicato [37450055158](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37450055158) PASS, firme e qualificazione byte v2 incluse. [Procedura VPS v2](/docs/installation/SEMANTIC_IMAGE_REMEDIATION_V2_TARGET_QUALIFICATION_2026-10-06.md) pronta; esecuzione sul VPS ancora da osservare. PASS VPS v1 storico, non ripetere. Ambiente test preservato; importazione, runtime, publisher trust, copertura accettata, acceptance e start restano non autorizzati. [Receipt corrente](/docs/handoffs/receipts/SEMANTIC_LUAJIT_RUNTIME_IDENTITY_2026-10-06_CI.json).

> Le sezioni conservate sotto documentano anche candidati storici. I precedenti conteggi 2 Critical / 1 High non descrivono il nuovo bundle v2.

# Qualificazione delle evidenze remediation sul VPS — 6 ottobre 2026

Stato: comando ESEGUITO/PASS dall'operatore il 6 ottobre 2026 alle 08:21:50 Europe/Rome. Non ripeterlo. È un nuovo snapshot di sole evidenze; il gate49 storico resta a soglia falsa. Nessuna immagine viene importata o avviata. La CI prova byte, test e attestazioni; copertura completa, publisher trust e verifica crittografica target restano non accettati.

## Prova letta

[Run37420144098](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37420144098), job112127446154 SUCCESS, code b6be410449c7dc5b11d227d732f9776a1ab24b52, merge CI226b1d3cb0562ed1cd840c758873f92ab3401991. Test container/APISIX2PASS0skip, qualificatore3negativePASS, archivi/SBOM/report realmente verificati, Grype0Critical/0High/0Unknown su entrambi. Restano5Medium adapter e141Medium/17Low/4Negligible southbound. OpenSSL4suite selezionate/7testPASS; il solo setup FIPS è saltato perché non è una build FIPS. Tre attestazioni CI, quattro verifiche crittografiche PASS, medesimo qualificatore standalone esercitato sui veri archivi:0import,0container e acceptance/runtime/start false.

[Receipt CI](../handoffs/receipts/SEMANTIC_IMAGE_REMEDIATION_2026-10-06_CI.json) e [piano/limiti](SEMANTIC_IMAGE_VULNERABILITY_REMEDIATION_2026-10-06.md). Le librerie native OpenResty richiedono ancora revisione/integrazione della copertura SBOM prima di complete acceptance. Questa qualificazione conserva e verifica i byte, non concede tale accettazione.

## Operazione eseguita — riferimento storico, non ripetere

1. Scaricare lo ZIP **completo** [image-remediation-alpine-ubuntu-source-fixed-37420144098](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37420144098/artifacts/11392623308),205454159byte. Non usare l'artifact evidence più piccolo: non contiene le immagini. SHA256 dello ZIP bf369a5e445a7e84c51d0252b6714912b0d92897097f3afeb2a21c85db38fa2a.
2. Copiarlo sul VPS, come utente oufadmin, con nome `$HOME/ouf-remediation-transfer-20261006/ouf-remediation-20261006.zip`. Non estrarlo e non eseguire docker load.
3. Sul VPS eseguire il wrapper immutabile qui sotto. Legge lo ZIP e crea esclusivamente `/etc/ouf/deploy-snapshots/semantic-image-remediation-20261006-v1`, directory root700 e file root600. Verifica ZIP bounded, SHA256, tar/config/rootfs, tar identico a quello letto da Syft, SBOM/report/receipt e soglia/freschezza del DB. I report sono conservati privati, stdout è redatto.

```bash
ouf_task=$(mktemp -d)
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 --max-time 90 --max-filesize 131072 \
  https://raw.githubusercontent.com/GioNob/ouf-semantic-registry/120eee43c2ff02a204c58363538d60b57b3d6a79/docs/handoffs/commands/OUF_QUALIFY_REMEDIATED_IMAGES_2026-10-06.sh \
  --output "$ouf_task/qualify.sh"
printf '%s  %s\n' 5c47d7c14e260d7ebb1d245dd83476646df61cbb9e378dd00fddb45eb5fa0697 "$ouf_task/qualify.sh" | sha256sum --check --strict &&
bash "$ouf_task/qualify.sh" "$HOME/ouf-remediation-transfer-20261006/ouf-remediation-20261006.zip"
```

Il comando scarica soltanto il codice fissato, non scanner o nuovi database. Codice standalone c51fe31215efac37308ff6fcb9c577ac475a256f/SHA256db95b97cce62a4c3e164d0dad20a8674052dced80ff7e683e84ac21cef925112. L'artefatto e il merge CI sono fissati anche nel loader root; il codice viene letto, verificato e compilato dagli stessi byte stabili. Non sono lette chiavi del VPS.

## Esito atteso e recupero

Output `SEMANTIC_REMEDIATION_BYTE_QUALIFICATION={...}`, entrambe le immagini `bytesVerified:true`, tutti i flag acceptance/runtime/start/import false;0container/scanner. Il report redatto è salvato anche nel file mostrato da `REPORT_REDACTED_SAVED`. Comunicare quell'output; non pubblicare i report privati completi.

La finestra DB48h termina **7 ottobre2026 alle08:45:38Europe/Rome**. Oltre il limite, il wrapper blocca prima dello snapshot; preparare e provare un nuovo pin/scansione/bundle, senza bypass. Se il nuovo snapshot esiste già o un'operazione fallisce, non cancellarlo né forzare la ripetizione: conservare l'evidenza e leggere l'output redatto per un recupero esplicito.

Gli snapshot48/49 e i due candidati fermati restano storici. Nessuna sostituzione, policy installata, publisher acceptance, firma autoritativa VPS, runtime registration o start è implicata da questa operazione.

## Esito operatore ricevuto

Receipt: [SEMANTIC_IMAGE_REMEDIATION_TARGET_PASS_2026-10-06_OPERATOR.json](../handoffs/receipts/SEMANTIC_IMAGE_REMEDIATION_TARGET_PASS_2026-10-06_OPERATOR.json). ZIP trasferito in una nuova cartella, senza sovrascrivere lo ZIP omonimo nella home. Output salvato in `/tmp/ouf-remediation-qualification.lT6Bz9`. Entrambe le immagini bytesVerified=true, 0 Critical/High/Unknown. Adapter conserva 5 Medium; southbound 141 Medium, 17 Low, 4 Negligible. Zero scanner/container/import; acceptance, runtime, start, publisher trust, coverage e verifica crittografica target false. È una qualificazione delle evidenze, non installazione o nuovo scan target. Nessuna prova atomica target aggiunta.

Prossimo lavoro: revisione PET delle componenti custom/native, copertura SBOM e publisher/dossier. Nel workspace di ripresa il pacchetto normativo v1.7 non è disponibile; richiederlo come prescrive handoff §8. Non dedurre complete acceptance da questo PASS e non ripetere la qualificazione.
