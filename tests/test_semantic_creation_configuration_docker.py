"""Mandatory real Docker/isolated embedded CLI on two owned, never-started fixtures."""
import json,os,sys,subprocess,tempfile,unittest,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import read_semantic_creation_configuration as m
ROOT=Path(__file__).resolve().parents[1]
def embedded():
    helper=(ROOT/'tools/read_semantic_acceptance_metadata.py').read_text().split("if __name__ == '__main__':")[0]
    source=(ROOT/'tools/read_semantic_creation_configuration.py').read_text()
    return source.replace('from tools.read_semantic_acceptance_metadata import private,decode,sha,encoded,attrs',helper)
class Native(unittest.TestCase):
    def test_real_private_inspect_two_never_started_candidates_and_isolated_cli(self):
        self.assertEqual(os.geteuid(),0);docker=Path('/usr/bin/docker');host='unix:///var/run/docker.sock'
        token=uuid.uuid4().hex;tag='ouf-ci-creation-'+token;ids=[]
        def run(*args):return subprocess.check_output([str(docker),'--host',host,*map(str,args)],stderr=subprocess.DEVNULL,timeout=45).decode().strip()
        with tempfile.TemporaryDirectory(dir=os.environ['OUF_TEST_ROOT']) as d:
            root=Path(d);root.chmod(0o700);(root/'proof').write_text('CI_PRIVATE_VALUE');(root/'Dockerfile').write_text('FROM scratch\nCOPY proof /proof\nENV BASE=CI_PRIVATE_VALUE\nCMD ["never-start"]\n')
            try:
                run('build','--network=none','--pull=false','--tag',tag,root)
                image=run('image','inspect','--format','{{.Id}}',tag);specs=[]
                for i in range(2):specs.append({'name':tag+'-'+str(i),'image':image,'user':'0:0','command':[],
                    'envFile':None,'readOnlyRoot':i==0,'memoryBytes':192*1024*1024,'pidsLimit':32,'dnsServers':[],
                    'mounts':[{'source':str(root/'proof'),'target':'/proof','readOnly':True}]})
                from test_semantic_environment_binding import env_bytes,materialize,embedded as env_embedded
                (root/'southbound.env').write_bytes(env_bytes());(root/'southbound.env').chmod(0o600)
                specs[1]['envFile']=str(root/'southbound.env')
                manifest={'schema':'ouf.semantic-provider-stopped-manifest.v1','startAuthorized':False,'installation':'ci','containers':specs}
                raw=m.encoded(manifest);pin=m.sha(raw)
                for s in specs:
                    args=['create','--name',s['name'],'--user','0:0','--restart','no','--cap-drop','ALL',
                        '--memory',str(s['memoryBytes']),'--memory-swap',str(s['memoryBytes']),'--pids-limit','32','--no-healthcheck',
                        '--label','ouf.semantic.candidate.transaction='+token,'--label','ouf.semantic.candidate.manifest='+pin,
                        '--mount','type=bind,source='+str(root/'proof')+',target=/proof,readonly']
                    if s['readOnlyRoot']:args.append('--read-only')
                    if s['envFile']:args+=['--env-file',s['envFile']]
                    ids.append(run(*args,image))
                journal={'schema':'ouf.semantic-provider-stopped-create.v1','state':'CREATED_STOPPED','startAuthorized':False,
                    'manifestHash':pin,'transaction':token,'candidateIds':{s['name']:cid for s,cid in zip(specs,ids)}}
                rawj=m.encoded(journal)
                for name,content in [('stopped-manifest.json',raw),('creation-journal.json',rawj),('reader.py',embedded().encode())]:
                    p=root/name;p.write_bytes(content);p.chmod(0o600)
                args=['/usr/bin/python3','-I','-B',str(root/'reader.py'),'--manifest-root',str(root),'--creation-root',str(root),
                    '--manifest-hash',pin,'--creation-hash',m.sha(rawj),'--installation','ci','--docker-path',str(docker),
                    '--docker-hash',m.binary(docker,m.Budget()),'--docker-host',host,'--public-scratch-root',str(root)]
                before={p.name:p.read_bytes() for p in root.iterdir() if p.is_file()}
                p=subprocess.run(args,capture_output=True,timeout=65)
                self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.assertIn(b'SEMANTIC_CREATION_CONFIGURATION=PASS',p.stdout)
                self.assertNotIn(b'CI_PRIVATE_VALUE',p.stdout+p.stderr);self.assertNotIn(str(root).encode(),p.stdout+p.stderr)
                self.assertEqual(before,{p.name:p.read_bytes() for p in root.iterdir() if p.is_file()})
                for cid in ids:self.assertEqual(run('inspect','--format','{{.State.Status}}',cid),'created')
                expected={r['role']:r for r in json.loads(p.stdout.decode().splitlines()[0].split('=',1)[1])['candidates']}
                materialized=materialize(root,raw,rawj)
                cli=root/'env-reader.py';cli.write_text(env_embedded());cli.chmod(0o600)
                envargs=['/usr/bin/python3','-I','-B',str(cli)]
                for name in ('manifest','creation','launch','credential','runtime','trust'):envargs+=['--'+name+'-root',str(root)]
                envargs+=['--manifest-hash',pin,'--creation-hash',m.sha(rawj),'--launch-hash',m.sha(materialized['launch']),
                    '--installation','ci','--docker-path',str(docker),'--docker-hash',m.binary(docker,m.Budget()),
                    '--docker-host',host,'--public-scratch-root',str(root),'--credential-uid','636','--credential-gid','636',
                    '--expected-section45',m.encoded(expected).decode()]
                envbefore={path.name:path.read_bytes() for path in root.iterdir() if path.is_file()}
                envproc=subprocess.run(envargs,capture_output=True,timeout=65)
                self.assertEqual(envproc.returncode,0,envproc.stdout+envproc.stderr)
                self.assertIn(b'SEMANTIC_ENVIRONMENT_BINDING=PASS',envproc.stdout)
                for private_value in (materialized['secret'],str(root).encode(),env_bytes()):
                    self.assertNotIn(private_value,envproc.stdout+envproc.stderr)
                self.assertEqual(envbefore,{path.name:path.read_bytes() for path in root.iterdir() if path.is_file()})
                for cid in ids:self.assertEqual(run('inspect','--format','{{.State.Status}}',cid),'created')
                (root/'client-secret').write_bytes(b'CI_WRONG_SECRET_0123456789')
                envproc=subprocess.run(envargs,capture_output=True,timeout=65);self.assertEqual(envproc.returncode,1)
                self.assertIn(b'NO_SECRETS_PRINTED=true',envproc.stdout)
                self.assertNotIn(b'CI_WRONG_SECRET',envproc.stdout+envproc.stderr)
                run('update','--memory',str(193*1024*1024),'--memory-swap',str(193*1024*1024),ids[0])
                p=subprocess.run(args,capture_output=True,timeout=65);self.assertEqual(p.returncode,1)
                self.assertIn(b'NO_SECRETS_PRINTED=true',p.stdout);self.assertNotIn(b'CI_PRIVATE_VALUE',p.stdout+p.stderr)
            finally:
                for cid in ids:run('rm',cid)
                run('image','rm',tag)
if __name__=='__main__':unittest.main()
