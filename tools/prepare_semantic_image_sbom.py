"""Offline SBOM preparation from hash-verified archives, never acceptance.

Caller explicitly grants private image spooling/scanner execution. It must
source-seal this closure, pin the scanner and own an unused private directory.
No mounted runtime configuration, credential, signing key or provider IO.
"""
import argparse,base64,hashlib,io,json,os,re,selectors,signal,stat,subprocess,sys,tarfile,time
from pathlib import Path
from tools import verify_semantic_image_archive as archive

LIMIT=67108864
SCANNER_ARCHIVE_SHA256='54a87372498168b2d033e876fd41fa4e8035b872699e525a57046e1f2f09c860'
class Denied(ValueError):pass
def require(ok):
    if not ok:raise Denied('IMAGE_SBOM_PREPARATION_UNPROVEN')
def digest(raw):return hashlib.sha256(raw).hexdigest()
def scanner_from_archive(raw,destination):
    require(type(raw) is bytes and 0<len(raw)<=LIMIT and digest(raw)==SCANNER_ARCHIVE_SHA256)
    require(not destination.exists());ancestors(destination);binary=None;count=0
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r|gz') as package:
        for member in package:
            count+=1;require(count<=32)
            require(member.isfile() and 0<=member.size<=268435456 and member.name in {'syft','LICENSE','README.md','CHANGELOG.md'})
            if member.name=='syft':
                require(binary is None and member.size>0);binary=package.extractfile(member).read(member.size+1);require(len(binary)==member.size)
    require(binary is not None)
    fd=os.open(destination,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o700)
    with os.fdopen(fd,'wb') as out:out.write(binary);out.flush();os.fsync(out.fileno())
    return digest(binary)
def attributes(info):return tuple(getattr(info,k) for k in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
def ancestors(path):
    require(path.is_absolute() and '..' not in path.parts)
    for parent in path.parents:
        s=parent.lstat();require(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and not s.st_mode&0o022)
def private(path,limit=LIMIT):
    ancestors(path);fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        s=os.fstat(fd);require(stat.S_ISREG(s.st_mode) and s.st_uid==s.st_gid==0 and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600 and 0<s.st_size<=limit)
        parts=[];n=0
        while True:
            part=os.read(fd,min(65536,limit+1-n))
            if not part:break
            parts.append(part);n+=len(part);require(n<=limit)
        require(n==s.st_size and attributes(s)==attributes(os.fstat(fd))==attributes(path.lstat()))
        return b''.join(parts)
    finally:os.close(fd)
def executable(path,expected):
    ancestors(path);fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        s=os.fstat(fd);require(stat.S_ISREG(s.st_mode) and s.st_uid==s.st_gid==0 and s.st_mode&0o111 and not s.st_mode&0o022 and 0<s.st_size<=268435456)
        h=hashlib.sha256()
        while True:
            raw=os.read(fd,65536)
            if not raw:break
            h.update(raw)
        require(h.hexdigest()==expected and attributes(s)==attributes(os.fstat(fd))==attributes(path.lstat()))
        return attributes(s)
    finally:os.close(fd)
def decode(raw):
    def unique(items):
        out={}
        for k,v in items:require(k not in out);out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(Denied()))
def export(docker,image,out,env):
    child=subprocess.Popen([str(docker),'--host','unix:///var/run/docker.sock','image','save',image],
        stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,stdin=subprocess.DEVNULL,env=env,start_new_session=True)
    done=False;end=time.monotonic()+60;size=0
    try:
        with selectors.DefaultSelector() as selector:
            os.set_blocking(child.stdout.fileno(),False);selector.register(child.stdout,selectors.EVENT_READ)
            while True:
                left=end-time.monotonic();require(left>0)
                require(selector.select(left));raw=os.read(child.stdout.fileno(),65536)
                if not raw:break
                size+=len(raw);require(size<=536870912);out.write(raw)
        left=end-time.monotonic();require(left>0);require(child.wait(timeout=left)==0);done=True
    finally:
        if not done:
            try:os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            child.wait(timeout=1)
        child.stdout.close()
def summarize(syft_raw,spdx_raw,verified):
    require(0<len(syft_raw)<=LIMIT and 0<len(spdx_raw)<=LIMIT)
    syft=decode(syft_raw);spdx=decode(spdx_raw);source=syft['source'];meta=source['metadata']
    require(source['type']=='image' and meta['imageID']=='sha256:'+verified['configByteSha256']
        and meta['os']=='linux' and meta['architecture']=='amd64')
    config=base64.b64decode(meta['config'],validate=True)
    require(digest(config)==verified['configByteSha256'])
    require(syft['descriptor']['name']=='syft' and syft['descriptor']['version']=='1.54.0')
    packages=syft['artifacts'];require(type(packages) is list and 0<len(packages)<=100000)
    require(all(type(p) is dict and type(p.get('id')) is str and type(p.get('name')) is str and p['name']
        and type(p.get('version')) is str for p in packages))
    require(len({p['id'] for p in packages})==len(packages))
    require(spdx['spdxVersion']=='SPDX-2.3' and spdx['SPDXID']=='SPDXRef-DOCUMENT'
        and type(spdx['packages']) is list and len(spdx['packages'])>=len(packages))
    require(any(c.startswith('Tool: syft-1.54.0') for c in spdx['creationInfo']['creators']))
    return {'schema':'ouf.semantic-image-sbom-artifact.v1','imageId':verified['imageId'],
        'archiveSha256':verified['archiveSha256'],'archiveBytes':verified['archiveBytes'],
        'configByteSha256':verified['configByteSha256'],'rootfsDescriptorsHash':verified['rootfsDescriptorsHash'],
        'syftJsonSha256':digest(syft_raw),'spdxJsonSha256':digest(spdx_raw),'packageCount':len(packages),
        'packageWithoutVersionCount':sum(not p['version'] for p in packages),
        'sbomProduced':True,'sbomImageIdentityBound':True,'networkIsolatedScanner':True,
        'dependencySbomAccepted':False,'vulnerabilityReviewProven':False,'imagePublisherProvenanceVerified':False,
        'completeCreationAccepted':False,'acceptanceGranted':False,'startAuthorized':False}
def prepare(root,images,docker,docker_hash,scanner,scanner_hash,unshare,unshare_hash):
    require(len(images)==2 and {r['role'] for r in images}=={'adapter','southbound'})
    require(len({r['imageId'] for r in images})==2)
    require(all(set(r)=={'role','imageId','configByteSha256','rootfsDescriptorsHash'} for r in images))
    require(all(type(r['imageId']) is str and re.fullmatch(r'sha256:[0-9a-f]{64}',r['imageId'])
        and all(type(r[k]) is str and re.fullmatch(r'[0-9a-f]{64}',r[k]) for k in ('configByteSha256','rootfsDescriptorsHash')) for r in images))
    ancestors(root);s=root.lstat();require(stat.S_ISDIR(s.st_mode) and s.st_uid==s.st_gid==0 and stat.S_IMODE(s.st_mode)==0o700)
    require(not (root/'receipt.json').exists() and all(not (root/(r['role']+'.tar')).exists() for r in images))
    pins={p:executable(p,h) for p,h in ((docker,docker_hash),(scanner,scanner_hash),(unshare,unshare_hash))}
    work=root/'scanner-home';work.mkdir(mode=0o700);(work/'tmp').mkdir(mode=0o700)
    env={'PATH':'/usr/bin:/bin','LC_ALL':'C','HOME':str(work),'XDG_CONFIG_HOME':str(work),
        'DOCKER_CONFIG':str(work),'TMPDIR':str(work/'tmp'),'SYFT_CHECK_FOR_APP_UPDATE':'false'}
    rows=[]
    for row in images:
        role=row['role'];tar=root/(role+'.tar');fd=os.open(tar,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as out:
            export(docker,row['imageId'],out,env);out.flush();os.fsync(out.fileno())
        s=tar.lstat();require(stat.S_ISREG(s.st_mode) and 0<s.st_size<=8589934592)
        with tar.open('rb') as stream:verified=archive.archive_verify(stream,row['imageId'],archive.Budget(180,8589934592,100000))
        require(all(verified[k]==row[k] for k in ('configByteSha256','rootfsDescriptorsHash')))
        before=attributes(tar.lstat());spdx=root/(role+'.spdx.json');syft=root/(role+'.syft.json')
        require(not spdx.exists() and not syft.exists())
        result=subprocess.run([str(unshare),'--net','--',str(scanner),'scan','docker-archive:'+str(tar),
            '--quiet','-o','spdx-json='+str(spdx),'-o','syft-json='+str(syft)],cwd=work,env=env,
            stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=90)
        require(result.returncode==0 and attributes(tar.lstat())==before)
        summary=summarize(private(syft),private(spdx),verified);summary['role']=role;rows.append(summary)
        # Verify the archive again after scanning; receipt binds the exact bytes.
        with tar.open('rb') as stream:after=archive.archive_verify(stream,row['imageId'],archive.Budget(180,8589934592,100000))
        require(after==verified and attributes(tar.lstat())==before)
    require(all(executable(p,h)==pins[p] for p,h in ((docker,docker_hash),(scanner,scanner_hash),(unshare,unshare_hash))))
    result={'schema':'ouf.semantic-private-image-sbom-preparation.v1','images':rows,
        'scannerVersion':'1.54.0','scannerBinarySha256':scanner_hash,'imageArchivesPrivatelySpooled':True,
        'scannerImageFilesExtractedPrivately':True,'mountedRuntimeFilesRead':False,'signingKeysRead':False,
        'containerOperations':0,'providerCalls':0,'signaturesIssued':0,'acceptanceGranted':False,
        'runtimeRegistered':False,'startAuthorized':False,'noSecretsPrinted':True}
    fd=os.open(root/'receipt.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as out:out.write(json.dumps(result,sort_keys=True,separators=(',',':')).encode());out.flush();os.fsync(out.fileno())
    fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
    return result
def main():
    try:
        require(os.geteuid()==0 and sys.flags.isolated and sys.dont_write_bytecode)
        os.umask(0o077);signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError()));signal.alarm(420)
        p=argparse.ArgumentParser()
        for name in ('root','images','docker','docker-hash','scanner','scanner-hash','unshare','unshare-hash'):p.add_argument('--'+name,required=True)
        a=p.parse_args();result=prepare(Path(a.root),decode(a.images.encode()),Path(a.docker),a.docker_hash,Path(a.scanner),a.scanner_hash,Path(a.unshare),a.unshare_hash)
        print('SEMANTIC_IMAGE_SBOM='+json.dumps(result,sort_keys=True));print('SEMANTIC_IMAGE_SBOM=PASS ACCEPTANCE_GRANTED=false START_AUTHORIZED=false');return 0
    except Exception:
        print('SEMANTIC_IMAGE_SBOM=BLOCKED REASON=IMAGE_SBOM_PREPARATION_UNPROVEN NO_SECRETS_PRINTED=true');return 1
if __name__=='__main__':raise SystemExit(main())
