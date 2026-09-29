#!/usr/bin/env python3
"""Read the existing cinema attestation through Onboarding's SERVICE route."""

import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SOURCE = "managed-cinema-8ec8ae90"
VERSION = "68394f42-5c82-4127-a1f3-126516665749"
ATTESTATION = "57499699-dbc5-419d-a14b-27cd3604ec6f"
HASH = "sha256:2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891"
CLASS = "https://api.ouf-lab.it/semantic/cinema#Cinema"
POLICY = "identity://ouf-lab/cinema/complete-canonical-equality/1"
TOKEN = Path("/run/ouf-onboarding-identity/token")


def query(sql):
    return subprocess.check_output(["docker", "exec", "ouf-postgres", "psql", "-X", "-qAt",
        "-v", "ON_ERROR_STOP=1", "-U", "ouf_onboarding", "-d", "ouf_onboarding", "-c", sql],
        stderr=subprocess.DEVNULL, timeout=30).decode().strip()


def main():
    if os.geteuid() != 0:
        raise RuntimeError("ROOT_REQUIRED")
    row = json.loads(query("select json_build_object('state',state,'lock',lock_version,"
        "'hash',configuration_hash)::text from ouf_onboarding.onboarding_version "
        "where source_id='" + SOURCE + "' and onboarding_version_id='" + VERSION + "'"))
    if row != {"state": "IN_REVIEW", "lock": 2, "hash": HASH}:
        raise RuntimeError("FROZEN_VERSION_CHANGED")
    print("R4A_EXISTING_VERSION_FROZEN=PASS LOCK=2", flush=True)
    bearer = TOKEN.read_text().strip()
    if len(bearer) > 16384 or bearer.count(".") != 2:
        raise RuntimeError("SERVICE_TOKEN_INVALID")
    url = "https://api.ouf-lab.it/api/udp/v1/governance/internal/identity/preflight?" + urlencode(
        {"configurationHash": HASH, "sourceId": SOURCE})
    try:
        with urlopen(Request(url, headers={"Accept": "application/json",
                                             "Authorization": "Bearer " + bearer}), timeout=30) as response:
            status, raw = response.status, response.read(65536)
    except HTTPError as error:
        error.read(65536)
        raise RuntimeError("SERVICE_ATTESTATION_HTTP_" + str(error.code)) from None
    if status != 200:
        raise RuntimeError("SERVICE_ATTESTATION_HTTP_" + str(status))
    value = json.loads(raw)
    if (value.get("attestationId") != ATTESTATION or value.get("configurationHash") != HASH
        or value.get("sourceId") != SOURCE or value.get("tenantId") != "ouf-lab"
        or value.get("canonicalClass") != CLASS or value.get("policyRef") != POLICY
        or value.get("policyVersion") != "1" or value.get("valid") is not True
        or not isinstance(value.get("indexedObjects"), int)
        or not str(value.get("coverageRef", "")).startswith("coverage://")):
        raise RuntimeError("SERVICE_ATTESTATION_MISMATCH")
    print("R4A_EXISTING_SERVICE_ATTESTATION=PASS INDEXED_OBJECTS=" +
          str(value["indexedObjects"]) + " ID=" + ATTESTATION, flush=True)
    compatibility = query("select coalesce((select compatible::text from "
        "ouf_onboarding.consumer_compatibility_attestation where onboarding_version_id='" +
        VERSION + "' and consumer='INGESTION_RUNTIME' and configuration_hash='" + HASH +
        "' order by created_at desc,attestation_id desc limit 1),'absent')")
    if compatibility not in {"true", "false", "absent"}:
        raise RuntimeError("INGESTION_COMPATIBILITY_SHAPE_CHANGED")
    print("R4A_INGESTION_COMPATIBILITY=" + compatibility.upper(), flush=True)
    staged = json.loads(Path("/opt/ouf/r4a-stage/identity-images.json").read_text())
    ingestion = staged["modules"]["ingestion"]
    live = json.loads(subprocess.check_output(["docker", "inspect", "ouf-ingestion"],
        stderr=subprocess.DEVNULL, timeout=20))[0]
    if ingestion.get("commit") != "e3f04f1d8ed47a62cde8b9c7831882c9cea17169":
        raise RuntimeError("INGESTION_STAGED_REVISION_CHANGED")
    print("R4A_INGESTION_LIVE_RUNNING=" + str(live["State"]["Running"]).lower(), flush=True)
    print("R4A_INGESTION_STAGED_DIFFERS_FROM_LIVE=" +
          str(ingestion.get("image_id") != live["Image"]).lower(), flush=True)
    print("R4A_EXISTING_ATTESTATION_VERIFY=PASS LIVE_UNCHANGED=true TOKEN_NOT_PRINTED=true")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, UnicodeError,
            subprocess.SubprocessError, RuntimeError) as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_EXISTING_ATTESTATION_BLOCKED=" + code +
              " TOKEN_NOT_PRINTED=true", file=sys.stderr)
        raise SystemExit(1)
