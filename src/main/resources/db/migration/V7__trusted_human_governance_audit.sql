ALTER TABLE ouf_sem.approval_decision ADD COLUMN actor_type text NOT NULL DEFAULT 'HUMAN_USER' CHECK(actor_type='HUMAN_USER');
ALTER TABLE ouf_sem.approval_decision ADD COLUMN authorization_context_ref text NOT NULL DEFAULT 'legacy:migration';

CREATE OR REPLACE FUNCTION ouf_sem.reject_challenge_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN IF TG_OP='DELETE' OR OLD.status<>'OPEN' OR NEW.challenge_id<>OLD.challenge_id OR NEW.revision_id<>OLD.revision_id OR NEW.target_content_hash<>OLD.target_content_hash OR NEW.expires_at<>OLD.expires_at OR NEW.created_by_subject<>OLD.created_by_subject OR NEW.created_at<>OLD.created_at THEN RAISE EXCEPTION USING ERRCODE='23001',MESSAGE='approval challenge immutable except OPEN status transition';END IF;RETURN NEW;END $$;
CREATE TRIGGER approval_challenge_guard BEFORE UPDATE OR DELETE ON ouf_sem.approval_challenge FOR EACH ROW EXECUTE FUNCTION ouf_sem.reject_challenge_mutation();

COMMENT ON COLUMN ouf_sem.approval_decision.authorization_context_ref IS 'Opaque trusted decision reference supplied by the Authorization integration.';
ALTER TABLE ouf_sem.semantic_migration_proposal ADD COLUMN decision_actor_type text CHECK(decision_actor_type IS NULL OR decision_actor_type='HUMAN_USER');
ALTER TABLE ouf_sem.semantic_migration_proposal ADD COLUMN decision_authorization_context_ref text;
