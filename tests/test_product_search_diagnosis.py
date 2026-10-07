import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import urllib.error

path = Path(__file__).parents[1] / 'scripts' / 'diagnose_product_search.py'
spec = importlib.util.spec_from_file_location('diagnosis', path)
diagnosis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnosis)


class ProductSearchDiagnosisTest(unittest.TestCase):
    def fixture(self):
        gateway = {'State': {'Running': True}, 'Config': {'Env': ['OUF_UDP_SEARCH_OWNER_KEY=' + 'a' * 64, 'UNRELATED_SECRET=never-print-me']}}
        udp = {'State': {'Running': True}, 'Config': {'Env': [name + '=private-value' for name in diagnosis.SEARCH_NAMES]}, 'Mounts': [{'Destination': 'private-value', 'Source': '/private/key', 'RW': False}], 'NetworkSettings': {'Networks': {'backend': {'IPAddress': '172.18.0.5'}}}}
        return gateway, udp

    def test_redaction_and_worker_inheritance(self):
        gateway, udp = self.fixture()
        report = diagnosis.summarize(gateway, udp, 'env OUF_UDP_SEARCH_OWNER_KEY;\n')
        serialized = json.dumps(report)
        for secret in ('a' * 64, 'never-print-me', 'private-value', '/private/key'):
            self.assertNotIn(secret, serialized)
        self.assertTrue(report['gatewayOwnerKeyInheritedByNginx'])
        self.assertTrue(report['udpOwnerKeyMountReadOnly'])
        self.assertFalse(report['keyFilesRead'])

    def test_missing_values_and_inheritance_are_separate(self):
        gateway, udp = self.fixture()
        udp['Config']['Env'] = [name + '=' for name in diagnosis.SEARCH_NAMES]
        report = diagnosis.summarize(gateway, udp, '# env OUF_UDP_SEARCH_OWNER_KEY;\n')
        self.assertFalse(report['gatewayOwnerKeyInheritedByNginx'])
        self.assertFalse(any(report['udpSearchBindingsPresent'].values()))
        self.assertEqual(report['udpOwnerKeyMountCount'], 0)

    def test_denial_and_unavailability_are_distinguished_without_body_read(self):
        _, udp = self.fixture()
        for status in (403, 503, 404):
            with patch.object(diagnosis.urllib.request, 'build_opener') as builder:
                builder.return_value.open.side_effect = urllib.error.HTTPError('private-url', status, 'private-detail', {}, None)
                result = diagnosis.anonymous_owner_probe(udp, 'backend')
                self.assertEqual(result['httpStatus'], status)
                self.assertFalse(result['objectResponseRead'])
                request = builder.return_value.open.call_args.args[0]
                self.assertNotIn('X-ouf-udp-search-receipt', request.headers)
                self.assertNotIn('Authorization', request.headers)

    def test_no_public_or_loopback_probe(self):
        _, udp = self.fixture()
        for address in ('8.8.8.8', '127.0.0.1'):
            udp['NetworkSettings']['Networks']['backend']['IPAddress'] = address
            with patch.object(diagnosis.urllib.request, 'build_opener') as builder:
                with self.assertRaises(ValueError):
                    diagnosis.anonymous_owner_probe(udp, 'backend')
                builder.assert_not_called()


if __name__ == '__main__':
    unittest.main()
