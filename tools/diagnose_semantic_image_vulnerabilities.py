"""Read-only fixed-artifact reconciliation after gate49 BLOCKED; no scanner IO."""
import hashlib,json,os,signal,stat,sys,time
from pathlib import Path

class Denied(ValueError):pass
def require(ok):
    if not ok:raise Denied('DIAGNOSTIC_INPUT_UNPROVEN')
def attrs(s):return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
def metadata(path):
    for parent in reversed(path.parents):
        try:s=parent.lstat()
        except FileNotFoundError:return {'state':'ABSENT'}
        require(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and not s.st_mode&0o022)
    try:s=path.lstat()
    except FileNotFoundError:return {'state':'ABSENT'}
    kind='FILE' if stat.S_ISREG(s.st_mode) else 'DIRECTORY' if stat.S_ISDIR(s.st_mode) else 'UNSUPPORTED'
    return {'state':'PRESENT','kind':kind,'rootOwned':s.st_uid==s.st_gid==0,'mode':oct(stat.S_IMODE(s.st_mode)),'bytes':s.st_size,'singleLink':s.st_nlink==1}
def read(path,limit,mode=0o600,keep=True):
    require(path.is_absolute() and '..' not in path.parts);metadata(path)
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        s=os.fstat(fd);require(stat.S_ISREG(s.st_mode) and s.st_uid==s.st_gid==0 and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==mode and 0<s.st_size<=limit)
        h=hashlib.sha256();parts=[];size=0
        while True:
            raw=os.read(fd,65536)
            if not raw:break
            size+=len(raw);require(size<=limit);h.update(raw)
            if keep:parts.append(raw)
        require(size==s.st_size and attrs(s)==attrs(os.fstat(fd))==attrs(path.lstat()))
        return h.hexdigest(),b''.join(parts) if keep else None
    finally:os.close(fd)
def decode(raw):
    def unique(items):
        out={}
        for k,v in items:require(k not in out);out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(Denied()))
def report_facts(raw,row,pin):
    r=decode(raw);require(type(r) is dict)
    descriptor=r.get('descriptor');descriptor=descriptor if type(descriptor) is dict else {}
    db=descriptor.get('db');db=db if type(db) is dict else {}
    status=db.get('status');status=status if type(status) is dict else {}
    source=r.get('source');source=source if type(source) is dict else {}
    target=source.get('target');target=target if type(target) is dict else {}
    matches=r.get('matches');shape=type(matches) is list and len(matches)<=100000
    counts={k:0 for k in ('Negligible','Low','Medium','High','Critical','Unknown')};invalid=0
    if shape:
        for match in matches:
            v=match.get('vulnerability') if type(match) is dict else None
            severity=v.get('severity') if type(v) is dict else None
            if type(severity) is str and severity in counts:counts[severity]+=1
            else:invalid+=1
    ignored=r.get('ignoredMatches');alerts=r.get('alertsByPackage')
    return {'scannerVersionMatches':descriptor.get('name')=='grype' and descriptor.get('version')=='0.120.0',
        'databaseStatusPresent':bool(status),'databaseSchemaMatches':status.get('schemaVersion')==pin['schemaVersion'],
        'databaseBuiltMatches':status.get('built')==pin['built'],'databaseValid':status.get('valid') is True,'databaseErrorPresent':bool(status.get('error')),
        'imageBindingMatches':source.get('type')=='image' and target.get('imageID')=='sha256:'+row['configByteSha256'],
        'matchesShapeValid':shape,'severityCounts':counts,'invalidSeverityCount':invalid,
        'ignoredShapeValid':ignored is None or type(ignored) is list,'ignoredCount':len(ignored) if type(ignored) is list else 0,
        'alertsShapeValid':alerts is None or type(alerts) is list,'alertCount':len(alerts) if type(alerts) is list else 0}
def diagnose(source_root,base,expected,pin,receipt_hash):
    require(source_root.is_absolute() and base.is_absolute())
    labels={'SOURCE_RECEIPT':source_root/'receipt.json','TARGET_ROOT':base,'SCANNER':base/'grype','DATABASE_ARCHIVE':base/'database.tar.zst',
        'PREPARED':base/'prepared','SCANNER_HOME':base/'prepared/scanner-home','DATABASE_CACHE':base/'prepared/database',
        'IMPORTED_DATABASE':base/'prepared/database/6/vulnerability.db','FINAL_RECEIPT':base/'prepared/receipt.json'}
    for row in expected:
        role=row['role'];require(role in ('adapter','southbound'))
        labels[role.upper()+'_SYFT']=source_root/(role+'.syft.json');labels[role.upper()+'_SPDX']=source_root/(role+'.spdx.json')
        labels[role.upper()+'_REPORT']=base/'prepared'/(role+'.grype.json')
    facts={};reports={}
    for label,path in labels.items():
        try:facts[label]=metadata(path)
        except Exception:facts[label]={'state':'METADATA_DENIED'}
    def checked(label,limit,expected_hash=None,mode=0o600,keep=False):
        if facts[label].get('state')!='PRESENT':return None
        try:
            digest,raw=read(labels[label],limit,mode,keep);facts[label]['readStable']=True;facts[label]['sha256']=digest
            if expected_hash is not None:facts[label]['hashMatches']=digest==expected_hash
            return raw
        except Exception:facts[label]['readStable']=False;return None
    checked('SOURCE_RECEIPT',131072,receipt_hash)
    for row in expected:
        role=row['role'];checked(role.upper()+'_SYFT',67108864,row['syftJsonSha256']);checked(role.upper()+'_SPDX',67108864,row['spdxJsonSha256'])
        label=role.upper()+'_REPORT';raw=checked(label,67108864,keep=True)
        if raw is not None:
            try:reports[role]=report_facts(raw,row,pin)
            except Exception:reports[role]={'jsonReadable':False}
    checked('DATABASE_ARCHIVE',1073741824,pin['checksum'][7:]);checked('SCANNER',268435456,mode=0o700)
    raw=checked('FINAL_RECEIPT',131072,keep=True);receipt={}
    if raw is not None:
        try:
            r=decode(raw);require(type(r) is dict)
            receipt={'schemaMatches':r.get('schema')=='ouf.semantic-private-image-vulnerability-review.v1',
                'sourceReceiptHashMatches':r.get('sourceReceiptSha256')==receipt_hash,'declaresAcceptanceFalse':r.get('acceptanceGranted') is False,
                'declaresStartFalse':r.get('startAuthorized') is False,'declaresRuntimeFalse':r.get('runtimeRegistered') is False,
                'thresholdFieldValid':type(r.get('allScannerSeverityThresholdsMet')) is bool}
        except Exception:receipt={'jsonReadable':False}
    try:d=os.statvfs(source_root);free=d.f_bavail*d.f_frsize
    except Exception:free=None
    return {'schema':'ouf.semantic-image-vulnerability-readonly-diagnostic.v1','artifactFacts':facts,'reports':reports,'finalReceiptFacts':receipt,
        'currentFreeBytes':free,'scannerInvoked':False,'targetFilesWritten':0,'containerOperations':0,'acceptanceGranted':False,'startAuthorized':False,
        'causeProven':False,'noRawMetadataPrinted':True}
def main():
    try:
        require(os.geteuid()==0 and sys.flags.isolated and sys.dont_write_bytecode);signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError()));signal.alarm(180)
        result=diagnose(Path('/etc/ouf/deploy-snapshots/semantic-image-sbom-20261005-v1/prepared'),
            Path('/etc/ouf/deploy-snapshots/semantic-image-vulnerability-20261005-v1'),EXPECTED,PIN,
            '6e0a436d8da6b55c3286811140efd46b679d2ceb9dc202b33576a76425ed08fc')
        print('SEMANTIC_VULNERABILITY_DIAGNOSTIC='+json.dumps(result,sort_keys=True));return 0
    except Exception:
        print('SEMANTIC_VULNERABILITY_DIAGNOSTIC=BLOCKED NO_RAW_METADATA_PRINTED=true');return 1

EXPECTED=[{"schema":"ouf.semantic-image-sbom-artifact.v1","sbomProduced":True,"sbomImageIdentityBound":True,"networkIsolatedScanner":True,"dependencySbomAccepted":False,"vulnerabilityReviewProven":False,"imagePublisherProvenanceVerified":False,"completeCreationAccepted":False,"acceptanceGranted":False,"startAuthorized":False,"packageWithoutVersionCount":0,"role":"adapter","imageId":"sha256:a697bf75bf7d51afadadfaccd3d80537e9a5fb2a08f0d194c6dfd9462e812468","archiveBytes":46233600,"archiveSha256":"d970ec9d1df1d003ad8afe8a9434204399e0e8725ad1a4318bbe91f880c9f730","configByteSha256":"c3607ad2aa45b464c6abce4bec92e8a2fb0a82c0ec65b845c7693d2265048480","rootfsDescriptorsHash":"e6b2f3bd33516825e3bee4a0af52090d917545bd644c294dfe0843b736b088d1","packageCount":95,"spdxJsonSha256":"5c2a5fb2a496abbc4ac58eca9038c7b86c230138bdd9059b67d17c4823d77bda","syftJsonSha256":"7e4aaa6d8df1dd9e9d98d71179aa228e3e3ac0325723f22e2d5d36ab59601acf"},{"schema":"ouf.semantic-image-sbom-artifact.v1","sbomProduced":True,"sbomImageIdentityBound":True,"networkIsolatedScanner":True,"dependencySbomAccepted":False,"vulnerabilityReviewProven":False,"imagePublisherProvenanceVerified":False,"completeCreationAccepted":False,"acceptanceGranted":False,"startAuthorized":False,"packageWithoutVersionCount":0,"role":"southbound","imageId":"sha256:84e6b5e787e9f889ebff88161cb9a16599bafcffa236c6b54c7f779a0655940d","archiveBytes":138930176,"archiveSha256":"fa63d2b535294f802bafed56766e61d98ef08bca15c6ecf19b604bc070fdd1e0","configByteSha256":"b6fd21b8c341f3bf274ddabbad2e3c1bbb6a17566f0e41bf618166e63e4641e4","rootfsDescriptorsHash":"ea6aeeef286a7c893cd0bd8eb7452196d87c8681f72a10a3001af288133528ed","packageCount":179,"spdxJsonSha256":"554a13f86efec9d90908f0da6243104971599b27a6de6eb6a55ad8b0a7d2902f","syftJsonSha256":"83b7fd419b6566df4ca62a524138fe7b50d580a9d4548f3d892fff1fdfa36e58"}]
PIN={"built":"2026-10-05T06:45:38Z","checksum":"sha256:97459838f3b53ba97e4562fb3d5d2fd92422cd44c179f59268f0c0d404c00e7a","path":"vulnerability-db_v6.1.10_2026-10-05T00:36:45Z_1791182738.tar.zst","schemaVersion":"v6.1.10","status":"active"}
if __name__=='__main__':raise SystemExit(main())
