#!/usr/bin/env python3
"""Replace live UDP with the tested principal fix, with backup and automatic runtime rollback."""

import base64
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import types
from urllib.error import HTTPError
from urllib.request import Request, urlopen


STAGE = Path("/opt/ouf/r4a-stage")
MANIFEST = STAGE / "udp-principal-fix-image.json"
TARGET = "edaba2bff18a2aaf52d1180f21f0e68984cc3437"
PREVIOUS = "3402050b36ee28758e5255a57b0d32bc3983a34f"
SOURCE_REVISION = "7f70c4eaaed42ec441ceadf09aa13dbd905b83fc"
SOURCE_ID = "managed-cinema-8ec8ae90"
VERSION_ID = "68394f42-5c82-4127-a1f3-126516665749"
CONFIG_SHA = "2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891"
BASE = "https://api.ouf-lab.it"
LIVE = "ouf-udp"
CANDIDATE = "ouf-udp-principal-candidate"


def output(args, timeout=60):
    return subprocess.check_output(args, text=True, stderr=subprocess.PIPE,
                                   timeout=timeout).strip()


def docker(*args, timeout=60):
    return output(["docker", *args], timeout=timeout)


def inspect(name):
    return json.loads(docker("inspect", name))[0]


def mounts(container):
    return sorted((x["Type"], x["Source"], x["Destination"], bool(x["RW"]))
                  for x in container.get("Mounts") or [])


def flyway():
    return docker("exec", "ouf-postgres", "psql", "-U", "ouf_udp", "-d", "ouf_udp",
                  "-Atc", "select version from ouf_udp.flyway_schema_history "
                  "order by installed_rank desc limit 1")


def health(name, attempts):
    for number in range(attempts):
        if inspect(name)["State"]["Running"]:
            result = subprocess.run(["docker", "run", "--rm", "--network", "container:" + name,
                "curlimages/curl:8.16.0", "--max-time", "3", "-sS", "-o", "/dev/null",
                "-w", "%{http_code}", "http://127.0.0.1:8080/actuator/health"],
                capture_output=True, text=True, timeout=15)
            if result.returncode == 0 and result.stdout == "200":
                return True
        if number and number % 10 == 0:
            print("R4A_UDP_PRINCIPAL_HEALTH_WAIT_SECONDS=" + str(number * 2), flush=True)
        time.sleep(2)
    return False


def backup():
    os.umask(0o077)
    fd, name = tempfile.mkstemp(prefix="udp-before-principal-fix-", suffix=".dump", dir=STAGE)
    target = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            subprocess.run(["docker", "exec", "ouf-postgres", "pg_dump", "-U",
                "ouf_udp", "-d", "ouf_udp", "-Fc"], stdout=stream,
                stderr=subprocess.PIPE, check=True, timeout=600)
            stream.flush()
            os.fsync(stream.fileno())
        if target.stat().st_size < 1024:
            raise RuntimeError("UDP_BACKUP_TOO_SMALL")
        with target.open("rb") as stream:
            subprocess.run(["docker", "exec", "-i", "ouf-postgres", "pg_restore", "-l"],
                stdin=stream, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                check=True, timeout=90)
        print("R4A_UDP_PRINCIPAL_BACKUP=" + name +
              " BYTES=" + str(target.stat().st_size) + " RESTORE_LIST=PASS", flush=True)
        return target
    except BaseException:
        target.unlink(missing_ok=True)
        raise


def get(url, bearer):
    request = Request(url, headers={"Accept": "application/json",
                                    "Authorization": "Bearer " + bearer})
    try:
        with urlopen(request, timeout=25) as response:
            return response.status, json.loads(response.read(1048576))
    except HTTPError as error:
        error.read(1048576)
        return error.code, {}


def post(url, bearer, body):
    data = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode()
    request = Request(url, method="POST", data=data, headers={
        "Accept": "application/json", "Content-Type": "application/json",
        "Authorization": "Bearer " + bearer})
    try:
        with urlopen(request, timeout=100) as response:
            return response.status, json.loads(response.read(1048576))
    except HTTPError as error:
        error.read(1048576)
        return error.code, {}


def human_token():
    git = ["git", "-c", "safe.directory=/opt/ouf/semantic", "-C", "/opt/ouf/semantic"]
    if output([*git, "rev-parse", SOURCE_REVISION + "^{commit}"]) != SOURCE_REVISION:
        raise RuntimeError("PINNED_SEMANTIC_REVISION_MISSING")
    source = subprocess.check_output([*git, "show", SOURCE_REVISION +
        ":scripts/r4a_cinema_semantic_draft.py"], stderr=subprocess.DEVNULL)
    helper = types.ModuleType("r4a_cinema_semantic_draft")
    exec(compile(source, "r4a_cinema_semantic_draft.py", "exec"), helper.__dict__)
    helper.SCOPES = {"ouf.onboarding.configuration.write", "urban.identity.preflight"}
    token, _ = helper.human_token()
    segment = token.split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))
    if claims.get("exp", 0) < time.time() + 180:
        raise RuntimeError("HUMAN_TOKEN_LIFETIME_INSUFFICIENT")
    return token, claims["exp"]


def frozen_configuration(bearer):
    url = (BASE + "/api/onboarding/v1/sources/" + SOURCE_ID +
           "/onboarding-versions/" + VERSION_ID)
    status, body = get(url, bearer)
    if status != 200 or body.get("state") != "IN_REVIEW" or body.get("lock_version") != 2:
        raise RuntimeError("FROZEN_VERSION_READ_FAILED_HTTP_" + str(status))
    configuration = body.get("configuration")
    digest = hashlib.sha256(json.dumps(configuration, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False).encode()).hexdigest()
    if (digest != CONFIG_SHA or body.get("configuration_hash") != "sha256:" + CONFIG_SHA):
        raise RuntimeError("FROZEN_CONFIGURATION_CHANGED")
    return configuration


def candidate(manifest, live):
    image = inspect(manifest["image_id"])
    old_image = inspect(live["Image"])
    host, config = live["HostConfig"], live["Config"]
    if (manifest["commit"] != TARGET or manifest["previous_commit"] != PREVIOUS
        or manifest["previous_live_image_id"] != live["Image"]
        or image["Id"] != manifest["image_id"]
        or (image["Config"].get("Labels") or {}).get("org.opencontainers.image.revision") != TARGET
        or (old_image["Config"].get("Labels") or {}).get("org.opencontainers.image.revision") != PREVIOUS
        or not live["State"]["Running"] or host.get("NetworkMode") != "ouf-backend"
        or set(live["NetworkSettings"]["Networks"]) != {"ouf-backend"}
        or config.get("User") != "10004:10004"
        or (host.get("RestartPolicy") or {}).get("Name") != "unless-stopped"
        or host.get("PortBindings") or host.get("Binds") or host.get("VolumesFrom")
        or host.get("Privileged") or host.get("ReadonlyRootfs") or host.get("ExtraHosts")
        or host.get("Dns") or host.get("DnsSearch") or host.get("CapAdd")
        or host.get("SecurityOpt") or host.get("Devices") or host.get("Tmpfs")
        or host.get("AutoRemove") or host.get("Init") or host.get("Ulimits")
        or host.get("CapDrop") or host.get("GroupAdd") or host.get("Memory")
        or host.get("MemorySwap") or host.get("NanoCpus") or host.get("CpuShares")
        or host.get("PidsLimit") or host.get("OomKillDisable")
        or host.get("CpusetCpus") or host.get("CpusetMems")
        or host.get("UsernsMode") or host.get("PidMode") or host.get("Sysctls")
        or config.get("Entrypoint") != old_image["Config"].get("Entrypoint")
        or config.get("Cmd") != old_image["Config"].get("Cmd")
        or config.get("WorkingDir") != old_image["Config"].get("WorkingDir")
        or (host.get("LogConfig") or {}).get("Type") != "json-file"):
        raise RuntimeError("LIVE_CONFIGURATION_UNSUPPORTED")
    old_mounts = mounts(live)
    if len(old_mounts) != 2 or any(kind != "bind" for kind, _, _, _ in old_mounts):
        raise RuntimeError("LIVE_MOUNTS_CHANGED")
    environment = config.get("Env") or []
    if (any("\n" in item or "\r" in item or "=" not in item for item in environment)
        or not {"OUF_UDP_IAM_ENABLED", "OUF_UDP_IAM_ISSUER", "OUF_UDP_IAM_AUDIENCE"}
             <= {entry.partition("=")[0] for entry in environment}):
        raise RuntimeError("LIVE_IAM_ENV_CHANGED")
    try:
        inspect(CANDIDATE)
    except subprocess.CalledProcessError:
        pass
    else:
        raise RuntimeError("CANDIDATE_NAME_OCCUPIED")
    fd, env_file = tempfile.mkstemp(prefix="ouf-r4a-udp-principal-env-", dir="/run")
    created = False
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write("\n".join(environment) + "\n")
        args = ["create", "--name", CANDIDATE, "--network", "ouf-backend",
                "--restart", "unless-stopped", "--user", "10004:10004",
                "--log-driver", "json-file", "--env-file", env_file]
        for key, value in (host.get("LogConfig") or {}).get("Config", {}).items():
            args.extend(["--log-opt", key + "=" + value])
        for kind, source, destination, writable in old_mounts:
            if "," in source or "," in destination:
                raise RuntimeError("MOUNT_PATH_UNSUPPORTED")
            spec = "type=bind,src=" + source + ",dst=" + destination
            args.extend(["--mount", spec if writable else spec + ",readonly"])
        docker(*args, manifest["image_id"])
        created = True
        new = inspect(CANDIDATE)
        if (new["Image"] != manifest["image_id"] or new["State"]["Running"]
            or new["Config"].get("User") != config.get("User")
            or new["HostConfig"].get("NetworkMode") != host.get("NetworkMode")
            or mounts(new) != old_mounts
            or {x.partition("=")[0]: x.partition("=")[2] for x in new["Config"]["Env"]}
               != {x.partition("=")[0]: x.partition("=")[2] for x in environment}):
            raise RuntimeError("CANDIDATE_READBACK_MISMATCH")
        print("R4A_UDP_PRINCIPAL_CANDIDATE=PASS STOPPED=true MOUNTS=2", flush=True)
        return new
    except BaseException:
        if created:
            docker("rm", CANDIDATE)
        raise
    finally:
        Path(env_file).unlink(missing_ok=True)


def rollback(previous, failed):
    try:
        docker("update", "--restart", "no", LIVE)
        if inspect(LIVE)["State"]["Running"]:
            docker("stop", "--time", "30", LIVE)
        docker("rename", LIVE, failed)
        docker("rename", previous, LIVE)
        docker("start", LIVE)
        print("R4A_UDP_PRINCIPAL_ROLLBACK=" +
              ("PASS" if health(LIVE, 25) else "UNHEALTHY"), flush=True)
    except (OSError, subprocess.SubprocessError, RuntimeError):
        print("R4A_UDP_PRINCIPAL_ROLLBACK=MANUAL_RECOVERY_REQUIRED", flush=True)


def preflight(bearer, configuration):
    url = BASE + "/api/udp/v1/governance/identity/preflight"
    status, body = post(url, bearer, {"sourceId": SOURCE_ID,
        "configurationHash": "sha256:" + CONFIG_SHA, "configuration": configuration})
    if status != 200:
        raise RuntimeError("AUTHENTICATED_PREFLIGHT_HTTP_" + str(status))
    attestation = body.get("attestationId")
    if (not isinstance(attestation, str) or not re.fullmatch(r"[0-9a-f-]{36}", attestation)
        or body.get("configurationHash") != "sha256:" + CONFIG_SHA
        or body.get("sourceId") != SOURCE_ID or body.get("tenantId") != "ouf-lab"
        or body.get("valid") is not True or not isinstance(body.get("indexedObjects"), int)):
        raise RuntimeError("AUTHENTICATED_PREFLIGHT_RESULT_INVALID")
    status, read = get(url + "?id=" + attestation, bearer)
    if status != 200 or read != body:
        raise RuntimeError("AUTHENTICATED_PREFLIGHT_READ_FAILED_HTTP_" + str(status))
    print("R4A_UDP_PRINCIPAL_PREFLIGHT=PASS INDEXED_OBJECTS=" +
          str(body["indexedObjects"]) + " ATTESTATION_ID=" + attestation, flush=True)


def main():
    if os.geteuid() != 0 or not MANIFEST.is_file():
        raise RuntimeError("ROOT_AND_STAGED_MANIFEST_REQUIRED")
    manifest = json.loads(MANIFEST.read_text())
    live = inspect(LIVE)
    if not health(LIVE, 1) or flyway() != "34":
        raise RuntimeError("LIVE_HEALTH_OR_FLYWAY_CHANGED")
    # Complete the interactive device authorization while the old runtime is still live.
    bearer, token_expiry = human_token()
    configuration = frozen_configuration(bearer)
    new = candidate(manifest, live)
    previous = "ouf-udp-principal-rollback-" + live["Id"][:12]
    failed = "ouf-udp-principal-failed-" + new["Id"][:12]
    snapshot, swapped, renamed = None, False, False
    try:
        for name in (previous, failed):
            try:
                inspect(name)
            except subprocess.CalledProcessError:
                pass
            else:
                raise RuntimeError("ROLLBACK_NAME_OCCUPIED")
        if token_expiry < time.time() + 120:
            raise RuntimeError("HUMAN_TOKEN_EXPIRES_BEFORE_SWITCH")
        print("R4A_UDP_PRINCIPAL_STOPPING_LIVE=true", flush=True)
        docker("stop", "--time", "60", LIVE)
        snapshot = backup()
        docker("rename", LIVE, previous)
        renamed = True
        docker("rename", CANDIDATE, LIVE)
        swapped = True
        docker("start", LIVE)
        if not health(LIVE, 45) or flyway() != "34":
            raise RuntimeError("NEW_RUNTIME_HEALTH_OR_FLYWAY_FAILED")
        preflight(bearer, configuration)
        print("R4A_UDP_PRINCIPAL_SWITCH=PASS LIVE_IMAGE=" + TARGET +
              " FLYWAY=34", flush=True)
        print("R4A_UDP_PRINCIPAL_ROLLBACK_CONTAINER=" + previous, flush=True)
        print("R4A_UDP_PRINCIPAL_BACKUP_RETAINED=" + str(snapshot), flush=True)
    except BaseException:
        if swapped:
            rollback(previous, failed)
        else:
            try:
                if renamed:
                    docker("rename", previous, LIVE)
                if not inspect(LIVE)["State"]["Running"]:
                    docker("start", LIVE)
                print("R4A_UDP_PRINCIPAL_PRE_SWITCH_RECOVERY=PASS", flush=True)
            except (OSError, subprocess.SubprocessError, RuntimeError):
                print("R4A_UDP_PRINCIPAL_PRE_SWITCH_RECOVERY=MANUAL_REQUIRED", flush=True)
            try:
                if not inspect(CANDIDATE)["State"]["Running"]:
                    docker("rm", CANDIDATE)
            except (OSError, subprocess.SubprocessError, RuntimeError):
                print("R4A_UDP_PRINCIPAL_CANDIDATE_CLEANUP=MANUAL_REQUIRED", flush=True)
        print("R4A_UDP_PRINCIPAL_BACKUP_RETAINED=" + str(snapshot) +
              " DB_NOT_AUTOMATICALLY_RESTORED=true", flush=True)
        raise


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, IndexError,
            subprocess.SubprocessError, RuntimeError) as error:
        reason = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_UDP_PRINCIPAL_SWITCH_BLOCKED=" + reason +
              " TOKEN_NOT_PRINTED=true", file=sys.stderr)
        raise SystemExit(1)
