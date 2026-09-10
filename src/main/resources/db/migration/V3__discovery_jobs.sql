CREATE TABLE ouf_sem.discovery_request(
 request_id uuid PRIMARY KEY,
 requested_artifact_type varchar(32) NOT NULL CHECK(requested_artifact_type IN('CLASS','PROPERTY','RELATIONSHIP','VOCABULARY','CONCEPT','ONTOLOGY')),
 intent text NOT NULL,
 preferred_languages text[] NOT NULL DEFAULT '{}',
 provider_policy jsonb NOT NULL DEFAULT '{}',
 state varchar(20) NOT NULL CHECK(state IN('PENDING','RUNNING','SUCCEEDED','FAILED','CANCELLED')),
 attempt_count integer NOT NULL DEFAULT 0 CHECK(attempt_count>=0),
 lease_until timestamptz,
 last_error_code text,
 created_by_subject text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
 completed_at timestamptz);

CREATE INDEX discovery_request_recovery_idx ON ouf_sem.discovery_request(state,lease_until)
 WHERE state IN('PENDING','RUNNING');

CREATE TABLE ouf_sem.discovery_candidate(
 candidate_id uuid PRIMARY KEY,
 request_id uuid NOT NULL REFERENCES ouf_sem.discovery_request ON DELETE CASCADE,
 provider_id text NOT NULL,
 canonical_uri text NOT NULL,
 source_location text NOT NULL,
 artifact_type varchar(32) NOT NULL,
 provider_trust varchar(16) NOT NULL CHECK(provider_trust IN('HIGH','MEDIUM','LOW')),
 score numeric(6,5) NOT NULL CHECK(score>=0 AND score<=1),
 match_reasons jsonb NOT NULL DEFAULT '[]',
 gaps jsonb NOT NULL DEFAULT '[]',
 normalized_payload jsonb NOT NULL,
 content_hash char(64) NOT NULL CHECK(content_hash ~ '^[0-9a-f]{64}$'),
 media_type text NOT NULL,
 content_bytes bytea NOT NULL,
 expires_at timestamptz NOT NULL,
 adopted_at timestamptz,
 UNIQUE(request_id,provider_id,canonical_uri,content_hash));

CREATE FUNCTION ouf_sem.claim_discovery_job(p_worker text,p_lease_seconds integer)
RETURNS SETOF ouf_sem.discovery_request LANGUAGE plpgsql AS $$
DECLARE v_id uuid;
BEGIN
 SELECT request_id INTO v_id FROM ouf_sem.discovery_request
 WHERE state='PENDING' OR (state='RUNNING' AND lease_until<transaction_timestamp())
 ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1;
 IF v_id IS NULL THEN RETURN; END IF;
 RETURN QUERY UPDATE ouf_sem.discovery_request SET state='RUNNING',attempt_count=attempt_count+1,
   lease_until=transaction_timestamp()+make_interval(secs=>p_lease_seconds)
 WHERE request_id=v_id RETURNING *;
END $$;

CREATE FUNCTION ouf_sem.complete_discovery_job(p_request uuid,p_success boolean,p_error text)
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
 UPDATE ouf_sem.discovery_request SET state=CASE WHEN p_success THEN 'SUCCEEDED' ELSE 'FAILED' END,
   last_error_code=p_error,lease_until=NULL,completed_at=transaction_timestamp()
 WHERE request_id=p_request AND state='RUNNING';
 IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='40001',MESSAGE='DISCOVERY_JOB_CAS_MISMATCH'; END IF;
END $$;

CREATE TRIGGER adopted_candidate_bytes_immutable BEFORE UPDATE OR DELETE ON ouf_sem.discovery_candidate
FOR EACH ROW WHEN(OLD.adopted_at IS NOT NULL) EXECUTE FUNCTION ouf_sem.enforce_immutable();
