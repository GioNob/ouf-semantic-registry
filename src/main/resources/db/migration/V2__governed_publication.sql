CREATE SEQUENCE ouf_sem.publication_no_seq;
SELECT setval('ouf_sem.publication_no_seq',coalesce((SELECT max(publication_no) FROM ouf_sem.semantic_publication_set),0)+1,false);

CREATE TABLE ouf_sem.approval_challenge(
 challenge_id uuid PRIMARY KEY,
 revision_id uuid NOT NULL REFERENCES ouf_sem.artifact_revision ON DELETE RESTRICT,
 target_content_hash char(64) NOT NULL CHECK(target_content_hash ~ '^[0-9a-f]{64}$'),
 status varchar(16) NOT NULL CHECK(status IN('OPEN','APPROVED','REJECTED','EXPIRED')),
 expires_at timestamptz NOT NULL,
 created_by_subject text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
 CHECK(expires_at>created_at));

CREATE TABLE ouf_sem.approval_decision(
 decision_id uuid PRIMARY KEY,
 challenge_id uuid NOT NULL UNIQUE REFERENCES ouf_sem.approval_challenge ON DELETE RESTRICT,
 decision varchar(16) NOT NULL CHECK(decision IN('APPROVED','REJECTED')),
 target_content_hash char(64) NOT NULL CHECK(target_content_hash ~ '^[0-9a-f]{64}$'),
 decided_by_subject text NOT NULL,
 decided_at timestamptz NOT NULL DEFAULT transaction_timestamp());

CREATE TABLE ouf_sem.audit_event(
 event_id uuid PRIMARY KEY,
 event_type text NOT NULL,
 subject_ref text NOT NULL,
 resource_type text NOT NULL,
 resource_id text NOT NULL,
 correlation_id text,
 detail_json jsonb NOT NULL DEFAULT '{}',
 occurred_at timestamptz NOT NULL DEFAULT transaction_timestamp());

CREATE OR REPLACE FUNCTION ouf_sem.reject_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION USING ERRCODE='23001',MESSAGE='append-only governance evidence'; END $$;
CREATE TRIGGER approval_decision_append_only BEFORE UPDATE OR DELETE ON ouf_sem.approval_decision FOR EACH ROW EXECUTE FUNCTION ouf_sem.reject_mutation();
CREATE TRIGGER audit_event_append_only BEFORE UPDATE OR DELETE ON ouf_sem.audit_event FOR EACH ROW EXECUTE FUNCTION ouf_sem.reject_mutation();

DROP FUNCTION ouf_sem.publish_revision(uuid,text,character,text);
CREATE FUNCTION ouf_sem.publish_revision(
 p_revision uuid,p_decision uuid,p_key text,p_request_hash char(64),p_actor text,p_correlation text)
RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE v_art uuid; v_sem text; v_set uuid; v_existing char(64); v_inserted int; v_approved char(64); v_no bigint;
BEGIN
 INSERT INTO ouf_sem.publish_claim(idempotency_key,request_hash,created_at)
 VALUES(p_key,p_request_hash,transaction_timestamp()) ON CONFLICT DO NOTHING;
 GET DIAGNOSTICS v_inserted=ROW_COUNT;
 SELECT request_hash,publication_set_id INTO STRICT v_existing,v_set
 FROM ouf_sem.publish_claim WHERE idempotency_key=p_key FOR UPDATE;
 IF v_existing<>p_request_hash THEN RAISE EXCEPTION USING ERRCODE='23505',MESSAGE='IDEMPOTENCY_CONFLICT'; END IF;
 IF v_inserted=0 AND v_set IS NOT NULL THEN RETURN v_set; END IF;

 SELECT d.target_content_hash INTO STRICT v_approved
 FROM ouf_sem.approval_decision d JOIN ouf_sem.approval_challenge c USING(challenge_id)
 WHERE d.decision_id=p_decision AND d.decision='APPROVED' AND c.status='APPROVED'
   AND c.revision_id=p_revision AND c.expires_at>=d.decided_at FOR SHARE OF d,c;
 IF v_approved<>p_request_hash THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='APPROVAL_STALE'; END IF;

 SELECT r.artifact_id,a.semantic_id INTO STRICT v_art,v_sem
 FROM ouf_sem.artifact_revision r JOIN ouf_sem.semantic_artifact a USING(artifact_id)
 WHERE r.revision_id=p_revision AND r.lifecycle_status='UNDER_REVIEW' AND r.content_hash=p_request_hash FOR UPDATE OF r;
 IF EXISTS(SELECT 1 FROM ouf_sem.semantic_dependency d LEFT JOIN ouf_sem.semantic_artifact a ON a.semantic_id=d.target_semantic_id WHERE d.source_revision_id=p_revision AND a.artifact_id IS NULL)
 THEN RAISE EXCEPTION USING ERRCODE='23503',MESSAGE='UNRESOLVED_DEPENDENCY'; END IF;

 v_set=gen_random_uuid(); v_no=nextval('ouf_sem.publication_no_seq');
 INSERT INTO ouf_sem.semantic_publication_set VALUES(v_set,v_no,p_request_hash,transaction_timestamp(),p_actor,'BUILDING');
 INSERT INTO ouf_sem.semantic_publication_member(publication_set_id,semantic_id,revision_id)
 SELECT v_set,a.semantic_id,ar.revision_id FROM ouf_sem.artifact_active_revision ar JOIN ouf_sem.semantic_artifact a USING(artifact_id) WHERE ar.artifact_id<>v_art;
 INSERT INTO ouf_sem.semantic_publication_member VALUES(v_set,v_sem,p_revision);
 UPDATE ouf_sem.artifact_revision SET lifecycle_status='ACTIVE',published_at=transaction_timestamp() WHERE revision_id=p_revision;
 INSERT INTO ouf_sem.artifact_active_revision VALUES(v_art,p_revision,transaction_timestamp(),p_actor)
 ON CONFLICT(artifact_id) DO UPDATE SET revision_id=excluded.revision_id,activated_at=excluded.activated_at,activated_by_subject=excluded.activated_by_subject;
 UPDATE ouf_sem.semantic_publication_set SET status='PUBLISHED' WHERE publication_set_id=v_set;
 UPDATE ouf_sem.publish_claim SET publication_set_id=v_set WHERE idempotency_key=p_key;
 INSERT INTO ouf_sem.audit_event VALUES(gen_random_uuid(),'SEMANTIC_PUBLISHED',p_actor,'REVISION',p_revision::text,p_correlation,jsonb_build_object('publicationSetId',v_set),transaction_timestamp());
 RETURN v_set;
END $$;
