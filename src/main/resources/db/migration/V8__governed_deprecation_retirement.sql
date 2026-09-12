CREATE OR REPLACE FUNCTION ouf_sem.revision_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='UPDATE'
    AND ((OLD.lifecycle_status='ACTIVE' AND NEW.lifecycle_status='DEPRECATED')
      OR (OLD.lifecycle_status='DEPRECATED' AND NEW.lifecycle_status='RETIRED'))
    AND (to_jsonb(NEW)-'lifecycle_status')=(to_jsonb(OLD)-'lifecycle_status') THEN RETURN NEW;END IF;
 IF OLD.lifecycle_status IN('ACTIVE','DEPRECATED','RETIRED') THEN RAISE EXCEPTION USING ERRCODE='23001',MESSAGE='published revision immutable';END IF;
 RETURN NEW;
END $$;

CREATE FUNCTION ouf_sem.govern_revision_lifecycle(p_revision uuid,p_target text,p_actor text,p_authorization_context text,p_correlation text) RETURNS text LANGUAGE plpgsql AS $$
DECLARE v_current text;v_artifact uuid;v_semantic_id text;v_consumers bigint;v_dependencies bigint;
BEGIN
 SELECT lifecycle_status,artifact_id INTO STRICT v_current,v_artifact FROM ouf_sem.artifact_revision WHERE revision_id=p_revision FOR UPDATE;
 SELECT semantic_id INTO STRICT v_semantic_id FROM ouf_sem.semantic_artifact WHERE artifact_id=v_artifact;
 IF NOT ((v_current='ACTIVE' AND p_target='DEPRECATED') OR (v_current='DEPRECATED' AND p_target='RETIRED')) THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SEMANTIC_LIFECYCLE_TRANSITION_FORBIDDEN';END IF;
 SELECT count(*) INTO v_consumers FROM ouf_sem.semantic_consumer_reference WHERE revision_id=p_revision;
 SELECT count(*) INTO v_dependencies FROM ouf_sem.semantic_dependency WHERE target_semantic_id=v_semantic_id;
 IF v_consumers>0 OR v_dependencies>0 THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SEMANTIC_BLOCKING_CONSUMERS';END IF;
 UPDATE ouf_sem.artifact_revision SET lifecycle_status=p_target WHERE revision_id=p_revision;
 DELETE FROM ouf_sem.artifact_active_revision WHERE revision_id=p_revision;
 IF p_target='RETIRED' THEN UPDATE ouf_sem.semantic_artifact SET retired_at=transaction_timestamp() WHERE artifact_id=v_artifact;END IF;
 INSERT INTO ouf_sem.audit_event VALUES(gen_random_uuid(),'SEMANTIC_'||p_target,p_actor,'REVISION',p_revision::text,p_correlation,jsonb_build_object('from',v_current,'to',p_target,'blockingConsumers',v_consumers,'blockingDependencies',v_dependencies,'actorType','HUMAN_USER','authorizationContextRef',p_authorization_context),transaction_timestamp());
 RETURN p_target;
END $$;
