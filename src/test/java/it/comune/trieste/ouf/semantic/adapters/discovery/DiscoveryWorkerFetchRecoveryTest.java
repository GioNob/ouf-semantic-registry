package it.comune.trieste.ouf.semantic.adapters.discovery;

import static java.nio.charset.StandardCharsets.UTF_8;
import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;

import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.application.DiscoveryService;
import it.comune.trieste.ouf.semantic.domain.SafeRdfParser;
import java.net.URI;
import java.net.URLEncoder;
import java.time.Clock;
import java.time.Duration;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.simple.JdbcClient;

@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
class DiscoveryWorkerFetchRecoveryTest {
  private static final String NAMESPACE = "https://w3id.org/italia/onto/CLV/";
  private static final URI BASE = URI.create("https://gateway.invalid");
  private final String actor = "fetch-recovery-" + UUID.randomUUID();
  @Autowired JdbcClient db;
  @Autowired ObjectMapper json;
  @Autowired SafeRdfParser parser;

  private SchemaGovProvider provider(String uri) {
    Duration timeout = Duration.ofSeconds(2);
    var cfg = new SchemaGovProperties(true, BASE, "/search", "/fetch", timeout, timeout,
        8192, 1, 1, Duration.ofMillis(100), 3, Duration.ofSeconds(30));
    var transport = mock(BoundedGatewayClient.class);
    String bindings = """
        {"results":{"bindings":[{"resource":{"value":"%s"}}]}}
        """.formatted(uri);
    when(transport.postForm(eq(BASE), eq(BASE.resolve("/search")), anyString(), eq(timeout),
        eq(8192), anySet())).thenReturn(new BoundedGatewayClient.Response(
            bindings.getBytes(UTF_8), "application/sparql-results+json"));
    URI fetch = BASE.resolve("/fetch?uri=" + URLEncoder.encode(uri, UTF_8));
    String rdf = "<" + uri + "> a <http://www.w3.org/2002/07/owl#Class> .";
    when(transport.get(eq(BASE), eq(fetch), eq(timeout), eq(8192), anySet()))
        .thenReturn(new BoundedGatewayClient.Response(rdf.getBytes(UTF_8), "text/turtle"));
    return new SchemaGovProvider(cfg, transport, json, Clock.systemUTC());
  }

  @AfterEach void retireUnfinishedFixture() {
    db.sql("update ouf_sem.discovery_request set state='CANCELLED', lease_until=null "
        + "where created_by_subject=:actor and state in ('PENDING','RUNNING')").param("actor", actor).update();
  }

  @Test void documentedInventoryShowsOnlyOperationalColumns() throws Exception {
    var service = new DiscoveryService(db, List.of(provider(NAMESPACE + "City")), parser, json);
    UUID request = service.request("CLASS", "teatro", List.of("it"), actor);
    String sql = java.nio.file.Files.readString(java.nio.file.Path.of("docs/installation/discovery-queue.sql"));
    var rows = db.sql(sql).query().listOfRows().stream()
        .filter(row -> request.equals(row.get("request_id"))).toList();
    assertThat(rows).singleElement().satisfies(row -> {
      assertThat(row).containsOnlyKeys("owner_scope", "request_id", "state", "recovery_state",
          "attempt_count", "worker_generation", "lease_until", "next_attempt_at",
          "budget_started_at", "budget_deadline");
      assertThat(row).containsEntry("owner_scope", actor).containsEntry("state", "PENDING")
          .containsEntry("recovery_state", "ACTIVE").containsEntry("attempt_count", 0)
          .containsEntry("worker_generation", 0L);
    });
  }

  @Test void restartAfterFetchPublishesOnlyTheRecoveredSchemaGovCandidate() {
    // Error models abrupt process loss outside the service's provider-failure handler.
    var stopped = new AssertionError("fixture process stopped after fetch");
    var interruptedParser = mock(SafeRdfParser.class);
    when(interruptedParser.parse(any(byte[].class), eq("text/turtle"))).thenThrow(stopped);
    var first = new DiscoveryService(db, List.of(provider(NAMESPACE + "Province")), interruptedParser, json);
    UUID id = first.request("CLASS", "city", List.of("it"), actor);
    db.sql("update ouf_sem.discovery_request set created_at=timestamp '1800-01-01' where request_id=?")
        .param(id).update();
    assertThatThrownBy(first::executeOne).isSameAs(stopped);
    assertThat(first.candidates(id)).isEmpty();
    assertThat(db.sql("select state, worker_generation from ouf_sem.discovery_request where request_id=?")
        .param(id).query().singleRow()).containsEntry("state", "RUNNING").containsEntry("worker_generation", 1L);

    db.sql("update ouf_sem.discovery_request set lease_until=clock_timestamp()-interval '1 second' where request_id=?")
        .param(id).update();
    db.sql("update ouf_sem.discovery_dependency set busy_until=clock_timestamp()-interval '1 second' where active_request=?")
        .param(id).update();
    var successor = new DiscoveryService(db, List.of(provider(NAMESPACE + "City")), parser, json);
    assertThat(successor.executeOne()).isOne();
    assertThat(db.sql("select state, worker_generation from ouf_sem.discovery_request where request_id=?")
        .param(id).query().singleRow()).containsEntry("state", "SUCCEEDED").containsEntry("worker_generation", 2L);
    assertThat(db.sql("select outcome from ouf_sem.discovery_attempt where request_id=? order by request_generation")
        .param(id).query(String.class).list()).containsExactly("LEASE_EXPIRED", "SUCCESS");
    assertThat(db.sql("select canonical_uri, provider_id from ouf_sem.discovery_candidate where request_id=?")
        .param(id).query().listOfRows()).singleElement().satisfies(row -> assertThat(row)
            .containsEntry("canonical_uri", NAMESPACE + "City").containsEntry("provider_id", "SCHEMA_GOV_IT"));
  }
}
