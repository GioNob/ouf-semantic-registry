-- Canonical Authorization actor vocabulary migration.
-- Preserve V7 as historical evidence and migrate persisted trusted-human actor types forward.

ALTER TABLE ouf_sem.approval_decision
  DROP CONSTRAINT IF EXISTS approval_decision_actor_type_check;

ALTER TABLE ouf_sem.approval_decision
  ALTER COLUMN actor_type DROP DEFAULT;

UPDATE ouf_sem.approval_decision
SET actor_type='HUMAN'
WHERE actor_type='HUMAN_USER';

ALTER TABLE ouf_sem.approval_decision
  ALTER COLUMN actor_type SET DEFAULT 'HUMAN';

ALTER TABLE ouf_sem.approval_decision
  ADD CONSTRAINT approval_decision_actor_type_check CHECK(actor_type='HUMAN');

ALTER TABLE ouf_sem.semantic_migration_proposal
  DROP CONSTRAINT IF EXISTS semantic_migration_proposal_decision_actor_type_check;

UPDATE ouf_sem.semantic_migration_proposal
SET decision_actor_type='HUMAN'
WHERE decision_actor_type='HUMAN_USER';

ALTER TABLE ouf_sem.semantic_migration_proposal
  ADD CONSTRAINT semantic_migration_proposal_decision_actor_type_check
  CHECK(decision_actor_type IS NULL OR decision_actor_type='HUMAN');

COMMENT ON COLUMN ouf_sem.approval_decision.actor_type IS
  'Canonical Authorization actor type; trusted-human decisions require HUMAN.';
COMMENT ON COLUMN ouf_sem.semantic_migration_proposal.decision_actor_type IS
  'Canonical Authorization actor type; governed human decisions require HUMAN.';
