"""Exact sealed launch Env/OIDC/MAC binding; no IAM grant, signature or start."""
import argparse
import hmac
import os
from pathlib import Path
import re
import stat
import sys
from tools.read_semantic_creation_configuration import Query,collect,environment,require,Blocked,private,decode,sha,encoded,attrs

def role_secret(path,uid,gid):
    require(path.is_absolute() and '..' not in path.parts)
    for p in path.parents:
        s=p.lstat();require(stat.S_ISDIR(s.st_mode) and s.st_uid==0 and not s.st_mode&0o022)
    s=path.parent.lstat();require(s.st_gid==0 and stat.S_IMODE(s.st_mode)==0o700)
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        before=os.fstat(fd);require(stat.S_ISREG(before.st_mode) and before.st_uid==uid and before.st_gid==gid
            and before.st_nlink==1 and stat.S_IMODE(before.st_mode)==0o600 and 16<=before.st_size<=1024)
        raw=os.read(fd,1025);require(len(raw)==before.st_size and attrs(before)==attrs(os.fstat(fd))==attrs(path.lstat()))
        require(re.fullmatch(rb'[!-~]{16,1024}',raw));return raw
    finally:os.close(fd)
def pairing(raws,launch_pin,uid,gid):
    require(sha(raws['launch'])==launch_pin)
    launch,binding,trust,credential=(decode(raws[k]) for k in ('launch','binding','trust','credential'))
    require(launch['schema']=='ouf.semantic-provider-launch-inputs.v1' and launch['notReleaseAcceptance'] is True
        and launch['containersCreated']==0 and launch['mountsInstalled'] is False and launch['providerCalls']==0
        and launch['bindingHash']==sha(raws['binding']) and launch['trustReceiptHash']==sha(raws['trust'])
        and launch['credentialReceiptHash']==sha(raws['credential']) and launch['environmentHash']==sha(raws['env']))
    intent=credential['intent'];routes=binding['routes']
    require(intent['schema']=='ouf.semantic-southbound-validator-credential.v1' and intent['purpose']=='OIDC_BEARER_TOKEN_VALIDATOR_ONLY'
        and intent['uid']==uid and intent['gid']==gid and uid>0 and gid>0
        and intent['trustReceiptHash']==sha(raws['trust']) and intent['tlsReceiptHash']==launch['tlsReceiptHash']
        and intent['clientProfile']['clientId']==routes['audience'] and intent['providerCalls']==0
        and all(intent[k] is False for k in ('clientCredentialsGrantRequested','iamConfigurationChanged','secretRotated'))
        and intent['notReleaseAcceptance'] is True and credential['credentialHash']==sha(raws['secret']))
    match=re.fullmatch(r'\$ENV://([A-Z][A-Z0-9_]{0,127})',routes['oidcSecretRef']);require(match)
    names=[match[1],routes['receiptKeyEnvironment']]
    require(names==launch['environmentNames'] and len(set(names))==2
        and all(re.fullmatch('[A-Z][A-Z0-9_]{0,127}',n) and n not in ('PATH','HOME','LD_PRELOAD','PYTHONPATH') for n in names))
    raw=raws['env'];require(type(raw) is bytes and 0<len(raw)<=4096 and raw.endswith(b'\n') and raw.count(b'\n')==2)
    lines=raw[:-1].decode('ascii').split('\n');values=[]
    for name,line in zip(names,lines):
        require(line.startswith(name+'='));values.append(line[len(name)+1:])
    oidc,mac=values;require(re.fullmatch('[!-~]{16,1024}',oidc) and re.fullmatch('[0-9a-f]{64}',mac))
    require(hmac.compare_digest(oidc.encode(),raws['secret']) and sha(mac.encode())==trust['artifactHashes']['southbound/provider-receipt.key'])
    require(trust['artifactHashes']['adapter/provider-receipt.key']==trust['artifactHashes']['southbound/provider-receipt.key'])
    return dict(zip(names,values))
def verify(raws,pins,installation,uid,gid,query,expected):
    extras=pairing(raws,pins['launch'],uid,gid);seen={}
    def capture(kind,identifier):
        value=query(kind,identifier);seen[kind,identifier]=value;return value
    result=collect([raws['manifest'],raws['creation']],[pins['manifest'],pins['creation']],installation,capture)
    rows=result['candidates'];require(len(expected)==2 and set(expected)=={'adapter','southbound'})
    for row in rows:
        require(all(row[k]==expected[row['role']][k] for k in ('configHash','hostConfigHash','environmentHash','fullInspectHash','imageInspectHash')))
    manifest,journal=decode(raws['manifest']),decode(raws['creation'])
    for spec in manifest['containers']:
        actual=environment(seen['container',journal['candidateIds'][spec['name']]]['Config'])
        base=environment(seen['image',spec['image']]['Config'])
        require(not set(extras)&set(base))
        if spec['readOnlyRoot']:
            require(spec['envFile'] is None and hmac.compare_digest(encoded(actual),encoded(base)))
        else:
            require(type(spec['envFile']) is str and spec['envFile']==pins['envPath'])
            require(hmac.compare_digest(encoded(actual),encoded({**base,**extras})))
    return {'schema':'ouf.semantic-sealed-environment-binding-review.v1','inputHashes':{k:sha(v) for k,v in raws.items()},
        'exactExtraEnvironmentEntryCount':2,'environmentNameBindingsHash':sha(encoded(sorted(extras))),
        'oidcCredentialPairConsistent':True,'purposeMacReceiptBindingConsistent':True,'containerEnvironmentMatchesSealedLaunch':True,
        'creationConfigurationUnchangedSinceSection45':True,'environmentFilesRead':True,'oidcPrivateCredentialFilesRead':1,
        'macSeparatePrivateKeyFilesRead':0,'tlsPrivateKeyFilesRead':0,'deploymentSigningKeysRead':False,'caPrivateKeyRead':False,
        'iamCurrentCredentialValidityProven':False,'providerCalls':0,'iamCalls':0,'signaturesIssued':0,'targetFilesWritten':0,
        'privateMaterialSpooled':False,'containersChanged':False,'fullOciAcceptanceProven':False,'generationObserved':False,
        'mountViewInspected':False,'atomicSnapshotProven':False,'allConfigurationFieldsSemanticallyAccepted':False,
        'acceptanceGranted':False,'runtimeRegistered':False,'startAuthorized':False}
def main():
    try:
        p=argparse.ArgumentParser(description=__doc__)
        for k in ('manifest-root','creation-root','launch-root','credential-root','runtime-root','trust-root','docker-path','public-scratch-root'):
            p.add_argument('--'+k,type=Path,required=True)
        for k in ('manifest-hash','creation-hash','launch-hash','installation','docker-hash','docker-host','expected-section45'):
            p.add_argument('--'+k,required=True)
        for k in ('credential-uid','credential-gid'):p.add_argument('--'+k,type=int,required=True)
        a=p.parse_args();require(os.geteuid()==0 and sys.flags.isolated and sys.dont_write_bytecode)
        paths={'manifest':a.manifest_root/'stopped-manifest.json','creation':a.creation_root/'creation-journal.json',
            'launch':a.launch_root/'launch-input-receipt.json','env':a.launch_root/'southbound.env',
            'credential':a.credential_root/'credential-receipt.json','secret':a.credential_root/'client-secret',
            'binding':a.runtime_root/'binding.json','trust':a.trust_root/'trust-receipt.json'}
        def readall():
            values={k:role_secret(path,a.credential_uid,a.credential_gid) if k=='secret' else private(path) for k,path in paths.items()}
            require(len(values['env'])<=4096);return values
        query=Query(a.docker_path,a.docker_hash,a.public_scratch_root,a.docker_host)
        raw=readall();result=verify(raw,{'manifest':a.manifest_hash,'creation':a.creation_hash,'launch':a.launch_hash,
            'envPath':str(paths['env'])},a.installation,a.credential_uid,a.credential_gid,query,decode(a.expected_section45.encode()))
        require(raw==readall());query.budget.remaining();result['dockerBinarySha256']=a.docker_hash
        print('SEMANTIC_ENVIRONMENT_BINDING='+encoded(result).decode())
        print('SEMANTIC_ENVIRONMENT_BINDING=PASS ACCEPTANCE_GRANTED=false START_AUTHORIZED=false');return 0
    except Exception:
        print('SEMANTIC_ENVIRONMENT_BINDING=BLOCKED REASON=SEALED_ENVIRONMENT_BINDING_UNPROVEN NO_SECRETS_PRINTED=true');return 1
if __name__=='__main__':raise SystemExit(main())
