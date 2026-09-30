#!/usr/bin/env python3
"""Inspect the attestation Gateway route without printing credentials or route values."""
import json
import os
import r4a_execution_route_inventory as routes


def main():
    if os.geteuid() != 0:
        raise RuntimeError("ROOT_REQUIRED")
    print("R4A_ING_ATTESTATION_ROUTE_INVENTORY=READ_ONLY", flush=True)
    try:
        helper = routes.helper
        owner = helper.inspect("ouf-onboarding")
        image = helper.inspect(owner["Image"], "image")
        print("ING_ATTESTATION_OWNER_REVISION_MATCH=" + str(
            image["Config"].get("Labels", {}).get("org.opencontainers.image.revision")
            == "6340d5bf120e09b47c32177656e2c377a4c03640").lower())
        apisix = helper.inspect("ouf-apisix")
        if not apisix["State"]["Running"]:
            raise RuntimeError("APISIX_NOT_RUNNING")
        key = routes.admin_key(routes.mounted_config(apisix).read_text())
        config = ('silent\nshow-error\nfail\nmax-time = 15\nmax-filesize = 10485760\n'
                  'header = "X-API-KEY: ' + key + '"\n'
                  'url = "http://127.0.0.1:9180/apisix/admin/routes"\n')
        raw = helper.run(["docker", "run", "--rm", "-i", "--read-only",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--network", "container:ouf-apisix", "curlimages/curl:8.16.0",
            "--config", "-"], input=config, timeout=30)
        target = "/api/internal/v1/onboarding/compatibility/ingestion-runtime"
        matching = []
        for route in routes.route_values(json.loads(raw)):
            uris = [route.get("uri")] + (route.get("uris") or [])
            rewrite = route.get("plugins", {}).get("proxy-rewrite", {}).get("uri")
            relevant = rewrite == target or any(
                isinstance(uri, str) and (uri.endswith("/compatibility/ingestion-runtime")
                or (uri.endswith("/*") and target.startswith(uri[:-1]) and not rewrite))
                for uri in uris)
            if relevant and (not route.get("methods") or "POST" in route["methods"]):
                matching.append(route)
        print("ING_ATTESTATION_ROUTE_COUNT=" + str(len(matching)))
        if len(matching) == 1:
            route = matching[0]
            plugins = route.get("plugins", {})
            oidc = plugins.get("openid-connect", {})
            rewrite = plugins.get("proxy-rewrite", {}).get("uri")
            uris = [route.get("uri")] + (route.get("uris") or [])
            facts = {
                "ING_ATTESTATION_ROUTE_ENABLED": route.get("status", 1) == 1,
                "ING_ATTESTATION_OWNER_PATH_MATCH": rewrite == target or
                    (not rewrite and any(isinstance(uri, str) and
                    (uri == target or (uri.endswith("/*") and target.startswith(uri[:-1])))
                    for uri in uris)),
                "ING_ATTESTATION_UPSTREAM_ONBOARDING":
                    route.get("upstream", {}).get("nodes") == {"ouf-onboarding:8080": 1},
                "ING_ATTESTATION_UPSTREAM_REFERENCE": "upstream_id" in route,
                "ING_ATTESTATION_OIDC_PRESENT": bool(oidc),
                "ING_ATTESTATION_REQUIRED_SCOPE_MATCH":
                    "ouf.ingestion.configuration.attest" in (oidc.get("required_scopes") or []),
                "ING_ATTESTATION_OIDC_ENABLED": not oidc.get("_meta", {}).get("disable", False),
            }
            for name, value in facts.items():
                print(name + "=" + str(bool(value)).lower())
        print("R4A_ING_ATTESTATION_ROUTE_INVENTORY=COMPLETE LIVE_UNCHANGED=true ATTESTATION_POST=false VALUES_NOT_PRINTED=true")
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_ING_ATTESTATION_ROUTE_INVENTORY=BLOCKED CODE="
              + code + " ATTESTATION_POST=false SECRETS_NOT_PRINTED=true")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

