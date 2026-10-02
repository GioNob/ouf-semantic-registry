# Discovery availability gate

The installed provider is disabled until a governed Gateway binding is configured. Requests must not claim an empty successful external search when no provider is enabled.

The provider port now exposes configured availability. SchemaGov reflects its existing enabled flag. A new native discovery request with no enabled provider returns HTTP503 / SEM_DISCOVERY_NO_ENABLED_PROVIDER before inserting a job. A queued request processed after providers are disabled completes FAILED with that code. Disabled adapters are never called. An enabled adapter successfully returning zero candidates still completes SUCCEEDED; one enabled successful adapter may complete a request despite another adapter failing. Existing candidate/adoption/publication semantics and migrations are unchanged.

Six PostgreSQL/HTTP runtime tests cover rejection without persistence, disabled/absent worker providers, a genuine empty result, mixed provider outcomes and authorized HTTP503. Existing governed adoption tests remain the regression baseline. No installation flag, policy, source, scheduler or fixture is changed by this commit. Gateway workload authentication, provider connectivity, candidate inspection, MCP async/idempotent projections and formal adoption review remain separate open gates.
