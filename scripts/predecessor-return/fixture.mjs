import { createHash, createPrivateKey, createPublicKey, generateKeyPairSync, randomBytes, sign } from 'node:crypto';
import { chownSync, readFileSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:https';
import { pathToFileURL } from 'node:url';

export const issuer = 'https://127.0.0.1:9443';
export const ontology = 'https://w3id.org/italia/onto/POI';
export const classes = ['MultiplePointOfInterest', 'PointOfInterest', 'POIState'];
export const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
export const encoded = value => Buffer.from(JSON.stringify(value)).toString('base64url');
export const key = name => readFileSync('/fixture/' + name, 'utf8').trim();
const capability = name => 'ouf.semantic.' + name;

// Descriptor, operation, required scope, actor and grantee as seen by the owner.
const policy = [
  ['discovery', 'COMMAND', 'discovery', 'HUMAN', 'agent'],
  ['discovery.status', 'READ', 'discovery', 'HUMAN', 'agent'],
  ['discovery.candidates', 'READ', 'discovery', 'HUMAN', 'agent'],
  ['discovery.adopt', 'COMMAND', 'discovery', 'HUMAN', 'agent'],
  ['review.prepare', 'COMMAND', 'review.prepare', 'AI_AGENT', 'agent'],
  ['approval.request', 'COMMAND', 'approval.request', 'AI_AGENT', 'agent'],
  ['consultation.read', 'READ', 'read', 'HUMAN', 'agent'],
  ['search', 'READ', 'search', 'HUMAN', 'agent'],
  ['review', 'READ', 'review', 'HUMAN', 'reviewer'],
  ['approve', 'COMMAND', 'approve', 'HUMAN', 'reviewer'],
  ['publish', 'COMMAND', 'publish', 'HUMAN', 'reviewer'],
];

function initialize() {
  for (const file of ['proposal', 'discovery', 'read', 'provider']) {
    writeFileSync('/fixture/' + file, randomBytes(32).toString('hex'), {mode: 0o440});
    chownSync('/fixture/' + file, 0, 10001);
  }
  writeFileSync('/private/provider-token', randomBytes(32).toString('hex'), {mode: 0o600});
  const {privateKey} = generateKeyPairSync('rsa', {modulusLength: 2048});
  writeFileSync('/private/issuer.pem', privateKey.export({type: 'pkcs8', format: 'pem'}), {mode: 0o600});
  const now = Date.now();
  const bundle = JSON.stringify({
    bundleId: 'return-ci', version: 1, publishedAt: new Date(now).toISOString(),
    capabilities: policy.map(([id, operation, scope, actor]) => ({
      capabilityId: capability(id), operation, requiredScope: capability(scope), allowedActors: [actor],
    })),
    grants: policy.map(([id, , , , subjectId]) => ({
      grantId: id, capabilityId: capability(id), tenantId: 'tenant-a', subjectId,
      validFrom: new Date(now - 60000).toISOString(), validUntil: new Date(now + 3600000).toISOString(),
    })),
  });
  writeFileSync('/fixture/bundle.json', bundle);
  writeFileSync('/fixture/application.properties', [
    'ouf.authorization.bundle-file=/fixture/bundle.json', 'ouf.authorization.bundle-id=return-ci',
    'ouf.authorization.bundle-version=1', 'ouf.authorization.bundle-sha256=' + sha256(bundle),
    'ouf.iam.enabled=true', 'ouf.iam.issuer=' + issuer, 'ouf.iam.audience=gateway',
    'ouf.semantic.proposal-receipt.key-file=/fixture/proposal', 'ouf.semantic.proposal-receipt.issuer=' + issuer,
    'ouf.semantic.proposal-receipt.audience=gateway', 'ouf.semantic.proposal-receipt.workload=workload',
    'ouf.semantic.discovery-delegation.key-file=/fixture/discovery', 'ouf.semantic.discovery-delegation.workload=workload',
    'ouf.semantic.delegation.key-file=/fixture/read', 'ouf.semantic.delegation.workload=workload',
  ].join('\n') + '\n');
}

export function reviewerToken() {
  const now = Math.floor(Date.now() / 1000);
  const payload = encoded({alg: 'RS256', kid: 'ci'}) + '.' + encoded({
    iss: issuer, aud: ['gateway'], sub: 'reviewer', tenant_id: 'tenant-a', ouf_actor_type: 'HUMAN',
    acr: '1', scope: 'ouf.semantic.review ouf.semantic.approve ouf.semantic.publish', iat: now, exp: now + 60,
  });
  return payload + '.' + sign('RSA-SHA256', Buffer.from(payload), readFileSync('/private/issuer.pem')).toString('base64url');
}

export function resources(directory) {
  const turtle = readFileSync(directory + '/POI-AP_IT.ttl', 'utf8').replaceAll('\r\n', '\n');
  const prefixes = turtle.slice(0, turtle.indexOf('\n\n'));
  function block(subject) {
    const start = turtle.indexOf('\n' + subject + ' rdf:type');
    const end = turtle.indexOf('\n\n', start + 1);
    if (start < 0 || end < 0) throw new Error('Missing OntoPiA subject ' + subject);
    return Buffer.from(prefixes + '\n' + turtle.slice(start, end) + '\n');
  }
  return new Map([
    [ontology, block('<' + ontology + '>')],
    ...classes.map(name => [ontology + '/' + name, name === 'PointOfInterest'
      ? readFileSync(directory + '/fetched/PointOfInterest.ttl') : block(':' + name)]),
  ]);
}

function serve() {
  const rdf = resources('/ontopia');
  const jwk = createPublicKey(createPrivateKey(readFileSync('/private/issuer.pem'))).export({format: 'jwk'});
  const token = readFileSync('/private/provider-token', 'utf8');
  createServer({key: readFileSync('/private/tls.key'), cert: readFileSync('/private/tls.crt')}, async (req, res) => {
    const url = new URL(req.url, issuer);
    function reply(status, body, type = 'application/json') {
      res.writeHead(status, {'content-type': type});
      res.end(Buffer.isBuffer(body) ? body : JSON.stringify(body));
    }
    if (req.method === 'GET' && url.pathname === '/.well-known/openid-configuration')
      return reply(200, {issuer, jwks_uri: issuer + '/jwks', token_endpoint: issuer + '/token',
        authorization_endpoint: issuer + '/authorize', response_types_supported: ['code'],
        subject_types_supported: ['public'], id_token_signing_alg_values_supported: ['RS256']});
    if (req.method === 'GET' && url.pathname === '/jwks')
      return reply(200, {keys: [{...jwk, kid: 'ci', alg: 'RS256', use: 'sig'}]});
    let raw = '';
    for await (const chunk of req) raw += chunk;
    const form = new URLSearchParams(raw);
    if (req.method === 'POST' && url.pathname === '/token') {
      if (form.get('grant_type') !== 'client_credentials' || form.get('client_id') !== 'semantic-ci' ||
          form.get('scope') !== 'fixture.invoke' || form.get('client_secret') !== key('provider')) return reply(403, {});
      return reply(200, {access_token: token, token_type: 'Bearer', expires_in: 120, scope: 'fixture.invoke'});
    }
    if (req.headers.authorization !== 'Bearer ' + token) return reply(403, {});
    if (req.method === 'POST' && url.pathname === '/search' && form.get('query')?.includes('SELECT')) {
      const bindings = classes.map(name => ({resource: {type: 'uri', value: ontology + '/' + name}}));
      return reply(200, {results: {bindings}}, 'application/sparql-results+json');
    }
    if (req.method === 'GET' && url.pathname === '/fetch' && rdf.has(url.searchParams.get('uri')))
      return reply(200, rdf.get(url.searchParams.get('uri')), 'text/turtle');
    reply(404, {});
  }).listen(9443, '127.0.0.1');
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (process.argv[2] === 'init') initialize();
  else if (process.argv[2] === 'serve') serve();
  else throw new Error('Expected init or serve');
}
