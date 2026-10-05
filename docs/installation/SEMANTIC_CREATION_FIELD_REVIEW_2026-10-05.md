# Complete creation-field review — software implementation

Status: SOFTWARE_IMPLEMENTED_NATIVE_CI_PENDING. Target §46 remains PASS; this
checkpoint does not supersede its execution or authorize another target action.

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
