package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.*;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.simple.JdbcClient;

@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
class Postgres17RuntimeTest {
  @Autowired JdbcClient db;
  @Test void runsAllFlywayMigrationsOnPostgresql17(){String version=db.sql("select version()").query(String.class).single();assertThat(version).startsWith("PostgreSQL 17.");long migrations=db.sql("select count(*) from ouf_sem.flyway_schema_history where success").query(Long.class).single();assertThat(migrations).isGreaterThanOrEqualTo(6);}
  @Test void criticalDatabaseFunctionsAreInstalled(){var names=db.sql("select proname from pg_proc join pg_namespace n on n.oid=pronamespace where n.nspname='ouf_sem'").query(String.class).list();assertThat(names).contains("publish_revision","validate_revision","compute_impact","create_change_notice","claim_discovery_job");}
}
