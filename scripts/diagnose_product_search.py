"""Bounded read-only diagnosis of the existing Gateway/UDP search path.

No configuration writes, key-file reads, container starts or domain mutations.
Gateway secret format is checked in memory and never disclosed.
The anonymous owner search probe cannot install a HUMAN principal.
"""
import argparse
import ipaddress
import json
import re
import subprocess
import urllib.error
import urllib.request

SEARCH_NAMES = (
    'OUF_UDP_SEARCH_TENANT_ID', 'OUF_UDP_SEARCH_ISSUER',
    'OUF_UDP_SEARCH_AUDIENCE', 'OUF_UDP_SEARCH_WORKLOAD',
    'OUF_UDP_SEARCH_OWNER_KEY_FILE',
)


def environment(doc):
    out = {}
    for item in doc.get('Config', {}).get('Env') or []:
        if isinstance(item, str) and '=' in item:
            name, value = item.split('=', 1)
            if name in out:
                raise ValueError('DUPLICATE_ENVIRONMENT_NAME')
            out[name] = value
    return out


def summarize(gateway, udp, nginx):
    ge, ue = environment(gateway), environment(udp)
    owner = ge.get('OUF_UDP_SEARCH_OWNER_KEY', '')
    key_target = ue.get('OUF_UDP_SEARCH_OWNER_KEY_FILE', '')
    matching = [m for m in udp.get('Mounts') or []
                if key_target and m.get('Destination') == key_target]
    inherited = set(re.findall(r'^\s*env\s+([A-Za-z_][A-Za-z0-9_]*)\s*;', nginx, re.M))
    return {
        'gatewayRunning': gateway.get('State', {}).get('Running') is True,
        'udpRunning': udp.get('State', {}).get('Running') is True,
        'gatewayOwnerKeyPresent': bool(owner),
        'gatewayOwnerKeyHex64': bool(re.fullmatch(r'[a-fA-F0-9]{64}', owner)),
        'gatewayOwnerKeyInheritedByNginx': 'OUF_UDP_SEARCH_OWNER_KEY' in inherited,
        'udpSearchBindingsPresent': {name: bool(ue.get(name)) for name in SEARCH_NAMES},
        'udpOwnerKeyMountCount': len(matching),
        'udpOwnerKeyMountReadOnly': len(matching) == 1 and matching[0].get('RW') is False,
        'keyFilesRead': False,
        'environmentValuesPrinted': False,
    }


def docker_json(binary, name):
    result = subprocess.run([binary, 'inspect', '--type', 'container', name],
                            capture_output=True, timeout=10, check=True)
    if len(result.stdout) > 2 * 1024 * 1024:
        raise ValueError('INSPECT_TOO_LARGE')
    docs = json.loads(result.stdout)
    if not isinstance(docs, list) or len(docs) != 1:
        raise ValueError('ONE_CONTAINER_REQUIRED')
    return docs[0]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def anonymous_owner_probe(udp, network):
    address = udp.get('NetworkSettings', {}).get('Networks', {}).get(network, {}).get('IPAddress', '')
    if not address:
        return {'performed': False, 'reason': 'UDP_NETWORK_ADDRESS_UNAVAILABLE'}
    ip = ipaddress.ip_address(address)
    if ip.version != 4 or not ip.is_private or ip.is_loopback or ip.is_unspecified:
        raise ValueError('PRIVATE_IPV4_REQUIRED')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    body = b'{"type":"https://api.ouf-lab.it/semantic/cinema","pageSize":1}'
    request = urllib.request.Request('http://' + str(ip) + ':8080/api/udp/v1/objects/search',
                                    data=body, method='POST',
                                    headers={'Content-Type': 'application/json'})
    try:
        with opener.open(request, timeout=4) as response:
            status = response.status
    except urllib.error.HTTPError as error:
        status = error.code
        error.close()
    except (urllib.error.URLError, TimeoutError, OSError):
        return {'performed': True, 'result': 'CONNECTION_FAILED', 'noReceiptSent': True}
    interpretations = {
        403: 'OWNER_REJECTS_UNSIGNED_REQUEST_AS_EXPECTED',
        503: 'OWNER_UNAVAILABLE_BEFORE_VALID_RECEIPT',
        404: 'OWNER_SEARCH_ENDPOINT_NOT_FOUND',
    }
    return {'performed': True, 'httpStatus': status, 'noReceiptSent': True,
            'result': interpretations.get(status, 'UNEXPECTED_STATUS_REQUIRES_REVIEW'),
            'objectResponseRead': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--docker', required=True)
    parser.add_argument('--gateway', required=True)
    parser.add_argument('--udp', required=True)
    parser.add_argument('--network', required=True)
    args = parser.parse_args()
    if not args.docker.startswith('/') or any(not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', x)
                                             for x in (args.gateway, args.udp, args.network)):
        raise SystemExit('PRODUCT_SEARCH_DIAGNOSIS=INVALID_ARGUMENT')
    stage = 'GATEWAY_INSPECT'
    try:
        gateway = docker_json(args.docker, args.gateway)
        stage = 'UDP_INSPECT'
        udp = docker_json(args.docker, args.udp)
        stage = 'NGINX_INHERITANCE_READ'
        result = subprocess.run([args.docker, 'exec', args.gateway, 'cat',
                                 '/usr/local/apisix/conf/nginx.conf'],
                                capture_output=True, timeout=10, check=True)
        if len(result.stdout) > 2 * 1024 * 1024:
            raise ValueError('NGINX_CONFIG_TOO_LARGE')
        stage = 'REDACTED_BINDING_REVIEW'
        report = summarize(gateway, udp, result.stdout.decode('utf-8'))
        stage = 'ANONYMOUS_OWNER_PROBE'
        report['anonymousOwnerProbe'] = anonymous_owner_probe(udp, args.network) if report['udpRunning'] else {'performed': False, 'reason': 'UDP_NOT_RUNNING'}
        report['scope'] = 'CURRENT_SEARCH_DIAGNOSIS_ONLY'
        report['targetConfigurationWrites'] = 0
        report['containerLifecycleOperations'] = 0
        print('OUF_PRODUCT_SEARCH_DIAGNOSIS=' + json.dumps(report, sort_keys=True))
    except Exception:
        # Never expose raw inspect, stderr, file/config content, URL or credentials.
        raise SystemExit('PRODUCT_SEARCH_DIAGNOSIS=BLOCKED STAGE=' + stage)


if __name__ == '__main__':
    main()
