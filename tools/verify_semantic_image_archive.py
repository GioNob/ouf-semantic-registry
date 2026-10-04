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
    before = command_snapshot(docker); child = None
    # Empty CLI config directory prevents reading host registry credentials.
    with tempfile.TemporaryDirectory(prefix='ouf-image-read-') as config:
        try:
            child = subprocess.Popen([str(docker),'--config',config,'--host',host,'image','save','--platform','/'.join(platform),image],
                stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                env={'PATH':'/usr/bin:/bin','LC_ALL':'C'},start_new_session=True)
            result = archive_verify(PipeReader(child.stdout,budget),image,budget,payload,metadata,platform)
            require(child.wait(timeout=max(0,budget.deadline-time.monotonic())) == 0)
            require(command_snapshot(docker) == before); result['dockerBinarySha256'] = before
            return result
        finally:
            if child is not None:
                if child.poll() is None:
                    import signal
                    try: os.killpg(child.pid,signal.SIGKILL)
                    except ProcessLookupError: pass
                    child.wait(timeout=2)
                child.stdout.close()


def main():
    try:
        parser = argparse.ArgumentParser(description=__doc__)
        for name in ('docker-path','docker-host','platform','adapter-image','southbound-image','payload-hashes','source-commit','payload-hash','runtime-user'):
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
        for image, hashes, meta in ((a.adapter_image,payload,metadata),(a.southbound_image,None,None)):
            rows.append(docker_verify(Path(a.docker_path),a.docker_host,image,
                Budget(a.seconds,a.max_bytes,a.max_entries),hashes,meta,platform))
        print('SEMANTIC_IMAGE_BYTES='+json.dumps({'schema':'ouf.semantic-image-bytes-readback.v1','images':rows,
            'containerOperations':0,'providerCalls':0,'signaturesIssued':0,'targetFilesWritten':0,
            'acceptanceGranted':False,'startAuthorized':False},sort_keys=True))
        print('SEMANTIC_IMAGE_BYTES=PASS ACCEPTANCE_GRANTED=false START_AUTHORIZED=false')
        return 0
    except Exception:
        print('SEMANTIC_IMAGE_BYTES=BLOCKED REASON=IMAGE_ARCHIVE_UNPROVEN NO_SECRETS_PRINTED=true')
        return 1


if __name__=='__main__': raise SystemExit(main())
