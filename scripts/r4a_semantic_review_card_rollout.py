#!/usr/bin/env python3
"""Replace the lab Semantic container from an exact commit, with automatic rollback.

Build and inspect the image before cutover. Compare every packaged Flyway
migration in the live and candidate JARs; a mismatch blocks the cutover.
The old container remains stopped under its backup name after success.
"""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import time
import zipfile

REPO = Path('/opt/ouf/semantic')
ROOT = Path('/etc/ouf/deploy-snapshots')
LIVE = 'ouf-semantic'
MIGRATIONS = 'BOOT-INF/classes/db/migration/'


class Blocked(RuntimeError):
    pass


def command(argv, *, stdin=None, capture=True):
    result = subprocess.run(argv, stdin=stdin,
                            stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, check=False)
    if result.returncode:
        raise Blocked('COMMAND_FAILED_' + Path(argv[0]).name.upper().replace('-', '_'))
    return result.stdout if capture else b''


def inspect(name):
    docs = json.loads(command(['docker', 'inspect', name]))
    if len(docs) != 1:
        raise Blocked('DOCKER_INSPECT_UNEXPECTED')
    return docs[0]


def exists(name):
    return subprocess.run(['docker', 'inspect', name], stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, check=False).returncode == 0


def migrations(jar):
    with zipfile.ZipFile(jar) as archive:
        names = [n for n in archive.namelist() if n.startswith(MIGRATIONS) and n.endswith('.sql')]
        if not names:
            raise Blocked('FLYWAY_MIGRATIONS_NOT_PACKAGED')
        return {n: archive.read(n) for n in names}


def readiness():
    for _ in range(30):
        live = inspect(LIVE)
        pid = live['State'].get('Pid', 0)
        if not live['State']['Running'] or pid <= 0:
            raise Blocked('NEW_CONTAINER_NOT_RUNNING')
        probe = subprocess.run(['nsenter', '-t', str(pid), '-n', sys.executable, '-c',
            'import urllib.request; assert urllib.request.urlopen("http://127.0.0.1:8080/actuator/health",timeout=3).status==200'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if probe.returncode == 0:
            return
        time.sleep(2)
    raise Blocked('SEMANTIC_HEALTH_TIMEOUT')


def rollback(old_id, new_id, backup, candidate):
    for name in (LIVE, candidate):
        if exists(name) and inspect(name)['Id'] == new_id:
            command(['docker', 'update', '--restart', 'no', name], capture=False)
            if inspect(name)['State']['Running']:
                command(['docker', 'stop', name], capture=False)
            command(['docker', 'rm', name], capture=False)
    if exists(LIVE) and inspect(LIVE)['Id'] == old_id:
        command(['docker', 'update', '--restart', 'unless-stopped', LIVE], capture=False)
        if not inspect(LIVE)['State']['Running']:
            command(['docker', 'start', LIVE], capture=False)
    elif not exists(LIVE) and exists(backup) and inspect(backup)['Id'] == old_id:
        command(['docker', 'rename', backup, LIVE], capture=False)
        command(['docker', 'update', '--restart', 'unless-stopped', LIVE], capture=False)
        command(['docker', 'start', LIVE], capture=False)
    if not exists(LIVE) or inspect(LIVE)['Id'] != old_id or not inspect(LIVE)['State']['Running']:
        raise Blocked('AUTOMATIC_ROLLBACK_INCOMPLETE')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('apply', 'rollback'))
    parser.add_argument('--revision')
    parser.add_argument('--state', type=Path)
    args = parser.parse_args()
    if args.mode == 'rollback':
        if os.geteuid() != 0 or args.state is None or args.state.parent != ROOT:
            raise Blocked('ROOT_AND_ROLLBACK_STATE_REQUIRED')
        meta = args.state.lstat()
        if not stat.S_ISREG(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o600:
            raise Blocked('ROLLBACK_STATE_UNSAFE')
        state = json.loads(args.state.read_text())
        if (not exists(LIVE) or inspect(LIVE)['Id'] != state['newId']
                or not exists(state['backup']) or inspect(state['backup'])['Id'] != state['oldId']):
            raise Blocked('ROLLBACK_CONTAINERS_CHANGED')
        rollback(state['oldId'], state['newId'], state['backup'],
                 'ouf-semantic-r4a-candidate-' + state['revision'][:7])
        readiness()
        print('SEMANTIC_REVIEW_CARD_ROLLBACK=PASS')
        return
    if os.geteuid() != 0 or not isinstance(args.revision, str) or not re.fullmatch('[0-9a-f]{40}', args.revision):
        raise Blocked('ROOT_AND_PINNED_REVISION_REQUIRED')
    meta = ROOT.lstat()
    if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != 0 or stat.S_IMODE(meta.st_mode) != 0o700:
        raise Blocked('SNAPSHOT_DIRECTORY_UNSAFE')
    safe = ['git', '-c', 'safe.directory=' + str(REPO), '-C', str(REPO)]
    if command([*safe, 'rev-parse', args.revision + '^{commit}']).decode().strip() != args.revision:
        raise Blocked('PINNED_SOURCE_UNAVAILABLE')
    old = inspect(LIVE)
    host, config = old['HostConfig'], old['Config']
    mounts = old.get('Mounts') or []
    if (not old['State']['Running'] or config.get('User') != '10001:10001'
            or host.get('NetworkMode') != 'ouf-backend'
            or host['RestartPolicy']['Name'] != 'unless-stopped'
            or host.get('Privileged') or host.get('PortBindings')
            or len(mounts) != 1 or mounts[0]['Type'] != 'bind' or mounts[0]['RW']
            or mounts[0]['Destination'] != '/run/ouf-semantic-auth'
            or (config.get('Entrypoint') or [])[-2:] != ['-jar', '/app/application.jar']):
        raise Blocked('SEMANTIC_RUNTIME_UNEXPECTED')
    backup = 'ouf-semantic-pre-r4a-' + args.revision[:7]
    candidate = 'ouf-semantic-r4a-candidate-' + args.revision[:7]
    if exists(backup) or exists(candidate):
        raise Blocked('ROLLOUT_CONTAINER_NAME_IN_USE')
    tag = 'ouf-semantic:r4a-' + args.revision[:7]
    os.umask(0o077)
    with tempfile.TemporaryDirectory(prefix='r4a-semantic-rollout-', dir=ROOT) as tmp:
        work = Path(tmp)
        archive = subprocess.Popen([*safe, 'archive', '--format=tar', args.revision],
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            build = subprocess.run(['docker', 'build', '--pull=false', '--quiet',
                '--label', 'org.opencontainers.image.revision=' + args.revision,
                '-t', tag, '-'], stdin=archive.stdout, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, check=False)
        finally:
            archive.stdout.close()
        if archive.wait() or build.returncode:
            raise Blocked('CANDIDATE_IMAGE_BUILD_FAILED')
        image = inspect(tag)
        if ((image['Config'].get('Labels') or {}).get('org.opencontainers.image.revision') != args.revision
                or image['Config'].get('User') != config.get('User')
                or image['Config'].get('Entrypoint') != config.get('Entrypoint')):
            raise Blocked('CANDIDATE_IMAGE_CONFIG_CHANGED')
        command(['docker', 'cp', LIVE + ':/app/application.jar', str(work / 'old.jar')], capture=False)
        # Create the stopped candidate to read its packaged migrations, then
        # retain it for the cutover after all checks pass.
        env_file = work / 'container.env'
        values = config.get('Env') or []
        if any('\n' in e or '\r' in e or '=' not in e for e in values):
            raise Blocked('CONTAINER_ENV_UNEXPECTED')
        env_file.write_text('\n'.join(values) + '\n')
        create = ['docker', 'create', '--name', candidate, '--network', 'ouf-backend',
                  '--restart', 'no', '--user', config['User'], '--env-file', str(env_file),
                  '--mount', 'type=bind,source=' + mounts[0]['Source'] +
                  ',target=' + mounts[0]['Destination'] + ',readonly']
        if config.get('WorkingDir'):
            create += ['--workdir', config['WorkingDir']]
        for alias in old['NetworkSettings']['Networks']['ouf-backend'].get('Aliases') or []:
            if alias == LIVE:
                create += ['--network-alias', LIVE]
        create.append(tag)
        try:
            command(create, capture=False)
            new = inspect(candidate)
            if (new['Image'] != image['Id'] or new['State']['Running']
                    or new['Config']['User'] != config['User']
                    or new['HostConfig']['NetworkMode'] != 'ouf-backend'
                    or set(new['Config'].get('Env') or []) != set(values)
                    or len(new.get('Mounts') or []) != 1
                    or new['Mounts'][0]['Source'] != mounts[0]['Source']
                    or new['Mounts'][0]['RW']):
                raise Blocked('CANDIDATE_CONFIG_MISMATCH')
            command(['docker', 'cp', candidate + ':/app/application.jar', str(work / 'new.jar')], capture=False)
            if migrations(work / 'old.jar') != migrations(work / 'new.jar'):
                raise Blocked('FLYWAY_MIGRATION_CHANGED')
            state_path = ROOT / ('r4a-semantic-review-' + args.revision[:7] + '.json')
            if state_path.exists():
                raise Blocked('ROLLOUT_STATE_ALREADY_EXISTS')
            state = {'revision': args.revision, 'oldId': old['Id'], 'newId': new['Id'],
                     'backup': backup, 'oldInspect': old}
            state_path.write_text(json.dumps(state))
            print('MODE=apply FLYWAY_MIGRATIONS_IDENTICAL=true ORIGINAL_RUNNING=true', flush=True)
            try:
                command(['docker', 'update', '--restart', 'no', LIVE], capture=False)
                command(['docker', 'stop', LIVE], capture=False)
                command(['docker', 'rename', LIVE, backup], capture=False)
                command(['docker', 'rename', candidate, LIVE], capture=False)
                command(['docker', 'start', LIVE], capture=False)
                readiness()
                command(['docker', 'update', '--restart', 'unless-stopped', LIVE], capture=False)
            except BaseException:
                rollback(old['Id'], new['Id'], backup, candidate)
                print('SEMANTIC_ROLLOUT_AUTO_ROLLBACK=PASS', file=sys.stderr)
                raise
            print('SEMANTIC_REVIEW_CARD_ROLLOUT=PASS')
            print('IMAGE_ID=' + image['Id'])
            print('BACKUP_CONTAINER=' + backup)
            print('ROLLBACK_STATE=' + str(state_path))
            print('SECRET_VALUES_NOT_PRINTED=true')
        finally:
            if exists(candidate) and not inspect(candidate)['State']['Running']:
                command(['docker', 'rm', candidate], capture=False)


if __name__ == '__main__':
    try:
        main()
    except (Blocked, OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        code = str(exc) if isinstance(exc, Blocked) else type(exc).__name__
        print('SEMANTIC_REVIEW_CARD_BLOCKED=' + code, file=sys.stderr)
        raise SystemExit(1)
