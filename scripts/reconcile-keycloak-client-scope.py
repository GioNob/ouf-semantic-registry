#!/usr/bin/env python3
"""Idempotently reconcile one Keycloak client-scope assignment.

Supports plan/apply/verify and exact DEFAULT or OPTIONAL assignment. It never
prints credentials, tokens, client secrets, or scope internals beyond names.
The caller must already have an authenticated kcadm session.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess

KC="/opt/keycloak/bin/kcadm.sh"


class ReconcileError(RuntimeError):
    pass


def run(*args:str)->str:
    p=subprocess.run(
        ["docker","exec","-i","ouf-keycloak",KC,*args],
        text=True,capture_output=True
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


def exact_client(realm:str,client_id:str)->dict:
    rows=get_json("get","clients","-r",realm,"--fields","id,clientId")
    matches=[x for x in rows if x.get("clientId")==client_id]
    if len(matches)!=1:
        raise ReconcileError("CLIENT_NOT_UNIQUE")
    return matches[0]


def exact_scope(realm:str,scope_name:str)->dict:
    rows=get_json("get","client-scopes","-r",realm)
    matches=[x for x in rows if x.get("name")==scope_name]
    if len(matches)!=1:
        raise ReconcileError("SCOPE_NOT_UNIQUE")
    return matches[0]


def assignment_names(realm:str,cid:str,kind:str)->set[str]:
    endpoint=f"clients/{cid}/{kind}-client-scopes"
    rows=get_json("get",endpoint,"-r",realm)
    return {x.get("name") for x in rows if isinstance(x,dict) and x.get("name")}


def inspect_state(realm:str,client_id:str,scope_name:str)->dict:
    client=exact_client(realm,client_id)
    exact_scope(realm,scope_name)
    defaults=assignment_names(realm,client["id"],"default")
    optionals=assignment_names(realm,client["id"],"optional")
    return {
        "clientInternalId":client["id"],
        "default":scope_name in defaults,
        "optional":scope_name in optionals,
    }


def assign(realm:str,cid:str,scope_id:str,kind:str)->None:
    run("update",f"clients/{cid}/{kind}-client-scopes/{scope_id}","-r",realm,"-n")


def remove(realm:str,cid:str,scope_id:str,kind:str)->None:
    run("delete",f"clients/{cid}/{kind}-client-scopes/{scope_id}","-r",realm)


def validate_name(value:str,label:str)->None:
    if not re.fullmatch(r"[A-Za-z0-9._:-]+",value):
        raise ReconcileError("INVALID_"+label)


def main()->None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("plan","apply","verify"))
    p.add_argument("--realm",default="ouf")
    p.add_argument("--client-id",required=True)
    p.add_argument("--scope",required=True)
    p.add_argument("--assignment",choices=("default","optional"),required=True)
    a=p.parse_args()

    validate_name(a.realm,"REALM")
    validate_name(a.client_id,"CLIENT_ID")
    validate_name(a.scope,"SCOPE")

    scope=exact_scope(a.realm,a.scope)
    before=inspect_state(a.realm,a.client_id,a.scope)
    wanted_default=a.assignment=="default"
    wanted_optional=a.assignment=="optional"
    drift=(before["default"]!=wanted_default or before["optional"]!=wanted_optional)

    print("MODE="+a.mode)
    print("CLIENT_ID="+a.client_id)
    print("SCOPE="+a.scope)
    print("ASSIGNMENT="+a.assignment.upper())
    print("CURRENT_DEFAULT="+str(before["default"]).lower())
    print("CURRENT_OPTIONAL="+str(before["optional"]).lower())
    print("DRIFT="+str(drift).lower())

    if a.mode=="plan":
        print("NO_CHANGES=true")
        return

    if a.mode=="apply" and drift:
        cid=before["clientInternalId"]
        if before["default"] and not wanted_default:
            remove(a.realm,cid,scope["id"],"default")
        if before["optional"] and not wanted_optional:
            remove(a.realm,cid,scope["id"],"optional")
        if wanted_default and not before["default"]:
            assign(a.realm,cid,scope["id"],"default")
        if wanted_optional and not before["optional"]:
            assign(a.realm,cid,scope["id"],"optional")

    after=inspect_state(a.realm,a.client_id,a.scope)
    if after["default"]!=wanted_default or after["optional"]!=wanted_optional:
        raise ReconcileError("VERIFY_DRIFT")
    print("VERIFY=PASS")
    print("SECRETS_PRINTED=false")


if __name__=="__main__":
    try:main()
    except (OSError,KeyError,TypeError,ReconcileError) as exc:
        code=str(exc) if isinstance(exc,ReconcileError) else type(exc).__name__
        raise SystemExit("CLIENT_SCOPE_RECONCILE_FAILED:"+code)
