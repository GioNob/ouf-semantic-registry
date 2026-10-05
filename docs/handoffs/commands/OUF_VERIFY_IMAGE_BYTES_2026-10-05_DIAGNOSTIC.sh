#!/usr/bin/env bash
# §42 diagnostic follow-up; SAME private scope authorized 2026-10-05.
# Fixed stage/class/line/counters only; no exception messages or Docker stderr.
# Original immutable wrapper returned BLOCKED; this wrapper is not yet executed.
# Docker save of TWO pinned images only, config + rootfs bytes streamed privately.
# No container create/start/build/pull; no registry credentials or target mount/Env reads.
# No archive extraction/spool; an empty temporary Docker CLI config directory is removed.
# 180 seconds / 8 GiB cumulative parser work / 100000 entries PER IMAGE.
# Publisher provenance, SBOM, mount view and release acceptance remain unproven.
set -euo pipefail
exec sudo /usr/bin/python3 -I -B - --docker-path /usr/bin/docker --docker-host unix:///var/run/docker.sock --platform linux/amd64 --adapter-image sha256:a697bf75bf7d51afadadfaccd3d80537e9a5fb2a08f0d194c6dfd9462e812468 --southbound-image sha256:84e6b5e787e9f889ebff88161cb9a16599bafcffa236c6b54c7f779a0655940d --adapter-rootfs-descriptors-hash e6b2f3bd33516825e3bee4a0af52090d917545bd644c294dfe0843b736b088d1 --southbound-rootfs-descriptors-hash ea6aeeef286a7c893cd0bd8eb7452196d87c8681f72a10a3001af288133528ed --payload-hashes '{"app/tools/semantic_provider_adapter.py":"718f031cd4116d233c3075ee74da2f28170b5ed4efcac1a77deef154f7fd320c","app/tools/semantic_provider_admission.py":"dca670d1f0ced678db6af9810199da07419901a21523385e0ebea623b608bbfc","app/tools/semantic_provider_boundary.py":"cae2b1d5970349ce1ebc95fb44ca4dd1bd67d93e43900ad4cbeabb3d5fbd6e69","app/tools/semantic_provider_relay.py":"04b33da9b3d599872c19ea20d3775141ef99c5989c7fb7175be6926b74cc7f6f","app/tools/southbound_security.py":"5953e6143fb7141b62a2d5cc26d8cf85ee74147d9eefaa923460f8e1706eb0ec"}' --source-commit 52c0dcf11654a4d3d0f17a6902ed095975466fb9 --payload-hash 379bad5a3083048ff012c5143ace15509321fa860cdaefd238b1218f6541afe7 --runtime-user 10006:10006 --seconds 180 --max-bytes 8589934592 --max-entries 100000 <<'OUF_PYTHON'
"""Bounded Docker save archive verification; never extracts or runs image files."""
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import selectors
import stat
import subprocess
import sys
import tempfile
import time


# Diagnostic fields contain only fixed vocabulary and numeric counters. Never
# serialize exception messages, archive names/config, Docker stderr or paths.
DIAGNOSTIC = {'imageRole': 'NOT_SELECTED', 'stage': 'ARGUMENT_VALIDATION'}


def blocked_diagnostic(error):
    allowed = {'Blocked', 'KeyError', 'TypeError', 'ValueError', 'OSError',
               'FileNotFoundError', 'PermissionError', 'ReadError', 'EOFError',
               'JSONDecodeError', 'BadGzipFile', 'TimeoutExpired'}
    kind = type(error).__name__
    line = 0
    frame = error.__traceback__
    while frame is not None:
        if (frame.tb_frame.f_code.co_filename == blocked_diagnostic.__code__.co_filename
                and frame.tb_frame.f_code.co_name != 'require'):
            line = frame.tb_lineno
        frame = frame.tb_next
    return {**DIAGNOSTIC, 'errorClass': kind if kind in allowed else 'OTHER',
            'verifierLine': line}


class Blocked(ValueError): pass
def require(ok):
    if not ok: raise Blocked('IMAGE_ARCHIVE_UNPROVEN')
def digest(raw): return hashlib.sha256(raw).hexdigest()
def json_bytes(raw):
    require(0 < len(raw) <= 131072)
    def unique(items):
        value = {}
        for key, item in items:
            require(key not in value); value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(Blocked()))
def path_name(value):
    require(type(value) is str and len(value) <= 4096 and '\x00' not in value)
    p = PurePosixPath(value)
    require(not p.is_absolute() and '..' not in p.parts)
    return str(p)


class Budget:
    def __init__(self, seconds=180, max_bytes=8589934592, max_entries=100000):
        require(type(seconds) is int and 1 <= seconds <= 180
                and type(max_bytes) is int and 1 <= max_bytes <= 8589934592
                and type(max_entries) is int and 1 <= max_entries <= 100000)
        self.deadline = time.monotonic() + seconds
        self.max_bytes, self.max_entries = max_bytes, max_entries
        self.bytes = self.entries = 0
    def check(self): require(time.monotonic() < self.deadline)
    def entry(self):
        self.check(); self.entries += 1; require(self.entries <= self.max_entries)
    def consume(self, amount):
        self.check(); self.bytes += amount; require(self.bytes <= self.max_bytes)


class HashReader:
    def __init__(self, stream, budget):
        self.stream, self.budget = stream, budget
        self.hash = hashlib.sha256(); self.size = 0
    def read(self, size=-1):
        require(type(size) is int and 0 <= size <= 131072)
        self.budget.check(); raw = self.stream.read(size)
        require(type(raw) is bytes and len(raw) <= size)
        self.budget.consume(len(raw)); self.size += len(raw); self.hash.update(raw)
        return raw
    def drain(self):
        while self.read(65536): pass


class PrefixReader:
    def __init__(self, prefix, stream): self.prefix, self.stream = prefix, stream
    def read(self, size=-1):
        require(type(size) is int and 0 <= size <= 131072)
        take, self.prefix = self.prefix[:size], self.prefix[size:]
        return take + self.stream.read(size-len(take))


def read_small(stream):
    raw = bytearray()
    while True:
        part = stream.read(min(65536, 131073-len(raw)))
        if not part: break
        raw.extend(part); require(len(raw) <= 131072)
    return bytes(raw)


def layer_summary(stream, prefix, budget):
    import tarfile
    source = PrefixReader(prefix, stream)
    if prefix[:2] == b'\x1f\x8b': source = gzip.GzipFile(fileobj=source, mode='rb')
    # Both compressed input and uncompressed layer bytes consume the same
    # budget; decompression cannot bypass byte/time ceilings.
    plain = HashReader(source, budget); seen = set(); app = {}; whiteouts = []
    with tarfile.open(fileobj=plain, mode='r|') as archive:
        for entry in archive:
            budget.entry(); name = path_name(entry.name)
            require(name not in seen and entry.size >= 0); seen.add(name)
            base = PurePosixPath(name).name; parent = str(PurePosixPath(name).parent)
            if base.startswith('.wh.'):
                require(entry.isfile() and entry.size == 0)
                target = parent if base == '.wh..wh..opq' else str(PurePosixPath(parent)/base[4:])
                whiteouts.append((path_name(target), base == '.wh..wh..opq'))
            if name == 'app' or name.startswith('app/'):
                if base.startswith('.wh.'): continue
                require(len(app) <= 128)
                row = {'mode': entry.mode, 'uid': entry.uid, 'gid': entry.gid}
                if entry.isdir(): row['kind'] = 'directory'
                elif entry.isfile():
                    row.update(kind='file', size=entry.size)
                    require(0 <= entry.size <= 131072)
                    row['sha256'] = digest(read_small(archive.extractfile(entry)))
                else: row['kind'] = 'unsupported'
                app[name] = row
            archive.members.clear()
    plain.drain()
    return {'diffId': 'sha256:'+plain.hash.hexdigest(), 'bytes': plain.size,
            'app': app, 'whiteouts': whiteouts}


def archive_verify(stream, image_id, budget, payload=None, adapter_metadata=None, platform=('linux','amd64')):
    import tarfile
    require(re.fullmatch('sha256:[0-9a-f]{64}', image_id))
    outer = HashReader(stream, budget); blobs = {}; manifest = None; names = set()
    with tarfile.open(fileobj=outer, mode='r|') as archive:
        for entry in archive:
            budget.entry(); name = path_name(entry.name)
            require(name not in names); names.add(name)
            if entry.isdir(): continue
            require(entry.isfile() and 0 <= entry.size <= budget.max_bytes and len(blobs) < 512)
            member = HashReader(archive.extractfile(entry), budget); prefix = member.read(min(entry.size,512))
            if name == 'manifest.json':
                raw = prefix + read_small(member); manifest = json_bytes(raw)
                row = {'json': manifest}
            elif name.endswith('/VERSION'):
                require(prefix + read_small(member) == b'1.0'); row = {'formatMetadata':True}
            elif prefix.lstrip().startswith((b'{',b'[')):
                raw = prefix + read_small(member); row = {'json':json_bytes(raw)}
            else:
                row = layer_summary(member, prefix, budget)
            member.drain(); require(member.size == entry.size)
            row['sha256'] = member.hash.hexdigest(); blobs[name] = row
            if name.startswith('blobs/sha256/'):
                require(name == 'blobs/sha256/'+row['sha256'])
            archive.members.clear()
    outer.drain()
    require(type(manifest) is list and len(manifest) == 1)
    item = manifest[0]; require(type(item) is dict)
    config = blobs[path_name(item['Config'])]
    require('sha256:'+config['sha256'] == image_id and type(config['json']) is dict)
    doc = config['json']; rootfs = doc['rootfs']
    require(rootfs['type'] == 'layers' and type(rootfs['diff_ids']) is list
            and 1 <= len(rootfs['diff_ids']) <= 256)
    paths = item['Layers']; require(type(paths) is list and len(paths) == len(rootfs['diff_ids'])
            and len(set(paths)) == len(paths))
    final = {}; layer_hashes = []
    for name, expected in zip(paths, rootfs['diff_ids']):
        row = blobs[path_name(name)]
        require(re.fullmatch('sha256:[0-9a-f]{64}', expected) and row['diffId'] == expected)
        layer_hashes.append(row['sha256'])
        for target, opaque in row['whiteouts']:
            prefix = '' if target == '.' else target+'/'
            for old in list(final):
                if (old == target and not opaque) or old.startswith(prefix): final.pop(old)
        final.update(row['app'])
    if payload is not None:
        require(type(payload) is dict and len(payload) == 5 and all(re.fullmatch('[0-9a-f]{64}', h) for h in payload.values()))
        require(set(final) == {'app','app/tools'} | set(payload))
        for name in ('app','app/tools'):
            require(final[name] == {'mode':0o555,'uid':0,'gid':0,'kind':'directory'})
        for name, expected in payload.items():
            row = final[name]
            require(row['kind'] == 'file' and row['sha256'] == expected and row['mode'] == 0o444
                    and row['uid'] == row['gid'] == 0)
        cfg = doc['config']; require(type(adapter_metadata) is dict)
        require(cfg['User'] == adapter_metadata['user'] and cfg['WorkingDir'] == '/app'
                and cfg['Entrypoint'] == ['python3','-B','-m','tools.semantic_provider_adapter']
                and not cfg.get('Cmd') and not cfg.get('Volumes') and not cfg.get('Healthcheck'))
        labels = cfg['Labels']
        require(labels['org.opencontainers.image.revision'] == adapter_metadata['sourceCommit']
                and labels['ouf.component'] == 'semantic-provider-transport'
                and labels['ouf.payload.sha256'] == adapter_metadata['payloadHash'])
    require(type(platform) is tuple and len(platform) == 2
            and (doc['os'],doc['architecture']) == platform)
    return {'schema':'ouf.semantic-exported-image-byte-verification.v1', 'imageId':image_id,
            'archiveSha256':outer.hash.hexdigest(), 'archiveBytes':outer.size,
            'verifiedLayerCount':len(paths), 'layerByteHashes':layer_hashes,
            'rootfsDescriptorsHash':digest(json.dumps({'Type':rootfs['type'],'Layers':rootfs['diff_ids']},
                sort_keys=True,separators=(',',':')).encode()),
            'layerDiffIdsMatchConfig':True, 'configBytesMatchImageId':True,
            'adapterPayloadVerified':payload is not None, 'archiveFilesExtracted':0,
            'imagePublisherProvenanceVerified':False, 'dependencySbomVerified':False,
            'currentRootfsInspected':False, 'generationObserved':False,
            'atomicSnapshotProven':False, 'acceptanceGranted':False, 'startAuthorized':False}


class PipeReader:
    def __init__(self, pipe, budget): self.pipe,self.budget = pipe,budget
    def read(self,size):
        require(0 <= size <= 131072)
        if size == 0: return b''
        self.budget.check()
        with selectors.DefaultSelector() as ready:
            ready.register(self.pipe,selectors.EVENT_READ)
            require(ready.select(max(0,self.budget.deadline-time.monotonic())))
        return os.read(self.pipe.fileno(),size)


def command_snapshot(path):
    require(path.is_absolute() and '..' not in path.parts)
    for parent in path.parents:
        info = parent.lstat(); require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022)
    fd = os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and info.st_mode & 0o111
                and not info.st_mode & 0o022 and info.st_size <= 64000000)
        raw = bytearray()
        while True:
            data = os.read(fd,65536)
            if not data: break
            raw.extend(data); require(len(raw) <= 64000000)
        return digest(raw)
    finally: os.close(fd)


def docker_verify(docker, host, image, budget, payload=None, metadata=None, platform=('linux','amd64')):
    require(re.fullmatch('sha256:[0-9a-f]{64}',image))
    DIAGNOSTIC['stage'] = 'DOCKER_BINARY_CHECK'
    before = command_snapshot(docker); child = None
    # Empty CLI config directory prevents reading host registry credentials.
    with tempfile.TemporaryDirectory(prefix='ouf-image-read-') as config:
        try:
            DIAGNOSTIC['stage'] = 'DOCKER_EXPORT_OPEN'
            child = subprocess.Popen([str(docker),'--config',config,'--host',host,'image','save','--platform','/'.join(platform),image],
                stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                env={'PATH':'/usr/bin:/bin','LC_ALL':'C'},start_new_session=True)
            DIAGNOSTIC['stage'] = 'ARCHIVE_VERIFICATION'
            result = archive_verify(PipeReader(child.stdout,budget),image,budget,payload,metadata,platform)
            DIAGNOSTIC['stage'] = 'DOCKER_EXPORT_EXIT'
            require(child.wait(timeout=max(0,budget.deadline-time.monotonic())) == 0)
            DIAGNOSTIC['stage'] = 'DOCKER_BINARY_RECHECK'
            require(command_snapshot(docker) == before); result['dockerBinarySha256'] = before
            return result
        except Exception:
            DIAGNOSTIC['dockerExitCode'] = child.poll() if child is not None else None
            DIAGNOSTIC['parserBytes'] = budget.bytes
            DIAGNOSTIC['parserEntries'] = budget.entries
            raise
        finally:
            if child is not None:
                if child.poll() is None:
                    import signal
                    try: os.killpg(child.pid,signal.SIGKILL)
                    except ProcessLookupError: pass
                    child.wait(timeout=2)
                child.stdout.close()


def main():
    DIAGNOSTIC.clear()
    DIAGNOSTIC.update(imageRole='NOT_SELECTED', stage='ARGUMENT_VALIDATION')
    try:
        parser = argparse.ArgumentParser(description=__doc__)
        for name in ('docker-path','docker-host','platform','adapter-image','southbound-image','adapter-rootfs-descriptors-hash',
                     'southbound-rootfs-descriptors-hash','payload-hashes','source-commit','payload-hash','runtime-user'):
            parser.add_argument('--'+name,required=True)
        parser.add_argument('--seconds',type=int,required=True)
        parser.add_argument('--max-bytes',type=int,required=True)
        parser.add_argument('--max-entries',type=int,required=True)
        a = parser.parse_args(); require(os.geteuid()==0 and sys.flags.isolated and sys.dont_write_bytecode)
        require(a.docker_host.startswith('unix:///') and '..' not in Path(a.docker_host[7:]).parts)
        payload = json_bytes(a.payload_hashes.encode())
        platform = tuple(a.platform.split('/')); require(len(platform) == 2 and all(re.fullmatch('[a-z0-9_]+',x) for x in platform))
        metadata = dict(user=a.runtime_user,sourceCommit=a.source_commit,payloadHash=a.payload_hash)
        rows = []
        for image, hashes, meta, descriptors in ((a.adapter_image,payload,metadata,a.adapter_rootfs_descriptors_hash),
                                               (a.southbound_image,None,None,a.southbound_rootfs_descriptors_hash)):
            DIAGNOSTIC['imageRole'] = 'ADAPTER' if hashes is not None else 'SOUTHBOUND'
            for key in ('dockerExitCode', 'parserBytes', 'parserEntries'):
                DIAGNOSTIC.pop(key, None)
            require(re.fullmatch('[0-9a-f]{64}',descriptors))
            row=docker_verify(Path(a.docker_path),a.docker_host,image,
                Budget(a.seconds,a.max_bytes,a.max_entries),hashes,meta,platform)
            DIAGNOSTIC['stage'] = 'ROOTFS_DESCRIPTOR_COMPARISON'
            require(row['rootfsDescriptorsHash']==descriptors);rows.append(row)
        print('SEMANTIC_IMAGE_BYTES='+json.dumps({'schema':'ouf.semantic-image-bytes-readback.v1','images':rows,
            'containerOperations':0,'providerCalls':0,'signaturesIssued':0,'targetFilesWritten':0,
            'acceptanceGranted':False,'startAuthorized':False},sort_keys=True))
        print('SEMANTIC_IMAGE_BYTES=PASS ACCEPTANCE_GRANTED=false START_AUTHORIZED=false')
        return 0
    except Exception as error:
        print('SEMANTIC_IMAGE_BYTES_DIAGNOSTIC='+json.dumps(blocked_diagnostic(error),sort_keys=True))
        print('SEMANTIC_IMAGE_BYTES=BLOCKED REASON=IMAGE_ARCHIVE_UNPROVEN NO_SECRETS_PRINTED=true')
        return 1


if __name__=='__main__': raise SystemExit(main())
OUF_PYTHON
