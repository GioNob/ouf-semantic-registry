import unittest
from datetime import datetime, timezone
import r4a_publication_access_inventory as inventory


class FlatPolicyTests(unittest.TestCase):
    def test_match_requires_principal_subject_tenant_and_validity(self):
        now = datetime(2026, 9, 30, tzinfo=timezone.utc)
        grant = dict(capabilityId=inventory.CAP, grantId='g', servicePrincipalId='svc',
                     subjectId='sub', tenantId='ouf-lab', validFrom='2026-09-01T00:00:00Z', validUntil='2026-10-01T00:00:00Z')
        claims = dict(sub='sub', client_id='svc', ouf_actor_type='SERVICE', tenant_id='ouf-lab')
        counts = inventory.policy_counts({'bundle': [grant]}, claims, now)
        self.assertEqual(counts['CURRENT_VALIDITY_DIAGNOSTIC_MATCH_COUNT'], 1)
        for field, value in [('subjectId', 'other'), ('tenantId', 'other'),
                             ('validUntil', '2026-09-30T00:00:00Z'), ('validFrom', 'invalid')]:
            changed = dict(grant, **{field: value})
            self.assertEqual(inventory.policy_counts([changed], claims, now)['CURRENT_VALIDITY_DIAGNOSTIC_MATCH_COUNT'], 0)

    def test_owner_claim_precedence_and_subject_only_grant(self):
        grant = dict(capabilityId=inventory.CAP, grantId='g', servicePrincipalId='svc',
                     subjectId='canonical', tenantId='ouf-lab', validFrom='2026-09-01T00:00:00Z', validUntil='2026-10-01T00:00:00Z')
        claims = dict(sub='raw', ouf_subject='canonical', client_id='svc', azp='other',
                      ouf_actor_type='SERVICE', tenant_id='ouf-lab')
        now = datetime(2026, 9, 30, tzinfo=timezone.utc)
        self.assertEqual(inventory.policy_counts([grant], claims, now)['CURRENT_VALIDITY_DIAGNOSTIC_MATCH_COUNT'], 1)
        claims['client_id'] = 'other'
        claims['service_principal_id'] = 'svc'
        self.assertEqual(inventory.policy_counts([grant], claims, now)['SERVICE_PRINCIPAL_CLAIM_DIAGNOSTIC_MATCH_COUNT'], 0)
        grant['servicePrincipalId'] = None
        self.assertEqual(inventory.policy_counts([grant], claims, now)['SUBJECT_ONLY_GRANT_COUNT'], 1)

    def test_descriptor_is_separate_from_flat_grant(self):
        descriptor = dict(capabilityId=inventory.CAP, allowedActors=['SERVICE'], requiredScope=inventory.CAP)
        counts = inventory.policy_counts([descriptor], {}, datetime.now(timezone.utc))
        self.assertEqual(counts['FLAT_DESCRIPTOR_SERVICE_SCOPE_COUNT'], 1)
        self.assertEqual(counts['FLAT_GRANT_COUNT'], 0)


if __name__ == '__main__':
    unittest.main()
