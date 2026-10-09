import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import observe_semantic_mount_view as m
from tools.review_semantic_oci_policy import Denied

class Parser(unittest.TestCase):
    def test_mount_only_ro_flag_is_not_filesystem_superblock_rw(self):
        raw=b'10 9 8:1 /rootfs / rw,relatime - ext4 /dev/sda1 rw\n11 10 8:1 /fixture/proof /proof ro,relatime - ext4 /dev/sda1 rw\n'
        rows=m.mountinfo(raw);self.assertIn('ro',rows[1]['options']);self.assertIn('rw',rows[1]['superOptions'])

    def test_kernel_escapes_are_decoded_without_shell_or_path_expansion(self):
        rows=m.mountinfo(b'11 10 8:1 /source\\040name /target\\134name ro - ext4 /dev/sda1 rw\n')
        self.assertEqual(rows[0]['root'],'/source name');self.assertEqual(rows[0]['target'],'/target\\name')
        with self.assertRaises(Denied):m.mountinfo(b'11 10 8:1 /bad\\077name /target ro - ext4 /dev/sda1 rw\n')

    def test_duplicate_ids_missing_separator_bad_devices_unknown_optional_and_bounds_denied(self):
        valid=b'11 10 8:1 /source /target ro - ext4 /dev/sda1 rw\n'
        for raw in (valid+valid,valid.replace(b' - ',b' '),valid.replace(b'8:1',b'8:1:0'),
                    valid.replace(b'ro -',b'ro unknown:1 -'),b'x'*131073,b'',valid+b'\x00'):
            with self.subTest(rawlen=len(raw)),self.assertRaises((Denied,UnicodeError)):m.mountinfo(raw)

    def test_generation_and_budget_invalid_inputs_fail_before_proc_io(self):
        for pid in (True,0,1,-1,2**31):
            with self.subTest(pid=pid),self.assertRaises(Denied):m.generation(pid,m.Budget())
        for seconds in (True,0,6):
            with self.subTest(seconds=seconds),self.assertRaises(Denied):m.Budget(seconds)

if __name__=='__main__':unittest.main()
