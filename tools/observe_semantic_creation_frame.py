"""Fresh source bytes plus real created-PID bind facts for an acceptance issuer.

Expected hashes/custody/OCI must come from independently authenticated policy.
This collector is read-only, spools no content and confers no authority.
"""
import hashlib,hmac,os,re,stat
from pathlib import Path
from tools import observe_semantic_mount_view as mounts
from tools.review_semantic_oci_policy import Denied,require,canonical,path,configured_profile

FIELDS={'source','target','readOnly','uid','gid','mode','sha256','maxBytes'}

def inputs(values):
    require(type(values) is list and 1<=len(values)<=32,'EXACT_SOURCE_FRAME_INPUTS_REQUIRED')
    seen=set()
    for item in values:
        require(type(item) is dict and set(item)==FIELDS,'EXACT_SOURCE_FRAME_INPUTS_REQUIRED')
        path(item['source']);path(item['target'])
        require(item['target'] not in seen and item['readOnly'] is True,'EXACT_SOURCE_FRAME_INPUTS_REQUIRED')
        seen.add(item['target'])
        require(all(type(item[k]) is int and 0<=item[k]<2**32 for k in ('uid','gid'))
            and type(item['mode']) is int and 0<item['mode']<=0o777 and not item['mode']&0o022
            and type(item['maxBytes']) is int and 1<=item['maxBytes']<=131072
            and type(item['sha256']) is str and re.fullmatch('[0-9a-f]{64}',item['sha256']),
            'EXACT_SOURCE_FRAME_INPUTS_REQUIRED')

def source_hash(item,held,before,budget):
    budget.check();fd=os.open(item['source'],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        info=os.fstat(fd)
        require(mounts.attributes(info)==before==mounts.attributes(os.fstat(held))
            and stat.S_ISREG(info.st_mode) and info.st_nlink==1
            and (info.st_uid,info.st_gid,stat.S_IMODE(info.st_mode))==(item['uid'],item['gid'],item['mode'])
            and 0<info.st_size<=item['maxBytes'],'SOURCE_FRAME_CUSTODY_DRIFT')
        digest=hashlib.sha256();count=0
        while True:
            budget.check();part=os.read(fd,min(65536,item['maxBytes']+1-count))
            if not part:break
            count+=len(part);require(count<=item['maxBytes'],'SOURCE_FRAME_BYTES_UNBOUNDED');digest.update(part)
        budget.check()
        require(count==info.st_size and before==mounts.attributes(os.fstat(fd))
            ==mounts.attributes(os.fstat(held))==mounts.attributes(Path(item['source']).lstat()),'SOURCE_FRAME_CHANGED')
        require(hmac.compare_digest(digest.hexdigest(),item['sha256']),'SOURCE_FRAME_BYTE_HASH_DRIFT')
        return count
    finally:os.close(fd)

def source_mount_frame(pid,expected_generation,bundle,sources,budget=None):
    """Double-read source hashes around mount observation, sharing <=5 seconds.

    Repeated stable reads detect drift; they do not prove an atomic snapshot or
    resistance to an administrator/kernel that can alter the observation.
    """
    budget=budget or mounts.Budget();opened=[]
    try:
        inputs(sources);source_inputs=canonical(sources);bundle_inputs=canonical(bundle)
        generation_inputs=canonical(expected_generation);budget.check()
        require(mounts.generation(pid,budget)==expected_generation,'CREATED_GENERATION_DRIFT')
        for item in sources:
            fd,info=mounts.source_fd(item['source'],budget)
            opened.append((fd,mounts.attributes(info)))
        sizes=[source_hash(item,fd,info,budget) for item,(fd,info) in zip(sources,opened)]
        bindings=[{k:item[k] for k in ('source','target','readOnly')} for item in sources]
        observed=mounts.observe(pid,expected_generation,bundle,bindings,[info for _,info in opened],budget)
        require(sizes==[source_hash(item,fd,info,budget) for item,(fd,info) in zip(sources,opened)],'SOURCE_FRAME_CHANGED')
        require(mounts.generation(pid,budget)==expected_generation,'CREATED_GENERATION_DRIFT')
        require(source_inputs==canonical(sources) and bundle_inputs==canonical(bundle)
            and generation_inputs==canonical(expected_generation),'CREATION_FRAME_INPUT_DRIFT');budget.check()
        return {'schema':'ouf.semantic-created-source-mount-frame.v1','mountObservation':observed,
            'sourceFiles':[{'slot':index,'sha256':item['sha256'],'bytes':size}
                for index,(item,size) in enumerate(zip(sources,sizes))],
            'sourceByteHashesMatchExpected':True,'sourceBytesRead':sum(sizes)*2,
            'stableAcrossReads':True,'atomicSnapshotProven':False,'policyAuthenticationProven':False,
            'privateMaterialSpooled':False,'completeCreationAccepted':False,
            'acceptanceGranted':False,'signaturesIssued':0,'startAuthorized':False}
    except Denied:raise
    except (OSError,ValueError,TypeError,KeyError,UnicodeError):
        raise Denied('CREATION_FRAME_OBSERVATION_UNPROVEN') from None
    finally:
        for fd,_ in opened:os.close(fd)

def configured_creation_frame(pid,expected_generation,bundle,expected,spec,startup,hooks,schema,sources,budget=None):
    budget=budget or mounts.Budget();budget.check()
    approved=configured_profile(bundle,expected,spec,startup,hooks,schema)
    inputs(sources)
    require(canonical([{k:item[k] for k in ('source','target','readOnly')} for item in sources])
        ==canonical(spec['mounts']),'EXACT_SOURCE_FRAME_MOUNT_BINDING_REQUIRED')
    before=canonical(bundle)
    frame=source_mount_frame(pid,expected_generation,bundle,sources,budget)
    require(before==canonical(bundle) and approved==configured_profile(bundle,expected,spec,startup,hooks,schema),
        'CONFIGURED_CREATION_FRAME_DRIFT');budget.check()
    return {'schema':'ouf.semantic-configured-created-frame.v1','configuredPolicy':approved,'sourceMountFrame':frame,
        'policyAuthenticationProven':False,'rootfsSealProven':False,'imagePublisherProvenanceVerified':False,
        'completeCreationAccepted':False,'acceptanceGranted':False,'signaturesIssued':0,'startAuthorized':False}
