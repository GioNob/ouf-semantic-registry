#!/usr/bin/env python3
"""Offline, read-only source gate for a six-module OUF installation.

The lock records the exact source snapshot to install. It is not a deployment
manifest, secret store, or evidence that a running installation is healthy.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

SHA = re.compile(r"^[0-9a-f]{40}$")
EXPECTED = {
    "ouf-source-onboarding",
    "ouf-ingestion-runtime",
    "ouf-udp-object-resolution",
    "ouf-semantic-registry",
    "ouf-api-gateway",
    "ouf-mcp-server",
}


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], text=True, capture_output=True, check=True
    ).stdout.strip()


def check(root, lock):
    entries = lock.get("repositories")
    if not isinstance(entries, dict) or set(entries) != EXPECTED:
        raise ValueError("lock must list exactly the six OUF repositories")
    issues = []
    for name in sorted(EXPECTED):
        ref = entries[name]
        if not isinstance(ref, str) or not SHA.fullmatch(ref):
            raise ValueError(f"{name}: expected a full 40-character commit SHA")
        repo = root / name
        if not repo.is_dir():
            issues.append(f"{name}: checkout missing")
            continue
        if not (repo / ".git").exists():
            issues.append(f"{name}: not a usable Git checkout")
            continue
        try:
            actual = git(repo, "rev-parse", "HEAD")
            origin = git(repo, "remote", "get-url", "origin")
            dirty = git(repo, "status", "--porcelain")
        except subprocess.CalledProcessError:
            issues.append(f"{name}: not a usable Git checkout")
            continue
        if not (origin == f"https://github.com/GioNob/{name}.git" or
                origin == f"git@github.com:GioNob/{name}.git"):
            issues.append(f"{name}: unrecognized Git origin")
        if actual != ref:
            issues.append(f"{name}: HEAD {actual} differs from lock {ref}")
        if dirty:
            issues.append(f"{name}: uncommitted files")
        if not (repo / "README.md").is_file():
            issues.append(f"{name}: README missing")
        print(f"{name}: {actual[:12]} checked")
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="directory containing six sibling checkouts")
    parser.add_argument("--lock", type=Path, required=True, help="reviewed exact-commit lock JSON")
    args = parser.parse_args()
    try:
        issues = check(args.root.resolve(), json.loads(args.lock.read_text(encoding="utf-8")))
    except (ValueError, OSError) as error:
        print(f"INSTALLATION_PREFLIGHT_INVALID: {error}", file=sys.stderr)
        return 2
    for issue in issues:
        print(f"BLOCKED: {issue}", file=sys.stderr)
    if issues:
        return 1
    print("SOURCE_PREFLIGHT_PASS (source only; no services installed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
