#!/usr/bin/env python3
"""Install and refresh a bounded SERVICE bearer for Onboarding's UDP read."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ISSUER = "https://auth.ouf-lab.it/realms/ouf"
CLIENT = "ouf-source-onboarding"
SCOPE = "ouf.udp.identity.attestation.read"
SECRET = Path("/var/lib/ouf-r4a-identity/onboarding-client-secret")
TOKEN_DIR = Path("/run/ouf-onboarding-identity")
TOKEN = TOKEN_DIR / "token"
STAGED = SECRET.parent / "r4a_onboarding_token_runtime.py"
SERVICE = Path("/etc/systemd/system/ouf-onboarding-identity-token.service")
TIMER = Path("/etc/systemd/system/ouf-onboarding-identity-token.timer")
TMPFILES = Path("/etc/tmpfiles.d/ouf-onboarding-identity.conf")
GROUP = 10003
LEGACY_STAGED_BLOB = "52d7a261b6b06a684d4ac10751b6ce2a33c49357"

SERVICE_CONTENT = """[Unit]
Description=Refresh OUF Onboarding SERVICE bearer for UDP identity read
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
User=root
ExecStart=/usr/bin/python3 /var/lib/ouf-r4a-identity/r4a_onboarding_token_runtime.py refresh
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=/run/ouf-onboarding-identity
PrivateTmp=true
"""
LEGACY_SERVICE_CONTENT = SERVICE_CONTENT.replace("User=root\n", "User=root\nGroup=10003\n")
TIMER_CONTENT = """[Unit]
Description=Refresh OUF Onboarding SERVICE bearer every minute

[Timer]
OnBootSec=30s
OnUnitInactiveSec=60s
AccuracySec=10s
Unit=ouf-onboarding-identity-token.service

[Install]
WantedBy=timers.target
"""
TMPFILES_CONTENT = "d /run/ouf-onboarding-identity 0750 root 10003 - -\n"


def protected(path, mode, owner=0, group=None):
    metadata = path.lstat()
    if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != owner
        or stat.S_IMODE(metadata.st_mode) != mode
        or (group is not None and metadata.st_gid != group)):
        raise RuntimeError("UNSAFE_FILE_METADATA")
    return metadata


def secret():
    parent = SECRET.parent.lstat()
    if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != 0
        or stat.S_IMODE(parent.st_mode) != 0o700):
        raise RuntimeError("SECRET_DIRECTORY_UNSAFE")
    protected(SECRET, 0o600)
    value = SECRET.read_text().strip()
    if not value or len(value) > 4096 or any(character.isspace() for character in value):
        raise RuntimeError("SECRET_INVALID")
    return value


def claims(value):
    if not isinstance(value, str) or len(value) > 16384 or value.count(".") != 2:
        raise RuntimeError("TOKEN_FORMAT_INVALID")
    part = value.split(".")[1]
    data = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
    audiences = data.get("aud")
    audiences = {audiences} if isinstance(audiences, str) else set(audiences or [])
    if (data.get("iss") != ISSUER or "ouf-api-gateway" not in audiences
        or SCOPE not in str(data.get("scope", "")).split()
        or data.get("ouf_actor_type") != "SERVICE"
        or data.get("tenant_id") != "ouf-lab"
        or (data.get("client_id") or data.get("azp")) != CLIENT
        or not data.get("sub") or not data.get("acr")
        or not isinstance(data.get("exp"), int)
        or data["exp"] - time.time() < 120):
        raise RuntimeError("TOKEN_CLAIMS_OR_LIFETIME_INVALID")
    return int(data["exp"] - time.time())


def directory():
    metadata = TOKEN_DIR.lstat()
    if (not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != 0
        or metadata.st_gid != GROUP or stat.S_IMODE(metadata.st_mode) != 0o750):
        raise RuntimeError("TOKEN_DIRECTORY_UNSAFE")


def refresh():
    if os.geteuid() != 0:
        raise RuntimeError("ROOT_REQUIRED")
    directory()
    credential = secret()
    basic = base64.b64encode((CLIENT + ":" + credential).encode()).decode()
    request = Request(ISSUER + "/protocol/openid-connect/token",
                      data=urlencode({"grant_type": "client_credentials"}).encode(),
                      headers={"Authorization": "Basic " + basic,
                               "Content-Type": "application/x-www-form-urlencoded"})
    with urlopen(request, timeout=12) as response:
        payload = json.load(response)
    if str(payload.get("token_type", "")).lower() != "bearer":
        raise RuntimeError("TOKEN_TYPE_INVALID")
    value = payload.get("access_token")
    ttl = claims(value)
    os.umask(0o077)
    fd, temporary = tempfile.mkstemp(prefix=".token-", dir=TOKEN_DIR)
    try:
        with os.fdopen(fd, "w") as stream:
            os.fchown(stream.fileno(), 0, GROUP)
            os.fchmod(stream.fileno(), 0o640)
            stream.write(value + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, TOKEN)
        directory_fd = os.open(TOKEN_DIR, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        Path(temporary).unlink(missing_ok=True)
    print("R4A_ONBOARDING_TOKEN_REFRESH=PASS TTL_SECONDS=" + str(ttl)
          + " TOKEN_NOT_PRINTED=true")


def approved_existing(path, content):
    if path == SERVICE:
        return content == LEGACY_SERVICE_CONTENT
    if path == STAGED:
        raw = content.encode()
        blob = b"blob " + str(len(raw)).encode() + b"\0" + raw
        return hashlib.sha1(blob).hexdigest() == LEGACY_STAGED_BLOB
    return False


def verify_existing(path, content, mode):
    if path.exists():
        protected(path, mode)
        existing = path.read_text()
        if existing != content and not approved_existing(path, existing):
            raise RuntimeError("INSTALLATION_FILE_DRIFT")


def install_file(path, content, mode):
    if path.exists():
        verify_existing(path, content, mode)
        if path.read_text() == content:
            return
        fd, temporary = tempfile.mkstemp(prefix=".r4a-unit-", dir=path.parent)
        try:
            with os.fdopen(fd, "w") as stream:
                os.fchmod(stream.fileno(), mode)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            Path(temporary).unlink(missing_ok=True)
        return
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    with os.fdopen(descriptor, "w") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def install():
    if os.geteuid() != 0:
        raise RuntimeError("ROOT_REQUIRED")
    print("R4A_TOKEN_INSTALL_STAGE=VERIFY_INPUTS", flush=True)
    secret()
    own_source = Path(__file__).read_text()
    files = ((STAGED, own_source, 0o600), (TMPFILES, TMPFILES_CONTENT, 0o644),
             (SERVICE, SERVICE_CONTENT, 0o644), (TIMER, TIMER_CONTENT, 0o644))
    for path, content, mode in files:
        verify_existing(path, content, mode)
    print("R4A_TOKEN_INSTALL_STAGE=WRITE_UNITS", flush=True)
    for path, content, mode in files:
        install_file(path, content, mode)
    print("R4A_TOKEN_INSTALL_STAGE=PREPARE_DIRECTORY", flush=True)
    subprocess.run(["systemd-tmpfiles", "--create", str(TMPFILES)], check=True,
                   capture_output=True, timeout=15)
    directory()
    print("R4A_TOKEN_INSTALL_STAGE=START_REFRESH", flush=True)
    subprocess.run(["systemctl", "daemon-reload"], check=True,
                   capture_output=True, timeout=20)
    subprocess.run(["systemctl", "start", SERVICE.name], check=True,
                   capture_output=True, timeout=30)
    subprocess.run(["systemctl", "enable", "--now", TIMER.name], check=True,
                   capture_output=True, timeout=25)
    subprocess.run(["systemctl", "is-active", "--quiet", TIMER.name], check=True,
                   capture_output=True, timeout=10)
    protected(TOKEN, 0o640, group=GROUP)
    if claims(TOKEN.read_text().strip()) < 120:
        raise RuntimeError("TOKEN_EXPIRES_TOO_SOON")
    print("R4A_ONBOARDING_TOKEN_RUNTIME=PASS TIMER_ENABLED=true MOUNT_DIRECTORY="
          + str(TOKEN_DIR) + " TOKEN_NOT_PRINTED=true")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "refresh"))
    arguments = parser.parse_args()
    try:
        {"install": install, "refresh": refresh}[arguments.action]()
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError,
            RuntimeError) as error:
        detail = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_ONBOARDING_TOKEN_RUNTIME=BLOCKED REASON=" + detail
              + " TOKEN_NOT_PRINTED=true")
        raise SystemExit(1)
