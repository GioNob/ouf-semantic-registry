#!/usr/bin/env python3
"""Inventory approval routes without creating, confirming or activating a challenge."""
import json
import os
import re
import subprocess
import r4a_execution_route_inventory as routes

SOURCE = "managed-cinema-8ec8ae90"
VERSION = "68394f42-5c82-4127-a1f3-126516665749"
HASH = "sha256:2b4a491e27e0d6bb2f7fabfb07d5644676986c5c4e90be31998d3cb9a9a81891"
OWNER = "6340d5bf120e09b47c32177656e2c377a4c03640"
CARD = "/api/trusted-human/v1/approval-challenges/00000000-0000-0000-0000-000000000000"
TARGETS = {
    "CREATE": ("POST", "/api/onboarding/v1/sources/" + SOURCE +
               "/onboarding-versions/" + VERSION + "/approval-challenges"),
    "CARD": ("GET", CARD),
    "CONFIRM": ("POST", CARD + "/confirm"),
    "ACTIVATE": ("POST", CARD + "/activate"),
}


def uri_matches(pattern, path):
    if not isinstance(pattern, str):
        return False
    # APISIX static paths, trailing wildcard and named path parameters.
    if "*" in pattern[:-1] or pattern.count("*") > 1:
        return False
    expression = re.escape(pattern).replace(r"\*", ".*")
    expression = re.sub(r":[A-Za-z_][A-Za-z0-9_]*", "[^/]+", expression)
    return re.fullmatch(expression, path) is not None


def candidates(values, method, path):
    return [value for value in values
            if (not value.get("methods") or method in value["methods"])
            and any(uri_matches(uri, path) for uri in
                    [value.get("uri")] + (value.get("uris") or []))]


def flag(name, value):
    print(name + "=" + str(bool(value)).lower())


def main():
    if os.geteuid() != 0:
        raise RuntimeError("ROOT_REQUIRED")
    print("R4A_APPROVAL_ROUTE_INVENTORY=READ_ONLY", flush=True)
    before = routes.helper.candidate_row(SOURCE, VERSION, HASH)
    print("APPROVAL_VERSION_STATE=" + before["state"])
    live = routes.helper.inspect("ouf-onboarding")
    image = routes.helper.inspect(live["Image"], "image")
    if (not live["State"]["Running"] or image["Config"].get("Labels", {}).get(
            "org.opencontainers.image.revision") != OWNER):
        raise RuntimeError("APPROVAL_OWNER_REVISION_DRIFT")
    apisix = routes.helper.inspect("ouf-apisix")
    if not apisix["State"]["Running"]:
        raise RuntimeError("APISIX_NOT_RUNNING")
    key = routes.admin_key(routes.mounted_config(apisix).read_text())
    config = ('silent\nshow-error\nfail\nmax-time = 15\nmax-filesize = 10485760\n'
              'header = "X-API-KEY: ' + key + '"\n'
              'url = "http://127.0.0.1:9180/apisix/admin/routes"\n')
    raw = routes.helper.run(["docker", "run", "--rm", "-i", "--read-only",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--network", "container:ouf-apisix", "curlimages/curl:8.16.0",
        "--config", "-"], input=config, timeout=30)
    values = routes.route_values(json.loads(raw))
    for name, (method, path) in TARGETS.items():
        matched = candidates(values, method, path)
        print("APPROVAL_" + name + "_ROUTE_COUNT=" + str(len(matched)))
        for index, route in enumerate(matched, 1):
            prefix = "APPROVAL_" + name + "_" + str(index) + "_"
            plugins = route.get("plugins", {})
            oidc = plugins.get("openid-connect", {})
            rewrite = plugins.get("proxy-rewrite", {})
            flag(prefix + "ENABLED", route.get("status", 1) == 1)
            flag(prefix + "UPSTREAM_ONBOARDING", route.get("upstream", {}).get(
                "nodes") == {"ouf-onboarding:8080": 1})
            flag(prefix + "UPSTREAM_REFERENCE", "upstream_id" in route)
            flag(prefix + "SERVICE_REFERENCE", "service_id" in route)
            flag(prefix + "PLUGIN_CONFIG_REFERENCE", "plugin_config_id" in route)
            flag(prefix + "OIDC_ENABLED", oidc and not oidc.get("_meta", {}).get("disable", False))
            flag(prefix + "OWNER_PATH_PRESERVED", not rewrite.get("uri") and not rewrite.get("regex_uri"))
            flag(prefix + "REWRITE_PRESENT", bool(rewrite))
            flag(prefix + "EXTRA_MATCH_CONDITIONS", any(route.get(k) for k in ("vars", "filter_func", "remote_addr", "remote_addrs")))
            hosts = ([route["host"]] if route.get("host") else []) + (route.get("hosts") or [])
            flag(prefix + "PUBLIC_HOST_UNRESTRICTED_OR_EXACT", not hosts or "api.ouf-lab.it" in hosts)
            scopes = oidc.get("required_scopes") or []
            if not isinstance(scopes, list) or any(not isinstance(s, str) or not re.fullmatch(r"[A-Za-z0-9._:-]{1,160}", s) for s in scopes):
                raise RuntimeError("APPROVAL_SCOPE_LAYOUT_UNSUPPORTED")
            print(prefix + "REQUIRED_SCOPES=" + (",".join(scopes) or "NONE_INLINE"))
    after = routes.helper.inspect("ouf-onboarding")
    if (after["Id"] != live["Id"] or after["Image"] != live["Image"] or
            routes.helper.candidate_row(SOURCE, VERSION, HASH) != before):
        raise RuntimeError("APPROVAL_LIVE_OR_VERSION_DRIFT")
    print("R4A_APPROVAL_ROUTE_INVENTORY=COMPLETE LIVE_UNCHANGED=true CHALLENGE_POST=false SOURCE_APPROVAL=false SOURCE_ACTIVATION=false SECRETS_NOT_PRINTED=true")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_APPROVAL_ROUTE_INVENTORY=BLOCKED CODE=" + code + " SECRETS_NOT_PRINTED=true")
        raise SystemExit(1)
