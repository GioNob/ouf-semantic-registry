#!/usr/bin/env python3
"""Read Gateway routes for real lake/handoff execution after ACTIVE publication."""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import r4a_execution_route_inventory as routes
import r4a_approval_route_inventory as matching

TARGETS = {'LAKE': '/api/internal/v1/lake/objects', 'HANDOFF': '/api/internal/v1/handoffs'}


def flag(key, value):
    print(key + '=' + str(bool(value)).lower())


def main(smoke_cinema=False):
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    if smoke_cinema:
        import r4a_cinema_execution_readback as readback
        receipt = readback.private(readback.ROOT / 'cinema-source-activation.json')
        if (receipt.get('status') != 'PASS' or receipt.get('sourceId') != readback.SOURCE or
            receipt.get('versionId') != readback.VERSION or receipt.get('configurationHash') != readback.HASH or
            receipt.get('publicationId') != readback.PUBLICATION):
            raise RuntimeError('ACTIVATION_RECEIPT_MISMATCH')
    print('R4A_RUNTIME_INTAKE_ROUTE_INVENTORY=READ_ONLY', flush=True)
    udp = routes.helper.inspect('ouf-udp')
    image = routes.helper.inspect(udp['Image'], 'image')
    flag('INTAKE_UDP_RUNNING', udp['State']['Running'])
    flag('INTAKE_UDP_REVISION_MATCH', image['Config'].get('Labels', {}).get('org.opencontainers.image.revision') == 'edaba2bff18a2aaf52d1180f21f0e68984cc3437')
    ing = routes.helper.inspect('ouf-ingestion')
    settings = routes.helper.transport_settings(ing, 'ouf-lab')
    auth = Path(next(m['Source'] for m in ing['Mounts'] if m['Destination'] == routes.helper.AUTH))
    token_path = auth / Path(settings['ouf.ingestion.activation.token-file']).relative_to(routes.helper.AUTH)
    token = token_path.read_text().strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', token):
        raise RuntimeError('TOKEN_FORMAT_INVALID')
    part = token.split('.')[1]
    claims = json.loads(base64.urlsafe_b64decode(part + '=' * (-len(part) % 4)))
    token_scopes = set(str(claims.get('scope', '')).split())
    apisix = routes.helper.inspect('ouf-apisix')
    if not apisix['State']['Running']:
        raise RuntimeError('APISIX_NOT_RUNNING')
    key = routes.admin_key(routes.mounted_config(apisix).read_text())
    config = ('silent\nshow-error\nfail\nmax-time = 15\nmax-filesize = 10485760\n'
        'header = "X-API-KEY: ' + key + '"\nurl = "http://127.0.0.1:9180/apisix/admin/routes"\n')
    raw = routes.helper.run(['docker','run','--rm','-i','--read-only','--cap-drop','ALL',
        '--security-opt','no-new-privileges','--network','container:ouf-apisix',
        'curlimages/curl:8.16.0','--config','-'], input=config, timeout=30)
    values = routes.route_values(json.loads(raw))
    for name, path in TARGETS.items():
        found = matching.candidates(values, 'POST', path)
        print('INTAKE_' + name + '_ROUTE_COUNT=' + str(len(found)))
        for index, route in enumerate(found, 1):
            prefix = 'INTAKE_' + name + '_' + str(index) + '_'
            plugins = route.get('plugins', {})
            oidc = plugins.get('openid-connect', {})
            rewrite = plugins.get('proxy-rewrite', {})
            flag(prefix + 'ENABLED', route.get('status',1) == 1)
            flag(prefix + 'UPSTREAM_UDP', route.get('upstream', {}).get('nodes') == {'ouf-udp:8080':1})
            flag(prefix + 'UPSTREAM_REFERENCE', 'upstream_id' in route)
            flag(prefix + 'SERVICE_REFERENCE', 'service_id' in route)
            flag(prefix + 'PLUGIN_CONFIG_REFERENCE', 'plugin_config_id' in route)
            flag(prefix + 'OIDC_ENABLED', oidc and not oidc.get('_meta', {}).get('disable',False))
            flag(prefix + 'OWNER_PATH_PRESERVED', not rewrite.get('uri') and not rewrite.get('regex_uri'))
            flag(prefix + 'REWRITE_PRESENT', bool(rewrite))
            flag(prefix + 'EXTRA_MATCH_CONDITIONS', any(route.get(k) for k in ('vars','filter_func','remote_addr','remote_addrs')))
            hosts = ([route['host']] if route.get('host') else []) + (route.get('hosts') or [])
            flag(prefix + 'PUBLIC_HOST_UNRESTRICTED_OR_EXACT', not hosts or 'api.ouf-lab.it' in hosts)
            scopes = oidc.get('required_scopes') or []
            if not isinstance(scopes,list) or any(not isinstance(s,str) or not re.fullmatch(r'[A-Za-z0-9._:-]{1,160}',s) for s in scopes):
                raise RuntimeError('ROUTE_SCOPE_LAYOUT_UNSUPPORTED')
            print(prefix + 'REQUIRED_SCOPES=' + (','.join(scopes) or 'NONE_INLINE'))
            flag(prefix + 'TOKEN_REQUIRED_SCOPES_PRESENT', set(scopes) <= token_scopes)
    after = routes.helper.inspect('ouf-udp')
    if after['Id'] != udp['Id'] or after['Image'] != udp['Image']:
        raise RuntimeError('UDP_RUNTIME_CHANGED_DURING_INVENTORY')
    print('R4A_RUNTIME_INTAKE_ROUTE_INVENTORY=COMPLETE READ_ONLY=true LIVE_UNCHANGED=true IAM_UNCHANGED=true INTAKE_POST=false RUN_RESUME=false OWNER_AUTHORIZATION_NOT_PROVEN=true SECRETS_NOT_PRINTED=true')


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--smoke-cinema', action='store_true', help='Optional lab receipt check; default inventory covers shared routes')
        main(parser.parse_args().smoke_cinema)
    except Exception as error:
        code = str(error) if isinstance(error,RuntimeError) else type(error).__name__
        print('R4A_RUNTIME_INTAKE_ROUTE_INVENTORY=BLOCKED CODE=' + code + ' READ_ONLY=true SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
