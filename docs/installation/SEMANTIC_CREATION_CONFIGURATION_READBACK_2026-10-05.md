Conferma CI del checkpoint758c2815249c80e8e8e4d78699c551e003b972d1: run37302568764, log letti65root/0skip (6nuovi),3Docker/0skip,6wrapper parity PASS; job111738527886/111738528338/111738528152. L'ultimo test resourcebudget/pin è quindi ora provato anche nellaCI. Receipt `docs/handoffs/receipts/SEMANTIC_CREATION_CONFIGURATION_CI_2026-10-05.json`. Wrapper eseguibile118b/SHA927c restaimmutato;45NON AUTORIZZATO/NON ESEGUITO. Questa conferma prevale sul futuro readback del test indicato nel testo storico sotto; CI liveprovider resta separata/bloccata503.

# §45 — configurazione completa di creazione dei due candidati

**PREPARATO/NON AUTORIZZATO/NON ESEGUITO.** Ultimo VPS§44 PASS. Wrapper codice immutabile `118b145ed4e83e077e058282d1fde7eee614f344`, SHA256 `927c0197a0059eef71662a4220e7b5d85038b454d95ac55bd12acebf0b3a5cad`, `docs/handoffs/commands/OUF_READ_CREATION_CONFIGURATION_2026-10-05.sh`. Non eseguire prima del conferimento dello scope. PET vincolanti; §39–44 non vanno ripetuti.

## Necessità e confine

§39 ha letto uno snapshot storico di campi selezionati senza Env;§43 prova bytes immagini;§44 verifica input statici8mount e compiler/TLS/MAC. Manca ancora l'intero Config/HostConfig corrente, incluso Env, da vincolare alla futura revisione issuer: startup o privilegi possono differire pur conservando gli stessi file. Questo reader chiude la disponibilità e il binding del dato privato, **non** l'acceptance dei contenuti, la full OCI prodotta da runc o la vista mount del processo. Docker inspect non è la OCI. Non introdurre un package target inerte e non migrare runtime per questa lettura.

## Scope concreto da conferire

2file privati fissi già hash-pinned: manifest130410/prepared/stopped-manifest.json e creation135106/prepared/creation-journal.json. Da questi, solo2containerId64hex e2imageId del manifest pinned; esattamente8comandi inspect read-only (container+image perruolo, duepassi). **Nuova lettura privata: JSON completi di Docker inspect, inclusi Config.Env di container/immagini e ogni eventuale segreto incorporato in quei metadata/labels.** Non leggere file Env host, mount contents, chiavi TLS/MAC/deployment/CA, credenziali registry, altri oggetti daemon. Non seguire path privati del JSON.

Docker /usr/bin/docker hash7f5b38163f9c5367f4b42d905c0505877eafa4c20abe49430c85a770aefacf40, endpoint unix:///var/run/docker.sock esplicito; niente ambient DOCKER_HOST/DOCKER_CONFIG/HOME. Directory CLI vuota root-owned temporanea in /tmp eliminata; nessun auth/config host letto. Stream stdout privato in memoria via pipe/selector, stderr eliminato, nessun dump/spool privato. Limit131072bytes peroggetto/file,60s overall,10s perinspect, executable≤64MB verificato owner/mode/nosymlink/hash-stabile. Reader file fissi root0600/nlink1/nofollow/ancestor e doppia rilettura byte-stabile.

Nessun pull/build/create/start/update/rm/exec target, provider/DNS/IAM/rete applicativa, firma, consumerlink, modifica policy/unit/runtime o target file. Solo CLI pubblica vuota temporanea. Report stdout soltanto hash/configEnvcount/esiti; nessun Env/name/path/labels/rawinspect. Rollback target non necessario per lettura. Su BLOCKED conservare output redatto e analizzare senza replay o ampliamento implicito.

## Predicati e limiti

ID/nome/immagine/ownershiptransaction/manifestlabel esatti; mai avviati statecreated/PID0/startzero/noRestart; user,entrypoint,cmd,workdir,healthNONE da manifest+image. Nonprivileged, capDropALL/noadd/devices/ports, memory/swap/pids/DNS dichiarati,8bindfileRO/rprivate esatti. Env senza duplicati: tutte leentrybase dell'immagine preservate e nessunextra se manifest.envFile assente. Se envFile dichiarato, entryextra sigillate/countate ma **non** validate byte-per-byte contro il fileEnv escluso. Non chiamare questo pairingM2MOAuth completo.

JSON completi container/image e interi Config/HostConfig/Env canonici hashati e confrontati duevolte, inclusi campi futuri/sconosciuti. allConfigurationFieldsSemanticallyAccepted=false. Doppia lettura non snapshot atomico. Nessun applicationHash/fullOCI/rootfsSeal/generation/mountview/PETsupplychain/publisher/SBOM/revocation derivabile da questo PASS. acceptance/start/runtime=false sempre. Restano da implementare issuer esterno con authority esplicita e policy completa e successivo shadow OCI/readback effettivo, prima della firma. Policy38 e packagev8/candidati restano invariati.

## Verifica software

Codicepin118b145ed4e83e077e058282d1fde7eee614f344, run37302120687: log rootjob111737058546 letti64test PASS/0skip (59precedenti+5nuovi),6wrapper bash-n/parity PASS. Dockerjob111737058485:2test reali PASS/0skip (archive+nuovo CLI embedded -I-B su2fixture possedute/mai avviate, Env privato/nonstampato, no filemutations e drift reale memoria viaDockerupdate rifiutato); containerd29.8.1 job111737058271:1test PASS/0skip. Nessun dato VPS usato nellefixture. Ulteriore testlocale nativo resourcebudget/binary-pin passa:6nuovi locali PASS; sarà pubblicato nel checkpoint e verificato nella suaCI separatamente, non retroattribuito al pin.

## CI esterna e prodotto

Checkpoint§44 4e3d0f:6workflowPR success, livepairwise run37300985693 FAIL al preflight schema.gov.it/sparql HTTP503 prima di Docker/probe. Unico rerun failedjob111734491491 fallisce identico503. Nuovo codice45livepairwise37302120671 fallisce anch'esso503; nessun fallback/endpoint alternativo/testignorato/green dichiarato. È una failure della dipendenza osservata nellaCI, non una diagnosi del Search503 sulVPS. Reader/fixtureDocker restanoverdi; recheckingest/Cinema/Teatri proibito. Filochatbot/file→mapping interno/externalonlygap→THS/ACTIVE→one-timeIngestion→UDP→Search preservato.

Handoff§7.4: «Se serve lettura privata/conferimento nuovo, chiedere scope concreto dopo preparazione.» §44 copriva TLS/MAC, non questo Env completo. Chiedere§45 solo dopo wrapper/test/CI revisionabili; consegnare comando dopo conferimento. Nessuna firma/start derivata dall'autorizzazione readonly.
