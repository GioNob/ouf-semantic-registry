#!/usr/bin/env python3
"""Inspect UDP token bindings and refresher structure; never print secrets or execute scripts."""
import argparse
import ast
import base64
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time


def run(argv):
    return subprocess.run(argv,check=True,capture_output=True,text=True,timeout=20).stdout.strip()


def writer_facts(source):
    tree=ast.parse(source)
    truncating=0;atomic=0
    for node in ast.walk(tree):
        if not isinstance(node,ast.Call):continue
        func=node.func
        name=func.attr if isinstance(func,ast.Attribute) else func.id if isinstance(func,ast.Name) else ''
        if name in ('write_text','write_bytes'):truncating+=1
        if name=='open':
            mode=next((x.value for x in node.keywords if x.arg=='mode'),None)
            if mode is None and len(node.args)>1:mode=node.args[1]
            if isinstance(mode,ast.Constant) and isinstance(mode.value,str) and 'w' in mode.value:truncating+=1
        if name in ('replace','rename'):atomic+=1
    return {'truncating_write_sites':truncating,'replace_or_rename_sites':atomic,
            'token_destination_write_behavior_not_proven':True}


def mapped(container,target):
    path=Path(target)
    if not path.is_absolute() or '..' in path.parts:raise ValueError('path')
    found=[]
    for mount in container['Mounts']:
        dest=Path(mount['Destination'])
        if mount['Type']=='bind' and (path==dest or path.is_relative_to(dest)):
            host=Path(mount['Source'])/path.relative_to(dest)
            if not host.resolve().is_relative_to(Path(mount['Source']).resolve()):
                raise ValueError('mount escape')
            found.append((host,path==dest))
    if len(found)!=1:raise ValueError('mount ambiguity')
    return found[0]


def inspect_services(units,token_path):
    for unit in units:
        print('REFRESHER_UNIT='+unit,flush=True)
        if '@.' in unit:
            print('REFRESHER_INSPECTION=SKIPPED UNINSTANTIATED_TEMPLATE=true')
            continue
        stage='EXEC_START'
        try:
            start=run(['systemctl','show',unit,'--property=ExecStart','--value'])
            paths=sorted(set(re.findall(r'(/[A-Za-z0-9_./-]+\\.py)(?=\\s|;|$)',start)))
            print('REFRESHER_PYTHON_SCRIPT_COUNT='+str(len(paths)))
            for source in paths:
                stage='SCRIPT_METADATA'
                file=Path(source);metadata=file.lstat()
                if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid!=0 or metadata.st_mode&0o022:
                    raise RuntimeError('REFRESHER_SCRIPT_UNSAFE')
                stage='SCRIPT_AST'
                text=file.read_text()
                facts=writer_facts(text)
                facts['execution_token_target_literal_present']=any(
                    isinstance(node,ast.Constant) and node.value==token_path for node in ast.walk(ast.parse(text)))
                print('REFRESHER_STRUCTURAL_FACTS='+json.dumps(facts,sort_keys=True))
        except Exception as error:
            print('REFRESHER_INSPECTION=UNAVAILABLE STAGE='+stage+' TYPE='+type(error).__name__)

def main(args):
    if os.geteuid()!=0:raise RuntimeError('ROOT_REQUIRED')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,159}',args.container):raise ValueError('container')
    matcher=re.compile(args.service_match)
    live=json.loads(run(['docker','inspect',args.container]))[0]
    env=dict(x.split('=',1) for x in live['Config'].get('Env',[]) if '=' in x)
    target=env.get('OUF_UDP_EXECUTION_TOKEN_FILE')
    print('UDP_EXECUTION_TOKEN_ENV_PRESENT='+str(bool(target)).lower(),flush=True)
    if not target:raise RuntimeError('EXPLICIT_EXECUTION_TOKEN_ENV_REQUIRED')
    path,file_bind=mapped(live,target)
    meta=path.stat()
    if not stat.S_ISREG(meta.st_mode):raise ValueError('regular')
    with path.open('rb') as stream:raw=stream.read(16385)
    value=raw.decode().strip()
    valid=bool(re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',value)) and len(raw)<=16384
    print('UDP_EXECUTION_TOKEN_FORMAT_VALID='+str(valid).lower())
    print('UDP_EXECUTION_TOKEN_FILE_BIND='+str(file_bind).lower())
    print('UDP_EXECUTION_TOKEN_AGE_SECONDS='+str(max(0,int(time.time()-meta.st_mtime))))
    if valid:
        part=value.split('.')[1];claims=json.loads(base64.urlsafe_b64decode(part+'='*(-len(part)%4)))
        print('UDP_EXECUTION_TOKEN_SERVICE_ACTOR='+str(claims.get('ouf_actor_type')=='SERVICE').lower())
        print('UDP_EXECUTION_TOKEN_TTL_SECONDS='+str(int(claims['exp']-time.time()) if type(claims.get('exp')) is int else 'INVALID'))
        for cap in ('ouf.onboarding.configuration.read','ouf.semantic.read'):
            print('UDP_EXECUTION_TOKEN_SCOPE_'+cap+'='+str(cap in str(claims.get('scope','')).split()).lower())
    units=[]
    for line in run(['systemctl','list-unit-files','--type=service','--no-legend','--no-pager']).splitlines():
        name=line.split()[0]
        if re.fullmatch(r'[A-Za-z0-9_.@-]+\.service',name) and matcher.search(name):units.append(name)
    print('UDP_TOKEN_REFRESHER_SERVICE_COUNT='+str(len(units)))
    inspect_services(units,str(path))
    print('R4A_UDP_TOKEN_TRANSPORT_INVENTORY=COMPLETE READ_ONLY=true TOKEN_REFRESH_NOT_TRIGGERED=true SCRIPT_VALUES_NOT_PRINTED=true CAUSALITY_NOT_PROVEN=true')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--container',required=True)
    parser.add_argument('--service-match',required=True)
    try:main(parser.parse_args())
    except Exception as error:
        print('R4A_UDP_TOKEN_TRANSPORT_INVENTORY=BLOCKED TYPE='+type(error).__name__+' READ_ONLY=true SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
