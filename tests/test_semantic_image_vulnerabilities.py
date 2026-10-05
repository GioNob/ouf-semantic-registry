import datetime,hashlib,json,os,sys,tempfile,time,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import review_semantic_image_vulnerabilities as m
from tools.build_semantic_image_vulnerability_reviewer import build
class Review(unittest.TestCase):
    def setUp(self):
        self.pin={'status':'active','schemaVersion':'6.0.0','built':'2026-10-05T12:00:00Z','path':'vulnerability-db_v6.0.0_2026-10-05T12:00:00Z_1.tar.zst','checksum':'sha256:'+'a'*64}
        self.expected={'role':'adapter','imageId':'sha256:'+'b'*64,'configByteSha256':'c'*64,'syftJsonSha256':'d'*64}
        self.report={'matches':[],'source':{'type':'image','target':{'imageID':'sha256:'+'c'*64}},'descriptor':{'name':'grype','version':m.GRYPE_VERSION,'db':{'schemaVersion':'6.0.0','built':self.pin['built']}}}
    def scan(self):return m.summary(m.canonical(self.report),self.expected,self.pin)
    def test_clean_scan_never_grants_acceptance(self):
        r=self.scan();self.assertTrue(r['scannerSeverityThresholdMet']);self.assertFalse(r['acceptanceGranted']);self.assertFalse(r['dependencyCoverageAccepted'])
    def test_high_and_unknown_findings_block_threshold_without_metadata_disclosure(self):
        for severity in ('High','Critical','Unknown'):
            self.report['matches']=[{'artifact':{'name':'PRIVATE_PACKAGE'},'vulnerability':{'id':'CVE-2026-12345','severity':severity}}]
            r=self.scan();self.assertFalse(r['scannerSeverityThresholdMet']);self.assertNotIn('PRIVATE_PACKAGE',json.dumps(r));self.assertFalse(r['startAuthorized'])
    def test_ignored_mismatched_database_and_foreign_image_denied(self):
        changes=[('ignoredMatches',[{}]),('source',{'type':'image','target':{'imageID':'sha256:'+'e'*64}}),('descriptor',{'name':'grype','version':'old','db':{}})]
        for key,value in changes:
            old=self.report.get(key);self.report[key]=value
            with self.assertRaises(Exception):self.scan()
            if old is None:self.report.pop(key)
            else:self.report[key]=old
    def test_stale_future_wrong_schema_database_denied(self):
        now=datetime.datetime.fromisoformat(self.pin['built'].replace('Z','+00:00')).timestamp()
        self.assertEqual(m.database_pin(self.pin,now+3600),self.pin)
        for moment in (now-1,now+172801):
            with self.assertRaises(Exception):m.database_pin(self.pin,moment)
        self.pin['path']='../unbound.tar.zst'
        with self.assertRaises(Exception):m.database_pin(self.pin,now)
    def test_duplicate_json_denied(self):
        with self.assertRaises(Exception):m.summary(b'{"matches":[],"matches":[]}',self.expected,self.pin)
    def test_generated_closure_exact(self):
        root=Path(__file__).resolve().parents[1]/'tools'
        self.assertEqual(build(root),(root/'semantic_image_vulnerability_reviewer.py').read_text())
    def test_private_database_bytes_mode_and_links_are_checked(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('OUF_TEST_ROOT',str(Path.cwd().parent))) as directory:
            root=Path(directory);root.chmod(0o700);p=root/'database';p.write_bytes(b'owned database bytes');p.chmod(0o600)
            expected=hashlib.sha256(p.read_bytes()).hexdigest();m.hash_file(p,expected,1024)
            p.chmod(0o644)
            with self.assertRaises(Exception):m.hash_file(p,expected,1024)
            p.chmod(0o600);p.write_bytes(b'changed')
            with self.assertRaises(Exception):m.hash_file(p,expected,1024)
            link=root/'link';link.symlink_to(p)
            with self.assertRaises(Exception):m.hash_file(link,expected,1024)
if __name__=='__main__':unittest.main()
