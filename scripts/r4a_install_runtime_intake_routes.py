#!/usr/bin/env python3
"""Add two exact UDP POST routes, retaining existing OIDC security and a private rollback record."""
import argparse
import base64
import copy
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import r4a_install_runtime_publication_list_route as admin
import r4a_cinema_execution_readback as readback

ROOT = readback.ROOT
RECEIPT = ROOT / 'runtime-intake-routes.json'
TEMPLATE = '/api/udp/v1/governance/internal/identity/preflight'
TARGETS = [('r4a-udp-runtime-lake-write','/api/internal/v1/lake/objects','datalake.write'),
           ('r4a-udp-runtime-handoff-write','/api/internal/v1/handoffs','udp.candidate.write')]


def objects(value):
    if isinstance(value,dict):
        yield value
        for child in value.values():
            yield from objects(child)
    elif isinstance(value,list):
        for child in value:
            yield from objects(child)


def scope_for(policy, capability):
    found = [x for x in objects(policy) if x.get('capabilityId') == capability and 'allowedActors' in x and 'requiredScope' in x]
    if (len(found) != 1 or 'SERVICE' not in found[0]['allowedActors'] or found[0].get('operation') != 'WRITE' or
        not isinstance(found[0]['requiredScope'],str) or not re.fullmatch(r'[A-Za-z0-9._:-]{1,160}',found[0]['requiredScope'])):
        raise RuntimeError('INTAKE_CAPABILITY_DESCRIPTOR_UNSUPPORTED')
    return found[0]['requiredScope']


def desired_routes(values, scopes):
    selected = admin.inventory.candidates(values,'GET',TEMPLATE)
    if len(selected) != 1:
        raise RuntimeError('UDP_OIDC_TEMPLATE_NOT_UNIQUE')
    route = selected[0]
    oidc = route.get('plugins',{}).get('openid-connect',{})
    hosts = ([route['host']] if route.get('host') else []) + (route.get('hosts') or [])
    if (route.get('status',1) != 1 or route.get('upstream',{}).get('nodes') != {'ouf-udp:8080':1} or
        any(k in route for k in ('upstream_id','service_id','plugin_config_id')) or
        any(route.get(k) for k in ('vars','filter_func','remote_addr','remote_addrs')) or
        route.get('plugins',{}).get('proxy-rewrite') or not oidc or oidc.get('_meta',{}).get('disable',False) or
        oidc.get('required_scopes') != ['ouf.udp.identity.attestation.read'] or
        (hosts and 'api.ouf-lab.it' not in hosts)):
        raise RuntimeError('UDP_OIDC_TEMPLATE_UNSUPPORTED')
    result = {}
    for route_id,path,capability in TARGETS:
        value = copy.deepcopy(route)
        for key in ('id','create_time','update_time','uri','uris','name','desc'):
            value.pop(key,None)
        value.update(uri=path,methods=['POST'],name=route_id,desc='Exact authenticated UDP runtime intake; owner SERVICE authorization retained')
        value['plugins']['openid-connect']['required_scopes'] = [scopes[capability]]
        result[route_id] = value
    return result


def save(value, exclusive=False):
    if exclusive:
        fd = os.open(RECEIPT,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
        temporary = None
    else:
        fd,name = tempfile.mkstemp(prefix='.intake-routes-',dir=ROOT)
        temporary = Path(name)
    with os.fdopen(fd,'w') as stream:
        json.dump(value,stream)
        stream.flush()
        os.fsync(stream.fileno())
    if temporary:
        os.replace(temporary,RECEIPT)
    fd = os.open(ROOT,os.O_RDONLY|os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def policy(live):
    helper = admin.inventory.routes.helper
    settings = helper.transport_settings(live,'ouf-lab')
    mounts = {m['Destination']:m for m in live['Mounts']}
    raw = Path(mounts[helper.PROPERTIES]['Source']).read_text()
    registry = helper.literal_property(raw,'ouf.authorization.registry-url')
    token_path = Path(mounts[helper.AUTH]['Source']) / Path(settings['ouf.ingestion.activation.token-file']).relative_to(helper.AUTH)
    token = token_path.read_text().strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',token):
        raise RuntimeError('TOKEN_FORMAT_INVALID')
    part = token.split('.')[1]
    claims = json.loads(base64.urlsafe_b64decode(part + '='*(-len(part)%4)))
    config = ('silent\nshow-error\nmax-time = 5\nmax-filesize = 2097152\n'
        'header = "Authorization: Bearer ' + token + '"\nurl = ' + json.dumps(registry) + '\nwrite-out = "\\n%{http_code}"\n')
    raw = helper.run(['docker','run','--rm','-i','--read-only','--cap-drop','ALL','--security-opt',
        'no-new-privileges','--network','ouf-backend','curlimages/curl:8.16.0','--config','-'],input=config,timeout=15)
    body,code = raw.rsplit('\n',1)
    if code != '200':
        raise RuntimeError('INTAKE_POLICY_READ_NOT_200')
    document = json.loads(body)
    scopes = {cap:scope_for(document,cap) for _,_,cap in TARGETS}
    if not set(scopes.values()) <= set(str(claims.get('scope','')).split()):
        raise RuntimeError('INTAKE_TOKEN_REQUIRED_SCOPE_MISSING_NO_IAM_CHANGED')
    return document,scopes


def existing(values):
    return {str(x['id']):admin.comparable(x) for x in values}


def rollback(key,desired,attempted):
    for route_id in reversed(attempted):
        raw,status = admin.api(key,'GET','routes/'+route_id,accepted=('200','404'))
        if status == '404':
            continue
        value = raw.get('value',raw.get('node',{}).get('value'))
        if isinstance(value,str):
            value = json.loads(value)
        if not isinstance(value,dict) or admin.comparable(value) != desired[route_id]:
            raise RuntimeError('INTAKE_ROLLBACK_ROUTE_DRIFT_MANUAL_REVIEW')
        admin.api(key,'DELETE','routes/'+route_id,accepted=('200','204'))
        _,status = admin.api(key,'GET','routes/'+route_id,accepted=('200','404'))
        if status != '404':
            raise RuntimeError('INTAKE_ROLLBACK_DELETE_NOT_VERIFIED')


def main(mode):
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    os.umask(0o077)
    meta = ROOT.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o700:
        raise RuntimeError('PRIVATE_SNAPSHOT_ROOT_UNSAFE')
    if RECEIPT.exists() or RECEIPT.is_symlink():
        raise RuntimeError('INTAKE_ROUTE_RECEIPT_EXISTS_RECONCILE_DO_NOT_REPUT')
    activation = readback.private(ROOT/'cinema-source-activation.json')
    if (activation.get('status') != 'PASS' or activation.get('sourceId') != readback.SOURCE or
        activation.get('versionId') != readback.VERSION or activation.get('configurationHash') != readback.HASH or
        activation.get('publicationId') != readback.PUBLICATION):
        raise RuntimeError('ACTIVATION_RECEIPT_MISMATCH')
    helper = admin.inventory.routes.helper
    udp = helper.inspect('ouf-udp')
    image = helper.inspect(udp['Image'],'image')
    if not udp['State']['Running'] or image['Config'].get('Labels',{}).get('org.opencontainers.image.revision') != 'edaba2bff18a2aaf52d1180f21f0e68984cc3437':
        raise RuntimeError('UDP_OWNER_REVISION_DRIFT')
    run = readback.sql('ouf_ingestion',"select json_build_object('state',state,'failure',failure_code,'outbox',(select count(*) from ouf_ingestion.handoff_outbox where run_id=r.run_id)) from ouf_ingestion.ing_run r where run_id='86809c17-3354-45ca-a7e6-57e903944b24' and source_id='"+readback.SOURCE+"'")
    if run != {'state':'PAUSED','failure':'ING_RECORD_QUARANTINED','outbox':0}:
        raise RuntimeError('PAUSED_RUN_BASELINE_DRIFT')
    ing = helper.inspect('ouf-ingestion')
    document,scopes = policy(ing)
    apisix = helper.inspect('ouf-apisix')
    if not apisix['State']['Running']:
        raise RuntimeError('APISIX_NOT_RUNNING')
    key = admin.inventory.routes.admin_key(admin.inventory.routes.mounted_config(apisix).read_text())
    raw,_ = admin.api(key,'GET','routes')
    values = admin.inventory.routes.route_values(raw)
    desired = desired_routes(values,scopes)
    for route_id,path,cap in TARGETS:
        if admin.inventory.candidates(values,'POST',path):
            raise RuntimeError('INTAKE_PATH_ALREADY_ROUTED_RECONCILE')
        _,status = admin.api(key,'GET','routes/'+route_id,accepted=('200','404'))
        if status != '404':
            raise RuntimeError('INTAKE_ROUTE_ID_ALREADY_OWNED')
        print('INTAKE_ROUTE_PLANNED='+route_id+' REQUIRED_SCOPE='+scopes[cap])
    print('R4A_RUNTIME_INTAKE_ROUTES_PLAN=PASS MODE='+mode+' OWNER_UDP=true TOKEN_SCOPES_PRESENT=true',flush=True)
    if mode == 'plan':
        print('R4A_RUNTIME_INTAKE_ROUTES=PLANNED LIVE_UNCHANGED=true RUN_RESUME=false')
        return
    snapshot_dir = Path(tempfile.mkdtemp(prefix='runtime-intake-routes-',dir=ROOT))
    snapshot = snapshot_dir/'routes-before.json'
    with snapshot.open('w') as stream:
        json.dump(raw,stream)
        stream.flush()
        os.fsync(stream.fileno())
    snapshot.chmod(0o600)
    receipt = dict(status='UNVERIFIED_DO_NOT_REPUT',beforeSnapshot=str(snapshot),desired=desired,attempted=[])
    save(receipt,exclusive=True)
    try:
        current,_ = admin.api(key,'GET','routes')
        if existing(admin.inventory.routes.route_values(current)) != existing(values) or policy(ing)[0] != document:
            raise RuntimeError('ROUTE_OR_POLICY_DRIFT_BEFORE_PUT')
        for route_id,_,_ in TARGETS:
            receipt['attempted'].append(route_id)
            save(receipt)
            admin.api(key,'PUT','routes/'+route_id,desired[route_id],accepted=('200','201'))
        after,_ = admin.api(key,'GET','routes')
        new = admin.inventory.routes.route_values(after)
        if existing([x for x in new if str(x['id']) not in desired]) != existing(values):
            raise RuntimeError('EXISTING_ROUTES_CHANGED')
        for route_id,path,_ in TARGETS:
            found = admin.inventory.candidates(new,'POST',path)
            if len(found) != 1 or str(found[0]['id']) != route_id or admin.comparable(found[0]) != desired[route_id]:
                raise RuntimeError('INTAKE_ROUTE_READBACK_MISMATCH')
        receipt['status'] = 'PASS'
        save(receipt)
    except BaseException:
        try:
            rollback(key,desired,receipt['attempted'])
            receipt['status'] = 'ROLLED_BACK'
            print('R4A_RUNTIME_INTAKE_ROUTES_ROLLBACK=PASS')
        except Exception:
            receipt['status'] = 'MANUAL_RECOVERY_REQUIRED'
            print('R4A_RUNTIME_INTAKE_ROUTES_ROLLBACK=MANUAL_RECOVERY_REQUIRED')
        save(receipt)
        raise
    print('R4A_RUNTIME_INTAKE_ROUTES=PASS ROUTE_COUNT=2 EXISTING_ROUTES_PRESERVED=true')
    print('R4A_RUNTIME_INTAKE_ROUTES_RECEIPT='+str(RECEIPT)+' PRIVATE=true')
    print('R4A_RUNTIME_INTAKE_ROUTES_SNAPSHOT='+str(snapshot)+' PRIVATE=true')
    print('R4A_RUNTIME_INTAKE_ROUTES_COMPLETE=PASS IAM_UNCHANGED=true WORKERS_UNCHANGED=true RUN_RESUME=false INTAKE_POST=false OWNER_AUTHORIZATION_NOT_PROVEN=true SECRETS_NOT_PRINTED=true')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('plan','apply'))
    try:
        main(parser.parse_args().mode)
    except Exception as error:
        code=str(error) if isinstance(error,RuntimeError) else type(error).__name__
        print('R4A_RUNTIME_INTAKE_ROUTES=BLOCKED CODE='+code+' RUN_RESUME=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
