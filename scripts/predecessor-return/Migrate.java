import org.flywaydb.core.Flyway;

/** Standalone CI migration executor, using the dependencies from the image under test. */
public class Migrate {
    public static void main(String[] args) {
        var flyway = Flyway.configure()
                .dataSource("jdbc:postgresql://127.0.0.1:5432/semantic", "semantic", "ci-only")
                .schemas("ouf_sem")
                .defaultSchema("ouf_sem")
                .locations("filesystem:/migration/sql")
                .group(false)
                .executeInTransaction(true)
                .validateOnMigrate(true)
                .load();
        flyway.migrate();
        flyway.validate();
    }
}
