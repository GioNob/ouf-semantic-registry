> 7 ottobre: riconciliazione LuaJIT vmdef.lua e dossier isolato PASS in [CI 37573769866](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37573769866). Il generatore è ricostruito da 246 file sorgente esattamente misurati; l'output coincide con il file installato. Zero file ELF e zero Lua OpenResty non associati nell'ambito misurato. Nuove scansioni offline: 0 Critical/High/Unknown. Cinque firme e [readback indipendente 37574177780](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37574177780) PASS, 32 test. Le immagini v2 non cambiano.

> La precedente verifica VPS delle evidenze estese è PASS e preservata; il nuovo archivio firmato, che include prova generata e dossier, attende verifica VPS. [Receipt corrente](/docs/handoffs/receipts/SEMANTIC_RECONCILED_DEPENDENCY_EVIDENCE_2026-10-07_CI.json), [comandi VPS](/docs/installation/SEMANTIC_RECONCILED_EVIDENCE_V2_TARGET_2026-10-07.md), [revisione custom/publisher](/docs/installation/SEMANTIC_V2_CUSTOM_COMPONENT_REVIEW_2026-10-07.md). Il dossier è plan-only: target bindings/private receipts, authority/consumer/complete creation, publisher trust e acceptance restano aperti. Le precedenti note di vmdef.lua non riconciliato sono storiche.

---

> 7 ottobre 2026, 06:46:39 Europe/Rome: verifica delle cinque firme del sidecar sul VPS PASS secondo l'output dell'operatore. Risultati conservati in /home/oufadmin/ouf-extended-v2.tXIpQD/reports. [Receipt operatore](/docs/handoffs/receipts/SEMANTIC_EXTENDED_EVIDENCE_TARGET_2026-10-07_OPERATOR.json). Nessuna importazione o modifica del runtime. Restano riconciliazione vmdef.lua, revisione custom/publisher/Wasm e percorso isolato dei nuovi digest. La precedente indicazione di verifica VPS in attesa è ora storica.

> Aggiornamento: [CI 37508392335](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37508392335) e [readback indipendente 37509074379](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37509074379) PASS. Un archivio separato di evidenze estende l'inventario degli stessi byte v2: 16 moduli statici aggiunti, 188 file Lua distinti legati a sorgenti, tutte le 75 versioni LuaRocks conservate, 111 ELF adapter e 810 ELF southbound associati a identità. Nuove scansioni offline e cinque firme PASS, 0 Critical/High/Unknown. Le SBOM originali e le immagini non sono cambiate. Il precedente gap dei 16 moduli descrive il supplemento originale; le nuove identità sono nel sidecar firmato.

> Rimane esplicito un file generato LuaJIT jit/vmdef.lua senza riconciliazione generatore/output nel manifesto pre-compilazione. Le associazioni MD5 LuaRocks conservano SHA256 misurati, ma non provano la provenienza upstream. Copertura completa, publisher trust, acceptance e start restano false. [Receipt corrente](/docs/handoffs/receipts/SEMANTIC_EXTENDED_DEPENDENCY_EVIDENCE_2026-10-06_CI.json) e [procedura VPS separata](/docs/installation/SEMANTIC_EXTENDED_EVIDENCE_V2_TARGET_2026-10-06.md). La verifica del sidecar sul VPS è ancora da ricevere dall'operatore; la CI non la sostituisce.

---

> Revisione aggiornata dopo gli output VPS delle 19:21 e 19:34 Europe/Rome. [CI 37505168458](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37505168458) PASS: otto controlli negativi e confronto sullo ZIP v2 effettivo, nuovamente verificato per hash/firme/byte. **16 moduli OpenResty realmente compilati non hanno identità individuali nella SBOM supplementare corrente.** [Receipt completa](/docs/handoffs/receipts/SEMANTIC_STATIC_MODULE_COVERAGE_2026-10-06_CI.json). Questo è un gap di inventario, non una nuova dichiarazione di vulnerabilità. Copertura completa e acceptance restano false; nessuna nuova operazione richiesta sul VPS per questa revisione.

## Riepiloghi e percorsi ricevuti dall'operatore

Adapter: 38 package (29 APK, 8 binary, 1 Python), zero versioni mancanti. I sei Simple Launcher 1.1.0.14 sono sei file distinti t32/t64/t64-arm/w32/w64/w64-arm.exe sotto pip/_vendor/distlib. Non sono prova di sei servizi in esecuzione, né questo dato autorizza rimozioni o esclusioni dallo scanner.

Southbound: 191 package (110 DEB, 75 LuaRocks, 6 binary), zero versioni mancanti. Le versioni duplicate di LuaFileSystem, api7-lua-resty-http, lua-protobuf, lua-resty-expr e penlight corrispondono a rockspec in directory di versione distinte. I percorsi non stabiliscono da soli quale modulo viene caricato; le identità scoperte restano tutte conservate.

OpenSSL di sistema: /usr/bin/openssl, versione binaria 3.0.13 e package Ubuntu 3.0.13-0ubuntu3.16. OpenSSL OpenResty: /usr/local/openresty/openssl3/bin/openssl 3.4.8. La prova registrata per Nginx riporta libssl/libcrypto del prefisso OpenResty. La sola versione upstream del binario Ubuntu non valuta le patch riportate nel package distro. [Receipt dei percorsi](/docs/handoffs/receipts/SEMANTIC_REMEDIATION_V2_PACKAGE_PATHS_2026-10-06_OPERATOR.json).

## Gap di inventario dimostrato

Il nuovo controllo lega la stringa configure al vero ELF Nginx nello stesso archivio southbound, verifica l'hash del manifesto sorgente e del supplemento contro le evidenze del bundle e riconcilia ciascun --add-module=../... con un archivio bloccato e file sorgente compilati registrati. Esclude gli archivi scaricati ma assenti dalle opzioni di compilazione.

Tutti i 16 moduli bundled configurati sono privi di una voce individuale nel supplemento: ngx_devel_kit, echo, xss, ngx_coolkit, set-misc, form-input, encrypted-session, srcache, ngx_lua, ngx_lua_upstream, headers-more, array-var, memc, redis2, redis-nginx e ngx_stream_lua. Repository, directory, hash degli archivi e conteggi dei file compilati sono nella receipt. Il package openresty aggregato e la copertura dei 17 ELF non dimostrano questa copertura individuale.

Non sono stati modificati le immagini o gli SBOM originali. La CI non importa immagini o invoca un nuovo scanner per questo confronto. Il PASS significa che la misurazione del gap è completata e che le prove v2 restano verificabili; non rende completa l'accettazione delle dipendenze.

Prossimo lavoro: integrare l'inventario dei moduli effettivi e delle dipendenze Lua installate, ripetere scansione e firma delle evidenze aggiornate, quindi preparare il dossier isolato dei nuovi digest. Restano revisione custom/publisher, scelta Wasm e vincolo dello stager al gateway live. Non forzare importazione o avvio e non ripetere il qualificatore VPS v2.

---

Le sezioni seguenti conservano la revisione precedente.

# Revisione prima dell'importazione v2 — 6 ottobre 2026

Qualificazione byte e verifica crittografica VPS PASS secondo gli output forniti dall'operatore alle 13:43:48 e 13:49:47 Europe/Rome. [Receipt delle firme](/docs/handoffs/receipts/SEMANTIC_REMEDIATION_V2_TARGET_CRYPTO_2026-10-06_OPERATOR.json). Le due immagini e i tre documenti nativi hanno firme di provenienza verificate; due SBOM hanno firme verificate. Repository, workflow, merge produttore e ref sono fissati. I risultati completi sono conservati in /home/oufadmin/ouf-crypto-v2.zjJNdo. La receipt byte originale rimane immutata: il suo targetAttestationCryptoVerified=false descrive quella fase precedente.

## Conclusioni della lettura dei sorgenti

| Controllo | Prova disponibile | Stato |
|---|---|---|
| Byte degli archivi e inventario supplementare | ZIP intero e archivi verificati; supplemento ricalcolato dai medesimi byte | PASS |
| Identità del builder | Cinque provenance e due SBOM verificate sul VPS con gh 2.102.0 | PASS operatore |
| Soglia scanner | Adapter, southbound e supplemento nativo: 0 Critical/High/Unknown, DB fissato | PASS per quel DB |
| Inventario nativo | Tutti i 17 ELF del prefisso /usr/local/openresty identificati | PASS entro quel prefisso |
| Copertura di tutte le dipendenze | Syft originale e supplemento separato; confronto completo runtime/sorgenti ancora da documentare | Aperto |
| Accettazione dei componenti custom | OpenResty e zlib non rilasciati; port delle patch; PCRE ereditato; chiave APK di build fixture | Aperto |
| Funzionalità Wasm | Esclusa dalla compilazione del candidato, scelta esplicita nel lock | Valutazione funzionale aperta |
| Dossier dei nuovi digest | Lo stager gateway corrente riusa obbligatoriamente l'immagine del gateway live | Percorso per i nuovi digest da preparare |

La funzione supplement in tools/supplement_semantic_rebuilt_native_sbom.py registra otto componenti e i sette moduli nel lock. L'uguaglianza covered==actual dimostra copertura degli ELF osservati nel prefisso, non automaticamente la copertura di ogni modulo statico, dipendenza Lua/Python o ELF esterno al prefisso. I 45 archivi sorgente fissati non sono, da soli, una SBOM dei soli componenti effettivamente installati. Occorre confrontare il contenuto delle SBOM, le sorgenti incorporate e le opzioni di compilazione, evitando sia componenti mancanti sia componenti scaricati ma non installati.

Dockerfile.semantic-provider-source-fixed introduce una chiave APK generata nel builder per il package zlib custom. La firma della build prova il builder e i byte; non trasforma quella chiave in un publisher approvato. Dockerfile.semantic-southbound-source-fixed e tests/semantic-native-runtime-sources.json dichiarano i commit upstream non rilasciati e l'omissione Wasm. Questi dati devono restare espliciti nella revisione custom.

Nel gateway fissato c0b1f97bdb1fbcd6a88117dea6520ea9c322f265, scripts/stage_semantic_provider_candidates.py imposta southbound.image=gateway_image['Id'] e verifica l'identità del gateway live. Lo ZIP v2 non deve essere forzato dentro quel percorso né sostituire il gateway live per soddisfarlo. Serve un dossier e un percorso di staging isolato coerente coi nuovi digest, preservando gli stager e candidati storici.

## Prossimo passo concreto

Leggere i riepiloghi delle SBOM e del manifesto sorgente già conservati nello snapshot v2. La lettura non avvia scanner o container. Poi completare la matrice di copertura e progettare il percorso isolato per i nuovi digest. Nessuna importazione/registrazione/start eseguita o autorizzata da questa revisione. Publisher trust, dependencyCoverageAccepted, acceptance e start restano false.

Il DB corrente scade il 7 ottobre 2026 alle 08:45:38 Europe/Rome; un eventuale nuovo bundle deve avere scansione e pin freschi, senza bypass. Gate 48 storico, gate 49 aperto, candidati fermati, Cinema/Teatri e il distinto HTTP503 restano preservati.
