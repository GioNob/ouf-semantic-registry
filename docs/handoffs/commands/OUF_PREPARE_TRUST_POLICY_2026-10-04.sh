#!/usr/bin/env bash
# STATO: ESEGUITO/PASS plan/apply/verify §38, 2026-10-04. NON RIPETERE.
# Root: /etc/ouf/deploy-snapshots/semantic-trust-policy-preparation-20261004-172336
# Bytes eseguiti: commit dad24714ca572ab45667313b8cc7ec748c851ce3, SHA256
# 1b3927170ba06722402050a25eb12d50bf3d5886ea443b5a1e5866770a573857.
# Conferimento37: sola policy privata di verifica ruoli.
# Nessuna nuova chiave, firma, mandato, collegamento consumer/runtime o start.
(
set -euo pipefail
OUF_POLICY_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_POLICY_TMP"' EXIT
for OUF_POLICY_FILE in prepare_semantic_trust_policy.py prepare_semantic_authority_keys.py; do
  curl --fail --silent --show-error --proto '=https' --max-time 30 \
    "https://raw.githubusercontent.com/GioNob/ouf-api-gateway/3bdedad3108112ee4c36e7cb8387aaf60912e97c/scripts/$OUF_POLICY_FILE" \
    -o "$OUF_POLICY_TMP/$OUF_POLICY_FILE"
done
printf '%s  %s\n' \
  b06cd1712588cf5c01eaec913202abe11667f68bb29ec3ed5121949abff036bf \
  "$OUF_POLICY_TMP/prepare_semantic_trust_policy.py" \
  095a9cd9523bc1ee2767737656884ff7e08b254a6b1aab015c977403e2b1e3ec \
  "$OUF_POLICY_TMP/prepare_semantic_authority_keys.py" | sha256sum -c -
OUF_POLICY_ROOT="/etc/ouf/deploy-snapshots/semantic-trust-policy-preparation-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_POLICY_ROOT"
sudo install -d -m 0700 -o root -g root "$OUF_POLICY_ROOT" "$OUF_POLICY_ROOT/source"
sudo install -m 0600 -o root -g root "$OUF_POLICY_TMP/"*.py "$OUF_POLICY_ROOT/source/"
printf '%s  %s\n' \
  b06cd1712588cf5c01eaec913202abe11667f68bb29ec3ed5121949abff036bf \
  "$OUF_POLICY_ROOT/source/prepare_semantic_trust_policy.py" \
  095a9cd9523bc1ee2767737656884ff7e08b254a6b1aab015c977403e2b1e3ec \
  "$OUF_POLICY_ROOT/source/prepare_semantic_authority_keys.py" | sudo sha256sum -c -
printf 'SEMANTIC_TRUST_POLICY_SOURCE_ROOT=%s PRIVATE=true\n' "$OUF_POLICY_ROOT"
for OUF_POLICY_MODE in plan apply verify; do
  sudo /usr/bin/python3 -I -B "$OUF_POLICY_ROOT/source/prepare_semantic_trust_policy.py" \
    --mode "$OUF_POLICY_MODE" \
    --inventory-root /etc/ouf/deploy-snapshots/semantic-target-acceptance-inventory-20261004-151023/prepared \
    --custody-root /etc/ouf/deploy-snapshots/semantic-authority-provisioning-20261004-164654 \
    --snapshot-root "$OUF_POLICY_ROOT" \
    --helper-source "$OUF_POLICY_ROOT/source/prepare_semantic_authority_keys.py" \
    --validator-source-root /etc/ouf/deploy-snapshots/semantic-local-producers-package-20261004-121542/source/tools \
    --installation-ref ouf-lab-netcup-01 --entity-ref ouf-lab \
    --installer-issuer-ref ouf-lab-infrastructure-installer --attestor-issuer-ref ouf-lab-node-attestor \
    --installer-key-ref ouf-lab-installer-ed25519-1 --attestor-key-ref ouf-lab-attestor-ed25519-1 \
    --dossier-sha256 a37f22635035ab8543a4654def5cd6a6f4fe45fd1affc0ff10ccc3c19f03085c \
    --authority-plan-sha256 31492d13db05b46252215bb4bde815712bd55a1e245aff25408350328fcb7093 \
    --package-receipt-sha256 f06c4b6ea2a7c05e008db3e615e35f475d44824b2073ff2d5f451c55dbce2850 \
    --custody-receipt-sha256 a134c4c8e8487860e6a8ed3a672520935a5de753d02507c4005a0475570b2d49 \
    --draft-sha256 a9e5bdbef01c391c216e23e7b99c9e9ed3d6e3a92da56e8e1e9d7b2ca91b040c \
    --openssl-path /usr/bin/openssl --openssl-sha256 f4aa15f2822f670af7b5c1043d7aa6ebbbc64229fd2fae382edfc6a4524749c1 \
    --auth-source-sha256 3f89e466638cdbb8311b661b64739c1903969758cb3bcf569d53cbdaa620386a \
    --protocol-source-sha256 87bb4cdaf6686aadbde69caddf1d1813ecc02664aeeef62b67dd80750adc15b1 \
    --helper-sha256 095a9cd9523bc1ee2767737656884ff7e08b254a6b1aab015c977403e2b1e3ec \
    --custody-source-commit 509a011cd920d9a9e9ece83a07e5b99ce05806a5 \
    --source-commit 3bdedad3108112ee4c36e7cb8387aaf60912e97c \
    --source-sha256 b06cd1712588cf5c01eaec913202abe11667f68bb29ec3ed5121949abff036bf \
    --authorize-private-role-policy-only
done
printf 'SEMANTIC_TRUST_POLICY_EVIDENCE_ROOT=%s PRIVATE=true\n' "$OUF_POLICY_ROOT"
)
