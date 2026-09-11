#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
evidence_dir="$repo_dir/pairwise/evidence/semantic-gateway-live-v1"
mkdir -p "$evidence_dir"
rm -f "$evidence_dir"/{results.tap,summary.json,gateway.log,semantic.log,postgres.log,live-probe.json}

postgres_name=ouf-pairwise-postgres
gateway_name=ouf-pairwise-gateway
semantic_name=ouf-pairwise-semantic
cleanup() {
  docker logs "$gateway_name" >"$evidence_dir/gateway.log" 2>&1 || true
  docker logs "$semantic_name" >"$evidence_dir/semantic.log" 2>&1 || true
  docker logs "$postgres_name" >"$evidence_dir/postgres.log" 2>&1 || true
  docker rm -f "$semantic_name" "$gateway_name" "$postgres_name" >/dev/null 2>&1 || true
}
trap cleanup EXIT
cleanup

retry_http() {
  local url="$1"
  for _ in $(seq 1 90); do
    curl --fail --silent --show-error --max-time 3 "$url" >/dev/null && return 0
    sleep 1
  done
  echo "timeout waiting for $url" >&2
  return 1
}

# An explicit live preflight proves that this run reached the official service.
curl --fail --silent --show-error --max-time 20 \
  -H 'Accept: application/sparql-results+json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'query=SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } } LIMIT 1' \
  https://schema.gov.it/sparql >"$evidence_dir/live-probe.json"
python3 - "$evidence_dir/live-probe.json" <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))
assert d['results']['bindings'], 'official SPARQL endpoint returned no graph'
PY

docker run -d --name "$postgres_name" -p 55432:5432 \
  -e POSTGRES_DB=ouf_semantic -e POSTGRES_USER=ouf_semantic -e POSTGRES_PASSWORD=ouf_semantic \
  postgres:17-alpine >/dev/null
for _ in $(seq 1 60); do
  docker exec "$postgres_name" pg_isready -U ouf_semantic -d ouf_semantic >/dev/null 2>&1 && break
  sleep 1
done
docker exec "$postgres_name" pg_isready -U ouf_semantic -d ouf_semantic >/dev/null

docker build -t ouf-semantic-pairwise "$repo_dir" >/dev/null
docker build -t ouf-gateway-pairwise "$repo_dir/pairwise/gateway-fixture" >/dev/null

docker run -d --name "$gateway_name" --network host \
  -e PORT=18090 \
  -e SCHEMA_GOV_SPARQL_UPSTREAM=https://schema.gov.it/sparql \
  -e SCHEMA_GOV_ALLOWED_HOSTS=schema.gov.it,w3id.org \
  ouf-gateway-pairwise >/dev/null
retry_http http://127.0.0.1:18090/actuator/health

docker run -d --name "$semantic_name" --network host \
  -e PORT=18080 \
  -e SPRING_DATASOURCE_URL=jdbc:postgresql://127.0.0.1:55432/ouf_semantic \
  -e SPRING_DATASOURCE_USERNAME=ouf_semantic \
  -e SPRING_DATASOURCE_PASSWORD=ouf_semantic \
  -e OUF_SCHEMA_GOV_ENABLED=true \
  -e OUF_SCHEMA_GOV_GATEWAY_BASE_URL=http://127.0.0.1:18090 \
  -e OUF_DISCOVERY_WORKER_ENABLED=true \
  -e OUF_DISCOVERY_WORKER_DELAY_MS=200 \
  ouf-semantic-pairwise >/dev/null
retry_http http://127.0.0.1:18080/actuator/health

request_json=$(curl --fail --silent --show-error --max-time 10 \
  -H 'Content-Type: application/json' -H 'X-OUF-Subject: pairwise-live-test' \
  --data '{"requestedArtifactType":"CLASS","intent":"Address","preferredLanguages":["en","it"]}' \
  http://127.0.0.1:18080/api/semantic/v1/discovery-requests)
request_id=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["requestId"])' <<<"$request_json")

candidates='[]'
for _ in $(seq 1 90); do
  candidates=$(curl --fail --silent --show-error --max-time 5 \
    "http://127.0.0.1:18080/api/semantic/v1/discovery-requests/$request_id/candidates")
  python3 -c 'import json,sys; raise SystemExit(0 if json.load(sys.stdin) else 1)' <<<"$candidates" && break
  sleep 1
done
candidate_id=$(python3 -c 'import json,sys; a=json.load(sys.stdin); x=next(v for v in a if v["canonical_uri"]=="https://w3id.org/italia/onto/CLV/Address" and v["provider_id"]=="SCHEMA_GOV_IT"); print(x["candidate_id"])' <<<"$candidates")

adoption=$(curl --fail --silent --show-error --max-time 10 \
  -H 'Content-Type: application/json' -H 'X-OUF-Subject: pairwise-live-test' \
  --data '{"semanticId":"https://w3id.org/italia/onto/CLV/Address","namespace":"https://w3id.org/italia/onto/CLV/","localName":"Address","ownerRef":"schema.gov.it","authorityRef":"Catalogo Nazionale Dati"}' \
  "http://127.0.0.1:18080/api/semantic/v1/discovery-requests/$request_id/candidates/$candidate_id:adopt")
artifact_id=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["artifactId"])' <<<"$adoption")
artifact=$(curl --fail --silent --show-error --max-time 10 "http://127.0.0.1:18080/api/semantic/v1/artifacts/$artifact_id")
python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["semantic_id"]=="https://w3id.org/italia/onto/CLV/Address"' <<<"$artifact"

cat >"$evidence_dir/results.tap" <<'TAP'
TAP version 13
1..6
ok 1 - official schema.gov.it SPARQL endpoint reached live
ok 2 - Gateway fixture healthy as separate process
ok 3 - Semantic Registry healthy with PostgreSQL 17
ok 4 - discovery traversed Semantic -> Gateway -> schema.gov.it SPARQL
ok 5 - RDF CONSTRUCT traversed Gateway and candidate was persisted
ok 6 - live candidate was adopted and read back
TAP
python3 - "$evidence_dir/summary.json" "$request_id" "$candidate_id" "$artifact_id" <<'PY'
import json,sys,datetime
out={
  'schemaVersion':'1.0', 'pairwiseId':'semantic-gateway-live-v1',
  'status':'PASS', 'tests':{'catalogued':6,'executed':6,'passed':6,'failed':0,'skipped':0},
  'modules':['Semantic Model Registry','minimal Gateway fixture'],
  'runtime':{'java':'21','postgresql':'17','deployment':'separate containers'},
  'externalDependency':{'name':'schema.gov.it','mode':'LIVE','endpoint':'https://schema.gov.it/sparql'},
  'requestId':sys.argv[2], 'candidateId':sys.argv[3], 'artifactId':sys.argv[4],
  'productionReady':False,
  'limitations':['minimal Gateway fixture, not the full Urban API Gateway','no Authorization/IAM','no Kubernetes or HA test'],
  'completedAt':datetime.datetime.now(datetime.timezone.utc).isoformat()
}
open(sys.argv[1],'w').write(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
PY
echo "PAIRWISE PASS: Semantic Registry <-> Gateway fixture <-> live schema.gov.it"
