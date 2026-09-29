#!/usr/bin/env python3
"""Read the effective SDK decision in an isolated diagnostic UDP clone."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import types
from urllib.error import HTTPError
from urllib.request import Request, ProxyHandler, build_opener


PIN = "30d9682080202f43343f64e957e5b3ef2575e118"
REPO = Path("/opt/ouf/semantic")


def load(name):
    git = ["git", "-c", "safe.directory=" + str(REPO), "-C", str(REPO)]
    if subprocess.check_output([*git, "rev-parse", PIN + "^{commit}"],
                               stderr=subprocess.DEVNULL).decode().strip() != PIN:
        raise RuntimeError("PINNED_REVISION_MISSING")
    source = subprocess.check_output([*git, "show", PIN + ":scripts/" + name],
                                     stderr=subprocess.DEVNULL)
    module = types.ModuleType(name.removesuffix(".py"))
    exec(compile(source, name, "exec"), module.__dict__)
    return module


def main():
    if os.geteuid() != 0:
        raise RuntimeError("ROOT_REQUIRED")
    clone = load("r4a_probe_udp_authorization_reason.py")
    human = load("r4a_cinema_semantic_draft.py")
    human.SCOPES = {"urban.identity.preflight"}
    clone.MANIFEST = Path("/opt/ouf/r4a-stage/udp-auth-diagnostic-image.json")
    clone.EXPECTED_PROBE = "fb31d7f851a79f16405a2fd4a14995014217ff37"
    clone.EXTRA_ENV = {"OUF_UDP_AUTHORIZATION_DIAGNOSTIC_ENABLED": "true"}
    service_probe = clone.probe_request

    def inspect(ip, token):
        service_probe(ip, token)
        bearer, _ = human.human_token()
        url = "http://" + ip + ":8080/api/internal/v1/udp/authorization/diagnostic"
        request = Request(url, headers={"Accept": "application/json",
                                        "Authorization": "Bearer " + bearer})
        opener = build_opener(ProxyHandler({}))
        try:
            with opener.open(request, timeout=20) as response:
                status, raw = response.status, response.read(4096)
        except HTTPError as error:
            status, raw = error.code, error.read(4096)
        print("R4A_EFFECTIVE_DECISION_HTTP=" + str(status), flush=True)
        try:
            result = json.loads(raw)
        except ValueError:
            result = {}
        if status != 200 or not isinstance(result, dict):
            print("R4A_EFFECTIVE_DECISION_KEYS=" + json.dumps(sorted(result)
                  if isinstance(result, dict) else []), flush=True)
            raise RuntimeError("ISOLATED_DIAGNOSTIC_NOT_AVAILABLE")
        expected = {"bundleId", "bundleVersion", "bundleReady", "lastRefreshError",
                    "actorType", "scopePresent", "grantCount", "subjectMatchCount",
                    "decisionCode", "allowed"}
        if set(result) != expected:
            raise RuntimeError("DIAGNOSTIC_RESPONSE_SHAPE_CHANGED")
        for key in sorted(expected):
            value = result[key]
            if key in {"bundleId", "lastRefreshError", "actorType", "decisionCode"}:
                if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,100}", value):
                    raise RuntimeError("DIAGNOSTIC_VALUE_INVALID")
            elif key in {"bundleVersion", "grantCount", "subjectMatchCount"}:
                if not isinstance(value, int) or isinstance(value, bool):
                    raise RuntimeError("DIAGNOSTIC_VALUE_INVALID")
            elif not isinstance(value, bool):
                raise RuntimeError("DIAGNOSTIC_VALUE_INVALID")
            print("R4A_EFFECTIVE_" + key.upper() + "=" + str(value), flush=True)
        print("R4A_EFFECTIVE_DECISION=PASS TOKEN_AND_IDENTITIES_NOT_PRINTED=true", flush=True)

    clone.probe_request = inspect
    clone.main()


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, UnicodeError,
            subprocess.SubprocessError, RuntimeError) as error:
        reason = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_EFFECTIVE_DECISION_BLOCKED=" + reason +
              " TOKEN_NOT_PRINTED=true", file=sys.stderr)
        raise SystemExit(1)
