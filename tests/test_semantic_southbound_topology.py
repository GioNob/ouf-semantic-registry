import copy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import r4a_semantic_southbound_topology as script


def row(name):
    return {'Id':name,'Name':'/'+name,'Image':'sha256:pinned',
        'Config':{'Image':'apisix' if name=='ouf-apisix' else 'runtime','Env':['PASSWORD=secret-value'],'User':'10001','Labels':{}},
        'State':{'Running':True,'StartedAt':'fixed'},'HostConfig':{'PortBindings':{'9443/tcp':[{'HostIp':'private-address','HostPort':'9443'}]}},
        'Mounts':[{'Destination':'/run/certificate','Source':'/private/host/path','RW':False,'Type':'bind'}],
        'NetworkSettings':{'Networks':{'ouf-backend':{'IPAddress':'private-address'}}}}


class TopologyTest(unittest.TestCase):
    roles={'semantic':'ouf-semantic','gateway':'ouf-apisix','proxy':'ouf-caddy','gatewayState':'ouf-etcd'}
    def runner(self,rows,changed=False):
        calls=[]
        def run(*args):
            calls.append(args)
            if args[0]=='ps':return '\n'.join(r['Id'] for r in rows)
            if args[:2]==('network','inspect'):return json.dumps([{'Name':'ouf-backend','Driver':'bridge','Internal':False,'IPAM':{'secret':'secret-value'}}])
            result=copy.deepcopy(rows)
            if changed and sum(c[0]=='inspect' for c in calls)>1:result[0]['State']['StartedAt']='new'
            return json.dumps(result)
        return run,calls
    def test_redacts_values_addresses_and_host_paths_and_only_uses_read_commands(self):
        run,calls=self.runner([row(n) for n in ('ouf-semantic','ouf-apisix','ouf-caddy','ouf-etcd')])
        result=script.inventory(self.roles,run);encoded=json.dumps(result)
        for secret in ('secret-value','private-address','/private/host/path'):self.assertNotIn(secret,encoded)
        self.assertFalse(result['dedicatedSouthboundContainerObserved'])
        self.assertFalse(result['egressDefaultDenyProven']);self.assertFalse(result['tlsConfigurationProven'])
        self.assertTrue(all(c[0] in ('ps','inspect','network') for c in calls))
    def test_named_dedicated_gateway_is_observed_without_claiming_tls_or_auth(self):
        rows=[row(n) for n in ('ouf-semantic','ouf-apisix','ouf-caddy','ouf-etcd','ouf-apisix-southbound')]
        run,_=self.runner(rows);result=script.inventory(self.roles | {'southbound':'ouf-apisix-southbound'},run)
        self.assertTrue(result['dedicatedSouthboundContainerObserved']);self.assertFalse(result['workloadAuthenticationProven'])
    def test_changed_runtime_is_rejected(self):
        run,_=self.runner([row(n) for n in ('ouf-semantic','ouf-apisix','ouf-caddy','ouf-etcd')],True)
        with self.assertRaisesRegex(RuntimeError,'TOPOLOGY_CHANGED'):script.inventory(self.roles,run)
    def test_missing_required_owner_is_rejected(self):
        run,_=self.runner([row('ouf-apisix')])
        with self.assertRaisesRegex(RuntimeError,'REQUIRED_CONTAINER_MISSING'):script.inventory(self.roles,run)
    def test_arbitrary_installation_names_and_networks_need_no_lab_defaults(self):
        roles={'semantic':'registry-west','gateway':'edge-private'}
        rows=[row(n) for n in roles.values()]
        for r in rows:r['NetworkSettings']['Networks']={'custom-install-network':{}}
        run,_=self.runner(rows)
        result=script.inventory(roles,run)
        self.assertEqual(result['roleBindings'],roles)
        self.assertTrue(all(r['networks']==['custom-install-network'] for r in result['containers']))
        self.assertNotIn('ouf-',json.dumps(result['containers']))
    def test_role_bindings_are_explicit_and_distinct(self):
        for roles in ({'semantic':'one'}, {'semantic':'one','gateway':'one'}, {'semantic':'one','gateway':'invalid/name'}):
            with self.assertRaises(RuntimeError):script.inventory(roles,lambda *args:self.fail('Docker read before binding validation'))

if __name__=='__main__':unittest.main()
