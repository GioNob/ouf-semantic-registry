#!/usr/bin/env python3
"""Read-only real consumer probe using the deployed image and unchanged live mounts.

Runs a separate JVM, without Spring, Flyway, schedulers or persistence ports.
Does not invoke a live application endpoint or post an attestation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time
import uuid
import r4a_switch_ingestion_candidate as switch
from r4a_switch_ingestion_candidate import prepare, inventory

PROOF = prepare.ROOT / "ingestion-deployed-compatibility-probe.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(args):
    if os.geteuid() != 0:
        raise RuntimeError("ROOT_REQUIRED")
    os.umask(0o077)
    root = prepare.ROOT.lstat()
    if not stat.S_ISDIR(root.st_mode) or root.st_uid != 0 or stat.S_IMODE(root.st_mode) != 0o700:
        raise RuntimeError("ING_SNAPSHOT_DIRECTORY_UNSAFE")
    state, receipt = switch.private_json(prepare.STATE), switch.private_json(switch.RECEIPT)
    if (receipt.get("status") != "PASS" or receipt.get("revision") != prepare.REVISION
            or state.get("revision") != prepare.REVISION
            or receipt.get("candidate_id") != state.get("candidate_id")
            or any(state.get(k) != getattr(args, k) for k in ("source", "version", "expected_hash", "tenant_id"))):
        raise RuntimeError("ING_DEPLOYMENT_RECEIPT_OR_CONTEXT_INVALID")
    live = inventory.inspect(switch.LIVE)
    image = inventory.inspect(state["image_id"], "image")
    properties = Path(state["properties"])
    prepare.private(properties, 0o440)
    prepare.guard(live, image)
    if (live["Id"] != state["candidate_id"] or live["Image"] != state["image_id"]
            or image["Config"].get("Labels", {}).get("org.opencontainers.image.revision") != prepare.REVISION
            or prepare.environment(live) != prepare.environment(state["old"])
            or prepare.mounts(live) != prepare.mounts(state["old"], properties)
            or any(live["HostConfig"].get(k, 0) != state["old"]["HostConfig"].get(k, 0)
                   for k in ("Memory", "MemorySwap"))
            or digest(properties) != state["properties_sha256"]):
        raise RuntimeError("ING_DEPLOYED_RUNTIME_DRIFT")
    settings = switch.tokens_fresh(live, args.tenant_id)
    text = properties.read_text()
    if any(inventory.literal_property(text, k) != v for k, v in settings.items()):
        raise RuntimeError("ING_DEPLOYED_TRANSPORT_SETTINGS_DRIFT")
    before, row = switch.history(), switch.frozen(args)
    if before != receipt["history"]:
        raise RuntimeError("ING_DEPLOYED_FLYWAY_DRIFT")
    switch.ready(1)
    name = "ouf-ingestion-deployed-probe-" + uuid.uuid4().hex
    command = ["docker", "run", "--rm", "--name", name, "--interactive", "--network", "ouf-backend",
        "--user", "10002:10002", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--pids-limit", "128", "--memory", "1g", "--cpus", "1", "--log-driver", "none",
        "--tmpfs", "/tmp:rw,nosuid,nodev,size=128m,mode=1777", *inventory.probe_mounts(live),
        "--entrypoint", "java", live["Image"],
        "-Dloader.main=it.comune.trieste.ouf.ingestion.FrozenConfigurationProbeMain", "-cp", "/app/app.jar",
        "org.springframework.boot.loader.launch.PropertiesLauncher", "--properties", inventory.PROPERTIES]
    print("R4A_ING_DEPLOYED_COMPAT_PROBE=RUNNING LIVE_CONFIG_CHANGED=false ATTESTATION_POST=false", flush=True)
    try:
        result = subprocess.run(command, input=json.dumps(row), capture_output=True, text=True, timeout=120)
    finally:
        subprocess.run(["docker", "rm", "--force", name], capture_output=True, text=True, timeout=30)
    try:
        proof = json.loads(result.stdout)
    except ValueError:
        raise RuntimeError("ING_DEPLOYED_PROBE_OUTPUT_INVALID") from None
    if result.returncode:
        code = proof.get("code")
        raise RuntimeError(code if isinstance(code, str) and re.fullmatch(r"ING_[A-Z0-9_]{1,80}", code)
                           else "ING_DEPLOYED_PROBE_FAILED")
    inventory.validate_proof(proof, row)
    if (proof.get("validatedRows") != 8
            or any(proof.get(k) != state["proof"].get(k) for k in
                   ("contentHash", "adapterId", "adapterRuntimeVersion", "semanticBindingCount"))):
        raise RuntimeError("ING_DEPLOYED_CONSUMER_PROOF_DRIFT")
    if (prepare.stable(inventory.inspect(switch.LIVE)) != prepare.stable(live)
            or digest(properties) != state["properties_sha256"]
            or switch.history() != before or switch.frozen(args) != row):
        raise RuntimeError("ING_LIVE_OR_FROZEN_VERSION_CHANGED_DURING_PROBE")
    proof.update({"candidateCommit": prepare.REVISION, "candidateDeployed": True,
        "liveContainerId": live["Id"], "liveImageId": live["Image"],
        "propertiesSha256": state["properties_sha256"], "sourceId": args.source,
        "tenantId": args.tenant_id, "verifiedAtEpochSeconds": int(time.time()),
        "executionMode": "SEPARATE_JVM_DEPLOYED_IMAGE_AND_LIVE_MOUNTS"})
    temporary = prepare.ROOT / (".ingestion-deployed-proof-" + uuid.uuid4().hex)
    try:
        with temporary.open("x") as stream:
            stream.write(json.dumps(proof, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, PROOF)
    finally:
        temporary.unlink(missing_ok=True)
    print("R4A_ING_DEPLOYED_COMPAT_PROBE=PASS VALIDATED_ROWS=8")
    print("R4A_ING_DEPLOYED_COMPAT_REVISION=" + prepare.REVISION)
    print("R4A_ING_DEPLOYED_COMPAT_PROOF=" + str(PROOF) + " PRIVATE=true")
    print("R4A_ING_DEPLOYED_COMPAT_COMPLETE=PASS SEPARATE_JVM=true LIVE_CONFIG_CHANGED=false ATTESTATION_POST=false SECRETS_NOT_PRINTED=true")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("source", "version", "expected-hash", "tenant-id"):
        parser.add_argument("--" + option, required=True)
    try:
        main(parser.parse_args())
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_ING_DEPLOYED_COMPAT_PROBE=BLOCKED CODE=" + code + " ATTESTATION_POST=false SECRETS_NOT_PRINTED=true")
        raise SystemExit(1)
