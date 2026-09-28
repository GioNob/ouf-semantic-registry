#!/usr/bin/env python3
"""Read-only Keycloak inventory for R4a human and Onboarding service scopes."""

import json
import subprocess
from urllib.request import urlopen


KC = "/opt/keycloak/bin/kcadm.sh"
SCOPES = ("urban.identity.preflight", "ouf.udp.identity.attestation.read",
          "resolution.issue.read", "resolution.match.approve")
CLIENTS = ("ouf-human-admin", "ouf-source-onboarding")


def get(*args):
    result = subprocess.run(["docker", "exec", "-i", "ouf-keycloak", KC, "get", *args,
                             "-r", "ouf"], capture_output=True, text=True)
    if result.returncode:
        detail = (result.stderr + result.stdout).lower()
        reason = "SESSION_EXPIRED" if "session has expired" in detail else (
            "UNAUTHORIZED" if "unauthorized" in detail or "401" in detail else "COMMAND_FAILED")
        raise RuntimeError("KCADM_" + reason)
    return json.loads(result.stdout)


def exactly_one(rows, key, value):
    matches = [item for item in rows if isinstance(item, dict) and item.get(key) == value]
    if len(matches) > 1:
        raise RuntimeError("IAM_DUPLICATE_" + key.upper())
    return matches[0] if matches else None


def main():
    try:
        metadata = json.loads(urlopen(
            "https://auth.ouf-lab.it/realms/ouf/.well-known/openid-configuration", timeout=8).read())
        advertised = set(metadata.get("scopes_supported") or [])
        for scope in SCOPES:
            print("OIDC_SCOPE_ADVERTISED=" + scope + " PRESENT=" + str(scope in advertised).lower(), flush=True)
    except (OSError, ValueError):
        print("OIDC_SCOPE_DISCOVERY=UNAVAILABLE", flush=True)
    descriptor = json.loads(subprocess.run(["docker", "inspect", "ouf-keycloak"],
                                      capture_output=True, text=True, check=True).stdout)[0]
    names = {item.partition("=")[0] for item in descriptor["Config"].get("Env") or []}
    for name in ("KC_BOOTSTRAP_ADMIN_USERNAME", "KC_BOOTSTRAP_ADMIN_PASSWORD",
                 "KC_BOOTSTRAP_ADMIN_PASSWORD_FILE", "KEYCLOAK_ADMIN",
                 "KEYCLOAK_ADMIN_PASSWORD", "KEYCLOAK_ADMIN_PASSWORD_FILE"):
        print("KEYCLOAK_ENV_NAME=" + name + " PRESENT=" + str(name in names).lower(), flush=True)
    print("KEYCLOAK_MOUNT_DESTINATIONS=" + ",".join(sorted(
        item["Destination"] for item in descriptor.get("Mounts") or [])), flush=True)
    scopes = get("client-scopes")
    clients = get("clients", "--fields", "id,clientId")
    for scope in SCOPES:
        item = exactly_one(scopes, "name", scope)
        print("IAM_SCOPE=" + scope + " EXISTS=" + str(item is not None).lower())
    for name in CLIENTS:
        client = exactly_one(clients, "clientId", name)
        print("IAM_CLIENT=" + name + " EXISTS=" + str(client is not None).lower())
        if client is None:
            continue
        cid = client["id"]
        details = get("clients/" + cid, "--fields", "enabled,publicClient,serviceAccountsEnabled")
        defaults = {x.get("name") for x in get("clients/" + cid + "/default-client-scopes")}
        optionals = {x.get("name") for x in get("clients/" + cid + "/optional-client-scopes")}
        print("IAM_CLIENT=" + name + " ENABLED=" + str(details.get("enabled") is True).lower()
              + " SERVICE_ACCOUNTS=" + str(details.get("serviceAccountsEnabled") is True).lower())
        for scope in SCOPES:
            assignment = "DEFAULT" if scope in defaults else "OPTIONAL" if scope in optionals else "NONE"
            print("IAM_ASSIGNMENT=" + name + " SCOPE=" + scope + " KIND=" + assignment)
        if name == "ouf-source-onboarding":
            mappers = get("clients/" + cid + "/protocol-mappers/models")
            by_name = {item.get("name"): item for item in mappers if isinstance(item, dict)}
            expected = {"ouf-api-gateway-audience": ("included.client.audience", "ouf-api-gateway"),
                        "ouf-service-actor-type": ("claim.value", "SERVICE"),
                        "ouf-lab-tenant": ("claim.value", "ouf-lab")}
            for mapper, (key, value) in expected.items():
                actual = by_name.get(mapper) or {}
                print("IAM_MAPPER=" + mapper + " EXPECTED="
                      + str((actual.get("config") or {}).get(key) == value).lower())
    print("IAM_SCOPE_INVENTORY=READ_ONLY SECRET_VALUES_NOT_PRINTED=true")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        print("IAM_SCOPE_INVENTORY_BLOCKED=" + type(error).__name__ + ":" + str(error))
        raise SystemExit(1)
