#!/usr/bin/env python3
"""Prepare source-independent HUMAN recovery descriptors and an add-only draft.

Deployment OIDC/base endpoints use the existing authorization lifecycle helper.
No publication, Keycloak changes, routes, retry or resume. Grants target the
explicit administrator subject and tenant, with an explicit validity window.
"""
import argparse
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import time
import uuid
from urllib.request import HTTPRedirectHandler, build_opener
import r4a_authorization_lifecycle as policy
import r4a_register_capabilities as registry

ROOT = Path('/etc/ouf/deploy-snapshots')
STATE = ROOT / 'ingestion-recovery-policy-draft.json'
CAPABILITIES = ('ingestion.run.read', 'ingestion.run.resume',
                'ingestion.quarantine.read', 'ouf.ingestion.quarantine.retry')

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def descriptors():
    return [dict(capabilityId=c, operation='READ' if c.endswith('.read') else 'WRITE',
                 requiredScope=c, allowedActors=['HUMAN']) for c in CAPABILITIES]

def grant_rows(tenant, subject, valid_until, now=None):
    when = now or datetime.now(timezone.utc)
    end = datetime.fromisoformat(valid_until.replace('Z', '+00:00'))
    if end.tzinfo is None or end <= when:
        raise RuntimeError('RECOVERY_GRANT_VALIDITY_INVALID')
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', tenant):
        raise RuntimeError('RECOVERY_TENANT_INVALID')
    subject = str(uuid.UUID(subject))
    return [dict(grantId='grant-recovery-'+c.replace('.', '-')+'-'+tenant+'-'+subject,
                 capabilityId=c, tenantId=tenant, subjectId=subject,
                 servicePrincipalId=None, organizationId=None,
                 validFrom=when.isoformat().replace('+00:00', 'Z'),
                 validUntil=end.isoformat().replace('+00:00', 'Z'), constraints=None)
            for c in CAPABILITIES]

def build(current, desired, additions):
    candidate, missing = policy.build_candidate(current, desired)
    if missing != desired:
        raise RuntimeError('RECOVERY_CAPABILITIES_ALREADY_ACTIVE_RECONCILE')
    old = current['policy']['grants']
    if ({g['grantId'] for g in old} & {g['grantId'] for g in additions} or
        any(g.get('capabilityId') in CAPABILITIES for g in old)):
        raise RuntimeError('RECOVERY_GRANTS_ALREADY_PRESENT_RECONCILE')
    candidate['grants'] = [*old, *additions]
    return candidate

def normalize_grant(row):
    return {**row, 'constraints': row.get('constraints')}

def preview_check(preview, desired, additions):
    actual = [policy.normalize_descriptor(d) for d in preview.get('addedCapabilities', [])]
    if sorted(actual, key=lambda d:d['capabilityId']) != sorted(desired, key=lambda d:d['capabilityId']) or preview.get('removedCapabilities'):
        raise RuntimeError('RECOVERY_PREVIEW_CAPABILITY_DIFF_MISMATCH')
    changes = preview.get('grantChanges', [])
    expected = {g['grantId']:normalize_grant(g) for g in additions}
    actual = {g.get('grantId'):normalize_grant(g['after']) for g in changes}
    if len(changes) != len(expected) or actual != expected or any(g.get('before') is not None for g in changes):
        raise RuntimeError('RECOVERY_PREVIEW_GRANT_DIFF_MISMATCH')

def write(state, exclusive=False):
    if exclusive:
        fd = os.open(STATE, os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW, 0o600)
        temporary = None
    else:
        fd, name = tempfile.mkstemp(prefix='.recovery-policy-', dir=ROOT)
        temporary = Path(name)
    with os.fdopen(fd, 'w') as stream:
        json.dump(state, stream, sort_keys=True)
        stream.flush(); os.fsync(stream.fileno())
    if temporary:
        os.replace(temporary, STATE)
    fd = os.open(ROOT, os.O_RDONLY|os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)

def catalogue(token):
    result = {}
    for offset in range(0, 100001, 200):
        _, raw = registry.request(policy.DEFAULT_BASE+'/capabilities?limit=200&offset='+str(offset), token)
        page = json.loads(raw)
        if not isinstance(page, list) or len(page)>200:
            raise RuntimeError('RECOVERY_CATALOGUE_PAGE_UNSUPPORTED')
        for row in page:
            ident = row.get('capability_id')
            if not isinstance(ident, str) or ident in result:
                raise RuntimeError('RECOVERY_CATALOGUE_DUPLICATE_ID')
            result[ident] = row
        if len(page)<200:
            return result
    raise RuntimeError('RECOVERY_CATALOGUE_PAGINATION_LIMIT')

def check_registered(row, wanted):
    value = row.get('descriptor')
    if isinstance(value, dict) and value.get('type')=='jsonb': value = value.get('value')
    if isinstance(value, str): value = json.loads(value)
    if row.get('owner_ref')!='ingestion' or policy.normalize_descriptor(value)!=wanted:
        raise RuntimeError('RECOVERY_REGISTERED_DESCRIPTOR_CONFLICT')

def login(tenant, subject):
    # Claim checks are defensive diagnostics; authorization is enforced by the owner APIs.
    policy.urllib.request.urlopen = build_opener(NoRedirect()).open
    token = registry.device_login()
    if not isinstance(token, str) or len(token)>16384 or token.count('.')!=2:
        raise RuntimeError('RECOVERY_HUMAN_TOKEN_INVALID')
    part = token.split('.')[1]
    claims = json.loads(base64.urlsafe_b64decode(part+'='*(-len(part)%4)))
    aud = claims.get('aud', [])
    if isinstance(aud, str): aud = [aud]
    if not (claims.get('iss')==policy.ISSUER and claims.get('azp')=='ouf-human-admin'
            and claims.get('sub')==subject and claims.get('tenant_id')==tenant
            and claims.get('ouf_actor_type') in ('HUMAN', 'HUMAN_USER')
            and 'ouf-api-gateway' in aud
            and 'authorization.policy.admin' in str(claims.get('scope', '')).split()
            and isinstance(claims.get('exp'), int) and claims['exp']>time.time()+60):
        raise RuntimeError('RECOVERY_HUMAN_IDENTITY_OR_SCOPE_MISMATCH')
    return token

def main(args):
    if os.geteuid()!=0: raise RuntimeError('ROOT_REQUIRED')
    os.umask(0o077)
    meta = ROOT.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid!=0 or stat.S_IMODE(meta.st_mode)!=0o700:
        raise RuntimeError('PRIVATE_ROOT_UNSAFE')
    if STATE.exists() or STATE.is_symlink():
        raise RuntimeError('RECOVERY_STATE_EXISTS_RECONCILE_DO_NOT_REPOST')
    subject = str(uuid.UUID(args.subject))
    desired = descriptors()
    additions = grant_rows(args.tenant, subject, args.valid_until)
    token = login(args.tenant, subject)
    current = policy.active(policy.DEFAULT_BASE, token)
    if current.get('policyRef')!=args.expected_base:
        raise RuntimeError('RECOVERY_EXPECTED_POLICY_BASELINE_DRIFT')
    candidate = build(current, desired, additions)
    registered = catalogue(token)
    for cap in desired:
        if cap['capabilityId'] in registered:
            check_registered(registered[cap['capabilityId']], cap)
    target = candidate['bundleId']+':'+str(candidate['version'])
    state = dict(status='STARTING', baseActiveRef=args.expected_base,
                 targetPolicyRef=target, baselinePolicy=current['policy'], candidate=candidate,
                 addedDescriptors=desired, addedGrants=additions, tenant=args.tenant,
                 subject=subject, registeredCapabilities=[])
    write(state, exclusive=True)
    for cap in desired:
        if cap['capabilityId'] not in registered:
            # Persist intent before every non-idempotent POST; reconcile after an uncertain response.
            state['status']='REGISTRATION_POST_UNVERIFIED_DO_NOT_REPOST'; write(state)
            status, _ = registry.request(policy.DEFAULT_BASE+'/capabilities', token, 'POST',
                                         dict(ownerRef='ingestion', descriptor=cap))
            if status!=201: raise RuntimeError('RECOVERY_REGISTRATION_NOT_201')
            state['registeredCapabilities'].append(cap['capabilityId']); write(state)
    registered = catalogue(token)
    for cap in desired: check_registered(registered[cap['capabilityId']], cap)
    if policy.active(policy.DEFAULT_BASE, token)!=current:
        raise RuntimeError('RECOVERY_POLICY_BASE_DRIFT')
    state['status']='DRAFT_POST_UNVERIFIED_DO_NOT_REPOST'; write(state)
    status, draft, headers = policy.request(policy.DEFAULT_BASE, token, '/policies', 'POST', candidate)
    etag = headers.get('ETag', '').strip('"')
    if status!=200 or not etag.isdigit(): raise RuntimeError('RECOVERY_DRAFT_RESPONSE_UNVERIFIED')
    state.update(draftId=str(uuid.UUID(draft['id'])), revision=int(etag), status='DRAFT_PREVIEW_PENDING'); write(state)
    _, preview, _ = policy.request(policy.DEFAULT_BASE, token, '/policies/'+state['draftId']+':preview', 'POST', etag=state['revision'])
    preview_check(preview, desired, additions)
    if policy.active(policy.DEFAULT_BASE, token)!=current:
        raise RuntimeError('RECOVERY_POLICY_BASE_DRIFT_AFTER_PREVIEW')
    state.update(status='PASS', preview=preview,
                 baselineCapabilitiesHash=policy.digest(current['policy']['capabilities']),
                 baselineGrantsHash=policy.digest(current['policy']['grants'])); write(state)
    print('R4A_RECOVERY_CAPABILITY_REGISTRATION=PASS COUNT=4 POLICY_UNPUBLISHED=true')
    print('R4A_RECOVERY_POLICY_DRAFT=PASS BASE='+args.expected_base+' TARGET='+target+' DRAFT_ID='+state['draftId']+' REVISION='+str(state['revision']))
    print('ADD_CAPABILITIES='+','.join(CAPABILITIES)+' ADD_GRANTS=4 EXISTING_ENTRIES_PRESERVED=true')
    print('ACTOR=HUMAN TENANT='+args.tenant+' SOURCE_SCOPE=ALL_TENANT_SOURCES SERVICE_GRANTS=0')
    print('VALID_UNTIL='+additions[0]['validUntil'])
    print('R4A_RECOVERY_POLICY_STATE='+str(STATE)+' PRIVATE=true')
    print('R4A_RECOVERY_POLICY_PREPARE=PASS POLICY_NOT_PUBLISHED=true IAM_UNCHANGED=true ROUTES_UNCHANGED=true RUN_RESUME=false RETRY=false SECRETS_NOT_PRINTED=true')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--expected-base', required=True)
    p.add_argument('--tenant', required=True)
    p.add_argument('--subject', required=True)
    p.add_argument('--valid-until', required=True)
    try: main(p.parse_args())
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_RECOVERY_POLICY_PREPARE=BLOCKED CODE='+code+' RECONCILE_IF_STATE_EXISTS=true POLICY_NOT_PUBLISHED=true RUN_RESUME=false RETRY=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
