"""Root CI-only offline archive/SBOM/report proof on already tested owned images."""
import argparse,hashlib,json,os,subprocess,sys,tarfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import verify_semantic_image_archive as archive
from tools import prepare_semantic_image_sbom as sbom
from tools import review_semantic_image_vulnerabilities as grype

def main():
    assert os.geteuid()==0;os.umask(0o077)
    p=argparse.ArgumentParser();p.add_argument('--adapter',required=True);p.add_argument('--southbound',required=True);a=p.parse_args()
    base=Path('/root/ouf-ci-image-remediation');base.mkdir(mode=0o700)
    scanner_root=Path('/root/ouf-ci-vulnerability')
    syft=scanner_root/'syft';grype_bin=scanner_root/'grype';db=scanner_root/'database.tar.zst'
    pin=sbom.decode((scanner_root/'database-pin.json').read_bytes());grype.database_pin(pin)
    docker=Path('/usr/bin/docker');unshare=Path('/usr/bin/unshare')
    tool_hashes={p:archive.command_snapshot(p) for p in (docker,unshare)}
    for scanner in (syft,grype_bin):
        h=hashlib.sha256(scanner.read_bytes()).hexdigest()
        sbom.executable(scanner,h)
        tool_hashes[scanner]=h
    print('CI_SCAN_STAGE=ARCHIVE_BINDING',file=sys.stderr)
    rows=[];bindings=[]
    for role,image in (('adapter',a.adapter),('southbound',a.southbound)):
        path=base/(role+'.probe.tar')
        with path.open('xb') as out:
            subprocess.run([str(docker),'image','save',image],stdout=out,stderr=subprocess.DEVNULL,check=True,timeout=120)
        print('CI_ARCHIVE_ROLE='+role,file=sys.stderr)
        try:
            with path.open('rb') as stream:
                verified=archive.archive_verify(stream,image,archive.Budget(180,8589934592,100000))
        except Exception:
            with tarfile.open(path,'r') as diagnostic:
                manifest=json.load(diagnostic.extractfile('manifest.json'));assert len(manifest)==1
                config=json.load(diagnostic.extractfile(manifest[0]['Config']))
                layers=manifest[0]['Layers'];diffs=config['rootfs']['diff_ids']
                # CI-owned public image; structure counts only, never target data.
                print('CI_PUBLIC_ARCHIVE_STRUCTURE='+json.dumps({'role':role,'layerReferences':len(layers),'uniqueLayerReferences':len(set(layers)),'diffIds':len(diffs),'uniqueDiffIds':len(set(diffs)),'repeatedLayerPositions':[i for i,name in enumerate(layers) if name in layers[:i]]}),file=sys.stderr)
            raise
        bindings.append({'role':role,**verified})
        rows.append({'role':role,**{k:verified[k] for k in ('imageId','configByteSha256','rootfsDescriptorsHash')}})
    prepared=base/'sbom';prepared.mkdir(mode=0o700)
    print('CI_SCAN_STAGE=SBOM_PREPARATION',file=sys.stderr)
    result=sbom.prepare(prepared,rows,docker,tool_hashes[docker],syft,tool_hashes[syft],unshare,tool_hashes[unshare])
    expected=result['images'];receipt_hash=hashlib.sha256((prepared/'receipt.json').read_bytes()).hexdigest()
    reviewed=base/'review';reviewed.mkdir(mode=0o700)
    print('CI_SCAN_STAGE=VULNERABILITY_REVIEW',file=sys.stderr)
    result=grype.review(reviewed,prepared,expected,receipt_hash,pin,db,grype_bin,tool_hashes[grype_bin],unshare,tool_hashes[unshare])
    result['schema']='ouf.semantic-image-remediation-experiment.v1'
    result['imageArchivesVerified']=True
    result['imageArchiveBindings']=bindings
    result['scannerCountersScope']='offline vulnerability reviewer only; CI build and compatibility containers run separately'
    result['sbomPackageCounts']={row['role']:row['packageCount'] for row in expected}
    result['sbomPackageWithoutVersionCounts']={row['role']:row['packageWithoutVersionCount'] for row in expected}
    result['fullReceiptSha256']=hashlib.sha256((reviewed/'receipt.json').read_bytes()).hexdigest()
    result['remainingHighCriticalUnknown']={}
    for row in expected:
        role=row['role'];report=json.loads((reviewed/(role+'.grype.json')).read_bytes())
        remaining=[]
        for match in report['matches']:
            v=match['vulnerability']
            if v['severity'] not in ('High','Critical','Unknown'):continue
            artifact=match['artifact']
            remaining.append({k:artifact.get(k) for k in ('name','version','type')} | {
                'id':v['id'],'severity':v['severity'],'namespace':v.get('namespace'),'fix':v.get('fix'),
                'matchers':[d.get('matcher') for d in match.get('matchDetails',[])]})
        result['remainingHighCriticalUnknown'][role]=remaining
    result['experimentOnly']=True
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
