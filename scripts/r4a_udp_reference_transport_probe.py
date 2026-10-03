#!/usr/bin/env python3
"""GET-only UDP-bound publication/Semantic transport probe using persisted exact refs."""
import argparse
import json
import os
import re
import uuid
from urllib.parse import urlsplit,quote
import r4a_udp_token_transport_inventory as inventory


def check(label,value):
    print(label+'='+str(bool(value)).lower(),flush=True)
    if not value:raise RuntimeError('PIN_CHECK_FAILED')


def get(args,gateway,token_path,path,label):
    with token_path.open('rb') as stream:raw=stream.read(16385)
    token=raw.decode().strip()
    if len(raw)>16384 or not re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',token):
        raise RuntimeError('TOKEN_READ_INVALID')
    config=('silent\nshow-error\nmax-time = 10\nmax-filesize = 2097152\nrequest = "GET"\n'
            'header = "Authorization: Bearer '+token+'"\nheader = "Accept: application/json"\n'
            'url = '+json.dumps(gateway+path)+'\nwrite-out = "\\n%{http_code}"\n')
    import subprocess
    raw=subprocess.run(['docker','run','--rm','-i','--read-only','--cap-drop','ALL',
        '--security-opt','no-new-privileges','--network',args.network,args.curl_image,
        '--config','-'],input=config,check=True,capture_output=True,text=True,timeout=20).stdout.strip()
    body,sep,status=raw.rpartition('\n')
    if not sep:body,status='',raw
    if not re.fullmatch(r'\d{3}',status):raise RuntimeError('HTTP_STATUS_INVALID')
    print(label+'_HTTP='+status,flush=True)
    if status!='200':raise RuntimeError('OWNER_GET_UNAVAILABLE')
    value=json.loads(body)
    if not isinstance(value,dict):raise RuntimeError('OWNER_RESPONSE_SHAPE')
    return value


def compare(refs,bundle):
    execution=bundle['extractionProfile']['runtime']['execution']
    keys=('sourceSchemaRef','semanticPublicationSetRef','adapterProfileRef',
          'mappingRefs','authorityPolicyRef','relationshipResolutionStrategyRefs')
    return all(execution.get(key)==refs.get(key) for key in keys)


def main(args):
    if os.geteuid()!=0:raise RuntimeError('ROOT_REQUIRED')
    args.run=str(uuid.UUID(args.run))
    for value in (args.source,args.container,args.postgres_container,args.database,args.db_user):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,159}',value):raise ValueError('identifier')
    for value in (args.network,args.curl_image):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/@-]{0,255}',value):raise ValueError('transport')
    live=json.loads(inventory.run(['docker','inspect',args.container]))[0]
    env=dict(x.split('=',1) for x in live['Config'].get('Env',[]) if '=' in x)
    gateway=env.get('OUF_UDP_EXECUTION_GATEWAY_URL','').rstrip('/')
    parsed=urlsplit(gateway)
    if (parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.path or parsed.query or parsed.fragment or any(c.isspace() for c in gateway)):
        raise RuntimeError('SUPPORTED_GATEWAY_BINDING_REQUIRED')
    token_path,_=inventory.mapped(live,env.get('OUF_UDP_EXECUTION_TOKEN_FILE',''))
    sql=("begin read only; set local statement_timeout='15s'; select coalesce(json_agg(r),'[]'::json) "
        "from (select distinct payload_json->'contractRefs' r from ouf_udp.handoff_intake "
        "where source_id='"+args.source+"' and ingestion_run_id='"+args.run+"') q; rollback;")
    rows=json.loads(inventory.run(['docker','exec',args.postgres_container,'psql','-X','-qAt','-v',
        'ON_ERROR_STOP=1','-U',args.db_user,'-d',args.database,'-c',sql]))
    if len(rows)!=1 or not isinstance(rows[0],dict):raise RuntimeError('ONE_EXACT_REF_GROUP_REQUIRED')
    refs=rows[0];ref=refs.get('bundleRef')
    if not isinstance(ref,str) or not ref or len(ref)>2048:raise RuntimeError('BUNDLE_REF_INVALID')
    print('R4A_UDP_REFERENCE_TRANSPORT_PROBE=GET_ONLY',flush=True)
    envelope=get(args,gateway,token_path,'/api/onboarding/v1/runtime/publications/resolve?bundleRef='+quote(ref,safe=''),'UDP_PUBLICATION')
    bundle=envelope['bundle']
    check('UDP_PUBLICATION_SOURCE_MATCH',envelope.get('sourceId')==args.source)
    check('UDP_PUBLICATION_ENVELOPE_CHECKSUM_MATCH',bundle.get('checksum')==envelope.get('checksum'))
    check('UDP_PUBLICATION_EXACT_REF_MATCH',ref==str(bundle.get('bundleId'))+':'+str(bundle.get('bundleVersion'))+':'+str(bundle.get('checksum')))
    check('UDP_PUBLICATION_EXECUTION_REFS_MATCH',compare(refs,bundle))
    bindings=bundle.get('semanticReferenceBindings')
    if not isinstance(bindings,list) or not 1<=len(bindings)<=20:raise RuntimeError('BINDINGS_SHAPE')
    found=False
    for index,binding in enumerate(bindings,1):
        revision=str(uuid.UUID(binding['revisionId']));publication=str(uuid.UUID(binding['publicationSetId']))
        semantic=binding['semanticId']
        if not isinstance(semantic,str) or not 1<=len(semantic)<=2048:raise RuntimeError('SEMANTIC_ID_INVALID')
        response=get(args,gateway,token_path,'/api/semantic/v1/references:resolve?semanticId='+quote(semantic,safe='')+'&revisionId='+revision+'&publicationSetId='+publication,'UDP_SEMANTIC_'+str(index))
        check('UDP_SEMANTIC_'+str(index)+'_PIN_MATCH',
            response.get('semantic_id')==semantic and response.get('semantic_version')==binding.get('semanticVersion')
            and response.get('revision_id')==revision and response.get('publication_set_id')==publication)
        found|=publication==refs.get('semanticPublicationSetRef')
    check('UDP_SEMANTIC_HANDOFF_PUBLICATION_FOUND',found)
    print('R4A_UDP_REFERENCE_TRANSPORT_PROBE=PASS GET_ONLY=true RETRY=false MATERIALIZATION=false JAVA_PROFILE_VALIDATION_NOT_PROVEN=true VALUES_NOT_PRINTED=true')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('run','source','container','postgres-container','database','db-user','network','curl-image'):
        parser.add_argument('--'+name,required=True)
    try:main(parser.parse_args())
    except Exception as error:
        print('R4A_UDP_REFERENCE_TRANSPORT_PROBE=BLOCKED TYPE='+type(error).__name__+' BUSINESS_STATE_UNCHANGED=true SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
