#!/usr/bin/env bash
set -euo pipefail
mode="${1:-}"
valid_image='^[A-Za-z0-9._/:@-]+$'
valid_fixture='^[A-Za-z0-9._-]+$'
validate() {
  [[ "${PEER_IMAGE:-}" =~ $valid_image ]] || { echo 'invalid peer_image' >&2; exit 64; }
  [[ "${FIXTURE_SET:-}" =~ $valid_fixture ]] || { echo 'invalid fixture_set' >&2; exit 64; }
  [[ -d "pairwise/fixtures/$FIXTURE_SET" ]] || { echo 'unknown fixture_set' >&2; exit 66; }
}
case "$mode" in
  validate-inputs) validate ;;
  execute)
    validate
    mkdir -p pairwise/evidence
    echo 'Pairwise execution is enabled only after a versioned fixture set and its peer adapter are committed.' >&2
    exit 78
    ;;
  *) echo 'usage: run-pairwise.sh validate-inputs|execute' >&2; exit 64 ;;
esac

