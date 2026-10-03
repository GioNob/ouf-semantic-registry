#!/usr/bin/env python3
"""Stage one pinned Semantic image; preserve all live containers and Gateway routes."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import r4a_stage_semantic_consultation as stage
import r4a_prepare_semantic_consultation as prep

PIN = 'e7bc5190f9e6afbbc4cf3c90d5d4970afbfad14b'
LIVE_PIN = '025a542bfe6c76d8c45ee5af668b7cb7bb0de0d6'
NAMES = ('ouf-semantic','ouf-mcp','ouf-apisix','ouf-onboarding','ouf-ingestion','ouf-udp')
ROOT = Path('/etc/ouf/deploy-snapshots')


def main(args):
    prep.require(os.geteuid()==0,'ROOT_REQUIRED')
    os.umask(0o077)
    root=args.stage_root
    prep.require(root.parent==ROOT,'STAGE_PARENT_INVALID')
    prep.private(root.parent,0o700)
    previous=args.consultation_stage_root/'runtime-snapshot.json'
    prep.private(previous.parent,0o700);prep.private(previous,0o600)
    gateway=json.loads(previous.read_text())['config']['gateway']
    baseline={name:stage.inspect(name) for name in NAMES}
    stage.guard(baseline['ouf-semantic'],LIVE_PIN)
    prep.require(all(row['State']['Running'] for row in baseline.values()),'OWNER_NOT_RUNNING')
    routes=stage.routes(gateway,baseline['ouf-apisix'])
    root.mkdir(mode=0o700,exist_ok=False)
    stage.save(root/'runtime-snapshot.json',{'live':baseline,'gatewayConfig':gateway,'routes':routes})
    source=root/'semantic'
    stage.run(['git','clone','--no-checkout','https://github.com/GioNob/ouf-semantic-registry.git',str(source)],180)
    stage.run(['git','-C',str(source),'fetch','--no-tags','origin',PIN],180)
    stage.run(['git','-C',str(source),'checkout','--detach',PIN],60)
    prep.require(stage.run(['git','-C',str(source),'rev-parse','HEAD'])==PIN,'SOURCE_PIN_DRIFT')
    tag='ouf-semantic:rdf-read-'+PIN[:12]
    print('SEMANTIC_RDF_READ_BUILD_STARTED=true COMMIT='+PIN,flush=True)
    with (root/'semantic-build.log').open('x') as log:
        result=subprocess.run(['docker','build','--label','org.opencontainers.image.revision='+PIN,
            '-t',tag,str(source)],stdout=log,stderr=subprocess.STDOUT,timeout=2400)
    prep.require(result.returncode==0,'BUILD_FAILED_PRIVATE_LOG')
    image=stage.inspect(tag)
    prep.require((image['Config'].get('Labels') or {}).get('org.opencontainers.image.revision')==PIN,'IMAGE_PIN_DRIFT')
    prep.launch_guard(baseline['ouf-semantic'],image)
    for name,row in baseline.items():
        prep.require(stage.fingerprint(stage.inspect(name))==stage.fingerprint(row),'LIVE_CHANGED_DURING_STAGE')
    prep.require(stage.routes(gateway,stage.inspect('ouf-apisix'))==routes,'ROUTES_CHANGED_DURING_STAGE')
    stage.save(root/'image-receipt.json',{'status':'PASS','commit':PIN,'image':image['Id'],'tag':tag,
        'oldId':baseline['ouf-semantic']['Id'],'liveUnchanged':True,'noContainersCreated':True})
    print('SEMANTIC_RDF_READ_IMAGE='+json.dumps({'commit':PIN,'image':image['Id'],'tag':tag},sort_keys=True),flush=True)
    print('SEMANTIC_RDF_READ_STAGE=PASS LIVE_UNCHANGED=true ROUTES_UNCHANGED=true NO_SWITCH=true NO_CONTAINERS_CREATED=true NO_SOURCE_RUN=true PRIVATE_ROOT='+str(root),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage-root',type=Path,required=True)
    p.add_argument('--consultation-stage-root',type=Path,required=True)
    try:main(p.parse_args())
    except BaseException as error:
        if isinstance(error,SystemExit) and error.code==0:raise
        code=str(error) if isinstance(error,RuntimeError) and re.fullmatch('[A-Z_]{1,80}',str(error)) else type(error).__name__
        print('SEMANTIC_RDF_READ_STAGE=BLOCKED CODE='+code+' NO_SECRETS_PRINTED=true',flush=True)
        sys.exit(1)
