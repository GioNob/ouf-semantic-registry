package it.comune.trieste.ouf.semantic.application;

import static it.comune.trieste.ouf.semantic.application.PublishedBatchSearch.*;
import static org.assertj.core.api.Assertions.assertThat;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.sql.DriverManager;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.stream.IntStream;
import org.flywaydb.core.Flyway;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestReporter;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;

/** SEM-51O-03. Measure the same catalog before and after its V22 -> V23 upgrade. */
class PublishedBatchIndexMeasureTest {
  private static final ObjectMapper JSON = new ObjectMapper();
  // 51l sends one filter per DISTINCT (type, namespace, domain, range) to PostgreSQL.
  private static final String BEFORE = """
      select f.idx,a.artifact_id,a.semantic_id,a.local_name,r.semantic_version,r.revision_id,
             p.publication_set_id,r.label_json::text as label_json
      %s
      join jsonb_array_elements(cast(? as jsonb)) with ordinality f(data,idx)
        on a.artifact_type=f.data->>'type'
       and (f.data->>'namespace' is null or a.namespace=f.data->>'namespace')
       and (f.data->>'domain' is null or %s)
       and (f.data->>'range' is null or %s)
      where r.lifecycle_status='ACTIVE' and %s
      """.formatted(SemanticReadService.SEARCH_JOINS, SemanticReadService.referenceFilter("DOMAIN","f.data->>'domain'"),
          SemanticReadService.referenceFilter("RANGE","f.data->>'range'"), SemanticReadService.CURRENT_PUBLISHED);

  @Test void measures64IntentsOn5000PublishedArtifacts(TestReporter reporter) throws Exception {
    String url = Objects.requireNonNull(System.getenv("OUF_SEM_DB_URL"));
    String user = System.getenv("OUF_SEM_DB_USER"), password = System.getenv("OUF_SEM_DB_PASSWORD");
    String database = "batch_measure_" + UUID.randomUUID().toString().replace("-", "");
    try (var admin = DriverManager.getConnection(url,user,password); var ddl = admin.createStatement()) {
      ddl.execute("CREATE DATABASE " + database);
      try {
        var source = new DriverManagerDataSource(url.substring(0,url.lastIndexOf('/')+1)+database,user,password);
        var flyway = Flyway.configure().dataSource(source).schemas("ouf_sem").defaultSchema("ouf_sem");
        flyway.target("22").load().migrate();
        var db = new JdbcTemplate(source);
        seed(db);
        var filter = new Filter(ArtifactType.CLASS,"fixture",null,null);
        List<Intent> intents = IntStream.rangeClosed(1,64).mapToObj(i -> new Intent("i"+i,
            String.format(Locale.ROOT,"term-%05d",i),List.of("it"),filter)).toList();
        var before = measure(db,BEFORE,List.of(filter),"V22",reporter);
        assertThat(before.path("Actual Rows").asInt()).isEqualTo(5000);

        assertThat(flyway.target("23").load().migrate().migrationsExecuted).isOne();
        assertThat(db.queryForObject("select count(*) from ouf_sem.revision_batch_term",Integer.class)).isEqualTo(10000);
        var after = measure(db,PublishedBatchSearch.SQL,intents,"V23",reporter);
        assertThat(after.path("Actual Rows").asInt()).isEqualTo(64);
        assertThat(after.findValuesAsText("Index Name")).contains("revision_batch_term_lookup");
        assertThat(scanTupleVisits(after)).isLessThan(scanTupleVisits(before));
        assertSelectiveScans(after);

        var response = new PublishedBatchSearch(db,JSON).search(intents,1,id -> true);
        assertThat(response.results()).hasSize(64);
        for (int i=0; i<intents.size(); i++) {
          var result = response.results().get(i);
          assertThat(result.intentId()).isEqualTo(intents.get(i).id());
          assertThat(result.state()).isEqualTo(State.MATCH);
          assertThat(result.hasMore()).isFalse();
          assertThat(result.hits()).singleElement().satisfies(hit -> {
            assertThat(hit.semanticId()).isEqualTo("urn:fixture:"+result.intentId().substring(1));
            assertThat(hit.score()).isEqualTo(100);
          });
        }

        // A partial projection can be rebuilt twice from the same immutable revisions.
        db.update("delete from ouf_sem.revision_batch_term where kind='LABEL'");
        db.execute("call ouf_sem.backfill_batch_terms()");
        db.execute("call ouf_sem.backfill_batch_terms()");
        assertThat(db.queryForObject("select count(*) from ouf_sem.revision_batch_term",Integer.class)).isEqualTo(10000);
      } finally {
        ddl.execute("DROP DATABASE " + database + " WITH (FORCE)");
      }
    }
  }

  private static void seed(JdbcTemplate db) {
    db.update("""
        insert into ouf_sem.semantic_artifact(artifact_id,semantic_id,artifact_type,namespace,local_name,owner_ref,authority_ref,origin_kind)
        select gen_random_uuid(),'urn:fixture:'||i,'CLASS','fixture','local-'||i,'fixture','fixture','OUF'
        from generate_series(1,5000) i
        """);
    db.update("""
        insert into ouf_sem.artifact_revision(revision_id,artifact_id,revision_no,lifecycle_status,semantic_version,
          label_json,created_by_subject,published_at)
        select gen_random_uuid(),artifact_id,1,'ACTIVE','1.0.0',
          jsonb_build_object('it','term-'||lpad(substr(local_name,7),5,'0')),'fixture',now()
        from ouf_sem.semantic_artifact
        """);
    db.update("insert into ouf_sem.artifact_active_revision select artifact_id,revision_id,now(),'fixture' from ouf_sem.artifact_revision");
    db.update("insert into ouf_sem.semantic_publication_set values(gen_random_uuid(),1,repeat('a',64),now(),'fixture','PUBLISHED')");
    db.update("""
        insert into ouf_sem.semantic_publication_member
        select publication_set_id,semantic_id,revision_id from ouf_sem.semantic_publication_set
        cross join ouf_sem.artifact_revision join ouf_sem.semantic_artifact using(artifact_id)
        """);
    db.execute("analyze");
  }

  private static JsonNode measure(JdbcTemplate db,String sql,Object args,String phase,TestReporter reporter) throws Exception {
    String explain = "explain (analyze,buffers,format json) " + sql;
    String parameters = JSON.writeValueAsString(args);
    db.queryForObject(explain,String.class,parameters); // warm up each plan once
    var measured = JSON.readTree(db.queryForObject(explain,String.class,parameters)).get(0);
    var plan = measured.required("Plan");
    var metrics = Map.of("phase",phase, "rowsToJdbc",plan.required("Actual Rows").asText(),
        "scanTupleVisits",Long.toString(scanTupleVisits(plan)),
        "executionMs",measured.required("Execution Time").asText(),
        "sharedHitBlocks",plan.required("Shared Hit Blocks").asText(),
        "sharedReadBlocks",plan.required("Shared Read Blocks").asText());
    reporter.publishEntry(metrics);
    System.out.println("SEM-51O-03 " + metrics);
    return plan;
  }

  // EXPLAIN reports rounded per-loop averages. Count visits at base relations,
  // excluding intermediate join/sort output and distinguishing them from buffer I/O.
  private static long relationVisits(JsonNode node) {
    if (!node.has("Relation Name")) return 0;
    long perLoop = node.path("Actual Rows").asLong() + node.path("Rows Removed by Filter").asLong()
        + node.path("Rows Removed by Index Recheck").asLong();
    return perLoop * node.path("Actual Loops").asLong();
  }

  private static long scanTupleVisits(JsonNode node) {
    long visits = relationVisits(node);
    for (var child : node.path("Plans")) visits += scanTupleVisits(child);
    return visits;
  }

  private static void assertSelectiveScans(JsonNode node) {
    if (node.has("Relation Name") && !node.path("Relation Name").asText().equals("semantic_publication_set")) {
      assertThat(relationVisits(node))
          .as("tuples examined by %s on %s",node.path("Node Type"),node.path("Relation Name")).isLessThan(5000);
    }
    for (var child : node.path("Plans")) assertSelectiveScans(child);
  }
}
