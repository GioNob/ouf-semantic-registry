#!/usr/bin/env python3
"""Back up and switch Onboarding to the staged UDP attestation gate image."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time


LIVE = "ouf-onboarding"
CANDIDATE = "ouf-onboarding-r4a-candidate"
STAGE = Path("/opt/ouf/r4a-stage")
EXPECTED = "f74c3a9f377b5ce93b5cab298fa24372de1602bc"
TOKEN = Path("/run/ouf-onboarding-identity/token")


def docker(*arguments):
    return subprocess.run(["docker", *arguments], check=True, capture_output=True,
                          text=True, timeout=60).stdout.strip()


def inspect(name):
    return json.loads(docker("inspect", name))[0]


def flyway():
    return docker("exec", "ouf-postgres", "psql", "-U", "ouf_onboarding", "-d",
                  "ouf_onboarding", "-Atc", "select version from "
                  "ouf_onboarding.flyway_schema_history order by installed_rank desc limit 1")


def health(name, attempts=45):
    for number in range(attempts):
        if inspect(name)["State"]["Running"]:
            result = subprocess.run(["docker", "run", "--rm", "--network",
                "container:" + name, "curlimages/curl:8.16.0", "--max-time", "3",
                "-sS", "-o", "/dev/null", "-w", "%{http_code}",
                "http://127.0.0.1:8080/actuator/health"],
                capture_output=True, text=True, timeout=15)
            if result.returncode == 0 and result.stdout == "200":
                return True
        if number and number % 10 == 0:
            print("R4A_ONB_HEALTH_WAIT_SECONDS=" + str(number * 2), flush=True)
        time.sleep(2)
    return False


def backup():
    os.umask(0o077)
    fd, filename = tempfile.mkstemp(prefix="onboarding-before-r4a-", suffix=".dump",
                                    dir=STAGE)
    target = Path(filename)
    try:
        with os.fdopen(fd, "wb") as stream:
            subprocess.run(["docker", "exec", "ouf-postgres", "pg_dump", "-U",
                            "ouf_onboarding", "-d", "ouf_onboarding", "-Fc"],
                           stdout=stream, stderr=subprocess.PIPE, check=True, timeout=600)
            stream.flush()
            os.fsync(stream.fileno())
        if target.stat().st_size < 1024:
            raise RuntimeError("BACKUP_TOO_SMALL")
        with target.open("rb") as stream:
            subprocess.run(["docker", "exec", "-i", "ouf-postgres", "pg_restore", "-l"],
                           stdin=stream, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                           check=True, timeout=90)
        print("R4A_ONB_DB_BACKUP=" + str(target) + " BYTES=" + str(target.stat().st_size)
              + " RESTORE_LIST=PASS", flush=True)
        return target
    except BaseException:
        target.unlink(missing_ok=True)
        raise


def rollback(previous, failed):
    try:
        docker("update", "--restart", "no", LIVE)
        if inspect(LIVE)["State"]["Running"]:
            docker("stop", "--time", "30", LIVE)
        docker("rename", LIVE, failed)
        docker("rename", previous, LIVE)
        docker("start", LIVE)
        print("R4A_ONB_RUNTIME_ROLLBACK=" + ("PASS" if health(LIVE, 25) else "UNHEALTHY"),
              flush=True)
    except (OSError, subprocess.SubprocessError, RuntimeError):
        print("R4A_ONB_RUNTIME_ROLLBACK=MANUAL_RECOVERY_REQUIRED", flush=True)


def main(expected_flyway):
    if os.geteuid() != 0 or not re.fullmatch(r"[0-9]+", expected_flyway):
        raise RuntimeError("ROOT_AND_FLYWAY_REQUIRED")
    record = json.loads((STAGE / "identity-images.json").read_text())["modules"]["onboarding"]
    old, new = inspect(LIVE), inspect(CANDIDATE)
    if (record["commit"] != EXPECTED or old["Image"] != record["live_image_id"]
        or new["Image"] != record["image_id"] or not old["State"]["Running"]
        or new["State"]["Running"] or old["HostConfig"]["NetworkMode"] != "ouf-backend"
        or new["HostConfig"]["NetworkMode"] != "ouf-backend"
        or not any(mount["Destination"] == "/run/ouf-onboarding-identity"
                   and not mount["RW"] for mount in new.get("Mounts") or [])
        or not TOKEN.is_file()):
        raise RuntimeError("PINNED_PREFLIGHT_CHANGED")
    timer = subprocess.run(["systemctl", "is-active", "--quiet",
        "ouf-onboarding-identity-token.timer"], capture_output=True, timeout=10)
    if timer.returncode != 0:
        raise RuntimeError("TOKEN_REFRESH_TIMER_INACTIVE")
    if not health(LIVE, 1) or flyway() != expected_flyway:
        raise RuntimeError("LIVE_HEALTH_OR_FLYWAY_CHANGED")
    previous = "ouf-onboarding-rollback-" + old["Id"][:12]
    failed = "ouf-onboarding-r4a-failed-" + new["Id"][:12]
    for name in (previous, failed):
        try:
            inspect(name)
        except subprocess.CalledProcessError:
            pass
        else:
            raise RuntimeError("ROLLBACK_NAME_OCCUPIED")
    print("R4A_ONB_FLYWAY_BEFORE=" + expected_flyway, flush=True)
    print("R4A_ONB_STOPPING_LIVE=true", flush=True)
    docker("stop", "--time", "60", LIVE)
    snapshot = None
    swapped = renamed = False
    try:
        snapshot = backup()
        docker("rename", LIVE, previous)
        renamed = True
        docker("rename", CANDIDATE, LIVE)
        swapped = True
        docker("start", LIVE)
        if not health(LIVE):
            raise RuntimeError("NEW_ONBOARDING_UNHEALTHY")
        if flyway() != expected_flyway:
            raise RuntimeError("FLYWAY_CHANGED_UNEXPECTEDLY")
        print("R4A_ONB_SWITCH=PASS LIVE_IMAGE=" + EXPECTED + " FLYWAY="
              + expected_flyway, flush=True)
        print("R4A_ONB_ROLLBACK_CONTAINER=" + previous, flush=True)
        print("R4A_ONB_DB_BACKUP_RETAINED=" + str(snapshot), flush=True)
        print("R4A_ONB_ATTESTATION_POSITIVE_SMOKE_PENDING=true", flush=True)
    except BaseException:
        if swapped:
            rollback(previous, failed)
            print("R4A_ONB_DB_BACKUP_RETAINED=" + str(snapshot)
                  + " DB_NOT_AUTOMATICALLY_RESTORED=true", flush=True)
        else:
            try:
                if renamed:
                    docker("rename", previous, LIVE)
                if not inspect(LIVE)["State"]["Running"]:
                    docker("start", LIVE)
                print("R4A_ONB_PRE_SWITCH_RECOVERY=OLD_CONTAINER_STARTED", flush=True)
            except (OSError, subprocess.SubprocessError, RuntimeError):
                print("R4A_ONB_PRE_SWITCH_RECOVERY=MANUAL_ACTION_REQUIRED", flush=True)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-flyway", required=True)
    arguments = parser.parse_args()
    try:
        main(arguments.expected_flyway)
    except (OSError, ValueError, KeyError, IndexError, RuntimeError,
            subprocess.SubprocessError) as error:
        label = str(error) if isinstance(error, RuntimeError) else "COMMAND_FAILED"
        print("R4A_ONB_SWITCH_BLOCKED=" + label + " SECRETS_NOT_PRINTED=true")
        raise SystemExit(1)
