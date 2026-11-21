-- New callers supply the description when inserting a draft. Existing revisions are never rewritten.

CREATE FUNCTION ouf_sem.adopt_candidate(p_candidate uuid,p_semantic_id text,p_namespace text,p_local_name text,
 p_owner text,p_authority text,p_actor text,p_publisher text,p_license text,p_definition jsonb,p_description jsonb)
RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE
 c ouf_sem.discovery_candidate;
 o ouf_sem.external_semantic_origin;
 s ouf_sem.immutable_semantic_snapshot;
 artifact uuid:=gen_random_uuid();
 revision uuid:=gen_random_uuid();
BEGIN
 SELECT * INTO STRICT c FROM ouf_sem.discovery_candidate WHERE candidate_id=p_candidate FOR UPDATE;
 IF c.expires_at<=clock_timestamp() THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='CANDIDATE_EXPIRED'; END IF;
 IF c.adopted_at IS NOT NULL THEN RETURN c.adopted_artifact_id; END IF;
 IF encode(public.digest(c.content_bytes,'sha256'),'hex')<>c.content_hash THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='CANDIDATE_HASH_MISMATCH';
 END IF;
 INSERT INTO ouf_sem.semantic_artifact(artifact_id,semantic_id,artifact_type,namespace,local_name,owner_ref,authority_ref,origin_kind)
 VALUES(artifact,p_semantic_id,c.artifact_type,p_namespace,p_local_name,p_owner,p_authority,'EXTERNAL');
 INSERT INTO ouf_sem.external_semantic_origin(origin_id,artifact_id,canonical_uri,provider_id,source_url,publisher,license_ref,upstream_status,last_checked_at)
 VALUES(gen_random_uuid(),artifact,c.canonical_uri,c.provider_id,c.source_location,p_publisher,p_license,'ACTIVE',transaction_timestamp())
 RETURNING * INTO o;
 INSERT INTO ouf_sem.immutable_semantic_snapshot(snapshot_id,origin_id,content_hash,media_type,content_bytes,ontology_rdf,ontology_sha256,retrieved_at)
 VALUES(gen_random_uuid(),o.origin_id,c.content_hash,c.media_type,c.content_bytes,c.ontology_rdf,c.ontology_sha256,transaction_timestamp()) RETURNING * INTO s;
 INSERT INTO ouf_sem.artifact_revision(revision_id,artifact_id,revision_no,semantic_version,lifecycle_status,label_json,description_json,definition_json,content_hash,created_by_subject)
 VALUES(revision,artifact,1,'1.0.0','DRAFT',c.discovery_labels,p_description,c.normalized_payload || p_definition ||
  jsonb_build_object('adoptionProvenance',ouf_sem.adoption_provenance(o,s)),c.content_hash,p_actor);
 INSERT INTO ouf_sem.revision_adoption VALUES(revision,s.snapshot_id);
 UPDATE ouf_sem.discovery_candidate SET adopted_at=clock_timestamp(),adopted_artifact_id=artifact
 WHERE candidate_id=p_candidate AND expires_at>clock_timestamp();
 IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='CANDIDATE_EXPIRED'; END IF;
 INSERT INTO ouf_sem.audit_event(event_id,event_type,subject_ref,resource_type,resource_id,detail_json)
 VALUES(gen_random_uuid(),'SEMANTIC_CANDIDATE_ADOPTED',p_actor,'CANDIDATE',p_candidate::text,
  jsonb_build_object('artifactId',artifact,'revisionId',revision,'snapshotId',s.snapshot_id,'requestId',c.request_id));
 RETURN artifact;
END $$;

-- Keep the V17 signature and the V13 seven-argument wrapper on the same insertion path.

CREATE OR REPLACE FUNCTION ouf_sem.adopt_candidate(p_candidate uuid,p_semantic_id text,p_namespace text,p_local_name text,
 p_owner text,p_authority text,p_actor text,p_publisher text,p_license text,p_definition jsonb)
RETURNS uuid LANGUAGE sql AS $$
 SELECT ouf_sem.adopt_candidate(p_candidate,p_semantic_id,p_namespace,p_local_name,p_owner,p_authority,p_actor,
   p_publisher,p_license,p_definition,'{}'::jsonb)
$$;

CREATE FUNCTION ouf_sem.adopt_or_find_candidate(p_candidate uuid,p_uri text,p_namespace text,p_name text,
 p_actor text,p_publisher text,p_license text,p_definition jsonb,p_description jsonb)
RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE artifact uuid; conflict_table text; conflict_constraint text;
BEGIN
 SELECT artifact_id INTO artifact FROM ouf_sem.semantic_artifact WHERE semantic_id=p_uri;
 IF FOUND THEN RETURN artifact; END IF;
 BEGIN
  RETURN ouf_sem.adopt_candidate(p_candidate,p_uri,p_namespace,p_name,p_actor,p_publisher,
                                 p_actor,p_publisher,p_license,p_definition,p_description);
 EXCEPTION WHEN unique_violation THEN
  GET STACKED DIAGNOSTICS conflict_table=TABLE_NAME,conflict_constraint=CONSTRAINT_NAME;
  IF conflict_table NOT IN ('semantic_artifact','external_semantic_origin') OR
     conflict_constraint IN ('semantic_artifact_pkey','external_semantic_origin_pkey') THEN RAISE; END IF;
  SELECT artifact_id INTO artifact FROM ouf_sem.semantic_artifact WHERE semantic_id=p_uri;
  IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='P1503',MESSAGE='SEMANTIC_IDENTITY_MISMATCH'; END IF;
  RETURN artifact;
 END;
END $$;

CREATE OR REPLACE FUNCTION ouf_sem.adopt_or_find_candidate(p_candidate uuid,p_uri text,p_namespace text,p_name text,
 p_actor text,p_publisher text,p_license text,p_definition jsonb)
RETURNS uuid LANGUAGE sql AS $$
 SELECT ouf_sem.adopt_or_find_candidate(p_candidate,p_uri,p_namespace,p_name,p_actor,
   p_publisher,p_license,p_definition,'{}'::jsonb)
$$;
