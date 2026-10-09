#!/usr/bin/env bash
# §29 ESEGUITO/PASS 2026-10-04 — comando storico; non ripetere.
# Root: /etc/ouf/deploy-snapshots/semantic-local-broker-package-20261004-110947
# Hash del wrapper eseguito: 430694376a5b745a35ad2efaf46c2ceede5df9542f62edceacf95c1d47680072
# Solo sorgenti private; nessun install/start/replay.
set -euo pipefail
OUF_BROKER_PKG_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_BROKER_PKG_TMP"' EXIT
cat > "$OUF_BROKER_PKG_TMP/sources.sha256" <<'OUF_BROKER_PKG_SHA'
725f747db3c91a32a6000ca1f4d3e4913c7e664fa0aadf1828203749be37439d  scripts/stage_semantic_local_broker_package.py
693f4db5f5ae08edecc6d735b0f1bccb16c79104d5a909598275ec97fe6d1e0f  scripts/semantic_provider_deployment_broker.py
4c504928a4a85d86d5e024d0216d8efb81b169f31b88c8b4205dfe00e98873a5  scripts/semantic_provider_docker_runtime.py
da1239843da3219ec393d3680c2c4a9480f6500487927d8fca38dbf8ae029b7a  scripts/semantic_provider_admission_preparer.py
cff093f14bd0a6a04ecf8e32f67d02a05fc245806de75811e6b8c15070d3de8e  scripts/semantic_provider_preexec_hook.py
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
87bb4cdaf6686aadbde69caddf1d1813ecc02664aeeef62b67dd80750adc15b1  tools/semantic_provider_deployment_protocol.py
053e2e5031cd51adf957388296a808cd8ba824dbc2ab671143e756312d050aef  tools/semantic_provider_deployment_consumption.py
3f89e466638cdbb8311b661b64739c1903969758cb3bcf569d53cbdaa620386a  tools/semantic_provider_deployment_authentication.py
7182573aaaccf9dfea3ba47de52e75daa2f9c007ed6d83ddc7eaaa5bc3c38075  tools/semantic_provider_deployment_reauthorization.py
04ed5dd2e9da9cb181b0808408b57ee4df740e209a0f8c1f8902cd9028c49f6c  tools/semantic_provider_deployment_producer.py
OUF_BROKER_PKG_SHA
printf '%s  %s\n' e258b94090319124cbdf9520fa5b179e772836f3d6477e3824809741e08a5035 "$OUF_BROKER_PKG_TMP/sources.sha256" | sha256sum -c -
while read -r OUF_BROKER_PKG_HASH OUF_BROKER_PKG_FILE; do
  mkdir -p -- "$OUF_BROKER_PKG_TMP/$(dirname -- "$OUF_BROKER_PKG_FILE")"
  curl --fail --silent --show-error --proto '=https' --max-time 30 \
    "https://raw.githubusercontent.com/GioNob/ouf-api-gateway/04d775e892cd42e42d34de02959b9c7ba6483f3b/$OUF_BROKER_PKG_FILE" \
    -o "$OUF_BROKER_PKG_TMP/$OUF_BROKER_PKG_FILE"
done < "$OUF_BROKER_PKG_TMP/sources.sha256"
(cd "$OUF_BROKER_PKG_TMP"; sha256sum -c sources.sha256)
OUF_BROKER_PKG_ROOT="/etc/ouf/deploy-snapshots/semantic-local-broker-package-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_BROKER_PKG_ROOT"
sudo install -d -m 0700 -o root -g root \
  "$OUF_BROKER_PKG_ROOT/source" "$OUF_BROKER_PKG_ROOT/source/scripts" "$OUF_BROKER_PKG_ROOT/source/tools"
sudo install -m 0600 -o root -g root "$OUF_BROKER_PKG_TMP/sources.sha256" "$OUF_BROKER_PKG_ROOT/sources.sha256"
while read -r OUF_BROKER_PKG_HASH OUF_BROKER_PKG_FILE; do
  sudo install -m 0600 -o root -g root \
    "$OUF_BROKER_PKG_TMP/$OUF_BROKER_PKG_FILE" "$OUF_BROKER_PKG_ROOT/source/$OUF_BROKER_PKG_FILE"
done < "$OUF_BROKER_PKG_TMP/sources.sha256"
printf 'SEMANTIC_LOCAL_BROKER_PACKAGE_ROOT=%s\n' "$OUF_BROKER_PKG_ROOT"
for OUF_BROKER_PKG_MODE in plan apply verify; do
  sudo /usr/bin/python3 -I -B \
    "$OUF_BROKER_PKG_ROOT/source/scripts/stage_semantic_local_broker_package.py" \
    --mode "$OUF_BROKER_PKG_MODE" --package-root "$OUF_BROKER_PKG_ROOT" \
    --source-commit 04d775e892cd42e42d34de02959b9c7ba6483f3b \
    --source-manifest-sha256 e258b94090319124cbdf9520fa5b179e772836f3d6477e3824809741e08a5035
done
