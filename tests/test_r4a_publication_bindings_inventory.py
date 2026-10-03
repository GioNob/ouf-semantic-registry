import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import r4a_publication_bindings_inventory as subject


class Bindings(unittest.TestCase):
    def test_nested_relaxed_tenant_names(self):
        source = {'ouf': {'runtimePublications': {'tenantId': 'ouf-lab'}}, 'unrelated': {'tenantId': 'private'}}
        self.assertEqual(subject.tenant_values(subject.flatten(source)), ['ouf-lab'])

    def test_multiple_aliases_are_visible_as_ambiguous(self):
        source = {'ouf.runtime-publications.tenant-id': 'ouf-lab', 'ouf.runtimePublications.tenantId': 'different'}
        self.assertEqual(len(subject.tenant_values(subject.flatten(source))), 2)

    def test_wrapped_policy_objects_are_inspected_without_values_printed(self):
        policy = {'bundle': {'capabilities': [{'capabilityId': subject.CAP, 'riskClass': 'READ'}],
                             'grants': [{'capabilityId': subject.CAP, 'effect': 'ALLOW', 'actorTypes': ['SERVICE']}]}}
        matches = [x for x in subject.objects(policy) if x.get('capabilityId') == subject.CAP]
        self.assertEqual(len(matches), 2)


if __name__ == '__main__':
    unittest.main()
