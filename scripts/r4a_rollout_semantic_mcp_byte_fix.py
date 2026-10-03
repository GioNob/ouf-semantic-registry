#!/usr/bin/env python3
"""Coordinate existing MCP-only rollout, private DB backup and unchanged-owner checks."""
import argparse
import importlib
import json
import os
from pathlib import Path
import re
import sys
from types import SimpleNamespace
import r4a_release_semantic_consultation as release
stage=release.stage
prep=release.prep
require=release.require


def launcher_arguments(receipt,apply=False):
    options=receipt['options']
    args=['r4a_rollout_mcp_runtime.py','--snapshot',receipt['snapshot'],'--candidate',receipt['candidate'],
          '--image',receipt['tag'],'--image-id',receipt['image'],'--backup-name',receipt['backupName'],
          '--upload-mode',options['upload_mode']]
    if options['host_origin'] is not None:args+=['--host-origin',options['host_origin']]
    if options['picker_url'] is not None:args+=['--picker-url',options['picker_url']]
    if apply:args+=['--apply']
    return args


def main(args):
    require(os.geteuid()==0,'ROOT_REQUIRED');os.umask(0o077)
    root=args.stage_root;prep.private(root,0o700)
    for name in ('stage-receipt.json','runtime-snapshot.json'):prep.private(root/name,0o600)
    receipt=json.loads((root/'stage-receipt.json').read_text());before=json.loads((root/'runtime-snapshot.json').read_text())
    require(receipt['status']=='PASS' and receipt['liveUnchanged'] is True and receipt['noContainersCreated'] is True,'STAGE_NOT_PASS')
    source=root/'mcp'
    require(stage.run(['git','-C',str(source),'rev-parse','HEAD'])==receipt['commit']
            and not stage.run(['git','-C',str(source),'status','--porcelain']),'PINNED_MCP_SOURCE_DRIFT')
    require(receipt['oldId']==before['mcp']['Id'],'OLD_ID_RECEIPT_DRIFT')
    for row in [before['mcp'],*before['others'].values()]:require(stage.fingerprint(stage.inspect(row['Id']))==stage.fingerprint(row),'LIVE_CHANGED_SINCE_STAGE')
    image=stage.inspect(receipt['image'])
    require((image['Config'].get('Labels') or {}).get('org.opencontainers.image.revision')==receipt['commit'],'IMAGE_PIN_DRIFT')
    for value in ('snapshot','candidate'):require(Path(receipt[value]).is_relative_to(root),'PRIVATE_CANDIDATE_OUTSIDE_STAGE')
    sys.path.insert(0,str(source));launcher=importlib.import_module('scripts.r4a_rollout_mcp_runtime')
    _,_,environment=launcher.original_and_args(Path(receipt['snapshot']),Path(receipt['candidate']),receipt['tag'],receipt['image'],**receipt['options'])
    require(sorted(environment)==sorted(before['mcp']['Config']['Env']),'ENVIRONMENT_CHANGE_NOT_ALLOWED')
    previous=args.consultation_stage_root/'runtime-snapshot.json';prep.private(previous.parent,0o700);prep.private(previous,0o600)
    gateway_config=json.loads(previous.read_text())['config']['gateway']
    routes=stage.routes(gateway_config,before['others']['ouf-apisix'])
    old={'mcp':before['mcp'],'semantic':before['others']['ouf-semantic']}
    pg,user,databases=release.databases(SimpleNamespace(postgres_container=args.postgres_container),old)
    history=release.history(args.postgres_container,user,databases['mcp'],'mcp');require(bool(history),'MCP_MIGRATION_HISTORY_EMPTY')
    state_path=root/'rollout-byte-fix-receipt.json'
    require(not state_path.exists(),'ROLLOUT_STATE_EXISTS_RECONCILE')
    original_argv=sys.argv
    try:
        sys.argv=launcher_arguments(receipt);launcher.main()
    finally:sys.argv=original_argv
    print('MCP_BYTE_FIX_PLAN=PASS OTHER_SERVICES_AND_ROUTES_UNCHANGED=true',flush=True)
    if args.mode=='plan':return
    state={'status':'STARTING','oldId':receipt['oldId'],'image':receipt['image'],'commit':receipt['commit'],'history':history,'postgresId':pg['Id']}
    stage.save(state_path,state)
    try:
        state['backup']=release.backup(args.postgres_container,user,databases['mcp'],root/'mcp-before-byte-fix.dump')
        prep.checkpoint(state_path,state)
        print('MCP_BYTE_FIX_BACKUP=PASS TOC_VERIFIED=true PRIVATE=true',flush=True)
        require(release.history(args.postgres_container,user,databases['mcp'],'mcp')==history,'MIGRATION_CHANGED_BEFORE_SWITCH')
        state['status']='SWITCH_ATTEMPTED';prep.checkpoint(state_path,state)
        try:
            sys.argv=launcher_arguments(receipt,True);launcher.main()
        finally:sys.argv=original_argv
        current=stage.inspect('ouf-mcp');stage.guard(current,receipt['commit'])
        require(current['Image']==receipt['image'],'LIVE_IMAGE_DRIFT')
        release.ready(current['Id'],'http://127.0.0.1:8080','/health/ready',204)
        require(release.history(args.postgres_container,user,databases['mcp'],'mcp')==history,'MIGRATION_CHANGED_AFTER_SWITCH')
        for row in before['others'].values():require(stage.fingerprint(stage.inspect(row['Id']))==stage.fingerprint(row),'OTHER_SERVICE_CHANGED')
        require(stage.routes(gateway_config,before['others']['ouf-apisix'])==routes,'GATEWAY_ROUTES_CHANGED')
        state.update(status='PASS',newId=current['Id'],backupContainer=receipt['backupName']);prep.checkpoint(state_path,state)
    except BaseException:
        state['status']='RECONCILIATION_REQUIRED';prep.checkpoint(state_path,state)
        raise
    print('MCP_BYTE_FIX_RELEASE=PASS CONTAINERS=1 ENVIRONMENT_UNCHANGED=true OTHER_SERVICES_UNCHANGED=true ROUTES_UNCHANGED=true MIGRATION_HISTORY_UNCHANGED=true NO_POLICY_PUBLICATION=true NO_SOURCE_RUN=true POSITIVE_HUMAN_NOT_PROVEN=true',flush=True)
    print('MCP_BYTE_FIX_RELEASE_RECEIPT='+str(state_path)+' PRIVATE=true',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('plan','apply'))
    p.add_argument('--stage-root',type=Path,required=True)
    p.add_argument('--consultation-stage-root',type=Path,required=True)
    p.add_argument('--postgres-container',required=True)
    try:main(p.parse_args())
    except BaseException as error:
        if isinstance(error,SystemExit) and error.code==0:raise
        code=str(error) if isinstance(error,RuntimeError) and re.fullmatch('[A-Z_]{1,80}',str(error)) else type(error).__name__
        print('MCP_BYTE_FIX_RELEASE=BLOCKED CODE='+code+' DO_NOT_RERUN_BLINDLY=true NO_SECRETS_PRINTED=true',flush=True)
        sys.exit(1)
