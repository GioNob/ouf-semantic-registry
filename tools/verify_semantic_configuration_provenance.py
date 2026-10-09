"""Verify sealed receipt/configuration consistency privately; grants no acceptance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

LIMIT = 131072
NAMES = ('manifest','launch','tls','trust','stage','binding','plan','adapter.json','config.yaml','apisix.yaml')
class Blocked(ValueError): pass
def require(ok):
    if not ok: raise Blocked('CONFIGURATION_PROVENANCE_UNPROVEN')
def sha(raw): return hashlib.sha256(raw).hexdigest()
def decode(raw, end=False):
    require(type(raw) is bytes and 0 < len(raw) <= LIMIT)
    if end:
        require(raw.endswith(b'\n#END\n')); raw=raw[:-6]
    def unique(items):
        out={}
        for key,value in items:
            require(key not in out);out[key]=value
        return out
    value=json.loads(raw,object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(Blocked()))
    require(type(value) is dict);return value
def attrs(s):
    return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
def read(path,uid=0,gid=0):
    require(path.is_absolute() and '..' not in path.parts)
    for parent in path.parents:
        s=parent.lstat()
        require(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and not s.st_mode & 0o022)
    s=path.parent.lstat();require(s.st_gid==0 and stat.S_IMODE(s.st_mode)==0o700)
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        s=os.fstat(fd)
        require(stat.S_ISREG(s.st_mode) and s.st_uid==uid and s.st_gid==gid
            and stat.S_IMODE(s.st_mode)==0o600 and s.st_nlink==1 and 0<s.st_size<=LIMIT)
        raw=os.read(fd,LIMIT+1)
        require(len(raw)==s.st_size and attrs(s)==attrs(os.fstat(fd))==attrs(path.lstat()))
        return raw,attrs(s)
    finally: os.close(fd)
def project(raws,manifest_hash,installation):
    require(set(raws)==set(NAMES) and sha(raws['manifest'])==manifest_hash)
    v={k:decode(raw,end=k=='apisix.yaml') for k,raw in raws.items()}
    m,l,t,tr,s,b,p=(v[k] for k in NAMES[:7])
    require(m['schema']=='ouf.semantic-provider-stopped-manifest.v1'
        and m['installation']==installation and m['startAuthorized'] is False)
    require(l['schema']=='ouf.semantic-provider-launch-inputs.v1' and m['launchReceiptHash']==sha(raws['launch']))
    for key,name in (('tlsReceiptHash','tls'),('trustReceiptHash','trust'),('bindingHash','binding')):
        require(l[key]==sha(raws[name]))
    require(t['intent']['trustReceiptHash']==sha(raws['trust']) and t['intent']['stageReceiptHash']==sha(raws['stage'])
        and s['bindingHash']==sha(raws['binding']) and s['planHash']==sha(raws['plan']))
    for receipt in (l,t,tr,s): require(receipt['notReleaseAcceptance'] is True)
    require(l['mountsInstalled'] is False and t['mountsInstalled'] is False and tr['mountsInstalled'] is False
        and s['runtimeFilesMounted'] is False and tr['verified'] is True)
    for receipt in (l,t): require(type(receipt['containersCreated']) is int and receipt['containersCreated']==0
        and type(receipt['providerCalls']) is int and receipt['providerCalls']==0)
    require(p['schema']=='ouf.semantic-provider-runtime-plan.v1' and p['installed'] is False
        and p['notReleaseAcceptance'] is True and p['providerCalls']==0)
    intent=tr['intent']
    require(t['intent']['gateway']==intent['gateway'] and t['intent']['adapterImage']==intent['adapterImage']
        and t['intent']['adapterUid']==intent['adapterUid'] and t['intent']['adapterGid']==intent['adapterGid']
        and b['adapter']['admission']['installation']==intent['installation']==installation
        and b['tlsIdentities']['adapterHostname']==intent['adapterHostname']
        and b['tlsIdentities']['southboundHostname']==intent['southboundHostname'])
    require(v['adapter.json']==b['adapter']==p['adapterConfiguration'])
    for name in NAMES[7:]:
        require(t['outputHashes'][name]==sha(raws[name]))
    for name in ('config.yaml','apisix.yaml'):
        require(l['privateArtifactHashes'][name]==sha(raws[name]))
    # Compare routes to the sealed plan. This is NOT independent recompilation.
    require(v['apisix.yaml']['routes']==p['southboundRoutes']['routes'])
    return {'schema':'ouf.semantic-configuration-provenance-readback.v1',
        'receiptChainConsistent':True,'sealedConfigurationBytesConsistent':True,
        'adapterBindingConsistent':True,'routesMatchSealedPlan':True,
        'inputHashes':{k:sha(raws[k]) for k in NAMES},'configurationFilesRead':3,
        'inlineTlsPrivateKeyFileRead':True,'separatePrivateKeyFilesRead':0,
        'independentCompilerReplay':False,'cryptographicKeyValidation':False,
        'imagePublisherProvenanceVerified':False,'currentTargetInspected':False,
        'atomicSnapshotProven':False,'acceptanceGranted':False,'environmentRead':False,
        'signaturesIssued':0,'providerCalls':0,'targetFilesWritten':0,
        'runtimeRegistered':False,'startAuthorized':False}
def verify(paths,owners,manifest_hash,installation,reader=read):
    require(set(paths)==set(NAMES) and set(owners)==set(NAMES))
    first={k:reader(paths[k],*owners[k]) for k in NAMES}
    result=project({k:first[k][0] for k in NAMES},manifest_hash,installation)
    intent=decode(first['trust'][0])['intent']
    require(owners['adapter.json']==(intent['adapterUid'],intent['adapterGid'])
        and owners['config.yaml']==owners['apisix.yaml']==(intent['gateway']['uid'],intent['gateway']['gid']))
    require(first=={k:reader(paths[k],*owners[k]) for k in NAMES})
    return result

def main():
    try:
        parser=argparse.ArgumentParser(description=__doc__)
        for name in ('manifest','launch','tls','trust','stage'):
            parser.add_argument('--'+name+'-root',type=Path,required=True)
        parser.add_argument('--manifest-hash',required=True)
        parser.add_argument('--installation',required=True)
        for name in ('adapter-uid','adapter-gid','gateway-uid','gateway-gid'):
            parser.add_argument('--'+name,type=int,required=True)
        a=parser.parse_args();require(os.geteuid()==0 and sys.flags.isolated and sys.dont_write_bytecode)
        paths={'manifest':a.manifest_root/'stopped-manifest.json','launch':a.launch_root/'launch-input-receipt.json',
            'tls':a.tls_root/'tls-runtime-receipt.json','trust':a.trust_root/'trust-receipt.json',
            'stage':a.stage_root/'stage-receipt.json','binding':a.stage_root/'binding.json','plan':a.stage_root/'runtime-plan.json'}
        paths.update({k:a.tls_root/k for k in NAMES[7:]})
        require(all(0<=v<=2147483647 for v in (a.adapter_uid,a.adapter_gid,a.gateway_uid,a.gateway_gid)))
        owners={k:(0,0) for k in NAMES};owners.update({'adapter.json':(a.adapter_uid,a.adapter_gid),
            'config.yaml':(a.gateway_uid,a.gateway_gid),'apisix.yaml':(a.gateway_uid,a.gateway_gid)})
        result=verify(paths,owners,a.manifest_hash,a.installation)
        print('SEMANTIC_CONFIGURATION_PROVENANCE='+json.dumps(result,sort_keys=True,allow_nan=False))
        print('SEMANTIC_CONFIGURATION_PROVENANCE=PASS ACCEPTANCE_GRANTED=false START_AUTHORIZED=false')
        return 0
    except Exception:
        print('SEMANTIC_CONFIGURATION_PROVENANCE=BLOCKED REASON=CONFIGURATION_PROVENANCE_UNPROVEN NO_SECRETS_PRINTED=true')
        return 1
if __name__=='__main__': raise SystemExit(main())
