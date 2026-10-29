package it.comune.trieste.ouf.semantic.adapters.discovery;

import static org.assertj.core.api.Assertions.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.net.httpserver.HttpServer;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.nio.file.attribute.PosixFilePermissions;
import java.time.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.io.TempDir;

class ClientCredentialsTokenSourceTest {
  @TempDir Path temp;
  HttpServer server;URI base;Path secret;
  AtomicInteger tokenCalls=new AtomicInteger(),gatewayCalls=new AtomicInteger();
  volatile String response="{\"access_token\":\"fixture.token\",\"token_type\":\"Bearer\",\"expires_in\":300,\"scope\":\"gateway.invoke\"}";
  volatile String contentType="application/json";
  volatile int status=200;
  volatile long delay;
  volatile String form,authorization;
  final MutableClock clock=new MutableClock();
  @BeforeEach void start() throws Exception {
    secret=temp.resolve("credential");Files.writeString(secret,"test-secret\n");
    Files.setPosixFilePermissions(secret,PosixFilePermissions.fromString("rw-------"));
    server=HttpServer.create(new InetSocketAddress("127.0.0.1",0),0);
    server.createContext("/oauth/token",x->{
      tokenCalls.incrementAndGet();form=new String(x.getRequestBody().readAllBytes(),StandardCharsets.UTF_8);
      byte[] body=response.getBytes(StandardCharsets.UTF_8);
      x.getResponseHeaders().add("Content-Type",contentType);
      x.getResponseHeaders().add("Location","/unexpected");x.sendResponseHeaders(status,body.length);
      try{if(delay>0)Thread.sleep(delay);x.getResponseBody().write(body);}catch(Exception ignored){}finally{x.close();}
    });
    server.createContext("/gateway/search",x->{gatewayCalls.incrementAndGet();authorization=x.getRequestHeaders().getFirst("Authorization");byte[] body="{}".getBytes();x.getResponseHeaders().add("Content-Type","application/json");x.sendResponseHeaders(200,body.length);x.getResponseBody().write(body);x.close();});
    server.start();base=URI.create("http://127.0.0.1:"+server.getAddress().getPort());
  }
  @AfterEach void stop(){server.stop(0);}
  GatewayOAuthProperties config(boolean enabled,URI endpoint,int limit,Duration timeout){return new GatewayOAuthProperties(enabled,endpoint,"custom-client",secret,"gateway.invoke",timeout,Duration.ofSeconds(10),limit);}
  ClientCredentialsTokenSource source(){return new ClientCredentialsTokenSource(config(true,base.resolve("/oauth/token"),32768,Duration.ofSeconds(2)),new ObjectMapper(),clock,true);}
  @Test void authenticatesGetAndPostAndCachesToken() {
    var source=source();var client=new BoundedGatewayClient(Duration.ofSeconds(1),source);
    client.get(base,base.resolve("/gateway/search"),Duration.ofSeconds(1),100,Set.of("application/json"));
    client.postForm(base,base.resolve("/gateway/search"),"query=x",Duration.ofSeconds(1),100,Set.of("application/json"));
    assertThat(authorization).isEqualTo("Bearer fixture.token");assertThat(tokenCalls).hasValue(1);assertThat(gatewayCalls).hasValue(2);
    assertThat(form).contains("grant_type=client_credentials","client_id=custom-client","client_secret=test-secret","scope=gateway.invoke");
  }
  @Test void concurrentCallsObtainOneTokenAndRenewBeforeExpiry() throws Exception {
    var source=source();try(var executor=Executors.newFixedThreadPool(6)){
      List<Future<String>> calls=new ArrayList<>();for(int i=0;i<12;i++)calls.add(executor.submit(source::get));
      for(var call:calls)assertThat(call.get()).isEqualTo("fixture.token");
    }
    assertThat(tokenCalls).hasValue(1);clock.now=clock.now.plusSeconds(291);source.get();assertThat(tokenCalls).hasValue(2);
    clock.now=clock.now.plusSeconds(291);status=401;
    assertThatThrownBy(source::get).hasMessage("GATEWAY_TOKEN_REJECTED");assertThat(tokenCalls).hasValue(3);
  }
  @Test void originViolationDoesNotRequestTokenOrContactGateway() {
    var client=new BoundedGatewayClient(Duration.ofSeconds(1),source());
    assertThatThrownBy(()->client.get(base,URI.create("https://other.example:9443/search"),Duration.ofSeconds(1),100,Set.of("application/json"))).hasMessage("GATEWAY_ORIGIN_VIOLATION");
    assertThat(tokenCalls).hasValue(0);assertThat(gatewayCalls).hasValue(0);
  }
  @Test void disabledAuthenticationAndProductionPlainHttpFailClosed() {
    var disabled=new ClientCredentialsTokenSource(config(false,base.resolve("/oauth/token"),100,Duration.ofSeconds(1)),new ObjectMapper(),clock,true);
    var client=new BoundedGatewayClient(Duration.ofSeconds(1),disabled);
    assertThatThrownBy(()->client.get(base,base.resolve("/gateway/search"),Duration.ofSeconds(1),100,Set.of("application/json"))).hasMessage("GATEWAY_AUTH_REQUIRED");
    assertThatThrownBy(new ClientCredentialsTokenSource(config(true,base.resolve("/oauth/token"),100,Duration.ofSeconds(1)),new ObjectMapper())::get).hasMessage("GATEWAY_AUTH_CONFIGURATION_INVALID");
    assertThat(tokenCalls).hasValue(0);assertThat(gatewayCalls).hasValue(0);
  }
  @Test void rejectsWrongScopeTypeLifetimeAndMalformedTokenWithoutLeakingResponse() {
    for(String invalid:List.of("{}","{\"access_token\":\"secret\\n\"}",response.replace("gateway.invoke","wrong.scope"),response.replace("300","0"),response.replace("300","\"300\""),response.replace("Bearer","Basic"),"not-json")){
      response=invalid;assertThatThrownBy(source()::get).isInstanceOf(BoundedGatewayClient.ProviderFailure.class).satisfies(e->assertThat(e.getMessage()).startsWith("GATEWAY_TOKEN_").doesNotContain("secret","wrong.scope","not-json"));
    }
    assertThat(gatewayCalls).hasValue(0);
  }
  @Test void rejectsRedirectMediaAndOversizedResponses() {
    status=302;assertThatThrownBy(source()::get).hasMessage("GATEWAY_TOKEN_REJECTED");assertThat(tokenCalls).hasValue(1);
    status=200;contentType="text/html";assertThatThrownBy(source()::get).hasMessage("GATEWAY_TOKEN_INVALID");
    contentType="application/json";response="x".repeat(40000);assertThatThrownBy(source()::get).isInstanceOf(BoundedGatewayClient.ProviderFailure.class);
    assertThat(gatewayCalls).hasValue(0);
  }
  @Test void timeoutIncludesBodyAfterHeaders() {
    delay=600;
    var source=new ClientCredentialsTokenSource(config(true,base.resolve("/oauth/token"),32768,Duration.ofMillis(100)),new ObjectMapper(),clock,true);
    long started=System.nanoTime();assertThatThrownBy(source::get).hasMessage("GATEWAY_TOKEN_UNAVAILABLE");
    assertThat(Duration.ofNanos(System.nanoTime()-started)).isLessThan(Duration.ofMillis(500));
  }
  @Test void rejectsPublicSymlinkAndOversizedCredentialsBeforeNetwork() throws Exception {
    Files.setPosixFilePermissions(secret,PosixFilePermissions.fromString("rw-r--r--"));assertThatThrownBy(source()::get).hasMessage("GATEWAY_CREDENTIAL_FILE_INVALID");
    Files.setPosixFilePermissions(secret,PosixFilePermissions.fromString("rw-------"));Files.writeString(secret,"x".repeat(4097));assertThatThrownBy(source()::get).hasMessage("GATEWAY_CREDENTIAL_FILE_INVALID");
    Path target=temp.resolve("target");Files.move(secret,target);Files.createSymbolicLink(secret,target);assertThatThrownBy(source()::get).hasMessage("GATEWAY_CREDENTIAL_FILE_INVALID");
    assertThat(tokenCalls).hasValue(0);
  }
  static class MutableClock extends Clock {
    Instant now=Instant.parse("2026-10-02T00:00:00Z");
    public ZoneId getZone(){return ZoneOffset.UTC;}
    public Clock withZone(ZoneId zone){return this;}
    public Instant instant(){return now;}
  }
}
