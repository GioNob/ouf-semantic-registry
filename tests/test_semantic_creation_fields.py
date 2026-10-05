"""Complete field coverage and hostile substitutions; synthetic public inputs."""
import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import review_semantic_creation_fields as m

def fixture():
    spec = {'user': '10006:10006', 'image': 'sha256:' + 'a' * 64, 'command': [],
            'readOnlyRoot': True, 'memoryBytes': 201326592, 'pidsLimit': 32, 'dnsServers': [],
            'mounts': [{'source': '/CI_PRIVATE_SOURCE', 'target': '/proof', 'readOnly': True}],
            'networks': [{'id': 'b' * 64, 'name': 'ci-private'}]}
    journal = {'transaction': 'c' * 32, 'manifestHash': 'd' * 64}
    cid = 'e' * 64
    base = {'Entrypoint': None, 'Cmd': ['never-start'], 'WorkingDir': '', 'Labels': {'CI_IMAGE': 'CI_PRIVATE_LABEL'}}
    config = {k: False for k in ('AttachStdin', 'AttachStdout', 'AttachStderr', 'Tty', 'OpenStdin', 'StdinOnce')}
    config.update(AttachStdout=True, AttachStderr=True, Hostname=cid[:12], Domainname='', User=spec['user'], Image=spec['image'], Env=['BASE=CI_PRIVATE_VALUE'],
                  Cmd=base['Cmd'], Entrypoint=None, WorkingDir='', Volumes=None,
                  Labels={**base['Labels'], 'ouf.semantic.candidate.transaction': journal['transaction'],
                          'ouf.semantic.candidate.manifest': journal['manifestHash']}, Healthcheck={'Test': ['NONE']})
    host = {k: 0 for k in m.HOST_REQUIRED}
    for k in ('Binds', 'VolumesFrom', 'CapAdd', 'DnsOptions', 'DnsSearch', 'ExtraHosts', 'GroupAdd', 'Links',
              'BlkioWeightDevice', 'BlkioDeviceReadBps', 'BlkioDeviceWriteBps', 'BlkioDeviceReadIOps',
              'BlkioDeviceWriteIOps', 'Devices', 'DeviceCgroupRules', 'DeviceRequests', 'SecurityOpt', 'Ulimits'):
        host[k] = None
    for k in ('ContainerIDFile', 'VolumeDriver', 'Cgroup', 'PidMode', 'UTSMode', 'Isolation', 'CgroupParent', 'CpusetCpus', 'CpusetMems', 'UsernsMode'):
        host[k] = ''
    host.update(LogConfig={'Type': 'json-file', 'Config': {}}, PortBindings={}, RestartPolicy={'Name': 'no', 'MaximumRetryCount': 0},
                AutoRemove=False, Privileged=False, PublishAllPorts=False, ReadonlyRootfs=True, CapDrop=['ALL'],
                Memory=spec['memoryBytes'], MemorySwap=spec['memoryBytes'], PidsLimit=32, Dns=[], ConsoleSize=[0, 0],
                MemorySwappiness=None, OomKillDisable=False, NetworkMode='b' * 64, CgroupnsMode='private', IpcMode='private',
                ShmSize=64 * 1024 * 1024, Runtime='runc', MaskedPaths=['/proc/kcore'], ReadonlyPaths=['/proc/sys'],
                Mounts=[{'Type': 'bind', 'Source': '/CI_PRIVATE_SOURCE', 'Target': '/proof', 'ReadOnly': True}])
    return [config, host, base, spec, journal, cid, ['BASE=CI_PRIVATE_VALUE']]

class Review(unittest.TestCase):
    def test_schema_coverage_matches_reviewed_primary_moby_source(self):
        schema=json.loads((Path(__file__).parent/'fixtures/docker_creation_schema_29_8_1.json').read_text())
        self.assertEqual(schema['commit'],'464cd50c3d9e92877d56940ea160de6fca7bea23')
        for section,required,optional in (('config',m.CONFIG_REQUIRED,m.CONFIG_OPTIONAL),
                                         ('hostConfig',m.HOST_REQUIRED,m.HOST_OPTIONAL)):
            self.assertEqual(required,{v['name'] for v in schema[section] if not v['optional']})
            self.assertEqual(optional,{v['name'] for v in schema[section] if v['optional']})

    def test_all_fields_classified_but_effective_policy_never_self_accepted(self):
        result = m.review_fields(*fixture())
        self.assertTrue(result['declaredRequestConforms'])
        self.assertFalse(result['allConfigurationFieldsSemanticallyAccepted'])
        self.assertFalse(result['acceptanceGranted']); self.assertFalse(result['startAuthorized'])
        self.assertTrue(result['hostConfig']['effectivePolicyEvidenceRequired'])
        for section in ('config', 'hostConfig'):
            self.assertNotIn('UNCLASSIFIED', result[section]['fields'].values())
        raw = json.dumps(result)
        for value in ('CI_PRIVATE_VALUE', 'CI_PRIVATE_SOURCE', 'CI_PRIVATE_LABEL', 'ci-private'):
            self.assertNotIn(value, raw)

    def test_every_required_field_missing_denied(self):
        for index, section, fields in ((0, 'config', m.CONFIG_REQUIRED), (1, 'hostConfig', m.HOST_REQUIRED)):
            for key in fields:
                inputs = fixture(); del inputs[index][key]
                with self.subTest(section=section, key=key):
                    result = m.review_fields(*inputs)
                    self.assertFalse(result['declaredRequestConforms'])
                    self.assertIn(key, result[section]['missingRequiredFields'])

    def test_unknown_top_level_nested_health_restart_logging_and_mount_options_denied(self):
        mutations = [(0, [], 'CI_PRIVATE_UNKNOWN_NAME', 'secret'), (1, [], 'CI_PRIVATE_UNKNOWN_NAME', 'secret'),
                     (0, ['Healthcheck'], 'FutureOption', 'secret'), (1, ['RestartPolicy'], 'FutureOption', 'secret'),
                     (1, ['LogConfig'], 'FutureOption', 'secret'), (1, ['Mounts', 0], 'ImageOptions', {}),
                     (1, ['Mounts', 0], 'BindOptions', {'FutureOption': 'secret'})]
        for index, path, key, value in mutations:
            inputs = fixture(); target = inputs[index]
            for part in path: target = target[part]
            target[key] = value
            with self.subTest(path=path, key=key):
                result = m.review_fields(*inputs)
                self.assertFalse(result['declaredRequestConforms'])
                self.assertNotIn('secret', json.dumps(result))
                self.assertNotIn('CI_PRIVATE_UNKNOWN_NAME', json.dumps(result))

    def test_security_resources_and_startup_substitutions_denied(self):
        mutations = [(0, 'User', '0:0'), (0, 'Entrypoint', ['/evil']), (0, 'Env', ['BASE=wrong']),
                     (0, 'Hostname', 'host'), (0, 'Labels', {}), (0, 'Healthcheck', {'Test': ['CMD', 'evil']}),
                     (1, 'SecurityOpt', ['seccomp=unconfined']), (1, 'Runtime', ''), (1, 'IpcMode', 'host'),
                     (1, 'CgroupnsMode', 'host'), (1, 'PidMode', 'host'), (1, 'UsernsMode', 'host'),
                     (1, 'Privileged', True), (1, 'CapAdd', ['SYS_ADMIN']), (1, 'CapDrop', ['ALL', 'ALL']),
                     (1, 'MemorySwap', -1), (1, 'PidsLimit', -1), (1, 'Init', True),
                     (1, 'LogConfig', {'Type': 'syslog', 'Config': {'syslog-address': 'tcp://secret'}}),
                     (1, 'Tmpfs', {'/etc': 'rw'}), (1, 'Sysctls', {'net.ipv4.ip_forward': '1'}),
                     (1, 'PortBindings', {'80/tcp': [{'HostPort': '80'}]}), (1, 'MaskedPaths', []),
                     (1, 'ReadonlyPaths', []), (1, 'AutoRemove', True)]
        for index, key, value in mutations:
            inputs = fixture(); inputs[index][key] = value
            with self.subTest(key=key): self.assertFalse(m.review_fields(*inputs)['declaredRequestConforms'])

    def test_bool_numeric_coercion_and_no_request_wrong_types_denied(self):
        for index, key, value in ((0, 'AttachStdin', 0), (1, 'MemoryReservation', False),
                                 (1, 'ConsoleSize', [False, False]), (1, 'Binds', ''), (1, 'Annotations', [])):
            inputs = fixture(); inputs[index][key] = value
            with self.subTest(key=key): self.assertFalse(m.review_fields(*inputs)['declaredRequestConforms'])

    def test_docker_env_merge_order_is_semantic_but_duplicate_and_override_denied(self):
        inputs=fixture();inputs[6]=['BASE=CI_PRIVATE_VALUE','SECOND=CI_SECOND_VALUE']
        inputs[0]['Env']=list(reversed(inputs[6]))
        self.assertTrue(m.review_fields(*inputs)['declaredRequestConforms'])
        inputs[0]['Env'].append('BASE=CI_PRIVATE_VALUE')
        self.assertFalse(m.review_fields(*inputs)['declaredRequestConforms'])
        inputs[0]['Env']=['BASE=CI_PRIVATE_VALUE','SECOND=evil']
        self.assertFalse(m.review_fields(*inputs)['declaredRequestConforms'])

    def test_exact_bind_mount_options_missing_duplicate_propagation_and_recursive_overrides_denied(self):
        for kind in ('missing', 'duplicate', 'rw', 'shared', 'recursive', 'create', 'consistency'):
            inputs = fixture(); mounts = inputs[1]['Mounts']
            if kind == 'missing': del inputs[1]['Mounts']
            elif kind == 'duplicate': mounts.append(copy.deepcopy(mounts[0]))
            elif kind == 'rw': mounts[0]['ReadOnly'] = False
            elif kind == 'shared': mounts[0]['BindOptions'] = {'Propagation': 'rshared'}
            elif kind == 'recursive': mounts[0]['BindOptions'] = {'ReadOnlyNonRecursive': True}
            elif kind == 'create': mounts[0]['BindOptions'] = {'CreateMountpoint': True}
            else: mounts[0]['Consistency'] = 'cached'
            with self.subTest(kind=kind): self.assertFalse(m.review_fields(*inputs)['declaredRequestConforms'])

    def test_image_metadata_substitution_requires_provenance_and_denies_unmatched_values(self):
        inputs = fixture(); inputs[0]['StopSignal'] = inputs[2]['StopSignal'] = 'SIGTERM'
        result = m.review_fields(*inputs)
        self.assertTrue(result['declaredRequestConforms'])
        self.assertTrue(result['config']['imageProvenanceEvidenceRequired'])
        inputs[0]['StopSignal'] = 'SIGKILL'
        self.assertFalse(m.review_fields(*inputs)['declaredRequestConforms'])

if __name__ == '__main__': unittest.main()
