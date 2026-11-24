-- Widen the native artifact vocabulary without rewriting existing revisions.
ALTER TABLE ouf_sem.semantic_artifact
 DROP CONSTRAINT semantic_artifact_artifact_type_check,
 ADD CONSTRAINT semantic_artifact_artifact_type_check CHECK
 (artifact_type IN ('CLASS','PROPERTY','RELATIONSHIP','VOCABULARY','CONCEPT','ONTOLOGY','DATATYPE'));

-- semantic.propose carries editorial metadata in definition.description. Keep it
-- in the governed content hash and the card, outside the structural definition hash.
CREATE FUNCTION ouf_sem.datatype_description() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE description jsonb:=NEW.definition_json->'description';
BEGIN
 IF jsonb_typeof(description)='object' AND EXISTS
   (SELECT FROM ouf_sem.semantic_artifact WHERE artifact_id=NEW.artifact_id AND artifact_type='DATATYPE') THEN
  IF NOT EXISTS (SELECT FROM jsonb_each(description) WHERE jsonb_typeof(value)<>'string') THEN
   NEW.description_json:=description;
   NEW.definition_json:=NEW.definition_json-'description';
  END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER datatype_description BEFORE INSERT OR UPDATE OF definition_json ON ouf_sem.artifact_revision
 FOR EACH ROW WHEN (NEW.definition_json ? 'description') EXECUTE FUNCTION ouf_sem.datatype_description();

CREATE FUNCTION ouf_sem.datatype_constraints_valid(t text, limits jsonb) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE key text; bound text; lo text:=limits->>'minInclusive'; hi text:=limits->>'maxInclusive';
BEGIN
 IF jsonb_typeof(limits)<>'object' THEN RETURN false; END IF;
 FOR key,bound IN SELECT * FROM jsonb_each_text(limits) LOOP
  IF t='string' AND key='maxLength' THEN
   IF jsonb_typeof(limits->key)<>'number' OR bound !~ '^[0-9]+$' THEN RETURN false; END IF;
  ELSIF t='concept' AND key='vocabularyRef' THEN
   IF jsonb_typeof(limits->key)<>'string' OR bound !~ '^[A-Za-z][A-Za-z0-9+.-]*:[^[:space:]<>"{}|^\\`]+$' THEN RETURN false; END IF;
  ELSIF key IN ('minInclusive','maxInclusive') AND jsonb_typeof(limits->key)='string' THEN
   CASE t
   WHEN 'integer' THEN IF bound !~ '^(0|-?[1-9][0-9]*)$' THEN RETURN false; END IF;
   WHEN 'decimal' THEN IF bound !~ '^-?(0|[1-9][0-9]*)(\.[0-9]*[1-9])?$' OR bound='-0' THEN RETURN false; END IF;
   WHEN 'date','datetime' THEN
    IF t='date' AND bound !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' OR
       t='datetime' AND bound !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](\.[0-9]{1,9})?Z$'
    THEN RETURN false; END IF;
    -- Gregorian years repeat every 400 years, including ISO year zero.
    PERFORM make_date(2000+left(bound,4)::int%400,substring(bound,6,2)::int,substring(bound,9,2)::int);
   ELSE RETURN false;
   END CASE;
  ELSE RETURN false;
  END IF;
 END LOOP;
 IF lo IS NULL OR hi IS NULL THEN RETURN true; END IF;
 IF t IN ('integer','decimal') THEN RETURN lo::numeric<=hi::numeric; END IF;
 -- Removing the final Z preserves lexical ordering of UTC fractions at nanosecond precision.
 RETURN (left(lo,19) COLLATE "C",rpad(substring(rtrim(lo,'Z') from 21),9,'0')) <=
        (left(hi,19) COLLATE "C",rpad(substring(rtrim(hi,'Z') from 21),9,'0'));
EXCEPTION WHEN data_exception THEN RETURN false;
END $$;

-- Follow exact historical members, including deprecated children. Count each occurrence,
-- even when several components use the same revision. The remaining budget bounds traversal.
CREATE FUNCTION ouf_sem.check_datatype(def jsonb, path text[], remaining integer)
RETURNS integer LANGUAGE plpgsql STABLE AS $$
DECLARE c jsonb; names text[]:='{}'; n text; t text; child jsonb; pin text[]; leaves integer:=0;
BEGIN
 IF cardinality(path)>4 THEN RAISE EXCEPTION USING ERRCODE='P0840',MESSAGE='DT-DEPTH'; END IF;
 IF jsonb_typeof(def)<>'object' OR def-'components'<>'{}' OR jsonb_typeof(def->'components') IS DISTINCT FROM 'array'
 THEN RAISE EXCEPTION USING ERRCODE='P0840',MESSAGE='DT-DEFINITION'; END IF;
 IF jsonb_array_length(def->'components') NOT BETWEEN 1 AND 32
 THEN RAISE EXCEPTION USING ERRCODE='P0840',MESSAGE='DT-COUNT'; END IF;
 FOR c IN SELECT * FROM jsonb_array_elements(def->'components') LOOP
  IF jsonb_typeof(c)<>'object' THEN RAISE EXCEPTION USING ERRCODE='P0840',MESSAGE='DT-COMPONENT'; END IF;
  IF c-ARRAY['name','type','cardinality','required','constraints','labels']<>'{}'
  THEN RAISE EXCEPTION USING ERRCODE='P0840',MESSAGE='DT-COMPONENT'; END IF;
  n:=c->>'name'; t:=c->>'type';
  IF jsonb_typeof(c->'name') IS DISTINCT FROM 'string' OR n COLLATE "C" !~ '^[a-z][A-Za-z0-9]{0,63}$' OR n=ANY(names)
  THEN RAISE EXCEPTION USING ERRCODE='P0840',MESSAGE='DT-NAME'; END IF;
  names:=array_append(names,n);
  IF coalesce(c->>'cardinality','') NOT IN ('ONE','MANY') THEN RAISE EXCEPTION USING ERRCODE='P0840',MESSAGE='DT-CARDINALITY'; END IF;
  IF jsonb_typeof(c->'required') IS DISTINCT FROM 'boolean' THEN RAISE EXCEPTION USING ERRCODE='P0840',MESSAGE='DT-REQUIRED'; END IF;
  IF c ? 'labels' THEN
   IF jsonb_typeof(c->'labels')<>'object' THEN RAISE EXCEPTION USING ERRCODE='P0840',MESSAGE='DT-LABELS'; END IF;
   IF EXISTS (SELECT FROM jsonb_each(c->'labels') WHERE jsonb_typeof(value)<>'string')
   THEN RAISE EXCEPTION USING ERRCODE='P0840',MESSAGE='DT-LABELS'; END IF;
  END IF;
  IF jsonb_typeof(c->'type') IS DISTINCT FROM 'string' THEN RAISE EXCEPTION USING ERRCODE='P0840',MESSAGE='DT-TYPE'; END IF;
  IF NOT ouf_sem.datatype_constraints_valid(t,coalesce(c->'constraints','{}'))
  THEN RAISE EXCEPTION USING ERRCODE='P0840',MESSAGE='DT-CONSTRAINT'; END IF;
  IF t IN ('string','integer','decimal','boolean','date','datetime','geometry','concept') THEN
   leaves:=leaves+1;
  ELSE
   pin:=regexp_match(t,'^(.+)@([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})$');
   IF pin IS NULL THEN RAISE EXCEPTION USING ERRCODE='P0840',MESSAGE='DT-TYPE'; END IF;
   IF pin[1]=ANY(path) THEN RAISE EXCEPTION USING ERRCODE='P0840',MESSAGE='DT-CYCLE'; END IF;
   SELECT r.definition_json INTO child FROM ouf_sem.semantic_publication_member m
    JOIN ouf_sem.semantic_publication_set s USING(publication_set_id)
    JOIN ouf_sem.artifact_revision r USING(revision_id) JOIN ouf_sem.semantic_artifact a USING(artifact_id)
    WHERE m.semantic_id=pin[1] AND a.semantic_id=m.semantic_id AND m.publication_set_id=pin[2]::uuid
      AND s.status='PUBLISHED' AND a.artifact_type='DATATYPE';
   IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='P0840',MESSAGE='DT-UNPUBLISHED'; END IF;
   leaves:=leaves+ouf_sem.check_datatype(child,array_append(path,pin[1]),remaining-leaves);
  END IF;
  IF leaves>remaining THEN RAISE EXCEPTION USING ERRCODE='P0840',MESSAGE='DT-LEAVES'; END IF;
 END LOOP;
 RETURN leaves;
END $$;

-- Keep the public validation signature for the predecessor. Successful datatype runs
-- also receive the normal label/description warnings and green fingerprint from V19.
ALTER FUNCTION ouf_sem.validate_revision(uuid,text) RENAME TO validate_revision_v19;
CREATE FUNCTION ouf_sem.validate_revision(p_revision uuid,p_actor text) RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE rev ouf_sem.artifact_revision; id text; run uuid; rule text;
BEGIN
 SELECT a.semantic_id INTO id FROM ouf_sem.semantic_artifact a JOIN ouf_sem.artifact_revision r USING(artifact_id)
 WHERE r.revision_id=p_revision AND a.artifact_type='DATATYPE';
 IF NOT FOUND THEN RETURN ouf_sem.validate_revision_v19(p_revision,p_actor); END IF;
 SELECT * INTO STRICT rev FROM ouf_sem.artifact_revision WHERE revision_id=p_revision
 AND lifecycle_status IN ('DRAFT','UNDER_REVIEW') FOR UPDATE;
 BEGIN
  IF EXISTS (SELECT FROM ouf_sem.artifact_revision WHERE artifact_id=rev.artifact_id
             AND published_at IS NOT NULL AND semantic_version=rev.semantic_version)
  THEN RAISE EXCEPTION USING ERRCODE='P0840',MESSAGE='DT-VERSION'; END IF;
  PERFORM ouf_sem.check_datatype(rev.definition_json,ARRAY[id],256);
 EXCEPTION WHEN SQLSTATE 'P0840' THEN rule:=SQLERRM;
 END;
 IF rule IS NOT NULL THEN
  DELETE FROM ouf_sem.semantic_dependency WHERE source_revision_id=p_revision;
  run:=gen_random_uuid();
  INSERT INTO ouf_sem.validation_run(validation_run_id,revision_id,status,error_count,warning_count,
     validated_row_version,validated_content_hash,validator_version,created_by_subject)
  VALUES(run,p_revision,'FAIL',1,0,rev.row_version,encode(public.digest(convert_to(
    rev.label_json::text||rev.description_json::text||rev.definition_json::text,'UTF8'),'sha256'),'hex'),'ouf-datatype/1',p_actor);
  INSERT INTO ouf_sem.validation_issue VALUES(gen_random_uuid(),run,'L2',rule,'ERROR','definition',rule,'{}');
  RETURN run;
 END IF;
 run:=ouf_sem.validate_revision_v19(p_revision,p_actor);
 INSERT INTO ouf_sem.semantic_dependency(source_revision_id,dependency_type,target_semantic_id,target_revision_id,metadata_json)
 SELECT p_revision,'USES_DATATYPE',m.semantic_id,
   CASE WHEN count(DISTINCT m.revision_id)=1 THEN (array_agg(m.revision_id))[1] END,
   jsonb_build_object('pins',jsonb_agg(DISTINCT c->>'type'))
 FROM jsonb_array_elements(rev.definition_json->'components') c
 CROSS JOIN LATERAL regexp_match(c->>'type','^(.+)@([^@]+)$') pin
 JOIN ouf_sem.semantic_publication_member m ON m.semantic_id=pin[1] AND m.publication_set_id=pin[2]::uuid
 GROUP BY m.semantic_id;
 RETURN run;
END $$;

-- The direct challenge API and older binaries must bind the same validated draft.
CREATE FUNCTION ouf_sem.check_datatype_review() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF EXISTS (SELECT FROM ouf_sem.semantic_artifact WHERE artifact_id=NEW.artifact_id AND artifact_type='DATATYPE')
    AND NOT EXISTS (SELECT FROM ouf_sem.validation_run WHERE revision_id=NEW.revision_id AND status='PASS'
      AND validated_row_version=NEW.row_version AND validated_content_hash=NEW.content_hash
      AND validated_content_hash=encode(public.digest(convert_to(NEW.label_json::text||NEW.description_json::text||
          NEW.definition_json::text,'UTF8'),'sha256'),'hex'))
 THEN RAISE EXCEPTION USING ERRCODE='P0841',MESSAGE='CURRENT_GREEN_VALIDATION_REQUIRED'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER check_datatype_review BEFORE UPDATE OF lifecycle_status ON ouf_sem.artifact_revision
 FOR EACH ROW WHEN (NEW.lifecycle_status='UNDER_REVIEW' AND OLD.lifecycle_status='DRAFT')
 EXECUTE FUNCTION ouf_sem.check_datatype_review();

-- An approved revision is frozen. Use the existing impact classifier and publication gates.
CREATE FUNCTION ouf_sem.datatype_revision_impact() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 PERFORM ouf_sem.compute_impact(previous.revision_id,r.revision_id,NEW.decided_by_subject)
 FROM ouf_sem.approval_challenge c JOIN ouf_sem.artifact_revision r USING(revision_id)
 JOIN ouf_sem.semantic_artifact a USING(artifact_id)
 JOIN LATERAL (SELECT p.revision_id FROM ouf_sem.artifact_revision p WHERE p.artifact_id=r.artifact_id
               AND p.revision_no<r.revision_no AND p.published_at IS NOT NULL ORDER BY p.revision_no DESC LIMIT 1) previous ON true
 WHERE c.challenge_id=NEW.challenge_id AND a.artifact_type='DATATYPE' AND r.revision_no>1
 AND NOT EXISTS (SELECT FROM ouf_sem.impact_report WHERE from_revision_id=previous.revision_id AND to_revision_id=r.revision_id);
 RETURN NEW;
END $$;
CREATE TRIGGER approved_datatype_impact AFTER INSERT ON ouf_sem.approval_decision
 FOR EACH ROW WHEN (NEW.decision='APPROVED') EXECUTE FUNCTION ouf_sem.datatype_revision_impact();

-- Capture the readable representation in the same transaction as activation, even
-- when a predecessor process completes an already prepared HUMAN publication.
CREATE FUNCTION ouf_sem.snapshot_datatype() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE iri text; graph text; additional text; n integer;
BEGIN
 SELECT semantic_id INTO iri FROM ouf_sem.semantic_artifact WHERE artifact_id=NEW.artifact_id AND artifact_type='DATATYPE';
 IF NOT FOUND THEN RETURN NEW; END IF;
 graph:='<'||iri||'> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2000/01/rdf-schema#Datatype> .'||chr(10)
     ||'<'||iri||'> <http://www.w3.org/1999/02/22-rdf-syntax-ns#value> '||
       to_jsonb(NEW.definition_json::text)::text||
       '^^<http://www.w3.org/1999/02/22-rdf-syntax-ns#JSON> .'||chr(10);
 SELECT string_agg(line,chr(10) ORDER BY line COLLATE "C"),count(*) INTO additional,n FROM (
  SELECT DISTINCT '<'||iri||'> <http://www.w3.org/2000/01/rdf-schema#'||predicate||'> '||
     to_jsonb(value)::text||'@'||lower(key)||' .' line
  FROM (VALUES ('label',NEW.label_json),('comment',NEW.description_json)) metadata(predicate,localized)
  CROSS JOIN LATERAL jsonb_each_text(localized)
  WHERE key ~ '^[a-zA-Z]+(-[a-zA-Z0-9]+)*$' AND value IS NOT NULL
 ) labels;
 IF n>0 THEN graph:=graph||additional||chr(10); END IF;
 INSERT INTO ouf_sem.revision_interchange_snapshot(revision_id,media_type,content_hash,content_bytes,statement_count,imported_by_subject)
 VALUES(NEW.revision_id,'application/n-triples',encode(public.digest(convert_to(graph,'UTF8'),'sha256'),'hex'),
        convert_to(graph,'UTF8'),2+n,NEW.created_by_subject);
 RETURN NEW;
END $$;
CREATE TRIGGER snapshot_published_datatype AFTER UPDATE OF lifecycle_status ON ouf_sem.artifact_revision
 FOR EACH ROW WHEN (NEW.lifecycle_status='ACTIVE' AND OLD.lifecycle_status<>'ACTIVE')
 EXECUTE FUNCTION ouf_sem.snapshot_datatype();
