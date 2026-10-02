import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import r4a_semantic_discovery_preflight as script


def runtime(values=(),commands=()):
    return {'Config':{'Env':list(values),'Entrypoint':['java','-jar','/app/application.jar'], 'Cmd':list(commands)},
        'Mounts':[{'Destination':'/run/ouf-semantic-auth'},{'Destination':'/run/secrets/semantic-read-owner.key'}]}


class PreflightTest(unittest.TestCase):
    def test_pinned_defaults_are_not_mistaken_for_external_provider_enabled(self):
        cfg,paths=script.settings(runtime())
        self.assertEqual(cfg['providerEnabled'],False);self.assertEqual(cfg['workerEnabled'],True)
        self.assertFalse(cfg['gatewayOriginConfigured']);self.assertTrue(cfg['configurationProven'])
        self.assertEqual(paths['search'],'/semantic-providers/schema-gov/sparql')
    def test_never_outputs_endpoint_or_credentials(self):
        cfg,_=script.settings(runtime(['OUF_SCHEMA_GOV_ENABLED=true',
            'OUF_SCHEMA_GOV_GATEWAY_BASE_URL=https://user:secret@example.org/private',
            'SOME_PASSWORD=secret']))
        self.assertFalse(cfg['gatewayOriginSafe'])
        self.assertNotIn('secret',json.dumps(cfg));self.assertNotIn('example.org',json.dumps(cfg))
    def test_ambiguous_config_override_prevents_effective_config_claim(self):
        for row in [runtime(['SPRING_APPLICATION_JSON={"password":"secret"}']),
            runtime(commands=['--ouf.semantic.providers.schema-gov.enabled=true']),
            runtime(['JAVA_TOOL_OPTIONS=-Dpassword=secret'])]:
            cfg,_=script.settings(row)
            self.assertFalse(cfg['configurationProven']);self.assertEqual(cfg['providerEnabled'],'UNPROVEN')
            self.assertNotIn('secret',json.dumps(cfg))
    def test_relaxed_property_override_takes_precedence_and_invalid_boolean_is_unproven(self):
        cfg,_=script.settings(runtime(['OUF_SCHEMA_GOV_ENABLED=false','OUF_SEMANTIC_PROVIDERS_SCHEMA_GOV_ENABLED=true']))
        self.assertTrue(cfg['providerEnabled'])
        cfg,_=script.settings(runtime(['OUF_SCHEMA_GOV_ENABLED=secret']))
        self.assertEqual(cfg['providerEnabled'],'UNPROVEN');self.assertNotIn('secret',json.dumps(cfg))
    def test_only_active_routes_with_correct_http_method_count(self):
        routes=[{'uri':'/search','methods':['GET']},{'uri':'/search','methods':['POST'],'status':0},
            {'uri':'/search','methods':['POST'],'upstream_id':'u','plugins':{'openid-connect':{'secret':'never-output'}}},
            {'uri':'/fetch','methods':['GET'],'upstream':{'nodes':{'private-host':1}}}]
        summary=script.route_summary(routes,{'search':'/search','fetch':'/fetch'})
        self.assertEqual(summary['search']['activeRouteCount'],1)
        self.assertEqual(summary['search']['oidcEnforcedRouteCount'],1)
        self.assertTrue(summary['fetch']['upstreamBindingPresent'])
        self.assertNotIn('secret',json.dumps(summary));self.assertNotIn('private-host',json.dumps(summary))
    def test_queue_and_policy_queries_are_explicit_read_only_and_do_not_select_payloads(self):
        for sql in (script.QUEUE_SQL,script.POLICY_SQL):
            self.assertTrue(sql.strip().startswith('begin read only;'))
            for word in ('insert ','update ','delete ','intent','content_bytes','normalized_payload'):
                self.assertNotIn(word,sql.lower())
        with patch.object(script.stage,'run',return_value='{}') as call:
            self.assertEqual(script.query('pg','user','db',script.QUEUE_SQL),{})
            self.assertEqual(call.call_args.args[0][:3],['docker','exec','pg'])
    def test_invalid_origin_port_or_external_plain_http_is_not_configuration_ready(self):
        for value in ['https://example.org:invalid','http://example.org','https://example.org:0']:
            cfg,_=script.settings(runtime(['OUF_SCHEMA_GOV_GATEWAY_BASE_URL='+value]))
            self.assertFalse(cfg['gatewayOriginConfigured'])
        cfg,_=script.settings(runtime(['OUF_SCHEMA_GOV_GATEWAY_BASE_URL=http://127.0.0.1:9080']))
        self.assertTrue(cfg['gatewayOriginConfigured'])

if __name__=='__main__':unittest.main()
