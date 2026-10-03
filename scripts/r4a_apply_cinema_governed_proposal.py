#!/usr/bin/env python3
"""Apply the pinned governed cinema proposal via HUMAN Onboarding API and validate."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import types
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import r4a_cinema_governed_proposal_plan as proposal


EXPECTED_SHA = "2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891"
BASE = ("https://api.ouf-lab.it/api/onboarding/v1/sources/" + proposal.SOURCE +
        "/onboarding-versions/" + proposal.VERSION)


def token(revision):
    git = ["git", "-c", "safe.directory=/opt/ouf/semantic", "-C", "/opt/ouf/semantic"]
    if subprocess.check_output([*git, "rev-parse", revision + "^{commit}"],
                               stderr=subprocess.DEVNULL).decode().strip() != revision:
        raise RuntimeError("PINNED_REVISION_MISMATCH")
    source = subprocess.check_output([*git, "show", revision +
        ":scripts/r4a_cinema_semantic_draft.py"], stderr=subprocess.DEVNULL)
    helper = types.ModuleType("r4a_cinema_semantic_draft")
    exec(compile(source, "r4a_cinema_semantic_draft.py", "exec"), helper.__dict__)
    helper.SCOPES = {"ouf.onboarding.configuration.write"}
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
                     timeout=30) as response:
            return response.status, json.loads(response.read(1048576))
    except HTTPError as error:
        error.read(1048576)
        return error.code, {}


def require(response, label):
    status, body = response
    if status != 200:
        raise RuntimeError(label + "_HTTP_" + str(status))
    return body


def main(revision):
    if os.geteuid() != 0 or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise RuntimeError("ROOT_AND_PINNED_REVISION_REQUIRED")
    config, already = proposal.plan()
    digest = hashlib.sha256(json.dumps(config, sort_keys=True,
        separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    if digest != EXPECTED_SHA:
        raise RuntimeError("REVIEWED_PROPOSAL_HASH_CHANGED")
    bearer = token(revision)
    if not already:
        changed = require(request("PUT", BASE, bearer, {"configuration": config},
                                  'W/"ov:0"'), "DRAFT_PATCH")
        if (changed.get("state") != "DRAFT" or changed.get("lock_version") != 1
            or changed.get("configuration") != config):
            raise RuntimeError("DRAFT_PATCH_READBACK_MISMATCH")
        print("R4A_GOVERNED_DRAFT_PATCH=PASS LOCK=1", flush=True)
    else:
        print("R4A_GOVERNED_DRAFT_PATCH=ALREADY_APPLIED LOCK=1", flush=True)
    current = require(request("GET", BASE, bearer), "DRAFT_READBACK")
    if (current.get("state") != "DRAFT" or current.get("lock_version") != 1
        or current.get("configuration") != config):
        raise RuntimeError("DRAFT_READBACK_MISMATCH")
    print("R4A_GOVERNED_DRAFT_READBACK=PASS PROPOSAL_SHA256=" + digest,
          flush=True)
    validation = require(request("POST", BASE + "/validate", bearer, {}),
                         "DRAFT_VALIDATION")
    if validation.get("onboardingVersionId") != proposal.VERSION:
        raise RuntimeError("VALIDATION_VERSION_MISMATCH")
    print("R4A_GOVERNED_DRAFT_VALIDATION=" + str(validation.get("result"))
          + " ERRORS=" + str(validation.get("errorCount"))
          + " WARNINGS=" + str(validation.get("warningCount")), flush=True)
    for finding in validation.get("findings", []):
        if finding.get("severity") in ("ERROR", "WARNING"):
            print("FINDING=" + str(finding.get("code")) + " PATH="
                  + str(finding.get("path")), flush=True)
    if validation.get("result") != "PASS" or validation.get("errorCount") != 0:
        raise RuntimeError("VALIDATION_NOT_PASS")
    print("R4A_GOVERNED_DRAFT_READY=PASS NOT_SUBMITTED=true "
          "NOT_APPROVED=true NOT_ACTIVE=true TOKEN_NOT_PRINTED=true")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    try:
        main(args.revision)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError,
            RuntimeError) as error:
        label = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_GOVERNED_DRAFT_BLOCKED=" + label + " TOKEN_NOT_PRINTED=true")
        raise SystemExit(1)
