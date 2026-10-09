# Evidenze v2 riconciliate e dossier isolato — verifica VPS

La verifica precedente dell'operatore è PASS e resta conservata in /home/oufadmin/ouf-extended-v2.tXIpQD/reports. Il nuovo archivio aggiunge la riconciliazione esatta di jit/vmdef.lua e il dossier plan-only delle due immagini. Le immagini, lo ZIP v2 originale e i report precedenti restano identici. Questa procedura non importa immagini, non usa sudo o Docker e non avvia servizi.

Produttore: CI 37573769866, codice 621e9b6ba6d0bcc479893de080c932f3767701d0, merge firmato 27965d0a5c1997490b1e9542eb1e3d662523ee15. Archivio 11460989205: 1158051 byte, SHA256 479b761111fd20e192f8f195349107ee620b9b4f8c53453fc4557fe5a4d44797. Le scansioni offline e le cinque firme PASS; entrambe le immagini hanno 0 Critical/High/Unknown. La prova ricostruisce il generatore dai 246 file sorgente che corrispondono al manifesto originale: output SHA256 f634b76cb7937c403126c6d4904e7b4969de478c936b5ad9dba91d0a5b074a53, identico al file installato. Nessun payload dell'immagine è stato eseguito per questa riconciliazione.

Il dossier registra startup/UID nominale dei byte reali (adapter 10006:10006, southbound apisix), esclusivamente nomi delle variabili d'ambiente e ID immagine distinti. Non osserva il VPS e non sostituisce nuove receipt TLS/trust/launch/network o un manifest completo di creazione. Publisher trust, copertura universale advisory, acceptance e start restano aperti; la [revisione custom](/docs/installation/SEMANTIC_V2_CUSTOM_COMPONENT_REVIEW_2026-10-07.md) descrive i limiti.

## Windows PowerShell

Scaricare [extended-v2-dependency-evidence-37573769866.zip](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37573769866/artifacts/11460989205) nella cartella indicata dall'operatore: C:\utenti\giovannino\download. Usare la chiave SSH già funzionante. Il controllo SHA256 riguarda l'identità del nuovo archivio.

```powershell
& {
    $oufEvidence = "C:\utenti\giovannino\download\extended-v2-dependency-evidence-37573769866.zip"
    $oufKey = "C:\Users\NOBILI\Downloads\ouf--netcup"
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $oufEvidence).Hash -ne "479b761111fd20e192f8f195349107ee620b9b4f8c53453fc4557fe5a4d44797") {
        throw "Hash delle evidenze diverso: trasferimento interrotto."
    }
    ssh -i "$oufKey" oufadmin@62.83.33.202 "mkdir -m 700 /home/oufadmin/ouf-reconciled-evidence-transfer-20261007-37573769866"
    if ($LASTEXITCODE -ne 0) { throw "Cartella non creata: comunicare l'errore." }
    scp -i "$oufKey" "$oufEvidence" oufadmin@62.83.33.202:/home/oufadmin/ouf-reconciled-evidence-transfer-20261007-37573769866/evidence.zip
    if ($LASTEXITCODE -ne 0) { throw "Trasferimento non completato." }
}
```

## Sessione SSH sul VPS

Il verificatore richiede esplicitamente la nuova prova LuaJIT e il dossier. Verifica il nuovo ZIP, il vecchio ZIP v2 intero, i binding dei report e le cinque firme fissando workflow/merge/ref e runner hosted. Usa gh 2.102.0 già installato privatamente. Il blocco termina al primo errore; i risultati vanno in una cartella nuova con directory 700/file 600.

```bash
(
set -eu
umask 077
oufVerifyDir=$(mktemp -d /home/oufadmin/ouf-reconciled-v2.XXXXXX)
curl --fail --location --silent --show-error \
  https://raw.githubusercontent.com/GioNob/ouf-semantic-registry/15c421baaac9b1fc6c4de903254aac4cb09e1fc9/tools/verify_semantic_extended_evidence.py \
  -o "$oufVerifyDir/verify.py"
printf '%s  %s\n' 5f3a996c9186826ce186af9a73d7e52f5054f76872fc0bf0c0d72bdad2c85ddf "$oufVerifyDir/verify.py" | sha256sum -c -
python3 -I -B "$oufVerifyDir/verify.py" \
  --sidecar /home/oufadmin/ouf-reconciled-evidence-transfer-20261007-37573769866/evidence.zip \
  --sidecar-sha256 479b761111fd20e192f8f195349107ee620b9b4f8c53453fc4557fe5a4d44797 \
  --original-bundle /home/oufadmin/ouf-remediation-transfer-20261006-v2/ouf-remediation-20261006-v2.zip \
  --source-merge-commit 27965d0a5c1997490b1e9542eb1e3d662523ee15 \
  --require-generated-luajit --require-isolated-dossier \
  --gh /home/oufadmin/ouf-gh-2.102.0.PNoFbF/gh_2.102.0_linux_amd64/bin/gh \
  --output "$oufVerifyDir/reports"
)
```

Comunicare le cinque righe FIRMA_EXTENDED_PASS, OUF_EXTENDED_TARGET_CRYPTO=PASS e OUF_EXTENDED_REPORT_DIR. Non inviare il contenuto di chiavi o credenziali. Il programma conserva automaticamente receipt e verifiche; non occorre spostare i report originali.

## Stato e lavoro successivo

La CI verifica il nuovo archivio scaricabile; la sua esecuzione non è prova di verifica sul VPS. Dopo il readback dell'operatore, completare il collegamento target con nuovi intenti e receipt coerenti coi digest v2, mantenendo il gateway live e i candidati storici. Non usare lo stager storico gateway-bound per queste immagini.

La freschezza del database originale termina il 7 ottobre 2026 alle 08:45:38 Europe/Rome. Questa verifica crittografica conserva prove e non concede admission/start; qualunque admission successiva alla scadenza richiede scansioni e pin freschi. Niente bypass. Le revisioni private di authority/consumer/complete creation e i gate del piano acceptance rimangono distinti.
