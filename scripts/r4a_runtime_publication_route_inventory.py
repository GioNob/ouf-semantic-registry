#!/usr/bin/env python3
"""Inspect read-only runtime-publication routing and explicit tenant/scope prerequisites."""
import base64
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import r4a_approval_route_inventory as inventory


def main():
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    original = inventory.TARGETS
    captured = io.StringIO()
    try:
        inventory.TARGETS = {
            'LIST': ('GET', '/api/onboarding/v1/runtime/publications'),
            'ACTIVE': ('GET', '/api/onboarding/v1/runtime/publications/managed-cinema-8ec8ae90/active'),
            'RESOLVE': ('GET', '/api/onboarding/v1/runtime/publications/resolve'),
        }
        with redirect_stdout(captured):
            inventory.main()
    finally:
        inventory.TARGETS = original
    output = captured.getvalue().replace('R4A_APPROVAL_ROUTE_INVENTORY', 'R4A_RUNTIME_PUBLICATION_ROUTE_INVENTORY').replace('APPROVAL_', 'RUNTIME_PUBLICATION_')
    print(output, end='')
    owner = inventory.routes.helper.inspect('ouf-onboarding')
    env = dict(v.split('=', 1) for v in owner['Config'].get('Env', []) if '=' in v)
    tenant = env.get('OUF_RUNTIME_PUBLICATIONS_TENANT_ID')
    inventory.flag('RUNTIME_PUBLICATION_OWNER_TENANT_ENV_PRESENT', bool(tenant))
    inventory.flag('RUNTIME_PUBLICATION_OWNER_TENANT_ENV_MATCH', tenant == 'ouf-lab')
    inventory.flag('RUNTIME_PUBLICATION_OWNER_SPRING_JSON_PRESENT', bool(env.get('SPRING_APPLICATION_JSON')))
    live = inventory.routes.helper.inspect('ouf-ingestion')
    helper = inventory.routes.helper
    settings = helper.transport_settings(live, 'ouf-lab')
    mount = next(m for m in live['Mounts'] if m['Destination'] == helper.AUTH)
    relative = Path(settings['ouf.ingestion.activation.token-file']).relative_to(helper.AUTH)
    token = (Path(mount['Source']) / relative).read_text().strip()
    part = token.split('.')[1]
    claims = json.loads(base64.urlsafe_b64decode(part + '=' * (-len(part) % 4)))
    inventory.flag('RUNTIME_PUBLICATION_ING_TOKEN_CONFIG_READ_SCOPE_PRESENT',
                   'ouf.onboarding.configuration.read' in str(claims.get('scope', '')).split())
    print('R4A_RUNTIME_PUBLICATION_PREREQUISITES=COMPLETE READ_ONLY=true SECRETS_NOT_PRINTED=true')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_RUNTIME_PUBLICATION_ROUTE_INVENTORY=BLOCKED CODE=' + code + ' SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
