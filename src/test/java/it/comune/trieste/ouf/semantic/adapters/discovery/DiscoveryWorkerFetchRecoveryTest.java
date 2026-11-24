package it.comune.trieste.ouf.semantic.adapters.discovery;

import static java.nio.charset.StandardCharsets.UTF_8;
import static it.comune.trieste.ouf.semantic.adapters.discovery.SchemaGovFetchFixture.*;
import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;

import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.application.DiscoveryJobService;
import it.comune.trieste.ouf.semantic.application.DiscoveryService;
import it.comune.trieste.ouf.semantic.domain.SafeRdfParser;
import it.comune.trieste.ouf.semantic.ports.SemanticDiscoveryProvider;
import java.net.URI;
import java.net.URLEncoder;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.Properties;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.info.BuildProperties;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.transaction.support.TransactionTemplate;

@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
class DiscoveryWorkerFetchRecoveryTest {
  private static final String NAMESPACE = "https://w3id.org/italia/onto/CLV/";
  private static final URI BASE = URI.create("https://gateway.invalid");
  private final String actor = "fetch-recovery-" + UUID.randomUUID();
  @Autowired TransactionTemplate publicationTx;
  @Autowired JdbcClient db;
  @Autowired ObjectMapper json;
  @Autowired SafeRdfParser parser;
  @Autowired BuildProperties release;

  @Test void publishesLocalExclusionsEvenWhenThereAreNoCandidates(){
    var gateway=new SchemaGovFetchFixture(1,DENIED,DENIED);
    var worker=new DiscoveryService(db,List.of(gateway.provider),parser,json,publicationTx);
    var jobs=new DiscoveryJobService(db,worker,List.of(gateway.provider),json);
    UUID request=queueProperty(worker);
    db.sql("update ouf_sem.discovery_request set provider_policy='{\"fixture\":true}' where request_id=?")
        .param(request).update();
    assertThat(worker.executeOne()).isOne();
    assertThat(jobs.status(request,actor)).containsEntry("state","SUCCEEDED").containsEntry("candidateCount",0L)
        .containsEntry("excludedCandidates",Map.of("CANDIDATE_FETCH_DENIED",0,"CANDIDATE_RDF_INVALID",0,
            "CANDIDATE_RDF_BOUND",0,"CANDIDATE_NAMESPACE_EXCLUDED",1));
    assertThat(db.sql("select provider_policy->>'fixture' from ouf_sem.discovery_request where request_id=?")
        .param(request).query(String.class).single()).isEqualTo("true");
    gateway.verifyFetches(DENIED,0);
  }

  @ParameterizedTest
  @CsvSource({
      "429,35,SEM_DISCOVERY_RATE_LIMITED,35",
      "429,'Mon, 23 Nov 2026 12:00:35 GMT',SEM_DISCOVERY_RATE_LIMITED,35",
      "429,1,SEM_DISCOVERY_RATE_LIMITED,5",
      "429,,SEM_DISCOVERY_RATE_LIMITED,5",
      "503,,SEM_DISCOVERY_PROVIDER_FAILED,5",
      "timeout,,SEM_DISCOVERY_PROVIDER_FAILED,5"
  })
  void statusAndDurableRetryReflectChannelResponse(String status,String header,String publicCode,int minimum){
    var clock=Clock.fixed(Instant.parse("2026-11-23T12:00:00.250Z"),ZoneOffset.UTC);
    var decision="timeout".equals(status)
        ?ProviderFailurePolicy.exception(new java.net.http.HttpTimeoutException("fixture"))
        :ProviderFailurePolicy.http(Integer.parseInt(status),header,clock);
    var provider=new SemanticDiscoveryProvider(){
      public String providerId(){return "TEST";}
      public List<Candidate> search(Query query){throw new BoundedGatewayClient.ProviderFailure(decision);}
    };
    var worker=new DiscoveryService(db,List.of(provider),parser,json,publicationTx);
    var jobs=new DiscoveryJobService(db,worker,List.of(provider),json);
    UUID request=queueProperty(worker);
    assertThat(worker.executeOne()).isOne();
    assertThat(jobs.status(request,actor)).containsEntry("state","PENDING")
        .containsEntry("recoveryState","RETRY_WAIT").containsEntry("errorCode",publicCode);
    assertThat(db.sql("""
        select r.next_attempt_at=d.next_attempt_at
          and r.next_attempt_at>=a.started_at+make_interval(secs=>:minimum)
        from ouf_sem.discovery_request r join ouf_sem.discovery_attempt a using(request_id)
        join ouf_sem.discovery_dependency d on d.scope_subject=a.scope_subject and d.provider_id=a.provider_id
        where r.request_id=:r
        """).param("minimum",minimum).param("r",request).query(Boolean.class).single()).isTrue();
  }

  @Test void malformedRetryAfterKeepsThe429VisibleAndBlocksAutomaticRetry(){
    var decision=ProviderFailurePolicy.http(429,"invalid",Clock.systemUTC());
    assertThat(decision.kind()).isEqualTo(ProviderFailurePolicy.Kind.BLOCKED);
    var gateway=new SchemaGovFetchFixture(1,VALID);
    gateway.rejectSearch(decision.code());
    var worker=new DiscoveryService(db,List.of(gateway.provider),parser,json,publicationTx);
    UUID request=queueProperty(worker);
    assertThat(worker.executeOne()).isOne();
    var jobs=new DiscoveryJobService(db,worker,List.of(gateway.provider),json);
    assertThat(jobs.status(request,actor)).containsEntry("recoveryState","BLOCKED")
        .containsEntry("errorCode","SEM_DISCOVERY_RATE_LIMITED").doesNotContainKey("pollAfterSeconds");
  }

  @Test void releaseProbeResolvesThe102IncidentAndSubsequentPropertyDiscoverySucceeds(){
    // Reproduce the 1.0.2 adapter outcome at the provider boundary.
    var legacyProvider=new SemanticDiscoveryProvider(){
      public String providerId(){return "SCHEMA_GOV_IT";}
      public List<Candidate> search(Query query){throw new BoundedGatewayClient.ProviderFailure("PROVIDER_HTTP_400");}
    };
    var oldBuild=new Properties();
    oldBuild.setProperty("version","1.0.2");
    var old=new DiscoveryService(db,List.of(legacyProvider),parser,json,publicationTx,new BuildProperties(oldBuild));
    UUID failed=queueProperty(old);
    assertThat(old.executeOne()).isOne();
    assertThat(db.sql("select state,last_error_code from ouf_sem.discovery_request where request_id=?")
        .param(failed).query().singleRow()).containsEntry("state","FAILED").containsEntry("last_error_code","PROVIDER_HTTP_400");
    UUID incident=db.sql("""
        select incident_id from ouf_sem.discovery_incident where scope_subject=? and provider_id='SCHEMA_GOV_IT'
          and state='OPEN' and code='PROVIDER_HTTP_400' and opened_worker_version='1.0.2'
        """).param(actor).query(UUID.class).single();
    db.sql("update ouf_sem.discovery_dependency set next_attempt_at=clock_timestamp() where incident_id=?")
        .param(incident).update();

    assertThat(release.getVersion()).isEqualTo("1.0.3");
    var gateway=new SchemaGovFetchFixture(2,DENIED,REMOTE_DENIAL,VALID);
    gateway.reject(REMOTE_DENIAL,"PROVIDER_HTTP_400");
    gateway.describe(VALID,"<"+VALID+"> a <http://www.w3.org/2002/07/owl#DatatypeProperty> .");
    var worker=new DiscoveryService(db,List.of(gateway.provider),parser,json,publicationTx,release);
    var jobs=new DiscoveryJobService(db,worker,List.of(gateway.provider),json);
    // A fresh request can exercise the V15 probe even after the original job expires.
    for(boolean probe:List.of(true,false)){
      UUID request=queueProperty(worker);
      assertThat(worker.executeOne()).isOne();
      assertThat(jobs.status(request,actor)).containsEntry("state","SUCCEEDED").containsEntry("candidateCount",1L)
          .containsEntry("excludedCandidates",Map.of("CANDIDATE_FETCH_DENIED",1,"CANDIDATE_NAMESPACE_EXCLUDED",1,"CANDIDATE_RDF_INVALID",0,"CANDIDATE_RDF_BOUND",0))
          .doesNotContainKey("errorCode");
      assertThat(worker.candidates(request)).singleElement().satisfies(row->
          assertThat(row).containsEntry("canonical_uri",VALID).containsEntry("artifact_type","PROPERTY"));
      assertThat(db.sql("select outcome,version_probe,worker_version,incident_id from ouf_sem.discovery_attempt where request_id=?")
          .param(request).query().singleRow()).containsEntry("outcome","SUCCESS").containsEntry("version_probe",probe)
          .containsEntry("worker_version",release.getVersion()).containsEntry("incident_id",probe?incident:null);
      assertThat(jobs.providerStatus("SCHEMA_GOV_IT",true,actor)).containsEntry("recoveryState","HEALTHY");
      assertThat(db.sql("select state from ouf_sem.discovery_incident where scope_subject=? and provider_id='SCHEMA_GOV_IT'")
          .param(actor).query(String.class).list()).containsExactly("RESOLVED");
    }
  }

  private UUID queueProperty(DiscoveryService worker){
    UUID id=worker.request("PROPERTY","latitudine",List.of("it"),actor);
    db.sql("update ouf_sem.discovery_request set created_at=timestamp '1800-01-01' where request_id=?")
        .param(id).update();
    return id;
  }

  private SchemaGovProvider provider(String uri) {
    Duration timeout = Duration.ofSeconds(2);
    var cfg = new SchemaGovProperties(true, BASE, "/search", "/fetch", timeout, timeout,
        8192, 1, 1, Duration.ofMillis(100), 3, Duration.ofSeconds(30),List.of("https://w3id.org/italia/onto/"));
    var transport = mock(BoundedGatewayClient.class);
    String bindings = """
        {"results":{"bindings":[{"resource":{"value":"%s"}}]}}
        """.formatted(uri);
    when(transport.postForm(eq(BASE), eq(BASE.resolve("/search")), anyString(), eq(timeout),
        eq(8192), anySet(),any())).thenReturn(new BoundedGatewayClient.Response(
            bindings.getBytes(UTF_8), "application/sparql-results+json"));
    URI fetch = BASE.resolve("/fetch?uri=" + URLEncoder.encode(uri, UTF_8));
    String rdf = "<" + uri + "> a <http://www.w3.org/2002/07/owl#Class> .";
    when(transport.get(eq(BASE), eq(fetch), eq(timeout), eq(8192), anySet(),any(),anyString()))
        .thenReturn(new BoundedGatewayClient.Response(rdf.getBytes(UTF_8), "text/turtle"));
    return new SchemaGovProvider(cfg, transport, json, Clock.systemUTC());
  }

  @AfterEach void retireUnfinishedFixture() {
    db.sql("update ouf_sem.discovery_request set state='CANCELLED', lease_until=null "
        + "where created_by_subject=:actor and state in ('PENDING','RUNNING')").param("actor", actor).update();
  }

  @Test void documentedInventoryShowsOnlyOperationalColumns() throws Exception {
    var service = new DiscoveryService(db, List.of(provider(NAMESPACE + "City")), parser, json,publicationTx);
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
    var first = new DiscoveryService(db, List.of(provider(NAMESPACE + "Province")), interruptedParser, json,publicationTx);
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
    var successor = new DiscoveryService(db, List.of(provider(NAMESPACE + "City")), parser, json,publicationTx);
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
