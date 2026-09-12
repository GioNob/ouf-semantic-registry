package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.*;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.simple.JdbcClient;

@SpringBootTest(properties={
    "ouf.semantic.discovery-worker.enabled=false",
    "ouf.semantic.providers.schema-gov.enabled=false"
})
class DatabaseBehaviorRuntimeTest {
  @Autowired JdbcClient db;

  @Test
  void validatedApprovalPublishesAtomicallyAndReplaysIdempotently() {
    UUID artifact=UUID.randomUUID(), revision=UUID.randomUUID();
    insertArtifact(artifact,revision,"ouf:test:"+artifact,"UNDER_REVIEW","1.0.0");

    UUID validation=db.sql("select ouf_sem.validate_revision(:r,'tester')")
        .param("r",revision).query(UUID.class).single();
    String hash=db.sql("select validated_content_hash from ouf_sem.validation_run where validation_run_id=:v")
        .param("v",validation).query(String.class).single();
    assertThat(db.sql("select status from ouf_sem.validation_run where validation_run_id=:v")
        .param("v",validation).query(String.class).single()).isEqualTo("PASS");
    db.sql("update ouf_sem.artifact_revision set content_hash=:h where revision_id=:r")
        .param("h",hash).param("r",revision).update();

    UUID challenge=UUID.randomUUID(),decision=UUID.randomUUID();
    db.sql("""
        insert into ouf_sem.approval_challenge
          (challenge_id,revision_id,target_content_hash,status,expires_at,created_by_subject)
        values(:c,:r,:h,'APPROVED',transaction_timestamp()+interval '5 minutes','reviewer')
        """).param("c",challenge).param("r",revision).param("h",hash).update();
    db.sql("""
        insert into ouf_sem.approval_decision
          (decision_id,challenge_id,decision,target_content_hash,decided_by_subject)
        values(:d,:c,'APPROVED',:h,'reviewer')
        """).param("d",decision).param("c",challenge).param("h",hash).update();

    String key="publish-"+revision;
    UUID first=publish(revision,decision,key,hash,"corr-1");
    UUID replay=publish(revision,decision,key,hash,"corr-1");
    assertThat(replay).isEqualTo(first);
    assertThat(db.sql("select lifecycle_status from ouf_sem.artifact_revision where revision_id=:r")
        .param("r",revision).query(String.class).single()).isEqualTo("ACTIVE");
    assertThat(db.sql("select count(*) from ouf_sem.audit_event where resource_id=:r")
        .param("r",revision.toString()).query(Long.class).single()).isEqualTo(1);
    assertThatThrownBy(()->publish(revision,decision,key,"f".repeat(64),"corr-2"))
        .hasStackTraceContaining("IDEMPOTENCY_CONFLICT");
  }

  @Test
  void activationWithoutMatchingGreenValidationFailsClosed() {
    UUID artifact=UUID.randomUUID(), revision=UUID.randomUUID();
    insertArtifact(artifact,revision,"ouf:test:"+artifact,"UNDER_REVIEW","1.0.0");
    assertThatThrownBy(()->db.sql("""
        update ouf_sem.artifact_revision
        set lifecycle_status='ACTIVE',published_at=transaction_timestamp()
        where revision_id=:r
        """).param("r",revision).update())
        .hasStackTraceContaining("SEMANTIC_VALIDATION_REQUIRED");
  }

  @Test
  void governedLifecycleDeprecatesAndRetiresWithoutDeletingHistory() {
    UUID artifact=UUID.randomUUID(),revision=UUID.randomUUID();
    db.sql("insert into ouf_sem.semantic_artifact(artifact_id,semantic_id,artifact_type,namespace,local_name,owner_ref,authority_ref,origin_kind) values(:a,:s,'CLASS','test',:n,'owner','authority','OUF')")
        .param("a",artifact).param("s","ouf:lifecycle:"+artifact).param("n",artifact.toString()).update();
    db.sql("insert into ouf_sem.artifact_revision(revision_id,artifact_id,revision_no,lifecycle_status,semantic_version,label_json,description_json,definition_json,content_hash,created_by_subject,published_at) values(:r,:a,1,'ACTIVE','1.0.0','{}','{}','{}',:h,'tester',transaction_timestamp())")
        .param("r",revision).param("a",artifact).param("h","a".repeat(64)).update();
    db.sql("insert into ouf_sem.artifact_active_revision values(:a,:r,transaction_timestamp(),'tester')").param("a",artifact).param("r",revision).update();
    assertThat(db.sql("select ouf_sem.govern_revision_lifecycle(:r,'DEPRECATED','human','authz:test','corr')").param("r",revision).query(String.class).single()).isEqualTo("DEPRECATED");
    assertThat(db.sql("select ouf_sem.govern_revision_lifecycle(:r,'RETIRED','human','authz:test','corr')").param("r",revision).query(String.class).single()).isEqualTo("RETIRED");
    assertThat(db.sql("select count(*) from ouf_sem.artifact_revision where revision_id=:r").param("r",revision).query(Long.class).single()).isOne();
    assertThat(db.sql("select count(*) from ouf_sem.audit_event where resource_id=:r and event_type in ('SEMANTIC_DEPRECATED','SEMANTIC_RETIRED')").param("r",revision.toString()).query(Long.class).single()).isEqualTo(2);
  }

  @Test
  void candidateAdoptionIsIdempotentAndFreezesSourceBytes() {
    UUID request=UUID.randomUUID(),candidate=UUID.randomUUID();
    byte[] payload="@prefix ex: <https://example.test/> .".getBytes(StandardCharsets.UTF_8);
    db.sql("""
        insert into ouf_sem.discovery_request
          (request_id,requested_artifact_type,intent,state,created_by_subject)
        values(:r,'CLASS','place','SUCCEEDED','tester')
        """).param("r",request).update();
    db.sql("""
        insert into ouf_sem.discovery_candidate
          (candidate_id,request_id,provider_id,canonical_uri,source_location,
           artifact_type,provider_trust,score,normalized_payload,content_hash,
           media_type,content_bytes,expires_at)
        values(:c,:r,'SCHEMA_GOV_IT',:uri,:uri,'CLASS','HIGH',0.9,'{}',:h,
               'text/turtle',:bytes,transaction_timestamp()+interval '1 hour')
        """).param("c",candidate).param("r",request)
        .param("uri","https://schema.gov.it/test/"+candidate)
        .param("h",sha256(payload)).param("bytes",payload).update();

    String semanticId="ouf:adopted:"+candidate;
    UUID first=adopt(candidate,semanticId);
    UUID replay=adopt(candidate,semanticId);
    assertThat(replay).isEqualTo(first);
    assertThat(db.sql("""
        select count(*) from ouf_sem.immutable_semantic_snapshot s
        join ouf_sem.external_semantic_origin o using(origin_id)
        where o.artifact_id=:a
        """).param("a",first).query(Long.class).single()).isEqualTo(1);
    assertThatThrownBy(()->db.sql("update ouf_sem.discovery_candidate set content_bytes='x' where candidate_id=:c")
        .param("c",candidate).update()).hasStackTraceContaining("published semantic state is immutable");
  }

  private void insertArtifact(UUID artifact,UUID revision,String semanticId,String state,String version) {
    db.sql("""
        insert into ouf_sem.semantic_artifact
          (artifact_id,semantic_id,artifact_type,namespace,local_name,owner_ref,authority_ref,origin_kind)
        values(:a,:s,'CLASS','test',:n,'owner','authority','OUF')
        """).param("a",artifact).param("s",semanticId).param("n",artifact.toString()).update();
    db.sql("""
        insert into ouf_sem.artifact_revision
          (revision_id,artifact_id,revision_no,lifecycle_status,semantic_version,
           label_json,description_json,definition_json,created_by_subject)
        values(:r,:a,1,:state,:version,'{"it":"Luogo"}','{"it":"Descrizione"}','{}','tester')
        """).param("r",revision).param("a",artifact).param("state",state).param("version",version).update();
  }

  private UUID publish(UUID revision,UUID decision,String key,String hash,String correlation) {
    return db.sql("select ouf_sem.publish_revision(:r,:d,:k,:h,'tester',:c)")
        .param("r",revision).param("d",decision).param("k",key).param("h",hash)
        .param("c",correlation).query(UUID.class).single();
  }

  private UUID adopt(UUID candidate,String semanticId) {
    return db.sql("select ouf_sem.adopt_candidate(:c,:s,'ouf','Place','owner','authority','tester')")
        .param("c",candidate).param("s",semanticId).query(UUID.class).single();
  }

  private static String sha256(byte[] value) {
    try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value));}
    catch(Exception e){throw new IllegalStateException(e);}
  }
}
