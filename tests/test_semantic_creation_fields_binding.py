import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import verify_semantic_creation_fields as m
from tools.read_semantic_creation_configuration import review
from test_semantic_creation_configuration import fixture as old_fixture
from test_semantic_creation_fields import fixture as field_fixture
from test_semantic_environment_binding import public_receipts,SECRET,MAC,embedded as env_embedded
ROOT=Path(__file__).resolve().parents[1]

def embedded():
    env=env_embedded().split("if __name__=='__main__':")[0]
    source=(ROOT/'tools/verify_semantic_creation_fields.py').read_text()
    policy=(ROOT/'tools/review_semantic_creation_fields.py').read_text()
    return source.replace('from tools.verify_semantic_environment_binding import Query,verify,pairing,role_secret,require,private,decode,sha,encoded',env).replace('from tools.review_semantic_creation_fields import review_fields',policy)

def inputs():
    manifest,journal,data=old_fixture();raw=public_receipts();manifest['installation']='ci'
    prototype=field_fixture();base=copy.deepcopy(prototype[2]);base['Env']=['BASE=CI_PRIVATE_VALUE'];base['Volumes']=None
    base['User']='1:1';data['image','sha256:'+'a'*64].update(Config=base,Os='linux',Architecture='amd64')
    for i,spec in enumerate(manifest['containers']):
        cid=str(i+1)*64;spec['networks']=copy.deepcopy(prototype[3]['networks'])
        spec['mounts']=copy.deepcopy(prototype[3]['mounts'])
        cfg=copy.deepcopy(prototype[0]);host=copy.deepcopy(prototype[1])
        cfg.update(Hostname=cid[:12],User=spec['user'],Env=list(base['Env']))
        host.update(ReadonlyRootfs=spec['readOnlyRoot'],Memory=spec['memoryBytes'],MemorySwap=spec['memoryBytes'],PidsLimit=spec['pidsLimit'])
        if i:
            spec['envFile']='/fixed/southbound.env';cfg['Env']+=['OUF_VALIDATOR='+SECRET.decode(),'OUF_RECEIPT_MAC='+MAC.decode()]
        row=data['container',cid];row.update(Config=cfg,HostConfig=host)
        row['Mounts']=[{'Source':v['source'],'Destination':v['target'],'RW':False,'Type':'bind','Propagation':'rprivate'} for v in spec['mounts']]
    raw['manifest']=m.encoded(manifest);journal['manifestHash']=m.sha(raw['manifest']);raw['creation']=m.encoded(journal)
    for key,row in data.items():
        if key[0]=='container':row['Config']['Labels']={**base['Labels'],'ouf.semantic.candidate.transaction':journal['transaction'],
                                                      'ouf.semantic.candidate.manifest':journal['manifestHash']}
    query=lambda k,i:copy.deepcopy(data[k,i]);rows,_=review(manifest,journal,query)
    return raw,{'manifest':m.sha(raw['manifest']),'creation':m.sha(raw['creation']),'launch':m.sha(raw['launch']),
                'envPath':'/fixed/southbound.env'},data,{r['role']:r for r in rows}

class Binding(unittest.TestCase):
    def test_complete_fields_after_exact_historical_and_current_env_binding(self):
        raw,pins,data,expected=inputs();calls=[]
        def query(k,i):calls.append((k,i));return copy.deepcopy(data[k,i])
        result=m.verify_all(raw,pins,'ci',636,636,query,expected,{k:m.sha(v) for k,v in raw.items()})
        self.assertTrue(result['declaredRequestConforms']);self.assertEqual(len(calls),8)
        self.assertTrue(result['environmentBindingsUnchangedSinceSection46']);self.assertFalse(result['acceptanceGranted'])
        for private in (SECRET,MAC,b'CI_PRIVATE_VALUE',b'/CI_PRIVATE_SOURCE'):
            self.assertNotIn(private,m.encoded(result))

    def test_wrong_section46_pin_denies_before_docker(self):
        raw,pins,data,expected=inputs();hashes={k:m.sha(v) for k,v in raw.items()};hashes['env']='f'*64
        def query(*args):self.fail('No Docker query allowed after receipt drift')
        with self.assertRaises(Exception):m.verify_all(raw,pins,'ci',636,636,query,expected,hashes)

    def test_matching_hashes_cannot_approve_unknown_host_field(self):
        raw,pins,data,expected=inputs();data['container','1'*64]['HostConfig']['CI_PRIVATE_NEW_NAME']='CI_PRIVATE_NEW_VALUE'
        manifest,journal=m.decode(raw['manifest']),m.decode(raw['creation']);query=lambda k,i:copy.deepcopy(data[k,i])
        rows,_=review(manifest,journal,query);expected={r['role']:r for r in rows}
        result=m.verify_all(raw,pins,'ci',636,636,query,expected,{k:m.sha(v) for k,v in raw.items()})
        self.assertFalse(result['declaredRequestConforms']);self.assertFalse(result['acceptanceGranted'])
        self.assertNotIn(b'CI_PRIVATE_NEW',m.encoded(result))

    def test_wrong_architecture_denies_after_bound_configuration(self):
        raw,pins,data,expected=inputs();data['image','sha256:'+'a'*64]['Architecture']='arm64'
        manifest,journal=m.decode(raw['manifest']),m.decode(raw['creation']);query=lambda k,i:copy.deepcopy(data[k,i])
        rows,_=review(manifest,journal,query);expected={r['role']:r for r in rows}
        with self.assertRaises(Exception):m.verify_all(raw,pins,'ci',636,636,query,expected,{k:m.sha(v) for k,v in raw.items()})

if __name__=='__main__':unittest.main()
