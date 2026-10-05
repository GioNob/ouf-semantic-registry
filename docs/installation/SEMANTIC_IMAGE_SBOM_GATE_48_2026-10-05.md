# Gate 48 — artefatti SBOM privati per acceptance PET

Stato: PREPARATO, NUOVO SCOPE NON CONFERITO, NON ESEGUITO SUL VPS.

Ultimo VPS §47 PASS; non ripetere §39–47. Il raccordo v4 software Gateway f38e1533e91258874950577b947d84a4b9134f18 ha238 test root/0skip e prove runc della riautenticazione tardiva. Non conferisce acceptance completa. I PET Semantic159.1–159.2/Gateway supply-chain richiedono ancora le prove SBOM/provenance prima della decisione di acceptance.

Il gate48 produce input concreti per quella decisione: SBOM SPDX2.3 e SyftJSON delle due immagini esatte già verificate al §43. Non crea un nuovo package inerte o un'inventory generica, non riesegue i wrapper storici.

## Scope da conferire

- Read/export `docker image save` delle sole immagini INDEX `sha256:a697bf75bf7d51afadadfaccd3d80537e9a5fb2a08f0d194c6dfd9462e812468` e `sha256:84e6b5e787e9f889ebff88161cb9a16599bafcffa236c6b54c7f779a0655940d`; verifica config/layer/chain/rootfs-descriptor Linux/amd64 prima e dopo lo scanner.
- Scrittura nella sola nuova directory root:root0700 `/etc/ouf/deploy-snapshots/semantic-image-sbom-20261005-v1`: scanner0700, subdirectory `prepared`0700, due archivi immagine, quattro JSON SBOM e receipt0600. Cache/estrazioni temporanee dello scanner restano private nello stesso albero. Gli archivi contengono byte/configurazioni **incorporati nelle immagini**, e vengono conservati privatamente; non dichiarare `privateMaterialSpooled=false` per questi artefatti.
- Download pubblico di Syft1.54.0 Linux/amd64 (archiveSHA256 `54a87372498168b2d033e876fd41fa4e8035b872699e525a57046e1f2f09c860`), estrazione del solo binario dopo verifica e sua esecuzione come root dentro un nuovo namespace di rete isolato con `/usr/bin/unshare --net`. Scanner offline con ambiente/HOME/config/cache dedicati, nessun registry pull o update check. Il binario resta in staging, non viene installato nel PATH dell'host.
- Download pubblico della closure Python deterministica pinned. Docker host `unix:///var/run/docker.sock`, binario DockerSHA già sigillato al §47 `7f5b38163f9c5367f4b42d905c0505877eafa4c20abe49430c85a770aefacf40`; `/usr/bin/python3` isolato e `/usr/bin/unshare` root-owned, binari verificati e ri-verificati. Prerequisiti: Linux/amd64, sudo, questi tre comandi e almeno2GiB liberi sul filesystem di staging.

Nessuna lettura dei mount runtime, TLS/MAC/OIDC/CA/deployment key, fileEnv o credenziali registry. Nessun provider/IAM/DNS applicativo, firma, creazione/start/removal di container, modifica unit/network host, consumer/runtime registration o nuova immagine target. Il namespace di rete appartiene al solo scanner e scompare con il processo.

SBOM prodotta/binding all'immagine non equivalgono a SBOM accettata, scansione vulnerabilità, publisher provenance o fullOCI acceptance. Tutti questi conferimenti restano false. La CI usa fixture di package proprie e scanner reale; nessuna prova privata target è inventata. Le immagini Apache di convenienza non sono release ASF firmate: la documentazione Apache raccomanda di costruire dal source; la firma ASC del source non autentica da sola il digest di questa immagine Docker. Riferimenti: https://apisix.apache.org/docs/docker/build/ e https://apisix.apache.org/downloads/.

## Codice e comportamento operativo

Source scanner-preparer `4662257947d1c81550daf87cf7d5ea7283a24e06`, closureSHA256 `e08a3cc012c7984c11f4e13f4c22f2dcebf3702251a2123131d1ac98b5160c5e`. CIrun37360645687: **123 test PASS/0skip**, log dei5 job letti; root113, Docker runner2, Docker target3, runc4, scanner nativo1 (job111934099062). Scanner reale, immagini salvate reali, namespace rete reale, output privato, no container/application/replay. Unit7 comprendono source/wrapper parity, bash-n e diniego di injection prima di hostIO. La stessa closure è verificata nel commit wrapper 0047e62fd12bb5cf7ed3fa8951bf34d4e88969ef. Receipt `docs/handoffs/receipts/SEMANTIC_IMAGE_SBOM_GATE_48_CI_PASS_2026-10-05.json`.

Wrapper: `docs/handoffs/commands/OUF_PREPARE_IMAGE_SBOM_2026-10-05.sh`. Pin wrapper `0047e62fd12bb5cf7ed3fa8951bf34d4e88969ef`, SHA256 `8b23574892b9b929b28879c2ff17ee3e8ccdda0dffd4f67faf0858317baa8e2d`; parity/bash-n e prova nativa PASS. Non eseguire prima del conferimento esplicito di questo scope. Esecuzione una sola volta dopo conferimento esplicito di questo scope. Directory già esistente, hash/config/layer/piattaforma diversa, scanner SBOM su altro source, mancanza dei package o errore/timeout negano PASS. La directory parziale viene conservata: non rimuovere o ritentare automaticamente.

Budget preparazione420s, distinto dai deadline immutati issuer/consumer5/12/18s. Ogni export≤60s e512MiB; scanner≤90s; report JSON≤64MiB. Nessuna pausa HUMAN dentro questa deadline. Condividere solo output redatto, non i JSON/archivi privati. Il passo successivo usa questi artefatti per review supply-chain e issuer completo, con scope firma/install/runtime/start distinti.

## Comando sigillato da usare solo dopo autorizzazione scope48

```bash
sbom_gate_tmp=$(mktemp -d)
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 'https://raw.githubusercontent.com/GioNob/ouf-semantic-registry/0047e62fd12bb5cf7ed3fa8951bf34d4e88969ef/docs/handoffs/commands/OUF_PREPARE_IMAGE_SBOM_2026-10-05.sh' --output "$sbom_gate_tmp/verify.sh"
printf '%s  %s\n' '8b23574892b9b929b28879c2ff17ee3e8ccdda0dffd4f67faf0858317baa8e2d' "$sbom_gate_tmp/verify.sh" | sha256sum --check --strict && bash "$sbom_gate_tmp/verify.sh"
```

Se compare un prompt sudo, inserire la password nel terminale del server, mai in chat. Restituire solo l'output redatto. Il comando produce artefatti necessari alla review PET, non autorizzazioni; l'ultimo target PASS resta47 finché non arriva l'output48.
