#!/usr/bin/env python3
"""Prepare/plan/apply the staged Semantic-only RDF read candidate, retaining its predecessor."""
import argparse
import copy
import fcntl
import json
import os
from pathlib import Path
import re
import sys
import zipfile
from types import SimpleNamespace
import r4a_release_semantic_consultation as release
stage=release.stage
prep=release.prep
require=release.require
PIN='e7bc5190f9e6afbbc4cf3c90d5d4970afbfad14b'
IMAGE='sha256:f6525f2512c72a600ebcbc7060d55355d86e0627487b655e7c5c6288a0be7fc6'
ROOT=Path('/etc/ouf/deploy-snapshots')


def migration_bytes(path):
    with zipfile.ZipFile(path) as jar:
        names=[n for n in jar.namelist() if n.startswith('BOOT-INF/classes/db/migration/') and n.endswith('.sql')]
        require(bool(names),'PACKAGED_MIGRATIONS_EMPTY')
        return {n:jar.read(n) for n in names}


def unchanged(before,semantic=True):
    for name,row in before['live'].items():
        if name=='ouf-semantic' and not semantic:continue
        require(stage.fingerprint(stage.inspect(name))==stage.fingerprint(row),'LIVE_CHANGED_SINCE_STAGE')
    require(stage.routes(before['gatewayConfig'],stage.inspect('ouf-apisix'))==before['routes'],'ROUTES_CHANGED_SINCE_STAGE')


def load(root):
    require(root.parent==ROOT,'STAGE_PARENT_INVALID');prep.private(root,0o700)
    for name in ('runtime-snapshot.json','image-receipt.json'):prep.private(root/name,0o600)
    before=json.loads((root/'runtime-snapshot.json').read_text())
    receipt=json.loads((root/'image-receipt.json').read_text())
    require(receipt.get('status')=='PASS' and receipt.get('liveUnchanged') is True
        and receipt.get('noContainersCreated') is True,'STAGE_NOT_PASS')
    require(receipt.get('commit')==PIN and receipt.get('image')==IMAGE,'CANDIDATE_PIN_INVALID')
    require(receipt['oldId']==before['live']['ouf-semantic']['Id'],'ORIGINAL_ID_DRIFT')
    source=root/'semantic'
    require(stage.run(['git','-C',str(source),'rev-parse','HEAD'])==PIN
        and not stage.run(['git','-C',str(source),'status','--porcelain']),'PINNED_SOURCE_DRIFT')
    image=stage.inspect(IMAGE)
    require((image['Config'].get('Labels') or {}).get('org.opencontainers.image.revision')==PIN,'IMAGE_REVISION_DRIFT')
    prep.launch_guard(before['live']['ouf-semantic'],image)
    unchanged(before)
    return before,image


def prepare(root,before,image):
    folder=root/'rdf-prepared';folder.mkdir(mode=0o700,exist_ok=False)
    old=before['live']['ouf-semantic'];name='ouf-semantic-rdf-read-candidate-'+PIN[:12]
    existing=stage.run(['docker','container','ls','--all','--format','{{.Names}}']).splitlines()
    require(name not in existing,'CANDIDATE_NAME_OCCUPIED')
    state={'status':'PREPARING','candidateName':name}
    stage.save(folder/'prepare-receipt.json',state)
    environment=prep.env(old);mounts=copy.deepcopy(old['Mounts'])
    prep.write(folder/'semantic.env',''.join(k+'='+v+'\n' for k,v in environment.items()))
    argv=prep.command(old,image,name,folder/'semantic.env',mounts,PIN)
    unchanged(before)
    state['createAttempted']=True;prep.checkpoint(folder/'prepare-receipt.json',state)
    ident=stage.run(argv,60)
    state['candidate']={'id':ident,'name':name,'image':IMAGE};prep.checkpoint(folder/'prepare-receipt.json',state)
    for network in old['NetworkSettings']['Networks']:
        if network==old['HostConfig']['NetworkMode']:continue
        connect=['docker','network','connect']
        for alias in prep.aliases(old,network):connect+=['--alias',alias]
        stage.run(connect+[network,ident],60)
    prep.matches(stage.inspect(ident),old,image,environment,mounts)
    for jar,container in [('old.jar',old['Id']),('new.jar',ident)]:
        stage.run(['docker','cp',container+':/app/application.jar',str(folder/jar)],60)
    require(migration_bytes(folder/'old.jar')==migration_bytes(folder/'new.jar'),'PACKAGED_MIGRATIONS_CHANGED')
    unchanged(before)
    state.update(status='PASS',environment=environment,mounts=mounts,packagedMigrationsIdentical=True)
    prep.checkpoint(folder/'prepare-receipt.json',state)
    print('SEMANTIC_RDF_READ_PREPARE=PASS CANDIDATES=1 STOPPED=true MOUNTS='+str(len(mounts))+
        ' ENVIRONMENT_UNCHANGED=true PACKAGED_MIGRATIONS_IDENTICAL=true LIVE_UNCHANGED=true ROUTES_UNCHANGED=true',flush=True)


def planned(root,before,image,pgname):
    folder=root/'rdf-prepared';prep.private(folder,0o700);prep.private(folder/'prepare-receipt.json',0o600)
    prepared=json.loads((folder/'prepare-receipt.json').read_text())
    require(prepared.get('status')=='PASS' and prepared.get('packagedMigrationsIdentical') is True,'PREPARE_NOT_PASS')
    old=before['live']['ouf-semantic'];candidate=prepared['candidate']
    require(candidate['image']==IMAGE and candidate['name']=='ouf-semantic-rdf-read-candidate-'+PIN[:12],'PREPARED_PIN_INVALID')
    require(prepared['environment']==prep.env(old) and prepared['mounts']==old['Mounts'],'PREPARED_RUNTIME_DRIFT')
    prep.matches(stage.inspect(candidate['id']),old,image,prepared['environment'],prepared['mounts'])
    for jar,container in [('check-old.jar',old['Id']),('check-new.jar',candidate['id'])]:
        stage.run(['docker','cp',container+':/app/application.jar',str(folder/jar)],60)
    require(migration_bytes(folder/'check-old.jar')==migration_bytes(folder/'check-new.jar'),'PACKAGED_MIGRATIONS_CHANGED')
    pg,user,dbs=release.databases(SimpleNamespace(postgres_container=pgname),
        {'semantic':old,'mcp':before['live']['ouf-mcp']})
    history=release.history(pgname,user,dbs['semantic'],'semantic')
    require(bool(history) and all(row.get('success') is True for row in history),'MIGRATION_HISTORY_NOT_GREEN')
    require(not (root/'rdf-release-receipt.json').exists(),'RELEASE_STATE_EXISTS_RECONCILE')
    names=stage.run(['docker','container','ls','--all','--format','{{.Names}}']).splitlines()
    backup='ouf-semantic-rdf-read-rollback-'+old['Id'][:12]
    failed='ouf-semantic-rdf-read-failed-'+candidate['id'][:12]
    require(backup not in names and failed not in names,'RETAINED_NAME_OCCUPIED')
    unchanged(before)
    print('SEMANTIC_RDF_READ_PLAN=PASS CONTAINERS=1 OTHER_SERVICES_AND_ROUTES_UNCHANGED=true',flush=True)
    return prepared,pg,user,dbs['semantic'],history,backup,failed


def verify_new(before,prepared,image):
    old=before['live']['ouf-semantic'];candidate=prepared['candidate'];row=stage.inspect(candidate['id'])
    require(row['Name']==old['Name'] and row['State']['Running'],'NEW_CONTAINER_NAME_STATE_DRIFT')
    require(not stage.inspect(old['Id'])['State']['Running'],'ORIGINAL_STILL_RUNNING')
    view=copy.deepcopy(row);view['State']={'Status':'created','Running':False};view['HostConfig']['RestartPolicy']['Name']='no'
    prep.matches(view,old,image,prepared['environment'],prepared['mounts'])
    release.ready(candidate['id'],'http://127.0.0.1:8080','/actuator/health/readiness',200)
    for name,cap in [('search','ouf.semantic.search'),('get','ouf.semantic.consultation.read')]:
        body=release.probe_body(name,'READ',cap)
        require(release.http_code(candidate['id'],'http://127.0.0.1:8080','POST',
            '/internal/capabilities/v1/execute/semantic/'+name,body) in (401,403),'FORGED_DIRECT_REQUEST_NOT_DENIED')
        route=next(r for r in before['routes'] if r.get('uri')=='/internal/capabilities/v1/execute/semantic/'+name)
        headers={'Content-Type':'application/json'};host=route.get('host') or (route.get('hosts') or [None])[0]
        if host:headers['Host']=host.replace('*','probe')
        require(release.http_code('ouf-apisix','http://127.0.0.1:9080','POST',
            '/internal/capabilities/v1/execute/semantic/'+name,body,headers) in (401,403),'ANONYMOUS_GATEWAY_REQUEST_NOT_DENIED')
    unchanged(before,semantic=False)


def apply(root,before,image,prepared,pg,user,database,history,backup,failed,pgname):
    old=before['live']['ouf-semantic'];candidate=prepared['candidate'];path=root/'rdf-release-receipt.json'
    state={'status':'STARTING','commit':PIN,'image':IMAGE,'oldId':old['Id'],'candidate':candidate,
        'switchAttempted':[],'rollbackNames':{'semantic':backup},'history':history,'postgresId':pg['Id']}
    stage.save(path,state)
    try:
        state['backup']=release.backup(pgname,user,database,root/'semantic-before-rdf-read.dump');prep.checkpoint(path,state)
        print('SEMANTIC_RDF_READ_BACKUP=PASS TOC_VERIFIED=true PRIVATE=true',flush=True)
        require(release.history(pgname,user,database,'semantic')==history,'MIGRATION_CHANGED_BEFORE_SWITCH')
        unchanged(before)
        state['status']='SWITCH_ATTEMPTED';prep.checkpoint(path,state)
        release.switch('semantic',old,candidate,state,path)
        verify_new(before,prepared,image)
        require(release.history(pgname,user,database,'semantic')==history,'MIGRATION_CHANGED_AFTER_SWITCH')
        stage.run(['docker','update','--restart',old['HostConfig']['RestartPolicy']['Name'],candidate['id']])
        require(stage.inspect(candidate['id'])['HostConfig']['RestartPolicy']==old['HostConfig']['RestartPolicy'],'RESTART_POLICY_DRIFT')
        state.update(status='PASS',newId=candidate['id'],retainedOriginal=backup);prep.checkpoint(path,state)
    except BaseException:
        if state['switchAttempted']:
            state['status']='ROLLBACK_ATTEMPTED'
            # A full disk or lost checkpoint must not prevent restoring the predecessor.
            try:prep.checkpoint(path,state)
            except OSError:pass
            try:
                release.restore_container(old,candidate,failed)
                release.ready(old['Id'],'http://127.0.0.1:8080','/actuator/health/readiness',200)
                state['status']='SEMANTIC_RESTORED_RECONCILIATION_REQUIRED'
                print('SEMANTIC_RDF_READ_ORIGINAL_RESTORED=PASS DO_NOT_RERUN_BLINDLY=true',flush=True)
            except BaseException:
                state['status']='ROLLBACK_INCOMPLETE_RECONCILIATION_REQUIRED'
        else:state['status']='PRE_SWITCH_FAILED_LIVE_NOT_SWITCHED'
        prep.checkpoint(path,state)
        raise
    print('SEMANTIC_RDF_READ_RELEASE=PASS CONTAINERS=1 ENVIRONMENT_UNCHANGED=true OTHER_SERVICES_UNCHANGED=true ROUTES_UNCHANGED=true MIGRATION_HISTORY_UNCHANGED=true NO_POLICY_PUBLICATION=true NO_SOURCE_RUN=true RDF_POSITIVE_HUMAN_NOT_PROVEN=true',flush=True)
    print('SEMANTIC_RDF_READ_RETAINED_ORIGINAL='+backup,flush=True)
    print('SEMANTIC_RDF_READ_RELEASE_RECEIPT='+str(path)+' PRIVATE=true',flush=True)


def main(args):
    require(os.geteuid()==0,'ROOT_REQUIRED');os.umask(0o077)
    require(args.stage_root.parent==ROOT,'STAGE_PARENT_INVALID');prep.private(args.stage_root,0o700)
    fd=os.open(args.stage_root/'rdf-operation.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        before,image=load(args.stage_root)
        if args.mode=='prepare':prepare(args.stage_root,before,image);return
        values=planned(args.stage_root,before,image,args.postgres_container)
        if args.mode=='apply':apply(args.stage_root,before,image,*values,args.postgres_container)
    finally:os.close(fd)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('prepare','plan','apply'))
    p.add_argument('--stage-root',type=Path,required=True)
    p.add_argument('--postgres-container',required=True)
    try:main(p.parse_args())
    except BaseException as error:
        if isinstance(error,SystemExit) and error.code==0:raise
        code=str(error) if isinstance(error,RuntimeError) and re.fullmatch('[A-Z_]{1,80}',str(error)) else type(error).__name__
        print('SEMANTIC_RDF_READ_RELEASE=BLOCKED CODE='+code+' DO_NOT_RERUN_BLINDLY=true NO_SECRETS_PRINTED=true',flush=True)
        sys.exit(1)
