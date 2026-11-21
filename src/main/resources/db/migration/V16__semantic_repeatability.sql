-- V2 stored only the payload hash. Bind historical claims only where the publication
-- event, manifest member and timely approval prove one revision/decision pair.
ALTER TABLE ouf_sem.publish_claim
 ADD COLUMN revision_id uuid REFERENCES ouf_sem.artifact_revision DEFERRABLE INITIALLY DEFERRED,
 ADD COLUMN decision_id uuid REFERENCES ouf_sem.approval_decision DEFERRABLE INITIALLY DEFERRED;

CREATE INDEX publication_event_revision_idx ON ouf_sem.audit_event(resource_id)
 WHERE event_type='SEMANTIC_PUBLISHED' AND resource_type='REVISION';
CREATE INDEX adopted_candidate_artifact_idx ON ouf_sem.discovery_candidate(adopted_artifact_id)
 WHERE adopted_artifact_id IS NOT NULL;
CREATE INDEX review_challenge_revision_idx ON ouf_sem.approval_challenge(revision_id)
 WHERE status IN ('OPEN','APPROVED');

WITH publication_events AS (
 SELECT resource_id,detail_json->>'publicationSetId' set_id,occurred_at,
        count(*) OVER (PARTITION BY detail_json->>'publicationSetId') events
 FROM ouf_sem.audit_event WHERE event_type='SEMANTIC_PUBLISHED' AND resource_type='REVISION'
), legacy_claims AS (
 SELECT k.*,count(*) OVER (PARTITION BY publication_set_id) claim_count
 FROM ouf_sem.publish_claim k WHERE publication_set_id IS NOT NULL
), evidence AS (
 SELECT k.idempotency_key,m.revision_id,d.decision_id,
        count(*) OVER (PARTITION BY k.idempotency_key) AS matches
 FROM legacy_claims k
 JOIN ouf_sem.semantic_publication_set s ON s.publication_set_id=k.publication_set_id AND s.status='PUBLISHED'
 JOIN publication_events e ON e.events=1 AND e.set_id=s.publication_set_id::text
 JOIN ouf_sem.semantic_publication_member m ON m.publication_set_id=s.publication_set_id AND m.revision_id::text=e.resource_id
 JOIN ouf_sem.approval_challenge c ON c.revision_id=m.revision_id AND c.target_content_hash=k.request_hash AND c.status='APPROVED'
 JOIN ouf_sem.approval_decision d ON d.challenge_id=c.challenge_id AND d.decision='APPROVED'
  AND d.target_content_hash=k.request_hash AND d.decided_at<=c.expires_at AND d.decided_at<=e.occurred_at
 WHERE k.claim_count=1
)
UPDATE ouf_sem.publish_claim k SET revision_id=e.revision_id,decision_id=e.decision_id
 FROM evidence e WHERE e.matches=1 AND k.idempotency_key=e.idempotency_key;

-- The deferred foreign keys above must be checked before altering the table again.
SET CONSTRAINTS ALL IMMEDIATE;
-- Unprovable legacy claims retain their evidence and cannot be reused.
ALTER TABLE ouf_sem.publish_claim ADD CONSTRAINT publish_claim_intent_required
 CHECK(revision_id IS NOT NULL AND decision_id IS NOT NULL) NOT VALID;

CREATE OR REPLACE FUNCTION ouf_sem.publish_revision(
 p_revision uuid,p_decision uuid,p_key text,p_request_hash char(64),p_actor text,p_correlation text)
RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE v_art uuid; v_sem text; v_set uuid; v_claim ouf_sem.publish_claim;
 v_inserted int; v_approved char(64); v_no bigint; v_manifest_hash char(64);
BEGIN
 INSERT INTO ouf_sem.publish_claim(idempotency_key,request_hash,revision_id,decision_id)
 VALUES(p_key,p_request_hash,p_revision,p_decision) ON CONFLICT(idempotency_key) DO NOTHING;
 GET DIAGNOSTICS v_inserted=ROW_COUNT;
 IF v_inserted=0 THEN
  SELECT * INTO STRICT v_claim FROM ouf_sem.publish_claim WHERE idempotency_key=p_key FOR UPDATE;
  IF v_claim.revision_id IS NULL OR v_claim.decision_id IS NULL OR v_claim.publication_set_id IS NULL THEN
   RAISE EXCEPTION USING ERRCODE='P1502',MESSAGE='PUBLICATION_RECONCILIATION_REQUIRED';
  END IF;
  IF (v_claim.revision_id,v_claim.decision_id,v_claim.request_hash)
     IS DISTINCT FROM (p_revision,p_decision,p_request_hash) THEN
   RAISE EXCEPTION USING ERRCODE='P1501',MESSAGE='PUBLICATION_IDEMPOTENCY_CONFLICT';
  END IF;
  RETURN v_claim.publication_set_id;
 END IF;
 SELECT d.target_content_hash INTO STRICT v_approved
 FROM ouf_sem.approval_decision d JOIN ouf_sem.approval_challenge c USING(challenge_id)
 WHERE d.decision_id=p_decision AND d.decision='APPROVED' AND c.status='APPROVED'
   AND c.revision_id=p_revision AND c.target_content_hash=d.target_content_hash AND c.expires_at>=d.decided_at FOR SHARE OF d,c;
 IF v_approved<>p_request_hash THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='APPROVAL_STALE'; END IF;

 SELECT r.artifact_id,a.semantic_id INTO STRICT v_art,v_sem
 FROM ouf_sem.artifact_revision r JOIN ouf_sem.semantic_artifact a USING(artifact_id)
 WHERE r.revision_id=p_revision AND r.lifecycle_status='UNDER_REVIEW' AND r.content_hash=p_request_hash FOR UPDATE OF r;
 IF EXISTS(SELECT 1 FROM ouf_sem.semantic_dependency d LEFT JOIN ouf_sem.semantic_artifact a ON a.semantic_id=d.target_semantic_id WHERE d.source_revision_id=p_revision AND a.artifact_id IS NULL)
 THEN RAISE EXCEPTION USING ERRCODE='23503',MESSAGE='UNRESOLVED_DEPENDENCY'; END IF;

 v_set=gen_random_uuid(); v_no=nextval('ouf_sem.publication_no_seq');
 -- The request hash identifies the revision payload and belongs to the claim.
 -- The publication checksum identifies the complete ordered manifest.  A
 -- provisional value is required while the BUILDING row has no members yet.
 INSERT INTO ouf_sem.semantic_publication_set
 VALUES(v_set,v_no,encode(public.digest(v_set::text::bytea,'sha256'),'hex'),transaction_timestamp(),p_actor,'BUILDING');
 INSERT INTO ouf_sem.semantic_publication_member(publication_set_id,semantic_id,revision_id)
 SELECT v_set,a.semantic_id,ar.revision_id FROM ouf_sem.artifact_active_revision ar JOIN ouf_sem.semantic_artifact a USING(artifact_id) WHERE ar.artifact_id<>v_art;
 INSERT INTO ouf_sem.semantic_publication_member VALUES(v_set,v_sem,p_revision);
 UPDATE ouf_sem.artifact_revision SET lifecycle_status='ACTIVE',published_at=transaction_timestamp() WHERE revision_id=p_revision;
 INSERT INTO ouf_sem.artifact_active_revision VALUES(v_art,p_revision,transaction_timestamp(),p_actor)
 ON CONFLICT(artifact_id) DO UPDATE SET revision_id=excluded.revision_id,activated_at=excluded.activated_at,activated_by_subject=excluded.activated_by_subject;
 SELECT encode(public.digest(string_agg(m.semantic_id||':'||m.revision_id::text,'|' ORDER BY m.semantic_id)::bytea,'sha256'),'hex')
 INTO STRICT v_manifest_hash
 FROM ouf_sem.semantic_publication_member m WHERE m.publication_set_id=v_set;
 UPDATE ouf_sem.semantic_publication_set SET checksum=v_manifest_hash,status='PUBLISHED' WHERE publication_set_id=v_set;
 UPDATE ouf_sem.publish_claim SET publication_set_id=v_set WHERE idempotency_key=p_key;
 INSERT INTO ouf_sem.audit_event VALUES(gen_random_uuid(),'SEMANTIC_PUBLISHED',p_actor,'REVISION',p_revision::text,p_correlation,jsonb_build_object('publicationSetId',v_set),transaction_timestamp());
 RETURN v_set;
END $$;

-- Pre-V16 OPEN challenges follow the same lazy transition as new ones. The
-- revision lock serializes preparation with decisions. Never renew an old TTL.
CREATE FUNCTION ouf_sem.expire_review(p_revision uuid,p_version bigint,p_actor text)
RETURNS boolean LANGUAGE plpgsql AS $$
DECLARE expired_id uuid;
BEGIN
 PERFORM 1 FROM ouf_sem.artifact_revision WHERE revision_id=p_revision
   AND row_version=p_version AND lifecycle_status='UNDER_REVIEW' FOR UPDATE;
 IF NOT FOUND THEN RETURN false; END IF;
 UPDATE ouf_sem.approval_challenge c SET status='EXPIRED'
 WHERE c.revision_id=p_revision AND c.status='OPEN' AND c.expires_at<=clock_timestamp()
   AND c.target_content_hash=(SELECT content_hash FROM ouf_sem.artifact_revision WHERE revision_id=p_revision)
   AND NOT EXISTS(SELECT 1 FROM ouf_sem.approval_decision d WHERE d.challenge_id=c.challenge_id)
   AND NOT EXISTS(SELECT 1 FROM ouf_sem.approval_challenge other WHERE other.revision_id=p_revision
                  AND other.challenge_id<>c.challenge_id AND other.status IN ('OPEN','APPROVED'))
 RETURNING c.challenge_id INTO expired_id;
 IF NOT FOUND THEN RETURN false; END IF;
 UPDATE ouf_sem.artifact_revision SET lifecycle_status='DRAFT',row_version=row_version+1
 WHERE revision_id=p_revision;
 INSERT INTO ouf_sem.audit_event(event_id,event_type,subject_ref,resource_type,resource_id,detail_json)
 VALUES(gen_random_uuid(),'SEMANTIC_APPROVAL_EXPIRED',p_actor,'APPROVAL_CHALLENGE',expired_id::text,
        jsonb_build_object('revisionId',p_revision,'rowVersion',p_version+1));
 RETURN true;
END $$;

-- V13 owns draft creation and immutable evidence. A unique collision can also
-- come from a concurrent insert. The subtransaction rolls back partial effects
-- before inspecting the committed winner in a fresh statement.
CREATE FUNCTION ouf_sem.adopt_or_find_candidate(p_candidate uuid,p_uri text,p_namespace text,p_name text,
 p_actor text,p_publisher text,p_license text,p_definition jsonb)
RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE artifact uuid; conflict_table text; conflict_constraint text;
BEGIN
 SELECT artifact_id INTO artifact FROM ouf_sem.semantic_artifact WHERE semantic_id=p_uri;
 IF FOUND THEN RETURN artifact; END IF;
 BEGIN
  RETURN ouf_sem.adopt_candidate(p_candidate,p_uri,p_namespace,p_name,p_actor,p_publisher,
                                 p_actor,p_publisher,p_license,p_definition);
 EXCEPTION WHEN unique_violation THEN
  GET STACKED DIAGNOSTICS conflict_table=TABLE_NAME,conflict_constraint=CONSTRAINT_NAME;
  IF conflict_table NOT IN ('semantic_artifact','external_semantic_origin') OR
     conflict_constraint IN ('semantic_artifact_pkey','external_semantic_origin_pkey') THEN RAISE; END IF;
  SELECT artifact_id INTO artifact FROM ouf_sem.semantic_artifact WHERE semantic_id=p_uri;
  IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='P1503',MESSAGE='SEMANTIC_IDENTITY_MISMATCH'; END IF;
  RETURN artifact;
 END;
END $$;
