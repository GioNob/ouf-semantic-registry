import unittest

from scripts import r4a_prepare_onboarding_candidate as candidate


class CandidateReuseTest(unittest.TestCase):
    def test_only_exact_stopped_candidate_is_reusable(self):
        expected_mounts = [("bind", "/run/ouf-onboarding-identity",
                            "/run/ouf-onboarding-identity", False)]
        record = {"image_id": "sha256:staged"}
        environment = ["OUF_ONB_UDP_IDENTITY_TOKEN_FILE=/run/ouf-onboarding-identity/token"]
        descriptor = {
            "Image": "sha256:staged", "State": {"Running": False},
            "Config": {"User": "10003:10003", "Env": environment},
            "HostConfig": {"NetworkMode": "ouf-backend",
                           "RestartPolicy": {"Name": "unless-stopped"},
                           "LogConfig": {"Type": "json-file"}},
            "Mounts": [{"Type": "bind", "Source": "/run/ouf-onboarding-identity",
                        "Destination": "/run/ouf-onboarding-identity", "RW": False}],
        }
        self.assertTrue(candidate.candidate_matches(descriptor, record,
                                                       expected_mounts, environment))
        descriptor["State"]["Running"] = True
        self.assertFalse(candidate.candidate_matches(descriptor, record,
                                                        expected_mounts, environment))
        descriptor["State"]["Running"] = False
        descriptor["Mounts"][0]["RW"] = True
        self.assertFalse(candidate.candidate_matches(descriptor, record,
                                                        expected_mounts, environment))


if __name__ == "__main__":
    unittest.main()
