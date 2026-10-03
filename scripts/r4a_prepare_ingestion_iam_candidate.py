#!/usr/bin/env python3
"""Build a pinned generic Ingestion release and prepare a stopped IAM candidate."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
from urllib.parse import urlparse
import r4a_prepare_frozen_compatibility_probe as probe
import r4a_prepare_ingestion_candidate as clone
from r4a_ingestion_iam_inventory import external_config_status

ROOT = clone.ROOT
STATE = ROOT / 'ingestion-iam-release-prepare.json'
NAME = 'ouf-ingestion-r4a-iam-candidate'
BRANCH = 'codex/r4a-governed-record-retry'


def content_for(original, env, issuer, audience):
    if not external_config_status(env)[1] or env.get('SPRING_APPLICATION_JSON'):
        raise RuntimeError('ING_IAM_CONFIG_SOURCE_UNSUPPORTED')
    if any(re.sub(r'[^a-z0-9]', '', k.lower()).startswith(('oufingiam', 'oufingestioniam')) for k in env):
        raise RuntimeError('ING_IAM_ENV_ALREADY_PRESENT')
    text = original.decode('utf-8')
    # Java properties continuations/escaped keys require another parser and review.
    if '\\' in text:
        raise RuntimeError('ING_PROPERTIES_ESCAPES_REVIEW_REQUIRED')
    keys = []
    for line in text.splitlines():
        if line.lstrip().startswith(('#', '!')) or not line.strip():
            continue
        key = re.split(r'[\s=:]', line.strip(), maxsplit=1)[0]
        normalized = re.sub(r'[^a-z0-9]', '', key.lower())
        keys.append(normalized)
        if normalized.startswith(('oufingestioniam', 'springconfig')) or normalized == 'springapplicationjson':
            raise RuntimeError('ING_IAM_PROPERTY_OR_IMPORT_ALREADY_PRESENT')
    if len(keys) != len(set(keys)):
        raise RuntimeError('ING_PROPERTIES_DUPLICATE_KEYS')
    for loop in ('activation', 'execution'):
        if probe.literal_property(text, 'ouf.ingestion.' + loop + '.enabled') != 'true':
            raise RuntimeError('ING_BOTH_LOOPS_REQUIRED')
    values = {'enabled': 'true', 'issuer': issuer, 'audience': audience}
    return original + b'\n' + ''.join('ouf.ingestion.iam.'+k+'='+v+'\n' for k,v in values.items()).encode()


def main(args):
    if os.geteuid() != 0:
        raise RuntimeError('ROOT_REQUIRED')
    os.umask(0o077)
    for value in (args.revision, args.expected_live_revision):
        if not re.fullmatch(r'[a-f0-9]{40}', value):
            raise RuntimeError('REVISION_INVALID')
    issuer = urlparse(args.issuer)
    if (issuer.scheme != 'https' or not issuer.hostname or issuer.username or issuer.password
            or issuer.query or issuer.fragment or any(c in args.issuer for c in '\r\n\\')):
        raise RuntimeError('ISSUER_INVALID')
    if not re.fullmatch(r'[A-Za-z0-9._:/-]{1,200}', args.audience):
        raise RuntimeError('AUDIENCE_INVALID')
    metadata = ROOT.lstat()
    if not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != 0 or stat.S_IMODE(metadata.st_mode) != 0o700:
        raise RuntimeError('ING_STAGE_DIRECTORY_UNSAFE')
    if STATE.exists() or STATE.is_symlink() or clone.optional(NAME) is not None:
        raise RuntimeError('ING_IAM_CANDIDATE_ALREADY_PRESENT_REVIEW_RECEIPT')
    live = probe.inspect('ouf-ingestion')
    old_image = probe.inspect(live['Image'], 'image')
    if not live['State']['Running'] or old_image['Config'].get('Labels', {}).get('org.opencontainers.image.revision') != args.expected_live_revision:
        raise RuntimeError('ING_LIVE_REVISION_DRIFT')
    clone.guard(live, old_image)
    env = clone.environment(live)
    if set(live['NetworkSettings']['Networks']) != {'ouf-backend'} or live['HostConfig']['NetworkMode'] != 'ouf-backend':
        raise RuntimeError('ING_LIVE_NETWORK_UNSUPPORTED')
    command = [*(live['Config'].get('Cmd') or []), *(live['Config'].get('Entrypoint') or [])]
    if any(re.search(r'ouf[._-]ingestion[._-]iam|spring[._-]config', str(x), re.I) for x in command):
        raise RuntimeError('ING_COMMAND_CONFIG_OVERRIDE')
    source = Path(next(m['Source'] for m in live['Mounts'] if m['Destination'] == probe.PROPERTIES))
    original = source.read_bytes()
    content = content_for(original, env, args.issuer, args.audience)
    manifest = json.loads(probe.MANIFEST.read_text())
    checkout = Path(manifest['modules']['ingestion']['worktree'])
    remote = probe.run(['git', '-C', str(checkout), 'remote', 'get-url', 'origin'])
    if remote not in ('https://github.com/GioNob/ouf-ingestion-runtime.git', 'https://github.com/GioNob/ouf-ingestion-runtime', 'git@github.com:GioNob/ouf-ingestion-runtime.git'):
        raise RuntimeError('ING_GIT_REMOTE_UNSUPPORTED')
    probe.run(['git', '-C', str(checkout), 'fetch', '--no-tags', 'origin', BRANCH], timeout=180)
    if probe.run(['git', '-C', str(checkout), 'rev-parse', 'FETCH_HEAD']) != args.revision:
        raise RuntimeError('ING_TARGET_BRANCH_HEAD_DRIFT')
    probe.run(['git', '-C', str(checkout), 'merge-base', '--is-ancestor', args.expected_live_revision, args.revision])
    folder = Path(tempfile.mkdtemp(prefix='ingestion-iam-', dir=ROOT))
    worktree = folder / 'source'
    probe.run(['git', '-C', str(checkout), 'worktree', 'add', '--detach', str(worktree), args.revision])
    baseline = probe.run(['git', '-C', str(checkout), 'ls-tree', '-r', args.expected_live_revision, '--', 'src/main/resources/db/migration'])
    target = probe.run(['git', '-C', str(worktree), 'ls-tree', '-r', 'HEAD', '--', 'src/main/resources/db/migration'])
    if not baseline or baseline != target:
        raise RuntimeError('ING_MIGRATIONS_CHANGED_REVIEW_REQUIRED')
    version = probe.run(['docker', 'exec', 'ouf-postgres', 'psql', '-X', '-qAt', '-v', 'ON_ERROR_STOP=1', '-U', 'ouf_ingestion', '-d', 'ouf_ingestion', '-c', 'begin read only; select version from ouf_ingestion.flyway_schema_history order by installed_rank desc limit 1; rollback;'])
    if version != '14':
        raise RuntimeError('ING_FLYWAY14_DRIFT')
    tag = 'ouf-ingestion:r4a-iam-' + args.revision[:12]
    print('R4A_INGESTION_IAM_CANDIDATE=BUILDING LIVE_UNCHANGED=true', flush=True)
    with (folder / 'build.log').open('w') as log:
        subprocess.run(['docker', 'build', '--label', 'org.opencontainers.image.revision='+args.revision, '--tag', tag, str(worktree)], check=True, stdout=log, stderr=subprocess.STDOUT, timeout=1800)
    image = probe.inspect(tag, 'image')
    if image['Config'].get('Labels', {}).get('org.opencontainers.image.revision') != args.revision:
        raise RuntimeError('ING_IMAGE_REVISION_MISMATCH')
    clone.guard(live, image)
    if image['Config'].get('User') != '10002:10002':
        raise RuntimeError('ING_IMAGE_USER_MISMATCH')
    properties = folder / 'ingestion-summary.properties'
    properties.write_bytes(content)
    os.chown(properties, 0, 10002)
    properties.chmod(0o440)
    env_path = folder / 'candidate.env'
    created = None
    try:
        env_path.write_text('\n'.join(live['Config']['Env'])+'\n')
        cmd = ['docker', 'create', '--name', NAME, '--network', 'ouf-backend', '--network-alias', 'ouf-ingestion', '--restart', 'no', '--user', '10002:10002', '--log-driver', 'json-file', '--env-file', str(env_path)]
        cmd.extend(clone.memory_flags(live['HostConfig']))
        for k,v in live['HostConfig']['LogConfig'].get('Config', {}).items():
            cmd.extend(['--log-opt', k+'='+v])
        for _,src,dst,_ in clone.mounts(live, properties):
            cmd.extend(['--mount', 'type=bind,src='+src+',dst='+dst+',readonly'])
        cmd.append(image['Id'])
        if clone.stable(probe.inspect('ouf-ingestion')) != clone.stable(live) or source.read_bytes() != original:
            raise RuntimeError('ING_LIVE_DRIFT')
        created = probe.run(cmd)
        candidate = probe.inspect(NAME)
        if not clone.matches(candidate, live, image, properties) or candidate['Id'] != created:
            raise RuntimeError('ING_CANDIDATE_READBACK_MISMATCH')
        if clone.stable(probe.inspect('ouf-ingestion')) != clone.stable(live) or source.read_bytes() != original:
            raise RuntimeError('ING_LIVE_DRIFT')
        value = {'status':'PASS','revision':args.revision,'expectedLiveRevision':args.expected_live_revision,'old':live,'imageId':image['Id'],'candidateId':created,'candidateName':NAME,'properties':str(properties),'propertiesSha256':hashlib.sha256(content).hexdigest(),'originalPropertiesSha256':hashlib.sha256(original).hexdigest(),'issuer':args.issuer,'audience':args.audience,'flyway':'14','deployed':False}
        staged = folder / 'state.json'
        staged.write_text(json.dumps(value, sort_keys=True)+'\n')
        os.link(staged, STATE)
    except BaseException:
        if created:
            current = clone.optional(NAME)
            if current is not None and current['Id'] == created and not current['State']['Running']:
                probe.run(['docker', 'rm', created])
        raise
    finally:
        env_path.unlink(missing_ok=True)
    print('R4A_INGESTION_IAM_CANDIDATE=PASS STOPPED=true ENV_PRESERVED=true BOTH_LOOPS_PRESERVED=true MIGRATIONS_UNCHANGED=true')
    print('R4A_INGESTION_IAM_CANDIDATE_STATE='+str(STATE)+' PRIVATE=true')
    print('R4A_INGESTION_IAM_PREPARE=COMPLETE LIVE_UNCHANGED=true WORKLOAD_TOKEN_UNCHANGED=true RETRY=false RUN_RESUME=false SOURCE_ACTIVATION=false OWNER_AUTHORIZATION_NOT_PROVEN=true SECRETS_NOT_PRINTED=true')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('revision','expected-live-revision','issuer','audience'):
        parser.add_argument('--'+name, required=True)
    try:
        main(parser.parse_args())
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('R4A_INGESTION_IAM_PREPARE=BLOCKED CODE='+code+' RETRY=false RUN_RESUME=false SECRETS_NOT_PRINTED=true')
        raise SystemExit(1)
