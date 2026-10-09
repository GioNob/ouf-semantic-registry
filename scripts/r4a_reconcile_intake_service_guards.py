#!/usr/bin/env python3
"""Replace owned cloned preflight Lua; prove lake admission without storing content."""
import argparse
import copy
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import uuid
import r4a_install_runtime_intake_routes as install
admin=install.admin
helper=admin.inventory.routes.helper
ROOT=install.ROOT
RECEIPT=ROOT/'runtime-intake-service-guards.json'
REVISION='edaba2bff18a2aaf52d1180f21f0e68984cc3437'


def private(path):
    meta=path.lstat()
    if not stat.S_ISREG(meta.st_mode) or meta.st_uid!=0 or stat.S_IMODE(meta.st_mode)!=0o600:raise RuntimeError('PRIVATE_RECEIPT_UNSAFE')
    return json.loads(path.read_text())


def save(value,exclusive=False):
    if exclusive:
        fd=os.open(RECEIPT,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);name=None
    else:fd,name=tempfile.mkstemp(prefix='.intake-guards-',dir=ROOT)
    try:
        with os.fdopen(fd,'w') as stream:json.dump(value,stream,sort_keys=True);stream.flush();os.fsync(stream.fileno())
        if name:os.replace(name,RECEIPT)
    finally:
        if name:Path(name).unlink(missing_ok=True)


def patch_route(route,cap):
    if (route.get('methods')!=['POST'] or route.get('upstream',{}).get('nodes')!={'ouf-udp:8080':1}
        or route.get('plugins',{}).get('proxy-rewrite') or route.get('plugins',{}).get('openid-connect',{}).get('required_scopes')!=[cap]
        or any(k in route for k in ('upstream_id','service_id','plugin_config_id'))):raise RuntimeError('INTAKE_ROUTE_CONTEXT_UNSUPPORTED')
    result=admin.comparable(route)
    result['plugins']=install.intake_plugins(route['plugins'])
    return result


def negative_probe(args,token,direct=False):
    # Pinned RuntimeLakeApi authorizes then rejects missing contentBase64 BEFORE
    # invoking lake.store. Include real source/run to evaluate the actual scope.
    args.run=str(uuid.UUID(args.run))
    if not re.fullmatch(r'[A-Za-z0-9._-]{1,160}',args.source):raise RuntimeError('SOURCE_INVALID')
    body=json.dumps({'runId':args.run,'sourceId':args.source,'typeCode':'FILE','zone':'RAW'},separators=(',',':'))
    url=('http://ouf-udp:8080' if direct else 'https://api.ouf-lab.it')+'/api/internal/v1/lake/objects'
    config='silent\nshow-error\nmax-time = 15\nmax-filesize = 1048576\nrequest = "POST"\nheader = "Authorization: Bearer '+token+'"\nheader = "Content-Type: application/json"\ndata = '+json.dumps(body)+'\nurl = '+json.dumps(url)+'\nwrite-out = "\\n%{http_code}"\n'
    raw=helper.run(['docker','run','--rm','-i','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--network','ouf-backend','curlimages/curl:8.16.0','--config','-'],input=config,timeout=25)
    _,sep,code=raw.rpartition('\n')
    if not sep:code=raw
    if not re.fullmatch(r'\d{3}',code):raise RuntimeError('PROBE_HTTP_INVALID')
    print('INTAKE_NEGATIVE_PROBE_'+('DIRECT_OWNER' if direct else 'GATEWAY')+'_HTTP='+code,flush=True)
    return code


def token(live):
    settings=helper.transport_settings(live,'ouf-lab')
    mount=next(m for m in live['Mounts'] if m['Destination']==helper.AUTH)
    path=Path(mount['Source'])/Path(settings['ouf.ingestion.activation.token-file']).relative_to(helper.AUTH)
    value=path.read_text().strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',value):raise RuntimeError('TOKEN_INVALID')
    return value


def main(args):
    if os.geteuid()!=0:raise RuntimeError('ROOT_REQUIRED')
    os.umask(0o077)
    meta=ROOT.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid!=0 or stat.S_IMODE(meta.st_mode)!=0o700:raise RuntimeError('PRIVATE_ROOT_UNSAFE')
    args.run=str(uuid.UUID(args.run))
    if not re.fullmatch(r'[A-Za-z0-9._-]{1,160}',args.source):raise RuntimeError('SOURCE_INVALID')
    udp=helper.inspect('ouf-udp');image=helper.inspect(udp['Image'],'image')
    if not udp['State']['Running'] or image['Config'].get('Labels',{}).get('org.opencontainers.image.revision')!=REVISION:raise RuntimeError('NEGATIVE_PROBE_OWNER_REVISION_UNSUPPORTED')
    apisix=helper.inspect('ouf-apisix');key=admin.inventory.routes.admin_key(admin.inventory.routes.mounted_config(apisix).read_text())
    document,_=admin.api(key,'GET','routes');values=admin.inventory.routes.route_values(document)
    ing=helper.inspect('ouf-ingestion');credential=token(ing)
    if args.mode=='verify':
        receipt=private(RECEIPT)
        if any(receipt.get(k)!=getattr(args,k) for k in ('source','run')):raise RuntimeError('VERIFY_RECEIPT_CONTEXT_MISMATCH')
        for ident,expected in receipt['after'].items():
            found=[x for x in values if str(x.get('id'))==ident]
            if len(found)!=1 or admin.comparable(found[0])!=expected:raise RuntimeError('VERIFY_ROUTE_DRIFT')
        for direct in (True,False):
            if negative_probe(args,credential,direct)!='400':raise RuntimeError('NEGATIVE_PROBE_ADMISSION_NOT_PROVEN')
        print('R4A_INTAKE_SERVICE_GUARDS_VERIFY=PASS STORAGE_NOT_INVOKED=true RETRY=false RUN_RESUME=false');return
    if RECEIPT.exists() or RECEIPT.is_symlink():raise RuntimeError('GUARDS_RECEIPT_EXISTS_USE_VERIFY')
    original=private(install.RECEIPT)
    if original.get('status')!='PASS':raise RuntimeError('ORIGINAL_INSTALL_RECEIPT_NOT_PASS')
    before={};after={}
    for ident,path,cap in install.TARGETS:
        found=admin.inventory.candidates(values,'POST',path)
        if len(found)!=1 or str(found[0]['id'])!=ident or admin.comparable(found[0])!=original['desired'].get(ident):raise RuntimeError('ORIGINAL_OWNED_ROUTE_DRIFT')
        before[ident]=admin.comparable(found[0]);after[ident]=patch_route(found[0],cap)
        lua=json.dumps({k:v for k,v in found[0].get('plugins',{}).items() if k.startswith('serverless-')})
        print('INTAKE_GUARD_SCOPE_LITERAL_'+cap+'='+str('ouf.udp.identity.attestation.read' in lua).lower())
        print('INTAKE_GUARD_SERVICE_ALLOWED_LITERAL_'+cap+'='+str('SERVICE' in lua).lower())
    print('R4A_INTAKE_SERVICE_GUARDS_PLAN=PASS MODE='+args.mode+' ROUTE_COUNT=2 OIDC_AND_LIMITS_PRESERVED=true',flush=True)
    if args.mode=='plan':return
    # Verify owner admission independently first. A non400 response localizes
    # another blocker BEFORE changing routes; storage is never reached.
    if negative_probe(args,credential,True)!='400':raise RuntimeError('OWNER_ADMISSION_BLOCKED_ROUTES_UNCHANGED')
    receipt={'status':'STARTING','source':args.source,'run':args.run,'before':before,'after':after,'attempted':[]}
    save(receipt,True)
    try:
        current,_=admin.api(key,'GET','routes')
        if install.existing(admin.inventory.routes.route_values(current))!=install.existing(values):raise RuntimeError('ROUTES_CHANGED_BEFORE_APPLY')
        for ident,expected in after.items():
            receipt['attempted'].append(ident);save(receipt)
            admin.api(key,'PUT','routes/'+ident,expected,accepted=('200','201'))
        current,_=admin.api(key,'GET','routes');new=admin.inventory.routes.route_values(current)
        for ident,expected in after.items():
            found=[x for x in new if str(x.get('id'))==ident]
            if len(found)!=1 or admin.comparable(found[0])!=expected:raise RuntimeError('ROUTE_READBACK_MISMATCH')
        if install.existing([x for x in new if str(x['id']) not in after])!=install.existing([x for x in values if str(x['id']) not in before]):raise RuntimeError('OTHER_ROUTES_CHANGED')
        if negative_probe(args,credential,False)!='400':raise RuntimeError('GATEWAY_ADMISSION_NOT_PROVEN')
        receipt['status']='PASS';save(receipt)
    except BaseException:
        try:
            for ident in reversed(receipt['attempted']):
                raw,_=admin.api(key,'GET','routes/'+ident)
                value=raw.get('value',raw.get('node',{}).get('value'))
                if isinstance(value,str):value=json.loads(value)
                if admin.comparable(value)!=after[ident]:raise RuntimeError('ROLLBACK_ROUTE_DRIFT')
                admin.api(key,'PUT','routes/'+ident,before[ident],accepted=('200','201'))
                raw,_=admin.api(key,'GET','routes/'+ident);value=raw.get('value',raw.get('node',{}).get('value'))
                if isinstance(value,str):value=json.loads(value)
                if admin.comparable(value)!=before[ident]:raise RuntimeError('ROLLBACK_READBACK_MISMATCH')
            receipt['status']='ROLLED_BACK';save(receipt)
        except Exception:
            receipt['status']='MANUAL_RECOVERY_REQUIRED';save(receipt)
        raise
    print('R4A_INTAKE_SERVICE_GUARDS=PASS ROUTES=2 LAKE_ADMISSION_PROVEN_WITH_INCOMPLETE_BODY=true STORAGE_NOT_INVOKED=true')
    print('R4A_INTAKE_SERVICE_GUARDS_RECEIPT='+str(RECEIPT)+' PRIVATE=true')
    print('R4A_INTAKE_SERVICE_GUARDS_COMPLETE=PASS IAM_UNCHANGED=true TOKEN_UNCHANGED_BY_SCRIPT=true RETRY=false RUN_RESUME=false HANDOFF_ADMISSION_NOT_TESTED=true S3_WRITE_NOT_PROVEN=true')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('plan','apply','verify'));p.add_argument('--source',required=True);p.add_argument('--run',required=True)
    try:main(p.parse_args())
    except Exception as error:
        code=str(error) if isinstance(error,RuntimeError) else type(error).__name__
        print('R4A_INTAKE_SERVICE_GUARDS=BLOCKED CODE='+code+' RETRY=false RUN_RESUME=false AUTOMATIC_REPOST=false SECRETS_NOT_PRINTED=true');raise SystemExit(1)
