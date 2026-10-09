#!/usr/bin/env python3
"""Diagnose the UDP 403 on an isolated database clone and temporary container."""

import base64
import importlib.util
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, build_opener, ProxyHandler


REPO = Path("/opt/ouf/semantic")
HELPER_REVISION = "90cfbea6ab598698b4052d15c51d7d6b43b9f30b"
BACKUP = Path("/opt/ouf/r4a-stage/udp-before-principal-fix-9pruwm49.dump")
MANIFEST = Path("/opt/ouf/r4a-stage/udp-principal-fix-image.json")
TOKEN = Path("/run/ouf-onboarding-identity/token")
EXPECTED_LIVE = "3402050b36ee28758e5255a57b0d32bc3983a34f"
EXPECTED_PROBE = "edaba2bff18a2aaf52d1180f21f0e68984cc3437"
EXTRA_ENV = {}


def helper():
    git = ["git", "-c", "safe.directory=" + str(REPO), "-C", str(REPO)]
    if subprocess.check_output([*git, "rev-parse", HELPER_REVISION + "^{commit}"],
                               stderr=subprocess.DEVNULL).decode().strip() != HELPER_REVISION:
        raise RuntimeError("PINNED_HELPER_MISSING")
    source = subprocess.check_output([*git, "show", HELPER_REVISION +
        ":scripts/r4a_probe_udp_migration.py"], stderr=subprocess.DEVNULL)
    spec = importlib.util.spec_from_loader("r4a_probe_udp_migration", loader=None)
    module = importlib.util.module_from_spec(spec)
    exec(compile(source, "r4a_probe_udp_migration.py", "exec"), module.__dict__)
    return module


def probe_request(ip, token):
    address = ipaddress.ip_address(ip)
    if address.version != 4 or not address.is_private:
        raise RuntimeError("PROBE_ADDRESS_NOT_PRIVATE")
    query = urlencode({"configurationHash": "sha256:" + "0" * 64,
                       "sourceId": "r4a-diagnostic-absent"})
    url = "http://" + ip + ":8080/api/udp/v1/governance/internal/identity/preflight?" + query
    request = Request(url, headers={"Accept": "application/json",
                                    "Authorization": "Bearer " + token})
    opener = build_opener(ProxyHandler({}))
    try:
        with opener.open(request, timeout=15) as response:
            code, raw = response.status, response.read(4096)
    except HTTPError as error:
        code, raw = error.code, error.read(4096)
    try:
        body = json.loads(raw)
    except ValueError:
        body = {}
    print("R4A_PROBE_SERVICE_HTTP=" + str(code), flush=True)
    print("R4A_PROBE_SERVICE_JSON_KEYS=" + json.dumps(sorted(body) if isinstance(body, dict)
          else []), flush=True)
    if isinstance(body, dict):
        reasons = ("TRUSTED_PRINCIPAL_REQUIRED", "NO_POLICY_BUNDLE",
                   "STALE_POLICY_BUNDLE", "TENANT_MISMATCH", "HUMAN_REQUIRED",
                   "UDP_IDENTITY_PREFLIGHT_NOT_FOUND", "CAPABILITY_DENIED")
        found = next((reason for reason in reasons if any(reason in str(body.get(field, ""))
                     for field in ("message", "detail", "error"))), "UNEXPOSED")
        print("R4A_PROBE_SERVICE_AUTH_REASON=" + found, flush=True)
        for key in ("message", "detail", "error"):
            value = body.get(key)
            if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_ .:-]{1,100}", value):
                print("R4A_PROBE_SERVICE_" + key.upper() + "=" + value, flush=True)


def service_token():
    token = TOKEN.read_text().strip()
    if len(token) > 16384 or token.count(".") != 2:
        raise RuntimeError("SERVICE_TOKEN_INVALID")
    segment = token.split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))
    if (claims.get("exp", 0) < time.time() + 120
        or claims.get("ouf_actor_type") != "SERVICE"
        or "ouf.udp.identity.attestation.read" not in str(claims.get("scope", "")).split()):
        raise RuntimeError("SERVICE_TOKEN_CLAIMS_CHANGED")
    return token


def main():
    if os.geteuid() != 0:
        raise RuntimeError("ROOT_REQUIRED")
    h = helper()
    live = h.inspect("ouf-udp")
    image = h.inspect(live["Image"])
    staged = json.loads(MANIFEST.read_text())
    if (not live["State"]["Running"] or h.version("ouf_udp") != "34"
        or (image["Config"].get("Labels") or {}).get("org.opencontainers.image.revision")
           != EXPECTED_LIVE or staged["commit"] != EXPECTED_PROBE
        or staged["previous_live_image_id"] != live["Image"]
        or h.inspect(staged["image_id"])["Id"] != staged["image_id"]
        or len(h.mounts(live)) != 2 or BACKUP.stat().st_size < 1024):
        raise RuntimeError("PINNED_PROBE_PREFLIGHT_CHANGED")
    with BACKUP.open("rb") as stream:
        subprocess.run(["docker", "exec", "-i", "ouf-postgres", "pg_restore", "-l"],
                       stdin=stream, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                       check=True, timeout=90)
    service_token()
    pg = h.inspect("ouf-postgres")
    pg_env = dict(item.partition("=")[::2] for item in pg["Config"]["Env"])
    admin = pg_env.get("POSTGRES_USER", "postgres")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", admin):
        raise RuntimeError("POSTGRES_ADMIN_INVALID")
    flags = h.admin_command("psql", "-U", admin, "-d", "ouf_udp", "-Atc",
                            "select rolsuper::text||':'||rolcreatedb::text "
                            "from pg_roles where rolname=current_user")
    if flags not in {"true:true", "true:false", "false:true"}:
        raise RuntimeError("POSTGRES_ADMIN_CANNOT_CLONE")
    rows = h.docker("exec", "ouf-postgres", "psql", "-U", "ouf_udp", "-d", "ouf_udp",
                    "-Atc", "select extname||':'||extversion from pg_extension "
                    "where extname<>'plpgsql' order by extname").splitlines()
    extensions = [row.split(":", 1) for row in rows]
    if any(not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", name) for name, _ in extensions):
        raise RuntimeError("EXTENSION_NAME_INVALID")
    if extensions and not flags.startswith("true:"):
        raise RuntimeError("POSTGRES_EXTENSION_ADMIN_REQUIRED")
    suffix = secrets.token_hex(4)
    database, name = "ouf_udp_auth_probe_" + suffix, "ouf-udp-auth-probe-" + suffix
    created_db = created_container = False
    print("R4A_UDP_AUTH_PROBE=ISOLATED LIVE_FLYWAY=34", flush=True)
    try:
        h.admin_command("createdb", "-U", admin, "-O", "ouf_udp", database)
        created_db = True
        for extension, expected in extensions:
            h.admin_command("psql", "-U", admin, "-d", database,
                            "-v", "ON_ERROR_STOP=1", "-Atc",
                            "create extension if not exists " + extension)
            actual = h.docker("exec", "ouf-postgres", "psql", "-U", "ouf_udp", "-d",
                              database, "-Atc", "select extversion from pg_extension "
                              "where extname='" + extension + "'")
            if actual != expected:
                raise RuntimeError("EXTENSION_VERSION_DRIFT")
        with BACKUP.open("rb") as stream:
            restored = subprocess.run(["docker", "exec", "-i", "ouf-postgres", "sh", "-c",
                'PGPASSWORD="${POSTGRES_PASSWORD:-}" exec "$@"', "auth-probe",
                "pg_restore", "-U", admin, "-d", database, "--no-acl", "--no-comments"],
                stdin=stream, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=300)
        if restored.returncode:
            print("R4A_PROBE_RESTORE_ERROR_CATEGORIES=" + json.dumps(
                h.restore_error_category(restored.stderr.decode("utf-8", "replace"))), flush=True)
            raise RuntimeError("CLONE_RESTORE_FAILED")
        if h.version(database) != "34" or h.application_ownership(database) != h.application_ownership("ouf_udp"):
            raise RuntimeError("CLONE_VERSION_OR_OWNERSHIP_DRIFT")
        env = dict(entry.partition("=")[::2] for entry in live["Config"]["Env"])
        updated, count = re.subn(r"/ouf_udp(?=$|\?)", "/" + database,
                                 env.get("OUF_UDP_DB_URL", ""))
        if count != 1:
            raise RuntimeError("JDBC_DATABASE_PATH_UNEXPECTED")
        env["OUF_UDP_DB_URL"] = updated
        env["OUF_UDP_EXECUTION_ENABLED"] = "false"
        env["OUF_UDP_LAKE_MAINTENANCE_INITIAL_DELAY_MS"] = "3600000"
        env["OUF_UDP_LAKE_SHADOW_INITIAL_DELAY_MS"] = "3600000"
        env["SERVER_ERROR_INCLUDE_MESSAGE"] = "always"
        env.update(EXTRA_ENV)
        os.umask(0o077)
        fd, env_file = tempfile.mkstemp(prefix="ouf-r4a-auth-probe-env-", dir="/run")
        try:
            with os.fdopen(fd, "w") as stream:
                stream.writelines(key + "=" + value + "\n" for key, value in env.items())
            args = ["docker", "create", "--name", name, "--network", "ouf-backend",
                    "--restart", "no", "--user", "10004:10004", "--env-file", env_file]
            for kind, source, destination, writable in h.mounts(live):
                if kind != "bind" or "," in source or "," in destination:
                    raise RuntimeError("BIND_MOUNT_UNSUPPORTED")
                spec = "type=bind,src=" + source + ",dst=" + destination
                args.extend(["--mount", spec if writable else spec + ",readonly"])
            args.append(staged["image_id"])
            h.run(args)
            created_container = True
        finally:
            Path(env_file).unlink(missing_ok=True)
        h.docker("start", name)
        if not h.probe_health(name):
            raise RuntimeError("CLONE_RUNTIME_UNHEALTHY")
        if h.version(database) != "34":
            raise RuntimeError("CLONE_FLYWAY_CHANGED")
        ip = h.inspect(name)["NetworkSettings"]["Networks"]["ouf-backend"]["IPAddress"]
        probe_request(ip, service_token())
    finally:
        if created_container:
            try:
                h.docker("stop", "--time", "30", name, timeout=60)
            except subprocess.CalledProcessError:
                pass
            h.docker("rm", "-f", name)
        if created_db:
            h.admin_command("dropdb", "-U", admin, "--force", database)
        if h.version("ouf_udp") != "34" or h.inspect("ouf-udp")["Image"] != live["Image"]:
            raise RuntimeError("LIVE_STATE_CHANGED_DURING_PROBE")
        print("R4A_UDP_AUTH_PROBE_CLEANUP=PASS LIVE_CONTAINER_UNCHANGED=true", flush=True)
    print("SECRET_NOT_PRINTED=true LIVE_DB_UNCHANGED=true", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, IndexError, TypeError, UnicodeError,
            subprocess.SubprocessError, RuntimeError) as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_UDP_AUTH_PROBE_BLOCKED=" + code +
              " SECRET_NOT_PRINTED=true", file=sys.stderr)
        raise SystemExit(1)
