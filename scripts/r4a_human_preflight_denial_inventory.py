#!/usr/bin/env python3
"""Read-only HUMAN preflight denial inventory; no token or full policy output."""

import argparse
import base64
from datetime import datetime, timezone
import ipaddress
import json
import os
import re
import subprocess
import types
from urllib.error import HTTPError
from urllib.request import Request, urlopen


CAPABILITY = "urban.identity.preflight"
URL = ("https://api.ouf-lab.it/api/udp/v1/governance/identity/preflight"
       "?id=00000000-0000-0000-0000-000000000000")


def probe(url, bearer):
    request = Request(url, headers={"Accept": "application/json",
                                    "Authorization": "Bearer " + bearer})
    try:
        with urlopen(request, timeout=15) as response:
            return response.status, response.headers.get("Content-Type", "UNKNOWN"), response.read(4096)
    except HTTPError as error:
        return error.code, error.headers.get("Content-Type", "UNKNOWN"), error.read(4096)


def summarize(label, result):
    status, media, body = result
    try:
        detail = json.loads(body)
    except ValueError:
        detail = {}
    owner = isinstance(detail, dict) and detail.get("detail") == "Owner authorization denied"
    keys = sorted(detail) if isinstance(detail, dict) else []
    print(label + "_HTTP=" + str(status) + " MEDIA=" +
          ("JSON" if "json" in media.lower() else "NON_JSON")
          + " OWNER_DENIAL_BODY=" + str(owner).lower()
          + " BODY_EMPTY=" + str(not body).lower()
          + " JSON_KEYS=" + json.dumps(keys))
    if isinstance(detail, dict):
        for key in ("error", "code", "error_code"):
            value = detail.get(key)
            if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", value):
                print(label + "_" + key.upper() + "=" + value)


def main(revision):
    if os.geteuid() != 0 or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise RuntimeError("ROOT_AND_PINNED_REVISION_REQUIRED")
    git = ["git", "-c", "safe.directory=/opt/ouf/semantic", "-C", "/opt/ouf/semantic"]
    if subprocess.check_output([*git, "rev-parse", revision + "^{commit}"],
                               stderr=subprocess.DEVNULL).decode().strip() != revision:
        raise RuntimeError("PINNED_REVISION_MISMATCH")
    source = subprocess.check_output([*git, "show", revision +
        ":scripts/r4a_cinema_semantic_draft.py"], stderr=subprocess.DEVNULL)
    helper = types.ModuleType("r4a_cinema_semantic_draft")
    exec(compile(source, "r4a_cinema_semantic_draft.py", "exec"), helper.__dict__)
    helper.SCOPES = {"urban.identity.preflight"}
    bearer, subject = helper.human_token()
    segment = bearer.split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))
    roles = claims.get("externalRoleRefs", claims.get("external_role_refs", []))
    if isinstance(roles, str):
        roles = [roles]
    if not isinstance(roles, list):
        raise RuntimeError("ROLE_CLAIM_SHAPE_UNEXPECTED")
    sql = ("select p.bundle_payload::text from ouf_authorization.active_policy_bundle a "
           "join ouf_authorization.policy_bundle p using (bundle_id,version)")
    raw = subprocess.run(["docker", "exec", "ouf-postgres", "psql", "-U",
        "ouf_onboarding", "-d", "ouf_onboarding", "-Atc", sql],
        capture_output=True, text=True, check=True, timeout=30).stdout.strip()
    bundle = json.loads(raw)
    bundle = bundle.get("bundle", bundle)
    descriptor = [x for x in bundle["capabilities"]
                  if x.get("capabilityId") == CAPABILITY]
    grants = [x for x in bundle["grants"] if x.get("capabilityId") == CAPABILITY]
    now = datetime.now(timezone.utc)
    print("R4A_HUMAN_PREFLIGHT_DENIAL=READ_ONLY")
    print("ACTIVE_POLICY_REF=" + str(bundle["bundleId"]) + ":" + str(bundle["version"]))
    print("DESCRIPTOR_COUNT=" + str(len(descriptor)))
    if len(descriptor) == 1:
        d = descriptor[0]
        print("DESCRIPTOR_SCOPE_AND_ACTOR=" + str(
            d.get("requiredScope") == CAPABILITY and "HUMAN" in d.get("allowedActors", [])
            and d.get("operation") == "COMMAND").lower())
    print("TOKEN_SCOPE_PRESENT=" + str(CAPABILITY in str(claims.get("scope", "")).split()).lower())
    print("TOKEN_ACTOR_HUMAN=" + str(claims.get("ouf_actor_type") in
          ("HUMAN", "HUMAN_USER")).lower())
    print("TOKEN_ACTOR_TYPE=" + str(claims.get("ouf_actor_type")))
    print("TOKEN_ROLE_REFS=" + json.dumps(sorted(roles)))
    print("POLICY_GRANT_COUNT=" + str(len(grants)))
    applicable = 0
    for grant in grants:
        constraints = grant.get("constraints") or {}
        role = constraints.get("externalRoleRef")
        start = datetime.fromisoformat(grant["validFrom"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(grant["validUntil"].replace("Z", "+00:00"))
        match = (grant.get("tenantId") == "ouf-lab"
            and (not grant.get("subjectId") or grant["subjectId"] == subject)
            and not grant.get("servicePrincipalId")
            and (not role or role in roles) and start <= now < end
            and constraints.get("effect", "ALLOW") == "ALLOW"
            and constraints.get("resourceType") in (None, "capability")
            and not constraints.get("resourceId")
            and not constraints.get("resourceAttributes")
            and constraints.get("requiredAcr") in (None, claims.get("acr"))
            and set(constraints.get("requiredAmr") or []) <=
                set(claims.get("amr") or [])
            and (constraints.get("maxAuthenticationAgeSeconds") is None
                or (isinstance(claims.get("auth_time"), int)
                    and 0 <= now.timestamp() - claims["auth_time"] <
                        constraints["maxAuthenticationAgeSeconds"])))
        applicable += bool(match)
        print("GRANT_ID=" + str(grant.get("grantId")) + " APPLICABLE="
              + str(match).lower() + " ROLE_REF=" + str(role or "NONE")
              + " EFFECT=" + str(constraints.get("effect", "ALLOW")))
    print("APPLICABLE_GRANT_COUNT=" + str(applicable))
    summarize("GATEWAY_READ_MISSING_ID", probe(URL, bearer))
    udp = json.loads(subprocess.run(["docker", "inspect", "ouf-udp"],
        capture_output=True, text=True, check=True, timeout=20).stdout)[0]
    ip = udp["NetworkSettings"]["Networks"]["ouf-backend"]["IPAddress"]
    address = ipaddress.ip_address(ip)
    if not address.is_private or address.version != 4 or not udp["State"]["Running"]:
        raise RuntimeError("PRIVATE_UDP_ADDRESS_INVALID")
    direct = "http://" + ip + ":8080" + URL.removeprefix("https://api.ouf-lab.it")
    try:
        summarize("DIRECT_UDP_READ_MISSING_ID", probe(direct, bearer))
    except OSError:
        print("DIRECT_UDP_READ_MISSING_ID=UNREACHABLE")
    print("TOKEN_POLICY_VALUES_NOT_PRINTED=true DB_UNCHANGED=true")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    try:
        main(args.revision)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError,
            RuntimeError) as error:
        detail = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_HUMAN_PREFLIGHT_INVENTORY_BLOCKED=" + detail +
              " TOKEN_NOT_PRINTED=true DB_UNCHANGED=true")
        raise SystemExit(1)
