import copy
import unittest
from tools.review_semantic_static_module_coverage import review

class StaticModuleCoverageTests(unittest.TestCase):
    def setUp(self):
        self.configure = "--prefix=/usr/local/openresty/nginx --add-module=../echo-nginx-module-0.65 --add-module=/native-source/extra --with-cc-opt='-O2 -DAPISIX_RUNTIME_VER=1.3.16'"
        self.elf = b'\x7fELF' + self.configure.encode() + b'\x00'
        self.sources = {'openresty': {'archives': [
            {'file': 'echo-nginx-module-0.65.tar.gz', 'url': 'https://github.com/openresty/echo-nginx-module/tarball/v0.65', 'sha256': 'a' * 64},
            {'file': 'unused-0.1.tar.gz', 'url': 'https://github.com/openresty/unused/tarball/v0.1', 'sha256': 'b' * 64}]},
            'embeddedSourceDirectories': ['echo-nginx-module-0.65', 'unused-0.1'],
            'sourceFiles': {'compiledSourceFiles': {'bundle/echo-nginx-module-0.65/src/a.c': 'c' * 64}}}
        self.sbom = {'artifacts': []}
    def result(self):
        return review(self.configure, self.elf, self.sources, self.sbom)
    def test_reports_missing_individual_module_and_excludes_unused_download(self):
        r = self.result()
        self.assertEqual(r['unrepresentedStaticModules'], ['echo-nginx-module-0.65'])
        self.assertEqual(r['configuredBundledModuleCount'], 1)
        self.assertFalse(r['dependencyCoverageAccepted'])
    def test_existing_individual_identity_does_not_grant_full_coverage(self):
        self.sbom['artifacts'] = [{'name': 'echo-nginx-module', 'locations': [{'path': '/usr/local/openresty/nginx/sbin/nginx'}]}]
        r = self.result()
        self.assertEqual(r['unrepresentedStaticModules'], [])
        self.assertFalse(r['dependencyCoverageAccepted'])
    def test_rejects_proof_not_embedded_in_actual_binary(self):
        with self.assertRaises(ValueError): review(self.configure + ' --with-debug', self.elf, self.sources, self.sbom)
    def test_rejects_unlocked_compiled_module(self):
        self.sources['openresty']['archives'] = []
        with self.assertRaises(ValueError): self.result()
    def test_rejects_missing_compiled_source_hashes(self):
        self.sources['sourceFiles']['compiledSourceFiles'] = {}
        with self.assertRaises(ValueError): self.result()
    def test_rejects_module_present_only_at_unrelated_location(self):
        self.sbom['artifacts'] = [{'name': 'echo-nginx-module', 'locations': [{'path': '/tmp/example'}]}]
        self.assertEqual(self.result()['unrepresentedStaticModules'], ['echo-nginx-module-0.65'])
    def test_rejects_duplicate_configure_module_paths(self):
        self.configure += ' --add-module=../echo-nginx-module-0.65'
        self.elf += self.configure.encode()
        with self.assertRaises(ValueError): self.result()
    def test_upstream_directory_alias_requires_matching_archive(self):
        self.configure = '--add-module=../ngx_lua-0.10.32rc5'
        self.elf = self.configure.encode()
        self.sources['embeddedSourceDirectories'] = ['ngx_lua-0.10.32rc5']
        self.sources['openresty']['archives'][0]['file'] = 'lua-nginx-module-0.10.32rc5.tar.gz'
        self.sources['openresty']['archives'][0]['url'] = 'https://github.com/openresty/lua-nginx-module/archive/v0.10.32rc5.tar.gz'
        self.sources['sourceFiles']['compiledSourceFiles'] = {'bundle/ngx_lua-0.10.32rc5/src/a.c': 'c' * 64}
        self.assertEqual(self.result()['modules'][0]['repository'], 'openresty/lua-nginx-module')

if __name__ == '__main__': unittest.main()
