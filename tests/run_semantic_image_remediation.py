"""CI-only compatibility experiment; public owned fixtures, never target deployment."""
import argparse,json,os,re,subprocess,sys
from pathlib import Path

CANDIDATES={'alpine-ubuntu':('python:3.13-alpine','apache/apisix:3.18.0-ubuntu'),
            'slim-debian':('python:3.13-slim','apache/apisix:3.18.0-debian')}
def run(args,**kwargs):return subprocess.run(args,check=kwargs.pop('check',True),timeout=kwargs.pop('timeout',240),**kwargs)
def inspect(reference):
    return json.loads(subprocess.check_output(['docker','image','inspect',reference],text=True,timeout=20))[0]
def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',choices=CANDIDATES,required=True);p.add_argument('--gateway',type=Path,required=True)
    a=p.parse_args();gateway=a.gateway.resolve();semantic=Path(__file__).resolve().parents[1]
    images={};locks={}
    for role,tag in zip(('adapter','southbound'),CANDIDATES[a.candidate]):
        run(['docker','pull','--platform=linux/amd64',tag],timeout=180)
        info=inspect(tag);assert info['Architecture']=='amd64' and info['Os']=='linux'
        prefix='python@sha256:' if role=='adapter' else 'apache/apisix@sha256:'
        digests=[d for d in info['RepoDigests'] if d.startswith(prefix) and re.fullmatch(r'.+@sha256:[0-9a-f]{64}',d)]
        assert len(digests)==1;images[role]=digests[0]
        locks[role]={'discoveryTag':tag,'resolvedDigest':digests[0],'pulledImageId':info['Id']}
    out=semantic/'generated'/a.candidate;out.mkdir(parents=True,exist_ok=False)
    (out/'inputs.json').write_text(json.dumps(locks,sort_keys=True,indent=2)+'\n')
    env=dict(os.environ,OUF_PROVIDER_CONTAINER_TEST='1',OUF_SEMANTIC_PROVIDER_APISIX_TEST='1',
        OUF_PROVIDER_TEST_BASE_IMAGE=images['adapter'],OUF_PROVIDER_TEST_APISIX_IMAGE=images['southbound'])
    for test in ('tests.test_semantic_provider_container','tests.test_semantic_provider_apisix_live'):
        run([sys.executable,'-B','-m','unittest',test],cwd=gateway,env=env,timeout=420)
    adapter=json.loads((gateway/'generated/semantic-provider-package-proof.json').read_text())
    southbound=json.loads((gateway/'generated/semantic-southbound-package-proof.json').read_text())
    assert adapter['baseImage']==images['adapter'] and southbound['requestedImage']==images['southbound']
    assert adapter['tlsAdmissionProven'] is True and southbound['tlsOidcNegativeBoundariesProven'] is True
    (out/'compatibility.json').write_text(json.dumps({'adapter':adapter,'southbound':southbound},indent=2,sort_keys=True)+'\n')
    result=run(['sudo','/usr/bin/python3','-B',str(semantic/'tests/scan_semantic_image_remediation.py'),
        '--adapter',adapter['imageId'],'--southbound',southbound['imageId']],capture_output=True,text=True,timeout=900,check=False)
    if result.returncode:
        print(result.stderr[-12000:],file=sys.stderr)
        raise RuntimeError('CI_OFFLINE_SCAN_FAILED')
    receipt=json.loads(result.stdout);assert receipt['schema']=='ouf.semantic-image-remediation-experiment.v1'
    receipt.update(candidate=a.candidate,inputs=locks,gatewayCodeCommit=adapter['sourceRevision'],compatibilityProven=True)
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print('SEMANTIC_IMAGE_REMEDIATION_EXPERIMENT='+json.dumps(receipt,sort_keys=True))
    print('EXPERIMENT_COMPLETED=true THRESHOLD_MET='+str(receipt['allScannerSeverityThresholdsMet']).lower()+' TARGET_ACCEPTANCE=false')
if __name__=='__main__':main()
