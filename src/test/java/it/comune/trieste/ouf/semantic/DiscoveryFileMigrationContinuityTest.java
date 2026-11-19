package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.*;
import java.sql.*;
import java.util.*;
import org.flywaydb.core.Flyway;
import org.junit.jupiter.api.Test;

/** Disposable CI database only: exercise the real file V10 -> discovery V12 upgrade. */
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
        }
        var after=Flyway.configure().dataSource(dbUrl,user,password).schemas("ouf_sem")
            .defaultSchema("ouf_sem").locations("classpath:db/migration").load();
        assertThat(after.migrate().migrationsExecuted).isEqualTo(2);
        after.validate();
        try(var connection=DriverManager.getConnection(dbUrl,user,password)) {
          assertThat(history(connection).subList(0,10)).isEqualTo(oldHistory);
          assertThat(history(connection)).hasSize(12);
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
