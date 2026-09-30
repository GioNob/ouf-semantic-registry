#!/usr/bin/env python3
"""Prepare the proven Ingestion image without starting it or changing live files."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import r4a_prepare_frozen_compatibility_probe as probe

REVISION = "0dfab1e7b2253fd939088259ea61754d6e56706c"
NAME = "ouf-ingestion-r4a-compatibility-candidate"
ROOT = Path("/etc/ouf/deploy-snapshots")
STATE = ROOT / "ingestion-compatibility-release.json"
PROOF = Path("/opt/ouf/r4a-stage/ingestion-compatibility-probe.json")


def stable(doc):
    return {k: doc[k] for k in ("Id", "Image", "Config", "HostConfig", "Mounts")}


def mounts(doc, replacement=None):
    return sorted((m["Type"], str(replacement) if replacement is not None
                   and m["Destination"] == probe.PROPERTIES else m["Source"],
                   m["Destination"], m["RW"]) for m in doc["Mounts"])


def environment(doc):
    values = doc["Config"].get("Env") or []
    if any("=" not in v or "\n" in v or "\r" in v for v in values):
        raise RuntimeError("ING_ENV_FORMAT_UNSUPPORTED")
    result = dict(v.split("=", 1) for v in values)
    if len(result) != len(values):
        raise RuntimeError("ING_ENV_DUPLICATED")
    return result


def memory_flags(host):
    memory, swap = host.get("Memory", 0), host.get("MemorySwap", 0)
    if (type(memory) is not int or type(swap) is not int or memory < 0 or swap < -1
            or (memory == 0 and swap != 0) or (swap > 0 and swap < memory)):
        raise RuntimeError("ING_MEMORY_SETTINGS_UNSUPPORTED")
    flags = ["--memory", str(memory)] if memory else []
    if swap:
        flags.extend(["--memory-swap", str(swap)])
    return flags


def validate_binds(live):
    resolved = mounts(live)
    if any(m.get("Propagation", "rprivate") != "rprivate" for m in live["Mounts"]):
        raise RuntimeError("ING_MOUNT_PROPAGATION_UNSUPPORTED")
    binds = live["HostConfig"].get("Binds") or []
    parsed = []
    for value in binds:
        parts = value.rsplit(":", 2)
        if (len(parts) != 3 or not parts[0].startswith("/") or not parts[1].startswith("/")
                or set(parts[2].split(",")) not in ({"ro"}, {"ro", "rprivate"})):
            raise RuntimeError("ING_BIND_FORMAT_UNSUPPORTED")
        parsed.append(("bind", parts[0], parts[1], False))
    if len(parsed) != len(set(parsed)) or any(m not in resolved for m in parsed):
        raise RuntimeError("ING_BINDS_RESOLVED_MOUNT_MISMATCH")


def guard(live, image):
    probe.probe_mounts(live)
    host, config = live["HostConfig"], live["Config"]
    unsupported = ("PortBindings", "VolumesFrom", "Privileged", "ReadonlyRootfs",
        "ExtraHosts", "Dns", "DnsSearch", "CapAdd", "SecurityOpt", "Devices", "Tmpfs",
        "AutoRemove", "GroupAdd", "UsernsMode", "Init", "Ulimits", "CapDrop", "MemoryReservation",
        "NanoCpus", "CpuShares", "PidsLimit", "OomKillDisable", "CpusetCpus",
        "CpusetMems", "PidMode", "Sysctls")
    if (any(host.get(k) for k in unsupported) or config.get("Healthcheck")
            or host.get("RestartPolicy", {}).get("Name") != "unless-stopped"
            or host.get("LogConfig", {}).get("Type") != "json-file"
            or any(t != "bind" or rw or any(c in source + target for c in ",\n\r")
                   for t, source, target, rw in mounts(live))):
        raise RuntimeError("ING_RUNTIME_SETTINGS_UNSUPPORTED")
    validate_binds(live)
    memory_flags(host)
    for key in ("User", "Entrypoint", "Cmd", "WorkingDir", "ExposedPorts"):
        if config.get(key) != image["Config"].get(key):
            raise RuntimeError("ING_IMAGE_LAUNCH_CONTRACT_CHANGED")
    env = environment(live)
    # Refuse conflicting activation settings; the observed baseline has none.
    if any(k.upper().startswith("OUF_INGESTION_ACTIVATION") for k in env):
        raise RuntimeError("ING_ACTIVATION_ENV_ALREADY_PRESENT")


def optional(name=NAME):
    names = probe.run(["docker", "container", "ls", "--all", "--format", "{{.Names}}"])
    return probe.inspect(name) if name in names.splitlines() else None


def private(path, mode):
    metadata = path.lstat()
    if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != 0
            or stat.S_IMODE(metadata.st_mode) != mode):
        raise RuntimeError("ING_PRIVATE_FILE_UNSAFE")


def matches(candidate, old, image, properties):
    return (candidate["Image"] == image["Id"]
        and candidate["State"]["Status"] == "created" and not candidate["State"]["Running"]
        and environment(candidate) == environment(old)
        and mounts(candidate) == mounts(old, properties)
        and candidate["HostConfig"].get("NetworkMode") == "ouf-backend"
        and set(candidate["NetworkSettings"]["Networks"]) == {"ouf-backend"}
        and "ouf-ingestion" in candidate["NetworkSettings"]["Networks"]["ouf-backend"].get("Aliases", [])
        and candidate["HostConfig"].get("RestartPolicy", {}).get("Name") == "no"
        and candidate["HostConfig"].get("LogConfig") == old["HostConfig"].get("LogConfig")
        and all(candidate["HostConfig"].get(k, 0) == old["HostConfig"].get(k, 0)
                for k in ("Memory", "MemorySwap"))
        and all(candidate["Config"].get(k) == old["Config"].get(k)
                for k in ("User", "Entrypoint", "Cmd", "WorkingDir", "ExposedPorts")))


def main(args):
    if os.geteuid() != 0:
        raise RuntimeError("ROOT_REQUIRED")
    os.umask(0o077)
    meta = ROOT.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o700:
        raise RuntimeError("ING_STAGE_DIRECTORY_UNSAFE")
    old = probe.inspect("ouf-ingestion")
    proof = json.loads(PROOF.read_text())
    row = probe.candidate_row(args.source, args.version, args.expected_hash)
    probe.validate_proof(proof, row)
    if (proof.get("candidateCommit") != REVISION or proof.get("validatedRows") != 8
            or proof.get("candidateDeployed") is not False or proof.get("liveImageId") != old["Image"]):
        raise RuntimeError("ING_PROOF_BASELINE_DRIFT")
    image = probe.inspect(proof["candidateImageId"], "image")
    if image["Config"].get("Labels", {}).get("org.opencontainers.image.revision") != REVISION:
        raise RuntimeError("ING_CANDIDATE_PROVENANCE_MISMATCH")
    guard(old, image)
    settings = probe.transport_settings(old, args.tenant_id)
    source = next(m["Source"] for m in old["Mounts"] if m["Destination"] == probe.PROPERTIES)
    original = Path(source).read_bytes()
    if any(key in original.decode() for key in settings):
        raise RuntimeError("ING_ACTIVATION_PROPERTY_ALREADY_PRESENT")
    version = probe.run(["docker", "exec", "ouf-postgres", "psql", "-X", "-qAt", "-v",
        "ON_ERROR_STOP=1", "-U", "ouf_ingestion", "-d", "ouf_ingestion", "-c",
        "begin read only; select version from ouf_ingestion.flyway_schema_history order by installed_rank desc limit 1; rollback;"])
    if version != "14":
        raise RuntimeError("ING_LIVE_SCHEMA_DRIFT")
    content = original + b"\n" + "".join(k + "=" + v + "\n" for k, v in settings.items()).encode()
    existing = optional()
    if STATE.exists() or STATE.is_symlink():
        private(STATE, 0o600)
        state = json.loads(STATE.read_text())
        properties = Path(state["properties"])
        private(properties, 0o440)
        if (state.get("revision") != REVISION or stable(state["old"]) != stable(old)
                or state.get("image_id") != image["Id"] or existing is None
                or state.get("candidate_id") != existing["Id"] or properties.read_bytes() != content
                or not matches(existing, old, image, properties)):
            raise RuntimeError("ING_RELEASE_STATE_DRIFT")
    else:
        if existing is not None:
            raise RuntimeError("ING_UNOWNED_CANDIDATE_PRESENT")
        folder = Path(tempfile.mkdtemp(prefix="ingestion-compatibility-", dir=ROOT))
        properties = folder / "ingestion-summary.properties"
        properties.write_bytes(content)
        os.chown(properties, 0, 10002)
        properties.chmod(0o440)
        env_path = folder / "candidate.env"
        created = None
        try:
            env_path.write_text("\n".join(old["Config"]["Env"]) + "\n")
            cmd = ["docker", "create", "--name", NAME, "--network", "ouf-backend",
                "--network-alias", "ouf-ingestion", "--restart", "no", "--user", "10002:10002",
                "--log-driver", "json-file", "--env-file", str(env_path)]
            cmd.extend(memory_flags(old["HostConfig"]))
            for k, v in old["HostConfig"]["LogConfig"].get("Config", {}).items():
                cmd.extend(["--log-opt", k + "=" + v])
            for _, src, dst, _ in mounts(old, properties):
                cmd.extend(["--mount", "type=bind,src=" + src + ",dst=" + dst + ",readonly"])
            cmd.append(image["Id"])
            if stable(probe.inspect("ouf-ingestion")) != stable(old) or Path(source).read_bytes() != original:
                raise RuntimeError("ING_LIVE_CHANGED_DURING_PREPARE")
            created = probe.run(cmd)
            candidate = probe.inspect(NAME)
            if candidate["Id"] != created or not matches(candidate, old, image, properties):
                raise RuntimeError("ING_CANDIDATE_READBACK_MISMATCH")
            probe.candidate_row(args.source, args.version, args.expected_hash)
            if stable(probe.inspect("ouf-ingestion")) != stable(old) or Path(source).read_bytes() != original:
                raise RuntimeError("ING_LIVE_CHANGED_DURING_PREPARE")
            staged = folder / "state.json"
            staged.write_text(json.dumps({"revision": REVISION, "image_id": image["Id"], "old": old,
                "candidate_id": created, "candidate_name": NAME, "properties": str(properties),
                "properties_sha256": hashlib.sha256(content).hexdigest(), "proof": proof,
                "source": args.source, "version": args.version, "expected_hash": args.expected_hash,
                "tenant_id": args.tenant_id}, sort_keys=True) + "\n")
            os.link(staged, STATE)
        except BaseException:
            if created:
                current = optional()
                if current is not None and current["Id"] == created and not current["State"]["Running"]:
                    probe.run(["docker", "rm", created])
            raise
        finally:
            env_path.unlink(missing_ok=True)
    print("R4A_ING_COMPAT_CANDIDATE=PASS STOPPED=true ENV_PRESERVED=true TRANSPORT_CONFIG_PREPARED=true")
    print("R4A_ING_COMPAT_RELEASE_STATE=" + str(STATE) + " PRIVATE=true")
    print("R4A_ING_COMPAT_RELEASE_PREPARE=PASS LIVE_UNCHANGED=true DB_UNCHANGED=true ATTESTATION_POST=false SECRETS_NOT_PRINTED=true")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("source", "version", "expected-hash", "tenant-id"):
        parser.add_argument("--" + option, required=True)
    try:
        main(parser.parse_args())
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_ING_COMPAT_RELEASE_PREPARE=BLOCKED CODE=" + code + " SECRETS_NOT_PRINTED=true")
        raise SystemExit(1)
