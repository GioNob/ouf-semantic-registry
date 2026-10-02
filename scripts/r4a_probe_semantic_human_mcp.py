#!/usr/bin/env python3
"""Read-only positive Semantic MCP probe using the existing HUMAN device client."""
import argparse
import json
import sys
import uuid
from urllib.parse import urlsplit
import r4a_admin_permission_proposal as client


def payload(result, tool=None):
    if result.get('isError'):
        # Never print arbitrary backend messages, detail, or unknown code strings.
        safe={'tool':tool if tool in ('semantic.search','semantic.get') else 'unknown',
              'code':'UNCLASSIFIED_TOOL_ERROR'}
        try:
            blocks=result.get('content',[])
            if len(blocks)!=1 or blocks[0].get('type')!='text':raise ValueError()
            error=json.loads(blocks[0]['text'])
            if not isinstance(error,dict):raise ValueError()
            code=error.get('code',error.get('Code'))
            known={'authorization denied':'MCP_AUTHORIZATION_DENIED',
                   'UNAUTHENTICATED':'UNAUTHENTICATED',
                   'MCP_1A_BACKEND_NOT_BOUND':'MCP_1A_BACKEND_NOT_BOUND',
                   'SEM_READ_RECEIPT_OR_POLICY_DENIED':'SEM_READ_RECEIPT_OR_POLICY_DENIED',
                   'NOT_AUTHORIZED':'NOT_AUTHORIZED','UPSTREAM_ERROR':'UPSTREAM_ERROR',
                   'BAD_REQUEST':'BAD_REQUEST','RESULT_LIMIT_EXCEEDED':'RESULT_LIMIT_EXCEEDED'}
            if isinstance(code,str) and code in known:safe['code']=known[code]
            status=error.get('status',error.get('Status'))
            if type(status) is int and 100<=status<=599:safe['httpStatus']=status
        except (ValueError,TypeError,KeyError,IndexError):pass
        print('SEMANTIC_TOOL_ERROR='+json.dumps(safe,sort_keys=True),flush=True)
        raise ValueError('MCP_TOOL_DENIED')
    blocks = result.get('content', [])
    if len(blocks) != 1 or blocks[0].get('type') != 'text':
        raise ValueError('MCP_RESULT_INVALID')
    return json.loads(blocks[0]['text'])


def tool_call(token,name,arguments,request_id):
    correlation=str(uuid.uuid4())
    original=client.mcp_headers
    def headers(*args,**kwargs):
        value=original(*args,**kwargs);value['X-Correlation-ID']=correlation;return value
    print('SEMANTIC_PROBE_REQUEST='+json.dumps({'tool':name,'correlationId':correlation}),flush=True)
    client.mcp_headers=headers
    try:
        result=client.rpc(token,'tools/call',{'name':name,'arguments':arguments},request_id,
                          name.replace('.','-')+'-'+uuid.uuid4().hex)
    finally:client.mcp_headers=original
    return payload(result,name)


def probe(token, query):
    discovery = client.rpc(token, 'tools/list', {}, 1)
    names = {row.get('name') for row in discovery.get('tools', [])}
    available = {name: name in names for name in ('semantic.search', 'semantic.get')}
    print('SEMANTIC_MCP_DISCOVERY=' + json.dumps(available), flush=True)
    if not all(available.values()):
        raise ValueError('SEMANTIC_TOOLS_MISSING_FROM_SERVER_DISCOVERY')
    rows = tool_call(token,'semantic.search',{'q':query,'limit':1},2)
    if not isinstance(rows, list):
        raise ValueError('SEARCH_RESULT_NOT_LIST')
    print('SEMANTIC_SEARCH=PASS RESULT_COUNT=' + str(len(rows)), flush=True)
    if not rows:
        raise ValueError('GET_NOT_PROVEN_SEARCH_EMPTY')
    row = rows[0]
    arguments = {'semanticId': row['semantic_id'], 'revisionId': row['revision_id'],
                 'publicationSetId': row['publication_set_id']}
    if not all(isinstance(v, str) and v for v in arguments.values()):
        raise ValueError('SEARCH_REFERENCE_INVALID')
    resolved = tool_call(token,'semantic.get',arguments,3)
    if not isinstance(resolved, dict) or any(resolved.get(k) != row[k]
            for k in ('semantic_id', 'revision_id', 'publication_set_id')):
        raise ValueError('EXACT_REFERENCE_MISMATCH')
    print('SEMANTIC_GET=PASS EXACT_REFERENCE_MATCH=true', flush=True)
    print('SEMANTIC_HUMAN_MCP=PASS READ_ONLY=true NO_SOURCE_RUN=true NO_SECRETS_PRINTED=true', flush=True)


def human_login(a, scopes):
    client.ISSUER, client.ADMIN_SUB = a.issuer.rstrip('/'), a.subject
    if getattr(a, "mcp_url", None):client.MCP_URL = a.mcp_url
    client.REQUIRED_SCOPES = scopes
    original_post = client.oidc_post
    def post(url, fields):
        fields = dict(fields)
        fields['client_id'] = a.client
        if 'scope' in fields:
            fields['scope'] = 'openid ' + ' '.join(sorted(scopes))
        return original_post(url, fields)
    def validate(claims):
        if (claims.get('iss') != client.ISSUER or claims.get('sub') != a.subject
                or claims.get('azp') != a.client or claims.get('tenant_id') != a.tenant
                or claims.get('ouf_actor_type') not in ('HUMAN', 'HUMAN_USER')
                or not client.audience_has(claims.get('aud'), a.audience)
                or not scopes.issubset(str(claims.get('scope', '')).split())
                or not claims.get('acr') or claims.get('exp', 0) <= client.time.time() + 30):
            raise ValueError('HUMAN_TOKEN_CONTEXT_MISMATCH')
        return True
    client.oidc_post, client.validate_admin_claims = post, validate
    return client.device_login()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--issuer', required=True)
    p.add_argument('--mcp-url', required=True)
    p.add_argument('--client', required=True)
    p.add_argument('--subject', required=True)
    p.add_argument('--tenant', required=True)
    p.add_argument('--audience', required=True)
    p.add_argument('--query', required=True)
    a = p.parse_args()
    for value in (a.issuer, a.mcp_url):
        u = urlsplit(value)
        if u.scheme != 'https' or not u.hostname or u.username or u.password or u.query or u.fragment:
            raise ValueError('HTTPS_ENDPOINT_REQUIRED')
    if not a.query.strip() or len(a.query) > 256:
        raise ValueError('QUERY_INVALID')
    scopes = {'mcp.connect', 'ouf.semantic.search', 'ouf.semantic.read'}
    token = human_login(a, scopes)
    print('SEMANTIC_HUMAN_TOKEN_CONTEXT=PASS', flush=True)
    probe(token, a.query)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        code = str(exc).split(':', 1)[0] if isinstance(exc, (ValueError, RuntimeError)) else type(exc).__name__
        print('SEMANTIC_HUMAN_MCP=BLOCKED REASON=' + code, flush=True)
        sys.exit(1)
