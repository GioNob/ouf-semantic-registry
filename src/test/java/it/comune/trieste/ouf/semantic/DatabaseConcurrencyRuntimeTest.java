package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.*;

import java.sql.*;
import java.time.Duration;
import java.util.UUID;
import java.util.concurrent.*;
import javax.sql.DataSource;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.simple.JdbcClient;

@SpringBootTest(properties={
    "ouf.semantic.discovery-worker.enabled=false",
    "ouf.semantic.providers.schema-gov.enabled=false"
})
class DatabaseConcurrencyRuntimeTest {
  @Autowired DataSource dataSource;
  @Autowired JdbcClient db;

  @Test
  void skipLockedAssignsDifferentJobsWhileFirstTransactionStillOwnsItsLease() throws Exception {
    UUID first=insertPendingDiscovery(),second=insertPendingDiscovery();
    CountDownLatch firstClaimed=new CountDownLatch(1),releaseFirst=new CountDownLatch(1);
    try(ExecutorService pool=Executors.newVirtualThreadPerTaskExecutor()){
      Future<UUID> a=pool.submit(()->claimAndHold("worker-a",firstClaimed,releaseFirst));
      assertThat(firstClaimed.await(5,TimeUnit.SECONDS)).isTrue();
      Future<UUID> b=pool.submit(()->claim("worker-b"));
      UUID secondClaim=b.get(5,TimeUnit.SECONDS);
      releaseFirst.countDown();
      UUID firstClaim=a.get(5,TimeUnit.SECONDS);
      assertThat(firstClaim).isIn(first,second);
      assertThat(secondClaim).isIn(first,second).isNotEqualTo(firstClaim);
    } finally {
      releaseFirst.countDown();
    }
  }

  @Test
  void expiredLeaseIsReclaimedAndAttemptCounterAdvances() {
    UUID request=UUID.randomUUID();
    db.sql("""
        insert into ouf_sem.discovery_request
          (request_id,requested_artifact_type,intent,state,attempt_count,lease_until,created_by_subject)
        values(:r,'CLASS','recover','RUNNING',1,transaction_timestamp()-interval '1 second','tester')
        """).param("r",request).update();
    UUID claimed=db.sql("select request_id from ouf_sem.claim_discovery_job('recovery-worker',30)")
        .query(UUID.class).single();
    assertThat(claimed).isEqualTo(request);
    assertThat(db.sql("select attempt_count from ouf_sem.discovery_request where request_id=:r")
        .param("r",request).query(Integer.class).single()).isEqualTo(2);
    assertThat(db.sql("select lease_until>transaction_timestamp() from ouf_sem.discovery_request where request_id=:r")
        .param("r",request).query(Boolean.class).single()).isTrue();
  }

  @Test
  void concurrentPublicationWithSameClaimReturnsOnePublicationSet() throws Exception {
    PublicationFixture f=publicationFixture();
    CyclicBarrier start=new CyclicBarrier(2);
    try(ExecutorService pool=Executors.newVirtualThreadPerTaskExecutor()){
      Callable<UUID> call=()->{
        start.await(5,TimeUnit.SECONDS);
        try(Connection c=dataSource.getConnection();
            PreparedStatement p=c.prepareStatement("select ouf_sem.publish_revision(?,?,?,?,?,?)")){
          p.setObject(1,f.revision());p.setObject(2,f.decision());p.setString(3,f.key());
          p.setString(4,f.hash());p.setString(5,"tester");p.setString(6,"concurrent");
          try(ResultSet r=p.executeQuery()){r.next();return r.getObject(1,UUID.class);}
        }
      };
      Future<UUID> a=pool.submit(call),b=pool.submit(call);
      UUID x=a.get(10,TimeUnit.SECONDS),y=b.get(10,TimeUnit.SECONDS);
      assertThat(x).isEqualTo(y);
      assertThat(db.sql("select count(*) from ouf_sem.publish_claim where idempotency_key=:k")
          .param("k",f.key()).query(Long.class).single()).isEqualTo(1);
      assertThat(db.sql("select count(*) from ouf_sem.audit_event where resource_id=:r")
          .param("r",f.revision().toString()).query(Long.class).single()).isEqualTo(1);
    }
  }

  @Test
  void concurrentDraftCasAllowsExactlyOneWriter() throws Exception {
    UUID artifact=UUID.randomUUID(),revision=UUID.randomUUID();
    db.sql("""
        insert into ouf_sem.semantic_artifact
          (artifact_id,semantic_id,artifact_type,namespace,local_name,owner_ref,authority_ref,origin_kind)
        values(:a,:s,'CLASS','test',:n,'owner','authority','OUF')
        """).param("a",artifact).param("s","ouf:cas:"+artifact).param("n",artifact.toString()).update();
    db.sql("""
        insert into ouf_sem.artifact_revision
          (revision_id,artifact_id,revision_no,lifecycle_status,created_by_subject)
        values(:r,:a,1,'DRAFT','tester')
        """).param("r",revision).param("a",artifact).update();

    CyclicBarrier start=new CyclicBarrier(2);
    try(ExecutorService pool=Executors.newVirtualThreadPerTaskExecutor()){
      Callable<Boolean> writer=()->{
        start.await(5,TimeUnit.SECONDS);
        try(Connection c=dataSource.getConnection();
            PreparedStatement p=c.prepareStatement("select ouf_sem.edit_draft(?,0,'{}'::jsonb,'{}'::jsonb)")){
          p.setObject(1,revision);p.executeQuery();return true;
        }catch(SQLException e){
          if("40001".equals(e.getSQLState()))return false;
          throw e;
        }
      };
      Future<Boolean> a=pool.submit(writer),b=pool.submit(writer);
      assertThat(java.util.List.of(a.get(10,TimeUnit.SECONDS),b.get(10,TimeUnit.SECONDS)))
          .containsExactlyInAnyOrder(true,false);
      assertThat(db.sql("select row_version from ouf_sem.artifact_revision where revision_id=:r")
          .param("r",revision).query(Long.class).single()).isEqualTo(1);
    }
  }

  private UUID insertPendingDiscovery(){
    UUID id=UUID.randomUUID();
    db.sql("""
        insert into ouf_sem.discovery_request
          (request_id,requested_artifact_type,intent,state,created_by_subject)
        values(:r,'CLASS','concurrency','PENDING','tester')
        """).param("r",id).update();
    return id;
  }

  private UUID claimAndHold(String worker,CountDownLatch claimed,CountDownLatch release) throws Exception {
    try(Connection c=dataSource.getConnection()){
      c.setAutoCommit(false);
      UUID id=claim(c,worker);
      claimed.countDown();
      assertThat(release.await(5,TimeUnit.SECONDS)).isTrue();
      c.commit();
      return id;
    }
  }

  private UUID claim(String worker) throws SQLException {
    try(Connection c=dataSource.getConnection()){return claim(c,worker);}
  }

  private static UUID claim(Connection c,String worker) throws SQLException {
    try(PreparedStatement p=c.prepareStatement("select request_id from ouf_sem.claim_discovery_job(?,30)")){
      p.setString(1,worker);
      try(ResultSet r=p.executeQuery()){
        assertThat(r.next()).isTrue();
        return r.getObject(1,UUID.class);
      }
    }
  }

  private PublicationFixture publicationFixture(){
    UUID artifact=UUID.randomUUID(),revision=UUID.randomUUID(),challenge=UUID.randomUUID(),decision=UUID.randomUUID();
    db.sql("""
        insert into ouf_sem.semantic_artifact
          (artifact_id,semantic_id,artifact_type,namespace,local_name,owner_ref,authority_ref,origin_kind)
        values(:a,:s,'CLASS','test',:n,'owner','authority','OUF')
        """).param("a",artifact).param("s","ouf:publish:"+artifact).param("n",artifact.toString()).update();
    db.sql("""
        insert into ouf_sem.artifact_revision
          (revision_id,artifact_id,revision_no,lifecycle_status,semantic_version,
           label_json,description_json,definition_json,created_by_subject)
        values(:r,:a,1,'UNDER_REVIEW','1.0.0','{"it":"Luogo"}','{"it":"Descrizione"}','{}','tester')
        """).param("r",revision).param("a",artifact).update();
    UUID validation=db.sql("select ouf_sem.validate_revision(:r,'tester')")
        .param("r",revision).query(UUID.class).single();
    String hash=db.sql("select validated_content_hash from ouf_sem.validation_run where validation_run_id=:v")
        .param("v",validation).query(String.class).single();
    db.sql("update ouf_sem.artifact_revision set content_hash=:h where revision_id=:r")
        .param("h",hash).param("r",revision).update();
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
    return new PublicationFixture(revision,decision,"concurrent-publish-"+revision,hash);
  }

  private record PublicationFixture(UUID revision,UUID decision,String key,String hash){}
}
