#!/usr/bin/env python3
"""Create a stopped Onboarding candidate with a rotating UDP bearer mount."""

import base64
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import time


NAME = "ouf-onboarding-r4a-candidate"
EXPECTED = "f74c3a9f377b5ce93b5cab298fa24372de1602bc"
MANIFEST = Path("/opt/ouf/r4a-stage/identity-images.json")
TOKEN_DIR = Path("/run/ouf-onboarding-identity")
TOKEN_FILE = TOKEN_DIR / "token"


def docker(*args):
    return subprocess.run(["docker", *args], check=True, capture_output=True,
                          text=True, timeout=30).stdout.strip()


def inspect(name):
    return json.loads(docker("inspect", name))[0]


def mounts(descriptor):
    return sorted((x["Type"], x["Source"], x["Destination"], bool(x["RW"]))
                  for x in descriptor.get("Mounts") or [])


def token_preflight():
    directory = TOKEN_DIR.lstat()
    token = TOKEN_FILE.lstat()
    if (not stat.S_ISDIR(directory.st_mode) or directory.st_uid != 0
        or directory.st_gid != 10003 or stat.S_IMODE(directory.st_mode) != 0o750
        or not stat.S_ISREG(token.st_mode) or token.st_uid != 0
        or token.st_gid != 10003 or stat.S_IMODE(token.st_mode) != 0o640):
        raise RuntimeError("TOKEN_METADATA_UNSAFE")
    value = TOKEN_FILE.read_text().strip()
    if len(value) > 16384 or value.count(".") != 2:
        raise RuntimeError("TOKEN_FORMAT_INVALID")
    encoded = value.split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
    audience = claims.get("aud")
    audience = {audience} if isinstance(audience, str) else set(audience or [])
    if (claims.get("iss") != "https://auth.ouf-lab.it/realms/ouf"
        or "ouf-api-gateway" not in audience
        or "ouf.udp.identity.attestation.read" not in str(claims.get("scope", "")).split()
        or claims.get("ouf_actor_type") != "SERVICE" or claims.get("tenant_id") != "ouf-lab"
        or (claims.get("client_id") or claims.get("azp")) != "ouf-source-onboarding"
        or not isinstance(claims.get("exp"), int) or claims["exp"] - time.time() < 120):
        raise RuntimeError("TOKEN_CLAIMS_OR_EXPIRY_INVALID")


def main():
    if os.geteuid() != 0:
        raise RuntimeError("ROOT_REQUIRED")
    token_preflight()
    live = inspect("ouf-onboarding")
    record = json.loads(MANIFEST.read_text())["modules"]["onboarding"]
    image, old_image = inspect(record["image_id"]), inspect(live["Image"])
    host, config = live["HostConfig"], live["Config"]
    if (record["commit"] != EXPECTED or record["live_image_id"] != live["Image"]
        or image["Id"] != record["image_id"] or not live["State"]["Running"]
        or (image["Config"].get("Labels") or {}).get("org.opencontainers.image.revision")
           != EXPECTED or host.get("NetworkMode") != "ouf-backend"
        or set(live["NetworkSettings"]["Networks"]) != {"ouf-backend"}
        or config.get("User") != "10003:10003"
        or (host.get("RestartPolicy") or {}).get("Name") != "unless-stopped"
        or host.get("PortBindings") or host.get("Binds") or host.get("VolumesFrom")
        or host.get("Privileged") or host.get("ReadonlyRootfs") or host.get("ExtraHosts")
        or host.get("Dns") or host.get("DnsSearch") or host.get("CapAdd")
        or host.get("SecurityOpt") or host.get("Devices") or host.get("Tmpfs")
        or host.get("AutoRemove") or host.get("GroupAdd") or host.get("UsernsMode")
        or host.get("Init") or host.get("Ulimits") or host.get("CapDrop")
        or host.get("Memory") or host.get("MemorySwap") or host.get("NanoCpus")
        or host.get("CpuShares") or host.get("PidsLimit") or host.get("OomKillDisable")
        or host.get("CpusetCpus") or host.get("CpusetMems") or host.get("PidMode")
        or host.get("Sysctls")
        or config.get("Entrypoint") != old_image["Config"].get("Entrypoint")
        or config.get("Cmd") != old_image["Config"].get("Cmd")
        or config.get("WorkingDir") != old_image["Config"].get("WorkingDir")
        or (host.get("LogConfig") or {}).get("Type") != "json-file"):
        raise RuntimeError("LIVE_CONTAINER_SETTINGS_UNSUPPORTED")
    old_mounts = mounts(live)
    if len(old_mounts) != 5 or any(kind != "bind" for kind, _, _, _ in old_mounts):
        raise RuntimeError("LIVE_MOUNTS_CHANGED")
    environment = config.get("Env") or []
    if (any("\n" in value or "\r" in value or "=" not in value for value in environment)
        or any(value.startswith("OUF_ONB_UDP_IDENTITY_") for value in environment)):
        raise RuntimeError("LIVE_ENV_UNEXPECTED")
    try:
        inspect(NAME)
    except subprocess.CalledProcessError:
        pass
    else:
        raise RuntimeError("CANDIDATE_ALREADY_EXISTS")
    new_env = [*environment,
        "OUF_ONB_UDP_IDENTITY_GATEWAY_URL=https://api.ouf-lab.it",
        "OUF_ONB_UDP_IDENTITY_TOKEN_FILE=/run/ouf-onboarding-identity/token"]
    os.umask(0o077)
    fd, env_path = tempfile.mkstemp(prefix="ouf-r4a-onb-env-", dir="/run")
    created = False
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write("\n".join(new_env) + "\n")
        command = ["docker", "create", "--name", NAME, "--network", "ouf-backend",
                   "--restart", "unless-stopped", "--user", "10003:10003",
                   "--log-driver", "json-file", "--env-file", env_path]
        for key, value in (host.get("LogConfig") or {}).get("Config", {}).items():
            command.extend(["--log-opt", key + "=" + value])
        for kind, source, target, writable in old_mounts + [
            ("bind", str(TOKEN_DIR), str(TOKEN_DIR), False)]:
            if "," in source or "," in target:
                raise RuntimeError("MOUNT_PATH_UNSUPPORTED")
            spec = "type=bind,src=" + source + ",dst=" + target
            command.extend(["--mount", spec if writable else spec + ",readonly"])
        command.append(record["image_id"])
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=60)
        created = True
        candidate = inspect(NAME)
        if (candidate["Image"] != record["image_id"] or candidate["State"]["Running"]
            or candidate["Config"].get("User") != "10003:10003"
            or candidate["HostConfig"].get("NetworkMode") != "ouf-backend"
            or mounts(candidate) != sorted(old_mounts + [
                ("bind", str(TOKEN_DIR), str(TOKEN_DIR), False)])
            or {value.partition("=")[0]: value.partition("=")[2]
                for value in candidate["Config"].get("Env") or []}
               != {value.partition("=")[0]: value.partition("=")[2]
                   for value in new_env}):
            raise RuntimeError("CANDIDATE_READBACK_MISMATCH")
        print("R4A_ONB_CANDIDATE_PREPARED=true RUNNING=false IMAGE=" + EXPECTED)
        print("R4A_ONB_MOUNTS=LIVE_PLUS_TOKEN_DIRECTORY TOKEN_NOT_PRINTED=true")
        print("R4A_ONB_LIVE_UNCHANGED=true DB_UNCHANGED=true")
    except BaseException:
        if created:
            subprocess.run(["docker", "rm", NAME], capture_output=True, text=True)
        raise
    finally:
        Path(env_path).unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, IndexError, RuntimeError,
            subprocess.SubprocessError) as error:
        detail = str(error) if isinstance(error, RuntimeError) else "COMMAND_FAILED"
        print("R4A_ONB_CANDIDATE_BLOCKED=" + detail + " SECRETS_NOT_PRINTED=true")
        raise SystemExit(1)
