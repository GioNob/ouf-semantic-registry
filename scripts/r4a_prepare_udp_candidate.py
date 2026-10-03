#!/usr/bin/env python3
"""Create but do not start a pinned UDP IAM candidate preserving live settings."""

import json
import os
from pathlib import Path
import subprocess
import tempfile


NAME = "ouf-udp-r4a-candidate"
EXPECTED = "3402050b36ee28758e5255a57b0d32bc3983a34f"
MANIFEST = Path("/opt/ouf/r4a-stage/identity-images.json")
PROJECTION = Path("/opt/ouf/installation/active-projection.json")


def docker(*args):
    return subprocess.run(["docker", *args], check=True, capture_output=True, text=True).stdout


def inspected(name):
    return json.loads(docker("inspect", name))[0]


def mounts(descriptor):
    return sorted((x["Type"], x["Source"], x["Destination"], bool(x["RW"]))
                  for x in descriptor.get("Mounts") or [])


def main():
    if os.geteuid() != 0:
        raise RuntimeError("R4A_CANDIDATE_REQUIRES_ROOT")
    live = inspected("ouf-udp")
    record = json.loads(MANIFEST.read_text())["modules"]["udp"]
    image = inspected(record["image_id"])
    old_image = inspected(live["Image"])
    projection = json.loads(PROJECTION.read_text())["gateway"]
    host, config = live["HostConfig"], live["Config"]
    if (record["commit"] != EXPECTED or record["live_image_id"] != live["Image"]
        or image["Id"] != record["image_id"] or not live["State"]["Running"]):
        raise RuntimeError("R4A_IMAGE_OR_LIVE_STATE_CHANGED")
    if (image["Config"].get("Labels") or {}).get("org.opencontainers.image.revision") != EXPECTED:
        raise RuntimeError("R4A_IMAGE_REVISION_INVALID")
    if (host.get("NetworkMode") != "ouf-backend" or set(live["NetworkSettings"]["Networks"]) != {"ouf-backend"}
        or config.get("User") != "10004:10004" or (host.get("RestartPolicy") or {}).get("Name") != "unless-stopped"
        or host.get("PortBindings") or host.get("Binds") or host.get("VolumesFrom")
        or host.get("Privileged") or host.get("ReadonlyRootfs") or host.get("ExtraHosts")
        or host.get("Dns") or host.get("DnsSearch") or host.get("CapAdd") or host.get("SecurityOpt")
        or host.get("Devices") or host.get("Tmpfs") or host.get("AutoRemove")
        or host.get("Init") or host.get("Ulimits") or host.get("CapDrop") or host.get("GroupAdd")
        or host.get("Memory") or host.get("MemorySwap") or host.get("NanoCpus")
        or host.get("CpuShares") or host.get("PidsLimit") or host.get("OomKillDisable")
        or host.get("CpusetCpus") or host.get("CpusetMems") or host.get("UsernsMode")
        or host.get("PidMode") or host.get("Sysctls")
        or config.get("Entrypoint") != old_image["Config"].get("Entrypoint")
        or config.get("Cmd") != old_image["Config"].get("Cmd")
        or config.get("WorkingDir") != old_image["Config"].get("WorkingDir")):
        raise RuntimeError("R4A_UNSUPPORTED_LIVE_CONTAINER_SETTING")
    old_mounts = mounts(live)
    if len(old_mounts) != 2 or any(kind != "bind" for kind, _, _, _ in old_mounts):
        raise RuntimeError("R4A_BIND_MOUNTS_CHANGED")
    if (host.get("LogConfig") or {}).get("Type") != "json-file":
        raise RuntimeError("R4A_LOG_DRIVER_CHANGED")
    environment = config.get("Env") or []
    if any("\n" in value or "\r" in value or "=" not in value for value in environment):
        raise RuntimeError("R4A_ENV_FILE_UNSAFE")
    if any(value.startswith("OUF_UDP_IAM_") for value in environment):
        raise RuntimeError("R4A_IAM_ALREADY_CONFIGURED")
    issuer, audience = projection.get("issuerUrl"), projection.get("requiredAudience")
    if issuer != "https://auth.ouf-lab.it/realms/ouf" or audience != "ouf-api-gateway":
        raise RuntimeError("R4A_PROJECTION_CHANGED")
    try:
        inspected(NAME)
    except subprocess.CalledProcessError:
        pass
    else:
        raise RuntimeError("R4A_CANDIDATE_ALREADY_EXISTS")
    new_env = [*environment, "OUF_UDP_IAM_ENABLED=true",
               "OUF_UDP_IAM_ISSUER=" + issuer, "OUF_UDP_IAM_AUDIENCE=" + audience]
    os.umask(0o077)
    fd, env_path = tempfile.mkstemp(prefix="ouf-r4a-udp-env-", dir="/run")
    created = False
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write("\n".join(new_env) + "\n")
        cmd = ["docker", "create", "--name", NAME, "--network", "ouf-backend",
               "--restart", "unless-stopped", "--user", "10004:10004",
               "--log-driver", "json-file", "--env-file", env_path]
        for key, value in (host.get("LogConfig") or {}).get("Config", {}).items():
            cmd.extend(["--log-opt", key + "=" + value])
        for kind, source, target, writable in old_mounts:
            if "," in source or "," in target:
                raise RuntimeError("R4A_MOUNT_PATH_UNSUPPORTED")
            spec = "type=bind,src=" + source + ",dst=" + target
            cmd.extend(["--mount", spec if writable else spec + ",readonly"])
        cmd.append(record["image_id"])
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        created = True
        candidate = inspected(NAME)
        actual_env = candidate["Config"].get("Env") or []
        if (candidate["Image"] != record["image_id"] or candidate["State"]["Running"]
            or candidate["Config"].get("User") != "10004:10004"
            or candidate["HostConfig"].get("NetworkMode") != "ouf-backend"
            or mounts(candidate) != old_mounts
            or {x.partition("=")[0]: x.partition("=")[2] for x in actual_env}
               != {x.partition("=")[0]: x.partition("=")[2] for x in new_env}):
            raise RuntimeError("R4A_CANDIDATE_READBACK_MISMATCH")
        print("R4A_UDP_CANDIDATE_PREPARED=true RUNNING=false")
        print("R4A_UDP_CANDIDATE_IMAGE=" + record["commit"])
        print("R4A_UDP_CANDIDATE_MOUNTS=" + str(len(old_mounts)) + " MATCH_LIVE=true")
        print("R4A_UDP_CANDIDATE_ENV=LIVE_PLUS_THREE_IAM")
        print("R4A_UDP_LIVE_UNCHANGED=true DB_UNCHANGED=true SECRETS_PRINTED=false")
    except BaseException:
        if created:
            subprocess.run(["docker", "rm", NAME], capture_output=True, text=True)
        raise
    finally:
        Path(env_path).unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, IndexError, subprocess.CalledProcessError,
            RuntimeError) as error:
        detail = str(error) if not isinstance(error, subprocess.CalledProcessError) else "DOCKER_COMMAND_FAILED"
        print("R4A_UDP_CANDIDATE_BLOCKED=" + type(error).__name__ + ":" + detail)
        raise SystemExit(1)
