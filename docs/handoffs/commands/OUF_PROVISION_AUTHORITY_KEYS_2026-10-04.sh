#!/usr/bin/env bash
# STATO: ESEGUITO/PASS. §36 plan/apply/verify completati; NON RIPETERE né rigenerare.
# Root164654. Byte eseguiti commit1e129e0, SHA25614c506fc; hash receipt/draft nei documenti.
# Nessuna firma deployment, policy ACTIVE, producer, runtime registration o start autorizzati.
(
set -euo pipefail
OUF_KEYS_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_KEYS_TMP"' EXIT
curl --fail --silent --show-error --proto '=https' --max-time 30 \
  https://raw.githubusercontent.com/GioNob/ouf-api-gateway/509a011cd920d9a9e9ece83a07e5b99ce05806a5/scripts/prepare_semantic_authority_keys.py \
  -o "$OUF_KEYS_TMP/prepare.py"
printf '%s  %s\n' \
  095a9cd9523bc1ee2767737656884ff7e08b254a6b1aab015c977403e2b1e3ec \
  "$OUF_KEYS_TMP/prepare.py" | sha256sum -c -
OUF_KEYS_ROOT="/etc/ouf/deploy-snapshots/semantic-authority-provisioning-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_KEYS_ROOT"
sudo install -d -m 0700 -o root -g root "$OUF_KEYS_ROOT" "$OUF_KEYS_ROOT/source"
sudo install -m 0600 -o root -g root "$OUF_KEYS_TMP/prepare.py" "$OUF_KEYS_ROOT/source/prepare.py"
printf '%s  %s\n' \
  095a9cd9523bc1ee2767737656884ff7e08b254a6b1aab015c977403e2b1e3ec \
  "$OUF_KEYS_ROOT/source/prepare.py" | sudo sha256sum -c -
printf 'SEMANTIC_AUTHORITY_KEY_CUSTODY_ROOT=%s PRIVATE=true\n' "$OUF_KEYS_ROOT"
for OUF_KEYS_MODE in plan apply verify; do
  sudo /usr/bin/python3 -I -B "$OUF_KEYS_ROOT/source/prepare.py" \
    --mode "$OUF_KEYS_MODE" \
    --inventory-root /etc/ouf/deploy-snapshots/semantic-target-acceptance-inventory-20261004-151023/prepared \
    --snapshot-root "$OUF_KEYS_ROOT" \
    --installation-ref ouf-lab-netcup-01 \
    --entity-ref ouf-lab \
    --installer-issuer-ref ouf-lab-infrastructure-installer \
    --attestor-issuer-ref ouf-lab-node-attestor \
    --installer-key-ref ouf-lab-installer-ed25519-1 \
    --attestor-key-ref ouf-lab-attestor-ed25519-1 \
    --dossier-sha256 a37f22635035ab8543a4654def5cd6a6f4fe45fd1affc0ff10ccc3c19f03085c \
    --authority-plan-sha256 31492d13db05b46252215bb4bde815712bd55a1e245aff25408350328fcb7093 \
    --package-receipt-sha256 f06c4b6ea2a7c05e008db3e615e35f475d44824b2073ff2d5f451c55dbce2850 \
    --openssl-path /usr/bin/openssl \
    --openssl-sha256 f4aa15f2822f670af7b5c1043d7aa6ebbbc64229fd2fae382edfc6a4524749c1 \
    --source-commit 509a011cd920d9a9e9ece83a07e5b99ce05806a5 \
    --source-sha256 095a9cd9523bc1ee2767737656884ff7e08b254a6b1aab015c977403e2b1e3ec \
    --authorize-key-generation-only
done
printf 'SEMANTIC_AUTHORITY_KEY_CUSTODY_EVIDENCE_ROOT=%s PRIVATE=true\n' "$OUF_KEYS_ROOT"
)
