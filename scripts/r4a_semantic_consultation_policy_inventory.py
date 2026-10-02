#!/usr/bin/env python3
"""Read only native SERVICE and HUMAN consultation descriptors from registry and active policy."""
import argparse
import json
import os
from pathlib import Path
import sys
import r4a_release_semantic_consultation as release

SQL="""
begin read only;
select jsonb_build_object(
 'policyRef',a.bundle_id||':'||a.version,
 'publishedDescriptors',(select coalesce(jsonb_agg(jsonb_build_object(
   'capabilityId',c->>'capabilityId','operation',c->>'operation',
   'requiredScope',c->>'requiredScope','allowedActors',c->'allowedActors')),'[]'::jsonb)
   from jsonb_array_elements(p.bundle_payload->'capabilities') c
   where c->>'capabilityId' in ('ouf.semantic.search','ouf.semantic.read','ouf.semantic.consultation.read')),
 'registeredDescriptors',(select coalesce(jsonb_agg(jsonb_build_object(
   'capabilityId',r.capability_id,'ownerRef',r.owner_ref,
   'operation',r.descriptor->>'operation','requiredScope',r.descriptor->>'requiredScope',
   'allowedActors',r.descriptor->'allowedActors')),'[]'::jsonb)
   from ouf_authorization.capability_registration r
   where r.capability_id in ('ouf.semantic.search','ouf.semantic.read','ouf.semantic.consultation.read')))
from ouf_authorization.active_policy_bundle a
join ouf_authorization.policy_bundle p on p.bundle_id=a.bundle_id and p.version=a.version
where a.singleton_key=true;
commit;
"""


def main(args):
    release.require(os.geteuid()==0,'ROOT_REQUIRED')
    release.prep.private(args.stage_root,0o700)
    file=args.stage_root/'runtime-snapshot.json';release.prep.private(file,0o600)
    before=json.loads(file.read_text());old=before['live']|{'gateway':before['gateway']}
    for row in old.values():
        release.require(release.stage.fingerprint(release.stage.inspect(row['Id']))==release.stage.fingerprint(row),'STAGED_LIVE_DRIFT')
    pg,user,_=release.databases(args,old)
    raw=release.stage.run(['docker','exec',args.postgres_container,'psql','-X','-qAt',
        '-v','ON_ERROR_STOP=1','-U',user,'-d',database(args,pg),'-c',SQL])
    value=json.loads(raw)
    print('SEMANTIC_CONSULTATION_POLICY='+json.dumps(value,sort_keys=True),flush=True)
    print('SEMANTIC_CONSULTATION_POLICY_INVENTORY=PASS READ_ONLY=true NO_POLICY_CHANGED=true NO_SECRETS_PRINTED=true',flush=True)


def database(args,pg):
    # Authorization is owned by Onboarding, not by the Semantic/MCP database.
    from urllib.parse import urlsplit,unquote
    row=release.stage.inspect(args.onboarding_container)
    release.require(row['State']['Running'],'ONBOARDING_NOT_RUNNING')
    parsed=urlsplit(release.prep.env(row)['OUF_ONB_DB_URL'].removeprefix('jdbc:'))
    allowed={args.postgres_container,pg['Name'].lstrip('/')}
    for n in pg['NetworkSettings']['Networks'].values():allowed.update(n.get('Aliases') or [])
    name=unquote(parsed.path.lstrip('/'))
    release.require(parsed.scheme=='postgresql' and parsed.hostname in allowed and parsed.port in (None,5432)
        and bool(release.re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,62}',name)),'AUTHORIZATION_DATABASE_BINDING_INVALID')
    return name


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage-root',type=Path,required=True)
    p.add_argument('--postgres-container',required=True)
    p.add_argument('--onboarding-container',required=True)
    try:
        args=p.parse_args();main(args)
    except Exception as error:
        code=str(error) if isinstance(error,RuntimeError) and release.re.fullmatch('[A-Z_]{1,80}',str(error)) else type(error).__name__
        print('SEMANTIC_CONSULTATION_POLICY_INVENTORY=BLOCKED CODE='+code+' NO_POLICY_CHANGED=true',flush=True)
        sys.exit(1)
