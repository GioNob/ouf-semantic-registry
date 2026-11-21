package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.*;
import java.sql.*;
import java.util.*;
import org.flywaydb.core.Flyway;
import org.junit.jupiter.api.Test;

/** Disposable CI database only: exercise the real file V10 -> discovery V13 upgrade. */
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
          }
        }
        // Exercise V15 with an actual V13 publish and an incomplete old claim.
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
        var upgrade=Flyway.configure().dataSource(dbUrl,user,password).schemas("ouf_sem")
            .defaultSchema("ouf_sem").locations("classpath:db/migration").load();
        upgrade.migrate();
        try(var connection=DriverManager.getConnection(dbUrl,user,password)) {
          assertThat(legacyPublish(connection,"v13-bound")).isEqualTo(legacySet);
          assertThatThrownBy(()->legacyPublish(connection,"v13-incomplete"))
              .isInstanceOf(SQLException.class).hasMessageContaining("PUBLICATION_RECONCILIATION_REQUIRED");
          assertThatThrownBy(()->legacyPublish(connection,"v13-ambiguous"))
              .isInstanceOf(SQLException.class).hasMessageContaining("PUBLICATION_RECONCILIATION_REQUIRED");
          assertThat(value(connection,"select count(*) from ouf_sem.publish_claim where decision_id is null")).isEqualTo("2");
        }
        // New Flyway instance and physical connection cannot recreate or reset committed history.
        var reopened=Flyway.configure().dataSource(dbUrl,user,password).schemas("ouf_sem")
            .defaultSchema("ouf_sem").locations("classpath:db/migration").load();
        assertThat(reopened.migrate().migrationsExecuted).isZero();reopened.validate();
        try(var connection=DriverManager.getConnection(dbUrl,user,password)) {
          assertThat(history(connection).subList(0,10)).isEqualTo(oldHistory);
          assertThat(value(connection,"select attempt_count::text||':'||recovery_state from ouf_sem.discovery_request where idempotency_key_hash=repeat('b',64)")).isEqualTo("128:PAUSED_EXHAUSTED");
          assertThat(value(connection,"select cumulative_attempts::text||':'||state from ouf_sem.discovery_dependency where scope_subject='composed-caller'")).isEqualTo("128:PAUSED_EXHAUSTED");
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
