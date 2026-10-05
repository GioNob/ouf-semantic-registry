#!/usr/bin/env bash
# PREPARED_SCOPE_NOT_GRANTED: five private SBOM files + offline Grype evidence.
# No acceptance, signing, registration or application/container operation.
set -Eeuo pipefail
umask 077
SOURCE_COMMIT=4e51e03ccbe6b1fc62d8ca9ba79c03cbeb749cdb
SOURCE_SHA256=52177ba6b8c9a64045d3b1dec51da4730022695f3a45cdf2ebf2e45f1338bce5
SCANNER_ARCHIVE_SHA256=a5a1218dce63acdac152a6b3b5bb366e7267e36f4069848cf455543b3fa5700e
DATABASE_PATH=vulnerability-db_v6.1.10_2026-10-05T00:36:45Z_1791182738.tar.zst
DATABASE_SHA256=97459838f3b53ba97e4562fb3d5d2fd92422cd44c179f59268f0c0d404c00e7a
task_download=$(mktemp -d)
trap 'rm -rf -- "$task_download"' EXIT
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 --max-time 90 --max-filesize 131072 \
  "https://raw.githubusercontent.com/GioNob/ouf-semantic-registry/$SOURCE_COMMIT/tools/semantic_image_vulnerability_reviewer.py" \
  --output "$task_download/reviewer.py"
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 --max-time 90 --max-filesize 67108864 \
  'https://github.com/anchore/grype/releases/download/v0.120.0/grype_0.120.0_linux_amd64.tar.gz' \
  --output "$task_download/scanner.tar.gz"
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 --max-time 180 --max-filesize 1073741824 \
  --user-agent 'grype 0.120.0' "https://grype.anchore.io/databases/v6/$DATABASE_PATH" \
  --output "$task_download/database.tar.zst"
printf '%s  %s\n' "$SOURCE_SHA256" "$task_download/reviewer.py" "$SCANNER_ARCHIVE_SHA256" "$task_download/scanner.tar.gz" \
  "$DATABASE_SHA256" "$task_download/database.tar.zst" | sha256sum --check --strict
sudo /usr/bin/python3 -I -B - "$task_download/reviewer.py" "$task_download/scanner.tar.gz" "$task_download/database.tar.zst" <<'PY'
import hashlib,json,os,signal,stat,sys
from pathlib import Path
def require(ok):
    if not ok:raise ValueError('VULNERABILITY_SCOPE_INPUT_UNPROVEN')
def attrs(s):return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
def captured(filename,expected,limit,destination=None):
    path=Path(filename);fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        s=os.fstat(fd);require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not s.st_mode&0o022 and 0<s.st_size<=limit)
        h=hashlib.sha256();chunks=[];size=0
        while True:
            raw=os.read(fd,65536)
            if not raw:break
            size+=len(raw);require(size<=limit);h.update(raw)
            if destination is None:chunks.append(raw)
            else:destination.write(raw)
        require(size==s.st_size and attrs(s)==attrs(os.fstat(fd))==attrs(path.lstat()) and h.hexdigest()==expected)
        return b''.join(chunks) if destination is None else size
    finally:os.close(fd)
try:
    require(os.geteuid()==0 and sys.flags.isolated and sys.dont_write_bytecode)
    os.umask(0o077);signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError()));signal.alarm(720)
    source=captured(sys.argv[1],'52177ba6b8c9a64045d3b1dec51da4730022695f3a45cdf2ebf2e45f1338bce5',131072)
    scanner_archive=captured(sys.argv[2],'a5a1218dce63acdac152a6b3b5bb366e7267e36f4069848cf455543b3fa5700e',67108864)
    namespace={'__name__':'source_sealed_vulnerability'};exec(compile(source,'<ouf-source-sealed-vulnerability>','exec'),namespace)
    module=sys.modules['tools.review_semantic_image_vulnerabilities'];sbom=sys.modules['tools.prepare_semantic_image_sbom'];archive=sys.modules['tools.verify_semantic_image_archive']
    pin={"built":"2026-10-05T06:45:38Z","checksum":"sha256:97459838f3b53ba97e4562fb3d5d2fd92422cd44c179f59268f0c0d404c00e7a","path":"vulnerability-db_v6.1.10_2026-10-05T00:36:45Z_1791182738.tar.zst","schemaVersion":"v6.1.10","status":"active"}
    module.database_pin(pin)
    unshare=Path('/usr/bin/unshare');unshare_hash=archive.command_snapshot(unshare);sbom.executable(unshare,unshare_hash)
    parent=Path('/etc/ouf/deploy-snapshots');sbom.ancestors(parent/'new-snapshot')
    info=parent.lstat();require(stat.S_ISDIR(info.st_mode) and info.st_uid==info.st_gid==0 and not info.st_mode&0o022)
    disk=os.statvfs(parent);require(disk.f_bavail*disk.f_frsize>=4294967296)
    base=parent/'semantic-image-vulnerability-20261005-v1';base.mkdir(mode=0o700)
    scanner=base/'grype';scanner_hash=module.scanner_from_archive(scanner_archive,scanner)
    database=base/'database.tar.zst';fd=os.open(database,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as out:
        captured(sys.argv[3],pin['checksum'][7:],1073741824,out);out.flush();os.fsync(out.fileno())
    module.hash_file(database,pin['checksum'][7:],1073741824)
    prepared=base/'prepared';prepared.mkdir(mode=0o700)
    expected=[{"schema":"ouf.semantic-image-sbom-artifact.v1","sbomProduced":True,"sbomImageIdentityBound":True,"networkIsolatedScanner":True,"dependencySbomAccepted":False,"vulnerabilityReviewProven":False,"imagePublisherProvenanceVerified":False,"completeCreationAccepted":False,"acceptanceGranted":False,"startAuthorized":False,"packageWithoutVersionCount":0,"role":"adapter","imageId":"sha256:a697bf75bf7d51afadadfaccd3d80537e9a5fb2a08f0d194c6dfd9462e812468","archiveBytes":46233600,"archiveSha256":"d970ec9d1df1d003ad8afe8a9434204399e0e8725ad1a4318bbe91f880c9f730","configByteSha256":"c3607ad2aa45b464c6abce4bec92e8a2fb0a82c0ec65b845c7693d2265048480","rootfsDescriptorsHash":"e6b2f3bd33516825e3bee4a0af52090d917545bd644c294dfe0843b736b088d1","packageCount":95,"spdxJsonSha256":"5c2a5fb2a496abbc4ac58eca9038c7b86c230138bdd9059b67d17c4823d77bda","syftJsonSha256":"7e4aaa6d8df1dd9e9d98d71179aa228e3e3ac0325723f22e2d5d36ab59601acf"},{"schema":"ouf.semantic-image-sbom-artifact.v1","sbomProduced":True,"sbomImageIdentityBound":True,"networkIsolatedScanner":True,"dependencySbomAccepted":False,"vulnerabilityReviewProven":False,"imagePublisherProvenanceVerified":False,"completeCreationAccepted":False,"acceptanceGranted":False,"startAuthorized":False,"packageWithoutVersionCount":0,"role":"southbound","imageId":"sha256:84e6b5e787e9f889ebff88161cb9a16599bafcffa236c6b54c7f779a0655940d","archiveBytes":138930176,"archiveSha256":"fa63d2b535294f802bafed56766e61d98ef08bca15c6ecf19b604bc070fdd1e0","configByteSha256":"b6fd21b8c341f3bf274ddabbad2e3c1bbb6a17566f0e41bf618166e63e4641e4","rootfsDescriptorsHash":"ea6aeeef286a7c893cd0bd8eb7452196d87c8681f72a10a3001af288133528ed","packageCount":179,"spdxJsonSha256":"554a13f86efec9d90908f0da6243104971599b27a6de6eb6a55ad8b0a7d2902f","syftJsonSha256":"83b7fd419b6566df4ca62a524138fe7b50d580a9d4548f3d892fff1fdfa36e58"}]
    result=module.review(prepared,Path('/etc/ouf/deploy-snapshots/semantic-image-sbom-20261005-v1/prepared'),expected,
        '6e0a436d8da6b55c3286811140efd46b679d2ceb9dc202b33576a76425ed08fc',pin,database,scanner,scanner_hash,unshare,unshare_hash)
    result['sourceCommit']='4e51e03ccbe6b1fc62d8ca9ba79c03cbeb749cdb'
    print('SEMANTIC_IMAGE_VULNERABILITIES='+json.dumps(result,sort_keys=True))
    print('SEMANTIC_IMAGE_VULNERABILITIES=SCAN_COMPLETED ACCEPTANCE_GRANTED=false START_AUTHORIZED=false')
except Exception:
    print('SEMANTIC_IMAGE_VULNERABILITIES=BLOCKED REASON=IMAGE_VULNERABILITY_REVIEW_UNPROVEN EXPLICIT_RECOVERY_REQUIRED=true NO_SECRETS_PRINTED=true');raise SystemExit(1)
PY
