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
        result=script.inventory(run);encoded=json.dumps(result)
        for secret in ('secret-value','private-address','/private/host/path'):self.assertNotIn(secret,encoded)
        self.assertFalse(result['dedicatedSouthboundContainerObserved'])
        self.assertFalse(result['egressDefaultDenyProven']);self.assertFalse(result['tlsConfigurationProven'])
        self.assertTrue(all(c[0] in ('ps','inspect','network') for c in calls))
    def test_named_dedicated_gateway_is_observed_without_claiming_tls_or_auth(self):
        rows=[row(n) for n in ('ouf-semantic','ouf-apisix','ouf-caddy','ouf-etcd','ouf-apisix-southbound')]
        run,_=self.runner(rows);result=script.inventory(run)
        self.assertTrue(result['dedicatedSouthboundContainerObserved']);self.assertFalse(result['workloadAuthenticationProven'])
    def test_changed_runtime_is_rejected(self):
        run,_=self.runner([row(n) for n in ('ouf-semantic','ouf-apisix','ouf-caddy','ouf-etcd')],True)
        with self.assertRaisesRegex(RuntimeError,'TOPOLOGY_CHANGED'):script.inventory(run)
    def test_missing_required_owner_is_rejected(self):
        run,_=self.runner([row('ouf-apisix')])
        with self.assertRaisesRegex(RuntimeError,'REQUIRED_CONTAINER_MISSING'):script.inventory(run)

if __name__=='__main__':unittest.main()
