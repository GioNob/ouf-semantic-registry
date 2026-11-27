-- D-103 C. Predecessor source 8598d7b1e6a51dc18a7eba7798a8eda30112c812 (V24).
-- Apply after V24 and before enabling paged owner reads. The predecessor can
-- still read and write its original tables with these objects installed.
CREATE INDEX discovery_candidate_page_idx ON ouf_sem.discovery_candidate
 (request_id, (-score), canonical_uri COLLATE "C", candidate_id);
CREATE INDEX discovery_candidate_page_expiry_idx ON ouf_sem.discovery_candidate
 (request_id, expires_at);

CREATE TABLE ouf_sem.discovery_candidate_page_head (
 request_id uuid PRIMARY KEY REFERENCES ouf_sem.discovery_request ON DELETE CASCADE,
 evidence_version bigint NOT NULL DEFAULT 1,
 candidate_count bigint NOT NULL CHECK(candidate_count >= 0)
);

INSERT INTO ouf_sem.discovery_candidate_page_head(request_id,candidate_count)
 SELECT request_id,count(*) FROM ouf_sem.discovery_candidate GROUP BY request_id;

-- Also follows publications by the predecessor. Keep membership/version
-- changes atomic with the evidence, including adoption and cascading deletes.
CREATE FUNCTION ouf_sem.refresh_discovery_candidate_page_head()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP <> 'INSERT' THEN
  UPDATE ouf_sem.discovery_candidate_page_head h
  SET candidate_count=h.candidate_count-d.amount,evidence_version=h.evidence_version+1
  FROM (SELECT request_id,count(*) AS amount FROM old_candidates GROUP BY request_id) d
  WHERE h.request_id=d.request_id;
 END IF;
 IF TG_OP <> 'DELETE' THEN
  INSERT INTO ouf_sem.discovery_candidate_page_head AS h(request_id,candidate_count)
  SELECT request_id,count(*) FROM new_candidates GROUP BY request_id ORDER BY request_id
  ON CONFLICT(request_id) DO UPDATE
  SET candidate_count=h.candidate_count+EXCLUDED.candidate_count,evidence_version=h.evidence_version+1;
 END IF;
 RETURN NULL;
END $$;

CREATE TRIGGER discovery_candidate_page_insert AFTER INSERT ON ouf_sem.discovery_candidate
 REFERENCING NEW TABLE AS new_candidates FOR EACH STATEMENT
 EXECUTE FUNCTION ouf_sem.refresh_discovery_candidate_page_head();
CREATE TRIGGER discovery_candidate_page_update AFTER UPDATE ON ouf_sem.discovery_candidate
 REFERENCING OLD TABLE AS old_candidates NEW TABLE AS new_candidates FOR EACH STATEMENT
 EXECUTE FUNCTION ouf_sem.refresh_discovery_candidate_page_head();
CREATE TRIGGER discovery_candidate_page_delete AFTER DELETE ON ouf_sem.discovery_candidate
 REFERENCING OLD TABLE AS old_candidates FOR EACH STATEMENT
 EXECUTE FUNCTION ouf_sem.refresh_discovery_candidate_page_head();
