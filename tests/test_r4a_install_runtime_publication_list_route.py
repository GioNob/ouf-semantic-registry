import io
import json
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import r4a_install_runtime_publication_list_route as subject


class ListRoute(unittest.TestCase):
    def route(self):
        return {'id': 'active', 'uri': subject.PATH + '/*', 'methods': ['GET'], 'status': 1,
                'upstream': {'nodes': {'ouf-onboarding:8080': 1}},
                'plugins': {'openid-connect': {'required_scopes': ['ouf.onboarding.configuration.read'],
                                             'client_secret': 'private-example'}}}

    def test_clone_is_exact_get_and_preserves_security_without_mutating_template(self):
        old = self.route()
        new = subject.template([old])
        self.assertEqual(new['uri'], subject.PATH)
        self.assertEqual(new['plugins'], old['plugins'])
        self.assertNotIn('id', new)
        self.assertEqual(old['uri'], subject.PATH + '/*')

    def test_scope_or_rewrite_drift_blocks(self):
        bad = self.route()
        bad['plugins']['openid-connect']['required_scopes'] = []
        with self.assertRaises(RuntimeError):
            subject.template([bad])
        bad = self.route()
        bad['plugins']['proxy-rewrite'] = {'uri': '/wrong'}
        with self.assertRaises(RuntimeError):
            subject.template([bad])

    def test_nested_and_flat_spring_json(self):
        self.assertEqual(subject.tenant_from_json({'SPRING_APPLICATION_JSON': '{"ouf":{"runtime-publications":{"tenant-id":"ouf-lab"}}}'}), 'ouf-lab')
        self.assertEqual(subject.tenant_from_json({'SPRING_APPLICATION_JSON': '{"ouf.runtime-publications.tenant-id":"ouf-lab"}'}), 'ouf-lab')

    def flow(self, stack, root):
        stack.enter_context(patch.object(subject, 'ROOT', root))
        stack.enter_context(patch.object(subject, 'RECEIPT', root / 'receipt.json'))
        stack.enter_context(patch.object(subject.inventory.routes.helper, 'candidate_row', return_value={'state': 'APPROVED'}))
        owner = {'Id': 'live', 'Image': 'image', 'State': {'Running': True}, 'Config': {'Env': []}}
        image = {'Config': {'Labels': {'org.opencontainers.image.revision': subject.inventory.OWNER}}}
        stack.enter_context(patch.object(subject.inventory.routes.helper, 'inspect', side_effect=lambda name, kind='container': image if kind == 'image' else owner))
        stack.enter_context(patch.object(subject.inventory.routes, 'admin_key', return_value='private-key'))
        config = stack.enter_context(patch.object(subject.inventory.routes, 'mounted_config'))
        config.return_value.read_text.return_value = 'private config'
        stack.enter_context(patch('sys.stdout', io.StringIO()))
        route = self.route()
        desired = subject.template([route])
        raw = {'list': [{'value': route}]}
        after = {'list': [{'value': dict(desired, id=subject.ID)}]}
        return stack.enter_context(patch.object(subject, 'api', side_effect=[(raw, '200'), ({}, '404'), ({}, '201'), (after, '200')]))

    def test_plan_has_no_put_or_receipt(self):
        with tempfile.TemporaryDirectory() as d, ExitStack() as stack:
            api = self.flow(stack, Path(d))
            subject.main('plan')
            self.assertEqual([c.args[1] for c in api.call_args_list], ['GET', 'GET'])
            self.assertFalse(subject.RECEIPT.exists())

    def test_apply_single_put_and_blocks_repeated_mutation(self):
        with tempfile.TemporaryDirectory() as d, ExitStack() as stack:
            api = self.flow(stack, Path(d))
            subject.main('apply')
            self.assertEqual([c.args[1] for c in api.call_args_list], ['GET', 'GET', 'PUT', 'GET'])
            self.assertEqual(json.loads(subject.RECEIPT.read_text())['status'], 'PASS')
            api.side_effect = [({'list': [{'value': self.route()}]}, '200')]
            with self.assertRaisesRegex(RuntimeError, 'DO_NOT_REPUT'):
                subject.main('apply')

    def test_private_admin_transport(self):
        with patch.object(subject.inventory.routes.helper, 'run', return_value='{}\n201') as run:
            subject.api('private-key', 'PUT', 'routes/example', self.route(), accepted=('201',))
        self.assertNotIn('private-key', ' '.join(run.call_args.args[0]))
        self.assertNotIn('private-example', ' '.join(run.call_args.args[0]))
        self.assertIn('private-example', run.call_args.kwargs['input'])


if __name__ == '__main__':
    unittest.main()
