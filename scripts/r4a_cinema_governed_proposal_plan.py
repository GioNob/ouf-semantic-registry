#!/usr/bin/env python3
"""Plan the exact governed cinema DRAFT; read-only, no bearer or config dump."""

import hashlib
import json
import os
from pathlib import Path
import subprocess


SOURCE = "managed-cinema-8ec8ae90"
VERSION = "68394f42-5c82-4127-a1f3-126516665749"
ASSET = "8ec8ae90-808a-4d9e-907c-d56de119e376"
PROFILE = "4462692b-9c85-446b-b6fd-779f01eab64d"
SEMANTIC = "https://api.ouf-lab.it/semantic/cinema"
REVISION = "51706bed-81e4-4306-aca1-70119821727d"
PUBLICATION_SET = "f92a2e17-30c9-456f-bb12-63afa84f41e6"
CLASS = SEMANTIC + "#Cinema"
PROPERTIES = [SEMANTIC + "#indirizzo", SEMANTIC + "#nome"]
POLICY_REF = "identity://ouf-lab/cinema/complete-canonical-equality/1"
ASSERTION_REF = "assertion://ouf-lab/r4a/2026-09-28/canonical-equality"
STATE = Path("/etc/ouf/deploy-snapshots/r4a-cinema-semantic-draft.json")


def db(sql):
    return subprocess.run(["docker", "exec", "ouf-postgres", "psql", "-U",
                           "ouf_onboarding", "-d", "ouf_onboarding", "-Atc", sql],
                          capture_output=True, text=True, check=True,
                          timeout=30).stdout.strip()


def plan():
    if os.geteuid() != 0:
        raise RuntimeError("ROOT_REQUIRED")
    state = json.loads(STATE.read_text())
    if (state.get("semanticId") != SEMANTIC or state.get("revisionId") != REVISION
        or state.get("publicationSetId") != PUBLICATION_SET):
        raise RuntimeError("SEMANTIC_PUBLICATION_DRIFT")
    row = json.loads(db("select json_build_object('state',v.state,'lock',v.lock_version,"
        "'configuration',v.configuration,'assetHash',a.content_hash,"
        "'assetSize',a.size_bytes,'assetStagingRef',a.staging_ref)::text "
        "from ouf_onboarding.onboarding_version v "
        "join ouf_onboarding.managed_file_asset a on a.asset_id='" + ASSET + "' "
        "where v.source_id='" + SOURCE + "' and v.onboarding_version_id='" + VERSION + "'"))
    config = row["configuration"]
    ex = config["extractionProfile"]
    rt = ex["runtime"]
    semantic = config["semanticMapping"]
    mappings = semantic["propertyMappings"]
    if (row["state"] != "DRAFT" or row["lock"] != 0
        or ex["selection"] != {"assetId": ASSET, "fileProfileId": PROFILE}
        or rt.get("assetId") != ASSET or rt.get("fileProfileId") != PROFILE
        or rt.get("mode") != "MANAGED" or rt.get("recordModel") != "ONE_ROW_ONE_SOURCE_OBJECT"
        or rt.get("rowIdentityBasis") != "ASSET_AND_ROW_ORDINAL"
        or rt.get("contentHash") != row["assetHash"]
        or rt.get("stagingRef") != row["assetStagingRef"]
        or not str(row["assetStagingRef"]).startswith("object://")
        or row["assetSize"] != 509 or rt.get("execution") or rt.get("udp")
        or config.get("semanticReferenceBindings")
        or semantic.get("semanticRefs") != [SEMANTIC + "@1.0.0"]
        or semantic.get("targetClasses") != [{"classIri": CLASS,
             "ontologyId": SEMANTIC, "ontologyVersion": "1.0.0"}]
        or sorted(x.get("targetPropertyIri") for x in mappings) != PROPERTIES
        or len(mappings) != 2
        or config["sourceObjectIdentityPolicy"].get("sourceFields") != ["$managedRowOrdinal"]
        or set(config["bundle"].get("source", {})) !=
           {"sourceId", "sourceKind", "acquisitionMode"}):
        raise RuntimeError("LIVE_DRAFT_OR_ASSET_DRIFT")
    proposed = json.loads(json.dumps(config))
    proposed["semanticReferenceBindings"] = [{"semanticId": SEMANTIC,
        "semanticVersion": "1.0.0", "revisionId": REVISION,
        "publicationSetId": PUBLICATION_SET}]
    execution = {"acquisitionMode": "INTERNAL_MANAGED_CSV",
        "adapterId": "managed-tabular-v1", "adapterRuntimeVersion": "1.0.0",
        "sourceSchemaRef": config["bundle"]["schemaRef"],
        "sourceSchemaId": SOURCE, "sourceSchemaVersion": "1",
        "semanticPublicationSetRef": PUBLICATION_SET,
        "adapterProfileRef": "adapter://managed-tabular/1",
        "observationPolicy": "ACQUISITION_TIME", "expectedSize": row["assetSize"],
        "maxRows": 1000, "maxColumns": 20, "maxCellChars": 10000}
    signals = [{"id": prop, "semanticRef": prop + "@" + PUBLICATION_SET,
        "comparator": "TEXT_V1", "excludesOnDisagreement": False,
        "uniqueWithinScope": False, "assertionRef": ASSERTION_REF + "/" + prop.rsplit("#", 1)[-1]}
        for prop in PROPERTIES]
    rules = [{"id": prop.rsplit("#", 1)[-1] + "-observed-subset",
        "signalIds": [prop], "assertionRef": ASSERTION_REF + "/subset"}
        for prop in PROPERTIES]
    resolution = {"strategyId": "GOVERNED_IDENTITY", "strategyVersion": "1",
        "policyRef": POLICY_REF, "governedIdentity": {"ref": POLICY_REF,
        "version": "1", "tenantId": "ouf-lab", "canonicalClass": CLASS,
        "sourceId": SOURCE, "maxCandidates": 100, "allowAutoNew": True,
        "signals": signals, "sufficientRules": rules}}
    labels = {entry["target"]: entry["label"]
              for entry in config["dataAccessPolicies"]}
    if labels != {prop: "OPEN" for prop in PROPERTIES}:
        raise RuntimeError("ACCESS_POLICY_DRIFT")
    materialization = {"policyRef": "policy://ouf-lab/cinema/materialization/1",
        "checkpointInterval": 1, "bitemporalProperties": [],
        "properties": [{"sourceField": prop, "propertyIri": prop,
            "datatype": "http://www.w3.org/2001/XMLSchema#string",
            "accessLabel": labels[prop], "authorityOrder": [SOURCE]}
            for prop in PROPERTIES]}
    proposed["extractionProfile"]["runtime"]["execution"] = execution
    proposed["extractionProfile"]["runtime"]["udp"] = {
        "resolution": resolution, "materialization": materialization}
    digest = hashlib.sha256(json.dumps(proposed, sort_keys=True,
        separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    print("R4A_GOVERNED_PROPOSAL=PLAN READ_ONLY=true")
    print("SOURCE=" + SOURCE + " VERSION=" + VERSION + " LOCK=0")
    print("SEMANTIC_BINDING=" + SEMANTIC + "@1.0.0 REVISION=" + REVISION
          + " PUBLICATION_SET=" + PUBLICATION_SET)
    print("ASSET_BYTES=509 MAPPED_FIELDS=2 CANONICAL_CLASS=" + CLASS)
    print("INGESTION_ADAPTER=managed-tabular-v1 IDENTITY=asset-and-row-ordinal")
    print("MATCHING=all-shared-equal-and-nested DISTINCT=all-shared-different "
          "UNRESOLVED=human-review")
    print("CANDIDATE_LIMIT=100 AUTO_NEW_WHEN_CERTAIN=true "
          "SIGNALS=indirizzo,nome")
    print("PROPOSAL_SHA256=" + digest)
    print("CONFIGURATION_VALUES_AND_SECRET_NOT_PRINTED=true DRAFT_UNCHANGED=true")
    return proposed


if __name__ == "__main__":
    try:
        plan()
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError,
            RuntimeError) as error:
        label = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print("R4A_GOVERNED_PROPOSAL_BLOCKED=" + label + " DRAFT_UNCHANGED=true")
        raise SystemExit(1)
