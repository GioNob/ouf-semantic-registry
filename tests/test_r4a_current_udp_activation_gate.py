from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import r4a_current_udp_activation_gate as gate


class GateTests(unittest.TestCase):
    def test_exact_current_gate_and_invalid_scope_fields(self):
        policy = {"tenantId": "tenant", "canonicalClass": "class", "ref": "policy", "version": "1"}
        current = {"valid": True, "sourceId": "source", "configurationHash": "hash",
                   "tenantId": "tenant", "canonicalClass": "class", "policyRef": "policy",
                   "policyVersion": "1", "coverageRef": "coverage://current"}
        self.assertTrue(all(gate.gate_facts(current, policy, "source", "hash").values()))
        for key, value in (("valid", False), ("sourceId", "other"), ("configurationHash", "other"),
                           ("tenantId", "other"), ("canonicalClass", "other"), ("policyRef", "other"),
                           ("policyVersion", "2"), ("coverageRef", "other://current")):
            with self.subTest(key=key):
                self.assertFalse(all(gate.gate_facts({**current, key: value}, policy, "source", "hash").values()))

    def test_absent_gate_is_not_valid(self):
        self.assertFalse(all(gate.gate_facts({}, {"tenantId": "tenant", "canonicalClass": "class", "ref": "policy", "version": "1"}, "source", "hash").values()))


if __name__ == "__main__":
    unittest.main()
