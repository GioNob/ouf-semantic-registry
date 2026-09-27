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
    command = ["docker", "inspect", "--type", "container", *names]
    # A missing optional name makes Docker exit non-zero, so inspect each one.
    entries = []
    for name in names:
        proc = subprocess.run(
            ["docker", "inspect", "--type", "container", name],
            capture_output=True, text=True, check=False,
        )
        if proc.returncode:
            entries.append({"name": name, "present": False})
            continue
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
    except (OSError, RuntimeError) as exc:
        print(f"R4A_INVENTORY_BLOCKED={type(exc).__name__}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
