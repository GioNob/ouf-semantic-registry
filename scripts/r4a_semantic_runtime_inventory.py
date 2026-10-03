#!/usr/bin/env python3
"""Read-only, secret-redacted live Semantic container inventory for R4a rollout."""
import json
import subprocess


def docker(*args):
    result = subprocess.run(['docker', *args], text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('DOCKER_' + args[0].upper() + '_FAILED')
    return result.stdout


def main():
    names = docker('ps', '-a', '--format', '{{.Names}}').splitlines()
    candidates = [n for n in ('ouf-semantic', 'ouf-semantic-registry') if n in names]
    if len(candidates) != 1:
        raise RuntimeError('SEMANTIC_CONTAINER_AMBIGUOUS_OR_MISSING')
    name = candidates[0]
    d = json.loads(docker('inspect', name))[0]
    config, host = d['Config'], d['HostConfig']
    print('SEMANTIC_CONTAINER=' + name)
    print('RUNNING=' + str(d['State']['Running']).lower())
    print('IMAGE_ID=' + d['Image'])
    print('IMAGE_REVISION=' + str((config.get('Labels') or {}).get('org.opencontainers.image.revision', 'NONE')))
    print('USER=' + str(config.get('User', '')))
    print('NETWORK_MODE=' + str(host.get('NetworkMode', '')))
    print('NETWORKS=' + ','.join(sorted(d['NetworkSettings']['Networks'])))
    print('RESTART=' + str(host['RestartPolicy']['Name']))
    print('MOUNT_TARGETS=' + json.dumps(sorted([{'destination': m['Destination'], 'type': m['Type'],
                                                'readOnly': not m['RW']} for m in d.get('Mounts', [])])))
    print('ENV_NAMES=' + json.dumps(sorted(e.partition('=')[0] for e in (config.get('Env') or []))))
    print('PORT_BINDING_COUNT=' + str(len(host.get('PortBindings') or {})))
    print('PRIVILEGED=' + str(host.get('Privileged', False)).lower())
    print('HEALTHCHECK=' + str(bool(config.get('Healthcheck'))).lower())
    print('READ_ONLY_ROOT=' + str(host.get('ReadonlyRootfs', False)).lower())
    print('RESOURCE_LIMITS=' + json.dumps({k: host.get(k) for k in ('Memory', 'MemorySwap', 'NanoCpus')}))
    print('ENTRYPOINT_COUNT=' + str(len(config.get('Entrypoint') or [])))
    print('CMD_COUNT=' + str(len(config.get('Cmd') or [])))
    print('SECRET_VALUES_AND_MOUNT_SOURCES_NOT_PRINTED=true')
    print('NO_WRITES=true')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, KeyError, IndexError) as exc:
        print('SEMANTIC_INVENTORY_BLOCKED=' + str(exc))
        raise SystemExit(1)
