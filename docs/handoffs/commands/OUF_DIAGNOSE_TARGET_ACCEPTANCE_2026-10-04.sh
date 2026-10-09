#!/usr/bin/env bash
# STATO: ESEGUITO/BLOCKED. §33 CHECK=IMAGE_INSPECT REASON=TARGET_ACCEPTANCE_INVENTORY_UNPROVEN.
# Root diagnostic-20261004-145230; byte eseguiti commit014ace6, SHA2566d61183f. NON RIESEGUIRE.
(
set -euo pipefail
OUF_DIAG_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_DIAG_TMP"' EXIT
curl --fail --silent --show-error --proto '=https' --max-time 30 \
  https://raw.githubusercontent.com/GioNob/ouf-api-gateway/28272696308d449ac1380e0df0966a5224986c98/scripts/inventory_semantic_target_acceptance.py \
  -o "$OUF_DIAG_TMP/inventory.py"
printf '%s  %s\n' b0abe2d6ef0cd3a31bae7896bfedd9043beabdd83a638fa7465e9210e121af0e \
  "$OUF_DIAG_TMP/inventory.py" | sha256sum -c -
OUF_DIAG_ROOT="/etc/ouf/deploy-snapshots/semantic-target-acceptance-diagnostic-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_DIAG_ROOT"
sudo install -d -m 0700 -o root -g root \
  "$OUF_DIAG_ROOT" "$OUF_DIAG_ROOT/source" "$OUF_DIAG_ROOT/prepared"
sudo install -m 0600 -o root -g root "$OUF_DIAG_TMP/inventory.py" "$OUF_DIAG_ROOT/source/inventory.py"
printf '%s  %s\n' b0abe2d6ef0cd3a31bae7896bfedd9043beabdd83a638fa7465e9210e121af0e \
  "$OUF_DIAG_ROOT/source/inventory.py" | sudo sha256sum -c -
printf 'SEMANTIC_TARGET_ACCEPTANCE_DIAGNOSTIC_SOURCE_ROOT=%s\n' "$OUF_DIAG_ROOT"
sudo /usr/bin/python3 -I -B "$OUF_DIAG_ROOT/source/inventory.py" --diagnose \
  --manifest-root /etc/ouf/deploy-snapshots/semantic-provider-candidate-manifest-20261003-130410/prepared \
  --creation-root /etc/ouf/deploy-snapshots/semantic-provider-stopped-create-20261003-135106/prepared \
  --package-root /etc/ouf/deploy-snapshots/semantic-local-producers-package-20261004-121542 \
  --snapshot-root "$OUF_DIAG_ROOT/prepared" --docker-path /usr/bin/docker \
  --expected-manifest-hash 052b46a56ea666971f135c75af48b3342dbeb68e2f17f1f16263a99351df88bd \
  --expected-creation-journal-hash a1c2acd9924fc0f924ded7c2d59f128ef2d8b8dd11c62484a901f628022aaae7 \
  --creation-source-commit 93e861fe8c8a43912f0cb78a74adceb2db509dd9 \
  --package-source-commit 7ded9df0c74c6db919c7a68d4c75ab2c132dea53 \
  --source-manifest-sha256 a1b11fbfb9d701101f2efa1048c7f99a54f123ed1f1b71f480ffcd883c0e560b
)
