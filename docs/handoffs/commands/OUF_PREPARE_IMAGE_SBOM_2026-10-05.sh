#!/usr/bin/env bash
# PREPARED_SCOPE_NOT_GRANTED: private image spooling + offline Syft execution.
# PET supply-chain input generation only; no acceptance, signature or start.
set -Eeuo pipefail
umask 077
SOURCE_COMMIT=d9a024dfd526be619759948e0cf1b0158f45631e
SOURCE_SHA256=315057ec4718db053eb8865a1d2b1e2317bd9f16dad2b8c31ea36e0250ab97ca
SCANNER_ARCHIVE_SHA256=54a87372498168b2d033e876fd41fa4e8035b872699e525a57046e1f2f09c860
task_download=$(mktemp -d)
trap 'rm -rf -- "$task_download"' EXIT
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 --max-time 90 \
  "https://raw.githubusercontent.com/GioNob/ouf-semantic-registry/$SOURCE_COMMIT/tools/semantic_image_sbom_preparer.py" \
  --output "$task_download/preparer.py"
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 --max-time 90 \
  'https://github.com/anchore/syft/releases/download/v1.54.0/syft_1.54.0_linux_amd64.tar.gz' \
  --output "$task_download/scanner.tar.gz"
printf '%s  %s\n' "$SOURCE_SHA256" "$task_download/preparer.py" "$SCANNER_ARCHIVE_SHA256" "$task_download/scanner.tar.gz" | sha256sum --check --strict
sudo /usr/bin/python3 -I -B - "$task_download/preparer.py" "$task_download/scanner.tar.gz" <<'PY'
import hashlib,json,os,signal,stat,sys
from pathlib import Path
def require(ok):
    if not ok:raise ValueError('SBOM_SCOPE_INPUT_UNPROVEN')
def attrs(s):return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
def captured(filename,expected,limit):
    path=Path(filename);fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        s=os.fstat(fd);require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not s.st_mode&0o022 and 0<s.st_size<=limit)
        chunks=[];size=0
        while True:
            raw=os.read(fd,65536)
            if not raw:break
            size+=len(raw);require(size<=limit);chunks.append(raw)
        raw=b''.join(chunks);require(size==s.st_size and attrs(s)==attrs(os.fstat(fd))==attrs(path.lstat()) and hashlib.sha256(raw).hexdigest()==expected)
        return raw
    finally:os.close(fd)
try:
    require(os.geteuid()==0 and sys.flags.isolated and sys.dont_write_bytecode)
    os.umask(0o077);signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError()));signal.alarm(420)
    source=captured(sys.argv[1],'315057ec4718db053eb8865a1d2b1e2317bd9f16dad2b8c31ea36e0250ab97ca',131072)
    scanner_archive=captured(sys.argv[2],'54a87372498168b2d033e876fd41fa4e8035b872699e525a57046e1f2f09c860',67108864)
    namespace={'__name__':'source_sealed_sbom'};exec(compile(source,'<ouf-source-sealed-sbom>','exec'),namespace)
    module=sys.modules['tools.prepare_semantic_image_sbom'];archive=sys.modules['tools.verify_semantic_image_archive']
    docker=Path('/usr/bin/docker');docker_hash='7f5b38163f9c5367f4b42d905c0505877eafa4c20abe49430c85a770aefacf40'
    module.executable(docker,docker_hash)
    unshare=Path('/usr/bin/unshare');unshare_hash=archive.command_snapshot(unshare)
    parent=Path('/etc/ouf/deploy-snapshots');module.ancestors(parent/'new-snapshot')
    info=parent.lstat();require(stat.S_ISDIR(info.st_mode) and info.st_uid==info.st_gid==0 and not info.st_mode&0o022)
    disk=os.statvfs(parent);require(disk.f_bavail*disk.f_frsize>=2147483648)
    base=parent/'semantic-image-sbom-20261005-v1';base.mkdir(mode=0o700)
    prepared=base/'prepared';prepared.mkdir(mode=0o700)
    scanner=base/'syft';scanner_hash=module.scanner_from_archive(scanner_archive,scanner)
    images=[{'role':'adapter','imageId':'sha256:a697bf75bf7d51afadadfaccd3d80537e9a5fb2a08f0d194c6dfd9462e812468',
        'configByteSha256':'c3607ad2aa45b464c6abce4bec92e8a2fb0a82c0ec65b845c7693d2265048480',
        'rootfsDescriptorsHash':'e6b2f3bd33516825e3bee4a0af52090d917545bd644c294dfe0843b736b088d1'},
        {'role':'southbound','imageId':'sha256:84e6b5e787e9f889ebff88161cb9a16599bafcffa236c6b54c7f779a0655940d',
        'configByteSha256':'b6fd21b8c341f3bf274ddabbad2e3c1bbb6a17566f0e41bf618166e63e4641e4',
        'rootfsDescriptorsHash':'ea6aeeef286a7c893cd0bd8eb7452196d87c8681f72a10a3001af288133528ed'}]
    result=module.prepare(prepared,images,docker,docker_hash,scanner,scanner_hash,unshare,unshare_hash)
    result['sourceCommit']='d9a024dfd526be619759948e0cf1b0158f45631e'
    print('SEMANTIC_IMAGE_SBOM='+json.dumps(result,sort_keys=True))
    print('SEMANTIC_IMAGE_SBOM=PASS ACCEPTANCE_GRANTED=false START_AUTHORIZED=false')
except Exception:
    print('SEMANTIC_IMAGE_SBOM=BLOCKED REASON=IMAGE_SBOM_PREPARATION_UNPROVEN PARTIAL_ROOT_PRESERVED=true NO_SECRETS_PRINTED=true');raise SystemExit(1)
PY
