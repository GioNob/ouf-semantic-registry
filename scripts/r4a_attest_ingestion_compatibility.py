#!/usr/bin/env python3
"""Plan/apply the SERVICE compatibility attestation after a fresh deployed-image proof."""
import argparse
import json
import os
from pathlib import Path
import re
import tempfile
import uuid
from urllib.parse import urlsplit
import r4a_probe_deployed_ingestion as deployed
import r4a_execution_route_inventory as routes
from r4a_probe_deployed_ingestion import prepare, inventory, switch

TARGET = "/api/internal/v1/onboarding/compatibility/ingestion-runtime"
RECEIPT = prepare.ROOT / "ingestion-compatibility-attestation.json"


def save(value):
    fd, name = tempfile.mkstemp(prefix=".ingestion-attestation-", dir=prepare.ROOT)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(json.dumps(value, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, RECEIPT)
    finally:
        Path(name).unlink(missing_ok=True)


def reserve(value):
    # Exclusive creation also prevents concurrent submitters from both posting.
    with RECEIPT.open("x") as stream:
        stream.write(json.dumps(value, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def existing_count(args):
    version = str(uuid.UUID(args.version))
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", args.expected_hash):
        raise RuntimeError("ING_ATTESTATION_HASH_INVALID")
    query = ("begin read only; select count(*) from ouf_onboarding.consumer_compatibility_attestation "
        "where onboarding_version_id='" + version + "' and configuration_hash='" + args.expected_hash
        + "' and consumer='INGESTION_RUNTIME'; rollback;")
    return int(inventory.run(["docker", "exec", "ouf-postgres", "psql", "-X", "-qAt", "-v",
        "ON_ERROR_STOP=1", "-U", "ouf_onboarding", "-d", "ouf_onboarding", "-c", query]))


def route_path(documents, gateway):
    matching = []
    for route in documents:
        uris = [route.get("uri")] + (route.get("uris") or [])
        rewrite = route.get("plugins", {}).get("proxy-rewrite", {}).get("uri")
        relevant = rewrite == TARGET or any(isinstance(u, str) and
            (u.endswith("/compatibility/ingestion-runtime") or
             (u.endswith("/*") and TARGET.startswith(u[:-1]) and not rewrite)) for u in uris)
        if relevant and (not route.get("methods") or "POST" in route["methods"]):
            matching.append(route)
    if len(matching) != 1:
        raise RuntimeError("ING_ATTESTATION_ROUTE_NOT_UNIQUE")
    route = matching[0]
    plugins = route.get("plugins", {})
    oidc = plugins.get("openid-connect", {})
    rewrite = plugins.get("proxy-rewrite", {}).get("uri")
    uris = [u for u in [route.get("uri")] + (route.get("uris") or []) if u is not None]
    if (route.get("status", 1) != 1 or not oidc or oidc.get("_meta", {}).get("disable", False)
            or "ouf.ingestion.configuration.attest" not in (oidc.get("required_scopes") or [])
            or route.get("upstream", {}).get("nodes") != {"ouf-onboarding:8080": 1}
            or "upstream_id" in route or len(uris) != 1
            or plugins.get("proxy-rewrite", {}).get("regex_uri")
            or plugins.get("proxy-rewrite", {}).get("_meta", {}).get("disable", False)):
        raise RuntimeError("ING_ATTESTATION_ROUTE_CONTRACT_DRIFT")
    path = uris[0]
    if path.endswith("/*") and not rewrite and TARGET.startswith(path[:-1]):
        path = TARGET
    elif rewrite != TARGET and not (path == TARGET and not rewrite):
        raise RuntimeError("ING_ATTESTATION_OWNER_PATH_DRIFT")
    if not re.fullmatch(r"/[A-Za-z0-9/_-]+", path):
        raise RuntimeError("ING_ATTESTATION_PUBLIC_PATH_UNSUPPORTED")
    hosts = route.get("hosts") or ([route["host"]] if route.get("host") else [])
    if hosts and urlsplit(gateway).hostname not in hosts:
        raise RuntimeError("ING_ATTESTATION_ROUTE_HOST_MISMATCH")
    return path


def resolve_route(gateway):
    owner = inventory.inspect("ouf-onboarding")
    image = inventory.inspect(owner["Image"], "image")
    if (not owner["State"]["Running"] or image["Config"].get("Labels", {}).get(
            "org.opencontainers.image.revision") != "6340d5bf120e09b47c32177656e2c377a4c03640"):
        raise RuntimeError("ING_ATTESTATION_OWNER_REVISION_DRIFT")
    apisix = inventory.inspect("ouf-apisix")
    if not apisix["State"]["Running"]:
        raise RuntimeError("APISIX_NOT_RUNNING")
    key = routes.admin_key(routes.mounted_config(apisix).read_text())
    config = ('silent\nshow-error\nfail\nmax-time = 15\nmax-filesize = 10485760\n'
              'header = "X-API-KEY: ' + key + '"\n'
              'url = "http://127.0.0.1:9180/apisix/admin/routes"\n')
    raw = inventory.run(["docker", "run", "--rm", "-i", "--read-only", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges", "--network", "container:ouf-apisix",
        "curlimages/curl:8.16.0", "--config", "-"], input=config, timeout=30)
    return route_path(routes.route_values(json.loads(raw)), gateway)


def body_for(proof, args):
    inventory.validate_proof(proof, {"onboardingVersionId": args.version, "configurationHash": args.expected_hash})
    if (proof.get("candidateDeployed") is not True or proof.get("candidateCommit") != prepare.REVISION
            or proof.get("sourceId") != args.source or proof.get("tenantId") != args.tenant_id
            or proof.get("validatedRows") != 8
            or proof.get("executionMode") != "SEPARATE_JVM_DEPLOYED_IMAGE_AND_LIVE_MOUNTS"):
        raise RuntimeError("ING_ATTESTATION_PROOF_CONTEXT_INVALID")
    evidence = {k: proof[k] for k in ("candidateCommit", "liveContainerId", "liveImageId",
        "onboardingVersionId", "configurationHash", "contentHash", "adapterId", "adapterRuntimeVersion",
        "semanticBindingCount", "validatedRows", "propertiesSha256", "verifiedAtEpochSeconds", "executionMode")}
    return {"sourceId": args.source, "onboardingVersionId": args.version, "compatible": True,
            "detail": json.dumps({"schema": "ouf.r4a.ingestion.compatibility-evidence.v1", **evidence}, sort_keys=True)}


def post(body, live, settings, path, correlation):
    token_file = Path(settings["ouf.ingestion.activation.token-file"]).relative_to(inventory.AUTH)
    mount = next(m for m in live["Mounts"] if m["Destination"] == inventory.AUTH)
    token = Path(mount["Source"]).joinpath(token_file).read_text().strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", token):
        raise RuntimeError("ING_ATTESTATION_TOKEN_FORMAT_INVALID")
    config = ('silent\nshow-error\nmax-time = 15\nmax-filesize = 1048576\n'
        'request = "POST"\nheader = "Content-Type: application/json"\n'
        'header = "Authorization: Bearer ' + token + '"\n'
        'header = "X-Correlation-ID: ' + correlation + '"\n'
        'url = ' + json.dumps(settings["ouf.ingestion.activation.gateway-url"] + path) + '\n'
        'data = ' + json.dumps(json.dumps(body)) + '\nwrite-out = "\\n%{http_code}"\n')
    raw = inventory.run(["docker", "run", "--rm", "-i", "--read-only", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges", "--network", "ouf-backend",
        "curlimages/curl:8.16.0", "--config", "-"], input=config, timeout=30)
    response, status = raw.rsplit("\n", 1)
    if status != "201":
        raise RuntimeError("ING_ATTESTATION_GATEWAY_" + (status if re.fullmatch(r"\d{3}", status) else "INVALID_STATUS"))
    return json.loads(response)


def verify_response(response, body, args):
    identifier = str(uuid.UUID(str(response["attestation_id"])))
    if (str(response.get("onboarding_version_id")) != args.version
            or response.get("consumer") != "INGESTION_RUNTIME"
            or response.get("configuration_hash") != args.expected_hash
            or response.get("compatible") is not True or response.get("detail") != body["detail"]):
        raise RuntimeError("ING_ATTESTATION_RESPONSE_MISMATCH")
    return identifier


def readback(identifier):
    identifier = str(uuid.UUID(identifier))
    query = ("begin read only; select row_to_json(a)::text from (select attestation_id,"
        "onboarding_version_id,consumer,configuration_hash,compatible,detail "
        "from ouf_onboarding.consumer_compatibility_attestation where attestation_id='" + identifier + "') a; rollback;")
    return json.loads(inventory.run(["docker", "exec", "ouf-postgres", "psql", "-X", "-qAt", "-v",
        "ON_ERROR_STOP=1", "-U", "ouf_onboarding", "-d", "ouf_onboarding", "-c", query]))


def main(args):
    if os.geteuid() != 0:
        raise RuntimeError("ROOT_REQUIRED")
    os.umask(0o077)
    if RECEIPT.exists() or RECEIPT.is_symlink():
        raise RuntimeError("ING_ATTESTATION_RECEIPT_ALREADY_EXISTS_NO_REPOST")
    # Fresh production consumer evidence with the actual deployed image/mounts.
    deployed.main(args)
    proof = switch.private_json(deployed.PROOF)
    body = body_for(proof, args)
    live = inventory.inspect(switch.LIVE)
    if live["Id"] != proof["liveContainerId"] or live["Image"] != proof["liveImageId"]:
        raise RuntimeError("ING_ATTESTATION_LIVE_DRIFT")
    settings = switch.tokens_fresh(live, args.tenant_id)
    path = resolve_route(settings["ouf.ingestion.activation.gateway-url"])
    before = switch.frozen(args)
    if before.get("state") != "IN_REVIEW":
        raise RuntimeError("ING_ATTESTATION_EXPECTED_IN_REVIEW")
    if existing_count(args):
        raise RuntimeError("ING_ATTESTATION_ALREADY_PRESENT_RECONCILIATION_REQUIRED")
    print("R4A_ING_ATTESTATION_PLAN=PASS MODE=" + args.mode + " VALIDATED_ROWS=8 SECRETS_NOT_PRINTED=true", flush=True)
    if args.mode == "plan":
        print("R4A_ING_ATTESTATION=PLANNED ATTESTATION_POST=false SOURCE_APPROVAL=false SOURCE_ACTIVATION=false")
        return
    receipt = {"status": "POST_PENDING", "source": args.source, "version": args.version,
               "configuration_hash": args.expected_hash, "proof": proof, "body": body,
               "correlation_id": str(uuid.uuid4()), "post_attempted": False}
    reserve(receipt)  # Persist exclusively before a non-idempotent request.
    try:
        if (prepare.stable(inventory.inspect(switch.LIVE)) != prepare.stable(live)
                or switch.frozen(args) != before
                or deployed.digest(Path(next(m["Source"] for m in live["Mounts"]
                      if m["Destination"] == inventory.PROPERTIES))) != proof["propertiesSha256"]):
            raise RuntimeError("ING_ATTESTATION_CONTEXT_CHANGED_BEFORE_POST")
        settings = switch.tokens_fresh(live, args.tenant_id)
        if existing_count(args):
            raise RuntimeError("ING_ATTESTATION_APPEARED_BEFORE_POST")
        receipt["post_attempted"] = True
        save(receipt)
        response = post(body, live, settings, path, receipt["correlation_id"])
        receipt["response"] = response
        identifier = verify_response(response, body, args)
        save(receipt)
        verify_response(readback(identifier), body, args)
        if switch.frozen(args) != before:
            raise RuntimeError("ING_ATTESTATION_FROZEN_VERSION_CHANGED")
        receipt.update(status="PASS", attestation_id=identifier)
        save(receipt)
        print("R4A_ING_ATTESTATION=PASS ATTESTATION_ID=" + identifier)
        print("R4A_ING_ATTESTATION_READBACK=PASS FROZEN_VERSION_UNCHANGED=true")
        print("R4A_ING_ATTESTATION_RECEIPT=" + str(RECEIPT) + " PRIVATE=true")
        print("R4A_ING_ATTESTATION_COMPLETE=PASS ATTESTATION_POST=true SOURCE_APPROVAL=false SOURCE_ACTIVATION=false SECRETS_NOT_PRINTED=true")
    except BaseException:
        receipt["status"] = "UNVERIFIED_DO_NOT_REPOST"
        save(receipt)
        print("R4A_ING_ATTESTATION=UNVERIFIED RECEIPT_RETAINED=true AUTOMATIC_REPOST=false", flush=True)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "apply"))
    for option in ("source", "version", "expected-hash", "tenant-id"):
        parser.add_argument("--" + option, required=True)
    try:
        main(parser.parse_args())
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_ING_ATTESTATION=BLOCKED CODE=" + code + " SECRETS_NOT_PRINTED=true")
        raise SystemExit(1)
