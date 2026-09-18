# OUF roadmap evidence update — R2f + real IAM production gate — 2026-09-18

Authority: Reality Baseline Package v1.7, Cross-Module Alignment Matrix v1.7 and current module PETs. This history record is evidence/coordination only; it does not supersede PET identifiers or criteria.

## Roadmap context

The project-wide gap register states:
- PET and Matrix govern implementation;
- green CI does not amend requirements;
- static inspection, module tests, process integration and representative acceptance are distinct evidence levels;
- closure requires immutable commit plus successful CI/test evidence for the criterion.

The prior R2e roadmap snapshot records the next step as **R3 Operational Awareness**, followed by **R4a guided map UI** and **R4b remaining formats**.

Since that snapshot, R2f Source Onboarding and the real IAM/Authorization production gate have materially advanced and must be included in the evidence baseline before starting R3.

## R2f Source Onboarding checkpoint

R2f Source Onboarding PR #17 had already been merged and production-deployed before this acceptance session:
- merge commit `0f1467f5d8bed279a37094a83671930125f01aa7`;
- R2f trusted review browser run `35273607616` — SUCCESS;
- Source Onboarding module CI run `35273607485` — SUCCESS;
- production image `ouf-onboarding:0f1467f`;
- Flyway V20 applied;
- managed formats include GeoPackage, Shapefile and Microsoft Access;
- Access PK/unique/FK/declared-relationship metadata feeds governed semantic proposals, not automatic ontology publication;
- duplicate/existing-object tolerance and THS review remain governed behavior.

## Real IAM / Authorization gate closed on 2026-09-18

Repository evidence:

### Source Onboarding / Authorization
PR #18 — canonical bootstrap capability descriptors:
- merge `8c444cb3ae52ef78093a0d1763358bb19278b774`;
- Source Onboarding CI `35313470808` — SUCCESS;
- R2f browser CI `35313470898` — SUCCESS.

PR #19 — first-bundle distribution bootstrap-cycle fix:
- merge `26986fe09c236a3aabcfcc3a32283128c087b7d0`;
- Source Onboarding CI `35318850814` — SUCCESS;
- R2f browser CI `35318850826` — SUCCESS.

### Gateway deployment
PR #29 — declarative Caddy internal issuer DNS:
- merge `9af37cee292b8a5930b40ad0849078c26aaffc3e`;
- Gateway CI `35316146906` — SUCCESS.

PR #30 — live-validation hotfix for Docker candidate network mode:
- merge `6cd593a926399d793a78b408952a4a997ef0d40c`;
- Gateway CI `35317130999` — SUCCESS.

## Representative deployed acceptance achieved

Keycloak:
- HUMAN Device Flow established with trusted claims;
- MCP client credentials established with SERVICE claims;
- issuer/audience/tenant/actor/acr/scope claims verified;
- passwords remain only in IAM;
- bootstrap scope removed after successful restart acceptance.

Authorization:
- three canonical capabilities registered via trusted-human API;
- first real PolicyBundle `ouf-lab-authorization:1` published;
- HUMAN admin anti-lockout grant verified;
- MCP bundle-reader and related-search grants present;
- bootstrap latch closed one-way;
- no manual DB bypass used.

Production Onboarding:
- production image `ouf-onboarding:26986fe`;
- IAM enabled;
- health 200;
- protected endpoint without token 401;
- SERVICE bundle-reader 200;
- restart acceptance health 200;
- SERVICE bundle-reader after restart 200;
- HUMAN admin after restart 200.

Deployment:
- Caddy internal issuer DNS works declaratively;
- OIDC discovery from `ouf-backend` is HTTP 200;
- previous Caddy and Onboarding containers retained as rollback evidence;
- temporary IAM smoke container removed after acceptance.

## Intermediate failures retained in history

- Docker-internal DNS failure for public issuer;
- initial declarative Caddy candidate using network mode `none` failed safely;
- temporary env-file permission issue;
- smoke host-port publishing anomaly;
- missing MCP `ouf_actor_type`;
- first bundle-reader implementation returned 403 circular `NO_POLICY_BUNDLE`;
- short-lived token expirations produced expected 401s before mutation;
- first publish attempt failed 401 with DB unchanged;
- corrected publish succeeded and closed latch.

These are documented in detail in the module-specific history records.

## Roadmap disposition

Evidence now supports treating the real IAM/bootstrap/first-policy/production-activation gate as completed for this deployed environment.

The next roadmap increment remains **R3 Operational Awareness**, but R3 should begin from this updated baseline:
- IAM is no longer an external-only fixture for Source Onboarding Authorization;
- Caddy issuer reachability is now production-deployed and repository-tracked;
- active policy distribution has a real SERVICE path;
- operational/fault awareness should therefore consume real trusted identity and active Authorization state rather than test-only assumptions.

R3 must still be checked against the PETs at sprint start. This record does not assert full PET closure, representative SLO/load acceptance, complete THS/browser acceptance, or closure of unrelated module gaps.
