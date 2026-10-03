#!/usr/bin/env python3
"""Read the exact UDP gate with Onboarding's live SERVICE binding; no POST."""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import stat
import time
from urllib.parse import urlencode, urlsplit
import r4a_managed_identity_release_inventory as owner
import r4a_prepare_frozen_compatibility_probe as frozen


def gate_facts(gate, policy, source, configuration_hash):
    return {
        "UDP_GATE_VALID": gate.get("valid") is True,
        "UDP_GATE_SOURCE_MATCH": gate.get("sourceId") == source,
        "UDP_GATE_HASH_MATCH": gate.get("configurationHash") == configuration_hash,
        "UDP_GATE_TENANT_MATCH": gate.get("tenantId") == policy.get("tenantId"),
        "UDP_GATE_CLASS_MATCH": gate.get("canonicalClass") == policy.get("canonicalClass"),
        "UDP_GATE_POLICY_REF_MATCH": gate.get("policyRef") == policy.get("ref"),
        "UDP_GATE_POLICY_VERSION_MATCH": gate.get("policyVersion") == policy.get("version"),
        "UDP_GATE_COVERAGE_REF_PRESENT": isinstance(gate.get("coverageRef"), str)
            and gate["coverageRef"].startswith("coverage://"),
    }


def main(args):
    if os.geteuid() != 0:
        raise RuntimeError("ROOT_REQUIRED")
    print("R4A_CURRENT_UDP_ACTIVATION_GATE=READ_ONLY", flush=True)
    before = frozen.candidate_row(args.source, args.version, args.expected_hash)
    resolution = before["configuration"]["extractionProfile"]["runtime"]["udp"]["resolution"]
    policy = resolution["governedIdentity"]
    if (set(resolution) != {"strategyId", "strategyVersion", "policyRef", "governedIdentity"}
            or resolution.get("strategyId") != "GOVERNED_IDENTITY"
            or policy.get("sourceId") != args.source or policy.get("tenantId") != args.tenant_id
            or resolution.get("policyRef") != policy.get("ref")
            or resolution.get("strategyVersion") != policy.get("version")):
        raise RuntimeError("UDP_GATE_FROZEN_POLICY_INVALID")
    live = frozen.inspect("ouf-onboarding")
    image = frozen.inspect(live["Image"], "image")
    if (not live["State"]["Running"] or image["Config"].get("Labels", {}).get(
            "org.opencontainers.image.revision") != "6340d5bf120e09b47c32177656e2c377a4c03640"):
        raise RuntimeError("UDP_GATE_OWNER_REVISION_DRIFT")
    env = owner.environment(live)
    gateway = env.get("OUF_ONB_UDP_IDENTITY_GATEWAY_URL", "")
    url = urlsplit(gateway)
    if (url.scheme != "https" or not url.hostname or url.username is not None
            or url.password is not None or url.path not in ("", "/") or url.query or url.fragment):
        raise RuntimeError("UDP_GATE_OWNER_GATEWAY_INVALID")
    path = owner.host_file(live, env.get("OUF_ONB_UDP_IDENTITY_TOKEN_FILE"))
    if not owner.private_readable(path):
        raise RuntimeError("UDP_GATE_OWNER_TOKEN_UNREADABLE")
    token = path.read_text().strip()
    if len(token) > 16384 or not re.fullmatch(r"[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", token):
        raise RuntimeError("UDP_GATE_OWNER_TOKEN_FORMAT_INVALID")
    part = token.split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
    aud = claims.get("aud")
    aud = [aud] if isinstance(aud, str) else aud
    if (claims.get("ouf_actor_type") != "SERVICE" or claims.get("tenant_id") != args.tenant_id
            or (claims.get("client_id") or claims.get("azp")) != "ouf-source-onboarding"
            or claims.get("iss") != "https://auth.ouf-lab.it/realms/ouf"
            or not isinstance(aud, list) or "ouf-api-gateway" not in aud
            or "ouf.udp.identity.attestation.read" not in str(claims.get("scope", "")).split()
            or type(claims.get("exp")) is not int or claims["exp"] - time.time() < 60
            or time.time() - path.stat().st_mtime > 150):
        raise RuntimeError("UDP_GATE_OWNER_TOKEN_CLAIMS_OR_FRESHNESS_INVALID")
    endpoint = gateway.rstrip("/") + "/api/udp/v1/governance/internal/identity/preflight?" + urlencode(
        {"configurationHash": args.expected_hash, "sourceId": args.source})
    config = ('silent\nshow-error\nmax-time = 5\nmax-filesize = 65536\n'
        'header = "Authorization: Bearer ' + token + '"\nurl = ' + json.dumps(endpoint)
        + '\nwrite-out = "\\n%{http_code}"\n')
    raw = frozen.run(["docker", "run", "--rm", "-i", "--read-only", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges", "--network", "ouf-backend",
        "curlimages/curl:8.16.0", "--config", "-"], input=config, timeout=15)
    data, status = raw.rsplit("\n", 1)
    print("UDP_GATE_HTTP=" + (status if re.fullmatch(r"\d{3}", status) else "INVALID"))
    if status != "200":
        raise RuntimeError("UDP_GATE_GATEWAY_RESPONSE_NOT_200")
    facts = gate_facts(json.loads(data), policy, args.source, args.expected_hash)
    for key, value in facts.items():
        print(key + "=" + str(bool(value)).lower())
    current = frozen.inspect("ouf-onboarding")
    if (current["Id"] != live["Id"] or current["Image"] != live["Image"]
            or frozen.candidate_row(args.source, args.version, args.expected_hash) != before):
        raise RuntimeError("UDP_GATE_LIVE_OR_FROZEN_VERSION_CHANGED")
    print("R4A_CURRENT_UDP_ACTIVATION_GATE=" + ("PASS" if all(facts.values()) else "BLOCKED")
          + " LIVE_UNCHANGED=true SOURCE_APPROVAL=false SOURCE_ACTIVATION=false VALUES_NOT_PRINTED=true")
    if not all(facts.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("source", "version", "expected-hash", "tenant-id"):
        parser.add_argument("--" + option, required=True)
    try:
        main(parser.parse_args())
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_CURRENT_UDP_ACTIVATION_GATE=BLOCKED CODE=" + code + " SECRETS_NOT_PRINTED=true")
        raise SystemExit(1)
