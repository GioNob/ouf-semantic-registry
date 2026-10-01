#!/usr/bin/env python3
"""Review existing scoped HUMAN draft; governed terminal publication; no business retry."""
import argparse
import copy
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import uuid
import r4a_prepare_scoped_human_policy as api

def moment(value):
    return datetime.fromisoformat(value.replace('Z','+00:00'))

def validate(args,state,resources,now=None):
    now=now or datetime.now(timezone.utc)
    api.require(state.get('status')=='PASS_UNPUBLISHED' and state.get('tenant')==args.tenant
        and state.get('subject')==args.subject,'DRAFT_RECEIPT_IDENTITY_OR_STATUS')
    base=state['baseActive'];target=state['candidate'];grants=state['addedGrants']
    api.require(api.digest(base)==state['baselineHash'],'BASELINE_HASH_MISMATCH')
    api.require(str(uuid.UUID(state['draftId']))==state['draftId'] and isinstance(state['revision'],int)
        and state['revision']>=0,'DRAFT_IDENTITY_INVALID')
    old=base['policy'];desc={'capabilityId':args.capability,'operation':args.operation,
        'requiredScope':args.required_scope,'allowedActors':['HUMAN']}
    api.descriptor(desc)
    existing=[v for v in old['capabilities'] if v['capabilityId']==args.capability]
    api.require(existing in ([],[desc]) and not any(g['capabilityId']==args.capability for g in old['grants']),
        'BASELINE_CAPABILITY_OR_GRANTS_CONFLICT')
    added=[] if existing else [desc]
    api.require(set(target)==set(old) and state['addedDescriptors']==added and target['bundleId']==old['bundleId']
        and target['version']==old['version']+1 and target['capabilities']==old['capabilities']+added
        and target['grants']==old['grants']+grants,'CANDIDATE_DIFF_NOT_EXACT')
    api.require(len(resources)==args.expected_resources and len(grants)==len(resources)
        and len({g['grantId'] for g in grants})==len(grants),'SCOPED_RESOURCE_COUNT_MISMATCH')
    expected={}
    for resource in resources:
        api.require(set(resource)=={'capabilityId','resourceType','resourceId','resourceAttributes','allowedDataLabels'}
            and resource['capabilityId']==args.capability and api.text(resource['resourceId'])
            and api.text(resource['resourceType']) and resource['resourceAttributes']
            and all(api.text(k) and api.text(v) for k,v in resource['resourceAttributes'].items())
            and resource['allowedDataLabels'] and all(api.text(v) for v in resource['allowedDataLabels']),
            'RESOURCE_MANIFEST_INVALID')
        key=(resource['resourceType'],resource['resourceId'])
        api.require(key not in expected,'RESOURCE_DUPLICATE');expected[key]=resource
    seen=set()
    for grant in grants:
        constraint=grant['constraints'];key=(constraint['resourceType'],constraint['resourceId'])
        api.require(key in expected and key not in seen,'GRANT_RESOURCE_NOT_EXACT');seen.add(key)
        resource=expected[key]
        exact={'effect':'ALLOW','externalRoleRef':None,'resourceType':resource['resourceType'],
            'resourceId':resource['resourceId'],'resourceAttributes':resource['resourceAttributes'],
            'allowedDataLabels':sorted(resource['allowedDataLabels']),'allowedDetailLevels':[],
            'requiredAcr':None,'requiredAmr':[],'maxAuthenticationAgeSeconds':None}
        api.require(grant['capabilityId']==args.capability and grant['tenantId']==args.tenant
            and grant['subjectId']==args.subject and grant['servicePrincipalId'] is None
            and grant['organizationId'] is None and constraint==exact,'GRANT_SCOPE_WIDENED')
        api.require(moment(grant['validUntil'])>moment(grant['validFrom']),'GRANT_VALIDITY_INVALID')
        if args.mode!='verify':
            api.require(moment(grant['validFrom'])<=now and
                (moment(grant['validUntil'])-now).total_seconds()>=args.min_remaining_seconds,'GRANT_EXPIRY_TOO_CLOSE')
    return desc

def snapshot(args,token,state):
    base=args.base_url.rstrip('/');current=api.active(base,token)
    api.require(current==state['baseActive'],'ACTIVE_DRIFT_REBASE_REQUIRED')
    status,draft,headers=api.http(base+'/policies/'+state['draftId'],token)
    api.require(status==200 and headers.get('ETag','').strip('"')==str(state['revision'])
        and draft.get('id')==state['draftId'] and draft.get('revision')==state['revision']
        and draft.get('baseActiveRef')==current['policyRef'] and draft.get('state')=='DRAFT'
        and draft.get('policy')==state['candidate'],'DRAFT_READBACK_DRIFT')
    registered=api.catalogue(base,token)
    desc={'capabilityId':args.capability,'operation':args.operation,'requiredScope':args.required_scope,'allowedActors':['HUMAN']}
    api.check_registered(registered.get(args.capability,{}),{'ownerRef':args.owner,'descriptor':desc})
    return draft

def scenarios(args,resources):
    cases=[]
    foreign='outside-'+str(uuid.uuid4())
    for index,resource in enumerate(resources,1):
        principal={'subjectId':args.subject,'tenantId':args.tenant,'actorType':'HUMAN','servicePrincipalId':None,
            'authenticationContextRef':'hypothetical-review','issuer':args.issuer,'audience':args.audience,
            'scopes':[args.required_scope],'claims':None}
        for label in sorted(set(resource['allowedDataLabels'])):
            scenario={'hypotheticalPrincipal':copy.deepcopy(principal),'resource':{
                'resourceType':resource['resourceType'],'resourceId':resource['resourceId'],'tenantId':args.tenant,
                'organizationId':None,'attributes':{**resource['resourceAttributes'],'dataAccessLabel':label}},
                'capabilityId':args.capability,'operation':args.operation}
            cases.append(('ALLOW_RESOURCE_'+str(index),scenario,True,None))
        original=copy.deepcopy(cases[-1][1])
        def negative(name,mutate,code=None):
            value=copy.deepcopy(original);mutate(value);cases.append((name+'_'+str(index),value,False,code))
        negative('SERVICE',lambda v:v['hypotheticalPrincipal'].update(actorType='SERVICE',servicePrincipalId=foreign),'ACTOR_NOT_ALLOWED')
        negative('AI',lambda v:v['hypotheticalPrincipal'].update(actorType='AI_AGENT'),'ACTOR_NOT_ALLOWED')
        negative('MISSING_SCOPE',lambda v:v['hypotheticalPrincipal'].update(scopes=[]),'SCOPE_MISSING')
        negative('OTHER_SUBJECT',lambda v:v['hypotheticalPrincipal'].update(subjectId=foreign),'NO_APPLICABLE_GRANT')
        negative('OTHER_RESOURCE',lambda v:v['resource'].update(resourceId=foreign),'NO_APPLICABLE_GRANT')
        negative('OTHER_TYPE',lambda v:v['resource'].update(resourceType=foreign),'NO_APPLICABLE_GRANT')
        for key in resource['resourceAttributes']:
            negative('ATTR_'+str(len(cases)),lambda v,k=key:v['resource']['attributes'].update({k:foreign}),'NO_APPLICABLE_GRANT')
        negative('OTHER_LABEL',lambda v:v['resource']['attributes'].update(dataAccessLabel=foreign),'NO_APPLICABLE_GRANT')
        negative('MISSING_LABEL',lambda v:v['resource']['attributes'].pop('dataAccessLabel'),'NO_APPLICABLE_GRANT')
    original=copy.deepcopy(cases[0][1])
    for field in ('hypotheticalPrincipal','resource'):
        value=copy.deepcopy(original);value[field]['tenantId']=foreign
        cases.append(('FOREIGN_TENANT_'+field,value,False,'HTTP_403'))
    return cases

def review(args,token,state,resources,evidence):
    validate(args,state,resources);snapshot(args,token,state)
    path=args.base_url.rstrip('/')+'/policies/'+state['draftId']
    status,preview,_=api.http(path+':preview',token,'POST',etag=state['revision'])
    api.require(status==200 and preview.get('draftId')==state['draftId']
        and preview.get('revision')==state['revision'] and preview.get('baseActiveRef')==state['baseActive']['policyRef']
        and preview.get('authoritative') is False and api.text(preview.get('activeHash'))
        and api.text(preview.get('draftHash')) and preview['activeHash']!=preview['draftHash'],'PREVIEW_CONTEXT_MISMATCH')
    api.preview_check(preview,state['addedDescriptors'],state['addedGrants'])
    evidence['preview']=preview;evidence['simulations']=[];api.write(args.receipt,evidence)
    for name,body,allow,code in scenarios(args,resources):
        try:
            status,result,_=api.http(path+':simulate',token,'POST',body,etag=state['revision'])
        except api.Blocked as error:
            api.require(code=='HTTP_403' and str(error)=='HTTP_403','SIMULATION_UNEXPECTED_HTTP')
            evidence['simulations'].append({'name':name,'guardDenied':True,'http':403})
        else:
            api.require(code!='HTTP_403' and status==200 and result.get('draftId')==state['draftId']
                and result.get('revision')==state['revision'] and result.get('baseActiveRef')==state['baseActive']['policyRef']
                and result.get('activeHash')==preview.get('activeHash') and result.get('draftHash')==preview.get('draftHash')
                and result.get('contextSource')=='HYPOTHETICAL_NOT_IAM_VERIFIED' and result.get('authoritative') is False
                and result.get('before',{}).get('allowed') is False and result.get('after',{}).get('allowed') is allow
                and result['after'].get('code')==('ALLOW' if allow else code),'SIMULATION_RESULT_MISMATCH')
            evidence['simulations'].append({'name':name,'result':result})
        api.write(args.receipt,evidence)
    snapshot(args,token,state);validate(args,state,resources)
    evidence['status']='REVIEWED_NOT_PUBLISHED';api.write(args.receipt,evidence)
    print('R4A_SCOPED_HUMAN_POLICY_REVIEW=PASS SCOPED_RESOURCES='+str(len(resources))
        +' SCENARIOS='+str(len(evidence['simulations']))+' BEFORE_DENIED=true EXPECTED_AFTER_RESULTS=true ACTIVE_UNCHANGED=true',flush=True)
    print('SIMULATION_AUTHORITATIVE=false HUMAN_OWNER_AUTHORIZATION_NOT_PROVEN=true RETRY=false',flush=True)

def semantic(policy):
    return {k:v for k,v in policy.items() if k!='publishedAt'}

def publication_readback(args,token,state,evidence):
    base=args.base_url.rstrip('/');status,draft,headers=api.http(base+'/policies/'+state['draftId'],token)
    active=api.active(base,token);target=state['candidate']
    ref=target['bundleId']+':'+str(target['version'])
    api.require(status==200 and draft.get('id')==state['draftId'] and draft.get('state')=='PUBLISHED'
        and draft.get('revision')==state['revision']+1 and headers.get('ETag','').strip('"')==str(state['revision']+1)
        and draft.get('baseActiveRef')==state['baseActive']['policyRef'] and draft.get('policy')==target
        and active.get('policyRef')==ref and semantic(active['policy'])==semantic(target),'PUBLICATION_READBACK_UNVERIFIED')
    api.require(moment(active['policy']['publishedAt']).tzinfo is not None,'ACTIVE_PUBLISHED_AT_INVALID')
    evidence.update(status='PASS_PUBLISHED',activeReadback=active,publishedDraft=draft);api.write(args.receipt,evidence)
    print('R4A_SCOPED_HUMAN_POLICY_PUBLICATION=PASS ACTIVE='+ref+' REVISION='+str(state['revision']+1)
        +' EXACT_SCOPED_DIFF=true PUBLICATION_READBACK=true RETRY=false HUMAN_OWNER_AUTHORIZATION_NOT_PROVEN=true SECRETS_NOT_PRINTED=true',flush=True)

def confirm(ref):
    phrase='PUBBLICO '+ref
    print('Per pubblicare questa bozza, digitare nel terminale: '+phrase,flush=True)
    with open('/dev/tty','r+') as terminal:
        terminal.write('CONFERMA HUMAN> ');terminal.flush()
        api.require(terminal.readline().strip()==phrase,'HUMAN_CONFIRMATION_NOT_MATCHED')

def execute(args):
    api.require(os.geteuid()==0,'ROOT_REQUIRED');os.umask(0o077)
    api.https(args.base_url);api.https(args.issuer)
    api.private(args.draft_receipt);api.private(args.resources);api.private(args.receipt.parent,True)
    state=json.loads(args.draft_receipt.read_text());resources=json.loads(args.resources.read_text())
    api.require(args.expected_resources>0 and args.min_remaining_seconds>=60,'BOUND_REQUIRED')
    desc=validate(args,state,resources)
    if args.mode=='verify':
        api.private(args.receipt);evidence=json.loads(args.receipt.read_text())
        api.require(evidence.get('draftReceiptHash')==api.digest(state)
            and evidence.get('resourcesHash')==api.digest(resources)
            and evidence.get('status') in ('PUBLISH_POST_UNVERIFIED_DO_NOT_REPOST','PASS_PUBLISHED'),
            'NO_PUBLICATION_INTENT_RECONCILE')
        token=api.login(args);publication_readback(args,token,state,evidence);return
    api.reserve(args.receipt)
    evidence={'status':'LOGIN_PENDING_NO_PUBLISH','draftReceiptHash':api.digest(state),
        'resourcesHash':api.digest(resources),'mode':args.mode};api.write(args.receipt,evidence)
    token=api.login(args);review(args,token,state,resources,evidence)
    print('R4A_SCOPED_POLICY_REVIEW_RECEIPT='+str(args.receipt)+' PRIVATE=true',flush=True)
    if args.mode=='review':
        print('POLICY_PUBLISH_NOT_CALLED=true RETRY=false SECRETS_NOT_PRINTED=true');return
    ref=state['candidate']['bundleId']+':'+str(state['candidate']['version'])
    print('PUBBLICAZIONE PROPOSTA: '+state['baseActive']['policyRef']+' -> '+ref
        +' CAPABILITY='+desc['capabilityId']+' GRANTS='+str(len(resources))
        +' ACTOR=HUMAN NOMINAL_SUBJECT=true EXACT_RESOURCES_AND_DATA_LABELS=true',flush=True)
    confirm(ref)
    validate(args,state,resources);snapshot(args,token,state)
    evidence['status']='PUBLISH_POST_UNVERIFIED_DO_NOT_REPOST';api.write(args.receipt,evidence)
    status,draft,_=api.http(args.base_url.rstrip('/')+'/policies/'+state['draftId']+':publish',
        token,'POST',etag=state['revision'])
    api.require(status==200 and draft.get('state')=='PUBLISHED','PUBLICATION_RESPONSE_UNVERIFIED')
    publication_readback(args,token,state,evidence)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('review','publish','verify'))
    for name in ('issuer','client','audience','admin-scope','base-url','tenant','subject','capability','operation','required-scope','owner'):
        p.add_argument('--'+name,required=True)
    for name in ('draft-receipt','resources','receipt'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--expected-resources',type=int,required=True)
    p.add_argument('--min-remaining-seconds',type=int,required=True)
    try:execute(p.parse_args())
    except Exception as error:
        code=str(error) if isinstance(error,api.Blocked) else 'UNCLASSIFIED'
        print('R4A_SCOPED_HUMAN_POLICY_REVIEW_OR_PUBLISH=BLOCKED CODE='+code+' TYPE='+type(error).__name__
            +' RECONCILE_RECEIPT_DO_NOT_REPOST=true RETRY=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
