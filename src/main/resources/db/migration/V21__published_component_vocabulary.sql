-- Keep V20's lexical rules and resolve a concept constraint against published membership.
ALTER FUNCTION ouf_sem.datatype_constraints_valid(text,jsonb) RENAME TO datatype_constraints_lexically_valid;

CREATE FUNCTION ouf_sem.datatype_constraints_valid(t text, limits jsonb) RETURNS boolean
LANGUAGE sql STABLE AS $$
 SELECT ouf_sem.datatype_constraints_lexically_valid(t, limits)
    AND (t <> 'concept' OR NOT (limits ? 'vocabularyRef') OR EXISTS (
      SELECT FROM ouf_sem.semantic_artifact a
      JOIN ouf_sem.artifact_revision r USING (artifact_id)
      JOIN ouf_sem.semantic_publication_member m ON m.revision_id = r.revision_id AND m.semantic_id = a.semantic_id
      JOIN ouf_sem.semantic_publication_set s USING (publication_set_id)
      WHERE a.semantic_id = limits->>'vocabularyRef' AND a.artifact_type = 'VOCABULARY' AND s.status = 'PUBLISHED'
    ))
$$;
