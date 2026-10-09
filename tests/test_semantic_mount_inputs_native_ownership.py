"""Mandatory native UID checks on root CI; no skip or mocked ownership."""
import os
from pathlib import Path
import tempfile
import unittest
from test_semantic_mount_inputs import m

class NativeOwnership(unittest.TestCase):
    def test_actual_nonroot_role_ownership_matches_fixed_vps_uids(self):
        self.assertEqual(os.geteuid(),0)
        with tempfile.TemporaryDirectory(dir=os.environ['OUF_TEST_ROOT']) as d:
            root=Path(d);root.chmod(0o700)
            for uid in (10006,636):
                p=root/str(uid);p.write_bytes(b'fixture');p.chmod(0o600);os.chown(p,uid,uid)
                raw,_=m.read(p,uid,uid,0o600,65536,m.Budget())
                self.assertEqual(raw,b'fixture')
                with self.assertRaises(m.Blocked):m.read(p,0,0,0o600,65536,m.Budget())

if __name__=='__main__':unittest.main()
