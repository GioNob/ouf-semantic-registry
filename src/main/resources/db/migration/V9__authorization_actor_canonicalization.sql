UPDATE ouf_sem.approval_decision
SET actor_type='HUMAN'
WHERE actor_type='HUMAN_USER';

ALTER TABLE ouf_sem.approval_decision
  DROP CONSTRAINT IF EXISTS approval_decision_actor_type_check;
ALTER TABLE ouf_sem.approval_decision
  ALTER COLUMN actor_type SET DEFAULT 'HUMAN';
ALTER TABLE ouf_sem.approval_decision
  ADD CONSTRAINT approval_decision_actor_type_check CHECK(actor_type='HUMAN');

UPDATE ouf_sem.semantic_migration_proposal
SET decision_actor_type='HUMAN'
WHERE decision_actor_type='HUMAN_USER';

ALTER TABLE ouf_sem.semantic_migration_proposal
  DROP CONSTRAINT IF EXISTS semantic_migration_proposal_decision_actor_type_check;
ALTER TABLE ouf_sem.semantic_migration_proposal
  ADD CONSTRAINT semantic_migration_proposal_decision_actor_type_check
  CHECK(decision_actor_type IS NULL OR decision_actor_type='HUMAN');

COMMENT ON COLUMN ouf_sem.approval_decision.authorization_context_ref IS
  'Canonical Authorization decisionRef; legacy column name retained for storage compatibility.';
COMMENT ON COLUMN ouf_sem.semantic_migration_proposal.decision_authorization_context_ref IS
  'Canonical Authorization decisionRef; legacy column name retained for storage compatibility.';
