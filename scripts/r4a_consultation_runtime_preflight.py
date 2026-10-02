#!/usr/bin/env python3
"""Read-only runtime metadata for the coordinated Semantic/MCP rollout.

All container names and expected revisions are explicit installation inputs.
No environment values, host mount sources, credentials or container command values leave the process.
"""
import argparse
import json
import re
import subprocess


def summary(item, expected):
    config=item['Config'];host=item['HostConfig']
    revision=(config.get('Labels') or {}).get('org.opencontainers.image.revision')
    if revision!=expected or not item['State']['Running']:
        raise RuntimeError('LIVE_REVISION_OR_STATE_DRIFT')
    if host.get('Privileged'):
        raise RuntimeError('PRIVILEGED_RUNTIME_REQUIRES_REVIEW')
    return {'container':item['Name'],'running':True,'revision':revision,'image':item['Image'],
            'user':config.get('User'),'restart':(host.get('RestartPolicy') or {}).get('Name'),
            'network_names':sorted(item['NetworkSettings']['Networks']),
            'environment_names':sorted(e.partition('=')[0] for e in config.get('Env') or []),
            'mount_targets':[{'target':m['Destination'],'type':m['Type'],'readOnly':not m['RW']} for m in item.get('Mounts') or []],
            'entrypoint_count':len(config.get('Entrypoint') or []),'command_count':len(config.get('Cmd') or []),
            'port_binding_count':len(host.get('PortBindings') or {}),'read_only_root':bool(host.get('ReadonlyRootfs')),
            'healthcheck_configured':bool(config.get('Healthcheck'))}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--semantic-container',required=True);p.add_argument('--semantic-revision',required=True)
    p.add_argument('--mcp-container',required=True);p.add_argument('--mcp-revision',required=True)
    args=p.parse_args();records=[]
    for name,revision in [(args.semantic_container,args.semantic_revision),(args.mcp_container,args.mcp_revision)]:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',name) or not re.fullmatch(r'[0-9a-f]{40}',revision):
            p.error('explicit container names and exact revision SHA required')
        response=subprocess.run(['docker','inspect','--type','container',name],capture_output=True,text=True,check=False,timeout=15)
        if response.returncode:raise RuntimeError('CONTAINER_INSPECT_FAILED')
        items=json.loads(response.stdout)
        if len(items)!=1:raise RuntimeError('AMBIGUOUS_CONTAINER')
        records.append(summary(items[0],revision))
    print(json.dumps({'schema':'ouf.semantic-consultation-preflight.v1','read_only':True,
                      'no_secrets_printed':True,'not_release_acceptance':True,'containers':records},sort_keys=True))

if __name__=='__main__':
    try:main()
    except (RuntimeError,ValueError,KeyError,OSError,subprocess.SubprocessError):
        raise SystemExit('CONSULTATION_PREFLIGHT=BLOCKED; NO_MUTATION=true') from None
