# Complete configured OCI policy — unsigned implementation

Status: SOFTWARE_IMPLEMENTED_NATIVE_DOCKER_GENERATION_CI_PENDING.
Last target result: §47 PASS. No target command or new target authority is issued
by this document; do not replay historical wrappers.

The policy reviewer validates every present OCI field recursively against a
closed typed schema derived from the primary runtime-spec v1.3.0 Go model.
The official file at commit `92249139eea7161e13745abd4cb6d0ea02a3227a`
was read and compared byte-for-byte with the vendored model in Docker 29.8.1;
they match. The initial v1.2.1 model was replaced BEFORE native CI publication
after checking Docker's actual vendor version. The derived metadata contains
63 struct definitions and 14 typed aliases; it is field/type information, not
proof of the installed target runtime or publisher provenance. The schema JSON
must join the sealed issuer source closure, not be a mutable external authority.

`review_semantic_oci_policy.py` requires the entire canonical document to match
an independently prepared expected policy. It separately checks compiled
startup/Env/nonroot identity, no-new-privileges, capabilities, namespace
isolation, bounded resources, seccomp, protected paths, approved hooks and exact
manifest read-only binds. Future fields, unsupported shapes/types/enums, late
hooks, host/shared namespaces, unrestricted read/write host devices, seccomp
listeners/notify/trace, mount overrides and undeclared mounts fail closed.
These are proposed hardening rules for the reviewed issuer profile; they are
not quoted PET requirements and are not silently applied to existing targets.

An unsigned expected policy is NOT acceptance. The caller must independently
authenticate its preparation/custody/source and bind it to image, compiler,
launch, transport and deployment authority evidence. Current target creation
does not explicitly request no-new-privileges; the target daemon default and
eventual OCI must be established before deciding whether any recreation or
runtime configuration change is needed. No candidate is altered here.

The reviewer emits only a canonical application hash and fixed booleans.
`configuredPolicyConforms` cannot set `completeCreationAccepted`: policy
authentication, kernel enforcement, live mount view, generation, rootfs seal,
image publisher provenance, acceptance, signing and start stay false.
Typed omitted OCI fields still need the exact runtime implementation/defaults
in the final issuer decision; shape conformance does not authorize defaults.
Docker logging policy sits outside OCI and also needs its host policy review.

Pure tests exercise complete-document drift, unknown fields at every present
struct depth, strict bool/integer/range/enum handling, inherited defaults,
matching-digest dangerous startup/security variants, mount/path/hook/device
changes, seccomp escape modes, namespace substitutions, bounds and redaction.

The new native CI fixture uses an isolated Docker 29.8.1 daemon and a CI-only
observer runtime. Docker generates the real OCI document; the observer copies
only synthetic CI data under a root-owned private CI directory and ALWAYS
returns failure before invoking runc create/start. `features` delegates to the
actual CI runc executable. This is not a mock replacement for native runc,
kernel, generation, mount or issuer evidence: none of those are claimed.
The fixture is never installed or registered on the VPS. Its later refusal is
intentional and the native test verifies application Running=false and Pid=0.

PET precedence remains Semantic §159.1–159.2 and Gateway supply-chain/custom
plugin policy. SBOM/vendor allowlist/custom-image provenance, runtime source,
compiler custody, actual effective mount/PID/namespace proof, complete signed
acceptance issuer and the distinct deployment/sign/start gates remain open.

Primary sources:

- [runtime-spec v1.3.0 model](https://github.com/opencontainers/runtime-spec/blob/92249139eea7161e13745abd4cb6d0ea02a3227a/specs-go/config.go)
- [Docker 29.8.1 vendored model](https://github.com/moby/moby/blob/docker-v29.8.1/vendor/github.com/opencontainers/runtime-spec/specs-go/config.go)
- [Docker 29.8.1 vendored version](https://github.com/moby/moby/blob/docker-v29.8.1/vendor/github.com/opencontainers/runtime-spec/specs-go/version.go)

## Continuity checkpoint: interrupted session resumed

Section 47 remains EXECUTED_PASS; no operator command is pending and sections 39–47 must not be replayed. Software head before this checkpoint: `2ba1b026b6d4b553106eaf53eb038ad6b833f5eb`.

CI run 37350505094: sealed-readback and runner Docker passed; four mandatory real-runc mount tests passed in 0.608 seconds (job 111899870111). No application was started. The stdio timeout was caused by inherited output pipes in the CI fixture and was corrected using synthetic CI temporary output files. The Docker 29.8.1 OCI test still failed because its seven private namespaces include `time`; its diagnostic exposed only finite type names and path-presence booleans, with no paths or environment values. Moby's reviewed WithNamespaces retains this private time namespace on supported kernels. The next code revision permits that optional namespace only without a joined path; time offsets and shared namespaces remain denied. Twelve local OCI policy tests pass. Native CI for that revision is pending; no full-suite success or target acceptance is claimed.

Next work: read the fresh native OCI CI result, resolve any remaining policy mismatch using primary source and bounded diagnostics, then continue authenticated acceptance issuer integration. Mount metadata observation does not prove source byte hashes, full OCI acceptance, publisher/SBOM provenance or issuer authority. Acceptance, registration, signing and start remain unauthorized by these read-only/software results. PET requirements retain precedence.


Primary implementation for optional private time namespace: [Moby 29.8.1 WithNamespaces](https://github.com/moby/moby/blob/docker-v29.8.1/daemon/oci_linux.go).
