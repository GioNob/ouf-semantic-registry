"""Read frozen build evidence and context; grants no image acceptance."""
import argparse
import json
import os
from pathlib import Path
import re
import sys

from tools.verify_semantic_configuration_provenance import read, decode, require, sha


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def project(raws, pins, expected):
    payload = expected['payloadHashes']
    require(set(raws) == {'manifest', 'trust', 'image-stage', 'build-intent'} | set(payload))
    require(set(pins) == {'manifest', 'trust'})
    require(all(re.fullmatch('[0-9a-f]{64}', h) and sha(raws[k]) == h for k, h in pins.items()))
    m, t, s, intent = (decode(raws[k]) for k in ('manifest', 'trust', 'image-stage', 'build-intent'))
    require(m['schema'] == 'ouf.semantic-provider-stopped-manifest.v1'
            and m['installation'] == expected['installation'] and m['startAuthorized'] is False)
    require(t['verified'] is True and t['notReleaseAcceptance'] is True)
    require(s['intent'] == intent and intent['schema'] == 'ouf.semantic-provider-image-stage.v1')
    for key in ('sourceCommit', 'sourceURLBase', 'baseImage', 'runtimeUser', 'payloadHashes'):
        require(intent[key] == expected[key])
    require(intent['payloadHash'] == sha(encoded(payload)))
    require(all(sha(raws[k]) == h for k, h in payload.items()))
    require(re.fullmatch('sha256:[0-9a-f]{64}', s['baseImageId']))
    require(s['imageId'] == expected['adapterImage'])
    for key in ('noRuntimeContainersCreated', 'noRouteWrites', 'noIAMWrites',
                'noPolicyPublication', 'notReleaseAcceptance'):
        require(s[key] is True)
    require(type(s['providerCalls']) is int and s['providerCalls'] == 0)
    adapter = t['intent']['adapterImage']; gateway = t['intent']['gateway']
    require(adapter['id'] == s['imageId'] and adapter['sourceCommit'] == intent['sourceCommit']
            and adapter['runtimeUser'] == intent['runtimeUser'] and adapter['payloadHash'] == intent['payloadHash'])
    require(t['intent']['installation'] == expected['installation'])
    require(gateway['id'] == intent['gateway']['id']
            and gateway['image'] == intent['gateway']['image'] == expected['southboundImage']
            and intent['gateway']['version'] == expected['gatewayVersion'])
    require(re.fullmatch('[0-9a-f]{64}', intent['gateway']['configurationHash']))
    candidates = m['containers']
    require(type(candidates) is list and len(candidates) == 2)
    require(sorted(c['image'] for c in candidates) == sorted([s['imageId'], gateway['image']]))
    require(sum(c['image'] == s['imageId'] and c['readOnlyRoot'] is True for c in candidates) == 1
            and sum(c['image'] == gateway['image'] and c['readOnlyRoot'] is False for c in candidates) == 1)
    return {'schema': 'ouf.semantic-image-lineage-readback.v1',
            'inputHashes': {k: sha(raws[k]) for k in sorted(raws)},
            'buildContextFileCount': len(payload), 'buildContextMatchesPinnedSource': True,
            'adapterReceiptBindingsConsistent': True, 'southboundSelectionConsistent': True,
            'historicalEvidenceOnly': True, 'currentTargetInspected': False,
            'imageBytesVerified': False, 'imagePublisherProvenanceVerified': False,
            'dependencySbomVerified': False, 'buildReproduced': False,
            'rootfsSealProven': False, 'generationObserved': False, 'atomicSnapshotProven': False,
            'acceptanceGranted': False, 'startAuthorized': False, 'runtimeRegistered': False,
            'configurationFilesRead': 0, 'privateKeyFilesRead': 0, 'environmentRead': False,
            'providerCalls': 0, 'signaturesIssued': 0, 'targetFilesWritten': 0}


def verify(paths, pins, expected, reader=read):
    require(set(paths) == {'manifest', 'trust', 'image-stage', 'build-intent'} | set(expected['payloadHashes']))
    first = {k: reader(p) for k, p in paths.items()}
    result = project({k: first[k][0] for k in paths}, pins, expected)
    require(first == {k: reader(p) for k, p in paths.items()})
    return result


def main():
    try:
        parser = argparse.ArgumentParser(description=__doc__)
        for name in ('manifest-root', 'trust-root', 'image-stage-root'):
            parser.add_argument('--' + name, type=Path, required=True)
        for name in ('manifest-hash', 'trust-hash', 'installation', 'adapter-image',
                     'southbound-image', 'source-commit', 'source-url-base', 'base-image',
                     'runtime-user', 'gateway-version', 'payload-hashes'):
            parser.add_argument('--' + name, required=True)
        a = parser.parse_args()
        require(os.geteuid() == 0 and sys.flags.isolated and sys.dont_write_bytecode)
        payload = decode(a.payload_hashes.encode())
        require(1 <= len(payload) <= 32 and all(type(k) is str and type(v) is str
                and re.fullmatch('[0-9a-f]{64}', v) and not Path(k).is_absolute()
                and '..' not in Path(k).parts and len(k) <= 256 for k, v in payload.items()))
        paths = {'manifest': a.manifest_root / 'stopped-manifest.json',
                 'trust': a.trust_root / 'trust-receipt.json',
                 'image-stage': a.image_stage_root / 'stage-receipt.json',
                 'build-intent': a.image_stage_root / 'build-intent.json'}
        paths.update({k: a.image_stage_root / 'context' / k for k in payload})
        require(len(set(paths.values())) == len(paths))
        expected = dict(installation=a.installation, adapterImage=a.adapter_image,
                        southboundImage=a.southbound_image, sourceCommit=a.source_commit,
                        sourceURLBase=a.source_url_base, baseImage=a.base_image,
                        runtimeUser=a.runtime_user, gatewayVersion=a.gateway_version, payloadHashes=payload)
        result = verify(paths, {'manifest': a.manifest_hash, 'trust': a.trust_hash}, expected)
        print('SEMANTIC_IMAGE_LINEAGE=' + encoded(result).decode())
        print('SEMANTIC_IMAGE_LINEAGE=PASS HISTORICAL_ONLY=true ACCEPTANCE_GRANTED=false START_AUTHORIZED=false')
        return 0
    except Exception:
        print('SEMANTIC_IMAGE_LINEAGE=BLOCKED REASON=IMAGE_LINEAGE_UNPROVEN NO_SECRETS_PRINTED=true')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
