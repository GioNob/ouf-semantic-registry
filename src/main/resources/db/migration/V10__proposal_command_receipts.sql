-- A receipt and all owner effects commit together. No retry scheduler or budget reset.
CREATE TABLE ouf_sem.proposal_command_receipt (
 tenant_id text NOT NULL,
 principal_id text NOT NULL,
 idempotency_key varchar(128) NOT NULL,
 operation varchar(16) NOT NULL CHECK (operation IN ('CREATE','VALIDATE','REVIEW')),
 request_hash char(64) NOT NULL CHECK (request_hash ~ '^[0-9a-f]{64}$'),
 result_json jsonb,
 created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
 PRIMARY KEY (tenant_id, principal_id, idempotency_key)
);
CREATE FUNCTION ouf_sem.proposal_receipt_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='UPDATE' AND OLD.result_json IS NULL AND NEW.result_json IS NOT NULL
   AND (NEW.tenant_id,NEW.principal_id,NEW.idempotency_key,NEW.operation,NEW.request_hash,NEW.created_at)
     IS NOT DISTINCT FROM (OLD.tenant_id,OLD.principal_id,OLD.idempotency_key,OLD.operation,OLD.request_hash,OLD.created_at)
 THEN RETURN NEW; END IF;
 RAISE EXCEPTION USING ERRCODE='23001',MESSAGE='PROPOSAL_RECEIPT_IMMUTABLE';
END $$;
CREATE TRIGGER proposal_receipt_immutable BEFORE UPDATE OR DELETE ON ouf_sem.proposal_command_receipt
 FOR EACH ROW EXECUTE FUNCTION ouf_sem.proposal_receipt_guard();
CREATE FUNCTION ouf_sem.proposal_receipt_complete() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF EXISTS(SELECT 1 FROM ouf_sem.proposal_command_receipt WHERE tenant_id=NEW.tenant_id
   AND principal_id=NEW.principal_id AND idempotency_key=NEW.idempotency_key AND result_json IS NULL)
 THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='PROPOSAL_RECEIPT_INCOMPLETE'; END IF;
 RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER proposal_receipt_complete AFTER INSERT ON ouf_sem.proposal_command_receipt
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION ouf_sem.proposal_receipt_complete();
