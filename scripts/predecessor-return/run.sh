#!/usr/bin/env bash
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
root="$(git rev-parse --show-toplevel)"
tmp="$(mktemp -d)"
db="semantic-return-db-$GITHUB_RUN_ID-$GITHUB_RUN_ATTEMPT"
fixture="$db-fixture"
previous="$db-previous"
candidate="$db-candidate"
cleanup() {
  docker rm -fv "$previous" "$candidate" "$fixture" "$db" >/dev/null 2>&1 || true
  sudo rm -rf -- "$tmp"
}
trap cleanup EXIT
note() {
  echo "$*"
  echo "- $*" >> "$GITHUB_STEP_SUMMARY"
}
mkdir "$tmp"/{old-sql,new-sql,fixture,private,state}
old_id="$(python3 "$here/images.py" "$root/target/predecessor" "$tmp/old-sql" predecessor)"
new_id="$(python3 "$here/images.py" "$root/target/governed-image" "$tmp/new-sql" candidate)"
[[ "$old_id" != "$new_id" ]]
note "Installed predecessor $PREDECESSOR_COMMIT, run $PREDECESSOR_RUN, image $old_id"
note "Candidate $GITHUB_SHA, image $new_id"

# All runtime containers share only the database container's loopback interface.
# Fetch support images before entering the isolated qualification scenario.
postgres_image=postgres:17-alpine
node_image=node:22-alpine
for image in "$postgres_image" "$node_image"; do docker pull "$image" >/dev/null; done
docker run --pull=never -d --network none --name "$db" \
  -e POSTGRES_DB=semantic -e POSTGRES_USER=semantic -e POSTGRES_PASSWORD=ci-only "$postgres_image" >/dev/null
shared=(--pull=never --network "container:$db")
sql() {
  docker exec -e PGPASSWORD=ci-only "$db" psql -XwAtq -h 127.0.0.1 -U semantic -d semantic -v ON_ERROR_STOP=1 -c "$1"
}
# Use TCP: the entrypoint's temporary bootstrap server listens on a socket only.
for ((i=0; i<60; i++)); do
  if docker exec "$db" pg_isready -q -h 127.0.0.1 -U semantic -d semantic; then break; fi
  sleep 1
done
db_identity() { sql "select system_identifier || '/' || oid from pg_control_system(), pg_database where datname=current_database()"; }
database="$(db_identity)"
note "PostgreSQL system/database $database"

openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj '/CN=127.0.0.1' \
  -addext 'subjectAltName=IP:127.0.0.1' -keyout "$tmp/private/tls.key" \
  -out "$tmp/private/tls.crt" >/dev/null 2>&1
keytool -importcert -noprompt -alias fixture -storetype PKCS12 -storepass fixture-only \
  -file "$tmp/private/tls.crt" -keystore "$tmp/fixture/trust.p12" >/dev/null
fixture_mounts=(-v "$here:/driver:ro" -v "$root/src/test/resources/discovery/ontopia:/ontopia:ro")
docker run --rm --pull=never --network none "${fixture_mounts[@]}" \
  -v "$tmp/fixture:/fixture" -v "$tmp/private:/private" "$node_image" node /driver/fixture.mjs init
sudo chown root:root "$tmp/fixture"
sudo chmod 0755 "$tmp/fixture"
sudo chmod 0644 "$tmp/fixture"/{bundle.json,application.properties,trust.p12}
docker run -d "${shared[@]}" --name "$fixture" "${fixture_mounts[@]}" \
  -v "$tmp/fixture:/fixture:ro" -v "$tmp/private:/private:ro" -v "$tmp/state:/state" \
  "$node_image" node /driver/fixture.mjs serve >/dev/null

create_app() {
  docker create "${shared[@]}" --name "$1" -v "$tmp/fixture:/fixture:ro" \
    -e SPRING_CONFIG_ADDITIONAL_LOCATION=file:/fixture/application.properties \
    -e SPRING_FLYWAY_ENABLED=false -e MANAGEMENT_ENDPOINT_HEALTH_GROUP_CUTOVER_INCLUDE=livenessState,readinessState,db \
    -e OUF_SEM_DB_URL=jdbc:postgresql://127.0.0.1:5432/semantic -e OUF_SEM_DB_USER=semantic -e OUF_SEM_DB_PASSWORD=ci-only \
    -e OUF_SCHEMA_GOV_ENABLED=true -e OUF_DISCOVERY_WORKER_ENABLED=true -e OUF_DISCOVERY_WORKER_DELAY=500ms \
    -e OUF_SCHEMA_GOV_GATEWAY_BASE_URL=https://127.0.0.1:9443 -e OUF_SCHEMA_GOV_SEARCH_PATH=/search -e OUF_SCHEMA_GOV_FETCH_PATH=/fetch \
    -e OUF_SCHEMA_GOV_GATEWAY_AUTH_ENABLED=true -e OUF_SCHEMA_GOV_TOKEN_ENDPOINT=https://127.0.0.1:9443/token \
    -e OUF_SCHEMA_GOV_CLIENT_ID=semantic-ci -e OUF_SCHEMA_GOV_CLIENT_SECRET_FILE=/fixture/provider \
    -e OUF_SCHEMA_GOV_WORKLOAD_SCOPE=fixture.invoke \
    -e JAVA_TOOL_OPTIONS='-Djavax.net.ssl.trustStore=/fixture/trust.p12 -Djavax.net.ssl.trustStorePassword=fixture-only' \
    "$2" >/dev/null
}
migrate() {
  "$JAVA_HOME_21_X64/bin/javac" -proc:none -cp "$1/lib/*" -d "$1" "$here/Migrate.java"
  docker run --rm "${shared[@]}" -v "$1:/migration:ro" --entrypoint java "$2" \
    -cp '/migration:/migration/lib/*' Migrate
}
history() {
  sql "select version || ':' || script || ':' || checksum || ':' || success from ouf_sem.flyway_schema_history where type='SQL' order by installed_rank"
}
exercise() {
  local name="$1" id="$2" phase="$3"
  [[ "$(docker inspect --format '{{.Image}}' "$name")" == "$id" && "$(db_identity)" == "$database" ]]
  docker start "$name" >/dev/null
  note "$phase started on image $id"
  docker exec "$fixture" node /driver/scenario.mjs "$phase"
  note "$phase passed readiness and HTTP scenario"
}

create_app "$previous" "$old_id"
create_app "$candidate" "$new_id"
migrate "$tmp/old-sql" "$old_id"
old_history="$(history)"
[[ -n "$old_history" ]]
if [[ "$(git rev-parse "$PREDECESSOR_COMMIT^{commit}")" == d9f0bf9cc3ed074371a8e337ac6f833e91c2f51b ]]; then
  [[ "$(tail -1 <<<"$old_history")" == 18:V18__* ]]
fi
exercise "$previous" "$old_id" baseline
docker stop "$previous" >/dev/null
[[ "$(history)" == "$old_history" ]]
note "Predecessor seeded through $(tail -1 <<<"$old_history")"

migrate "$tmp/new-sql" "$new_id"
new_history="$(history)"
[[ "$new_history" == "$old_history"* ]]
grep -Eq '^19:V19__adoption_description.sql:-?[0-9]+:true$' <<<"$new_history"
exercise "$candidate" "$new_id" candidate
docker stop "$candidate" >/dev/null
[[ "$(history)" == "$new_history" ]]

# Restart the same container. No migration, clean, snapshot restore or SQL repair.
exercise "$previous" "$old_id" return
[[ "$(history)" == "$new_history" && "$(db_identity)" == "$database" ]]
[[ "$(sql "select count(*) from ouf_sem.approval_challenge where created_by_subject='agent'")" == 3 ]]
[[ "$(sql "select count(*) from ouf_sem.proposal_command_receipt where tenant_id='tenant-a' and principal_id='agent' and operation='ADOPT'")" == 3 ]]
note "D-080 passed through $(tail -1 <<<"$new_history") with three distinct adoptions and review challenges."
