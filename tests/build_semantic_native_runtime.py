"""CI container build only: pinned OpenResty/APISIX modules, no WASM VM.

The native source manifest describes the deliberate optional-feature change.
It does not grant production acceptance or vendor publisher trust.
"""
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path


def run(*args, cwd=None):
    subprocess.run(args, cwd=cwd, check=True, timeout=900)


def main():
    assert os.geteuid() == 0
    lock = json.loads(Path('/tmp/native-sources.json').read_text())
    work = Path('/native-source')
    work.mkdir()
    source = lock['openresty']
    from prepare_semantic_openresty_source import prepare
    archive = prepare(work, source)
    source_files = {'openrestyArchiveSha256': source['sha256'], 'modules': []}
    for module in lock['modules']:
        target = work / module['directory']
        run('git', 'init', str(target))
        run('git', '-C', str(target), 'fetch', '--depth=1',
            'https://github.com/' + module['repository'] + '.git', module['commit'])
        run('git', '-C', str(target), 'checkout', '--detach', 'FETCH_HEAD')
        actual = subprocess.check_output(['git', '-C', str(target), 'rev-parse', 'HEAD'], text=True).strip()
        assert actual == module['commit']
        run('git', '-C', str(target), 'fsck', '--full')
        shutil.rmtree(target / '.git')
        if module['repository'] == 'api7/apisix-nginx-module':
            guard = Path('/tmp/native-shdict.patch')
            assert hashlib.sha256(guard.read_bytes()).hexdigest() == lock['api7SharedDictPatch']['sha256']
            run('patch', '--batch', '--fuzz=0', '-p1', '-i', str(guard), cwd=target)
        files = {str(p.relative_to(target)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(target.rglob('*')) if p.is_file()}
        source_files['modules'].append(dict(module, files=files))
    resty = work / ('openresty-' + source['version'])
    patch = Path('/tmp/native-api7.patch')
    assert hashlib.sha256(patch.read_bytes()).hexdigest() == source['vendorPatchSha256']
    run('patch', '--batch', '--fuzz=0', '-p1', '-i', str(patch), cwd=resty)
    limit = resty / 'bundle/lua-resty-limit-traffic-0.09'
    assert limit.is_dir()
    shutil.rmtree(limit)
    shutil.copytree(work / 'lua-resty-limit-traffic-1.2.0', limit)
    source_files['compiledSourceFiles'] = {str(p.relative_to(resty)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(resty.rglob('*')) if p.is_file() and not p.is_symlink()}
    lua_bundle = list((resty / 'bundle').glob('ngx_lua-*'))
    assert len(lua_bundle) == 1
    os.environ['NGX_HTTP_LUA_MODULE_DIR'] = str(lua_bundle[0])
    prefix = Path('/usr/local/openresty')
    # Replace the entire compiled OpenResty payload; no inherited native leftovers.
    for name in ('luajit', 'nginx', 'lualib', 'bin', 'site', 'wasmtime-c-api'):
        path = prefix / name
        if path.exists():
            shutil.rmtree(path)
    options = ['--prefix=' + str(prefix),
        '--with-cc-opt=-DAPISIX_RUNTIME_VER=1.3.16 -DNGX_LUA_ABORT_AT_PANIC '
        '-I/usr/local/openresty/zlib/include -I/usr/local/openresty/pcre/include '
        '-I/usr/local/openresty/openssl3/include',
        '--with-ld-opt=-L/usr/local/openresty/zlib/lib -L/usr/local/openresty/pcre/lib '
        '-L/usr/local/openresty/openssl3/lib -Wl,-rpath,/usr/local/openresty/zlib/lib:'
        '/usr/local/openresty/pcre/lib:/usr/local/openresty/openssl3/lib']
    for module in ('mod_dubbo-1.0.2', 'ngx_multi_upstream_module-1.3.3',
                   'apisix-nginx-module-1.19.9', 'apisix-nginx-module-1.19.9/src/stream',
                   'apisix-nginx-module-1.19.9/src/meta', 'lua-var-nginx-module-v0.5.3',
                   'lua-resty-events-0.2.0', 'ngx_http_ffi_client-v0.1.3'):
        options.append('--add-module=' + str(work / module))
    options += ['--with-poll_module', '--with-pcre-jit', '--without-http_rds_json_module',
        '--without-http_rds_csv_module', '--without-lua_rds_parser', '--with-stream',
        '--with-stream_ssl_module', '--with-stream_ssl_preread_module', '--with-stream_realip_module',
        '--with-http_v2_module', '--with-http_v3_module', '--without-mail_pop3_module',
        '--without-mail_imap_module', '--without-mail_smtp_module', '--with-http_stub_status_module',
        '--with-http_realip_module', '--with-http_addition_module', '--with-http_auth_request_module',
        '--with-http_secure_link_module', '--with-http_random_index_module', '--with-http_gzip_static_module',
        '--with-http_sub_module', '--with-http_dav_module', '--with-http_flv_module', '--with-http_mp4_module',
        '--with-http_gunzip_module', '--with-threads', '--with-compat',
        '--with-luajit-xcflags=-DLUAJIT_NUMMODE=2 -DLUAJIT_ENABLE_LUA52COMPAT', '-j2']
    run('./configure', *options, cwd=resty)
    run('make', '-j2', cwd=resty)
    run('make', 'install', cwd=resty)
    events = work / 'lua-resty-events-0.2.0/lualib/resty/events'
    shutil.copytree(events, prefix / 'lualib/resty/events', dirs_exist_ok=True)
    shutil.copy2(work / 'ngx_http_ffi_client-v0.1.3/lib/resty/ngx_http_ffi_client.lua', prefix / 'lualib/resty')
    os.environ['OPENRESTY_PREFIX'] = str(prefix)
    run('make', 'install', cwd=work / 'apisix-nginx-module-1.19.9')
    assert not (prefix / 'wasmtime-c-api').exists()
    manifest = dict(lock, sourceFiles=source_files,
        embeddedSourceDirectories=sorted(p.name for p in (resty / 'bundle').iterdir() if p.is_dir()),
        dependencyCoverageAccepted=False, acceptanceGranted=False, startAuthorized=False)
    dest = Path('/usr/local/share/ouf')
    dest.mkdir(parents=True, exist_ok=True)
    (dest / 'native-runtime-sources.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    binaries = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(prefix.rglob('*'))
                if p.is_file() and not p.is_symlink() and p.open('rb').read(4) == b'\x7fELF'}
    (dest / 'native-runtime-binaries.json').write_text(json.dumps(binaries, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
