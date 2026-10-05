"""Typed complete OCI document review against an independently prepared policy.

This is an unsigned policy check. It cannot authenticate the supplied policy,
observe kernel enforcement, issue an acceptance mandate or authorize a start.
The schema accompanies this source in the sealed issuer source closure.
"""
import hashlib
import json
from pathlib import PurePosixPath,Path
import re

class Denied(ValueError):
    pass

def require(ok,code='OCI_POLICY_UNPROVEN'):
    if not ok:raise Denied(code)

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def shape(value,kind,schema,budget=None,depth=0):
    if budget is None:budget=[16384]
    budget[0]-=1;require(budget[0]>=0 and depth<=32,'OCI_SHAPE_UNBOUNDED')
    recurse=lambda v,k:shape(v,k,schema,budget,depth+1)
    if kind.startswith('*'):
        if value is not None:recurse(value,kind[1:])
    elif kind.startswith('[]'):
        require(value is None or type(value) is list,'OCI_TYPE_UNPROVEN')
        if value is not None:
            require(len(value)<=4096,'OCI_SHAPE_UNBOUNDED')
            for item in value:recurse(item,kind[2:])
    elif kind.startswith('map[string]'):
        require(value is None or type(value) is dict,'OCI_TYPE_UNPROVEN')
        if value is not None:
            require(len(value)<=4096,'OCI_SHAPE_UNBOUNDED')
            for key,item in value.items():
                require(type(key) is str and len(key)<=256 and '\x00' not in key,'OCI_TYPE_UNPROVEN')
                recurse(item,kind[11:])
    elif kind in schema['structs']:
        fields=schema['structs'][kind]['fields']
        require(type(value) is dict and not set(value)-set(fields)
                and all(k in value for k,v in fields.items() if not v['optional']),'OCI_FIELDS_UNPROVEN')
        for key,item in value.items():recurse(item,fields[key]['type'])
    elif kind in schema['aliases']:
        alias=schema['aliases'][kind];recurse(value,alias['type'])
        require(not alias['values'] or value in alias['values'],'OCI_ENUM_UNPROVEN')
    elif kind=='bool':require(type(value) is bool,'OCI_TYPE_UNPROVEN')
    elif kind=='string':require(type(value) is str and len(value)<=16384 and '\x00' not in value,'OCI_TYPE_UNPROVEN')
    elif kind=='os.FileMode' or re.fullmatch('u?int(?:16|32|64)?',kind):
        bits=32 if kind=='os.FileMode' else int(re.search(r'\d+',kind)[0]) if re.search(r'\d+',kind) else 64
        unsigned=kind.startswith('u') or kind=='os.FileMode'
        require(type(value) is int and (0 if unsigned else -(1<<(bits-1)))<=value<1<<(bits if unsigned else bits-1),'OCI_TYPE_UNPROVEN')
    else:raise Denied('OCI_UNSUPPORTED_TYPE')

def path(value):
    require(type(value) is str and value.startswith('/') and '\x00' not in value and len(value)<=4096
            and '..' not in value.split('/') and str(PurePosixPath(value))==value,'OCI_PATH_UNPROVEN')
    return value

def env(rows):
    require(type(rows) is list and len(rows)<=256,'OCI_ENV_UNPROVEN');values={}
    for row in rows:
        require(type(row) is str and '=' in row and len(row)<=16384,'OCI_ENV_UNPROVEN')
        name,value=row.split('=',1)
        require(re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',name) and name not in values,'OCI_ENV_UNPROVEN')
        values[name]=value
    return values

def configured_profile(bundle,expected,spec,startup,approved_hooks,schema):
    """Fail closed on complete OCI shape, exact prepared policy and hardening.

    All inputs must subsequently be source/custody/authenticated by the issuer.
    startup comes from image/launch compilation, not from copying bundle values.
    Proposed hardening checks are not a substitute for PET supply-chain gates.
    """
    require(len(canonical(bundle))<=131072 and len(canonical(expected))<=131072,'OCI_SHAPE_UNBOUNDED')
    shape(bundle,'Spec',schema);shape(expected,'Spec',schema)
    require(canonical(bundle)==canonical(expected),'OCI_EXACT_POLICY_DRIFT')
    require(bundle['ociVersion'] in ('1.0.2','1.1.0','1.2.0','1.2.1','1.3.0') and
            not any(k in bundle for k in ('windows','solaris','vm','zos','freebsd')),'OCI_LINUX_PROFILE_REQUIRED')
    process,root,linux=bundle.get('process'),bundle.get('root'),bundle.get('linux')
    require(all(type(v) is dict for v in (process,root,linux)),'OCI_LINUX_PROFILE_REQUIRED')
    require(set(startup)=={'args','cwd','env','uid','gid','umask'},'OCI_STARTUP_INPUT_REQUIRED')
    require(type(startup['uid']) is int and type(startup['gid']) is int and startup['uid']>0 and startup['gid']>0
            and spec['user']==str(startup['uid'])+':'+str(startup['gid']),'OCI_NONROOT_IDENTITY_REQUIRED')
    require(process.get('terminal',False) is False and process.get('noNewPrivileges') is True
            and not any(k in process for k in ('consoleSize','commandLine','scheduler','ioPriority','execCPUAffinity')),
            'OCI_PROCESS_HARDENING_REQUIRED')
    require(type(process.get('args')) is list and bool(process['args']) and all(type(v) is str for v in process['args'])
            and canonical(process['args'])==canonical(startup['args']) and process['cwd']==startup['cwd'],
            'OCI_COMPILED_STARTUP_DRIFT')
    path(process['cwd']);require(env(process.get('env',[]))==env(startup['env']),'OCI_COMPILED_ENV_DRIFT')
    # Docker's reviewed WithUser emits the primary GID once in AdditionalGids.
    # That adds no group authority; any other group or duplicate is rejected.
    user=process['user'];groups=user.get('additionalGids') or []
    require(user['uid']==startup['uid'] and user['gid']==startup['gid']
        and groups in ([],[startup['gid']]) and not user.get('username') and user.get('umask')==startup['umask'],
        'OCI_USER_PROFILE_DRIFT')
    caps=process.get('capabilities');require(type(caps) is dict and all(not v for v in caps.values()),'OCI_CAPABILITIES_DENIED')
    require(process.get('apparmorProfile','')!='unconfined' and process.get('oomScoreAdj',0)==0,'OCI_PROCESS_HARDENING_REQUIRED')
    path(root['path']);require(root.get('readonly',False) is spec['readOnlyRoot'],'OCI_ROOT_PROFILE_DRIFT')
    hooks=bundle.get('hooks') or {};require(not set(hooks)-{'prestart','createRuntime'}
        and canonical(hooks)==canonical(approved_hooks),'OCI_COMPILED_HOOK_DRIFT')
    for values in hooks.values():
        for hook in values:
            path(hook['path']);require(type(hook.get('timeout')) is int and 1<=hook['timeout']<=40,'OCI_HOOK_UNBOUNDED')
            require(hook.get('args') and hook['args'][0]==hook['path'],'OCI_HOOK_PROFILE_DRIFT')
    namespaces=linux.get('namespaces');require(type(namespaces) is list,'OCI_NAMESPACE_PROFILE_REQUIRED')
    mapping={v['type']:v for v in namespaces}
    # Moby 29.8.1 preserves its default private time namespace when supported
    # by the kernel (WithNamespaces removes it on unsupported kernels).
    # No joined time namespace or time offset is accepted by this profile.
    required_namespaces={'mount','pid','ipc','uts','network','cgroup'}
    require(len(mapping)==len(namespaces) and required_namespaces<=set(mapping)
            and set(mapping)<=required_namespaces|{'time'}
            and all(not v.get('path') for k,v in mapping.items() if k!='network')
            and not linux.get('uidMappings') and not linux.get('gidMappings'),'OCI_PRIVATE_NAMESPACES_REQUIRED')
    if mapping['network'].get('path'):path(mapping['network']['path'])
    require(not any(linux.get(k) for k in ('timeOffsets','intelRdt','personality')) and
            linux.get('rootfsPropagation','') in ('','rprivate'),'OCI_UNSUPPORTED_HOST_FEATURE')
    require('/proc/kcore' in (linux.get('maskedPaths') or []) and '/proc/sys' in (linux.get('readonlyPaths') or []),
            'OCI_PROTECTED_PATHS_REQUIRED')
    for key in ('maskedPaths','readonlyPaths'):
        values=linux[key];require(len(set(values))==len(values),'OCI_PROTECTED_PATHS_REQUIRED')
        for value in values:path(value)
    resources=linux.get('resources') or {};memory=resources.get('memory') or {};pids=resources.get('pids') or {}
    require(type(spec['memoryBytes']) is int and 16777216<=spec['memoryBytes']<=2147483648
        and type(spec['pidsLimit']) is int and 1<=spec['pidsLimit']<=4096
        and memory.get('limit')==memory.get('swap')==spec['memoryBytes'] and memory.get('disableOOMKiller',False) is False
        and pids.get('limit')==spec['pidsLimit'],'OCI_RESOURCE_BOUNDS_REQUIRED')
    for item in resources.get('devices') or []:
        major,minor=item.get('major'),item.get('minor')
        permitted=major==1 and minor in (3,5,7,8,9) or major==5 and minor in (0,1,2) or major==136 and minor is None
        mknod_only=item.get('type') in ('c','b') and major is None and minor is None and item.get('access')=='m'
        require(not item['allow'] or mknod_only or item.get('type')=='c' and permitted,
                'OCI_UNRESTRICTED_DEVICES_DENIED')
    for device in linux.get('devices') or []:
        require(device['type']=='c' and (device['major'],device['minor']) in
                {(1,3),(1,5),(1,7),(1,8),(1,9),(5,0),(5,1),(5,2)},'OCI_HOST_DEVICE_DENIED')
        path(device['path'])
    seccomp=linux.get('seccomp');require(type(seccomp) is dict and seccomp['defaultAction'] in
        ('SCMP_ACT_ERRNO','SCMP_ACT_KILL_PROCESS','SCMP_ACT_KILL_THREAD')
        and 'SCMP_ARCH_X86_64' in (seccomp.get('architectures') or [])
        and set(seccomp['architectures'])<={'SCMP_ARCH_X86_64','SCMP_ARCH_X86','SCMP_ARCH_X32'}
        and not seccomp.get('listenerPath') and not seccomp.get('listenerMetadata'),'OCI_SECCOMP_PROFILE_REQUIRED')
    for syscall in seccomp.get('syscalls') or []:
        require(syscall['action'] not in ('SCMP_ACT_NOTIFY','SCMP_ACT_TRACE','SCMP_ACT_LOG'),'OCI_SECCOMP_ESCAPE_DENIED')
        require(syscall.get('errnoRet',0) is None or syscall.get('errnoRet',0)<=4095,'OCI_SECCOMP_ARGUMENT_UNPROVEN')
        for argument in syscall.get('args') or []:
            require(argument['index']<=5,'OCI_SECCOMP_ARGUMENT_UNPROVEN')
    require(seccomp.get('defaultErrnoRet',0) is None or seccomp.get('defaultErrnoRet',0)<=4095,'OCI_SECCOMP_ARGUMENT_UNPROVEN')
    mounts=bundle.get('mounts') or [];seen={}
    for mount in mounts:
        target=path(mount['destination']);require(target not in seen and not mount.get('uidMappings') and not mount.get('gidMappings'),
            'OCI_MOUNT_PROFILE_DRIFT');seen[target]=mount
    declared={v['target']:v for v in spec['mounts']};require(len(declared)==len(spec['mounts']),'OCI_MOUNT_PROFILE_DRIFT')
    for target,item in declared.items():
        require(item['readOnly'] is True and target in seen,'OCI_MANIFEST_MOUNT_DRIFT');actual=seen[target]
        require(actual.get('type')=='bind' and actual.get('source')==item['source'] and 'ro' in (actual.get('options') or [])
            and not set(actual.get('options') or [])&{'rw','shared','rshared','slave','rslave'},'OCI_MANIFEST_MOUNT_DRIFT')
    kernel={'/proc','/dev','/dev/pts','/dev/shm','/dev/mqueue','/sys','/sys/fs/cgroup','/etc/hosts','/etc/hostname','/etc/resolv.conf'}
    require(not set(seen)-set(declared)-kernel,'OCI_UNDECLARED_MOUNT_DENIED')
    return {'schema':'ouf.semantic-configured-oci-policy-review.v1','configuredPolicyConforms':True,
        'completeOciShapeReviewed':True,'applicationHash':hashlib.sha256(canonical(bundle)).hexdigest(),
        'policyAuthenticationProven':False,'kernelEnforcementObserved':False,'mountViewInspected':False,
        'generationObserved':False,'rootfsSealProven':False,'imagePublisherProvenanceVerified':False,
        'completeCreationAccepted':False,'allConfigurationFieldsSemanticallyAccepted':False,
        'acceptanceGranted':False,'signaturesIssued':0,'startAuthorized':False}

def schema_from_source_closure():
    # Not an independent authority lookup: issuer must source-seal this JSON
    # with its program before invoking the reviewer.
    raw=(Path(__file__).with_name('semantic_oci_shape_schema.json')).read_bytes()
    require(len(raw)<=131072,'OCI_SCHEMA_UNBOUNDED');value=json.loads(raw)
    require(value['schema']=='ouf.oci-runtime-shape-schema.v1' and
        value['sourceCommit']=='92249139eea7161e13745abd4cb6d0ea02a3227a','OCI_SCHEMA_SOURCE_DRIFT')
    return value
