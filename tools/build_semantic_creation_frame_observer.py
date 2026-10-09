"""Deterministically bundle the reviewed observer closure for isolated Python.

CI regenerates and checks this artifact; deployment still pins its exact bytes.
No private policy, credential, key or target input is embedded in the source.
"""
import hashlib,json
from pathlib import Path

MODULES=('review_semantic_oci_policy','observe_semantic_mount_view','observe_semantic_creation_frame')
PREFIX='''"""Generated source-sealed observer; stdin private data, stdout redacted facts."""
import argparse,hashlib,json,os,signal,stat,sys,types
from pathlib import Path
'''
SUFFIX='''
def decode(raw):
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:raise ValueError('DUPLICATE_INPUT')
            result[key]=value
        return result
    return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda value:(_ for _ in ()).throw(ValueError('NONFINITE_INPUT')))

def main():
    try:
        def deadline(signum,frame):raise TimeoutError('FRAME_INVOCATION_TIMEOUT')
        signal.signal(signal.SIGALRM,deadline);signal.alarm(5)
        if os.geteuid()!=0 or not sys.flags.isolated or not sys.dont_write_bytecode:raise ValueError('ISOLATED_ROOT_REQUIRED')
        parser=argparse.ArgumentParser();parser.add_argument('--configuration',required=True)
        args=parser.parse_args()
        def private(filename):
            filename=Path(filename)
            if not filename.is_absolute() or '..' in filename.parts:raise ValueError('PRIVATE_INPUT_REQUIRED')
            for parent in filename.parents:
                info=parent.lstat()
                if not stat.S_ISDIR(info.st_mode) or info.st_uid!=0 or info.st_mode&0o022:raise ValueError('PRIVATE_INPUT_REQUIRED')
            info=filename.parent.lstat()
            if info.st_gid!=0 or stat.S_IMODE(info.st_mode)!=0o700:raise ValueError('PRIVATE_INPUT_REQUIRED')
            fd=os.open(filename,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
            try:
                info=os.fstat(fd)
                if not stat.S_ISREG(info.st_mode) or info.st_uid!=0 or info.st_gid!=0 or info.st_nlink!=1 or stat.S_IMODE(info.st_mode)!=0o600 or not 0<info.st_size<=131072:raise ValueError('PRIVATE_INPUT_REQUIRED')
                raw=os.read(fd,131073)
                if len(raw)!=info.st_size or attributes(info)!=attributes(os.fstat(fd)) or attributes(info)!=attributes(filename.lstat()):raise ValueError('PRIVATE_INPUT_DRIFT')
                return raw
            finally:os.close(fd)
        request_raw=sys.stdin.buffer.read(4097)
        if not 0<len(request_raw)<=4096:raise ValueError('BOUNDED_REQUEST_REQUIRED')
        request=decode(request_raw)
        if set(request)!={'pid','generation','bundlePath','applicationHash','policyHash'}:raise ValueError('EXACT_REQUEST_REQUIRED')
        policy_raw=private(args.configuration)
        if hashlib.sha256(policy_raw).hexdigest()!=request['policyHash']:raise ValueError('PRIVATE_POLICY_DRIFT')
        policy=decode(policy_raw)
        if set(policy)!={'schema','expectedOci','manifest','startup','approvedHooks','sources'} or policy['schema']!='ouf.semantic-configured-creation-frame-policy.v1':raise ValueError('EXACT_POLICY_REQUIRED')
        bundle_raw=private(request['bundlePath']);bundle=decode(bundle_raw)
        if hashlib.sha256(canonical(bundle)).hexdigest()!=request['applicationHash']:raise ValueError('PRIVATE_BUNDLE_DRIFT')
        current=generation(request['pid'],Budget())
        expected=request['generation']
        if set(expected)!={'pid','startTicks','namespaceInode'} or any(type(expected[k]) is not int for k in expected) or (current['pid'],current['startTicks'],current['networkNamespaceInode'])!=(expected['pid'],expected['startTicks'],expected['namespaceInode']):raise ValueError('CREATED_GENERATION_DRIFT')
        result=configured_creation_frame(request['pid'],current,bundle,policy['expectedOci'],
            policy['manifest'],policy['startup'],policy['approvedHooks'],SCHEMA,policy['sources'])
        if private(args.configuration)!=policy_raw or private(request['bundlePath'])!=bundle_raw:raise ValueError('PRIVATE_INPUT_DRIFT')
        sys.stdout.buffer.write(canonical(result));signal.alarm(0);return 0
    except Exception:
        print('SEMANTIC_CREATION_FRAME=DENIED NO_SECRETS_PRINTED=true',file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
'''

def build(root):
    sources={name:(root/(name+'.py')).read_text() for name in MODULES}
    schema=(root/'semantic_oci_shape_schema.json').read_bytes()
    digest={name:hashlib.sha256(raw.encode()).hexdigest() for name,raw in sources.items()}
    digest['semantic_oci_shape_schema.json']=hashlib.sha256(schema).hexdigest()
    loader='\nSOURCE_HASHES='+repr(digest)+'\nSOURCES='+repr(sources)+'\nSCHEMA_BYTES='+repr(schema)+'\n'
    loader+='''
package=types.ModuleType('tools');package.__path__=[];sys.modules['tools']=package
for name,source in SOURCES.items():
    module=types.ModuleType('tools.'+name);module.__package__='tools';module.__file__='<ouf-source-sealed-observer>'
    sys.modules[module.__name__]=module;setattr(package,name,module)
    exec(compile(source,module.__file__,'exec'),module.__dict__)
from tools.review_semantic_oci_policy import canonical,schema_from_source_closure
from tools.observe_semantic_mount_view import attributes,generation,Budget
from tools.observe_semantic_creation_frame import configured_creation_frame
SCHEMA=schema_from_source_closure(SCHEMA_BYTES)
'''
    return PREFIX+loader+SUFFIX

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();args.output.write_text(build(Path(__file__).parent))
