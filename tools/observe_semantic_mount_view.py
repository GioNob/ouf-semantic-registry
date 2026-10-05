"""Bounded real-PID file-bind mount observation; no application start/content IO.

Caller must authenticate OCI/source custody and the created runtime state.
This module cannot issue complete acceptance or prove source byte hashes.
"""
import hashlib,os,re,stat,time
from pathlib import Path,PurePosixPath
from tools.review_semantic_oci_policy import require,canonical,path

class Budget:
    def __init__(self,seconds=5):
        require(type(seconds) is int and 1<=seconds<=5,'MOUNT_BUDGET_REQUIRED');self.end=time.monotonic()+seconds
    def check(self):require(time.monotonic()<self.end,'MOUNT_OBSERVATION_TIMEOUT')

def attributes(value):
    return tuple(getattr(value,k) for k in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))

def proc_read(filename,budget,limit):
    budget.check();fd=os.open(filename,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        info=os.fstat(fd);require(stat.S_ISREG(info.st_mode),'KERNEL_PROC_FILE_REQUIRED')
        raw=bytearray()
        while True:
            budget.check();part=os.read(fd,min(65536,limit+1-len(raw)))
            if not part:break
            raw.extend(part);require(len(raw)<=limit,'KERNEL_PROC_FILE_UNBOUNDED')
        return bytes(raw)
    finally:os.close(fd)

def generation(pid,budget):
    require(type(pid) is int and 1<pid<2**31,'CREATED_PID_REQUIRED')
    root=Path('/proc')/str(pid);raw=proc_read(root/'stat',budget,16384)
    boundary=raw.rfind(b') ');require(boundary>0 and raw.split(b' ',1)[0]==str(pid).encode(),'KERNEL_GENERATION_UNPROVEN')
    values=raw[boundary+2:].split();require(len(values)>=20 and values[19].isdigit(),'KERNEL_GENERATION_UNPROVEN')
    boot=proc_read(Path('/proc/sys/kernel/random/boot_id'),budget,256).strip().decode('ascii')
    require(re.fullmatch('[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}',boot),'KERNEL_GENERATION_UNPROVEN')
    budget.check()
    return {'pid':pid,'bootId':boot,'startTicks':int(values[19]),
        'mountNamespaceInode':(root/'ns/mnt').stat().st_ino,'networkNamespaceInode':(root/'ns/net').stat().st_ino}

def unescape(value):
    require(not re.search(r'\\(?!040|011|012|134)',value),'MOUNTINFO_ESCAPE_UNPROVEN')
    return re.sub(r'\\(040|011|012|134)',lambda m:chr(int(m[1],8)),value)

def mountinfo(raw):
    require(type(raw) is bytes and 0<len(raw)<=131072 and b'\x00' not in raw,'MOUNTINFO_UNBOUNDED')
    rows=[];ids=set()
    for line in raw.decode('utf-8').splitlines():
        fields=line.split(' ');require(fields.count('-')==1,'MOUNTINFO_SHAPE_UNPROVEN');boundary=fields.index('-')
        require(boundary>=6 and len(fields)==boundary+4 and fields[0].isdigit() and fields[1].isdigit()
            and re.fullmatch(r'\d+:\d+',fields[2]),'MOUNTINFO_SHAPE_UNPROVEN')
        mid=int(fields[0]);require(mid>0 and mid not in ids and len(rows)<4096,'MOUNTINFO_SHAPE_UNPROVEN');ids.add(mid)
        optional=fields[6:boundary]
        require(all(v=='unbindable' or re.fullmatch(r'(?:shared|master|propagate_from):[1-9]\d*',v) for v in optional),
            'MOUNTINFO_OPTION_UNPROVEN')
        rows.append({'id':mid,'parent':int(fields[1]),'device':fields[2],'root':unescape(fields[3]),
            'target':unescape(fields[4]),'options':fields[5].split(','),'optional':optional,
            'type':fields[boundary+1],'source':unescape(fields[boundary+2]),'superOptions':fields[boundary+3].split(',')})
    require(rows,'MOUNTINFO_SHAPE_UNPROVEN');return rows

def source_fd(filename,budget,directory=False):
    filename=Path(path(str(filename)));budget.check()
    for parent in filename.parents:
        info=parent.lstat();require(stat.S_ISDIR(info.st_mode) and info.st_uid==0 and not info.st_mode&0o022,
            'MOUNT_SOURCE_CUSTODY_UNPROVEN')
    fd=os.open(filename,os.O_PATH|os.O_NOFOLLOW)
    try:
        info=os.fstat(fd)
        require((stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode) and info.st_nlink==1)
            and attributes(info)==attributes(filename.lstat()),'MOUNT_SOURCE_CUSTODY_UNPROVEN')
        return fd,info
    except BaseException:os.close(fd);raise

def beneath(rootfd,target,budget):
    path(target);fd=os.dup(rootfd)
    try:
        parts=PurePosixPath(target).parts[1:]
        require(parts,'FILE_BIND_TARGET_REQUIRED')
        for index,part in enumerate(parts):
            budget.check();flags=os.O_PATH|os.O_NOFOLLOW
            if index<len(parts)-1:flags|=os.O_DIRECTORY
            nested=os.open(part,flags,dir_fd=fd);os.close(fd);fd=nested
        info=os.fstat(fd);require(stat.S_ISREG(info.st_mode),'REGULAR_FILE_BIND_REQUIRED')
        return attributes(info)
    finally:os.close(fd)

def observe(pid,expected_generation,bundle,bindings,expected_source_attributes,budget=None):
    budget=budget or Budget();before=generation(pid,budget)
    require(before==expected_generation,'CREATED_GENERATION_DRIFT')
    require(type(bindings) is list and 1<=len(bindings)<=32 and len(expected_source_attributes)==len(bindings),
        'EXACT_FILE_BIND_LIST_REQUIRED')
    root_source,root_info=source_fd(bundle['root']['path'],budget,directory=True);rootfd=None;opened=[]
    try:
        # /proc/PID/root is a deliberate kernel magic-link, anchored only after
        # checking the independently observed PID generation and namespace.
        rootfd=os.open('/proc/'+str(pid)+'/root',os.O_PATH|os.O_DIRECTORY)
        require(attributes(os.fstat(rootfd))==attributes(root_info),'CREATED_ROOTFS_IDENTITY_DRIFT')
        raw=proc_read(Path('/proc')/str(pid)/'mountinfo',budget,131072);rows=mountinfo(raw)
        by_target={r['target']:r for r in rows};require(len(by_target)==len(rows),'MOUNT_STACK_UNPROVEN')
        mandatory={v['destination'] for v in bundle.get('mounts') or []}
        allowed=mandatory|set(bundle.get('linux',{}).get('maskedPaths') or [])|set(bundle.get('linux',{}).get('readonlyPaths') or [])|{'/'}
        require(mandatory<=set(by_target) and set(by_target)<=allowed,'UNEXPLAINED_EFFECTIVE_MOUNT')
        require('/' in by_target and ('ro' in by_target['/']['options']) is bundle['root'].get('readonly',False),
            'EFFECTIVE_ROOT_READONLY_DRIFT')
        seen=set();reports=[]
        for index,(binding,approved) in enumerate(zip(bindings,expected_source_attributes)):
            require(set(binding)=={'source','target','readOnly'} and binding['readOnly'] is True
                and binding['target'] not in seen,'EXACT_FILE_BIND_LIST_REQUIRED');seen.add(binding['target'])
            fd,info=source_fd(binding['source'],budget);opened.append((fd,Path(binding['source']),attributes(info)))
            require(attributes(info)==tuple(approved),'MOUNT_SOURCE_FRAME_DRIFT')
            require(binding['target'] in by_target,'MISSING_EFFECTIVE_FILE_BIND');mounted=by_target[binding['target']]
            require('ro' in mounted['options'] and 'rw' not in mounted['options'] and not mounted['optional'],
                'EFFECTIVE_READONLY_PRIVATE_BIND_REQUIRED')
            require(beneath(rootfd,binding['target'],budget)==attributes(info),'EFFECTIVE_FILE_BIND_IDENTITY_DRIFT')
            reports.append({'slot':index,'sourceMetadataHash':hashlib.sha256(canonical(attributes(info))).hexdigest(),
                'destinationBindingHash':hashlib.sha256(binding['target'].encode()).hexdigest(),'effectiveReadOnly':True})
        require(raw==proc_read(Path('/proc')/str(pid)/'mountinfo',budget,131072),'EFFECTIVE_MOUNT_VIEW_CHANGED')
        for fd,filename,info in opened:
            require(info==attributes(os.fstat(fd))==attributes(filename.lstat()),'MOUNT_SOURCE_CHANGED')
        require(attributes(root_info)==attributes(os.fstat(root_source))==attributes(os.fstat(rootfd)),
            'CREATED_ROOTFS_IDENTITY_DRIFT')
        require(generation(pid,budget)==before,'CREATED_GENERATION_DRIFT');budget.check()
        return {'schema':'ouf.semantic-effective-file-bind-observation.v1','fileBindings':reports,
            'fileBindCount':len(reports),'effectiveMountCount':len(rows),'allMountPointsExplained':True,
            'effectiveReadOnlyFileBindingsObserved':True,'mountInfoHash':hashlib.sha256(raw).hexdigest(),
            'generationHash':hashlib.sha256(canonical(before)).hexdigest(),'stableAcrossReads':True,
            'sourceByteHashesProven':False,'fullMountViewAccepted':False,'completeCreationAccepted':False,
            'privateFileContentsRead':0,'privateMaterialSpooled':False,'acceptanceGranted':False,'startAuthorized':False}
    finally:
        for fd,_,_ in opened:os.close(fd)
        if rootfd is not None:os.close(rootfd)
        os.close(root_source)
