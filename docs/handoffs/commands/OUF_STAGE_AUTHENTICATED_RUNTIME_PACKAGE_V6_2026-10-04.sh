#!/usr/bin/env bash
# §28 NON ESEGUITO — source package v6, privato; nessun install/start/replay.
set -euo pipefail
OUF_AUTH_RUNTIME_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_AUTH_RUNTIME_TMP"' EXIT
cat > "$OUF_AUTH_RUNTIME_TMP/sources.sha256" <<'OUF_AUTH_RUNTIME_SHA'
21426170ce0746588c2ee478ade02312a78c70fa823642069266226765fbffc5  scripts/stage_semantic_authenticated_runtime_package.py
2be2d851db0ae5f5189c0b4c5aed27a74a7e91a58f080e5ef16d1a0bba181d9a  scripts/stage_semantic_authenticated_deployment_package.py
e2ee1c81de0cf9004538adc0393833453d826a9e1a2533fa9baba95aab50e8b0  scripts/stage_semantic_deployment_package.py
84f6b1fec995b9675284253321930efee0056e4546168058bae6a3667a2ff7d7  scripts/stage_semantic_admission_package.py
3fb04519de05131087a5bd12095b42f97026e7c5826d5f8f3845608404008f95  scripts/stage_semantic_preexec_package.py
4c504928a4a85d86d5e024d0216d8efb81b169f31b88c8b4205dfe00e98873a5  scripts/semantic_provider_docker_runtime.py
cff093f14bd0a6a04ecf8e32f67d02a05fc245806de75811e6b8c15070d3de8e  scripts/semantic_provider_preexec_hook.py
da1239843da3219ec393d3680c2c4a9480f6500487927d8fca38dbf8ae029b7a  scripts/semantic_provider_admission_preparer.py
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
f12a808ce5c45013311673e773531c5c99c3092e526678afe9b5ef04a2d59dbe  tools/semantic_provider_deployment_authentication.py
7182573aaaccf9dfea3ba47de52e75daa2f9c007ed6d83ddc7eaaa5bc3c38075  tools/semantic_provider_deployment_reauthorization.py
OUF_AUTH_RUNTIME_SHA
while read -r OUF_AUTH_RUNTIME_HASH OUF_AUTH_RUNTIME_FILE; do
  mkdir -p -- "$OUF_AUTH_RUNTIME_TMP/$(dirname -- "$OUF_AUTH_RUNTIME_FILE")"
  curl --fail --silent --show-error --proto '=https' --max-time 30 \
    "https://raw.githubusercontent.com/GioNob/ouf-api-gateway/f1996cca60e66f1807b88f126793a8edc1aed15f/$OUF_AUTH_RUNTIME_FILE" \
    -o "$OUF_AUTH_RUNTIME_TMP/$OUF_AUTH_RUNTIME_FILE"
done < "$OUF_AUTH_RUNTIME_TMP/sources.sha256"
(cd "$OUF_AUTH_RUNTIME_TMP"; sha256sum -c sources.sha256)
OUF_AUTH_RUNTIME_ROOT="/etc/ouf/deploy-snapshots/semantic-authenticated-runtime-package-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_AUTH_RUNTIME_ROOT"
sudo install -d -m 0700 -o root -g root "$OUF_AUTH_RUNTIME_ROOT/source/scripts" "$OUF_AUTH_RUNTIME_ROOT/source/tools"
while read -r OUF_AUTH_RUNTIME_HASH OUF_AUTH_RUNTIME_FILE; do
  sudo install -m 0600 -o root -g root \
    "$OUF_AUTH_RUNTIME_TMP/$OUF_AUTH_RUNTIME_FILE" "$OUF_AUTH_RUNTIME_ROOT/source/$OUF_AUTH_RUNTIME_FILE"
done < "$OUF_AUTH_RUNTIME_TMP/sources.sha256"
printf 'SEMANTIC_AUTHENTICATED_RUNTIME_PACKAGE_ROOT=%s\n' "$OUF_AUTH_RUNTIME_ROOT"
for OUF_AUTH_RUNTIME_MODE in plan apply verify; do
  sudo /usr/bin/python3 -I -B \
    "$OUF_AUTH_RUNTIME_ROOT/source/scripts/stage_semantic_authenticated_runtime_package.py" \
    --mode "$OUF_AUTH_RUNTIME_MODE" --package-root "$OUF_AUTH_RUNTIME_ROOT" \
    --source-commit f1996cca60e66f1807b88f126793a8edc1aed15f \
    --hook-source-sha256 cff093f14bd0a6a04ecf8e32f67d02a05fc245806de75811e6b8c15070d3de8e
done
