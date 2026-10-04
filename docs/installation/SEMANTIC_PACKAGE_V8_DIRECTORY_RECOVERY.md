# Recovery del tentativo package v8 bloccato in plan

## Stato corrente — recovery ESEGUITA/PASS

Output operatore: inspect/repair PASS, source0755→0700 sul package121542, seguito da plan/apply/verify PASS. Sorgenti26 invariati, proprietà e inode preservati; nessuna chiave/firma/provider o avvio. [Evidenza](../handoffs/receipts/SEMANTIC_LOCAL_PRODUCERS_V8_RECOVERY_PASS_2026-10-04_OPERATOR.json). La descrizione del blocco sotto è storica. Recovery root123655; non ripetere recovery né staging sul package esistente.

Per nuovi package usare [il wrapper canonico completo corretto](../handoffs/commands/OUF_STAGE_LOCAL_PRODUCERS_PACKAGE_V8_2026-10-04.sh), senza concatenare comando errato e recovery. Questa revisione di bootstrap non è stata eseguita sul VPS; permessi corretti verificati nei test con GNU install e umask022/077.

## Evidenza e causa

L’operatore ha eseguito §30. Root riportato: `/etc/ouf/deploy-snapshots/semantic-local-producers-package-20261004-121542`; sorgenti Gateway `7ded9df0c74c6db919c7a68d4c75ab2c132dea53`. Wrapper SHA256 `f1c2e775d4882916e0840fe5ab9965fdf4477d984dd4dd5b1e0f5a7a2ea9d5bb`, manifest SHA256 `a1b11fbfb9d701101f2efa1048c7f99a54f123ed1f1b71f480ffcd883c0e560b`:28 checksum OK (wrapper, manifest,26 sorgenti). Esito: **ESEGUITO/BLOCKED MODE=plan REASON=PRIVATE_PACKAGE_DIRECTORY_REQUIRED**. apply/verify non raggiunti nel wrapper set-e; nessuna ricevuta PASS fornita. Non dichiarare source custody o staging acceptance completati.

La causa del wrapper è riprodotta con GNU install reale: `install -d -m0700 .../source/scripts .../source/tools` crea la directory intermedia source con0755, mentre le directory finali sono0700. I test precedenti creavano source esplicitamente con0700 e non coprivano il wrapper. La metadata concreta del VPS non è ancora ispezionata indipendentemente: la recovery controlla esattamente questa precondizione e si blocca se proprietari/modi sono diversi.

Il validatore di package rimane invariato e richiede tutte le quattro directory root:root0700. Nessun allentamento a0755, chmod ricorsivo o normalizzazione automatica di proprietari inattesi.

## Intervento storico — §31 ESEGUITO/PASS, non ripetere

[Wrapper recovery](../handoffs/commands/OUF_RECOVER_LOCAL_PRODUCERS_PACKAGE_V8_DIRECTORY_2026-10-04.sh), SHA256 `2d770d268cf5a9e164d6559b60c3246500009d80ab076838f9fab4387df94a5d`. Helper Gateway `7941098e4253a50916542471328f556d979436fe`: `scripts/repair_semantic_local_producers_package_directory.py`, SHA256 `116efd276852fc184479017ab853fb5ccce5c30667489771f097da4f505dbac4`.

Il wrapper:
1. Scarica e verifica l’helper pinned, lo custodisce root0600 in un nuovo snapshot privato di recovery.
2. Riporta mode/UID/GID delle quattro directory del root già creato.
3. Esegue inspect, senza scrivere nel package originale: esige root/scripts/tools0700, source0700 o0755, tutti root:root; manifest originale pinned;26 sorgenti private0600 e hash esatti; ricevuta assente anche come symlink.
4. Esegue repair: soltanto source0755→0700 tramite fd/O_NOFOLLOW/fchmod e fsync; se già0700 è no-op. Rilegge metadata, manifest e tutti i byte, senza modificare owner o sorgenti.
5. Sullo **stesso root e sulle stesse sorgenti originali** completa plan/apply/verify dello stager v8 già presente, sourceCommit7ded9df e manifest originale. apply crea la prima ricevuta; verify la verifica senza ripararla.

Non è un replay di apply: il primo tentativo è stato bloccato in plan. Qualunque ricevuta presente, anche parziale o inattesa, impedisce la recovery. Se il comando si blocca, riportare l’output; non cancellare ricevute o root e non rieseguire il wrapper originario. fsync fallito non attesta correzione durabile; l’assenza di receipt consente soltanto nuova ispezione del modo, non assunzioni di successo.

La sola mutazione autorizzata nel package preesistente è il permesso di source. Nessuna regola/unit/container, registrazione runtime, authority, chiave o firma. I producer non vengono eseguiti. Il completamento dello staging conserva i contatori zero e startAuthorized=false; non è accettazione target o release acceptance.

## Correzione per i futuri package

[Wrapper futuro corretto](../handoffs/commands/OUF_STAGE_LOCAL_PRODUCERS_PACKAGE_V8_FIXED_2026-10-04.sh) crea esplicitamente root, source, source/scripts e source/tools con install -d -m0700 -o root -g root. Non usarlo per sostituire il root bloccato121542: per quel tentativo usare §31. Il wrapper eseguito originale resta documentato come ESEGUITO/BLOCKED e deprecato; il vecchio commit immutabile conserva byte e checksum di esecuzione.

## Verifiche

8 nuovi test: reale errore GNU install e conseguente denial del validatore; recovery seguito da plan/apply/verify originale; variante futura corretta con umask022 e077; receipt/symlink incerti; sorgente/manifest cambiati; modo/owner/symlink inattesi; hardlink sorgente; source già privata senza mutazione; fsync fallito senza receipt. Le verifiche dei modi e dei file sono reali; la metadata con GID estraneo è simulata nel test perché scratch supporta soltanto UID/GID root.

Locale165 test:162PASS/3Docker skip. CI e commit della correzione sono riportati nel checkpoint corrente di handoff, roadmap, manuale e sprint. Il package target continua a usare il commit7ded9df, perché i suoi26 file non sono modificati dalla correzione del wrapper e dall’helper di recovery.

## Passo successivo

Solo dopo l’output §31 aggiornare receipt di staging, stato del comando e checkpoint. Poi provisioning esplicito di authority e mandati di accettazione per immagini/volumi target. §29 v7 ESEGUITO/PASS resta preservato. PR draft, nessun merge, avvio, replay o reboot implicito. Il percorso ingestion interno MCP/THS/ACTIVE/Ingestion/UDP resta aperto e non cambia con questa recovery.
