-- A logical owner survives an execution lease and a retry wait. V24 workers
-- continue using their own functions and never acquire a lock on these rows.
CREATE TABLE ouf_sem.discovery_provider_owner (
 scope_subject text NOT NULL, provider_id text NOT NULL,
 request_id uuid NOT NULL REFERENCES ouf_sem.discovery_request ON DELETE CASCADE,
 PRIMARY KEY(scope_subject,provider_id)
);

-- As in the V12 claim, expiry consumes the original job budget. Exclude
-- subjects with another logical owner before charging a claim against a job.
CREATE FUNCTION ouf_sem.claim_discovery_owner_job(p_providers text[])
RETURNS SETOF ouf_sem.discovery_request LANGUAGE plpgsql AS $$
DECLARE job uuid;
BEGIN
 UPDATE ouf_sem.discovery_request SET state='PENDING',recovery_state='PAUSED_EXHAUSTED',
   lease_until=NULL,worker_generation=worker_generation+1
 WHERE state IN ('PENDING','RUNNING') AND recovery_state IN ('ACTIVE','RETRY_WAIT')
 AND ((attempt_count>=128 AND NOT (state='PENDING' AND recovery_state='RETRY_WAIT'
   AND last_error_code IS NOT DISTINCT FROM 'SEM_DISCOVERY_PROVIDER_SLOT_BUSY')) OR budget_deadline<=clock_timestamp())
 AND (state='PENDING' OR lease_until<=clock_timestamp());
 SELECT r.request_id INTO job FROM ouf_sem.discovery_request r
 WHERE r.recovery_state IN ('ACTIVE','RETRY_WAIT') AND r.next_attempt_at<=clock_timestamp()
 AND (r.state='PENDING' OR (r.state='RUNNING' AND r.lease_until<=clock_timestamp()))
 AND NOT EXISTS (SELECT FROM ouf_sem.discovery_provider_owner o
   JOIN ouf_sem.discovery_request owner ON owner.request_id=o.request_id
   WHERE o.scope_subject=r.created_by_subject AND o.provider_id=ANY(p_providers)
   AND o.request_id<>r.request_id AND owner.state IN ('RUNNING','PENDING'))
 ORDER BY r.created_at,r.request_id FOR UPDATE OF r SKIP LOCKED LIMIT 1;
 IF job IS NULL THEN RETURN; END IF;
 RETURN QUERY UPDATE ouf_sem.discovery_request SET state='RUNNING',recovery_state='ACTIVE',
   attempt_count=attempt_count+CASE WHEN state='PENDING' AND recovery_state='RETRY_WAIT'
     AND last_error_code='SEM_DISCOVERY_PROVIDER_SLOT_BUSY' THEN 0 ELSE 1 END,
   worker_generation=worker_generation+1,
   budget_started_at=coalesce(budget_started_at,clock_timestamp()),
   budget_deadline=coalesce(budget_deadline,clock_timestamp()+interval '24 hours'),
   lease_until=least(coalesce(budget_deadline,clock_timestamp()+interval '24 hours'),clock_timestamp()+interval '120 seconds')
 WHERE request_id=job RETURNING *;
END $$;

CREATE FUNCTION ouf_sem.bind_discovery_owner(p_job uuid,p_subject text,p_provider text)
RETURNS boolean LANGUAGE plpgsql AS $$
BEGIN
 INSERT INTO ouf_sem.discovery_provider_owner AS o VALUES(p_subject,p_provider,p_job)
 ON CONFLICT (scope_subject,provider_id) DO UPDATE SET request_id=excluded.request_id
 WHERE o.request_id=p_job OR EXISTS (
   SELECT FROM ouf_sem.discovery_request r WHERE r.request_id=o.request_id
   AND r.state IN ('FAILED','CANCELLED','SUCCEEDED'));
 IF NOT FOUND THEN RETURN false; END IF;
 -- A cancellation may arrive outside the worker. Once the old job is terminal
 -- its execution fence can expire immediately; its physical reservation survives.
 UPDATE ouf_sem.discovery_dependency d SET busy_until=clock_timestamp()
 FROM ouf_sem.discovery_request r WHERE d.scope_subject=p_subject AND d.provider_id=p_provider
 AND d.active_request=r.request_id AND r.state IN ('CANCELLED','FAILED','SUCCEEDED')
 AND d.busy_until>clock_timestamp();
 RETURN true;
END $$;

-- The V15 functions retain authority over one-shot version probes.

-- A slot timeout parks the existing logical attempt. Resume only that attempt,
-- under the new execution fence, including V15's single-use version probe.
CREATE FUNCTION ouf_sem.reserve_owner_dependency(p_job uuid,p_worker bigint,p_provider text,p_version text)
RETURNS jsonb LANGUAGE plpgsql AS $$
DECLARE token bigint;
BEGIN
 UPDATE ouf_sem.discovery_dependency d SET request_generation=p_worker,
   busy_until=least(r.lease_until,r.budget_deadline,d.budget_deadline)
 FROM ouf_sem.discovery_request r, ouf_sem.discovery_attempt a
 WHERE r.request_id=p_job AND r.worker_generation=p_worker AND r.state='RUNNING' AND r.recovery_state='ACTIVE'
 AND r.last_error_code='SEM_DISCOVERY_PROVIDER_SLOT_BUSY' AND r.created_by_subject=d.scope_subject
 AND d.provider_id=p_provider AND d.active_request=p_job AND d.request_generation=p_worker-1
 AND d.busy_until IS NULL AND d.next_attempt_at<=clock_timestamp()
 AND least(r.lease_until,r.budget_deadline,d.budget_deadline)>clock_timestamp()
 AND (a.scope_subject,a.provider_id,a.generation)=(d.scope_subject,d.provider_id,d.generation)
 AND a.request_id=p_job AND a.request_generation=d.request_generation AND a.completed_at IS NULL
 AND (d.state='ACTIVE' OR (d.state='BLOCKED' AND a.version_probe AND a.worker_version=p_version))
 RETURNING d.generation INTO token;
 IF FOUND THEN
   UPDATE ouf_sem.discovery_attempt SET request_generation=p_worker WHERE request_id=p_job
   AND provider_id=p_provider AND generation=token;
   RETURN jsonb_build_object('admitted',true,'generation',token);
 END IF;
 RETURN ouf_sem.reserve_discovery_dependency(p_job,p_worker,p_provider,p_version);
END $$;

-- One authoritative binding for this adapter in the shared owner database.
-- The capacity key excludes tenant, subject, worker and profile version.
CREATE TABLE ouf_sem.discovery_provider_capacity (
 installation text NOT NULL, logical_provider text NOT NULL, adapter text NOT NULL UNIQUE,
 profile_version text NOT NULL,
 waits bigint NOT NULL DEFAULT 0, acquisitions bigint NOT NULL DEFAULT 0,
 acquisition_micros bigint NOT NULL DEFAULT 0,
 PRIMARY KEY(installation,logical_provider)
);

-- Versions are opaque. Registration under the capacity lock establishes their
-- order and remembers retired versions so an old replica cannot roll back.
CREATE TABLE ouf_sem.discovery_capacity_version (
 adapter text NOT NULL REFERENCES ouf_sem.discovery_provider_capacity(adapter),
 profile_version text NOT NULL, revision bigint GENERATED ALWAYS AS IDENTITY,
 max_in_flight integer NOT NULL CHECK(max_in_flight BETWEEN 1 AND 32),
 slot_seconds integer NOT NULL CHECK(slot_seconds BETWEEN 1 AND 120),
 reconcile_seconds integer NOT NULL CHECK(reconcile_seconds BETWEEN slot_seconds AND 86400),
 wait_seconds integer NOT NULL CHECK(wait_seconds BETWEEN 1 AND 120),
 PRIMARY KEY(adapter,profile_version), UNIQUE(adapter,revision)
);

CREATE TABLE ouf_sem.discovery_slot_waiter (
 id uuid PRIMARY KEY, adapter text NOT NULL REFERENCES ouf_sem.discovery_provider_capacity(adapter),
 ticket bigint GENERATED ALWAYS AS IDENTITY, request_id uuid NOT NULL REFERENCES ouf_sem.discovery_request ON DELETE CASCADE,
 worker_generation bigint NOT NULL, dependency_generation bigint NOT NULL,
 started_at timestamptz NOT NULL, wait_until timestamptz NOT NULL,
 UNIQUE(adapter,ticket)
);

-- Bounded reusable cells. The reservation id is never reused. No cascading
-- deletion of a job can free an unresolved physical send.
CREATE TABLE ouf_sem.discovery_provider_slot (
 installation text NOT NULL, logical_provider text NOT NULL, cell integer NOT NULL,
 reservation uuid NOT NULL UNIQUE, request_id uuid NOT NULL, worker_generation bigint NOT NULL,
 dependency_generation bigint NOT NULL, expires_at timestamptz NOT NULL, reconcile_at timestamptz NOT NULL,
 outcome text NOT NULL CHECK(outcome IN ('RESERVED','IN_FLIGHT','UNCERTAIN','SUCCESS','KNOWN_ERROR','RECONCILED')),
 ended_at timestamptz,
 PRIMARY KEY(installation,logical_provider,cell),
 FOREIGN KEY(installation,logical_provider) REFERENCES ouf_sem.discovery_provider_capacity
);

-- Call with the capacity row locked. Idle maintenance skips scopes currently
-- admitting a send; the admission itself performs the same reconciliation.
CREATE FUNCTION ouf_sem.reconcile_discovery_slots(p_install text,p_logical text)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
 UPDATE ouf_sem.discovery_provider_slot SET outcome='UNCERTAIN'
 WHERE (installation,logical_provider)=(p_install,p_logical)
 AND outcome IN ('RESERVED','IN_FLIGHT') AND expires_at<=clock_timestamp();
 UPDATE ouf_sem.discovery_provider_slot SET outcome='RECONCILED'
 WHERE (installation,logical_provider)=(p_install,p_logical)
 AND outcome='UNCERTAIN' AND (ended_at IS NOT NULL OR reconcile_at<=clock_timestamp())
 AND expires_at<=clock_timestamp();
END $$;

CREATE FUNCTION ouf_sem.reconcile_discovery_slots()
RETURNS void LANGUAGE plpgsql AS $$
DECLARE c ouf_sem.discovery_provider_capacity;
BEGIN
 FOR c IN SELECT * FROM ouf_sem.discovery_provider_capacity ORDER BY adapter FOR UPDATE SKIP LOCKED LOOP
   PERFORM ouf_sem.reconcile_discovery_slots(c.installation,c.logical_provider);
   DELETE FROM ouf_sem.discovery_slot_waiter WHERE adapter=c.adapter AND wait_until<=clock_timestamp();
 END LOOP;
END $$;

-- Lock owner rows before checking the clock, including after any lock wait.
CREATE FUNCTION ouf_sem.discovery_owner_deadline(p_job uuid,p_worker bigint,p_provider text,p_token bigint)
RETURNS timestamptz LANGUAGE plpgsql AS $$
DECLARE deadline timestamptz;
BEGIN
 SELECT least(r.lease_until,r.budget_deadline,d.busy_until,d.budget_deadline) INTO deadline
 FROM ouf_sem.discovery_request r
 JOIN ouf_sem.discovery_dependency d ON d.scope_subject=r.created_by_subject AND d.provider_id=p_provider
 JOIN ouf_sem.discovery_provider_owner o USING(scope_subject,provider_id)
 WHERE r.request_id=p_job AND o.request_id=p_job AND d.active_request=p_job
 AND r.state='RUNNING' AND r.recovery_state='ACTIVE' AND r.worker_generation=p_worker
 AND d.request_generation=p_worker AND d.generation=p_token AND d.busy_until IS NOT NULL
 AND r.lease_until IS NOT NULL FOR UPDATE OF r,d;
 IF deadline>clock_timestamp() THEN RETURN deadline; END IF;
 RETURN NULL;
END $$;

CREATE FUNCTION ouf_sem.acquire_discovery_slot(p_job uuid,p_worker bigint,p_provider text,p_token bigint,
 p_install text,p_logical text,p_version text,p_limit integer,p_seconds integer,p_reconcile integer,
 p_wait integer,p_id uuid,p_first boolean)
RETURNS TABLE(status text,remaining_ms bigint) LANGUAGE plpgsql AS $$
DECLARE c ouf_sem.discovery_provider_capacity; target ouf_sem.discovery_capacity_version;
 waiter ouf_sem.discovery_slot_waiter; chosen integer; head uuid; deadline timestamptz;
 started timestamptz:=clock_timestamp(); checked timestamptz; cutoff timestamptz;
 draining boolean;
BEGIN
 deadline=ouf_sem.discovery_owner_deadline(p_job,p_worker,p_provider,p_token);
 IF deadline IS NULL THEN
   DELETE FROM ouf_sem.discovery_slot_waiter WHERE id=p_id AND request_id=p_job AND worker_generation=p_worker;
   RETURN QUERY SELECT 'STALE'::text,0::bigint; RETURN;
 END IF;
 INSERT INTO ouf_sem.discovery_provider_capacity(installation,logical_provider,adapter,profile_version)
 VALUES(p_install,p_logical,p_provider,p_version) ON CONFLICT DO NOTHING;
 SELECT * INTO c FROM ouf_sem.discovery_provider_capacity WHERE adapter=p_provider FOR UPDATE;
 IF deadline<=clock_timestamp() THEN RETURN QUERY SELECT 'STALE'::text,0::bigint; RETURN; END IF;
 IF NOT FOUND OR (c.installation,c.logical_provider) IS DISTINCT FROM (p_install,p_logical) THEN
   RETURN QUERY SELECT 'DRIFT'::text,0::bigint; RETURN;
 END IF;
 SELECT * INTO target FROM ouf_sem.discovery_capacity_version WHERE adapter=p_provider AND profile_version=p_version;
 IF NOT FOUND THEN
   INSERT INTO ouf_sem.discovery_capacity_version(adapter,profile_version,max_in_flight,slot_seconds,reconcile_seconds,wait_seconds)
   VALUES(p_provider,p_version,p_limit,p_seconds,p_reconcile,p_wait);
 ELSIF (target.max_in_flight,target.slot_seconds,target.reconcile_seconds,target.wait_seconds)
   IS DISTINCT FROM (p_limit,p_seconds,p_reconcile,p_wait) THEN
   RETURN QUERY SELECT 'DRIFT'::text,0::bigint; RETURN;
 END IF;
 SELECT * INTO STRICT target FROM ouf_sem.discovery_capacity_version WHERE adapter=p_provider
 ORDER BY revision DESC LIMIT 1;
 PERFORM ouf_sem.reconcile_discovery_slots(p_install,p_logical);
 draining=c.profile_version<>target.profile_version;
 IF draining AND NOT EXISTS (SELECT FROM ouf_sem.discovery_provider_slot WHERE installation=p_install
   AND logical_provider=p_logical AND outcome IN ('RESERVED','IN_FLIGHT','UNCERTAIN')) THEN
   UPDATE ouf_sem.discovery_provider_capacity SET profile_version=target.profile_version WHERE adapter=p_provider;
   draining=false;
 END IF;

 checked=clock_timestamp();
 IF deadline<=checked THEN RETURN QUERY SELECT 'STALE'::text,0::bigint; RETURN; END IF;
 DELETE FROM ouf_sem.discovery_slot_waiter w WHERE w.adapter=p_provider AND
   (w.wait_until<=checked OR NOT EXISTS (SELECT FROM ouf_sem.discovery_request r
     JOIN ouf_sem.discovery_dependency d ON d.scope_subject=r.created_by_subject AND d.provider_id=w.adapter
     WHERE r.request_id=w.request_id AND r.state='RUNNING' AND r.recovery_state='ACTIVE'
     AND r.worker_generation=w.worker_generation AND d.active_request=r.request_id
     AND d.request_generation=r.worker_generation AND d.generation=w.dependency_generation
     AND r.lease_until>checked AND d.busy_until>checked));
 SELECT * INTO waiter FROM ouf_sem.discovery_slot_waiter WHERE id=p_id AND request_id=p_job AND worker_generation=p_worker;
 IF NOT FOUND AND NOT p_first THEN RETURN QUERY SELECT 'TIMEOUT'::text,0::bigint; RETURN; END IF;
 started=coalesce(waiter.started_at,started);
 cutoff=least(waiter.wait_until,started+make_interval(secs=>target.wait_seconds),
   deadline-make_interval(secs=>target.slot_seconds));
 SELECT id INTO head FROM ouf_sem.discovery_slot_waiter WHERE adapter=p_provider ORDER BY ticket LIMIT 1;
 IF NOT draining AND (head IS NULL OR head=p_id) AND (p_first OR checked<cutoff) THEN
   SELECT n INTO chosen FROM generate_series(1,target.max_in_flight) n
   WHERE NOT EXISTS (SELECT FROM ouf_sem.discovery_provider_slot s WHERE s.installation=p_install
     AND s.logical_provider=p_logical AND s.cell=n AND s.outcome IN ('RESERVED','IN_FLIGHT','UNCERTAIN'))
   ORDER BY n LIMIT 1;
 END IF;
 checked=clock_timestamp();
 IF checked>=deadline THEN RETURN QUERY SELECT 'STALE'::text,0::bigint; RETURN; END IF;
 IF NOT p_first AND checked>=cutoff THEN chosen=NULL; END IF;
 IF chosen IS NULL THEN
   IF p_first THEN
     UPDATE ouf_sem.discovery_provider_capacity SET waits=waits+1 WHERE adapter=p_provider;
   END IF;
   IF cutoff<=clock_timestamp() THEN
     DELETE FROM ouf_sem.discovery_slot_waiter WHERE id=p_id;
     RETURN QUERY SELECT 'TIMEOUT'::text,0::bigint; RETURN;
   END IF;
   IF p_first THEN
     INSERT INTO ouf_sem.discovery_slot_waiter(id,adapter,request_id,worker_generation,dependency_generation,started_at,wait_until)
     VALUES(p_id,p_provider,p_job,p_worker,p_token,started,cutoff);
   ELSIF cutoff<waiter.wait_until THEN
     UPDATE ouf_sem.discovery_slot_waiter SET wait_until=cutoff WHERE id=p_id;
   END IF;
   RETURN QUERY SELECT 'WAIT'::text,greatest(0,floor(extract(epoch FROM cutoff-clock_timestamp())*1000)::bigint);
   RETURN;
 END IF;

 INSERT INTO ouf_sem.discovery_provider_slot(installation,logical_provider,cell,reservation,request_id,
   worker_generation,dependency_generation,expires_at,reconcile_at,outcome)
 VALUES(p_install,p_logical,chosen,p_id,p_job,p_worker,p_token,
   least(deadline,checked+make_interval(secs=>target.slot_seconds)),checked+make_interval(secs=>target.reconcile_seconds),'RESERVED')
 ON CONFLICT (installation,logical_provider,cell) DO UPDATE SET reservation=excluded.reservation,
   request_id=p_job,worker_generation=p_worker,dependency_generation=p_token,
   expires_at=excluded.expires_at,reconcile_at=excluded.reconcile_at,outcome='RESERVED',ended_at=NULL;
 DELETE FROM ouf_sem.discovery_slot_waiter WHERE id=p_id;
 UPDATE ouf_sem.discovery_provider_capacity SET acquisitions=acquisitions+1,
   acquisition_micros=acquisition_micros+greatest(0,extract(epoch FROM clock_timestamp()-started)*1000000)::bigint
 WHERE adapter=p_provider;
 RETURN QUERY SELECT 'ACQUIRED'::text,0::bigint;
END $$;

-- A known transient may have already persisted a cooldown at slot close.
-- Finalizing the incident must never shorten it, including on optional fetch.
CREATE FUNCTION ouf_sem.finish_owner_dependency(p_job uuid,p_worker bigint,p_provider text,p_token bigint,
 p_kind text,p_code text,p_delay double precision) RETURNS boolean LANGUAGE plpgsql AS $$
DECLARE not_before timestamptz;
BEGIN
 IF p_kind='TRANSIENT' THEN
   SELECT next_attempt_at INTO not_before FROM ouf_sem.discovery_dependency
   WHERE active_request=p_job AND request_generation=p_worker AND provider_id=p_provider AND generation=p_token;
   IF p_delay>2147483647 THEN not_before='infinity'; END IF;
 END IF;
 IF NOT ouf_sem.finish_discovery_dependency(p_job,p_worker,p_provider,p_token,p_kind,p_code,least(p_delay,2147483647))
 THEN RETURN false; END IF;
 IF not_before IS NOT NULL THEN
   UPDATE ouf_sem.discovery_dependency SET next_attempt_at=greatest(next_attempt_at,not_before)
   WHERE scope_subject=(SELECT created_by_subject FROM ouf_sem.discovery_request WHERE request_id=p_job)
   AND provider_id=p_provider AND generation=p_token;
 END IF;
 RETURN true;
END $$;

CREATE VIEW ouf_sem.discovery_slot_metrics AS
 SELECT 'slotOccupancy'::text AS metric,count(*)::double precision AS amount
 FROM ouf_sem.discovery_provider_slot WHERE outcome IN ('RESERVED','IN_FLIGHT','UNCERTAIN')
 UNION ALL SELECT 'slotUncertain',count(*) FROM ouf_sem.discovery_provider_slot
 WHERE outcome='UNCERTAIN' OR (outcome IN ('RESERVED','IN_FLIGHT') AND expires_at<=statement_timestamp())
 UNION ALL SELECT 'slotWaits',coalesce(sum(waits),0) FROM ouf_sem.discovery_provider_capacity
 UNION ALL SELECT 'slotAcquisitionSeconds',
   coalesce(sum(acquisition_micros)/nullif(sum(acquisitions),0)/1000000,0)
 FROM ouf_sem.discovery_provider_capacity;
