#!/usr/bin/env python3
"""Read-only release preflight: both histories, live bindings and Flyway checksums."""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from urllib.parse import urlsplit
import zlib

BASELINE = "f74c3a9f377b5ce93b5cab298fa24372de1602bc"
INTAKE = "5d770df635f8328a1e901b2d47bf8cd5bacab6c5"
MIGRATIONS = "src/main/resources/db/migration/"


def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=30).stdout


def inspect(name):
    return json.loads(run(["docker", "inspect", name]))[0]


def checksum(text):
    # Flyway SQL checksum: UTF-8 without initial BOM or CR/LF line separators.
    value = zlib.crc32(text.removeprefix("\ufeff").replace("\r", "").replace("\n", "").encode())
    return value if value < 2**31 else value - 2**32


def compare_migrations(candidate, installed):
    applied = [row for row in installed if row.get("version") is not None]
    versions = {row["version"] for row in applied}
    if (len(versions) != len(applied) or set(candidate) != versions
            or any(row.get("type") != "SQL" or row.get("success") is not True for row in applied)):
        return False
    return all((row["script"], row["checksum"]) == candidate[row["version"]] for row in applied)


def environment(container):
    result = {}
    for value in container["Config"].get("Env") or []:
        key, sep, value = value.partition("=")
        if not sep or key in result:
            raise RuntimeError("OWNER_ENV_UNSUPPORTED")
        result[key] = value
    return result


def host_file(container, target):
    if not target or not Path(target).is_absolute():
        return None
    matches = []
    for mount in container.get("Mounts", []):
        destination = Path(mount["Destination"])
        if (mount.get("Type") == "bind" and mount.get("RW") is False
                and Path(target).is_relative_to(destination)):
            source = Path(mount["Source"]).resolve()
            host = (source / Path(target).relative_to(destination)).resolve()
            if host == source or host.is_relative_to(source):
                matches.append(host)
    return matches[0] if len(matches) == 1 else None


def private_readable(path):
    if path is None:
        return False
    try:
        metadata = path.stat()
        return (stat.S_ISREG(metadata.st_mode) and metadata.st_size > 0
                and metadata.st_uid == 0 and metadata.st_gid == 10003
                and bool(metadata.st_mode & stat.S_IRGRP) and not metadata.st_mode & 0o007)
    except OSError:
        return False


def binding_facts(container):
    env = environment(container)
    staging = ("OUF_ONBOARDING_STAGING_ENDPOINT", "OUF_ONBOARDING_STAGING_BUCKET",
               "OUF_ONBOARDING_STAGING_ACCESS_KEY_FILE", "OUF_ONBOARDING_STAGING_SECRET_KEY_FILE")
    credential_paths = [host_file(container, env.get(key)) for key in staging[2:]]
    object_token = host_file(container, env.get("OUF_ONBOARDING_OBJECT_STORE_TOKEN_FILE"))
    identity_token = host_file(container, env.get("OUF_ONB_UDP_IDENTITY_TOKEN_FILE"))
    return {
        "OWNER_STAGING_ENV_PRESENT": all(env.get(key) for key in staging),
        "OWNER_STAGING_CREDENTIAL_MOUNTS_PRESENT": all(path is not None for path in credential_paths),
        "OWNER_STAGING_CREDENTIAL_FILES_READABLE": all(private_readable(path) for path in credential_paths),
        "OWNER_MANAGED_READ_GATEWAY_ENV_PRESENT": bool(env.get("OUF_ONBOARDING_OBJECT_STORE_GATEWAY_BASE_URL")),
        "OWNER_MANAGED_READ_TOKEN_MOUNT_PRESENT": object_token is not None,
        "OWNER_MANAGED_READ_TOKEN_FILE_READABLE": private_readable(object_token),
        "OWNER_IDENTITY_GATE_ENV_PRESENT": bool(env.get("OUF_ONB_UDP_IDENTITY_GATEWAY_URL")
                                                and env.get("OUF_ONB_UDP_IDENTITY_TOKEN_FILE")),
        "OWNER_IDENTITY_TOKEN_MOUNT_PRESENT": identity_token is not None,
        "OWNER_IDENTITY_TOKEN_FILE_READABLE": private_readable(identity_token),
    }


def main(args):
    if os.geteuid() != 0 or not re.fullmatch(r"[0-9a-f]{40}", args.revision):
        raise RuntimeError("ROOT_AND_PINNED_REVISION_REQUIRED")
    print("R4A_MANAGED_IDENTITY_RELEASE_INVENTORY=READ_ONLY")
    safe = ["git", "-c", "safe.directory=" + str(args.repo.resolve(strict=True)), "-C", str(args.repo)]
    for parent in (BASELINE, INTAKE):
        run([*safe, "merge-base", "--is-ancestor", parent, args.revision])
    print("OWNER_RELEASE_PRESERVES_BOTH_HISTORIES=true")
    owner = inspect("ouf-onboarding")
    image = inspect(owner["Image"])
    facts = {"OWNER_LIVE_BASELINE_MATCH": (image["Config"].get("Labels") or {}).get(
                 "org.opencontainers.image.revision") == BASELINE,
             "OWNER_LIVE_RUNNING": owner["State"]["Running"],
             **binding_facts(owner)}
    env = environment(owner)
    url = urlsplit(env.get("OUF_ONB_DB_URL", "").removeprefix("jdbc:"))
    user = env.get("OUF_ONB_DB_USER", "")
    if (url.scheme != "postgresql" or url.path != "/ouf_onboarding" or url.username or url.password
            or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", user)):
        raise RuntimeError("OWNER_DATABASE_BINDING_UNSUPPORTED")
    candidate = {}
    paths = run([*safe, "ls-tree", "-r", "--name-only", args.revision, "--", MIGRATIONS]).splitlines()
    for path in paths:
        match = re.fullmatch(r"V([0-9]+(?:[._][0-9]+)*)__.+\.sql", Path(path).name)
        if not match:
            raise RuntimeError("OWNER_MIGRATION_LAYOUT_UNSUPPORTED")
        version = match[1].replace("_", ".")
        if version in candidate:
            raise RuntimeError("OWNER_MIGRATION_VERSION_DUPLICATE")
        candidate[version] = (Path(path).name, checksum(run([*safe, "show", args.revision + ":" + path])))
    sql = ("begin read only; select coalesce(json_agg(json_build_object('version',version,"
           "'script',script,'checksum',checksum,'success',success,'type',type)), '[]'::json)::text "
           "from ouf_onboarding.flyway_schema_history; rollback;")
    installed = json.loads(run(["docker", "exec", "ouf-postgres", "psql", "-X", "-qAt", "-v",
        "ON_ERROR_STOP=1", "-U", user, "-d", "ouf_onboarding", "-c", sql]))
    facts["OWNER_RELEASE_MIGRATIONS_MATCH_DATABASE"] = bool(candidate) and compare_migrations(candidate, installed)
    print("OWNER_RELEASE_MIGRATION_COUNT=" + str(len(candidate)))
    for key, value in facts.items():
        print(key + "=" + str(bool(value)).lower())
    print("R4A_MANAGED_IDENTITY_RELEASE_INVENTORY=COMPLETE RELEASE_PREREQUISITES="
          + ("PASS" if all(facts.values()) else "BLOCKED")
          + " LIVE_UNCHANGED=true VALUES_NOT_PRINTED=true")
    return all(facts.values())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--repo", type=Path, default=Path("/opt/ouf/onboarding"))
    try:
        main(parser.parse_args())
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_MANAGED_IDENTITY_RELEASE_INVENTORY=BLOCKED CODE=" + code + " VALUES_NOT_PRINTED=true")
        raise SystemExit(1)
