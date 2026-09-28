#!/usr/bin/env python3
"""Read-only, secret-redacted deployment contract for the staged UDP image."""

import json
from pathlib import Path
import subprocess


MANIFEST = Path("/opt/ouf/r4a-stage/identity-images.json")
PROJECTION = Path("/opt/ouf/installation/active-projection.json")
EXPECTED_COMMIT = "d9626a91b3252b6bc0380f81e4f7a141bda4f3e7"


def docker(*args):
    return subprocess.run(["docker", *args], check=True, capture_output=True, text=True).stdout


def main():
    current = json.loads(docker("inspect", "ouf-udp"))[0]
    manifest = json.loads(MANIFEST.read_text())["modules"]["udp"]
    staged = json.loads(docker("image", "inspect", manifest["image_id"]))[0]
    old_image = json.loads(docker("image", "inspect", current["Image"]))[0]
    projection = json.loads(PROJECTION.read_text())
    host, config = current["HostConfig"], current["Config"]
    image_config = old_image["Config"]
    if manifest["commit"] != EXPECTED_COMMIT or staged["Id"] != manifest["image_id"]:
        raise RuntimeError("STAGED_UDP_IMAGE_MISMATCH")
    if (staged["Config"].get("Labels") or {}).get("org.opencontainers.image.revision") != EXPECTED_COMMIT:
        raise RuntimeError("STAGED_UDP_REVISION_MISMATCH")
    env = config.get("Env") or []
    mounts = current.get("Mounts") or []
    binds = host.get("Binds") or []
    print("UDP_ROLLOUT_INVENTORY=READ_ONLY")
    print("UDP_STAGED_COMMIT=" + EXPECTED_COMMIT)
    print("UDP_STAGED_DIFFERS_FROM_LIVE=" + str(staged["Id"] != current["Image"]).lower())
    print("UDP_LIVE_RUNNING=" + str(current["State"]["Running"]).lower())
    print("UDP_NETWORK_MODE=" + str(host.get("NetworkMode")))
    print("UDP_NETWORKS=" + ",".join(sorted(current["NetworkSettings"]["Networks"])))
    print("UDP_USER=" + str(config.get("User")))
    print("UDP_RESTART=" + str((host.get("RestartPolicy") or {}).get("Name")))
    print("UDP_BIND_COUNT=" + str(len(binds)))
    print("UDP_MOUNTS=" + json.dumps(sorted(({"destination": x["Destination"],
         "type": x["Type"], "readOnly": not x["RW"]} for x in mounts),
         key=lambda x: x["destination"]), sort_keys=True))
    print("UDP_HOSTCONFIG_MOUNTS=" + str(len(host.get("Mounts") or [])))
    print("UDP_VOLUMES_FROM=" + str(len(host.get("VolumesFrom") or [])))
    print("UDP_PORT_BINDINGS=" + str(len(host.get("PortBindings") or {})))
    print("UDP_PRIVILEGED=" + str(host.get("Privileged", False)).lower())
    print("UDP_READ_ONLY_ROOT=" + str(host.get("ReadonlyRootfs", False)).lower())
    print("UDP_LOG_DRIVER=" + str((host.get("LogConfig") or {}).get("Type")))
    print("UDP_ENTRYPOINT_IMAGE_DEFAULT=" + str(config.get("Entrypoint") == image_config.get("Entrypoint")).lower())
    print("UDP_CMD_IMAGE_DEFAULT=" + str(config.get("Cmd") == image_config.get("Cmd")).lower())
    print("UDP_WORKDIR_IMAGE_DEFAULT=" + str(config.get("WorkingDir") == image_config.get("WorkingDir")).lower())
    print("UDP_ENV_MULTILINE_COUNT=" + str(sum("\n" in x or "\r" in x for x in env)))
    print("UDP_IAM_ENV_ALREADY_PRESENT=" + str(any(x.startswith("OUF_UDP_IAM_") for x in env)).lower())
    print("UDP_EXTRA_HOSTS=" + str(len(host.get("ExtraHosts") or [])))
    print("UDP_DNS_OVERRIDES=" + str(len(host.get("Dns") or []) + len(host.get("DnsSearch") or [])))
    print("UDP_CAP_ADDS=" + str(len(host.get("CapAdd") or [])))
    print("UDP_SECURITY_OPTS=" + str(len(host.get("SecurityOpt") or [])))
    print("PROJECTION_ISSUER=" + str(projection.get("gateway", {}).get("issuerUrl", "MISSING")))
    print("PROJECTION_AUDIENCE=" + str(projection.get("gateway", {}).get("requiredAudience", "MISSING")))
    print("POSTGRES_PGDUMP_VERSION=" + docker("exec", "ouf-postgres", "pg_dump", "--version").strip())
    print("SECRETS_AND_MOUNT_SOURCES_NOT_PRINTED=true CONTAINERS_UNCHANGED=true")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, IndexError, subprocess.CalledProcessError, RuntimeError) as error:
        print("UDP_ROLLOUT_INVENTORY_BLOCKED=" + type(error).__name__)
        raise SystemExit(1)
