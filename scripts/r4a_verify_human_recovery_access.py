#!/usr/bin/env python3
"""Device login and GET-only recovery authorization proof for any tenant source."""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import time
import uuid
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, HTTPRedirectHandler, build_opener
import r4a_prepare_frozen_compatibility_probe as helper

ROOT = Path('/etc/ouf/deploy-snapshots')
SCOPES = {'ingestion.run.read','ingestion.quarantine.read'}
RUNTIME = {}


def configure(args):
    """Explicit bindings for new recovery cycles; legacy CLI remains compatible."""
    global ROOT, RUNTIME
    fields=('receipt_root','ingestion_container','postgres_container','database','db_user','network','curl_image')
    values={key:getattr(args,key,None) for key in fields}
    if getattr(args,'cycle',None) and not all(values.values()):
        raise RuntimeError('RECOVERY_INSTALLATION_BINDINGS_REQUIRED')
    for key in ('ingestion_container','postgres_container','database','db_user','network','curl_image'):
        value=values[key]
        if value is not None and (not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/@-]{0,255}',value)):
            raise RuntimeError('RECOVERY_INSTALLATION_BINDING_INVALID')
    if values['receipt_root'] is not None:
        path=Path(values['receipt_root'])
        if not path.is_absolute() or '..' in path.parts:
            raise RuntimeError('RECOVERY_RECEIPT_ROOT_INVALID')
        ROOT=path
    RUNTIME={key:value for key,value in values.items() if value is not None}


def ingestion_container():return RUNTIME.get('ingestion_container','ouf-ingestion')


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def origin(value):
    parsed = urlparse(value)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or any(c.isspace() for c in value)
            or any(c in value for c in '\\"')):
        raise RuntimeError('HTTPS_ENDPOINT_INVALID')
    return parsed


def oidc(url, values=None):
    req = Request(url, data=None if values is None else urlencode(values).encode(),
                  headers={'Accept':'application/json', **({'Content-Type':'application/x-www-form-urlencoded'} if values is not None else {})})
    try:
        with build_opener(NoRedirect()).open(req,timeout=20) as response:
            raw = response.read(1048577)
            if len(raw)>1048576:
                raise RuntimeError('OIDC_RESPONSE_TOO_LARGE')
            return response.status,json.loads(raw)
    except HTTPError as error:
        try:
            body=json.loads(error.read(1048576))
        except ValueError:
            body={}
        return error.code,{'error':body.get('error')}


def claims_check(token, args):
    if not isinstance(token,str) or len(token)>16384 or not re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',token):
        raise RuntimeError('HUMAN_TOKEN_FORMAT_INVALID')
    part=token.split('.')[1]
    claims=json.loads(base64.urlsafe_b64decode(part+'='*(-len(part)%4)))
    audience=claims.get('aud',[])
    if isinstance(audience,str):audience=[audience]
    if not (claims.get('iss')==args.issuer and claims.get('azp')==args.client
            and claims.get('sub')==args.subject and claims.get('tenant_id')==args.tenant
            and claims.get('ouf_actor_type') in ('HUMAN','HUMAN_USER')
            and args.audience in audience and SCOPES <= set(str(claims.get('scope','')).split())
            and type(claims.get('exp')) is int and claims['exp']>time.time()+60):
        raise RuntimeError('HUMAN_IDENTITY_OR_READ_SCOPES_MISMATCH')
    # Claim decoding is diagnostic. Gateway and owner validate the signature.


def login(args):
    code,metadata=oidc(args.issuer+'/.well-known/openid-configuration')
    if code!=200 or metadata.get('issuer')!=args.issuer:
        raise RuntimeError('OIDC_DISCOVERY_MISMATCH')
    device=metadata.get('device_authorization_endpoint','')
    endpoint=metadata.get('token_endpoint','')
    for value in (device,endpoint):
        origin(value)
        if not value.startswith(args.issuer+'/protocol/openid-connect/'):
            raise RuntimeError('OIDC_ENDPOINT_MISMATCH')
    code,start=oidc(device,{'client_id':args.client,'scope':'openid '+' '.join(sorted(SCOPES))})
    if code!=200 or not all(start.get(k) for k in ('device_code','user_code','verification_uri','expires_in')):
        raise RuntimeError('DEVICE_AUTHORIZATION_FAILED')
    verification=origin(start['verification_uri'])
    if verification.netloc!=origin(args.issuer).netloc or not re.fullmatch(r'[A-Za-z0-9-]{1,40}',start['user_code']):
        raise RuntimeError('DEVICE_VERIFICATION_MISMATCH')
    print('OPEN_IN_BROWSER='+start['verification_uri'],flush=True)
    print('ENTER_DEVICE_CODE='+start['user_code'],flush=True)
    print('Non incollare codice dispositivo o token in chat.',flush=True)
    delay=max(5,min(30,int(start.get('interval',5))))
    deadline=time.monotonic()+min(600,int(start['expires_in']))
    while time.monotonic()<deadline:
        time.sleep(delay)
        code,result=oidc(endpoint,{'grant_type':'urn:ietf:params:oauth:grant-type:device_code','client_id':args.client,'device_code':start['device_code']})
        if code==200:
            token=result.get('access_token')
            claims_check(token,args)
            return token
        if result.get('error')=='slow_down':delay=min(30,delay+5)
        elif result.get('error')!='authorization_pending':raise RuntimeError('DEVICE_LOGIN_FAILED')
    raise RuntimeError('DEVICE_LOGIN_EXPIRED')


def snapshot(run, quarantine):
    query=("begin read only; set local statement_timeout=15000; select json_build_object("
           "'run',(select row_to_json(x) from (select run_id,tenant_id,source_id,state,failure_code,control_version from ouf_ingestion.ing_run where run_id='"+run+"') x),"
           "'quarantine',(select row_to_json(x) from (select quarantine_id,run_id,state,lifecycle_state,lifecycle_version,reason_code from ouf_ingestion.ing_quarantine where quarantine_id='"+quarantine+"') x))::text; rollback;")
    return json.loads(helper.run(['docker','exec',RUNTIME.get('postgres_container','ouf-postgres'),'psql','-X','-qAt','-v','ON_ERROR_STOP=1','-U',RUNTIME.get('db_user','ouf_ingestion'),'-d',RUNTIME.get('database','ouf_ingestion'),'-c',query]))


def get(api,path,token):
    # Bearer is sent through stdin only, never docker argv or a file.
    config=('silent\nshow-error\nmax-time = 20\nmax-filesize = 1048576\n'
            'request = "GET"\nheader = "Authorization: Bearer '+token+'"\n'
            'header = "Accept: application/json"\nurl = "'+api+path+'"\nwrite-out = "\\n%{http_code}"\n')
    raw=helper.run(['docker','run','--rm','-i','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--network',RUNTIME.get('network','ouf-backend'),RUNTIME.get('curl_image','curlimages/curl:8.16.0'),'--config','-'],input=config,timeout=30)
    body,sep,code=raw.rpartition('\n')
    if not sep:body,code='',raw
    if code!='200':
        raise RuntimeError('RECOVERY_READ_HTTP_'+(code if re.fullmatch(r'\d{3}',code) else 'INVALID'))
    return json.loads(body)


def match_response(actual, baseline):
    if not isinstance(actual,dict) or any(actual.get(k)!=v for k,v in baseline.items() if k!='tenant_id'):
        raise RuntimeError('HUMAN_READ_OWNER_DATABASE_MISMATCH')


def main(args):
    if os.geteuid()!=0:raise RuntimeError('ROOT_REQUIRED')
    os.umask(0o077)
    meta=ROOT.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid!=0 or stat.S_IMODE(meta.st_mode)!=0o700:
        raise RuntimeError('PRIVATE_ROOT_UNSAFE')
    args.run=str(uuid.UUID(args.run));args.quarantine=str(uuid.UUID(args.quarantine))
    args.subject=str(uuid.UUID(args.subject))
    for endpoint in (args.api,args.issuer):origin(endpoint)
    if urlparse(args.api).path not in ('','/') or args.api.endswith('/') or args.issuer.endswith('/'):
        raise RuntimeError('ENDPOINT_PATH_UNSUPPORTED')
    for value in (args.client,args.tenant,args.audience):
        if not re.fullmatch(r'[A-Za-z0-9._:-]{1,160}',value):raise RuntimeError('IDENTIFIER_INVALID')
    if not re.fullmatch(r'[0-9a-f]{40}',args.expected_revision):raise RuntimeError('REVISION_INVALID')
    live=helper.inspect('ouf-ingestion')
    image=helper.inspect(live['Image'],'image')
    if not live['State']['Running'] or image['Config'].get('Labels',{}).get('org.opencontainers.image.revision')!=args.expected_revision:
        raise RuntimeError('LIVE_RELEASE_MISMATCH')
    before=snapshot(args.run,args.quarantine)
    if (not before['run'] or not before['quarantine'] or before['run']['tenant_id']!=args.tenant
            or before['quarantine']['run_id']!=args.run):
        raise RuntimeError('RUN_QUARANTINE_TENANT_CONTEXT_MISMATCH')
    print('R4A_HUMAN_RECOVERY_ACCESS=READ_ONLY',flush=True)
    token=login(args)
    run=get(args.api,'/api/trusted-human/v1/ingestion/runs/'+args.run,token)
    match_response(run,before['run'])
    print('HUMAN_RECOVERY_RUN_READ=PASS HTTP=200',flush=True)
    quarantine=get(args.api,'/api/trusted-human/v1/ingestion/quarantine/'+args.quarantine,token)
    match_response(quarantine,before['quarantine'])
    print('HUMAN_RECOVERY_QUARANTINE_READ=PASS HTTP=200',flush=True)
    if snapshot(args.run,args.quarantine)!=before or helper.inspect('ouf-ingestion')['Id']!=live['Id']:
        raise RuntimeError('RECOVERY_CONTEXT_CHANGED_DURING_READ')
    receipt=ROOT/('ingestion-human-recovery-read-'+args.run+'.json')
    value={'status':'PASS','runId':args.run,'quarantineId':args.quarantine,'tenant':args.tenant,'subject':args.subject,'revision':args.expected_revision,'snapshot':before,'runHttp':200,'quarantineHttp':200,'retry':False,'resume':False}
    fd,name=tempfile.mkstemp(prefix='.human-recovery-',dir=ROOT)
    try:
        with os.fdopen(fd,'w') as stream:
            json.dump(value,stream,sort_keys=True);stream.write('\n');stream.flush();os.fsync(stream.fileno())
        os.replace(name,receipt)
    finally:
        Path(name).unlink(missing_ok=True)
    print('HUMAN_RECOVERY_RUN_STATE='+str(run['state'])+' CONTROL_VERSION='+str(run['control_version']))
    print('HUMAN_RECOVERY_QUARANTINE_STATE='+str(quarantine['lifecycle_state'])+' LIFECYCLE_VERSION='+str(quarantine['lifecycle_version']))
    print('R4A_HUMAN_RECOVERY_RECEIPT='+str(receipt)+' PRIVATE=true')
    print('R4A_HUMAN_RECOVERY_ACCESS=PASS READ_AUTHORIZATION_PROVEN=true WRITE_AUTHORIZATION_NOT_TESTED=true RETRY=false RUN_RESUME=false SECRETS_NOT_PRINTED=true')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('issuer','api','client','subject','tenant','audience','run','quarantine','expected-revision'):
        p.add_argument('--'+key,required=True)
    try:main(p.parse_args())
    except Exception as error:
        code=str(error) if isinstance(error,RuntimeError) else type(error).__name__
        print('R4A_HUMAN_RECOVERY_ACCESS=BLOCKED CODE='+code+' RETRY=false RUN_RESUME=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
