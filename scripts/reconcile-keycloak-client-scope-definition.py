#!/usr/bin/env python3
"""Idempotently reconcile one Keycloak OpenID Connect client scope.

Modes:
  plan   - read-only comparison
  apply  - create/update exact scope definition
  verify - read-only acceptance

The helper never prints credentials, tokens, or client secrets. The caller must
already have an authenticated kcadm session.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess

KC="/opt/keycloak/bin/kcadm.sh"

class ReconcileError(RuntimeError):
    pass

def run(*args:str,input_text:str|None=None)->str:
    p=subprocess.run(
        ["docker","exec","-i","ouf-keycloak",KC,*args],
        input=input_text,text=True,capture_output=True
    )
    if p.returncode:
        msg=(p.stderr or p.stdout).strip()
        if "Session has expired" in msg:
            raise ReconcileError("KCADM_SESSION_EXPIRED")
        raise ReconcileError("KCADM_COMMAND_FAILED")
    return p.stdout

def get_json(*args:str):
    try:
        return json.loads(run(*args))
    except json.JSONDecodeError as exc:
        raise ReconcileError("KCADM_INVALID_JSON") from exc

def validate_name(value:str,label:str)->None:
    if not re.fullmatch(r"[A-Za-z0-9._:-]+",value):
        raise ReconcileError("INVALID_"+label)

def exact_scope(realm:str,name:str):
    rows=get_json("get","client-scopes","-r",realm)
    matches=[x for x in rows if isinstance(x,dict) and x.get("name")==name]
    if len(matches)>1:
        raise ReconcileError("SCOPE_NOT_UNIQUE")
    return matches[0] if matches else None

def desired(name:str)->dict:
    return {
        "name":name,
        "description":"OUF governed scope "+name,
        "protocol":"openid-connect",
        "attributes":{
            "include.in.token.scope":"true",
            "display.on.consent.screen":"false",
        },
    }

def inspect(realm:str,name:str)->dict:
    ref=exact_scope(realm,name)
    if ref is None:
        return {"exists":False,"drift":["SCOPE_MISSING"],"id":None}
    sid=ref.get("id")
    if not sid:
        raise ReconcileError("SCOPE_WITHOUT_ID")
    current=get_json("get",f"client-scopes/{sid}","-r",realm)
    drift=[]
    wanted=desired(name)
    if current.get("name")!=wanted["name"]:
        drift.append("NAME")
    if current.get("protocol")!=wanted["protocol"]:
        drift.append("PROTOCOL")
    attrs=current.get("attributes") or {}
    for key,value in wanted["attributes"].items():
        if attrs.get(key)!=value:
            drift.append("ATTRIBUTE:"+key)
    return {"exists":True,"drift":drift,"id":sid}

def create(realm:str,name:str)->None:
    payload=json.dumps(desired(name),separators=(",",":"))
    run("create","client-scopes","-r",realm,"-f","-",input_text=payload)

def update(realm:str,sid:str,name:str)->None:
    payload=json.dumps(desired(name),separators=(",",":"))
    run("update",f"client-scopes/{sid}","-r",realm,"-f","-",input_text=payload)

def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("plan","apply","verify"))
    p.add_argument("--realm",default="ouf")
    p.add_argument("--scope",required=True)
    a=p.parse_args()

    validate_name(a.realm,"REALM")
    validate_name(a.scope,"SCOPE")

    before=inspect(a.realm,a.scope)
    print("MODE="+a.mode)
    print("SCOPE="+a.scope)
    print("EXISTS="+str(before["exists"]).lower())
    print("DRIFT="+(",".join(before["drift"]) if before["drift"] else "NONE"))

    if a.mode=="plan":
        print("NO_CHANGES=true")
        return

    if a.mode=="apply":
        if before["exists"]:
            if before["drift"]:
                update(a.realm,before["id"],a.scope)
        else:
            create(a.realm,a.scope)

    after=inspect(a.realm,a.scope)
    if not after["exists"] or after["drift"]:
        raise ReconcileError("VERIFY_DRIFT:"+",".join(after["drift"]))
    print("VERIFY=PASS")
    print("SECRETS_PRINTED=false")

if __name__=="__main__":
    try:
        main()
    except (OSError,KeyError,TypeError,ReconcileError) as exc:
        code=str(exc) if isinstance(exc,ReconcileError) else type(exc).__name__
        raise SystemExit("CLIENT_SCOPE_PROVISION_FAILED:"+code)
