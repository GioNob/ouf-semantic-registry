package it.comune.trieste.ouf.semantic.adapters.discovery;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.URI;
import java.net.http.*;
import java.time.Duration;
import java.util.Set;

public class BoundedGatewayClient {
  private final HttpClient http;
  public BoundedGatewayClient(Duration connectTimeout){this.http=HttpClient.newBuilder().connectTimeout(connectTimeout).followRedirects(HttpClient.Redirect.NEVER).build();}
  public Response get(URI base,URI uri,Duration timeout,int maxBytes,Set<String> mediaTypes){
    return send(base,HttpRequest.newBuilder(uri).timeout(timeout).header("Accept",String.join(",",mediaTypes)).GET().build(),maxBytes,mediaTypes);
  }
  public Response postForm(URI base,URI uri,String form,Duration timeout,int maxBytes,Set<String> mediaTypes){
    return send(base,HttpRequest.newBuilder(uri).timeout(timeout).header("Accept",String.join(",",mediaTypes)).header("Content-Type","application/x-www-form-urlencoded; charset=UTF-8").POST(HttpRequest.BodyPublishers.ofString(form)).build(),maxBytes,mediaTypes);
  }
  private Response send(URI base,HttpRequest req,int maxBytes,Set<String> mediaTypes){
    URI uri=req.uri();
    requireSameOrigin(base,uri);
    try{
      var res=http.send(req,HttpResponse.BodyHandlers.ofInputStream());
      if(res.statusCode()/100==3)throw new ProviderFailure("PROVIDER_REDIRECT_FORBIDDEN");
      if(res.statusCode()!=200)throw new ProviderFailure("PROVIDER_HTTP_"+res.statusCode());
      var type=res.headers().firstValue("content-type").orElse("").split(";",2)[0].trim().toLowerCase();
      if(!mediaTypes.contains(type))throw new ProviderFailure("PROVIDER_MEDIA_TYPE_REJECTED");
      try(InputStream in=res.body();var out=new ByteArrayOutputStream()){byte[] buf=new byte[8192];int total=0,n;while((n=in.read(buf))>=0){total+=n;if(total>maxBytes)throw new ProviderFailure("PROVIDER_RESPONSE_TOO_LARGE");out.write(buf,0,n);}return new Response(out.toByteArray(),type);}
    }catch(ProviderFailure e){throw e;}catch(Exception e){throw new ProviderFailure("PROVIDER_UNAVAILABLE",e);}
  }
  static void requireSameOrigin(URI base,URI target){if(!"https".equalsIgnoreCase(base.getScheme())&&!isLoopback(base))throw new ProviderFailure("GATEWAY_HTTPS_REQUIRED");if(!base.getScheme().equalsIgnoreCase(target.getScheme())||!base.getHost().equalsIgnoreCase(target.getHost())||effectivePort(base)!=effectivePort(target)||target.getUserInfo()!=null)throw new ProviderFailure("GATEWAY_ORIGIN_VIOLATION");}
  private static boolean isLoopback(URI u){return "http".equalsIgnoreCase(u.getScheme())&&Set.of("127.0.0.1","localhost","::1").contains(u.getHost());}
  private static int effectivePort(URI u){return u.getPort()>=0?u.getPort():("https".equalsIgnoreCase(u.getScheme())?443:80);}
  public record Response(byte[] body,String mediaType){}
  public static class ProviderFailure extends RuntimeException{public ProviderFailure(String m){super(m);}public ProviderFailure(String m,Throwable t){super(m,t);}}
}
