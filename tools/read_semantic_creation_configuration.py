"""Fixed never-started candidate Config/HostConfig review; no OCI acceptance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import stat
import subprocess
import sys
import tempfile
import time
from tools.read_semantic_acceptance_metadata import private,decode,sha,encoded,attrs

class Blocked(ValueError):pass
def require(ok):
    if not ok:raise Blocked('CREATION_CONFIGURATION_UNPROVEN')
class Budget:
    def __init__(self):self.deadline=time.monotonic()+60
    def remaining(self):
        value=self.deadline-time.monotonic();require(value>0);return min(value,10)
def binary(path,budget):
    require(path.is_absolute() and '..' not in path.parts)
    for p in path.parents:
        s=p.lstat();require(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and not s.st_mode&0o022)
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        before=os.fstat(fd);require(stat.S_ISREG(before.st_mode) and before.st_uid==0
            and before.st_mode&0o111 and not before.st_mode&0o022 and 0<before.st_size<=64000000)
        h=hashlib.sha256();size=0
        while True:
            budget.remaining();raw=os.read(fd,65536)
            if not raw:break
            size+=len(raw);require(size<=64000000);h.update(raw)
        require(size==before.st_size and attrs(before)==attrs(os.fstat(fd))==attrs(path.lstat()))
        return h.hexdigest()
    finally:os.close(fd)
class Query:
    def __init__(self,path,pin,scratch,host):
        self.budget=Budget();self.path=path;self.pin=pin;self.scratch=scratch;self.host=host
        require(re.fullmatch('[0-9a-f]{64}',pin) and host.startswith('unix:///') and '..' not in Path(host[7:]).parts)
        info=scratch.lstat();require(scratch.is_absolute() and '..' not in scratch.parts and stat.S_ISDIR(info.st_mode) and info.st_uid==0
            and (not info.st_mode&0o022 or info.st_mode&stat.S_ISVTX))
        for p in scratch.parents:
            info=p.lstat();require(stat.S_ISDIR(info.st_mode) and info.st_uid==0 and not info.st_mode&0o022)
        require(binary(path,self.budget)==pin)
    def __call__(self,kind,identifier):
        require(kind in ('container','image') and re.fullmatch('[0-9a-f]{64}' if kind=='container' else 'sha256:[0-9a-f]{64}',identifier))
        require(binary(self.path,self.budget)==self.pin)
        # Empty CLI directory only. Full private inspect stdout stays in memory.
        with tempfile.TemporaryDirectory(prefix='ouf-empty-docker-',dir=self.scratch) as config:
            p=subprocess.Popen([str(self.path),'--config',config,'--host',self.host,'inspect','--type',kind,
                '--format','{{json .}}',identifier],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                env={'PATH':'/usr/bin:/bin','LC_ALL':'C'})
            try:
                raw=bytearray();deadline=time.monotonic()+self.budget.remaining()
                with selectors.DefaultSelector() as sel:
                    sel.register(p.stdout,selectors.EVENT_READ)
                    while True:
                        left=min(deadline-time.monotonic(),self.budget.remaining());require(left>0)
                        require(sel.select(left))
                        part=os.read(p.stdout.fileno(),65536)
                        if not part:break
                        raw.extend(part);require(len(raw)<=131072)
                require(p.wait(timeout=max(0.001,deadline-time.monotonic()))==0)
            finally:
                if p.poll() is None:p.kill();p.wait()
                p.stdout.close()
        require(binary(self.path,self.budget)==self.pin);return decode(bytes(raw))
def environment(cfg):
    rows=cfg.get('Env') or [];require(type(rows) is list and len(rows)<=256);out={}
    for item in rows:
        require(type(item) is str and '=' in item);name,value=item.split('=',1)
        require(re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',name) and name not in out and len(item)<=16384);out[name]=value
    return out
def review(manifest,journal,query):
    require(manifest['schema']=='ouf.semantic-provider-stopped-manifest.v1' and manifest['startAuthorized'] is False
        and journal['schema']=='ouf.semantic-provider-stopped-create.v1' and journal['state']=='CREATED_STOPPED'
        and journal['startAuthorized'] is False)
    specs=manifest['containers'];ids=journal['candidateIds'];require(type(specs) is list and len(specs)==len(ids)==2
        and set(ids)=={s['name'] for s in specs} and len(set(ids.values()))==2)
    rows=[];captured=[]
    for spec in specs:
        cid=ids[spec['name']];row=query('container',cid);image=query('image',spec['image']);captured.extend((row,image))
        require(row['Id']==cid and row['Image']==image['Id']==spec['image'] and row['Name']=='/'+spec['name'])
        state=row['State'];require(state['Status']=='created' and state['Running'] is False and state['Restarting'] is False
            and state['Pid']==0 and state['StartedAt'].startswith('0001-01-01T') and row['RestartCount']==0)
        cfg,base,host=row['Config'],image['Config'],row['HostConfig']
        labels=cfg.get('Labels') or {}
        require(labels.get('ouf.semantic.candidate.transaction')==journal['transaction']
            and labels.get('ouf.semantic.candidate.manifest')==journal['manifestHash'])
        require(cfg['User']==spec['user'] and cfg.get('Entrypoint')==base.get('Entrypoint')
            and cfg.get('Cmd')==(spec['command'] or base.get('Cmd')) and cfg.get('WorkingDir')==base.get('WorkingDir')
            and not base.get('Volumes') and cfg['Healthcheck']['Test']==['NONE'])
        require(host['Privileged'] is False and host['ReadonlyRootfs'] is spec['readOnlyRoot']
            and host['RestartPolicy']['Name']=='no' and set(host['CapDrop'] or [])=={'ALL'}
            and not any(host.get(k) for k in ('CapAdd','Devices','DeviceRequests','PortBindings'))
            and host['Memory']==host['MemorySwap']==spec['memoryBytes'] and host['PidsLimit']==spec['pidsLimit']
            and host['Dns']==spec['dnsServers'])
        expected={(m['source'],m['target']) for m in spec['mounts']};mounts=row['Mounts']
        require(len(expected)==len(mounts)==len(spec['mounts']) and expected=={(m['Source'],m['Destination']) for m in mounts}
            and all(m['readOnly'] is True for m in spec['mounts'])
            and all(m['Type']=='bind' and m['RW'] is False and m['Propagation']=='rprivate' for m in mounts))
        env,baseenv=environment(cfg),environment(base)
        require(all(env.get(k)==v for k,v in baseenv.items()) and (spec.get('envFile') or env==baseenv))
        # Complete objects are sealed, including unclassified or future fields.
        # Their hashes do not confer semantic acceptance of those fields.
        rows.append({'role':'adapter' if spec['readOnlyRoot'] else 'southbound','containerIdHash':sha(cid.encode()),
            'imageId':image['Id'],'fullInspectHash':sha(encoded(row)),'imageInspectHash':sha(encoded(image)),
            'configHash':sha(encoded(cfg)),'hostConfigHash':sha(encoded(host)),
            'environmentHash':sha(encoded(env)),'imageEnvironmentHash':sha(encoded(baseenv)),
            'environmentEntryCount':len(env),'additionalEnvironmentEntryCount':len(set(env)-set(baseenv)),
            'packagedStartupMatches':True,'declaredHostRestrictionsMatch':True,'manifestMountBindingsMatch':True,
            'allConfigurationFieldsSemanticallyAccepted':False})
    return sorted(rows,key=lambda r:r['role']),captured
def collect(raws,pins,installation,query):
    require([sha(raw) for raw in raws]==pins);manifest,journal=map(decode,raws)
    require(manifest['installation']==installation and journal['manifestHash']==pins[0])
    rows,first=review(manifest,journal,query);other,second=review(manifest,journal,query)
    require(first==second and rows==other)
    return {'schema':'ouf.semantic-creation-configuration-readback.v1','inputHashes':pins,'candidates':rows,
        'environmentRead':True,'environmentFilesRead':False,'fullInspectRead':True,'currentTargetInspected':True,
        'stableAcrossReads':True,'atomicSnapshotProven':False,'fullOciAcceptanceProven':False,'generationObserved':False,
        'mountViewInspected':False,'privateKeysRead':0,'privateMaterialSpooled':False,'providerCalls':0,
        'signaturesIssued':0,'targetFilesWritten':0,'containersChanged':False,'acceptanceGranted':False,
        'runtimeRegistered':False,'startAuthorized':False}
def main():
    try:
        p=argparse.ArgumentParser(description=__doc__)
        for k in ('manifest-root','creation-root','docker-path','public-scratch-root'):p.add_argument('--'+k,type=Path,required=True)
        for k in ('manifest-hash','creation-hash','installation','docker-hash','docker-host'):p.add_argument('--'+k,required=True)
        a=p.parse_args();require(os.geteuid()==0 and sys.flags.isolated and sys.dont_write_bytecode)
        paths=[a.manifest_root/'stopped-manifest.json',a.creation_root/'creation-journal.json']
        raw=[private(x) for x in paths];query=Query(a.docker_path,a.docker_hash,a.public_scratch_root,a.docker_host)
        result=collect(raw,[a.manifest_hash,a.creation_hash],a.installation,query);require(raw==[private(x) for x in paths])
        result['dockerBinarySha256']=a.docker_hash
        print('SEMANTIC_CREATION_CONFIGURATION='+encoded(result).decode())
        print('SEMANTIC_CREATION_CONFIGURATION=PASS ACCEPTANCE_GRANTED=false START_AUTHORIZED=false');return 0
    except Exception:
        print('SEMANTIC_CREATION_CONFIGURATION=BLOCKED REASON=CREATION_CONFIGURATION_UNPROVEN NO_SECRETS_PRINTED=true');return 1
if __name__=='__main__':raise SystemExit(main())
