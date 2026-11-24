package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.application.DiscoveryJobService;
import it.comune.trieste.ouf.semantic.application.DiscoveryService;
import it.comune.trieste.ouf.semantic.domain.SafeRdfParser;
import it.comune.trieste.ouf.semantic.ports.SemanticDiscoveryProvider;
import java.sql.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.flywaydb.core.Flyway;
import org.junit.jupiter.api.Test;
import org.springframework.boot.info.BuildProperties;
import org.springframework.jdbc.core.simple.JdbcClient;

/** Disposable CI database only: exercise upgrades through V19 using populated schemas. */
class DiscoveryFileMigrationContinuityTest {
  @Test void fileReceiptsHistoryAndDiscoveryBudgetsSurviveAdditiveUpgradeAndReconnect() throws Exception {
    String url=Objects.requireNonNull(System.getenv("OUF_SEM_DB_URL"),"isolated PostgreSQL fixture required");
    String user=Objects.requireNonNull(System.getenv("OUF_SEM_DB_USER"));
    String password=Objects.requireNonNull(System.getenv("OUF_SEM_DB_PASSWORD"));
    String database="m2_discovery_upgrade_"+UUID.randomUUID().toString().replace("-","");
    String dbUrl=url.substring(0,url.lastIndexOf('/')+1)+database;
    try(var control=DriverManager.getConnection(url,user,password)) {
      try(var statement=control.createStatement()){statement.execute("CREATE DATABASE "+database);}
      try {
        var before=Flyway.configure().dataSource(dbUrl,user,password).schemas("ouf_sem")
            .defaultSchema("ouf_sem").locations("classpath:db/migration").target("10").load();
        before.migrate();
        List<String> oldHistory;
        UUID legacy=UUID.randomUUID(),durable=UUID.randomUUID();
        try(var connection=DriverManager.getConnection(dbUrl,user,password)) {
          oldHistory=history(connection);
          assertThat(oldHistory).hasSize(10);
          try(var s=connection.createStatement()) {
            s.execute("insert into ouf_sem.proposal_command_receipt(tenant_id,principal_id,idempotency_key,operation,request_hash,result_json) values('fixture-tenant','fixture-user','same-file-intent','CREATE',repeat('a',64),'{\"revision\":1,\"proposalId\":\"retained\"}')");
          }
          try(var s=connection.prepareStatement("insert into ouf_sem.discovery_request(request_id,requested_artifact_type,intent,state,created_by_subject,attempt_count) values(?,'CLASS','retained discovery','PENDING','legacy-caller',5)")) {
            s.setObject(1,legacy);s.executeUpdate();
          }
          try(var s=connection.createStatement()) {
            s.executeUpdate("""
                insert into ouf_sem.discovery_candidate(candidate_id,request_id,provider_id,canonical_uri,source_location,
                  artifact_type,provider_trust,score,normalized_payload,content_hash,media_type,content_bytes,expires_at)
                select gen_random_uuid(),request_id,'TEST','urn:v4','urn:source','CLASS','HIGH',1,'{}',
                  encode(public.digest('v4','sha256'),'hex'),'text/turtle',convert_to('v4','UTF8'),now()+interval '1 hour'
                from ouf_sem.discovery_request
                """);
            s.execute("select ouf_sem.adopt_candidate(candidate_id,'urn:v4','urn:','v4','owner','authority','legacy-caller') from ouf_sem.discovery_candidate");
          }
        }
        var after=Flyway.configure().dataSource(dbUrl,user,password).schemas("ouf_sem")
            .defaultSchema("ouf_sem").locations("classpath:db/migration").target("13").load();
        assertThat(after.migrate().migrationsExecuted).isEqualTo(3);
        after.validate();
        try(var connection=DriverManager.getConnection(dbUrl,user,password)) {
          assertThat(history(connection).subList(0,10)).isEqualTo(oldHistory);
          assertThat(history(connection)).hasSize(13);
          assertThat(value(connection,"""
              select semantic_version || ':' || row_version || ':' || convert_from(s.content_bytes,'UTF8')
              from ouf_sem.artifact_revision r join ouf_sem.revision_rdf_snapshot s using(revision_id)
              where r.definition_json->'adoptionProvenance'->>'snapshotId'=s.snapshot_id::text
              """)).isEqualTo("1.0.0:1:v4");
          assertThat(value(connection,"select result_json->>'proposalId' from ouf_sem.proposal_command_receipt where idempotency_key='same-file-intent'" )).isEqualTo("retained");
          try(var s=connection.prepareStatement("select intent,state,attempt_count,worker_generation,recovery_state from ouf_sem.discovery_request where request_id=?")) {
            s.setObject(1,legacy);
            try(var row=s.executeQuery()) {
              assertThat(row.next()).isTrue();assertThat(row.getString(1)).isEqualTo("retained discovery");
              assertThat(row.getString(2)).isEqualTo("PENDING");assertThat(row.getInt(3)).isEqualTo(5);
              assertThat(row.getLong(4)).isZero();assertThat(row.getString(5)).isEqualTo("ACTIVE");
            }
          }
          // No worker or provider ran during migration. Preserve an exhausted incident explicitly.
          assertThat(value(connection,"select count(*)::text from ouf_sem.discovery_attempt")).isEqualTo("0");
          try(var s=connection.prepareStatement("insert into ouf_sem.discovery_request(request_id,requested_artifact_type,intent,state,created_by_subject,idempotency_key_hash,request_fingerprint,attempt_count,recovery_state,budget_deadline) values(?,'CLASS','durable intent','PENDING','composed-caller',repeat('b',64),repeat('c',64),128,'PAUSED_EXHAUSTED',clock_timestamp()-interval '1 second')")) {
            s.setObject(1,durable);s.executeUpdate();
          }
          try(var s=connection.createStatement()) {
            s.execute("insert into ouf_sem.discovery_dependency(scope_subject,provider_id,state,attempts,cumulative_attempts) values('composed-caller','TEST','PAUSED_EXHAUSTED',128,128)");
            s.execute("update ouf_sem.discovery_request set next_attempt_at=now()+interval '1 hour' where created_by_subject='legacy-caller'");
          }
          seedV13Block(connection,"D078","PROVIDER_UNKNOWN");
          seedV13Block(connection,"TLS","PROVIDER_TLS_UNPROVEN");
        }
        // Seed a real V13 publication and historical claims for the V16 reconciliation.
        String legacySet;
        try(var connection=DriverManager.getConnection(dbUrl,user,password);var statement=connection.createStatement()) {
          statement.execute("select ouf_sem.validate_revision(revision_id,'fixture') from ouf_sem.artifact_revision");
          statement.execute("""
              update ouf_sem.artifact_revision r set lifecycle_status='UNDER_REVIEW',content_hash=v.validated_content_hash
              from ouf_sem.validation_run v where v.revision_id=r.revision_id and v.status='PASS'
              """);
          statement.execute("""
              insert into ouf_sem.approval_challenge(challenge_id,revision_id,target_content_hash,status,expires_at,created_by_subject)
              select gen_random_uuid(),revision_id,content_hash,'APPROVED',now()+interval '15 minutes','fixture'
              from ouf_sem.artifact_revision
              """);
          statement.execute("""
              insert into ouf_sem.approval_decision(decision_id,challenge_id,decision,target_content_hash,decided_by_subject)
              select gen_random_uuid(),challenge_id,'APPROVED',target_content_hash,'fixture' from ouf_sem.approval_challenge
              """);
          legacySet=legacyPublish(connection,"v13-bound");
          statement.execute("insert into ouf_sem.publish_claim(idempotency_key,request_hash) values('v13-incomplete',repeat('c',64))");
          // A later manifest contains the same revision but has contradictory publication evidence.
          statement.execute("""
              insert into ouf_sem.semantic_publication_set
              select gen_random_uuid(),nextval('ouf_sem.publication_no_seq'),repeat('f',64),now(),'fixture','BUILDING'
              """);
          statement.execute("""
              insert into ouf_sem.semantic_publication_member
              select s.publication_set_id,a.semantic_id,r.revision_id from ouf_sem.semantic_publication_set s
              cross join ouf_sem.artifact_revision r join ouf_sem.semantic_artifact a using(artifact_id)
              where s.status='BUILDING'
              """);
          statement.execute("update ouf_sem.semantic_publication_set set status='PUBLISHED' where status='BUILDING'");
          statement.execute("""
              insert into ouf_sem.audit_event(event_id,event_type,subject_ref,resource_type,resource_id,detail_json)
              select gen_random_uuid(),'SEMANTIC_PUBLISHED','fixture','REVISION',m.revision_id::text,
                jsonb_build_object('publicationSetId',m.publication_set_id)
              from ouf_sem.semantic_publication_member m join ouf_sem.semantic_publication_set s using(publication_set_id)
              cross join generate_series(1,2) where s.checksum=repeat('f',64)
              """);
          statement.execute("""
              insert into ouf_sem.publish_claim(idempotency_key,request_hash,publication_set_id)
              select 'v13-ambiguous',r.content_hash,s.publication_set_id from ouf_sem.artifact_revision r
              cross join ouf_sem.semantic_publication_set s where s.checksum=repeat('f',64)
              """);
        }
        var v14=Flyway.configure().dataSource(dbUrl,user,password).schemas("ouf_sem").defaultSchema("ouf_sem")
            .locations("classpath:db/migration").target("14").load();
        assertThat(v14.migrate().migrationsExecuted).isOne();
        try(var connection=DriverManager.getConnection(dbUrl,user,password);var s=connection.createStatement()){
          // V14 could leave this dependency exhausted even though the failed job still had time.
          s.executeUpdate("update ouf_sem.discovery_dependency set state='PAUSED_EXHAUSTED',budget_deadline=now()-interval '1 hour' where provider_id='D078'");
        }
        var v15=Flyway.configure().dataSource(dbUrl,user,password).schemas("ouf_sem")
            .defaultSchema("ouf_sem").locations("classpath:db/migration").target("15").load();
        assertThat(v15.migrate().migrationsExecuted).isOne();
        try(var connection=DriverManager.getConnection(dbUrl,user,password)) {
          assertThat(history(connection)).hasSize(15);
          assertThat(value(connection,"select count(*) from ouf_sem.discovery_incident where state='OPEN' and opened_worker_version is null")).isEqualTo("2");
          assertThat(value(connection,"select count(*) from ouf_sem.claim_discovery_version_probe('new',array['TLS'])")).isEqualTo("0");
          try(var s=connection.createStatement()) {
            s.executeUpdate("""
                with review as (
                  insert into ouf_sem.artifact_revision(revision_id,artifact_id,revision_no,lifecycle_status,content_hash,created_by_subject)
                  select gen_random_uuid(),artifact_id,2,'UNDER_REVIEW',repeat('d',64),'fixture' from ouf_sem.semantic_artifact
                  returning revision_id,content_hash
                )
                insert into ouf_sem.approval_challenge(challenge_id,revision_id,target_content_hash,status,created_at,expires_at,created_by_subject)
                select gen_random_uuid(),revision_id,content_hash,'OPEN',now()-interval '1 hour',now()-interval '1 minute','fixture' from review
                """);
          }
        }
        var v16=Flyway.configure().dataSource(dbUrl,user,password).schemas("ouf_sem")
            .defaultSchema("ouf_sem").locations("classpath:db/migration").target("16").load();
        assertThat(v16.migrate().migrationsExecuted).isOne();
        var v17=Flyway.configure().dataSource(dbUrl,user,password).schemas("ouf_sem")
            .defaultSchema("ouf_sem").locations("classpath:db/migration").target("17").load();
        assertThat(v17.migrate().migrationsExecuted).isOne();
        var v18=Flyway.configure().dataSource(dbUrl,user,password).schemas("ouf_sem")
            .defaultSchema("ouf_sem").locations("classpath:db/migration").target("18").load();
        assertThat(v18.migrate().migrationsExecuted).isOne();
        String published="select to_jsonb(r)::text from ouf_sem.artifact_revision r where lifecycle_status='ACTIVE'";
        String beforeDescriptionUpgrade;
        try(var connection=DriverManager.getConnection(dbUrl,user,password)){
          beforeDescriptionUpgrade=value(connection,published);
        }
        // Reopening the fully upgraded database must preserve the history and all claims.
        var reopened=Flyway.configure().dataSource(dbUrl,user,password).schemas("ouf_sem")
            .defaultSchema("ouf_sem").locations("classpath:db/migration").load();
        assertThat(reopened.migrate().migrationsExecuted).isOne();
        assertThat(reopened.migrate().migrationsExecuted).isZero();
        reopened.validate();
        try(var connection=DriverManager.getConnection(dbUrl,user,password)) {
          assertThat(history(connection)).hasSize(19);
          assertThat(value(connection,published)).isEqualTo(beforeDescriptionUpgrade);
          assertThat(value(connection,"select count(*) from ouf_sem.discovery_request where fetch_denied_count<>0")).isEqualTo("0");
          // Exercise the running 1.0.2 publication signature on the upgraded schema.
          try(var statement=connection.createStatement()){
            statement.executeUpdate("update ouf_sem.discovery_request set state='RUNNING', worker_generation=1, lease_until=now()+interval '1 minute', budget_deadline=now()+interval '1 hour' where request_id='"+legacy+"'");
          }
          assertThat(value(connection,"select ouf_sem.publish_discovery_candidates('"+legacy+"',0,'[]',0,0,3)::text")).isEqualTo("false");
          assertThat(value(connection,"select ouf_sem.publish_discovery_candidates('"+legacy+"',1,'[]',1,2)::text")).isEqualTo("true");
          assertThat(value(connection,"select rdf_invalid_count||':'||rdf_bound_count||':'||fetch_denied_count from ouf_sem.discovery_request where request_id='"+legacy+"'")).isEqualTo("1:2:0");
          SemanticDiscoveryProvider provider=new SemanticDiscoveryProvider(){
            public String providerId(){return "D078";}
            public List<Candidate> search(Query query){return List.of();}
          };
          var release=new Properties();release.setProperty("version","new");
          var worker=new DiscoveryService(JdbcClient.create(reopened.getConfiguration().getDataSource()),List.of(provider),
              new SafeRdfParser(),new ObjectMapper(),new BuildProperties(release));
          assertThat(worker.executeOne()).isOne();
          assertThat(worker.executeOne()).isZero();
          assertThat(value(connection,"select state||':'||attempt_count from ouf_sem.discovery_request where created_by_subject='D078'")).isEqualTo("SUCCEEDED:2");
          assertThat(value(connection,"select state from ouf_sem.discovery_incident where provider_id='D078'")).isEqualTo("RESOLVED");
          assertThat(value(connection,"select state||':'||cumulative_attempts from ouf_sem.discovery_dependency where provider_id='D078'")).isEqualTo("HEALTHY:2");
          assertThat(history(connection).subList(0,10)).isEqualTo(oldHistory);
          assertThat(value(connection,"select attempt_count::text||':'||recovery_state from ouf_sem.discovery_request where idempotency_key_hash=repeat('b',64)")).isEqualTo("128:PAUSED_EXHAUSTED");
          assertThat(value(connection,"select cumulative_attempts::text||':'||state from ouf_sem.discovery_dependency where scope_subject='composed-caller'")).isEqualTo("128:PAUSED_EXHAUSTED");
          verifyFreshRequestAfterExpiry(JdbcClient.create(reopened.getConfiguration().getDataSource()));
          assertThat(value(connection,"select count(*) from ouf_sem.immutable_semantic_snapshot where ontology_rdf is not null")).isEqualTo("0");
          assertThat(legacyPublish(connection,"v13-bound")).isEqualTo(legacySet);
          assertThatThrownBy(()->legacyPublish(connection,"v13-incomplete"))
              .isInstanceOf(SQLException.class).hasMessageContaining("PUBLICATION_RECONCILIATION_REQUIRED");
          assertThatThrownBy(()->legacyPublish(connection,"v13-ambiguous"))
              .isInstanceOf(SQLException.class).hasMessageContaining("PUBLICATION_RECONCILIATION_REQUIRED");
          assertThat(value(connection,"select count(*) from ouf_sem.publish_claim where decision_id is null")).isEqualTo("2");
          assertThat(value(connection,"select ouf_sem.expire_review(revision_id,row_version,'fixture')::text from ouf_sem.artifact_revision where revision_no=2"))
              .isEqualTo("true");
          assertThat(value(connection,"""
              select c.status||':'||r.lifecycle_status||':'||r.row_version from ouf_sem.approval_challenge c
              join ouf_sem.artifact_revision r using(revision_id) where r.revision_no=2
              """)).isEqualTo("EXPIRED:DRAFT:1");
          try(var s=connection.createStatement()) {
            assertThatThrownBy(()->s.executeUpdate("update ouf_sem.proposal_command_receipt set result_json='{}' where idempotency_key='same-file-intent'"))
                .isInstanceOf(SQLException.class).hasMessageContaining("PROPOSAL_RECEIPT_IMMUTABLE");
          }
        }
      } finally {
        try(var statement=control.createStatement()){statement.execute("DROP DATABASE "+database+" WITH (FORCE)");}
      }
    }
  }
  private static void verifyFreshRequestAfterExpiry(JdbcClient db) {
    var calls=new AtomicInteger();
    String actor="mcp-discovery-v1:"+"d".repeat(64);
    SemanticDiscoveryProvider provider=new SemanticDiscoveryProvider(){
      public String providerId(){return "FRESH";}
      public List<Candidate> search(Query query){
        if(calls.incrementAndGet()==1)throw new IllegalStateException("fixture");
        assertThat(db.sql("""
            select d.attempts=1 and d.cumulative_attempts=2 and a.version_probe
              and a.previous_episode_attempts=1 and a.previous_budget_deadline<a.started_at
              and d.budget_deadline between a.started_at+interval '24 hours' and clock_timestamp()+interval '24 hours'
              and d.busy_until>clock_timestamp() and d.busy_until<=r.lease_until
              and i.state='OPEN' and i.code='PROVIDER_UNKNOWN'
            from ouf_sem.discovery_dependency d join ouf_sem.discovery_attempt a using(scope_subject,provider_id,generation,incident_id)
            join ouf_sem.discovery_incident i using(incident_id) join ouf_sem.discovery_request r on r.request_id=a.request_id
            where d.scope_subject=:actor and d.provider_id='FRESH'
            """).param("actor",actor).query(Boolean.class).single()).isTrue();
        return List.of();
      }
    };
    var json=new ObjectMapper();
    var release=new Properties();
    release.setProperty("version","v1");
    var original=new DiscoveryService(db,List.of(provider),new SafeRdfParser(),json,new BuildProperties(release));
    var jobs=new DiscoveryJobService(db,original,List.of(provider),json);
    UUID old=(UUID)jobs.request("CLASS","poi",List.of("it"),actor,"discovery-request-01").get("requestId");
    assertThat(original.executeOne()).isOne();
    assertThat(jobs.status(old,actor)).containsEntry("state","FAILED").containsEntry("attemptCount",1);
    db.sql("update ouf_sem.discovery_request set budget_deadline=now()-interval '1 hour' where request_id=:r").param("r",old).update();
    var failedReceipt=jobs.status(old,actor);
    db.sql("update ouf_sem.discovery_dependency set budget_deadline=now()-interval '1 hour',next_attempt_at=now() where scope_subject=:a")
        .param("a",actor).update();
    UUID same=(UUID)jobs.request("CLASS","poi",List.of("it"),actor,"discovery-request-02").get("requestId");
    assertThat(original.executeOne()).isOne();
    assertThat(jobs.status(same,actor)).containsEntry("state","FAILED");
    assertThat(calls).hasValue(1);
    release.setProperty("version","v2");
    var upgraded=new DiscoveryService(db,List.of(provider),new SafeRdfParser(),json,new BuildProperties(release));
    assertThat(upgraded.executeOne()).isZero();
    var newJobs=new DiscoveryJobService(db,upgraded,List.of(provider),json);
    UUID fresh=(UUID)newJobs.request("CLASS","poi",List.of("it"),actor,"discovery-request-03").get("requestId");
    assertThat(fresh).isNotEqualTo(old);
    assertThat(upgraded.executeOne()).isOne();
    assertThat(calls).hasValue(2);
    assertThat(newJobs.status(fresh,actor)).containsEntry("state","SUCCEEDED").containsEntry("attemptCount",1);
    assertThat(newJobs.request("CLASS","poi",List.of("it"),actor,"discovery-request-01")).isEqualTo(failedReceipt);
    assertThat(newJobs.providerStatus("FRESH",true,actor)).containsEntry("recoveryState","HEALTHY").containsEntry("cumulative_attempts",2L);
    assertThat(db.sql("""
        select a.outcome from ouf_sem.discovery_attempt a join ouf_sem.discovery_incident i using(incident_id)
        where i.scope_subject=:actor and i.state='RESOLVED' and i.attempts=2 order by a.generation
        """).param("actor",actor).query(String.class).list()).containsExactly("BLOCKED","SUCCESS");
  }
  private static void seedV13Block(Connection c,String provider,String code) throws SQLException {
    UUID job=UUID.randomUUID();
    try(var s=c.prepareStatement("""
        insert into ouf_sem.discovery_request(request_id,requested_artifact_type,intent,state,created_by_subject,
          attempt_count,worker_generation,lease_until,budget_deadline)
        values(?,'CLASS','poi','RUNNING',?,1,1,now()+interval '120 seconds',now()+interval '24 hours')
        """)){
      s.setObject(1,job);s.setString(2,provider);s.executeUpdate();
    }
    try(var s=c.createStatement()){
      s.execute("select ouf_sem.reserve_discovery_dependency('"+job+"',1,'"+provider+"')");
      s.execute("select ouf_sem.finish_discovery_dependency('"+job+"',1,'"+provider+"',1,'BLOCKED','"+code+"',0)");
      s.execute("select ouf_sem.finish_discovery_job('"+job+"',1,'BLOCKED','"+code+"','[]',null)");
      s.executeUpdate("update ouf_sem.discovery_dependency set next_attempt_at=now() where provider_id='"+provider+"'");
    }
  }
  private static String legacyPublish(Connection c,String fixtureKey) throws SQLException {
    try(var statement=c.prepareStatement("""
        select ouf_sem.publish_revision(c.revision_id,d.decision_id,?,d.target_content_hash,'fixture','test')
        from ouf_sem.approval_challenge c join ouf_sem.approval_decision d using(challenge_id)
        """)) {
      statement.setString(1,fixtureKey);
      try(var row=statement.executeQuery()){assertThat(row.next()).isTrue();return row.getString(1);}
    }
  }
  private static List<String> history(Connection c) throws SQLException {
    var rows=new ArrayList<String>();
    try(var s=c.createStatement();var r=s.executeQuery("select version,script,checksum from ouf_sem.flyway_schema_history where type='SQL' and success order by installed_rank")) {
      while(r.next())rows.add(r.getString(1)+":"+r.getString(2)+":"+r.getInt(3));
    }
    return rows;
  }
  private static String value(Connection c,String sql) throws SQLException {
    try(var s=c.createStatement();var r=s.executeQuery(sql)){assertThat(r.next()).isTrue();return r.getString(1);}
  }
}
