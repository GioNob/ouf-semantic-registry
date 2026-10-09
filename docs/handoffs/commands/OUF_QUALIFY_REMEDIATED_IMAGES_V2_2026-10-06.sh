#!/usr/bin/env bash
# Stage a hash-pinned public CI bundle in a NEW private evidence snapshot.
# No Docker/image import, replacement, acceptance, registration or start.
set -Eeuo pipefail
umask 077
[[ $# == 1 ]] || { printf '%s\n' 'Usage: bash qualify-v2.sh /path/to/ouf-remediation-v2.zip'; exit 2; }
SOURCE_COMMIT=1ef1d7abdbc6b2b879e57f3c09eaa5fe18f18ef6
SOURCE_SHA256=f9634d518f6812a33953cf64f25a6217a9438d813379823cb69ffb39d697bc58
ARTIFACT_SHA256=2cdd7a73c1fc2a710f1e6604eb6cab2988492e4c45b5252defffa9832b91d9d0
CI_COMMIT=0a1b4460c52c74cefe806286f043f71cbf5a5647
task_download=$(mktemp -d)
trap 'rm -rf -- "$task_download"' EXIT
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 --max-time 90 --max-filesize 131072 \
  "https://raw.githubusercontent.com/GioNob/ouf-semantic-registry/$SOURCE_COMMIT/tools/semantic_remediation_bundle_qualifier.py" \
  --output "$task_download/qualifier.py"
printf '%s  %s\n' "$SOURCE_SHA256" "$task_download/qualifier.py" | sha256sum --check --strict
task_report=$(mktemp /tmp/ouf-remediation-qualification-v2.XXXXXX)
printf 'REPORT_REDACTED_SAVED=%s\n' "$task_report"
sudo /usr/bin/python3 -I -B - "$task_download/qualifier.py" "$1" "$ARTIFACT_SHA256" "$CI_COMMIT" <<'PY' | tee "$task_report"
import datetime,hashlib,os,signal,stat,sys,time
from pathlib import Path
def require(ok):
    if not ok:raise ValueError('REMEDIATION_SOURCE_UNPROVEN')
def attrs(s):return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
try:
    require(os.geteuid()==os.getegid()==0 and sys.flags.isolated and sys.dont_write_bytecode)
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError()));signal.alarm(900)
    path=Path(sys.argv[1]);fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as file:
        before=os.fstat(file.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and not before.st_mode&0o022 and 0<before.st_size<=131072)
        raw=file.read(131073)
        require(len(raw)==before.st_size and attrs(before)==attrs(os.fstat(file.fileno()))==attrs(path.lstat()))
        require(hashlib.sha256(raw).hexdigest()=='f9634d518f6812a33953cf64f25a6217a9438d813379823cb69ffb39d697bc58')
    require(sys.argv[3]=='2cdd7a73c1fc2a710f1e6604eb6cab2988492e4c45b5252defffa9832b91d9d0' and sys.argv[4]=='0a1b4460c52c74cefe806286f043f71cbf5a5647')
    built=datetime.datetime.fromisoformat('2026-10-05T06:45:38+00:00').timestamp()
    require(0<=time.time()-built<=172800)
    disk=os.statvfs('/etc/ouf/deploy-snapshots');require(disk.f_bavail*disk.f_frsize>=4294967296)
    sys.argv=['qualifier','--bundle',sys.argv[2],'--root','/etc/ouf/deploy-snapshots/semantic-image-remediation-20261006-v2','--sha256',sys.argv[3],'--ci-commit',sys.argv[4]]
    exec(compile(raw,'<ouf-source-sealed-remediation-qualifier>','exec'),{'__name__':'__main__'})
except Exception:
    print('SEMANTIC_REMEDIATION_BYTE_QUALIFICATION=BLOCKED SOURCE_OR_BUNDLE_UNPROVEN ACCEPTANCE=false START=false')
    raise SystemExit(1)
PY
