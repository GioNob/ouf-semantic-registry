-- Record the superseded budget on the attempt that actually opens the next episode.
-- Historical V14 probes used the original budget and have no episode boundary.
ALTER TABLE ouf_sem.discovery_attempt
 ADD COLUMN previous_episode_attempts integer,
 ADD COLUMN previous_budget_deadline timestamptz;

CREATE INDEX discovery_exhausted_probe_queue ON ouf_sem.discovery_dependency(provider_id,next_attempt_at)
 WHERE state='PAUSED_EXHAUSTED';

CREATE OR REPLACE FUNCTION ouf_sem.discovery_probe_allowed(d ouf_sem.discovery_dependency,p_version text)
RETURNS boolean LANGUAGE sql STABLE AS $$
 SELECT d.state IN ('BLOCKED','PAUSED_EXHAUSTED') AND d.budget_deadline IS NOT NULL AND p_version ~ '^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$'
 AND EXISTS (SELECT FROM ouf_sem.discovery_incident i WHERE i.incident_id=d.incident_id AND i.state='OPEN'
   AND i.scope_subject=d.scope_subject AND i.provider_id=d.provider_id
   AND i.opened_worker_version IS DISTINCT FROM p_version
   AND i.code IN ('PROVIDER_UNKNOWN','PROVIDER_MEDIA_TYPE_REJECTED','PROVIDER_RESPONSE_TOO_LARGE',
     'SCHEMA_GOV_SPARQL_RESULT_INVALID','PROVIDER_RETRY_AFTER_INVALID','SCHEMA_GOV_CIRCUIT_OPEN',
     'PROVIDER_HTTP_400','PROVIDER_HTTP_404','PROVIDER_HTTP_405','PROVIDER_HTTP_406',
     'PROVIDER_HTTP_409','PROVIDER_HTTP_410','PROVIDER_HTTP_411','PROVIDER_HTTP_413','PROVIDER_HTTP_414',
     'PROVIDER_HTTP_415','PROVIDER_HTTP_416','PROVIDER_HTTP_417','PROVIDER_HTTP_422','PROVIDER_HTTP_424',
     'PROVIDER_HTTP_431','PROVIDER_HTTP_501','PROVIDER_HTTP_505'))
 AND NOT EXISTS (SELECT FROM ouf_sem.discovery_attempt a WHERE a.incident_id=d.incident_id
   AND a.worker_version=p_version AND (a.version_probe OR a.outcome='BLOCKED'))
$$;

-- Idle workers may resume the original failed job only within its own remaining budget.
CREATE OR REPLACE FUNCTION ouf_sem.claim_discovery_version_probe(p_version text,p_providers text[])
RETURNS SETOF ouf_sem.discovery_request LANGUAGE plpgsql AS $$
DECLARE job uuid;
BEGIN
 SELECT r.request_id INTO job FROM ouf_sem.discovery_dependency d
 JOIN ouf_sem.discovery_attempt a ON (a.scope_subject,a.provider_id,a.generation)=(d.scope_subject,d.provider_id,d.generation)
 JOIN ouf_sem.discovery_request r ON r.request_id=a.request_id AND r.created_by_subject=d.scope_subject
 WHERE d.state IN ('BLOCKED','PAUSED_EXHAUSTED') AND d.provider_id=ANY(p_providers)
 AND d.next_attempt_at<=clock_timestamp() AND ouf_sem.discovery_probe_allowed(d,p_version)
 AND a.incident_id=d.incident_id AND a.request_generation=r.worker_generation AND (a.outcome='BLOCKED' OR (a.version_probe AND a.outcome='TRANSIENT'))
 AND r.state='FAILED' AND r.recovery_state='BLOCKED' AND r.last_error_code=a.code
 AND r.attempt_count<128 AND r.budget_deadline>clock_timestamp()
 ORDER BY r.created_at,r.request_id FOR UPDATE OF r,d SKIP LOCKED LIMIT 1;
 IF NOT FOUND THEN RETURN; END IF;
 RETURN QUERY UPDATE ouf_sem.discovery_request SET state='RUNNING',recovery_state='ACTIVE',completed_at=NULL,
   last_error_code=NULL,attempt_count=attempt_count+1,worker_generation=worker_generation+1,
   lease_until=least(budget_deadline,clock_timestamp()+interval '120 seconds')
 WHERE request_id=job RETURNING *;
END $$;

CREATE OR REPLACE FUNCTION ouf_sem.reserve_discovery_dependency(p_request uuid,p_generation bigint,p_provider text,p_version text)
RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE
 r ouf_sem.discovery_request;
 d ouf_sem.discovery_dependency;
 probe boolean := false;
 deadline timestamptz;
 token bigint;
BEGIN
 IF p_version IS NOT NULL AND p_version !~ '^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$' THEN
   RAISE EXCEPTION 'DISCOVERY_WORKER_VERSION_INVALID'; END IF;
 SELECT * INTO r FROM ouf_sem.discovery_request WHERE request_id=p_request FOR UPDATE;
 IF NOT FOUND OR r.state<>'RUNNING' OR r.worker_generation<>p_generation OR r.lease_until<=clock_timestamp()
 OR r.budget_deadline<=clock_timestamp() THEN RETURN jsonb_build_object('admitted',false,'state','STALE'); END IF;
 INSERT INTO ouf_sem.discovery_dependency(scope_subject,provider_id) VALUES(r.created_by_subject,p_provider) ON CONFLICT DO NOTHING;
 SELECT * INTO STRICT d FROM ouf_sem.discovery_dependency WHERE scope_subject=r.created_by_subject AND provider_id=p_provider FOR UPDATE;
 IF d.state IN ('BLOCKED','PAUSED_EXHAUSTED') THEN
   IF d.busy_until>clock_timestamp() THEN
     RETURN jsonb_build_object('admitted',false,'state','RETRY_WAIT','next',d.busy_until); END IF;
   probe=r.budget_deadline IS NOT NULL AND coalesce(ouf_sem.discovery_probe_allowed(d,p_version),false);
   IF NOT probe THEN RETURN jsonb_build_object('admitted',false,'state',d.state); END IF;
 ELSIF d.state<>'HEALTHY' AND (d.attempts>=128 OR d.budget_deadline<=clock_timestamp()) THEN
   UPDATE ouf_sem.discovery_dependency SET state='PAUSED_EXHAUSTED' WHERE scope_subject=d.scope_subject AND provider_id=p_provider;
   RETURN jsonb_build_object('admitted',false,'state','PAUSED_EXHAUSTED');
 END IF;
 IF d.busy_until>clock_timestamp() OR d.next_attempt_at>clock_timestamp() THEN
   RETURN jsonb_build_object('admitted',false,'state','RETRY_WAIT','next',greatest(d.busy_until,d.next_attempt_at)); END IF;
 -- Waiting for the dependency row must not consume an episode on an expired job lease.
 IF least(r.lease_until,r.budget_deadline)<=clock_timestamp() THEN
   RETURN jsonb_build_object('admitted',false,'state','STALE'); END IF;
 UPDATE ouf_sem.discovery_attempt SET completed_at=clock_timestamp(),outcome='LEASE_EXPIRED',code='PROVIDER_RESULT_UNPROVEN'
 WHERE scope_subject=d.scope_subject AND provider_id=p_provider AND generation=d.generation AND completed_at IS NULL;
 deadline=CASE WHEN probe OR d.budget_deadline IS NULL THEN clock_timestamp()+interval '24 hours' ELSE d.budget_deadline END;
 UPDATE ouf_sem.discovery_dependency SET generation=generation+1,state=CASE WHEN probe THEN 'BLOCKED' ELSE 'ACTIVE' END,
   attempts=CASE WHEN probe THEN 1 ELSE attempts+1 END,cumulative_attempts=cumulative_attempts+1,budget_deadline=deadline,
   active_request=p_request,request_generation=p_generation,busy_until=least(r.lease_until,r.budget_deadline,deadline)
 WHERE scope_subject=d.scope_subject AND provider_id=p_provider RETURNING generation INTO token;
 INSERT INTO ouf_sem.discovery_attempt(scope_subject,provider_id,generation,request_id,request_generation,incident_id,worker_version,
   version_probe,previous_episode_attempts,previous_budget_deadline)
 VALUES(d.scope_subject,p_provider,token,p_request,p_generation,d.incident_id,p_version,
   probe,CASE WHEN probe THEN d.attempts END,CASE WHEN probe THEN d.budget_deadline END);
 RETURN jsonb_build_object('admitted',true,'generation',token);
END $$;

CREATE OR REPLACE FUNCTION ouf_sem.finish_discovery_dependency(p_request uuid,p_generation bigint,p_provider text,p_token bigint,p_kind text,p_code text,p_retry_seconds double precision)
RETURNS boolean LANGUAGE plpgsql AS $$
DECLARE r ouf_sem.discovery_request; d ouf_sem.discovery_dependency; delay double precision; incident uuid; a ouf_sem.discovery_attempt;
 incident_attempts integer;
BEGIN
 IF p_kind IS NULL OR p_retry_seconds IS NULL OR p_kind NOT IN ('SUCCESS','TRANSIENT','BLOCKED','CANCELLED') OR p_retry_seconds<0 OR p_retry_seconds='Infinity'::float8 OR p_retry_seconds='NaN'::float8 THEN
  RAISE EXCEPTION 'DISCOVERY_OUTCOME_INVALID'; END IF;
 SELECT * INTO r FROM ouf_sem.discovery_request WHERE request_id=p_request FOR UPDATE;
 IF NOT FOUND OR r.state<>'RUNNING' OR r.worker_generation<>p_generation OR r.lease_until<=clock_timestamp()
 OR r.budget_deadline<=clock_timestamp() THEN RETURN false; END IF;
 SELECT * INTO d FROM ouf_sem.discovery_dependency WHERE scope_subject=r.created_by_subject AND provider_id=p_provider FOR UPDATE;
 IF NOT FOUND OR d.generation<>p_token OR d.active_request IS DISTINCT FROM p_request OR d.request_generation<>p_generation
 OR d.busy_until<=clock_timestamp() THEN RETURN false; END IF;
 SELECT * INTO STRICT a FROM ouf_sem.discovery_attempt WHERE scope_subject=d.scope_subject
   AND provider_id=p_provider AND generation=p_token;
 incident=d.incident_id;
 incident_attempts=d.attempts;
 IF a.version_probe THEN
  -- The incident spans episodes, even when a probe worker loses its lease.
  SELECT d.attempts+coalesce(sum(previous_episode_attempts),0) INTO incident_attempts
  FROM ouf_sem.discovery_attempt WHERE incident_id=incident AND version_probe;
 END IF;
 IF p_kind='SUCCESS' THEN
  UPDATE ouf_sem.discovery_incident SET state='RESOLVED',resolved_at=clock_timestamp(),last_seen_at=clock_timestamp(),attempts=incident_attempts WHERE incident_id=incident;
  UPDATE ouf_sem.discovery_dependency SET state='HEALTHY',attempts=0,budget_deadline=NULL,next_attempt_at=clock_timestamp(),
   busy_until=NULL,active_request=NULL,request_generation=NULL,incident_id=NULL WHERE scope_subject=d.scope_subject AND provider_id=p_provider;
 ELSE
  -- No exception text, endpoint, query or credential is accepted as an incident code.
  IF p_code IS NULL OR p_code !~ '^[A-Z][A-Z0-9_]{0,79}$' THEN RAISE EXCEPTION 'DISCOVERY_CODE_INVALID'; END IF;
  IF p_kind<>'CANCELLED' THEN
   IF incident IS NULL THEN
    incident=gen_random_uuid();
    INSERT INTO ouf_sem.discovery_incident(incident_id,scope_subject,provider_id,state,code,attempts,opened_worker_version)
     VALUES(incident,d.scope_subject,p_provider,'OPEN',p_code,d.attempts,a.worker_version);
   ELSE UPDATE ouf_sem.discovery_incident SET last_seen_at=clock_timestamp(),code=CASE WHEN a.version_probe AND p_kind='TRANSIENT' THEN code ELSE p_code END,attempts=incident_attempts WHERE incident_id=incident; END IF;
  END IF;
  -- Positive jitter never shortens Retry-After; maximum base is 900 seconds.
  delay=greatest(p_retry_seconds,(CASE d.attempts WHEN 1 THEN 5 WHEN 2 THEN 15 WHEN 3 THEN 60 WHEN 4 THEN 300 ELSE 900 END)*(1+random()*0.2));
  UPDATE ouf_sem.discovery_dependency SET state=CASE
    WHEN p_kind='BLOCKED' THEN 'BLOCKED'
    WHEN p_kind='CANCELLED' AND NOT a.version_probe THEN 'RETRY_WAIT'
    WHEN d.attempts>=128 OR clock_timestamp()+make_interval(secs=>delay)>=d.budget_deadline THEN 'PAUSED_EXHAUSTED'
    WHEN a.version_probe THEN 'BLOCKED'
    ELSE 'RETRY_WAIT' END,
   next_attempt_at=clock_timestamp()+make_interval(secs=>delay),busy_until=NULL,active_request=NULL,request_generation=NULL,incident_id=incident
   WHERE scope_subject=d.scope_subject AND provider_id=p_provider;
 END IF;
 UPDATE ouf_sem.discovery_attempt SET completed_at=clock_timestamp(),outcome=p_kind,code=p_code,incident_id=incident
 WHERE scope_subject=d.scope_subject AND provider_id=p_provider AND generation=p_token;
 RETURN true;
END $$;
