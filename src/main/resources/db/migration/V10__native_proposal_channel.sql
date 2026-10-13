-- Owner-local transaction receipt. Intent keys survive MCP attempts/restarts.
CREATE TABLE ouf_sem.native_proposal (
 proposal_id uuid PRIMARY KEY,
 tenant_id text NOT NULL,
 subject_id text NOT NULL,
 proposal_key varchar(128) NOT NULL,
 commands jsonb NOT NULL CHECK(jsonb_typeof(commands)='array' AND jsonb_array_length(commands) BETWEEN 1 AND 21),
 phase text NOT NULL CHECK(phase IN ('DRAFT','VALIDATED','UNDER_REVIEW')),
 row_version bigint NOT NULL DEFAULT 0,
 result_json jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
 updated_at timestamptz NOT NULL DEFAULT transaction_timestamp(),
 UNIQUE(tenant_id,subject_id,proposal_key)
);
