import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import review_semantic_oci_policy as m

def fixture():
    spec={'user':'10006:10006','readOnlyRoot':True,'memoryBytes':201326592,'pidsLimit':32,
          'mounts':[{'source':'/CI_PRIVATE_SOURCE','target':'/proof','readOnly':True}]}
    startup={'uid':10006,'gid':10006,'umask':None,'cwd':'/','args':['/bin/ci-never-start'],
             'env':['PATH=/bin','CI_PRIVATE_SECRET=CI_PRIVATE_VALUE']}
    doc={'ociVersion':'1.2.1','process':{'terminal':False,'user':{'uid':10006,'gid':10006},
          'args':list(startup['args']),'cwd':'/','env':list(startup['env']),'noNewPrivileges':True,
          'capabilities':{k:[] for k in ('bounding','effective','inheritable','permitted','ambient')}},
         'root':{'path':'/CI_PRIVATE_ROOTFS','readonly':True},
         'mounts':[{'destination':'/proof','type':'bind','source':'/CI_PRIVATE_SOURCE','options':['rbind','rprivate','ro']}],
         'linux':{'namespaces':[{'type':k} for k in ('mount','pid','ipc','uts','network','cgroup')],
                  'maskedPaths':['/proc/kcore'],'readonlyPaths':['/proc/sys'],
                  'resources':{'memory':{'limit':spec['memoryBytes'],'swap':spec['memoryBytes']},'pids':{'limit':32},
                               'devices':[{'allow':False,'access':'rwm'}]},
                  'seccomp':{'defaultAction':'SCMP_ACT_ERRNO','defaultErrnoRet':1,'architectures':['SCMP_ARCH_X86_64'],
                             'syscalls':[{'names':['read'],'action':'SCMP_ACT_ALLOW','args':[
                                 {'index':0,'value':0,'op':'SCMP_CMP_EQ'}]}]}}}
    return doc,copy.deepcopy(doc),spec,startup,{},m.schema_from_source_closure()

class Policy(unittest.TestCase):
    def test_typed_complete_review_returns_unsigned_redacted_facts_only(self):
        result=m.configured_profile(*fixture());self.assertTrue(result['configuredPolicyConforms'])
        for k in ('policyAuthenticationProven','kernelEnforcementObserved','mountViewInspected','generationObserved',
                  'rootfsSealProven','completeCreationAccepted','acceptanceGranted','startAuthorized'):
            self.assertFalse(result[k])
        raw=json.dumps(result)
        self.assertNotIn('CI_PRIVATE',raw);self.assertEqual(result['signaturesIssued'],0)

    def test_unknown_fields_denied_at_every_present_struct_depth_even_matching_policy(self):
        locations=[[],['root'],['process'],['process','user'],['process','capabilities'],['linux'],
            ['linux','namespaces',0],['linux','resources'],['linux','resources','memory'],['linux','resources','pids'],
            ['linux','resources','devices',0],['linux','seccomp'],['linux','seccomp','syscalls',0],
            ['linux','seccomp','syscalls',0,'args',0],['mounts',0]]
        for location in locations:
            inputs=list(fixture());target=inputs[0]
            for key in location:target=target[key]
            target['CI_PRIVATE_UNKNOWN_NAME']='CI_PRIVATE_UNKNOWN_VALUE';inputs[1]=copy.deepcopy(inputs[0])
            with self.subTest(location=location),self.assertRaises(m.Denied) as e:m.configured_profile(*inputs)
            self.assertNotIn('CI_PRIVATE',str(e.exception))

    def test_wrong_types_integer_ranges_and_unknown_enum_denied(self):
        changes=[(['process','user','uid'],False),(['process','user','gid'],-1),
            (['process','user','uid'],2**32),(['linux','resources','pids','limit'],True),
            (['process','noNewPrivileges'],1),(['linux','namespaces',0,'type'],'new-private-namespace'),
            (['linux','seccomp','defaultAction'],'SCMP_ACT_UNKNOWN'),(['root','readonly'],1)]
        for location,value in changes:
            inputs=list(fixture());target=inputs[0]
            for key in location[:-1]:target=target[key]
            target[location[-1]]=value;inputs[1]=copy.deepcopy(inputs[0])
            with self.subTest(location=location),self.assertRaises(m.Denied):m.configured_profile(*inputs)

    def test_exact_policy_drift_including_annotation_cannot_hide_in_selected_fields(self):
        inputs=list(fixture());inputs[0]['annotations']={'CI_PRIVATE_ANNOTATION':'CI_PRIVATE_VALUE'}
        with self.assertRaisesRegex(m.Denied,'OCI_EXACT_POLICY_DRIFT'):m.configured_profile(*inputs)

    def test_docker_primary_gid_is_not_an_extra_group_grant(self):
        inputs=list(fixture());inputs[0]['process']['user']['additionalGids']=[10006];inputs[1]=copy.deepcopy(inputs[0])
        self.assertTrue(m.configured_profile(*inputs)['configuredPolicyConforms'])
        for groups in ([10006,10006],[10006,0],[10007]):
            inputs[0]['process']['user']['additionalGids']=groups;inputs[1]=copy.deepcopy(inputs[0])
            with self.assertRaises(m.Denied):m.configured_profile(*inputs)

    def test_matching_oci_checksum_cannot_override_security_and_compiled_startup(self):
        changes=[(['process','noNewPrivileges'],False),(['process','terminal'],True),
            (['process','user','uid'],0),(['process','user','additionalGids'],[0]),
            (['process','capabilities','bounding'],['CAP_SYS_ADMIN']),(['process','args'],['/bin/evil']),
            (['process','env'],['PATH=/bin','CI_PRIVATE_SECRET=evil']),(['process','apparmorProfile'],'unconfined'),
            (['linux','seccomp','defaultAction'],'SCMP_ACT_ALLOW'),(['linux','maskedPaths'],[]),
            (['linux','readonlyPaths'],[]),(['linux','resources','memory','swap'],-1),
            (['linux','resources','pids','limit'],-1),(['root','readonly'],False)]
        for location,value in changes:
            inputs=list(fixture());target=inputs[0]
            for key in location[:-1]:target=target[key]
            target[location[-1]]=value;inputs[1]=copy.deepcopy(inputs[0])
            with self.subTest(location=location),self.assertRaises(m.Denied):m.configured_profile(*inputs)

    def test_shared_duplicate_namespaces_and_uid_host_mapping_denied(self):
        for kind in ('host','duplicate','missing','user'):
            inputs=list(fixture())
            if kind=='host':inputs[0]['linux']['namespaces'][0]['path']='/proc/1/ns/mnt'
            elif kind=='duplicate':inputs[0]['linux']['namespaces'].append({'type':'pid'})
            elif kind=='missing':inputs[0]['linux']['namespaces'].pop()
            else:inputs[0]['linux']['uidMappings']=[{'containerID':0,'hostID':0,'size':65536}]
            inputs[1]=copy.deepcopy(inputs[0])
            with self.subTest(kind=kind),self.assertRaises(m.Denied):m.configured_profile(*inputs)

    def test_optional_private_time_namespace_never_allows_join_or_offsets(self):
        inputs=list(fixture());inputs[0]['linux']['namespaces'].append({'type':'time'})
        inputs[1]=copy.deepcopy(inputs[0])
        self.assertTrue(m.configured_profile(*inputs)['configuredPolicyConforms'])
        for kind in ('join','offset','duplicate'):
            altered=copy.deepcopy(inputs)
            if kind=='join':altered[0]['linux']['namespaces'][-1]['path']='/proc/1/ns/time'
            elif kind=='offset':altered[0]['linux']['timeOffsets']={'monotonic':{'secs':1,'nanosecs':0}}
            else:altered[0]['linux']['namespaces'].append({'type':'time'})
            altered[1]=copy.deepcopy(altered[0])
            with self.subTest(kind=kind),self.assertRaises(m.Denied):m.configured_profile(*altered)

    def test_mount_rw_missing_extra_duplicate_remapped_and_path_escape_denied(self):
        for kind in ('rw','missing','extra','duplicate','mapping','escape','propagation'):
            inputs=list(fixture());mounts=inputs[0]['mounts']
            if kind=='rw':mounts[0]['options']=['rw']
            elif kind=='missing':mounts.clear()
            elif kind=='extra':mounts.append({'destination':'/host','type':'bind','source':'/','options':['rbind']})
            elif kind=='duplicate':mounts.append(copy.deepcopy(mounts[0]))
            elif kind=='mapping':mounts[0]['uidMappings']=[{'containerID':0,'hostID':0,'size':1}]
            elif kind=='escape':mounts[0]['destination']='/proof/../host'
            else:mounts[0]['options'].append('rshared')
            inputs[1]=copy.deepcopy(inputs[0])
            with self.subTest(kind=kind),self.assertRaises(m.Denied):m.configured_profile(*inputs)

    def test_recursive_readonly_request_still_rejects_rw_and_shared_options(self):
        inputs=list(fixture());inputs[0]['mounts'][0]['options']=['rbind','rprivate','rro']
        inputs[1]=copy.deepcopy(inputs[0])
        result=m.configured_profile(*inputs)
        self.assertTrue(result['configuredPolicyConforms']);self.assertFalse(result['kernelEnforcementObserved'])
        for option in ('rw','shared','rshared','slave','rslave'):
            altered=copy.deepcopy(inputs);altered[0]['mounts'][0]['options'].append(option)
            altered[1]=copy.deepcopy(altered[0])
            with self.subTest(option=option),self.assertRaises(m.Denied):m.configured_profile(*altered)

    def test_privileged_devices_seccomp_listener_action_and_index_denied(self):
        for kind in ('devices','device','listener','notify','index','errno'):
            inputs=list(fixture());linux=inputs[0]['linux']
            if kind=='devices':linux['resources']['devices']=[{'allow':True,'access':'rwm'}]
            elif kind=='device':linux['devices']=[{'path':'/dev/sda','type':'b','major':8,'minor':0}]
            elif kind=='listener':linux['seccomp']['listenerPath']='/host/listener'
            elif kind=='notify':linux['seccomp']['syscalls'][0]['action']='SCMP_ACT_NOTIFY'
            elif kind=='index':linux['seccomp']['syscalls'][0]['args'][0]['index']=6
            else:linux['seccomp']['defaultErrnoRet']=2**32
            inputs[1]=copy.deepcopy(inputs[0])
            with self.subTest(kind=kind),self.assertRaises(m.Denied):m.configured_profile(*inputs)

    def test_unapproved_late_hooks_and_unbounded_compiled_hooks_denied(self):
        for phase,timeout in (('poststart',5),('prestart',0),('createRuntime',41)):
            inputs=list(fixture());hooks={phase:[{'path':'/CI_PRIVATE_HOOK','args':['/CI_PRIVATE_HOOK'],'timeout':timeout}]}
            inputs[0]['hooks']=hooks;inputs[1]=copy.deepcopy(inputs[0]);inputs[4]=hooks
            with self.subTest(phase=phase),self.assertRaises(m.Denied):m.configured_profile(*inputs)

    def test_schema_primary_source_pin_and_complexity_bounds(self):
        schema=m.schema_from_source_closure();self.assertGreaterEqual(len(schema['structs']),55)
        self.assertEqual(schema['sourceCommit'],'92249139eea7161e13745abd4cb6d0ea02a3227a')
        self.assertTrue(schema['dockerVendorMatch']['configTypesByteIdentical'])
        inputs=list(fixture());inputs[0]['annotations']={'x':'a'*131073};inputs[1]=copy.deepcopy(inputs[0])
        with self.assertRaises(m.Denied):m.configured_profile(*inputs)
        with self.assertRaises(m.Denied):m.shape([], '[]string',schema,budget=[0])

if __name__=='__main__':unittest.main()
