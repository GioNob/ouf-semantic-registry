import hashlib
import io
import tarfile
import unittest
from tests.reconcile_semantic_generated_luajit import source_files

class GeneratedLuaJitTests(unittest.TestCase):
    def archive(self, files):
        output=io.BytesIO()
        with tarfile.open(fileobj=output,mode='w:gz') as archive:
            for path,raw in files.items():
                entry=tarfile.TarInfo('luajit/'+path);entry.size=len(raw)
                archive.addfile(entry,io.BytesIO(raw))
        return output.getvalue()
    def fixture(self):
        original=(b'".\\\\?.lua;" LUA_LDIR"?.lua;" LUA_LDIR"?\\\\init.lua;"\n'
                  b'".\\\\?.dll;" LUA_CDIR"?.dll;" LUA_CDIR"loadall.dll"\n')
        patched=(b'".\\\\?.lua;" "!\\\\lualib\\\\?.lua;" LUA_LDIR"?.lua;" LUA_LDIR"?\\\\init.lua;"\n'
                 b'".\\\\?.dll;" "!\\\\lualib\\\\?.so;" LUA_CDIR"?.dll;" LUA_CDIR"loadall.dll"\n')
        files={'src/luaconf.h':original,'src/host/buildvm.c':b'locked generator'}
        expected={'src/luaconf.h':hashlib.sha256(patched).hexdigest(),
                  'src/host/buildvm.c':hashlib.sha256(files['src/host/buildvm.c']).hexdigest()}
        return files,expected
    def test_reconstructs_only_exact_measured_source_bytes(self):
        files,expected=self.fixture()
        selected=source_files(self.archive(files),expected)
        self.assertEqual(set(selected),set(expected))
    def test_rejects_altered_generator_before_execution(self):
        files,expected=self.fixture();files['src/host/buildvm.c']=b'altered generator'
        with self.assertRaises(ValueError):source_files(self.archive(files),expected)
    def test_rejects_missing_source_and_path_traversal(self):
        files,expected=self.fixture();expected['src/missing.c']='a'*64
        with self.assertRaises(ValueError):source_files(self.archive(files),expected)
        files,expected=self.fixture();files['../escape']=b'unsafe'
        with self.assertRaises(ValueError):source_files(self.archive(files),expected)

if __name__=='__main__':unittest.main()
