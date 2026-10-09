"""Assemble the unreleased pinned upstream snapshot for CI, with locked inputs."""
import hashlib
import json
import os
import subprocess
from pathlib import Path


def prepare(work, source):
    upstream = work / 'upstream-openresty'
    subprocess.run(['git', 'init', str(upstream)], check=True)
    subprocess.run(['git', '-C', str(upstream), 'fetch', '--depth=1',
        'https://github.com/' + source['repository'] + '.git', source['commit']], check=True, timeout=180)
    subprocess.run(['git', '-C', str(upstream), 'checkout', '--detach', 'FETCH_HEAD'], check=True)
    assert subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', 'HEAD'], text=True).strip() == source['commit']
    subprocess.run(['git', '-C', str(upstream), 'fsck', '--full'], check=True)
    mirror = upstream / 'util/mirror-tarballs'
    assert subprocess.check_output(['git', '-C', str(upstream), 'hash-object', str(mirror)], text=True).strip() == source['mirrorScriptGitBlob']
    # All compilation sources and upstream patches precede documentation generation.
    original = mirror.read_text()
    marker = 'perl bundle/$resty_cli/bin/md2pod.pl'
    assert original.count(marker) == 1
    mirror.write_text(original.split(marker)[0] + '''cp "$root/doc/README-windows.md" README-windows.txt || exit 1
cd "$root" || exit 1
tar --sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner -cf "$name.tar" "$name" || exit 1
gzip -n -9 -f "$name.tar" || exit 1
''')
    lockfile = upstream / 'ouf-download-lock.json'
    lockfile.write_text(json.dumps(source['archives']))
    downloader = upstream / 'util/get-tarball'
    downloader.write_text('''#!/usr/bin/env python3
import hashlib,json,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[1]
url=sys.argv[1];target=pathlib.Path(sys.argv[3])
if url.startswith('http://'):url='https://'+url[7:]
rows=[r for r in json.loads((root/'ouf-download-lock.json').read_text()) if r['file']==target.name]
assert len(rows)==1 and rows[0]['url']==url
r=rows[0]
subprocess.run(['curl','--fail','--silent','--show-error','--location','--proto','=https','--tlsv1.2','--max-time','120','--max-filesize','33554432',url,'--output',str(target)],check=True)
data=target.read_bytes()
assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256']
with (root/'ouf-downloads-verified.jsonl').open('a') as out:out.write(json.dumps(r)+'\\n')
''')
    downloader.chmod(0o755)
    env = dict(os.environ, TAR_OPTIONS='--no-same-owner', MIRROR_JOBS='2')
    subprocess.run(['bash', 'util/mirror-tarballs'], cwd=upstream, env=env, check=True, timeout=1800)
    seen = [json.loads(x) for x in (upstream / 'ouf-downloads-verified.jsonl').read_text().splitlines()]
    assert sorted(seen, key=lambda x: x['file']) == source['archives']
    archive = upstream / ('openresty-' + source['version'] + '.tar.gz')
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == source['sha256']
    subprocess.run(['tar', 'xzf', str(archive), '-C', str(work)], check=True)
    return archive
