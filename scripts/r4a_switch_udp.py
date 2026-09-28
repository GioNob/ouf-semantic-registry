#!/usr/bin/env python3
"""Stop UDP, back up PostgreSQL, switch to the staged IAM image, retain rollback."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import time


CANDIDATE = "ouf-udp-r4a-candidate"
LIVE = "ouf-udp"
STAGE = Path("/opt/ouf/r4a-stage")
EXPECTED = "d9626a91b3252b6bc0380f81e4f7a141bda4f3e7"


def docker(*args):
    return subprocess.run(["docker", *args], check=True, capture_output=True, text=True).stdout.strip()


def inspect(name):
    return json.loads(docker("inspect", name))[0]


def health(name, attempts):
    for number in range(attempts):
        running = inspect(name)["State"]["Running"]
        if running:
            response = subprocess.run(["docker", "run", "--rm", "--network", "container:" + name,
                "curlimages/curl:8.16.0", "--max-time", "3", "-sS", "-o", "/dev/null",
                "-w", "%{http_code}", "http://127.0.0.1:8080/actuator/health"],
                capture_output=True, text=True, timeout=15)
            if response.returncode == 0 and response.stdout == "200":
                return True
        if number and number % 10 == 0:
            print("R4A_UDP_HEALTH_WAIT_SECONDS=" + str(number * 2), flush=True)
        time.sleep(2)
    return False


def gateway_reachability():
    result = subprocess.run(["docker", "run", "--rm", "--network", "container:ouf-apisix",
        "curlimages/curl:8.16.0", "--max-time", "5", "-sS", "-o", "/dev/null",
        "-w", "%{http_code}", "http://ouf-udp:8080/actuator/health"],
        capture_output=True, text=True, timeout=18)
    return result.returncode == 0 and result.stdout == "200"


def backup():
    os.umask(0o077)
    fd, name = tempfile.mkstemp(prefix="udp-before-r4a-", suffix=".dump", dir=STAGE)
    target = Path(name)
    try:
        with os.fdopen(fd, "wb") as out:
            subprocess.run(["docker", "exec", "ouf-postgres", "pg_dump", "-U", "ouf_udp",
                            "-d", "ouf_udp", "-Fc"], stdout=out, stderr=subprocess.PIPE,
                           check=True, timeout=600)
            out.flush()
            os.fsync(out.fileno())
        if target.stat().st_size < 1024:
            raise RuntimeError("R4A_UDP_BACKUP_TOO_SMALL")
        with target.open("rb") as source:
            subprocess.run(["docker", "exec", "-i", "ouf-postgres", "pg_restore", "-l"],
                           stdin=source, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                           check=True, timeout=90)
        print("R4A_UDP_DB_BACKUP=" + name + " BYTES=" + str(target.stat().st_size)
              + " RESTORE_LIST=PASS", flush=True)
        return target
    except BaseException:
        target.unlink(missing_ok=True)
        raise


def rollback_runtime(previous, failed):
    try:
        docker("update", "--restart", "no", LIVE)
        if inspect(LIVE)["State"]["Running"]:
            docker("stop", "--time", "30", LIVE)
        docker("rename", LIVE, failed)
        docker("rename", previous, LIVE)
        docker("start", LIVE)
        if health(LIVE, 25):
            print("R4A_UDP_RUNTIME_ROLLBACK=PASS PREVIOUS_IMAGE_RUNNING=true", flush=True)
        else:
            print("R4A_UDP_RUNTIME_ROLLBACK=BLOCKED PREVIOUS_IMAGE_UNHEALTHY=true", flush=True)
    except (OSError, subprocess.SubprocessError, RuntimeError):
        print("R4A_UDP_RUNTIME_ROLLBACK=BLOCKED MANUAL_RECOVERY_REQUIRED=true", flush=True)


def main():
    if os.geteuid() != 0:
        raise RuntimeError("R4A_UDP_SWITCH_REQUIRES_ROOT")
    manifest = json.loads((STAGE / "identity-images.json").read_text())["modules"]["udp"]
    old, new = inspect(LIVE), inspect(CANDIDATE)
    if (manifest["commit"] != EXPECTED or old["Image"] != manifest["live_image_id"]
        or new["Image"] != manifest["image_id"] or not old["State"]["Running"]
        or new["State"]["Running"] or old["HostConfig"]["NetworkMode"] != "ouf-backend"):
        raise RuntimeError("R4A_UDP_SWITCH_PREFLIGHT_CHANGED")
    if not health(LIVE, 1):
        raise RuntimeError("R4A_OLD_UDP_NOT_HEALTHY")
    old_version = docker("exec", "ouf-postgres", "psql", "-U", "ouf_udp", "-d", "ouf_udp",
                         "-Atc", "select version from ouf_udp.flyway_schema_history order by installed_rank desc limit 1")
    if not old_version.isdigit() or int(old_version) > 29:
        raise RuntimeError("R4A_OLD_FLYWAY_VERSION_UNEXPECTED")
    print("R4A_UDP_FLYWAY_BEFORE=" + old_version, flush=True)
    previous = "ouf-udp-rollback-" + old["Id"][:12]
    failed = "ouf-udp-r4a-failed-" + new["Id"][:12]
    for name in (previous, failed):
        try:
            inspect(name)
        except subprocess.CalledProcessError:
            pass
        else:
            raise RuntimeError("R4A_ROLLBACK_NAME_OCCUPIED")
    print("R4A_UDP_STOPPING_LIVE=true", flush=True)
    docker("stop", "--time", "60", LIVE)
    snapshot = None
    swapped = False
    old_renamed = False
    try:
        print("R4A_UDP_DB_BACKUP_STARTED=true", flush=True)
        snapshot = backup()
        docker("rename", LIVE, previous)
        old_renamed = True
        docker("rename", CANDIDATE, LIVE)
        swapped = True
        docker("start", LIVE)
        if not health(LIVE, 45):
            raise RuntimeError("R4A_NEW_UDP_UNHEALTHY")
        if not gateway_reachability():
            raise RuntimeError("R4A_GATEWAY_TO_NEW_UDP_UNREACHABLE")
        version = docker("exec", "ouf-postgres", "psql", "-U", "ouf_udp", "-d", "ouf_udp",
                         "-Atc", "select version from ouf_udp.flyway_schema_history order by installed_rank desc limit 1")
        if version != "29":
            raise RuntimeError("R4A_FLYWAY_VERSION_UNEXPECTED")
        print("R4A_UDP_SWITCH=PASS LIVE_IMAGE=" + EXPECTED + " FLYWAY=29", flush=True)
        print("R4A_UDP_ROLLBACK_CONTAINER=" + previous, flush=True)
        print("R4A_UDP_DB_BACKUP_RETAINED=" + str(snapshot), flush=True)
        print("R4A_UDP_AUTHENTICATED_OWNER_SMOKE_PENDING=true", flush=True)
    except BaseException:
        if swapped:
            rollback_runtime(previous, failed)
            print("R4A_UDP_DB_BACKUP_RETAINED=" + str(snapshot)
                  + " DB_NOT_AUTOMATICALLY_RESTORED=true", flush=True)
        else:
            try:
                if old_renamed:
                    docker("rename", previous, LIVE)
                if inspect(LIVE)["State"]["Running"] is False:
                    docker("start", LIVE)
                print("R4A_UDP_PRE_SWITCH_RECOVERY=OLD_CONTAINER_STARTED", flush=True)
            except (OSError, subprocess.SubprocessError, RuntimeError):
                print("R4A_UDP_PRE_SWITCH_RECOVERY=MANUAL_ACTION_REQUIRED", flush=True)
        raise


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, IndexError, subprocess.SubprocessError,
            RuntimeError) as error:
        detail = str(error) if not isinstance(error, subprocess.CalledProcessError) else "DOCKER_OR_POSTGRES_COMMAND_FAILED"
        print("R4A_UDP_SWITCH_BLOCKED=" + type(error).__name__ + ":" + detail)
        raise SystemExit(1)
