-- The receipt fence and the adoption effects share the proposal command transaction.
ALTER TABLE ouf_sem.proposal_command_receipt DROP CONSTRAINT proposal_command_receipt_operation_check,
 ADD CHECK (operation IN ('CREATE','VALIDATE','REVIEW','ADOPT'));

CREATE TABLE ouf_sem.revision_adoption (
 revision_id uuid PRIMARY KEY REFERENCES ouf_sem.artifact_revision,
 snapshot_id uuid NOT NULL UNIQUE REFERENCES ouf_sem.immutable_semantic_snapshot
);
CREATE TRIGGER revision_adoption_immutable BEFORE UPDATE OR DELETE ON ouf_sem.revision_adoption
 FOR EACH ROW EXECUTE FUNCTION ouf_sem.enforce_immutable();

-- Recover the exact V4 link using its audit event, never the latest origin or snapshot.
INSERT INTO ouf_sem.revision_adoption(revision_id,snapshot_id)
 SELECT r.revision_id,s.snapshot_id
 FROM ouf_sem.discovery_candidate c
 JOIN ouf_sem.artifact_revision r ON r.artifact_id=c.adopted_artifact_id AND r.revision_no=1
 JOIN ouf_sem.audit_event e ON e.event_type='SEMANTIC_CANDIDATE_ADOPTED' AND e.resource_type='CANDIDATE'
  AND e.resource_id=c.candidate_id::text AND e.detail_json->>'artifactId'=r.artifact_id::text
 JOIN ouf_sem.external_semantic_origin o ON o.artifact_id=r.artifact_id AND o.provider_id=c.provider_id
 JOIN ouf_sem.immutable_semantic_snapshot s ON s.origin_id=o.origin_id
  AND s.snapshot_id::text=e.detail_json->>'snapshotId' AND s.content_hash=c.content_hash;

CREATE FUNCTION ouf_sem.adoption_provenance(p_origin ouf_sem.external_semantic_origin,
 p_snapshot ouf_sem.immutable_semantic_snapshot) RETURNS jsonb LANGUAGE sql IMMUTABLE AS $$
 SELECT jsonb_build_object('providerId',p_origin.provider_id,'canonicalUri',p_origin.canonical_uri,
  'sourceLocation',p_origin.source_url,'publisher',p_origin.publisher,'license',p_origin.license_ref,
  'licenseWarning',CASE WHEN p_origin.license_ref IS NULL THEN 'licenza mancante' END,
  'snapshotId',p_snapshot.snapshot_id,'rdfSha256',p_snapshot.content_hash)
$$;

-- Prior approvals remain historical. Only editable drafts receive a new fingerprint/version.
UPDATE ouf_sem.artifact_revision r
 SET semantic_version=coalesce(nullif(r.semantic_version,''),'1.0.0'),row_version=r.row_version+1,
 definition_json=r.definition_json || jsonb_build_object('adoptionProvenance',ouf_sem.adoption_provenance(o,s))
 FROM ouf_sem.revision_adoption b JOIN ouf_sem.immutable_semantic_snapshot s USING(snapshot_id)
 JOIN ouf_sem.external_semantic_origin o USING(origin_id)
 WHERE r.revision_id=b.revision_id AND r.lifecycle_status='DRAFT';

CREATE FUNCTION ouf_sem.retain_adoption_provenance() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF EXISTS (SELECT 1 FROM ouf_sem.revision_adoption WHERE revision_id=OLD.revision_id)
    AND OLD.definition_json ? 'adoptionProvenance' THEN
  NEW.definition_json=jsonb_set(NEW.definition_json,'{adoptionProvenance}',OLD.definition_json->'adoptionProvenance');
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER retain_adoption_provenance BEFORE UPDATE OF definition_json ON ouf_sem.artifact_revision
 FOR EACH ROW EXECUTE FUNCTION ouf_sem.retain_adoption_provenance();

CREATE VIEW ouf_sem.revision_rdf_snapshot AS
 SELECT revision_id,NULL::uuid snapshot_id,media_type,content_hash,content_bytes,statement_count
 FROM ouf_sem.revision_interchange_snapshot
 UNION ALL
 SELECT b.revision_id,s.snapshot_id,s.media_type,s.content_hash,s.content_bytes,NULL::bigint
 FROM ouf_sem.revision_adoption b JOIN ouf_sem.immutable_semantic_snapshot s USING(snapshot_id);

CREATE FUNCTION ouf_sem.adopt_candidate(p_candidate uuid,p_semantic_id text,p_namespace text,p_local_name text,
 p_owner text,p_authority text,p_actor text,p_publisher text,p_license text,p_definition jsonb)
RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE
 c ouf_sem.discovery_candidate;
 o ouf_sem.external_semantic_origin;
 s ouf_sem.immutable_semantic_snapshot;
 artifact uuid:=gen_random_uuid();
 revision uuid:=gen_random_uuid();
BEGIN
 SELECT * INTO STRICT c FROM ouf_sem.discovery_candidate WHERE candidate_id=p_candidate FOR UPDATE;
 IF c.expires_at<=clock_timestamp() THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='CANDIDATE_EXPIRED'; END IF;
 IF c.adopted_at IS NOT NULL THEN RETURN c.adopted_artifact_id; END IF;
 IF encode(public.digest(c.content_bytes,'sha256'),'hex')<>c.content_hash THEN
  RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='CANDIDATE_HASH_MISMATCH';
 END IF;
 INSERT INTO ouf_sem.semantic_artifact(artifact_id,semantic_id,artifact_type,namespace,local_name,owner_ref,authority_ref,origin_kind)
 VALUES(artifact,p_semantic_id,c.artifact_type,p_namespace,p_local_name,p_owner,p_authority,'EXTERNAL');
 INSERT INTO ouf_sem.external_semantic_origin(origin_id,artifact_id,canonical_uri,provider_id,source_url,publisher,license_ref,upstream_status,last_checked_at)
 VALUES(gen_random_uuid(),artifact,c.canonical_uri,c.provider_id,c.source_location,p_publisher,p_license,'ACTIVE',transaction_timestamp())
 RETURNING * INTO o;
 INSERT INTO ouf_sem.immutable_semantic_snapshot(snapshot_id,origin_id,content_hash,media_type,content_bytes,retrieved_at)
 VALUES(gen_random_uuid(),o.origin_id,c.content_hash,c.media_type,c.content_bytes,transaction_timestamp()) RETURNING * INTO s;
 INSERT INTO ouf_sem.artifact_revision(revision_id,artifact_id,revision_no,semantic_version,lifecycle_status,definition_json,content_hash,created_by_subject)
 VALUES(revision,artifact,1,'1.0.0','DRAFT',c.normalized_payload || p_definition ||
  jsonb_build_object('adoptionProvenance',ouf_sem.adoption_provenance(o,s)),c.content_hash,p_actor);
 INSERT INTO ouf_sem.revision_adoption VALUES(revision,s.snapshot_id);
 UPDATE ouf_sem.discovery_candidate SET adopted_at=clock_timestamp(),adopted_artifact_id=artifact
 WHERE candidate_id=p_candidate AND expires_at>clock_timestamp();
 IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='CANDIDATE_EXPIRED'; END IF;
 INSERT INTO ouf_sem.audit_event(event_id,event_type,subject_ref,resource_type,resource_id,detail_json)
 VALUES(gen_random_uuid(),'SEMANTIC_CANDIDATE_ADOPTED',p_actor,'CANDIDATE',p_candidate::text,
  jsonb_build_object('artifactId',artifact,'revisionId',revision,'snapshotId',s.snapshot_id,'requestId',c.request_id));
 RETURN artifact;
END $$;

-- Preserve the native seven-argument SQL contract.
CREATE OR REPLACE FUNCTION ouf_sem.adopt_candidate(p_candidate uuid,p_semantic_id text,p_namespace text,
 p_local_name text,p_owner text,p_authority text,p_actor text)
RETURNS uuid LANGUAGE sql AS $$
 SELECT ouf_sem.adopt_candidate(p_candidate,p_semantic_id,p_namespace,p_local_name,p_owner,p_authority,p_actor,
  NULL::text,NULL::text,'{}'::jsonb)
$$;
