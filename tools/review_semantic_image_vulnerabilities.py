"""Hash-bound private SBOM scan with an offline pinned scanner/database.

Evidence production only: no release acceptance, waiver, signing or start.
SBOM metadata remains private; stdout contains hashes, counters and states.
"""
import argparse,datetime,hashlib,io,json,os,re,selectors,signal,stat,subprocess,sys,tarfile,time
from pathlib import Path
from tools import prepare_semantic_image_sbom as sbom

GRYPE_VERSION='0.120.0'
GRYPE_ARCHIVE_SHA256='a5a1218dce63acdac152a6b3b5bb366e7267e36f4069848cf455543b3fa5700e'
LIMIT=67108864
SEVERITIES=('Negligible','Low','Medium','High','Critical','Unknown')
class Denied(ValueError):pass
def require(ok):
    if not ok:raise Denied('IMAGE_VULNERABILITY_REVIEW_UNPROVEN')
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def database_pin(value,now=None):
    require(type(value) is dict and set(value)=={'status','schemaVersion','built','path','checksum'})
    require(value['status']=='active' and type(value['schemaVersion']) is str and re.fullmatch(r'6\.\d+\.\d+',value['schemaVersion']))
    require(type(value['path']) is str and re.fullmatch(r'vulnerability-db_v6\.\d+\.\d+_[A-Za-z0-9:T._+-]+\.tar\.zst',value['path']))
    require(type(value['checksum']) is str and re.fullmatch(r'sha256:[0-9a-f]{64}',value['checksum']))
    built=datetime.datetime.fromisoformat(value['built'].replace('Z','+00:00'));require(built.tzinfo is not None)
    now=time.time() if now is None else now;age=now-built.timestamp();require(0<=age<=172800)
    return dict(value)
def hash_file(path,expected,limit):
    sbom.ancestors(path);fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        before=os.fstat(fd);require(stat.S_ISREG(before.st_mode) and before.st_uid==before.st_gid==0 and before.st_nlink==1 and stat.S_IMODE(before.st_mode)==0o600 and 0<before.st_size<=limit)
        h=hashlib.sha256();size=0
        while True:
            raw=os.read(fd,65536)
            if not raw:break
            size+=len(raw);require(size<=limit);h.update(raw)
        require(h.hexdigest()==expected and size==before.st_size and sbom.attributes(before)==sbom.attributes(os.fstat(fd))==sbom.attributes(path.lstat()))
        return sbom.attributes(before)
    finally:os.close(fd)
def scanner_from_archive(raw,destination):
    require(type(raw) is bytes and 0<len(raw)<=LIMIT and sbom.digest(raw)==GRYPE_ARCHIVE_SHA256)
    require(not destination.exists());sbom.ancestors(destination);binary=None;count=0
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r|gz') as package:
        for member in package:
            count+=1;require(count<=32 and member.isfile() and 0<=member.size<=268435456 and member.name in {'grype','LICENSE','README.md','CHANGELOG.md'})
            if member.name=='grype':
                require(binary is None and member.size>0);binary=package.extractfile(member).read(member.size+1);require(len(binary)==member.size)
    require(binary is not None);fd=os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o700)
    with os.fdopen(fd,'wb') as out:out.write(binary);out.flush();os.fsync(out.fileno())
    return sbom.digest(binary)
def summary(raw,expected,pin):
    report=sbom.decode(raw);require(type(report) is dict and type(report['matches']) is list and len(report['matches'])<=100000)
    descriptor=report['descriptor'];require(descriptor['name']=='grype' and descriptor['version']==GRYPE_VERSION)
    ignored=report.get('ignoredMatches');require(ignored is None or (type(ignored) is list and not ignored))
    db=descriptor['db'];require(db['schemaVersion']==pin['schemaVersion'] and db['built']==pin['built'] and not db.get('error'))
    source=report['source'];require(source['type']=='image' and source['target']['imageID']=='sha256:'+expected['configByteSha256'])
    counts={k:0 for k in SEVERITIES};public_ids=set()
    for match in report['matches']:
        vuln=match['vulnerability'];severity=vuln['severity'];require(severity in counts)
        counts[severity]+=1
        identifier=vuln['id'];require(type(identifier) is str)
        if severity in ('High','Critical') and re.fullmatch(r'(CVE-\d{4}-\d{4,}|GHSA-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4})',identifier):public_ids.add(identifier)
    alerts=report.get('alertsByPackage') or [];require(type(alerts) is list)
    threshold=not any(counts[k] for k in ('High','Critical','Unknown')) and not alerts
    return {'schema':'ouf.semantic-image-vulnerability-facts.v1','role':expected['role'],'imageId':expected['imageId'],
        'syftJsonSha256':expected['syftJsonSha256'],'reportSha256':sbom.digest(raw),'databaseArchiveSha256':pin['checksum'][7:],
        'databaseBuilt':pin['built'],'databaseSchemaVersion':pin['schemaVersion'],'severityCounts':counts,
        'highCriticalPublicAdvisoryIds':sorted(public_ids)[:128],'highCriticalPublicAdvisoryIdsTruncated':len(public_ids)>128,
        'packageAlertCount':len(alerts),'scannerSeverityThresholdMet':threshold,
        'dependencyCoverageAccepted':False,'dependencySbomAccepted':False,'imagePublisherProvenanceVerified':False,
        'completeCreationAccepted':False,'acceptanceGranted':False,'startAuthorized':False}
def review(root,source_root,expected,receipt_hash,pin,db_archive,scanner,scanner_hash,unshare,unshare_hash):
    pin=database_pin(pin);require(type(expected) is list and len(expected)==2 and {r['role'] for r in expected}=={'adapter','southbound'})
    require(all(type(r['syftJsonSha256']) is str and re.fullmatch('[0-9a-f]{64}',r['syftJsonSha256']) for r in expected))
    receipt_raw=sbom.private(source_root/'receipt.json');require(sbom.digest(receipt_raw)==receipt_hash)
    receipt=sbom.decode(receipt_raw);require(receipt['schema']=='ouf.semantic-private-image-sbom-preparation.v1' and len(receipt['images'])==2)
    for row in expected:
        original=[r for r in receipt['images'] if r['role']==row['role']];require(len(original)==1 and original[0]==row)
    inputs={}
    for row in expected:
        role=row['role'];syft_path=source_root/(role+'.syft.json');spdx_path=source_root/(role+'.spdx.json')
        syft_raw=sbom.private(syft_path);spdx_raw=sbom.private(spdx_path)
        require(sbom.digest(syft_raw)==row['syftJsonSha256'] and sbom.digest(spdx_raw)==row['spdxJsonSha256'])
        checked=sbom.summarize(syft_raw,spdx_raw,row);require(checked['packageCount']==row['packageCount'] and checked['packageWithoutVersionCount']==0)
        inputs[syft_path]=syft_raw;inputs[spdx_path]=spdx_raw
    sbom.ancestors(root);s=root.lstat();require(stat.S_ISDIR(s.st_mode) and s.st_uid==s.st_gid==0 and stat.S_IMODE(s.st_mode)==0o700)
    require(not (root/'receipt.json').exists());tool_attrs=sbom.executable(scanner,scanner_hash);unshare_attrs=sbom.executable(unshare,unshare_hash)
    db_attrs=hash_file(db_archive,pin['checksum'][7:],1073741824)
    home=root/'scanner-home';home.mkdir(mode=0o700);(home/'tmp').mkdir(mode=0o700)
    env={'PATH':'/usr/bin:/bin','LC_ALL':'C','HOME':str(home),'XDG_CONFIG_HOME':str(home),'TMPDIR':str(home/'tmp'),
        'GRYPE_CHECK_FOR_APP_UPDATE':'false','GRYPE_DB_AUTO_UPDATE':'false','GRYPE_DB_CACHE_DIR':str(root/'database'),
        'GRYPE_DB_VALIDATE_BY_HASH_ON_START':'true','GRYPE_DB_VALIDATE_AGE':'true','GRYPE_DB_MAX_ALLOWED_BUILT_AGE':'48h',
        'GRYPE_EXTERNAL_SOURCES_ENABLE':'false','GRYPE_ONLY_FIXED':'false','GRYPE_ONLY_NOTFIXED':'false'}
    def run(args,output=None,timeout=180):
        child=subprocess.Popen([str(unshare),'--net','--',str(scanner),*args],cwd=home,env=env,
            stdin=subprocess.DEVNULL,stdout=subprocess.PIPE if output is not None else subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,start_new_session=True)
        done=False;end=time.monotonic()+timeout;size=0
        try:
            if output is not None:
                with selectors.DefaultSelector() as selector:
                    os.set_blocking(child.stdout.fileno(),False);selector.register(child.stdout,selectors.EVENT_READ)
                    while True:
                        left=end-time.monotonic();require(left>0 and selector.select(left))
                        raw=os.read(child.stdout.fileno(),65536)
                        if not raw:break
                        size+=len(raw);require(size<=LIMIT);output.write(raw)
            left=end-time.monotonic();require(left>0 and child.wait(timeout=left)==0);done=True
        finally:
            if not done:
                try:os.killpg(child.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                child.wait(timeout=1)
            if child.stdout is not None:child.stdout.close()
    run(['db','import',str(db_archive)])
    rows=[]
    for row in expected:
        path=root/(row['role']+'.grype.json');fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as out:run(['sbom:'+str(source_root/(row['role']+'.syft.json')),'--quiet','-o','json'],out,90);out.flush();os.fsync(out.fileno())
        raw=sbom.private(path);rows.append(summary(raw,row,pin))
    require(sbom.private(source_root/'receipt.json')==receipt_raw and all(sbom.private(p)==raw for p,raw in inputs.items()))
    require(hash_file(db_archive,pin['checksum'][7:],1073741824)==db_attrs)
    require(sbom.executable(scanner,scanner_hash)==tool_attrs and sbom.executable(unshare,unshare_hash)==unshare_attrs)
    database_pin(pin)
    result={'schema':'ouf.semantic-private-image-vulnerability-review.v1','images':rows,'scannerVersion':GRYPE_VERSION,
        'scannerBinarySha256':scanner_hash,'sourceReceiptSha256':receipt_hash,'privateReportsProduced':True,
        'networkIsolatedScanner':True,'providerCalls':0,'containerOperations':0,'signaturesIssued':0,
        'allScannerSeverityThresholdsMet':all(r['scannerSeverityThresholdMet'] for r in rows),
        'dependencyCoverageAccepted':False,'acceptanceGranted':False,'runtimeRegistered':False,'startAuthorized':False}
    fd=os.open(root/'receipt.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as out:out.write(canonical(result));out.flush();os.fsync(out.fileno())
    fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
    return result
def main():
    try:
        require(os.geteuid()==0 and sys.flags.isolated and sys.dont_write_bytecode);os.umask(0o077)
        signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError()));signal.alarm(600)
        p=argparse.ArgumentParser()
        for k in ('root','source-root','expected','receipt-hash','database-pin','db-archive','scanner','scanner-hash','unshare','unshare-hash'):p.add_argument('--'+k,required=True)
        a=p.parse_args();result=review(Path(a.root),Path(a.source_root),sbom.decode(a.expected.encode()),a.receipt_hash,
            sbom.decode(a.database_pin.encode()),Path(a.db_archive),Path(a.scanner),a.scanner_hash,Path(a.unshare),a.unshare_hash)
        print('SEMANTIC_IMAGE_VULNERABILITIES='+json.dumps(result,sort_keys=True))
        print('SEMANTIC_IMAGE_VULNERABILITIES=SCAN_COMPLETED ACCEPTANCE_GRANTED=false START_AUTHORIZED=false');return 0
    except Exception:
        print('SEMANTIC_IMAGE_VULNERABILITIES=BLOCKED REASON=IMAGE_VULNERABILITY_REVIEW_UNPROVEN NO_SECRETS_PRINTED=true');return 1
if __name__=='__main__':raise SystemExit(main())
