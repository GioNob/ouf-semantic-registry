# Verifica delle evidenze estese sul VPS — 6 ottobre 2026

Le immagini v2 già trasferite e firmate restano identiche. Questa procedura aggiunge un archivio di sole evidenze (1154855 byte), controlla i suoi byte e le cinque firme e conserva un nuovo report privato. Non usa sudo, Docker, import, scanner o avvio di servizi. I report originali e lo snapshot v2 rimangono conservati.

Produttore: [CI 37508392335](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37508392335), codice cea9ffd938d6a8780369baf9736cb4042c0afb5e, merge firmato e56a20aae8f8869bc760fd3b048c152680c1b854. Le due scansioni offline mantengono 0 Critical/High/Unknown. Gli ELF rilevati sono 111 nell'adapter e 810 nel southbound, tutti associati a identità di package. Il southbound esteso contiene 238 package, 16 identità dei moduli statici, 188 file Lua distinti legati a sorgenti e tutte le 75 versioni LuaRocks originali. La duplicazione di file tra sorgenti conserva tutte le associazioni dimostrate; non determina quale modulo verrà caricato.

Rimane esplicito il file generato LuaJIT jit/vmdef.lua, non presente nel manifesto dei sorgenti prima della compilazione. La sua riconciliazione generatore/output resta aperta. I manifesti LuaRocks legano i file installati tramite MD5 e conservano i loro SHA256, ma non dimostrano da soli la provenienza upstream. Le identità e i risultati del database non equivalgono a copertura universale degli advisory.

Publisher trust, copertura completa, acceptance, runtime registration e start restano false. La verifica delle firme è distinta dall'accettazione dei componenti custom. Il database scade il 7 ottobre alle 08:45:38 Europe/Rome; non estendere la validità o bypassare la freschezza.

## 1. Download e trasferimento da Windows PowerShell

Scaricare [extended-v2-dependency-evidence-37508392335.zip](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37508392335/artifacts/11433181340) nei Download. Se il browser aggiunge un suffisso, usare il nome esatto nel primo comando. Non rinominare altri ZIP per sostituirlo. Copiare soltanto i comandi, senza il prompt PS o l'output.

```powershell
& {
    $oufEvidence = "C:\Users\NOBILI\Downloads\extended-v2-dependency-evidence-37508392335.zip"
    $oufKey = "C:\Users\NOBILI\Downloads\ouf--netcup"
    if (!(Test-Path -LiteralPath $oufEvidence)) { throw "Archivio delle evidenze non trovato." }
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $oufEvidence).Hash -ne "d74b1e6406d013272806465b722903a082d63e171948a37e666ae59c45c32d87") {
        throw "Hash delle evidenze diverso: trasferimento interrotto."
    }
    ssh -i "$oufKey" oufadmin@62.83.33.202 "mkdir -m 700 /home/oufadmin/ouf-extended-evidence-transfer-20261006-37508392335"
    if ($LASTEXITCODE -ne 0) { throw "Cartella non creata: conservare e comunicare l'errore." }
    scp -i "$oufKey" "$oufEvidence" oufadmin@62.83.33.202:/home/oufadmin/ouf-extended-evidence-transfer-20261006-37508392335/evidence.zip
    if ($LASTEXITCODE -ne 0) { throw "Trasferimento non completato." }
}
```

## 2. Verifica nella sessione SSH del VPS

Il verificatore è fissato al commit c89e095484ac50b6ec3604879df9c3618c74974a e al suo SHA256. Usa il gh 2.102.0 portatile già verificato dall'operatore. Ogni esecuzione crea una cartella privata nuova, senza sostituire i risultati precedenti. Se un comando fallisce, il blocco termina e non stampa PASS.

```bash
(
set -eu
umask 077
oufVerifyDir=$(mktemp -d /home/oufadmin/ouf-extended-v2.XXXXXX)
curl --fail --location --silent --show-error \
  https://raw.githubusercontent.com/GioNob/ouf-semantic-registry/c89e095484ac50b6ec3604879df9c3618c74974a/tools/verify_semantic_extended_evidence.py \
  -o "$oufVerifyDir/verify.py"
printf '%s  %s\n' e109b4d4ac1e47fa33fba021ca47d3a2feb85b90d5a039b1442a02d1ac595db7 "$oufVerifyDir/verify.py" | sha256sum -c -
python3 -I -B "$oufVerifyDir/verify.py" \
  --sidecar /home/oufadmin/ouf-extended-evidence-transfer-20261006-37508392335/evidence.zip \
  --sidecar-sha256 d74b1e6406d013272806465b722903a082d63e171948a37e666ae59c45c32d87 \
  --original-bundle /home/oufadmin/ouf-remediation-transfer-20261006-v2/ouf-remediation-20261006-v2.zip \
  --source-merge-commit e56a20aae8f8869bc760fd3b048c152680c1b854 \
  --gh /home/oufadmin/ouf-gh-2.102.0.PNoFbF/gh_2.102.0_linux_amd64/bin/gh \
  --output "$oufVerifyDir/reports"
)
```

Comunicare le cinque righe FIRMA_EXTENDED_PASS, OUF_EXTENDED_TARGET_CRYPTO=PASS e OUF_EXTENDED_REPORT_DIR. Non inviare chiavi, passphrase o credenziali. I cinque nuovi risultati crittografici e target-receipt.json sono già conservati, con directory 700 e file 600.

## Condizioni per il lavoro successivo

La verifica sul VPS è un'azione dell'operatore: la CI non prova di averla eseguita. Occorrono inoltre la riconciliazione del file generato, la revisione dei componenti custom/publisher e della scelta funzionale Wasm, e un percorso isolato per i digest v2. Lo stager gateway esistente lega il southbound all'immagine del gateway live e non è adatto a questi nuovi digest. Non cambiare il gateway live, i candidati storici o Cinema/Teatri per soddisfare quel controllo.
