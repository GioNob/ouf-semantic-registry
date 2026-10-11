# Discovery resilience implementation — 11 October 2026

[Platform policy v3](https://github.com/GioNob/ouf-deploy/blob/main/docs/OUF_RESILIENCE_POLICY.md) and Semantic PET1.3 §§160.3–160.4 apply.

Work branches from the exact qualified candidate622614b0040cf11be2f6c7e3568733a488ca4ca8. The actual bounded HTTP adapter classifies timeouts, connection/DNS failure and HTTP408/429/500/502/503/504 as explicitly transient. HTTP501/505, authority denial, TLS/integrity and unknown failures block automatic retry. TLS/cancellation remain blocked/cancelled under transport wrappers. Retry-After seconds and RFC1123 dates retain their full delay; a delay beyond the budget must exhaust/pause rather than shorten the provider's request. No exception message is a public failure code.

The initial source d6930b579b6c6e6fd5386e88cc8801b052cac8e2 passed 52 actual HTTP/classification assertions at run38157621937 and the module Java/PostgreSQL build:90 tests,0 failures,0 errors,2 skipped, run38157621899 job114523797435. This source extends the fixture to wrapped TLS and includes transient HTTP500 consistently with PET160.3. Qualification of this revision is recorded separately.

This is a classification foundation, not complete resilience. Durable provider incident/circuit budgets, finite retry sessions, candidate fencing/atomic publication, bounded backlog scheduling and governed HUMAN budget renewal remain open. Existing in-memory provider retry/circuit and first-failure FAILED jobs are not policy compliant. No target apply, application cutover, new semantics, adoption or release acceptance is authorized by this source change. The previous image and private creation intent are historical and must not be reused for changed source.
