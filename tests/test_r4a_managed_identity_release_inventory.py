import contextlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import r4a_managed_identity_release_inventory as inventory


class ManagedIdentityReleaseInventoryTests(unittest.TestCase):
    def test_flyway_checksum_ignores_bom_and_line_endings_but_preserves_spaces(self):
        text = " select 'é';  "
        value = zlib.crc32(text.encode())
        expected = value if value < 2**31 else value - 2**32
        self.assertEqual(inventory.checksum("\ufeff select 'é';  \r\n"), expected)
        self.assertEqual(inventory.checksum(" select 'é';  \n"), expected)
        self.assertNotEqual(inventory.checksum(text.strip()), expected)

    def test_migrations_fail_on_missing_pending_changed_failed_and_duplicate_versions(self):
        candidate = {"1": ("V1__schema.sql", 123)}
        valid = {"version": "1", "script": "V1__schema.sql", "checksum": 123, "success": True, "type": "SQL"}
        self.assertTrue(inventory.compare_migrations(candidate, [valid]))
        for rows in ([], [valid, valid], [{**valid, "checksum": 124}], [{**valid, "success": False}],
                     [{**valid, "script": "V1__other.sql"}], [valid, {**valid, "version": "2"}]):
            self.assertFalse(inventory.compare_migrations(candidate, rows))

    def test_host_mount_mapping_rejects_symlink_escape_and_writable_mount(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            mounted = root / "mounted"
            mounted.mkdir()
            (root / "outside").write_text("private-test-key")
            (mounted / "token").symlink_to(root / "outside")
            doc = {"Mounts": [{"Type": "bind", "RW": False, "Source": str(mounted),
                              "Destination": "/run/auth"}]}
            self.assertIsNone(inventory.host_file(doc, "/run/auth/token"))
            self.assertEqual(inventory.host_file(doc, "/run/auth/new-token"), mounted / "new-token")
            doc["Mounts"][0]["RW"] = True
            self.assertIsNone(inventory.host_file(doc, "/run/auth/new-token"))

    def test_main_uses_only_inspect_git_reads_and_read_only_sql_without_values(self):
        migration = " select 1;  \n"
        installed = [{"version": "1", "script": "V1__schema.sql", "checksum": inventory.checksum(migration),
                      "success": True, "type": "SQL"}]
        owner = {"Image": "private-image-id", "State": {"Running": True}, "Config": {"Env": [
            "OUF_ONB_DB_URL=jdbc:postgresql://private-host:5432/ouf_onboarding",
            "OUF_ONB_DB_USER=ouf_onboarding", "OUF_ONB_DB_PASSWORD=private-password"]}}
        image = {"Config": {"Labels": {"org.opencontainers.image.revision": inventory.BASELINE}}}
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(inventory.os, "geteuid", return_value=0), \
             patch.object(inventory, "inspect", side_effect=[owner, image]), \
             patch.object(inventory, "binding_facts", return_value={"OWNER_STAGING_ENV_PRESENT": True}), \
             patch.object(inventory, "run", side_effect=["", "", inventory.MIGRATIONS + "V1__schema.sql\n", migration,
                                                         json.dumps(installed)]) as run, \
             contextlib.redirect_stdout(output):
            inventory.main(SimpleNamespace(repo=Path(folder), revision="a" * 40))
        text = output.getvalue()
        self.assertIn("OWNER_RELEASE_MIGRATIONS_MATCH_DATABASE=true", text)
        self.assertIn("RELEASE_PREREQUISITES=PASS", text)
        for value in ("private-password", "private-host", "private-image-id", migration):
            self.assertNotIn(value, text)
        sql = run.call_args_list[-1].args[0][-1]
        self.assertTrue(sql.startswith("begin read only;"))
        self.assertTrue(sql.endswith("rollback;"))
        for call in run.call_args_list[:-1]:
            self.assertIn(call.args[0][5], ("merge-base", "ls-tree", "show"))


if __name__ == "__main__":
    unittest.main()
