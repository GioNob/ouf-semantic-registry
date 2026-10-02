#!/usr/bin/env python3
"""Register one HUMAN read contract, preview its exact policy delta, publish only after terminal confirmation."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import sys
from urllib.parse import urlsplit
import r4a_authorization_lifecycle as policy
from r4a_probe_semantic_human_mcp import human_login

CAP='ouf.semantic.consultation.read'
DESCRIPTOR={'capabilityId':CAP,'operation':'READ','requiredScope':'ouf.semantic.read','allowedActors':['HUMAN']}
OLD='grant-semantic-read-human-admin'
NEW='grant-semantic-consultation-read-human-admin'


def normalized(row):return {k:v for k,v in row.items() if v is not None}


def structure(bundle):
    caps={c['capabilityId']:policy.normalize_descriptor(c) for c in bundle['capabilities']}
    grants={g['grantId']:normalized(g) for g in bundle['grants']}
    if len(caps)!=len(bundle['capabilities']) or len(grants)!=len(bundle['grants']):
        raise ValueError('DUPLICATE_POLICY_ENTRY')
    return {'capabilities':caps,'grants':grants}


def candidate(active,subject,tenant):
    current=active['policy'];indexed=structure(current)
    native=indexed['capabilities'].get('ouf.semantic.read')
    if native!={'capabilityId':'ouf.semantic.read','operation':'READ','requiredScope':'ouf.semantic.read','allowedActors':['SERVICE']}:
        raise ValueError('NATIVE_SERVICE_READ_CONTRACT_CHANGED')
    template=indexed['grants'].get('grant-semantic-search-human-admin')
    if not template or template.get('subjectId')!=subject or template.get('tenantId')!=tenant or template.get('servicePrincipalId') or template.get('organizationId') or template.get('constraints'):
        raise ValueError('HUMAN_SEARCH_TEMPLATE_CONFLICT')
    now=datetime.now(timezone.utc)
    start=datetime.fromisoformat(template['validFrom'].replace('Z','+00:00'))
    end=datetime.fromisoformat(template['validUntil'].replace('Z','+00:00'))
    if start.tzinfo is None or end.tzinfo is None or not start<=now<end:
        raise ValueError('HUMAN_SEARCH_TEMPLATE_NOT_CURRENT')
    old=indexed['grants'].get(OLD)
    expected_old={**template,'grantId':OLD,'capabilityId':'ouf.semantic.read'}
    if old is not None and old!=expected_old:raise ValueError('OLD_HUMAN_READ_GRANT_CONFLICT')
    desired={**template,'grantId':NEW,'capabilityId':CAP}
    existing=indexed['grants'].get(NEW)
    if existing is not None and existing!=desired:raise ValueError('HUMAN_READ_GRANT_CONFLICT')
    if any(g.get('capabilityId')==CAP and g['grantId']!=NEW and g.get('subjectId')==subject for g in current['grants']):
        raise ValueError('EQUIVALENT_GRANT_REQUIRES_REVIEW')
    result,missing=policy.build_candidate(active,[DESCRIPTOR])
    result['grants']=[g for g in result['grants'] if g['grantId']!=OLD]
    changes=[]
    if old is not None:changes.append({'grantId':OLD,'before':old,'after':None})
    if existing is None:
        result['grants'].append(desired);changes.append({'grantId':NEW,'before':None,'after':desired})
    return result,missing,changes


def validate_preview(preview,added,changes):
    actual={policy.normalize_descriptor(c)['capabilityId']:policy.normalize_descriptor(c) for c in preview['addedCapabilities']}
    expected={d['capabilityId']:policy.normalize_descriptor(d) for d in added}
    if actual!=expected or len(actual)!=len(preview['addedCapabilities']) or preview['removedCapabilities']:raise ValueError('PREVIEW_CAPABILITY_DRIFT')
    clean=lambda rows:{r['grantId']:{'before':normalized(r['before']) if r.get('before') is not None else None,
        'after':normalized(r['after']) if r.get('after') is not None else None} for r in rows}
    if clean(preview['grantChanges'])!=clean(changes) or len(preview['grantChanges'])!=len(changes):
        raise ValueError('PREVIEW_GRANT_DRIFT')


def catalogue(base,token):
    found=None
    for offset in range(0,100001,200):
        _,rows,_=policy.request(base,token,'/capabilities?limit=200&offset='+str(offset))
        if not isinstance(rows,list) or len(rows)>200:raise ValueError('CATALOGUE_PAGE_INVALID')
        for row in rows:
            if row.get('capability_id')!=CAP:continue
            if found is not None:raise ValueError('CATALOGUE_DUPLICATE')
            descriptor=row['descriptor']
            if isinstance(descriptor,dict) and descriptor.get('type')=='jsonb':descriptor=descriptor['value']
            if isinstance(descriptor,str):descriptor=json.loads(descriptor)
            if row.get('owner_ref')!='semantic' or policy.normalize_descriptor(descriptor)!=DESCRIPTOR:
                raise ValueError('CATALOGUE_HUMAN_READ_CONFLICT')
            found=row
        if len(rows)<200:return found is not None
    raise ValueError('CATALOGUE_PAGINATION_LIMIT')


def state_file(path):
    if path is None or not path.is_absolute():raise ValueError('ABSOLUTE_STATE_FILE_REQUIRED')
    parent=path.parent.lstat()
    if path.parent.is_symlink() or not stat.S_ISDIR(parent.st_mode) or parent.st_uid!=os.geteuid() or stat.S_IMODE(parent.st_mode)!=0o700:
        raise ValueError('PRIVATE_STATE_DIRECTORY_REQUIRED')


def verify(active,state):
    if active['policyRef']!=state['targetPolicyRef'] or policy.digest(structure(active['policy']))!=state['expectedStructureHash']:
        raise ValueError('ACTIVE_POLICY_DELTA_MISMATCH')


def publish(args,token,state):
    active=policy.active(args.base_url,token)
    if active['policyRef']==state['targetPolicyRef']:
        verify(active,state)
        state['status']='PUBLISHED';policy.write_state(args.state_file,state);return
    if active['policyRef']!=state['basePolicyRef']:raise ValueError('ACTIVE_CHANGED_REVIEW_NEW_DRAFT')
    _,preview,_=policy.request(args.base_url,token,'/policies/'+state['draftId']+':preview','POST',etag=state['revision'])
    if preview.get('draftId')!=state['draftId'] or preview.get('revision')!=state['revision'] or preview.get('baseActiveRef')!=state['basePolicyRef']:
        raise ValueError('OWNER_PREVIEW_CONTEXT_MISMATCH')
    validate_preview(preview,state['addedDescriptors'],state['expectedGrantChanges'])
    print('OWNER_PREVIEW=PASS SERVICE_CONTRACTS_AND_GRANTS_PRESERVED=true',flush=True)
    print('POLICY_DELTA='+json.dumps({'base':state['basePolicyRef'],'target':state['targetPolicyRef'],
        'addedDescriptors':state['addedDescriptors'],'grantChanges':state['expectedGrantChanges']},sort_keys=True),flush=True)
    phrase='PUBBLICA LETTURA SEMANTICA HUMAN'
    if input('Per confermare questo delta digita '+phrase+': ').strip()!=phrase:
        raise ValueError('HUMAN_PUBLICATION_NOT_CONFIRMED_DRAFT_RETAINED')
    state['status']='PUBLICATION_ATTEMPTED';policy.write_state(args.state_file,state)
    try:
        _,result,_=policy.request(args.base_url,token,'/policies/'+state['draftId']+':publish','POST',etag=state['revision'])
        if result.get('state')!='PUBLISHED':raise ValueError('PUBLICATION_NOT_PUBLISHED')
    except Exception:
        verify(policy.active(args.base_url,token),state)
    verify(policy.active(args.base_url,token),state)
    state['status']='PUBLISHED';policy.write_state(args.state_file,state)


def main(args):
    for value in (args.issuer,args.base_url):
        u=urlsplit(value)
        if u.scheme!='https' or not u.hostname or u.username or u.password or u.query or u.fragment:
            raise ValueError('HTTPS_ENDPOINT_REQUIRED')
    if args.mode!='plan':state_file(args.state_file)
    if args.mode=='apply' and args.state_file.exists():raise ValueError('STATE_EXISTS_RECONCILE_NOT_REPEAT')
    token=human_login(args,{'authorization.policy.admin'})
    active=policy.active(args.base_url,token)
    if args.mode in ('publish','verify'):
        state=policy.read_state(args.state_file)
        if args.mode=='publish':publish(args,token,state)
        else:verify(active,state)
    else:
        proposed,added,changes=candidate(active,args.subject,args.tenant)
        registered=catalogue(args.base_url,token)
        print('HUMAN_READ_POLICY_PLAN='+json.dumps({'basePolicyRef':active['policyRef'],
            'registrationMissing':not registered,'addedDescriptors':added,'grantChanges':changes},sort_keys=True),flush=True)
        if args.mode=='plan':print('NO_WRITES=true');return
        if not added and not changes:print('HUMAN_READ_POLICY_ALREADY_ACTIVE=true');return
        state={'status':'PREPARING','basePolicyRef':active['policyRef'],
            'targetPolicyRef':proposed['bundleId']+':'+str(proposed['version']),
            'addedDescriptors':added,'expectedGrantChanges':changes,'expectedStructureHash':policy.digest(structure(proposed))}
        policy.write_state(args.state_file,state)
        if not registered:
            state['status']='REGISTRATION_ATTEMPTED';policy.write_state(args.state_file,state)
            try:policy.request(args.base_url,token,'/capabilities','POST',{'ownerRef':'semantic','descriptor':DESCRIPTOR})
            except Exception:
                if not catalogue(args.base_url,token):raise
            if not catalogue(args.base_url,token):raise ValueError('REGISTRATION_NOT_VERIFIED')
        state['status']='DRAFT_CREATE_ATTEMPTED';policy.write_state(args.state_file,state)
        _,draft,headers=policy.request(args.base_url,token,'/policies','POST',proposed)
        revision=headers.get('ETag','').strip('"')
        if not revision.isdigit():raise ValueError('DRAFT_REVISION_INVALID')
        state.update(draftId=draft['id'],revision=int(revision),status='DRAFT_PREPARED')
        policy.write_state(args.state_file,state)
        publish(args,token,state)
    print('SEMANTIC_HUMAN_READ_POLICY=PASS POLICY_REF='+state['targetPolicyRef']+' NO_SOURCE_RUN=true NO_SECRETS_PRINTED=true',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('plan','apply','publish','verify'))
    for name in ('issuer','base-url','client','subject','tenant','audience'):p.add_argument('--'+name,required=True)
    p.add_argument('--state-file',type=Path)
    try:main(p.parse_args())
    except Exception as error:
        code=str(error).split(':',1)[0] if isinstance(error,(ValueError,RuntimeError)) else type(error).__name__
        print('SEMANTIC_HUMAN_READ_POLICY=BLOCKED REASON='+code+' RECONCILE_PRIVATE_STATE_BEFORE_RETRY=true',flush=True)
        sys.exit(1)
