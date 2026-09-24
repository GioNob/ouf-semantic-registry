#!/usr/bin/env python3
"""Reconcile exact OUF Keycloak client scopes. Never creates users or credentials.

plan: validate the desired state offline; check: read Keycloak; apply: create
missing scopes and bind them as defaults to existing clients. No deletions.
"""
import argparse
import json
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

NAME = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,127}$")


def validate(desired):
    if not isinstance(desired, dict) or set(desired) != {"issuer", "clients"}:
        raise ValueError("expected issuer and clients only")
    if not isinstance(desired["issuer"], str):
        raise ValueError("issuer must be a string")
    url = urlsplit(desired["issuer"])
    if url.scheme != "https" or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ValueError("issuer must be an HTTPS realm URL")
    m = re.fullmatch(r"/realms/([a-zA-Z0-9._-]+)", url.path)
    if not m or not isinstance(desired["clients"], dict) or not desired["clients"]:
        raise ValueError("expected /realms/<realm> and a nonempty clients map")
    scopes = set()
    for client, names in desired["clients"].items():
        if not isinstance(client, str) or not NAME.fullmatch(client):
            raise ValueError("invalid client ID")
        if not isinstance(names, list) or not names or not all(
                isinstance(n, str) and NAME.fullmatch(n) for n in names):
            raise ValueError(f"{client}: invalid scope name")
        if len(names) != len(set(names)):
            raise ValueError(f"{client}: default scopes must be unique")
        scopes.update(names)
    return f"{url.scheme}://{url.netloc}/admin/realms/{m.group(1)}", sorted(scopes)


class Admin:
    def __init__(self, base, token):
        self.base = base
        self.token = token

    def request(self, method, path, body=None):
        data = None if body is None else json.dumps(body, separators=(",", ":")).encode()
        request = Request(self.base + path, data=data, method=method, headers={
            "Authorization": "Bearer " + self.token,
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        try:
            with urlopen(request, timeout=15) as response:
                raw = response.read(2_000_000)
                return (json.loads(raw) if raw else None), response.headers
        except HTTPError as error:
            raise RuntimeError(f"Keycloak {method} {path.split('?')[0]} returned HTTP {error.code}") from None
        except URLError:
            raise RuntimeError("Keycloak is unreachable or its TLS certificate was rejected") from None


def exact(items, field, value):
    found = [item for item in items if isinstance(item, dict) and item.get(field) == value]
    if len(found) > 1:
        raise RuntimeError(f"ambiguous Keycloak {field}: {value}")
    return found[0] if found else None


def reconcile(admin, desired, scopes, apply):
    # Read every client and scope before the first write. Keycloak may return
    # unfiltered lists for ?name=; always compare the complete name ourselves.
    clients = admin.request("GET", "/clients")[0]
    existing = admin.request("GET", "/client-scopes")[0]
    if not isinstance(clients, list) or not isinstance(existing, list):
        raise RuntimeError("invalid Keycloak clients/client-scopes response")
    ids = {}
    for name in desired["clients"]:
        client = exact(clients, "clientId", name)
        if client is None or not isinstance(client.get("id"), str):
            raise RuntimeError(f"existing client required: {name}")
        ids[name] = client["id"]
    scope_ids = {}
    drift = False
    for scope in scopes:
        item = exact(existing, "name", scope)
        if item is not None:
            if item.get("protocol") != "openid-connect" or not isinstance(item.get("id"), str):
                raise RuntimeError(f"incompatible existing scope: {scope}")
            scope_ids[scope] = item["id"]
        else:
            drift = True
            print(f"CREATE scope {scope}" if apply else f"MISSING scope {scope}")
            if apply:
                _, headers = admin.request("POST", "/client-scopes", {
                    "name": scope, "protocol": "openid-connect", "attributes": {
                        "include.in.token.scope": "true",
                        "display.on.consent.screen": "true",
                    },
                })
                location = headers.get("Location", "")
                scope_id = location.rsplit("/", 1)[-1]
                if not re.fullmatch(r"[0-9a-fA-F-]{36}", scope_id):
                    raise RuntimeError(f"scope {scope}: missing canonical ID from create response")
                created = admin.request("GET", "/client-scopes/" + quote(scope_id))[0]
                if not isinstance(created, dict) or created.get("name") != scope or created.get("id") != scope_id:
                    raise RuntimeError(f"scope {scope}: create readback disagrees")
                scope_ids[scope] = scope_id
    for name, wanted in desired["clients"].items():
        current = admin.request("GET", "/clients/" + quote(ids[name]) + "/default-client-scopes")[0]
        if not isinstance(current, list):
            raise RuntimeError(f"{name}: invalid default scopes response")
        assigned = {item.get("id") for item in current if isinstance(item, dict)}
        for scope in wanted:
            if scope not in scope_ids:
                drift = True
                print(f"MISSING binding {name} -> {scope}")
            elif scope_ids[scope] not in assigned:
                drift = True
                print(f"BIND default {name} -> {scope}" if apply else f"MISSING binding {name} -> {scope}")
                if apply:
                    path = "/clients/" + quote(ids[name]) + "/default-client-scopes/" + quote(scope_ids[scope])
                    admin.request("PUT", path)
                    after = admin.request("GET", "/clients/" + quote(ids[name]) + "/default-client-scopes")[0]
                    if scope_ids[scope] not in {item.get("id") for item in after}:
                        raise RuntimeError(f"{name}: scope {scope} failed readback")
    return drift


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--desired", required=True, type=Path)
    p.add_argument("--mode", choices=["plan", "check", "apply"], default="plan")
    p.add_argument("--token-file", type=Path)
    args = p.parse_args()
    try:
        desired = json.loads(args.desired.read_text(encoding="utf-8"))
        base, scopes = validate(desired)
        if args.mode == "plan":
            for client, names in desired["clients"].items():
                print(f"{client}: {', '.join(names)}")
            print("PLAN_ONLY: no Keycloak access")
            return 0
        if args.token_file is None or args.token_file.stat().st_mode & 0o077:
            raise ValueError("admin token file must exist and be private (mode 0600)")
        token = args.token_file.read_text(encoding="utf-8").strip()
        if not token or "\n" in token:
            raise ValueError("admin token file must contain exactly one token")
        drift = reconcile(Admin(base, token), desired, scopes, args.mode == "apply")
        if drift and args.mode == "check":
            print("KEYCLOAK_SCOPE_DRIFT", file=sys.stderr)
            return 1
        print("KEYCLOAK_SCOPE_RECONCILIATION_PASS")
        return 0
    except (ValueError, RuntimeError, OSError, json.JSONDecodeError) as error:
        print(f"KEYCLOAK_SCOPE_RECONCILIATION_BLOCKED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
