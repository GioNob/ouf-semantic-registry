#!/usr/bin/env python3
"""Compare the same HUMAN bearer on isolated UDP and Gateway without writing data."""

import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import types
from urllib.error import HTTPError
from urllib.request import Request, ProxyHandler, build_opener


REPO = Path("/opt/ouf/semantic")
PIN = "e557c772d4f59116b194b1280b1bf81b3146b955"
QUERY = "/api/udp/v1/governance/identity/preflight?id=00000000-0000-0000-0000-000000000000"


def source(name):
    git = ["git", "-c", "safe.directory=" + str(REPO), "-C", str(REPO)]
    if subprocess.check_output([*git, "rev-parse", PIN + "^{commit}"],
                               stderr=subprocess.DEVNULL).decode().strip() != PIN:
        raise RuntimeError("PINNED_REVISION_MISSING")
    return subprocess.check_output([*git, "show", PIN + ":scripts/" + name],
                                   stderr=subprocess.DEVNULL)


def load(name):
    module = types.ModuleType(name.removesuffix(".py"))
    exec(compile(source(name), name, "exec"), module.__dict__)
    return module


def request(url, bearer, direct):
    opener = build_opener(ProxyHandler({})) if direct else build_opener()
    req = Request(url, headers={"Accept": "application/json",
                                "Authorization": "Bearer " + bearer})
    try:
        with opener.open(req, timeout=20) as response:
            code, raw = response.status, response.read(4096)
    except HTTPError as error:
        code, raw = error.code, error.read(4096)
    try:
        body = json.loads(raw)
    except ValueError:
        body = {}
    return code, body if isinstance(body, dict) else {}


def summarize(label, result):
    code, body = result
    print(label + "_HTTP=" + str(code), flush=True)
    print(label + "_JSON_KEYS=" + json.dumps(sorted(body)), flush=True)
    reasons = ("TRUSTED_PRINCIPAL_REQUIRED", "NO_POLICY_BUNDLE", "STALE_POLICY_BUNDLE",
               "TENANT_MISMATCH", "CAPABILITY_DENIED", "UDP_IDENTITY_PREFLIGHT_NOT_FOUND")
    reason = next((item for item in reasons if any(item in str(body.get(key, ""))
                   for key in ("message", "detail", "error"))), "UNEXPOSED")
    print(label + "_AUTH_REASON=" + reason, flush=True)
    for key in ("message", "detail", "error"):
        value = body.get(key)
        if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_ .:-]{1,100}", value):
            print(label + "_" + key.upper() + "=" + value, flush=True)


def main():
    if os.geteuid() != 0:
        raise RuntimeError("ROOT_REQUIRED")
    clone = load("r4a_probe_udp_authorization_reason.py")
    human = load("r4a_cinema_semantic_draft.py")
    human.SCOPES = {"urban.identity.preflight"}
    original_probe = clone.probe_request

    def compare(ip, service_token):
        original_probe(ip, service_token)
        # The clone is healthy before asking the user to complete Device Flow.
        bearer, _ = human.human_token()
        direct = request("http://" + ip + ":8080" + QUERY, bearer, True)
        gateway = request("https://api.ouf-lab.it" + QUERY, bearer, False)
        summarize("R4A_PROBE_HUMAN_DIRECT", direct)
        summarize("R4A_PROBE_HUMAN_GATEWAY", gateway)
        print("R4A_PROBE_HUMAN_COMPARISON=PASS TOKEN_NOT_PRINTED=true", flush=True)

    clone.probe_request = compare
    clone.main()


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, UnicodeError,
            subprocess.SubprocessError, RuntimeError) as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_PROBE_HUMAN_BLOCKED=" + code +
              " TOKEN_NOT_PRINTED=true", file=sys.stderr)
        raise SystemExit(1)
