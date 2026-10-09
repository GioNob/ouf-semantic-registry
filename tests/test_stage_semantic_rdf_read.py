import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import r4a_stage_semantic_rdf_read as script


class StageTest(unittest.TestCase):
    def scenario(self,drift=None,build=0):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);previous=base/'previous';previous.mkdir()
            (previous/'runtime-snapshot.json').write_text(json.dumps({'config':{'gateway':{'container':'ouf-apisix'}}}))
            root=base/'stage';rows={n:{'Id':n+'-id','Image':'old','State':{'Running':True,'StartedAt':'same'},
                'Config':{'Labels':{'org.opencontainers.image.revision':script.LIVE_PIN}},'HostConfig':{},'Mounts':[]} for n in script.NAMES}
            image={'Id':'new-image','Config':{'Labels':{'org.opencontainers.image.revision':script.PIN}}}
            calls={};route_calls=[]
            def inspect(name):
                if name.startswith('ouf-semantic:rdf-read-'):return image
                calls[name]=calls.get(name,0)+1
                row=copy.deepcopy(rows[name])
                if drift==name and calls[name]>1:row['Image']='unexpected'
                return row
            def routes(*args):
                route_calls.append(1)
                return [{'id':'route','uri':'changed' if drift=='routes' and len(route_calls)>1 else 'original'}]
            output=io.StringIO()
            with patch.object(script,'ROOT',base),patch.object(script.os,'geteuid',return_value=0),\
                patch.object(script.prep,'private'),patch.object(script.prep,'launch_guard') as guard,\
                patch.object(script.stage,'inspect',side_effect=inspect),patch.object(script.stage,'routes',side_effect=routes),\
                patch.object(script.stage,'run',side_effect=lambda args,*a:script.PIN if 'rev-parse' in args else ''),\
                patch.object(script.subprocess,'run',return_value=SimpleNamespace(returncode=build)) as runner,\
                contextlib.redirect_stdout(output):
                error=None
                try:script.main(SimpleNamespace(stage_root=root,consultation_stage_root=previous))
                except RuntimeError as exc:error=str(exc)
                receipt=json.loads((root/'image-receipt.json').read_text()) if (root/'image-receipt.json').exists() else None
            return error,receipt,output.getvalue(),runner.call_args,guard.call_count
    def test_stages_only_semantic_and_retains_all_live_owners(self):
        error,receipt,output,call,guards=self.scenario()
        self.assertIsNone(error);self.assertTrue(receipt['noContainersCreated'])
        self.assertEqual(receipt['commit'],script.PIN)
        self.assertEqual(call.args[0][:2],['docker','build']);self.assertEqual(guards,1)
        self.assertIn('NO_SWITCH=true',output);self.assertNotIn('SECRET=',output)
    def test_mcp_drift_blocks_receipt(self):
        error,receipt,*_=self.scenario('ouf-mcp')
        self.assertEqual(error,'LIVE_CHANGED_DURING_STAGE');self.assertIsNone(receipt)
    def test_semantic_drift_blocks_receipt(self):
        error,receipt,*_=self.scenario('ouf-semantic')
        self.assertEqual(error,'LIVE_CHANGED_DURING_STAGE');self.assertIsNone(receipt)
    def test_routes_drift_blocks_receipt(self):
        error,receipt,*_=self.scenario('routes')
        self.assertEqual(error,'ROUTES_CHANGED_DURING_STAGE');self.assertIsNone(receipt)
    def test_build_failure_keeps_details_in_private_log(self):
        error,receipt,output,*_=self.scenario(build=1)
        self.assertEqual(error,'BUILD_FAILED_PRIVATE_LOG');self.assertIsNone(receipt)
        self.assertNotIn('STAGE=PASS',output)

if __name__=='__main__':unittest.main()
