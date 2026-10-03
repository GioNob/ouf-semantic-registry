#!/usr/bin/env python3
"""Emergency DB restore for a failed R4a UDP switch, with UDP stopped."""

import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess


def docker(*args):
    return subprocess.run(["docker", *args], check=True, capture_output=True, text=True).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--old-version", required=True)
    args = parser.parse_args()
    if os.geteuid() != 0 or not re.fullmatch(r"[0-9]+", args.old_version):
        raise RuntimeError("R4A_RESTORE_ARGS_INVALID")
    backup = args.backup
    st = backup.lstat()
    if (backup.parent != Path("/opt/ouf/r4a-stage")
        or not backup.name.startswith("udp-before-r4a-") or backup.suffix != ".dump"
        or not stat.S_ISREG(st.st_mode) or st.st_uid != 0
        or stat.S_IMODE(st.st_mode) != 0o600 or st.st_size < 1024):
        raise RuntimeError("R4A_BACKUP_METADATA_INVALID")
    # Read individual known containers; no UDP owner may hold a DB connection.
    for name in ("ouf-udp", "ouf-udp-r4a-candidate"):
        result = subprocess.run(["docker", "inspect", name], capture_output=True, text=True)
        if result.returncode == 0 and json.loads(result.stdout)[0]["State"]["Running"]:
            raise RuntimeError("R4A_UDP_MUST_BE_STOPPED:" + name)
    with backup.open("rb") as source:
        subprocess.run(["docker", "exec", "-i", "ouf-postgres", "pg_restore", "-l"],
                       stdin=source, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                       check=True, timeout=90)
    print("R4A_DB_RESTORE_STARTING=true UDP_STOPPED=true", flush=True)
    with backup.open("rb") as source:
        subprocess.run(["docker", "exec", "-i", "ouf-postgres", "pg_restore",
                        "-U", "ouf_udp", "-d", "ouf_udp", "--clean", "--if-exists",
                        "--single-transaction"], stdin=source, stdout=subprocess.DEVNULL,
                       stderr=subprocess.PIPE, check=True, timeout=900)
    actual = docker("exec", "ouf-postgres", "psql", "-U", "ouf_udp", "-d", "ouf_udp",
                    "-Atc", "select version from ouf_udp.flyway_schema_history order by installed_rank desc limit 1").strip()
    if actual != args.old_version:
        raise RuntimeError("R4A_DB_RESTORE_VERSION_MISMATCH")
    print("R4A_DB_RESTORE=PASS FLYWAY=" + actual + " BACKUP_RETAINED=" + str(backup), flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        detail = str(error) if not isinstance(error, subprocess.CalledProcessError) else "POSTGRES_COMMAND_FAILED"
        print("R4A_DB_RESTORE_BLOCKED=" + type(error).__name__ + ":" + detail)
        raise SystemExit(1)
