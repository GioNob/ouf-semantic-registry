-- Exact class bytes and hashes retain their V16 meaning. Only the optional projection is new.
ALTER TABLE ouf_sem.discovery_candidate
 ADD COLUMN ontology_rdf bytea CHECK(octet_length(ontology_rdf) BETWEEN 1 AND 65536),
 ADD COLUMN ontology_sha256 text,
 ADD CHECK(ontology_sha256 IS NOT DISTINCT FROM encode(sha256(ontology_rdf),'hex')),
 ADD COLUMN discovery_labels jsonb NOT NULL DEFAULT '{}';
ALTER TABLE ouf_sem.immutable_semantic_snapshot
 ADD COLUMN ontology_rdf bytea CHECK(octet_length(ontology_rdf) BETWEEN 1 AND 65536),
 ADD COLUMN ontology_sha256 text,
 ADD CHECK(ontology_sha256 IS NOT DISTINCT FROM encode(sha256(ontology_rdf),'hex'));

CREATE TRIGGER discovery_ontology_immutable BEFORE UPDATE OF ontology_rdf,discovery_labels ON ouf_sem.discovery_candidate
 FOR EACH ROW WHEN (OLD.ontology_rdf IS DISTINCT FROM NEW.ontology_rdf OR OLD.discovery_labels IS DISTINCT FROM NEW.discovery_labels)
 EXECUTE FUNCTION ouf_sem.enforce_immutable();

-- Insert class, labels and companion in the existing fenced batch, before its final lease check.
CREATE OR REPLACE FUNCTION ouf_sem.finish_discovery_job(p_request uuid,p_generation bigint,p_outcome text,p_code text,p_candidates jsonb,p_next timestamptz DEFAULT NULL)
RETURNS boolean LANGUAGE plpgsql AS $$
DECLARE r ouf_sem.discovery_request; c jsonb; next_time timestamptz; ontology bytea;
BEGIN
 SELECT * INTO r FROM ouf_sem.discovery_request WHERE request_id=p_request FOR UPDATE;
 IF NOT FOUND OR r.state<>'RUNNING' OR r.worker_generation<>p_generation OR r.lease_until<=clock_timestamp()
 OR r.budget_deadline<=clock_timestamp() THEN RETURN false; END IF;
 IF p_outcome IS NULL OR p_outcome NOT IN ('SUCCESS','RETRY_WAIT','PAUSED_EXHAUSTED','BLOCKED','CANCELLED') THEN RAISE EXCEPTION 'DISCOVERY_OUTCOME_INVALID'; END IF;
 IF p_outcome='SUCCESS' THEN
  IF p_candidates IS NULL OR jsonb_typeof(p_candidates)<>'array' OR jsonb_array_length(p_candidates)>256 THEN RAISE EXCEPTION 'DISCOVERY_CANDIDATES_INVALID'; END IF;
  FOR c IN SELECT value FROM jsonb_array_elements(p_candidates) LOOP
   ontology=decode(c->>'ontology','base64');
   INSERT INTO ouf_sem.discovery_candidate(candidate_id,request_id,provider_id,canonical_uri,source_location,
     artifact_type,provider_trust,score,match_reasons,gaps,normalized_payload,content_hash,media_type,content_bytes,
     ontology_rdf,ontology_sha256,discovery_labels,expires_at)
   VALUES(gen_random_uuid(),p_request,c->>'provider',c->>'uri',c->>'source',c->>'type',c->>'trust',(c->>'score')::numeric,
     c->'reasons',c->'gaps','{}',c->>'hash',c->>'mediaType',decode(c->>'bytes','base64'),
     ontology,encode(sha256(ontology),'hex'),coalesce(c->'labels','{}'::jsonb),clock_timestamp()+interval '24 hours');
  END LOOP;
  -- Parsing/inserts/lock acquisition consume lease time too. Failure rolls back the whole set.
  IF r.lease_until<=clock_timestamp() OR r.budget_deadline<=clock_timestamp() THEN RAISE EXCEPTION 'DISCOVERY_PUBLICATION_LEASE_EXPIRED'; END IF;
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

CREATE OR REPLACE FUNCTION ouf_sem.adoption_provenance(p_origin ouf_sem.external_semantic_origin,
 p_snapshot ouf_sem.immutable_semantic_snapshot) RETURNS jsonb LANGUAGE sql IMMUTABLE AS $$
 SELECT jsonb_build_object('providerId',p_origin.provider_id,'canonicalUri',p_origin.canonical_uri,
  'sourceLocation',p_origin.source_url,'publisher',p_origin.publisher,'license',p_origin.license_ref,
  'licenseWarning',CASE WHEN p_origin.license_ref IS NULL THEN 'licenza mancante' END,
  'snapshotId',p_snapshot.snapshot_id,'rdfSha256',p_snapshot.content_hash)
 || CASE WHEN p_snapshot.ontology_rdf IS NULL THEN '{}'::jsonb ELSE
      jsonb_build_object('ontologySha256',p_snapshot.ontology_sha256) END
$$;

CREATE OR REPLACE FUNCTION ouf_sem.adopt_candidate(p_candidate uuid,p_semantic_id text,p_namespace text,p_local_name text,
 p_owner text,p_authority text,p_actor text,p_publisher text,p_license text,p_definition jsonb)
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
 INSERT INTO ouf_sem.artifact_revision(revision_id,artifact_id,revision_no,semantic_version,lifecycle_status,label_json,definition_json,content_hash,created_by_subject)
 VALUES(revision,artifact,1,'1.0.0','DRAFT',c.discovery_labels,c.normalized_payload || p_definition ||
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
