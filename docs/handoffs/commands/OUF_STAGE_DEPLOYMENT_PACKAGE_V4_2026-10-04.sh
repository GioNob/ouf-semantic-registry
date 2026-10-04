# HISTORICAL: handoff §25 EXECUTED/PASS plan/apply/verify on 2026-10-04.
# Package root: /etc/ouf/deploy-snapshots/semantic-deployment-package-20261004-072744
# Source-only snapshot; do not replay automatically.
(
set -euo pipefail
OUF_DEPLOYMENT_PKG_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_DEPLOYMENT_PKG_TMP"' EXIT

cat > "$OUF_DEPLOYMENT_PKG_TMP/sources.sha256" <<'OUF_DEPLOYMENT_SHA'
e2ee1c81de0cf9004538adc0393833453d826a9e1a2533fa9baba95aab50e8b0  scripts/stage_semantic_deployment_package.py
84f6b1fec995b9675284253321930efee0056e4546168058bae6a3667a2ff7d7  scripts/stage_semantic_admission_package.py
3fb04519de05131087a5bd12095b42f97026e7c5826d5f8f3845608404008f95  scripts/stage_semantic_preexec_package.py
c05c0216c0cec774f13ab27b193ab92599dd191314a157dc76b26ad978bc215c  scripts/semantic_provider_docker_runtime.py
a4ca047fc76dda6378e81834cac421d5d829b55d63ac62dde29a3178245aaabc  scripts/semantic_provider_preexec_hook.py
e8f6670029e6e3bf7a74e79dadd710b5a62bf31a23abd4c2785a71f36245a03c  scripts/semantic_provider_admission_preparer.py
98e3004300226fecd509a46c009585df14021927f20d4e5c82d8ff7a8a8180de  tools/materialize_southbound_kernel.py
1c0d7f1243752fe216ef62eefbc2e3253b8f2503b518fafe11277e4d7721a084  tools/materialize_southbound_lease_refresh.py
c466172113d1ffe850bf2c69762113b55fbc65d9091c96dca98a74548fddf930  tools/semantic_provider_dns.py
7a5f2b21c096228a3e4d298674e380f667c3004dd6d8ec19934a2302844c0f93  tools/semantic_provider_lease_nft.py
92736eebeccf344e565186bce94d29c65ffe1d50638d57eae81486e7b26e884d  tools/semantic_provider_lease_owner.py
b97f31cc17c22abbb7a021c274be73816f649196762f9c6dfcc54a58d8382e8a  tools/materialize_semantic_shared_faces.py
25c6df90d33e39fe83321df6ab9e5c38d4c33bcd290ad57c7a85c03b1bb8ba78  tools/semantic_provider_lease_coordination.py
1ade8d45a7387bd3b22464a34401ab6b4358f76e5c025ac84d80951542eb1fad  tools/semantic_provider_preexec.py
ef0b98c96879933480a26418edc2b971b21a116509ac87cbc39e3b2062e7a528  tools/semantic_provider_preexec_native.py
4bd0051fad23acd91fc42eb9b6cd2f2dac6e8d9d960fefd391add261a3646499  tools/semantic_provider_deployment_admission.py
87e4eed4485cee0736bb7031827ee773efde6f4fb97d6289c885fc5cf2049592  tools/semantic_provider_deployment_protocol.py
88b848be497607a71a9fc8def9164119d8bcf74d095d906fd56e6f91b7cb642a  tools/semantic_provider_deployment_consumption.py
OUF_DEPLOYMENT_SHA

while read -r OUF_DEPLOYMENT_HASH OUF_DEPLOYMENT_FILE; do
  mkdir -p -- "$OUF_DEPLOYMENT_PKG_TMP/$(dirname -- "$OUF_DEPLOYMENT_FILE")"
  curl --fail --silent --show-error --proto '=https' --max-time 30 \
    "https://raw.githubusercontent.com/GioNob/ouf-api-gateway/cc161b94c1af014403dabd113200d3180f02089d/$OUF_DEPLOYMENT_FILE" \
    -o "$OUF_DEPLOYMENT_PKG_TMP/$OUF_DEPLOYMENT_FILE"
done < "$OUF_DEPLOYMENT_PKG_TMP/sources.sha256"

(cd "$OUF_DEPLOYMENT_PKG_TMP"; sha256sum -c sources.sha256)

OUF_DEPLOYMENT_PKG_ROOT="/etc/ouf/deploy-snapshots/semantic-deployment-package-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_DEPLOYMENT_PKG_ROOT"
sudo install -d -m 0700 -o root -g root \
  "$OUF_DEPLOYMENT_PKG_ROOT/source/scripts" "$OUF_DEPLOYMENT_PKG_ROOT/source/tools"
while read -r OUF_DEPLOYMENT_HASH OUF_DEPLOYMENT_FILE; do
  sudo install -m 0600 -o root -g root \
    "$OUF_DEPLOYMENT_PKG_TMP/$OUF_DEPLOYMENT_FILE" "$OUF_DEPLOYMENT_PKG_ROOT/source/$OUF_DEPLOYMENT_FILE"
done < "$OUF_DEPLOYMENT_PKG_TMP/sources.sha256"
printf 'SEMANTIC_DEPLOYMENT_PACKAGE_ROOT=%s\n' "$OUF_DEPLOYMENT_PKG_ROOT"

for OUF_DEPLOYMENT_PKG_MODE in plan apply verify; do
  sudo /usr/bin/python3 -I -B \
    "$OUF_DEPLOYMENT_PKG_ROOT/source/scripts/stage_semantic_deployment_package.py" \
    --mode "$OUF_DEPLOYMENT_PKG_MODE" \
    --package-root "$OUF_DEPLOYMENT_PKG_ROOT" \
    --source-commit cc161b94c1af014403dabd113200d3180f02089d \
    --hook-source-sha256 a4ca047fc76dda6378e81834cac421d5d829b55d63ac62dde29a3178245aaabc
done
)
