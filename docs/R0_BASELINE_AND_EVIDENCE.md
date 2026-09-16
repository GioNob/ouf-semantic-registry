# R0 — authenticated fixture and evidence baseline

Authority: Reality Baseline Package v1.7, Blueprint v0.3, Matrix v1.7,
Semantic PET v1.3 §§160.6–160.7, Authorization PET v1.5 §109.5.
The PETs govern implementation throughout development. No requirement,
ownership, canonical contract or acceptance threshold changes in R0.

## Regression and bounded correction

Main commit `353d2fc821035c5c3db1c2b142aeb9e3800ec0e3`, live workflow
[35142826742](https://github.com/GioNob/ouf-semantic-registry/actions/runs/35142826742),
failed with HTTP 403: the old fixture sent `X-OUF-Subject`, while the production
resolver correctly requires an authenticated principal.

The dedicated test bootstrap now verifies an ephemeral 256-bit bearer credential,
establishes a fixed SERVICE principal and bounded discovery/draft permissions,
and rejects every other API route. Client identity headers cannot establish or
override that identity. This adapter is under `src/test`, outside the production
component scan, and is started only by the dedicated fixture image. Module CI
also checks that its classes are absent from the production boot JAR.

Tests cover missing/wrong credentials, spoofed identity, SERVICE identity and
denial of the real human approval route. The live test traverses separate
Semantic/PostgreSQL/Gateway-fixture processes to schema.gov.it, persists the
candidate and creates/readbacks a DRAFT. It does not approve or publish it.
The live workflow now runs on pull requests before merge as well as main.

This is a laboratory identity adapter with fixed test policy, not the shared
Authorization SDK, production IAM, browser SSO, APISIX or representative
acceptance. Those gaps remain open. The live external dependency can fail;
the runner must fail visibly rather than substitute a canned PASS.

## Common register

[`ouf-pet-gap-register-v1.7.json`](../evidence/ouf-pet-gap-register-v1.7.json)
is the project coordination register, initially containing the 23 gap groups
from the [pinned audit/roadmap](OUF_ROADMAP_PET_1_7.md). These local IDs do not
replace the PET acceptance IDs. Semantic is only the hosting repository;
each module keeps its ownership and detailed acceptance matrix. The register
is an initial gap inventory, not an exhaustive certification of every PET clause.

Every entry records PET/version/references, owner, audit commit, CI baseline,
evidence level, residual work, phase/dependencies and closure criteria. Baseline
CI is context, not evidence that an OPEN gap has been closed. Closing a group
requires immutable commit, successful run, test/artifact and complete criterion
coverage. A resolved decision is reopened only on new repository/CI evidence.

Evidence levels must remain distinct: static contract/source inspection; module
runtime tests; integration between processes; representative acceptance. In
particular the Authorization/Semantic string/schema pairwise does not demonstrate
production bundle evaluation. The live Gateway fixture does not demonstrate
the complete Gateway APISIX dataplane.

## Reconciliation

- Semantic acceptance metadata now cites PET v1.3 and package/Matrix v1.7.
- UDP JSON at `a18e1c1d1f6add41bb11c975e5f2487f352d1bdb` is the current
  detailed snapshot: 48 VERIFIED, 16 PARTIAL, 3 VERIFIED-LAB, 2 EXTERNAL-OPEN.
  Its Markdown summary is reconciled in the companion UDP R0 change.
- MCP current OA evidence is `docs/MCP_OPERATIONAL_AWARENESS_AGGREGATION_TRACEABILITY.md`
  at `6980aac2e113ebbbe5f7b7329f58854d60dd6846`; Gateway current OA evidence is
  `docs/GATEWAY_OPERATIONAL_AWARENESS_PRODUCER_TRACEABILITY.md` at
  `8a1757e5879f73ee60c2786a7f5e2b325741c940`. Earlier increment notes remain
  historical. Current residuals are MCP-02/GW-02, not every former pending item.
- V9 duplication is closed by the existing main/module CI. No migration changes.
- The audit snapshot pins all six repositories. It is not a release-combination
  compatibility claim: older green peer pins must not be relabeled as all-main
  integration. R2/R6 must record the actual executed combination.

## R0 verification record

Executed Semantic commit `ce71b6d53265014f7f81c751c415b1eda9a363a3`:

- [Live run 35145479786](https://github.com/GioNob/ouf-semantic-registry/actions/runs/35145479786): PASS, nine assertions; artifact 10467750046,
  GitHub-reported SHA-256 `a3d45bf3ed7ec854815564b87508412a4f65e53de70968aa8e2c5b48ed4c30ef`.
- [Module run 35145479760](https://github.com/GioNob/ouf-semantic-registry/actions/runs/35145479760): PASS, 44 tests with zero failures/errors/skips;
  production packaging exclusion and non-root image checks also pass.
- [Authorization run 35145479722](https://github.com/GioNob/ouf-semantic-registry/actions/runs/35145479722): PASS, static contract inspection only.
- [UDP PR #22](https://github.com/GioNob/ouf-udp-object-resolution/pull/22) merged after
  [35145601822](https://github.com/GioNob/ouf-udp-object-resolution/actions/runs/35145601822) passed all existing jobs.

The common register records immutable commits, CI URLs and artifact metadata.
Artifact digests above are reported by GitHub; no independent archive-content
verification is claimed. CI artifacts have retention limits; preserve them in the
release evidence store before expiry when used for acceptance.

R0 closes the fixture regression and baseline bookkeeping. All 23 broader
roadmap gap groups remain OPEN; in particular SEM-01 still requires the real
Gateway/identity and consumer integration. This record does not claim future
main CI results: the PR and main workflows remain the integration gates.
