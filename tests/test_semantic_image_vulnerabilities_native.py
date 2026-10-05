"""Real Syft, real saved images and a real isolated network namespace.

Owned package fixtures only, no container creation/start, mandatory root CI.
"""
import hashlib,json,os,subprocess,sys,tempfile,unittest,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import prepare_semantic_image_sbom as m
from tools import verify_semantic_image_archive as archive
from tools import review_semantic_image_vulnerabilities as g
class NativeVulnerability(unittest.TestCase):
    def test_real_offline_scanner_binds_both_images_and_never_creates_container(self):
        self.assertEqual(os.geteuid(),0)
        docker=Path('/usr/bin/docker');scanner=Path(os.environ['OUF_SBOM_SCANNER']);unshare=Path('/usr/bin/unshare')
        token=uuid.uuid4().hex;tags=[]
        def run(*args):
            p=subprocess.run([str(docker),*map(str,args)],capture_output=True,timeout=60)
            self.assertEqual(p.returncode,0,'OWNED_SBOM_FIXTURE_SETUP_FAILED');return p.stdout.decode().strip()
        before=run('ps','--all','--quiet')
        with tempfile.TemporaryDirectory(dir='/root') as dirname:
            root=Path(dirname);root.chmod(0o700);images=[]
            try:
                for i,role in enumerate(('adapter','southbound')):
                    context=root/role;context.mkdir(mode=0o700)
                    (context/'status').write_text('Package: ci-owned-'+role+'\nStatus: install ok installed\nArchitecture: amd64\nVersion: 1.'+str(i)+'\nMaintainer: CI <ci@example.invalid>\nDescription: Owned CI package fixture\n\n')
                    (context/'Dockerfile').write_text('FROM scratch\nCOPY status /var/lib/dpkg/status\nCOPY METADATA /usr/local/lib/python3.12/site-packages/Django-2.2.0.dist-info/METADATA\nCMD ["ci-never-start"]\n')
                    (context/'METADATA').write_text('Metadata-Version: 2.1\nName: Django\nVersion: 2.2.0\n')
                    tag='ouf-ci-sbom-'+role+'-'+token;tags.append(tag);run('build','--network=none','--pull=false','--tag',tag,context)
                    image=run('image','inspect','--format','{{.Id}}',tag);probe=root/(role+'-probe.tar')
                    with probe.open('wb') as out:
                        p=subprocess.run([str(docker),'image','save',image],stdout=out,stderr=subprocess.DEVNULL,timeout=60)
                        self.assertEqual(p.returncode,0)
                    with probe.open('rb') as stream:v=archive.archive_verify(stream,image,archive.Budget())
                    images.append({'role':role,'imageId':image,**{k:v[k] for k in ('configByteSha256','rootfsDescriptorsHash')}})
                output=root/'prepared';output.mkdir(mode=0o700)
                env={'PATH':'/usr/bin:/bin','OUF_SBOM_SCANNER':str(scanner)}
                args=['/usr/bin/python3','-I','-B',str(Path(__file__).resolve().parents[1]/'tools/semantic_image_sbom_preparer.py'),
                    '--root',str(output),'--images',json.dumps(images)]
                for name,path in (('docker',docker),('scanner',scanner),('unshare',unshare)):
                    args.extend(['--'+name,str(path),'--'+name+'-hash',hashlib.sha256(path.read_bytes()).hexdigest()])
                p=subprocess.run(args,capture_output=True,timeout=420,env=env)
                self.assertEqual(p.returncode,0,'NATIVE_ISOLATED_SBOM_PREPARATION_FAILED')
                self.assertNotIn(b'ci-owned',p.stdout);self.assertNotIn(str(root).encode(),p.stdout)
                receipt=json.loads((output/'receipt.json').read_bytes())
                self.assertEqual(len(receipt['images']),2)
                self.assertTrue(all(r['packageCount']>0 and r['sbomImageIdentityBound'] for r in receipt['images']))
                self.assertFalse(receipt['acceptanceGranted']);self.assertFalse(receipt['startAuthorized'])
                self.assertEqual(receipt['containerOperations'],0)
                for role in ('adapter','southbound'):
                    self.assertEqual((output/(role+'.spdx.json')).stat().st_mode&0o777,0o600)
                reviewed=root/'reviewed';reviewed.mkdir(mode=0o700)
                scanner_root=Path('/root/ouf-ci-vulnerability')
                pin=json.loads((scanner_root/'database-pin.json').read_bytes())
                review_args=['/usr/bin/python3','-I','-B',str(Path(__file__).resolve().parents[1]/'tools/semantic_image_vulnerability_reviewer.py'),
                    '--root',str(reviewed),'--source-root',str(output),'--expected',json.dumps(receipt['images']),
                    '--receipt-hash',hashlib.sha256((output/'receipt.json').read_bytes()).hexdigest(),
                    '--database-pin',json.dumps(pin),'--db-archive',str(scanner_root/'database.tar.zst')]
                for name,path in (('scanner',scanner_root/'grype'),('unshare',unshare)):
                    review_args.extend(['--'+name,str(path),'--'+name+'-hash',hashlib.sha256(path.read_bytes()).hexdigest()])
                scanned=subprocess.run(review_args,capture_output=True,timeout=600,env={'PATH':'/usr/bin:/bin'})
                if scanned.returncode:
                    # CI-owned fixture diagnostics only, never VPS inputs.
                    for f in reviewed.glob('*.grype.json'):
                        report=json.loads(f.read_bytes())
                        print('NATIVE_MODEL_DIAGNOSTIC='+json.dumps({'sourceType':report.get('source',{}).get('type'),'sourceTargetKeys':list(report.get('source',{}).get('target',{})),'db':report.get('descriptor',{}).get('db')}))
                self.assertEqual(scanned.returncode,0,'REAL_OFFLINE_GRYPE_REVIEW_FAILED')
                facts=json.loads((reviewed/'receipt.json').read_bytes())
                self.assertFalse(facts['allScannerSeverityThresholdsMet'])
                self.assertTrue(all(r['severityCounts']['High']+r['severityCounts']['Critical']>0 for r in facts['images']))
                self.assertFalse(facts['acceptanceGranted']);self.assertFalse(facts['startAuthorized'])
                self.assertNotIn(b'Django',scanned.stdout);self.assertNotIn(str(root).encode(),scanned.stdout)
                self.assertEqual(run('ps','--all','--quiet'),before)
                print('SEMANTIC_IMAGE_VULNERABILITY_NATIVE=PASS REAL_SCANNER=true REAL_DATABASE=true KNOWN_HIGH_DETECTED=true NETWORK_ISOLATED=true NO_APPLICATION_STARTED=true CI_ONLY=true')
            finally:
                for tag in tags:run('image','rm',tag)
if __name__=='__main__':unittest.main()
