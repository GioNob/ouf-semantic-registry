#!/usr/bin/env bash
# STATO: ESEGUITO/PASS, recovery root123655; inspect/repair e plan/apply/verify PASS.
# NON RIESEGUIRE. Byte eseguiti al commit e9d5a0e, SHA256 2d770d268cf5a9e164d6559b60c3246500009d80ab076838f9fab4387df94a5d.
# Non riutilizzare il wrapper originario; una ricevuta presente blocca la recovery.
(
set -euo pipefail
OUF_DIR_RECOVERY_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_DIR_RECOVERY_TMP"' EXIT
curl --fail --silent --show-error --proto '=https' --max-time 30 \
  https://raw.githubusercontent.com/GioNob/ouf-api-gateway/7941098e4253a50916542471328f556d979436fe/scripts/repair_semantic_local_producers_package_directory.py \
  -o "$OUF_DIR_RECOVERY_TMP/repair.py"
printf '%s  %s\n' 116efd276852fc184479017ab853fb5ccce5c30667489771f097da4f505dbac4 "$OUF_DIR_RECOVERY_TMP/repair.py" | sha256sum -c -

OUF_DIR_RECOVERY_ROOT="/etc/ouf/deploy-snapshots/semantic-local-producers-directory-recovery-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_DIR_RECOVERY_ROOT"
sudo install -d -m 0700 -o root -g root "$OUF_DIR_RECOVERY_ROOT"
sudo install -m 0600 -o root -g root "$OUF_DIR_RECOVERY_TMP/repair.py" "$OUF_DIR_RECOVERY_ROOT/repair.py"
printf '%s  %s\n' 116efd276852fc184479017ab853fb5ccce5c30667489771f097da4f505dbac4 "$OUF_DIR_RECOVERY_ROOT/repair.py" | sudo sha256sum -c -
printf 'SEMANTIC_PACKAGE_DIRECTORY_RECOVERY_SOURCE_ROOT=%s\n' "$OUF_DIR_RECOVERY_ROOT"
OUF_DIR_PACKAGE_ROOT=/etc/ouf/deploy-snapshots/semantic-local-producers-package-20261004-121542
sudo stat -c 'DIRECTORY_METADATA MODE=%a UID=%u GID=%g PATH=%n' \
  "$OUF_DIR_PACKAGE_ROOT" "$OUF_DIR_PACKAGE_ROOT/source" \
  "$OUF_DIR_PACKAGE_ROOT/source/scripts" "$OUF_DIR_PACKAGE_ROOT/source/tools"
for OUF_DIR_RECOVERY_MODE in inspect repair; do
  sudo /usr/bin/python3 -I -B "$OUF_DIR_RECOVERY_ROOT/repair.py" \
    --mode "$OUF_DIR_RECOVERY_MODE" --package-root "$OUF_DIR_PACKAGE_ROOT" \
    --source-manifest-sha256 a1b11fbfb9d701101f2efa1048c7f99a54f123ed1f1b71f480ffcd883c0e560b
done
for OUF_DIR_STAGE_MODE in plan apply verify; do
  sudo /usr/bin/python3 -I -B \
    "$OUF_DIR_PACKAGE_ROOT/source/scripts/stage_semantic_local_producers_package.py" \
    --mode "$OUF_DIR_STAGE_MODE" --package-root "$OUF_DIR_PACKAGE_ROOT" \
    --source-commit 7ded9df0c74c6db919c7a68d4c75ab2c132dea53 \
    --source-manifest-sha256 a1b11fbfb9d701101f2efa1048c7f99a54f123ed1f1b71f480ffcd883c0e560b
done
)

