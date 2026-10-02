import base64
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import tempfile
import time
import ssl
import shutil
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

path = Path(__file__).resolve().parents[1] / 'scripts/r4a_prepare_semantic_provider_credentials.py'
spec = importlib.util.spec_from_file_location('provider_credentials', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
trusted_ancestors = module.trusted_ancestors


class CredentialPreparationTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.addCleanup(self.directory.cleanup)
        self.target = Path(self.directory.name) / 'private' / 'key'
        self.args = SimpleNamespace(mode='apply', realm='realm-custom', client_id='service-custom',
            audience='gateway-custom', tenant='tenant-custom', provider_scope='custom.invoke',
            issuer='https://iam.example:9443/realms/custom', token_endpoint='https://iam.example:9443/token',
            introspection_endpoint='https://iam.example:9443/introspect', actor_claim='actor', tenant_claim='tenant',
            credential_file=self.target, iam_container='iam-custom', kcadm_path='/custom/kcadm.sh',
            semantic_container='semantic-custom', expected_semantic_id='a' * 64, ca_file=None, timeout=2)
        self.binding = {'id': 'a' * 64, 'uid': 10071, 'gid': 10071, 'issuer': self.args.issuer}
        self.workload = Mock()
        self.workload.inspect_state.return_value = {'exists': True, 'internalId': 'custom-internal-id', 'drift': []}
        self.workload.get_json.return_value = {'value': 'private-secret'}
        self.metadata = {'issuer': self.args.issuer, 'token_endpoint': self.args.token_endpoint,
                         'introspection_endpoint': self.args.introspection_endpoint}
        # Leaf permissions/atomic creation use real files. Ancestor metadata is tested separately;
        # GitHub runners keep their checkout under a non-root-owned home directory.
        probe = Path(self.directory.name) / 'ownership-probe'
        probe.write_text('fixture')
        self.ownership_supported = True
        try:
            os.chown(probe, 10071, 10071)
        except OSError:
            self.ownership_supported = False
        finally:
            probe.unlink()
        if os.environ.get('OUF_REQUIRE_CREDENTIAL_OWNERSHIP_TESTS') == '1' and not self.ownership_supported:
            self.fail('required CI credential ownership fixture is unsupported')
        self.ancestors = patch.object(module, 'trusted_ancestors')
        self.ancestors.start(); self.addCleanup(self.ancestors.stop)

    def valid_claims(self):
        now = int(time.time())
        return {'iss': self.args.issuer, 'aud': ['another', self.args.audience], 'scope': 'custom.invoke other.read',
                'actor': 'SERVICE', 'tenant': self.args.tenant, 'azp': self.args.client_id, 'sub': 'account',
                'acr': '1', 'iat': now, 'exp': now + 300}

    def token(self, value=None, header=None):
        def enc(value):
            return base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip('=')
        return enc(header or {'alg': 'RS256'}) + '.' + enc(value or self.valid_claims()) + '.fixture'

    def response(self):
        return {'access_token': self.token(), 'token_type': 'Bearer', 'scope': self.args.provider_scope, 'expires_in': 300}

    def prepare(self, acceptance=295):
        output = io.StringIO()
        with patch.object(module, 'semantic_binding', return_value=self.binding), \
             patch.object(module, 'http_json', return_value=self.metadata), \
             patch.object(module, 'token_acceptance', return_value=acceptance), contextlib.redirect_stdout(output):
            module.prepare(self.args, self.workload)
        return output.getvalue()

    def test_plan_does_not_read_secret_request_token_or_create_directory(self):
        self.args.mode = 'plan'
        with patch.object(module, 'semantic_binding', return_value=self.binding), \
             patch.object(module, 'http_json', return_value=self.metadata), \
             patch.object(module, 'token_acceptance') as token, contextlib.redirect_stdout(io.StringIO()):
            module.prepare(self.args, self.workload)
        self.workload.get_json.assert_not_called(); token.assert_not_called()
        self.assertFalse(self.target.parent.exists())

    @unittest.skipUnless(os.geteuid() == 0, 'file ownership checks require root')
    def test_apply_creates_one_private_copy_and_reapply_preserves_inode(self):
        if not self.ownership_supported:
            self.skipTest('scratch runtime does not support arbitrary numeric owners')
        output = self.prepare()
        self.assertIn('PRIVATE_COPY_CREATED=true', output)
        self.assertNotIn('private-secret', output)
        metadata = self.target.stat(); inode = metadata.st_ino
        self.assertEqual((metadata.st_uid, metadata.st_gid, stat.S_IMODE(metadata.st_mode)), (10071, 10071, 0o600))
        self.assertEqual(self.target.parent.stat().st_uid, 0)
        self.assertEqual(stat.S_IMODE(self.target.parent.stat().st_mode), 0o700)
        self.assertEqual(module.local_secret(self.target, 10071, 10071), 'private-secret')
        self.assertIn('PRIVATE_COPY_CREATED=false', self.prepare())
        self.assertEqual(self.target.stat().st_ino, inode)
        for call in self.workload.get_json.call_args_list:
            self.assertEqual(call.args[:2], ('get', 'clients/custom-internal-id/client-secret'))

    @unittest.skipUnless(os.geteuid() == 0, 'file ownership checks require root')
    def test_verify_preserves_file_and_credential_drift_does_not_overwrite(self):
        if not self.ownership_supported:
            self.skipTest('scratch runtime does not support arbitrary numeric owners')
        self.prepare(); original = self.target.stat().st_ino
        self.args.mode = 'verify'; self.prepare()
        self.assertEqual(self.target.stat().st_ino, original)
        self.workload.get_json.return_value = {'value': 'changed-secret'}
        with self.assertRaisesRegex(module.Blocked, 'EXISTING_CREDENTIAL_DRIFT'):
            self.prepare()
        self.assertEqual(module.local_secret(self.target, 10071, 10071), 'private-secret')

    def test_inactive_introspection_prevents_any_persistent_write(self):
        with patch.object(module, 'semantic_binding', return_value=self.binding), \
             patch.object(module, 'http_json', return_value=self.metadata), \
             patch.object(module, 'token_acceptance', side_effect=module.Blocked('TOKEN_INTROSPECTION_INACTIVE')):
            with self.assertRaisesRegex(module.Blocked, 'TOKEN_INTROSPECTION_INACTIVE'):
                module.prepare(self.args, self.workload)
        self.assertFalse(self.target.parent.exists())

    def test_rotation_and_runtime_drift_prevent_persistent_write(self):
        self.workload.get_json.side_effect = [{'value': 'old-secret'}, {'value': 'new-secret'}]
        with self.assertRaisesRegex(module.Blocked, 'IAM_CREDENTIAL_CHANGED_DURING_PREPARATION'):
            self.prepare()
        self.assertFalse(self.target.parent.exists())
        self.workload.get_json.side_effect = None
        with patch.object(module, 'semantic_binding', side_effect=[self.binding, dict(self.binding, id='b' * 64)]), \
             patch.object(module, 'http_json', return_value=self.metadata), patch.object(module, 'token_acceptance', return_value=295):
            with self.assertRaisesRegex(module.Blocked, 'RUNTIME_CHANGED_DURING_PREPARATION'):
                module.prepare(self.args, self.workload)
        self.assertFalse(self.target.parent.exists())

    def test_profile_and_endpoint_drift_fail_before_secret_read(self):
        self.workload.inspect_state.return_value['drift'] = ['MAPPER_DRIFT:actor']
        with self.assertRaisesRegex(module.Blocked, 'WORKLOAD_PROFILE_OR_SCOPE_DRIFT'):
            self.prepare()
        self.workload.get_json.assert_not_called()
        self.workload.inspect_state.return_value['drift'] = []
        with patch.object(module, 'semantic_binding', return_value=self.binding), \
             patch.object(module, 'http_json', return_value=dict(self.metadata, token_endpoint='https://other.example/token')):
            with self.assertRaisesRegex(module.Blocked, 'OIDC_ENDPOINT_BINDING_MISMATCH'):
                module.prepare(self.args, self.workload)
        self.workload.get_json.assert_not_called()

    def test_token_request_and_authority_validation_bind_exact_context(self):
        claims = self.valid_claims()
        with patch.object(module, 'http_json', side_effect=[self.response(), dict(claims, active=True)]) as request:
            ttl = module.token_acceptance(self.args, 'secret-only-in-memory')
        self.assertGreaterEqual(ttl, 290)
        self.assertEqual(request.call_args_list[0].args[1], self.args.token_endpoint)
        self.assertEqual(request.call_args_list[0].args[2]['scope'], 'custom.invoke')
        self.assertEqual(request.call_args_list[1].args[1], self.args.introspection_endpoint)
        self.assertNotIn('secret-only-in-memory', request.call_args_list[0].args[1])

    def test_claim_mismatches_and_expiry_are_rejected(self):
        now = time.time()
        for name, value in [('iss', 'https://foreign.example'), ('aud', ['wrong']), ('actor', 'HUMAN'),
                            ('tenant', 'wrong'), ('azp', 'wrong'), ('scope', 'other.read'), ('sub', ''),
                            ('exp', True), ('exp', int(now) + 20), ('iat', int(now) - 600), ('nbf', int(now) + 300)]:
            claims = self.valid_claims(); claims[name] = value
            with self.subTest(name=name, value=value), self.assertRaisesRegex(module.Blocked, 'TOKEN_CLAIMS_INVALID'):
                module.claims(self.args, claims, now)

    def test_inactive_or_conflicting_authority_and_unsigned_token_rejected(self):
        for authority in [dict(self.valid_claims(), active=False), dict(self.valid_claims(), active=True, sub='different')]:
            with patch.object(module, 'http_json', side_effect=[self.response(), authority]), self.assertRaises(module.Blocked):
                module.token_acceptance(self.args, 'secret')
        response = self.response(); response['access_token'] = self.token(header={'alg': 'none'})
        with patch.object(module, 'http_json', return_value=response) as request, self.assertRaisesRegex(module.Blocked, 'TOKEN_RESPONSE_INVALID'):
            module.token_acceptance(self.args, 'secret')
        self.assertEqual(request.call_count, 1)

    def test_deadline_interrupts_body_receipt(self):
        started = time.monotonic()
        with self.assertRaisesRegex(module.Blocked, 'IAM_REQUEST_TIMEOUT'):
            with module.deadline(0.05):
                time.sleep(0.2)
        self.assertLess(time.monotonic() - started, 0.2)

    def test_strict_https_no_redirect_and_bounded_json_body(self):
        for url in ['http://iam.example/token', 'https://u:secret@iam.example/token', 'https://iam.example/token?secret=x']:
            with self.assertRaisesRegex(module.Blocked, 'IAM_ENDPOINT_INVALID'):
                module.https_url(url)
        with self.assertRaisesRegex(module.Blocked, 'IAM_REDIRECT_FORBIDDEN'):
            module.NoRedirect().redirect_request(None, None, 302, None, None, 'https://evil.example')
        response = Mock(); response.status = 200; response.headers.get_content_type.return_value = 'application/json'
        response.read.return_value = b'x' * 65537
        manager = Mock(); manager.__enter__ = Mock(return_value=response); manager.__exit__ = Mock(return_value=False)
        opener = Mock(); opener.open.return_value = manager
        with patch.object(module, 'build_opener', return_value=opener), self.assertRaisesRegex(module.Blocked, 'IAM_RESPONSE_TOO_LARGE'):
            module.http_json(self.args, self.args.token_endpoint, {'client_secret': 'secret'})
        response.read.assert_called_once_with(65537)
        response.read.return_value = b'{"active":true,"active":false}'
        with patch.object(module, 'build_opener', return_value=opener), self.assertRaisesRegex(module.Blocked, 'IAM_JSON_INVALID'):
            module.http_json(self.args, self.args.token_endpoint)

    @unittest.skipUnless(os.geteuid() == 0, 'file ownership checks require root')
    def test_symlink_permissions_hardlink_and_create_race_fail_closed(self):
        if not self.ownership_supported:
            self.skipTest('scratch runtime does not support arbitrary numeric owners')
        self.prepare()
        self.target.chmod(0o644)
        with self.assertRaisesRegex(module.Blocked, 'CREDENTIAL_FILE_UNSAFE'):
            module.private_target(self.target, 10071, 10071)
        self.target.chmod(0o600)
        alias = self.target.with_name('alias'); os.link(self.target, alias)
        with self.assertRaisesRegex(module.Blocked, 'CREDENTIAL_FILE_UNSAFE'):
            module.private_target(self.target, 10071, 10071)
        alias.unlink(); self.target.unlink(); self.target.symlink_to('/etc/passwd')
        with self.assertRaisesRegex(module.Blocked, 'CREDENTIAL_FILE_UNSAFE'):
            module.private_target(self.target, 10071, 10071)
        self.target.unlink()
        real_link = os.link
        def race(source, destination, **kwargs):
            self.target.write_text('racing-file')
            real_link(source, destination, **kwargs)
        with patch.object(module.os, 'link', side_effect=race), self.assertRaises(FileExistsError):
            module.install_secret(self.args, 'secret', self.binding)
        self.assertEqual(self.target.read_text(), 'racing-file')
        self.assertEqual(list(self.target.parent.glob('.provider-credential-*')), [])

    def test_untrusted_ancestor_and_symlink_directory_rejected(self):
        ancestor = Mock()
        parent = SimpleNamespace(parents=[ancestor])
        for mode, owner in [(stat.S_IFDIR | 0o777, 0), (stat.S_IFDIR | 0o755, 1000), (stat.S_IFLNK | 0o777, 0)]:
            ancestor.lstat.return_value = SimpleNamespace(st_mode=mode, st_uid=owner)
            with self.assertRaisesRegex(module.Blocked, 'CREDENTIAL_ANCESTOR_UNSAFE'):
                trusted_ancestors(parent)
        ancestor.lstat.return_value = SimpleNamespace(st_mode=stat.S_IFDIR | 0o755, st_uid=0)
        trusted_ancestors(parent)
        self.target.parent.symlink_to(Path(self.directory.name), target_is_directory=True)
        with self.assertRaisesRegex(module.Blocked, 'CREDENTIAL_DIRECTORY_UNSAFE'):
            module.private_target(self.target, 10071, 10071)

    def test_selected_container_pin_and_issuer_guard(self):
        row = {'Id': 'a' * 64, 'State': {'Running': True}, 'Config': {'User': '10071:10071',
               'Env': ['OUF_IAM_ISSUER=' + self.args.issuer]}, 'Mounts': []}
        with patch.object(module.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=json.dumps([row]))):
            self.assertEqual(module.semantic_binding(self.args)['uid'], 10071)
        row['Id'] = 'b' * 64
        with patch.object(module.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=json.dumps([row]))), self.assertRaisesRegex(module.Blocked, 'SEMANTIC_ID_OR_RUNNING_STATE_CHANGED'):
            module.semantic_binding(self.args)

    def test_kcadm_wrapper_forbids_all_mutation_and_redacts_session_errors(self):
        module_path = path.parent / 'provision-keycloak-workload.py'
        self.assertTrue(module_path.exists())
        workload = module.workload_module(self.args)
        with patch.object(module.subprocess, 'run') as run:
            with self.assertRaisesRegex(module.Blocked, 'IAM_MUTATION_FORBIDDEN'):
                workload.run('update', 'clients/id')
            run.assert_not_called()
            run.return_value = SimpleNamespace(returncode=1, stdout='secret', stderr='Session has expired')
            with self.assertRaisesRegex(module.Blocked, '^KCADM_SESSION_EXPIRED$'):
                workload.run('get', 'clients/id')
            self.assertEqual(run.call_args.args[0][:5], ['docker', 'exec', '-i', 'iam-custom', '/custom/kcadm.sh'])


@unittest.skipUnless(shutil.which('openssl'), 'TLS fixture generation requires OpenSSL')
class TLSAuthorityTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=Path.cwd()); self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name); cert, key = root / 'cert.pem', root / 'key.pem'
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
                        '-subj', '/CN=127.0.0.1', '-addext', 'subjectAltName=IP:127.0.0.1',
                        '-out', str(cert), '-keyout', str(key)], capture_output=True, check=True, timeout=15)
        self.requests = []
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                body = self.rfile.read(int(self.headers.get('Content-Length', '0')))
                form = parse_qs(body.decode()); owner.requests.append((self.path, form))
                if self.path == '/redirect':
                    self.send_response(302); self.send_header('Location', '/unexpected'); self.end_headers(); return
                if self.path == '/token':
                    if form.get('client_secret') != ['fixture-secret']:
                        self.send_response(401); self.end_headers(); return
                    value = {'access_token': owner.token, 'token_type': 'Bearer', 'expires_in': 300, 'scope': 'custom.invoke'}
                elif self.path == '/introspect':
                    value = dict(owner.claims, active=owner.active and form.get('token') == [owner.token])
                else:
                    self.send_response(404); self.end_headers(); return
                raw = json.dumps(value).encode()
                self.send_response(200); self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(raw))); self.end_headers(); self.wfile.write(raw)
        self.server = HTTPServer(('127.0.0.1', 0), Handler)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); context.load_cert_chain(cert, key)
        self.server.socket = context.wrap_socket(self.server.socket, server_side=True)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close); self.addCleanup(self.server.shutdown)
        base = 'https://127.0.0.1:' + str(self.server.server_port)
        self.args = SimpleNamespace(issuer=base + '/realm', token_endpoint=base + '/token',
            introspection_endpoint=base + '/introspect', client_id='service-custom', audience='gateway-custom',
            tenant='tenant-custom', actor_claim='actor', tenant_claim='tenant', provider_scope='custom.invoke',
            ca_file=str(cert), timeout=2)
        now = int(time.time()); self.active = True
        self.claims = {'iss': self.args.issuer, 'aud': 'gateway-custom', 'scope': 'custom.invoke',
                       'actor': 'SERVICE', 'tenant': 'tenant-custom', 'azp': 'service-custom',
                       'sub': 'fixture-service', 'acr': '1', 'iat': now, 'exp': now + 300}
        def enc(value):
            return base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip('=')
        self.token = enc({'alg': 'RS256'}) + '.' + enc(self.claims) + '.fixture'

    def test_real_trusted_tls_token_and_introspection(self):
        self.assertGreaterEqual(module.token_acceptance(self.args, 'fixture-secret'), 290)
        self.assertEqual([r[0] for r in self.requests], ['/token', '/introspect'])
        self.assertEqual(self.requests[0][1]['grant_type'], ['client_credentials'])
        self.assertEqual(self.requests[1][1]['token_type_hint'], ['access_token'])
        self.active = False
        with self.assertRaisesRegex(module.Blocked, 'TOKEN_INTROSPECTION_INACTIVE'):
            module.token_acceptance(self.args, 'fixture-secret')

    def test_untrusted_tls_and_redirect_are_not_followed(self):
        ca = self.args.ca_file; self.args.ca_file = None
        with self.assertRaisesRegex(module.Blocked, 'IAM_REQUEST_FAILED'):
            module.http_json(self.args, self.args.token_endpoint, {'client_secret': 'fixture-secret'})
        self.assertEqual(self.requests, [])
        self.args.ca_file = ca
        with self.assertRaisesRegex(module.Blocked, 'IAM_REDIRECT_FORBIDDEN'):
            module.http_json(self.args, self.args.token_endpoint.replace('/token', '/redirect'), {'client_secret': 'fixture-secret'})
        self.assertEqual([r[0] for r in self.requests], ['/redirect'])


if __name__ == '__main__':
    unittest.main()
