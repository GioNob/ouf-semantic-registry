## §47 eseguito/PASS — campi di creazione classificati, nessun replay

Output operatore ricevuto il 5 ottobre 2026 alle 18:56:53 Europe/Rome: checksum OK, `SEMANTIC_CREATION_FIELDS=PASS ACCEPTANCE_GRANTED=false START_AUTHORIZED=false`. Pin eseguito `3f49c743b721885d74a00e528b9b2d4bf8fdb772`, SHA256 `3a0182208cdd3e22383edaaed16e1db8e78b74cb92d567a0d5834ac3721142d6`. Receipt completa: `docs/handoffs/receipts/SEMANTIC_CREATION_FIELDS_PASS_2026-10-05_OPERATOR.json`. **Ultimo VPS §47 PASS; non ripetere §47 o i wrapper precedenti. Nessun comando VPS pendente.** Evidenza fornita dall’operatore, non ispezione SSH indipendente.

Tutti i campi presenti seguono regole esplicite: Config adapter17/southbound19, HostConfig64 per ruolo, zero campi sconosciuti e zero obbligatori mancanti. Config/HostConfig/Env sono ancora gli stessi §45/§46. Dieci campi HostConfig per ruolo richiedono policy effettiva OCI/host; ExposedPorts e StopSignal del southbound richiedono provenance immagine. Nessun dato privato stampato/spooled, provider/IAM/firma/target-write/containermutation; acceptance/start/fullOCI/mount-view/generation/atomic restano false.

Proseguire autonomamente sulla policy di acceptance dell’intero OCI e dell’issuer: hash di configurazione e classificazione della richiesta non autorizzano default del daemon né conferiscono acceptance. Occorrono prova dei namespace/seccomp/LSM/no-new-privileges, runtime/logging/protected paths, rootfs e mount effettivi, generation e supply chain; preparazione/signing/runtime/create/start o nuove letture private richiedono scope concreti distinti secondo handoff7.4–7.5. PET vincolanti. Non sostituire prove native con mock/skip o auto-acceptance.

CI software §47 già verificata:83root+4Docker PASS/0skip,8wrapper parity. Il 503 upstream providerCI resta distinto dal Search503VPS. Cinema/Teatri/HUMAN, packagev8/policy/consumer e installer Linux/amd64/domain/reti/moduli→macchine restano invariati. Questo stato prevale sulle istruzioni di esecuzione §47 sottostanti.

# Complete creation-field review — software implementation

Status: READY_FOR_OPERATOR_EXECUTION_WITHIN_EXISTING_READ_SCOPE_45_46.
Target §46 remains PASS and must not be replayed. §47 has not been executed.
The new wrapper classifies the same exact private inputs and candidate/image
inspect objects already authorized in §45/§46; no new private file or authority
scope is requested. The only pending intervention is operator execution.

`tools/review_semantic_creation_fields.py` examines every field in the complete
container Config and HostConfig. The reviewed Docker 29.8.1 API has 24 Config
fields and 70 HostConfig/resource fields. Required fields must be present;
documented omitted fields may be absent. Unknown fields, wrong JSON types,
additional labels or mount options, resource/security overrides, and any field
without a rule fail the declared-request review. Unknown field names and all
values remain private; reports contain only schema-defined names, status codes,
counts and whole-object hashes. JSON `false` never equals numeric `0`.

The module checks the authenticated manifest's user, exact image/startup,
resources, primary network, DNS, read-only bind declarations and sealed Env.
It requires the image labels plus exactly the two ownership labels. The caller
must supply already authenticated identity/receipt/image/Env evidence: this
module is not a credential or image provenance verifier.

`declaredRequestConforms` means that the declared creation request follows the
specified rules. It cannot confer `completeCreationAccepted`,
`allConfigurationFieldsSemanticallyAccepted`, OCI acceptance or start authority.
Inherited image metadata still needs supply-chain evidence. Runtime, cgroup/IPC
and user namespaces, seccomp/LSM defaults, protected paths, shared memory,
logging, init, umask and ulimits require effective OCI/host-policy review. The
absence of a Docker security override does not establish no-new-privileges,
seccomp enforcement or an AppArmor profile. Read-only bind declarations do not
establish the effective mount view or recursive read-only enforcement.

Tests include exhaustive required-field omission, unknown top-level/nested
fields, dangerous startup/security/resource changes, boolean/numeric coercion,
mount duplication and recursion options, private-output redaction, and exact
field coverage against the reviewed primary API schema. Mandatory Docker CI
uses only two owned, never-started synthetic candidates, on the runner daemon
and the target Docker 29.8.1/containerd image store. No skipped/mocked Docker
success substitutes for native evidence. No candidate on the VPS is changed.

Primary sources (field schema and CLI defaults, not image publisher proof):

- [Moby Config](https://github.com/moby/moby/blob/464cd50c3d9e92877d56940ea160de6fca7bea23/api/types/container/config.go)
- [Moby HostConfig/Resources](https://github.com/moby/moby/blob/464cd50c3d9e92877d56940ea160de6fca7bea23/api/types/container/hostconfig.go)
- [Moby Mount/BindOptions](https://github.com/moby/moby/blob/464cd50c3d9e92877d56940ea160de6fca7bea23/api/types/mount/mount.go)
- [Docker CLI create options](https://github.com/docker/cli/blob/v29.8.1/cli/command/container/opts.go)

PET precedence: Semantic Registry §159.1–159.2 and Gateway supply-chain/custom
plugin policy remain binding. This review neither supplies an SBOM/signature nor
approves a custom APISIX plugin. The complete acceptance issuer, native OCI and
mount/generation evidence, signing, consumer installation and runtime/start
gates remain open. Historical wrappers §39–46 must not be replayed.

## Verified code and operator execution

Code/wrapper pin: `3f49c743b721885d74a00e528b9b2d4bf8fdb772`. Wrapper SHA256: `3a0182208cdd3e22383edaaed16e1db8e78b74cb92d567a0d5834ac3721142d6`.
CI run 37343675450: root job 111876783737 passed 83 tests, zero skips;
runner Docker job 111876784108 passed 2 tests; target Docker 29.8.1/containerd
job 111876783401 passed 2 tests. All 8 wrapper parity checks and bash parsing
passed. Logs read independently through GitHub. CI-native isolated §47 CLI
passed on both daemons, kept both owned fixtures never started, preserved file
bytes, and emitted no private fixture values or paths. Initial native failures
were corrected in software/fixtures before operator execution: exact Env maps
permit Docker merge ordering but reject duplicates/overrides; DNS is explicit
in the synthetic fixture, avoiding nil/empty daemon-default ambiguity. Target
checks were not relaxed and historical target wrappers were not modified.

The full PR CI is not globally green: live pairwise run 37343675434, job
111876782870, failed with upstream HTTP 503 before Docker/product probes.
This is separate from the VPS internal Search 503; no bypass or retry is implied.

Execute once in the existing `oufadmin` server session:

```bash
(
  set -euo pipefail
  workdir=$(mktemp -d)
  trap 'rm -rf -- "$workdir"' EXIT
  curl --fail --silent --show-error --location \
    'https://raw.githubusercontent.com/GioNob/ouf-semantic-registry/3f49c743b721885d74a00e528b9b2d4bf8fdb772/docs/handoffs/commands/OUF_REVIEW_CREATION_FIELDS_2026-10-05.sh' \
    -o "$workdir/verify.sh"
  printf '%s  %s\n' '3a0182208cdd3e22383edaaed16e1db8e78b74cb92d567a0d5834ac3721142d6' "$workdir/verify.sh" | sha256sum -c -
  bash "$workdir/verify.sh"
)
```

Share only the redacted output. `SEMANTIC_CREATION_FIELDS=PASS` means the
complete declared request conformed; the report explicitly keeps effective OCI
policy, image publisher provenance, full OCI, mount view, generation, atomic
snapshot, signing, runtime, acceptance and start false. A field-rule rejection
returns schema-defined names/statuses plus hashes and counts, never values.
Binding failures return only a generic redacted reason. Do not retry a blocked
operation or modify a candidate to make the check pass without reviewing it.
