import importlib.util,json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

path=Path(__file__).resolve().parents[1]/'scripts/r4a_semantic_southbound_host_inventory.py'
spec=importlib.util.spec_from_file_location('host_inventory',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class HostInventoryTest(unittest.TestCase):
    def test_nft_metadata_redacts_every_rule_expression_and_binding(self):
        report=module.nft_summary({'nftables':[{'chain':{'family':'inet','hook':'forward','policy':'drop','name':'private-chain','table':'private-table'}},{'rule':{'expr':[{'match':'private-address-or-token'}],'comment':'secret-comment'}}]})
        self.assertEqual(report['baseChainPolicyCounts'],{'forward:drop':1});self.assertEqual(report['ruleCount'],1)
        self.assertNotIn('private',json.dumps(report));self.assertNotIn('secret',json.dumps(report))
    def test_iptables_counts_only_selected_policies(self):
        report=module.iptables_summary(':FORWARD DROP [0:0]\n:DOCKER-USER - [0:0]\n-A private-chain -s private-address --comment secret\n')
        self.assertEqual(report,{'selectedChainPolicies':{'FORWARD':'DROP','DOCKER-USER':'-'},'filterRuleCount':1})
    def test_selected_commands_are_read_only_and_never_print_raw_failures(self):
        with patch.object(module.subprocess,'run',return_value=SimpleNamespace(returncode=1,stdout='secret',stderr='secret')) as run:
            with self.assertRaisesRegex(module.Blocked,'^READ_ONLY_COMMAND_FAILED$'):module.run_json(['nft','-j','list','ruleset'])
            self.assertEqual(run.call_args.args[0],['nft','-j','list','ruleset'])
    def test_runtime_custom_bindings_and_absent_firewalls_are_not_acceptance(self):
        args=SimpleNamespace(docker_path='/custom/docker',gateway_container='custom-gateway',nft_path=None,iptables_save_path=None)
        gateway={'Id':'selected-id','Image':'image','State':{'Running':True},'NetworkSettings':{'Networks':{'private-custom':{}}}}
        info={'ServerVersion':'28.5.0','SecurityOptions':['name=rootless']}
        with patch.object(module,'run_json',side_effect=[[gateway],info,[gateway]]) as run,patch.object(module.shutil,'which',return_value=None):report=module.inventory(args)
        self.assertTrue(report['docker']['rootlessObserved']);self.assertFalse(report['egressDefaultDenyProven']);self.assertFalse(report['fqdnPolicyProven'])
        self.assertEqual(run.call_args_list[0].args[0],['/custom/docker','inspect','custom-gateway'])
        self.assertFalse(report['tokenRequested']);self.assertEqual(report['providerCalls'],0)
    def test_unreadable_firewall_is_not_proven(self):
        args=SimpleNamespace(docker_path='docker',gateway_container='gateway',nft_path='/custom/nft',iptables_save_path='/custom/iptables-save')
        gateway={'Id':'id','State':{'Running':True}}
        with patch.object(module,'run_json',side_effect=[[gateway],{'ServerVersion':'28'},module.Blocked('READ_ONLY_COMMAND_FAILED'),[gateway]]),patch.object(module.subprocess,'run',return_value=SimpleNamespace(returncode=1,stdout='secret',stderr='secret')) as run:report=module.inventory(args)
        self.assertFalse(report['firewall']['nft']['readable']);self.assertFalse(report['firewall']['iptables']['readable']);self.assertNotIn('secret',json.dumps(report))
        self.assertEqual(run.call_args.args[0],['/custom/iptables-save','-t','filter'])
    def test_runtime_drift_and_invalid_firewall_json_block(self):
        args=SimpleNamespace(docker_path='docker',gateway_container='gateway',nft_path=None,iptables_save_path=None)
        with patch.object(module,'inspect_gateway',side_effect=[{'id':'first'},{'id':'changed'}]),patch.object(module,'run_json',return_value={'ServerVersion':'28'}),patch.object(module.shutil,'which',return_value=None):
            with self.assertRaisesRegex(module.Blocked,'GATEWAY_CHANGED_DURING_INVENTORY'):module.inventory(args)
        with self.assertRaisesRegex(module.Blocked,'NFT_JSON_INVALID'):module.nft_summary({})

if __name__=='__main__':unittest.main()
