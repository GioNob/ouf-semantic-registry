# §42 — verifica privata dei bytes delle immagini

Stato: **PREPARATO; scope nuovo NON conferito; NON eseguito sul VPS**. Ultimo risultato operatore §41 PASS, storico. Nessuna acceptance o autorizzazione di avvio deriva da questo verificatore. §39–41 non vanno ripetuti.

Il reader `tools/verify_semantic_image_archive.py` esporta con `docker image save` soltanto i due image ID già selezionati, sulla piattaforma linux/amd64. Riceve config e layer in pipe, non estrae file, non esegue codice dell'immagine e non salva un archivio. Usa una directory temporanea vuota per il config Docker CLI, rimossa al termine: non legge le credenziali registry dell'host. PATH/LC_ALL sono espliciti; nessun ambiente target viene stampato o usato come configurazione. La configurazione **contenuta nell'immagine**, inclusi eventuali campi Env, viene letta privatamente per verificarne il digest; non è il southbound.env del target.

| Immagine | Digest selezionato | Digest descriptor rootfs storico §39 |
| --- | --- | --- |
| Adapter | sha256:a697bf75bf7d51afadadfaccd3d80537e9a5fb2a08f0d194c6dfd9462e812468 | e6b2f3bd33516825e3bee4a0af52090d917545bd644c294dfe0843b736b088d1 |
| Southbound | sha256:84e6b5e787e9f889ebff88161cb9a16599bafcffa236c6b54c7f779a0655940d | ea6aeeef286a7c893cd0bd8eb7452196d87c8681f72a10a3001af288133528ed |

Prove: SHA256 dei bytes config uguale all'image ID; ogni layer decompresso ha il DiffID ordinato dichiarato dal config; descriptor `{Type,Layers}` identico al pin §39; blob OCI `blobs/sha256/*` corrispondente al nome. Supporta Docker save legacy e formato moderno. Per l'adapter applica le whiteout prima delle nuove entries del layer e ricostruisce soltanto il riepilogo `/app`: due directory root:root 0555 e cinque file root:root 0444, hashes del source52c0dcf11654a4d3d0f17a6902ed095975466fb9. Extra moduli, antenati symlink, bytes/permessi differenti, startup user/entrypoint/labels differenti, volumi/Cmd/healthcheck impliciti bloccano.

Il label payloadHash atteso è `379bad5a3083048ff012c5143ace15509321fa860cdaefd238b1218f6541afe7`, digest JSON canonico dei sei hash del build context verificato §41. Il Dockerfile non viene cercato nel rootfs: il suo hash entra nel label del context, i cinque moduli sono verificati nei layer. Non ricompila il Dockerfile e non prova la provenienza del publisher o della base Python.

Limiti per immagine: 180s, 8GiB **cumulativi di lavoro del parser** (stream esterno, membri e bytes decompressi vengono conteggiati), 100000 entries, 512 blobs, 256 layers, JSON e singolo file applicativo128KiB. Non equivale a permettere un archivio8GiB con decompressione illimitata. Pipe bloccata/deadline/hash errato → BLOCKED redatto; processo CLI posseduto terminato e raccolto. Non riprovare automaticamente con budget ampliati. SHA del binario Docker è ricontrollato, senza attribuirgli una provenienza publisher.

La lettura comprende tutti i bytes esportati dell'immagine, quindi **eventuali segreti incorporati nell'immagine** possono essere letti in memoria. Output esclusivamente hash/count/booleani; nessun path o valore config/Env dell'immagine. Non apre mount target, PEM separati, southbound.env, credential/client-secret dell'host o chiavi di firma. Nessun container create/start/exec/inspect, pull/build, chiamata provider, firma, installazione, consumerlink, modifica daemon o scrittura configurazione target. La sola directory temporanea CLI è vuota e non contiene l'archivio.

Restano non provati: publisher/base provenance, SBOM, build riprodotta, stato target corrente, OCI effettivo, mount view, sigillo completo rootfs live, generation, snapshot atomico, readiness, acceptance e start. Gli eventuali `imageBytesVerified=true` riguardano la chiusura config/layer dell'immagine selezionata; non tutti questi altri gate.

Wrapper: `docs/handoffs/commands/OUF_VERIFY_IMAGE_BYTES_2026-10-04.sh`; SHA256 `c8602ba1279481df8a7cbc66864bd5a978be0234678d6cc5515da6b2f7e45b57`. Pin immutabile: commit che aggiunge il wrapper, da registrare dopo pubblicazione. Scope nuovo secondo handoff §7.4: consegnare il wrapper e chiedere soltanto questa lettura privata quando l'operatore torna disponibile. Nessun comando VPS pendente.

Prove software:13 test unitari/CLI,0 skip; test CI obbligatorio con Docker vero, immagine fixture FROM scratch creata con tag casuale e mai avviata, rimossa dal test. Copre config/layer/payload drift, whiteout, symlink, extra module, tar duplicati/traversal, gzip bomb, bytes/entry/deadline, redaction e CLI config vuoto. Il test Docker non misura le due immagini VPS. Wrapper bash-n e confronto esatto col reader in CI.

Fonti primarie: [Docker image save](https://docs.docker.com/reference/cli/docker/image/save/), [OCI Image Configuration v1.1.1](https://github.com/opencontainers/image-spec/blob/v1.1.1/config.md), [OCI Image Layers v1.1.1](https://github.com/opencontainers/image-spec/blob/v1.1.1/layer.md).
