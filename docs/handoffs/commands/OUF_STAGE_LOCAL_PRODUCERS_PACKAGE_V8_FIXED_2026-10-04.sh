#!/usr/bin/env bash
# STATO: NON ESEGUITO. Variante corretta per future installazioni; non usare per il root bloccato 121542.
# Staging privato v8; nessun producer eseguito, chiave, authority o start.
(
set -euo pipefail
OUF_PRODUCERS_TMP=$(mktemp -d)
trap 'rm -rf -- "$OUF_PRODUCERS_TMP"' EXIT
cat > "$OUF_PRODUCERS_TMP/sources.sha256" <<'OUF_PRODUCERS_SHA'
d4fcef01343bb05097fa7c1b5913893e37ec0023ed5254b347936c8208daa1f3  scripts/stage_semantic_local_producers_package.py
693f4db5f5ae08edecc6d735b0f1bccb16c79104d5a909598275ec97fe6d1e0f  scripts/semantic_provider_deployment_broker.py
4c504928a4a85d86d5e024d0216d8efb81b169f31b88c8b4205dfe00e98873a5  scripts/semantic_provider_docker_runtime.py
da1239843da3219ec393d3680c2c4a9480f6500487927d8fca38dbf8ae029b7a  scripts/semantic_provider_admission_preparer.py
cff093f14bd0a6a04ecf8e32f67d02a05fc245806de75811e6b8c15070d3de8e  scripts/semantic_provider_preexec_hook.py
54617ac45551091bc0e78417f7c63aaf38671b371c14e79367d8addc3f452b90  scripts/semantic_provider_installer_approval.py
8b16d47aa0f957c586e38022a5a2e9c8f31f7831860a24d88ae32a209869f70c  scripts/semantic_provider_node_attestor.py
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
97a55866d436d973e17b84b5f6176ba17db3d6019c4fe68c0db7a398f8a2b66f  tools/semantic_provider_deployment_signing.py
5deffad3ed663c3e7d1a7f09e802935555035f4e585ca771e23049a7d916ab71  tools/semantic_provider_installer_approval.py
6c46ca7c585b72efde69a58dd50cbe23ef9c550993dba69b44f6f595158aa11a  tools/semantic_provider_node_observation.py
b0b05723a1c384fcfa97f29edddfd1afce22baa1fbe760190aa77af76cde2b14  tools/semantic_provider_node_attestor.py
OUF_PRODUCERS_SHA

printf '%s  %s\n' 'a1b11fbfb9d701101f2efa1048c7f99a54f123ed1f1b71f480ffcd883c0e560b' "$OUF_PRODUCERS_TMP/sources.sha256" | sha256sum -c -
while read -r OUF_PRODUCERS_HASH OUF_PRODUCERS_FILE; do
  mkdir -p -- "$OUF_PRODUCERS_TMP/$(dirname -- "$OUF_PRODUCERS_FILE")"
  curl --fail --silent --show-error --proto '=https' --max-time 30 \
    "https://raw.githubusercontent.com/GioNob/ouf-api-gateway/7ded9df0c74c6db919c7a68d4c75ab2c132dea53/$OUF_PRODUCERS_FILE" \
    -o "$OUF_PRODUCERS_TMP/$OUF_PRODUCERS_FILE"
done < "$OUF_PRODUCERS_TMP/sources.sha256"
(cd "$OUF_PRODUCERS_TMP"; sha256sum -c sources.sha256)

OUF_PRODUCERS_ROOT="/etc/ouf/deploy-snapshots/semantic-local-producers-package-$(date -u +%Y%m%d-%H%M%S)"
sudo mkdir -m 0700 -- "$OUF_PRODUCERS_ROOT"
sudo install -d -m 0700 -o root -g root \
  "$OUF_PRODUCERS_ROOT" "$OUF_PRODUCERS_ROOT/source" \
  "$OUF_PRODUCERS_ROOT/source/scripts" "$OUF_PRODUCERS_ROOT/source/tools"
sudo install -m 0600 -o root -g root "$OUF_PRODUCERS_TMP/sources.sha256" "$OUF_PRODUCERS_ROOT/sources.sha256"
while read -r OUF_PRODUCERS_HASH OUF_PRODUCERS_FILE; do
  sudo install -m 0600 -o root -g root \
    "$OUF_PRODUCERS_TMP/$OUF_PRODUCERS_FILE" "$OUF_PRODUCERS_ROOT/source/$OUF_PRODUCERS_FILE"
done < "$OUF_PRODUCERS_TMP/sources.sha256"
printf 'SEMANTIC_LOCAL_PRODUCERS_PACKAGE_ROOT=%s\n' "$OUF_PRODUCERS_ROOT"
for OUF_PRODUCERS_MODE in plan apply verify; do
  sudo /usr/bin/python3 -I -B \
    "$OUF_PRODUCERS_ROOT/source/scripts/stage_semantic_local_producers_package.py" \
    --mode "$OUF_PRODUCERS_MODE" --package-root "$OUF_PRODUCERS_ROOT" \
    --source-commit 7ded9df0c74c6db919c7a68d4c75ab2c132dea53 \
    --source-manifest-sha256 a1b11fbfb9d701101f2efa1048c7f99a54f123ed1f1b71f480ffcd883c0e560b
done
)

