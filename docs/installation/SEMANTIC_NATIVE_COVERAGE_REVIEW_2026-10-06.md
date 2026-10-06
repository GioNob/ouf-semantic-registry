# Revisione delle dipendenze native — 6 ottobre 2026

La qualificazione byte VPS resta PASS. L'immagine southbound qualificata non supera la scansione supplementare: 2 Critical e 8 High, tutti Wasmtime 0.38.1. Nessuna importazione o operazione container è stata eseguita da questa revisione.

## Evidenza riproducibile

- ZIP originale: `bf369a5e445a7e84c51d0252b6714912b0d92897097f3afeb2a21c85db38fa2a`.
- Immagine: `sha256:213ff3377465784bc1f5dd82863d65d6585a3c22062eb4e7d78c7c0239af0334`.
- [CI 37424720686](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37424720686), codice `150e059e8722c27ce0949254aa850ff82c64af7b`: tre test negativi/strutturali PASS, scansione Grype offline sul DB fissato e ancora fresco, originale attestazione verificata.
- [Artifact 11395230041](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37424720686/artifacts/11395230041), SHA256 `02a1b44a1b737e5c95b74cb7e310c014f78526a41ce44652a08b8056167776c8`, 883798 byte; scaricato, hash verificato e report letti.
- La nuova attestazione dell'evidenza è stata emessa dalla CI; la sua verifica crittografica indipendente resta da eseguire. Non equivale a publisher trust approvato.

Il Syft originale enumera 182 package ma non identifica separatamente alcune librerie native possedute dal package APISIX. Il nuovo documento conserva package/relazioni originali e aggiunge quattro componenti con evidenza di versione e hash: OpenSSL 3.4.8, zlib 1.3.2.1-motley, PCRE 8.45 e Wasmtime 0.38.1. Non modifica il vecchio SBOM o il report qualificato sulla VPS. Il binario libwasmtime.so corrisponde byte per byte al C API x86_64 Linux ufficiale v0.38.1 (SHA256 `ec2b5868c0e602c5e233607d422fad3422758c7a12bd38faded483da62081c2d`).

La copertura resta incompleta per sei file ELF: LuaJIT eseguibile/libreria, cjson, restysignal, redis/parser e Nginx con moduli statici. Etichette generiche come 2.1.ROLLING non dimostrano un commit corretto. Nessun ignore, VEX o soglia ridotta.

## Contratti PET recuperati

Il pacchetto ri-allegato `OUF_Reality_Baseline_Package_v1_7(4).zip` ha SHA256 `e63df67e8817eec38a9d4b3eb736b020f693b932f3360dc02f4555330f2201ce`; tutti i 323 checksum interni sono corretti. Gateway v1.5 T16 e T33.13 richiedono scanning/SBOM/firme/provenienza e nessun blocker/high irrisolto. Semantic v1.3 159.1–159.2 e 160 richiedono artifact/BOM e descrittore di build riproducibile. La chiave APK di fixture e le firme CI non costituiscono automaticamente chiavi publisher target approvate.

## Blocco e seguito

CVE-2023-26489 (Critical, GHSA-ff4p-7xrq-q5r8) è confermata dall'advisory upstream per Wasmtime 0.38.1 su x86_64: errore di compilazione con accessi fuori dalla sandbox. CVE-2022-39393 (High, GHSA-wh6w-3828-g9qf) riguarda allocatore pooling; l'eventuale non uso richiede prova specifica, non esclusione automatica. Le severità GHSA/NVD differiscono per altri finding; il report Grype e la soglia restano integri. Receipt contiene tutti i dieci finding e i fix suggeriti.

Riferimenti primari:
- https://github.com/bytecodealliance/wasmtime/security/advisories/GHSA-ff4p-7xrq-q5r8
- https://github.com/bytecodealliance/wasmtime/security/advisories/GHSA-wh6w-3828-g9qf
- https://github.com/api7/wasm-nginx-module/blob/0.7.0/install-wasmtime.sh
- https://github.com/api7/apisix-build-tools/blob/35292b649a01887cd54597fd16b2bea99648cdf5/build-apisix-runtime.sh

Lo script upstream installa ancora v0.38.1 e collega il modulo WASM staticamente a Nginx. Sostituire/cancellare soltanto libwasmtime non è una correzione dimostrata. Alternative da esercitare in CI: aggiornare e ricompilare modulo/Wasmtime con ABI verificata, oppure runtime ricompilato senza modulo opzionale WASM dopo aver verificato i contratti richiesti. Nessuna build corretta o compatibilità di queste alternative è ancora dichiarata.

Prima di nuovi passi VPS servono build corretta, identità/provenienza delle dipendenze native, scansione completa su DB fresco, regressioni reali TLS/OIDC e nuovo dossier coerente coi digest. Il gateway live e lo snapshot già qualificato restano invariati. Acceptance/runtime/start false; gate49 storico aperto.
