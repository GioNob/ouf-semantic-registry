#!/usr/bin/env python3
"""Read-only Onboarding rollout inventory; omit secret values and mount sources."""

import json
from pathlib import Path
import stat
import subprocess


MANIFEST = Path("/opt/ouf/r4a-stage/identity-images.json")
SECRET = Path("/var/lib/ouf-r4a-identity/onboarding-client-secret")
TOKEN_DIR = Path("/run/ouf-onboarding-identity")
EXPECTED = "f74c3a9f377b5ce93b5cab298fa24372de1602bc"


def docker(*arguments):
    return subprocess.run(["docker", *arguments], capture_output=True, check=True,
                          text=True, timeout=30).stdout.strip()


def inspect(name):
    return json.loads(docker("inspect", name))[0]


def main():
    live = inspect("ouf-onboarding")
    record = json.loads(MANIFEST.read_text())["modules"]["onboarding"]
    image = inspect(record["image_id"])
    if record["commit"] != EXPECTED or record["live_image_id"] != live["Image"]:
        raise RuntimeError("PINNED_IMAGE_OR_LIVE_CHANGED")
    print("R4A_ONB_INVENTORY=READ_ONLY")
    print("LIVE_RUNNING=" + str(live["State"]["Running"]).lower())
    print("STAGED_IMAGE_REVISION_MATCH=" + str(
        (image["Config"].get("Labels") or {}).get("org.opencontainers.image.revision")
        == EXPECTED).lower())
    print("NETWORK_MODE=" + str(live["HostConfig"].get("NetworkMode")))
    print("NETWORKS=" + ",".join(sorted(live["NetworkSettings"]["Networks"])))
    print("USER=" + str(live["Config"].get("User")))
    print("RESTART=" + str((live["HostConfig"].get("RestartPolicy") or {}).get("Name")))
    print("LOG_DRIVER=" + str((live["HostConfig"].get("LogConfig") or {}).get("Type")))
    print("MOUNT_DESTINATIONS=" + ",".join(sorted(
        mount["Destination"] + (":ro" if not mount["RW"] else ":rw")
        for mount in live.get("Mounts") or [])))
    print("ENV_NAMES=" + ",".join(sorted(item.partition("=")[0]
        for item in live["Config"].get("Env") or [])))
    print("EXTRA_HOSTCONFIG=" + ",".join(sorted(key for key in
        ("Binds", "VolumesFrom", "PortBindings", "ExtraHosts", "Dns", "DnsSearch",
         "CapAdd", "SecurityOpt", "Devices", "Tmpfs", "GroupAdd", "UsernsMode")
        if live["HostConfig"].get(key))))
    print("SECRET_METADATA_VALID=" + str(SECRET.exists() and
        stat.S_ISREG(SECRET.lstat().st_mode) and SECRET.lstat().st_uid == 0 and
        stat.S_IMODE(SECRET.lstat().st_mode) == 0o600).lower())
    if TOKEN_DIR.exists():
        mode = TOKEN_DIR.lstat()
        print("TOKEN_DIRECTORY_READY=" + str(stat.S_ISDIR(mode.st_mode)
            and mode.st_uid == 0 and mode.st_gid == 10003
            and stat.S_IMODE(mode.st_mode) == 0o750).lower())
    else:
        print("TOKEN_DIRECTORY_READY=false")
    version = docker("exec", "ouf-postgres", "psql", "-U", "ouf_onboarding",
                     "-d", "ouf_onboarding", "-Atc",
                     "select version from ouf_onboarding.flyway_schema_history "
                     "order by installed_rank desc limit 1")
    print("LIVE_FLYWAY=" + version)
    print("SECRET_VALUES_AND_MOUNT_SOURCES_NOT_PRINTED=true LIVE_UNCHANGED=true")


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, ValueError, subprocess.SubprocessError, RuntimeError):
        print("R4A_ONB_INVENTORY=BLOCKED LIVE_UNCHANGED=true")
        raise SystemExit(1)
