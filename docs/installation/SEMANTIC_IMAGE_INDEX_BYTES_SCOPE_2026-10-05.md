# §43 — scope concreto di verifica indice/bytes immagini

PREPARATO, NON AUTORIZZATO, NON ESEGUITO. §42 autorizzato per export --platform linux/amd64 resta BLOCKED. Nessun altro conferimento derivato.

Il wrapper `docs/handoffs/commands/OUF_VERIFY_IMAGE_INDEX_BYTES_2026-10-05.sh` esporta SOLO i due image ID esatti già §39–42:
- adapter sha256:a697bf75bf7d51afadadfaccd3d80537e9a5fb2a08f0d194c6dfd9462e812468;
- southbound sha256:84e6b5e787e9f889ebff88161cb9a16599bafcffa236c6b54c7f779a0655940d.

Delta da autorizzare: image save senza filtro --platform, con flag esplicito --retain-image-index. Può leggere in memoria anche contenuti delle altre piattaforme/attestazioni già conservati localmente in queste stesse due immagini, inclusi eventuali segreti incorporati; non li divulga. Nessun pull di piattaforme mancanti. Linux/amd64 resta la sola piattaforma verificata. I bytes di index/manifest/config/layer vengono hashati; la catena parte dall'ID pinned, non da un manifest arbitrario né dal solo Docker inspect. Se non può provarla resta BLOCKED.

Docker29/containerd ImageInspect usa target.Digest come ID. ExportImage, con una sola platform, sostituisce target con getPushDescriptor. Fonte primaria: https://github.com/moby/moby/blob/master/daemon/containerd/image_inspect.go e https://github.com/moby/moby/blob/master/daemon/containerd/image_exporter.go. In CI29.8.1 il caso è riprodotto (run37264605556 job111618641830); non è ancora conferma sul target. Nuova fixture richiede default filtered BLOCKED e unfiltered INDEX PASS, mai start dell'immagine e cleanup solo risorsa CI posseduta.

Limiti identici §42:180s,8GiB cumulativi parser,100000 entries perimmagine;512blob/256layer/128KiBJSON o appfile. Non salva né estrae archivio. CLI config temporaneo vuoto, rimosso; nessuna registrycredential letta. /usr/bin/python3 -I -B tramite sudo, /usr/bin/docker root-owned stabile before/after, ambiente subprocess fissato PATH/LC_ALL. Nessun private host mount/Env/chiave/credential letto, nessun containeroperation/daemonmutation/build/pull/networkprovider/firma/acceptance/runtime/start/consumerlink.

Output solo hash,counts,booleani e vocabolario diagnostico fisso. Nessun stderr Docker, exception message, archive/path/configvalue/Env divulgato. configBytesMatchImageId è true soltanto per CONFIG; imageTargetChainVerified indica identità provata CONFIG/MANIFEST/INDEX. Le prove rootfsdescriptor storico, cinque appfile hash/rootuid/gid/modes, directory, labels,user/workdir/entrypoint e assenza volumes/Cmd/healthcheck restano invarianti.

SHA256 `6413193ac7f1b1d91eb71b59f7ae3140e594cfe788cd89c9cfa722161ca081ff`; pin definitivo dopo pubblicazione/CI.21 test unit/CLI locali PASS0skip. Verifica nuovo workflow reale Docker29.8.1/containerd obbligatoria prima della richiesta di scope. Handoff§7.4: “Se serve lettura privata/conferimento nuovo, chiedere scope concreto dopo preparazione.” Qui il delta sono bytes aggiuntivi delle stesse immagini, non un nuovo grant acceptance/firma/start.

Debito release separato: generator CI di manifest/pin/wrapper perbuild e host prerequisite preflight/privileged entry limitato. Questa verifica amministrativa non chiude quel debito né publisher/SBOM/fullOCI/generation/mountview/atomic/live readiness/Search503.

## Checkpoint CI e consegna scope

Pin immutabile `1a5e159fa130981a9f102a2d50c4dacb3cfda5f5`; SHA wrapper6413193ac7f1b1d91eb71b59f7ae3140e594cfe788cd89c9cfa722161ca081ff verificato uguale remoto/locale. Workflow37264907986 SUCCESS:47 root0skip; job111619529628. Docker standard job111619529796:1 PASS. Docker29.8.1/containerd job111619529767:1 PASS con default filtered deliberatamente BLOCKED prima dell'export unfiltered INDEX/config/layer/payload PASS. Nessuna immagine fixture avviata, cleanup posseduto. Nuova autorizzazione §43 resta NON concessa: chiedere solo il delta dopo questo checkpoint. Esecuzione VPS NON osservata; target causa/bytes ancora non provati.
