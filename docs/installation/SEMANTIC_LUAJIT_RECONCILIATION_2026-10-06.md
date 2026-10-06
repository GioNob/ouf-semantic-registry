# Riconciliazione LuaJIT — 6 ottobre 2026

I fix di CVE-2024-25176, 25177 e25178 sono presenti nelle sorgenti effettivamente compilate della stessa immagine southbound già analizzata. La prova aggiunta nella [CI37447434158](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37447434158), codice `b0a2f825297085dd391efd9bdb001bdafe5fff66`, job112215537016, passa. Otto controlli negativi e sei esecuzioni delle regressioni upstream, con JIT attivo/disattivo, PASS.

La prova non modifica SBOM, CPE, versioni, severità o report. Il risultato Grype originale resta **2Critical/1High/0Unknown** e scannerSeverityThresholdMet=false. Acceptance, publisher trust, copertura accettata e start restano false. Nessuna operazione VPS; snapshot v1 e test esistente preservati.

## Catena delle prove

1. Artifact nativo11397838781: hash dell'intero ZIP, firme dei tre documenti nativi, repository/workflow/ref/merge e codice produttore verificati prima della riconciliazione.
2. Sei blob upstream del commit luajit2 `fbfc558aacd57a54623df0ced4c31a28f81f8ff2` corrispondono per SHA256 ai sei file nei manifesti delle sorgenti compilate; digest dei manifesti corrispondenti ai documenti nativi firmati.
3. Ogni commit di fix è antenato del commit compilato ed è citato dal record CNA bloccato per Git blob. Sono controllate anche le istruzioni del fix nel sorgente corrente, inclusa la rappresentazione del frame evoluta con LJ_FR2.
4. ZIP completo11397709159 scaricato sul runner CI: SHA256 `0614b43d8843b8ebe24b4a6a4d564dfb1d36271b8660e8d0379d147a1db231c0`. Archivio southbound estratto, hash e firma provenance verificati prima dell'importazione nel solo runner usa e getta.
5. Immagine `sha256:516f49278f48c808427d346ad8d1520f60433d071949435774395e6c0ebc29b3`; hash del binario LuaJIT effettivamente eseguito `9eeb150ad8a90d3c71034aa592305c038ade805a6d7ae3f9b2b52a8e8ac726a1`, identico al manifesto.
6. Sei esecuzioni in container senza rete, filesystem read-only, nessuna capability, UID10006, limite memoria128MiB, PID32 e CPU1. Nessun token o volume host passato al container.

| CVE | Report grezzo | Prova sul runtime, JIT on/off |
|---|---|---|
| CVE-2024-25176 | Critical | Riproduttore upstream %g termina normalmente |
| CVE-2024-25177 | High | Riproduttore upstream termina con il previsto errore Lua di ordinamento, intercettato; nessun crash nativo |
| CVE-2024-25178 | Critical | Quattro casi upstream di overflow/handler/coroutine/traceback passano |

Le prove usano il binario di produzione, senza ASan. Sono regressioni funzionali mirate: non dimostrano assenza universale di difetti di memoria. Il fixture25177 contiene un input di fuzzing che nel runtime corrente raggiunge un normale errore di tipo; il wrapper richiede esattamente quel messaggio e rifiuta altri errori, timeout o crash. La prova di presenza della correzione dipende anche dagli hash completi dei sorgenti e dall'ancestry verificata.

## Causa del blocco automatico

Il report conservato usa stock-matcher, namespace nvd:cpe, CPE `luajit:luajit:2.1-20260824`, vincolo `<=2.1 (unknown)`. Il componente compilato è il fork OpenResty luajit2 con snapshot2026 che include i fix del2024; il testo CNA distingue gli snapshot luajit2 precedenti alle correzioni del2024.

L'issue primaria [Anchore Grype2890](https://github.com/anchore/grype/issues/2890#issuecomment-3293513871) descrive lo stesso meccanismo: il testo descrittivo non è un intervallo machine-readable e il match CPE resta finché il catalogo del package non documenta la correzione. Quel caso Alpine fu chiuso dopo l'annotazione secfixes del package. Qui il binario è una build custom, non un APK Alpine; la risoluzione del caso Alpine non concede automaticamente una deroga a questa immagine.

Il lavoro tecnico sulle tre correzioni è ora verificato, e ripetere la stessa ricompilazione non risolve il match. Il seguito concreto è correggere/rendere applicabili i dati di matching upstream oppure valutare esplicitamente un criterio che accetti questa evidenza di fix legata ai byte. Il criterio grezzo corrente resta invariato: questa receipt non approva soppressioni, VEX o override e non autorizza un comando VPS. Copertura completa, publisher trust e dossier coerente coi digest/gateway live restano passaggi distinti.

## Evidenza conservata

Receipt: `docs/handoffs/receipts/SEMANTIC_LUAJIT_RECONCILIATION_2026-10-06_CI.json`. Artifact11404136916: 1990 byte, SHA256 `b46979e6fb7a4790dd96f0fe5b2077a589dda3e3685a56cb9ce80cbdd3946cb4`; scaricato, hash verificato e risultato identico al log CI autenticato. L'output di questa riconciliazione non viene presentato come nuova attestazione firmata: i suoi input nativi e l'immagine sono verificati crittograficamente.

Fonti delle regressioni:
- https://github.com/LuaJIT/LuaJIT/issues/1149
- https://github.com/LuaJIT/LuaJIT/issues/1147
- https://github.com/LuaJIT/LuaJIT/issues/1152#issuecomment-1922461739

Correzione del precedente riepilogo OpenSSL: il run37433261779 esegue quattro suite/sette test PASS. NOTESTS riguarda solo il preparativo FIPS saltato e non il risultato delle suite.
