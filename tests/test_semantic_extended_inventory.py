import copy
import io
import json
import tarfile
import hashlib
import struct
import unittest
from unittest.mock import patch
from tools.extend_semantic_dependency_inventory import literal_manifest, image_files, ownership, rock_bindings, extend, constant_elf_function, add_package

class ExtendedInventoryTests(unittest.TestCase):
    def test_package_identity_uses_paths_and_accepts_binary_evidence_maps(self):
        left={'artifacts':[]};right={'artifacts':[]}
        add_package(left,'brotli','1.1.0','google/brotli',{'usr/lib/example.so':{'raw':b'ELF'}})
        add_package(right,'brotli','1.1.0','google/brotli',['usr/lib/example.so'])
        self.assertEqual(left,right)
    def test_shared_lua_bytes_retain_every_proven_source_component(self):
        digest='a'*64
        sources={'modules':[], 'sourceFiles':{'modules':[], 'compiledSourceFiles':{
            'bundle/lua-resty-dns-0.23/lib/shared.lua':digest,
            'bundle/lua-resty-core-0.1/lib/shared.lua':digest}},
            'openresty':{'archives':[
                {'file':'lua-resty-dns-0.23.tar.gz','url':'https://github.com/openresty/lua-resty-dns/tarball/v0.23','sha256':'b'*64},
                {'file':'lua-resty-core-0.1.tar.gz','url':'https://github.com/openresty/lua-resty-core/tarball/v0.1','sha256':'c'*64}]}}
        rows={'usr/local/openresty/nginx/sbin/nginx':{'raw':b'ELF'},
              'usr/local/openresty/lualib/shared.lua':{'sha256':digest}}
        with patch('tools.extend_semantic_dependency_inventory.review',return_value={'modules':[]}):
            doc,details=extend({'artifacts':[]},sources,rows,'--prefix=example')
        self.assertEqual({p['name'] for p in doc['artifacts']},{'lua-resty-dns','lua-resty-core'})
        self.assertEqual(details['unresolvedOpenRestyLuaFiles'],[])
    def accessor(self, body):
        raw=bytearray(1024);raw[:6]=b'\x7fELF\x02\x01'
        struct.pack_into('<H',raw,18,62);struct.pack_into('<Q',raw,40,128);struct.pack_into('<HH',raw,58,64,4)
        strings=b'\x00BrotliEncoderVersion\x00'
        sections=[(0,0,0,0,0,0,0,0,0,0),(0,11,0,0,512,24,2,0,8,24),(0,3,0,0,600,len(strings),0,0,1,0),(0,1,0,4096,700,len(body),0,0,16,0)]
        for n,section in enumerate(sections):struct.pack_into('<IIQQQQIIQQ',raw,128+n*64,*section)
        struct.pack_into('<IBBHQQ',raw,512,1,2,0,3,4096,len(body));raw[600:600+len(strings)]=strings;raw[700:700+len(body)]=body
        return bytes(raw)
    def test_reads_version_accessor_without_running_library(self):
        raw=self.accessor(b'\xf3\x0f\x1e\xfa\xb8\x00\x10\x00\x01\xc3')
        self.assertEqual(constant_elf_function(raw,'BrotliEncoderVersion'),0x01001000)
    def test_rejects_accessor_that_calls_other_code(self):
        with self.assertRaises(ValueError):constant_elf_function(self.accessor(b'\xe8\x00\x00\x00\x00\xc3'),'BrotliEncoderVersion')
    def test_rejects_wrong_symbol_and_architecture(self):
        raw=self.accessor(b'\xb8\x00\x10\x00\x01\xc3')
        with self.assertRaises(ValueError):constant_elf_function(raw,'OtherVersion')
        raw=bytearray(raw);struct.pack_into('<H',raw,18,183)
        with self.assertRaises(ValueError):constant_elf_function(bytes(raw),'BrotliEncoderVersion')
    def test_python_identity_does_not_cover_arbitrary_native_site_packages(self):
        doc={'artifacts':[{'id':'py','name':'python','type':'binary','locations':[]}]}
        row={'elf':True,'sha256':'a'*64,'raw':b''}
        self.assertEqual(len(ownership(doc,{'usr/local/lib/python3.13/site-packages/unowned.so':row})['unresolvedElfFiles']),1)
    def test_literal_manifest_is_data_only(self):
        self.assertEqual(literal_manifest(b'rock_manifest = { lua = { ["a.lua"] = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" } }'), {'lua': {'a.lua': 'a'*32}})
        for bad in (b'rock_manifest = os.execute("id")', b'rock_manifest = { lua = require("x") }', b'rock_manifest = { a = "x", a = "y" }'):
            with self.assertRaises((ValueError, IndexError)): literal_manifest(bad)
    def test_ownership_resolves_usr_merge_links(self):
        doc = {'artifacts': [{'id':'libc','name':'libc','type':'deb','locations':[], 'metadata':{'files':[{'path':'/lib/libc.so'}]}}]}
        rows = {'lib':{'link':'usr/lib'},'usr/lib/libc.so':{'elf':True,'sha256':'a'*64}}
        r = ownership(doc, rows)
        self.assertEqual(r['unresolvedElfFiles'], [])
        self.assertEqual(r['identifiedElfFiles'][0]['packageIds'], ['libc'])
    def test_unknown_native_file_is_not_silently_accepted(self):
        r = ownership({'artifacts':[]}, {'tmp/unowned.so':{'elf':True,'sha256':'a'*64}})
        self.assertEqual(len(r['unresolvedElfFiles']), 1)
    def test_rock_versions_bind_different_deployed_bytes_without_removing_catalog_entries(self):
        doc = {'artifacts': [{'id':str(n), 'name':'example', 'version':str(n), 'type':'lua-rocks',
                              'locations':[{'path':f'/usr/local/apisix/deps/lib/luarocks/rocks-5.1/example/{n}/example.rockspec'}]} for n in (1,2)]}
        rows = {}
        for n in (1,2):
            md5 = str(n)*32; base=f'usr/local/apisix/deps/lib/luarocks/rocks-5.1/example/{n}/rock_manifest'
            rows[base] = {'raw': ('rock_manifest = { lib = { ["example.so"] = "'+md5+'" } }').encode(), 'sha256':str(n)*64}
            rows[f'usr/local/apisix/deps/lib/lua/5.1/example{n}.so'] = {'md5':md5,'sha256':str(n)*64}
        r = rock_bindings(doc, rows)
        self.assertEqual(r['unboundRockManifestFiles'], [])
        self.assertEqual([p['version'] for p in doc['artifacts']], ['1','2'])
        self.assertEqual(len(doc['artifacts'][0]['locations']),2)
    def test_missing_rock_implementation_remains_explicit(self):
        doc={'artifacts':[{'id':'x','name':'example','version':'1','type':'lua-rocks','locations':[{'path':'/usr/local/apisix/deps/lib/luarocks/rocks-5.1/example/1/example.rockspec'}]}]}
        rows={'usr/local/apisix/deps/lib/luarocks/rocks-5.1/example/1/rock_manifest':{'raw':b'rock_manifest = { lib = { ["example.so"] = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" } }','sha256':'b'*64}}
        self.assertEqual(len(rock_bindings(doc,rows)['unboundRockManifestFiles']),1)
    def test_overlay_whiteout_removes_old_native_payload(self):
        def layer(files):
            out=io.BytesIO()
            with tarfile.open(fileobj=out,mode='w') as tar:
                for path, raw in files:
                    item=tarfile.TarInfo(path);item.size=len(raw);tar.addfile(item,io.BytesIO(raw))
            return out.getvalue()
        config=b'{}'; manifest=json.dumps([{'Config':'config.json','Layers':['one.tar','two.tar']}]).encode()
        out=io.BytesIO()
        with tarfile.open(fileobj=out,mode='w') as tar:
            for path,raw in [('config.json',config),('manifest.json',manifest),('one.tar',layer([('tmp/old.so',b'\x7fELFold')])),('two.tar',layer([('tmp/.wh.old.so',b''),('tmp/new.so',b'\x7fELFnew')]))]:
                item=tarfile.TarInfo(path);item.size=len(raw);tar.addfile(item,io.BytesIO(raw))
        raw=out.getvalue();rows,config_hash=image_files(io.BytesIO(raw),hashlib.sha256(raw).hexdigest(),len(raw))
        self.assertNotIn('tmp/old.so',rows);self.assertTrue(rows['tmp/new.so']['elf'])
    def test_wrong_archive_hash_rejected_before_inventory(self):
        with self.assertRaises(ValueError): image_files(io.BytesIO(b'untrusted'),'a'*64,9)

if __name__ == '__main__': unittest.main()
