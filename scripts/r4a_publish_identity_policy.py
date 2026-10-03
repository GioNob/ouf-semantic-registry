#!/usr/bin/env python3
"""Review and HUMAN-publish the exact R4a identity policy draft.

No bearer or password is persisted. This action changes ACTIVE irreversibly;
the administrator must confirm the exact draft in the terminal after IAM login.
"""

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys

from r4a_create_identity_policy_draft import (
    PINNED, active_ref, human_token, http, private_owner, validate,
)


DRAFT_ID = "fb931b4e-46bb-4aee-8f0e-434b8aeda10b"


def normalize(value):
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items() if item is not None}
    if isinstance(value, list):
        return [normalize(item) for item in value]
    return value


def timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def same_policy(actual, expected):
    a, b = normalize(actual), normalize(expected)
    for policy in (a, b):
        policy["publishedAt"] = timestamp(policy["publishedAt"]).isoformat()
        for grant in policy["grants"]:
            for field in ("validFrom", "validUntil"):
                grant[field] = timestamp(grant[field]).isoformat()
    return a == b


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--active", type=Path, required=True)
    parser.add_argument("--review-dir", type=Path, required=True)
    args = parser.parse_args()
    raw = json.loads(args.active.read_text())
    base = raw.get("bundle", raw)
    candidate = json.loads((args.review_dir / "policy-draft.json").read_text())
    registrations = json.loads((args.review_dir / "capability-registrations.json").read_text())
    validate(base, candidate, registrations)
    if active_ref() != PINNED:
        raise RuntimeError("ACTIVE_CHANGED_REBASE_REQUIRED")
    owner = private_owner()
    token = human_token()
    status, result = http(owner + "/policies/" + DRAFT_ID, token=token)
    if status != 200 or not isinstance(result, dict):
        raise RuntimeError("DRAFT_READ_FAILED:" + str(status))
    if (result.get("id") != DRAFT_ID or result.get("revision") != 0 or
            result.get("state") != "DRAFT" or result.get("baseActiveRef") != PINNED or
            not same_policy(result.get("policy"), candidate)):
        raise RuntimeError("DRAFT_DIFFERS_FROM_REVIEWED_FILE")
    if active_ref() != PINNED:
        raise RuntimeError("ACTIVE_CHANGED_REBASE_REQUIRED")
    grant = candidate["grants"][-1]
    print("\nRevisione per pubblicazione:", flush=True)
    print("  ACTIVE: " + PINNED + " -> ouf-lab-authorization:29", flush=True)
    print("  Bozza: " + DRAFT_ID + ", revisione 0", flush=True)
    print("  Quattro capability UDP registrate; grant preesistenti conservati", flush=True)
    print("  Nuovo grant SERVICE: ouf-source-onboarding / ouf.udp.identity.attestation.read", flush=True)
    print("  Scadenza del grant: " + grant["validUntil"], flush=True)
    print("  Nuovi grant HUMAN: 0; il ruolo ouf-admin sarà aggiornato separatamente", flush=True)
    confirmation = input("Per pubblicare, digita esattamente 'PUBBLICA " + DRAFT_ID + "': ")
    if confirmation != "PUBBLICA " + DRAFT_ID:
        print("R4A_POLICY_PUBLICATION_CANCELLED=true ACTIVE_UNCHANGED=true")
        return
    if active_ref() != PINNED:
        raise RuntimeError("ACTIVE_CHANGED_REBASE_REQUIRED")
    status, published = http(owner + "/policies/" + DRAFT_ID + ":publish", "POST", token=token,
                             extra_headers={"If-Match": '"0"'})
    if (status != 200 or not isinstance(published, dict) or
            published.get("state") != "PUBLISHED" or published.get("revision") != 1):
        raise RuntimeError("PUBLISH_RESULT_UNCERTAIN_CHECK_ACTIVE_AND_DRAFT:" + str(status))
    if active_ref() != "ouf-lab-authorization:29":
        raise RuntimeError("PUBLISHED_RESPONSE_BUT_ACTIVE_NOT_29_CHECK_SERVER")
    print("R4A_POLICY_PUBLISHED=ouf-lab-authorization:29 DRAFT=" + DRAFT_ID +
          " ROLE_UPDATE_PENDING=true", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, EOFError) as error:
        print("R4A_POLICY_PUBLICATION_BLOCKED=" + str(error), file=sys.stderr)
        sys.exit(1)
