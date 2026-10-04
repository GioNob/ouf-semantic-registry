#!/usr/bin/env bash
# STATO: NON ESEGUITO. §34 wrapper canonico completo compatibile Docker29: diagnose poi inventario.
# §32 originale e §33 diagnostico restano storico BLOCKED; nessun overwrite/replay di staging.
(
set -euo pipefail
OUF_ACCEPTANCE_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_ACCEPTANCE_TMP"' EXIT
curl --fail --silent --show-error --proto '=https' --max-time 30 \
  https://raw.githubusercontent.com/GioNob/ouf-api-gateway/d42a8c563a58ed041bf7b7a2921be975e93becf5/scripts/inventory_semantic_target_acceptance.py \
  -o "$OUF_ACCEPTANCE_TMP/inventory.py"
printf '%s  %s\n' \
  10c543fa8d42839110fb8d12a385a4e58b0db43240eb07efe2e3b9b4c6f22080 \
  "$OUF_ACCEPTANCE_TMP/inventory.py" | sha256sum -c -
OUF_ACCEPTANCE_ROOT="/etc/ouf/deploy-snapshots/semantic-target-acceptance-inventory-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_ACCEPTANCE_ROOT"
sudo install -d -m 0700 -o root -g root \
  "$OUF_ACCEPTANCE_ROOT" "$OUF_ACCEPTANCE_ROOT/source" "$OUF_ACCEPTANCE_ROOT/prepared"
sudo install -m 0600 -o root -g root \
  "$OUF_ACCEPTANCE_TMP/inventory.py" "$OUF_ACCEPTANCE_ROOT/source/inventory.py"
printf '%s  %s\n' \
  10c543fa8d42839110fb8d12a385a4e58b0db43240eb07efe2e3b9b4c6f22080 \
  "$OUF_ACCEPTANCE_ROOT/source/inventory.py" | sudo sha256sum -c -
printf 'SEMANTIC_TARGET_ACCEPTANCE_SOURCE_ROOT=%s\n' "$OUF_ACCEPTANCE_ROOT"
for OUF_ACCEPTANCE_PASS in diagnose inventory; do
  OUF_ACCEPTANCE_EXTRA=()
  if [[ "$OUF_ACCEPTANCE_PASS" == diagnose ]]; then OUF_ACCEPTANCE_EXTRA=(--diagnose); fi
  sudo /usr/bin/python3 -I -B "$OUF_ACCEPTANCE_ROOT/source/inventory.py" "${OUF_ACCEPTANCE_EXTRA[@]}" \
  --manifest-root /etc/ouf/deploy-snapshots/semantic-provider-candidate-manifest-20261003-130410/prepared \
  --creation-root /etc/ouf/deploy-snapshots/semantic-provider-stopped-create-20261003-135106/prepared \
  --package-root /etc/ouf/deploy-snapshots/semantic-local-producers-package-20261004-121542 \
  --snapshot-root "$OUF_ACCEPTANCE_ROOT/prepared" \
  --docker-path /usr/bin/docker \
  --expected-manifest-hash 052b46a56ea666971f135c75af48b3342dbeb68e2f17f1f16263a99351df88bd \
  --expected-creation-journal-hash a1c2acd9924fc0f924ded7c2d59f128ef2d8b8dd11c62484a901f628022aaae7 \
  --creation-source-commit 93e861fe8c8a43912f0cb78a74adceb2db509dd9 \
  --package-source-commit 7ded9df0c74c6db919c7a68d4c75ab2c132dea53 \
  --source-manifest-sha256 a1b11fbfb9d701101f2efa1048c7f99a54f123ed1f1b71f480ffcd883c0e560b
done
printf 'SEMANTIC_TARGET_ACCEPTANCE_EVIDENCE_ROOT=%s/prepared PRIVATE=true\n' "$OUF_ACCEPTANCE_ROOT"
)
