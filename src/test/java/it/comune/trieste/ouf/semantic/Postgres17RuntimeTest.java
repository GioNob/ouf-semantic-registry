package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.regex.Pattern;
import org.flywaydb.core.Flyway;
import org.flywaydb.core.api.MigrationState;
import org.flywaydb.core.api.MigrationVersion;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.core.io.support.PathMatchingResourcePatternResolver;
import org.springframework.jdbc.core.simple.JdbcClient;

@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
class Postgres17RuntimeTest {
  @Autowired JdbcClient db;
  @Autowired Flyway flyway;
  @Test void runsAllFlywayMigrationsOnPostgresql17(){String version=db.sql("select version()").query(String.class).single();assertThat(version).startsWith("PostgreSQL 17.");long migrations=db.sql("select count(*) from ouf_sem.flyway_schema_history where success").query(Long.class).single();assertThat(migrations).isGreaterThanOrEqualTo(6);}
  @Test void criticalDatabaseFunctionsAreInstalled(){var names=db.sql("select proname from pg_proc join pg_namespace n on n.oid=pronamespace where n.nspname='ouf_sem'").query(String.class).list();assertThat(names).contains("publish_revision","validate_revision","compute_impact","create_change_notice","claim_discovery_job");}

  @Test void previousImageValidatesTheDatabaseAfterV13(@TempDir Path previousMigrations) throws IOException {
    var v13 = MigrationVersion.fromVersion("13");
    assertThat(flyway.info().applied())
        .anySatisfy(migration -> {
          assertThat(migration.getVersion()).isEqualTo(v13);
          assertThat(migration.getState()).isEqualTo(MigrationState.SUCCESS);
        });

    var versions = new ArrayList<Integer>();
    var versionedSql = Pattern.compile("V([0-9]+)__.+\\.sql");
    var resources = new PathMatchingResourcePatternResolver().getResources("classpath:db/migration/V*.sql");
    for (var resource : resources) {
      var name = resource.getFilename();
      var match = versionedSql.matcher(name);
      if (!match.matches()) {
        continue;
      }
      int version = Integer.parseInt(match.group(1));
      if (version > 12) {
        continue;
      }
      versions.add(version);
      try (var sql = resource.getInputStream()) {
        Files.copy(sql, previousMigrations.resolve(name));
      }
    }
    assertThat(versions).containsExactlyInAnyOrder(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12);

    // Use the configuration bound from application.yml, including Flyway's default validation rules.
    var previousImage = Flyway.configure()
        .configuration(flyway.getConfiguration())
        .locations("filesystem:" + previousMigrations.toString().replace('\\', '/'))
        .load();
    assertThat(previousImage.info().applied())
        .anySatisfy(migration -> {
          assertThat(migration.getVersion()).isEqualTo(v13);
          assertThat(migration.getState()).isEqualTo(MigrationState.FUTURE_SUCCESS);
        });
    previousImage.validate();
  }
}
