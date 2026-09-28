#!/usr/bin/env python3
"""Stage pinned R4a images in isolated worktrees; never replace live containers.

Run --plan first. --stage fetches the verified branch heads, builds three images,
and records their IDs alongside the existing container image IDs. It does not
change the checked-out branches, databases, routes, secrets, or running services.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


SPECS = (
    ("udp", "codex/r4a-governed-identity-engine", "d9626a91b3252b6bc0380f81e4f7a141bda4f3e7"),
    ("onboarding", "codex/r4a-udp-identity-activation-gate", "f74c3a9f377b5ce93b5cab298fa24372de1602bc"),
    ("ingestion", "codex/r4a-managed-csv-dialect", "e3f04f1d8ed47a62cde8b9c7831882c9cea17169"),
)


def output(args, timeout=60):
    return subprocess.check_output(args, text=True, stderr=subprocess.PIPE, timeout=timeout).strip()


def docker(*args, timeout=1800):
    return output(["sudo", "docker", *args], timeout=timeout)


def checked_repo(root, name, branch, sha):
    repo = root / name
    if not (repo / ".git").exists():
        raise RuntimeError(f"CHECKOUT_MISSING:{name}")
    if output(["git", "-C", str(repo), "status", "--porcelain"]):
        raise RuntimeError(f"CHECKOUT_DIRTY:{name}")
    remote = output(["git", "-C", str(repo), "ls-remote", "origin", "refs/heads/" + branch])
    if not remote or remote.split()[0] != sha:
        raise RuntimeError(f"REMOTE_HEAD_CHANGED:{name}")
    return repo


def stage_image(repo, stage_root, name, branch, sha):
    output(["git", "-C", str(repo), "fetch", "--no-tags", "origin", branch], timeout=180)
    if output(["git", "-C", str(repo), "rev-parse", "FETCH_HEAD"]) != sha:
        raise RuntimeError(f"FETCH_HEAD_CHANGED:{name}")
    worktree = stage_root / f"{name}-{sha[:12]}"
    if worktree.exists():
        if output(["git", "-C", str(worktree), "rev-parse", "HEAD"]) != sha:
            raise RuntimeError(f"STAGE_WORKTREE_CONFLICT:{name}")
        if output(["git", "-C", str(worktree), "status", "--porcelain"]):
            raise RuntimeError(f"STAGE_WORKTREE_DIRTY:{name}")
    else:
        output(["git", "-C", str(repo), "worktree", "add", "--detach", str(worktree), sha], timeout=180)
    tag = f"ouf-{name}:r4a-{sha[:12]}"
    try:
        revision = docker("image", "inspect", "--format",
                          "{{index .Config.Labels \"org.opencontainers.image.revision\"}}", tag)
    except subprocess.CalledProcessError:
        revision = None
    if revision == sha:
        print(f"R4A_IMAGE_REUSED={name}:{sha[:12]}", flush=True)
    else:
        print(f"R4A_IMAGE_BUILDING={name}:{sha[:12]}", flush=True)
        subprocess.run(["sudo", "docker", "build", "--label",
                        f"org.opencontainers.image.revision={sha}", "--tag", tag,
                        str(worktree)], check=True, timeout=1800)
    image_id = docker("image", "inspect", "--format", "{{.Id}}", tag)
    return {"commit": sha, "tag": tag, "image_id": image_id, "worktree": str(worktree)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--stage", action="store_true")
    parser.add_argument("--root", type=Path, default=Path("/opt/ouf"))
    args = parser.parse_args()
    if args.plan == args.stage:
        parser.error("choose exactly one of --plan or --stage")
    current = {}
    repos = {}
    for name, branch, sha in SPECS:
        repos[name] = checked_repo(args.root, name, branch, sha)
        current[name] = {
            "container": "ouf-" + name,
            "live_image_id": docker("inspect", "--type", "container", "--format", "{{.Image}}", "ouf-" + name),
            "target_commit": sha,
        }
    if args.plan:
        print(json.dumps({"result": "R4A_STAGE_PLAN_PASS", "live_unchanged": True,
                          "modules": current}, sort_keys=True))
        return
    stage_root = args.root / "r4a-stage"
    stage_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    staged = {}
    for name, branch, sha in SPECS:
        staged[name] = {**current[name], **stage_image(repos[name], stage_root, name, branch, sha)}
        print(f"R4A_IMAGE_STAGED={name}:{sha[:12]}", flush=True)
    manifest = stage_root / "identity-images.json"
    temporary = stage_root / ".identity-images.tmp"
    descriptor = os.open(temporary, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, "w") as handle:
        json.dump({"schema": "ouf.r4a.identity-images.v1", "live_unchanged": True,
                   "modules": staged}, handle, sort_keys=True, indent=2)
        handle.write("\n")
    temporary.replace(manifest)
    print(f"R4A_IMAGES_READY={manifest} LIVE_CONTAINERS_UNCHANGED=true")


if __name__ == "__main__":
    try:
        main()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired, RuntimeError) as error:
        detail = str(error)
        if isinstance(error, subprocess.CalledProcessError):
            detail = "COMMAND_FAILED:" + " ".join(error.cmd[:4])
        print("R4A_STAGE_BLOCKED=" + detail, file=sys.stderr)
        sys.exit(1)
