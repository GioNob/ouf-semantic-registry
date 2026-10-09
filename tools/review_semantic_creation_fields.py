"""Exhaustive Docker creation-field review, never an OCI acceptance issuer.

Schema: Moby 464cd50c3d9e92877d56940ea160de6fca7bea23 (Docker 29.8.1).
Rules intentionally distinguish a declared creation request from the effective
OCI security policy. No daemon default, inherited image metadata or checksum
can confer effective-runtime or supply-chain acceptance.
"""
import hashlib
import json
import re

CONFIG_REQUIRED = frozenset('Hostname Domainname User AttachStdin AttachStdout AttachStderr Tty OpenStdin StdinOnce Env Cmd Image Volumes WorkingDir Entrypoint Labels'.split())
CONFIG_OPTIONAL = frozenset('ExposedPorts Healthcheck ArgsEscaped NetworkDisabled OnBuild StopSignal StopTimeout Shell'.split())
HOST_OPTIONAL = frozenset('Annotations StorageOpt Tmpfs Sysctls Runtime Umask Mounts Init'.split())
HOST_REQUIRED = frozenset('Binds ContainerIDFile LogConfig NetworkMode PortBindings RestartPolicy AutoRemove VolumeDriver VolumesFrom ConsoleSize CapAdd CapDrop CgroupnsMode Dns DnsOptions DnsSearch ExtraHosts GroupAdd IpcMode Cgroup Links OomScoreAdj PidMode Privileged PublishAllPorts ReadonlyRootfs SecurityOpt UTSMode UsernsMode ShmSize Isolation CpuShares Memory NanoCpus CgroupParent BlkioWeight BlkioWeightDevice BlkioDeviceReadBps BlkioDeviceWriteBps BlkioDeviceReadIOps BlkioDeviceWriteIOps CpuPeriod CpuQuota CpuRealtimePeriod CpuRealtimeRuntime CpusetCpus CpusetMems Devices DeviceCgroupRules DeviceRequests MemoryReservation MemorySwap MemorySwappiness OomKillDisable PidsLimit Ulimits CpuCount CpuPercent IOMaximumIOps IOMaximumBandwidth MaskedPaths ReadonlyPaths'.split())

def same(a, b):
    # JSON bool and number equality in Python is not semantic type equality.
    return type(a) is type(b) and (a == b if type(a) not in (dict, list) else
        (set(a) == set(b) and all(same(a[k], b[k]) for k in a) if type(a) is dict else
         len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))))

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

def no_request(value, kind):
    return value is None or type(value) is kind and len(value) == 0

def environment_map(rows):
    if type(rows) is not list or len(rows) > 256:
        return None
    result = {}
    for row in rows:
        if type(row) is not str or '=' not in row or len(row) > 16384:
            return None
        key, value = row.split('=', 1)
        if not re.fullmatch('[A-Za-z_][A-Za-z0-9_]*', key) or key in result:
            return None
        result[key] = value
    return result

class Fields:
    def __init__(self, obj, required, optional):
        if type(obj) is not dict:
            raise ValueError('CONFIGURATION_OBJECT_REQUIRED')
        self.obj, self.known = obj, required | optional
        self.results = {k: 'UNCLASSIFIED' for k in sorted(set(obj) & self.known)}
        self.missing = sorted(required - set(obj))
        self.unknown = len(set(obj) - self.known)

    def rule(self, key, ok, status='REQUEST_CONFORMS'):
        if key in self.obj:
            if key in self.results and self.results[key] != 'UNCLASSIFIED':
                raise ValueError('DUPLICATE_FIELD_RULE')
            self.results[key] = status if ok else 'REJECTED'

    def exact(self, key, value):
        self.rule(key, same(self.obj.get(key), value))

    def empty(self, key, kind):
        self.rule(key, no_request(self.obj.get(key), kind))

    def report(self):
        # Only schema-defined names and finite reason codes are public. Unknown
        # field names and ALL values, including paths and labels, stay private.
        statuses = set(self.results.values())
        rejected = bool(self.missing or self.unknown or {'REJECTED', 'UNCLASSIFIED'} & statuses)
        return {'fieldCount': len(self.obj), 'unknownFieldCount': self.unknown,
                'missingRequiredFields': self.missing, 'fields': self.results,
                'declaredRequestConforms': not rejected,
                'effectivePolicyEvidenceRequired': 'EFFECTIVE_POLICY_REQUIRED' in statuses,
                'imageProvenanceEvidenceRequired': 'IMAGE_PROVENANCE_REQUIRED' in statuses,
                'configurationHash': digest(self.obj)}

def mounts_match(actual, intended):
    if type(actual) is not list or type(intended) is not list or len(actual) != len(intended):
        return False
    expected = {(v['source'], v['target']) for v in intended}
    if len(expected) != len(intended) or not all(v['readOnly'] is True for v in intended):
        return False
    seen = set()
    for value in actual:
        if type(value) is not dict or not {'Type', 'Source', 'Target', 'ReadOnly'} <= set(value):
            return False
        if set(value) - {'Type', 'Source', 'Target', 'ReadOnly', 'Consistency', 'BindOptions'}:
            return False
        if value['Type'] != 'bind' or value['ReadOnly'] is not True or value.get('Consistency', '') != '':
            return False
        pair = (value['Source'], value['Target'])
        if pair in seen or pair not in expected:
            return False
        seen.add(pair)
        options = value.get('BindOptions')
        if options is not None:
            if type(options) is not dict or set(options) - {'Propagation', 'NonRecursive', 'CreateMountpoint', 'ReadOnlyNonRecursive', 'ReadOnlyForceRecursive'}:
                return False
            if options.get('Propagation', '') not in ('', 'rprivate'):
                return False
            if any(options.get(k, False) is not False for k in ('NonRecursive', 'CreateMountpoint', 'ReadOnlyNonRecursive', 'ReadOnlyForceRecursive')):
                return False
    return seen == expected

def review_fields(config, host, base, spec, journal, container_id, sealed_environment):
    """Review complete objects using already authenticated in-memory inputs.

    Caller must prove identity, stopped state, byte/source/receipt binding and
    exact sealed_environment pairing. This function cannot authenticate inputs,
    inspect effective mounts/namespaces, sign or authorize a start.
    """
    c = Fields(config, CONFIG_REQUIRED, CONFIG_OPTIONAL)
    h = Fields(host, HOST_REQUIRED, HOST_OPTIONAL)
    for key in ('AttachStdin', 'Tty', 'OpenStdin', 'StdinOnce', 'ArgsEscaped', 'NetworkDisabled'):
        c.exact(key, False)
    # docker create CLI, without -a or -i, requests stdout/stderr attachment.
    # This is not OpenStdin/interactive execution or permission to start.
    c.exact('AttachStdout', True); c.exact('AttachStderr', True)
    c.exact('Hostname', container_id[:12]); c.exact('Domainname', '')
    c.exact('User', spec['user']); c.exact('Image', spec['image'])
    actual_env, expected_env = environment_map(config.get('Env')), environment_map(sealed_environment)
    c.rule('Env', actual_env is not None and expected_env is not None and same(actual_env, expected_env))
    c.exact('Cmd', spec['command'] or base.get('Cmd'))
    c.exact('Entrypoint', base.get('Entrypoint'))
    c.exact('WorkingDir', base.get('WorkingDir', ''))
    c.empty('Volumes', dict)
    labels = {**(base.get('Labels') or {}), 'ouf.semantic.candidate.transaction': journal['transaction'],
              'ouf.semantic.candidate.manifest': journal['manifestHash']}
    c.exact('Labels', labels)
    health = config.get('Healthcheck')
    c.rule('Healthcheck', type(health) is dict and health.get('Test') == ['NONE']
           and not set(health) - {'Test', 'Interval', 'Timeout', 'StartPeriod', 'StartInterval', 'Retries'}
           and all(type(v) is int and v == 0 for k, v in health.items() if k != 'Test'))
    if 'Healthcheck' not in config:
        c.missing.append('Healthcheck')
    # Image metadata can be inherited without being trusted publisher evidence.
    for key in ('ExposedPorts', 'OnBuild', 'StopSignal', 'Shell'):
        c.rule(key, same(config.get(key), base.get(key)), 'IMAGE_PROVENANCE_REQUIRED')
    c.exact('StopTimeout', None)
    for key in ('AutoRemove', 'Privileged', 'PublishAllPorts'):
        h.exact(key, False)
    h.exact('ReadonlyRootfs', spec['readOnlyRoot'])
    h.exact('RestartPolicy', {'Name': 'no', 'MaximumRetryCount': 0})
    h.exact('CapDrop', ['ALL'])
    h.exact('Memory', spec['memoryBytes']); h.exact('MemorySwap', spec['memoryBytes'])
    h.exact('PidsLimit', spec['pidsLimit']); h.exact('Dns', spec['dnsServers'])
    for key in ('Binds', 'VolumesFrom', 'CapAdd', 'DnsOptions', 'DnsSearch', 'ExtraHosts', 'GroupAdd', 'Links',
                'BlkioWeightDevice', 'BlkioDeviceReadBps', 'BlkioDeviceWriteBps', 'BlkioDeviceReadIOps',
                'BlkioDeviceWriteIOps', 'Devices', 'DeviceCgroupRules', 'DeviceRequests'):
        h.empty(key, list)
    for key in ('PortBindings', 'Annotations', 'StorageOpt', 'Tmpfs', 'Sysctls'):
        h.empty(key, dict)
    for key in ('ContainerIDFile', 'VolumeDriver', 'Cgroup', 'PidMode', 'UTSMode', 'Isolation', 'CgroupParent', 'CpusetCpus', 'CpusetMems'):
        h.exact(key, '')
    for key in ('OomScoreAdj', 'CpuShares', 'NanoCpus', 'BlkioWeight', 'CpuPeriod', 'CpuQuota', 'CpuRealtimePeriod',
                'CpuRealtimeRuntime', 'MemoryReservation', 'CpuCount', 'CpuPercent', 'IOMaximumIOps', 'IOMaximumBandwidth'):
        h.exact(key, 0)
    h.exact('ConsoleSize', [0, 0]); h.exact('MemorySwappiness', None)
    h.rule('OomKillDisable', host.get('OomKillDisable') is None or host.get('OomKillDisable') is False)
    networks = spec.get('networks')
    h.rule('NetworkMode', type(networks) is list and bool(networks)
           and host.get('NetworkMode') in (networks[0]['id'], networks[0]['name']))
    h.rule('Mounts', mounts_match(host.get('Mounts'), spec['mounts']))
    if spec['mounts'] and 'Mounts' not in host:
        h.missing.append('Mounts')
    # These defaults depend on daemon/host and the generated OCI process,
    # namespaces, seccomp/LSM, mounts and cgroup resources. They never become
    # accepted solely because they were not overridden in docker create.
    h.rule('CgroupnsMode', host.get('CgroupnsMode') == 'private', 'EFFECTIVE_POLICY_REQUIRED')
    h.rule('IpcMode', host.get('IpcMode') == 'private', 'EFFECTIVE_POLICY_REQUIRED')
    h.rule('UsernsMode', host.get('UsernsMode') == '', 'EFFECTIVE_POLICY_REQUIRED')
    h.rule('Runtime', type(host.get('Runtime')) is str and bool(host.get('Runtime')), 'EFFECTIVE_POLICY_REQUIRED')
    h.rule('SecurityOpt', no_request(host.get('SecurityOpt'), list), 'EFFECTIVE_POLICY_REQUIRED')
    h.rule('ShmSize', type(host.get('ShmSize')) is int and host['ShmSize'] == 64 * 1024 * 1024, 'EFFECTIVE_POLICY_REQUIRED')
    h.rule('Init', host.get('Init') is None or host.get('Init') is False, 'EFFECTIVE_POLICY_REQUIRED')
    h.rule('Umask', host.get('Umask') is None, 'EFFECTIVE_POLICY_REQUIRED')
    h.rule('Ulimits', no_request(host.get('Ulimits'), list), 'EFFECTIVE_POLICY_REQUIRED')
    for key in ('MaskedPaths', 'ReadonlyPaths'):
        value = host.get(key)
        h.rule(key, type(value) is list and bool(value) and all(type(v) is str for v in value)
               and len(set(value)) == len(value), 'EFFECTIVE_POLICY_REQUIRED')
    log = host.get('LogConfig')
    h.rule('LogConfig', type(log) is dict and set(log) == {'Type', 'Config'}
           and log['Type'] in ('json-file', 'local') and no_request(log['Config'], dict), 'EFFECTIVE_POLICY_REQUIRED')
    cr, hr = c.report(), h.report()
    return {'schema': 'ouf.semantic-creation-field-review.v1', 'config': cr, 'hostConfig': hr,
            'declaredRequestConforms': cr['declaredRequestConforms'] and hr['declaredRequestConforms'],
            'allConfigurationFieldsSemanticallyAccepted': False, 'fullOciAcceptanceProven': False,
            'acceptanceGranted': False, 'signaturesIssued': 0, 'startAuthorized': False}
