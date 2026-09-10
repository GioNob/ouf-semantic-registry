package it.comune.trieste.ouf.semantic.adapters.discovery;

import static org.assertj.core.api.Assertions.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.net.httpserver.HttpServer;
import it.comune.trieste.ouf.semantic.ports.SemanticDiscoveryProvider.Query;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.*;

class SchemaGovProviderIntegrationTest {
  HttpServer gateway; URI base; AtomicInteger fetches;
  @BeforeEach void start() throws Exception {
    gateway=HttpServer.create(new InetSocketAddress("127.0.0.1",0),0);fetches=new AtomicInteger();
    base=URI.create("http://127.0.0.1:"+gateway.getAddress().getPort());gateway.start();
  }
  @AfterEach void stop(){gateway.stop(0);}
  @Test void searchesThroughGatewayDeduplicatesBoundsAndFetchesRdf() {
    gateway.createContext("/sparql",x->{byte[] b=("{\"results\":{\"bindings\":["+
      "{\"resource\":{\"value\":\"https://w3id.org/italia/onto/CLV/City\"},\"label\":{\"value\":\"Città\",\"xml:lang\":\"it\"}},"+
      "{\"resource\":{\"value\":\"https://w3id.org/italia/onto/CLV/City\"}}]}}").getBytes(StandardCharsets.UTF_8);
      x.getResponseHeaders().add("Content-Type","application/sparql-results+json");x.sendResponseHeaders(200,b.length);x.getResponseBody().write(b);x.close();});
    gateway.createContext("/fetch",x->{fetches.incrementAndGet();byte[] b="@prefix owl: <http://www.w3.org/2002/07/owl#> . <https://w3id.org/italia/onto/CLV/City> a owl:Class .".getBytes(StandardCharsets.UTF_8);x.getResponseHeaders().add("Content-Type","text/turtle");x.sendResponseHeaders(200,b.length);x.getResponseBody().write(b);x.close();});
    var provider=new SchemaGovProvider(config(1,2),new ObjectMapper());
    var result=provider.search(new Query("CLASS","città",List.of("it")));
    assertThat(result).hasSize(1);assertThat(fetches).hasValue(1);assertThat(result.get(0).reasons()).containsExactly("label: Città [it]");
  }
  @Test void retriesTransientFailureButNotPermanentMediaFailure() {
    AtomicInteger calls=new AtomicInteger();gateway.createContext("/sparql",x->{int n=calls.incrementAndGet();if(n==1){x.sendResponseHeaders(503,-1);x.close();return;}byte[] b="{\"results\":{\"bindings\":[]}}".getBytes();x.getResponseHeaders().add("Content-Type","application/sparql-results+json");x.sendResponseHeaders(200,b.length);x.getResponseBody().write(b);x.close();});
    assertThat(new SchemaGovProvider(config(2,2),new ObjectMapper()).search(new Query("CLASS","x",List.of()))).isEmpty();assertThat(calls).hasValue(2);
  }
  private SchemaGovProperties config(int attempts,int threshold){return new SchemaGovProperties(true,base,"/sparql","/fetch",Duration.ofSeconds(1),Duration.ofSeconds(2),1024*1024,1,attempts,Duration.ofMillis(1),threshold,Duration.ofSeconds(30));}
}
