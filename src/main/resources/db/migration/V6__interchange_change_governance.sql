CREATE TABLE ouf_sem.revision_interchange_snapshot(
 revision_id uuid PRIMARY KEY REFERENCES ouf_sem.artifact_revision ON DELETE RESTRICT,
 media_type text NOT NULL CHECK(media_type IN('text/turtle','application/ld+json','application/rdf+xml','application/n-triples')),
 content_hash char(64) NOT NULL CHECK(content_hash ~ '^[0-9a-f]{64}$'),
 content_bytes bytea NOT NULL,
 statement_count bigint NOT NULL CHECK(statement_count>=0),
 imported_by_subject text NOT NULL,
 imported_at timestamptz NOT NULL DEFAULT transaction_timestamp());
CREATE TRIGGER interchange_snapshot_immutable BEFORE UPDATE OR DELETE ON ouf_sem.revision_interchange_snapshot FOR EACH ROW EXECUTE FUNCTION ouf_sem.enforce_immutable();

CREATE OR REPLACE FUNCTION ouf_sem.revision_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN IF TG_OP='UPDATE' AND OLD.lifecycle_status='ACTIVE' AND NEW.lifecycle_status='DEPRECATED' AND (to_jsonb(NEW)-'lifecycle_status')=(to_jsonb(OLD)-'lifecycle_status') THEN RETURN NEW;END IF;IF OLD.lifecycle_status IN('ACTIVE','DEPRECATED','RETIRED') THEN RAISE EXCEPTION USING ERRCODE='23001',MESSAGE='published revision immutable';END IF;RETURN NEW;END $$;
CREATE FUNCTION ouf_sem.deprecate_previous_active() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN IF OLD.revision_id<>NEW.revision_id THEN UPDATE ouf_sem.artifact_revision SET lifecycle_status='DEPRECATED' WHERE revision_id=OLD.revision_id AND lifecycle_status='ACTIVE';END IF;RETURN NEW;END $$;
CREATE TRIGGER active_pointer_deprecates_previous BEFORE UPDATE OF revision_id ON ouf_sem.artifact_active_revision FOR EACH ROW EXECUTE FUNCTION ouf_sem.deprecate_previous_active();

CREATE TABLE ouf_sem.semantic_change_notice(
 change_notice_id uuid PRIMARY KEY,
 change_id uuid NOT NULL UNIQUE REFERENCES ouf_sem.impact_report ON DELETE RESTRICT,
 semantic_id text NOT NULL,
 from_revision_id uuid NOT NULL REFERENCES ouf_sem.artifact_revision ON DELETE RESTRICT,
 to_revision_id uuid NOT NULL REFERENCES ouf_sem.artifact_revision ON DELETE RESTRICT,
 classification varchar(24) NOT NULL CHECK(classification IN('NO_SEMANTIC_CHANGE','NON_BREAKING','POTENTIALLY_BREAKING','BREAKING')),
 decision text NOT NULL,
 detected_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
 created_by_subject text NOT NULL);
CREATE TRIGGER change_notice_immutable BEFORE UPDATE OR DELETE ON ouf_sem.semantic_change_notice FOR EACH ROW EXECUTE FUNCTION ouf_sem.enforce_immutable();

CREATE TABLE ouf_sem.semantic_migration_proposal(
 migration_proposal_id uuid PRIMARY KEY,
 change_id uuid NOT NULL UNIQUE REFERENCES ouf_sem.impact_report ON DELETE RESTRICT,
 status varchar(16) NOT NULL CHECK(status IN('PROPOSED','APPROVED','REJECTED')),
 replacement_refs jsonb NOT NULL DEFAULT '[]',
 rationale text,
 proposed_by_subject text NOT NULL,
 proposed_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
 decided_by_subject text,
 decided_at timestamptz,
 CHECK((status='PROPOSED' AND decided_by_subject IS NULL AND decided_at IS NULL) OR (status IN('APPROVED','REJECTED') AND decided_by_subject IS NOT NULL AND decided_at IS NOT NULL)));
ALTER TABLE ouf_sem.impact_report ADD CONSTRAINT impact_migration_proposal_fk FOREIGN KEY(migration_proposal_id) REFERENCES ouf_sem.semantic_migration_proposal ON DELETE RESTRICT;

CREATE FUNCTION ouf_sem.migration_proposal_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN IF OLD.status='PROPOSED' AND NEW.status IN('APPROVED','REJECTED') AND OLD.migration_proposal_id=NEW.migration_proposal_id AND OLD.change_id=NEW.change_id AND OLD.replacement_refs=NEW.replacement_refs AND OLD.rationale IS NOT DISTINCT FROM NEW.rationale AND OLD.proposed_by_subject=NEW.proposed_by_subject AND OLD.proposed_at=NEW.proposed_at THEN RETURN NEW;END IF;RAISE EXCEPTION USING ERRCODE='23001',MESSAGE='migration proposal transition forbidden';END $$;
CREATE TRIGGER migration_proposal_transition BEFORE UPDATE OR DELETE ON ouf_sem.semantic_migration_proposal FOR EACH ROW EXECUTE FUNCTION ouf_sem.migration_proposal_guard();

CREATE FUNCTION ouf_sem.create_change_notice(p_change uuid,p_decision text,p_actor text) RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE v_id uuid:=gen_random_uuid();v_existing_decision text;
BEGIN INSERT INTO ouf_sem.semantic_change_notice(change_notice_id,change_id,semantic_id,from_revision_id,to_revision_id,classification,decision,created_by_subject) SELECT v_id,i.change_id,a.semantic_id,i.from_revision_id,i.to_revision_id,i.computed_classification,p_decision,p_actor FROM ouf_sem.impact_report i JOIN ouf_sem.semantic_artifact a USING(artifact_id) WHERE i.change_id=p_change ON CONFLICT(change_id) DO NOTHING;SELECT change_notice_id,decision INTO STRICT v_id,v_existing_decision FROM ouf_sem.semantic_change_notice WHERE change_id=p_change FOR SHARE;IF v_existing_decision<>p_decision THEN RAISE EXCEPTION USING ERRCODE='23505',MESSAGE='CHANGE_NOTICE_CONFLICT';END IF;RETURN v_id;END $$;

CREATE OR REPLACE FUNCTION ouf_sem.require_green_validation() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_revision_no integer;v_impact ouf_sem.impact_report%ROWTYPE;
BEGIN
 IF NEW.lifecycle_status='ACTIVE' AND OLD.lifecycle_status<>'ACTIVE' THEN
  IF NOT EXISTS(SELECT 1 FROM ouf_sem.validation_run v WHERE v.revision_id=NEW.revision_id AND v.status='PASS' AND v.error_count=0 AND v.validated_row_version=NEW.row_version AND v.validated_content_hash=encode(public.digest((NEW.label_json::text||NEW.description_json::text||NEW.definition_json::text)::bytea,'sha256'),'hex')) THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SEMANTIC_VALIDATION_REQUIRED';END IF;
  SELECT revision_no INTO v_revision_no FROM ouf_sem.artifact_revision WHERE revision_id=NEW.revision_id;
  IF v_revision_no>1 THEN
   SELECT * INTO v_impact FROM ouf_sem.impact_report WHERE to_revision_id=NEW.revision_id ORDER BY created_at DESC LIMIT 1;
   IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SEMANTIC_IMPACT_REQUIRED';END IF;
   IF v_impact.computed_classification='BREAKING' AND NOT EXISTS(SELECT 1 FROM ouf_sem.semantic_migration_proposal p WHERE p.change_id=v_impact.change_id AND p.status='APPROVED') THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='SEMANTIC_MIGRATION_APPROVAL_REQUIRED';END IF;
  END IF;
 END IF;RETURN NEW;
END $$;
