import io
import json
import tarfile
import unittest
from tools.audit_semantic_native_coverage import native_files, sha, supplement, ROOT


def tar(items):
    result = io.BytesIO()
    with tarfile.open(fileobj=result, mode='w') as archive:
        for path, data in items:
            info = tarfile.TarInfo(path)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return result.getvalue()


class NativeCoverageTests(unittest.TestCase):
    def test_layer_whiteout_and_same_layer_replacement(self):
        config = b'{}'
        layers = [tar([(ROOT + 'zlib/old', b'old'), (ROOT + 'zlib/keep', b'keep')]),
                  tar([(ROOT + 'zlib/.wh..wh..opq', b''), (ROOT + 'zlib/new', b'new')])]
        manifest = json.dumps([{'Config': 'config.json', 'Layers': ['a.tar', 'b.tar']}]).encode()
        image = tar([('config.json', config), ('manifest.json', manifest),
                     ('a.tar', layers[0]), ('b.tar', layers[1])])
        rows, identity = native_files(io.BytesIO(image), sha(image), len(image))
        self.assertEqual(set(rows), {ROOT + 'zlib/new'})
        self.assertEqual(identity, sha(config))

    def test_wrong_archive_bytes_rejected(self):
        with self.assertRaises(ValueError):
            native_files(io.BytesIO(b'wrong'), '0' * 64, 5)

    def test_supplement_keeps_packages_and_unresolved_identities(self):
        rows = {
            ROOT + 'wasmtime-c-api/lib/libwasmtime.so': {'sha256': 'a' * 64, 'elf': True, 'bytes': 4},
            ROOT + 'pcre/lib/libpcre.so.1.2.13': {'sha256': 'b' * 64, 'elf': True, 'bytes': 4, 'raw': b'8.45 2021-06-15\x00'},
            ROOT + 'pcre/include/pcre.h': {'raw': b'#define PCRE_MAJOR 8\n#define PCRE_MINOR 45\n'},
            ROOT + 'openssl3/lib/libssl.so.3': {'sha256': 'c' * 64, 'elf': True, 'bytes': 4},
            ROOT + 'zlib/lib/libz.so.1.3.2.1-motley': {'sha256': 'd' * 64, 'elf': True, 'bytes': 4},
            ROOT + 'luajit/lib/libluajit.so': {'sha256': 'e' * 64, 'elf': True, 'bytes': 4},
        }
        original = {'artifacts': [{'id': 'original', 'name': 'apisix', 'version': '3.18.0'}],
                    'artifactRelationships': [{'parent': 'original', 'child': 'file', 'type': 'contains'}]}
        sbom, audit = supplement(original, rows, 'a' * 64)
        self.assertEqual(sbom['artifacts'][0], original['artifacts'][0])
        self.assertEqual(sbom['artifactRelationships'], original['artifactRelationships'])
        self.assertEqual(len(original['artifacts']), 1)
        self.assertEqual(len(audit['unresolvedNativeIdentities']), 1)
        self.assertFalse(audit['dependencyCoverageAccepted'])
        with self.assertRaises(ValueError):
            supplement(original, rows, '0' * 64)


if __name__ == '__main__':
    unittest.main()
