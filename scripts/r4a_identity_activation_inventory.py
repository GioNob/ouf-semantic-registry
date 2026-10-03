#!/usr/bin/env python3
"""Read-only, secret-redacted inventory before the R4a identity activation."""

import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


NAMES = ("ouf-apisix", "ouf-onboarding", "ouf-ingestion", "ouf-udp")
ROUTES = ("ths-identity-preflight-create", "ths-identity-preflight-read",
          "onboarding-identity-preflight-read")
PROJECTION = Path("/opt/ouf/installation/active-projection.json")
ADMIN_KEY = Path("/opt/ouf/secrets/apisix-admin-key")


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def inspect(name):
    return json.loads(run("docker", "inspect", name))[0]


def report_container(name, descriptor):
    env = {item.partition("=")[0] for item in descriptor["Config"].get("Env") or []}
    mounts = {item["Destination"] for item in descriptor.get("Mounts") or []}
    networks = descriptor["NetworkSettings"].get("Networks") or {}
    print(name.upper().replace("-", "_") + "_RUNNING=" + str(descriptor["State"]["Running"]).lower())
    print(name.upper().replace("-", "_") + "_NETWORKS=" + ",".join(sorted(networks)))
    if name == "ouf-udp":
        for key in ("OUF_UDP_IAM_ENABLED", "OUF_UDP_IAM_ISSUER", "OUF_UDP_IAM_AUDIENCE"):
            print("UDP_" + key + "_PRESENT=" + str(key in env).lower())
        aliases = set(networks.get("ouf-backend", {}).get("Aliases") or [])
        print("UDP_DNS_ALIAS_OUF_UDP=" + str("ouf-udp" in aliases).lower())
    if name == "ouf-onboarding":
        for key in ("OUF_ONB_UDP_IDENTITY_GATEWAY_URL", "OUF_ONB_UDP_IDENTITY_TOKEN_FILE"):
            print("ONBOARDING_" + key + "_PRESENT=" + str(key in env).lower())
        print("ONBOARDING_MOUNT_DESTINATIONS=" + ",".join(sorted(mounts)))
    if name == "ouf-apisix":
        print("APISIX_OIDC_ENV_PRESENT=" + str("OUF_GATEWAY_OIDC_CLIENT_SECRET" in env).lower())
        nginx = run("docker", "exec", name, "cat", "/usr/local/apisix/conf/nginx.conf")
        inherited = bool(re.search(r"^\s*env\s+\"?OUF_GATEWAY_OIDC_CLIENT_SECRET\"?\s*;", nginx, re.M))
        print("APISIX_OIDC_NGINX_INHERITED=" + str(inherited).lower())


def admin_routes(pid):
    if not ADMIN_KEY.is_file():
        print("APISIX_ADMIN_KEY_FILE_PRESENT=false")
        return
    print("APISIX_ADMIN_KEY_FILE_PRESENT=true")
    # Namespace selection keeps the Admin API private. The credential stays in the file.
    command = ["nsenter", "-t", str(pid), "-n", sys.executable,
               str(Path(__file__).resolve()), "--inside"]
    print(run(*command).strip())


def inside():
    key = ADMIN_KEY.read_text().strip()
    if not key or "\n" in key or "\r" in key:
        raise ValueError("ADMIN_KEY_INVALID")
    for route in ROUTES:
        req = Request("http://127.0.0.1:9180/apisix/admin/routes/" + route,
                      headers={"X-API-KEY": key})
        try:
            with urlopen(req, timeout=8) as response:
                code = response.status
        except HTTPError as error:
            code = error.code
        print("APISIX_ROUTE_" + route.upper().replace("-", "_") + "_HTTP=" + str(code))


def main():
    if sys.argv[1:] == ["--inside"]:
        inside()
        return
    if sys.argv[1:]:
        raise ValueError("UNEXPECTED_ARGUMENT")
    print("R4A_IDENTITY_ACTIVATION_INVENTORY=READ_ONLY")
    print("PROJECTION_PRESENT=" + str(PROJECTION.is_file()).lower())
    if PROJECTION.is_file():
        projection = json.loads(PROJECTION.read_text())
        print("PROJECTION_INSTALLATION=" + str(projection.get("installationId", "MISSING")))
        print("PROJECTION_AUDIENCE=" + str(projection.get("gateway", {}).get("requiredAudience", "MISSING")))
    for name in NAMES:
        descriptor = inspect(name)
        report_container(name, descriptor)
        if name == "ouf-apisix":
            admin_routes(descriptor["State"]["Pid"])
    manifest = Path("/opt/ouf/r4a-stage/identity-images.json")
    print("STAGING_MANIFEST_PRESENT=" + str(manifest.is_file()).lower())
    if manifest.is_file():
        data = json.loads(manifest.read_text())
        for module, item in sorted(data.get("modules", {}).items()):
            live = inspect("ouf-" + module)["Image"]
            print("STAGED_" + module.upper() + "_COMMIT=" + str(item.get("commit", "MISSING")))
            print("STAGED_" + module.upper() + "_DIFFERS_FROM_LIVE="
                  + str(item.get("image_id") != live).lower())
    print("SECRET_VALUES_NOT_PRINTED=true LIVE_CONTAINERS_UNCHANGED=true")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, IndexError, subprocess.CalledProcessError,
            URLError, json.JSONDecodeError) as error:
        print("R4A_INVENTORY_BLOCKED=" + type(error).__name__, file=sys.stderr)
        raise SystemExit(1)
