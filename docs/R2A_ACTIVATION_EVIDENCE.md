# R2a — automatic admission evidence

The mandatory authority is Reality Baseline Package v1.7, especially Onboarding
1.6 §37/§109.17 and Ingestion 1.3 §5/§21/§§32–37. Roadmap R2a covers automatic
first-run creation, exact preflight and versioned scheduling. It does not close
the broader ONB-02/ING-01 criteria that also require acquisition, durable ACK,
watermarks, replay and drift recovery.

| Boundary | Delivered behavior | Evidence |
|---|---|---|
| Onboarding publisher | Bounded SERVICE-only current-publication feed; configured owner namespace; checksum-covered exact Semantic bindings; scheduled-policy validation | RuntimePublicationBoundaryTest; existing governed activation suite |
| Ingestion admission | Automatic configured Spring loop; bounded authenticated Gateway HTTP; immutable publisher checksum/source/tenant/version validation | PublishedActivationTest; AutomaticActivationRuntimeTest |
| Semantic preflight | Explicit semanticId/version/revision/publicationSet lookup; no latest fallback; wrong returned version denies | PublicationGatewayClientTest |
| Schedule/recovery | MANAGED_ONCE per publication; publisher PULL cadence/retry maxima; generation fencing; same-slot recovery; publication regression rejection and snapshot preservation | ActivationLeaseRuntimeTest |
| Process integration | Real Onboarding service lifecycle and CSV profiling; production Ingestion JAR; automatic file/PULL admission; process restart without duplicate runs | R2a Onboarding automatic activation workflow |

Immutable commit, PR, CI and artifact references are in the `r2a` section of
`evidence/ouf-pet-gap-register-v1.7.json`. GitHub artifact metadata does not imply
independent download/hash verification of the artifact archives.

The process test uses explicit Gateway/Semantic response fixtures and a test-only
workload identity adapter. Compatibility attestation and the human approval actor
are laboratory fixtures. The publisher test adapter is excluded from its production
JAR. This evidence proves two real application processes and persisted automatic
admission; it does not certify APISIX, production IAM/THS or real Semantic acceptance.
No source-acquisition or Data Lake/UDP ACK claim is made. Java 21/Maven execution
occurred in CI; the local workspace performed edits and static consistency checks.

Validation corrections: replaced an unavailable JDBC optional-row API; isolated
new scheduler fixtures from preexisting admission load; bounded test-only connection
pools so cached Spring contexts do not exhaust PostgreSQL; waited for migration
completion before the process probe. No production capacity, security or acceptance
threshold was weakened. Failed historical CI runs remain visible.

Deployment must configure Gateway URL, workload token-file, platform control-plane
namespace and activation.enabled, and provision publication-read/Semantic-read
capabilities. Legacy publications lacking exact bindings or schedule policy fail
closed and require a governed new version. Details are in the owner repositories:
`docs/R2A_PUBLICATION_FEED.md` (Onboarding) and `docs/R2A_AUTOMATIC_ACTIVATION.md`
(Ingestion).

Next: R2b composes source adapters → Data Lake raw/normalized/curated → durable UDP
handoff → ACK/committed watermark and authorized serving, preserving the R2a snapshot
and resource authorization. R3 retains complete misfire/incident/recovery/retention
projection. AUT-03/AUT-04 and representative R6 acceptance remain explicit gates.
