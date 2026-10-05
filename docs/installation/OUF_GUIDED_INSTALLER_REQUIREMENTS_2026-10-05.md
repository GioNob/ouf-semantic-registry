# Installer OUF guidato — requisito operativo

Requisito utente5 ottobre2026 alle06:48:20 Europe/Rome: software di installazione che interroga l'admin e seleziona script e valori corretti per la piattaforma dell'ente. Stato **SPECIFICATO, NON IMPLEMENTATO**. Non confondere i wrapper di verifica amministrativa VPS con l'installer definitivo.

## Rilevamento e scelte

Rilevare automaticamente OS, architettura, bitness, runtime Docker/backend/versione e prerequisiti Python/privilegi. Normalizzare x86_64→linux/amd64 e aarch64→linux/arm64 solo su host Linux. amd64 è x86-64, utilizzabile con Intel e AMD compatibili; non scegliere in base alla marca. ARM64,32bit e target Windows/macOS non sono implicitamente supportati; un Docker Linux VM non equivale a supporto nativo host. La matrice corrente provata è linux/amd64 sul lab; aggiungere altre piattaforme solo dopo immagini, native CI e procedure di installazione convalidate.

Chiedere solo scelte che non si rilevano affidabilmente: installazione nuova o ambiente esistente, profilo/componenti, domini/issuer/tenant identificativi, reti/porte e storage richiesti dai contratti PET, eventuale target differente dall'host. Mostrare i valori rilevati e il piano prima delle mutazioni. Password/chiavi e credential restano locali e privati; non passarli nella chat, negli argomenti pubblici o nei log. Preservare credenziali/config già esistenti; nessuna rigenerazione/reinstallazione implicita.

## Selezione degli artefatti e rilascio

Validare gli input contro schema e matrice supportata. Selezionare script/versioni e immagini con piattaforma esatta; verificare disponibilità e dipendenze senza fallback arbitrario. Generare manifest, parametri, wrapper e checksum dalla stessa release/build e dai valori convalidati; conservarli come artefatti versionati verificabili. Eseguire test/parity e native CI per ogni combinazione supportata. Dopo la generazione i bytes/pin sono immutabili: il rilevamento precede il sigillo, non ne modifica i parametri durante acceptance.

Distinguere dry-run/piano, prepare/stage e apply. Operazioni ripetibili devono riconoscere stato e receipt già presenti; niente replay di pipeline Cinema/Teatri o scritture side-effect duplicate. Verifiche fallite arrestano la fase interessata con diagnosi redatta. Avvio/acceptance/firma/migrazione e attivazione consumer rispettano sempre le autorizzazioni e i confini dei PET/handoff; le risposte al wizard non sostituiscono automaticamente i conferimenti necessari.

## Criteri di completamento

Un admin su piattaforma supportata può fornire scelte minime, vedere rilevamenti e piano, ottenere artefatti con parametri coerenti e riprendere dopo un'interruzione senza rigenerare segreti o rifare side-effect. Host Intel/AMD64 ricevono la stessa variante amd64 quando compatibili; ARM64 passa una matrice indipendente oppure riceve unsupported esplicito. Preflight copre /usr/bin/python3, Docker/backend/versione, accesso privilegiato limitato e incongruenze host/immagine. Test di integrazione e documentazione riproducono almeno installazione nuova, ambiente esistente e recovery.

Debito precedente confermato: CI oggi testa/verifica i wrapper presenti; generazione automatica completa dei pin a ogni build e installer generalizzato non sono ancora completati. Nessun supporto aggiuntivo o R-INSTALL PASS è dichiarato da questo requisito.
