#!/usr/bin/env python3
"""Read-only UDP policy refresh inventory without printing a bearer or policy bundle."""

import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import PurePosixPath
import subprocess
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


URL = "https://api.ouf-lab.it/internal/capabilities/v1/authorization/policy-bundle/active"


def run(*args):
    return subprocess.run(args, capture_output=True, check=True, timeout=25).stdout


def main():
    if os.geteuid() != 0:
        raise RuntimeError("ROOT_REQUIRED")
    container = json.loads(run("docker", "inspect", "ouf-udp"))[0]
    if not container["State"]["Running"]:
        raise RuntimeError("UDP_NOT_RUNNING")
    env = dict(entry.partition("=")[::2] for entry in container["Config"]["Env"])
    endpoint = env.get("OUF_AUTHORIZATION_REGISTRY_URL", "")
    token_path = env.get("OUF_AUTHORIZATION_REGISTRY_TOKEN_FILE", "")
    refresh = env.get("OUF_AUTHORIZATION_REFRESH_SECONDS", "")
    stale = env.get("OUF_AUTHORIZATION_MAX_STALENESS_SECONDS", "")
    path = PurePosixPath(token_path)
    print("R4A_UDP_AUTH_RUNTIME=READ_ONLY", flush=True)
    print("REGISTRY_URL_MATCH=" + str(endpoint == URL).lower(), flush=True)
    print("REFRESH_SECONDS=" + (refresh if refresh.isdecimal() else "UNSET"), flush=True)
    print("MAX_STALENESS_SECONDS=" + (stale if stale.isdecimal() else "UNSET"), flush=True)
    print("TOKEN_PATH_IN_AUTH_MOUNT=" + str(path.is_relative_to(
          PurePosixPath("/run/ouf-udp-auth")) and path != PurePosixPath("/run/ouf-udp-auth")).lower(),
          flush=True)
    if (endpoint != URL or path == PurePosixPath("/run/ouf-udp-auth")
        or not path.is_relative_to(PurePosixPath("/run/ouf-udp-auth"))):
        raise RuntimeError("REGISTRY_OR_TOKEN_PATH_UNEXPECTED")
    try:
        raw = run("docker", "exec", "ouf-udp", "cat", str(path)).decode().strip()
        stat = run("docker", "exec", "ouf-udp", "stat", "-c", "%Y", str(path)).decode().strip()
    except subprocess.SubprocessError:
        print("TOKEN_READ=FAILED SECRET_NOT_PRINTED=true", flush=True)
        return
    if not raw or len(raw) > 16384 or raw.count(".") != 2:
        print("TOKEN_FORMAT=INVALID SECRET_NOT_PRINTED=true", flush=True)
        return
    claims = json.loads(base64.urlsafe_b64decode(raw.split(".")[1] + "=" *
                       (-len(raw.split(".")[1]) % 4)))
    now = datetime.now(timezone.utc).timestamp()
    expires = claims.get("exp")
    print("TOKEN_AGE_SECONDS=" + str(max(0, int(now - int(stat)))), flush=True)
    print("TOKEN_EXPIRY_SECONDS=" + str(int(expires - now) if isinstance(expires, int)
                                        else "INVALID"), flush=True)
    print("TOKEN_SCOPE_BUNDLE_READ=" + str("authorization.bundle.read" in
          str(claims.get("scope", "")).split()).lower(), flush=True)
    print("TOKEN_ACTOR_SERVICE=" + str(claims.get("ouf_actor_type") == "SERVICE").lower(), flush=True)
    print("TOKEN_TENANT_MATCH=" + str(claims.get("tenant_id") == "ouf-lab").lower(), flush=True)
    if not isinstance(expires, int) or expires <= now or urlparse(endpoint).scheme != "https":
        print("REGISTRY_REQUEST_SKIPPED=TOKEN_EXPIRED_OR_ENDPOINT_INVALID", flush=True)
        return
    request = Request(endpoint, headers={"Authorization": "Bearer " + raw,
                                         "Accept": "application/json"})
    try:
        with urlopen(request, timeout=15) as response:
            status, body = response.status, response.read(6 * 1024 * 1024)
    except HTTPError as error:
        status, body = error.code, error.read(4096)
    except (OSError, URLError):
        print("REGISTRY_REQUEST=UNREACHABLE", flush=True)
        return
    print("REGISTRY_HTTP=" + str(status), flush=True)
    if status == 200:
        envelope = json.loads(body)
        print("REGISTRY_BUNDLE_ID=" + str(envelope.get("bundleId", "MISSING")), flush=True)
        print("REGISTRY_BUNDLE_VERSION=" + str(envelope.get("bundleVersion", "MISSING")), flush=True)
        print("REGISTRY_CONTENT_HASH_PRESENT=" + str(isinstance(envelope.get("contentHash"), str)
              and len(envelope["contentHash"]) == 64).lower(), flush=True)
        print("REGISTRY_BUNDLE_PRESENT=" + str(isinstance(envelope.get("bundle"), dict)).lower(),
              flush=True)
        if isinstance(envelope.get("bundle"), dict):
            compact = json.dumps(envelope["bundle"], separators=(",", ":"),
                                 ensure_ascii=False).encode()
            print("REGISTRY_COMPACT_HASH_MATCH=" + str(hashlib.sha256(compact).hexdigest()
                  == envelope.get("contentHash")).lower(), flush=True)
    print("SECRET_AND_POLICY_VALUES_NOT_PRINTED=true CONTAINERS_UNCHANGED=true", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (KeyError, ValueError, TypeError, UnicodeError, OSError,
            subprocess.SubprocessError, RuntimeError) as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_UDP_AUTH_INVENTORY_BLOCKED=" + code +
              " SECRET_NOT_PRINTED=true CONTAINERS_UNCHANGED=true", file=sys.stderr)
        raise SystemExit(1)
