import unittest
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import r4a_udp_reference_transport_probe as probe


class ReferenceTransportTests(unittest.TestCase):
    def test_absent_optional_refs_match_and_drift_refused(self):
        refs={'sourceSchemaRef':'schema','semanticPublicationSetRef':'set','adapterProfileRef':'adapter'}
        bundle={'extractionProfile':{'runtime':{'execution':dict(refs)}}}
        self.assertTrue(probe.compare(refs,bundle))
        bundle['extractionProfile']['runtime']['execution']['sourceSchemaRef']='other'
        self.assertFalse(probe.compare(refs,bundle))
    def test_get_uses_stdin_only_and_never_posts_or_prints_response_values(self):
        args=SimpleNamespace(network='other-network',curl_image='registry/curl:version')
        with tempfile.TemporaryDirectory() as folder:
            token=Path(folder)/'token';token.write_text('e30.e30.sig')
            with patch('subprocess.run',return_value=SimpleNamespace(stdout='{"private":"SECRET"}\n200')) as tool,patch('builtins.print') as output:
                result=probe.get(args,'https://other.example',token,'/exact?ref=private','LABEL')
                self.assertEqual(result,{'private':'SECRET'})
                self.assertNotIn('e30.e30.sig',' '.join(tool.call_args.args[0]))
                self.assertIn('request = "GET"',tool.call_args.kwargs['input'])
                self.assertNotIn('SECRET',str(output.call_args_list))
            with patch('subprocess.run',return_value=SimpleNamespace(stdout='PRIVATE\n403')),patch('builtins.print') as output:
                with self.assertRaises(RuntimeError):probe.get(args,'https://other.example',token,'/exact','LABEL')
                self.assertNotIn('PRIVATE',str(output.call_args_list))


if __name__=='__main__':unittest.main()
