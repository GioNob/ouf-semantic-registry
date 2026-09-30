#!/usr/bin/env python3
"""Switch the verified Ingestion candidate with private backup and runtime rollback."""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import time
import uuid
import hashlib
import r4a_prepare_ingestion_candidate as prepare
from r4a_prepare_ingestion_candidate import probe as inventory

LIVE = "ouf-ingestion"
RECEIPT = prepare.ROOT / "ingestion-compatibility-switch.json"


def docker(*args):
    return subprocess.run(["docker", *args], check=True, capture_output=True,
                          text=True, timeout=90).stdout.strip()


def private_json(path):
    meta = path.lstat()
    if not stat.S_ISREG(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o600:
        raise RuntimeError("ING_PRIVATE_STATE_UNSAFE")
    return json.loads(path.read_text())


def save(value):
    fd, name = tempfile.mkstemp(prefix="ingestion-compatibility-receipt-", dir=prepare.ROOT)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, RECEIPT)
    finally:
        Path(name).unlink(missing_ok=True)


def sql(query):
    return docker("exec", "ouf-postgres", "psql", "-X", "-qAt", "-v", "ON_ERROR_STOP=1",
                  "-U", "ouf_ingestion", "-d", "ouf_ingestion", "-c", "begin read only; " + query + "; rollback;")


def history_query():
    return ("select coalesce(json_agg(json_build_object('version',version,'script',script,"
        "'checksum',checksum,'success',success,'type',type) order by installed_rank),'[]'::json) "
        "from ouf_ingestion.flyway_schema_history")


def history():
    return json.loads(sql(history_query()))


def frozen(args):
    return inventory.candidate_row(args.source, args.version, args.expected_hash)


def tokens_fresh(owner, tenant):
    settings = inventory.transport_settings(owner, tenant)
    mount = next(m for m in owner["Mounts"] if m["Destination"] == inventory.AUTH)
    relative = Path(settings["ouf.ingestion.activation.token-file"]).relative_to(inventory.AUTH)
    path = Path(mount["Source"]).joinpath(relative).resolve()
    token = path.read_text().strip()
    part = token.split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
    audience = claims.get("aud")
    audience = [audience] if isinstance(audience, str) else audience
    scopes = set(str(claims.get("scope", "")).split())
    if (claims.get("iss") != "https://auth.ouf-lab.it/realms/ouf"
            or not isinstance(audience, list) or "ouf-api-gateway" not in audience
            or not {"ouf.semantic.read", "ouf.internal.object-storage.read",
                    "ouf.ingestion.configuration.attest"}.issubset(scopes)
            or claims["exp"] - time.time() < 90 or time.time() - path.stat().st_mtime > 150):
        raise RuntimeError("ING_WORKLOAD_TOKEN_NOT_FRESH_OR_CLAIMS_INVALID")
    return settings


def http_code(path):
    return docker("run", "--rm", "--network", "container:" + LIVE, "curlimages/curl:8.16.0",
                  "--max-time", "3", "-sS", "-o", "/dev/null", "-w", "%{http_code}",
                  "http://127.0.0.1:8080" + path)


def ready(attempts=45):
    for number in range(attempts):
        current = inventory.inspect(LIVE)
        if not current["State"]["Running"]:
            raise RuntimeError("ING_CONTAINER_NOT_RUNNING")
        try:
            if http_code("/actuator/health/readiness") == "200":
                return
        except subprocess.SubprocessError:
            pass
        if number and number % 10 == 0:
            print("R4A_ING_COMPAT_HEALTH_WAIT_SECONDS=" + str(number * 2), flush=True)
        time.sleep(2)
    raise RuntimeError("ING_READINESS_TIMEOUT")


def backup_restore(expected_history):
    user = prepare.environment(inventory.inspect("ouf-postgres")).get("POSTGRES_USER", "")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", user):
        raise RuntimeError("ING_BACKUP_DATABASE_USER_UNSUPPORTED")
    fd, name = tempfile.mkstemp(prefix="ingestion-before-compatibility-", suffix=".dump", dir=prepare.ROOT)
    path = Path(name)
    print("R4A_ING_COMPAT_DB_BACKUP=" + str(path) + " PRIVATE=true", flush=True)
    with os.fdopen(fd, "wb") as stream:
        subprocess.run(["docker", "exec", "ouf-postgres", "pg_dump", "-U", user, "-d", "ouf_ingestion", "-Fc"],
                       stdout=stream, stderr=subprocess.PIPE, check=True, timeout=600)
        stream.flush()
        os.fsync(stream.fileno())
    if path.stat().st_size < 1024:
        raise RuntimeError("ING_BACKUP_TOO_SMALL")
    scratch = "ouf_ingestion_restore_" + uuid.uuid4().hex[:12]
    docker("exec", "ouf-postgres", "createdb", "-U", user, scratch)
    try:
        with path.open("rb") as stream:
            subprocess.run(["docker", "exec", "-i", "ouf-postgres", "pg_restore", "-U", user,
                "--no-owner", "--no-acl", "-d", scratch], stdin=stream,
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True, timeout=600)
        restored = docker("exec", "ouf-postgres", "psql", "-X", "-qAt", "-v", "ON_ERROR_STOP=1",
                          "-U", user, "-d", scratch, "-c", history_query())
        if json.loads(restored) != expected_history:
            raise RuntimeError("ING_BACKUP_RESTORE_HISTORY_MISMATCH")
    finally:
        docker("exec", "ouf-postgres", "dropdb", "-U", user, scratch)
    print("R4A_ING_COMPAT_DB_RESTORE_TO_SCRATCH=PASS BACKUP_RETAINED=true", flush=True)
    return path


def recover(state, previous, failed):
    old_id, new_id = state["old"]["Id"], state["candidate_id"]
    current = prepare.optional(LIVE)
    if current is not None and current["Id"] == new_id:
        log = prepare.ROOT / ("ingestion-compatibility-failed-" + new_id[:12] + ".log")
        try:
            with log.open("x") as stream:
                subprocess.run(["docker", "logs", "--tail", "120", LIVE],
                               stdout=stream, stderr=stream, timeout=15, check=False)
            print("R4A_ING_COMPAT_FAILURE_LOG=" + str(log) + " PRIVATE=true", flush=True)
        except (OSError, subprocess.SubprocessError):
            pass
        docker("update", "--restart", "no", LIVE)
        if current["State"]["Running"]:
            docker("stop", "--time", "30", LIVE)
        if prepare.optional(failed) is not None:
            raise RuntimeError("ING_FAILED_RETENTION_NAME_OCCUPIED")
        docker("rename", LIVE, failed)
        current = None
    if current is None:
        retained = inventory.inspect(previous)
        if retained["Id"] != old_id:
            raise RuntimeError("ING_ROLLBACK_CONTAINER_ID_MISMATCH")
        docker("rename", previous, LIVE)
    elif current["Id"] != old_id:
        raise RuntimeError("ING_ROLLBACK_LIVE_ID_MISMATCH")
    docker("update", "--restart", "unless-stopped", LIVE)
    if not inventory.inspect(LIVE)["State"]["Running"]:
        docker("start", LIVE)
    ready(25)


def main(args):
    if os.geteuid() != 0:
        raise RuntimeError("ROOT_REQUIRED")
    os.umask(0o077)
    root = prepare.ROOT.lstat()
    if not stat.S_ISDIR(root.st_mode) or root.st_uid != 0 or stat.S_IMODE(root.st_mode) != 0o700:
        raise RuntimeError("ING_SNAPSHOT_DIRECTORY_UNSAFE")
    state = private_json(prepare.STATE)
    if (state["revision"] != prepare.REVISION or state["candidate_name"] != prepare.NAME
            or any(state.get(k) != getattr(args, k) for k in ("source", "version", "expected_hash", "tenant_id"))):
        raise RuntimeError("ING_RELEASE_STATE_CONTEXT_MISMATCH")
    if RECEIPT.exists() or RECEIPT.is_symlink():
        raise RuntimeError("ING_SWITCH_RECEIPT_ALREADY_EXISTS")
    old, candidate = inventory.inspect(LIVE), inventory.inspect(prepare.NAME)
    image = inventory.inspect(state["image_id"], "image")
    properties = Path(state["properties"])
    prepare.private(properties, 0o440)
    properties_hash = hashlib.sha256(properties.read_bytes()).hexdigest()
    if (properties_hash != state["properties_sha256"]
            or prepare.stable(old) != prepare.stable(state["old"])
            or candidate["Id"] != state["candidate_id"]
            or not prepare.matches(candidate, old, image, properties)
            or (image["Config"].get("Labels") or {}).get("org.opencontainers.image.revision") != prepare.REVISION):
        raise RuntimeError("ING_PINNED_RUNTIME_OR_CANDIDATE_DRIFT")
    prepare.guard(old, image)
    settings = tokens_fresh(old, args.tenant_id)
    original_source = next(m["Source"] for m in old["Mounts"] if m["Destination"] == inventory.PROPERTIES)
    original = Path(original_source).read_bytes()
    expected = original + b"\n" + "".join(k + "=" + v + "\n" for k, v in settings.items()).encode()
    if properties.read_bytes() != expected:
        raise RuntimeError("ING_PREPARED_PROPERTIES_DRIFT")
    before, version = history(), frozen(args)
    inventory.validate_proof(state["proof"], version)
    if (state["proof"].get("candidateCommit") != prepare.REVISION
            or state["proof"].get("candidateImageId") != image["Id"]
            or state["proof"].get("validatedRows") != 8
            or len([r for r in before if r.get("version") is not None]) != 14
            or not all(r.get("success") is True for r in before)
            or before[-1].get("version") != "14"):
        raise RuntimeError("ING_PROOF_OR_FLYWAY14_DRIFT")
    ready(1)
    previous = "ouf-ingestion-compatibility-rollback-" + old["Id"][:12]
    failed = "ouf-ingestion-compatibility-failed-" + candidate["Id"][:12]
    if prepare.optional(previous) is not None or prepare.optional(failed) is not None:
        raise RuntimeError("ING_RETENTION_NAME_OCCUPIED")
    print("R4A_ING_COMPAT_SWITCH_PLAN=PASS MODE=" + args.mode + " FLYWAY=14 FROZEN_VERSION_UNCHANGED=true", flush=True)
    if args.mode == "plan":
        print("R4A_ING_COMPAT_SWITCH=PLANNED LIVE_UNCHANGED=true ATTESTATION_POST=false")
        return
    receipt = {"status": "STARTING", "old_id": old["Id"], "candidate_id": candidate["Id"],
               "revision": prepare.REVISION, "rollback_container": previous,
               "failed_container": failed, "db_dump": None, "history": before}
    save(receipt)
    print("R4A_ING_COMPAT_SWITCH=STOPPING_LIVE ATTESTATION_POST=false", flush=True)
    try:
        if (prepare.stable(inventory.inspect(LIVE)) != prepare.stable(old)
                or hashlib.sha256(properties.read_bytes()).hexdigest() != properties_hash
                or Path(original_source).read_bytes() != original):
            raise RuntimeError("ING_LIVE_CHANGED_BEFORE_STOP")
        docker("update", "--restart", "no", LIVE)
        docker("stop", "--time", "60", LIVE)
        receipt["db_dump"] = str(backup_restore(before))
        save(receipt)
        if (history() != before or frozen(args) != version
                or hashlib.sha256(properties.read_bytes()).hexdigest() != properties_hash):
            raise RuntimeError("ING_DATABASE_OR_PROPERTIES_CHANGED_DURING_BACKUP")
        # Recheck the candidate immediately before the swap.
        candidate = inventory.inspect(prepare.NAME)
        if candidate["Id"] != state["candidate_id"] or not prepare.matches(candidate, old, image, properties):
            raise RuntimeError("ING_CANDIDATE_CHANGED_BEFORE_SWAP")
        docker("rename", LIVE, previous)
        docker("rename", prepare.NAME, LIVE)
        docker("start", LIVE)
        ready()
        current = inventory.inspect(LIVE)
        if (current["Id"] != state["candidate_id"] or current["Image"] != state["image_id"]
                or prepare.environment(current) != prepare.environment(old)
                or prepare.mounts(current) != prepare.mounts(old, properties)
                or any(current["HostConfig"].get(k, 0) != old["HostConfig"].get(k, 0)
                       for k in ("Memory", "MemorySwap"))
                or history() != before or frozen(args) != version
                or hashlib.sha256(properties.read_bytes()).hexdigest() != properties_hash
                or Path(original_source).read_bytes() != original):
            raise RuntimeError("ING_POST_SWITCH_RUNTIME_OR_DATABASE_DRIFT")
        tokens_fresh(current, args.tenant_id)
        docker("update", "--restart", "unless-stopped", LIVE)
        prepare.guard(inventory.inspect(LIVE), image)
        receipt["status"] = "PASS"
        save(receipt)
        print("R4A_ING_COMPAT_SWITCH=PASS LIVE_REVISION=" + prepare.REVISION + " FLYWAY=14")
        print("R4A_ING_COMPAT_ROLLBACK_CONTAINER=" + previous)
        print("R4A_ING_COMPAT_DB_BACKUP_RETAINED=" + receipt["db_dump"])
        print("R4A_ING_COMPAT_FROZEN_VERSION=PASS ATTESTATION_POST=false DEPLOYED_CONSUMER_PROBE_PENDING=true SECRETS_NOT_PRINTED=true")
    except BaseException:
        try:
            recover(state, previous, failed)
            receipt["status"] = "ROLLED_BACK"
            print("R4A_ING_COMPAT_RUNTIME_ROLLBACK=PASS DB_NOT_AUTOMATICALLY_RESTORED=true", flush=True)
        except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError):
            receipt["status"] = "MANUAL_RECOVERY_REQUIRED"
            print("R4A_ING_COMPAT_RUNTIME_ROLLBACK=MANUAL_RECOVERY_REQUIRED DB_NOT_AUTOMATICALLY_RESTORED=true", flush=True)
        save(receipt)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "apply"))
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--expected-hash", required=True)
    try:
        main(parser.parse_args())
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_ING_COMPAT_SWITCH=BLOCKED CODE=" + code + " SECRETS_NOT_PRINTED=true")
        raise SystemExit(1)
