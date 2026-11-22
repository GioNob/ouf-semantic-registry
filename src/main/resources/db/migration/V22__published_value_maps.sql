-- V21 is already occupied by the published component vocabulary check.
ALTER TABLE ouf_sem.semantic_artifact DROP CONSTRAINT semantic_artifact_artifact_type_check;
ALTER TABLE ouf_sem.semantic_artifact ADD CONSTRAINT semantic_artifact_artifact_type_check CHECK
 (artifact_type IN ('CLASS','PROPERTY','RELATIONSHIP','VOCABULARY','CONCEPT','ONTOLOGY','DATATYPE','VALUE_MAP'));

-- UTF-16 orders supplementary code points between U+D7FF and U+E000.
-- Ranking each scalar this way gives the same lexicographic order as String.compareTo.
CREATE FUNCTION ouf_sem.value_map_code_order(code text) RETURNS integer[]
LANGUAGE sql IMMUTABLE STRICT AS $$
 SELECT array_agg(CASE WHEN point BETWEEN 57344 AND 65535 THEN point+1114112 ELSE point END ORDER BY ordinal)
 FROM (
  SELECT ascii(ch) AS point, ordinal
  FROM regexp_split_to_table(code, '') WITH ORDINALITY AS chars(ch, ordinal)
 ) codepoints
$$;

CREATE FUNCTION ouf_sem.validate_value_map_definition(definition jsonb) RETURNS jsonb
LANGUAGE plpgsql AS $$
DECLARE
 pin text[];
 canonical_entries jsonb;
 invalid constant text := 'SEMANTIC_VALUE_MAP_INVALID';
 -- Character.isWhitespace at the ends, as in the VALUE_MAP_V1 reader's String.strip.
 edge_space constant text := U&'[\0009-\000D\001C-\0020\1680\2000-\2006\2008-\200A\2028\2029\205F\3000]';
BEGIN
 IF jsonb_typeof(definition) IS DISTINCT FROM 'object' THEN
  RAISE EXCEPTION USING ERRCODE='P0842', MESSAGE=invalid;
 END IF;
 IF (definition - ARRAY['targetVocabulary','entries','labels']) <> '{}'::jsonb
    OR jsonb_typeof(definition->'targetVocabulary') IS DISTINCT FROM 'string'
    OR jsonb_typeof(definition->'entries') IS DISTINCT FROM 'array'
 THEN RAISE EXCEPTION USING ERRCODE='P0842', MESSAGE=invalid; END IF;

 IF definition ? 'labels' THEN
  IF jsonb_typeof(definition->'labels') <> 'object' THEN
   RAISE EXCEPTION USING ERRCODE='P0842', MESSAGE=invalid;
  END IF;
  IF ((definition->'labels') - ARRAY['it','en']) <> '{}'::jsonb
     OR EXISTS (SELECT FROM jsonb_each(definition->'labels') l WHERE jsonb_typeof(l.value)<>'string')
  THEN RAISE EXCEPTION USING ERRCODE='P0842', MESSAGE=invalid; END IF;
 END IF;

 IF jsonb_array_length(definition->'entries') NOT BETWEEN 1 AND 2000 THEN
  RAISE EXCEPTION USING ERRCODE='P0842', MESSAGE=invalid;
 END IF;
 IF EXISTS (
  SELECT FROM jsonb_array_elements(definition->'entries') e(entry)
  WHERE CASE WHEN jsonb_typeof(entry)<>'object' THEN true ELSE
    (entry - ARRAY['code','concept']) <> '{}'::jsonb
    OR jsonb_typeof(entry->'code') IS DISTINCT FROM 'string'
    OR jsonb_typeof(entry->'concept') IS DISTINCT FROM 'string'
    OR char_length(entry->>'code') NOT BETWEEN 1 AND 128
    OR (entry->>'code') ~ U&'[\0001-\001F\007F]'
    OR (entry->>'code') ~ ('^'||edge_space||'|'||edge_space||'$')
  END
 ) OR EXISTS (
  SELECT FROM jsonb_array_elements(definition->'entries') e(entry)
  GROUP BY (entry->>'code') COLLATE "C" HAVING count(*)>1
 ) THEN RAISE EXCEPTION USING ERRCODE='P0842', MESSAGE=invalid; END IF;

 pin := regexp_match(definition->>'targetVocabulary',
   '^(.+)@([0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12})$');
 IF pin IS NULL THEN RAISE EXCEPTION USING ERRCODE='P0842', MESSAGE=invalid; END IF;
 PERFORM FROM ouf_sem.semantic_publication_member m
 JOIN ouf_sem.semantic_publication_set s USING (publication_set_id)
 JOIN ouf_sem.artifact_revision r USING (revision_id)
 JOIN ouf_sem.semantic_artifact a USING (artifact_id)
 JOIN ouf_sem.artifact_active_revision active USING (artifact_id, revision_id)
 WHERE m.publication_set_id=pin[2]::uuid AND m.semantic_id=pin[1] AND a.semantic_id=m.semantic_id
   AND a.artifact_type='VOCABULARY' AND s.status='PUBLISHED' AND r.lifecycle_status='ACTIVE'
 FOR SHARE OF r;
 IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='P0842', MESSAGE=invalid; END IF;

 IF EXISTS (
  SELECT FROM (SELECT DISTINCT entry->>'concept' AS id FROM jsonb_array_elements(definition->'entries') e(entry)) codes
  WHERE NOT EXISTS (
   SELECT FROM ouf_sem.semantic_publication_member m
   JOIN ouf_sem.artifact_revision r USING (revision_id)
   JOIN ouf_sem.semantic_artifact a USING (artifact_id)
   WHERE m.publication_set_id=pin[2]::uuid AND m.semantic_id=codes.id AND a.semantic_id=m.semantic_id
    AND a.artifact_type='CONCEPT' AND r.definition_json->>'vocabularyRef'=pin[1]
  )
 ) THEN RAISE EXCEPTION USING ERRCODE='P0842', MESSAGE=invalid; END IF;

 SELECT jsonb_agg(entry ORDER BY ouf_sem.value_map_code_order(entry->>'code')) INTO canonical_entries
 FROM jsonb_array_elements(definition->'entries') e(entry);
 RETURN jsonb_set(definition,'{entries}',canonical_entries);
END $$;

-- Apply the same checks on native proposal and draft edits, even after a binary rollback.
-- Published definitions are already protected by revision_immutable from V8.
CREATE FUNCTION ouf_sem.guard_value_map_draft() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NOT EXISTS (SELECT FROM ouf_sem.semantic_artifact WHERE artifact_id=NEW.artifact_id AND artifact_type='VALUE_MAP')
 THEN RETURN NEW; END IF;

 IF NEW.semantic_version IS NULL OR NEW.semantic_version !~ '^[0-9]+\.[0-9]+\.[0-9]+(-[A-Za-z0-9.-]+)?(\+[A-Za-z0-9.-]+)?$'
    OR EXISTS (SELECT FROM ouf_sem.artifact_revision r WHERE r.artifact_id=NEW.artifact_id
               AND r.revision_id<>NEW.revision_id AND r.published_at IS NOT NULL AND r.semantic_version=NEW.semantic_version)
 THEN RAISE EXCEPTION USING ERRCODE='P0843', MESSAGE='SEMANTIC_VERSION_INVALID'; END IF;

 IF TG_OP='INSERT' OR NEW.definition_json IS DISTINCT FROM OLD.definition_json THEN
  NEW.definition_json := ouf_sem.validate_value_map_definition(NEW.definition_json);
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER guard_value_map_draft BEFORE INSERT OR UPDATE OF definition_json,semantic_version
 ON ouf_sem.artifact_revision FOR EACH ROW WHEN (NEW.lifecycle_status='DRAFT')
 EXECUTE FUNCTION ouf_sem.guard_value_map_draft();

-- Reuse the fingerprint and impact gates of native versioned definitions.
CREATE OR REPLACE FUNCTION ouf_sem.check_datatype_review() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF EXISTS (SELECT FROM ouf_sem.semantic_artifact WHERE artifact_id=NEW.artifact_id AND artifact_type IN ('DATATYPE','VALUE_MAP'))
    AND NOT EXISTS (SELECT FROM ouf_sem.validation_run WHERE revision_id=NEW.revision_id AND status='PASS'
      AND validated_row_version=NEW.row_version AND validated_content_hash=NEW.content_hash
      AND validated_content_hash=encode(public.digest(convert_to(NEW.label_json::text||NEW.description_json::text||
          NEW.definition_json::text,'UTF8'),'sha256'),'hex'))
 THEN RAISE EXCEPTION USING ERRCODE='P0841',MESSAGE='CURRENT_GREEN_VALIDATION_REQUIRED'; END IF;
 RETURN NEW;
END $$;
-- An approved revision is frozen. Use the existing impact classifier and publication gates.
CREATE OR REPLACE FUNCTION ouf_sem.datatype_revision_impact() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 PERFORM ouf_sem.compute_impact(previous.revision_id,r.revision_id,NEW.decided_by_subject)
 FROM ouf_sem.approval_challenge c JOIN ouf_sem.artifact_revision r USING(revision_id)
 JOIN ouf_sem.semantic_artifact a USING(artifact_id)
 JOIN LATERAL (SELECT p.revision_id FROM ouf_sem.artifact_revision p WHERE p.artifact_id=r.artifact_id
               AND p.revision_no<r.revision_no AND p.published_at IS NOT NULL ORDER BY p.revision_no DESC LIMIT 1) previous ON true
 WHERE c.challenge_id=NEW.challenge_id AND a.artifact_type IN ('DATATYPE','VALUE_MAP') AND r.revision_no>1
 AND NOT EXISTS (SELECT FROM ouf_sem.impact_report WHERE from_revision_id=previous.revision_id AND to_revision_id=r.revision_id);
 RETURN NEW;
END $$;
