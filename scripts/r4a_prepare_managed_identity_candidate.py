#!/usr/bin/env python3
"""Build the green combined release and create an inert clone of the live runtime."""
import argparse
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import r4a_managed_identity_release_inventory as inventory

REVISION = "6340d5bf120e09b47c32177656e2c377a4c03640"
NAME = "ouf-onboarding-r4a-managed-identity-candidate"
TAG = "ouf-onboarding:managed-identity-" + REVISION[:7]
ROOT = Path("/etc/ouf/deploy-snapshots")
STATE = ROOT / "onboarding-managed-identity-release.json"


def mounts(doc):
    return sorted((m["Type"], m["Source"], m["Destination"], m["RW"]) for m in doc["Mounts"])


def stable(doc):
    return {key: doc[key] for key in ("Id", "Image", "Config", "HostConfig", "Mounts")}


def runtime_guard(old, new_image=None):
    host, config = old["HostConfig"], old["Config"]
    unsupported = ("PortBindings", "Binds", "VolumesFrom", "Privileged", "ReadonlyRootfs", "ExtraHosts",
        "Dns", "DnsSearch", "CapAdd", "SecurityOpt", "Devices", "Tmpfs", "AutoRemove", "GroupAdd",
        "UsernsMode", "Init", "Ulimits", "CapDrop", "Memory", "MemorySwap", "NanoCpus", "CpuShares",
        "PidsLimit", "OomKillDisable", "CpusetCpus", "CpusetMems", "PidMode", "Sysctls")
    if (not old["State"]["Running"] or config.get("User") != "10003:10003"
            or host.get("NetworkMode") != "ouf-backend"
            or set(old["NetworkSettings"]["Networks"]) != {"ouf-backend"}
            or host.get("RestartPolicy", {}).get("Name") != "unless-stopped"
            or host.get("LogConfig", {}).get("Type") != "json-file"
            or any(host.get(key) for key in unsupported) or config.get("Healthcheck")
            or any(m[0] != "bind" or m[3] for m in mounts(old))):
        raise RuntimeError("OWNER_RUNTIME_SETTINGS_UNSUPPORTED")
    inventory.environment(old)  # Reject ambiguous env, including duplicate keys.
    if any("\n" in value or "\r" in value for value in config.get("Env") or []):
        raise RuntimeError("OWNER_ENV_FORMAT_UNSUPPORTED")
    if any(any(c in source + target for c in ",\n\r") for _, source, target, _ in mounts(old)):
        raise RuntimeError("OWNER_MOUNT_PATH_UNSUPPORTED")
    if new_image is not None:
        for key in ("User", "Entrypoint", "Cmd", "WorkingDir"):
            if config.get(key) != new_image["Config"].get(key):
                raise RuntimeError("OWNER_IMAGE_LAUNCH_CONTRACT_CHANGED")


def optional(name):
    # Listing an absent container succeeds with no matching name. Do not infer
    # absence from version-dependent Docker inspect error messages.
    try:
        names = inventory.run(["docker", "container", "ls", "--all", "--format", "{{.Names}}"])
        if name not in names.splitlines():
            return None
        return inventory.inspect(name)
    except subprocess.CalledProcessError:
        raise RuntimeError("OWNER_DOCKER_INSPECT_FAILED") from None


def candidate_matches(candidate, old, image):
    return (candidate["Image"] == image["Id"] and not candidate["State"]["Running"]
        and candidate["State"]["Status"] == "created"
        and inventory.environment(candidate) == inventory.environment(old)
        and mounts(candidate) == mounts(old)
        and candidate["HostConfig"].get("NetworkMode") == "ouf-backend"
        and set(candidate["NetworkSettings"]["Networks"]) == {"ouf-backend"}
        and "ouf-onboarding" in candidate["NetworkSettings"]["Networks"]["ouf-backend"].get("Aliases", [])
        and candidate["HostConfig"].get("RestartPolicy", {}).get("Name") == "no"
        and candidate["HostConfig"].get("LogConfig") == old["HostConfig"].get("LogConfig")
        and all(candidate["Config"].get(key) == old["Config"].get(key)
                for key in ("User", "Entrypoint", "Cmd", "WorkingDir")))


def build(repo, log):
    safe = ["git", "-c", "safe.directory=" + str(repo.resolve(strict=True)), "-C", str(repo)]
    with log.open("wb") as stream:
        archive = subprocess.Popen([*safe, "archive", "--format=tar", REVISION],
                                   stdout=subprocess.PIPE, stderr=stream)
        try:
            result = subprocess.run(["docker", "build", "--pull=false", "--quiet", "--label",
                "org.opencontainers.image.revision=" + REVISION, "-t", TAG, "-"],
                stdin=archive.stdout, stdout=stream, stderr=stream, timeout=1800)
        finally:
            archive.stdout.close()
        if archive.wait(timeout=30) or result.returncode:
            raise RuntimeError("OWNER_CANDIDATE_BUILD_FAILED")


def main(args):
    if os.geteuid() != 0:
        raise RuntimeError("ROOT_REQUIRED")
    os.umask(0o077)
    meta = ROOT.lstat()
    if (not stat.S_ISDIR(meta.st_mode) or meta.st_uid != 0
            or stat.S_IMODE(meta.st_mode) != 0o700):
        raise RuntimeError("OWNER_STAGE_DIRECTORY_UNSAFE")
    args.revision = REVISION
    old = inventory.inspect("ouf-onboarding")
    runtime_guard(old)
    if not inventory.main(args):
        raise RuntimeError("OWNER_RELEASE_PREREQUISITES_FAILED")
    if stable(inventory.inspect("ouf-onboarding")) != stable(old):
        raise RuntimeError("OWNER_LIVE_CHANGED_DURING_INVENTORY")
    folder = Path(tempfile.mkdtemp(prefix="onboarding-managed-identity-", dir=ROOT))
    print("R4A_MANAGED_IDENTITY_PREPARE=BUILDING LIVE_SWITCH=false ATTESTATION_POST=false", flush=True)
    print("R4A_MANAGED_IDENTITY_BUILD_LOG=" + str(folder / "build.log") + " PRIVATE=true", flush=True)
    build(args.repo, folder / "build.log")
    image = inventory.inspect(TAG)
    if (image["Config"].get("Labels") or {}).get("org.opencontainers.image.revision") != REVISION:
        raise RuntimeError("OWNER_CANDIDATE_IMAGE_PROVENANCE_MISMATCH")
    runtime_guard(old, image)
    if stable(inventory.inspect("ouf-onboarding")) != stable(old) or not inventory.main(args):
        raise RuntimeError("OWNER_LIVE_CHANGED_DURING_BUILD")
    existing = optional(NAME)
    if existing is not None and not candidate_matches(existing, old, image):
        raise RuntimeError("OWNER_EXISTING_CANDIDATE_DRIFT")
    if STATE.exists():
        metadata = STATE.lstat()
        if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != 0
                or stat.S_IMODE(metadata.st_mode) != 0o600):
            raise RuntimeError("OWNER_RELEASE_STATE_UNSAFE")
        previous = json.loads(STATE.read_text())
        if (existing is None or stable(previous["old"]) != stable(old)
                or previous.get("candidate_id") != existing["Id"]
                or previous.get("revision") != REVISION or previous.get("image_id") != image["Id"]):
            raise RuntimeError("OWNER_RELEASE_STATE_DRIFT")
    env_path = folder / "candidate.env"
    created_id = None
    try:
        if existing is None:
            with env_path.open("x") as stream:
                stream.write("\n".join(old["Config"]["Env"]) + "\n")
            command = ["docker", "create", "--name", NAME, "--network", "ouf-backend",
                "--network-alias", "ouf-onboarding", "--restart", "no", "--user", "10003:10003",
                "--log-driver", "json-file", "--env-file", str(env_path)]
            for key, value in old["HostConfig"]["LogConfig"].get("Config", {}).items():
                command.extend(["--log-opt", key + "=" + value])
            for _, source, target, _ in mounts(old):
                command.extend(["--mount", "type=bind,src=" + source + ",dst=" + target + ",readonly"])
            command.append(image["Id"])
            created_id = inventory.run(command).strip()
        candidate = inventory.inspect(NAME)
        if (candidate["Id"] != (created_id or existing["Id"])
                or not candidate_matches(candidate, old, image)):
            raise RuntimeError("OWNER_CANDIDATE_READBACK_MISMATCH")
        if stable(inventory.inspect("ouf-onboarding")) != stable(old):
            raise RuntimeError("OWNER_LIVE_CHANGED_DURING_PREPARE")
        if not STATE.exists():
            staged = folder / "state.json"
            staged.write_text(json.dumps({"revision": REVISION, "image_id": image["Id"], "old": old,
                "candidate_id": candidate["Id"], "candidate_name": NAME}, sort_keys=True) + "\n")
            os.link(staged, STATE)  # Atomic creation; never overwrite an unrelated state.
        print("R4A_MANAGED_IDENTITY_CANDIDATE=PASS STOPPED=true ENV_AND_MOUNTS_PRESERVED=true")
        print("R4A_MANAGED_IDENTITY_STATE=" + str(STATE) + " PRIVATE=true")
        print("R4A_MANAGED_IDENTITY_PREPARE=PASS LIVE_UNCHANGED=true DB_UNCHANGED=true SECRETS_NOT_PRINTED=true")
    except BaseException:
        if created_id:
            current = optional(NAME)
            if current is not None and current["Id"] == created_id and not current["State"]["Running"]:
                inventory.run(["docker", "rm", NAME])
        raise
    finally:
        env_path.unlink(missing_ok=True)


if __name__ == "__main__":
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("/opt/ouf/onboarding"))
    try:
        main(parser.parse_args())
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_MANAGED_IDENTITY_PREPARE=BLOCKED CODE=" + code + " SECRETS_NOT_PRINTED=true")
        raise SystemExit(1)
