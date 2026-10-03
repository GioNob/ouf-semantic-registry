(
set -euo pipefail
OUF_PREEXEC_PKG_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_PREEXEC_PKG_TMP"' EXIT

cat > "$OUF_PREEXEC_PKG_TMP/sources.sha256" <<'OUF_PREEXEC_SHA'
84f6b1fec995b9675284253321930efee0056e4546168058bae6a3667a2ff7d7  scripts/stage_semantic_admission_package.py
3fb04519de05131087a5bd12095b42f97026e7c5826d5f8f3845608404008f95  scripts/stage_semantic_preexec_package.py
3106ade7c32e5d37ce7aa0214726907a3422c2850741168b7ee7d273b98b00fb  scripts/semantic_provider_docker_runtime.py
5f38532f73f620cbbc9980b02a2e29cd8a4cdabafce370aba5a8a50e330065a5  scripts/semantic_provider_preexec_hook.py
5b31650fddb0d47dad99f128d0d8775bde56a2f7489b0f5476956e17eaba125d  scripts/semantic_provider_admission_preparer.py
98e3004300226fecd509a46c009585df14021927f20d4e5c82d8ff7a8a8180de  tools/materialize_southbound_kernel.py
1c0d7f1243752fe216ef62eefbc2e3253b8f2503b518fafe11277e4d7721a084  tools/materialize_southbound_lease_refresh.py
c466172113d1ffe850bf2c69762113b55fbc65d9091c96dca98a74548fddf930  tools/semantic_provider_dns.py
7a5f2b21c096228a3e4d298674e380f667c3004dd6d8ec19934a2302844c0f93  tools/semantic_provider_lease_nft.py
92736eebeccf344e565186bce94d29c65ffe1d50638d57eae81486e7b26e884d  tools/semantic_provider_lease_owner.py
b97f31cc17c22abbb7a021c274be73816f649196762f9c6dfcc54a58d8382e8a  tools/materialize_semantic_shared_faces.py
25c6df90d33e39fe83321df6ab9e5c38d4c33bcd290ad57c7a85c03b1bb8ba78  tools/semantic_provider_lease_coordination.py
b0fc54f39ec1b650a1e51a721127cca2cda1c2cd6bd9c2179919929a1cb50bc7  tools/semantic_provider_preexec.py
ef0b98c96879933480a26418edc2b971b21a116509ac87cbc39e3b2062e7a528  tools/semantic_provider_preexec_native.py
4bd0051fad23acd91fc42eb9b6cd2f2dac6e8d9d960fefd391add261a3646499  tools/semantic_provider_deployment_admission.py
OUF_PREEXEC_SHA

while read -r OUF_PREEXEC_HASH OUF_PREEXEC_FILE; do
  mkdir -p -- "$OUF_PREEXEC_PKG_TMP/$(dirname -- "$OUF_PREEXEC_FILE")"
  curl --fail --silent --show-error --proto '=https' --max-time 30 \
    "https://raw.githubusercontent.com/GioNob/ouf-api-gateway/ed6fab81acc17591a1087761266701f877233799/$OUF_PREEXEC_FILE" \
    -o "$OUF_PREEXEC_PKG_TMP/$OUF_PREEXEC_FILE"
done < "$OUF_PREEXEC_PKG_TMP/sources.sha256"

(cd "$OUF_PREEXEC_PKG_TMP"; sha256sum -c sources.sha256)

OUF_PREEXEC_PKG_ROOT="/etc/ouf/deploy-snapshots/semantic-admission-package-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_PREEXEC_PKG_ROOT"
sudo install -d -m 0700 -o root -g root \
  "$OUF_PREEXEC_PKG_ROOT/source/scripts" "$OUF_PREEXEC_PKG_ROOT/source/tools"
while read -r OUF_PREEXEC_HASH OUF_PREEXEC_FILE; do
  sudo install -m 0600 -o root -g root \
    "$OUF_PREEXEC_PKG_TMP/$OUF_PREEXEC_FILE" "$OUF_PREEXEC_PKG_ROOT/source/$OUF_PREEXEC_FILE"
done < "$OUF_PREEXEC_PKG_TMP/sources.sha256"
printf 'SEMANTIC_ADMISSION_PACKAGE_ROOT=%s\n' "$OUF_PREEXEC_PKG_ROOT"

for OUF_PREEXEC_PKG_MODE in plan apply verify; do
  sudo /usr/bin/python3 -I -B \
    "$OUF_PREEXEC_PKG_ROOT/source/scripts/stage_semantic_admission_package.py" \
    --mode "$OUF_PREEXEC_PKG_MODE" \
    --package-root "$OUF_PREEXEC_PKG_ROOT" \
    --source-commit ed6fab81acc17591a1087761266701f877233799 \
    --hook-source-sha256 5f38532f73f620cbbc9980b02a2e29cd8a4cdabafce370aba5a8a50e330065a5
done
)
