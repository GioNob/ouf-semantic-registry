#!/usr/bin/env python3
"""Build the pinned opt-in UDP diagnostic image; leave live services unchanged."""

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path("/opt/ouf")
REPO = ROOT / "udp"
STAGE = ROOT / "r4a-stage"
BRANCH = "codex/r4a-live-schema-integration"
PREVIOUS = "edaba2bff18a2aaf52d1180f21f0e68984cc3437"
TARGET = "fb31d7f851a79f16405a2fd4a14995014217ff37"
ALLOWED = {
    "Dockerfile",
    "src/main/java/it/comune/trieste/ouf/udp/UdpAuthorizationDiagnosticApi.java",
    "src/test/java/it/comune/trieste/ouf/udp/UdpAuthorizationDiagnosticApiTest.java",
}


def output(args, timeout=60):
    return subprocess.check_output(args, text=True, stderr=subprocess.PIPE,
                                   timeout=timeout).strip()


def docker(*args):
    return output(["docker", *args])


def main():
    if os.geteuid() != 0 or not REPO.is_dir() or not STAGE.is_dir():
        raise RuntimeError("ROOT_AND_EXISTING_STAGE_REQUIRED")
    git = ["git", "-c", "safe.directory=" + str(REPO), "-C", str(REPO)]
    remote = output([*git, "ls-remote", "origin", "refs/heads/" + BRANCH], 120)
    if not remote or remote.split()[0] != TARGET:
        raise RuntimeError("PINNED_REMOTE_HEAD_CHANGED")
    output([*git, "fetch", "--no-tags", "origin", BRANCH], 180)
    if output([*git, "rev-parse", "FETCH_HEAD"]) != TARGET:
        raise RuntimeError("FETCH_HEAD_MISMATCH")
    changed = set(output([*git, "diff", "--name-only", PREVIOUS, TARGET]).splitlines())
    if changed != ALLOWED:
        raise RuntimeError("UNEXPECTED_DIFF_PATHS")
    live_before = docker("inspect", "--type", "container", "--format", "{{.Image}}", "ouf-udp")
    live = json.loads(docker("inspect", "--type", "container", "ouf-udp"))[0]
    if not live["State"]["Running"]:
        raise RuntimeError("LIVE_STATE_CHANGED")
    worktree = STAGE / ("udp-" + TARGET[:12])
    if worktree.exists():
        if (output(["git", "-C", str(worktree), "rev-parse", "HEAD"]) != TARGET
            or output(["git", "-C", str(worktree), "status", "--porcelain"])):
            raise RuntimeError("STAGE_WORKTREE_CONFLICT")
    else:
        output([*git, "worktree", "add", "--detach", str(worktree), TARGET], 180)
    tag = "ouf-udp:r4a-authdiag-" + TARGET[:12]
    try:
        image = docker("image", "inspect", "--format", "{{.Id}}", tag)
        revision = docker("image", "inspect", "--format",
                          '{{index .Config.Labels "org.opencontainers.image.revision"}}', tag)
        if revision != TARGET:
            raise RuntimeError("STAGED_TAG_REVISION_MISMATCH")
        print("R4A_AUTH_DIAG_IMAGE_REUSED=true", flush=True)
    except subprocess.CalledProcessError:
        log = STAGE / ("udp-authdiag-build-" + TARGET[:12] + ".log")
        fd = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as stream:
            print("R4A_AUTH_DIAG_BUILD_STARTED=true TEST_REQUIRED=true", flush=True)
            result = subprocess.run(["docker", "build", "--label",
                "org.opencontainers.image.revision=" + TARGET, "--tag", tag,
                str(worktree)], stdout=stream, stderr=subprocess.STDOUT, timeout=1800)
        if result.returncode:
            print("R4A_AUTH_DIAG_BUILD_FAILED=true LOG=" + str(log), flush=True)
            raise RuntimeError("DOCKER_BUILD_OR_REGRESSION_TEST_FAILED")
        image = docker("image", "inspect", "--format", "{{.Id}}", tag)
    if docker("inspect", "--type", "container", "--format", "{{.Image}}", "ouf-udp") != live_before:
        raise RuntimeError("LIVE_IMAGE_CHANGED_DURING_BUILD")
    manifest = STAGE / "udp-auth-diagnostic-image.json"
    temp = STAGE / ".udp-auth-diagnostic-image.tmp"
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump({"commit": TARGET, "image_id": image, "tag": tag,
                   "previous_commit": PREVIOUS, "previous_live_image_id": live_before}, stream)
        stream.write("\n")
    temp.replace(manifest)
    print("R4A_AUTH_DIAG_STAGE=PASS COMMIT=" + TARGET +
          " DIFF_PATHS=3 TEST_IN_IMAGE_BUILD=true", flush=True)
    print("R4A_AUTH_DIAG_MANIFEST=" + str(manifest) +
          " LIVE_CONTAINER_UNCHANGED=true DB_UNCHANGED=true", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, IndexError, subprocess.SubprocessError,
            RuntimeError) as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_AUTH_DIAG_STAGE_BLOCKED=" + code +
              " LIVE_UNCHANGED=true", file=sys.stderr)
        raise SystemExit(1)
