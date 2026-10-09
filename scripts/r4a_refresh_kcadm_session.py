#!/usr/bin/env python3
"""Refresh the existing kcadm session using Keycloak container bootstrap env."""

import subprocess


SCRIPT = r'''
set -eu
test -n "${KC_BOOTSTRAP_ADMIN_USERNAME:-}"
test -n "${KC_BOOTSTRAP_ADMIN_PASSWORD:-}"
/opt/keycloak/bin/kcadm.sh config credentials \
  --server https://auth.ouf-lab.it --realm master \
  --user "$KC_BOOTSTRAP_ADMIN_USERNAME" \
  --password "$KC_BOOTSTRAP_ADMIN_PASSWORD" >/dev/null 2>&1
/opt/keycloak/bin/kcadm.sh get realms/ouf -r master --fields realm >/dev/null 2>&1
'''


def main():
    result = subprocess.run(["docker", "exec", "ouf-keycloak", "sh", "-c", SCRIPT],
                            capture_output=True, text=True, timeout=40)
    if result.returncode:
        raise RuntimeError("KCADM_REFRESH_OR_READ_FAILED")
    print("KCADM_SESSION_REFRESHED=true REALM_OUF_READ=PASS SECRET_VALUES_PRINTED=false")


if __name__ == "__main__":
    try:
        main()
    except (OSError, subprocess.TimeoutExpired, RuntimeError) as error:
        print("KCADM_REFRESH_BLOCKED=" + type(error).__name__)
        raise SystemExit(1)
