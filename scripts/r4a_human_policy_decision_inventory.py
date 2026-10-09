#!/usr/bin/env python3
"""Mirror the SDK's HUMAN preflight decision using active policy and a fresh bearer."""

import base64
from datetime import datetime, timezone
import json
import os
import subprocess
import sys
import types


REVISION = "2254e75b7f9bc720e8f1d3df0ecdc7c5fc6a6389"
CAPABILITY = "urban.identity.preflight"


def main():
    if os.geteuid() != 0:
        raise RuntimeError("ROOT_REQUIRED")
    git = ["git", "-c", "safe.directory=/opt/ouf/semantic", "-C", "/opt/ouf/semantic"]
    if subprocess.check_output([*git, "rev-parse", REVISION + "^{commit}"],
                               stderr=subprocess.DEVNULL).decode().strip() != REVISION:
        raise RuntimeError("PINNED_REVISION_MISSING")
    source = subprocess.check_output([*git, "show", REVISION +
        ":scripts/r4a_cinema_semantic_draft.py"], stderr=subprocess.DEVNULL)
    helper = types.ModuleType("r4a_cinema_semantic_draft")
    exec(compile(source, "r4a_cinema_semantic_draft.py", "exec"), helper.__dict__)
    helper.SCOPES = {CAPABILITY}
    bearer, iam_sub = helper.human_token()
    segment = bearer.split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))
    effective_subject = str(claims.get("ouf_subject") or claims.get("sub") or "")
    raw_roles = claims.get("externalRoleRefs", claims.get("external_role_refs", []))
    if not isinstance(raw_roles, list):
        raise RuntimeError("ROLE_CLAIMS_UNEXPECTED")
    roles = set(raw_roles)
    raw_amr = claims.get("amr", [])
    amr = set(raw_amr.split()) if isinstance(raw_amr, str) else set(raw_amr)
    tenant = claims.get("tenant_id")
    sql = ("select p.bundle_payload::text from ouf_authorization.active_policy_bundle a "
           "join ouf_authorization.policy_bundle p using (bundle_id,version)")
    raw = subprocess.check_output(["docker", "exec", "ouf-postgres", "psql", "-U",
        "ouf_onboarding", "-d", "ouf_onboarding", "-Atc", sql],
        stderr=subprocess.DEVNULL, timeout=30).decode().strip()
    payload = json.loads(raw)
    policy = payload.get("bundle", payload)
    descriptors = [item for item in policy["capabilities"] if item["capabilityId"] == CAPABILITY]
    grants = [item for item in policy["grants"] if item["capabilityId"] == CAPABILITY]
    if len(descriptors) != 1 or len(grants) != 1 or policy["version"] != 30:
        raise RuntimeError("ACTIVE_POLICY_SHAPE_CHANGED")
    descriptor, grant = descriptors[0], grants[0]
    constraints = grant.get("constraints") or {}
    now = datetime.now(timezone.utc)
    start = datetime.fromisoformat(grant["validFrom"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(grant["validUntil"].replace("Z", "+00:00"))
    authentication = claims.get("auth_time")
    age = constraints.get("maxAuthenticationAgeSeconds")
    checks = {
        "DESCRIPTOR_ACTOR": claims.get("ouf_actor_type") in descriptor["allowedActors"],
        "DESCRIPTOR_SCOPE": descriptor["requiredScope"] in str(claims.get("scope", "")).split(),
        "TENANT": tenant == grant["tenantId"] == "ouf-lab",
        "VALIDITY": start <= now < end,
        "ORGANIZATION": not grant.get("organizationId"),
        "SUBJECT": not grant.get("subjectId") or grant["subjectId"] == effective_subject,
        "SERVICE": not grant.get("servicePrincipalId"),
        "EXTERNAL_ROLE": not constraints.get("externalRoleRef") or
                         constraints["externalRoleRef"] in roles,
        "RESOURCE_TYPE": constraints.get("resourceType") in (None, "capability"),
        "RESOURCE_ID": not constraints.get("resourceId"),
        "RESOURCE_ATTRIBUTES": not constraints.get("resourceAttributes"),
        "ACR": not constraints.get("requiredAcr") or
               constraints["requiredAcr"] == claims.get("acr"),
        "AMR": set(constraints.get("requiredAmr") or []) <= amr,
        "AUTH_AGE": age is None or (isinstance(authentication, int)
                     and authentication <= now.timestamp() < authentication + age),
        "EFFECT_ALLOW": constraints.get("effect", "ALLOW") == "ALLOW",
    }
    print("R4A_HUMAN_POLICY_DECISION=READ_ONLY POLICY=" +
          policy["bundleId"] + ":" + str(policy["version"]), flush=True)
    print("TOKEN_OUF_SUBJECT_PRESENT=" + str(bool(claims.get("ouf_subject"))).lower(), flush=True)
    print("EFFECTIVE_SUBJECT_EQUALS_IAM_SUB=" + str(effective_subject == iam_sub).lower(), flush=True)
    print("GRANT_ORGANIZATION_PRESENT=" + str(bool(grant.get("organizationId"))).lower(), flush=True)
    print("GRANT_SUBJECT_MATCHES_IAM_SUB=" + str(grant.get("subjectId") == iam_sub).lower(), flush=True)
    for name, allowed in checks.items():
        print("SDK_CHECK_" + name + "=" + ("PASS" if allowed else "FAIL"), flush=True)
    print("SDK_EVALUATED_GRANT=" + ("ALLOW" if all(checks.values()) else "DENY"), flush=True)
    print("TOKEN_AND_POLICY_VALUES_NOT_PRINTED=true LIVE_UNCHANGED=true", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, UnicodeError,
            subprocess.SubprocessError, RuntimeError) as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_HUMAN_POLICY_INVENTORY_BLOCKED=" + code +
              " TOKEN_NOT_PRINTED=true", file=sys.stderr)
        raise SystemExit(1)
