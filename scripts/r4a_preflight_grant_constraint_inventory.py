#!/usr/bin/env python3
"""Read only the label/detail constraint shape of the active preflight role grant."""

import json
import os
import subprocess
import sys


CAPABILITY = "urban.identity.preflight"


def query(sql):
    return subprocess.check_output(["docker", "exec", "ouf-postgres", "psql", "-U",
        "ouf_onboarding", "-d", "ouf_onboarding", "-Atc", sql],
        stderr=subprocess.DEVNULL, timeout=30).decode().strip()


def counts(constraints):
    if not isinstance(constraints, dict):
        constraints = {}
    labels = constraints.get("allowedDataLabels") or []
    levels = constraints.get("allowedDetailLevels") or []
    if not isinstance(labels, list) or not isinstance(levels, list):
        raise RuntimeError("CONSTRAINT_SHAPE_CHANGED")
    return len(labels), len(levels)


def main():
    if os.geteuid() != 0:
        raise RuntimeError("ROOT_REQUIRED")
    payload = json.loads(query("select p.bundle_payload::text from "
        "ouf_authorization.active_policy_bundle a join "
        "ouf_authorization.policy_bundle p using (bundle_id,version)"))
    bundle = payload.get("bundle", payload)
    grants = [g for g in bundle["grants"] if g["capabilityId"] == CAPABILITY]
    if bundle["version"] != 30 or len(grants) != 1:
        raise RuntimeError("ACTIVE_POLICY_SHAPE_CHANGED")
    grant = grants[0]
    labels, levels = counts(grant.get("constraints"))
    print("R4A_PREFLIGHT_GRANT=READ_ONLY POLICY=" + bundle["bundleId"] + ":30", flush=True)
    print("ACTIVE_ALLOWED_DATA_LABEL_COUNT=" + str(labels), flush=True)
    print("ACTIVE_ALLOWED_DETAIL_LEVEL_COUNT=" + str(levels), flush=True)
    print("ACTIVE_RESOURCE_WITHOUT_LABEL_MATCH=" + str(labels == 0).lower(), flush=True)
    print("ACTIVE_RESOURCE_WITHOUT_DETAIL_MATCH=" + str(levels == 0).lower(), flush=True)
    if not grant["grantId"].startswith("ouf-role:"):
        raise RuntimeError("ROLE_MANAGED_GRANT_EXPECTED")
    raw = query("select payload::text from ouf_authorization.role_catalogue "
                "where tenant_id='ouf-lab'")
    if not raw:
        raise RuntimeError("ROLE_CATALOGUE_MISSING")
    catalogue = json.loads(raw)
    permissions = [p for role in catalogue["roles"] for p in role["permissions"]
                   if p["capabilityId"] == CAPABILITY]
    print("ROLE_PERMISSION_COUNT=" + str(len(permissions)), flush=True)
    for index, permission in enumerate(permissions, 1):
        rlabels, rlevels = counts(permission.get("constraints"))
        print("ROLE_PERMISSION_" + str(index) + "_LABEL_COUNT=" + str(rlabels), flush=True)
        print("ROLE_PERMISSION_" + str(index) + "_DETAIL_COUNT=" + str(rlevels), flush=True)
    print("ROLE_AND_POLICY_VALUES_NOT_PRINTED=true LIVE_UNCHANGED=true", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, UnicodeError,
            subprocess.SubprocessError, RuntimeError) as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_PREFLIGHT_GRANT_INVENTORY_BLOCKED=" + code +
              " LIVE_UNCHANGED=true", file=sys.stderr)
        raise SystemExit(1)
