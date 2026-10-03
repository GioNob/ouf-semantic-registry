#!/usr/bin/env python3
"""Read-only inventory of the next R4a Ingestion compatibility gate."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys


STAGE = Path("/opt/ouf/r4a-stage/identity-images.json")
TARGET = "e3f04f1d8ed47a62cde8b9c7831882c9cea17169"
CAPABILITY = "ouf.ingestion.configuration.attest"


def run(*args):
    return subprocess.check_output(args, stderr=subprocess.DEVNULL, timeout=30).decode().strip()


def sql(user, database, statement):
    return run("docker", "exec", "ouf-postgres", "psql", "-X", "-qAt", "-v",
               "ON_ERROR_STOP=1", "-U", user, "-d", database, "-c", statement)


def main():
    if os.geteuid() != 0:
        raise RuntimeError("ROOT_REQUIRED")
    manifest = json.loads(STAGE.read_text())
    staged = manifest["modules"]["ingestion"]
    if manifest.get("schema") != "ouf.r4a.identity-images.v1" or staged.get("commit") != TARGET:
        raise RuntimeError("STAGED_IMAGE_DRIFT")
    live = json.loads(run("docker", "inspect", "ouf-ingestion"))[0]
    image = json.loads(run("docker", "image", "inspect", staged["image_id"]))[0]
    if (not live["State"]["Running"] or image["Id"] != staged["image_id"]
        or image["Config"]["Labels"].get("org.opencontainers.image.revision") != TARGET):
        raise RuntimeError("INGESTION_IMAGE_OR_LIVE_DRIFT")
    print("R4A_ING_COMPAT_INVENTORY=READ_ONLY", flush=True)
    print("ING_STAGED_COMMIT=" + TARGET, flush=True)
    print("ING_STAGED_DIFFERS_FROM_LIVE=" + str(staged["image_id"] != live["Image"]).lower(), flush=True)
    print("ING_NETWORK_MODE=" + str(live["HostConfig"]["NetworkMode"]), flush=True)
    print("ING_NETWORKS=" + ",".join(sorted(live["NetworkSettings"]["Networks"])), flush=True)
    print("ING_USER=" + str(live["Config"]["User"]), flush=True)
    print("ING_RESTART=" + str(live["HostConfig"]["RestartPolicy"]["Name"]), flush=True)
    print("ING_MOUNT_DESTINATIONS=" + ",".join(sorted(m["Destination"] for m in live["Mounts"])), flush=True)
    print("ING_ENV_NAMES=" + ",".join(sorted(e.partition("=")[0] for e in live["Config"]["Env"])), flush=True)
    version = sql("ouf_ingestion", "ouf_ingestion", "select version from "
                  "ouf_ingestion.flyway_schema_history order by installed_rank desc limit 1")
    print("ING_LIVE_FLYWAY=" + version, flush=True)
    worktree = Path(staged["worktree"])
    if run("git", "-C", str(worktree), "rev-parse", "HEAD") != TARGET:
        raise RuntimeError("STAGED_WORKTREE_DRIFT")
    migrations = [int(m.group(1)) for path in
                  (worktree / "src/main/resources/db/migration").glob("V*__*.sql")
                  if (m := re.match(r"V(\d+)__", path.name))]
    if not migrations:
        raise RuntimeError("STAGED_MIGRATIONS_MISSING")
    print("ING_STAGED_FLYWAY_MAX=" + str(max(migrations)), flush=True)
    payload = json.loads(sql("ouf_onboarding", "ouf_onboarding", "select p.bundle_payload::text "
        "from ouf_authorization.active_policy_bundle a join ouf_authorization.policy_bundle p "
        "using (bundle_id,version)"))
    bundle = payload.get("bundle", payload)
    descriptors = [c for c in bundle["capabilities"] if c["capabilityId"] == CAPABILITY]
    grants = [g for g in bundle["grants"] if g["capabilityId"] == CAPABILITY]
    print("AUTH_POLICY=" + bundle["bundleId"] + ":" + str(bundle["version"]), flush=True)
    print("ING_COMPAT_DESCRIPTOR_COUNT=" + str(len(descriptors)), flush=True)
    print("ING_COMPAT_DESCRIPTOR_SERVICE=" + str(len(descriptors) == 1 and
        "SERVICE" in descriptors[0].get("allowedActors", [])).lower(), flush=True)
    print("ING_COMPAT_SERVICE_GRANT_COUNT=" + str(sum(g.get("servicePrincipalId") is not None
        for g in grants)), flush=True)
    print("ING_COMPAT_OTHER_GRANT_COUNT=" + str(sum(g.get("servicePrincipalId") is None
        for g in grants)), flush=True)
    print("R4A_ING_COMPAT_INVENTORY=PASS SECRETS_AND_IDENTITIES_NOT_PRINTED=true "
          "LIVE_UNCHANGED=true")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, IndexError, UnicodeError,
            subprocess.SubprocessError, RuntimeError) as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_ING_COMPAT_INVENTORY_BLOCKED=" + code +
              " LIVE_UNCHANGED=true", file=sys.stderr)
        raise SystemExit(1)
