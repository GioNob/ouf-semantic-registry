# Semantic provider workload authentication

Candidate implementation; no live deployment or provider connectivity acceptance.

The Spring provider uses OAuth client credentials to authenticate every Gateway search/fetch request. Authentication disabled or incomplete fails closed before sending a provider request. A disabled provider remains inert. Credentials come from an operator provisioned private, regular, non-symlink file mounted read-only. Tokens remain in process memory, refresh before expiry, and are never returned through discovery APIs or error messages. Renewals are synchronized; renewal failure never falls back to a previous token.

Installation parameters (no domain, port, client identifier or credential path defaults):

| Environment | Meaning |
| --- | --- |
| OUF_SCHEMA_GOV_GATEWAY_BASE_URL | Trusted Gateway HTTPS origin |
| OUF_SCHEMA_GOV_GATEWAY_AUTH_ENABLED | Enable workload authentication |
| OUF_SCHEMA_GOV_TOKEN_ENDPOINT | Trusted IAM HTTPS token endpoint |
| OUF_SCHEMA_GOV_CLIENT_ID | Existing workload client identifier |
| OUF_SCHEMA_GOV_CLIENT_SECRET_FILE | Private mounted credential file |
| OUF_SCHEMA_GOV_WORKLOAD_SCOPE | Explicit granted scope required for southbound invocation |
| OUF_SCHEMA_GOV_SEARCH_PATH / OUF_SCHEMA_GOV_FETCH_PATH | Installed Gateway route paths |
| OUF_SCHEMA_GOV_TOKEN_TIMEOUT | Maximum token request duration including body receipt |
| OUF_SCHEMA_GOV_TOKEN_REFRESH_SKEW | Refresh margin before token expiration |
| OUF_SCHEMA_GOV_TOKEN_MAX_BYTES | Bounded token response size |

Token endpoint redirects are forbidden. JSON media type, bounded body, bearer type, token syntax, positive integral lifetime and returned scopes are checked. Production token endpoints require HTTPS; the package-private test constructor permits loopback HTTP only for controlled fixtures. Gateway same-origin validation happens before token acquisition and disclosure. Gateway response bodies also have allocation and elapsed-time bounds.

The OAuth response is trusted through the configured TLS endpoint; actual JWT issuer, signature, audience, SERVICE actor, tenant and scope admission must be proven at the installed Gateway. This candidate does not configure Gateway routes, southbound isolation, egress policy, TLS, credentials, IAM mappers, application authorization policy or MCP discovery commands. It inherits the separate V10 discovery request migration; the existing RDF migration-identical release helper cannot deploy this branch.

Server evidence, 2026-10-02: IAM prepare apply and verify passed; both `gateway.southbound.invoke` and `ouf.semantic.discovery` definitions exist without drift; provider scope is DEFAULT on the existing Semantic workload client. Discovery scope binding was not requested. Policy, mappers and credentials remained unchanged. Actual token claims remain unproven. No instruction to rerun the successful IAM mutation.
