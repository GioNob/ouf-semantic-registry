package it.comune.trieste.ouf.semantic.adapters.discovery;

import static java.nio.charset.StandardCharsets.UTF_8;
import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Tag;
import it.comune.trieste.ouf.semantic.application.DiscoveryJobService;
import it.comune.trieste.ouf.semantic.application.DiscoveryService;
import it.comune.trieste.ouf.semantic.domain.SafeRdfParser;
import it.comune.trieste.ouf.semantic.ports.DiscoveryTraffic.Origin;
import java.io.IOException;
import java.net.*;
import java.time.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.*;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.support.TransactionTemplate;

@SpringBootTest(properties={"ouf.semantic.discovery-worker.enabled=false","ouf.semantic.providers.schema-gov.enabled=false"})
@AutoConfigureMockMvc
class DiscoveryTrafficRuntimeTest {
  static final String NS="https://terms.example.test/";
  static final String EXCLUDED="https://excluded.example.test/a";
  static final String A=NS+"a", B=NS+"b", ONTOLOGY=NS+"ontology";
  static final String PREFIX="ouf.semantic.discovery.";
  final String actor="traffic-fixture-"+UUID.randomUUID();
  final AtomicInteger searches=new AtomicInteger(), fetches=new AtomicInteger();
  @Autowired JdbcClient db;
  @Autowired SafeRdfParser parser;
  @Autowired ObjectMapper json;
  @Autowired TransactionTemplate tx;
  @Autowired MeterRegistry meters;
  @Autowired MockMvc http;
  HttpServer gateway;
  SchemaGovProperties cfg;

  @BeforeEach void start() throws IOException {
    gateway=HttpServer.create(new InetSocketAddress("localhost",0),0);
    gateway.start();
    var base=URI.create("http://localhost:"+gateway.getAddress().getPort());
    cfg=new SchemaGovProperties(true,base,"/search","/fetch",Duration.ofSeconds(2),Duration.ofSeconds(2),
        8192,8,1,Duration.ofMillis(100),3,Duration.ofSeconds(30),List.of(NS));
  }

  @AfterEach void stop(){
    gateway.stop(0);
    db.sql("update ouf_sem.discovery_request set state='CANCELLED', lease_until=null where created_by_subject=? and state in ('PENDING','RUNNING')")
        .param(actor).update();
  }

  DiscoveryService worker(BoundedGatewayClient client){
    var provider=new SchemaGovProvider(cfg,client,json,Clock.systemUTC());
    return new DiscoveryService(db,List.of(provider),parser,json,tx);
  }
  DiscoveryService worker(){return worker(new BoundedGatewayClient(cfg.connectTimeout()));}
  UUID queue(DiscoveryService worker){
    UUID id=worker.request("CLASS","fixture",List.of(),actor);
    db.sql("update ouf_sem.discovery_request set created_at=timestamp '1800-01-01' where request_id=?").param(id).update();
    return id;
  }
  void search(String... resources){
    var result=json.createObjectNode();
    var rows=result.putObject("results").putArray("bindings");
    for(String uri:resources)rows.addObject().putObject("resource").put("value",uri);
    gateway.createContext("/search",x->{
      searches.incrementAndGet();
      reply(x,"application/json",result.toString());
    });
  }
  static void reply(HttpExchange x,String type,String body) throws IOException {
    try(x){
      byte[] bytes=body.getBytes(UTF_8);
      x.getResponseHeaders().add("Content-Type",type);
      x.sendResponseHeaders(200,bytes.length);
      x.getResponseBody().write(bytes);
    }
  }
  static String resource(HttpExchange x){
    return URLDecoder.decode(x.getRequestURI().getRawQuery().substring("uri=".length()),UTF_8);
  }
  static void description(HttpExchange x) throws IOException {
    reply(x,"text/turtle","<"+resource(x)+"> a <urn:fixture:Class> .");
  }
  long count(UUID id,String metric){
    return db.sql("select coalesce(sum(amount),0) from ouf_sem.discovery_job_traffic where request_id=? and metric=?")
        .param(id).param(metric).query(Long.class).single();
  }
  void counts(UUID id,long search,long sent,long excluded,long useful,long repeated){
    assertThat(count(id,"searchSent")).isEqualTo(search);
    assertThat(count(id,"getSent")).isEqualTo(sent);
    assertThat(count(id,"getExcluded")).isEqualTo(excluded);
    assertThat(count(id,"getUseful")).isEqualTo(useful);
    assertThat(count(id,"getRepeated")).isEqualTo(repeated);
  }

  @Test @DisplayName("SEM-55K-01 filter, usable descriptions and shared ontology")
  void countsOnlyPhysicalFetchesAndUsableResources(){
    String deniedOntology=EXCLUDED+"/ontology", invalid=NS+"invalid";
    search(EXCLUDED,EXCLUDED,A,B,B,invalid);
    gateway.createContext("/fetch",x->{
      fetches.incrementAndGet();
      String uri=resource(x);
      if(uri.equals(invalid))reply(x,"text/turtle","invalid RDF");
      else if(uri.equals(ONTOLOGY))reply(x,"text/turtle","<"+uri+"> <http://purl.org/dc/terms/license> <urn:fixture:license> .");
      else reply(x,"text/turtle","<"+uri+"> <http://www.w3.org/2000/01/rdf-schema#isDefinedBy> <"+ONTOLOGY+">,<"+deniedOntology+"> .");
    });
    var service=worker();
    UUID id=queue(service);
    assertThat(service.executeOne()).isOne();
    counts(id,1,4,2,3,0);
    assertThat(service.candidates(id)).hasSize(2);
    assertThat(searches.get()).isOne();
    assertThat(fetches.get()).isEqualTo(4);
  }

  @Test @DisplayName("SEM-55K-02 timeout and retry after worker restart")
  void successfulRetryIsRepeatedAndUseful(){
    search(EXCLUDED,A,B);
    var unfinished=new AtomicReference<HttpExchange>();
    gateway.createContext("/fetch",x->{
      fetches.incrementAndGet();
      if(resource(x).equals(B) && unfinished.compareAndSet(null,x)){
        x.getResponseHeaders().add("Content-Type","text/turtle");
        x.sendResponseHeaders(200,32); // The declared body never completes.
      }else description(x);
    });
    var first=worker();
    UUID id=queue(first);
    assertThat(first.executeOne()).isOne();
    counts(id,1,2,1,1,0);
    assertThat(db.sql("select last_error_code from ouf_sem.discovery_request where request_id=?")
        .param(id).query(String.class).single()).isEqualTo("PROVIDER_TIMEOUT");
    unfinished.get().close();
    // Advance the uncertainty horizon as well as the retry clock.
    db.sql("update ouf_sem.discovery_provider_slot set expires_at=now(),reconcile_at=now() where request_id=? and outcome='UNCERTAIN'")
        .param(id).update();
    db.sql("update ouf_sem.discovery_dependency set next_attempt_at=now() where scope_subject=?").param(actor).update();
    db.sql("update ouf_sem.discovery_request set next_attempt_at=now() where request_id=?").param(id).update();
    var successor=worker();
    assertThat(successor.executeOne()).isOne();
    counts(id,2,4,2,2,2);
    assertThat(successor.candidates(id)).hasSize(2);
    UUID another=queue(successor);
    assertThat(successor.executeOne()).isOne();
    counts(another,1,2,1,2,0);
    assertThat(searches.get()).isEqualTo(3);
    assertThat(fetches.get()).isEqualTo(6);
  }

  @Test @DisplayName("SEM-55K-03 zero and two read-only Actuator scrapes")
  void reportsEmptySearchWithoutChangingTheTotals() throws Exception {
    search();
    var service=worker();
    UUID id=queue(service);
    counts(id,0,0,0,0,0);
    var names=List.of("getUseful","getExcluded","getRepeated","getSent","searchSent");
    var baseline=new HashMap<String,Double>();
    for(String name:names){
      var gauge=meters.get(PREFIX+name).gauge();
      assertThat(gauge.getId().getTags()).extracting(Tag::getKey).isSubsetOf("application");
      baseline.put(name,gauge.value());
    }
    assertThat(service.executeOne()).isOne();
    for(int read=0;read<2;read++){
      for(String name:names){
        double expected=baseline.get(name)+("searchSent".equals(name)?1:0);
        http.perform(get("/actuator/metrics/"+PREFIX+name)).andExpect(status().isOk())
            .andExpect(jsonPath("$.measurements[0].value").value(expected));
      }
    }
    for(String name:List.of("slotOccupancy","slotWaits","slotUncertain","slotAcquisitionSeconds")){
      var gauge=meters.get(PREFIX+name).gauge();
      assertThat(gauge.getId().getTags()).extracting(Tag::getKey).isSubsetOf("application");
      double value=gauge.value();
      assertThat(value).isGreaterThanOrEqualTo(0);
      assertThat(gauge.value()).isEqualTo(value);
    }
    counts(id,1,0,0,0,0);
    assertThat(searches.get()).isOne();
    var refused=worker(new BoundedGatewayClient(cfg.connectTimeout(),()->{
      throw new BoundedGatewayClient.ProviderFailure("GATEWAY_AUTH_REQUIRED");
    }));
    UUID denied=queue(refused);
    assertThat(refused.executeOne()).isOne();
    counts(denied,0,0,0,0,0);
    assertThat(searches.get()).isOne();
  }

  // PET-semantic-294/307 · Gateway 55l proof through the 55k persistent counter and Actuator.
  @ParameterizedTest(name="SEM-58G-05 / SEM-55K-04 {0} 429 becomes {1}")
  @CsvSource({"search,UNKNOWN","fetch,UNKNOWN","search,APISIX","fetch,UPSTREAM"})
  void attributesOnlyVerifiedRejections(String route,Origin expected) throws Exception {
    boolean fetch=route.equals("fetch");
    if(fetch)search(A);
    gateway.createContext("/"+route,x->{
      try(x){
        (fetch?fetches:searches).incrementAndGet();
        x.getResponseHeaders().add("X-RateLimit-Origin",fetch?"APISIX":"UPSTREAM");
        x.getResponseHeaders().add("Retry-After","35");
        if(fetch || expected!=Origin.UNKNOWN){
          Origin producer=fetch?Origin.UPSTREAM:Origin.APISIX;
          String nonce=x.getRequestHeaders().getFirst("X-OUF-Exchange-Id");
          if(expected==Origin.UNKNOWN)nonce=OriginAttestationFixture.NONCE; // replay from another exchange
          var proof=OriginAttestationFixture.sign(x.getRequestMethod(),x.getRequestURI().toASCIIString(),nonce,
              producer.name(),OriginAttestationFixture.IAT,OriginAttestationFixture.EXP);
          x.getResponseHeaders().add(OriginAttestationFixture.HEADER,proof);
        }
        x.sendResponseHeaders(429,-1);
      }
    });
    var verifier=new Ed25519RateLimitOriginVerifier(OriginAttestationFixture.routes("/search","/fetch"),
        OriginAttestationFixture.PUBLIC_KEY,OriginAttestationFixture.INSTALLATION,0,
        OriginAttestationFixture.clock(OriginAttestationFixture.IAT));
    // The fixture uses loopback HTTP. Substitute only its authority, retaining the actual request target.
    RateLimitOriginVerifier.ExchangeBound loopback=(method,target,nonce,response)->{
      var rawTarget=cfg.gatewayBaseUrl().resolve("/").relativize(target);
      return verifier.verifiedOrigin(method,OriginAttestationFixture.GATEWAY.resolve(rawTarget),nonce,response);
    };
    var client=new BoundedGatewayClient(cfg.connectTimeout(),null,loopback);
    var gauge=meters.get(PREFIX+"http429").tags("route",route,"origin",expected.name()).gauge();
    assertThat(gauge.getId().getTags()).extracting(Tag::getKey)
        .contains("route","origin").isSubsetOf("route","origin","application");
    double before=gauge.value();
    var service=worker(client);
    UUID id=queue(service);
    assertThat(service.executeOne()).isOne();
    counts(id,1,fetch?1:0,0,0,0);
    assertThat(count(id,"http429")).isOne();
    assertThat(searches.get()).isOne();
    assertThat(fetches.get()).isEqualTo(fetch?1:0);
    var jobs=new DiscoveryJobService(db,service,List.of(),json);
    assertThat(jobs.status(id,actor)).containsEntry("errorCode","SEM_DISCOVERY_RATE_LIMITED");
    for(int read=0;read<2;read++){
      http.perform(get("/actuator/metrics/"+PREFIX+"http429")
          .param("tag","route:"+route,"origin:"+expected.name())).andExpect(status().isOk())
          .andExpect(jsonPath("$.measurements[0].value").value(before+1));
    }
  }

  @Test @DisplayName("SEM-55K-04 optional ontology rejection and unavailable attestation")
  void countsOptional429EvenWhenTheJobSucceeds(){
    search(A);
    gateway.createContext("/fetch",x->{
      if(resource(x).equals(A)){
        reply(x,"text/turtle","<"+A+"> <http://www.w3.org/2000/01/rdf-schema#isDefinedBy> <"+ONTOLOGY+"> .");
      }else{
        try(x){
          x.getResponseHeaders().add("X-RateLimit-Origin","APISIX");
          x.sendResponseHeaders(429,-1);
        }
      }
    });
    var service=worker(new BoundedGatewayClient(cfg.connectTimeout(),null,(method,target,response)->{
      throw new IllegalStateException("fixture evidence unavailable");
    }));
    UUID id=queue(service);
    assertThat(service.executeOne()).isOne();
    assertThat(service.candidates(id)).hasSize(1);
    counts(id,1,2,0,1,0);
    assertThat(db.sql("""
        select state='RETRY_WAIT' and next_attempt_at>now() and busy_until is null
        from ouf_sem.discovery_dependency where scope_subject=?
        """).param(actor).query(Boolean.class).single()).isTrue();
    assertThat(db.sql("select origin from ouf_sem.discovery_job_traffic where request_id=? and metric='http429' and route='fetch'")
        .param(id).query(String.class).single()).isEqualTo("UNKNOWN");
  }
}
