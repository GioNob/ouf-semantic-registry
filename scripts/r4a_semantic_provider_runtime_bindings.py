#!/usr/bin/env python3
"""Read selected deployment bindings needed for Semantic workload transport; never secrets."""
import argparse
import json
import re
import subprocess
from urllib.parse import urlsplit

class Blocked(RuntimeError):
    pass


def inspect_container(name):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', name):
        raise Blocked('INVALID_CONTAINER_BINDING')
    result = subprocess.run(['docker', 'inspect', name], capture_output=True, text=True)
    if result.returncode:
        raise Blocked('CONTAINER_INSPECTION_FAILED')
    try:
        rows = json.loads(result.stdout)
        if len(rows) != 1 or not isinstance(rows[0], dict):
            raise ValueError()
        return rows[0]
    except (ValueError, TypeError):
        raise Blocked('CONTAINER_INSPECTION_INVALID') from None


def environment(container):
    values = {}
    for item in container.get('Config', {}).get('Env', []) or []:
        name, separator, value = item.partition('=')
        if not separator or name in values:
            raise Blocked('ENVIRONMENT_AMBIGUOUS')
        values[name] = value
    return values


def endpoint(value):
    if not value:
        return {'configured': False, 'url': None, 'https': False}
    try:
        parsed = urlsplit(value)
        if (parsed.scheme not in ('http', 'https') or not parsed.hostname
                or parsed.username is not None or parsed.password is not None
                or parsed.query or parsed.fragment or '\\' in value
                or any(c.isspace() or ord(c) < 32 for c in value)
                or (parsed.port is not None and not 1 <= parsed.port <= 65535)):
            raise ValueError()
    except ValueError:
        # Do not echo an unsafe value, which may itself contain credentials.
        raise Blocked('ENDPOINT_BINDING_UNSAFE') from None
    return {'configured': True, 'url': value, 'https': parsed.scheme == 'https'}


def inventory(semantic, mcp):
    sem, requester = environment(semantic), environment(mcp)
    credential = sem.get('OUF_SCHEMA_GOV_CLIENT_SECRET_FILE', '')
    mounts = [m for m in semantic.get('Mounts', []) if credential and m.get('Destination') == credential]
    user = semantic.get('Config', {}).get('User', '')
    if user and not re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}', user):
        raise Blocked('USER_BINDING_UNSAFE')
    return {
        'schema': 'ouf.semantic-provider-runtime-bindings.v1',
        'semantic': {
            'id': semantic.get('Id'), 'running': bool(semantic.get('State', {}).get('Running')),
            'user': user,
            'issuer': endpoint(sem.get('OUF_IAM_ISSUER')),
            'providerGateway': endpoint(sem.get('OUF_SCHEMA_GOV_GATEWAY_BASE_URL')),
            'tokenEndpoint': endpoint(sem.get('OUF_SCHEMA_GOV_TOKEN_ENDPOINT')),
            'providerEnabled': sem.get('OUF_SCHEMA_GOV_ENABLED', '').lower() == 'true',
            'authEnabled': sem.get('OUF_SCHEMA_GOV_GATEWAY_AUTH_ENABLED', '').lower() == 'true',
            'clientBindingConfigured': bool(sem.get('OUF_SCHEMA_GOV_CLIENT_ID')),
            'scopeBindingConfigured': bool(sem.get('OUF_SCHEMA_GOV_WORKLOAD_SCOPE')),
            'credentialMountProven': len(mounts) == 1 and mounts[0].get('RW') is False,
            'credentialRead': False,
        },
        'mcpGateway': endpoint(requester.get('MCP_GATEWAY_ENDPOINT')),
        'readOnly': True, 'noSecretsPrinted': True,
        'tokenRequested': False, 'providerCalls': 0,
        'tlsConnectivityProven': False, 'workloadAuthenticationProven': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--semantic-container', required=True)
    parser.add_argument('--mcp-container', required=True)
    args = parser.parse_args()
    try:
        before = [inspect_container(args.semantic_container), inspect_container(args.mcp_container)]
        report = inventory(*before)
        after = [inspect_container(args.semantic_container), inspect_container(args.mcp_container)]
        if before != after:
            raise Blocked('RUNTIME_CHANGED_DURING_INVENTORY')
        print('SEMANTIC_PROVIDER_RUNTIME_BINDINGS=' + json.dumps(report, sort_keys=True))
        print('SEMANTIC_PROVIDER_RUNTIME_BINDINGS_INVENTORY=PASS READ_ONLY=true NO_TOKEN_REQUEST=true NO_SECRETS_PRINTED=true')
    except Blocked as exc:
        print('SEMANTIC_PROVIDER_RUNTIME_BINDINGS_INVENTORY=BLOCKED REASON=' + str(exc) + ' NO_SECRETS_PRINTED=true')
        raise SystemExit(1) from None
    except Exception:
        print('SEMANTIC_PROVIDER_RUNTIME_BINDINGS_INVENTORY=BLOCKED REASON=UNCLASSIFIED_INVENTORY_FAILURE NO_SECRETS_PRINTED=true')
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
