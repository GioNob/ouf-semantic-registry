#!/usr/bin/env bash
# Read-only recovery within already granted scope49; never reruns Grype.
set -Eeuo pipefail
umask 077
task_diag49=$(mktemp -d)
task_report49=$(mktemp /tmp/ouf-gate49-diagnostic.XXXXXX)
trap 'rm -rf -- "$task_diag49"' EXIT
printf 'REPORT_REDACTED_SAVED=%s\n' "$task_report49"
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 --max-time 90 --max-filesize 131072 \
  'https://raw.githubusercontent.com/GioNob/ouf-semantic-registry/56ab1db6f063290bfbcf15afb6638dddc8b242f4/tools/diagnose_semantic_image_vulnerabilities.py' \
  --output "$task_diag49/diagnostic.py"
printf '%s  %s\n' '4f6197c0dbf90056060c7435f2cffc807d5ede5c44a22205292bb0a54b2bc48a' "$task_diag49/diagnostic.py" | sha256sum --check --strict
sudo /usr/bin/python3 -I -B - "$task_diag49/diagnostic.py" <<'PY' | tee "$task_report49"
import hashlib,os,stat,sys
from pathlib import Path
try:
    path=Path(sys.argv[1]);fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        info=os.fstat(fd)
        if not (stat.S_ISREG(info.st_mode) and info.st_nlink==1 and not info.st_mode&0o022 and 0<info.st_size<=131072):raise ValueError()
        def attrs(s):return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
        source=bytearray()
        while True:
            part=os.read(fd,65536)
            if not part:break
            source.extend(part)
            if len(source)>131072:raise ValueError()
        if not (len(source)==info.st_size and attrs(info)==attrs(os.fstat(fd))==attrs(path.lstat()) and
            hashlib.sha256(source).hexdigest()=='4f6197c0dbf90056060c7435f2cffc807d5ede5c44a22205292bb0a54b2bc48a'):raise ValueError()
    finally:os.close(fd)
    exec(compile(bytes(source),'<ouf-source-sealed-vulnerability-diagnostic>','exec'),{'__name__':'__main__'})
except Exception:
    print('SEMANTIC_VULNERABILITY_DIAGNOSTIC=BLOCKED SOURCE_OR_EXECUTION_UNPROVEN NO_RAW_METADATA_PRINTED=true');raise SystemExit(1)
PY
