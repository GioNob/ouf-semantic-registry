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

CREATE OR REPLACE FUNCTION ouf_sem.validate_revision(p_revision uuid,p_actor text) RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE v_run uuid:=gen_random_uuid();v_artifact_type text;v_semantic_version text;v_definition jsonb;v_labels jsonb;v_descriptions jsonb;v_row_version bigint;v_fingerprint char(64);v_errors integer;v_warnings integer;
BEGIN
 PERFORM ouf_sem.rebuild_revision_dependencies(p_revision);
 SELECT a.artifact_type,r.semantic_version,r.definition_json,r.label_json,r.description_json,r.row_version,encode(public.digest(convert_to(r.label_json::text||r.description_json::text||r.definition_json::text,'UTF8'),'sha256'),'hex') INTO STRICT v_artifact_type,v_semantic_version,v_definition,v_labels,v_descriptions,v_row_version,v_fingerprint FROM ouf_sem.artifact_revision r JOIN ouf_sem.semantic_artifact a USING(artifact_id) WHERE r.revision_id=p_revision;
 INSERT INTO ouf_sem.validation_run(validation_run_id,revision_id,status,error_count,warning_count,validated_row_version,validated_content_hash,validator_version,created_by_subject,created_at) VALUES(v_run,p_revision,'BUILDING',0,0,v_row_version,v_fingerprint,'ouf-sem-validator/1.0',p_actor,transaction_timestamp());
 IF coalesce(v_semantic_version,'')='' THEN INSERT INTO ouf_sem.validation_issue VALUES(gen_random_uuid(),v_run,'L0','VAL-VERSION','ERROR','semanticVersion','Versione semantica mancante','{}');END IF;
 IF coalesce(v_labels->>'it','')='' THEN INSERT INTO ouf_sem.validation_issue VALUES(gen_random_uuid(),v_run,'L2','VAL-008','WARN','label.it','Label italiana mancante','{}');END IF;
 IF v_descriptions='{}'::jsonb THEN INSERT INTO ouf_sem.validation_issue VALUES(gen_random_uuid(),v_run,'L2','VAL-008','WARN','description','Descrizione mancante','{}');END IF;
 IF EXISTS(SELECT 1 FROM ouf_sem.semantic_dependency d LEFT JOIN ouf_sem.semantic_artifact a ON a.semantic_id=d.target_semantic_id WHERE d.source_revision_id=p_revision AND a.artifact_id IS NULL) THEN INSERT INTO ouf_sem.validation_issue SELECT gen_random_uuid(),v_run,'L1','VAL-002','ERROR','dependencies','Riferimento semantico non risolto',jsonb_build_object('targets',jsonb_agg(d.target_semantic_id)) FROM ouf_sem.semantic_dependency d LEFT JOIN ouf_sem.semantic_artifact a ON a.semantic_id=d.target_semantic_id WHERE d.source_revision_id=p_revision AND a.artifact_id IS NULL;END IF;
 IF v_artifact_type='RELATIONSHIP' AND (jsonb_array_length(coalesce(v_definition->'domainRefs','[]'))=0 OR jsonb_array_length(coalesce(v_definition->'rangeRefs','[]'))=0) THEN INSERT INTO ouf_sem.validation_issue VALUES(gen_random_uuid(),v_run,'L2','VAL-003','ERROR','definition','Relationship priva di domain o range','{}');END IF;
 IF v_artifact_type='PROPERTY' AND v_definition ? 'datatype' AND jsonb_array_length(coalesce(v_definition->'rangeRefs','[]'))>0 THEN INSERT INTO ouf_sem.validation_issue VALUES(gen_random_uuid(),v_run,'L2','VAL-004','ERROR','definition','Property con datatype e range di classe','{}');END IF;
 IF v_artifact_type='CONCEPT' AND NOT (v_definition ? 'vocabularyRef') THEN INSERT INTO ouf_sem.validation_issue VALUES(gen_random_uuid(),v_run,'L2','VAL-005','ERROR','definition.vocabularyRef','Concept privo di Vocabulary','{}');END IF;
 IF v_definition ? 'minCardinality' AND (v_definition->>'minCardinality')::integer<0 THEN INSERT INTO ouf_sem.validation_issue VALUES(gen_random_uuid(),v_run,'L2','VAL-CARD','ERROR','definition.minCardinality','Cardinalità minima negativa','{}');END IF;
 IF v_definition ? 'maxCardinality' AND ((v_definition->>'maxCardinality')::integer<0 OR (v_definition ? 'minCardinality' AND (v_definition->>'maxCardinality')::integer<(v_definition->>'minCardinality')::integer)) THEN INSERT INTO ouf_sem.validation_issue VALUES(gen_random_uuid(),v_run,'L2','VAL-CARD','ERROR','definition.maxCardinality','Cardinalità massima incompatibile','{}');END IF;
 WITH RECURSIVE graph(source_revision_id,target_semantic_id,path,cycle) AS (SELECT d.source_revision_id,d.target_semantic_id,ARRAY[a.semantic_id,d.target_semantic_id],false FROM ouf_sem.semantic_dependency d JOIN ouf_sem.artifact_revision r ON r.revision_id=d.source_revision_id JOIN ouf_sem.semantic_artifact a ON a.artifact_id=r.artifact_id WHERE d.source_revision_id=p_revision AND coalesce((d.metadata_json->>'required')::boolean,false) UNION ALL SELECT g.source_revision_id,d.target_semantic_id,g.path||d.target_semantic_id,d.target_semantic_id=ANY(g.path) FROM graph g JOIN ouf_sem.semantic_artifact a ON a.semantic_id=g.target_semantic_id JOIN ouf_sem.artifact_active_revision ar ON ar.artifact_id=a.artifact_id JOIN ouf_sem.semantic_dependency d ON d.source_revision_id=ar.revision_id WHERE NOT g.cycle AND coalesce((d.metadata_json->>'required')::boolean,false)) INSERT INTO ouf_sem.validation_issue SELECT gen_random_uuid(),v_run,'L2','VAL-007','ERROR','dependencies','Ciclo REQUIRED rilevato',jsonb_build_object('path',path) FROM graph WHERE cycle LIMIT 1;
 SELECT count(*) FILTER(WHERE severity='ERROR'),count(*) FILTER(WHERE severity='WARN') INTO v_errors,v_warnings FROM ouf_sem.validation_issue WHERE validation_run_id=v_run;
 UPDATE ouf_sem.validation_run SET status=CASE WHEN v_errors=0 THEN 'PASS' ELSE 'FAIL' END,error_count=v_errors,warning_count=v_warnings WHERE validation_run_id=v_run;
 RETURN v_run;
END $$;

CREATE OR REPLACE FUNCTION ouf_sem.require_green_validation() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_revision_no integer;v_impact ouf_sem.impact_report%ROWTYPE;
BEGIN
 IF NEW.lifecycle_status='ACTIVE' AND OLD.lifecycle_status<>'ACTIVE' THEN
  IF NOT EXISTS(SELECT 1 FROM ouf_sem.validation_run v WHERE v.revision_id=NEW.revision_id AND v.status='PASS' AND v.error_count=0 AND v.validated_row_version=NEW.row_version AND v.validated_content_hash=encode(public.digest(convert_to(NEW.label_json::text||NEW.description_json::text||NEW.definition_json::text,'UTF8'),'sha256'),'hex')) THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SEMANTIC_VALIDATION_REQUIRED';END IF;
  SELECT revision_no INTO v_revision_no FROM ouf_sem.artifact_revision WHERE revision_id=NEW.revision_id;
  IF v_revision_no>1 THEN
   SELECT * INTO v_impact FROM ouf_sem.impact_report WHERE to_revision_id=NEW.revision_id ORDER BY created_at DESC LIMIT 1;
   IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SEMANTIC_IMPACT_REQUIRED';END IF;
   IF v_impact.computed_classification='BREAKING' AND NOT EXISTS(SELECT 1 FROM ouf_sem.semantic_migration_proposal p WHERE p.change_id=v_impact.change_id AND p.status='APPROVED') THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SEMANTIC_MIGRATION_APPROVAL_REQUIRED';END IF;
  END IF;
 END IF;RETURN NEW;
END $$;

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
