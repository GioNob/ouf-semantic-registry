#!/usr/bin/env python3
"""Reconcile exact R4a Keycloak scopes and the Onboarding SERVICE client."""

import argparse
import os
from pathlib import Path
import stat
import subprocess
import sys


HERE = Path(__file__).resolve().parent
HUMAN = ("urban.identity.preflight", "resolution.issue.read", "resolution.match.approve")
SERVICE = "ouf.udp.identity.attestation.read"
SECRET_DIR = Path("/var/lib/ouf-r4a-identity")
SECRET_FILE = SECRET_DIR / "onboarding-client-secret"


def call(script, mode, *args):
    result = subprocess.run([sys.executable, str(HERE / script), mode, *args],
                            capture_output=True, text=True, timeout=90)
    if result.returncode:
        print("IAM_STEP_BLOCKED=" + script + " MODE=" + mode + " EXIT="
              + str(result.returncode), flush=True)
        raise RuntimeError("IAM_RECONCILE_STEP_FAILED")
    print(result.stdout.strip(), flush=True)
    return result.stdout


def directory():
    parent = SECRET_DIR.parent
    pst = parent.lstat()
    if parent.is_symlink() or pst.st_uid != 0 or not stat.S_ISDIR(pst.st_mode) \
            or stat.S_IMODE(pst.st_mode) & 0o022:
        raise RuntimeError("IAM_SECRET_PARENT_INVALID")
    SECRET_DIR.mkdir(mode=0o700, exist_ok=True)
    st = SECRET_DIR.lstat()
    if SECRET_DIR.is_symlink() or st.st_uid != 0 or stat.S_IMODE(st.st_mode) != 0o700:
        raise RuntimeError("IAM_SECRET_DIRECTORY_NOT_PRIVATE")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "apply", "verify"))
    args = parser.parse_args()
    if args.mode == "apply" and os.geteuid() != 0:
        raise RuntimeError("IAM_APPLY_REQUIRES_ROOT")
    if args.mode == "apply":
        directory()
    print("R4A_IAM_MODE=" + args.mode.upper(), flush=True)
    missing = set()
    for scope in (*HUMAN, SERVICE):
        output = call("reconcile-keycloak-client-scope-definition.py", args.mode,
                      "--scope", scope)
        if "EXISTS=false" in output:
            missing.add(scope)
    for scope in HUMAN:
        if args.mode == "plan" and scope in missing:
            print("IAM_ASSIGNMENT_PLAN_DEFERRED=" + scope + " SCOPE_MISSING=true", flush=True)
            continue
        call("reconcile-keycloak-client-scope.py", args.mode,
             "--client-id", "ouf-human-admin", "--scope", scope,
             "--assignment", "optional")
    workload_args = ("--client-id", "ouf-source-onboarding", "--tenant", "ouf-lab",
                     "--audience", "ouf-api-gateway", "--required-scope", SERVICE)
    if args.mode == "apply":
        call("provision-keycloak-workload.py", "apply", *workload_args,
             "--secret-output", str(SECRET_FILE))
    elif args.mode == "plan" and SERVICE in missing:
        print("IAM_WORKLOAD_PLAN_DEFERRED=SERVICE_SCOPE_MISSING", flush=True)
    else:
        call("provision-keycloak-workload.py", args.mode, *workload_args)
    if args.mode == "verify":
        st = SECRET_FILE.stat()
        if st.st_uid != 0 or stat.S_IMODE(st.st_mode) != 0o600 or SECRET_FILE.is_symlink():
            raise RuntimeError("IAM_SECRET_METADATA_INVALID")
        print("IAM_SERVICE_SECRET_METADATA=ROOT_0600", flush=True)
    if args.mode == "apply":
        st = SECRET_FILE.stat()
        if st.st_uid != 0 or stat.S_IMODE(st.st_mode) != 0o600:
            raise RuntimeError("IAM_SECRET_METADATA_INVALID")
        print("IAM_SERVICE_SECRET_METADATA=ROOT_0600", flush=True)
    print("R4A_IAM_RECONCILE=PASS MODE=" + args.mode.upper()
          + " SECRET_VALUES_PRINTED=false", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        print("R4A_IAM_RECONCILE_BLOCKED=" + type(error).__name__ + ":" + str(error))
        raise SystemExit(1)
