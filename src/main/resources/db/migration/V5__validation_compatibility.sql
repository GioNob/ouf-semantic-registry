ALTER TABLE ouf_sem.semantic_dependency DROP CONSTRAINT semantic_dependency_pkey;
ALTER TABLE ouf_sem.semantic_dependency ADD COLUMN dependency_role varchar(16) NOT NULL DEFAULT 'GENERIC'
 CHECK(dependency_role IN('GENERIC','DOMAIN','RANGE','INVERSE'));
ALTER TABLE ouf_sem.semantic_dependency ADD PRIMARY KEY(source_revision_id,dependency_type,target_semantic_id,dependency_role);

CREATE TABLE ouf_sem.validation_run(
 validation_run_id uuid PRIMARY KEY,
 revision_id uuid NOT NULL REFERENCES ouf_sem.artifact_revision ON DELETE RESTRICT,
 status varchar(8) NOT NULL CHECK(status IN('BUILDING','PASS','FAIL')),
 error_count integer NOT NULL CHECK(error_count>=0),
 warning_count integer NOT NULL CHECK(warning_count>=0),
 validated_row_version bigint NOT NULL CHECK(validated_row_version>=0),
 validated_content_hash char(64) NOT NULL CHECK(validated_content_hash ~ '^[0-9a-f]{64}$'),
 validator_version text NOT NULL,
 created_by_subject text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT transaction_timestamp());

CREATE TABLE ouf_sem.validation_issue(
 issue_id uuid PRIMARY KEY,
 validation_run_id uuid NOT NULL REFERENCES ouf_sem.validation_run ON DELETE RESTRICT,
 level varchar(2) NOT NULL CHECK(level IN('L0','L1','L2')),
 rule_id varchar(16) NOT NULL,
 severity varchar(8) NOT NULL CHECK(severity IN('ERROR','WARN')),
 path text,
 message text NOT NULL,
 details_json jsonb NOT NULL DEFAULT '{}');
CREATE INDEX validation_issue_run_idx ON ouf_sem.validation_issue(validation_run_id,severity);

CREATE TABLE ouf_sem.semantic_consumer_reference(
 consumer_type text NOT NULL,
 consumer_id text NOT NULL,
 semantic_id text NOT NULL,
 revision_id uuid NOT NULL REFERENCES ouf_sem.artifact_revision ON DELETE RESTRICT,
 publication_set_id uuid NOT NULL REFERENCES ouf_sem.semantic_publication_set ON DELETE RESTRICT,
 registered_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
 PRIMARY KEY(consumer_type,consumer_id,semantic_id));
CREATE INDEX semantic_consumer_revision_idx ON ouf_sem.semantic_consumer_reference(revision_id);

CREATE TABLE ouf_sem.impact_report(
 change_id uuid PRIMARY KEY,
 artifact_id uuid NOT NULL REFERENCES ouf_sem.semantic_artifact ON DELETE RESTRICT,
 from_revision_id uuid NOT NULL REFERENCES ouf_sem.artifact_revision ON DELETE RESTRICT,
 to_revision_id uuid NOT NULL REFERENCES ouf_sem.artifact_revision ON DELETE RESTRICT,
 computed_classification varchar(24) NOT NULL CHECK(computed_classification IN('NO_SEMANTIC_CHANGE','NON_BREAKING','POTENTIALLY_BREAKING','BREAKING')),
 approved_classification varchar(24) CHECK(approved_classification IN('NO_SEMANTIC_CHANGE','NON_BREAKING','POTENTIALLY_BREAKING','BREAKING')),
 impacts_json jsonb NOT NULL,
 blocking_issues jsonb NOT NULL DEFAULT '[]',
 migration_proposal_id uuid,
 created_by_subject text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
 UNIQUE(from_revision_id,to_revision_id));

CREATE FUNCTION ouf_sem.validation_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN IF TG_TABLE_NAME='validation_run' AND TG_OP='UPDATE' AND OLD.status='BUILDING' AND NEW.status IN('PASS','FAIL') AND OLD.validation_run_id=NEW.validation_run_id AND OLD.revision_id=NEW.revision_id AND OLD.validated_row_version=NEW.validated_row_version AND OLD.validated_content_hash=NEW.validated_content_hash AND OLD.validator_version=NEW.validator_version AND OLD.created_by_subject=NEW.created_by_subject AND OLD.created_at=NEW.created_at THEN RETURN NEW;END IF;RAISE EXCEPTION USING ERRCODE='23001',MESSAGE='validation and impact evidence is append-only'; END $$;
CREATE TRIGGER validation_run_immutable BEFORE UPDATE OR DELETE ON ouf_sem.validation_run FOR EACH ROW EXECUTE FUNCTION ouf_sem.validation_append_only();
CREATE TRIGGER validation_issue_immutable BEFORE UPDATE OR DELETE ON ouf_sem.validation_issue FOR EACH ROW EXECUTE FUNCTION ouf_sem.validation_append_only();
CREATE TRIGGER impact_report_immutable BEFORE UPDATE OR DELETE ON ouf_sem.impact_report FOR EACH ROW EXECUTE FUNCTION ouf_sem.validation_append_only();

CREATE FUNCTION ouf_sem.rebuild_revision_dependencies(p_revision uuid) RETURNS integer LANGUAGE plpgsql AS $$
DECLARE v_definition jsonb;v_type text;v_target text;v_count integer;
BEGIN
 SELECT r.definition_json,a.artifact_type INTO STRICT v_definition,v_type FROM ouf_sem.artifact_revision r JOIN ouf_sem.semantic_artifact a USING(artifact_id) WHERE r.revision_id=p_revision AND r.lifecycle_status IN('DRAFT','UNDER_REVIEW') FOR UPDATE OF r;
 DELETE FROM ouf_sem.semantic_dependency WHERE source_revision_id=p_revision;
 FOR v_target IN SELECT jsonb_array_elements_text(coalesce(v_definition->'domainRefs','[]')) LOOP INSERT INTO ouf_sem.semantic_dependency(source_revision_id,dependency_type,target_semantic_id,target_revision_id,metadata_json,dependency_role) VALUES(p_revision,'USES_CLASS',v_target,NULL,'{"role":"domain","required":true}','DOMAIN') ON CONFLICT DO NOTHING;END LOOP;
 FOR v_target IN SELECT jsonb_array_elements_text(coalesce(v_definition->'rangeRefs','[]')) LOOP INSERT INTO ouf_sem.semantic_dependency(source_revision_id,dependency_type,target_semantic_id,target_revision_id,metadata_json,dependency_role) VALUES(p_revision,'USES_CLASS',v_target,NULL,'{"role":"range","required":true}','RANGE') ON CONFLICT DO NOTHING;END LOOP;
 v_target=v_definition->>'vocabularyRef';IF v_target IS NOT NULL THEN INSERT INTO ouf_sem.semantic_dependency(source_revision_id,dependency_type,target_semantic_id,target_revision_id,metadata_json,dependency_role) VALUES(p_revision,'USES_VOCABULARY',v_target,NULL,'{"required":true}','GENERIC') ON CONFLICT DO NOTHING;END IF;
 v_target=v_definition->>'inverseRef';IF v_target IS NOT NULL THEN INSERT INTO ouf_sem.semantic_dependency(source_revision_id,dependency_type,target_semantic_id,target_revision_id,metadata_json,dependency_role) VALUES(p_revision,'USES_PROPERTY',v_target,NULL,'{"role":"inverse","required":true}','INVERSE') ON CONFLICT DO NOTHING;END IF;
 SELECT count(*) INTO v_count FROM ouf_sem.semantic_dependency WHERE source_revision_id=p_revision;RETURN v_count;
END $$;

CREATE FUNCTION ouf_sem.validate_revision(p_revision uuid,p_actor text) RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE v_run uuid:=gen_random_uuid();v_artifact_type text;v_semantic_version text;v_definition jsonb;v_labels jsonb;v_descriptions jsonb;v_row_version bigint;v_fingerprint char(64);v_errors integer;v_warnings integer;
BEGIN
 PERFORM ouf_sem.rebuild_revision_dependencies(p_revision);
 SELECT a.artifact_type,r.semantic_version,r.definition_json,r.label_json,r.description_json,r.row_version,encode(public.digest((r.label_json::text||r.description_json::text||r.definition_json::text)::bytea,'sha256'),'hex') INTO STRICT v_artifact_type,v_semantic_version,v_definition,v_labels,v_descriptions,v_row_version,v_fingerprint FROM ouf_sem.artifact_revision r JOIN ouf_sem.semantic_artifact a USING(artifact_id) WHERE r.revision_id=p_revision;
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

CREATE FUNCTION ouf_sem.compute_impact(p_from uuid,p_to uuid,p_actor text) RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE v_change uuid:=gen_random_uuid();v_artifact uuid;v_old jsonb;v_new jsonb;v_class text;v_impacted_artifacts integer;v_sets integer;v_consumers integer;v_blocking jsonb:='[]';
BEGIN
 SELECT o.artifact_id,o.definition_json,n.definition_json INTO STRICT v_artifact,v_old,v_new FROM ouf_sem.artifact_revision o JOIN ouf_sem.artifact_revision n ON n.artifact_id=o.artifact_id WHERE o.revision_id=p_from AND n.revision_id=p_to;
 IF v_old=v_new THEN v_class='NO_SEMANTIC_CHANGE';
 ELSIF (v_old ? 'maxCardinality' AND (NOT v_new ? 'maxCardinality' OR (v_new->>'maxCardinality')::integer>(v_old->>'maxCardinality')::integer)) OR (v_old ? 'minCardinality' AND coalesce((v_new->>'minCardinality')::integer,0)<(v_old->>'minCardinality')::integer) THEN v_class='NON_BREAKING';
 ELSIF (v_new ? 'maxCardinality' AND (NOT v_old ? 'maxCardinality' OR (v_new->>'maxCardinality')::integer<(v_old->>'maxCardinality')::integer)) OR coalesce((v_new->>'minCardinality')::integer,0)>coalesce((v_old->>'minCardinality')::integer,0) OR v_old->'rangeRefs' IS DISTINCT FROM v_new->'rangeRefs' OR v_old->>'datatype' IS DISTINCT FROM v_new->>'datatype' THEN v_class='BREAKING';v_blocking=jsonb_build_array('Vincolo, range o datatype incompatibile con la revisione pubblicata');
 ELSE v_class='POTENTIALLY_BREAKING';END IF;
 SELECT count(DISTINCT source_revision_id) INTO v_impacted_artifacts FROM ouf_sem.semantic_dependency d JOIN ouf_sem.semantic_artifact a ON a.semantic_id=d.target_semantic_id WHERE a.artifact_id=v_artifact;
 SELECT count(DISTINCT publication_set_id) INTO v_sets FROM ouf_sem.semantic_publication_member m JOIN ouf_sem.artifact_revision r ON r.revision_id=m.revision_id WHERE r.artifact_id=v_artifact;
 SELECT count(*) INTO v_consumers FROM ouf_sem.semantic_consumer_reference c JOIN ouf_sem.artifact_revision r ON r.revision_id=c.revision_id WHERE r.artifact_id=v_artifact;
 INSERT INTO ouf_sem.impact_report VALUES(v_change,v_artifact,p_from,p_to,v_class,NULL,jsonb_build_object('semanticArtifacts',v_impacted_artifacts,'publicationSets',v_sets,'runtimeConsumers',v_consumers),v_blocking,NULL,p_actor,transaction_timestamp());RETURN v_change;
END $$;

CREATE FUNCTION ouf_sem.require_green_validation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN IF NEW.lifecycle_status='ACTIVE' AND OLD.lifecycle_status<>'ACTIVE' AND NOT EXISTS(SELECT 1 FROM ouf_sem.validation_run v WHERE v.revision_id=NEW.revision_id AND v.status='PASS' AND v.error_count=0 AND v.validated_row_version=NEW.row_version AND v.validated_content_hash=encode(public.digest((NEW.label_json::text||NEW.description_json::text||NEW.definition_json::text)::bytea,'sha256'),'hex')) THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SEMANTIC_VALIDATION_REQUIRED';END IF;RETURN NEW;END $$;
CREATE TRIGGER revision_green_validation BEFORE UPDATE OF lifecycle_status ON ouf_sem.artifact_revision FOR EACH ROW EXECUTE FUNCTION ouf_sem.require_green_validation();
