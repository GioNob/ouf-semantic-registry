-- OUF resilience v3. Server time, short transactions and persistent generations.
ALTER TABLE ouf_sem.discovery_request
 ADD COLUMN worker_generation bigint NOT NULL DEFAULT 0,
 ADD COLUMN recovery_state text NOT NULL DEFAULT 'ACTIVE' CHECK(recovery_state IN ('ACTIVE','RETRY_WAIT','PAUSED_EXHAUSTED','BLOCKED','CANCELLED')),
 ADD COLUMN next_attempt_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
 ADD COLUMN budget_started_at timestamptz,
 ADD COLUMN budget_deadline timestamptz;
CREATE TABLE ouf_sem.discovery_dependency (
 scope_subject text NOT NULL, provider_id text NOT NULL,
 generation bigint NOT NULL DEFAULT 0, state text NOT NULL DEFAULT 'HEALTHY'
 CHECK(state IN ('HEALTHY','ACTIVE','RETRY_WAIT','PAUSED_EXHAUSTED','BLOCKED')),
 attempts integer NOT NULL DEFAULT 0, cumulative_attempts bigint NOT NULL DEFAULT 0,
 budget_deadline timestamptz, next_attempt_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
 active_request uuid, request_generation bigint, busy_until timestamptz, incident_id uuid,
 PRIMARY KEY(scope_subject,provider_id));
CREATE TABLE ouf_sem.discovery_incident (
 incident_id uuid PRIMARY KEY, scope_subject text NOT NULL, provider_id text NOT NULL,
 state text NOT NULL CHECK(state IN ('OPEN','RESOLVED')), code text NOT NULL,
 first_seen_at timestamptz NOT NULL DEFAULT transaction_timestamp(), last_seen_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
 attempts integer NOT NULL, resolved_at timestamptz);
CREATE UNIQUE INDEX discovery_one_open_incident ON ouf_sem.discovery_incident(scope_subject,provider_id) WHERE state='OPEN';
CREATE TABLE ouf_sem.discovery_attempt (
 scope_subject text NOT NULL, provider_id text NOT NULL, generation bigint NOT NULL,
 request_id uuid NOT NULL REFERENCES ouf_sem.discovery_request, request_generation bigint NOT NULL,
 started_at timestamptz NOT NULL DEFAULT transaction_timestamp(), completed_at timestamptz,
 outcome text, code text, incident_id uuid REFERENCES ouf_sem.discovery_incident,
 PRIMARY KEY(scope_subject,provider_id,generation));

CREATE OR REPLACE FUNCTION ouf_sem.claim_discovery_job(p_worker text,p_lease_seconds integer)
RETURNS SETOF ouf_sem.discovery_request LANGUAGE plpgsql AS $$
DECLARE v_id uuid;
BEGIN
 IF p_worker IS NULL OR p_worker='' OR p_lease_seconds NOT BETWEEN 1 AND 120 THEN
  RAISE EXCEPTION 'DISCOVERY_LEASE_INVALID'; END IF;
 UPDATE ouf_sem.discovery_request SET state='PENDING',recovery_state='PAUSED_EXHAUSTED',lease_until=NULL,worker_generation=worker_generation+1
 WHERE state IN ('PENDING','RUNNING') AND recovery_state IN ('ACTIVE','RETRY_WAIT')
 AND (attempt_count>=128 OR budget_deadline<=clock_timestamp())
 AND (state='PENDING' OR lease_until<=clock_timestamp());
 SELECT request_id INTO v_id FROM ouf_sem.discovery_request
 WHERE recovery_state IN ('ACTIVE','RETRY_WAIT') AND next_attempt_at<=clock_timestamp()
 AND (state='PENDING' OR (state='RUNNING' AND lease_until<=clock_timestamp()))
 ORDER BY created_at,request_id FOR UPDATE SKIP LOCKED LIMIT 1;
 IF v_id IS NULL THEN RETURN; END IF;
 RETURN QUERY UPDATE ouf_sem.discovery_request SET state='RUNNING',recovery_state='ACTIVE',
 attempt_count=attempt_count+1,worker_generation=worker_generation+1,
 budget_started_at=coalesce(budget_started_at,clock_timestamp()),
 budget_deadline=coalesce(budget_deadline,clock_timestamp()+interval '24 hours'),
 lease_until=clock_timestamp()+make_interval(secs=>p_lease_seconds)
 WHERE request_id=v_id RETURNING *;
END $$;
-- The old unversioned completion would defeat the new publication fence.
CREATE OR REPLACE FUNCTION ouf_sem.complete_discovery_job(p_request uuid,p_success boolean,p_error text)
RETURNS void LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'DISCOVERY_GENERATION_REQUIRED'; END $$;

CREATE FUNCTION ouf_sem.reserve_discovery_dependency(p_request uuid,p_generation bigint,p_provider text)
RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE r ouf_sem.discovery_request; d ouf_sem.discovery_dependency;
BEGIN
 SELECT * INTO r FROM ouf_sem.discovery_request WHERE request_id=p_request FOR UPDATE;
 IF NOT FOUND OR r.state<>'RUNNING' OR r.worker_generation<>p_generation OR r.lease_until<=clock_timestamp()
 OR r.budget_deadline<=clock_timestamp() THEN RETURN jsonb_build_object('admitted',false,'state','STALE'); END IF;
 INSERT INTO ouf_sem.discovery_dependency(scope_subject,provider_id) VALUES(r.created_by_subject,p_provider) ON CONFLICT DO NOTHING;
 SELECT * INTO d FROM ouf_sem.discovery_dependency WHERE scope_subject=r.created_by_subject AND provider_id=p_provider FOR UPDATE;
 IF d.state IN ('PAUSED_EXHAUSTED','BLOCKED') THEN
  RETURN jsonb_build_object('admitted',false,'state',d.state); END IF;
 IF d.state<>'HEALTHY' AND (d.attempts>=128 OR d.budget_deadline<=clock_timestamp()) THEN
  UPDATE ouf_sem.discovery_dependency SET state='PAUSED_EXHAUSTED' WHERE scope_subject=d.scope_subject AND provider_id=p_provider;
  RETURN jsonb_build_object('admitted',false,'state','PAUSED_EXHAUSTED'); END IF;
 IF d.busy_until>clock_timestamp() OR d.next_attempt_at>clock_timestamp() THEN
  RETURN jsonb_build_object('admitted',false,'state','RETRY_WAIT','next',greatest(d.busy_until,d.next_attempt_at)); END IF;
 -- A dead process cannot replenish attempts or authorize a late result.
 UPDATE ouf_sem.discovery_attempt SET completed_at=clock_timestamp(),outcome='LEASE_EXPIRED',code='PROVIDER_RESULT_UNPROVEN'
 WHERE scope_subject=d.scope_subject AND provider_id=p_provider AND generation=d.generation AND completed_at IS NULL;
 UPDATE ouf_sem.discovery_dependency SET generation=generation+1,state='ACTIVE',attempts=attempts+1,
 cumulative_attempts=cumulative_attempts+1,budget_deadline=coalesce(budget_deadline,clock_timestamp()+interval '24 hours'),
 active_request=p_request,request_generation=p_generation,busy_until=least(r.lease_until,coalesce(budget_deadline,clock_timestamp()+interval '24 hours'))
 WHERE scope_subject=d.scope_subject AND provider_id=p_provider RETURNING * INTO d;
 INSERT INTO ouf_sem.discovery_attempt(scope_subject,provider_id,generation,request_id,request_generation,incident_id)
 VALUES(d.scope_subject,p_provider,d.generation,p_request,p_generation,d.incident_id);
 RETURN jsonb_build_object('admitted',true,'generation',d.generation);
END $$;

CREATE FUNCTION ouf_sem.finish_discovery_dependency(p_request uuid,p_generation bigint,p_provider text,p_token bigint,p_kind text,p_code text,p_retry_seconds double precision)
RETURNS boolean LANGUAGE plpgsql AS $$
DECLARE r ouf_sem.discovery_request; d ouf_sem.discovery_dependency; delay double precision; incident uuid;
BEGIN
 IF p_kind IS NULL OR p_retry_seconds IS NULL OR p_kind NOT IN ('SUCCESS','TRANSIENT','BLOCKED','CANCELLED') OR p_retry_seconds<0 OR p_retry_seconds='Infinity'::float8 OR p_retry_seconds='NaN'::float8 THEN
  RAISE EXCEPTION 'DISCOVERY_OUTCOME_INVALID'; END IF;
 SELECT * INTO r FROM ouf_sem.discovery_request WHERE request_id=p_request FOR UPDATE;
 IF NOT FOUND OR r.state<>'RUNNING' OR r.worker_generation<>p_generation OR r.lease_until<=clock_timestamp()
 OR r.budget_deadline<=clock_timestamp() THEN RETURN false; END IF;
 SELECT * INTO d FROM ouf_sem.discovery_dependency WHERE scope_subject=r.created_by_subject AND provider_id=p_provider FOR UPDATE;
 IF NOT FOUND OR d.generation<>p_token OR d.active_request IS DISTINCT FROM p_request OR d.request_generation<>p_generation
 OR d.busy_until<=clock_timestamp() THEN RETURN false; END IF;
 incident=d.incident_id;
 IF p_kind='SUCCESS' THEN
  UPDATE ouf_sem.discovery_incident SET state='RESOLVED',resolved_at=clock_timestamp(),last_seen_at=clock_timestamp(),attempts=d.attempts WHERE incident_id=incident;
  UPDATE ouf_sem.discovery_dependency SET state='HEALTHY',attempts=0,budget_deadline=NULL,next_attempt_at=clock_timestamp(),
   busy_until=NULL,active_request=NULL,request_generation=NULL,incident_id=NULL WHERE scope_subject=d.scope_subject AND provider_id=p_provider;
 ELSE
  -- No exception text, endpoint, query or credential is accepted as an incident code.
  IF p_code IS NULL OR p_code !~ '^[A-Z][A-Z0-9_]{0,79}$' THEN RAISE EXCEPTION 'DISCOVERY_CODE_INVALID'; END IF;
  IF p_kind<>'CANCELLED' THEN
   IF incident IS NULL THEN
    incident=gen_random_uuid();
    INSERT INTO ouf_sem.discovery_incident(incident_id,scope_subject,provider_id,state,code,attempts)
     VALUES(incident,d.scope_subject,p_provider,'OPEN',p_code,d.attempts);
   ELSE UPDATE ouf_sem.discovery_incident SET last_seen_at=clock_timestamp(),code=p_code,attempts=d.attempts WHERE incident_id=incident; END IF;
  END IF;
  -- Positive jitter never shortens Retry-After; maximum base is 900 seconds.
  delay=greatest(p_retry_seconds,(CASE d.attempts WHEN 1 THEN 5 WHEN 2 THEN 15 WHEN 3 THEN 60 WHEN 4 THEN 300 ELSE 900 END)*(1+random()*0.2));
  UPDATE ouf_sem.discovery_dependency SET state=CASE
    WHEN p_kind='BLOCKED' THEN 'BLOCKED'
    WHEN p_kind='CANCELLED' THEN 'RETRY_WAIT'
    WHEN d.attempts>=128 OR clock_timestamp()+make_interval(secs=>delay)>=d.budget_deadline THEN 'PAUSED_EXHAUSTED'
    ELSE 'RETRY_WAIT' END,
   next_attempt_at=clock_timestamp()+make_interval(secs=>delay),busy_until=NULL,active_request=NULL,request_generation=NULL,incident_id=incident
   WHERE scope_subject=d.scope_subject AND provider_id=p_provider;
 END IF;
 UPDATE ouf_sem.discovery_attempt SET completed_at=clock_timestamp(),outcome=p_kind,code=p_code,incident_id=incident
 WHERE scope_subject=d.scope_subject AND provider_id=p_provider AND generation=p_token;
 RETURN true;
END $$;

CREATE FUNCTION ouf_sem.finish_discovery_job(p_request uuid,p_generation bigint,p_outcome text,p_code text,p_candidates jsonb,p_next timestamptz DEFAULT NULL)
RETURNS boolean LANGUAGE plpgsql AS $$
DECLARE r ouf_sem.discovery_request; c jsonb; next_time timestamptz;
BEGIN
 SELECT * INTO r FROM ouf_sem.discovery_request WHERE request_id=p_request FOR UPDATE;
 IF NOT FOUND OR r.state<>'RUNNING' OR r.worker_generation<>p_generation OR r.lease_until<=clock_timestamp()
 OR r.budget_deadline<=clock_timestamp() THEN RETURN false; END IF;
 IF p_outcome IS NULL OR p_outcome NOT IN ('SUCCESS','RETRY_WAIT','PAUSED_EXHAUSTED','BLOCKED','CANCELLED') THEN RAISE EXCEPTION 'DISCOVERY_OUTCOME_INVALID'; END IF;
 IF p_outcome='SUCCESS' THEN
  IF p_candidates IS NULL OR jsonb_typeof(p_candidates)<>'array' OR jsonb_array_length(p_candidates)>256 THEN RAISE EXCEPTION 'DISCOVERY_CANDIDATES_INVALID'; END IF;
  FOR c IN SELECT value FROM jsonb_array_elements(p_candidates) LOOP
   INSERT INTO ouf_sem.discovery_candidate(candidate_id,request_id,provider_id,canonical_uri,source_location,artifact_type,provider_trust,score,match_reasons,gaps,normalized_payload,content_hash,media_type,content_bytes,expires_at)
   VALUES(gen_random_uuid(),p_request,c->>'provider',c->>'uri',c->>'source',c->>'type',c->>'trust',(c->>'score')::numeric,c->'reasons',c->'gaps','{}',c->>'hash',c->>'mediaType',decode(c->>'bytes','base64'),clock_timestamp()+interval '24 hours');
  END LOOP;
  UPDATE ouf_sem.discovery_request SET state='SUCCEEDED',completed_at=clock_timestamp(),lease_until=NULL,last_error_code=NULL WHERE request_id=p_request;
 ELSE
  next_time=coalesce(p_next,clock_timestamp()+interval '5 seconds');
  UPDATE ouf_sem.discovery_request SET
   state=CASE WHEN p_outcome='CANCELLED' THEN 'CANCELLED' WHEN p_outcome='BLOCKED' THEN 'FAILED' ELSE 'PENDING' END,
   recovery_state=CASE WHEN p_outcome='RETRY_WAIT' AND (r.attempt_count>=128 OR next_time>=r.budget_deadline) THEN 'PAUSED_EXHAUSTED' ELSE p_outcome END,
   next_attempt_at=next_time,lease_until=NULL,last_error_code=p_code,
   completed_at=CASE WHEN p_outcome IN ('BLOCKED','CANCELLED') THEN clock_timestamp() ELSE NULL END
  WHERE request_id=p_request;
 END IF;
 RETURN true;
END $$;
