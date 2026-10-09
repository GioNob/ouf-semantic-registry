import importlib.util
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import r4a_stage_semantic_mcp_byte_fix as m
root=Path(__file__).resolve().parents[2]/'mcp-file-to-udp'
spec=importlib.util.spec_from_file_location('existing_upload_mode',root/'scripts/r4a_managed_upload_mode.py')
if root.exists():
    environment=importlib.util.module_from_spec(spec);spec.loader.exec_module(environment)
else:
    from scripts import r4a_managed_upload_mode as environment

class MCPByteFixTests(unittest.TestCase):
    def test_existing_modes_have_exactly_the_same_environment(self):
        for value in (None,'probe','true','picker'):
            entries=['MCP_DATABASE_URL=fixture','PATH=/bin']
            if value:entries.append('MCP_MANAGED_UPLOAD_ENABLED='+value)
            if value=='picker':entries.append('MCP_MANAGED_FILE_PICKER_URL=https://api.test/trusted-human/managed-files/')
            options=m.upload_options(entries)
            self.assertEqual(sorted(entries),sorted(environment.expected_environment(entries,options['upload_mode'],options['host_origin'],options['picker_url'])))
    def test_unknown_mode_and_duplicate_environment_block(self):
        for entries in (['MCP_MANAGED_UPLOAD_ENABLED=false'],['PATH=/bin','PATH=/other']):
            with self.assertRaises(RuntimeError):m.upload_options(entries)
    def test_root_and_pin_validation_happen_before_filesystem_changes(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        args=SimpleNamespace(commit='not-a-pin',expected_live_revision='a'*40,stage_root=Path('/never-created'))
        with patch.object(m.os,'geteuid',return_value=0),patch.object(Path,'mkdir') as mkdir:
            with self.assertRaisesRegex(RuntimeError,'PIN_INVALID'):m.main(args)
            mkdir.assert_not_called()

if __name__=='__main__':unittest.main()
