#!/usr/bin/env python3
"""Isolated GET-only resolver diagnostic using classes from the running UDP jar."""
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
import uuid
import zipfile
from urllib.parse import urlsplit
import r4a_udp_token_transport_inventory as inventory

JAVA = r'''package it.comune.trieste.ouf.udp;
import com.fasterxml.jackson.databind.*;
import org.springframework.http.converter.json.Jackson2ObjectMapperBuilder;
import java.nio.file.*;
import java.util.*;
public final class R4aReadOnlyReferenceProbe {
  public static void main(String[] args) {
    try {
      ObjectMapper json=Jackson2ObjectMapperBuilder.json()
        .featuresToDisable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS).build();
      @SuppressWarnings("unchecked") Map<String,Object> refs=json.readValue(Files.readAllBytes(Path.of(args[3])),Map.class);
      var resolver=new PublishedRuntimeConfiguration(json,args[0],args[1],args[2]);
      var result=resolver.resolveContracts(refs);
      if(!result.ready())throw new IllegalStateException("UDP_PROBE_REFERENCES_NOT_READY");
      System.out.println("UDP_SHIPPED_JAVA_RESOLVE_CONTRACTS=PASS");
      System.out.println("R4A_UDP_JAVA_REFERENCE_PROBE=PASS GET_ONLY=true SPRING_STARTED=false MATERIALIZATION=false RETRY=false MAPPER_RUNTIME_PARITY_NOT_PROVEN=true HISTORICAL_CAUSALITY_NOT_PROVEN=true VALUES_NOT_PRINTED=true");
    } catch(Exception error) {
      String message=error.getMessage();
      Set<String> safe=Set.of("UDP_PINNED_PROFILE_INVALID","UDP_GOVERNED_IDENTITY_PROFILE_INVALID",
        "UDP_RESOLUTION_PROFILE_UNSUPPORTED","UDP_GATEWAY_INVALID","UDP_PUBLICATION_UNAVAILABLE",
        "UDP_PUBLICATION_INTERRUPTED","UDP_PROBE_REFERENCES_NOT_READY");
      String kind=error instanceof IllegalArgumentException?"IllegalArgumentException":
        error instanceof IllegalStateException?"IllegalStateException":"OTHER";
      System.out.println("UDP_JAVA_EXCEPTION_TYPE="+kind);
      System.out.println("UDP_JAVA_SAFE_CODE="+(message!=null&&safe.contains(message)?message:"UNCLASSIFIED"));
      int count=0;
      for(StackTraceElement frame:error.getStackTrace()) {
        if(frame.getClassName().startsWith("it.comune.trieste.ouf.udp.")&&count++<4)
          System.out.println("UDP_JAVA_FRAME="+frame.getClassName()+"#"+frame.getMethodName()+":"+frame.getLineNumber());
      }
      System.out.println("R4A_UDP_JAVA_REFERENCE_PROBE=BLOCKED GET_ONLY=true BUSINESS_STATE_UNCHANGED=true SECRETS_NOT_PRINTED=true");
      System.exit(2);
    }
  }
}
'''


def extract(jar, destination):
    """Extract only byte-identical application classes and dependencies, bounded."""
    with zipfile.ZipFile(jar) as archive:
        selected=[];total=0
        for entry in archive.infolist():
            if entry.is_dir():continue
            if not entry.filename.startswith(('BOOT-INF/classes/','BOOT-INF/lib/')):continue
            relative=PurePosixPath(entry.filename)
            if '..' in relative.parts or relative.is_absolute() or '\\' in entry.filename:
                raise ValueError('JAR_PATH_UNSAFE')
            total+=entry.file_size
            if total>512*1024*1024 or len(selected)>=30000:raise ValueError('JAR_LIMIT')
            selected.append(entry)
        required='BOOT-INF/classes/it/comune/trieste/ouf/udp/PublishedRuntimeConfiguration.class'
        if required not in [entry.filename for entry in selected]:raise ValueError('RESOLVER_ABSENT')
        for entry in selected:
            target=destination/entry.filename
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(archive.read(entry))
            target.chmod(0o644)
        for directory in destination.rglob('*'):
            if directory.is_dir():directory.chmod(0o755)


def invoke(argv, timeout=30):
    return subprocess.run(argv,check=True,capture_output=True,text=True,timeout=timeout).stdout.strip()


def main(args):
    if os.geteuid()!=0:raise RuntimeError('ROOT_REQUIRED')
    args.run=str(uuid.UUID(args.run))
    for value in (args.source,args.container,args.postgres_container,args.database,args.db_user):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,159}',value):raise ValueError('identifier')
    for value in (args.network,args.jdk_image):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/@-]{0,255}',value):raise ValueError('binding')
    if not re.fullmatch(r'/[A-Za-z0-9_./-]+\.jar',args.jar_path) or '..' in Path(args.jar_path).parts:
        raise ValueError('jar path')
    live=json.loads(inventory.run(['docker','inspect',args.container]))[0]
    if not live.get('State',{}).get('Running'):raise RuntimeError('UDP_NOT_RUNNING')
    image=live['Image'];user=live['Config'].get('User','')
    if not re.fullmatch(r'sha256:[a-f0-9]{64}',image):raise ValueError('image')
    if not re.fullmatch(r'[1-9][0-9]*:[1-9][0-9]*',user):raise ValueError('NUMERIC_NONROOT_USER_REQUIRED')
    uid,gid=map(int,user.split(':'))
    env=dict(x.split('=',1) for x in live['Config'].get('Env',[]) if '=' in x)
    gateway=env.get('OUF_UDP_EXECUTION_GATEWAY_URL','').rstrip('/')
    parsed=urlsplit(gateway)
    if (parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.path or parsed.query or parsed.fragment or any(c.isspace() for c in gateway)):
        raise ValueError('HTTPS_ORIGIN_REQUIRED')
    tenant=env.get('OUF_UDP_LAKE_TENANT_ID',env.get('OUF_UDP_TENANT_ID',''))
    if not tenant or any(c.isspace() for c in tenant):raise ValueError('TENANT_ENV_REQUIRED')
    token,file_bind=inventory.mapped(live,env.get('OUF_UDP_EXECUTION_TOKEN_FILE',''))
    if file_bind or token.is_symlink():raise ValueError('DIRECTORY_TOKEN_BIND_REQUIRED')
    if ',' in str(token.parent) or ',' in token.name:raise ValueError('mount path')
    sql=("begin read only; set local statement_timeout='15s'; select coalesce(json_agg(r),'[]'::json) "
         "from (select distinct payload_json->'contractRefs' r from ouf_udp.handoff_intake "
         "where source_id='"+args.source+"' and ingestion_run_id='"+args.run+"') q; rollback;")
    rows=json.loads(inventory.run(['docker','exec',args.postgres_container,'psql','-X','-qAt','-v',
        'ON_ERROR_STOP=1','-U',args.db_user,'-d',args.database,'-c',sql]))
    if len(rows)!=1 or not isinstance(rows[0],dict):raise ValueError('ONE_REF_GROUP_REQUIRED')
    encoded=json.dumps(rows[0]).encode()
    if len(encoded)>65536:raise ValueError('REF_LIMIT')
    # No implicit compiler image pull. Operator explicitly provisions the JDK image.
    compiler=json.loads(inventory.run(['docker','image','inspect',args.jdk_image]))[0]['Id']
    if not re.fullmatch(r'sha256:[a-f0-9]{64}',compiler):raise ValueError('compiler image')
    print('R4A_UDP_JAVA_REFERENCE_PROBE=GET_ONLY',flush=True)
    print('UDP_JAVA_LIVE_IMAGE_ID='+image,flush=True)
    print('UDP_JAVA_COMPILER_IMAGE_ID='+compiler,flush=True)
    with tempfile.TemporaryDirectory(prefix='ouf-r4a-java-') as temporary:
        root=Path(temporary);root.chmod(0o711)
        jar=root/'runtime.jar'
        invoke(['docker','cp',args.container+':'+args.jar_path,str(jar)])
        extract(jar,root);jar.unlink()
        source=root/'R4aReadOnlyReferenceProbe.java';source.write_text(JAVA);source.chmod(0o644)
        refs=root/'refs.json';refs.write_bytes(encoded);os.chown(refs,uid,gid);refs.chmod(0o600)
        classes=root/'probe-classes';classes.mkdir(mode=0o755)
        common=['docker','run','--rm','--pull','never','--read-only','--cap-drop','ALL',
            '--security-opt','no-new-privileges','--tmpfs','/tmp:rw,nosuid,nodev,size=64m']
        cp='/probe/probe-classes:/probe/BOOT-INF/classes:/probe/BOOT-INF/lib/*'
        invoke(common+['--network','none','--user','0:0','--mount',
            'type=bind,src='+str(root)+',dst=/probe','--entrypoint','javac',compiler,
            '--release','21','-cp',cp,'-d','/probe/probe-classes','/probe/R4aReadOnlyReferenceProbe.java'],timeout=45)
        # Use the actual immutable live image and same numeric identity. No DB credentials/environment.
        process=subprocess.run(common+['--network',args.network,'--user',user,'--mount',
            'type=bind,src='+str(root)+',dst=/probe,readonly','--mount',
            'type=bind,src='+str(token.parent)+',dst=/probe-token,readonly','--entrypoint','java',image,
            '-cp',cp,'it.comune.trieste.ouf.udp.R4aReadOnlyReferenceProbe',gateway,
            '/probe-token/'+token.name,tenant,'/probe/refs.json'],capture_output=True,text=True,timeout=35)
        # Only protocol lines are released. Docker/JVM stderr and exception messages stay private.
        output=process.stdout.splitlines()
        for line in output:
            if re.fullmatch(r'(?:UDP_SHIPPED_JAVA_RESOLVE_CONTRACTS|UDP_JAVA_EXCEPTION_TYPE|UDP_JAVA_SAFE_CODE|UDP_JAVA_FRAME|R4A_UDP_JAVA_REFERENCE_PROBE)=[A-Za-z0-9_.#:= -]{1,700}',line):
                print(line,flush=True)
        if process.returncode!=0:raise RuntimeError('JAVA_PROBE_FAILED')
        if 'UDP_SHIPPED_JAVA_RESOLVE_CONTRACTS=PASS' not in output:raise RuntimeError('JAVA_PROTOCOL_MISSING')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('run','source','container','postgres-container','database','db-user','network','jdk-image','jar-path'):
        parser.add_argument('--'+name,required=True)
    try:main(parser.parse_args())
    except Exception as error:
        print('R4A_UDP_JAVA_REFERENCE_PROBE=BLOCKED TYPE='+type(error).__name__+' BUSINESS_STATE_UNCHANGED=true SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
