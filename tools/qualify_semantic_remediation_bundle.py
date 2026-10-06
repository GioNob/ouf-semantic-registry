"""Stage and byte-verify a pinned CI bundle; no image import, signing or execution."""
import argparse,gzip,hashlib,json,os,re,stat,sys,zipfile
from pathlib import Path
from tools import verify_semantic_image_archive as archive
from tools import prepare_semantic_image_sbom as sbom
from tools import review_semantic_image_vulnerabilities as grype

def require(value):
    if not value:raise ValueError('REMEDIATION_BUNDLE_UNPROVEN')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def file_hash(stream):
    stream.seek(0);h=hashlib.sha256();size=0
    while part:=stream.read(1024*1024):
        size+=len(part);require(size<=2147483648);h.update(part)
    stream.seek(0);return h.hexdigest(),size
def inventory(bundle):
    items=bundle.infolist();require(1<=len(items)<=2048)
    names={};total=0
    for item in items:
        name=item.filename
        require(type(name) is str and len(name)<=1024 and '\x00' not in name and '\\' not in name)
        path=Path(name);require(not path.is_absolute() and '..' not in path.parts and name not in names)
        require(not item.flag_bits&1 and not stat.S_ISLNK(item.external_attr>>16))
        total+=item.file_size;require(0<=item.file_size<=1073741824 and total<=2147483648)
        names[name]=item
    return names
def small(bundle,names,name):
    require(name in names and 0<names[name].file_size<=67108864)
    raw=bundle.read(name);require(len(raw)==names[name].file_size);return raw
def write(root,name,raw):
    path=root/name
    path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as out:out.write(raw);out.flush();os.fsync(out.fileno())
def qualify(source,root,expected_hash,expected_commit):
    require(re.fullmatch('[0-9a-f]{64}',expected_hash) and re.fullmatch('[0-9a-f]{40}',expected_commit))
    require(file_hash(source)[0]==expected_hash)
    with zipfile.ZipFile(source) as bundle:
        names=inventory(bundle)
        receipt=sbom.decode(small(bundle,names,'receipt.json'))
        require(receipt['schema']=='ouf.semantic-image-remediation-experiment.v1'
            and receipt['candidate']=='alpine-ubuntu-source-fixed' and receipt['semanticBuildCommit']==expected_commit
            and receipt['allScannerSeverityThresholdsMet'] is True and receipt['compatibilityProven'] is True
            and receipt['acceptanceGranted'] is False and receipt['runtimeRegistered'] is False and receipt['startAuthorized'] is False)
        require(receipt['inputs']['zlibSource']['commit']=='df84af25dc1942490e1d1c899a07619152a46148')
        require(receipt['inputs']['zlibSource']['releaseStatus']=='unreleased upstream')
        source_receipt_raw=small(bundle,names,'sbom/receipt.json');source_receipt=sbom.decode(source_receipt_raw)
        require(sha(source_receipt_raw)==receipt['sourceReceiptSha256'])
        require(source_receipt['schema']=='ouf.semantic-private-image-sbom-preparation.v1')
        original_review=small(bundle,names,'review/receipt.json')
        require(sha(original_review)==receipt['fullReceiptSha256'])
        original_review=sbom.decode(original_review)
        require(original_review['allScannerSeverityThresholdsMet'] is True and original_review['images']==receipt['images'])
        expected=source_receipt['images'];require(len(expected)==2 and {r['role'] for r in expected}=={'adapter','southbound'})
        pin={'built':receipt['images'][0]['databaseBuilt'],'checksum':'sha256:'+receipt['images'][0]['databaseArchiveSha256'],
            'schemaVersion':receipt['images'][0]['databaseSchemaVersion'],'status':'active',
            'path':'vulnerability-db_v6.1.10_2026-10-05T00:36:45Z_1791182738.tar.zst'}
        grype.database_pin(pin)
        proven=[]
        for row in expected:
            role=row['role'];fact=[r for r in receipt['images'] if r['role']==role];require(len(fact)==1)
            syft=small(bundle,names,'sbom/'+role+'.syft.json');spdx=small(bundle,names,'sbom/'+role+'.spdx.json')
            require(sha(syft)==row['syftJsonSha256'] and sha(spdx)==row['spdxJsonSha256'])
            summary=sbom.summarize(syft,spdx,row)
            require(summary['packageCount']==row['packageCount'] and summary['packageWithoutVersionCount']==0)
            report=small(bundle,names,'review/'+role+'.grype.json')
            require(grype.summary(report,row,pin)==fact[0] and fact[0]['scannerSeverityThresholdMet'] is True)
            records=[r for r in receipt['candidateArchives'] if r['role']==role];require(len(records)==1)
            record=records[0];name=role+'.image.tar.gz'
            require(record['file']==name and record['kind']=='docker-save-tar-gzip' and name in names
                and record['imageId']==row['imageId'] and names[name].file_size==record['bytes'])
            path=root/name
            fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);h=hashlib.sha256();count=0
            with os.fdopen(fd,'wb') as out,bundle.open(name) as incoming:
                while part:=incoming.read(1024*1024):
                    count+=len(part);require(count<=1073741824);h.update(part);out.write(part)
                out.flush();os.fsync(out.fileno())
            require(count==record['bytes'] and h.hexdigest()==record['sha256'])
            with gzip.open(path,'rb') as uncompressed:
                binding=archive.archive_verify(uncompressed,row['imageId'],archive.Budget())
            require(binding['archiveSha256']==record['uncompressedSha256'] and binding['archiveBytes']==record['uncompressedBytes']
                and binding['archiveSha256']==row['archiveSha256'] and binding['archiveBytes']==row['archiveBytes']
                and binding['configByteSha256']==row['configByteSha256'] and binding['rootfsDescriptorsHash']==row['rootfsDescriptorsHash'])
            for filename,raw in ((role+'.syft.json',syft),(role+'.spdx.json',spdx),(role+'.grype.json',report)):
                write(root,'reports/'+filename,raw)
            proven.append({'role':role,'imageId':row['imageId'],'archiveSha256':record['sha256'],'severityCounts':fact[0]['severityCounts'],'bytesVerified':True})
        # These are retained evidence, never treated as root-authority approval.
        keep=['receipt.json','checksums.sha256','compatibility.json','zlib-source-files.json','openssl-source-lock.json',
            'bundled-openssl-runtime-proof.txt','sbom/receipt.json','review/receipt.json',
            'attestations/provenance.json','attestations/adapter-sbom.json','attestations/southbound-sbom.json',
            'attestations/adapter-verification.json','attestations/southbound-verification.json',
            'attestations/adapter-sbom-verification.json','attestations/southbound-sbom-verification.json']
        for name in keep:write(root,'evidence/'+name,small(bundle,names,name))
    require(file_hash(source)[0]==expected_hash)
    result={'schema':'ouf.semantic-remediation-bundle-byte-qualification.v1','images':proven,
        'sourceArtifactSha256':expected_hash,'ciSourceCommit':expected_commit,'ciAttestationEvidenceRetained':True,
        'targetAttestationCryptoVerified':False,'publisherTrustAccepted':False,'dependencyCoverageAccepted':False,
        'scannerInvoked':False,'containerOperations':0,'imageImportPerformed':False,
        'acceptanceGranted':False,'runtimeRegistered':False,'startAuthorized':False}
    return result
def main():
    try:
        require(os.geteuid()==os.getegid()==0 and sys.flags.isolated and sys.dont_write_bytecode);os.umask(0o077)
        p=argparse.ArgumentParser()
        p.add_argument('--bundle',type=Path,required=True);p.add_argument('--root',type=Path,required=True)
        p.add_argument('--sha256',required=True);p.add_argument('--ci-commit',required=True);a=p.parse_args()
        require(str(a.root) in ('/etc/ouf/deploy-snapshots/semantic-image-remediation-20261006-v1','/root/ouf-ci-remediation-qualification'))
        for parent in a.root.parents:
            s=parent.lstat();require(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and not s.st_mode&0o022)
        fd=os.open(a.bundle,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(fd,'rb') as incoming:
            before=os.fstat(incoming.fileno());require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<before.st_size<=2147483648)
            # Hash before creating any target output; wrong input creates no snapshot.
            require(file_hash(incoming)[0]==a.sha256);a.root.mkdir(mode=0o700)
            result=qualify(incoming,a.root,a.sha256,a.ci_commit)
            require(sbom.attributes(before)==sbom.attributes(os.fstat(incoming.fileno()))==sbom.attributes(a.bundle.lstat()))
            write(a.root,'receipt.json',grype.canonical(result))
        print('SEMANTIC_REMEDIATION_BYTE_QUALIFICATION='+json.dumps(result,sort_keys=True));return 0
    except Exception:
        print('SEMANTIC_REMEDIATION_BYTE_QUALIFICATION=BLOCKED ARTIFACT_UNPROVEN ACCEPTANCE=false START=false');return 1
if __name__=='__main__':raise SystemExit(main())
