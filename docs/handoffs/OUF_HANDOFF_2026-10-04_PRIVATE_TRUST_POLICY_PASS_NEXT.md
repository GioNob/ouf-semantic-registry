# OUF — ripartenza pulita dopo policy privata §38 PASS

## §43 AUTORIZZATO — wrapper pinned pronto, output VPS ancora non ricevuto

L'utente ha conferito esplicitamente “Autorizzo il43” il5 ottobre2026 alle06:48:20 Europe/Rome. Scope: export senza filtro di piattaforma delle medesime2 immagini esatte, con lettura privata in memoria anche di eventuali contenuti locali di altre piattaforme/attestazioni e segreti incorporati, mai divulgati. Verifica resta linux/amd64, limiti180s/8GiB/100000 entries perimmagine invariati. Nessun pull/build/containeroperation/provider/firma/acceptance/start/runtime/consumerlink/hostkeyEnv o registrycredential grant. Receipt `docs/handoffs/receipts/SEMANTIC_IMAGE_INDEX_BYTES_SCOPE_43_AUTHORIZATION_2026-10-05.json`.

Stato **AUTHORIZED_NOT_EXECUTED**. Pin esecutivo `1a5e159fa130981a9f102a2d50c4dacb3cfda5f5`, SHA256 `6413193ac7f1b1d91eb71b59f7ae3140e594cfe788cd89c9cfa722161ca081ff`;47 root0skip+1 Docker standard+1 Docker29.8.1/containerd PASS sul pin. Il commento NOT GRANTED del wrapper immutabile registra la preparazione; il conferimento successivo è qui, non modifica il pin. §42 precedente resta BLOCKED e non si ripete; ultimo VPS PASS §41. Consegnare comando checksum-verified come oufadmin, poi registrare output; nessun retry/limite esteso automatico.

Requisito utente installer guidato registrato in `docs/installation/OUF_GUIDED_INSTALLER_REQUIREMENTS_2026-10-05.md`: **amd64 significa x86-64 sia Intel sia AMD**, non marca CPU. Installer rileva OS/architettura/Docker e chiede le scelte amministrative, valida matrice supportata, sceglie immagini/script e genera manifest/pin per i parametri corretti. Platform verificata prima dell'operazione e poi sigillata; non deve modificare arbitrariamente wrapper già pinned. ARM64 e altri ambienti richiedono immagini/verifiche/native CI specifiche: supporto non ancora provato. Stato requisito SPECIFICATO_NON_IMPLEMENTATO; questa verifica VPS43 non è il futuro installer generalizzato.


## §43 preparato NON AUTORIZZATO — conservare indice immagine, niente nuovo tentativo §42

La nuova CI Docker29.8.1/containerd ha riprodotto il limite: l'ID della fixture è l'indice originale, ma save --platform linux/amd64 ne esporta solo il manifest selezionato; il pin indice non è nell'archivio. CI run37264605556 job111618641830 BLOCKED alla catena OCI_TARGET_BINDING. È evidenza software sulla fixture, non prova della causa target; §42 VPS resta BLOCKED diagnosticamente alla congiunzione configSHA==ID / config JSON dict, secondo receipt06:34:44. Non consegnare il wrapper filtered e47dd8e/88ed2ea: NON eseguito sul VPS, superseded per questo limite; nessun replay dei due pin eseguiti.

Follow-up concreto **§43**: `docs/handoffs/commands/OUF_VERIFY_IMAGE_INDEX_BYTES_2026-10-05.sh`, SHA256 `6413193ac7f1b1d91eb71b59f7ae3140e594cfe788cd89c9cfa722161ca081ff`, **scope NON conferito e NON eseguito**. Rimuove il filtro di esportazione --platform SOLO con flag esplicito --retain-image-index, per conservare indice/manifest originali dei medesimi2 image ID. Piattaforma verificata resta linux/amd64. **Può leggere privatamente anche bytes delle altre piattaforme/attestazioni già conservati localmente nelle stesse2 immagini**, oltre config/layer già nello scope42; mai stampati/eseguiti/spooled. Questo delta richiede scope concreto secondo handoff§7.4, dopo preparazione/test del wrapper. Nessuna firma/start/pull/build/install/runtime/consumerlink/provider/lettura privata host keyEnv/registrycredentials; stessi limiti180s/8GiB/100000 entries perimmagine. Non allargare budget o leggere altriimageID.

Catena CONFIG oppure esatto MANIFEST/INDEX→config/layer con digest,size,mediaType,platform univoca e ordine esatti; DiffID/rootfs/payload/startup invariati. Nessun fallback unanchored.21 test locali PASS0 skip incluse default senzaindex e opt-in esplicito; CI readback `1a5e159fa130981a9f102a2d50c4dacb3cfda5f5` PASS:47 test root0 skip,1 Docker standard+1 Docker29.8.1/containerd reale PASS, wrapper parity/bash-n PASS; run37264907986, jobs111619529628/111619529796/111619529767. La fixture containerd richiede filtered BLOCKED e unfiltered INDEX PASS, mai avviata. Altri2 workflow ancora in progress, nessuna dichiarazione full CI. [Scope completo](https://github.com/GioNob/ouf-semantic-registry/blob/1a5e159fa130981a9f102a2d50c4dacb3cfda5f5/docs/installation/SEMANTIC_IMAGE_INDEX_BYTES_SCOPE_2026-10-05.md). Acceptance/publisher/SBOM/currentOCI/generation/mountview/start non sono conferiti. Questa intestazione prevale sulle precedenti.


## §42 secondo BLOCKED — controllo identità config; correzione OCI pronta

Output operatore5 ottobre2026 alle06:34:44 Europe/Rome: checksum wrapper41a03e4 OK; `dockerExitCode=0,errorClass=Blocked,imageRole=ADAPTER,parserBytes=223532435,parserEntries=5798,stage=ARCHIVE_VERIFICATION,verifierLine=167`; poi BLOCKED. La linea167 è nel Python incorporato (non la linea167 del file shell): confronto congiunto hash config==ID Docker e JSON config dict. Nessun PASS immagini, causa target ancora da confermare; non interpretare counters come prova della catena completa. Receipt `docs/handoffs/receipts/SEMANTIC_IMAGE_BYTES_DIAGNOSTIC_BLOCKED_2026-10-05.json`; ultimo VPS PASS resta §41.

Il lettore aveva assunto ID==configSHA sempre. Moby backend containerd usa invece target.Digest per ID, con config separata: https://github.com/moby/moby/blob/master/daemon/containerd/image_inspect.go . Il follow-up `docs/handoffs/commands/OUF_VERIFY_IMAGE_BYTES_2026-10-05_CONTAINERD.sh` conserva scope42, immagini, --platform linux/amd64, controlli/limiti180s/8GiB/100000 entries. Accetta CONFIG esatto oppure **MANIFEST/INDEX esatto SHA-anchored**, con ogni edge selezionato validato per digest/size/mediaType, platform univoca, config esatta e layer ordinati identici al manifest Docker esportato, poi DiffID/rootfs/app/startup pins invariati. Nessun fallback a manifest non ancorato; se --platform omette l'indice target pinned, BLOCKED resta obbligatorio. Non omettere --platform né ampliare letture senza analisi/scope concreto.

SHA256 nuovo wrapper `733e5fd1dfc12732b840003bce398a86ad8ca49e715568f635f0026c8ecdbeaa`;20 test locali PASS0 skip; CI standard e nuova fixture Docker29.8.1/containerd da verificare. Follow-up PREPARATO_NON_ESEGUITO. Campo configBytesMatchImageId diventa veritiero per CONFIG; identityBindingKind e imageTargetChainVerified riportano la catena in modo distinto. Niente acceptance/firma/start/provider/publisher/SBOM/full mount proof. Tutte le intestazioni precedenti sono storia, non stato corrente.

Debito di rilascio discusso con utente: CI testa/parity wrapper già presente, non genera ancora tutti i pin a ogni build. Generazione automatica manifest/wrapper/versioned artefacts e preflight prerequisiti host python3/docker/privileged entry limitato restano da implementare; path fissato non prova integrità interprete. Questo repair non trasforma il wrapper amministrativo nel meccanismo definitivo release.


## §42 eseguito BLOCKED — diagnosi redatta pronta, causa ancora sconosciuta

Il5 ottobre2026 alle06:28:51 Europe/Rome l'operatore ha restituito checksum wrapper OK e `SEMANTIC_IMAGE_BYTES=BLOCKED REASON=IMAGE_ARCHIVE_UNPROVEN NO_SECRETS_PRINTED=true`. Nessun JSON immagini/contatore ricevuto: non attribuire una causa, una lettura completata, image bytes PASS o acceptance. Ultimo VPS PASS resta §41. Receipt: `docs/handoffs/receipts/SEMANTIC_IMAGE_BYTES_BLOCKED_2026-10-05.json`. Non ripetere il wrapper originario immutabile ffe6a9b: il suo output accorpa ogni eccezione.

Il follow-up `docs/handoffs/commands/OUF_VERIFY_IMAGE_BYTES_2026-10-05_DIAGNOSTIC.sh` mantiene **lo stesso scope §42 già autorizzato**, immagini, controlli e limiti180s/8GiB/100000 entries per immagine; aggiunge solo ruolo/fase/vocabulary classe errore/linea sorgente/counters numerici. Nessun messaggio eccezione, path/config/Env/file privato o stderr Docker stampato. Nessun controllo rilassato, nuova authority, firma/start/registry credentials/provider/consumer o lettura privata host. SHA256 `c6c64cbfe881261495be28b323c0c400612b62590e6156fc4a7b63bb68fc30bb`;15 test locali PASS,0 skip e parity/bash-n PASS; CI readback su `41a03e492d2dd76c6c0f7749d7c9cd9987475790` PASS:41 test root,0 skip+1 Docker reale PASS, wrapper parity/bash-n PASS (run37263946062; jobs111616698801/111616698530). Gli altri workflow non sono tutti conclusi: nessuna dichiarazione full CI. Follow-up PREPARATO_NON_ESEGUITO, nessun retry automatico sul VPS. Blocchi separati Search503 e full target acceptance restano aperti. Sezione corrente prevale sulle intestazioni storiche sotto.


## §42 AUTORIZZATO — esecuzione operatore ancora NON osservata

Il5 ottobre2026 alle06:20:36 Europe/Rome l'utente ha risposto **“autorizzo”** allo scope concreto §42. La sola lettura privata config/layer bytes delle2 immagini esatte è conferita, inclusi eventuali segreti incorporati letti privatamente in memoria e mai stampati. Wrapper esecutivo immutabile `ffe6a9bceeee08bae95c93425f646bd354780d7c`, SHA256 `c8602ba1279481df8a7cbc66864bd5a978be0234678d6cc5515da6b2f7e45b57`;39 test root+1 Docker e7 workflow CI PASS già verificati. Il commento NOT GRANTED nel pin originario registra il momento di preparazione, non lo stato attuale: conferimento registrato in `docs/handoffs/receipts/SEMANTIC_IMAGE_BYTES_SCOPE_42_AUTHORIZATION_2026-10-05.json`.

Stato corrente **AUTHORIZED_NOT_EXECUTED**: nessun output VPS ricevuto, ultimo VPS §41 PASS resta invariato. Nessun nuovo grant di acceptance/firma/start/migrazione runtime/consumerlink/provider o lettura host key/Env/registry credential. Non ripetere §39–41; non estendere lo scope42 alla diagnosi Search503. Download wrapper temporaneo pubblico, checksum obbligatorio prima di bash; lettore conserva config CLI temporaneo vuoto e pipe senza extraction/spool. Dopo output aggiornare autonomamente4 documenti/stato/receipt; BLOCKED richiede analisi prima di qualsiasi nuovo tentativo.


## Checkpoint autonomo corrente — raccordo temporale software provato con Docker; §42 pronto

Questo checkpoint prevale sulle sezioni storiche sottostanti. Ultimo VPS operatore **§41 PASS storico**, receipt immutata; §39–41 completati, nessun replay. Le letture prodotto MCP aggiunte sotto non sono deploy. Packagev8 target7ded9df, policy privata38, candidati fermi e consumer restano nel precedente stato. Nessuna firma operativa/registrazione runtime/migrazione/acceptance/start target eseguita; nessun comando VPS pendente.

**Raccordo observation→mandate e dipendenza dal pin pre-create risolti e testati in software.** Gateway PR56 draft, commit `516133e59be869012d3003758e545a5b5aa0060a`. v1 mandato preesistente preservato; v2 autorizzazione bytes hash-pinned per OCI già noto; v3 percorso privato esatto sigillato nella configurazione, autorizzazione completa firmata fornita dopo che shadow OCI è noto, senza mutare producer/broker già pinned. Nessun input unsigned/mixed/fallback o wildcard. Firma CREATION_ATTESTATION selezionata con install/entity/issuer/intent/OCI/rootfs/transport/runtime/artifact esatti,≤300s entro intent; contenuti catturati e stabili durante issuance. [Contratto completo](https://github.com/GioNob/ouf-api-gateway/blob/516133e59be869012d3003758e545a5b5aa0060a/docs/semantic-node-live-mandate.md).

Node osserva realmente generation/OCI/rootfs/trasporto, claim durabile prima della chiave, mandato v1 con generation reale, tre osservazioni, O_EXCL/fsync, nessun replay/concorrenza duplicata; producer5s/node12s/broker18s invariati. **v3 rimuove il ciclo dei bytes di configurazione, non implementa né conferisce l'issuer esterno di acceptance sul target.** Quel provisioning deve validare immagini,8 mount/bind esterni, mount generate e vincoli nel punto shadow-OCI prima dell'invocazione; rootfsSeal host non è full mount view. Nessuna pausa HUMAN dentro deadline, nuova authority/keypair, callback o lock annidato del broker.

CI Gateway `516133e` riletta:2 workflow PR/19 jobs returned completed/success; run37233834317/37233834435. Job111528912218: **224 test root,0 skip**, inclusi15 live mandate+8 signed-path,2 native admission,3 native node/runc,2 native target Docker/Go. Node positivo CLI source-sealed senza mocks:0,427s sulla piccola fixture Busybox; real OCI/rootfs drift negano prima di claim/mandato, applicazione mai avviata. Job111528912131: **7 test Docker PASS,0 skip**, include v3 config producer/broker pinned prima che authority esista e invariati dopo, generation reale, rootfs-drift senza mandato, lease/signature denial, guarded start solo fixture CI posseduta. v1 native regressioni preservate. Locale51 test issuer/node/v2/v3 PASS,0 skip. Non misura immagini VPS o prova native v3 target.

**§42 lettura privata bytes immagini PREPARATA/NON AUTORIZZATA/NON ESEGUITA.** Wrapper pin immutabile `ffe6a9bceeee08bae95c93425f646bd354780d7c`, SHA256 `c8602ba1279481df8a7cbc66864bd5a978be0234678d6cc5515da6b2f7e45b57`; [scope completo](https://github.com/GioNob/ouf-semantic-registry/blob/ffe6a9bceeee08bae95c93425f646bd354780d7c/docs/installation/SEMANTIC_IMAGE_BYTES_READBACK_2026-10-04.md). Solo2 Docker save image IDs pinned/linux-amd64; stream config/layer inclusi eventuali segreti incorporati privatamente in memoria, no extraction/spool. Config CLI temporaneo vuoto, no registry credential o mount/key/Env target letti. ConfigSHA→imageID/DiffID ordinati→descriptor §39, payload adapter5file source52c0/permissions/startup/labels/whiteout. Max180s/8GiB lavoro parser cumulativo/100000 entries per immagine; no pull/build/create/start/firma/daemon change.

CI reader pin `ffe6a9b`:7 workflow PR completed/success; run37232696817, job111525565709 **39 test readback root/0 skip +4wrapper bash-n/parity**, job111525566149 **1 test Docker reale PASS**. Nuovi13 unit/CLI locali PASS; rootfs descriptor mismatch/redaction/limits e wrapper parity verificati. Publisher/base/SBOM/build riprodotta/full OCI/mount/rootfs live/generation/atomic/acceptance/start restano aperti. Checkpoint documentale4f28ddfc8b6f9ef3df9e53aac33b0c4e6d7fb36d:7 workflow PR completed/success, esito separato rilettura finale. I puntatori CI indicano il precedente commit verificato, non attribuiscono tale esito a un successivo aggiornamento metadata.

**Prodotto: letture autonome MCP effettive.** [Report](https://github.com/GioNob/ouf-semantic-registry/blob/codex/r4a-smoke-semantic-inventory/docs/OUF_AUTONOMOUS_PRODUCT_SMOKE_2026-10-04.md): account HUMAN correnteouf-admin; urban.object.search(type Cinema URI,pageSize2)→HTTP503, campi Problem vuoti, nessuna paginazione/oggetto provato; non ritentato con altra identità. semantic.search(Theatre,CLASS,limit3)→risposta valida[], non censimento completo. Source-only: Gateway firma/owner-key e UDP5binding/key-file sono possibili punti503, non causa target dimostrata; MCP può perdere dettagli di un corpo non-Problem. Nessun grant/restart/ingestion replay per correggere a intuito. R-SMOKE completo rimane OPEN; next diagnostic deve discriminare componente/upstream/binding nel minimo scope target pertinente.

Filo prodotto: chatbot→file/profile→mapping semantico→THS/ACTIVE→one-time Ingestion/RAW/handoff→UDP→Search. Riutilizzare Cinema8/8 e Teatri asset/profile/proposta PENDING_HUMAN_REVIEW, niente nuovi upload/job. Ricerca interna autosufficiente, esterna soltanto se gap. CAP/CRS/tempo/provenance/identity, definitions/vocab, minimizzazione/2pagine/cursor/audit, Lake/replay/portabilità/reboot/release non chiusi per omissione. PET Semantic9.2/10–11/159.2, Gateway supply chain, Onboarding92–92.3/109, UDP21–22/109 e Authorization36.10 riesaminati/riusati.

Stima aggiornata orientativa al ritmo quasi24h7g comunicato:3–7 giorni di calendario prima prova completa,1–2 settimane con correzioni significative; nessuna data garantita. Il lavoro autonomo non richiede prompt notturni. **Prossimo unico intervento proposto al ritorno dell'operatore: scope privato §42 con wrapper completo pinned e CI verificata secondo handoff7.4**; richiesta di continuare codice non è sua concessione implicita. Prima di firme/start target concretizzare issuer acceptance e piano runtime/migrazione/rollback, niente staging inerte o nuove inventory generiche. Diagnosi Search503 è attività indipendente, da non confondere con avvio provider.


## Checkpoint corrente — §41 ESEGUITO/PASS, non ripetere

Scope §41 conferito dall'utente il4 ottobre2026 21:48:38 Europe/Rome; output ricevuto21:53:39. Wrapper checksum OK; SEMANTIC_IMAGE_LINEAGE=PASS/HISTORICAL_ONLY. Evidenza operatore, nessuna ispezione VPS indipendente. Pin eseguito `77407922584a68ffbbeb7068a88d9acac33fa52d`, SHA256 `ac40df1dba21cc528641ea38aad2020e557dd3424612ab53071bc57f74992083`. [Receipt redatta](https://github.com/GioNob/ouf-semantic-registry/blob/codex/r4a-smoke-semantic-inventory/docs/handoffs/receipts/SEMANTIC_IMAGE_LINEAGE_PASS_2026-10-04_OPERATOR.json).

Quattro evidenze e sei sorgenti conservati verificati; buildContextMatchesPinnedSource/adapterReceiptBindingsConsistent/southboundSelectionConsistent=true. Nuovi hash osservati: build-intent `806197190e8665bc01c641c5ad0dc1809670f2deee4d9bf4abf8f1a4b1ece5e0`, image-stage `64b5ec653d3b7037795ae380120a1127d9b6d8e10e60d2cfa381eedc87b4438b`. Nessun file configurazione/chiave/Env letto; providerCalls/signaturesIssued/targetFilesWritten=0. acceptanceGranted/startAuthorized/runtimeRegistered=false. Prova storica dei binding e dei sorgenti, non dei bytes dentro le immagini, publisher trust, SBOM/base, build riproducibile, OCI/rootfs/generation live o snapshot atomico. Quei gate restano aperti.

**Nessun comando VPS pendente. Non ripetere §41/40/39/38/36/34/31.** Scope41 completato e non esteso ad altre letture. Le sezioni PREPARATO/non autorizzato/non eseguito sotto sono cronologia superata da questo checkpoint. La policy privata38 resta non collegata ai consumer, nessuna firma operativa/avvio implicito.

Priorità successiva autorizzata per lavoro autonomo: risolvere e testare il raccordo observation→mandate nel broker/producer prima di nuove richieste di firma/start; completare la prova mirata dei bytes/provenance delle immagini, riusando gli hash receipt acquisiti. Non aprire inventari ridondanti o ulteriori package inerti. Dossier/generation reali non sostituibili con candidati fermi. Migrazione runtime, consumerlink e avvio richiedono scope distinti dopo risultato concreto revisionabile.

Stima orientativa comunicata all'utente per prima prova completa chatbot→file→mapping semantico (incluso ramo esterno)→THS/ACTIVE→Ingestion/UDP→Search:5–10 giornate intense, circa1–2 settimane al ritmo continuativo; margine2–3 settimane se il raccordo/live richiede correzioni significative. È una previsione, non una data garantita o release acceptance. La ricerca interna rimane indipendente dal provider esterno; le prove manuali Cinema/Teatri restano congelate, non si rifanno.

CI del precedente HEAD documentale `3a590539231a71f898784eab1b3f1825ca05ffb8` riletta:7 workflow PR completed/success. Codice §41 `7740792`:26 test CI PASS/0 skip e3wrapper parity/bash-n PASS già verificati, non rerun locale in questo aggiornamento di sola documentazione. CI di questo nuovo checkpoint da verificare separatamente. PR26/30/56 restano draft/nonmerged.


## §41 PREPARATO — lettura privata lineage immagini da autorizzare

Ultimo VPS §40 ESEGUITO/PASS; scope §40 completato, non riutilizzato per altre letture. Preparato `tools/verify_semantic_image_lineage.py` e wrapper `docs/handoffs/commands/OUF_VERIFY_IMAGE_LINEAGE_2026-10-04.sh`, SHA256 `ac40df1dba21cc528641ea38aad2020e557dd3424612ab53071bc57f74992083`. Stato NON AUTORIZZATO/NON ESEGUITO. Nessun comando VPS pendente prima del conferimento.

Scope concreto proposto: quattro file di evidenza (manifest e trust receipt già hash-pinned, image stage receipt e build-intent nel root adapter173408), più i sei file del contesto di build congelato sotto context. Nessun file configurazione runtime, TLS/PEM/MAC/OAuth/Env; niente Docker/image export/pull/build, rete/IAM/provider, scritture target, firma, consumerlink o avvio. Reader nofollow/regular/root0600/nlink1/ancestor e doppio read metadata/bytes del verificatore §40 riusato, con cap128KiB/file; output solo hash/esiti. Paths/binding del lab espliciti, nessun path da JSON privato aperto. Rollback non necessario per lettura; BLOCKED conserva prove e richiede analisi senza replay.

Verifica: manifest/trust §40 → image IDs/ruoli RO-RW; stage receipt = build intent; source52c0dcf/sourceURL/base digest/runtime user/payloadHash coerenti; sei bytes sorgente corrispondono ai checksum revisionati al pin; adapter label snapshot in trust e selezione APISIX3.18.0 del Gateway coerenti. Le sei fonti GitHub pinned sono state scaricate via connector e tutti i checksum confrontati con PAYLOAD_HASHES del builder52c0dcf:6/6 uguali. Nessuna ricostruzione dell'immagine o inventario target ripetuto.

**Limite:** il PASS attesta la lineage dichiarata dalle receipt e i bytes del contesto conservato, non i bytes installati dentro l'immagine, publisher trust, SBOM dipendenze/base, build riproducibile, OCI/rootfs/generation live o acceptance. Non assumere che un root-host compromesso non possa falsificare receipt non firmate. Questi limiti restano APERTI insieme al ponte observation→mandate; nessun nuovo prerequisito infrastrutturale o package source-only introdotto.

PET riesaminati per questo slice: Alignment Matrix v1.7/Terminology v1.1, Semantic9.2/10/28.11/28.11.1/159.2/160.6–160.7, Gateway supply-chain/vendor digest gate, Authorization36.10 e Onboarding92–92.3. Confini owner/THS e ricerca interna indipendente dai provider preservati. Dockerfile selezionato usa base digest pinned e cinque file Python senza installazioni pip; ciò non costituisce SBOM completo della base.

Test nuovi locali:8/8 PASS,0 skip (drift input, source/base/role sostituiti, hash coerenti ma binding errati, metadata drift, CLI isolata con zero scritture ed errori redatti). Wrapper bash-n e closure parity PASS. Test §39/40 già verdi riusati; CI estesa esegue11+7+8 test e tutte le parity. CI del checkpoint §40 `e14b424ba523dd4f024e8042043131ea441a52dd`:7 workflow PR completed/success. CI nuovo codice da verificare prima della richiesta VPS. Dopo PASS41 proseguire con prova mirata dei bytes immagine/provenance e raccordo temporale, senza firme/avvii impliciti.


## Checkpoint corrente — §40 ESEGUITO/PASS, non ripetere

Scope §40 conferito dall'utente «Autorizzo»; output operatore ricevuto 4 ottobre 2026, 21:28:07 Europe/Rome. Checksum OK; SEMANTIC_CONFIGURATION_PROVENANCE=PASS. Evidenza operatore, nessun accesso VPS indipendente. Pin eseguito `4e69bcf2a66abf75f0ec18db11c339293891f630`, wrapper SHA256 `1ab35491972810bc72a995c534e1bfc438f6f0c1e469b8dc8a3685e020c50b9b`. Receipt redatta: `docs/handoffs/receipts/SEMANTIC_CONFIGURATION_PROVENANCE_PASS_2026-10-04_OPERATOR.json`.

Sette evidenze e tre configurazioni lette privatamente: receiptChainConsistent, sealedConfigurationBytesConsistent, adapterBindingConsistent e routesMatchSealedPlan=true. Chiave TLS inline letta solo in memoria; PEM separati/Env non letti. ProviderCalls/signaturesIssued/targetFilesWritten=0; acceptanceGranted/startAuthorized/runtimeRegistered=false. Doppie letture stabili, non snapshot atomico. Non prova compiler replay indipendente, validazione crittografica chiavi, publisher provenance immagini, OCI/rootfs/generazione live o release acceptance. Non ripetere §40/39/38/36/34/31.

CI HEAD precedente `4f4416ec4f08d443ff79ef2cdfacc9267a85a903` riletta: sette workflow PR completed/success, inclusi i due prima in corso. I 18 test/parity già verdi restano prova ereditata, non rerun locale. PR26 draft/unmerged. Nessun comando VPS pendente. Prossimo lavoro autonomo: verifica mirata della lineage della build adapter e selezione southbound dalle receipt esistenti, senza rebuild/pull o accettazione automatica; risolvere anche il ponte observation→mandate prima di qualsiasi firma/avvio. Gli stati PREPARATO/non autorizzato/non eseguito sotto sono cronologia superata da questo checkpoint.


## §40 PREPARATO — scope di lettura privata non ancora conferito

§39 resta l'ultimo VPS PASS, storico; §38 private trust policy PASS preservato, nessun replay. Preparato il verificatore `tools/verify_semantic_configuration_provenance.py` e wrapper `docs/handoffs/commands/OUF_VERIFY_CONFIGURATION_PROVENANCE_2026-10-04.sh`, non eseguito. SHA256 wrapper `1ab35491972810bc72a995c534e1bfc438f6f0c1e469b8dc8a3685e020c50b9b`. Il wrapper contiene esattamente il verificatore testato; i root/owner sono espliciti e non derivati da JSON privato.

Scope proposto: lettura read-only redatta di stopped-manifest, launch-input-receipt, tls-runtime-receipt, trust-receipt, stage-receipt, binding e runtime-plan già esistenti, più adapter.json/config.yaml/apisix.yaml nei root storici. **apisix.yaml contiene la chiave TLS southbound inline, quindi il suo contenuto sarà letto privatamente in memoria**, senza stamparlo/copiarlo. Nessun file PEM separato, MAC key, southbound.env, credential/client-secret o offline CA key viene aperto. Nessun Docker/IAM/network/provider, scrittura sul target, firma, installazione, consumerlink, runtime registration o start.

Prova limitata: manifest SHA già noto→launch receipt→TLS/trust/binding→stage→plan; hash esatti dei tre output, adapter binding e routes rispetto al piano sigillato. Doppio read bytes/stat stabile, non snapshot atomico. **Non** replay indipendente del compiler, validazione crittografica chiavi/certificati, provenienza publisher immagine, ispezione Docker live/full OCI, generation/rootfs seal, né acceptance. I gate e il ponte observation→mandate restano aperti. I file di evidenza non conferiscono autorità.

Test locali: 7 nuovi test PASS +11 readback storico PASS, nessuno skip; CLI isolata senza scritture, errori redatti, hash/contract drift, symlink/hardlink/FIFO/owner/mode e metadata drift. CI del checkpoint §39 `8caee157822045e39305812953fdee295f889285`:7 workflow PR success. Nuova CI da verificare sul commit del verificatore prima della richiesta VPS. Ai sensi handoff§7.4, chiedere scope concreto per la lettura privata solo dopo wrapper pinned/testato; nessun comando pendente prima della risposta.

## Checkpoint corrente — §39 ESEGUITO/PASS, non ripetere

Output operatore ricevuto4 ottobre2026 20:41:08 Europe/Rome: checksum wrapper OK e SEMANTIC_ACCEPTANCE_METADATA PASS/HISTORICAL_ONLY. [Ricevuta operatore](receipts/SEMANTIC_ACCEPTANCE_METADATA_PASS_2026-10-04_OPERATOR.json). Nessuna ispezione VPS indipendente: letti solo4 JSON storici hash-pinned, mai contenuti mount/Env/PEM/Docker. Receipt34 ora ha hash noto `6b0814aefde46df9b849df9596b666cc5b99c74aa82bc4fbf71f292b0a189e43`. Fonte eseguita43011fe14ef31ea6b6378de618a6be2e8ddf6256, wrapperSHA0be85f2f2c1d6cbd7f5b0f86c396e6a1050c024adcc85950029b8980cab6b001; nuovo header documentale non modifica quei bytes immutabili. **Non ripetere39/38/36/34/31. Nessun altro comando VPS attualmente offerto.**

Matrice completata con8 metadati salvati al34: adapter4 file10006:10006/0600 (973,717,241,64 byte); southbound2 file636:636/0600 (742,12239 byte); stessa fonte trust-bundle root0:0/0644/225117 byte montata2 volte. Immagini confermate soltanto nel dossier storico: adapter8 layer descriptor/rootRO; APISIX9/rootRW. Source/destination/container ID e layer descriptor hashes sono nella receipt; nessun contenuto o path privato pubblicato.

currentTargetInspected/fullCreationAcceptanceProven/generationObserved/acceptanceGranted/atomicSnapshotProven/runtimeRegistered/startAuthorized=false; targetFilesWritten/privateKeysRead/signaturesIssued/providerCalls=0. Ultimo intervento VPS39 PASS non sostituisce privatepolicy38 PASS; ruolo firma/consumer/start non conferiti. [Piano aggiornato](../installation/SEMANTIC_CANDIDATE_ACCEPTANCE_PLAN_2026-10-04.md). Prossimo lavoro autonomo: verifica privata reviewable delle configurazioni/provenance e raccordo osservazione→mandato, con codice/test/CI prima di qualunque richiesta di lettura privata o nuova authority. Nessuna autoacceptance o staging source-only. CI codice43011fe e documentiaab0f3e:7 workflow PR/9 jobs SUCCESS riletti,11 test PASS/0skip; CI di questa registrazione da verificare.


## Checkpoint corrente — §39 preparato, NON ESEGUITO

§38 rimane ultimo VPS ESEGUITO/PASS; nessun replay31/34/36/38 o creazione. Ripartenza dalla sezione7 completata per analisi/contratti/matrice: [piano di accettazione](../installation/SEMANTIC_CANDIDATE_ACCEPTANCE_PLAN_2026-10-04.md) con2 immagini/8 slot mount, provenance/mutabilità, binding OCI/rootfs/generazione, limiti temporali e rollback. Dati privati esatti owner/mode/destinazione non ricevuti: prossimo unico intervento §39 legge soltanto metadati storici da4 file sigillati, senza inspect target, Env/mount contents/PEM/Docker/DNS/IAM, firme o scritture target.

[Wrapper39 completo](commands/OUF_READ_ACCEPTANCE_METADATA_2026-10-04.sh), SHA256 `0be85f2f2c1d6cbd7f5b0f86c396e6a1050c024adcc85950029b8980cab6b001`, stato **NON ESEGUITO**; pin immutabile del wrapper è 43011fe14ef31ea6b6378de618a6be2e8ddf6256.11 test locali PASS/0 skip, CLI isolata/no-write/redaction/filesystem/hash/drift; bash-n e parità wrapper/reader PASS. CI codice al commit 43011fe14ef31ea6b6378de618a6be2e8ddf6256:7 workflow PR/9 jobs restituiti SUCCESS,11 test readback confermati nel log111502111965; la CI della registrazione documentale successiva resta da rileggere; nessun esito VPS39 inventato. Rollback39 non necessario perché non modifica il target; BLOCKED conserva originali e richiede analisi senza replay.

HEAD verificati prima delle modifiche: Semantic coordinamento7b0ed8b/PR26, Gateway3bdedad/PR56, Semantic workloadc2b4ae5/PR30; tutti OPEN DRAFT/non merged. Workflow PR riletti: rispettivamente6/2/6 SUCCESS, jobs restituiti tutti SUCCESS; il connector restituisce prima pagina dei run PR, non audit universale push/check suite.323 checksum PET allegati verificati/0 mismatch. Nessun test applicativo già verde rieseguito indiscriminatamente.

Punti concreti lasciati aperti: Docker stopped non dà generation; adapter prepare in start dopo final network setup richiede raccordo osservazione→mandato prima del broker (non pausa HUMAN dentro18s); rootfs host non sostituisce bind mount acceptance; transazione stopped32hex distinta da deployment64hex; runtime runc non si migra con sola registrazione. Nessun nuovo package source-only; consumer/signing/runtime/start/reboot/merge non autorizzati. Filo prodotto interno→mapping→THS→ACTIVE→Ingestion→UDP preservato, Cinema/Teatri non rifatti. Dopo output39 aggiornare autonomamente4 documenti e comando, completare matrice con metadati ricevuti e preparare revisione privata nel solo scope necessario.


Checkpoint: 4 ottobre2026, 19:42 Europe/Rome. Questo è il punto di ingresso corrente: sostituisce le istruzioni di ripartenza storiche, non cancella evidenze, gate o ricevute. La chat viene chiusa per ripartire puliti; non eseguire ulteriori attività tecniche durante la preparazione dell'handoff.

## 1. Stato in trenta secondi

Ultimo comando VPS **§38 ESEGUITO: plan/apply/verify PASS**, root `/etc/ouf/deploy-snapshots/semantic-trust-policy-preparation-20261004-172336`. Due grant/tre ruoli ACTIVE soltanto nell'artefatto privato, nessun consumer collegato. Due candidati provider ancora mai avviati; ultimo runtime attestato RUNTIME_EMPTY, provider sets vuoti. Nessuna nuova chiave/firma/mandato/call DNS/IAM/provider in §38, nessuna modifica regole/unit/container.

**Nessun comando VPS pendente/offerto da eseguire.** Non ripetere §38, custodia36, inventory34, recovery31, creazione candidati o vecchi wrapper. Il prossimo lavoro autonomo è il piano tecnico di accettazione concreta dei2 candidati/8 mount e binding full OCI/rootfs/generazione, riusando codice e dossier esistenti. Firme operative/mandati, consumer link, runtime registration, start, restart/reboot e merge non sono autorizzati implicitamente.

Obiettivo di prodotto ancora aperto: CSV/XLSX/GeoPackage → chatbot/MCP → Onboarding/profiling → ricerca/mapping semantico → review THS → ACTIVE → Ingestion/RAW/handoff → UDP/identità/materializzazione → serving autorizzato. Le fasi manuali già corrette non vanno rifatte; va completato il collegamento generale e governato. Il provider esterno è un ramo necessario quando la semantica interna non basta, non una dipendenza universale di qualunque ingestion.

## 2. GitHub, branch e prove verificate ora

| Repository | Branch / pin | Stato |
| --- | --- | --- |
| GioNob/ouf-api-gateway | codex/semantic-provider-request-boundary, `3bdedad3108112ee4c36e7cb8387aaf60912e97c` | PR56 OPEN DRAFT, non merged;38/38 check SUCCESS riletti. |
| GioNob/ouf-semantic-registry — coordinamento | codex/r4a-smoke-semantic-inventory, `53699493fa4c52c7f0e6ef62bbad306525d38f9c` prima di questo handoff | PR26 OPEN DRAFT, non merged;13/13 check SUCCESS riletti. Il commit contenente questo handoff diventa il nuovo HEAD, leggere il branch per il pin finale. |
| GioNob/ouf-semantic-registry — workload auth | codex/semantic-provider-workload-auth, `c2b4ae5abed1236378c7060b3eb3dac126672cbc` | PR30 OPEN DRAFT, non merged, head riletto ora;14/14 CI era verificata nel precedente checkpoint, non riletta oggi per questo branch. Incremento non dimostrato deployed/live. |

Links: [PR56](https://github.com/GioNob/ouf-api-gateway/pull/56), [PR26](https://github.com/GioNob/ouf-semantic-registry/pull/26), [PR30](https://github.com/GioNob/ouf-semantic-registry/pull/30). Non confondere main, head PR, immagine staged, container live e release acceptance. Nuova chat: rileggere head/PR/CI prima di mutare, senza ripetere test già verdi salvo nuove modifiche/rischi. Altri branch/PR ereditati restano da riconciliare, elencati sotto.

Gateway: suite locale privata policy46 PASS/0 skip (15 nuovi policy +17 keycustody +14 authentication); CI root job111486419048:201 unit+2 native preparer+2 target native PASS senza skip. Queste prove sono software/CI, non authority/startup target. Vecchie suite locali contenevano skip Docker/Go; quei test sono stati eseguiti in CI, non trasformare uno skip in PASS locale. In questo checkpoint nessun nuovo codice runtime o test applicativo introdotto; verifica documentale/receipt/wrapper e CI documentazione da completare sul nuovo commit.

## 3. Regole di lavoro vincolanti, valide nelle nuove chat

**Validazione obbligatoria.** Prima dell’implementazione, verifica il flusso, le dipendenze e i principali rischi logici, di concorrenza, memoria e compatibilità. Correggi autonomamente i problemi individuati e valida il risultato con test pertinenti e CI. Presenta il codice completato insieme alle verifiche eseguite e agli eventuali limiti residui. Non dichiarare superata una verifica basandoti soltanto sull’auto-revisione.

**Autonomia e completamento.** Procedi autonomamente entro l’obiettivo concordato. Risolvi le scelte tecniche privilegiando coerenza con PET e repository, semplicità, reversibilità e scalabilità necessaria; documenta le decisioni nell’handoff senza fermarti per scelte ordinarie. Mantieni aggiornati handoff, roadmap, manuale e sprint, comprese le sezioni dei comandi eseguiti. Fermati soltanto quando serve un’azione sul VPS, un’informazione indispensabile o una decisione di autorità non già conferita. Niente merge, avvii o replay impliciti.

**Checkpoint.** Lascia sempre un risultato verificabile: commit, stato dei test/CI, lavoro completato, questioni aperte e prossimo passo preciso. Se un blocco impedisce una parte, completa comunque le attività indipendenti.

Regola rafforzata dell'utente: procedere “a nastro/a manetta”, uno step dopo l'altro; non fermarsi per chiedere se continuare, scegliere nomi/strutture ordinarie o riautorizzare analisi/codice/test/docs già nel piano. Preparare un risultato concreto e reviewable prima di chiedere una nuova autorità. Un checkpoint non è un motivo per fermare il lavoro autonomo; questa sospensione è chiesta espressamente per cambiare chat.

Ulteriori vincoli permanenti:

- **Ogni Ente installa una piattaforma indipendente**, senza tenant collegati o controllo centrale tra Enti. Migliaia di adozioni significa migliaia di installazioni; non progettare un'istanza multitenant centrale. In una stessa installazione i servizi possono stare sullo stesso server/rete/subnet o distribuiti su server/reti differenti. Parametrizzare tutti i binding, non universalizzare i valori del lab; coerenza PET prima della scalabilità non necessaria.
- Non presumere SSH/sessioni/account. Qui il VPS è operato dall'utente oufadmin con wrapper pinned, checksum e output redatto; GitHub via connector. Non confondere SSH/master oufadmin con utente HUMAN MCP ouf-admin. Non ricostruire account routing/link_id di vecchie chat.
- Conservare prove/backup/rollback/tentativi falliti e root sigillati. Non riscrivere cohort in place, rigenerare keypair, rifare upload/profile/job o replay Cinema/Teatri per comodità. Nessun force su container estranei/avviati o cleanup non verificato.
- Consegnare **un solo wrapper completo e corretto** per il prossimo intervento, checksum/pin/mode/rollback/binding espliciti; non lasciare errore+pezzo di riparazione come procedura fresh install. Le recovery storiche restano nel registro. Dopo output aggiornare autonomamente stato ESEGUITO/PASS/BLOCKED nei4 documenti e comando; vecchio commit immutabile non si modifica.
- Non stampare token,secret,private key,Env completi,mount contents,payload raw o log integrali. Ricevute/dossier restano privati sul VPS; GitHub contiene hash/conteggi/stati. Python host -B; -I quando previsto dal wrapper. Tutti hostname/endpoint/path/UID/GID/reti/porte/issuer/scope/timeout/limiti sono parametri espliciti.
- Snapshot stabile su letture ripetute non significa atomico. CIverde/build/staging/ACTIVEgrant/signaturavalida non significa deploy approvato, consumerlinked, startup o release acceptance. Distingui verifica effettuata ora, outputoperatore, prova ereditata e limite aperto.
- L'utente osserva disconnessioni dopo circa33minuti: causa non provata. Salvare checkpoint frequenti su GitHub e comunicare avanzamento; non attribuire a stringhe “preexec”, filtri o overflow senza evidenza. Una chat interrotta non dimostra task finito: controllare commit/CI prima di affermarlo.
- Evitare duplicazione codice già sviluppato o ripetizione indiscriminata test/manuale. Workspace può essere dirty o effimero: pubblicare solo file mirati su tree GitHub fresco, non tutto il checkout. Nessun merge automatico/main mutation; PR restano draft.

## 4. Ultimi PASS VPS e hash da riusare

Tutti i path seguenti sono binding del lab sotto `/etc/ouf/deploy-snapshots/`, non default prodotto. Evidenza output operatore, non accesso SSH indipendente dell'agent.

| Fase | Root e binding | Stato |
| --- | --- | --- |
| §31 recovery v8 | semantic-local-producers-package-20261004-121542; source `7ded9df0c74c6db919c7a68d4c75ab2c132dea53`; manifestSHA `a1b11fbfb9d701101f2efa1048c7f99a54f123ed1f1b71f480ffcd883c0e560b` | plan/apply/verify PASS via recovery directory0755→0700.26 sorgenti sigillati; producer/preparer/adapter non installati, runtime non registrato. Non replay v8stage/recovery. |
| §34 target inventory | semantic-target-acceptance-inventory-20261004-151023/prepared | PASS,2 candidate neverstarted,8 mount metadata/stat, non letti Env/mountcontents/privatekey. DossierSHA `a37f22635035ab8543a4654def5cd6a6f4fe45fd1affc0ff10ccc3c19f03085c`; authorityPlanSHA `31492d13db05b46252215bb4bde815712bd55a1e245aff25408350328fcb7093`; packageReceiptSHA `f06c4b6ea2a7c05e008db3e615e35f475d44824b2073ff2d5f451c55dbce2850`. Non full OCI/rootfs/provenance/content acceptance. |
| §36 key custody | semantic-authority-provisioning-20261004-164654 | plan/apply/verify PASS.2 chiavi generate e2firme sintetiche selftest in apply, verify0nuove. DraftSHA `a9e5bdbef01c391c216e23e7b99c9e9ed3d6e3a92da56e8e1e9d7b2ca91b040c`; custodyReceiptSHA `a134c4c8e8487860e6a8ed3a672520935a5de753d02507c4005a0475570b2d49`. Binding public/private verificato al36; zero firme operative/mandati. |
| §38 private policy | semantic-trust-policy-preparation-20261004-172336 | plan/apply/verify PASS; policySHA `21122630e52cb63c3744fee89f5c81ed926dad55231190243ca11be6d481bd42` in tutti3modi; receiptSHA `42d27903c65e6a1334fff5647a817e393a661e27f5c4fbf69c8d7910a6abb7ab` apply/verify. Originalvaliditypreserved, parserreale/publicbinding/custodyreceipt verificati. ZeroPEMreads/newkeys/signatures/mandates/calls. |

§38 wrapper eseguito `docs/handoffs/commands/OUF_PREPARE_TRUST_POLICY_2026-10-04.sh`, **commit immutabile `dad24714ca572ab45667313b8cc7ec748c851ce3`**, SHA256 `1b3927170ba06722402050a25eb12d50bf3d5886ea443b5a1e5866770a573857`. Download/install checksum tuttiOK. L'header del wrapper corrente ora indica ESEGUITO e cambia l'hash documentale: confrontare i bytes eseguiti con il vecchio commit, non con l'header nuovo. **Non eseguire di nuovo.** [Ricevuta operatore](receipts/SEMANTIC_PRIVATE_TRUST_POLICY_PASS_2026-10-04_OPERATOR.json).

Source38 Gateway3bdedad, prepare_semantic_trust_policy.py SHA `b06cd1712588cf5c01eaec913202abe11667f68bb29ec3ed5121949abff036bf`; helper prepare_semantic_authority_keys.py SHA `095a9cd9523bc1ee2767737656884ff7e08b254a6b1aab015c977403e2b1e3ec` dal commit `509a011cd920d9a9e9ece83a07e5b99ce05806a5`. Parser v8authenticationSHA `3f89e466638cdbb8311b661b64739c1903969758cb3bcf569d53cbdaa620386a`, protocolSHA `87bb4cdaf6686aadbde69caddf1d1813ecc02664aeeef62b67dd80750adc15b1`. OpenSSL `/usr/bin/openssl`3.5.7 SHA `f4aa15f2822f670af7b5c1043d7aa6ebbbc64229fd2fae382edfc6a4524749c1`. Dates originali90 giorni del draft preservate, non rinnovare. Privatepolicy outputs trust-policy.json e policy-preparation-receipt.json root0600, root700.

Storico BLOCKED preservato: §30v8plan PRIVATE_PACKAGE_DIRECTORY_REQUIRED, poi risolto31; §32inventory BLOCKED, §33diagnostic root semantic-target-acceptance-diagnostic-20261004-145230 BLOCKED IMAGE_INSPECT/TARGET_ACCEPTANCE_INVENTORY_UNPROVEN, poi corretto34 Docker29optionalConfigfields. Questi BLOCKED non sono lo stato corrente, non replay né cancellazione. Freshinstall wrapper canonico corretto è distinto dalla recovery già eseguita; non farlo girare sull'installazione esistente.

## 5. Autorità effettivamente conferita e limiti del modello

Scope35 conferito17:57:37 Europe/Rome:2 keypair privati e draft inerte, completato36. Scope37 conferito18:58:29 dall'utente “autorizzo”: soltanto preparazione privata della policy di verifica ruoli sui keypair esistenti, completato38. Non chiedere nuovamente questi conferimenti.

| Grant nel file privato | issuerRef / keyRef | Ruoli |
| --- | --- | --- |
| Installer | ouf-lab-infrastructure-installer / ouf-lab-installer-ed25519-1 | DEPLOYMENT_INTENT, FINAL_DEPLOYMENT_APPROVAL |
| Attestor | ouf-lab-node-attestor / ouf-lab-attestor-ed25519-1 | CREATION_ATTESTATION |

Scope installationRef `ouf-lab-netcup-01`, entityRef `ouf-lab`. policyGrantState ACTIVE e policyActiveInArtifact=true in apply/verify; **policyConsumerLinked=false, policyActiveInConsumer=false, trustPolicyInstalled=false, roleSigningAuthorized=false, startAuthorized=false, runtimeRegistered=false, deploymentAuthorityProven=false, atomicSnapshotProven=false**. currentPrivateKeyBindingsReverified=false al38, coerente con noPEMreads; non sostituisce il binding verificato36. Admission fullcreation ancora non provata.

Installer intento+approvazione stessa chiave è scelta deliberata lab a operatore singolo, non four-eyes. Distintoattestor deve autenticare creation/mandatoaccettazione e legareintent/container/transaction/artifact/OCI/transport/runtime/generation. Installerkey sola non può falsificare attestor, ma può abusare di evidenzecompatibili ancora valide; non dichiarare immunità dopo compromissione. Max300 s riguarda payload/mandati, non lifetime della chiave: chiave rubata può emettere altri payload finchégrantammesso/nonrevocato/scaduto.90 giorni grant è finestra distinta. Due chiavi sullo stesso root host non proteggono da root né costituiscono due persone indipendenti.

Produzione/multinodo: Ente decide separazione proponente/approvatore secondo governance/threatmodel. Il formato consente1..32keyRef diversi; non introdurre nuovechiavi/authorityimplicitamente. Attestor futuro per nodo con issuer/key distinti e selezione esplicita attestor atteso nel deployment; non ammettere qualunque key aventeruolo. Binding nodo/prove susecondonodo reale restano APERTI, non implementarli per inferenza dal lab.

## 6. Codice già disponibile: riusare, non ricominciare

Nel Gateway branch3bdedad esistono shared-facecompiler,guard/leasecoordination,preexecnative,hookOCI,adapterrunc,admissionpreparer,protocol/consumption/authentication/reauthorization,broker,installerapproval,nodeattestor e key/policybuilders. Il packagev8 target è sigillato7ded9df; headrepo non significa package target aggiornato. Non migrare closure/package alla cieca.

Leggere prima questi file Gateway: tools/semantic_provider_deployment_protocol.py, semantic_provider_deployment_authentication.py, semantic_provider_deployment_reauthorization.py, semantic_provider_deployment_producer.py, semantic_provider_deployment_consumption.py, semantic_provider_installer_approval.py, semantic_provider_node_attestor.py, semantic_provider_node_observation.py; scripts/semantic_provider_deployment_broker.py, semantic_provider_docker_runtime.py, semantic_provider_admission_preparer.py, semantic_provider_preexec_hook.py, inventory_semantic_target_acceptance.py e prepare_semantic_trust_policy.py. Guide Semantic: [broker](../installation/SEMANTIC_LOCAL_DEPLOYMENT_BROKER.md), [authority](../installation/SEMANTIC_DEPLOYMENT_AUTHORITY_PROVISIONING.md), [keycustody](../installation/SEMANTIC_AUTHORITY_KEY_CUSTODY.md), [policy](../installation/SEMANTIC_PRIVATE_TRUST_POLICY_PREPARATION.md), [decisione lab](../installation/SEMANTIC_LAB_TRUST_POLICY_DECISION_2026-10-04.md).

La policy38 usa il parser puro reale estratto da sorgenti v8 hashchecked, senza eseguire corpi/import producer; helperstdonly caricato da bytescheckati, no main. publicDER/draft/receipt/selftest publicverify soltanto, lock rootexclusiveNB/fsync/receiptlast/nooverwrite. Freshness checkedseparatamente perché il parserformato non usa now.15 testincludonoparity/crash/concurrency/expiry/tamper/redaction/CLI. Non riaprire questa preparazione senza nuovo problema concreto.

NodeAttestor.acceptance richiede mandato firmato CREATION_ATTESTATION schema ouf.semantic-node-creation-acceptance-mandate.v1, completeCreationAccepted=true/attestationAuthorized=true, exacte request/intent/generation/rootfsSeal, finestra entrointent. emit verifica brokerPREPARING, full OCI/liveobservation e rootfsSeal uguale a quello approvato, poi firma e ricontrolla. NodeObservation.rootfs_seal stream bounded metadata/contenuti/xattr senzaexclusion, nofollow/specialfiledeny/deadline. **Nessun digest costituisce da solo autorità.** Unrootfs live e namespace/generation possono esistere soltanto nella fasepreexecautorizzata, non inventare generation dai container fermi senzaSandboxKey.

## 7. Prossimo passo preciso e ordine di lavoro della nuova chat

1. Leggere questo handoff intero,4 documenti canonici e guide sopra; controllarebranch/PR/CI e PETdisponibili. Non assumere filelocali/SSH/sessioni. Breve conferma dell'ultimoPASS e poi lavoro autonomo; nessun comando VPS già da eseguire.
2. Analizzare contratti attuali e dossier34 (forma descritta dall'inventoryscript, i contenuti privati restano sultarget), manifest/journal creazione e producer/broker/nodeconfig. Preparare **matrice d'accettazione concreta** per2 immagini/8 mount: fonte/provenance/immutabilità,destinazione/RO-RW/owner/permessi,contenuti revisionati vssegreti/runtimegenerated, driftbounds,rollback. Distinguere cosa è già provato e cosa richiede lettura privata o osservazionepreexec. Il count8 o imageinspect non equivalgono fullacceptance.
3. Definire binding full OCI/applicationHash/artifactHash/transport/runtime/generation/rootfsseal e sequenza intent→create/preexec→nodeacceptance/attestation→finalapproval→consumption, guard/leasefailclosed. Risolvere dipendenze temporali: niente mandati300 s emessi ora per uso futuro e niente generation/rootfs fittizi. Preparare configurazioni/piani/test e decisioni reviewable, senza consumerlink o firmaoperativa. Non creare ulteriori package source-only per simulare gates chiusi.
4. Se manca dato privato indispensabile, realizzare/testare un wrapper **read-only e redatto** mirato al dato necessario, pinned/hash, senza stampare Env/contenuti mount/private keys o mutare candidati. Se serve lettura privata/conferimento nuovo, chiedere scope concreto dopo preparazione. Non dichiarare acceptance autoapprovata. Le attività indipendenti proseguono.
5. Solo dopo acceptance/authorityesplicite pianificare install/consumer/issuer signing/runtime registration e fasepreexec/start distinti. Non usare il “prosegui” generico come scope per firme/avvii/reboot. Conservare guardEMPTY_ONLY finoa transizionecorretta; verificare coordinationlease/revoca/commonlock e sharedinterfaces sourceenforcement, namespacebinding/spoofIPv6/OIDCpurposeTLSadmission, rollback/recovery e realreboot. StartupReady non attestato.
6. Tenere il filo del prodotto: dopo gate provider necessari per il ramoexternal, collegare Discovery/lookup/definitions/adoptionexactrefs al mappingassistant, THS e ACTIVE/fileingestion. Procedere anche sulle attività interne indipendenti dai provider quando autorizzate, preservando fixtures/test già manualmente corretti. Non cambiare obiettivo né aprire architettura multitenant.

Gateprovider readiness ereditati tutti da distinguere da componentisoftwareCI: INFRASTRUCTURE_AUTHORITY, SHARED_FACE_SOURCE_ENFORCEMENT, LIVE_NAMESPACE_ADDRESS_BINDING, PACKET_SPOOF_BYPASS_IPV6, OIDC_PURPOSE_TLS_REVOCATION_ADMISSION, ACTIVE_LEASE_GUARD_COORDINATION, REAL_REBOOT. atomicSnapshotProven=false, activeLeaseLifecycleReady=false/startupReady=false all'ultimo inventory. Reboot/releaseacceptance aperti.

## 8. PET, responsabilità prodotto e ragione del ramo deploy

Dal ciclo ingestion si è passati al ramo deploy perché la discovery esterna richiesta dal mapping ha introdotto un percorso southbound reale verso un endpoint esterno: separazione di identità/credenziali/TLS/egress, deny prima dell’esecuzione, namespace e lease, poi evidenze di creazione e approvazione. Per evitare una configurazione solo manuale del lab, il lavoro è diventato riusabile nelle installazioni autonome. Questo spiega la dipendenza del ramo esterno, ma non chiude il ciclo ingestion né giustifica ulteriore staging inerte: il prossimo gate deve produrre acceptance/configurazione concreta e riportare al mapping, preservando il percorso interno indipendente. Non inventare altri prerequisiti di piattaforma a ogni checkpoint.


Semantic/Registry esegue ricercaesterna, Gateway governa southbound/egress, endpointSPARQL **schema.gov.it default parametrizzabile**, es.schema.maggioli.it configurato all'occorrenza; non arbitraryURL/SPARQLda chatbot. Chatbot/MCP ricerca/consulta/confronta/proponemapping; non agenteAIinternoOnboarding. THS governa decisioni HUMAN/pubblicazione/adozione/merge; Onboardingvalida/persistesourcemapping, Semanticversionaartefatti, UDPdecideidentitycanonicale dopo handoff. Non attribuiresearchesternaalchatbot o Onboarding. Gateway non ETL/dominio. Filemanualegestito→ingestiononetimeimmediata dopoACTIVEcompatible, nonschedulerperiodico; APIverticalescheduler distinto, Onboardingnonpolling. Dubbi/quarantene durable/idempotenti, nontransazioneDBaperta in attesaHUMAN.

### Documenti normativi e disponibilità

[Roadmap](../OUF_ROADMAP_PET_1_7.md), [manuale installazione](../installation/OUF_INSTALLATION_MANUAL.md), [sprint](../sprints/OUF_ACQUISITION_TO_UDP_2026-10-02.md), storico [1 ottobre](OUF_HANDOFF_2026-10-01_FILE_TO_UDP_NEXT_SPRINT.md), con registro gate ereditati e collegamenti agli handoff 25/27/29/30 settembre e audit 27 settembre. Le sezioni cronologiche vecchie non sostituiscono questo checkpoint attuale.

Normativa: L0 Alignment Matrix v1.7; Source Onboarding v1.6 §§92–92.2 e THS; Semantic v1.3 §§9.2,10–11,17–18; UDP v1.3 §§21–22,109.2,109.6–109.9; Authorization v1.5 §36.10; MCP v1.4; Gateway v1.5. Gateway prescrive confini northbound/southbound distinguibili per route, policy, credenziali, log e zone; il proxy non fa ETL né decisioni di dominio.

Pacchetto letto nella chat: `OUF_Reality_Baseline_Package_v1_7(20261001-185201).zip`, SHA256 `e63df67e8817eec38a9d4b3eb736b020f693b932f3360dc02f4555330f2201ce`; 323 checksum interni verificati senza mismatch. Nel vecchio workspace esistono `baseline/OUF_Reality_Baseline_Package_v1_7/` e `pet-text/`. Possono non sopravvivere alla nuova chat. Verificare disponibilità autorizzata; se mancano, richiedere il pacchetto normativo. Non accedere alla Library di altre chat e non trattare questa sintesi come sostituto PET. Si può proseguire il readback già preparato senza reinterpretare una norma assente.


## 9. Baseline e ricevute target ereditate, da preservare

Questa sezione riporta binding/prove dei checkpoint precedenti, non nuovo inventario live. La tabella deny-only originale è storica: ultimo stato runtime attestato è RUNTIME_EMPTY/EMPTY_ONLY; la creazione stopped non è l’ultimo intervento complessivo.

### 9.1 Container produttivi e policy

| Ruolo | Revisione live / digest |
| --- | --- |
| Semantic `ouf-semantic` | `e7bc5190f9e6afbbc4cf3c90d5d4970afbfad14b`, `sha256:f6525f2512c72a600ebcbc7060d55355d86e0627487b655e7c5c6288a0be7fc6` |
| MCP `ouf-mcp` | `394b4b1540b575564f0ba58541df9d7efc59fb87`, `sha256:99a158f780243b3fa05199bed9db01197be8ae60ae1e75ad5432964509422872` |
| Gateway `ouf-apisix` | APISIX **3.18.0**, image `sha256:84e6b5e787e9f889ebff88161cb9a16599bafcffa236c6b54c7f779a0655940d`, c14d3f23-derived routes |
| Onboarding | `6340d5bf120e09b47c32177656e2c377a4c03640`, `sha256:ec6f2a962261a8433bfe103347afa2202837fcec90d210d9b5232711b854ee8a` |
| Ingestion | `163c167d09b8371ff7a62ce7068e9d485b6969b7`, `sha256:b07a4a786ca48335feae887e18dc7c4c6cdd9bd0a3a255f83d18c7c1616eec48` |
| UDP | `83249a897eb4add4289b5181b3299f48ea4c0f99`, `sha256:5e048a859716d6674355e72238f03f899abd705a943ceadbdc5c8863d28f4e9f`, Flyway34 |

Last observed IDs: live Gateway `dcbe26bed97dd5c7ac8a131ec2badf77b0291c2ef32907be639bfa09c36596d9`; Semantic `7ae83be8c1fe9fe25774b7d748e35153652b29b2501886f89daeabb83bd1a147`; Ingestion `1fa5450574e72ef15ebb2c74e0f421f04d24c842975e324ac958f071672fbb7e`. These are readback bindings, not permanent role defaults. Other shared infrastructure (Caddy, etcd, Keycloak, MinIO, Postgres, operational owner) was not switched in the provider preparation.

Authorization remains **ouf-lab-authorization:38**. Historical :36 recovery grants expired; don't reuse them. `gateway.southbound.invoke` and `ouf.semantic.discovery` scopes exist/no drift; only `gateway.southbound.invoke` DEFAULT-bound to **ouf-semantic** SERVICE. Discovery scope not client-bound/descriptor not registered or published at last inventory. Provider disabled, live workload/provider OAuth configuration uninstalled, worker enabled, queue/adopted/unexpired counts zero at inventory. HUMAN discovery/MCP binding and live provider connectivity unproven.

Calling workload: `ouf-semantic` existing confidential service account. Private credential `/etc/ouf/semantic-provider-auth/client-secret`, UID/GID10001,0600; prepared/verified, no rotation. RS256/JWKS signature, SERVICE claims/tenant/audience/TTL299 verified; introspection inactive was corrected by signature verification. Revocation and Gateway admission not proven; no mount on live Semantic.

Passive OIDC validator: **ouf-api-gateway**, enabled/confidential/client-secret, **serviceAccountsEnabled=false**. It validates bearer/JWKS; do not enable service accounts or invent a second M2M identity. Validator credential is distinct from caller credential. Successful master login administrative user **oufadmin** was explicitly observed; SSH user alone is not evidence of KC identity. Session may expire; the §6 inventory does not use kcadm.

Issuer `https://auth.ouf-lab.it/realms/ouf`, token endpoint `/protocol/openid-connect/token` under issuer; MCP execution `https://api.ouf-lab.it/internal/capabilities/v1/execute`. These are explicit lab configuration only.

### 9.2 Receipt roots — absolute paths are host bindings, not defaults

All roots below are under `/etc/ouf/deploy-snapshots/`; keep private root ownership/modes and referenced cohorts. Preparation flags describe time of receipt, not current mounts after creation.

| Preparation | Exact receipt relative to parent | Proven / residual |
| --- | --- | --- |
| Adapter image | `semantic-provider-adapter-20261002-173408/stage-receipt.json` | image `sha256:a697bf75bf7d51afadadfaccd3d80537e9a5fb2a08f0d194c6dfd9462e812468`, source `52c0dcf11654a4d3d0f17a6902ed095975466fb9`, UID10006; now created stopped, no rebuild. Base `python@sha256:bb2988715db2cf7ace7b53f38f3cffbef7c7046a656bee66245eb0ed386e2e81`. |
| Trust PKI/MAC | `semantic-provider-trust-20261002-212033/trust-receipt.json` | CA/public-root merged bundle/role leaves/purpose MAC pair verified. Offline ca.key never mounted/read by launch; role files individually RO mounted on stopped candidates. |
| Runtime plan | `semantic-provider-runtime-20261002-222530/stage-receipt.json` | root-private binding.json/runtime-plan.json compiled; native runtime activation not proved. |
| TLS startup | `semantic-provider-tls-runtime-20261002-230418/tls-runtime-receipt.json` | config.yaml/apisix.yaml/adapter.json prepared, now mounted RO on stopped candidates. apisix.yaml includes private leaf key: never cat. |
| Java trust | `semantic-provider-java-trust-20261003-061729/java-trust-receipt.json` | merged public roots preserved for selected old Semantic image; private PKCS12/JVM options UID10001, no private keys. Not mounted on live Semantic. Recheck public roots for future selected PR30 image. |
| DNS observation | `semantic-provider-dns-20261003-063746/dns-receipt.json` | Historical only, one address observed, **no kernel lease**. Expired observation must never seed runtime sets. |
| Cold networks/guards | `semantic-provider-networks-20261003-072023/prepared/network-receipt.json` | Two dedicated networks + owned inet/bridge deny-only tables installed. Candidate configuration now exists: old EMPTY predicates are historical. |
| Lease source package | `semantic-lease-package-20261003-075940/source-package-receipt.json` | Nine sealed files staged, no daemon/unit installed or started. Reuse frozen cohort. |
| Boot stage | `semantic-boot-guard-20261003-083310/boot-stage-receipt.json` | Sealed deny-only restore profile, unit and Docker drop-in. |
| Boot installation | `semantic-boot-install-20261003-103547/install-journal.json` | Plan/apply/verify PASS, loaded guard/drop-in, Docker PID1740 preserved, no restart/rule/provider call. Real reboot unproven. |
| Candidate-input inventory | `semantic-candidate-inputs-20261003-111502` | Original false block retained; corrected inventory-public-trust-fix.py PASS. Do not reuse bad original inventory.py. |
| Validator credential | `semantic-southbound-validator-20261003-114001/prepared/credential-receipt.json` | Existing secret private copy636:6360600, current profile/secret verified; no rotate/config/grant. |
| Launch inputs | `semantic-provider-launch-inputs-20261003-124906/prepared/launch-input-receipt.json` | Leaf key pairs/receipt MAC pair verified, root0600 southbound.env created; no offline CA key read; no grants/providers. |
| Stopped manifest | `semantic-provider-candidate-manifest-20261003-130410/prepared/stopped-manifest.json` | Sealed exact images/mounts/network/IP/resource specs; initial no-container/no-reservation state historical. |
| Static IPAM | `semantic-provider-static-ipam-20261003-133526/prepared/ipam-receipt.json` | Target accepted never-started disposable static create on all THREE existing networks; probes removed; no address reservation/packet proof. |
| Actual stopped creation | `semantic-provider-stopped-create-20261003-135106/prepared/creation-journal.json` | Two actual candidates, owned transaction/manifest labels, never started, checked strict config/env/RO mounts/net IDs/static IP config. Historical stopped-creation PASS; later PASS38 recorded above. |

Metadata pitfall resolved: public trust-bundle.pem225117 bytes/root644 was incorrectly subjected to 131072 private-JSON cap. Only public CA/trust bundle cap raised to1MiB; private JSON/ownership/mode/link/ancestor checks preserved. Correct inventory source840abe...; no chmod/chown of valid artifacts needed.

IPAM pitfall resolved: one CI daemon rejected static IP on an auto-allocated subnet. This did NOT prove the target incapable. Target Docker29.8.1 positively accepted static create on backend/internal/egress. **Do not recreate/normalize these networks, rebind boot guard or restage all artifacts for that old inference.** Do not infer causality from daemon version alone; evidence is the target probe.

### 9.3 Source pins for frozen helpers

| Helper | Source commit | SHA256 |
| --- | --- | --- |
| create_semantic_provider_stopped_candidates.py | `93e861fe8c8a43912f0cb78a74adceb2db509dd9` | `4babe7ebfdffe6ef1ab4f81bacad52c86eabbbe991d30bf3c41de65d7f47ffdd` |
| stage_semantic_provider_candidates.py | `9596f450ccb2ee38730b147e22e58ceaafd52841` | `cb04a31e4d13e182b08de2df75fa13a4ec01a7c0671239339451523f2dfc9f84` |
| prepare_semantic_provider_launch_inputs.py | `732d65a8bcebb1545086702da54ee01c01c3b823` | `4a5483d5ff54bdc79ef26e4ae436ac41ebd12363be0640005d1d6f695df93e8d` |
| prepare_semantic_southbound_validator_credentials.py | `faaf43748648207f51edee890be4b3dc6592cfc5` | `3d349fd816c1c04091daada0c20eefae7b41396230e89fb7dcc46cb427aace31` |
| inventory_semantic_provider_candidate_inputs.py | `840abe970bde4ab1edc1c6aeecd84eee9d1fc5a8` | `7bbf6a50722f475323b33568e3bc875b57d7f3e3de78d62c8f7410442c48c6c9` |
| inventory_semantic_provider_static_ipam.py | `8c04d8fb6dd251407e8c86c583d40b53a66f1179` | `426d3aab4c05bb24a46b2c41279a6f6fc847b85d3fc6c2954d236200a4cc68a3` |
| inventory_semantic_provider_guard_custody.py — target PASS | `85914e39bd0aa9f8e7a0a0a9d3b9db6007633ff8` | `fabd47c6ce8919bc7a910cbaf63f66f1fb786b00c239ae41757c1fd0df829b8d` |

Frozen lease cohort source `7a81cc344b513d04fd276cd1923a9c23197aceee`: scripts stage_semantic_lease_package.py/run_semantic_provider_lease_owner.py/prepare_semantic_provider_trust.py; tools materialize_semantic_lease_service.py/materialize_southbound_kernel.py/materialize_southbound_lease_refresh.py/semantic_provider_dns.py/semantic_provider_lease_owner.py/semantic_provider_lease_nft.py. Nine root0600 files in source/scripts and source/tools; no daemon/API started.

Boot stage source `d7f65fc73a6beb0a36e77972301a4c823fe21c5d`; installer `39923852d93a3b0907edce91cf87e9386b11621b`. Host source files and artifact hashes are bound by receipts. Do not mutate frozen cohorts in place.

### 9.4 Network/trust/runtime facts

Host rootful Docker29.8.1, systemd257, Python3.13.5, nftables1.1.3. Paths `/usr/bin/docker`, `/usr/bin/python3`, `/usr/sbin/nft`, `/usr/sbin/ip`, `/usr/bin/systemctl`, `/usr/bin/openssl`; Keycloak `/opt/keycloak/bin/kcadm.sh` in ouf-keycloak.

| Network | ID | Binding |
| --- | --- | --- |
| ouf-backend | `113b5f0a3c53059b087a2ce997d2670cc057e88c0c17d4291b3b41a51ce26ba3` | internal, br-113b5f0a3c53,172.18.0.0/16,gateway172.18.0.1,v4 |
| ouf-gateway-control | `1209d67944755d95601b96719c0a5b1860ac2a6f137c10077da7b4e9967637aa` | internal,br-1209d6794475,172.20/16,v4; shared |
| ouf-semantic-provider-internal | `2a6652422b45db6f359d94d779ab8625b1ad99b1750bb54582b4b8c4e8aa9307` | bridge oufsp-int,internal,v4,172.21.0.0/16,gateway172.21.0.1 |
| ouf-semantic-provider-egress | `db8bc9f8feccc3c14f2818a5c843f5c08e5eb2e192530858d88a70ce1cc0a86d` | bridge oufsp-egress,non-internal,v4,172.22.0.0/16,gateway172.22.0.1 |

Owned **inet + bridge table ouf_sem_provider**, historically **deny-only**, later attested RUNTIME_EMPTY/EMPTY_ONLY, no provider sets/flows/lease installed. Never DROP the entire shared backend/control network. Original topology snapshot hash `8b0eb1c691a5010f98f22e34bb3de8de0b65cf8f9bab3079fc6c193778b857d4` is historical, not an atomic current state proof.

Southbound candidate primary backend, secondary provider-internal + provider-egress; adapter primary provider-internal + provider-egress. Planned static addresses in private manifest/journal, not inferred as allocated while stopped. Both restart=no/capDropALL/no published ports/512MiB memory and same swap limit/pids128/no healthcheck; adapter read-only root, APISIX root writable; exact individual RO mounts. Created Docker endpoints can defer NetworkID until start: helper binds current network name→ID separately and checks IPAMConfig rather than claiming packet proof.

Selected lab DNS resolvers `46.38.252.230`, `46.38.225.230`, UDP/TCP53. Supplied IPv6 `2a03:4000:0:1::e1e6` deferred; current profileIPv4 only. Provider `https://schema.gov.it:443/sparql`; namespaces https://w3id.org/italia/ont/ and controlled-vocabulary/. No arbitrary chatbot SPARQL/provider URL.

Southbound TLS-only10443/SNIouf-semantic-southbound, no HTTP/admin/control/extra-metrics listeners. Adapter9443/SNIouf-semantic-provider; POST `/internal/providers/schema-gov/search`, GET `/internal/providers/schema-gov/fetch`. Adapter worker4/deadline20/providerTimeout10/maxRequest65536/maxResponse8388608/maxIntent2000. TLS cert/key/purpose MAC paths under `/run/ouf-semantic-provider/`, upstream CA/trust-bundle.pem. Separate purpose-bound receipt MAC, not OAuth/delegation key. Issuer/audience/service workload/tenant/scopes bound by private plan. Northbound Gateway env must not be copied wholesale into southbound.

Boot guard installed targets `/etc/systemd/system/ouf-semantic-boot-guard.service` and `/etc/systemd/system/docker.service.d/90-ouf-semantic-boot-guard.conf`. DefaultDependencies=no, after local-fs/nftables, before Docker; Docker Requires/After guard and **ExecStartPre validates every start**. Existing tables must match; both absent can restore strict-create; partial/foreign tables block. Original installer verifies Docker PID preservation, not a permanent verifier after a legitimate restart/reboot. Current expected PID1740 is intentional custody binding; any later change requires reconciliation, not silent adoption.

### 9.5 Already proven native tests — don't rerun indiscriminately

- Real nft/netns default-deny and expiry rejecting new **and established** packets,9 host tests PASS.
- Real Docker bridge native hook + scoped host forward, default-deny/unregistered workload/expired leases, own cleanup,1 host test17.521s PASS.
- Real APISIX3.18 CI OIDC → purpose receipt → adapter TLS, forged/direct/incomplete TLS+HTTP and wrong-hostname/SNI/plaintext denials.
- Boot/systemd native CI restore/dependency/foreign/partial recovery, no Docker restart/PID change. Actual host boot install PASS; **real reboot not proven**.
- Target embedded DockerDNS fixture at `semantic-docker-dns-20261003-105129`: source `b4c2faefb7a526c3455632212275633c60d826e7`; UDP/TCPA+AAAA, forwarded source bound to container, selected resolver/default deny/unregistered denial/flow removal, shared structure unchanged, own cleanup,15.661s. **provider0/externalDNS0**; isolated fixture, not production packet acceptance.
- Real Docker stopped-create tests4 and target static-IPAM admission tests4, plus root role-owned launch/trust/credential fixtures in CI. Target creation itself now PASS.
- Current custody helper7 fixture tests pass; native jobs inherited unchanged are green. **Custody inventory target PASS ora registrato nel checkpoint corrente; intent target ancora pendente**.


### Transizione runtime già completata

Intent root semantic-provider-transition-intent-20261003-151036/prepared PASS; stagingruntime root semantic-runtime-transition-stage-20261003-160211/prepared PASS, stageSourceCommit ef2270a57446da1f23a58548aa4d44920e578fe0; plan/apply/verify RUNTIME_EMPTY PASS, Docker nonrestartato. Readinessroot semantic-runtime-readiness-20261003-165430: configurationHash24968cf990a32b87f3169b9226fe63d224c93a403540afec197011fbd670b0bb, journalHash4ccb05b0a28b6e7e823de3d9af81f29255d60b38271d0a74a00f64e2e5828a74, leaseStructureHash26f6f80af9d1e4898c1a6fe6dc8721cd6f67f1ceed05c7eea35e3b9f4a040e54. Guardedinterfaces2/excludedshared4, providerflow1/staticflows9(DNS,GATEWAY_ADAPTER), sets vuoti, stableAcrossReads ma nonatomic. ManifestSHA052b46a56ea666971f135c75af48b3342dbeb68e2f17f1f16263a99351df88bd, creationjournalSHAa1c2acd9924fc0f924ded7c2d59f128ef2d8b8dd11c62484a901f628022aaae7, bootinstalljournalSHA44dfac2145f509c8fb0b66983630616d25958b40f3ffc811074ebb9b3c1edda5. Nessuna kernellease installata all’ultimo readback.

Inventari preexec runtime/candidates PASS: runc1.5.1, Docker29.8.1; candidates runtime runc, configuredbindingsmatchmanifest true,3network, sandboxKeypresent0, liveNamespaceBinding/OCIhookintegration/atomic/fullcreationacceptance unproven. BindingSHA0337655a5c3d6d80653aca363d8479ce10e6d27cde024518060a6c628e542aeb. Packagev1root195926/source1a020..., adapterv2root213033/sourceb526..., admissionv3root055825/sourceed6..., deploymentv4root072744/sourcecc161..., v7 §29 root semantic-local-broker-package-20261004-110947/source04d775e892cd42e42d34de02959b9c7ba6483f3b PASS (20 sorgenti, noncontiene nuoviproducerv8), poi v8: sorgenti privati, non installazione/registration/start. Registro completo sezioni20–38 nel handoff storico, non ripetere quelle procedure.

## 10. Prove business congelate e gate ereditati

### Cinema

Source `managed-cinema-8ec8ae90`, run `86809c17-3354-45ca-a7e6-57e903944b24` SUCCEEDED; otto handoff ACKED/lineage e otto UDP intake PROCESSED/jobsSUCCEEDED/NEW_OBJECT/observations/revisions/bindings/active objects; quarantene recuperate governatamente, audit conservato. Schedule trigger_once consumed/DISABLED. Vecchio `ouf-udp-r4a-smoke` con JAR incompatibile è stato fermato/retained/restart=no; non riavviare. Historical owner causa non provata integralmente.

Semantic artifact `5ae731cc-e4c5-43a3-aa5e-a7576adbd3a1`, semanticId `https://api.ouf-lab.it/semantic/cinema`, revision `51706bed-81e4-4306-aca1-70119821727d`, publication set `f92a2e17-30c9-456f-bb12-63afa84f41e6`, ACTIVEv1. Positivo HUMAN ChatGPT/MCP semantic.get pinned dopo RDF rollout:17 asserted triples,partialfalse,text/turtle,RDF SHA256 `4340986102db6e47345dd8157734d9db83b928edd94485f1b9a5b9e81c497a2e`. JSON metadata hash distinto `78a39fc30dab8bf221bc9eb8c2567bb2abef57e72ba1e4e29a87a23db4142391`. Cinema subClassOf schema:MovieTheater, nome/indirizzo labels/domain/range. Non prova ontology closure/inference o class Teatro; JSON definitions restano vuote. R-SMOKE Search completo rimane aperto.

### Teatri

Account MCP precedente `ouf-admin`, subject `b93d8cf6-cd14-4ee6-91d7-84cd76c4f500`; non confonderlo con master admin/SSH oufadmin. Nuova chat deve seguire account routing connector corrente, non ricostruire link_id. Connector storico `6aafef96b4148191b767e9af7b756a07` è un riferimento, non autorizzazione a presumere sessione o tool attivi.

Picker `b6de7b63-4a1a-47d8-858e-3cc5f0adad51`; asset `6609b245-86ed-4315-8ce0-73f2a8555bf3`; profile job `2f49ea03-b715-493b-ba25-a3f82007cd3d` SUCCEEDED; profile `7984c39c-7396-4248-ab0a-f2efc390b49c`v1. CSVUTF8/semicolon/header1,13rows20cols/ONE_ROW_ONE_SOURCE_OBJECT, proposta PENDING_HUMAN_REVIEW. Nessuna nuova DRAFT/ACTIVE/run/UDP Teatri provata.

Fields: nome_teatro,tipologia,toponimo,nome_indirizzo,civico,cap,citta,provincia,latitudine,longitudine,sistema_riferimento,precisione_coordinate,capienza_posti,spettacoli_stagione,stagione_riferimento,note,fonte_indirizzo,fonte_coordinate,fonte_altri_dati,data_verifica. Non riportare sample raw. CAP inferitoLONG non è tipo semantico/codice preservato; CRS dichiarato non valida geometria. data_verifica≠businessvalidFrom. Multi-hall granularity e provenance per-field da governare. Proposta NATIVE_KEY nome_teatro ancora unapproved: unicità su13righe non prova stabilità e non è chiave canonica. CLASS Teatro/Theatre search[] osservato non è censimento completo. Cinema/MovieTheater non autorizza analogia Theatre. Official vocabulary tipologia/precisione e transformations whitelist da valutare.

Identità: source-row key distinta da canonical UDP identity. Motore class-neutral già nel branch corretto; non riscrivere weighted legacy. Policy proprietà/comparatori/candidate coverage; subset sufficiente concorde anche in entrambe direzioni può MATCH con premesse/unicità; tutti comuni confrontabili diversi→distinct; partial/conflict/missing→incerto. NEW solo allowAutoNew + coverage completa; overflow REVIEW_REQUIRED/RESOLUTION_TOO_BROAD. Score/frequenza/selettività non conferiscono autorità. MATCH non equivale a merge canonico automatico. Review HUMAN/THS non blocca durable ACK/watermark né tiene transazione DB aperta; append-only audit/lineage.

### Backlog ereditato: nessuna chiusura per omissione

| Gate | Residuo / limite della prova |
| --- | --- |
| R-SMOKE completo | Cinema8/8 non basta: Search Gateway/MCP almeno3oggetti, minimizzazione proprietà/oggetto,2pagine,cursor invalid/partial,label/authority/audit. |
| Seconda fonte sovrapposta/identity review | Source distinta con class/candidate overlap, subset entrambe direzioni, concorde/differente/conflicts/missing/authority, disjoint forms,boundedness/overflow/coverage/backfill, THS atomic/resume. Teatri non prova automaticamente questo gate. |
| Gateway managed upload acceptance | Streaming/primi byte,413 oversized senza assetparziale,415,media-type/digest,anonimi,limiti/idempotenza/rollback. Upload/profile reale è solo una parte. |
| MCP/channel neutrality | Secondo host/client senza copia manuale AssetID,login continuity e limiti/adattatori; niente bridge hostfiles arbitrario. |
| Semantic generalità | Exact refs/provenance/DTO/schema/consumer compatibilità, external discovery/adoption snapshot/definitions, class/property/vocab sufficienti, mapping completo. HUMAN read positivo provato soltanto per il path attuale. |
| Data Lake indipendente | Byte/hash/S3 e DB-objectstore reconciliation, backup/restore oggetti. ACK/materializzazione non sono lettura indipendente byte. |
| Replay RAW/SPI | Trasporto/esecutore e RAW durevole. UDP REPRODUCE non sostituisce retry originale/source replay. Nessun replay per chiudere formalmente questo handoff. |
| Lake policy | Retention/access per source/type/zone,enforcement/cancellazione effettiva; no defaults lab universalizzati. |
| R-INSTALL/portabilità | Manifest/secretrefs,bootstrap idempotente capabilities/IAM/Authorization/routes,cleaninstall,upgradeN/N+1,rollback/restore/PITR/reconciliation,macchine/reti/domain/Enti diversi. Le oltre100capabilities devono avere procedura batch/reconcile automatizzabile, non una lunga sequenza manuale ciascuna. |
| Network/TLS/egress | Native fixture/CI PASS nel proprio scope; target provider deployment/boot custody e runtime packets/admission ancora da provare. Real reboot/IPv6/FQDN leases non attestati dal cold stage. |
| Performance/concurrency | Profili/SLO rappresentativi,race lease/rollout/governor multi-replica; fixture vuote non acceptance. |
| Awareness/collectors | Cross-owner raccolta/proiezioni/alert e13marker ING_ACTIVATION_DISCOVERY_UNAVAILABLE da correlare; non dichiarare run riuscito fallito né healthy dalla mancanza log. |
| Latenza ChatGPT–MCP | Correlare host/tool/Gateway/owner; la lentezza chat percepita non prova latenza backend. |
| Cross-module release/branch/PR | Reconcile main/stalebase/live/pin,SBOM/checksum/security/compatibility/consumer schema; workercompatibility generale non divieto arbitrario N/N+1. CI/build/tag/deploy/live acceptance distinti. |
| Causalità storica403/reference | Non integralmente provata; conservare evidenze, niente mutazioni aggiuntive solo per una spiegazione. |


## 11. Cronologia, file e continuità

[Handoff storico completo3ottobre](OUF_HANDOFF_2026-10-03_STOPPED_PROVIDER_CUSTODY_NEXT.md): cronologia,sezioni1–38,source pins/wrappers/receipt; leggere come registro storico con questo checkpoint corrente prevalente. [Handoff1ottobre](OUF_HANDOFF_2026-10-01_FILE_TO_UDP_NEXT_SPRINT.md), [30settembre](OUF_HANDOFF_2026-09-30_R4A_INGESTION_COMPATIBILITY.md), [29settembre](OUF_HANDOFF_2026-09-29_R4A_PREFLIGHT_TO_INGESTION.md), [27settembre](OUF_HANDOFF_2026-09-27_R4A.md) e auditreferenziato: gate ereditati conservati.4 documenti canonici: roadmap/manuale/sprint/handoff, pointercorrenteaggiunto in questo commit.

Workspace precedente checkpoint/ e gateway/ erano copie transitorie; non dipenderne. Codice e docs autorevoli sono i branch GitHub pinned, ricevuteprivateVPS. La nuova chat non ha necessariamente baseline/PETzip o plugin/accessi: verificare disponibilità, chiedere solo materiale normativo indispensabile quando serve, non biblioteca di altre chat. Nessuna immagine allegata mancante è evidence: alcuni allegati storici non erano leggibili; usare output operatore registrati, non inferire contenuti.

Prima di terminare ogni step: commit aggiornato, test/CI effettivi con skip/limiti,4 docs + comando eseguito, next step univoco. Per questo handoff non ci sono comandi ineseguiti da riproporre; il prossimo agent riparte dalla sezione 7.

Pin immutabile verificatore/wrapper §40: commit `4e69bcf2a66abf75f0ec18db11c339293891f630`; SHA256 `1ab35491972810bc72a995c534e1bfc438f6f0c1e469b8dc8a3685e020c50b9b`. CI dedicata run37226268082/job111506443576 PASS: log effettivo 11+7 test OK senza skip e parity dei due wrapper PASS. Cinque workflow PR completati/success al checkpoint, due ancora in corso (module/container-smoke e live-pairwise), senza failure osservate. Questo esito CI non conferisce scope privato o acceptance. Ultimo VPS §39 PASS; §40 non eseguito, nessun comando VPS pendente.

## Pin e verifica del §41 preparato

Wrapper immutabile §41: commit `77407922584a68ffbbeb7068a88d9acac33fa52d`, SHA256 `ac40df1dba21cc528641ea38aad2020e557dd3424612ab53071bc57f74992083`. CI dedicata run37228966326/job111514395188 completed/success; log letto:11+7+8 test OK,0 skip; bash-n/parity per tutti3wrapper PASS. Sei workflow PR completed/success; uno ancora in corso al presente checkpoint (Semantic Registry module CI/container-smoke), senza failure osservate. §41 rimane NON AUTORIZZATO/NON ESEGUITO, ultimo VPS §40 PASS.

Raccordo temporale riesaminato nel codice Gateway3bdedad: `Broker.prepare` passa CREATED→PREPARING e chiama immediatamente emit attestation; `NodeAttestor.acceptance` apre un mandato preesistente prima di `NodeObservation.observe`; adapter start è il primo punto con rete finale. Il futuro raccordo dovrà osservare la stessa generazione e ottenere il mandato entro quella fase, prima dell'emit, senza lock annidati né attesa umana nella finestra; la mera osservazione non può concedere completeCreationAccepted. Servono acceptance concreta preautorizzata e revalidation di OCI/rootfs/trasporto/guard/lease. Nessuna modifica del broker/adapter o packagev8 target effettuata qui.

Rilettura CI successiva: codice §41 `77407922584a68ffbbeb7068a88d9acac33fa52d`, tutti7 workflow PR completed/success. Checkpoint documentale `bccc9d0bef3480f9d290fd18e4ae82999eb15eed`:4 completed/success,3 in corso alla lettura; nessuna failure. Stato ultimo commit documentale da rileggere separatamente, senza attribuirgli gli esiti del codice.
