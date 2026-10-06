# Identità effettiva LuaJIT e bundle v2 — 6 ottobre 2026

Il supplemento nativo utilizzava erroneamente il tag sorgente come versione del programma. Il runtime compilato riporta `LuaJIT 2.1.1787558776`; il tag resta `v2.1-20260824`, commit `fbfc558aacd57a54623df0ced4c31a28f81f8ff2`. La correzione registra la versione osservata, preservando vendor/prodotto luajit:luajit, pacchetti Syft originali, severità e criterio di scansione.

La lettura del runtime firmato nella [CI 37448503005](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37448503005) conferma la versione. Il supplemento richiede concordanza fra entrambi gli ELF, nomi installati e hash del file compilato .relver. Il [generatore upstream fissato](https://github.com/openresty/luajit2/blob/fbfc558aacd57a54623df0ced4c31a28f81f8ff2/src/host/genversion.lua) genera questa versione dal valore 1787558776. Sei test rifiutano identità mancanti, ambigue o alterate; 13 test locali e 10 test di identità/qualificatore nella CI PASS.

Gli hash del binario LuaJIT e della libreria sono invariati rispetto all'immagine delle sei regressioni JIT on/off nella CI 37447434158. Il manifesto sorgente è invariato. Quelle regressioni restano prove funzionali sul medesimo binario, senza ASan. I report storici 2 Critical / 1 High sono conservati. Nessun ignore, VEX o override aggiunto.

La [CI produttrice 37448782226](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37448782226), codice `1ef1d7abdbc6b2b879e57f3c09eaa5fe18f18ef6`, supera build, TLS/OIDC, shared-dict, gRPC, firme e qualificazione byte positiva. Quattro suite OpenSSL, sette test PASS. Inventario nativo: 17 ELF identificati nel prefisso /usr/local/openresty, nessun ELF irrisolto in quel perimetro.

| Report | Critical | High | Unknown | Medium | Low | Negligible |
|---|---:|---:|---:|---:|---:|---:|
| Adapter | 0 | 0 | 0 | 5 | 0 | 0 |
| Southbound Syft originale | 0 | 0 | 0 | 141 | 18 | 4 |
| Southbound supplemento nativo | 0 | 0 | 0 | 141 | 18 | 4 |

La [verifica indipendente 37450055158](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37450055158) scarica lo ZIP effettivamente pubblicato, verifica dimensione/hash, firme delle due immagini e dei tre documenti nativi, firme SBOM e qualificazione byte v2: PASS. Artifact 11406755583, 230675888 byte, SHA256 `2cdd7a73c1fc2a710f1e6604eb6cab2988492e4c45b5252defffa9832b91d9d0`. Il digest dello ZIP temporaneo interno al produttore è differente e non va utilizzato per il trasferimento.

Seguire la [procedura byte v2](/docs/installation/SEMANTIC_IMAGE_REMEDIATION_V2_TARGET_QUALIFICATION_2026-10-06.md), usando nuova cartella di trasferimento e snapshot v2. Wrapper fissato al commit `9db48efa8eb65f3d25aa6a0b58203cf7f644ca34`; nessuna importazione, container o registrazione runtime. VPS v2 ancora da osservare; PASS v1 e ambiente test preservati. DB valido fino al 7 ottobre 2026 alle 08:45:38 Europe/Rome, senza bypass.

Zero finding Critical/High/Unknown con questo DB non prova copertura universale. OpenResty resta un commit di sviluppo; Wasm escluso dalla compilazione; PCRE ereditato dall'immagine APISIX fissata. Publisher trust, copertura completa accettata, acceptance e start restano false. Il dossier deve essere coerente coi nuovi digest prima di importazione, registrazione o avvio.

La [receipt completa](/docs/handoffs/receipts/SEMANTIC_LUAJIT_RUNTIME_IDENTITY_2026-10-06_CI.json) conserva pin, hash, scope e risultati indipendenti.
