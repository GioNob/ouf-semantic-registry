#!/usr/bin/env python3
"""Read-only ownership/ACL inventory for the isolated UDP restore failure."""

from pathlib import Path
import re
import subprocess


BACKUP = Path("/opt/ouf/r4a-stage/udp-before-r4a-j5k8rens.dump")


def main():
    with BACKUP.open("rb") as source:
        listed = subprocess.run(
            ["docker", "exec", "-i", "ouf-postgres", "pg_restore", "-l"],
            stdin=source, capture_output=True, check=True, timeout=90).stdout.decode(
                "utf-8", "replace")
    toc = [line.split(";", 1)[1].strip() for line in listed.splitlines()
           if re.match(r"^\d+;", line)]
    flyway = [line for line in toc if re.search(
        r"\bTABLE\s+ouf_udp\s+flyway_schema_history\s+", line)]
    schema = [line for line in toc if re.search(r"\bSCHEMA\s+-\s+ouf_udp\s+", line)]
    acl_count = sum(bool(re.search(r"\bACL\s+ouf_udp\s+.*flyway_schema_history\b", line))
                    for line in toc)
    print("DUMP_FLYWAY_TABLE_COUNT=" + str(len(flyway)))
    print("DUMP_FLYWAY_OWNER=" + (flyway[0].split()[-1] if len(flyway) == 1 else "UNKNOWN"))
    print("DUMP_SCHEMA_COUNT=" + str(len(schema)))
    print("DUMP_SCHEMA_OWNER=" + (schema[0].split()[-1] if len(schema) == 1 else "UNKNOWN"))
    print("DUMP_FLYWAY_ACL_ENTRIES=" + str(acl_count))
    query = (
        "select (pg_get_userbyid(c.relowner)='ouf_udp')::text||'|'||"
        "has_table_privilege('ouf_udp',c.oid,'SELECT')::text||'|'||"
        "has_schema_privilege('ouf_udp',n.oid,'USAGE')::text "
        "from pg_class c join pg_namespace n on n.oid=c.relnamespace "
        "where n.nspname='ouf_udp' and c.relname='flyway_schema_history' "
        "and c.relkind in ('r','p')"
    )
    result = subprocess.run(
        ["docker", "exec", "ouf-postgres", "psql", "-U", "ouf_udp", "-d",
         "ouf_udp", "-Atc", query], capture_output=True, check=True,
        timeout=20).stdout.decode("utf-8", "replace").strip().splitlines()
    if len(result) != 1 or len(result[0].split("|")) != 3:
        raise RuntimeError("LIVE_FLYWAY_INVENTORY_UNEXPECTED")
    owner, read, usage = result[0].split("|")
    print("LIVE_FLYWAY_OWNER_IS_APP=" + owner)
    print("LIVE_FLYWAY_SELECT_ALLOWED=" + read)
    print("LIVE_SCHEMA_USAGE_ALLOWED=" + usage)
    print("R4A_RESTORE_ACCESS_INVENTORY=READ_ONLY LIVE_UNCHANGED=true")


if __name__ == "__main__":
    try:
        main()
    except (OSError, subprocess.SubprocessError, RuntimeError):
        print("R4A_RESTORE_ACCESS_INVENTORY=BLOCKED")
        raise SystemExit(1)
