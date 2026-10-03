#!/usr/bin/env python3
"""Parameterized batch capability registration and unpublished scoped HUMAN draft.

No IAM, routes, publication or business command. Durable intent precedes each
non-idempotent POST; an existing receipt requires reconciliation, never repost.
"""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid


class Blocked(RuntimeError):
    pass


def require(condition, code):
    if not condition:raise Blocked(code)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def private(path, directory=False):
    info=path.lstat()
    require((stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))
            and info.st_uid==os.geteuid() and stat.S_IMODE(info.st_mode)==(0o700 if directory else 0o600),
            'PRIVATE_PATH_REQUIRED')


def write(path, value):
    fd,name=tempfile.mkstemp(prefix='.human-policy-',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as stream:
            json.dump(value,stream,sort_keys=True);stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
        fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)
    finally:
        Path(name).unlink(missing_ok=True)


def reserve(path):
    private(path.parent,True)
    require(not path.exists() and not path.is_symlink(),'STATE_EXISTS_RECONCILE_DO_NOT_REPOST')
    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as stream:
        json.dump({'status':'RESERVED_NO_POST'},stream);stream.flush();os.fsync(stream.fileno())
    write(path,{'status':'RESERVED_NO_POST'})


def text(value):
    return isinstance(value,str) and 0<len(value)<=256 and not any(ord(c)<32 for c in value)


def descriptor(value):
    require(isinstance(value,dict) and set(value)=={'capabilityId','operation','requiredScope','allowedActors'},
            'DESCRIPTOR_INVALID')
    require(all(text(value[k]) for k in ('capabilityId','operation','requiredScope'))
            and value['allowedActors']==['HUMAN'],'HUMAN_DESCRIPTOR_REQUIRED')
    return value


def inputs(args, now=None):
    now=now or datetime.now(timezone.utc)
    manifest=json.loads(args.manifest.read_text())
    require(isinstance(manifest,list) and 0<len(manifest)<=10000,'MANIFEST_INVALID')
    desired={}
    for row in manifest:
        require(isinstance(row,dict) and set(row)=={'ownerRef','descriptor'} and text(row['ownerRef']),
                'MANIFEST_ROW_INVALID')
        cap=descriptor(row['descriptor']);ident=cap['capabilityId']
        require(ident not in desired,'MANIFEST_DUPLICATE');desired[ident]=row
    private(args.resources)
    resources=json.loads(args.resources.read_text())
    require(isinstance(resources,list) and 0<len(resources)<=10000,'RESOURCES_INVALID')
    end=datetime.fromisoformat(args.valid_until.replace('Z','+00:00'))
    require(end.tzinfo is not None and now<end,'GRANT_VALIDITY_INVALID')
    require(text(args.tenant) and text(args.subject),'IDENTITY_BINDING_INVALID')
    grants=[];ids=set()
    for row in resources:
        require(isinstance(row,dict) and set(row)=={'capabilityId','resourceType','resourceId',
                'resourceAttributes','allowedDataLabels'},'RESOURCE_FIELDS_INVALID')
        require(row['capabilityId'] in desired and text(row['resourceType']) and text(row['resourceId']),
                'RESOURCE_BINDING_INVALID')
        attrs=row['resourceAttributes'];labels=row['allowedDataLabels']
        require(isinstance(attrs,dict) and 0<len(attrs)<=64 and all(text(k) and text(v) for k,v in attrs.items()),
                'RESOURCE_ATTRIBUTES_REQUIRED')
        require(isinstance(labels,list) and 0<len(labels)<=64 and all(text(v) for v in labels)
                and len(set(labels))==len(labels),'DATA_LABEL_REQUIRED')
        identity=(row['capabilityId'],row['resourceType'],row['resourceId'])
        require(identity not in ids,'RESOURCE_DUPLICATE');ids.add(identity)
        constraints={'effect':'ALLOW','externalRoleRef':None,'resourceType':row['resourceType'],
            'resourceId':row['resourceId'],'resourceAttributes':attrs,'allowedDataLabels':sorted(labels),
            'allowedDetailLevels':[],'requiredAcr':None,'requiredAmr':[],'maxAuthenticationAgeSeconds':None}
        grants.append({'grantId':'grant-scoped-'+str(uuid.uuid4()),'capabilityId':row['capabilityId'],
            'tenantId':args.tenant,'subjectId':args.subject,'servicePrincipalId':None,'organizationId':None,
            'validFrom':now.isoformat().replace('+00:00','Z'),'validUntil':end.isoformat().replace('+00:00','Z'),
            'constraints':constraints})
    require({g['capabilityId'] for g in grants}==set(desired),'EVERY_CAPABILITY_REQUIRES_SCOPED_GRANT')
    return desired,grants


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None


def https(url):
    value=urllib.parse.urlsplit(url)
    require(value.scheme=='https' and value.hostname and not value.username and not value.password
            and not value.query and not value.fragment,'HTTPS_BINDING_REQUIRED')
    return value


def http(url,token=None,method='GET',body=None,form=None,etag=None):
    headers={'Accept':'application/json'}
    if token:headers['Authorization']='Bearer '+token
    data=None
    if body is not None:data=json.dumps(body,separators=(',',':')).encode();headers['Content-Type']='application/json'
    if form is not None:data=urllib.parse.urlencode(form).encode();headers['Content-Type']='application/x-www-form-urlencoded'
    if etag is not None:headers['If-Match']='"'+str(etag)+'"'
    req=urllib.request.Request(url,data=data,method=method,headers=headers)
    try:
        with urllib.request.build_opener(NoRedirect()).open(req,timeout=30) as response:
            raw=response.read(8_000_001);require(len(raw)<=8_000_000,'HTTP_RESPONSE_LIMIT')
            return response.status,json.loads(raw) if raw else None,response.headers
    except urllib.error.HTTPError as error:
        if form is not None:
            raw=error.read(65537);require(len(raw)<=65536,'OIDC_RESPONSE_LIMIT')
            try:value=json.loads(raw)
            except (ValueError,UnicodeError):value={}
            return error.code,{'error':value.get('error')},{}
        raise Blocked('HTTP_'+str(error.code)) from None


def login(args):
    issuer=args.issuer.rstrip('/');origin=https(issuer)
    _,meta,_=http(issuer+'/.well-known/openid-configuration')
    require(meta.get('issuer')==issuer,'OIDC_ISSUER_MISMATCH')
    device,endpoint=meta.get('device_authorization_endpoint'),meta.get('token_endpoint')
    for url in (device,endpoint):
        require(isinstance(url,str) and url.startswith(issuer+'/'),'OIDC_ENDPOINT_MISMATCH');https(url)
    status,start,_=http(device,method='POST',form={'client_id':args.client,'scope':'openid '+args.admin_scope})
    require(status==200 and all(start.get(k) for k in ('device_code','user_code','verification_uri','expires_in')),
            'DEVICE_AUTHORIZATION_FAILED')
    uri=https(start['verification_uri'])
    require((uri.scheme,uri.netloc)==(origin.scheme,origin.netloc),'DEVICE_VERIFICATION_ORIGIN_MISMATCH')
    print('OPEN_IN_BROWSER='+start['verification_uri'],flush=True)
    print('ENTER_DEVICE_CODE='+str(start['user_code']),flush=True)
    print('Non incollare codice o token in chat.',flush=True)
    interval=max(5,min(30,int(start.get('interval',5))));deadline=time.monotonic()+min(600,int(start['expires_in']))
    while time.monotonic()<deadline:
        time.sleep(interval)
        status,result,_=http(endpoint,method='POST',form={'client_id':args.client,'device_code':start['device_code'],
            'grant_type':'urn:ietf:params:oauth:grant-type:device_code'})
        if status==200:
            token=result.get('access_token');require(isinstance(token,str) and len(token)<=16384 and token.count('.')==2,
                                                  'TOKEN_FORMAT_INVALID')
            part=token.split('.')[1];claims=json.loads(base64.urlsafe_b64decode(part+'='*(-len(part)%4)))
            aud=claims.get('aud',[]);aud=[aud] if isinstance(aud,str) else aud
            require(claims.get('iss')==issuer and claims.get('azp')==args.client and claims.get('sub')==args.subject
                and claims.get('tenant_id')==args.tenant and claims.get('ouf_actor_type') in ('HUMAN','HUMAN_USER')
                and args.audience in aud and args.admin_scope in str(claims.get('scope','')).split()
                and isinstance(claims.get('exp'),int) and claims['exp']>time.time()+60,'HUMAN_IDENTITY_SCOPE_MISMATCH')
            # Backend verifies signature and authorization; decoded claims are defensive diagnostics only.
            return token
        if result.get('error')=='slow_down':interval=min(30,interval+5)
        elif result.get('error')!='authorization_pending':raise Blocked('DEVICE_LOGIN_NOT_COMPLETED')
    raise Blocked('DEVICE_LOGIN_EXPIRED')


def catalogue(base,token):
    result={}
    for offset in range(0,100001,200):
        status,rows,_=http(base+'/capabilities?limit=200&offset='+str(offset),token)
        require(status==200 and isinstance(rows,list) and len(rows)<=200,'CATALOGUE_PAGE_INVALID')
        for row in rows:
            ident=row.get('capability_id');require(text(ident) and ident not in result,'CATALOGUE_DUPLICATE')
            result[ident]=row
        if len(rows)<200:return result
    raise Blocked('CATALOGUE_LIMIT')


def check_registered(row,wanted):
    value=row.get('descriptor')
    if isinstance(value,dict) and value.get('type')=='jsonb':value=value.get('value')
    if isinstance(value,str):value=json.loads(value)
    if isinstance(value,dict) and isinstance(value.get('allowedActors'),list):value={**value,'allowedActors':sorted(value['allowedActors'])}
    require(row.get('owner_ref')==wanted['ownerRef'] and value==wanted['descriptor'],'CATALOGUE_SEMANTIC_CONFLICT')


def active(base,token):
    status,value,_=http(base+'/policies/active',token)
    require(status==200 and isinstance(value,dict) and text(value.get('policyRef')),'ACTIVE_VIEW_INVALID')
    return value


def candidate(current,desired,grants):
    old=current['policy'];require(set(old)=={'bundleId','version','publishedAt','capabilities','grants'},'ACTIVE_POLICY_SHAPE_UNSUPPORTED')
    require(isinstance(old['version'],int) and old['version']>0 and isinstance(old['capabilities'],list)
            and isinstance(old['grants'],list),'ACTIVE_POLICY_INVALID')
    existing={c['capabilityId']:c for c in old['capabilities']}
    require(len(existing)==len(old['capabilities']),'ACTIVE_CAPABILITY_DUPLICATE')
    missing=[]
    for ident,row in desired.items():
        if ident in existing:
            value=existing[ident];require({**value,'allowedActors':sorted(value['allowedActors'])}==row['descriptor'],
                                         'ACTIVE_DESCRIPTOR_CONFLICT')
        else:missing.append(row['descriptor'])
    require(not any(g.get('capabilityId') in desired for g in old['grants']),'ACTIVE_GRANTS_EXIST_RECONCILE')
    require(not ({g['grantId'] for g in old['grants']}&{g['grantId'] for g in grants}),'GRANT_ID_CONFLICT')
    return {**old,'version':old['version']+1,'publishedAt':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
            'capabilities':old['capabilities']+missing,'grants':old['grants']+grants},missing


def preview_check(preview,missing,grants):
    require(sorted(preview.get('addedCapabilities',[]),key=lambda x:x['capabilityId'])==sorted(missing,key=lambda x:x['capabilityId'])
        and not preview.get('removedCapabilities'),'PREVIEW_CAPABILITY_DIFF_MISMATCH')
    changes=preview.get('grantChanges',[])
    expected={g['grantId']:g for g in grants}
    actual={g['grantId']:g.get('after') for g in changes}
    require(len(changes)==len(expected) and actual==expected and all(g.get('before') is None for g in changes),
            'PREVIEW_GRANT_DIFF_MISMATCH')


def prepare(args):
    https(args.issuer);https(args.base_url)
    desired,grants=inputs(args)
    if args.validate_only:
        print('SCOPED_HUMAN_POLICY_INPUT=PASS CAPABILITIES='+str(len(desired))+' GRANTS='+str(len(grants))+' NO_NETWORK_OR_WRITES=true');return
    os.umask(0o077);reserve(args.state_file)
    state={'status':'LOGIN_PENDING_NO_POST'};write(args.state_file,state)
    token=login(args);base=args.base_url.rstrip('/');current=active(base,token)
    target,missing=candidate(current,desired,grants);registered=catalogue(base,token)
    for ident,wanted in desired.items():
        if ident in registered:check_registered(registered[ident],wanted)
    state.update(status='VALIDATED_NO_POST',baseActive=current,candidate=target,addedDescriptors=missing,
                 addedGrants=grants,registeredCapabilities=[],tenant=args.tenant,subject=args.subject)
    write(args.state_file,state)
    for ident,wanted in desired.items():
        if ident in registered:continue
        require(active(base,token)==current,'ACTIVE_DRIFT_BEFORE_REGISTRATION')
        state.update(status='REGISTRATION_POST_UNVERIFIED_DO_NOT_REPOST',pendingCapability=ident);write(args.state_file,state)
        status,_,_=http(base+'/capabilities',token,'POST',wanted);require(status==201,'REGISTRATION_RESPONSE_UNVERIFIED')
        state['registeredCapabilities'].append(ident);state['status']='REGISTRATION_ACCEPTED';write(args.state_file,state)
    registered=catalogue(base,token)
    for ident,wanted in desired.items():check_registered(registered.get(ident,{}),wanted)
    require(active(base,token)==current,'ACTIVE_DRIFT_BEFORE_DRAFT')
    state['status']='DRAFT_POST_UNVERIFIED_DO_NOT_REPOST';write(args.state_file,state)
    status,draft,headers=http(base+'/policies',token,'POST',target)
    etag=headers.get('ETag','').strip('"');require(status==200 and etag.isdigit(),'DRAFT_RESPONSE_UNVERIFIED')
    state.update(draftId=str(uuid.UUID(draft['id'])),revision=int(etag),status='DRAFT_READBACK_PENDING');write(args.state_file,state)
    require(draft.get('baseActiveRef')==current['policyRef'] and draft.get('state')=='DRAFT','DRAFT_BASE_OR_STATE_DRIFT')
    status,readback,headers=http(base+'/policies/'+state['draftId'],token)
    require(status==200 and headers.get('ETag','').strip('"')==etag and readback.get('policy')==target
            and readback.get('baseActiveRef')==current['policyRef'] and readback.get('state')=='DRAFT',
            'DRAFT_READBACK_MISMATCH')
    _,preview,_=http(base+'/policies/'+state['draftId']+':preview',token,'POST',etag=state['revision'])
    require(preview.get('baseActiveRef')==current['policyRef'] and preview.get('draftId')==state['draftId']
            and preview.get('revision')==state['revision'],'PREVIEW_BASE_OR_REVISION_DRIFT')
    preview_check(preview,missing,grants)
    require(active(base,token)==current,'ACTIVE_DRIFT_AFTER_DRAFT')
    state.update(status='PASS_UNPUBLISHED',preview=preview,baselineHash=digest(current));write(args.state_file,state)
    print('R4A_SCOPED_HUMAN_POLICY_DRAFT=PASS BASE='+current['policyRef']+' DRAFT_ID='+state['draftId']+' REVISION='+etag)
    print('CAPABILITIES='+str(len(desired))+' SCOPED_GRANTS='+str(len(grants))+' EXISTING_ENTRIES_PRESERVED=true ACTIVE_UNCHANGED=true')
    print('R4A_SCOPED_HUMAN_POLICY_RECEIPT='+str(args.state_file)+' PRIVATE=true')
    print('POLICY_UNPUBLISHED=true PREVIEW_AUTHORIZATION_PROOF=false IAM_UNCHANGED=true ROUTES_UNCHANGED=true RETRY=false SECRETS_NOT_PRINTED=true')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('issuer','client','audience','admin-scope','base-url','tenant','subject','valid-until'):p.add_argument('--'+name,required=True)
    for name in ('manifest','resources','state-file'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--validate-only',action='store_true')
    try:prepare(p.parse_args())
    except Exception as error:
        code=str(error) if isinstance(error,Blocked) else 'UNCLASSIFIED'
        print('R4A_SCOPED_HUMAN_POLICY_DRAFT=BLOCKED CODE='+code+' TYPE='+type(error).__name__+' RECONCILE_IF_RECEIPT_EXISTS=true RETRY=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
