#!/usr/bin/env python3
"""Prepare, without publishing, the next R4a Authorization PolicyBundle.

Inputs are read-only exports of the ACTIVE bundle and capability registrations.
The script never contacts the database or Authorization API and writes no tokens.
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys


CAPABILITIES = (
    ("urban.identity.preflight", "COMMAND", "HUMAN"),
    ("ouf.udp.identity.attestation.read", "READ", "SERVICE"),
    ("resolution.issue.read", "READ", "HUMAN"),
    ("resolution.match.approve", "COMMAND", "HUMAN"),
)


def descriptor(capability, operation, actor):
    return {"capabilityId": capability, "operation": operation,
            "requiredScope": capability, "allowedActors": [actor]}


def canonical(value):
    if isinstance(value, dict):
        return {key: canonical(item) for key, item in value.items() if item is not None}
    if isinstance(value, list):
        return sorted((canonical(item) for item in value), key=lambda item: json.dumps(item, sort_keys=True))
    return value


def parse_date(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def prepare(active, registrations, valid_until, now):
    bundle = active.get("bundle", active)
    if bundle.get("bundleId") != "ouf-lab-authorization" or bundle.get("version") != 28:
        raise ValueError("ACTIVE_CHANGED_EXPECTED_OUF_LAB_AUTHORIZATION_28")
    if set(bundle) != {"bundleId", "version", "publishedAt", "capabilities", "grants"}:
        raise ValueError("ACTIVE_BUNDLE_SHAPE_UNEXPECTED")
    if not now < parse_date(valid_until):
        raise ValueError("GRANT_EXPIRY_MUST_BE_FUTURE")
    registered = {}
    for row in registrations:
        cap = row.get("capability_id", row.get("capabilityId"))
        value = row.get("descriptor")
        if isinstance(value, str):
            value = json.loads(value)
        if not cap or not isinstance(value, dict) or cap in registered:
            raise ValueError("INVALID_REGISTRATION_EXPORT")
        registered[cap] = value
    result = json.loads(json.dumps(bundle))
    result["version"] += 1
    result["publishedAt"] = now.isoformat().replace("+00:00", "Z")
    existing = {item["capabilityId"]: item for item in result["capabilities"]}
    if len(existing) != len(result["capabilities"]):
        raise ValueError("DUPLICATE_ACTIVE_DESCRIPTOR")
    missing = []
    for cap, operation, actor in CAPABILITIES:
        expected = descriptor(cap, operation, actor)
        if cap in existing and canonical(existing[cap]) != canonical(expected):
            raise ValueError("ACTIVE_DESCRIPTOR_CONFLICT:" + cap)
        if cap in registered and canonical(registered[cap]) != canonical(expected):
            raise ValueError("REGISTERED_DESCRIPTOR_CONFLICT:" + cap)
        if cap not in existing:
            result["capabilities"].append(expected)
        if cap not in registered:
            missing.append({"ownerRef": "udp", "descriptor": expected})
    grant_id = "grant-r4a-identity-attestation-onboarding"
    if any(item["grantId"] == grant_id for item in result["grants"]):
        raise ValueError("SERVICE_GRANT_ID_ALREADY_EXISTS")
    result["grants"].append({
        "grantId": grant_id,
        "capabilityId": "ouf.udp.identity.attestation.read",
        "tenantId": "ouf-lab",
        "subjectId": None,
        "servicePrincipalId": "ouf-source-onboarding",
        "organizationId": None,
        "validFrom": now.isoformat().replace("+00:00", "Z"),
        "validUntil": valid_until,
    })
    return result, missing


def save(path, value):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    with os.fdopen(os.open(path, flags, 0o600), "w") as target:
        json.dump(value, target, indent=2, ensure_ascii=False)
        target.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--active", type=Path, required=True)
    parser.add_argument("--registrations", type=Path, required=True)
    parser.add_argument("--valid-until", required=True, help="Explicit UTC expiry, e.g. 2027-09-28T00:00:00Z")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise ValueError("OUTPUT_DIRECTORY_ALREADY_EXISTS")
    active = json.loads(args.active.read_text())
    registrations = json.loads(args.registrations.read_text())
    if not isinstance(registrations, list):
        raise ValueError("REGISTRATIONS_MUST_BE_ARRAY")
    bundle, missing = prepare(active, registrations, args.valid_until, datetime.now(timezone.utc))
    args.output_dir.mkdir(mode=0o700)
    save(args.output_dir / "policy-draft.json", bundle)
    save(args.output_dir / "capability-registrations.json", missing)
    print(f"R4A_POLICY_DRAFT_READY={args.output_dir} BASE=ouf-lab-authorization:28 NEXT=29 "
          f"REGISTER={len(missing)} HUMAN_GRANTS_DEFERRED_TO_ROLE_CATALOGUE=true")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print("R4A_POLICY_PREPARATION_BLOCKED=" + str(error), file=sys.stderr)
        sys.exit(1)
