package it.comune.trieste.ouf.semantic.adapters.discovery;

import java.net.URI;
import java.net.http.*;
import java.time.Duration;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import it.comune.trieste.ouf.semantic.ports.DiscoveryTraffic;
import it.comune.trieste.ouf.semantic.ports.DiscoveryTraffic.Route;
import it.comune.trieste.ouf.semantic.ports.DiscoveryTraffic.Origin;

public class BoundedGatewayClient {
  private final HttpClient http;
  private final java.util.function.Supplier<String> tokenSource;
  private final RateLimitOriginVerifier originVerifier;
  public BoundedGatewayClient(Duration connectTimeout){this(connectTimeout,null);}
  public BoundedGatewayClient(Duration connectTimeout,java.util.function.Supplier<String> tokenSource){
    this(connectTimeout,tokenSource,RateLimitOriginVerifier.UNATTESTED);
  }
  BoundedGatewayClient(Duration connectTimeout,java.util.function.Supplier<String> tokenSource,RateLimitOriginVerifier originVerifier){
    this.tokenSource=tokenSource;this.originVerifier=originVerifier;
    this.http=HttpClient.newBuilder().connectTimeout(connectTimeout).followRedirects(HttpClient.Redirect.NEVER).build();
  }
  public Response get(URI base,URI uri,Duration timeout,int maxBytes,Set<String> mediaTypes){
    return get(base,uri,timeout,maxBytes,mediaTypes,DiscoveryTraffic.NONE,null);
  }
  Response get(URI base,URI uri,Duration timeout,int maxBytes,Set<String> mediaTypes,DiscoveryTraffic traffic,String resource){
    return send(base,request(base,uri,timeout).header("Accept",String.join(",",mediaTypes)).GET().build(),
        maxBytes,mediaTypes,traffic,Route.fetch,resource);
  }
  public Response postForm(URI base,URI uri,String form,Duration timeout,int maxBytes,Set<String> mediaTypes){
    return postForm(base,uri,form,timeout,maxBytes,mediaTypes,DiscoveryTraffic.NONE);
  }
  Response postForm(URI base,URI uri,String form,Duration timeout,int maxBytes,Set<String> mediaTypes,DiscoveryTraffic traffic){
    var req=request(base,uri,timeout).header("Accept",String.join(",",mediaTypes))
        .header("Content-Type","application/x-www-form-urlencoded; charset=UTF-8").POST(HttpRequest.BodyPublishers.ofString(form)).build();
    return send(base,req,maxBytes,mediaTypes,traffic,Route.search,null);
  }
  private Response send(URI base,HttpRequest req,int maxBytes,Set<String> mediaTypes,DiscoveryTraffic traffic,Route route,String resource){
    URI uri=req.uri();
    requireSameOrigin(base,uri);
    var limited=new AtomicReference<Origin>();
    try{
      var boundedBody=BoundedResponseBody.handler(maxBytes);
      var res=BoundedResponseBody.send(http,req,headers->{
        // Once the 429 headers arrive, an oversized or slow error body cannot mask the limit.
        if(headers.statusCode()==429){
          limited.set(origin(req,headers));
          throw new ProviderFailure(ProviderFailurePolicy.http(
              429,headers.headers().firstValue("Retry-After").orElse(null),java.time.Clock.systemUTC()));
        }
        return boundedBody.apply(headers);
      },()->traffic.sent(route,resource));
      if(res.statusCode()/100==3)throw new ProviderFailure("PROVIDER_REDIRECT_FORBIDDEN");
      if(res.statusCode()!=200)throw new ProviderFailure(ProviderFailurePolicy.http(res.statusCode(),res.headers().firstValue("retry-after").orElse(null),java.time.Clock.systemUTC()));
      var type=res.headers().firstValue("content-type").orElse("").split(";",2)[0].trim().toLowerCase(java.util.Locale.ROOT);
      if(!mediaTypes.contains(type))throw new ProviderFailure("PROVIDER_MEDIA_TYPE_REJECTED");
      return new Response(res.body(),type);
    }catch(RuntimeException e){throw e;}catch(Exception e){var decision=ProviderFailurePolicy.exception(e);if(decision.kind()==ProviderFailurePolicy.Kind.CANCELLED)Thread.currentThread().interrupt();throw new ProviderFailure(decision,e);}
    finally{
      Origin observed=limited.get();
      if(observed!=null)traffic.http429(route,observed);
    }
  }
  private Origin origin(HttpRequest request,HttpResponse.ResponseInfo response){
    try{return java.util.Objects.requireNonNullElse(originVerifier.verifiedOrigin(request.method(),request.uri(),response),Origin.UNKNOWN);}
    catch(RuntimeException unverifiable){return Origin.UNKNOWN;}
  }
  static Duration remaining(long deadline){
    long nanos=deadline-System.nanoTime();
    if(nanos<1_000_000)throw new ProviderFailure("PROVIDER_TIMEOUT");
    return Duration.ofNanos(nanos);
  }
  private HttpRequest.Builder request(URI base,URI target,Duration timeout){
    requireSameOrigin(base,target); // Never obtain or disclose a token to another origin.
    var builder=HttpRequest.newBuilder(target);
    long deadline=System.nanoTime()+timeout.toNanos();
    if(tokenSource!=null){
      String token=tokenSource instanceof ClientCredentialsTokenSource oauth?oauth.get(deadline):tokenSource.get();
      builder.header("Authorization","Bearer "+token);
    }
    return builder.timeout(remaining(deadline));
  }
  static void requireSameOrigin(URI base,URI target){if(base==null||target==null||base.getHost()==null||target.getHost()==null||base.getUserInfo()!=null||base.getFragment()!=null||target.getFragment()!=null)throw new ProviderFailure("GATEWAY_ORIGIN_VIOLATION");if(!"https".equalsIgnoreCase(base.getScheme())&&!isLoopback(base))throw new ProviderFailure("GATEWAY_HTTPS_REQUIRED");if(!base.getScheme().equalsIgnoreCase(target.getScheme())||!base.getHost().equalsIgnoreCase(target.getHost())||effectivePort(base)!=effectivePort(target)||target.getUserInfo()!=null)throw new ProviderFailure("GATEWAY_ORIGIN_VIOLATION");}
  private static boolean isLoopback(URI u){return "http".equalsIgnoreCase(u.getScheme())&&Set.of("127.0.0.1","localhost","::1").contains(u.getHost());}
  private static int effectivePort(URI u){return u.getPort()>=0?u.getPort():("https".equalsIgnoreCase(u.getScheme())?443:80);}
  public record Response(byte[] body,String mediaType){}
  public static class ProviderFailure extends RuntimeException{
    private final ProviderFailurePolicy.Decision decision;
    public ProviderFailure(String code){this(ProviderFailurePolicy.code(code),null);}
    public ProviderFailure(String code,Throwable cause){this(ProviderFailurePolicy.code(code),cause);}
    public ProviderFailure(ProviderFailurePolicy.Decision decision){this(decision,null);}
    public ProviderFailure(ProviderFailurePolicy.Decision decision,Throwable cause){super(decision.code(),cause);this.decision=decision;}
    public ProviderFailurePolicy.Decision decision(){return decision;}
  }
}

