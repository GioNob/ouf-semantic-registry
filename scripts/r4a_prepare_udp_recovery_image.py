#!/usr/bin/env python3
"""Build an isolated UDP image; never start, switch or modify the live service."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import uuid
from urllib.parse import urlsplit


def execute(argv, log, cwd=None, timeout=60):
    result=subprocess.run(argv,cwd=cwd,stdout=subprocess.PIPE,stderr=log,
                          text=True,timeout=timeout,check=True)
    return result.stdout.strip()


def live_state(args,log):
    row=json.loads(execute(['docker','inspect',args.container],log))[0]
    if not row['State']['Running']:raise ValueError('LIVE_NOT_RUNNING')
    if row['Image']!=args.expected_live_image:raise ValueError('LIVE_IMAGE_CHANGED')
    user=row['Config'].get('User','')
    if not re.fullmatch(r'[1-9][0-9]*:[1-9][0-9]*',user):raise ValueError('LIVE_USER_INVALID')
    return {key:value for key,value in (
        ('id',row['Id']),('image',row['Image']),('user',user),
        ('started_at',row['State']['StartedAt']),('restart_count',row['RestartCount']))}


def migrations(source,revision,log):
    names=execute(['git','ls-tree','-r','--name-only',revision,'src/main/resources/db/migration'],log,source)
    result={}
    for name in names.splitlines():
        # Hash exact git blob bytes, not text stripped by execute().
        data=subprocess.run(['git','show',revision+':'+name],cwd=source,
                            stdout=subprocess.PIPE,stderr=log,check=True,timeout=30).stdout
        result[name]=hashlib.sha256(data).hexdigest()
    if not result:raise ValueError('MIGRATIONS_ABSENT')
    return result


def validate(args):
    parsed=urlsplit(args.repository)
    if (parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or any(c.isspace() for c in args.repository)):
        raise ValueError('PUBLIC_HTTPS_REPOSITORY_REQUIRED')
    for revision in (args.revision,args.baseline_revision):
        if not re.fullmatch('[a-f0-9]{40}',revision):raise ValueError('REVISION_INVALID')
    if not re.fullmatch('sha256:[a-f0-9]{64}',args.expected_live_image):raise ValueError('LIVE_IMAGE_INVALID')
    if not re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,159}',args.container):raise ValueError('CONTAINER_INVALID')
    if not re.fullmatch('[a-z0-9][a-z0-9._/-]{0,180}',args.image_repository):raise ValueError('LOCAL_IMAGE_REPOSITORY_INVALID')
    parent=Path(args.work_parent)
    if not parent.is_absolute() or parent.is_symlink() or not parent.is_dir():raise ValueError('WORK_PARENT_REQUIRED')
    if parent.stat().st_uid!=0 or parent.stat().st_mode&0o022:raise ValueError('ROOT_OWNED_WORK_PARENT_REQUIRED')


def main(args):
    if os.geteuid()!=0:raise ValueError('ROOT_REQUIRED')
    validate(args)
    os.umask(0o077)
    root=Path(tempfile.mkdtemp(prefix='udp-recovery-image-',dir=args.work_parent))
    receipt=root/'receipt.json';source=root/'source';logpath=root/'build.log'
    tag=args.image_repository+':r4a-'+args.revision[:12]+'-'+uuid.uuid4().hex[:12]
    evidence={'state':'PREPARING','revision':args.revision,'baseline_revision':args.baseline_revision,
              'image_tag':tag,'service_switched':False,'spring_started':False,'probe_executed':False}
    print('R4A_UDP_RECOVERY_IMAGE_RECEIPT='+str(receipt)+' PRIVATE=true',flush=True)
    def save():receipt.write_text(json.dumps(evidence,sort_keys=True,indent=2)+'\n')
    save()
    with logpath.open('x') as log:
        try:
            before=live_state(args,log);evidence['live_before']=before;save()
            execute(['git','init',str(source)],log)
            execute(['git','remote','add','origin',args.repository],log,source)
            for revision in (args.revision,args.baseline_revision):
                execute(['git','fetch','--no-tags','--depth','1','origin',revision],log,source,180)
            execute(['git','checkout','--detach',args.revision],log,source)
            if execute(['git','rev-parse','HEAD'],log,source)!=args.revision:raise ValueError('CHECKOUT_MISMATCH')
            candidate=migrations(source,args.revision,log)
            if candidate!=migrations(source,args.baseline_revision,log):raise ValueError('MIGRATION_SET_CHANGED')
            evidence['migration_count']=len(candidate);evidence['migration_hashes']=candidate;save()
            print('R4A_UDP_RECOVERY_IMAGE_BUILD=START REVISION='+args.revision,flush=True)
            # Source-only build context. No live env, secrets, mounts or Docker socket are injected into build.
            subprocess.run(['docker','build','--label','org.opencontainers.image.revision='+args.revision,
                '--tag',tag,str(source)],stdout=log,stderr=log,check=True,timeout=1800)
            image=json.loads(execute(['docker','image','inspect',tag],log))[0]
            if (image['Config'].get('Labels') or {}).get('org.opencontainers.image.revision')!=args.revision:
                raise ValueError('IMAGE_REVISION_MISMATCH')
            if image['Config'].get('User')!=before['user']:raise ValueError('IMAGE_USER_MISMATCH')
            if not re.fullmatch('sha256:[a-f0-9]{64}',image['Id']):raise ValueError('IMAGE_ID_INVALID')
            if live_state(args,log)!=before:raise ValueError('LIVE_CHANGED_DURING_BUILD')
            evidence.update(state='BUILT',image_id=image['Id'],live_identity_unchanged=True);save()
            print('UDP_RECOVERY_CANDIDATE_IMAGE_ID='+image['Id'],flush=True)
            print('UDP_RECOVERY_CANDIDATE_IMAGE_TAG='+tag,flush=True)
            print('R4A_UDP_RECOVERY_IMAGE_BUILD=PASS MIGRATIONS_IDENTICAL=true LIVE_IDENTITY_UNCHANGED=true DEPLOY=false RETRY=false PROBE_EXECUTED=false SECRETS_NOT_PRINTED=true',flush=True)
            return image['Id']
        except BaseException as error:
            evidence.update(state='BLOCKED',failure_type=type(error).__name__);save()
            raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('repository','revision','baseline-revision','container','expected-live-image','image-repository','work-parent'):
        parser.add_argument('--'+name,required=True)
    try:main(parser.parse_args())
    except Exception as error:
        print('R4A_UDP_RECOVERY_IMAGE_BUILD=BLOCKED TYPE='+type(error).__name__+' DEPLOY=false RETRY=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
