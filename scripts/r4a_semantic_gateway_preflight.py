#!/usr/bin/env python3
"""Read-only APISIX inventory for the first governed Semantic publication.

Run on the VPS as root. The Admin key is read in the APISIX network namespace;
neither the key nor route plugin configuration is printed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.request import Request, urlopen

EXPECTED = (
    ("POST", "/api/semantic/v1/artifacts", "ouf.semantic.propose"),
    ("POST", "/api/semantic/v1/revisions/*:validate", "ouf.semantic.review.prepare"),
    ("POST", "/api/semantic/v1/approval-challenges", "ouf.semantic.approval.request"),
    ("GET", "/api/trusted-human/v1/semantic-approval-challenges/*", "ouf.semantic.review"),
    ("POST", "/api/trusted-human/v1/semantic-approval-challenges/*/decision", "ouf.semantic.approve"),
    ("POST", "/api/trusted-human/v1/semantic-approval-challenges/*/publish", "ouf.semantic.publish"),
    ("GET", "/api/semantic/v1/search", "ouf.semantic.search"),
    ("GET", "/api/semantic/v1/artifacts/*", "ouf.semantic.read"),
)


def matches(pattern: str, path: str) -> bool:
    if not pattern.startswith("/"):
        return False
    # APISIX wildcard matching covers a prefix, including nested paths.
    return bool(re.fullmatch(re.escape(pattern).replace(r"\*", ".*"), path))


def route_rows(doc: object) -> list[dict]:
    if not isinstance(doc, dict) or not isinstance(doc.get("list"), list):
        raise ValueError("ADMIN_ROUTE_LIST_INVALID")
    if doc.get("total") is not None and doc["total"] > len(doc["list"]):
        raise ValueError("ADMIN_ROUTE_LIST_TRUNCATED")
    rows = []
    for item in doc["list"]:
        if not isinstance(item, dict):
            raise ValueError("ADMIN_ROUTE_ITEM_INVALID")
        route = item.get("value", item)
        if not isinstance(route, dict):
            raise ValueError("ADMIN_ROUTE_VALUE_INVALID")
        row = dict(route)
        row.setdefault("id", str(item.get("key", "")).rsplit("/", 1)[-1])
        rows.append(row)
    return rows


def coverage(routes: list[dict]) -> list[tuple[str, str, str, list[str]]]:
    result = []
    for method, path, scope in EXPECTED:
        ids = []
        for route in routes:
            methods = route.get("methods") or []
            patterns = [route.get("uri"), *(route.get("uris") or [])]
            if route.get("status", 1) == 0 or (methods and method not in methods):
                continue
            if any(isinstance(p, str) and matches(p, path.replace("*", "probe")) for p in patterns):
                ids.append(str(route.get("id", "UNKNOWN")))
        result.append((method, path, scope, sorted(ids)))
    return result


def inner(key_file: Path) -> None:
    key = key_file.read_text().strip()
    if not key or "\n" in key or "\r" in key:
        raise ValueError("ADMIN_KEY_INVALID")
    req = Request("http://127.0.0.1:9180/apisix/admin/routes",
                  headers={"X-API-KEY": key})
    with urlopen(req, timeout=10) as response:
        rows = route_rows(json.load(response))
    print("SEMANTIC_GATEWAY_ROUTE_COUNT=" + str(len(rows)))
    for method, path, scope, ids in coverage(rows):
        print("ROUTE=" + method + " " + path + " SCOPE=" + scope
              + " MATCHING_IDS=" + (",".join(ids) if ids else "NONE"))
    print("NO_WRITES=true SECRET_VALUES_NOT_PRINTED=true")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--container", default="ouf-apisix")
    parser.add_argument("--admin-key", type=Path,
                        default=Path("/opt/ouf/secrets/apisix-admin-key"))
    parser.add_argument("--inside", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.inside:
        inner(args.admin_key)
        return
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", args.container):
        raise ValueError("CONTAINER_NAME_INVALID")
    pid = subprocess.check_output(
        ["docker", "inspect", "--format", "{{.State.Pid}}", args.container], text=True).strip()
    if not pid.isdecimal() or int(pid) <= 1:
        raise ValueError("APISIX_CONTAINER_NOT_RUNNING")
    subprocess.run(["nsenter", "-t", pid, "-n", sys.executable,
                    str(Path(__file__).resolve()), "--inside", "--admin-key", str(args.admin_key)],
                   check=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print("SEMANTIC_GATEWAY_PREFLIGHT_BLOCKED=" + type(exc).__name__, file=sys.stderr)
        raise SystemExit(1)
