package it.comune.trieste.ouf.semantic.adapters.discovery;

import static org.assertj.core.api.Assertions.*;
import com.sun.net.httpserver.HttpServer;
import java.net.*;import java.time.Duration;import java.util.Set;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import org.junit.jupiter.api.*;

class BoundedGatewayClientTest {
  HttpServer server;URI base;BoundedGatewayClient client=new BoundedGatewayClient(Duration.ofSeconds(1));
  @BeforeEach void start() throws Exception{server=HttpServer.create(new InetSocketAddress("127.0.0.1",0),0);server.start();base=URI.create("http://127.0.0.1:"+server.getAddress().getPort());}
  @AfterEach void stop(){server.stop(0);}
  // PET-semantic-294/307 · Gateway 55l
  @Test @DisplayName("SEM-58G-06 one exchange ID on the wire per attempt, including two retries")
  void retriesOfTheSameIntentUseFreshNonces(){
    var wire=new CopyOnWriteArrayList<List<String>>();
    server.createContext("/limited",exchange->{
      try(exchange){
        wire.add(List.copyOf(exchange.getRequestHeaders().get("X-OUF-Exchange-Id")));
        exchange.sendResponseHeaders(429,-1);
      }
    });
    var observed=new CopyOnWriteArrayList<String>();
    RateLimitOriginVerifier.ExchangeBound recorder=(method,target,nonce,response)->{
      observed.add(nonce);
      return it.comune.trieste.ouf.semantic.ports.DiscoveryTraffic.Origin.UNKNOWN;
    };
    var transport=new BoundedGatewayClient(Duration.ofSeconds(1),null,recorder);
    var target=base.resolve("/limited?x=a%2Fb&x=");
    var timeout=Duration.ofSeconds(2);
    var types=Set.of("application/json");
    for(int attempt=0;attempt<3;attempt++){
      assertThatThrownBy(()->transport.postForm(base,target,"query=same",timeout,64,types)).hasMessage("PROVIDER_HTTP_429");
      assertThatThrownBy(()->transport.get(base,target,timeout,64,types)).hasMessage("PROVIDER_HTTP_429");
    }
    assertThat(observed).hasSize(6).doesNotHaveDuplicates().allMatch(nonce->
        nonce.matches("[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"));
    assertThat(wire).containsExactlyElementsOf(observed.stream().map(nonce->List.of(nonce)).toList());
  }

  @Test @DisplayName("SEM-58G-07 lost response: one dispatch, at most one transport repeat with the same exchange ID")
  void lostResponseDoesNotRedispatchTheRequest(){
    // The JDK client repeats an idempotent GET once when the connection ends before any
    // response byte (ConnectionExpiredException), and no property disables it for GET.
    // That repeat carries the same nonce: the Gateway voids a reused nonce, so the origin
    // stays UNKNOWN. Semantic itself never redispatches the attempt (review-58g).
    var nonces=new java.util.concurrent.CopyOnWriteArrayList<String>();
    server.createContext("/lost",exchange->{
      nonces.add(exchange.getRequestHeaders().getFirst("X-OUF-Exchange-Id"));
      exchange.close();
    });
    assertThatThrownBy(()->client.get(base,base.resolve("/lost"),Duration.ofSeconds(2),64,Set.of("application/json")))
        .isInstanceOf(BoundedGatewayClient.ProviderFailure.class);
    assertThat(nonces).hasSizeBetween(1,2);
    assertThat(java.util.Set.copyOf(nonces)).hasSize(1);
  }
  @Test void rateLimitKeepsRetryAfterAndIgnoresClaimedOrigin(){
    server.createContext("/limited",exchange->{
      exchange.getResponseHeaders().add("Retry-After","35");
      exchange.getResponseHeaders().add("X-RateLimit-Origin","local");
      try(exchange){
        byte[] body=new byte[256];
        exchange.sendResponseHeaders(429,body.length);
        exchange.getResponseBody().write(body);
      }
    });
    assertThatThrownBy(()->client.get(base,base.resolve("/limited"),Duration.ofSeconds(2),64,Set.of("text/turtle")))
        .isInstanceOfSatisfying(BoundedGatewayClient.ProviderFailure.class,failure->{
          assertThat(failure.decision().code()).isEqualTo("PROVIDER_HTTP_429");
          assertThat(failure.decision().retryAfter()).isEqualTo(Duration.ofSeconds(35));
        });
  }
  @Test void acceptsBoundedSameOriginResponse(){server.createContext("/ok",x->{byte[] b="{}".getBytes();x.getResponseHeaders().add("Content-Type","application/json");x.sendResponseHeaders(200,b.length);x.getResponseBody().write(b);x.close();});assertThat(client.get(base,base.resolve("/ok"),Duration.ofSeconds(1),20,Set.of("application/json")).body()).containsExactly("{}".getBytes());}
  @Test void postsSparqlFormWithoutRedirectFollowing(){server.createContext("/sparql",x->{assertThat(x.getRequestMethod()).isEqualTo("POST");assertThat(x.getRequestHeaders().getFirst("Content-Type")).startsWith("application/x-www-form-urlencoded");byte[] b="{\"results\":{\"bindings\":[]}}".getBytes();x.getResponseHeaders().add("Content-Type","application/sparql-results+json");x.sendResponseHeaders(200,b.length);x.getResponseBody().write(b);x.close();});assertThat(client.postForm(base,base.resolve("/sparql"),"query=SELECT",Duration.ofSeconds(1),100,Set.of("application/sparql-results+json")).body()).isNotEmpty();}
  @Test void rejectsRedirect(){server.createContext("/r",x->{x.getResponseHeaders().add("Location","https://evil.test/");x.sendResponseHeaders(302,-1);x.close();});assertThatThrownBy(()->client.get(base,base.resolve("/r"),Duration.ofSeconds(1),20,Set.of("application/json"))).hasMessage("PROVIDER_REDIRECT_FORBIDDEN");}
  @Test void rejectsOversizeAndWrongMediaType(){server.createContext("/large",x->{byte[] b=new byte[32];x.getResponseHeaders().add("Content-Type","application/json");x.sendResponseHeaders(200,b.length);x.getResponseBody().write(b);x.close();});assertThatThrownBy(()->client.get(base,base.resolve("/large"),Duration.ofSeconds(1),8,Set.of("application/json"))).hasMessage("PROVIDER_RESPONSE_TOO_LARGE");assertThatThrownBy(()->client.get(base,base.resolve("/large"),Duration.ofSeconds(1),64,Set.of("text/turtle"))).hasMessage("PROVIDER_MEDIA_TYPE_REJECTED");}
  @Test void rejectsCrossOriginAndPlainHttpOutsideLoopback(){assertThatThrownBy(()->client.get(base,URI.create("http://example.org/x"),Duration.ofSeconds(1),20,Set.of("text/plain"))).hasMessage("GATEWAY_ORIGIN_VIOLATION");assertThatThrownBy(()->client.get(URI.create("http://example.org"),URI.create("http://example.org/x"),Duration.ofSeconds(1),20,Set.of("text/plain"))).hasMessage("GATEWAY_HTTPS_REQUIRED");}
}
