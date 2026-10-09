#!/usr/bin/env python3
"""Read published HUMAN recovery descriptors/grants; no policy/IAM/route or run mutation."""
import argparse
import json
import os
from pathlib import Path
import re
import r4a_prepare_frozen_compatibility_probe as runtime

CAPABILITIES = ('ingestion.run.read','ingestion.run.resume','ingestion.quarantine.read','ouf.ingestion.quarantine.retry')


def objects(value):
    if isinstance(value,dict):
        yield value
        for child in value.values():
            yield from objects(child)
    elif isinstance(value,list):
        for child in value:
            yield from objects(child)


def safe(value):
    return str(value) if isinstance(value,(str,int)) and re.fullmatch(r'[A-Za-z0-9._:-]{1,160}',str(value)) else 'UNSUPPORTED_REDACTED'


def main(tenant):
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    live=runtime.inspect('ouf-ingestion')
    settings=runtime.transport_settings(live,tenant)
    mounts={m['Destination']:m for m in live['Mounts']}
    props=Path(mounts[runtime.PROPERTIES]['Source']).read_text()
    endpoint=runtime.literal_property(props,'ouf.authorization.registry-url')
    token_file=Path(mounts[runtime.AUTH]['Source']) / Path(settings['ouf.ingestion.activation.token-file']).relative_to(runtime.AUTH)
    token=token_file.read_text().strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',token):
        raise RuntimeError('TOKEN_FORMAT_INVALID')
    config='silent\nshow-error\nmax-time = 5\nmax-filesize = 2097152\nheader = "Authorization: Bearer '+token+'"\nurl = '+json.dumps(endpoint)+'\nwrite-out = "\\n%{http_code}"\n'
    raw=runtime.run(['docker','run','--rm','-i','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--network','ouf-backend','curlimages/curl:8.16.0','--config','-'],input=config,timeout=15)
    body,code=raw.rsplit('\n',1)
    print('R4A_RECOVERY_ACCESS_CATALOGUE=READ_ONLY HTTP='+code)
    if code != '200':
        raise RuntimeError('POLICY_READ_NOT_AUTHORIZED')
    policy=json.loads(body)
    print('RECOVERY_POLICY_REF='+safe(policy.get('bundleId'))+':'+safe(policy.get('bundleVersion')))
    all_objects=list(objects(policy))
    for capability in CAPABILITIES:
        relevant=[x for x in all_objects if x.get('capabilityId')==capability]
        descriptors=[x for x in relevant if 'requiredScope' in x and 'allowedActors' in x]
        grants=[x for x in relevant if 'grantId' in x]
        print('RECOVERY_CAPABILITY='+capability+' DESCRIPTOR_COUNT='+str(len(descriptors))+' GRANT_COUNT='+str(len(grants)))
        for descriptor in descriptors:
            actors=descriptor.get('allowedActors')
            human=isinstance(actors,list) and 'HUMAN' in actors
            print('RECOVERY_DESCRIPTOR_CAPABILITY='+capability+' OPERATION='+safe(descriptor.get('operation'))+' REQUIRED_SCOPE='+safe(descriptor.get('requiredScope'))+' HUMAN_ALLOWED='+str(human).lower())
        count=sum(x.get('tenantId')==tenant and bool(x.get('subjectId')) and not x.get('servicePrincipalId') for x in grants)
        print('RECOVERY_SUBJECT_BOUND_TENANT_GRANT_DIAGNOSTIC_COUNT='+str(count))
    after=runtime.inspect('ouf-ingestion')
    if any(after[k]!=live[k] for k in ('Id','Image','Config','HostConfig','Mounts')):
        raise RuntimeError('INGESTION_CONTEXT_CHANGED_DURING_READ')
    print('R4A_RECOVERY_ACCESS_CATALOGUE=COMPLETE READ_ONLY=true IAM_UNCHANGED=true ROUTES_UNCHANGED=true RUN_RESUME=false COUNTS_ARE_DIAGNOSTIC=true HUMAN_TOKEN_NOT_TESTED=true OWNER_AUTHORIZATION_NOT_PROVEN=true SECRETS_NOT_PRINTED=true')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tenant',required=True)
    try:
        main(parser.parse_args().tenant)
    except Exception as error:
        code=str(error) if isinstance(error,RuntimeError) else type(error).__name__
        print('R4A_RECOVERY_ACCESS_CATALOGUE=BLOCKED CODE='+code+' RUN_RESUME=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
