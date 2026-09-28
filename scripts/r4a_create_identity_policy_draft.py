#!/usr/bin/env python3
"""Register R4a identity descriptors and create a draft through HUMAN admin API.

Interactive IAM Device Flow keeps the bearer in memory. Never publishes ACTIVE.
The API is reached only through the private Docker bridge from the VPS host.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler


PINNED = "ouf-lab-authorization:28"
ISSUER = "https://auth.ouf-lab.it/realms/ouf"
CAPS = {
    "urban.identity.preflight": ("COMMAND", "HUMAN"),
    "ouf.udp.identity.attestation.read": ("READ", "SERVICE"),
    "resolution.issue.read": ("READ", "HUMAN"),
    "resolution.match.approve": ("COMMAND", "HUMAN"),
}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise RuntimeError("UNEXPECTED_HTTP_REDIRECT")


OPENER = build_opener(NoRedirect)


def http(url, method="GET", payload=None, token=None, form=False, extra_headers=None):
    headers = {"Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded" if form else "application/json"
        payload = urlencode(payload).encode() if form else json.dumps(payload).encode()
    if token:
        headers["Authorization"] = "Bearer " + token
    if extra_headers:
        headers.update(extra_headers)
    request = Request(url, data=payload, method=method, headers=headers)
    try:
        with OPENER.open(request, timeout=12) as response:
            body = response.read()
            return response.status, json.loads(body) if body else None
    except HTTPError as error:
        body = error.read(4096)
        try:
            detail = json.loads(body)
        except ValueError:
            detail = {"code": "HTTP_ERROR"}
        return error.code, detail


def docker(*args):
    return subprocess.check_output(["sudo", "docker", *args], text=True, timeout=15).strip()


def active_ref():
    sql = "select bundle_id||':'||version from ouf_authorization.active_policy_bundle"
    return docker("exec", "-i", "ouf-postgres", "psql", "-X", "-qAt", "-v", "ON_ERROR_STOP=1",
                  "-U", "ouf_onboarding", "-d", "ouf_onboarding", "-c", sql)


def private_owner():
    address = docker("inspect", "-f", '{{(index .NetworkSettings.Networks "ouf-backend").IPAddress}}', "ouf-onboarding")
    if not address or not all(part.isdigit() and 0 <= int(part) <= 255 for part in address.split(".")) or len(address.split(".")) != 4:
        raise RuntimeError("PRIVATE_ONBOARDING_ADDRESS_UNAVAILABLE")
    return "http://" + address + ":8080/api/trusted-human/v1/authorization"


def expected(cap, operation, actor):
    return {"capabilityId": cap, "operation": operation, "requiredScope": cap, "allowedActors": [actor]}


def validate(base, draft, registrations):
    if base.get("bundleId") != "ouf-lab-authorization" or base.get("version") != 28:
        raise RuntimeError("BASE_POLICY_CHANGED")
    if draft.get("bundleId") != base["bundleId"] or draft.get("version") != 29:
        raise RuntimeError("DRAFT_VERSION_INVALID")
    if draft["capabilities"][:len(base["capabilities"])] != base["capabilities"]:
        raise RuntimeError("EXISTING_CAPABILITIES_CHANGED")
    if draft["grants"][:len(base["grants"])] != base["grants"]:
        raise RuntimeError("EXISTING_GRANTS_CHANGED")
    additions = draft["capabilities"][len(base["capabilities"]):]
    if {item["capabilityId"]: item for item in additions} != {
        cap: expected(cap, operation, actor) for cap, (operation, actor) in CAPS.items()
    } or len(additions) != 4:
        raise RuntimeError("IDENTITY_DESCRIPTORS_INVALID")
    if len(registrations) != 4 or {item.get("descriptor", {}).get("capabilityId") for item in registrations} != set(CAPS):
        raise RuntimeError("REGISTRATION_SET_INVALID")
    for item in registrations:
        cap = item["descriptor"]["capabilityId"]
        if item.get("ownerRef") != "udp" or item["descriptor"] != expected(cap, *CAPS[cap]):
            raise RuntimeError("REGISTRATION_DESCRIPTOR_INVALID")
    added_grants = draft["grants"][len(base["grants"]):]
    if len(added_grants) != 1:
        raise RuntimeError("SERVICE_GRANT_COUNT_INVALID")
    grant = added_grants[0]
    if any(grant.get(key) != value for key, value in {
        "grantId": "grant-r4a-identity-attestation-onboarding",
        "capabilityId": "ouf.udp.identity.attestation.read", "tenantId": "ouf-lab",
        "servicePrincipalId": "ouf-source-onboarding", "subjectId": None,
        "organizationId": None}.items()):
        raise RuntimeError("SERVICE_GRANT_INVALID")
    until = datetime.fromisoformat(grant["validUntil"].replace("Z", "+00:00"))
    if until <= datetime.now(timezone.utc):
        raise RuntimeError("SERVICE_GRANT_EXPIRED")


def human_token():
    status, discovery = http(ISSUER + "/.well-known/openid-configuration")
    if status != 200 or discovery.get("issuer") != ISSUER:
        raise RuntimeError("IAM_DISCOVERY_MISMATCH")
    device_url = discovery.get("device_authorization_endpoint", "")
    token_url = discovery.get("token_endpoint", "")
    if not device_url.startswith(ISSUER + "/") or not token_url.startswith(ISSUER + "/"):
        raise RuntimeError("IAM_ENDPOINT_MISMATCH")
    status, challenge = http(device_url, "POST", {"client_id": "ouf-human-admin", "scope": "openid authorization.policy.admin"}, form=True)
    if status != 200 or not challenge.get("device_code") or not challenge.get("user_code"):
        raise RuntimeError("IAM_DEVICE_AUTHORIZATION_FAILED:" + str(status))
    print("Apri nel tuo browser: " + challenge.get("verification_uri_complete", challenge["verification_uri"]), flush=True)
    print("Codice da verificare: " + challenge["user_code"], flush=True)
    print("In attesa della tua autenticazione IAM...", flush=True)
    interval = max(5, int(challenge.get("interval", 5)))
    deadline = time.monotonic() + min(600, int(challenge.get("expires_in", 300)))
    while time.monotonic() + interval < deadline:
        time.sleep(interval)
        status, result = http(token_url, "POST", {"client_id": "ouf-human-admin", "device_code": challenge["device_code"],
                                               "grant_type": "urn:ietf:params:oauth:grant-type:device_code"}, form=True)
        if status == 200 and result.get("token_type", "").lower() == "bearer" and result.get("access_token"):
            return result["access_token"]
        code = (result or {}).get("error")
        if code == "authorization_pending":
            continue
        if code == "slow_down":
            interval += 5
            continue
        raise RuntimeError("IAM_DEVICE_FLOW_STOPPED:" + str(code or status))
    raise RuntimeError("IAM_DEVICE_FLOW_EXPIRED")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", type=Path, required=True)
    parser.add_argument("--active", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="Authenticate HUMAN, register descriptors and create DRAFT; never publish")
    args = parser.parse_args()
    raw = json.loads(args.active.read_text())
    base = raw.get("bundle", raw)
    draft = json.loads((args.review_dir / "policy-draft.json").read_text())
    registrations = json.loads((args.review_dir / "capability-registrations.json").read_text())
    validate(base, draft, registrations)
    if active_ref() != PINNED:
        raise RuntimeError("ACTIVE_CHANGED_REGENERATE_DRAFT")
    print("R4A_POLICY_REVIEW_PASS=base:28 next:29 descriptors:4 service_grants:1 human_grants:0", flush=True)
    if not args.apply:
        return
    owner = private_owner()
    status, _ = http(owner + "/capabilities")
    if status != 401:
        raise RuntimeError("ADMIN_PRIVATE_AUTH_BOUNDARY_UNEXPECTED:" + str(status))
    token = human_token()
    status, catalogue = http(owner + "/capabilities?limit=200", token=token)
    if status != 200 or not isinstance(catalogue, list):
        raise RuntimeError("ADMIN_AUTHENTICATION_OR_AUTHORIZATION_FAILED:" + str(status))
    present = {item.get("capability_id") for item in catalogue}
    if present.intersection(CAPS):
        raise RuntimeError("DESCRIPTOR_REGISTERED_SINCE_EXPORT_REVIEW_AGAIN")
    if active_ref() != PINNED:
        raise RuntimeError("ACTIVE_CHANGED_REGENERATE_DRAFT")
    for item in registrations:
        status, _ = http(owner + "/capabilities", "POST", item, token)
        if status != 201:
            raise RuntimeError("DESCRIPTOR_REGISTRATION_FAILED:" + item["descriptor"]["capabilityId"] + ":" + str(status))
        print("R4A_DESCRIPTOR_REGISTERED=" + item["descriptor"]["capabilityId"], flush=True)
    if active_ref() != PINNED:
        raise RuntimeError("ACTIVE_CHANGED_REGENERATE_DRAFT")
    status, response = http(owner + "/policies", "POST", draft, token)
    if status != 200 or not isinstance(response, dict) or response.get("state") != "DRAFT" or response.get("baseActiveRef") != PINNED:
        raise RuntimeError("POLICY_DRAFT_CREATION_FAILED:" + str(status))
    print("R4A_POLICY_DRAFT_CREATED=" + response["id"] + " REVISION=" + str(response["revision"]) +
          " ACTIVE_UNCHANGED=true PUBLICATION_REQUIRES_SEPARATE_HUMAN_ACTION=true", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError, URLError, subprocess.CalledProcessError) as error:
        print("R4A_POLICY_ADMIN_BLOCKED=" + str(error), file=sys.stderr)
        sys.exit(1)
