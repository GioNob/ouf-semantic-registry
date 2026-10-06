# Verifica byte del nuovo bundle v2 sul VPS — 6 ottobre 2026

La nuova CI [37448782226](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37448782226) supera build, TLS/OIDC, shared-dict, gRPC e scansione completa: **0 Critical / 0 High / 0 Unknown**, anche nel supplemento nativo. La verifica indipendente [37450055158](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37450055158) scarica lo ZIP pubblicato da Actions, ne verifica hash e firme e lo qualifica con lo stesso comando standalone v2: PASS.

Questi passi creano una nuova cartella di trasferimento sotto /home/oufadmin e lo snapshot privato /etc/ouf/deploy-snapshots/semantic-image-remediation-20261006-v2. L'ambiente di test e lo snapshot v1 restano preservati. Il qualificatore legge e conserva evidenze: zero Docker/import/scanner sul VPS, nessuna runtime registration o autorizzazione di avvio.

**1. Sul PC: scarica il nuovo ZIP completo.**

Apri [artifact11406755583](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37448782226/artifacts/11406755583), nome image-remediation-alpine-ubuntu-source-fixed-37448782226. Salvalo nei Download come **ouf-remediation-20261006-v2.zip**. Non usare l'artifact evidence piccolo o lo ZIP v1 già trasferito.

Dimensione: 230675888 byte; SHA256:
```text
2cdd7a73c1fc2a710f1e6604eb6cab2988492e4c45b5252defffa9832b91d9d0
```

**2. In PowerShell sul PC: verifica e trasferisci.**

Copia soltanto i comandi, senza il prefisso PS o il prompt Linux. La cartella remota deve essere nuova: se esiste già, il comando si ferma; non forzare una sovrascrittura.

```powershell
$oufZipV2 = "C:\Users\NOBILI\Downloads\ouf-remediation-20261006-v2.zip"
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $oufZipV2).Hash.ToLowerInvariant() -ne "2cdd7a73c1fc2a710f1e6604eb6cab2988492e4c45b5252defffa9832b91d9d0") { throw "SHA256 diverso: trasferimento interrotto." }
ssh -i "C:\Users\NOBILI\Downloads\ouf--netcup" oufadmin@62.83.33.202 "mkdir -m 700 /home/oufadmin/ouf-remediation-transfer-20261006-v2"
if ($LASTEXITCODE -ne 0) { throw "Cartella v2 non creata: fermati senza sovrascrivere file." }
scp -i "C:\Users\NOBILI\Downloads\ouf--netcup" "$oufZipV2" oufadmin@62.83.33.202:/home/oufadmin/ouf-remediation-transfer-20261006-v2/ouf-remediation-20261006-v2.zip
if ($LASTEXITCODE -ne 0) { throw "Trasferimento non completato." }
```

Il prompt della passphrase della chiave è quello già utilizzato nel trasferimento precedente.

**3. Collegati al VPS.**

Da PowerShell:
```powershell
ssh -i "C:\Users\NOBILI\Downloads\ouf--netcup" oufadmin@62.83.33.202
```

**4. Nella shell Linux del VPS: esegui una sola volta il wrapper v2 fissato.**

```bash
ouf_task=$(mktemp -d)
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 --max-time 90 --max-filesize 131072 \
  https://raw.githubusercontent.com/GioNob/ouf-semantic-registry/9db48efa8eb65f3d25aa6a0b58203cf7f644ca34/docs/handoffs/commands/OUF_QUALIFY_REMEDIATED_IMAGES_V2_2026-10-06.sh \
  --output "$ouf_task/qualify-v2.sh"
printf '%s  %s\n' 8e58a37aa91d24c27299fe19a8351535501a3c9c8c93aa7a353fe58fe3c033d2 "$ouf_task/qualify-v2.sh" | sha256sum --check --strict &&
bash "$ouf_task/qualify-v2.sh" "$HOME/ouf-remediation-transfer-20261006-v2/ouf-remediation-20261006-v2.zip"
```

Il codice standalone è fissato al commit 1ef1d7abdbc6b2b879e57f3c09eaa5fe18f18ef6, SHA256 f9634d518f6812a33953cf64f25a6217a9438d813379823cb69ffb39d697bc58; il merge produttore è 0a1b4460c52c74cefe806286f043f71cbf5a5647. Il wrapper verifica la freschezza del DB e richiede almeno 4 GiB liberi prima dello snapshot. Verifica hash/archivi/config/rootfs, tutti i report e il supplemento nativo ricalcolato dai byte. Crea directory root 700 / file root 600; non legge chiavi del VPS e non estrae file nelle directory applicative.

**5. Conserva e comunica l'output redatto.**

Esito atteso SEMANTIC_REMEDIATION_BYTE_QUALIFICATION con schema v2, entrambe le immagini bytesVerified=true, nativeEvidenceByteVerified=true, nativeEvidenceRetained=true. SourceArtifactSha256 deve essere 2cdd7a73c1fc2a710f1e6604eb6cab2988492e4c45b5252defffa9832b91d9d0. Adapter5Medium; southbound141Medium/18Low/4Negligible; Critical/High/Unknown tutti zero. Container/scanner/import zero; publisher trust, copertura accettata, target crypto, acceptance/runtime/start false.

Il percorso REPORT_REDACTED_SAVED indica il report riassuntivo da conservare. Incolla quel riepilogo; i report completi sono privati nello snapshot. Il PASS VPS v2 non è ancora stato osservato: questa guida è il passo operatore pronto, non una receipt di esecuzione.

La finestra del DB termina **7 ottobre 2026 alle 08:45:38 (Europe/Rome)**. Oltre il limite la procedura blocca: occorrono nuovo pin/scansione/bundle, senza bypass. Se lo snapshot v2 esiste già o compare BLOCKED, conserva l'evidenza e il report; non cancellare lo snapshot o forzare una ripetizione.

Dopo il PASS byte v2 restano revisione di copertura completa/publisher trust e dossier coerente coi nuovi digest/gateway live prima di importazione, registrazione o avvio. Gli snapshot storici 48/49, i candidati fermati e Cinema/Teatri restano preservati.
