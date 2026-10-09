import json
import unittest
from scripts import r4a_read_semantic_national_discovery_configuration as reader

class NationalDiscoveryConfigurationTests(unittest.TestCase):
    def runtime(self,env=()):
        return {"State":{"Running":True},"Config":{"Env":list(env),
            "Entrypoint":["java","-XX:MaxRAMPercentage=75","-jar","/app/application.jar"],
            "Cmd":None,"WorkingDir":"/app"},"Mounts":[]}

    def test_measured_defaults_keep_provider_disabled_and_worker_enabled(self):
        report=reader.summary(self.runtime(),reader.DEFAULTS_SHA,False)
        self.assertIs(report["providerEnabled"],False)
        self.assertIs(report["workerEnabled"],True)
        self.assertFalse(report["gatewayOriginConfigured"])

    def test_flags_require_exact_packaged_configuration_and_no_overrides(self):
        row=self.runtime(["OUF_SCHEMA_GOV_ENABLED=true"])
        self.assertIs(reader.summary(row,reader.DEFAULTS_SHA,False)["providerEnabled"],True)
        for sha,external,count in (("0"*64,False,0),(reader.DEFAULTS_SHA,True,0),(reader.DEFAULTS_SHA,False,1)):
            self.assertEqual(reader.summary(row,sha,external,count)["providerEnabled"],"UNPROVEN")

    def test_lowercase_spring_override_is_detected_without_values(self):
        report=reader.summary(self.runtime(['spring.application.json={"private":"do-not-print"}']),
                              reader.DEFAULTS_SHA,False)
        self.assertEqual(report["providerEnabled"],"UNPROVEN")
        self.assertNotIn("do-not-print",json.dumps(report))

    def test_unexpected_mount_or_startup_arguments_prevent_proof(self):
        row=self.runtime();row["Mounts"]=[{"Destination":"/app/config"}]
        self.assertEqual(reader.summary(row,reader.DEFAULTS_SHA,False)["providerEnabled"],"UNPROVEN")
        row=self.runtime();row["Config"]["Cmd"]=["--spring.config.location=/private"]
        self.assertEqual(reader.summary(row,reader.DEFAULTS_SHA,False)["providerEnabled"],"UNPROVEN")

    def test_endpoint_credentials_are_rejected_and_not_serialized(self):
        report=reader.summary(self.runtime(["OUF_SCHEMA_GOV_GATEWAY_BASE_URL=https://user:private-value@example.org/private"]),
                              reader.DEFAULTS_SHA,False)
        self.assertFalse(report["gatewayOriginConfigured"])
        self.assertNotIn("private-value",json.dumps(report))
        self.assertNotIn("example.org",json.dumps(report))

if __name__=="__main__":unittest.main()
