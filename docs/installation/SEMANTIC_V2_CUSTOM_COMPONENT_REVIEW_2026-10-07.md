# Revisione dei componenti custom e del dossier isolato v2

Questa revisione riguarda esclusivamente lo ZIP v2 SHA256 2cdd7a73c1fc2a710f1e6604eb6cab2988492e4c45b5252defffa9832b91d9d0, già verificato sul VPS. Le immagini restano adapter sha256:62e066bd021f386291f5de21ce0e1f9e67904a74b4146326070c7784493ad320 e southbound sha256:d4c47bbeca75d94e2231e17ca14552885b7b339a5f33dbace411e275c79ded04.

| Componente o vincolo | Prove disponibili | Limite che resta aperto |
|---|---|---|
| OpenResty 1.31.6.1 | Commit upstream bc8bf89488f2d02572389158533b3f85ca0ded7f; 45 archivi bloccati; sorgenti compilate e moduli API7 misurati; configurazione legata al vero ELF; test TLS/OIDC, shdict e gRPC della build originale | Snapshot di sviluppo upstream, dichiarato nel lock. La firma del builder non è approvazione vendor della release |
| zlib 1.3.2.1-motley | Commit df84af25dc1942490e1d1c899a07619152a46148; package custom con versione esplicita; test compressione e suite upstream nella build originale | Snapshot upstream non rilasciato. Il package APK usa una chiave generata nella build: non è un publisher produttivo preapprovato |
| OpenSSL 3.4.8 OpenResty | Sorgente bloccato e port esplicito della patch callback; quattro suite/sette test PASS; Nginx collegato alle librerie nel prefisso OpenResty | Build custom con patch portata: richiede revisione e proprietà del mantenimento distinta da OpenSSL di sistema Ubuntu |
| LuaJIT 2.1.1787558776 | Versione osservata separata dal tag; sorgente upstream fbfc558aacd57a54623df0ced4c31a28f81f8ff2; binari e precedenti regressioni JIT on/off conservati | Il supplemento originale non misurava il file generato jit/vmdef.lua. La riconciliazione ricostruisce l'output da 246 sorgenti esatti prima di associarlo alla stessa identità LuaJIT |
| PCRE 8.45 e Brotli 1.1.0 ereditati | Byte delle librerie misurati; per Brotli entrambe le funzioni ELF di versione lette senza esecuzione; scansione dell'inventario esteso | La provenienza del sorgente della build ereditata non è dimostrata dalla sola versione o dagli hash finali |
| LuaRocks e script OpenResty | Tutte le 75 versioni LuaRocks originali conservate; associazioni MD5 dei manifesti con SHA256 installati; 188 file Lua distinti associati ai sorgenti | MD5 è usato soltanto per associazioni, non come prova crittografica upstream. Identità inventariata e assenza di match non garantiscono copertura universale degli advisory |
| WASM | Omissione esplicita nel lock e nella compilazione; rimossa la vecchia dipendenza Wasmtime vulnerabile | Compatibilità del caso d'uso che richieda WASM non provata. Nessuna acceptance funzionale universale implicita |
| Builder GitHub Actions | Workflow/repository/ref/commit fissati, runner hosted obbligatorio, provenance e SBOM verificate sul VPS | Autenticazione dei byte e del builder distinta dall'approvazione di tutti i publisher upstream e dei package custom |

## Contratto del dossier isolato

Il nuovo planner legge le configurazioni effettive dei due archivi, usa il manifest e confronta SHA256 della configurazione con l'ID dell'immagine. Registra Entrypoint/Cmd/WorkingDir/User e soltanto i nomi delle variabili d'ambiente. Non legge dati target o segreti, non chiama Docker e non importa immagini.

I nuovi ruoli usano ciascuno il proprio ID locale di immagine. Il gateway live conserva la sua immagine; il planner non riusa lo stager storico che obbliga southbound.image=gateway_image['Id']. Non propone pull o fallback a tag, porte pubblicate o start. Lo stato previsto è CREATED_STOPPED, con restart=no, privileged=false e capDrop=ALL; UID/GID, budget di risorse, mount privati, identità TLS e reti devono provenire da un nuovo intento verificato.

Il dossier non è ancora un manifest operativo: non dichiara di aver osservato il target, aggiornato le receipt private o prenotato indirizzi. Il futuro percorso deve ricostruire le receipt coerenti con i nuovi digest, verificare proprietà/assenza di occupanti delle reti e deny-guard corrente, usare nomi nuovi e controllare l'intera creazione con readback indipendente. Non cambiare i digest negli intenti storici né riutilizzare i vecchi container per far passare un confronto.

## Condizioni di accettazione e autorità

Importazione, creazione fermata e avvio sono azioni distinte. La verifica delle firme e un dossier plan-only non conferiscono authority o acceptance. Restano necessarie revisione publisher/custom e funzionalità, freschezza del database, evidenza completa di configurazione/OCI/trasporto/generazione/rootfs e raccordo osservazione-mandato descritto nel piano acceptance esistente. Nessuna firma con le chiavi di autorità, migrazione di runtime, link di consumer o avvio è autorizzato da questo documento.

La precedente preparazione di private trust policy è conservata: consumerLinked=false e roleSigningAuthorized=false. Il successo del byte qualifier o dello scanner non cambia questi campi. Gate 48 storico, gate 49 aperto, Cinema/Teatri e il distinto problema HTTP503 restano preservati.

Il pin del database originale scade il 7 ottobre 2026 alle 08:45:38 Europe/Rome. I report restano evidenze storiche dopo la scadenza; un successivo controllo di admission deve usare un pin e scansioni freschi, senza ignorare l'età. Nessuna dichiarazione di copertura completa o startGranted è prodotta qui.
