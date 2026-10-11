package it.comune.trieste.ouf.semantic.adapters.discovery;

import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.*;
import java.net.http.HttpTimeoutException;
import java.time.*;
import java.util.Set;
import java.util.concurrent.*;
import javax.net.ssl.SSLHandshakeException;

/** Dependency-free fixture exercises the actual bounded HTTP adapter, not a parallel implementation. */
public class ProviderFailurePolicyNative {
  private static int assertions;
  private static void check(boolean value){assertions++;if(!value)throw new AssertionError("classification assertion "+assertions);}
  private static void kind(Throwable error,ProviderFailurePolicy.Kind expected,String code){
    var decision=ProviderFailurePolicy.exception(error);check(decision.kind()==expected);check(decision.code().equals(code));
  }
  public static void main(String[] args)throws Exception {
    var transientKind=ProviderFailurePolicy.Kind.TRANSIENT;
    var blocked=ProviderFailurePolicy.Kind.BLOCKED;
    var clock=Clock.fixed(Instant.parse("2026-10-11T12:00:00Z"),ZoneOffset.UTC);
    for(int status:new int[]{408,429,502,503,504})check(ProviderFailurePolicy.http(status,null,clock).kind()==transientKind);
    for(int status:new int[]{400,401,403,404,409,500,501,505})check(ProviderFailurePolicy.http(status,null,clock).kind()==blocked);
    check(ProviderFailurePolicy.http(503,"3600",clock).retryAfter().equals(Duration.ofHours(1)));
    check(ProviderFailurePolicy.http(429,"Sun, 11 Oct 2026 13:00:00 GMT",clock).retryAfter().equals(Duration.ofHours(1)));
    check(ProviderFailurePolicy.http(503,"172800",clock).retryAfter().equals(Duration.ofDays(2)));
    check(ProviderFailurePolicy.http(503,"Sun, 11 Oct 2026 11:00:00 GMT",clock).retryAfter().isZero());
    for(String invalid:new String[]{"", "-1", "NaN", "99999999999999999999999", "secret invalid date"})
      check(ProviderFailurePolicy.http(503,invalid,clock).code().equals("PROVIDER_RETRY_AFTER_INVALID"));
    kind(new ConnectException("sensitive endpoint"),transientKind,"PROVIDER_UNAVAILABLE");
    kind(new UnknownHostException("sensitive endpoint"),transientKind,"PROVIDER_UNAVAILABLE");
    kind(new ExecutionException(new HttpTimeoutException("sensitive")),transientKind,"PROVIDER_TIMEOUT");
    kind(new SSLHandshakeException("private certificate detail"),blocked,"PROVIDER_TLS_UNPROVEN");
    kind(new IOException("opaque error with private data"),blocked,"PROVIDER_UNKNOWN");
    kind(new IllegalStateException("secret=do-not-publish"),blocked,"PROVIDER_UNKNOWN");
    kind(new InterruptedException("cancel"),ProviderFailurePolicy.Kind.CANCELLED,"PROVIDER_INTERRUPTED");
    check(new BoundedGatewayClient.ProviderFailure("secret=do-not-publish").getMessage().equals("PROVIDER_UNKNOWN"));

    var executor=Executors.newCachedThreadPool();
    var server=HttpServer.create(new InetSocketAddress("127.0.0.1",0),0);server.setExecutor(executor);
    for(int status:new int[]{401,429,500,503})server.createContext("/"+status,x->{
      x.getResponseHeaders().add("Retry-After","3600");x.sendResponseHeaders(status,-1);x.close();
    });
    server.createContext("/slow",x->{
      try{x.getResponseHeaders().add("Content-Type","application/json");x.sendResponseHeaders(200,2);
        x.getResponseBody().write('{');x.getResponseBody().flush();Thread.sleep(800);x.getResponseBody().write('}');
      }catch(Exception ignored){}finally{x.close();}
    });
    server.start();var base=URI.create("http://127.0.0.1:"+server.getAddress().getPort());
    var client=new BoundedGatewayClient(Duration.ofSeconds(1));
    try {
      for(int status:new int[]{401,429,500,503}){
        try{client.get(base,base.resolve("/"+status),Duration.ofSeconds(2),100,Set.of("application/json"));throw new AssertionError("HTTP failure accepted");}
        catch(BoundedGatewayClient.ProviderFailure e){check(e.decision().code().equals("PROVIDER_HTTP_"+status));
          check(e.decision().kind()==(status==429||status==503?transientKind:blocked));
          if(status==429||status==503)check(e.decision().retryAfter().equals(Duration.ofHours(1)));
        }
      }
      long started=System.nanoTime();
      try{client.get(base,base.resolve("/slow"),Duration.ofMillis(200),100,Set.of("application/json"));throw new AssertionError("body deadline ignored");}
      catch(BoundedGatewayClient.ProviderFailure e){check(e.decision().kind()==transientKind);check(e.decision().code().equals("PROVIDER_TIMEOUT"));}
      check(Duration.ofNanos(System.nanoTime()-started).compareTo(Duration.ofSeconds(2))<0);
      Thread.currentThread().interrupt();
      try{client.get(base,base.resolve("/503"),Duration.ofSeconds(1),100,Set.of("application/json"));throw new AssertionError("interruption ignored");}
      catch(BoundedGatewayClient.ProviderFailure e){check(e.decision().kind()==ProviderFailurePolicy.Kind.CANCELLED);check(Thread.currentThread().isInterrupted());}
      finally{Thread.interrupted();}
    }finally{server.stop(0);executor.shutdownNow();}
    System.out.println("OUF_DISCOVERY_FAILURE_POLICY={\"status\":\"PASS\",\"assertions\":"+assertions+",\"actualHttpAdapter\":true,\"retryAfterSecondsAndDate\":true,\"slowBodyDeadline\":true,\"unknownAndTlsBlocked\":true,\"interruptionPreserved\":true,\"durableRecoveryQualified\":false,\"targetEffects\":0}");
  }
}
