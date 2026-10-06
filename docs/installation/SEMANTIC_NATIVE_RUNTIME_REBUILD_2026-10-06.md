> Stato corrente 6 ottobre 2026 — riconciliazione LuaJIT [37447434158](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37447434158) PASS: otto test negativi, sei file identici ai manifesti compilati, fix upstream/CNA verificati, sei regressioni sulla stessa immagine firmata (JIT on/off). ZIP completo e hash del binario verificati. I tre finding sono corretti nel sorgente del runtime; il report scanner resta integro **2 Critical / 1 High / 0 Unknown** e il gate grezzo rimane false. Il blocco successivo è la riconciliazione dei dati/match CPE con il criterio automatico, non una nuova ricompilazione delle stesse tre correzioni. Nessuna soppressione/VEX/deroga autorizzata da questa prova. Qualificazione byte VPS v1 PASS, non ripetere; ambiente test preservato, nessuna operazione target. Copertura/publisher trust/acceptance/runtime/start false. Receipt SEMANTIC_LUAJIT_RECONCILIATION_2026-10-06_CI.json e revisione SEMANTIC_LUAJIT_RECONCILIATION_2026-10-06.md. Questo stato prevale sui paragrafi storici.

# Ricompilazione del runtime nativo — 6 ottobre 2026

La build CI [37433261779](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37433261779), codice `385809bde50a20e4987c9c55c2b57a614dc240e0`, supera compilazione, installazione e prove reali TLS/OIDC, shared-dict e gRPC authority. Wasmtime è assente. La soglia completa resta **BLOCKED: 2 Critical / 1 High / 0 Unknown** nel report supplementare. Nessun ignore, VEX, modifica di severità o deroga alla soglia.

La qualificazione byte dello ZIP originale sul VPS resta PASS e non va ripetuta. Nessuna operazione VPS, importazione, sostituzione di file o avvio è stata eseguita per questa ricompilazione. Lo snapshot v1 e l'ambiente di test restano preservati.

## Risultato misurato

| Ambito | Critical | High | Medium | Low | Negligible | Unknown |
|---|---:|---:|---:|---:|---:|---:|
| Adapter Syft/Grype | 0 | 0 | 5 | 0 | 0 | 0 |
| Southbound Syft/Grype | 0 | 0 | 141 | 18 | 4 | 0 |
| Southbound inventario nativo supplementare | 2 | 1 | 141 | 18 | 4 | 0 |

Il supplemento conserva tutti i package e le relazioni Syft originali. Identifica e lega per hash tutti i **17 ELF sotto `/usr/local/openresty/`**, senza ELF irrisolti in quell'ambito. Questo risultato non equivale a copertura completa di ogni dipendenza dell'immagine, approvazione delle fonti o publisher trust target. PCRE 8.45 resta ereditato dalla base APISIX fissata.

La CI verifica le quattro firme di provenance/SBOM relative agli archivi. Il readback indipendente [37434717230](https://github.com/GioNob/ouf-semantic-registry/actions/runs/37434717230), job112173608320, verifica SHA256 dell'intero artifact, firma dei tre documenti nativi, workflow/ref/merge del produttore e appartenenza del codice produttore al merge; PASS. Acceptance, publisher trust, copertura accettata, runtime registration e start restano false.

## Sorgenti e patch

OpenResty upstream `bc8bf89488f2d02572389158533b3f85ca0ded7f` è uno snapshot **non rilasciato**, versione di sviluppo 1.31.6.1; include Nginx1.31.6, LuaJIT2.1-20260824, cjson2.1.0.19 e restysignal0.05. Non è un tarball ufficiale di release.

La preparazione conserva la ricetta upstream mirror-tarballs e blocca tutti i 45 download per URL, SHA256 e dimensione. Omette la generazione della documentazione e registra l'indice documentale vuoto necessario all'installer. L'archivio deterministico ha SHA256 `2e7e8a432fc4303833a1860f07620d989cab7024a326e0b5fdc93e2243ea84d0`.

I sette moduli conservano i commit della ricetta APISIX. Il port delle patch Multi-Upstream1.3.3 e APISIX native1.19.9 copre 81 file; mantiene sia i nuovi campi upstream sia quelli dei moduli. Il percorso gRPC usa la nuova gestione host_value per inoltrare :authority. La sostituzione shared-dict APISIX conserva i nuovi limiti key_len>65535 negli FFI store/incr. I manifesti salvano gli hash delle sorgenti compilate dopo le patch e dei binari installati.

APISIX resta3.18.0. L'adapter conserva Python3.13, UID10006, payload ed entrypoint. Nessun plugin applicativo custom introdotto. L'omissione WASM resta una variazione funzionale del candidato CI da valutare nel dossier.

## Validazione e limiti

Compilazione/installazione PASS; prove reali TLS/admission e APISIX/OIDC PASS; chiave shared-dict65536 rifiutata e normale set/get PASS; inoltro gRPC :authority osservato nel corpo HTTP PASS. Il fixture gRPC usa un response body prodotto da Nginx: il comando resty reindirizza ngx.say verso stdout, quindi il precedente fixture non misurava il corpo della risposta.

Quattro test del qualificatore e verifica della chiusura sorgente standalone PASS in CI; tre test strutturali/negativi dell'audit nativo PASS nella revisione precedente. La qualificazione positiva v2 resta **non provata**, perché la soglia combinata è falsa e viene rifiutata prima dell'accettazione degli archivi. OpenSSL: quattro suite, sette test PASS nel run37433261779. Il NOTESTS separato riguarda soltanto la preparazione FIPS saltata perché non è una build FIPS; la precedente interpretazione del riepilogo è corretta. Le prove TLS reali passano separatamente.

## Revisione delle segnalazioni LuaJIT

I record CNA distinguono LuaJIT generico <=2.1 da OpenResty luajit2 precedente alle correzioni del2024. Il tag v2.1-20260824 risolve al commit `fbfc558aacd57a54623df0ced4c31a28f81f8ff2`; i tre fix sono antenati verificati tramite compare e i corpi corretti sono presenti nell'archivio bloccato. Il report firmato conferma che gli unici finding bloccanti sono CVE-2024-25178 e25176 (Critical), CVE-2024-25177 (High), tutti luajit2.1-20260824 nel namespace nvd:cpe. La riconciliazione byte/sorgente e le regressioni sulla stessa immagine sono completate nel run37447434158. Il match CPE del report grezzo resta presente e la soglia automatica non viene modificata; vedere SEMANTIC_LUAJIT_RECONCILIATION_2026-10-06.md. Il CPE generico e tutte le segnalazioni restano conservati.

| CVE | Fix upstream presente nel sorgente |
|---|---|
| CVE-2024-25176 | `343ce0edaf3906a62022936175b2f5410024cbfc` |
| CVE-2024-25177 | `85b4fed0b0353dd78c8c875c2f562d522a2b310f` |
| CVE-2024-25178 | `defe61a56751a0db5f00ff3ab7b8f45436ba74c8` |

Fonti primarie:
- https://github.com/CVEProject/cvelistV5/blob/main/cves/2024/25xxx/CVE-2024-25176.json
- https://github.com/CVEProject/cvelistV5/blob/main/cves/2024/25xxx/CVE-2024-25177.json
- https://github.com/CVEProject/cvelistV5/blob/main/cves/2024/25xxx/CVE-2024-25178.json
- https://github.com/openresty/luajit2/commit/343ce0edaf3906a62022936175b2f5410024cbfc
- https://github.com/openresty/luajit2/commit/85b4fed0b0353dd78c8c875c2f562d522a2b310f
- https://github.com/openresty/luajit2/commit/defe61a56751a0db5f00ff3ab7b8f45436ba74c8
- https://nginx.org/en/security_advisories.html
- https://github.com/openresty/openresty/security/advisories/GHSA-wx83-v28q-68gx

## Artifact e seguito

Merge produttore `1c7e31a26c664a12f2588292d38b3896b4c4e7ec`, job112168860142. Evidence artifact11397838781: 7236277 byte, SHA256 `c3a284af013942a0fc33b2a7855e84d347315f061f5bf65072101403e7a51312`. ZIP completo11397709159: 230682834 byte, SHA256 `0614b43d8843b8ebe24b4a6a4d564dfb1d36271b8660e8d0379d147a1db231c0` (ora scaricato e SHA256 verificato sul runner del run37447434158; immagine estratta e firma verificata prima delle regressioni).

Southbound `sha256:516f49278f48c808427d346ad8d1520f60433d071949435774395e6c0ebc29b3`; archivio gzip SHA256 `8b1042906bf4d48a5fc07f1e0797cbe343d1c38b9e352ee1d51dfdd6322cc6e8`; manifesti sorgenti/binari e digest Syft sono conservati nella receipt `docs/handoffs/receipts/SEMANTIC_NATIVE_RUNTIME_REBUILD_2026-10-06_CI.json`.

La prima ricompilazione completa senza Wasmtime (run37427596293) aveva ancora 3Critical/10High nel supplemento: il nuovo aggiornamento elimina i finding Nginx/OpenResty da quel confronto. L'audit originale dello ZIP già qualificato conserva2Critical/8High Wasmtime e sei identità irrisolte. La sua firma supplementare è ora verificata indipendentemente dal run37432727620; il vecchio ZIP resta inadatto all'avvio.

Il qualificatore v2 prepara soltanto un nuovo snapshot `semantic-image-remediation-20261006-v2` e lega i documenti nativi ai byte dello stesso archivio. Non usare o ripetere il comando v1 sul nuovo ZIP. Nessun comando VPS pronto: servono risoluzione verificabile dei match residui, copertura/provenienza approvate e dossier coerente coi nuovi digest e col gateway live.

Gate48 storico, gate49 aperto, candidati fermati e Cinema/Teatri restano preservati. Il pairwise live HTTP503 è distinto da questa build. Il DB fissato scade il7ottobre alle08:45:38Europe/Rome; nessun bypass di freschezza.
