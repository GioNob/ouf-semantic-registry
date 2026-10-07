"""Check/repair only an omitted OWNER_KEY_ENV declaration in the live search route.

Uses the existing private Admin key for the exact route GET/PUT, never prints it.
Preserves a private route snapshot and restores on failed write/readback.
"""
import argparse
import copy
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import tempfile

ROUTE = 'execute-urban-object-search'
URI = '/internal/capabilities/v1/execute/urban.object.search'
MARKER = 'local OWNER_KEY_ENV = "OUF_UDP_SEARCH_OWNER_KEY"\n'


def env_directive_present(generated, name):
    for line in generated.splitlines():
        if not re.match(r'^\s*env\s+', line):
            continue
        try:
            tokens = shlex.split(line, comments=True)
        except ValueError:
            continue
        if len(tokens) == 2 and tokens[0] == 'env' and tokens[1].endswith(';'):
            if tokens[1][:-1].split('=', 1)[0] == name:
                return True
    return False


def diagnose_bindings(route, env, generated):
    if route.get('id') != ROUTE or route.get('uri') != URI or route.get('methods') != ['POST']:
        raise ValueError('SEARCH_ROUTE_IDENTITY_MISMATCH')
    functions = route.get('plugins', {}).get('serverless-post-function', {}).get('functions')
    if not isinstance(functions, list) or len(functions) != 1 or not isinstance(functions[0], str):
        raise ValueError('ONE_SEARCH_FUNCTION_REQUIRED')
    bindings = {}
    for role in ('DELEGATION_KEY_ENV', 'OWNER_KEY_ENV'):
        names = re.findall(r'^local ' + role + r' = "([A-Z][A-Z0-9_]*)"$', functions[0], re.M)
        if len(names) != 1:
            raise ValueError('EXACT_KEY_DECLARATION_REQUIRED')
        name = names[0]
        value = env.get(name, '')
        bindings[role] = {'environmentName': name, 'containerValuePresent': bool(value),
                          'containerValueHex64': bool(re.fullmatch(r'[a-fA-F0-9]{64}', value)),
                          'generatedEnvDirectivePresent': env_directive_present(generated, name)}
    return {'status': 'READ_ONLY_BINDING_DIAGNOSIS', 'bindings': bindings, 'routeChanged': False,
            'positiveSearchProven': False}


UNSIGNED_PROBE = r'''
import json,sys,urllib.request,urllib.error
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None
try:
    address=json.load(sys.stdin)['address']
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    req=urllib.request.Request('http://'+address+':8080/api/udp/v1/objects/search',data=b'{"type":"https://api.ouf-lab.it/semantic/cinema","pageSize":1}',headers={'Content-Type':'application/json'},method='POST')
    try:
        with opener.open(req,timeout=4) as response: status=response.status
    except urllib.error.HTTPError as error:
        status=error.code;error.close()
    print(json.dumps({'httpStatus':status,'responseBodyRead':False,'receiptSent':False}))
except Exception:
    print(json.dumps({'result':'CONNECTION_FAILED','responseBodyRead':False,'receiptSent':False}))
'''


def upstream_summary(route, gateway, udp):
    networks = gateway['NetworkSettings']['Networks']
    unets = udp['NetworkSettings']['Networks']
    shared = set(networks).intersection(unets)
    addresses = {unets[n].get('IPAddress') for n in shared} - {None, ''}
    aliases = {udp.get('Name', '').lstrip('/')}
    for n in shared:
        aliases.update(unets[n].get('Aliases') or [])
    up = route.get('upstream') or {}
    nodes = up.get('nodes')
    report = {'status':'READ_ONLY_UPSTREAM_DIAGNOSIS','sharedNetworkCount':len(shared),
              'udpRunning':udp.get('State',{}).get('Running') is True,
              'routeChanged':False,'positiveSearchProven':False}
    if not isinstance(nodes,dict) or len(nodes)!=1 or up.get('scheme','http')!='http':
        report['result']='INLINE_SINGLE_HTTP_UPSTREAM_REQUIRED';return report,None,addresses
    node = next(iter(nodes))
    if not isinstance(node,str) or not re.fullmatch(r'[A-Za-z0-9_.-]+:8080',node):
        report['result']='EXPECTED_INTERNAL_PORT_REQUIRED';return report,None,addresses
    host=node.rsplit(':',1)[0]
    report['upstreamMatchesUdpAliasOrAddress']=host in aliases or host in addresses
    if host not in aliases | addresses | {'ouf-udp-object-resolution','ouf-udp'}:
        report['result']='UPSTREAM_OUTSIDE_EXPECTED_UDP_NAMES';return report,None,addresses
    report['upstreamHost']=host
    return report,host,addresses


def diagnose_upstream(route, gateway, admin, args):
    doc=subprocess.run([args.docker,'inspect','--type','container',args.udp],capture_output=True,check=True,timeout=10)
    udp=json.loads(doc.stdout)[0]
    report,host,expected=upstream_summary(route,gateway,udp)
    if host is None: return report
    dns=subprocess.run([args.docker,'exec',args.gateway,'getent','ahostsv4',host],capture_output=True,text=True,timeout=10)
    if dns.returncode:
        report['result']='NAME_NOT_RESOLVED' if dns.returncode==2 else 'RESOLVER_COMMAND_UNAVAILABLE_OR_FAILED'
        return report
    resolved={line.split()[0] for line in dns.stdout.splitlines() if line.split()}
    report['resolvedAddressCount']=len(resolved)
    report['resolvedAddressesMatchUdp']=bool(resolved) and resolved.issubset(expected)
    if not report['resolvedAddressesMatchUdp']:
        report['result']='RESOLVED_ADDRESS_NOT_CURRENT_UDP';return report
    address=sorted(resolved)[0]
    ip=ipaddress.ip_address(address)
    if ip.version!=4 or not ip.is_private or ip.is_loopback or ip.is_unspecified:
        raise ValueError('PRIVATE_CURRENT_UDP_IPV4_REQUIRED')
    probe=subprocess.run([args.nsenter,'--net=/proc/self/fd/'+str(admin.namespace_fd),'/usr/bin/python3','-I','-B','-c',UNSIGNED_PROBE],input=json.dumps({'address':address}),capture_output=True,text=True,timeout=8,pass_fds=(admin.namespace_fd,))
    if probe.returncode: raise ValueError('UNSIGNED_NAMESPACE_PROBE_FAILED')
    result=json.loads(probe.stdout)
    report['unsignedOwnerProbe']={k:result[k] for k in ('httpStatus','result','responseBodyRead','receiptSent') if k in result}
    return report


def canonical(route):
    return {k: v for k, v in route.items() if k not in ('create_time', 'update_time')}


def proposed(route):
    if route.get('id') != ROUTE or route.get('uri') != URI or route.get('methods') != ['POST']:
        raise ValueError('SEARCH_ROUTE_IDENTITY_MISMATCH')
    functions = route.get('plugins', {}).get('serverless-post-function', {}).get('functions')
    if not isinstance(functions, list) or len(functions) != 1 or not isinstance(functions[0], str):
        raise ValueError('ONE_SEARCH_FUNCTION_REQUIRED')
    source = functions[0]
    if re.search(r'\blocal\s+OWNER_KEY_ENV\b', source):
        if source.count(MARKER.strip()) == 1:
            return None
        raise ValueError('EXISTING_OWNER_BINDING_REQUIRES_REVIEW')
    if not source.startswith('return function(conf, ctx)\n'):
        raise ValueError('FUNCTION_HEADER_REQUIRES_REVIEW')
    if source.count('local owner_key = os.getenv(OWNER_KEY_ENV)') != 1:
        raise ValueError('EXPECTED_OWNER_LOOKUP_REQUIRED')
    if not re.search(r'^local DELEGATION_KEY_ENV = "[A-Z][A-Z0-9_]*"$', source, re.M):
        raise ValueError('DELEGATION_BINDING_REQUIRED')
    for fragment in ("'urban.object.search'", "'udp-object-search-owner'", "'X-OUF-UDP-Search-Receipt'"):
        if fragment not in source:
            raise ValueError('EXPECTED_SEARCH_CONTRACT_REQUIRED')
    new = copy.deepcopy(route)
    header = 'return function(conf, ctx)\n'
    new['plugins']['serverless-post-function']['functions'][0] = header + MARKER + source[len(header):]
    check = copy.deepcopy(new)
    check['plugins']['serverless-post-function']['functions'][0] = check['plugins']['serverless-post-function']['functions'][0].replace(MARKER, '', 1)
    if check != route:
        raise ValueError('UNRELATED_ROUTE_CHANGE_DENIED')
    return new


ADMIN_WORKER = r"""
import json,sys,urllib.request,urllib.error
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None
try:
    doc=json.load(sys.stdin)
    if doc['method'] not in ('GET','PUT'): raise ValueError()
    data=None if doc['route'] is None else json.dumps(doc['route'],separators=(',',':')).encode()
    request=urllib.request.Request('http://127.0.0.1:9180/apisix/admin/routes/execute-urban-object-search',method=doc['method'],data=data,headers={'X-API-KEY':doc['key'],'Content-Type':'application/json'})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    with opener.open(request,timeout=5) as response:
        body=response.read(2*1024*1024+1)
        if len(body)>2*1024*1024: raise ValueError()
        result=json.loads(body)
        value=result.get('value') or (result.get('node') or {}).get('value')
        if not isinstance(value,dict): raise ValueError()
        print(json.dumps(value))
except urllib.error.HTTPError as error:
    print('ADMIN_HTTP_'+str(error.code),file=sys.stderr);sys.exit(1)
except Exception:
    print('ADMIN_TRANSPORT_OR_RESPONSE_INVALID',file=sys.stderr);sys.exit(1)
"""


def validate_admin_metadata(metadata, owner_uid):
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != owner_uid or stat.S_IMODE(metadata.st_mode) & 0o077:
        raise ValueError('PRIVATE_ADMIN_KEY_OWNER_OR_MODE_MISMATCH')


class Admin:
    def __init__(self, pid, key, nsenter, python):
        if not isinstance(pid,int) or pid <= 0:
            raise ValueError('RUNNING_GATEWAY_PID_REQUIRED')
        self.namespace_fd=os.open('/proc/'+str(pid)+'/ns/net',os.O_RDONLY)
        self.key=key
        self.nsenter=nsenter
        self.python=python

    def call(self, method, route=None):
        result=subprocess.run([self.nsenter,'--net=/proc/self/fd/'+str(self.namespace_fd),self.python,'-I','-B','-c',ADMIN_WORKER],
                              input=json.dumps({'key':self.key,'method':method,'route':route}),
                              capture_output=True,text=True,timeout=10,pass_fds=(self.namespace_fd,))
        if result.returncode:
            code=result.stderr.strip()
            if not re.fullmatch(r'ADMIN_HTTP_[0-9]{3}|ADMIN_TRANSPORT_OR_RESPONSE_INVALID',code):
                code='ADMIN_WORKER_FAILED'
            raise ValueError(code)
        value=json.loads(result.stdout)
        if not isinstance(value,dict):
            raise ValueError('ADMIN_ROUTE_RESPONSE_REQUIRED')
        return value

    def close(self):
        os.close(self.namespace_fd)


def transaction(admin, old, new):
    if canonical(admin.call('GET')) != canonical(old):
        raise ValueError('LIVE_ROUTE_CHANGED_BEFORE_WRITE')
    try:
        admin.call('PUT', canonical(new))
        if canonical(admin.call('GET')) != canonical(new):
            raise ValueError('REPAIR_READBACK_MISMATCH')
    except Exception:
        # Restore only our exact new state. Do not overwrite concurrent changes.
        try:
            current = canonical(admin.call('GET'))
            if current == canonical(old):
                return 'BLOCKED_ORIGINAL_PRESENT'
            if current != canonical(new):
                return 'BLOCKED_CONCURRENT_OR_UNKNOWN_STATE_REVIEW_REQUIRED'
            admin.call('PUT', canonical(old))
            if canonical(admin.call('GET')) == canonical(old):
                return 'BLOCKED_ORIGINAL_RESTORED'
        except Exception:
            pass
        return 'BLOCKED_ROLLBACK_UNVERIFIED_REVIEW_REQUIRED'
    return 'REPAIRED_AND_READBACK_VERIFIED'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--diagnose', action='store_true')
    mode.add_argument('--diagnose-upstream', action='store_true')
    parser.add_argument('--udp', default='ouf-udp')
    parser.add_argument('--docker', required=True)
    parser.add_argument('--gateway', required=True)
    parser.add_argument('--network', required=True)
    parser.add_argument('--admin-key-file', type=Path, required=True)
    parser.add_argument('--admin-key-owner-uid', type=int, required=True)
    parser.add_argument('--nsenter', required=True)
    parser.add_argument('--backup-root', type=Path, required=True)
    args = parser.parse_args()
    if os.geteuid() != 0 or not args.docker.startswith('/') or not args.nsenter.startswith('/') or args.admin_key_owner_uid < 0 or any(not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', x) for x in (args.gateway, args.network,args.udp)):
        raise SystemExit('SEARCH_OWNER_BINDING=ROOT_AND_EXPLICIT_BINDINGS_REQUIRED')
    stage = 'CONTAINER_BINDING_READ'
    try:
        result = subprocess.run([args.docker, 'inspect', '--type', 'container', args.gateway], capture_output=True, timeout=10, check=True)
        gateway = json.loads(result.stdout)[0]
        if gateway.get('State', {}).get('Running') is not True:
            raise ValueError('GATEWAY_NOT_RUNNING')
        env = dict(item.split('=', 1) for item in gateway['Config']['Env'])
        if not re.fullmatch(r'[a-fA-F0-9]{64}', env.get('OUF_UDP_SEARCH_OWNER_KEY', '')):
            raise ValueError('EXISTING_SEARCH_KEY_REQUIRED')
        if args.network not in gateway['NetworkSettings']['Networks']:
            raise ValueError('EXPECTED_GATEWAY_NETWORK_REQUIRED')
        stage = 'GENERATED_ENV_DIRECTIVE_READ'
        generated = subprocess.run([args.docker, 'exec', args.gateway, 'cat', '/usr/local/apisix/conf/nginx.conf'], capture_output=True, timeout=10, check=True).stdout.decode('utf-8')
        inherited = env_directive_present(generated, 'OUF_UDP_SEARCH_OWNER_KEY')
        stage = 'EXISTING_ADMIN_KEY_READ'
        metadata = args.admin_key_file.lstat()
        validate_admin_metadata(metadata, args.admin_key_owner_uid)
        key = args.admin_key_file.read_text().strip()
        if not key or any(c.isspace() for c in key) or len(key) > 4096:
            raise ValueError('ADMIN_KEY_FORMAT_INVALID')
        stage = 'EXISTING_ADMIN_LOOPBACK_NAMESPACE'
        admin = Admin(gateway['State']['Pid'], key, args.nsenter, '/usr/bin/python3')
        stage = 'SEARCH_ROUTE_GET_AND_EXACT_DELTA_REVIEW'
        old = admin.call('GET')
        if args.diagnose_upstream:
            diagnose_bindings(old,env,generated)
            stage='SEARCH_UPSTREAM_READ_ONLY_PROBE'
            print('SEARCH_UPSTREAM=' + json.dumps(diagnose_upstream(old,gateway,admin,args)))
            admin.close()
            return
        if args.diagnose:
            print('SEARCH_KEY_BINDINGS=' + json.dumps(diagnose_bindings(old, env, generated)))
            admin.close()
            return
        new = proposed(old)
        if new is None:
            print('SEARCH_OWNER_BINDING=' + json.dumps({'status': 'ALREADY_DECLARED', 'generatedSearchEnvDirectivePresent': inherited, 'routeChanged': False, 'positiveSearchProven': False}))
            return
        if not inherited:
            print('SEARCH_OWNER_BINDING=MISSING_DECLARATION GENERATED_SEARCH_ENV_DIRECTIVE_ABSENT=true NO_ROUTE_CHANGED=true')
            return
        if not args.apply:
            print('SEARCH_OWNER_BINDING=MISSING_DECLARATION_EXACT_REPAIR_READY NO_ROUTE_CHANGED=true')
            return
        stage = 'PRIVATE_SNAPSHOT'
        root = args.backup_root.lstat()
        if not stat.S_ISDIR(root.st_mode) or root.st_uid != 0 or stat.S_IMODE(root.st_mode) & 0o022:
            raise ValueError('ROOT_BACKUP_DIRECTORY_NOT_WRITABLE_BY_OTHERS_REQUIRED')
        os.umask(0o077)
        folder = Path(tempfile.mkdtemp(prefix='search-owner-binding-', dir=args.backup_root))
        previous = folder / 'previous-route.json'
        with previous.open('x') as output:
            json.dump(old, output)
            output.flush()
            os.fsync(output.fileno())
        stage = 'EXACT_ROUTE_REPAIR_AND_READBACK'
        status = transaction(admin, old, new)
        report = {'status': status, 'snapshotDirectory': str(folder), 'routeId': ROUTE,
                  'onlyAddedOwnerKeyDeclaration': True, 'secretValuesPrinted': False,
                  'configurationSnapshotModified': False, 'containerRestarted': False,
                  'positiveSearchProven': False}
        print('SEARCH_OWNER_BINDING=' + json.dumps(report, sort_keys=True))
        if status != 'REPAIRED_AND_READBACK_VERIFIED':
            raise SystemExit(1)
    except Exception as error:
        code=str(error) if isinstance(error,ValueError) and re.fullmatch(r'[A-Z][A-Z0-9_]{0,100}',str(error)) else type(error).__name__
        raise SystemExit('SEARCH_OWNER_BINDING=BLOCKED STAGE=' + stage + ' REASON=' + code + ' NO_RAW_OUTPUT=true')


if __name__ == '__main__':
    main()
