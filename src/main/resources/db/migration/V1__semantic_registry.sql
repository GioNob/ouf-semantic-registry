CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE SCHEMA IF NOT EXISTS ouf_sem;

CREATE TABLE ouf_sem.semantic_artifact(
 artifact_id uuid PRIMARY KEY, semantic_id text NOT NULL UNIQUE,
 artifact_type varchar(32) NOT NULL CHECK(artifact_type IN('CLASS','PROPERTY','RELATIONSHIP','VOCABULARY','CONCEPT','ONTOLOGY')),
 namespace text NOT NULL, local_name text NOT NULL, owner_ref text NOT NULL,
 authority_ref text NOT NULL, origin_kind varchar(32) NOT NULL,
 created_at timestamptz NOT NULL DEFAULT transaction_timestamp(), retired_at timestamptz,
 UNIQUE(namespace,local_name,artifact_type));

CREATE TABLE ouf_sem.artifact_revision(
 revision_id uuid PRIMARY KEY, artifact_id uuid NOT NULL REFERENCES ouf_sem.semantic_artifact ON DELETE RESTRICT,
 revision_no integer NOT NULL CHECK(revision_no>0),
 lifecycle_status varchar(24) NOT NULL CHECK(lifecycle_status IN('DRAFT','UNDER_REVIEW','ACTIVE','DEPRECATED','RETIRED')),
 semantic_version text, label_json jsonb NOT NULL DEFAULT '{}', description_json jsonb NOT NULL DEFAULT '{}',
 definition_json jsonb NOT NULL DEFAULT '{}', content_hash char(64), row_version bigint NOT NULL DEFAULT 0 CHECK(row_version>=0),
 created_by_subject text NOT NULL, created_at timestamptz NOT NULL DEFAULT transaction_timestamp(), published_at timestamptz,
 UNIQUE(artifact_id,revision_no),
 CHECK(content_hash IS NULL OR content_hash ~ '^[0-9a-f]{64}$'),
 CHECK((lifecycle_status IN('ACTIVE','DEPRECATED','RETIRED'))=(published_at IS NOT NULL)));

CREATE TABLE ouf_sem.artifact_active_revision(
 artifact_id uuid PRIMARY KEY REFERENCES ouf_sem.semantic_artifact ON DELETE RESTRICT,
 revision_id uuid NOT NULL UNIQUE REFERENCES ouf_sem.artifact_revision ON DELETE RESTRICT,
 activated_at timestamptz NOT NULL, activated_by_subject text NOT NULL);

CREATE TABLE ouf_sem.semantic_dependency(
 source_revision_id uuid NOT NULL REFERENCES ouf_sem.artifact_revision ON DELETE RESTRICT,
 dependency_type varchar(32) NOT NULL,
 target_semantic_id text NOT NULL,
 target_revision_id uuid REFERENCES ouf_sem.artifact_revision ON DELETE RESTRICT,
 metadata_json jsonb NOT NULL DEFAULT '{}',
 PRIMARY KEY(source_revision_id,dependency_type,target_semantic_id));

CREATE TABLE ouf_sem.semantic_publication_set(
 publication_set_id uuid PRIMARY KEY, publication_no bigint NOT NULL UNIQUE,
 checksum char(64) NOT NULL UNIQUE CHECK(checksum ~ '^[0-9a-f]{64}$'),
 created_at timestamptz NOT NULL DEFAULT transaction_timestamp(), created_by_subject text NOT NULL,
 status varchar(16) NOT NULL CHECK(status IN('BUILDING','PUBLISHED')));
CREATE TABLE ouf_sem.semantic_publication_member(
 publication_set_id uuid NOT NULL REFERENCES ouf_sem.semantic_publication_set ON DELETE RESTRICT,
 semantic_id text NOT NULL, revision_id uuid NOT NULL REFERENCES ouf_sem.artifact_revision ON DELETE RESTRICT,
 PRIMARY KEY(publication_set_id,semantic_id));

CREATE TABLE ouf_sem.external_semantic_origin(
 origin_id uuid PRIMARY KEY, artifact_id uuid NOT NULL REFERENCES ouf_sem.semantic_artifact ON DELETE RESTRICT,
 canonical_uri text NOT NULL, provider_id text NOT NULL, source_revision text, source_url text,
 license_ref text, publisher text, upstream_status varchar(24) NOT NULL CHECK(upstream_status IN('ACTIVE','UNCHANGED','WITHDRAWN','UNREACHABLE')),
 last_checked_at timestamptz, UNIQUE(canonical_uri,provider_id));
CREATE TABLE ouf_sem.immutable_semantic_snapshot(
 snapshot_id uuid PRIMARY KEY, origin_id uuid NOT NULL REFERENCES ouf_sem.external_semantic_origin ON DELETE RESTRICT,
 content_hash char(64) NOT NULL CHECK(content_hash ~ '^[0-9a-f]{64}$'), media_type text NOT NULL,
 content_bytes bytea NOT NULL, retrieved_at timestamptz NOT NULL, UNIQUE(origin_id,content_hash));

CREATE TABLE ouf_sem.publish_claim(
 idempotency_key text PRIMARY KEY, request_hash char(64) NOT NULL CHECK(request_hash ~ '^[0-9a-f]{64}$'),
 publication_set_id uuid REFERENCES ouf_sem.semantic_publication_set, created_at timestamptz NOT NULL DEFAULT transaction_timestamp());

CREATE INDEX revision_lifecycle_idx ON ouf_sem.artifact_revision(lifecycle_status);
CREATE INDEX dependency_target_idx ON ouf_sem.semantic_dependency(target_semantic_id);
CREATE INDEX artifact_semantic_trgm_idx ON ouf_sem.semantic_artifact USING gin(semantic_id gin_trgm_ops);

CREATE FUNCTION ouf_sem.enforce_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION USING ERRCODE='23001',MESSAGE='published semantic state is immutable'; END $$;
CREATE TRIGGER snapshot_immutable BEFORE UPDATE OR DELETE ON ouf_sem.immutable_semantic_snapshot FOR EACH ROW EXECUTE FUNCTION ouf_sem.enforce_immutable();
CREATE TRIGGER publication_set_immutable BEFORE UPDATE OR DELETE ON ouf_sem.semantic_publication_set FOR EACH ROW WHEN(OLD.status='PUBLISHED') EXECUTE FUNCTION ouf_sem.enforce_immutable();
CREATE TRIGGER publication_member_immutable BEFORE UPDATE OR DELETE ON ouf_sem.semantic_publication_member FOR EACH ROW EXECUTE FUNCTION ouf_sem.enforce_immutable();
CREATE FUNCTION ouf_sem.revision_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN IF OLD.lifecycle_status IN('ACTIVE','DEPRECATED','RETIRED') THEN RAISE EXCEPTION USING ERRCODE='23001',MESSAGE='published revision immutable'; END IF; RETURN NEW; END $$;
CREATE TRIGGER revision_immutable BEFORE UPDATE OR DELETE ON ouf_sem.artifact_revision FOR EACH ROW EXECUTE FUNCTION ouf_sem.revision_immutable();

CREATE FUNCTION ouf_sem.edit_draft(p_revision uuid,p_expected bigint,p_label jsonb,p_definition jsonb) RETURNS bigint LANGUAGE plpgsql AS $$
DECLARE v bigint; BEGIN
 UPDATE ouf_sem.artifact_revision SET label_json=coalesce(p_label,label_json),definition_json=coalesce(p_definition,definition_json),row_version=row_version+1
 WHERE revision_id=p_revision AND lifecycle_status='DRAFT' AND row_version=p_expected RETURNING row_version INTO v;
 IF v IS NULL THEN RAISE EXCEPTION USING ERRCODE='40001',MESSAGE='VERSION_CONFLICT'; END IF; RETURN v;
END $$;

CREATE FUNCTION ouf_sem.publish_revision(p_revision uuid,p_key text,p_request_hash char(64),p_actor text)
RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE v_art uuid; v_sem text; v_set uuid; v_existing char(64); v_no bigint;
BEGIN
 SELECT request_hash,publication_set_id INTO v_existing,v_set FROM ouf_sem.publish_claim WHERE idempotency_key=p_key FOR UPDATE;
 IF FOUND THEN IF v_existing<>p_request_hash THEN RAISE EXCEPTION USING ERRCODE='23505',MESSAGE='IDEMPOTENCY_CONFLICT'; END IF; RETURN v_set; END IF;
 SELECT r.artifact_id,a.semantic_id INTO STRICT v_art,v_sem FROM ouf_sem.artifact_revision r JOIN ouf_sem.semantic_artifact a USING(artifact_id) WHERE r.revision_id=p_revision AND r.lifecycle_status IN('DRAFT','UNDER_REVIEW') FOR UPDATE OF r;
 IF EXISTS(SELECT 1 FROM ouf_sem.semantic_dependency d LEFT JOIN ouf_sem.semantic_artifact a ON a.semantic_id=d.target_semantic_id WHERE d.source_revision_id=p_revision AND a.artifact_id IS NULL) THEN RAISE EXCEPTION USING ERRCODE='23503',MESSAGE='UNRESOLVED_DEPENDENCY'; END IF;
 v_set=gen_random_uuid(); SELECT coalesce(max(publication_no),0)+1 INTO v_no FROM ouf_sem.semantic_publication_set;
 INSERT INTO ouf_sem.semantic_publication_set VALUES(v_set,v_no,p_request_hash,transaction_timestamp(),p_actor,'BUILDING');
 INSERT INTO ouf_sem.semantic_publication_member VALUES(v_set,v_sem,p_revision);
 UPDATE ouf_sem.artifact_revision SET lifecycle_status='ACTIVE',content_hash=p_request_hash,published_at=transaction_timestamp() WHERE revision_id=p_revision;
 INSERT INTO ouf_sem.artifact_active_revision VALUES(v_art,p_revision,transaction_timestamp(),p_actor)
 ON CONFLICT(artifact_id) DO UPDATE SET revision_id=EXCLUDED.revision_id,activated_at=EXCLUDED.activated_at,activated_by_subject=EXCLUDED.activated_by_subject;
 UPDATE ouf_sem.semantic_publication_set SET status='PUBLISHED' WHERE publication_set_id=v_set;
 INSERT INTO ouf_sem.publish_claim VALUES(p_key,p_request_hash,v_set,transaction_timestamp()); RETURN v_set;
END $$;
