#!/usr/bin/env python3
"""Read selected Docker/firewall metadata needed for an isolated southbound deployment."""
import argparse
import json
import os
import re
import shutil
import subprocess


class Blocked(RuntimeError):
    pass


def run_json(command):
    result = subprocess.run(command, capture_output=True, text=True, timeout=15)
    if result.returncode:
        raise Blocked('READ_ONLY_COMMAND_FAILED')
    try:
        return json.loads(result.stdout)
    except (ValueError, TypeError):
        raise Blocked('READ_ONLY_JSON_INVALID') from None


def nft_summary(payload):
    objects = payload.get('nftables')
    if not isinstance(objects, list):
        raise Blocked('NFT_JSON_INVALID')
    policy_counts, families, rules = {}, set(), 0
    for item in objects:
        chain = item.get('chain')
        if isinstance(chain, dict):
            family = chain.get('family')
            if family in ('ip', 'ip6', 'inet', 'bridge', 'arp', 'netdev'):
                families.add(family)
            hook, policy = chain.get('hook'), chain.get('policy')
            if hook in ('input', 'output', 'forward', 'prerouting', 'postrouting', 'ingress', 'egress') and policy in ('accept', 'drop'):
                key = hook + ':' + policy
                policy_counts[key] = policy_counts.get(key, 0) + 1
        if isinstance(item.get('rule'), dict):
            rules += 1
    # Never return addresses, interface/table/chain names, expressions or comments.
    return {'families': sorted(families), 'baseChainPolicyCounts': policy_counts, 'ruleCount': rules}


def iptables_summary(text):
    policies, rule_count = {}, 0
    for line in text.splitlines():
        match = re.fullmatch(r':(INPUT|OUTPUT|FORWARD|DOCKER-USER) (ACCEPT|DROP|-) \[[0-9]+:[0-9]+\]', line)
        if match:
            policies[match.group(1)] = match.group(2)
        if line.startswith('-A '):
            rule_count += 1
    return {'selectedChainPolicies': policies, 'filterRuleCount': rule_count}


def inspect_gateway(args):
    rows = run_json([args.docker_path, 'inspect', args.gateway_container])
    if not isinstance(rows, list) or len(rows) != 1:
        raise Blocked('GATEWAY_INSPECTION_AMBIGUOUS')
    row = rows[0]
    if not row.get('State', {}).get('Running'):
        raise Blocked('GATEWAY_NOT_RUNNING')
    return {'id': row.get('Id'), 'image': row.get('Image'),
            'networkNames': sorted((row.get('NetworkSettings', {}).get('Networks') or {}).keys())}


def inventory(args):
    gateway = inspect_gateway(args)
    info = run_json([args.docker_path, 'info', '--format', '{{json .}}'])
    version = info.get('ServerVersion')
    if not isinstance(version, str) or not re.fullmatch(r'[A-Za-z0-9._+:-]{1,100}', version):
        version = 'UNPROVEN'
    firewall = {}
    nft = args.nft_path or shutil.which('nft')
    if nft:
        try:
            firewall['nft'] = {'available': True, 'readable': True, **nft_summary(run_json([nft, '-j', 'list', 'ruleset']))}
        except Blocked:
            firewall['nft'] = {'available': True, 'readable': False}
    else:
        firewall['nft'] = {'available': False, 'readable': False}
    iptables = args.iptables_save_path or shutil.which('iptables-save')
    if iptables:
        result = subprocess.run([iptables, '-t', 'filter'], capture_output=True, text=True, timeout=15)
        firewall['iptables'] = {'available': True, 'readable': result.returncode == 0}
        if result.returncode == 0:
            firewall['iptables'].update(iptables_summary(result.stdout))
    else:
        firewall['iptables'] = {'available': False, 'readable': False}
    if inspect_gateway(args) != gateway:
        raise Blocked('GATEWAY_CHANGED_DURING_INVENTORY')
    security = info.get('SecurityOptions') or []
    return {'schema': 'ouf.semantic-southbound-host-inventory.v1', 'gateway': gateway,
            'docker': {'serverVersion': version, 'rootlessObserved': any('rootless' in str(v) for v in security)},
            'firewall': firewall, 'egressDefaultDenyProven': False, 'fqdnPolicyProven': False,
            'tlsClientIdentityProven': False, 'readOnly': True, 'noSecretsPrinted': True,
            'providerCalls': 0, 'tokenRequested': False, 'rulesChanged': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gateway-container', required=True)
    parser.add_argument('--docker-path', default='docker')
    parser.add_argument('--nft-path', default=None)
    parser.add_argument('--iptables-save-path', default=None)
    arguments = parser.parse_args()
    try:
        if os.geteuid() != 0:
            raise Blocked('ROOT_REQUIRED')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', arguments.gateway_container):
            raise Blocked('GATEWAY_BINDING_INVALID')
        print('SEMANTIC_SOUTHBOUND_HOST=' + json.dumps(inventory(arguments), sort_keys=True))
        print('SEMANTIC_SOUTHBOUND_HOST_INVENTORY=PASS READ_ONLY=true NO_RULE_CHANGED=true NO_PROVIDER_CALL=true NO_SECRETS_PRINTED=true')
    except Exception as error:
        code = str(error) if isinstance(error, Blocked) else 'UNCLASSIFIED_INVENTORY_FAILURE'
        print('SEMANTIC_SOUTHBOUND_HOST_INVENTORY=BLOCKED CODE=' + code + ' NO_SECRETS_PRINTED=true')
        raise SystemExit(1) from None
