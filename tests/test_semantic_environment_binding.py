import copy,os,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import verify_semantic_environment_binding as m
from test_semantic_creation_configuration import fixture
from test_semantic_creation_configuration_docker import embedded as creation_embedded
ROOT=Path(__file__).resolve().parents[1]
SECRET=b'CI_ONLY_VALIDATOR_SECRET_0123456789';MAC=b'a'*64
def env_bytes():return b'OUF_VALIDATOR='+SECRET+b'\nOUF_RECEIPT_MAC='+MAC+b'\n'
def public_receipts():
    binding={'routes':{'audience':'ci-validator','oidcSecretRef':'$ENV://OUF_VALIDATOR','receiptKeyEnvironment':'OUF_RECEIPT_MAC'}}
    trust={'artifactHashes':{role+'/provider-receipt.key':m.sha(MAC) for role in ('adapter','southbound')}}
    raw={'binding':m.encoded(binding),'trust':m.encoded(trust),'secret':SECRET,'env':env_bytes()}
    intent={'schema':'ouf.semantic-southbound-validator-credential.v1','purpose':'OIDC_BEARER_TOKEN_VALIDATOR_ONLY',
        'uid':636,'gid':636,'trustReceiptHash':m.sha(raw['trust']),'tlsReceiptHash':'f'*64,
        'clientProfile':{'clientId':'ci-validator'},'providerCalls':0,'clientCredentialsGrantRequested':False,
        'iamConfigurationChanged':False,'secretRotated':False,'notReleaseAcceptance':True}
    raw['credential']=m.encoded({'intent':intent,'credentialHash':m.sha(SECRET)})
    raw['launch']=m.encoded({'schema':'ouf.semantic-provider-launch-inputs.v1','notReleaseAcceptance':True,
        'containersCreated':0,'mountsInstalled':False,'providerCalls':0,'bindingHash':m.sha(raw['binding']),
        'trustReceiptHash':m.sha(raw['trust']),'credentialReceiptHash':m.sha(raw['credential']),
        'environmentHash':m.sha(raw['env']),'environmentNames':['OUF_VALIDATOR','OUF_RECEIPT_MAC'],'tlsReceiptHash':'f'*64})
    return raw
def embedded():
    helper=creation_embedded().split("if __name__=='__main__':")[0]
    source=(ROOT/'tools/verify_semantic_environment_binding.py').read_text()
    return source.replace('from tools.read_semantic_creation_configuration import Query,collect,environment,require,Blocked,private,decode,sha,encoded,attrs',helper)
def materialize(root,manifest_raw,creation_raw):
    raw=public_receipts();raw.update(manifest=manifest_raw,creation=creation_raw)
    names={'launch':'launch-input-receipt.json','credential':'credential-receipt.json','trust':'trust-receipt.json',
        'binding':'binding.json','env':'southbound.env','secret':'client-secret'}
    for k,name in names.items():
        p=root/name;p.write_bytes(raw[k]);p.chmod(0o600)
        if k=='secret':os.chown(p,636,636)
    return raw
class Tests(unittest.TestCase):
    def test_exact_oidc_mac_names_and_purpose_receipt_pairing(self):
        raw=public_receipts();value=m.pairing(raw,m.sha(raw['launch']),636,636)
        self.assertEqual(value,{'OUF_VALIDATOR':SECRET.decode(),'OUF_RECEIPT_MAC':MAC.decode()})
    def test_wrong_secret_mac_extra_line_and_invalid_byte_names_deny(self):
        for field,value in [('secret',b'CI_OTHER_SECRET_00000'),('env',env_bytes()+b'EXTRA=secret\n'),
            ('env',env_bytes().replace(MAC,b'b'*64)),('env',env_bytes().replace(b'OUF_VALIDATOR',b'LD_PRELOAD'))]:
            raw=public_receipts();raw[field]=value
            with self.subTest(field=field),self.assertRaises(Exception):m.pairing(raw,m.sha(raw['launch']),636,636)
    def test_resealed_env_and_credential_hash_still_need_exact_semantic_pairing(self):
        raw=public_receipts();raw['env']=env_bytes().replace(MAC,b'b'*64)
        launch=m.decode(raw['launch']);launch['environmentHash']=m.sha(raw['env']);raw['launch']=m.encoded(launch)
        with self.assertRaises(m.Blocked):m.pairing(raw,m.sha(raw['launch']),636,636)
        raw=public_receipts();credential=m.decode(raw['credential']);credential['intent']['clientCredentialsGrantRequested']=True
        raw['credential']=m.encoded(credential);launch=m.decode(raw['launch']);launch['credentialReceiptHash']=m.sha(raw['credential']);raw['launch']=m.encoded(launch)
        with self.assertRaises(m.Blocked):m.pairing(raw,m.sha(raw['launch']),636,636)
    def test_adapter_cannot_receive_provider_secrets_and_current_env_is_exact(self):
        manifest,journal,data=fixture();raw=public_receipts();manifest['installation']='ci'
        envpath='/fixed/southbound.env';manifest['containers'][1]['envFile']=envpath
        data['container','2'*64]['Config']['Env']+=['OUF_VALIDATOR='+SECRET.decode(),'OUF_RECEIPT_MAC='+MAC.decode()]
        raw['manifest']=m.encoded(manifest);journal['manifestHash']=m.sha(raw['manifest'])
        for row in data.values():
            if 'State' in row:row['Config']['Labels']['ouf.semantic.candidate.manifest']=journal['manifestHash']
        raw['creation']=m.encoded(journal);pins={'manifest':m.sha(raw['manifest']),'creation':m.sha(raw['creation']),
            'launch':m.sha(raw['launch']),'envPath':envpath}
        from tools.read_semantic_creation_configuration import review
        def query(k,i):return copy.deepcopy(data[k,i])
        rows,_=review(manifest,journal,query);expected={r['role']:r for r in rows}
        result=m.verify(raw,pins,'ci',636,636,query,expected);out=m.encoded(result)
        self.assertTrue(result['containerEnvironmentMatchesSealedLaunch']);self.assertFalse(result['acceptanceGranted'])
        for value in (SECRET,MAC,envpath.encode()):self.assertNotIn(value,out)
        data['container','1'*64]['Config']['Env'].append('OUF_VALIDATOR='+SECRET.decode())
        with self.assertRaises(m.Blocked):m.verify(raw,pins,'ci',636,636,query,expected)
    def test_private_secret_owner_mode_link_limits_and_no_value_in_error(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('OUF_TEST_ROOT',str(ROOT.parent))) as d:
            root=Path(d);root.chmod(0o700);p=root/'secret';p.write_bytes(SECRET);p.chmod(0o600)
            self.assertEqual(m.role_secret(p,0,0),SECRET)
            with self.assertRaises(m.Blocked):m.role_secret(p,636,636)
            p.chmod(0o644)
            with self.assertRaises(m.Blocked) as ctx:m.role_secret(p,0,0)
            self.assertNotIn(SECRET.decode(),str(ctx.exception));p.chmod(0o600);link=root/'link';link.symlink_to(p)
            with self.assertRaises(OSError):m.role_secret(link,0,0)
            link.unlink();os.link(p,link)
            with self.assertRaises(m.Blocked):m.role_secret(p,0,0)
if __name__=='__main__':unittest.main()
