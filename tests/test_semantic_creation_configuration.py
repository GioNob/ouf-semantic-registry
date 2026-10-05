import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import read_semantic_creation_configuration as m
def fixture():
    specs=[];ids={};data={};image='sha256:'+'a'*64
    base={'User':'1:1','Entrypoint':['/app'],'Cmd':None,'WorkingDir':'/','Env':['BASE=private_fixture'],'Volumes':None}
    data['image',image]={'Id':image,'Config':base}
    for i in range(2):
        name='ci'+str(i);cid=str(i+1)*64;ids[name]=cid
        spec={'name':name,'image':image,'user':'1:1','command':[],'envFile':None,'readOnlyRoot':i==0,
            'memoryBytes':123,'pidsLimit':32,'dnsServers':[],'mounts':[{'source':'/fixture','target':'/proof','readOnly':True}]};specs.append(spec)
        cfg={**copy.deepcopy(base),'Healthcheck':{'Test':['NONE']},'Labels':{'ouf.semantic.candidate.transaction':'b'*32,'ouf.semantic.candidate.manifest':'c'*64}}
        data['container',cid]={'Id':cid,'Image':image,'Name':'/'+name,'RestartCount':0,'Config':cfg,
            'State':{'Status':'created','Running':False,'Restarting':False,'Pid':0,'StartedAt':'0001-01-01T00:00:00Z'},
            'HostConfig':{'Privileged':False,'ReadonlyRootfs':i==0,'RestartPolicy':{'Name':'no'},'CapDrop':['ALL'],
                'Memory':123,'MemorySwap':123,'PidsLimit':32,'Dns':[]},
            'Mounts':[{'Source':'/fixture','Destination':'/proof','RW':False,'Type':'bind','Propagation':'rprivate'}]}
    return {'schema':'ouf.semantic-provider-stopped-manifest.v1','startAuthorized':False,'containers':specs},\
        {'schema':'ouf.semantic-provider-stopped-create.v1','state':'CREATED_STOPPED','startAuthorized':False,'candidateIds':ids,'transaction':'b'*32,'manifestHash':'c'*64},data
class Tests(unittest.TestCase):
    def test_complete_hashes_are_redacted_and_not_acceptance(self):
        manifest,journal,data=fixture();rows,_=m.review(manifest,journal,lambda k,i:copy.deepcopy(data[k,i]))
        raw=m.encoded(rows);self.assertNotIn(b'private_fixture',raw);self.assertNotIn(b'/fixture',raw)
        self.assertTrue(all(not r['allConfigurationFieldsSemanticallyAccepted'] for r in rows))
        original=rows[0]['hostConfigHash'];data['container','1'*64]['HostConfig']['FutureField']='private_future'
        rows,_=m.review(manifest,journal,lambda k,i:copy.deepcopy(data[k,i]));self.assertNotEqual(rows[0]['hostConfigHash'],original)
    def test_actual_identity_ownership_startup_and_host_restrictions_drift(self):
        for path,value in [('Id','f'*64),('State.Pid',2),('State.Running',True),('HostConfig.Privileged',True),
            ('HostConfig.CapDrop',[]),('Config.User','0:0'),('Config.Cmd',['evil']),('HostConfig.MemorySwap',999),
            ('Config.Labels.ouf.semantic.candidate.transaction','wrong')]:
            manifest,journal,data=fixture();row=data['container','1'*64]
            # Label key deliberately includes dots.
            if path.startswith('Config.Labels.'):row['Config']['Labels'][path[14:]]=value
            else:
                parts=path.split('.');target=row
                for part in parts[:-1]:target=target[part]
                target[parts[-1]]=value
            with self.subTest(path=path),self.assertRaises(m.Blocked):m.review(manifest,journal,lambda k,i:data[k,i])
    def test_mount_missing_extra_rw_and_environment_override_denied(self):
        for kind in ('missing','extra','rw','env','duplicate'):
            manifest,journal,data=fixture();row=data['container','1'*64]
            if kind=='missing':row['Mounts']=[]
            elif kind=='extra':row['Mounts'].append(copy.deepcopy(row['Mounts'][0]))
            elif kind=='rw':row['Mounts'][0]['RW']=True
            elif kind=='env':row['Config']['Env']=['BASE=changed']
            else:row['Config']['Env']*=2
            with self.subTest(kind=kind),self.assertRaises(m.Blocked):m.review(manifest,journal,lambda k,i:data[k,i])
    def test_full_object_drift_between_passes_and_private_receipt_pins(self):
        manifest,journal,data=fixture();manifest['installation']='ci';raw0=m.encoded(manifest);journal['manifestHash']=m.sha(raw0)
        for row in data.values():
            if 'State' in row:row['Config']['Labels']['ouf.semantic.candidate.manifest']=journal['manifestHash']
        raw=[raw0,m.encoded(journal)];pins=list(map(m.sha,raw));calls=[]
        def query(k,i):
            calls.append((k,i));row=copy.deepcopy(data[k,i])
            if len(calls)>4:row['Unreviewed']='PRIVATE_DRIFT'
            return row
        with self.assertRaises(m.Blocked):m.collect(raw,pins,'ci',query)
        with self.assertRaises(m.Blocked):m.collect(raw,['f'*64,pins[1]],'ci',query)
    def test_duplicates_nan_and_query_identifiers_fail_before_docker(self):
        for raw in (b'{"x":1,"x":2}',b'{"x":NaN}'):
            with self.assertRaises(Exception):m.decode(raw)
        q=object.__new__(m.Query)
        for kind,value in [('container','name'),('network','a'*64),('container','--help')]:
            with self.assertRaises(m.Blocked):q(kind,value)
if __name__=='__main__':unittest.main()
