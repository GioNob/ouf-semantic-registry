#!/usr/bin/env bash
# Stage a hash-pinned public CI bundle in a NEW private evidence snapshot.
# No Docker/image import, replacement, acceptance, registration or start.
set -Eeuo pipefail
umask 077
[[ $# == 1 ]] || { printf '%s\n' 'Usage: bash qualify.sh /path/to/ouf-remediation.zip'; exit 2; }
SOURCE_COMMIT=c51fe31215efac37308ff6fcb9c577ac475a256f
SOURCE_SHA256=db95b97cce62a4c3e164d0dad20a8674052dced80ff7e683e84ac21cef925112
ARTIFACT_SHA256=bf369a5e445a7e84c51d0252b6714912b0d92897097f3afeb2a21c85db38fa2a
CI_COMMIT=226b1d3cb0562ed1cd840c758873f92ab3401991
task_download=$(mktemp -d)
trap 'rm -rf -- "$task_download"' EXIT
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 --max-time 90 --max-filesize 131072 \
  "https://raw.githubusercontent.com/GioNob/ouf-semantic-registry/$SOURCE_COMMIT/tools/semantic_remediation_bundle_qualifier.py" \
  --output "$task_download/qualifier.py"
printf '%s  %s\n' "$SOURCE_SHA256" "$task_download/qualifier.py" | sha256sum --check --strict
task_report=$(mktemp /tmp/ouf-remediation-qualification.XXXXXX)
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
        require(hashlib.sha256(raw).hexdigest()=='db95b97cce62a4c3e164d0dad20a8674052dced80ff7e683e84ac21cef925112')
    require(sys.argv[3]=='bf369a5e445a7e84c51d0252b6714912b0d92897097f3afeb2a21c85db38fa2a' and sys.argv[4]=='226b1d3cb0562ed1cd840c758873f92ab3401991')
    built=datetime.datetime.fromisoformat('2026-10-05T06:45:38+00:00').timestamp()
    require(0<=time.time()-built<=172800)
    disk=os.statvfs('/etc/ouf/deploy-snapshots');require(disk.f_bavail*disk.f_frsize>=4294967296)
    sys.argv=['qualifier','--bundle',sys.argv[2],'--root','/etc/ouf/deploy-snapshots/semantic-image-remediation-20261006-v1','--sha256',sys.argv[3],'--ci-commit',sys.argv[4]]
    exec(compile(raw,'<ouf-source-sealed-remediation-qualifier>','exec'),{'__name__':'__main__'})
except Exception:
    print('SEMANTIC_REMEDIATION_BYTE_QUALIFICATION=BLOCKED SOURCE_OR_BUNDLE_UNPROVEN ACCEPTANCE=false START=false')
    raise SystemExit(1)
PY
