package it.comune.trieste.ouf.fixture;

import static org.assertj.core.api.Assertions.*;
import com.sun.net.httpserver.HttpServer;
import java.net.*;
import java.time.Duration;
import java.util.Set;
import org.junit.jupiter.api.*;

class SchemaGovProxyTest {
  HttpServer upstream; URI base; SchemaGovProxy proxy;
  @BeforeEach void start() throws Exception {upstream=HttpServer.create(new InetSocketAddress("127.0.0.1",0),0);upstream.start();base=URI.create("http://127.0.0.1:"+upstream.getAddress().getPort());proxy=new SchemaGovProxy(new SchemaGovFixtureProperties(base.resolve("/sparql"),Set.of("schema.gov.it"),Duration.ofSeconds(1),Duration.ofSeconds(1),64,128));}
  @AfterEach void stop(){upstream.stop(0);}

  @Test void forwardsBoundedSparqlAndCorrelation(){upstream.createContext("/sparql",x->{try{assertThat(x.getRequestHeaders().getFirst("X-Correlation-Id")).isEqualTo("trace-1");byte[] b="{\"results\":{\"bindings\":[]}}".getBytes();x.getResponseHeaders().add("Content-Type","application/sparql-results+json");x.sendResponseHeaders(200,b.length);x.getResponseBody().write(b);x.close();}catch(Exception e){throw new RuntimeException(e);}});assertThat(proxy.sparql("query=SELECT".getBytes(),"trace-1").mediaType()).isEqualTo("application/sparql-results+json");}
  @Test void fetchesAuthoritativeRdfThroughSparql(){upstream.createContext("/sparql",x->{try{assertThat(x.getRequestMethod()).isEqualTo("POST");String form=new String(x.getRequestBody().readAllBytes());assertThat(URLDecoder.decode(form,java.nio.charset.StandardCharsets.UTF_8)).contains("CONSTRUCT").contains("https://schema.gov.it/resource");byte[] b="<urn:a> <urn:p> <urn:b> .".getBytes();x.getResponseHeaders().add("Content-Type","text/turtle");x.sendResponseHeaders(200,b.length);x.getResponseBody().write(b);x.close();}catch(Exception e){throw new RuntimeException(e);}});assertThat(proxy.fetch("https://schema.gov.it/resource","trace").mediaType()).isEqualTo("text/turtle");}
  @Test void rejectsArbitraryHostAndCredentials(){assertThatThrownBy(()->proxy.fetch("https://evil.example/x","x")).hasMessage("GATEWAY_TARGET_FORBIDDEN");assertThatThrownBy(()->proxy.fetch("https://user:pass@schema.gov.it/x","x")).hasMessage("GATEWAY_TARGET_INVALID");}
  @Test void rejectsRedirectWrongMediaAndOversize(){upstream.createContext("/sparql",x->{try{x.getResponseHeaders().add("Location","/other");x.sendResponseHeaders(302,-1);x.close();}catch(Exception e){throw new RuntimeException(e);}});assertThatThrownBy(()->proxy.sparql("query=x".getBytes(),"x")).hasMessage("GATEWAY_UPSTREAM_REDIRECT");}
  @Test void rejectsOversizeRequest(){assertThatThrownBy(()->proxy.sparql(new byte[65],"x")).hasMessage("GATEWAY_REQUEST_TOO_LARGE");}
}
