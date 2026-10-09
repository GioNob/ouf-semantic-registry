#!/usr/bin/env python3
"""Read-only R4a Docker runtime inventory; prints no environment or mount values.

This is an inventory, not a release gate. It never executes inside a container
or contacts a service. Use the PET handoff to interpret deployment evidence.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

DEFAULT_CONTAINERS = (
    "ouf-apisix", "ouf-onboarding", "ouf-mcp", "ouf-semantic",
    "ouf-ingestion", "ouf-udp", "ouf-minio",
)


def snapshot(names: tuple[str, ...]) -> dict:
    listing = subprocess.run(
        ["docker", "container", "ls", "-a", "--format", "{{.Names}}"],
        capture_output=True, text=True, check=False, timeout=10,
    )
    if listing.returncode:
        raise RuntimeError("docker container listing failed")
    present = set(listing.stdout.splitlines())
    entries = []
    for name in names:
        if name not in present:
            entries.append({"name": name, "present": False})
            continue
        proc = subprocess.run(
            ["docker", "inspect", "--type", "container", name],
            capture_output=True, text=True, check=False, timeout=10,
        )
        if proc.returncode:
            raise RuntimeError(f"docker inspect failed for {name}")
        try:
            item = json.loads(proc.stdout)[0]
            config = item["Config"]
            state = item["State"]
            host = item["HostConfig"]
            entry = {
                "name": name,
                "present": True,
                "running": bool(state["Running"]),
                "status": state["Status"],
                "image_id": item["Image"],
                "revision": (config.get("Labels") or {}).get(
                    "org.opencontainers.image.revision"),
                "restart": (host.get("RestartPolicy") or {}).get("Name"),
                "networks": sorted((item["NetworkSettings"].get("Networks") or {}).keys()),
            }
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"invalid docker inspect response for {name}") from exc
        entries.append(entry)
    return {
        "schema": "ouf.r4a.runtime-inventory.v1",
        "read_only": True,
        "no_secret_values": True,
        "not_release_acceptance": True,
        "containers": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--containers", nargs="+", default=DEFAULT_CONTAINERS,
                        help="Container names to inspect (defaults to OUF lab names)")
    args = parser.parse_args()
    try:
        result = snapshot(tuple(args.containers))
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"R4A_INVENTORY_BLOCKED={type(exc).__name__}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
