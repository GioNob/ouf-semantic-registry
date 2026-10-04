# Accettazione concreta dei candidati Semantic provider

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


Stato: piano tecnico revisionabile, NON accettazione concessa. Ultimo VPS §39 PASS; privatepolicy§38 PASS preservata; §39 readback metadati ESEGUITO/PASS (storico, non live). Nessuna firma operativa, lettura contenuti mount, registrazione runtime, collegamento consumer o avvio. Le prove §31/34/36/38 e tutti i tentativi BLOCKED restano immutabili.


## §39 ESEGUITO/PASS — metadati storici ricevuti

Evidenza operatore,4 ottobre2026 20:41:08 Europe/Rome. Nessun current inspect/content acceptance. Destinazioni/source binding hashes conservati nella [receipt](../handoffs/receipts/SEMANTIC_ACCEPTANCE_METADATA_PASS_2026-10-04_OPERATOR.json); owner/mode/size sono del dossier34. Non inferire stat live da questo readback.

| Ruolo | Slot | UID:GID | Mode | Byte | Mount |
| --- | --- | --- | --- | --- | --- |
| adapter | adapter.json | 10006:10006 | 0600 | 973 | RO, contenuto non letto/non accettato |
| adapter | adapter/server.crt | 10006:10006 | 0600 | 717 | RO, contenuto non letto/non accettato |
| adapter | adapter/server.key | 10006:10006 | 0600 | 241 | RO, contenuto non letto/non accettato |
| adapter | adapter/provider-receipt.key | 10006:10006 | 0600 | 64 | RO, contenuto non letto/non accettato |
| adapter | trust-bundle.pem | 0:0 | 0644 | 225117 | RO, contenuto non letto/non accettato |
| southbound | config.yaml | 636:636 | 0600 | 742 | RO, contenuto non letto/non accettato |
| southbound | apisix.yaml | 636:636 | 0600 | 12239 | RO, contenuto non letto/non accettato |
| southbound | trust-bundle.pem | 0:0 | 0644 | 225117 | RO, contenuto non letto/non accettato |

Adapter8 layer descriptors, southbound9; digest layer descriptors non è sigillo bytes/rootfs o publisher trust. Root adapterRO, southboundRW; nessun start/gen/mandato. inventory-receipt34 SHA2566b0814aefde46df9b849df9596b666cc5b99c74aa82bc4fbf71f292b0a189e43 ora osservato. Non ripetere39/34. I valori DA LEGGERE delle sezioni storiche sono ora sostituiti da questa tabella; revisione contenuti/provenance e fullOCI/rootfs/generation ancora APERTI.

## Normativa e fonti

Pacchetto allegato OUF Reality Baseline v1.7:323 checksum verificati,0 mismatch. L0 Alignment Matrix v1.7 e Terminology/Supersession v1.1; PET Semantic v1.3 §§9.2,10–11,17–18,25,28.11–28.11.1,115–128,160.6–160.7; Gateway v1.5 confini northbound/southbound; Onboarding v1.6 §§92–92.3; Authorization v1.5 §36.10. Riesaminare i PET applicabili prima di ogni nuovo lavoro, non sostituirli con questo piano. Semantic ricerca/fetch via Gateway, chatbot propone, THS decide, Onboarding persiste mapping, UDP decide identità canonica. Installazione autonoma per ogni Ente; nessuna authority centrale.

Codice revisionato al Gateway3bdedad: inventory target, manifest/creation, protocol/authentication/reauthorization/producer/consumption, installer approval/node attestor/node observation, broker, adapter Docker, preparer/hook e builder policy. Guide authority/custody/policy/broker consultate. Package target v8 resta7ded9df; non migrarlo a HEAD senza prova e scope. §34 descrive due immagini e8 mount con metadati, NON provenance/contenuti/full OCI/rootfs live.

## Due immagini: provenienza e mutabilità

| Candidato | Selezione ereditata | Già provato nello scope dichiarato | Accettazione ancora necessaria |
| --- | --- | --- | --- |
| Adapter | sha256:a697bf75bf7d51afadadfaccd3d80537e9a5fb2a08f0d194c6dfd9462e812468; source52c0dcf11654a4d3d0f17a6902ed095975466fb9; base python@sha256:bb2988715db2cf7ace7b53f38f3cffbef7c7046a656bee66245eb0ed386e2e81; UID10006; root RO | Receipt stage173408 e selected image/startup/layer descriptors §34, mai avviato | Collegare receipt/build/source/base/closure dipendenze/SBOM o evidenza equivalente disponibile a bytes immagine selezionata. Revisione entrypoint e file applicativi, assenza volumi impliciti; sigillo rootfs completo reale con limiti/deadline misurati. Un ID immagine non certifica publisher. |
| Southbound | APISIX3.18.0 sha256:84e6b5e787e9f889ebff88161cb9a16599bafcffa236c6b54c7f779a0655940d, stessa immagine verificata del Gateway; root RW | Selezione/pacchetto startup fingerprint; risorse512MiB/pids128, no healthcheck/restart/port publishing, capDropALL §34 | Provenance release e startup effettivo; distinguere baseline del root RW prima dell'exec da scritture applicative successive. Nessuna exclusion del sigillo per rendere il test verde. Variazione prima dell'attestation blocca; mutabilità dopo start richiede policy di esercizio e non è provata da questo piano. |

Le selezioni sopra sono binding del lab ereditati, non nuovo inspect. CI software non dimostra immagini target deployed. Il readback39 riporta gli ID dal dossier hash-pinned, senza dichiarare target corrente o publisher trusted.

## Otto mount: revisione concreta

Tutti8 sono individuali bind RO/rprivate secondo manifest e dossier34. RO nel container non rende immutabile la sorgente host. I suffissi indicano file precisi nei root trust212033/TLS230418. Destinazioni esatte derivano dai binding adapter/routes del runtime plan e dal manifest privato, non da default inventati. §39 restituisce hash destinazione/source binding e owner/mode/size salvati al34; non espone path privati. UID/GID/mode effettivi restano DA LEGGERE, non dedotti dal nome del ruolo.

| Ruolo / slot esatto | Fonte e destinazione contrattuale | Contenuto e criterio di revisione privata | Drift consentito / rollback |
| --- | --- | --- | --- |
| Adapter adapter.json | TLS230418; target adapter_configuration_target del manifest | CONFIG: listener9443/SNI, endpoint/allowlist provider, budget/size e riferimenti TLS/MAC/CA coerenti con binding. Verificare schema e hash receipt senza stdout contenuti. | Nessun drift durante transazione; conservare configurazione sigillata, nessun overwrite. |
| Adapter adapter/server.crt | trust212033; adapter.tlsCertificateFile | Certificato pubblico: leaf/purpose/SNI/chain/validità e hash receipt. Pubblico non significa autorizzazione di deploy. | Scadenza richiede successivo conferimento/reconcile; non rinnovare implicitamente. |
| Adapter adapter/server.key | trust212033; adapter.tlsPrivateKeyFile | TLS_SECRET: custodia/owner/permessi, hash privato e corrispondenza leaf già provata vs da riverificare. Non chiave di deployment. §39 non apre PEM. | Zero rotazione/copia/stampa; mantenere originale. Nuova verifica privata distinta. |
| Adapter adapter/provider-receipt.key | trust212033; adapter.receiptKeyFile | PURPOSE_MAC_SECRET: binding di purpose e pairing con Gateway da receipt privata. Mai riuso per OAuth o authority di deploy. | Zero deriva ammessa; rollback conserva pairing originale. |
| Adapter trust-bundle.pem | trust212033; adapter.provider.ca_file | PUBLIC_TRUST: bundle pubblico esistente, roots attesi e hash receipt, cap pubblico1MiB distinto da JSON128KiB. | Zero sostituzione transazionale; non perdere roots esistenti. |
| Southbound config.yaml | TLS230418; gateway_configuration_target | CONFIG: profilo solo TLS10443, nessun admin/HTTP/metrics listener aggiunto, worker/user/path/restrizioni espliciti. | Zero drift preexec; originali sigillati conservati. |
| Southbound apisix.yaml | TLS230418; gateway_resources_target | CONFIG_WITH_TLS_SECRET: contiene leaf private key; parsing/redazione privata di route/purpose/OIDC/TLS/plugin, nessun cat. Hash metadata non dimostra contenuto accettato. | Zero drift, nessuna pubblicazione o riscrittura segreti. |
| Southbound trust-bundle.pem | trust212033; routes.tlsProfile.trustedCertificateFile | Stessa fonte pubblica adapter, destinazione distinta. Verificare binding comune e trust upstream appropriato. | Preservare fonte; due mount non sono due diversi trust bundle. |

Fuori dagli8 mount: southbound.env è input di creazione, non bind mount; la sua corrispondenza è ereditata dal create helper e non viene stampata/letta dal39. Private signing key36 e offline ca.key non vanno promosse a mount. /etc/hosts, resolv.conf, hostname, /dev/proc/sys/tmpfs e altri mount generati dal runtime sono fuori dal count8: richiedono revisione nell'intero OCI, con allowlist di tipo/options/destinazione/provenance per profilo. Non ignorarli o aggiungerli implicitamente alla matrice. NodeObservation sigilla root.path sull'host: ciò non sostituisce accettazione dei bind esterni o dell'intera mount view nel namespace.

## Binding esatti e sequenza temporale

| Campo | Fonte e regola | Quando disponibile |
| --- | --- | --- |
| artifactHash | Digest dell'artefatto di accettazione revisionato per quel candidato: immagine+provenance+8-slot subset+runtime-generated mount policy+binding receipts; schema e bytes privati da definire dopo dati. Non usare count8 o Docker image ID come full acceptance. | Dopo revisione statica privata e authority di accettazione; NON valorizzato ora. |
| deploymentConstraintsHash | Bytes esatti dei vincoli approvati: risorse/user/capabilities/listener/network/namespace/root mutability/closure/hook/limiti. Non inventare che il protocollo convalida semanticamente il contenuto del digest: l'attestor/authority devono collegarlo alle osservazioni. | Prima dell'intento; NON valorizzato ora. |
| transportHash | Funzione operativa transport_hash(candidate): configurazione esplicita networkBindings/transport/table, non nome rete o indirizzo configurato da solo. | Profilo statico completo; riconfronto live preexec. |
| runtimeExecutableHash | Bytes del runc pinned e path/version/closure dell'adapter distinti. | Inventario backend autorizzato; non ricostruire da tag. |
| applicationHash | application_hash dell'intero OCI effettivo dopo trasformazioni adapter (root assoluto, alias namespace risolto) e shadow bundle privato. Non selected inspect hash. | authorize-create confronta bundleHash; record-created e prepare ricontrollano stessi bytes. |
| generation | {pid,startTicks,namespaceInode} reali positivi dal processo runc created. SandboxKey vuoto nei candidati fermi non consente una generation. | Solo runc create autorizzato; cambia invalida mandato/attestation/consumption. |
| rootfsSeal | NodeObservation.rootfs_seal: tutte entries/metadata/content/xattr, bounded e nofollow, niente exclusion; special files bloccano. Sigillo non è authority. | Prima del mandato attestor, poi confronto prima/dopo firma nella stessa fase live. |

Ordine futuro: revisione statica → scope distinct per runtime migration/consumer/signing/create/preexec → intento creation-only firmato con max300s → authorize-create → runc create → record-created → osservazione finale OCI/rootfs/trasporto/generazione dopo provisioning rete → mandato attestor firmato con esatti request/intent/generation/rootfs → broker PREPARING → NodeAttestor → validate_creation → InstallerApproval con mandato finale distinto → READY/preparer/driver sigillato → late reauthorization/guard+lease/common lock → consumo STARTING → FIFO/start → STARTED. STARTED non significa readiness o release acceptance.

Il mandato finale del producer attuale lega intent/vincoli/trasporto/runtime e autorizza issuance/start; non contiene generation/OCI, che sono obbligatori nell'attestation verificata e nell'approval risultante. Non attribuirgli un binding che non ha. Stessa installer key nei due ruoli è la scelta lab, non four-eyes; attestor distinto e atteso esplicitamente per nodo.

**Dipendenza temporale aperta concreta:** adapter v4 esegue admit/prepare nella chiamata runtime start, dopo che Docker ha collegato le interfacce finali. Broker prepare chiama subito il producer; non esiste oggi un callback per ottenere il nuovo mandato di acceptance dopo quella osservazione. Il piano non assume una pausa umana nella finestra18s broker/5s invocation/12s attestor né un mandato prefirmato con generation fittizia. Prima di un futuro intervento: scegliere e testare un punto di preparazione osservazione/mandato prima del broker, garantire ancora stesso generation/OCI/rootfs/trasporto al consumer e lasciare fail-closed ogni deriva. Eventuale adapter/issuer raccordo va implementato/testato prima di richiedere firma/start; non ampliare i budget per supposizione. Calibrare letture rootfs su immagini reali in scope privato dedicato: nessun benchmark target effettuato qui.

La transazione stopped-create storica è32hex; protocollo e Consumption richiedono64hex. Preservare il journal originale; futuro deployment transactionId distinto64hex con collegamento esplicito alla custody storica, non padding/riscrittura silenziosa. I container esistenti hanno runtime runc: un nome runtime aggiunto al daemon non li migra né dà un journal STAGED al broker. Piano di migrazione/nuovi CID e rollback deve essere esplicito e autorizzato; niente recreate/replay da questo documento.

## Rischi, recupero e prove richieste

Nessuna transazione DB resta aperta per approvazione HUMAN. Firme/journal conservano claim ISSUING e fasi PREPARING/STARTING su esito incerto; non cancellare per retry. Runtime create/admission failure richiede reconcile esplicito, conserva shadow/journal/evidenze e nega start. Rollback runtime solo tramite generazione morta/handle posseduti e guard/lease, senza cancellare cohort o toccare container estranei. Readback39 non modifica target: rollback non necessario; BLOCKED conserva evidenze e richiede analisi, non inventory34 ripetuto.

Test futuri pertinenti: root RW cambia fra mandato e attestation→deny prima dell'approval; bind host cambia anche con RO container→deny; layer/provenance mismatch; generated mount/plugin/hook non ammesso→deny; namespace/IPv6 spoof, policy revoke/expiry fra READY e FIFO→deny; common-lock contention, claim straniero, crash fra firma e receipt, generation reuse→deny; costo rootfs entro budget reale. Test native esistenti restano riusati; non ripeterli senza modifica/rischio nuovo. REAL_REBOOT/active lease lifecycle/startup/release rimangono APERTI.

## Prossimo intervento mirato §39

[Wrapper completo](../handoffs/commands/OUF_READ_ACCEPTANCE_METADATA_2026-10-04.sh): lettura storica di soli4 file (manifest, creation journal, dossier34, inventory-receipt34), ciascuno128KiB max, hash dei primi3 pinned, schema/counters e8 mapping slot verificati, doppia lettura stabile ma non atomica. Non legge paths ricavati dal JSON, mount contents/Env/PEM, né Docker/nft/IAM/DNS/provider. Nessun file root/source package target nuovo, nessuna authority/signature o consumer. Python host -I -B. Stdout solo hash/conteggi/categorie e metadati numerici, mai command/path privati.

SHA256 wrapper `0be85f2f2c1d6cbd7f5b0f86c396e6a1050c024adcc85950029b8980cab6b001`. Stato NON ESEGUITO; pin immutabile è il commit che aggiunge questo file, da usare nella consegna.11 test locali PASS/0 skip, inclusi CLI isolata riuscita senza scritture, redaction, hash/schema/drift, nofollow/symlink/hardlink/FIFO/permessi; bash-n PASS. CI codice al commit 43011fe14ef31ea6b6378de618a6be2e8ddf6256:7 workflow PR/9 jobs SUCCESS, log111502111965 conferma11 test/OK e wrapper parity/bash-n PASS. Il pin immutabile del wrapper è 43011fe14ef31ea6b6378de618a6be2e8ddf6256; la CI del successivo commit documentale va riletta separatamente. Non è readback live: restituisce owner/mode/size al tempo34. Dopo output39 aggiornare i4 documenti e stato comando, completare valori osservati, poi preparare verifica privata di provenance/configurazioni solo nello scope necessario; niente acceptance autoapprovata.

## Filo del prodotto mantenuto

Discovery/lookup/definitions/adoption exactrefs al mappingassistant→THS→ACTIVE→file ingestion→RAW/handoff→UDP restano obiettivo. Percorso interno non dipende dall'avvio provider se esiste già semantica sufficiente. Cinema8/8 e Teatri profile/proposta non vanno rifatti. R-SMOKE, Search/definitions/class Theatre/vocab/identity review, upload acceptance, Lake/replay/portabilità/OA restano aperti come registrati nell'handoff; nessuna chiusura per omissione.

## §40 PREPARATO — scope di lettura privata non ancora conferito

§39 resta l'ultimo VPS PASS, storico; §38 private trust policy PASS preservato, nessun replay. Preparato il [verificatore](../../tools/verify_semantic_configuration_provenance.py) e wrapper `docs/handoffs/commands/OUF_VERIFY_CONFIGURATION_PROVENANCE_2026-10-04.sh`, non eseguito. SHA256 wrapper `1ab35491972810bc72a995c534e1bfc438f6f0c1e469b8dc8a3685e020c50b9b`. Il wrapper contiene esattamente il verificatore testato; i root/owner sono espliciti e non derivati da JSON privato.

Scope proposto: lettura read-only redatta di stopped-manifest, launch-input-receipt, tls-runtime-receipt, trust-receipt, stage-receipt, binding e runtime-plan già esistenti, più adapter.json/config.yaml/apisix.yaml nei root storici. **apisix.yaml contiene la chiave TLS southbound inline, quindi il suo contenuto sarà letto privatamente in memoria**, senza stamparlo/copiarlo. Nessun file PEM separato, MAC key, southbound.env, credential/client-secret o offline CA key viene aperto. Nessun Docker/IAM/network/provider, scrittura sul target, firma, installazione, consumerlink, runtime registration o start.

Prova limitata: manifest SHA già noto→launch receipt→TLS/trust/binding→stage→plan; hash esatti dei tre output, adapter binding e routes rispetto al piano sigillato. Doppio read bytes/stat stabile, non snapshot atomico. **Non** replay indipendente del compiler, validazione crittografica chiavi/certificati, provenienza publisher immagine, ispezione Docker live/full OCI, generation/rootfs seal, né acceptance. I gate e il ponte observation→mandate restano aperti. I file di evidenza non conferiscono autorità.

Test locali: 7 nuovi test PASS +11 readback storico PASS, nessuno skip; CLI isolata senza scritture, errori redatti, hash/contract drift, symlink/hardlink/FIFO/owner/mode e metadata drift. CI del checkpoint §39 `8caee157822045e39305812953fdee295f889285`:7 workflow PR success. Nuova CI da verificare sul commit del verificatore prima della richiesta VPS. Ai sensi handoff§7.4, chiedere scope concreto per la lettura privata solo dopo wrapper pinned/testato; nessun comando pendente prima della risposta.

Pin immutabile verificatore/wrapper §40: commit `4e69bcf2a66abf75f0ec18db11c339293891f630`; SHA256 `1ab35491972810bc72a995c534e1bfc438f6f0c1e469b8dc8a3685e020c50b9b`. CI dedicata run37226268082/job111506443576 PASS: log effettivo 11+7 test OK senza skip e parity dei due wrapper PASS. Cinque workflow PR completati/success al checkpoint, due ancora in corso (module/container-smoke e live-pairwise), senza failure osservate. Questo esito CI non conferisce scope privato o acceptance. Ultimo VPS §39 PASS; §40 non eseguito, nessun comando VPS pendente.

## Pin e verifica del §41 preparato

Wrapper immutabile §41: commit `77407922584a68ffbbeb7068a88d9acac33fa52d`, SHA256 `ac40df1dba21cc528641ea38aad2020e557dd3424612ab53071bc57f74992083`. CI dedicata run37228966326/job111514395188 completed/success; log letto:11+7+8 test OK,0 skip; bash-n/parity per tutti3wrapper PASS. Sei workflow PR completed/success; uno ancora in corso al presente checkpoint (Semantic Registry module CI/container-smoke), senza failure osservate. §41 rimane NON AUTORIZZATO/NON ESEGUITO, ultimo VPS §40 PASS.

Raccordo temporale riesaminato nel codice Gateway3bdedad: `Broker.prepare` passa CREATED→PREPARING e chiama immediatamente emit attestation; `NodeAttestor.acceptance` apre un mandato preesistente prima di `NodeObservation.observe`; adapter start è il primo punto con rete finale. Il futuro raccordo dovrà osservare la stessa generazione e ottenere il mandato entro quella fase, prima dell'emit, senza lock annidati né attesa umana nella finestra; la mera osservazione non può concedere completeCreationAccepted. Servono acceptance concreta preautorizzata e revalidation di OCI/rootfs/trasporto/guard/lease. Nessuna modifica del broker/adapter o packagev8 target effettuata qui.

Rilettura CI successiva: codice §41 `77407922584a68ffbbeb7068a88d9acac33fa52d`, tutti7 workflow PR completed/success. Checkpoint documentale `bccc9d0bef3480f9d290fd18e4ae82999eb15eed`:4 completed/success,3 in corso alla lettura; nessuna failure. Stato ultimo commit documentale da rileggere separatamente, senza attribuirgli gli esiti del codice.
