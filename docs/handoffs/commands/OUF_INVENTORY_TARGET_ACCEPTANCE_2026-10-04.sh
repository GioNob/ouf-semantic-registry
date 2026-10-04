#!/usr/bin/env bash
# STATO: ESEGUITO/BLOCKED, nessuna receipt PASS fornita. NON RIESEGUIRE: diagnostica §33 pendente.
# Byte eseguiti al commit f0aca1711b4bc682d91469fe6d786b7a666a091a; SHA256 25023bef6501cfeec533d795619812ef6e3c79e44398e902979a1b24e51343b5.
(
set -euo pipefail
OUF_ACCEPTANCE_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_ACCEPTANCE_TMP"' EXIT
curl --fail --silent --show-error --proto '=https' --max-time 30 \
  https://raw.githubusercontent.com/GioNob/ouf-api-gateway/a6d4e0ce0b9d66013370184a64103e0922a2e6fe/scripts/inventory_semantic_target_acceptance.py \
  -o "$OUF_ACCEPTANCE_TMP/inventory.py"
printf '%s  %s\n' \
  959be951c87824a0949872c64c8582da3bc64571d8103032f44834ff0d98451e \
  "$OUF_ACCEPTANCE_TMP/inventory.py" | sha256sum -c -
OUF_ACCEPTANCE_ROOT="/etc/ouf/deploy-snapshots/semantic-target-acceptance-inventory-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_ACCEPTANCE_ROOT"
sudo install -d -m 0700 -o root -g root \
  "$OUF_ACCEPTANCE_ROOT" "$OUF_ACCEPTANCE_ROOT/source" "$OUF_ACCEPTANCE_ROOT/prepared"
sudo install -m 0600 -o root -g root \
  "$OUF_ACCEPTANCE_TMP/inventory.py" "$OUF_ACCEPTANCE_ROOT/source/inventory.py"
printf '%s  %s\n' \
  959be951c87824a0949872c64c8582da3bc64571d8103032f44834ff0d98451e \
  "$OUF_ACCEPTANCE_ROOT/source/inventory.py" | sudo sha256sum -c -
printf 'SEMANTIC_TARGET_ACCEPTANCE_SOURCE_ROOT=%s\n' "$OUF_ACCEPTANCE_ROOT"
sudo /usr/bin/python3 -I -B "$OUF_ACCEPTANCE_ROOT/source/inventory.py" \
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
printf 'SEMANTIC_TARGET_ACCEPTANCE_EVIDENCE_ROOT=%s/prepared PRIVATE=true\n' "$OUF_ACCEPTANCE_ROOT"
)
