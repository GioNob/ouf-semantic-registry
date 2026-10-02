import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('stage',Path(__file__).resolve().parents[1]/'scripts/r4a_stage_semantic_consultation.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class StageTest(unittest.TestCase):
    def config(self,root):
        return {'stageRoot':str(root),'images':[{'role':r,'repository':'https://github.com/GioNob/ouf-'+r,
                'commit':'b'*40,'container':r,'liveRevision':'a'*40} for r in ('semantic','mcp')],
                'gateway':{'container':'gateway','configDestination':'/conf/config.yaml','adminOrigin':'http://127.0.0.1:9180'}}
    def row(self,name):
        return {'Id':name,'Image':'old-image','State':{'Running':True,'StartedAt':'now'},
                'Config':{'Labels':{'org.opencontainers.image.revision':'a'*40},'Env':['PASSWORD=never-print']},
                'HostConfig':{'Privileged':False},'Mounts':[]}
    def test_builds_two_images_and_preserves_live_with_private_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'stage';cfg=self.config(root);calls=[]
            def inspect(name):
                if ':consultation-' in name:return {'Id':'image-'+name,'Config':{'Labels':{'org.opencontainers.image.revision':'b'*40}}}
                return self.row(name)
            def run(argv,*args,**kw):
                calls.append(argv)
                return 'b'*40 if 'rev-parse' in argv else ''
            with patch.object(m.os,'geteuid',return_value=0),patch.object(m,'inspect',side_effect=inspect),patch.object(m,'routes',return_value=[]),patch.object(m,'run',side_effect=run),patch.object(m.subprocess,'run') as build:
                build.return_value.returncode=0;out=io.StringIO()
                with contextlib.redirect_stdout(out):m.main(cfg)
            self.assertNotIn('never-print',out.getvalue())
            self.assertEqual(build.call_count,2)
            self.assertTrue(json.loads((root/'image-receipt.json').read_text())['noContainersCreated'])
            self.assertEqual((root/'runtime-snapshot.json').stat().st_mode&0o777,0o600)
            self.assertFalse(any(any(x in command for x in ('start','stop','rename','create','PUT')) for command in calls))
            with self.assertRaises(FileExistsError):m.main(cfg)
    def test_live_pin_drift_prevents_build(self):
        with tempfile.TemporaryDirectory() as d:
            cfg=self.config(Path(d)/'stage');cfg['images'][0]['liveRevision']='c'*40
            with patch.object(m.os,'geteuid',return_value=0),patch.object(m,'inspect',side_effect=self.row),patch.object(m.subprocess,'run') as build:
                with self.assertRaisesRegex(RuntimeError,'LIVE_DRIFT'):m.main(cfg)
                build.assert_not_called()
    def test_rejects_remote_admin_and_unpinned_repository(self):
        cfg=self.config(Path('/explicit'))
        cfg['gateway']['adminOrigin']='http://remote:9180'
        with self.assertRaisesRegex(RuntimeError,'ADMIN_ORIGIN_INVALID'):m.validate(cfg)
        cfg=self.config(Path('/explicit'));cfg['images'][0]['commit']='main'
        with self.assertRaisesRegex(RuntimeError,'PIN_INVALID'):m.validate(cfg)


if __name__=='__main__':unittest.main()
