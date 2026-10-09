# Installer OUF guidato — requisito operativo

Requisito utente5 ottobre2026, chiarito alle06:49:48 Europe/Rome. Stato **SPECIFICATO, NON IMPLEMENTATO**. Installer per configurare e distribuire i moduli dell'ente su macchine amministrate; distinto dai wrapper diagnostici VPS.

## Prerequisito piattaforma

Tutte le macchine di destinazione devono essere **Linux/amd64**. amd64 indica x86-64 e comprende Intel e AMD compatibili; non è una marca CPU. Il wizard rileva e verifica OS/architettura/bitness su ogni macchina, senza chiedere la marca e senza scegliere altre architetture. Non sono richiesti ARM64,32bit o host Windows/macOS. Verifica anche runtime Docker/backend/versione, Python e accesso amministrativo secondo i prerequisiti della release; percorso fisso non equivale a provenienza verificata dell'interprete. Host incompatibile arresta il piano con diagnosi chiara.

## Parametri richiesti all'admin

- Domain name e relativi nomi/endpoints dei servizi.
- Reti e assegnazioni/collegamenti necessari tra macchine e moduli.
- Inventario delle macchine e assegnazione di ciascun modulo alle macchine previste.
- Scelte ulteriori indispensabili al profilo e ai contratti PET, distinguendo installazione nuova e ambiente esistente.

Derivare dai dati una topologia coerente, endpoint e connessioni tra moduli; non presumere che tutti i moduli siano sullo stesso host. Verificare componenti obbligatori, dipendenze, risoluzione/raggiungibilità tra nodi, reti/porte senza conflitti e confini di ownership/accesso. Non chiedere all'admin dettagli che si possono derivare o rilevare affidabilmente. Mostrare riepilogo, rilevamenti e piano prima delle mutazioni.

Password/chiavi/credential restano locali e privati; niente chat, argomenti pubblici o log. Preservare configurazione e credenziali esistenti; nessuna rigenerazione/reinstallazione implicita. Parametri non sensibili e riferimenti privati sono gestiti separatamente.

## Artefatti e applicazione

Convalidare input e topologia contro schema/PET/matrice release Linux/amd64. Selezionare script e immagini pinned della release per ogni modulo e macchina. Generare manifest, parametri, wrapper e checksum dalla stessa build e dagli input convalidati; conservarli come artefatti versionati. Native CI verifica ogni topologia/profilo dichiarato supportato. Il rilevamento precede il sigillo: dopo la generazione i bytes/pin non si modificano arbitrariamente durante acceptance.

Distinguere dry-run/piano, prepare/stage e apply, con ordine dipendenze distribuite e recovery per nodo. Riconoscere receipt e stato già presenti, evitando side-effect duplicati. Non rifare pipeline Cinema/Teatri già testate. Verifiche fallite arrestano la fase interessata con diagnosi redatta. Acceptance/firma/start/migrazione/consumer activation rispettano conferimenti e PET/handoff; risposte al wizard non concedono automaticamente autorità ulteriori.

## Criteri di completamento

Un admin fornisce domini/reti/distribuzione moduli, vede un piano multi-macchina verificabile e ottiene artefatti coerenti e riproducibili. Tutti i target superano il prerequisito Linux/amd64. Test/documentazione coprono installazione nuova, ambiente esistente, topologia multi-macchina, parametri incompatibili e recovery dopo interruzione senza rigenerazione segreti né replay side-effect. Host Intel/AMD64 compatibili ricevono la stessa variante amd64.

Debito corrente: CI verifica e testa i wrapper presenti; generazione automatica completa pin/build e installer guidato non sono ancora realizzati. Nessun R-INSTALL PASS deriva da questa specifica. Chiarimento06:49:48 prevale sulle ipotesi multiarch precedenti.
