import contextlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

path = Path(__file__).resolve().parents[1] / 'scripts/r4a_semantic_provider_runtime_bindings.py'
spec = importlib.util.spec_from_file_location('bindings', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def container(env=None, mounts=None):
    return {'Id': 'fixture-id', 'State': {'Running': True},
            'Config': {'User': '10071:10071', 'Env': env or []}, 'Mounts': mounts or []}


class RuntimeBindingTest(unittest.TestCase):
    def test_custom_installation_and_secret_redaction(self):
        sem = container(['OUF_IAM_ISSUER=https://login.example:9443/realms/custom',
                         'OUF_SCHEMA_GOV_GATEWAY_BASE_URL=https://south.example:8443',
                         'OUF_SCHEMA_GOV_TOKEN_ENDPOINT=https://login.example:9443/oauth/token',
                         'OUF_SCHEMA_GOV_CLIENT_SECRET_FILE=/run/private/key',
                         'OUF_SCHEMA_GOV_CLIENT_ID=service-custom',
                         'OUF_SCHEMA_GOV_WORKLOAD_SCOPE=custom.invoke',
                         'OUF_SEM_DB_PASSWORD=do-not-print', 'OTHER_TOKEN=do-not-print'],
                        [{'Destination': '/run/private/key', 'Source': '/private/host-source', 'RW': False}])
        report = module.inventory(sem, container(['MCP_GATEWAY_ENDPOINT=http://gateway.internal:19080/execute']))
        self.assertEqual(report['semantic']['issuer']['url'], 'https://login.example:9443/realms/custom')
        self.assertTrue(report['semantic']['credentialMountProven'])
        self.assertFalse(report['mcpGateway']['https'])
        text = json.dumps(report)
        for hidden in ('do-not-print', 'host-source', 'service-custom', '/run/private/key'):
            self.assertNotIn(hidden, text)
        self.assertFalse(report['tokenRequested'])

    def test_absent_configuration_is_not_proven(self):
        report = module.inventory(container(), container())
        self.assertFalse(report['semantic']['tokenEndpoint']['configured'])
        self.assertFalse(report['semantic']['credentialMountProven'])
        self.assertFalse(report['workloadAuthenticationProven'])

    def test_unsafe_endpoint_never_echoed(self):
        for value in ('https://u:secret@example/path', 'https://example/path?token=secret',
                      'https://example/#secret', 'file:///secret', 'https://example:99999',
                      'https://example/\\secret', 'https://example/\nsecret'):
            with self.assertRaisesRegex(module.Blocked, '^ENDPOINT_BINDING_UNSAFE$'):
                module.endpoint(value)

    def test_duplicate_environment_is_blocked(self):
        with self.assertRaisesRegex(module.Blocked, 'ENVIRONMENT_AMBIGUOUS'):
            module.inventory(container(['OUF_IAM_ISSUER=x', 'OUF_IAM_ISSUER=y']), container())

    def test_exact_read_only_docker_command_and_no_default_bindings(self):
        with patch.object(module.subprocess, 'run') as run:
            run.return_value.returncode = 0
            run.return_value.stdout = json.dumps([container()])
            module.inspect_container('installation-semantic')
            self.assertEqual(run.call_args.args[0], ['docker', 'inspect', 'installation-semantic'])
            with self.assertRaisesRegex(module.Blocked, 'INVALID_CONTAINER_BINDING'):
                module.inspect_container('--malicious')
            self.assertEqual(run.call_count, 1)

    def test_runtime_drift_prints_no_configuration(self):
        output = io.StringIO()
        with patch('sys.argv', ['inventory', '--semantic-container', 'sem', '--mcp-container', 'mcp']), \
             patch.object(module, 'inspect_container', side_effect=[container(), container(), container(['OTHER_TOKEN=secret']), container()]), \
             contextlib.redirect_stdout(output):
            with self.assertRaises(SystemExit):
                module.main()
        self.assertIn('RUNTIME_CHANGED_DURING_INVENTORY', output.getvalue())
        self.assertNotIn('secret', output.getvalue())
        self.assertNotIn('SEMANTIC_PROVIDER_RUNTIME_BINDINGS={', output.getvalue())


if __name__ == '__main__':
    unittest.main()
