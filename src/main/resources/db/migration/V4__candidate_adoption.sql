ALTER TABLE ouf_sem.discovery_candidate
 ADD COLUMN adopted_artifact_id uuid REFERENCES ouf_sem.semantic_artifact ON DELETE RESTRICT;
ALTER TABLE ouf_sem.discovery_candidate
 ADD CONSTRAINT candidate_adoption_consistency CHECK(
   (adopted_at IS NULL AND adopted_artifact_id IS NULL) OR
   (adopted_at IS NOT NULL AND adopted_artifact_id IS NOT NULL));

CREATE FUNCTION ouf_sem.adopt_candidate(p_candidate uuid,p_semantic_id text,p_namespace text,p_local_name text,p_owner text,p_authority text,p_actor text)
RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE v ouf_sem.discovery_candidate;v_art uuid;v_rev uuid;v_origin uuid;v_snapshot uuid;
BEGIN
 SELECT * INTO STRICT v FROM ouf_sem.discovery_candidate WHERE candidate_id=p_candidate FOR UPDATE;
 IF v.expires_at<=transaction_timestamp() THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='CANDIDATE_EXPIRED'; END IF;
 IF v.adopted_at IS NOT NULL THEN RETURN v.adopted_artifact_id; END IF;
 v_art=gen_random_uuid();v_rev=gen_random_uuid();v_origin=gen_random_uuid();v_snapshot=gen_random_uuid();
 INSERT INTO ouf_sem.semantic_artifact(artifact_id,semantic_id,artifact_type,namespace,local_name,owner_ref,authority_ref,origin_kind)
 VALUES(v_art,p_semantic_id,v.artifact_type,p_namespace,p_local_name,p_owner,p_authority,'EXTERNAL');
 INSERT INTO ouf_sem.external_semantic_origin(origin_id,artifact_id,canonical_uri,provider_id,source_url,upstream_status,last_checked_at)
 VALUES(v_origin,v_art,v.canonical_uri,v.provider_id,v.source_location,'ACTIVE',transaction_timestamp());
 INSERT INTO ouf_sem.immutable_semantic_snapshot(snapshot_id,origin_id,content_hash,media_type,content_bytes,retrieved_at)
 VALUES(v_snapshot,v_origin,v.content_hash,v.media_type,v.content_bytes,transaction_timestamp());
 INSERT INTO ouf_sem.artifact_revision(revision_id,artifact_id,revision_no,lifecycle_status,definition_json,content_hash,created_by_subject)
 VALUES(v_rev,v_art,1,'DRAFT',v.normalized_payload,v.content_hash,p_actor);
 UPDATE ouf_sem.discovery_candidate SET adopted_at=transaction_timestamp(),adopted_artifact_id=v_art WHERE candidate_id=p_candidate AND adopted_at IS NULL;
 INSERT INTO ouf_sem.audit_event VALUES(gen_random_uuid(),'SEMANTIC_CANDIDATE_ADOPTED',p_actor,'CANDIDATE',p_candidate::text,NULL,jsonb_build_object('artifactId',v_art,'snapshotId',v_snapshot),transaction_timestamp());
 RETURN v_art;
END $$;
