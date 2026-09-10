package it.comune.trieste.ouf.semantic.adapters.discovery;

import static org.assertj.core.api.Assertions.*;
import com.sun.net.httpserver.HttpServer;
import java.net.*;import java.time.Duration;import java.util.Set;
import org.junit.jupiter.api.*;

class BoundedGatewayClientTest {
  HttpServer server;URI base;BoundedGatewayClient client=new BoundedGatewayClient(Duration.ofSeconds(1));
  @BeforeEach void start() throws Exception{server=HttpServer.create(new InetSocketAddress("127.0.0.1",0),0);server.start();base=URI.create("http://127.0.0.1:"+server.getAddress().getPort());}
  @AfterEach void stop(){server.stop(0);}
  @Test void acceptsBoundedSameOriginResponse(){server.createContext("/ok",x->{byte[] b="{}".getBytes();x.getResponseHeaders().add("Content-Type","application/json");x.sendResponseHeaders(200,b.length);x.getResponseBody().write(b);x.close();});assertThat(client.get(base,base.resolve("/ok"),Duration.ofSeconds(1),20,Set.of("application/json")).body()).containsExactly("{}".getBytes());}
  @Test void postsSparqlFormWithoutRedirectFollowing(){server.createContext("/sparql",x->{assertThat(x.getRequestMethod()).isEqualTo("POST");assertThat(x.getRequestHeaders().getFirst("Content-Type")).startsWith("application/x-www-form-urlencoded");byte[] b="{\"results\":{\"bindings\":[]}}".getBytes();x.getResponseHeaders().add("Content-Type","application/sparql-results+json");x.sendResponseHeaders(200,b.length);x.getResponseBody().write(b);x.close();});assertThat(client.postForm(base,base.resolve("/sparql"),"query=SELECT",Duration.ofSeconds(1),100,Set.of("application/sparql-results+json")).body()).isNotEmpty();}
  @Test void rejectsRedirect(){server.createContext("/r",x->{x.getResponseHeaders().add("Location","https://evil.test/");x.sendResponseHeaders(302,-1);x.close();});assertThatThrownBy(()->client.get(base,base.resolve("/r"),Duration.ofSeconds(1),20,Set.of("application/json"))).hasMessage("PROVIDER_REDIRECT_FORBIDDEN");}
  @Test void rejectsOversizeAndWrongMediaType(){server.createContext("/large",x->{byte[] b=new byte[32];x.getResponseHeaders().add("Content-Type","application/json");x.sendResponseHeaders(200,b.length);x.getResponseBody().write(b);x.close();});assertThatThrownBy(()->client.get(base,base.resolve("/large"),Duration.ofSeconds(1),8,Set.of("application/json"))).hasMessage("PROVIDER_RESPONSE_TOO_LARGE");assertThatThrownBy(()->client.get(base,base.resolve("/large"),Duration.ofSeconds(1),64,Set.of("text/turtle"))).hasMessage("PROVIDER_MEDIA_TYPE_REJECTED");}
  @Test void rejectsCrossOriginAndPlainHttpOutsideLoopback(){assertThatThrownBy(()->client.get(base,URI.create("http://example.org/x"),Duration.ofSeconds(1),20,Set.of("text/plain"))).hasMessage("GATEWAY_ORIGIN_VIOLATION");assertThatThrownBy(()->client.get(URI.create("http://example.org"),URI.create("http://example.org/x"),Duration.ofSeconds(1),20,Set.of("text/plain"))).hasMessage("GATEWAY_HTTPS_REQUIRED");}
}
