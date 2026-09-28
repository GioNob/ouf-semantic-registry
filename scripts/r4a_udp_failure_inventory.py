#!/usr/bin/env python3
"""Read-only failure evidence for the retained R4a UDP candidate; redact logs."""

import json
import re
import subprocess


def docker(*args):
    return subprocess.run(["docker", *args], check=True, capture_output=True, text=True).stdout


def docker_logs(name):
    result = subprocess.run(["docker", "logs", "--tail", "600", name],
                            check=True, capture_output=True, text=True)
    return result.stdout + "\n" + result.stderr


def inspect(name):
    return json.loads(docker("inspect", name))[0]


def safe_error_lines(raw):
    lines = []
    for line in raw.splitlines():
        if "Caused by:" not in line and "APPLICATION FAILED TO START" not in line \
                and "Error starting ApplicationContext" not in line:
            continue
        if "APPLICATION FAILED TO START" in line:
            lines.append("APPLICATION_FAILED_TO_START")
            continue
        if "Error starting ApplicationContext" in line:
            lines.append("APPLICATION_CONTEXT_FAILED")
            continue
        kind = re.search(r"Caused by:\s+([A-Za-z0-9_.$]+(?:Exception|Error))", line)
        if kind:
            lines.append(kind.group(1))
    return list(dict.fromkeys(lines))[-20:]


def main():
    names = docker("ps", "-a", "--format", "{{.Names}}").splitlines()
    matches = [n for n in names if n.startswith("ouf-udp-r4a-failed-")]
    if len(matches) != 1:
        raise RuntimeError("R4A_FAILED_CONTAINER_NOT_UNIQUE")
    failed = inspect(matches[0])
    live = inspect("ouf-udp")
    print("R4A_UDP_FAILURE_INVENTORY=READ_ONLY")
    print("LIVE_RUNNING=" + str(live["State"]["Running"]).lower())
    print("LIVE_IMAGE_MATCHES_PREVIOUS=" + str(live["Image"] != failed["Image"]).lower())
    print("FAILED_CONTAINER=" + matches[0])
    print("FAILED_EXIT_CODE=" + str(failed["State"].get("ExitCode")))
    print("FAILED_OOM_KILLED=" + str(failed["State"].get("OOMKilled")).lower())
    print("FAILED_RESTART_COUNT=" + str(failed.get("RestartCount")))
    env = {x.partition("=")[0]: x.partition("=")[2] for x in failed["Config"].get("Env") or []}
    print("FAILED_IAM_ENABLED=" + str(env.get("OUF_UDP_IAM_ENABLED") == "true").lower())
    raw = docker_logs(matches[0])
    print("FAILED_LOG_ERROR_CLASSES=" + json.dumps(safe_error_lines(raw)))
    version = docker("exec", "ouf-postgres", "psql", "-U", "ouf_udp", "-d", "ouf_udp",
                     "-Atc", "select coalesce(string_agg(version||':'||success,',' order by installed_rank),'none') from ouf_udp.flyway_schema_history where installed_rank > (select coalesce(max(installed_rank),0) from ouf_udp.flyway_schema_history where version='26')")
    print("FLYWAY_AFTER_ATTEMPT=" + version.strip())
    print("SECRETS_AND_RAW_LOG_NOT_PRINTED=true DB_UNCHANGED_BY_INVENTORY=true")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, IndexError, subprocess.SubprocessError, RuntimeError) as error:
        print("R4A_UDP_FAILURE_INVENTORY_BLOCKED=" + type(error).__name__)
        raise SystemExit(1)
