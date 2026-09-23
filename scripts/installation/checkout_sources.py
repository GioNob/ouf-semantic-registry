#!/usr/bin/env python3
"""Plan or materialize six clean OUF checkouts from an approved source lock.

This prepares source code only. It does not build images, install services, or
certify that the example lock represents a compatible release.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from source_preflight import EXPECTED, SHA, check, git


def validate(lock):
    entries = lock.get("repositories")
    if not isinstance(entries, dict) or set(entries) != EXPECTED:
        raise ValueError("lock must list exactly the six OUF repositories")
    for name, sha in entries.items():
        if not isinstance(sha, str) or not SHA.fullmatch(sha):
            raise ValueError(f"{name}: expected a full 40-character commit SHA")
    return entries


def inspect_existing(root, entries):
    missing = []
    for name in sorted(EXPECTED):
        target = root / name
        if not target.exists():
            missing.append(name)
            continue
        if not target.is_dir():
            raise ValueError(f"{name}: target exists and is not a directory")
        if not (target / ".git").exists():
            raise ValueError(f"{name}: existing checkout is not usable")
        try:
            sha = git(target, "rev-parse", "HEAD")
            origin = git(target, "remote", "get-url", "origin")
            dirty = git(target, "status", "--porcelain")
        except subprocess.CalledProcessError as error:
            raise ValueError(f"{name}: existing checkout is not usable") from error
        if sha != entries[name] or origin != f"https://github.com/GioNob/{name}.git" or dirty:
            raise ValueError(f"{name}: existing checkout differs from the lock, origin, or clean state")
    return missing


def checkout(root, name, sha):
    origin = f"https://github.com/GioNob/{name}.git"
    target = root / name
    staging = Path(tempfile.mkdtemp(prefix=f".{name}-", dir=root))
    try:
        # Clone into a directory created by us, then publish only after exact
        # commit verification. Never remove or replace an operator checkout.
        staging.rmdir()
        subprocess.run(["git", "clone", "--no-checkout", origin, str(staging)], check=True)
        git(staging, "cat-file", "-e", f"{sha}^{{commit}}")
        subprocess.run(["git", "-C", str(staging), "checkout", "--detach", sha], check=True)
        if git(staging, "rev-parse", "HEAD") != sha:
            raise RuntimeError(f"{name}: checkout mismatch")
        if target.exists():
            raise ValueError(f"{name}: target appeared during checkout; refusing overwrite")
        os.rename(staging, target)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="parent of the six sibling checkouts")
    parser.add_argument("--lock", type=Path, required=True, help="reviewed exact-commit lock JSON")
    parser.add_argument("--apply", action="store_true", help="clone missing repositories; default is offline plan")
    args = parser.parse_args()
    try:
        entries = validate(json.loads(args.lock.read_text(encoding="utf-8")))
        root = args.root.resolve()
        if root.exists() and not root.is_dir():
            raise ValueError("root is not a directory")
        missing = inspect_existing(root, entries) if root.exists() else sorted(EXPECTED)
        for name in missing:
            print(f"{'CLONE' if args.apply else 'PLAN'} {name}@{entries[name]}")
        if not args.apply:
            print("SOURCE_CHECKOUT_PLAN_ONLY (no network or writes)")
            return 0
        root.mkdir(parents=True, exist_ok=True)
        for name in missing:
            checkout(root, name, entries[name])
        issues = check(root, {"repositories": entries})
        if issues:
            for issue in issues:
                print(f"BLOCKED: {issue}", file=sys.stderr)
            return 1
        print("SIX_SOURCE_CHECKOUTS_PASS (sources only; no services installed)")
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError, RuntimeError) as error:
        print(f"SOURCE_CHECKOUT_BLOCKED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
