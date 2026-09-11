package it.comune.trieste.ouf.fixture;

import java.io.*;
import java.net.*;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.springframework.stereotype.Service;

@Service
public final class SchemaGovProxy {
  private static final Set<String> SPARQL_TYPES=Set.of("application/sparql-results+json","application/json");
  private static final Set<String> RDF_TYPES=Set.of("text/turtle","application/ld+json","application/rdf+xml","application/n-triples");
  private final SchemaGovFixtureProperties cfg;
  private final HttpClient http;

  public SchemaGovProxy(SchemaGovFixtureProperties cfg) {
    this.cfg=cfg;
    this.http=HttpClient.newBuilder().connectTimeout(cfg.connectTimeout()).followRedirects(HttpClient.Redirect.NEVER).build();
  }

  public ProxyResponse sparql(byte[] form,String correlationId) {
    if(form.length>cfg.maxRequestBytes()) throw new GatewayFailure(413,"GATEWAY_REQUEST_TOO_LARGE");
    requireAllowed(cfg.sparqlUpstream());
    var request=HttpRequest.newBuilder(cfg.sparqlUpstream()).timeout(cfg.requestTimeout())
        .header("Content-Type","application/x-www-form-urlencoded; charset=UTF-8")
        .header("Accept","application/sparql-results+json,application/json")
        .header("X-Correlation-Id",correlationId).POST(HttpRequest.BodyPublishers.ofByteArray(form)).build();
    return exchange(request,SPARQL_TYPES);
  }

  public ProxyResponse fetch(String rawUri,String correlationId) {
    URI target;
    try { target=URI.create(rawUri); } catch(RuntimeException e) { throw new GatewayFailure(400,"GATEWAY_TARGET_INVALID"); }
    requireAllowed(target);
    var request=HttpRequest.newBuilder(target).timeout(cfg.requestTimeout())
        .header("Accept",String.join(",",RDF_TYPES)).header("X-Correlation-Id",correlationId).GET().build();
    return exchange(request,RDF_TYPES);
  }

  private ProxyResponse exchange(HttpRequest request,Set<String> accepted) {
    try {
      var response=http.send(request,HttpResponse.BodyHandlers.ofInputStream());
      if(response.statusCode()/100==3) throw new GatewayFailure(502,"GATEWAY_UPSTREAM_REDIRECT");
      if(response.statusCode()!=200) throw new GatewayFailure(502,"GATEWAY_UPSTREAM_"+response.statusCode());
      String media=response.headers().firstValue("content-type").orElse("").split(";",2)[0].trim().toLowerCase();
      if(!accepted.contains(media)) throw new GatewayFailure(502,"GATEWAY_MEDIA_TYPE_REJECTED");
      try(var in=response.body();var out=new ByteArrayOutputStream()) {
        byte[] buffer=new byte[8192];int total=0,n;
        while((n=in.read(buffer))>=0) { total+=n;if(total>cfg.maxResponseBytes())throw new GatewayFailure(502,"GATEWAY_RESPONSE_TOO_LARGE");out.write(buffer,0,n); }
        return new ProxyResponse(out.toByteArray(),media);
      }
    } catch(GatewayFailure e) { throw e; }
      catch(InterruptedException e) { Thread.currentThread().interrupt();throw new GatewayFailure(503,"GATEWAY_INTERRUPTED"); }
      catch(Exception e) { throw new GatewayFailure(503,"GATEWAY_UPSTREAM_UNAVAILABLE"); }
  }

  private void requireAllowed(URI uri) {
    String host=uri.getHost();
    boolean loopback=host!=null&&Set.of("127.0.0.1","localhost","::1").contains(host);
    if(uri.getUserInfo()!=null||host==null||(!"https".equalsIgnoreCase(uri.getScheme())&&!loopback))
      throw new GatewayFailure(400,"GATEWAY_TARGET_INVALID");
    if(!loopback&&!cfg.allowedHosts().stream().anyMatch(x->x.equalsIgnoreCase(host)))
      throw new GatewayFailure(403,"GATEWAY_TARGET_FORBIDDEN");
  }

  public record ProxyResponse(byte[] body,String mediaType) {}
  public static final class GatewayFailure extends RuntimeException {
    final int status; GatewayFailure(int status,String code){super(code);this.status=status;}
  }
}
