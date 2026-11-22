import assert from 'node:assert/strict';
import { createHmac, randomUUID } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { setTimeout as sleep } from 'node:timers/promises';
import { classes, encoded, issuer, key, ontology, resources, reviewerToken, sha256 } from './fixture.mjs';

const base = 'http://127.0.0.1:8080';
const phase = process.argv[2];
const rdf = resources('/ontopia');
const cap = name => 'ouf.semantic.' + name;

async function api(path, body, headers = {}) {
  const response = await fetch(base + path, {
    method: body === undefined ? 'GET' : 'POST', body, redirect: 'error',
    headers: {'Content-Type': 'application/json', ...headers}, signal: AbortSignal.timeout(12000),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(path + ' HTTP ' + response.status + ' ' + (error.code ?? ''));
  }
  return response.json();
}

function delegated(domain, route, capability, scope, args, {actor = 'HUMAN', commandKey, operation = 'READ'} = {}) {
  const proposal = domain === 'proposal';
  const path = (proposal ? '/api/semantic/v1/proposal-commands/' : '/api/internal/v1/semantic/') + route;
  const envelope = {Owner: 'semantic', CapabilityID: cap(capability), GatewayBindingRef: 'capability://' + cap(capability),
    OperationClass: operation, Arguments: args};
  const purpose = 'semantic-' + domain + '-owner';
  const now = Math.floor(Date.now() / 1000);
  const receipt = {v: 1, purpose, method: 'POST', path, capability: cap(capability), iat: now, exp: now + 30,
    issuer, audience: 'gateway', workload: 'workload', subject: 'agent', tenant: 'tenant-a', acr: '1', roles: '', scope};
  const headers = {};
  if (proposal) {
    Object.assign(envelope, {Identity: {PrincipalID: 'agent', TenantID: 'tenant-a', ActorType: actor}, IdempotencyKey: commandKey});
    Object.assign(receipt, {actor, idempotencyKey: commandKey});
    headers['Idempotency-Key'] = commandKey;
  }
  const body = JSON.stringify(envelope);
  const payload = encoded({...receipt, bodyHash: sha256(body)});
  const mac = createHmac('sha256', key(domain)).update('ouf-' + purpose + '-v1.' + payload).digest('base64url');
  headers['X-OUF-Semantic-' + domain + '-Receipt'] = payload + '.' + mac;
  return api(path, body, headers);
}

function proposal(route, args, commandKey = randomUUID()) {
  const capability = {create: 'propose', adopt: 'discovery.adopt', validate: 'review.prepare', review: 'approval.request'}[route];
  const adoption = route === 'adopt';
  const scope = route === 'create' ? cap('propose') : adoption ? cap('discovery') : cap('review.prepare') + ' ' + cap('approval.request');
  return delegated('proposal', route, capability, scope, {...args, commandKey},
    {actor: adoption ? 'HUMAN' : 'AI_AGENT', commandKey, operation: 'COMMAND'});
}

async function discover(uri) {
  const request = await delegated('discovery', 'discovery/request', 'discovery', cap('discovery'), {
    requestedArtifactType: 'CLASS', intent: 'punto di interesse', preferredLanguages: ['it'], idempotencyKey: randomUUID(),
  }, {operation: 'COMMAND'});
  const requestId = request.requestId;
  for (let i = 0; i < 60; i++) {
    const status = await delegated('discovery', 'discovery/status', 'discovery.status', cap('discovery'), {requestId});
    if (status.state === 'SUCCEEDED') {
      const rows = await delegated('discovery', 'discovery/candidates', 'discovery.candidates', cap('discovery'), {requestId});
      const match = rows.find(row => row.canonical_uri === uri && row.provider_id === 'SCHEMA_GOV_IT');
      assert.ok(match, 'Expected discovered class ' + uri);
      return {requestId, candidateId: match.candidate_id};
    }
    assert.ok(['PENDING', 'RUNNING'].includes(status.state) && !status.errorCode,
      'Discovery ' + status.state + ' ' + (status.errorCode ?? ''));
    await sleep(1000);
  }
  throw new Error('Discovery deadline');
}

function ths(path, body, headers) {
  return api(path, JSON.stringify(body), {Authorization: 'Bearer ' + reviewerToken(), ...headers});
}

async function adoptAndReview(name, publish) {
  const semanticId = ontology + '/' + name;
  const selection = await discover(semanticId);
  const adoptionKey = randomUUID();
  const draft = await proposal('adopt', selection, adoptionKey);
  assert.equal(draft.semanticId, semanticId);
  assert.equal(draft.status, 'DRAFT');
  assert.equal(draft.provenance.rdfSha256, sha256(rdf.get(semanticId)));
  const {revisionId, expectedRowVersion} = draft;
  const validation = await proposal('validate', {revisionId, expectedRowVersion});
  assert.equal(validation.status, 'PASS');
  const args = {revisionId, expectedRowVersion, validationRunId: validation.validation_run_id};
  const reviewKey = randomUUID();
  const review = await proposal('review', args, reviewKey);
  const path = '/api/trusted-human/v1/semantic-approval-challenges/' + review.challengeId;
  const card = await ths(path);
  assert.equal(card.revision_id, revisionId);
  assert.equal(card.status, 'OPEN');
  assert.deepEqual(card.adoptionProvenance, draft.provenance);
  const description = card.description_json;
  if (phase === 'candidate') {
    assert.ok(description.en.includes('"superstructure"') && description.it.includes('"Entity-Entità"'),
      'The V19 review card must retain the quoted OntoPiA descriptions');
  }
  if (!publish) {
    assert.deepEqual(await proposal('review', args, reviewKey), review);
    const replay = await proposal('adopt', selection, adoptionKey);
    assert.equal(replay.revisionId, revisionId);
    assert.equal(replay.status, 'UNDER_REVIEW');
    assert.equal(replay.challengeId, review.challengeId);
    return;
  }
  const decision = await ths(path + '/decision', {decision: 'APPROVED'});
  assert.equal(decision.decision, 'APPROVED');
  const publication = await ths(path + '/publish',
    {approvalDecisionId: decision.decisionId, contentHash: review.targetContentHash}, {'Idempotency-Key': randomUUID()});
  assert.equal(publication.status, 'PUBLISHED');
  const {publicationSetId} = publication;
  assert.ok(publicationSetId);
  return {semanticId, revisionId, publicationSetId, description, selection, adoptionKey};
}

async function readPublished(record, latestSet) {
  const {semanticId, revisionId, publicationSetId, description} = record;
  const detail = await delegated('read', 'consultation/get', 'consultation.read', cap('read'),
    {semanticId, revisionId, publicationSetId});
  assert.equal(detail.publication_set_id, publicationSetId);
  assert.deepEqual(Buffer.from(detail.rdf_snapshot.content_base64, 'base64'), rdf.get(semanticId));
  const rows = await delegated('read', 'consultation/search', 'search', cap('search'),
    {q: semanticId, type: 'CLASS', namespace: ontology + '/'});
  const row = rows.find(item => item.semantic_id === semanticId);
  assert.ok(row, 'Published class missing from search');
  assert.equal(row.publication_set_id, latestSet);
  for (const item of [row, detail]) {
    assert.equal(item.semantic_id, semanticId);
    assert.equal(item.revision_id, revisionId);
    assert.equal(item.status, 'ACTIVE');
    assert.deepEqual(item.description, description);
  }
}

async function publishDatatype() {
  const semanticId = 'https://example.org/datatypes/Recapito';
  const definition = {components: [
    {cardinality: 'ONE', constraints: {maxLength: 80}, name: 'via', required: true, type: 'string'},
    {cardinality: 'ONE', constraints: {maxInclusive: '9007199254740993', minInclusive: '1'}, name: 'civico', required: false, type: 'integer'},
  ]};
  const draft = await proposal('create', {semanticId, artifactType: 'DATATYPE', namespace: 'https://example.org/datatypes/',
    localName: 'Recapito', ownerRef: 'owner', authorityRef: 'authority', semanticVersion: '1.0.0',
    labels: {it: 'Recapito'}, definition: {...definition, description: {it: 'Indirizzo del servizio'}}});
  const {revisionId} = draft;
  const args = {revisionId, expectedRowVersion: 0};
  const validation = await proposal('validate', args);
  assert.equal(validation.status, 'PASS');
  const review = await proposal('review', {...args, validationRunId: validation.validation_run_id});
  const path = '/api/trusted-human/v1/semantic-approval-challenges/' + review.challengeId;
  const card = await ths(path);
  assert.equal(card.datatypeReview.componenti[0].tipo, 'Testo');
  const decision = await ths(path + '/decision', {decision: 'APPROVED'});
  const {publicationSetId} = await ths(path + '/publish', {approvalDecisionId: decision.decisionId,
    contentHash: review.targetContentHash}, {'Idempotency-Key': randomUUID()});
  const ref = {semanticId, revisionId, publicationSetId};
  const result = await delegated('read', 'consultation/get', 'consultation.read', cap('read'), ref);
  assert.equal(result.status, 'ACTIVE');
  assert.deepEqual(result.definition, definition);
  assert.equal(result.definitionSha256, sha256(JSON.stringify(definition)));
  assert.match(result.rdf_snapshot.content_hash, /^[a-f0-9]{64}$/);
  writeFileSync('/state/datatype.json', JSON.stringify({ref, definition, rdfHash: result.rdf_snapshot.content_hash}));
}

async function publishNative({semanticId, artifactType, labels, definition}, inspectCard = () => {}) {
  const namespace = semanticId.slice(0, semanticId.lastIndexOf('/') + 1);
  const draft = await proposal('create', {semanticId, artifactType, namespace,
    localName: semanticId.slice(namespace.length), ownerRef: 'owner', authorityRef: 'authority',
    semanticVersion: '1.0.0', labels, definition});
  const {revisionId} = draft;
  const args = {revisionId, expectedRowVersion: 0};
  const validation = await proposal('validate', args);
  assert.equal(validation.status, 'PASS');
  const review = await proposal('review', {...args, validationRunId: validation.validation_run_id});
  const path = '/api/trusted-human/v1/semantic-approval-challenges/' + review.challengeId;
  inspectCard(await ths(path));
  const decision = await ths(path + '/decision', {decision: 'APPROVED'});
  const {publicationSetId} = await ths(path + '/publish', {approvalDecisionId: decision.decisionId,
    contentHash: review.targetContentHash}, {'Idempotency-Key': randomUUID()});
  return {semanticId, revisionId, publicationSetId};
}

async function publishValueMap() {
  const vocabularyId = 'https://example.org/termini/Servizi';
  const concept = 'https://example.org/termini/Biblioteca';
  const vocabulary = await publishNative({semanticId: vocabularyId, artifactType: 'VOCABULARY',
    labels: {it: 'Servizi'}, definition: {}});
  const term = await publishNative({semanticId: concept, artifactType: 'CONCEPT', labels: {it: 'Biblioteca'},
    definition: {vocabularyRef: vocabularyId}});
  const targetVocabulary = vocabularyId + '@' + term.publicationSetId;
  const entries = [{code: 'b', concept}, {code: 'B', concept}];
  const labels = {it: 'Codici servizio'};
  const ref = await publishNative({semanticId: 'https://example.org/mappe/CodiciServizio', artifactType: 'VALUE_MAP',
    definition: {targetVocabulary, entries, labels}}, card => {
    const review = card.valueMapReview;
    assert.equal(review.nome, labels.it);
    assert.equal(review.numeroVoci, 2);
    assert.deepEqual(review.vocabolario, {identificativo: vocabularyId, etichetta: 'Servizi'});
    assert.deepEqual(review.voci[0], {codice: 'B', concetto: {identificativo: concept, etichetta: 'Biblioteca'}});
  });
  const result = await delegated('read', 'consultation/get', 'consultation.read', cap('read'),
    {semanticId: ref.semanticId, publicationSetId: ref.publicationSetId});
  const definition = {entries: entries.toReversed(), labels, targetVocabulary};
  assert.deepEqual(result.definition, definition);
  assert.equal(result.status, 'ACTIVE');
  assert.equal(result.revision_id, ref.revisionId);
  assert.equal(result.definitionSha256, sha256(JSON.stringify(definition)));
  writeFileSync('/state/value-map.json', JSON.stringify({ref, definition, term, vocabulary}));
}

async function readiness() {
  let last = 'connection refused';
  for (let i = 0; i < 90; i++) {
    try {
      for (const group of ['readiness', 'cutover']) {
        const response = await fetch(base + '/actuator/health/' + group, {signal: AbortSignal.timeout(2000)});
        const body = await response.json();
        last = group + ' HTTP ' + response.status + ' ' + body.status;
        if (response.status === 503) break;
        assert.ok(response.ok && body.status === 'UP', last);
        if (group === 'cutover') return;
      }
    } catch (error) {
      if (error.cause?.code !== 'ECONNREFUSED' && error.name !== 'TimeoutError') throw error;
    }
    await sleep(1000);
  }
  throw new Error('Release readiness deadline: ' + last);
}

try {
  await readiness();
} catch (error) {
  if (phase === 'return') {
    console.error('Domande aperte — il predecessore non è pronto sullo schema candidato. Verificare la causa prima del rilascio.');
  }
  throw error;
}
console.log(phase + ': release readiness and cutover UP');
if (phase === 'baseline' || phase === 'candidate') {
  if (phase === 'candidate') {
    await publishDatatype();
    await publishValueMap();
  }
  const record = await adoptAndReview(classes[phase === 'baseline' ? 0 : 1], true);
  await readPublished(record, record.publicationSetId);
  writeFileSync('/state/' + phase + '.json', JSON.stringify(record));
  console.log(phase + ': published and resolved ' + record.semanticId + ' revision ' + record.revisionId);
} else if (phase === 'return') {
  const load = name => JSON.parse(readFileSync('/state/' + name + '.json'));
  const candidate = load('candidate');
  const datatype = load('datatype');
  assert.notEqual(datatype.ref.publicationSetId, candidate.publicationSetId);
  for (const publicationSetId of [datatype.ref.publicationSetId, candidate.publicationSetId]) {
    const result = await delegated('read', 'consultation/get', 'consultation.read', cap('read'), {...datatype.ref, publicationSetId});
    assert.equal(result.artifact_type, 'DATATYPE');
    assert.equal(result.status, 'ACTIVE');
    assert.equal(result.revision_id, datatype.ref.revisionId);
    assert.equal(result.publication_set_id, publicationSetId);
    assert.deepEqual(result.definition, datatype.definition);
    assert.equal(result.rdf_snapshot.content_hash, datatype.rdfHash);
  }
  console.log('return: DATATYPE revision ' + datatype.ref.revisionId + ' resolved in both publication sets');
  const valueMap = load('value-map');
  for (const publicationSetId of [valueMap.ref.publicationSetId, candidate.publicationSetId]) {
    const result = await delegated('read', 'consultation/get', 'consultation.read', cap('read'),
      {...valueMap.ref, publicationSetId});
    assert.equal(result.artifact_type, 'VALUE_MAP');
    assert.equal(result.status, 'ACTIVE');
    assert.equal(result.revision_id, valueMap.ref.revisionId);
    assert.equal(result.publication_set_id, publicationSetId);
    assert.deepEqual(result.definition, valueMap.definition);
  }
  const term = await delegated('read', 'consultation/get', 'consultation.read', cap('read'), valueMap.term);
  const vocabulary = await delegated('read', 'consultation/get', 'consultation.read', cap('read'), valueMap.vocabulary);
  assert.equal(term.artifact_type, 'CONCEPT');
  assert.equal(vocabulary.artifact_type, 'VOCABULARY');
  assert.equal(term.definition.vocabularyRef, valueMap.vocabulary.semanticId);
  console.log('return: published value map, vocabulary and concept reads succeeded');
  await readPublished(load('baseline'), candidate.publicationSetId);
  await readPublished(candidate, candidate.publicationSetId);
  const retry = await proposal('adopt', candidate.selection, candidate.adoptionKey);
  assert.equal(retry.status, 'ACTIVE');
  assert.equal(retry.revisionId, candidate.revisionId);
  assert.equal(retry.publicationSetId, candidate.publicationSetId);
  await adoptAndReview(classes[2], false);
  console.log('return: both publications resolved, candidate receipt replayed, new adoption reviewed and retried');
} else throw new Error('Unknown scenario');
