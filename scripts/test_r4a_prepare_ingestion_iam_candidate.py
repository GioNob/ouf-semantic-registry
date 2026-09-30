import unittest
from r4a_prepare_ingestion_iam_candidate import content_for


class CandidatePropertiesTests(unittest.TestCase):
    original = b'# preserved\nouf.ingestion.activation.enabled=true\nouf.ingestion.execution.enabled=true\ncustom.setting=keep\n'
    env = {'SPRING_CONFIG_ADDITIONAL_LOCATION':'optional:file:/run/secrets/ingestion-summary.properties'}

    def test_preserves_all_existing_bytes_and_enables_iam(self):
        result = content_for(self.original, self.env, 'https://auth.example/realms/ouf', 'ouf-api-gateway')
        self.assertTrue(result.startswith(self.original))
        self.assertIn(b'ouf.ingestion.iam.enabled=true\n', result)
        self.assertIn(b'ouf.ingestion.iam.issuer=https://auth.example/realms/ouf\n', result)
        self.assertIn(b'ouf.ingestion.iam.audience=ouf-api-gateway\n', result)

    def test_rejects_conflicting_config_and_properties(self):
        cases = [
            (self.original, {**self.env,'SPRING_CONFIG_IMPORT':'file:/other'}),
            (self.original, {**self.env,'SPRING_APPLICATION_JSON':'{}'}),
            (self.original, {**self.env,'OUF_ING_IAM_ENABLED':'false'}),
            (self.original+b'ouf.ingestion.iam.enabled=false\n', self.env),
            (self.original+b'spring.config.import=file:/other\n', self.env),
            (self.original+b'custom.setting=second\n', self.env),
            (self.original+b'escaped\\ key=value\n', self.env),
            (self.original.replace(b'execution.enabled=true',b'execution.enabled=false'), self.env),
        ]
        for original, env in cases:
            with self.subTest(original=original, env=env), self.assertRaises(RuntimeError):
                content_for(original, env, 'https://auth.example/realms/ouf', 'ouf-api-gateway')


if __name__ == '__main__':
    unittest.main()
