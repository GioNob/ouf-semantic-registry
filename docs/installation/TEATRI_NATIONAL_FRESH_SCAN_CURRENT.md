# Scansione aggiornata per la Discovery nazionale — 7 ottobre 2026

La scelta dell'utente resta la Discovery nazionale per il file Teatri già profilato: 13 righe, 20 campi. Cinema ha già restituito 8 oggetti in ChatGPT. La nuova scansione aggiorna soltanto le evidenze delle immagini necessarie al ramo provider.

Il database selezionato è `v6.1.10`, costruito il 7 ottobre alle 06:31:48Z; SHA256 dell'archivio `008449eb30e10988569b3bd54eb46158f33187211ba723f41ed9326ccfa1e174`. Il limite di freschezza è il 9 ottobre alle 08:31:48 Europe/Rome. Il pin storico del 5 ottobre è conservato.

Il primo run 37612887792 si è fermato prima della scansione: il qualificatore del vecchio archivio richiedeva un database storico ancora recente. La modalità esplicita `--historical-evidence` separa la verifica di quelle evidenze dalla freschezza attuale. Hash, firme, identità delle immagini, report storici e soglie sono ancora verificati; la ricevuta dichiara `historicalEvidenceOnly=true` e `currentVulnerabilityScanProven=false`. Senza questa opzione il controllo di freschezza rimane obbligatorio. L'archivio originale, il suo hash e le immagini non cambiano. Cinque test del qualificatore PASS, compreso il rifiuto del database scaduto come evidenza attuale.

Run aggiornato: [37613612404](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37613612404), source HEAD `84e91e199892bfda1d116a49f53a9990f61724c7`. Verifica originale, inventario, ricostruzione LuaJIT, piano dossier e download del nuovo database con hash verificato sono riusciti. Scansioni e cinque firme concluse PASS; dettagli del risultato sotto.

Il verificatore indipendente richiede che il pin nel documento firmato coincida con quello approvato e che entrambi i report Grype dichiarino lo stesso build/schema valido. Rifiuta database scaduti, futuri, sostituiti e report discordanti. Sei test PASS. I controlli di freschezza della nuova scansione non sono disattivati.

Passi successivi: completare il readback indipendente del nuovo artifact e delle cinque firme, con ID, hash ZIP e merge commit firmato già fissati. Solo dopo si prepara il comando VPS concreto. Le prove di firma non concedono publisher trust, copertura completa delle dipendenze, accettazione, registrazione runtime o avvio.

Provider nazionale non ancora invocato. Richiesta preparata: CLASS, intent `teatro`, lingue it/en. La versione MCP corrente non espone la richiesta Discovery e la configurazione effettiva del provider non è provata. Conservare candidati fermi, gateway, Cinema, asset/profile Teatri e approvazioni HUMAN/THS; non creare job destinati a fallire.

## Risultato del nuovo producer

Run 37613612404 concluso PASS. Merge commit firmato `00ba8b2ca6caf01902943b6d8d3dba60c00df6a9`. Artifact `11478662099`, 1158875 byte; ZIP SHA256 `a23ee77e6f2e21fc9a7ca1beb144d11f22228cc801693cac5fad47ee30e863ea`, verificato anche sul download tramite connector. Cinque firme verificate nel producer. Adapter: 0 Critical/High/Unknown, 5 Medium; southbound: 0 Critical/High/Unknown, 142 Medium, 18 Low, 4 Negligible. Il nuovo conteggio Medium è conservato, non sovrascritto con quello storico. Il readback indipendente ora seleziona esclusivamente questo artifact e richiede il pin del 7 ottobre. Target ancora da verificare; nessuna accettazione o avvio.
