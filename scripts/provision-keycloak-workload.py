#!/usr/bin/env python3
"""Idempotent Keycloak provisioning for OUF workload clients.

The command operates through kcadm in the running Keycloak container.
It never prints client secrets or access tokens.

Modes:
  plan   - read-only comparison; exits non-zero only on malformed environment
  apply  - create/update client, bind required default scope, install exact mappers,
           and atomically write the client secret to the requested root-only file
  verify - read-only acceptance; exits non-zero on any drift
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile

KC = "/opt/keycloak/bin/kcadm.sh"

BASE_DEFAULT_SCOPES = {
    "web-origins", "service_account", "acr", "roles", "profile", "basic", "email",
}
BASE_OPTIONAL_SCOPES = {
    "address", "phone", "organization", "offline_access", "microprofile-jwt",
}


class ProvisioningError(RuntimeError):
    pass


def run(*args: str, input_text: str | None = None) -> str:
    result = subprocess.run(
        ["docker", "exec", "-i", "ouf-keycloak", KC, *args],
        input=input_text,
        text=True,
        capture_output=True,
    )
    if result.returncode:
        message = (result.stderr or result.stdout).strip()
        if "Session has expired" in message:
            raise ProvisioningError("KCADM_SESSION_EXPIRED")
        raise ProvisioningError("KCADM_COMMAND_FAILED")
    return result.stdout


def get_json(*args: str):
    raw = run(*args)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProvisioningError("KCADM_INVALID_JSON") from exc


def exact_client(realm: str, client_id: str):
    clients = get_json("get", "clients", "-r", realm, "--fields", "id,clientId")
    matches = [item for item in clients if item.get("clientId") == client_id]
    if len(matches) > 1:
        raise ProvisioningError("DUPLICATE_CLIENT_ID")
    return matches[0] if matches else None


def exact_scope(realm: str, scope_name: str):
    scopes = get_json("get", "client-scopes", "-r", realm)
    matches = [item for item in scopes if item.get("name") == scope_name]
    if len(matches) != 1:
        raise ProvisioningError("REQUIRED_SCOPE_NOT_UNIQUE")
    return matches[0]


def desired_mappers(audience: str, tenant: str) -> dict[str, dict]:
    return {
        "ouf-api-gateway-audience": {
            "name": "ouf-api-gateway-audience",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-audience-mapper",
            "consentRequired": False,
            "config": {
                "included.client.audience": audience,
                "id.token.claim": "false",
                "lightweight.claim": "false",
                "access.token.claim": "true",
                "introspection.token.claim": "true",
                "userinfo.token.claim": "false",
            },
        },
        "ouf-service-actor-type": {
            "name": "ouf-service-actor-type",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-hardcoded-claim-mapper",
            "consentRequired": False,
            "config": {
                "introspection.token.claim": "true",
                "claim.value": "SERVICE",
                "userinfo.token.claim": "false",
                "id.token.claim": "false",
                "lightweight.claim": "false",
                "access.token.claim": "true",
                "claim.name": "ouf_actor_type",
                "jsonType.label": "String",
                "access.tokenResponse.claim": "false",
            },
        },
        "ouf-lab-tenant": {
            "name": "ouf-lab-tenant",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-hardcoded-claim-mapper",
            "consentRequired": False,
            "config": {
                "introspection.token.claim": "true",
                "claim.value": tenant,
                "userinfo.token.claim": "false",
                "id.token.claim": "false",
                "lightweight.claim": "false",
                "access.token.claim": "true",
                "claim.name": "tenant_id",
                "jsonType.label": "String",
                "access.tokenResponse.claim": "false",
            },
        },
    }


def mapper_equivalent(actual: dict, wanted: dict) -> bool:
    if actual.get("protocolMapper") != wanted["protocolMapper"]:
        return False
    config = actual.get("config") or {}
    return all(config.get(k) == v for k, v in wanted["config"].items())


def inspect_state(realm: str, client_id: str, required_scope: str, audience: str, tenant: str) -> dict:
    client_ref = exact_client(realm, client_id)
    if not client_ref:
        return {"exists": False, "drift": ["CLIENT_MISSING"]}

    cid = client_ref["id"]
    client = get_json(
        "get", f"clients/{cid}", "-r", realm,
        "--fields",
        "clientId,enabled,protocol,publicClient,bearerOnly,serviceAccountsEnabled,"
        "standardFlowEnabled,directAccessGrantsEnabled,defaultClientScopes,optionalClientScopes"
    )
    drift: list[str] = []
    expected = {
        "clientId": client_id,
        "enabled": True,
        "protocol": "openid-connect",
        "publicClient": False,
        "bearerOnly": False,
        "serviceAccountsEnabled": True,
        "standardFlowEnabled": False,
        "directAccessGrantsEnabled": False,
    }
    for key, value in expected.items():
        if client.get(key) != value:
            drift.append("CLIENT_" + key.upper())

    defaults = set(client.get("defaultClientScopes") or [])
    optional = set(client.get("optionalClientScopes") or [])
    if required_scope not in defaults:
        drift.append("REQUIRED_SCOPE_NOT_DEFAULT")
    if not BASE_DEFAULT_SCOPES.issubset(defaults):
        drift.append("BASE_DEFAULT_SCOPES_MISSING")
    if not BASE_OPTIONAL_SCOPES.issubset(optional):
        drift.append("BASE_OPTIONAL_SCOPES_MISSING")

    actual_mappers = {
        m.get("name"): m
        for m in get_json("get", f"clients/{cid}/protocol-mappers/models", "-r", realm)
        if isinstance(m, dict) and m.get("name")
    }
    for name, wanted in desired_mappers(audience, tenant).items():
        actual = actual_mappers.get(name)
        if not actual:
            drift.append("MAPPER_MISSING:" + name)
        elif not mapper_equivalent(actual, wanted):
            drift.append("MAPPER_DRIFT:" + name)

    account = get_json("get", f"clients/{cid}/service-account-user", "-r", realm, "--fields", "username,enabled")
    if account.get("enabled") is not True:
        drift.append("SERVICE_ACCOUNT_DISABLED")

    return {
        "exists": True,
        "internalId": cid,
        "drift": drift,
        "defaultScopes": sorted(defaults),
        "optionalScopes": sorted(optional),
    }


def create_client(realm: str, client_id: str) -> str:
    cid = run(
        "create", "clients", "-r", realm, "-i",
        "-s", f"clientId={client_id}",
        "-s", "enabled=true",
        "-s", "protocol=openid-connect",
        "-s", "publicClient=false",
        "-s", "bearerOnly=false",
        "-s", "serviceAccountsEnabled=true",
        "-s", "standardFlowEnabled=false",
        "-s", "directAccessGrantsEnabled=false",
    ).strip()
    if not cid:
        raise ProvisioningError("CLIENT_CREATE_NO_ID")
    return cid


def ensure_client_flags(realm: str, cid: str) -> None:
    run(
        "update", f"clients/{cid}", "-r", realm,
        "-s", "enabled=true",
        "-s", "protocol=openid-connect",
        "-s", "publicClient=false",
        "-s", "bearerOnly=false",
        "-s", "serviceAccountsEnabled=true",
        "-s", "standardFlowEnabled=false",
        "-s", "directAccessGrantsEnabled=false",
    )


def ensure_default_scope(realm: str, cid: str, scope_id: str) -> None:
    client = get_json("get", f"clients/{cid}", "-r", realm, "--fields", "defaultClientScopes")
    names = set(client.get("defaultClientScopes") or [])
    scope = get_json("get", f"client-scopes/{scope_id}", "-r", realm, "--fields", "name")
    name = scope.get("name")
    if name not in names:
        run("update", f"clients/{cid}/default-client-scopes/{scope_id}", "-r", realm, "-n")


def ensure_mappers(realm: str, cid: str, audience: str, tenant: str) -> None:
    current = get_json("get", f"clients/{cid}/protocol-mappers/models", "-r", realm)
    by_name = {m.get("name"): m for m in current if isinstance(m, dict) and m.get("name")}
    for name, wanted in desired_mappers(audience, tenant).items():
        existing = by_name.get(name)
        payload = json.dumps(wanted, separators=(",", ":"))
        if existing is None:
            run("create", f"clients/{cid}/protocol-mappers/models", "-r", realm, "-f", "-", input_text=payload)
        elif not mapper_equivalent(existing, wanted):
            mid = existing.get("id")
            if not mid:
                raise ProvisioningError("MAPPER_WITHOUT_ID")
            run("update", f"clients/{cid}/protocol-mappers/models/{mid}", "-r", realm, "-f", "-", input_text=payload)


def write_secret(realm: str, cid: str, target: Path) -> None:
    response = get_json("get", f"clients/{cid}/client-secret", "-r", realm)
    secret = response.get("value")
    if not isinstance(secret, str) or not secret or len(secret) > 4096 or any(ch.isspace() for ch in secret):
        raise ProvisioningError("INVALID_CLIENT_SECRET")
    target.parent.mkdir(parents=True, exist_ok=True)
    parent = target.parent.stat()
    if parent.st_uid != 0 or stat.S_IMODE(parent.st_mode) & 0o022:
        raise ProvisioningError("SECRET_DIRECTORY_NOT_PRIVATE")
    fd, temporary = tempfile.mkstemp(prefix="." + target.name + "-", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            os.fchown(stream.fileno(), 0, 0)
            os.fchmod(stream.fileno(), 0o600)
            stream.write(secret)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)


def validate_args(a) -> None:
    for value, label in ((a.realm, "realm"), (a.client_id, "client-id"), (a.tenant, "tenant")):
        if not re.fullmatch(r"[A-Za-z0-9._:-]+", value):
            raise ProvisioningError("INVALID_" + label.upper().replace("-", "_"))
    if not re.fullmatch(r"[A-Za-z0-9._:-]+", a.audience):
        raise ProvisioningError("INVALID_AUDIENCE")
    if not re.fullmatch(r"[A-Za-z0-9._:-]+", a.required_scope):
        raise ProvisioningError("INVALID_SCOPE")
    if a.secret_output and (not a.secret_output.is_absolute()):
        raise ProvisioningError("SECRET_OUTPUT_MUST_BE_ABSOLUTE")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("plan", "apply", "verify"))
    p.add_argument("--realm", default="ouf")
    p.add_argument("--client-id", required=True)
    p.add_argument("--tenant", required=True)
    p.add_argument("--audience", required=True)
    p.add_argument("--required-scope", default="authorization.bundle.read")
    p.add_argument("--secret-output", type=Path)
    a = p.parse_args()

    try:
        validate_args(a)
        scope = exact_scope(a.realm, a.required_scope)
        before = inspect_state(a.realm, a.client_id, a.required_scope, a.audience, a.tenant)
        print("MODE=" + a.mode)
        print("CLIENT_ID=" + a.client_id)
        print("EXISTS=" + str(before["exists"]).lower())
        print("DRIFT=" + (",".join(before["drift"]) if before["drift"] else "NONE"))

        if a.mode == "plan":
            print("NO_CHANGES=true")
            return

        if a.mode == "apply":
            if os.geteuid() != 0:
                raise ProvisioningError("APPLY_REQUIRES_ROOT")
            client = exact_client(a.realm, a.client_id)
            cid = client["id"] if client else create_client(a.realm, a.client_id)
            ensure_client_flags(a.realm, cid)
            ensure_default_scope(a.realm, cid, scope["id"])
            ensure_mappers(a.realm, cid, a.audience, a.tenant)
            if a.secret_output:
                write_secret(a.realm, cid, a.secret_output)

        after = inspect_state(a.realm, a.client_id, a.required_scope, a.audience, a.tenant)
        if not after["exists"] or after["drift"]:
            raise ProvisioningError("VERIFY_DRIFT:" + ",".join(after["drift"]))
        if a.mode == "apply" and a.secret_output:
            st = a.secret_output.stat()
            if (st.st_uid, st.st_gid, stat.S_IMODE(st.st_mode)) != (0, 0, 0o600):
                raise ProvisioningError("SECRET_OUTPUT_METADATA_INVALID")
        print("VERIFY=PASS")
        print("SECRET_VALUE_PRINTED=false")
    except (OSError, KeyError, TypeError, ProvisioningError) as exc:
        code = str(exc) if isinstance(exc, ProvisioningError) else type(exc).__name__
        raise SystemExit("WORKLOAD_PROVISIONING_FAILED:" + code)


if __name__ == "__main__":
    main()
