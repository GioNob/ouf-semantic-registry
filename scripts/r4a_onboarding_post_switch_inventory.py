#!/usr/bin/env python3
"""Read-only live Onboarding and frozen-proposal inputs after the R4a switch."""

import json
from pathlib import Path
import subprocess
import time


SOURCE = "managed-cinema-8ec8ae90"
VERSION = "68394f42-5c82-4127-a1f3-126516665749"
IMAGE_REVISION = "f74c3a9f377b5ce93b5cab298fa24372de1602bc"
TOKEN = Path("/run/ouf-onboarding-identity/token")


def command(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True,
                          timeout=30).stdout.strip()


def main():
    live = json.loads(command("docker", "inspect", "ouf-onboarding"))[0]
    image = json.loads(command("docker", "inspect", live["Image"]))[0]
    names = {item.partition("=")[0] for item in live["Config"].get("Env") or []}
    mounted = any(m.get("Destination") == "/run/ouf-onboarding-identity"
                  and m.get("Type") == "bind" and not m.get("RW")
                  for m in live.get("Mounts") or [])
    print("R4A_ONB_POST_SWITCH=READ_ONLY")
    print("LIVE_RUNNING=" + str(live["State"]["Running"]).lower())
    print("LIVE_IMAGE_PINNED=" + str((image["Config"].get("Labels") or {}).get(
        "org.opencontainers.image.revision") == IMAGE_REVISION).lower())
    print("TOKEN_DIRECTORY_READ_ONLY_MOUNT=" + str(mounted).lower())
    print("TOKEN_RUNTIME_ENV_PRESENT=" + str({
        "OUF_ONB_UDP_IDENTITY_GATEWAY_URL", "OUF_ONB_UDP_IDENTITY_TOKEN_FILE"
    } <= names).lower())
    print("TOKEN_FILE_AGE_SECONDS=" + str(int(time.time() - TOKEN.stat().st_mtime)))
    print("TOKEN_TIMER=" + command("systemctl", "is-active",
                                     "ouf-onboarding-identity-token.timer"))
    sql = ("select json_build_object('state',state,'configuration',configuration)::text "
           "from ouf_onboarding.onboarding_version where source_id='" + SOURCE +
           "' and onboarding_version_id='" + VERSION + "'")
    result = command("docker", "exec", "ouf-postgres", "psql", "-U",
                     "ouf_onboarding", "-d", "ouf_onboarding", "-Atc", sql)
    proposal = json.loads(result)
    config = proposal["configuration"]
    runtime = config.get("extractionProfile", {}).get("runtime", {})
    execution = runtime.get("execution", {})
    udp = runtime.get("udp", {})
    mapping = config.get("semanticMapping", {})
    print("DRAFT_STATE=" + str(proposal["state"]))
    print("CANONICAL_CLASSES=" + json.dumps(sorted(
        x.get("classIri") for x in mapping.get("targetClasses", []) if x.get("classIri"))))
    print("MAPPED_PROPERTIES=" + json.dumps(sorted(
        x.get("targetPropertyIri") for x in mapping.get("propertyMappings", [])
        if x.get("targetPropertyIri"))))
    print("SEMANTIC_REFS=" + json.dumps(mapping.get("semanticRefs", [])))
    print("SEMANTIC_BINDINGS_PRESENT=" + str(bool(config.get("semanticReferenceBindings"))).lower())
    print("EXECUTION_KEYS=" + json.dumps(sorted(execution)))
    print("EXECUTION_SEMANTIC_PUBLICATION_SET_REF=" + str(
        execution.get("semanticPublicationSetRef", "ABSENT")))
    print("UDP_RESOLUTION_PRESENT=" + str(bool(udp.get("resolution"))).lower())
    print("UDP_MATERIALIZATION_PRESENT=" + str(bool(udp.get("materialization"))).lower())
    print("CONFIGURATION_AND_SECRETS_NOT_PRINTED=true LIVE_UNCHANGED=true")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print("R4A_ONB_POST_SWITCH_BLOCKED=" + type(error).__name__
              + " SECRETS_NOT_PRINTED=true LIVE_UNCHANGED=true")
        raise SystemExit(1)
