ALTER TABLE ouf_sem.discovery_request
 ADD COLUMN fetch_denied_count integer NOT NULL DEFAULT 0 CHECK(fetch_denied_count BETWEEN 0 AND 256);

-- The five-argument publisher remains callable by 1.0.2. Its generation/lease
-- check, candidate inserts and all three counters share the caller's transaction.
CREATE FUNCTION ouf_sem.publish_discovery_candidates(p_request uuid,p_generation bigint,p_candidates jsonb,
 p_invalid integer,p_bound integer,p_fetch_denied integer) RETURNS boolean LANGUAGE plpgsql AS $$
BEGIN
 IF NOT ouf_sem.publish_discovery_candidates(p_request,p_generation,p_candidates,p_invalid,p_bound) THEN RETURN false; END IF;
 UPDATE ouf_sem.discovery_request SET fetch_denied_count=p_fetch_denied WHERE request_id=p_request;
 RETURN true;
END $$;
