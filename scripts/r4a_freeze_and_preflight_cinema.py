#!/usr/bin/env python3
"""Freeze the validated DRAFT and attest indexed UDP scope through HUMAN preflight."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import types
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from r4a_cinema_governed_proposal_plan import SOURCE, VERSION, CLASS, POLICY_REF, PUBLICATION_SET


EXPECTED_SHA = "2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891"
BASE = ("https://api.ouf-lab.it/api/onboarding/v1/sources/" + SOURCE +
        "/onboarding-versions/" + VERSION)
HUMAN = "https://api.ouf-lab.it/api/udp/v1/governance/identity/preflight"
SERVICE = "https://api.ouf-lab.it/api/udp/v1/governance/internal/identity/preflight"
TOKEN = Path("/run/ouf-onboarding-identity/token")


def human_token(revision):
    git = ["git", "-c", "safe.directory=/opt/ouf/semantic", "-C", "/opt/ouf/semantic"]
    if subprocess.check_output([*git, "rev-parse", revision + "^{commit}"],
                               stderr=subprocess.DEVNULL).decode().strip() != revision:
        raise RuntimeError("PINNED_REVISION_MISMATCH")
    source = subprocess.check_output([*git, "show", revision +
        ":scripts/r4a_cinema_semantic_draft.py"], stderr=subprocess.DEVNULL)
    helper = types.ModuleType("r4a_cinema_semantic_draft")
    exec(compile(source, "r4a_cinema_semantic_draft.py", "exec"), helper.__dict__)
    helper.SCOPES = {"ouf.onboarding.configuration.write", "urban.identity.preflight"}
    return helper.human_token()[0]


def request(method, url, bearer, payload=None, match=None):
    headers = {"Accept": "application/json", "Authorization": "Bearer " + bearer}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if match:
        headers["If-Match"] = match
    data = None if payload is None else json.dumps(payload, separators=(",", ":"),
                                                    ensure_ascii=False).encode()
    try:
        with urlopen(Request(url, method=method, data=data, headers=headers),
                     timeout=70) as response:
            return response.status, json.loads(response.read(1048576))
    except HTTPError as error:
        error.read(1048576)
        return error.code, {}


def required(result, label):
    code, body = result
    if code != 200:
        raise RuntimeError(label + "_HTTP_" + str(code))
    return body


def attestation(value, frozen_hash):
    if (value.get("configurationHash") != frozen_hash
        or value.get("sourceId") != SOURCE or value.get("tenantId") != "ouf-lab"
        or value.get("canonicalClass") != CLASS
        or value.get("policyRef") != POLICY_REF or value.get("policyVersion") != "1"
        or not str(value.get("coverageRef", "")).startswith("coverage://")
        or not isinstance(value.get("indexedObjects"), int)
        or not value.get("valid") is True
        or not re.fullmatch(r"[0-9a-f-]{36}", str(value.get("attestationId")))):
        raise RuntimeError("ATTESTATION_MISMATCH")


def service_read(frozen_hash):
    value = TOKEN.read_text().strip()
    if len(value) > 16384 or value.count(".") != 2:
        raise RuntimeError("SERVICE_TOKEN_INVALID")
    url = SERVICE + "?" + urlencode({"configurationHash": frozen_hash, "sourceId": SOURCE})
    return request("GET", url, value)


def main(revision):
    if os.geteuid() != 0 or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise RuntimeError("ROOT_AND_PINNED_REVISION_REQUIRED")
    bearer = human_token(revision)
    current = required(request("GET", BASE, bearer), "VERSION_READ")
    configuration = current.get("configuration")
    digest = hashlib.sha256(json.dumps(configuration, sort_keys=True,
        separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    if digest != EXPECTED_SHA:
        raise RuntimeError("REVIEWED_CONFIGURATION_CHANGED")
    if current.get("state") == "DRAFT" and current.get("lock_version") == 1:
        validation = required(request("POST", BASE + "/validate", bearer, {}),
                              "PRE_SUBMIT_VALIDATION")
        if (validation.get("result") != "PASS" or validation.get("errorCount") != 0
            or validation.get("configurationHash") != "sha256:" + EXPECTED_SHA):
            raise RuntimeError("VALIDATION_HASH_OR_RESULT_CHANGED")
        current = required(request("POST", BASE + "/submit", bearer, {},
                                   'W/"ov:1"'), "VERSION_SUBMIT")
        print("R4A_VERSION_SUBMIT=PASS", flush=True)
    if (current.get("state") != "IN_REVIEW" or current.get("lock_version") != 2
        or current.get("configuration_hash") != "sha256:" + EXPECTED_SHA
        or current.get("configuration") != configuration):
        raise RuntimeError("FROZEN_VERSION_MISMATCH")
    frozen_hash = current["configuration_hash"]
    print("R4A_VERSION_FROZEN=PASS HASH=" + frozen_hash + " LOCK=2", flush=True)
    result = required(request("POST", HUMAN, bearer,
        {"sourceId": SOURCE, "configurationHash": frozen_hash,
         "configuration": configuration}), "UDP_PREFLIGHT")
    attestation(result, frozen_hash)
    print("R4A_UDP_PREFLIGHT=PASS INDEXED_OBJECTS="
          + str(result["indexedObjects"]), flush=True)
    checked = required(request("GET", HUMAN + "?" + urlencode(
        {"id": result["attestationId"]}), bearer), "HUMAN_ATTESTATION_READ")
    attestation(checked, frozen_hash)
    latest = required(service_read(frozen_hash), "ONBOARDING_SERVICE_ATTESTATION_READ")
    attestation(latest, frozen_hash)
    if latest["attestationId"] != result["attestationId"]:
        raise RuntimeError("SERVICE_ATTESTATION_NOT_LATEST")
    print("R4A_ATTESTATION_HUMAN_READ=PASS SERVICE_READ=PASS VALID=true")
    print("R4A_ATTESTATION_ID=" + result["attestationId"])
    print("R4A_VERSION_IN_REVIEW=true NOT_APPROVED=true NOT_ACTIVE=true "
          "TOKEN_NOT_PRINTED=true")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    try:
        main(args.revision)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError,
            RuntimeError) as error:
        label = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_FREEZE_PREFLIGHT_BLOCKED=" + label + " TOKEN_NOT_PRINTED=true")
        raise SystemExit(1)
