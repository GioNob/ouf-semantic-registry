#!/usr/bin/env python3
"""Run the pinned UDP image against an isolated restore of the pre-R4a dump."""

import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import tempfile
import time


COMMIT = "3402050b36ee28758e5255a57b0d32bc3983a34f"
BACKUP = Path("/opt/ouf/r4a-stage/udp-before-r4a-j5k8rens.dump")
MANIFEST = Path("/opt/ouf/r4a-stage/identity-images.json")


def run(command, **kwargs):
    return subprocess.run(command, check=True, capture_output=True, text=True,
                          timeout=kwargs.pop("timeout", 90), **kwargs).stdout.strip()


def docker(*args, timeout=90):
    return run(["docker", *args], timeout=timeout)


def inspect(name):
    return json.loads(docker("inspect", name))[0]


def version(database):
    return docker("exec", "ouf-postgres", "psql", "-U", "ouf_udp", "-d", database,
                  "-Atc", "select version from ouf_udp.flyway_schema_history "
                  "order by installed_rank desc limit 1")


def mounts(descriptor):
    return sorted((m["Type"], m["Source"], m["Destination"], bool(m["RW"]))
                  for m in descriptor.get("Mounts") or [])


def admin_command(*args):
    # The password is expanded inside the database container, never in an
    # argument, log line, local env file, or this script's output.
    return docker("exec", "ouf-postgres", "sh", "-c",
                  'PGPASSWORD="${POSTGRES_PASSWORD:-}" exec "$@"',
                  "r4a-db-probe", *args)


def probe_health(name):
    for _ in range(45):
        if inspect(name)["State"]["Running"]:
            answer = subprocess.run(["docker", "run", "--rm", "--network", "container:" + name,
                                     "curlimages/curl:8.16.0", "--max-time", "3", "-sS",
                                     "-o", "/dev/null", "-w", "%{http_code}",
                                     "http://127.0.0.1:8080/actuator/health"],
                                    capture_output=True, text=True, timeout=15)
            if answer.returncode == 0 and answer.stdout == "200":
                return True
        time.sleep(2)
    return False


def restore_error_category(stderr):
    rules = (
        (r"permission denied to create extension|must be superuser to create this extension", "EXTENSION_CREATE_DENIED"),
        (r"must be owner of extension|permission denied for extension", "EXTENSION_OWNER_DENIED"),
        (r"permission denied (?:for|to create) schema", "SCHEMA_PERMISSION_DENIED"),
        (r"permission denied for database", "DATABASE_PERMISSION_DENIED"),
        (r"role [^\n]+ does not exist", "RESTORE_ROLE_MISSING"),
        (r"already exists", "OBJECT_ALREADY_EXISTS"),
        (r"must be owner of", "OBJECT_OWNER_DENIED"),
        (r"permission denied", "OTHER_PERMISSION_DENIED"),
        (r"could not execute query", "QUERY_FAILED"),
    )
    return [label for pattern, label in rules if re.search(pattern, stderr, re.IGNORECASE)] or ["UNCLASSIFIED"]


def restore_error_details(stderr):
    """Report bounded SQL error types and TOC kinds, never SQL or values."""
    kinds = ("TABLE DATA", "FK CONSTRAINT", "EVENT TRIGGER", "MATERIALIZED VIEW",
             "EXTENSION", "SCHEMA", "TABLE", "FUNCTION", "INDEX", "CONSTRAINT",
             "DEFAULT", "SEQUENCE", "ACL", "COMMENT", "TYPE", "DATABASE")
    details = []
    for segment in stderr.split("pg_restore: error:")[1:]:
        reason = re.search(r"ERROR:\s*([^\r\n]+)", segment)
        toc = re.search(r"pg_restore: from TOC entry \d+; \d+ \d+ ([A-Z ]+)", segment)
        kind = "UNKNOWN"
        if toc:
            label = toc.group(1).strip()
            kind = next((item for item in kinds if label == item or label.startswith(item + " ")),
                        "UNKNOWN")
        cause = "UNKNOWN"
        if reason:
            message = reason.group(1).lower()
            for pattern, name in (
                (r"permission denied for (\w+)", "PERMISSION_FOR_"),
                (r"permission denied to (\w+)", "PERMISSION_TO_"),
                (r"must be owner of (\w+)", "OWNER_OF_"),
            ):
                match = re.search(pattern, message)
                if match:
                    cause = name + match.group(1).upper()
                    break
            if cause == "UNKNOWN":
                for marker, name in (("must be superuser", "SUPERUSER_REQUIRED"),
                                     ("already exists", "ALREADY_EXISTS"),
                                     ("duplicate key", "DUPLICATE_KEY"),
                                     ("does not exist", "MISSING_OBJECT")):
                    if marker in message:
                        cause = name
                        break
        item = {"cause": cause, "toc": kind}
        if item not in details:
            details.append(item)
    return details[:12]


def main():
    if os.geteuid() != 0:
        raise RuntimeError("ROOT_REQUIRED")
    live, candidate = inspect("ouf-udp"), inspect("ouf-udp-r4a-candidate")
    staged = json.loads(MANIFEST.read_text())["modules"]["udp"]
    if (not live["State"]["Running"] or candidate["State"]["Running"]
        or live["Image"] != staged["live_image_id"] or candidate["Image"] != staged["image_id"]
        or staged["commit"] != COMMIT or len(mounts(candidate)) != 2
        or mounts(candidate) != mounts(live) or version("ouf_udp") != "26"):
        raise RuntimeError("PINNED_PREFLIGHT_CHANGED")
    if BACKUP.stat().st_size < 1024:
        raise RuntimeError("BACKUP_MISSING_OR_EMPTY")
    db_env = dict(item.partition("=")[::2] for item in inspect("ouf-postgres")["Config"]["Env"])
    admin = db_env.get("POSTGRES_USER", "postgres")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", admin):
        raise RuntimeError("POSTGRES_ADMIN_ROLE_INVALID")
    role_flags = admin_command("psql", "-U", admin, "-d", "ouf_udp", "-Atc",
                               "select rolsuper::text||':'||rolcreatedb::text "
                               "from pg_roles where rolname=current_user")
    if role_flags not in {"true:true", "true:false", "false:true"}:
        raise RuntimeError("POSTGRES_ADMIN_CANNOT_CREATE_CLONE")
    extension_rows = docker("exec", "ouf-postgres", "psql", "-U", "ouf_udp", "-d", "ouf_udp",
                            "-Atc", "select extname||':'||extversion from pg_extension "
                            "where extname<>'plpgsql' order by extname").splitlines()
    extensions = [tuple(row.split(":", 1)) for row in extension_rows]
    if any(not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", name) for name, _ in extensions):
        raise RuntimeError("EXTENSION_NAME_UNSUPPORTED")
    if extensions and not role_flags.startswith("true:"):
        raise RuntimeError("POSTGRES_EXTENSION_ADMIN_REQUIRED")
    with BACKUP.open("rb") as source:
        subprocess.run(["docker", "exec", "-i", "ouf-postgres", "pg_restore", "-l"],
                       stdin=source, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                       check=True, timeout=90)
    print("R4A_PROBE_PREFLIGHT=PASS LIVE_FLYWAY=26 ADMIN_CREATE_DB=true", flush=True)
    suffix = secrets.token_hex(4)
    database, name = "ouf_udp_r4a_probe_" + suffix, "ouf-udp-r4a-probe-" + suffix
    created_db = created_container = False
    try:
        print("R4A_PROBE_STAGE=CREATE_CLONE", flush=True)
        admin_command("createdb", "-U", admin, "-O", "ouf_udp", database)
        created_db = True
        print("R4A_PROBE_STAGE=PREPARE_EXTENSIONS COUNT=" + str(len(extensions)), flush=True)
        for extension, expected_version in extensions:
            admin_command("psql", "-U", admin, "-d", database, "-v", "ON_ERROR_STOP=1",
                          "-Atc", "create extension if not exists " + extension)
            actual_version = docker("exec", "ouf-postgres", "psql", "-U", "ouf_udp",
                                    "-d", database, "-Atc",
                                    "select extversion from pg_extension where extname='" + extension + "'")
            if actual_version != expected_version:
                raise RuntimeError("EXTENSION_VERSION_MISMATCH")
        # Extensions are installed by the superuser, so their configuration
        # relations are owned by that role. pg_dump includes their data and
        # pg_restore must be able to COPY it as the application role.
        config_rows = admin_command(
            "psql", "-U", admin, "-d", database, "-Atc",
            "select distinct c.relkind||':'||format('%I.%I', n.nspname, c.relname) "
            "from pg_extension e cross join lateral unnest(e.extconfig) as cfg(config_oid) "
            "join pg_class c on c.oid=cfg.config_oid "
            "join pg_namespace n on n.oid=c.relnamespace "
            "order by 1").splitlines()
        print("R4A_PROBE_EXTENSION_CONFIG_RELATIONS=" + str(len(config_rows)), flush=True)
        for row in config_rows:
            relation_kind, separator, identifier = row.partition(":")
            if not separator or relation_kind not in {"r", "p", "S"} or not identifier:
                raise RuntimeError("EXTENSION_CONFIG_RELATION_UNSUPPORTED")
            relation_type = "sequence" if relation_kind == "S" else "table"
            admin_command("psql", "-U", admin, "-d", database, "-v", "ON_ERROR_STOP=1",
                          "-Atc", "grant all privileges on " + relation_type + " " +
                          identifier + " to ouf_udp")
        print("R4A_PROBE_STAGE=RESTORE_DUMP", flush=True)
        with BACKUP.open("rb") as source:
            restored = subprocess.run(["docker", "exec", "-i", "ouf-postgres", "pg_restore",
                                       "-U", "ouf_udp", "-d", database,
                                       "--no-owner", "--no-acl", "--no-comments"],
                                      stdin=source, stdout=subprocess.DEVNULL,
                                      stderr=subprocess.PIPE, timeout=300)
        if restored.returncode != 0:
            stderr = restored.stderr.decode("utf-8", "replace")
            print("R4A_PROBE_RESTORE_ERROR_CATEGORIES=" +
                  json.dumps(restore_error_category(stderr)), flush=True)
            print("R4A_PROBE_RESTORE_ERROR_DETAILS=" +
                  json.dumps(restore_error_details(stderr), separators=(",", ":")),
                  flush=True)
            raise RuntimeError("RESTORE_DUMP_FAILED")
        if version(database) != "26":
            raise RuntimeError("RESTORED_FLYWAY_NOT_26")
        print("R4A_PROBE_STAGE=PREPARE_CONTAINER", flush=True)
        original = dict(item.partition("=")[::2] for item in candidate["Config"]["Env"])
        jdbc = original.get("OUF_UDP_DB_URL", "")
        changed, number = re.subn(r"/ouf_udp(?=$|\?)", "/" + database, jdbc)
        if number != 1:
            raise RuntimeError("JDBC_DATABASE_PATH_UNEXPECTED")
        original["OUF_UDP_DB_URL"] = changed
        original["OUF_UDP_EXECUTION_ENABLED"] = "false"
        os.umask(0o077)
        fd, env_file = tempfile.mkstemp(prefix="ouf-r4a-probe-env-", dir="/run")
        try:
            with os.fdopen(fd, "w") as out:
                out.writelines(key + "=" + value + "\n" for key, value in original.items())
            cmd = ["docker", "create", "--name", name, "--network", "ouf-backend",
                   "--restart", "no", "--user", "10004:10004", "--env-file", env_file]
            for kind, source, target, writable in mounts(candidate):
                if kind != "bind" or "," in source or "," in target:
                    raise RuntimeError("MOUNT_UNSUPPORTED")
                mount = "type=bind,src=" + source + ",dst=" + target
                cmd.extend(["--mount", mount if writable else mount + ",readonly"])
            cmd.append(staged["image_id"])
            run(cmd)
            created_container = True
        finally:
            Path(env_file).unlink(missing_ok=True)
        docker("start", name)
        print("R4A_PROBE_STAGE=START_AND_MIGRATE", flush=True)
        if not probe_health(name):
            logs = subprocess.run(["docker", "logs", "--tail", "300", name],
                                  capture_output=True, text=True, timeout=15)
            kinds = re.findall(r"Caused by:\s+([A-Za-z0-9_.$]+(?:Exception|Error))",
                               logs.stdout + "\n" + logs.stderr)
            print("R4A_PROBE_ERROR_CLASSES=" + json.dumps(list(dict.fromkeys(kinds))[-12:]),
                  flush=True)
            raise RuntimeError("PROBE_UNHEALTHY")
        if version(database) != "34" or version("ouf_udp") != "26":
            raise RuntimeError("FLYWAY_ISOLATION_FAILED")
        print("R4A_PROBE_MIGRATION=PASS CLONE_FLYWAY=34 LIVE_FLYWAY=26", flush=True)
    finally:
        if created_container:
            try:
                docker("stop", "--time", "30", name, timeout=60)
            except subprocess.CalledProcessError:
                pass
            docker("rm", "-f", name)
        if created_db:
            admin_command("dropdb", "-U", admin, "--force", database)
        if version("ouf_udp") != "26" or inspect("ouf-udp")["Image"] != live["Image"]:
            raise RuntimeError("LIVE_STATE_CHANGED_DURING_PROBE")
        print("R4A_PROBE_CLEANUP=PASS LIVE_CONTAINER_UNCHANGED=true", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, IndexError, TypeError, subprocess.SubprocessError,
            RuntimeError) as error:
        print("R4A_PROBE_BLOCKED=" + type(error).__name__ + ":" +
              (str(error) if isinstance(error, RuntimeError) else "COMMAND_FAILED"))
        raise SystemExit(1)
