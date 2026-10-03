#!/usr/bin/env python3
"""Idempotently reconcile the explicit OAuth scope set in one OUF policy-token config.

Only OUF_POLICY_TOKEN_REQUIRED_SCOPE is changed. Other configuration, including
secret file paths and client identifiers, is preserved byte-for-byte except for
the replaced scope line. Apply requires root, writes atomically, and creates a
0600 backup next to the target unless the desired state is already present.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile

KEY="OUF_POLICY_TOKEN_REQUIRED_SCOPE"

class ReconcileError(RuntimeError):
    pass

def normalize(scopes:list[str])->str:
    values=[]
    seen=set()
    for raw in scopes:
        for value in raw.split():
            if not re.fullmatch(r"[A-Za-z0-9._:-]+",value):
                raise ReconcileError("INVALID_SCOPE")
            if value not in seen:
                seen.add(value)
                values.append(value)
    if not values:
        raise ReconcileError("SCOPE_SET_EMPTY")
    return " ".join(values)

def parse(lines:list[str])->tuple[int|None,str|None]:
    found=[]
    for i,line in enumerate(lines):
        if line.startswith(KEY+"="):
            found.append((i,line[len(KEY)+1:].strip()))
    if len(found)>1:
        raise ReconcileError("DUPLICATE_SCOPE_KEY")
    return found[0] if found else (None,None)

def inspect(path:Path,wanted:str)->dict:
    if not path.is_absolute():
        raise ReconcileError("CONFIG_PATH_MUST_BE_ABSOLUTE")
    if not path.exists() or not path.is_file() or path.is_symlink():
        raise ReconcileError("CONFIG_FILE_INVALID")
    lines=path.read_text().splitlines(keepends=True)
    index,current=parse(lines)
    return {
        "lines":lines,
        "index":index,
        "current":current,
        "drift":current!=wanted,
    }

def render(state:dict,wanted:str)->str:
    lines=list(state["lines"])
    newline="\n"
    if lines and lines[-1].endswith("\r\n"):
        newline="\r\n"
    replacement=KEY+"="+wanted+newline
    if state["index"] is None:
        if lines and not lines[-1].endswith(("\n","\r")):
            lines[-1]=lines[-1]+newline
        lines.append(replacement)
    else:
        original=lines[state["index"]]
        ending="\r\n" if original.endswith("\r\n") else "\n"
        lines[state["index"]]=KEY+"="+wanted+ending
    return "".join(lines)

def atomic_apply(path:Path,content:str)->Path:
    st=path.stat()
    backup=path.with_name(path.name+".bak")
    shutil.copy2(path,backup)
    os.chown(backup,0,0)
    os.chmod(backup,0o600)
    fd,tmp=tempfile.mkstemp(prefix="."+path.name+"-",dir=path.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8",newline="") as stream:
            os.fchown(stream.fileno(),st.st_uid,st.st_gid)
            os.fchmod(stream.fileno(),stat.S_IMODE(st.st_mode))
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp,path)
    finally:
        Path(tmp).unlink(missing_ok=True)
    return backup

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("plan","apply","verify"))
    p.add_argument("--config",type=Path,required=True)
    p.add_argument("--scope",action="append",required=True)
    a=p.parse_args()
    wanted=normalize(a.scope)
    before=inspect(a.config,wanted)

    print("MODE="+a.mode)
    print("CONFIG="+str(a.config))
    print("REQUIRED_SCOPE="+wanted)
    print("DRIFT="+str(before["drift"]).lower())

    if a.mode=="plan":
        print("NO_CHANGES=true")
        return

    if a.mode=="apply" and before["drift"]:
        if os.geteuid()!=0:
            raise ReconcileError("APPLY_REQUIRES_ROOT")
        backup=atomic_apply(a.config,render(before,wanted))
        print("BACKUP="+str(backup))

    after=inspect(a.config,wanted)
    if after["drift"]:
        raise ReconcileError("VERIFY_DRIFT")
    print("VERIFY=PASS")
    print("SECRETS_PRINTED=false")

if __name__=="__main__":
    try:
        main()
    except (OSError,ReconcileError) as exc:
        code=str(exc) if isinstance(exc,ReconcileError) else type(exc).__name__
        raise SystemExit("POLICY_TOKEN_CONFIG_RECONCILE_FAILED:"+code)
