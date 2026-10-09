import unittest
from tools.supplement_semantic_rebuilt_native_sbom import luajit_runtime_version, sha, ROOT


class LuaJitRuntimeIdentityTests(unittest.TestCase):
    def setUp(self):
        self.rows = {ROOT + p: {'elf': True, 'raw': b'ELF\x00LuaJIT 2.1.1787558776 -- Copyright\x00'}
                     for p in ('luajit/bin/luajit-2.1.1787558776',
                               'luajit/lib/libluajit-5.1.so.2.1.1787558776')}
        self.sources = {'sourceFiles': {'compiledSourceFiles': {
            'bundle/LuaJIT-2.1-20260824/.relver': sha(b'1787558776\n')}}}

    def test_uses_built_in_version_instead_of_source_release_tag(self):
        self.assertEqual(luajit_runtime_version(self.rows,self.sources),'2.1.1787558776')

    def test_renamed_binary_without_matching_bytes_rejected(self):
        path=ROOT+'luajit/bin/luajit-2.1.1787558776'
        self.rows[path.replace('1787558776','9999999999')]=self.rows.pop(path)
        with self.assertRaises(ValueError): luajit_runtime_version(self.rows,self.sources)

    def test_disagreeing_executable_and_library_rejected(self):
        path=ROOT+'luajit/lib/libluajit-5.1.so.2.1.1787558776'
        self.rows[path.replace('1787558776','9999999999')]={'elf':True,'raw':b'LuaJIT 2.1.9999999999\x00'}
        del self.rows[path]
        with self.assertRaises(ValueError): luajit_runtime_version(self.rows,self.sources)

    def test_wrong_compiled_relver_rejected(self):
        self.sources['sourceFiles']['compiledSourceFiles']['bundle/LuaJIT-2.1-20260824/.relver']=sha(b'9999999999\n')
        with self.assertRaises(ValueError): luajit_runtime_version(self.rows,self.sources)

    def test_missing_embedded_identity_rejected(self):
        next(iter(self.rows.values()))['raw']=b'unknown ELF version'
        with self.assertRaises(ValueError): luajit_runtime_version(self.rows,self.sources)

    def test_ambiguous_embedded_version_rejected(self):
        next(iter(self.rows.values()))['raw']+=b'LuaJIT 2.1.9999999999\x00'
        with self.assertRaises(ValueError): luajit_runtime_version(self.rows,self.sources)


if __name__ == '__main__':
    unittest.main()
