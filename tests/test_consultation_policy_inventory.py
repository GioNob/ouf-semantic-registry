import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import r4a_semantic_consultation_policy_inventory as inventory


class InventoryTests(unittest.TestCase):
    def test_authorization_database_comes_from_onboarding_binding(self):
        pg={'Name':'/installation-pg','NetworkSettings':{'Networks':{'net':{'Aliases':['pg-service']}}}}
        row={'State':{'Running':True},'Config':{'Env':['OUF_ONB_DB_URL=jdbc:postgresql://pg-service:5432/onboarding_registry']}}
        args=SimpleNamespace(postgres_container='installation-pg',onboarding_container='installation-onboarding')
        with patch.object(inventory.release.stage,'inspect',return_value=row) as inspect:
            self.assertEqual(inventory.database(args,pg),'onboarding_registry')
        inspect.assert_called_once_with('installation-onboarding')
    def test_wrong_database_host_is_rejected(self):
        pg={'Name':'/pg','NetworkSettings':{'Networks':{}}}
        row={'State':{'Running':True},'Config':{'Env':['OUF_ONB_DB_URL=jdbc:postgresql://foreign:5432/registry']}}
        with patch.object(inventory.release.stage,'inspect',return_value=row):
            with self.assertRaisesRegex(RuntimeError,'AUTHORIZATION_DATABASE_BINDING_INVALID'):
                inventory.database(SimpleNamespace(postgres_container='pg',onboarding_container='owner'),pg)
    def test_inventory_sql_is_read_only_and_does_not_project_grants(self):
        self.assertTrue(inventory.SQL.strip().startswith('begin read only;'))
        self.assertTrue(inventory.SQL.strip().endswith('commit;'))
        self.assertNotIn("->'grants'",inventory.SQL)
        self.assertNotIn('update ',inventory.SQL.lower())
        self.assertNotIn('insert ',inventory.SQL.lower())


if __name__=='__main__':unittest.main()
