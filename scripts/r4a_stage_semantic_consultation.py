#!/usr/bin/env python3
"""Build pinned consultation images and privately snapshot live bindings; no live switch."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from urllib.request import Request, urlopen


def admin_key(text):
    """Accept the conventional literal APISIX admin_key list, fail closed otherwise."""
    lines = text.splitlines()
    starts = [(i, len(line) - len(line.lstrip())) for i, line in enumerate(lines)
              if re.fullmatch(r"\s*admin_key:\s*(?:#.*)?", line)]
    if len(starts) != 1:
        raise RuntimeError("APISIX_ADMIN_KEY_LAYOUT_UNSUPPORTED")
    start, indent = starts[0]
    entries, current = [], {}
    for line in lines[start + 1:]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        level = len(line) - len(line.lstrip())
        item = line.lstrip().startswith("- ")
        # YAML allows sequence items aligned with the owning mapping key.
        if level < indent or (level == indent and not item):
            break
        if item:
            if current:
                entries.append(current)
            current = {}
        match = re.fullmatch(r"\s*(?:-\s*)?(name|key|role):\s*(.*?)\s*", line)
        if match:
            value = match[2]
            scalar = re.fullmatch(r'''(?:"([^"\\]*)"|'([^'\\]*)'|([^#"'\\]+?))\s*(?:#.*)?''', value)
            if scalar is None:
                raise RuntimeError("APISIX_ADMIN_KEY_LAYOUT_UNSUPPORTED")
            value = next(v for v in scalar.groups() if v is not None).strip()
            current[match[1]] = value
    if current:
        entries.append(current)
    keys = [e.get("key", "") for e in entries if e.get("role") == "admin"]
    if len(keys) != 1 or not re.fullmatch(r"[A-Za-z0-9._-]{8,256}", keys[0]):
        raise RuntimeError("APISIX_ADMIN_KEY_LAYOUT_UNSUPPORTED")
    return keys[0]

def route_values(document):
    entries = document.get("list")
    if entries is None:
        entries = document.get("node", {}).get("nodes")
    if not isinstance(entries, list):
        raise RuntimeError("APISIX_ROUTE_RESPONSE_UNSUPPORTED")
    result = []
    for entry in entries:
        value = entry.get("value", {})
        if isinstance(value, str):
            value = json.loads(value)
        if not isinstance(value, dict):
            raise RuntimeError("APISIX_ROUTE_RESPONSE_UNSUPPORTED")
        result.append(value)
    return result

def run(argv, timeout=30, stdin=None):
    return subprocess.run(argv, input=stdin, capture_output=True, text=True,
                          check=True, timeout=timeout).stdout.strip()


def inspect(name):
    rows=json.loads(run(['docker','inspect',name]))
    if len(rows)!=1:raise RuntimeError('AMBIGUOUS_INSPECT')
    return rows[0]


def fingerprint(row):
    return {k:row.get(k) for k in ('Id','Image','Config','HostConfig','Mounts')} | {
        'running':row['State']['Running'],'startedAt':row['State']['StartedAt']}


def guard(row, revision):
    if (not row['State']['Running'] or row['HostConfig'].get('Privileged') or
        (row['Config'].get('Labels') or {}).get('org.opencontainers.image.revision')!=revision):
        raise RuntimeError('LIVE_DRIFT')


def save(path, data):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'w') as f:
        json.dump(data,f,sort_keys=True);f.flush();os.fsync(f.fileno())


def validate(config):
    if set(config)!={'stageRoot','images','gateway'} or len(config['images'])!=2:
        raise RuntimeError('CONFIG_INVALID')
    if {x['role'] for x in config['images']}!={'semantic','mcp'}:raise RuntimeError('ROLES_INVALID')
    names=[]
    for x in config['images']:
        if set(x)!={'role','repository','commit','container','liveRevision'}:raise RuntimeError('IMAGE_CONFIG_INVALID')
        if not re.fullmatch(r'https://github.com/GioNob/ouf-[a-z-]+(?:\.git)?',x['repository']):raise RuntimeError('REPOSITORY_INVALID')
        for k in ('commit','liveRevision'):
            if not re.fullmatch('[0-9a-f]{40}',x[k]):raise RuntimeError('PIN_INVALID')
        names.append(x['container'])
    g=config['gateway']
    if set(g)!={'container','configDestination','adminOrigin'}:raise RuntimeError('GATEWAY_CONFIG_INVALID')
    names.append(g['container'])
    if len(set(names))!=3 or any(not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',n) for n in names):raise RuntimeError('CONTAINER_INVALID')
    # Plain HTTP allowed only inside the Gateway network namespace on loopback.
    if not re.fullmatch(r'http://127\.0\.0\.1:[0-9]{1,5}',g['adminOrigin']):raise RuntimeError('ADMIN_ORIGIN_INVALID')
    if not Path(g['configDestination']).is_absolute() or not Path(config['stageRoot']).is_absolute():raise RuntimeError('PATH_INVALID')


def routes(g, row):
    target=Path(g['configDestination'])
    files=[Path(m['Source'])/target.relative_to(Path(m['Destination'])) for m in row.get('Mounts',[])
           if m['Type']=='bind' and target.is_relative_to(Path(m['Destination']))]
    if len(files)!=1:raise RuntimeError('GATEWAY_CONFIG_BIND_NOT_UNIQUE')
    key=admin_key(files[0].read_text())
    raw=run(['nsenter','-t',str(row['State']['Pid']),'-n',sys.executable,
             str(Path(__file__).resolve()),'--inside',g['adminOrigin']],stdin=key)
    doc=json.loads(raw)
    if doc.get('total',len(doc.get('list',[])))>len(doc.get('list',[])):raise RuntimeError('ROUTES_TRUNCATED')
    rows=route_values(doc)
    if len({str(x.get('id')) for x in rows})!=len(rows):raise RuntimeError('ROUTE_IDS_INVALID')
    return rows


def main(config):
    validate(config)
    if os.geteuid()!=0:raise RuntimeError('ROOT_REQUIRED')
    os.umask(0o077)
    root=Path(config['stageRoot'])
    # New exclusive run directory: uncertainty never triggers an overwrite/rebuild.
    root.mkdir(mode=0o700,parents=False,exist_ok=False)
    s=root.lstat()
    if not stat.S_ISDIR(s.st_mode) or s.st_uid!=0 or stat.S_IMODE(s.st_mode)!=0o700:raise RuntimeError('PRIVATE_STAGE_INVALID')
    live={x['role']:inspect(x['container']) for x in config['images']}
    for x in config['images']:guard(live[x['role']],x['liveRevision'])
    g=config['gateway'];gw=inspect(g['container'])
    if not gw['State']['Running'] or gw['HostConfig'].get('Privileged'):raise RuntimeError('GATEWAY_STATE_INVALID')
    baseline=routes(g,gw)
    save(root/'runtime-snapshot.json',{'schema':'ouf.consultation.stage.v1','config':config,'live':live,'gateway':gw,'routes':baseline})
    selected=[r for r in baseline if any(isinstance(u,str) and ('/semantic/' in u or u.startswith('/internal/capabilities/v1/execute')) for u in [r.get('uri')]+r.get('uris',[]))]
    summary=[]
    for r in selected:
        p=r.get('plugins',{});oidc=p.get('openid-connect',{})
        summary.append({'id':r.get('id'),'uri':r.get('uri'),'methods':r.get('methods'),
                        'inlineUpstream':r.get('upstream',{}).get('nodes'),
                        'upstreamRef':r.get('upstream_id'),'serviceRef':r.get('service_id'),
                        'requiredScopes':oidc.get('required_scopes'),'plugins':sorted(p),
                        'status':r.get('status',1)})
    print('CONSULTATION_GATEWAY='+json.dumps({'routes':summary,'environmentNames':sorted(e.partition('=')[0] for e in gw['Config'].get('Env',[]))},sort_keys=True),flush=True)
    images=[]
    for x in config['images']:
        source=root/x['role'];tag='ouf-'+x['role']+':consultation-'+x['commit'][:12]
        run(['git','clone','--no-checkout',x['repository'],str(source)],180)
        run(['git','-C',str(source),'fetch','--no-tags','origin',x['commit']],180)
        run(['git','-C',str(source),'checkout','--detach',x['commit']],60)
        if run(['git','-C',str(source),'rev-parse','HEAD'])!=x['commit']:raise RuntimeError('SOURCE_PIN_DRIFT')
        log=root/(x['role']+'-build.log')
        print('CONSULTATION_BUILD_STARTED='+x['role']+' COMMIT='+x['commit'],flush=True)
        with log.open('x') as stream:
            result=subprocess.run(['docker','build','--label','org.opencontainers.image.revision='+x['commit'],
                                   '-t',tag,str(source)],stdout=stream,stderr=subprocess.STDOUT,timeout=2400)
        if result.returncode:raise RuntimeError('IMAGE_BUILD_FAILED_PRIVATE_LOG')
        image=inspect(tag)
        if (image['Config'].get('Labels') or {}).get('org.opencontainers.image.revision')!=x['commit']:raise RuntimeError('IMAGE_PIN_DRIFT')
        images.append({'role':x['role'],'commit':x['commit'],'image':image['Id'],'tag':tag})
        print('CONSULTATION_IMAGE_STAGED='+json.dumps(images[-1],sort_keys=True),flush=True)
    for x in config['images']:
        if fingerprint(inspect(x['container']))!=fingerprint(live[x['role']]):raise RuntimeError('LIVE_CHANGED_DURING_STAGE')
    if fingerprint(inspect(g['container']))!=fingerprint(gw) or routes(g,gw)!=baseline:raise RuntimeError('GATEWAY_CHANGED_DURING_STAGE')
    save(root/'image-receipt.json',{'status':'PASS','images':images,'liveUnchanged':True,'noContainersCreated':True})
    print('CONSULTATION_STAGE=PASS LIVE_UNCHANGED=true ROUTES_UNCHANGED=true NO_SWITCH=true NO_SOURCE_RUN=true PRIVATE_ROOT='+str(root),flush=True)


if __name__=='__main__':
    try:
        if len(sys.argv)==3 and sys.argv[1]=='--inside':
            key=sys.stdin.read().strip()
            req=Request(sys.argv[2]+'/apisix/admin/routes',headers={'X-API-KEY':key})
            with urlopen(req,timeout=15) as response:
                raw=response.read(10485761)
            if len(raw)>10485760:raise RuntimeError('ADMIN_RESPONSE_LIMIT')
            print(raw.decode())
        else:
            p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True)
            main(json.loads(p.parse_args().config.read_text()))
    except Exception as error:
        code=str(error) if isinstance(error,RuntimeError) and re.fullmatch('[A-Z_]{1,80}',str(error)) else type(error).__name__
        print('CONSULTATION_STAGE=BLOCKED CODE='+code+' LIVE_SWITCH_NOT_ATTEMPTED=true PRIVATE_LOGS_NOT_PRINTED=true',file=sys.stderr)
        raise SystemExit(1) from None
