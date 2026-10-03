import unittest
import subprocess
from unittest.mock import patch
from types import SimpleNamespace
import r4a_udp_token_transport_inventory as inventory


class TokenInventoryTests(unittest.TestCase):
    def test_realistic_execstart_reaches_script_ast_and_token_literal_check(self):
        start='{ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 /opt/ouf/ops/refresh-token.py ; ignore_errors=no ; }'
        with patch.object(inventory,'run',return_value=start),patch.object(inventory.Path,'lstat',return_value=SimpleNamespace(st_mode=0o100700,st_uid=0)),patch.object(inventory.Path,'read_text',return_value="target='/private/token'\nos.replace(temp,target)"),patch('builtins.print') as output:
            inventory.inspect_services(['real.service'],'/private/token')
            text=str(output.call_args_list)
            self.assertIn('REFRESHER_PYTHON_SCRIPT_COUNT=1',text)
            self.assertIn('execution_token_target_literal_present',text)
            self.assertNotIn('UNAVAILABLE',text)
            self.assertNotIn('/private/token',text)
    def test_service_error_is_redacted_and_does_not_hide_next_unit(self):
        with patch.object(inventory,'run',side_effect=[subprocess.CalledProcessError(1,['PRIVATE']), '']),patch('builtins.print') as output:
            inventory.inspect_services(['first.service','next.service'],'/private/token')
            rendered=str(output.call_args_list)
            self.assertIn('REFRESHER_UNIT=first.service',rendered)
            self.assertIn('STAGE=EXEC_START TYPE=CalledProcessError',rendered)
            self.assertIn('REFRESHER_UNIT=next.service',rendered)
            self.assertNotIn('PRIVATE',rendered)
    def test_uninstantiated_template_is_skipped_without_systemctl_show(self):
        with patch.object(inventory,'run') as tool,patch('builtins.print'):
            inventory.inspect_services(['tokens@.service'],'/private/token')
            tool.assert_not_called()
    def test_truncating_and_atomic_operations_are_reported_without_source_values(self):
        result=inventory.writer_facts("open(path, 'w').write(secret)\npath.write_text(secret)\nos.replace(temp, path)\n")
        self.assertEqual(result['truncating_write_sites'],2)
        self.assertEqual(result['replace_or_rename_sites'],1)
        self.assertTrue(result['token_destination_write_behavior_not_proven'])
        self.assertNotIn('secret',str(result))
    def test_read_mode_and_unknown_dynamic_modes_not_classified_as_truncation(self):
        result=inventory.writer_facts("open(path,'r')\nopen(path,mode=runtime_mode)\n")
        self.assertEqual(result['truncating_write_sites'],0)
    def test_mount_mapping_distinguishes_file_and_directory_and_rejects_escape(self):
        container={'Mounts':[{'Type':'bind','Source':'/tmp/auth','Destination':'/run/auth'}]}
        self.assertEqual(inventory.mapped(container,'/run/auth/token')[1],False)
        with self.assertRaises(ValueError):inventory.mapped(container,'/run/auth/../secret')
        container['Mounts'][0]['Destination']='/run/auth/token'
        self.assertEqual(inventory.mapped(container,'/run/auth/token')[1],True)


if __name__=='__main__':unittest.main()
