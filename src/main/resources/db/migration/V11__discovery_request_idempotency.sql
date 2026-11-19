-- Additive only: historical requests retain their identifiers and contents.
ALTER TABLE ouf_sem.discovery_request
 ADD COLUMN idempotency_key_hash char(64),
 ADD COLUMN request_fingerprint char(64),
 ADD CONSTRAINT discovery_idempotency_hashes_valid CHECK (
   (idempotency_key_hash IS NULL AND request_fingerprint IS NULL) OR
   (idempotency_key_hash IS NOT NULL AND request_fingerprint IS NOT NULL
    AND idempotency_key_hash ~ '^[0-9a-f]{64}$' AND request_fingerprint ~ '^[0-9a-f]{64}$'));
CREATE UNIQUE INDEX discovery_request_idempotency_idx
 ON ouf_sem.discovery_request(created_by_subject,idempotency_key_hash)
 WHERE idempotency_key_hash IS NOT NULL;
