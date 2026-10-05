## Checkpoint corrente — raccordo v4 firmato e controllo tardivo nativo PASS

Ultimo VPS: **§47 PASS**, nessun replay §39–47 e nessun comando operatore pendente. Codice Gateway `f38e1533e91258874950577b947d84a4b9134f18`, PR56 draft/unmerged: entrambi i workflow returned SUCCESS (37357971003 / 37357971063, 19 job). Log del job111925113296 letti: **238 test root, zero skip; 2 native admission; 6 runc node; 2 Docker/Go**. Il test v4 verifica firme reali, helper sigillato, generation/mount/byte reali, riautenticazione dopo la firma e negazione di una modifica reale ai byte prima dell'avvio; l'applicazione della fixture node resta CREATED. I test del broker verificano il passaggio esatto della policy e il diniego prima della firma finale quando non coincide.

Observer Semantic `3505a2f6bfde9c3905b76a5e670ebc30b40d3d6d`, SHA256 `d15d290e903e16f64b9d153658453f2b857c5241eb30ded961fd981a3ba436e4`, run37355294240: **106 root + 2 Docker runner + 3 Docker target + 4 runc = 115 PASS, zero skip obbligatori**. CLI generata deterministicamente dal source/schema closure; nessuna copia di moduli modificabile nel Gateway. Receipt: `docs/handoffs/receipts/SEMANTIC_CREATION_FRAME_ISSUER_CONSUMER_CI_PASS_2026-10-05.json`.

L'attestation v2 firma artifactHash e creationFrameHash. Il consumer ricontrolla il frame sotto il lock comune prima di STARTING e dopo il suo fsync, prima del release. Drift/mancanza del binding negano start; una claim STARTING rimane non riutilizzabile. Nessun aumento dei deadline 5/12/18s, nessun fallback v1/v2, nessuna autorità dedotta da un report unsigned. Non è una snapshot atomica né una difesa contro root compromesso.

**Questo chiude il raccordo software osservazione→firma→consumer, non implementa ancora l'issuer esterno di acceptance completa sul target.** PET Semantic159.1–159.2/Gateway supply-chain restano vincolanti: publisher/provenance/SBOM/custom-image evidence, vendor digest allowlist, policy OCI indipendente, rootfs e kernel policy effettiva devono essere revisionati prima di conferire complete acceptance. Prossimo lavoro autonomo: preparare l'issuer e il gate concreto per queste prove, non altre inventory generiche. Non emettere una nuova firma target o conferire un nuovo ruolo per analogia.

Compiler statico §44 resta Gateway `516133e59be869012d3003758e545a5b5aa0060a`; package v8 `7ded9df0c74c6db919c7a68d4c75ab2c132dea53` resta staged/non installato. Policy §38/consumer/runtime/candidati, Cinema8/8 e Teatri PENDING_HUMAN_REVIEW restano invariati. Search503VPS non risolto dalla CI Search verde; provider live503 Semantic distinto. Installer Linux/amd64, domain/reti/moduli→macchine SPECIFICATO_NON_IMPLEMENTATO. Nessuna write/key/sign/provider/start target. Questo checkpoint prevale sulle cronologie sottostanti.

# Complete configured OCI policy — unsigned implementation

Status: SOFTWARE_IMPLEMENTED_NATIVE_OCI_AND_MOUNT_CI_PASS_TARGET_NOT_EXECUTED.
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

## Latest software checkpoint — unsigned OCI and native mount CI PASS

Verified code pin `4bd3b3c6efa0add42b217766bf45773e82fa958b`, run37351083289: all four acceptance-metadata jobs passed. Logs read:100 root tests (job111901785588),2 runner Docker tests (111901785523),3 Docker29.8.1/containerd tests including real OCI generation (111901785434),4 native runc mount tests (111901785070,0.763s);109 total,zero skips. Eight historical wrapper parity/bash checks remained intact. Receipt: `docs/handoffs/receipts/SEMANTIC_UNSIGNED_OCI_MOUNT_CI_PASS_2026-10-05.json`.

The three observed failures are corrected: inherited create stdio pipe retention in the CI fixture; optional private time namespace in actual Docker OCI; Docker recursive read-only rro request. Primary Moby source supports the latter two. Shared namespaces, time offsets, writable/shared manifest binds remain denied. Application execution was never allowed by these tests. Native proof is CI-only and does not authenticate an expected target policy or confer target acceptance.

Latest VPS state remains §47 EXECUTED_PASS. No operator command is pending; do not replay sections39–47. Next autonomous work is to integrate source-sealed configured OCI semantics and contemporaneous mount/source/rootfs/generation facts into the independently authorized complete acceptance issuer. The issuer must not trust unsigned booleans, self-signed policy proposals or historical facts as fresh proof. Runtime/package installation, new private scope, signing and start remain separate concrete gates. PET supply-chain/SBOM/publisher and authority requirements remain open. Separate live-pairwise CI remains failed; this is not a global-green claim or a diagnosis of internal VPS Search503.

