#!/usr/bin/env bash
# Verify the exact fresh evidence on the VPS; no sudo, Docker or service changes.
set -euo pipefail
umask 077
ouf_stage=PRECHECK
trap 'printf "OUF_TARGET_FRESH_EVIDENCE=BLOCKED STAGE=%s\n" "$ouf_stage" >&2' ERR
ouf_gh=/home/oufadmin/ouf-gh-2.102.0.PNoFbF/gh_2.102.0_linux_amd64/bin/gh
ouf_original=/home/oufadmin/ouf-remediation-transfer-20261006-v2/ouf-remediation-20261006-v2.zip
test "$(id -un)" = oufadmin
test -x "$ouf_gh"
test -r "$ouf_original"
ouf_stage=GH_AUTH_REQUIRED
"$ouf_gh" auth status --hostname github.com >/dev/null 2>&1
ouf_stage=CREATE_PRIVATE_EVIDENCE_DIRECTORY
ouf_root=$(mktemp -d /home/oufadmin/ouf-extended-fresh-v2.XXXXXX)
printf 'OUF_FRESH_EVIDENCE_DIRECTORY=%s\n' "$ouf_root"
ouf_stage=DOWNLOAD_EXACT_ARTIFACT
"$ouf_gh" api --hostname github.com /repos/GioNob/ouf-semantic-registry/actions/artifacts/11478662099/zip > "$ouf_root/extended-v2.zip" 2> "$ouf_root/download.stderr"
printf '%s  %s\n' a23ee77e6f2e21fc9a7ca1beb144d11f22228cc801693cac5fad47ee30e863ea "$ouf_root/extended-v2.zip" | sha256sum -c -
ouf_stage=DOWNLOAD_PINNED_VERIFIER
curl --fail --silent --show-error --location --proto '=https' "https://raw.githubusercontent.com/GioNob/ouf-semantic-registry/4c34215c3d93add59dae916dcd87f2ce4ea1c991/tools/verify_semantic_extended_evidence.py" -o "$ouf_root/verify.py"
curl --fail --silent --show-error --location --proto '=https' "https://raw.githubusercontent.com/GioNob/ouf-semantic-registry/4c34215c3d93add59dae916dcd87f2ce4ea1c991/docs/handoffs/receipts/SEMANTIC_IMAGE_VULNERABILITY_DATABASE_PIN_2026-10-07.json" -o "$ouf_root/database-pin.json"
printf '%s  %s\n' 0d47208d99be6f55035a88d87057114e7a1cbce530b5aa130e5715af61795843 "$ouf_root/verify.py" | sha256sum -c -
printf '%s  %s\n' 5b1ac099536e6ac23e4445822f3c20e3289a7720a89e40573a7178cd7aefe272 "$ouf_root/database-pin.json" | sha256sum -c -
ouf_stage=VERIFY_REPORTS_AND_FIVE_SIGNATURES
/usr/bin/python3 -I -B "$ouf_root/verify.py" \
  --sidecar "$ouf_root/extended-v2.zip" \
  --sidecar-sha256 a23ee77e6f2e21fc9a7ca1beb144d11f22228cc801693cac5fad47ee30e863ea \
  --original-bundle "$ouf_original" \
  --source-merge-commit 00ba8b2ca6caf01902943b6d8d3dba60c00df6a9 \
  --require-generated-luajit --require-isolated-dossier \
  --database-pin "$ouf_root/database-pin.json" \
  --gh "$ouf_gh" --output "$ouf_root/reports" 2> "$ouf_root/verification.stderr"
printf 'OUF_TARGET_FRESH_EVIDENCE=PASS NO_RUNTIME_OPERATIONS=true\n'
