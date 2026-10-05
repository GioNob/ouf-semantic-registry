#!/usr/bin/python3 -IB
"""CI-only real Docker OCI capture boundary; refuses ALL application execution.

Never register this fixture on a production daemon. Only the isolated CI daemon
knows this runtime. No runc create/start is invoked. `features` is delegated to
the actual CI runc binary, not mocked. JSON belongs to owned synthetic fixtures.
"""
import os
from pathlib import Path
import re
import stat
import sys

try:
    args=sys.argv[1:]
    if args==['features']:
        os.execv('/usr/bin/runc',['/usr/bin/runc','features'])
    if 'create' not in args or args.count('--bundle')!=1:
        raise ValueError()
    cid=args[-1]
    if not re.fullmatch('[0-9a-f]{64}',cid):raise ValueError()
    bundle=Path(args[args.index('--bundle')+1]);source=bundle/'config.json'
    if not bundle.is_absolute() or '..' in bundle.parts:raise ValueError()
    fd=os.open(source,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        before=os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_uid!=0 or not 0<before.st_size<=131072:raise ValueError()
        raw=os.read(fd,131073)
        attrs=lambda s:tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
        if len(raw)!=before.st_size or attrs(os.fstat(fd))!=attrs(before) or attrs(source.lstat())!=attrs(before):raise ValueError()
    finally:os.close(fd)
    parent=Path('/root/ouf-ci-runtime/observed-oci');info=parent.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid!=0 or stat.S_IMODE(info.st_mode)!=0o700:raise ValueError()
    out=os.open(parent/(cid+'.json'),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        with os.fdopen(out,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    except BaseException:
        raise
except Exception:
    pass
# A captured configuration is NOT a successful create. Always refuse execution.
raise SystemExit(69)
