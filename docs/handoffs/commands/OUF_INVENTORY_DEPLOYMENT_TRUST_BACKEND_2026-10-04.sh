#!/usr/bin/env bash
# §26 NON ESEGUITO: read-only public signature backend inventory.
set -euo pipefail
OUF_TRUST_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_TRUST_TMP"' EXIT
curl --fail --silent --show-error --proto '=https' --max-time 30 \
  https://raw.githubusercontent.com/GioNob/ouf-api-gateway/023cd4687c3a8e8627ab1bf6629834e3c1174d35/scripts/inventory_semantic_deployment_trust_backend.py \
  -o "$OUF_TRUST_TMP/inventory.py"
curl --fail --silent --show-error --proto '=https' --max-time 30 \
  https://raw.githubusercontent.com/GioNob/ouf-semantic-registry/d033b0b8a3bfafaa405ea8f9745ac7c0c6e99f90/docs/handoffs/receipts/SEMANTIC_DEPLOYMENT_PACKAGE_V4_2026-10-04_OPERATOR.json \
  -o "$OUF_TRUST_TMP/operator.json"
printf '%s  %s\n' \
  c0a1a349119ecc016c37e9a53b233935d6c3450d13f5cf0c06749b1589cd7e82 "$OUF_TRUST_TMP/inventory.py" \
  315cf438aa8dec194958e61a99a8364526531b72472cdb9f74bee930a5e15146 "$OUF_TRUST_TMP/operator.json" | sha256sum -c -
OUF_TRUST_ROOT="/etc/ouf/deploy-snapshots/semantic-deployment-trust-backend-inventory-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_TRUST_ROOT"
sudo install -d -m 0700 -o root -g root "$OUF_TRUST_ROOT/source"
sudo install -m 0600 -o root -g root "$OUF_TRUST_TMP/inventory.py" "$OUF_TRUST_TMP/operator.json" "$OUF_TRUST_ROOT/source/"
printf 'SEMANTIC_DEPLOYMENT_TRUST_BACKEND_SOURCE_ROOT=%s\n' "$OUF_TRUST_ROOT"
sudo /usr/bin/python3 -I -B "$OUF_TRUST_ROOT/source/inventory.py" \
  --package-root /etc/ouf/deploy-snapshots/semantic-deployment-package-20261004-072744 \
  --operator-attestation "$OUF_TRUST_ROOT/source/operator.json" \
  --openssl-path /usr/bin/openssl
