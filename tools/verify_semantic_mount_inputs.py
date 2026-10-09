"""Bounded private static mount input review; no acceptance, signing or start."""
import argparse
import copy
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import time
import types

from tools.verify_semantic_configuration_provenance import NAMES, project, decode, attrs, sha
from tools.semantic_mount_review_sources import GATEWAY_SOURCES, GATEWAY_SOURCE_COMMIT

TRUST_NAMES = ('ca.crt', 'trust-bundle.pem', 'adapter/server.crt', 'adapter/server.key',
               'adapter/provider-receipt.key', 'southbound/server.crt', 'southbound/server.key',
               'southbound/provider-receipt.key')
SOURCE_NAMES = tuple(k for k in GATEWAY_SOURCES if k != 'tools/materialize_semantic_provider_tls.py')
class Blocked(ValueError): pass
def require(ok, reason='MOUNT_INPUT_REVIEW_UNPROVEN'):
    if not ok: raise Blocked(reason)

class Budget:
    def __init__(self, seconds=60):
        require(type(seconds) is int and 1 <= seconds <= 60)
        self.deadline = time.monotonic()+seconds
    def check(self): require(time.monotonic() < self.deadline, 'REVIEW_DEADLINE')
    def timeout(self):
        self.check(); return min(3, self.deadline-time.monotonic())

def read(path, uid, gid, mode, limit, budget):
    budget.check(); require(path.is_absolute() and '..' not in path.parts)
    for parent in path.parents:
        info=parent.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022)
    parent=path.parent.lstat();require(parent.st_gid == 0 and stat.S_IMODE(parent.st_mode) == 0o700)
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        before=os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_uid == uid and before.st_gid == gid
                and stat.S_IMODE(before.st_mode) == mode and before.st_nlink == 1 and 0 < before.st_size <= limit)
        raw=os.read(fd,limit+1);budget.check()
        require(len(raw) == before.st_size and attrs(before) == attrs(os.fstat(fd)) == attrs(path.lstat()))
        return raw,attrs(before)
    finally: os.close(fd)

def compiler():
    # Only reviewed, embedded public source is executed. Private JSON is data.
    # The original Lua file read is replaced by that same frozen Lua text.
    saved={k:v for k,v in sys.modules.items() if k == 'tools' or k.startswith('tools.')}
    package=types.ModuleType('tools');package.__path__=[];sys.modules['tools']=package
    order=('southbound_security','semantic_provider_boundary','semantic_provider_admission',
           'semantic_provider_relay','semantic_provider_adapter','materialize_semantic_provider',
           'materialize_semantic_provider_runtime','materialize_semantic_provider_tls')
    try:
        for name in order:
            key='tools.'+name;module=types.ModuleType(key);module.__file__='<ouf-reviewed-compiler>'
            sys.modules[key]=module;setattr(package,name,module)
            source=GATEWAY_SOURCES['tools/'+name+'.py']
            if name == 'materialize_semantic_provider':
                old="(Path(__file__).parent/'lua/admit_semantic_provider.lua').read_text()"
                require(source.count(old) == 1)
                module.FROZEN_LUA=GATEWAY_SOURCES['tools/lua/admit_semantic_provider.lua']
                source=source.replace(old,'FROZEN_LUA')
            exec(compile(source,'<ouf-reviewed-compiler>','exec'),module.__dict__)
        return package.materialize_semantic_provider_runtime.compile_plan, package.materialize_semantic_provider_tls.materialize_tls
    finally:
        for key in list(sys.modules):
            if key == 'tools' or key.startswith('tools.'):sys.modules.pop(key)
        sys.modules.update(saved)

class Crypto:
    def __init__(self, path, budget, public_scratch=Path('/tmp')):
        self.path,self.budget,self.public_scratch=path,budget,public_scratch
        info=public_scratch.lstat()
        require(public_scratch.is_absolute() and '..' not in public_scratch.parts
                and stat.S_ISDIR(info.st_mode) and info.st_uid == 0
                and (not info.st_mode & 0o022 or bool(info.st_mode & stat.S_ISVTX)))
        for parent in public_scratch.parents:
            info=parent.lstat()
            require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022)
        self.binary_hash=self.binary()
    def binary(self):
        self.budget.check();require(self.path.is_absolute() and '..' not in self.path.parts)
        for parent in self.path.parents:
            s=parent.lstat();require(stat.S_ISDIR(s.st_mode) and s.st_uid == 0 and not s.st_mode & 0o022)
        fd=os.open(self.path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        try:
            before=os.fstat(fd)
            require(stat.S_ISREG(before.st_mode) and before.st_uid == 0 and before.st_mode & 0o111
                    and not before.st_mode & 0o022 and 0 < before.st_size <= 64000000)
            h=hashlib.sha256();size=0
            while True:
                self.budget.check();raw=os.read(fd,65536)
                if not raw:break
                size+=len(raw);require(size <= 64000000);h.update(raw)
            require(size == before.st_size and attrs(before) == attrs(os.fstat(fd)) == attrs(self.path.lstat()))
            return h.hexdigest()
        finally:os.close(fd)
    def run(self, args, raw, fds=(), allow_failure=False):
        require(self.binary() == self.binary_hash)
        # stdout is public DER or a verification result; private key input is
        # passed only through stdin. stderr is discarded, never disclosed.
        with tempfile.TemporaryFile(dir=self.public_scratch) as output:
            child=subprocess.run([str(self.path),*args],input=raw,stdout=output,stderr=subprocess.DEVNULL,
                pass_fds=fds,timeout=self.budget.timeout(),env={'PATH':'/usr/bin:/bin','LC_ALL':'C','OPENSSL_CONF':'/dev/null'})
            output.seek(0);value=output.read(16385)
        require(len(value) <= 16384 and (allow_failure or child.returncode == 0),'CRYPTO_CHECK_UNPROVEN')
        require(self.binary() == self.binary_hash);return child.returncode,value
    def validate_pair(self, cert, key, ca, hostname):
        require(type(hostname) is str and len(hostname) <= 253
                and all(re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?',p) for p in hostname.split('.')))
        _,public=self.run(['x509','-pubkey','-noout'],cert)
        _,certificate_der=self.run(['pkey','-pubin','-outform','DER'],public)
        _,key_der=self.run(['pkey','-pubout','-outform','DER','-passin','pass:'],key)
        require(hmac.compare_digest(certificate_der,key_der),'TLS_KEY_PAIR_MISMATCH')
        # Only public CA bytes are materialized in a root-owned temporary
        # directory. Private keys and configuration never touch scratch files.
        with tempfile.TemporaryDirectory(prefix='ouf-public-ca-',dir=self.public_scratch) as directory:
            path=Path(directory)/'ca.pem'
            fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
            try:require(os.write(fd,ca) == len(ca))
            finally:os.close(fd)
            base=['verify','-no-CApath','-no-CAstore','-no-CAfile','-CAfile',str(path),
                  '-purpose','sslserver','-verify_hostname']
            self.run(base+[hostname],cert)
            rc,_=self.run(base+['ouf-negative-hostname.invalid'],cert,allow_failure=True)
            require(rc != 0,'WRONG_TLS_IDENTITY_NOT_DENIED')
            require(path.read_bytes() == ca,'CRYPTO_CHECK_UNPROVEN')


def review(raws, trust_raws, manifest_hash, installation, tls_root, trust_root, crypto):
    require(set(trust_raws) == set(TRUST_NAMES))
    previous=project(raws,manifest_hash,installation)
    values={k:decode(raw,end=k == 'apisix.yaml') for k,raw in raws.items()}
    tr,t,stage,binding,plan=(values[k] for k in ('trust','tls','stage','binding','plan'))
    source_hashes={k:sha(GATEWAY_SOURCES[k].encode()) for k in SOURCE_NAMES}
    require(stage.get('sourceHashes') == source_hashes,'STAGED_COMPILER_SOURCE_DRIFT')
    runtime_hashes={k:sha(trust_raws[k]) for k in TRUST_NAMES}
    require(t['intent'].get('runtimeTrustHashes') == runtime_hashes,'TLS_RUNTIME_TRUST_DRIFT')
    require(all(tr.get('artifactHashes',{}).get(k) == h for k,h in runtime_hashes.items()),'TRUST_ARTIFACT_HASH_DRIFT')
    require(all(b'PRIVATE KEY' not in trust_raws[k] for k in ('ca.crt','trust-bundle.pem','adapter/server.crt','southbound/server.crt')))
    require(trust_raws['trust-bundle.pem'].endswith(trust_raws['ca.crt']),'TRUST_BUNDLE_LOCAL_CA_MISSING')
    mac=trust_raws['adapter/provider-receipt.key']
    require(re.fullmatch(b'[0-9a-f]{64}',mac) and hmac.compare_digest(mac,trust_raws['southbound/provider-receipt.key']),
            'PURPOSE_MAC_PAIR_DRIFT')
    for role in ('adapter','southbound'):
        crypto.validate_pair(trust_raws[role+'/server.crt'],trust_raws[role+'/server.key'],trust_raws['ca.crt'],
                             binding['tlsIdentities'][role+'Hostname'])
    compile_plan,materialize_tls=compiler()
    require(compile_plan(copy.deepcopy(binding)) == plan,'INDEPENDENT_RUNTIME_PLAN_DRIFT')
    listener=t['intent']['listener']
    require(listener['hostname'] == binding['tlsIdentities']['southboundHostname'])
    bootstrap=materialize_tls(copy.deepcopy(binding['routes']),{'listenAddress':listener['address'],
        'listenPort':listener['port'],'serverHostname':listener['hostname'],'sslResourceId':listener['sslResourceId']},
        certificate_pem=trust_raws['southbound/server.crt'].decode('ascii'),
        private_key_pem=trust_raws['southbound/server.key'].decode('ascii'))
    regenerated={'adapter.json':json.dumps(binding['adapter'],sort_keys=True).encode()+b'\n',
        'config.yaml':json.dumps(bootstrap['runtimeConfiguration'],sort_keys=True).encode()+b'\n',
        'apisix.yaml':json.dumps(bootstrap['resources'],sort_keys=True).encode()+b'\n#END\n'}
    require(all(raws[k] == raw for k,raw in regenerated.items()),'INDEPENDENT_TLS_COMPILER_DRIFT')
    specs=values['manifest']['containers'];require(type(specs) is list and len(specs) == 2)
    expected={'adapter':{'adapter.json':str(tls_root/'adapter.json'),**{k:str(trust_root/k) for k in
        ('adapter/server.crt','adapter/server.key','adapter/provider-receipt.key','trust-bundle.pem')}},
        'southbound':{k:str(tls_root/k) for k in ('config.yaml','apisix.yaml')}}
    expected['southbound']['trust-bundle.pem']=str(trust_root/'trust-bundle.pem')
    destinations={'adapter/server.crt':binding['adapter']['tlsCertificateFile'],
        'adapter/server.key':binding['adapter']['tlsPrivateKeyFile'],
        'adapter/provider-receipt.key':binding['adapter']['receiptKeyFile'],
        'trust-bundle.pem':binding['adapter']['provider']['ca_file']}
    roles=set();mounts=[]
    for spec in specs:
        require(type(spec.get('readOnlyRoot')) is bool)
        role='adapter' if spec['readOnlyRoot'] else 'southbound';require(role not in roles);roles.add(role)
        rows=spec['mounts'];require(type(rows) is list and len(rows) == len(expected[role]))
        require({m['source'] for m in rows} == set(expected[role].values()) and len({m['target'] for m in rows}) == len(rows))
        for slot,source in expected[role].items():
            row=next(x for x in rows if x['source'] == source);target=row['target']
            require(row['readOnly'] is True and type(target) is str and Path(target).is_absolute() and '..' not in Path(target).parts)
            if slot in destinations:require(target == destinations[slot],'MOUNT_DESTINATION_BINDING_DRIFT')
            raw=raws[slot] if slot in regenerated else trust_raws[slot]
            mounts.append({'role':role,'slot':slot,'sourceBindingHash':sha(source.encode()),
                'destinationBindingHash':sha(target.encode()),'contentHash':sha(raw),'readOnly':True})
    return {'schema':'ouf.semantic-static-mount-input-review.v1','inputHashes':previous['inputHashes'],
        'trustArtifactHashes':runtime_hashes,'reviewedCompilerCommit':GATEWAY_SOURCE_COMMIT,
        'reviewedCompilerHashes':{k:sha(v.encode()) for k,v in GATEWAY_SOURCES.items()},
        'manifestMountCount':len(mounts),'manifestMountInputs':mounts,'manifestMountMappingConsistent':True,
        'independentCompilerReplay':True,'cryptographicKeyValidation':True,'serverPurposeAndHostnameValidated':True,
        'wrongHostnameDenied':True,'purposeMacPairConsistent':True,'separateTlsPrivateKeyFilesRead':2,
        'purposeMacFilesRead':2,'publicTrustFilesRead':4,'inlineTlsPrivateKeyFileRead':True,
        'caPrivateKeyRead':False,'privateMaterialSpooled':False,'publicCaTemporaryFilesUsed':True,'deploymentSigningKeysRead':False,'environmentRead':False,
        'certificateRevocationChecked':False,'imagePublisherProvenanceVerified':False,
        'currentTargetInspected':False,'fullOciAcceptanceProven':False,'generationObserved':False,
        'atomicSnapshotProven':False,'acceptanceGranted':False,'runtimeRegistered':False,'startAuthorized':False,
        'providerCalls':0,'signaturesIssued':0,'targetFilesWritten':0}

def verify(paths, metadata, pin, installation, tls_root, trust_root, crypto, budget, reader=read):
    require(set(paths) == set(metadata) == set(NAMES)|{'trust:'+k for k in TRUST_NAMES})
    first={k:reader(paths[k],*metadata[k],budget) for k in paths}
    result=review({k:first[k][0] for k in NAMES},{k:first['trust:'+k][0] for k in TRUST_NAMES},
                  pin,installation,tls_root,trust_root,crypto)
    require(first == {k:reader(paths[k],*metadata[k],budget) for k in paths},'INPUTS_CHANGED_DURING_REVIEW')
    result['opensslBinarySha256']=crypto.binary_hash;budget.check();return result

def main():
    try:
        p=argparse.ArgumentParser(description=__doc__)
        for k in ('manifest','launch','tls','trust','stage'):p.add_argument('--'+k+'-root',type=Path,required=True)
        p.add_argument('--openssl-path',type=Path,required=True)
        p.add_argument('--public-scratch-root',type=Path,required=True)
        for k in ('manifest-hash','installation'):p.add_argument('--'+k,required=True)
        for k in ('adapter-uid','adapter-gid','gateway-uid','gateway-gid'):p.add_argument('--'+k,type=int,required=True)
        a=p.parse_args();require(os.geteuid() == 0 and sys.flags.isolated and sys.dont_write_bytecode)
        require(all(type(v) is int and 0 <= v <= 2147483647 for v in (a.adapter_uid,a.adapter_gid,a.gateway_uid,a.gateway_gid)))
        budget=Budget();crypto=Crypto(a.openssl_path,budget,a.public_scratch_root)
        paths={'manifest':a.manifest_root/'stopped-manifest.json','launch':a.launch_root/'launch-input-receipt.json',
            'tls':a.tls_root/'tls-runtime-receipt.json','trust':a.trust_root/'trust-receipt.json','stage':a.stage_root/'stage-receipt.json',
            'binding':a.stage_root/'binding.json','plan':a.stage_root/'runtime-plan.json'}
        paths.update({k:a.tls_root/k for k in NAMES[7:]});paths.update({'trust:'+k:a.trust_root/k for k in TRUST_NAMES})
        meta={k:(0,0,0o600,131072) for k in paths}
        for k in ('adapter.json',):meta[k]=(a.adapter_uid,a.adapter_gid,0o600,131072)
        for k in ('config.yaml','apisix.yaml'):meta[k]=(a.gateway_uid,a.gateway_gid,0o600,131072)
        for k in TRUST_NAMES:
            role=k.split('/')[0]
            owner=(a.adapter_uid,a.adapter_gid) if role == 'adapter' else (a.gateway_uid,a.gateway_gid)
            meta['trust:'+k]=(*owner,0o600,65536) if '/' in k else (0,0,0o644,1048576)
        result=verify(paths,meta,a.manifest_hash,a.installation,a.tls_root,a.trust_root,crypto,budget)
        print('SEMANTIC_MOUNT_INPUTS='+json.dumps(result,sort_keys=True))
        print('SEMANTIC_MOUNT_INPUTS=PASS ACCEPTANCE_GRANTED=false START_AUTHORIZED=false');return 0
    except Exception as error:
        reason=str(error) if type(error) is Blocked and str(error) in {'REVIEW_DEADLINE','CRYPTO_CHECK_UNPROVEN',
            'TLS_KEY_PAIR_MISMATCH','WRONG_TLS_IDENTITY_NOT_DENIED','STAGED_COMPILER_SOURCE_DRIFT','TLS_RUNTIME_TRUST_DRIFT',
            'TRUST_ARTIFACT_HASH_DRIFT','TRUST_BUNDLE_LOCAL_CA_MISSING','PURPOSE_MAC_PAIR_DRIFT','INDEPENDENT_RUNTIME_PLAN_DRIFT',
            'INDEPENDENT_TLS_COMPILER_DRIFT','MOUNT_DESTINATION_BINDING_DRIFT','INPUTS_CHANGED_DURING_REVIEW'} else 'MOUNT_INPUT_REVIEW_UNPROVEN'
        print('SEMANTIC_MOUNT_INPUTS=BLOCKED REASON='+reason+' NO_SECRETS_PRINTED=true');return 1

if __name__ == '__main__':raise SystemExit(main())
