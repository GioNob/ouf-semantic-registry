# HISTORICAL: operator executed plan/apply/verify PASS on 2026-10-03.
# Attested root: /etc/ouf/deploy-snapshots/semantic-preexec-adapter-package-20261003-213033
# Preserve the completed snapshot; do not replay this command automatically.
(
set -euo pipefail
OUF_PREEXEC_PKG_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_PREEXEC_PKG_TMP"' EXIT

cat > "$OUF_PREEXEC_PKG_TMP/sources.sha256" <<'OUF_PREEXEC_SHA'
3fb04519de05131087a5bd12095b42f97026e7c5826d5f8f3845608404008f95  scripts/stage_semantic_preexec_package.py
f4185658a7a9a1190cd9ee85ed6f6397de5344bad15a6d3078d765f88c914093  scripts/semantic_provider_docker_runtime.py
2da64dc68707fb694a49656562800d733184a21845293fee172a6f99167534b3  scripts/semantic_provider_preexec_hook.py
98e3004300226fecd509a46c009585df14021927f20d4e5c82d8ff7a8a8180de  tools/materialize_southbound_kernel.py
1c0d7f1243752fe216ef62eefbc2e3253b8f2503b518fafe11277e4d7721a084  tools/materialize_southbound_lease_refresh.py
c466172113d1ffe850bf2c69762113b55fbc65d9091c96dca98a74548fddf930  tools/semantic_provider_dns.py
7a5f2b21c096228a3e4d298674e380f667c3004dd6d8ec19934a2302844c0f93  tools/semantic_provider_lease_nft.py
92736eebeccf344e565186bce94d29c65ffe1d50638d57eae81486e7b26e884d  tools/semantic_provider_lease_owner.py
b97f31cc17c22abbb7a021c274be73816f649196762f9c6dfcc54a58d8382e8a  tools/materialize_semantic_shared_faces.py
25c6df90d33e39fe83321df6ab9e5c38d4c33bcd290ad57c7a85c03b1bb8ba78  tools/semantic_provider_lease_coordination.py
f541eca6bee47a68a08d06ad7b577a3a7894ca02d8674d97e36d6cb2bafe0fcd  tools/semantic_provider_preexec.py
b6b09ef5209d92405d85ef4161b671ade10c300b797569362c301ae9293b6ac0  tools/semantic_provider_preexec_native.py
OUF_PREEXEC_SHA

while read -r OUF_PREEXEC_HASH OUF_PREEXEC_FILE; do
  mkdir -p -- "$OUF_PREEXEC_PKG_TMP/$(dirname -- "$OUF_PREEXEC_FILE")"
  curl --fail --silent --show-error --proto '=https' --max-time 30 \
    "https://raw.githubusercontent.com/GioNob/ouf-api-gateway/b5260260fff1adf798626f12e24323c20ae1bb2e/$OUF_PREEXEC_FILE" \
    -o "$OUF_PREEXEC_PKG_TMP/$OUF_PREEXEC_FILE"
done < "$OUF_PREEXEC_PKG_TMP/sources.sha256"

(cd "$OUF_PREEXEC_PKG_TMP"; sha256sum -c sources.sha256)

OUF_PREEXEC_PKG_ROOT="/etc/ouf/deploy-snapshots/semantic-preexec-adapter-package-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_PREEXEC_PKG_ROOT"
sudo install -d -m 0700 -o root -g root \
  "$OUF_PREEXEC_PKG_ROOT/source/scripts" "$OUF_PREEXEC_PKG_ROOT/source/tools"
while read -r OUF_PREEXEC_HASH OUF_PREEXEC_FILE; do
  sudo install -m 0600 -o root -g root \
    "$OUF_PREEXEC_PKG_TMP/$OUF_PREEXEC_FILE" "$OUF_PREEXEC_PKG_ROOT/source/$OUF_PREEXEC_FILE"
done < "$OUF_PREEXEC_PKG_TMP/sources.sha256"
printf 'SEMANTIC_PREEXEC_PACKAGE_ROOT=%s\n' "$OUF_PREEXEC_PKG_ROOT"

for OUF_PREEXEC_PKG_MODE in plan apply verify; do
  sudo /usr/bin/python3 -I -B \
    "$OUF_PREEXEC_PKG_ROOT/source/scripts/stage_semantic_preexec_package.py" \
    --mode "$OUF_PREEXEC_PKG_MODE" \
    --package-root "$OUF_PREEXEC_PKG_ROOT" \
    --source-commit b5260260fff1adf798626f12e24323c20ae1bb2e \
    --hook-source-sha256 2da64dc68707fb694a49656562800d733184a21845293fee172a6f99167534b3
done
)
