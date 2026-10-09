#!/usr/bin/env python3
"""Check the Onboarding SERVICE token and guarded Gateway route without logging it."""

import base64
import json
from pathlib import Path
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import build_opener, HTTPRedirectHandler, Request


ISSUER = "https://auth.ouf-lab.it/realms/ouf"
SECRET = Path("/var/lib/ouf-r4a-identity/onboarding-client-secret")
CLIENT = "ouf-source-onboarding"
SCOPE = "ouf.udp.identity.attestation.read"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


HTTP = build_opener(NoRedirect())


def token():
    secret = SECRET.read_text().strip()
    if not secret or len(secret) > 4096 or any(x.isspace() for x in secret):
        raise ValueError("SERVICE_SECRET_INVALID")
    basic = base64.b64encode((CLIENT + ":" + secret).encode()).decode()
    data = urlencode({"grant_type": "client_credentials"}).encode()
    req = Request(ISSUER + "/protocol/openid-connect/token", data=data,
                  headers={"Authorization": "Basic " + basic,
                           "Content-Type": "application/x-www-form-urlencoded"})
    with HTTP.open(req, timeout=12) as response:
        payload = json.load(response)
    value = payload.get("access_token")
    if payload.get("token_type", "").lower() != "bearer" or not isinstance(value, str) \
            or len(value) > 65536 or value.count(".") != 2:
        raise ValueError("SERVICE_TOKEN_INVALID")
    return value


def check_claims(value):
    middle = value.split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(middle + "=" * (-len(middle) % 4)))
    audience = claims.get("aud")
    audiences = {audience} if isinstance(audience, str) else set(audience or [])
    expected = {
        "issuer": claims.get("iss") == ISSUER,
        "audience": "ouf-api-gateway" in audiences,
        "scope": SCOPE in str(claims.get("scope", "")).split(),
        "actor": claims.get("ouf_actor_type") == "SERVICE",
        "tenant": claims.get("tenant_id") == "ouf-lab",
        "service": (claims.get("client_id") or claims.get("azp")) == CLIENT,
        "subject": isinstance(claims.get("sub"), str) and bool(claims["sub"]),
        "acr": bool(claims.get("acr")),
        "expiry": isinstance(claims.get("exp"), int) and claims["exp"] > time.time() + 30,
    }
    for name, passed in expected.items():
        print("SERVICE_CLAIM_" + name.upper() + "=" + ("PASS" if passed else "FAIL"), flush=True)
    if not all(expected.values()):
        raise ValueError("SERVICE_CLAIMS_INCOMPLETE")


def gateway(value):
    url = "https://api.ouf-lab.it/api/udp/v1/governance/internal/identity/preflight?" + urlencode(
        {"sourceId": "r4a-probe"})
    # Missing configurationHash is rejected by the owner request binding
    # after Gateway and UDP bearer authentication. This does not fabricate
    # or depend on an attestation that has not been prepared by a HUMAN.
    def status(headers):
        try:
            with HTTP.open(Request(url, headers=headers), timeout=12) as response:
                return response.status
        except HTTPError as error:
            return error.code
    anonymous = status({})
    authenticated = status({"Authorization": "Bearer " + value})
    print("SERVICE_GATEWAY_ANONYMOUS_HTTP=" + str(anonymous))
    print("SERVICE_GATEWAY_AUTHENTICATED_HTTP=" + str(authenticated))
    if anonymous != 401 or authenticated != 400:
        raise ValueError("SERVICE_GATEWAY_AUTH_PATH_UNVERIFIED")
    print("SERVICE_GATEWAY_AUTH_PATH=PASS ATTESTATION_READ_PENDING=true")


def main():
    value = token()
    check_claims(value)
    gateway(value)
    print("R4A_SERVICE_TOKEN_SMOKE=PASS TOKEN_PRINTED=false TOKEN_PERSISTED=false")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        print("R4A_SERVICE_TOKEN_SMOKE_BLOCKED=" + type(error).__name__ + ":" + str(error))
        raise SystemExit(1)
