#!/usr/bin/env python3
"""Stage a pinned MCP-only image using existing MCP snapshot/prepare/rollout helpers."""
import argparse
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import r4a_stage_semantic_consultation as stage


def require(value,code):
    if not value:raise RuntimeError(code)


def upload_options(entries):
    env=dict(e.split('=',1) for e in entries)
    require(len(env)==len(entries),'DUPLICATE_ENVIRONMENT')
    value=env.get('MCP_MANAGED_UPLOAD_ENABLED')
    mode={None:'off','probe':'probe','true':'enabled','picker':'picker'}.get(value)
    require(mode is not None,'UPLOAD_MODE_UNSUPPORTED')
    options={'upload_mode':mode,'host_origin':None,'picker_url':env.get('MCP_MANAGED_FILE_PICKER_URL') if mode=='picker' else None}
    return options


def main(args):
    require(os.geteuid()==0,'ROOT_REQUIRED');os.umask(0o077)
    for value in (args.commit,args.expected_live_revision):require(bool(re.fullmatch('[0-9a-f]{40}',value)),'PIN_INVALID')
    require(args.stage_root.is_absolute(),'ABSOLUTE_STAGE_ROOT_REQUIRED')
    root=args.stage_root;root.mkdir(mode=0o700,exist_ok=False)
    old=stage.inspect('ouf-mcp');stage.guard(old,args.expected_live_revision)
    others={name:stage.inspect(name) for name in ('ouf-semantic','ouf-apisix','ouf-onboarding','ouf-ingestion','ouf-udp')}
    require(all(r['State']['Running'] for r in others.values()),'EXISTING_SERVICE_NOT_RUNNING')
    stage.save(root/'runtime-snapshot.json',{'mcp':old,'others':others})
    source=root/'mcp';tag='ouf-mcp:semantic-byte-fix-'+args.commit[:12]
    stage.run(['git','clone','--no-checkout','https://github.com/GioNob/ouf-mcp-server',str(source)],180)
    stage.run(['git','-C',str(source),'fetch','--no-tags','origin',args.commit],180)
    stage.run(['git','-C',str(source),'checkout','--detach',args.commit],60)
    require(stage.run(['git','-C',str(source),'rev-parse','HEAD'])==args.commit,'SOURCE_PIN_DRIFT')
    print('MCP_BYTE_FIX_BUILD_STARTED=true COMMIT='+args.commit,flush=True)
    with (root/'mcp-build.log').open('x') as log:
        result=subprocess.run(['docker','build','--label','org.opencontainers.image.revision='+args.commit,'-t',tag,str(source)],stdout=log,stderr=subprocess.STDOUT,timeout=2400)
    require(result.returncode==0,'IMAGE_BUILD_FAILED_PRIVATE_LOG')
    image=stage.inspect(tag)
    require((image['Config'].get('Labels') or {}).get('org.opencontainers.image.revision')==args.commit,'IMAGE_PIN_DRIFT')
    sys.path.insert(0,str(source))
    snapshotter=importlib.import_module('scripts.r4a_snapshot_mcp_runtime')
    preflight=importlib.import_module('scripts.r4a_preflight_mcp_runtime')
    prepare=importlib.import_module('scripts.r4a_prepare_mcp_candidate')
    rollout=importlib.import_module('scripts.r4a_rollout_mcp_runtime')
    environment=importlib.import_module('scripts.r4a_managed_upload_mode')
    options=upload_options(old['Config']['Env'])
    require(sorted(environment.expected_environment(old['Config']['Env'],**{'mode':options['upload_mode'],'origin':options['host_origin'],'picker_url':options['picker_url']}))==sorted(old['Config']['Env']),'ENVIRONMENT_OVERLAY_WOULD_CHANGE_LIVE')
    snapshot=snapshotter.snapshot(root)
    preflight.safe_summary(preflight.read_private_snapshot(snapshot),stage.inspect('ouf-mcp'))
    candidate=prepare.prepare(snapshot,tag,image['Id'],**options)
    saved,_,expected=rollout.original_and_args(snapshot,candidate,tag,image['Id'],**options)
    require(stage.fingerprint(saved)==stage.fingerprint(old) and sorted(expected)==sorted(old['Config']['Env']),'MCP_CANDIDATE_BINDING_DRIFT')
    require(stage.fingerprint(stage.inspect('ouf-mcp'))==stage.fingerprint(old),'MCP_LIVE_CHANGED')
    for name,row in others.items():require(stage.fingerprint(stage.inspect(name))==stage.fingerprint(row),'OTHER_LIVE_CHANGED')
    receipt={'status':'PASS','commit':args.commit,'image':image['Id'],'tag':tag,'snapshot':str(snapshot),'candidate':str(candidate),
             'options':options,'oldId':old['Id'],'expectedLiveRevision':args.expected_live_revision,
             'backupName':'ouf-mcp-r4a-rollback-'+old['Id'][:12],'liveUnchanged':True,'noContainersCreated':True}
    stage.save(root/'stage-receipt.json',receipt)
    print('MCP_BYTE_FIX_IMAGE='+json.dumps({'commit':args.commit,'image':image['Id'],'tag':tag}),flush=True)
    print('MCP_BYTE_FIX_STAGE=PASS LIVE_UNCHANGED=true ENVIRONMENT_UNCHANGED=true NO_CONTAINERS_CREATED=true NO_SOURCE_RUN=true PRIVATE_ROOT='+str(root),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage-root',type=Path,required=True)
    p.add_argument('--commit',required=True)
    p.add_argument('--expected-live-revision',required=True)
    try:main(p.parse_args())
    except Exception as error:
        code=str(error) if isinstance(error,RuntimeError) and re.fullmatch('[A-Z_]{1,80}',str(error)) else type(error).__name__
        print('MCP_BYTE_FIX_STAGE=BLOCKED CODE='+code+' NO_SWITCH=true DO_NOT_RERUN_BLINDLY=true NO_SECRETS_PRINTED=true',flush=True)
        sys.exit(1)
