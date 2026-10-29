package it.comune.trieste.ouf.semantic.adapters.discovery;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.nio.file.attribute.PosixFilePermission;
import java.time.*;
import java.util.*;
import java.util.function.Supplier;
import static it.comune.trieste.ouf.semantic.adapters.discovery.BoundedGatewayClient.ProviderFailure;

/** Workload credentials stay in the mounted file; access tokens stay in process memory. */
final class ClientCredentialsTokenSource implements Supplier<String> {
  private final GatewayOAuthProperties cfg;
  private final ObjectMapper json;
  private final Clock clock;
  private final HttpClient http;
  private final boolean loopbackFixture;
  private String cached;
  private Instant refreshAt;

  ClientCredentialsTokenSource(GatewayOAuthProperties cfg, ObjectMapper json) {
    this(cfg,json,Clock.systemUTC(),false);
  }
  ClientCredentialsTokenSource(GatewayOAuthProperties cfg,ObjectMapper json,Clock clock,boolean loopbackFixture) {
    this.cfg=cfg;this.json=json;this.clock=clock;this.loopbackFixture=loopbackFixture;
    this.http=HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(2))
        .followRedirects(HttpClient.Redirect.NEVER).build();
  }
  @Override public synchronized String get() {
    validate();
    if(cached!=null && clock.instant().isBefore(refreshAt))return cached;
    // A failed renewal must never return the old token.
    cached=null;refreshAt=null;
    try {
      String form="grant_type=client_credentials&client_id="+enc(cfg.clientId())
          +"&client_secret="+enc(secret())+"&scope="+enc(cfg.scope());
      Instant started=clock.instant();
      HttpRequest request=HttpRequest.newBuilder(cfg.tokenEndpoint()).timeout(cfg.requestTimeout())
          .header("Accept","application/json")
          .header("Content-Type","application/x-www-form-urlencoded; charset=UTF-8")
          .POST(HttpRequest.BodyPublishers.ofString(form)).build();
      var response=BoundedResponseBody.send(http,request,cfg.maxResponseBytes());
      if(response.statusCode()!=200)throw new ProviderFailure("GATEWAY_TOKEN_REJECTED");
      if(!response.headers().firstValue("content-type").orElse("").split(";",2)[0].trim()
          .equalsIgnoreCase("application/json"))throw new ProviderFailure("GATEWAY_TOKEN_INVALID");
      JsonNode body=json.readTree(response.body());
      JsonNode expires=body.path("expires_in");
      String token=body.path("access_token").asText("");
      Set<String> granted=new HashSet<>(Arrays.asList(body.path("scope").asText("").split(" +")));
      if(!body.path("token_type").asText("").equalsIgnoreCase("Bearer")
          || !token.matches("[A-Za-z0-9._~+/-]{1,16384}={0,2}")
          || !expires.isIntegralNumber() || !expires.canConvertToInt()
          || expires.intValue()<=0 || expires.intValue()>86400
          || !granted.containsAll(Arrays.asList(cfg.scope().split(" +"))))
        throw new ProviderFailure("GATEWAY_TOKEN_INVALID");
      refreshAt=started.plusSeconds(expires.intValue()).minus(cfg.refreshSkew());
      if(!clock.instant().isBefore(refreshAt))throw new ProviderFailure("GATEWAY_TOKEN_INVALID");
      cached=token;return cached;
    }catch(ProviderFailure e){throw e;}
    catch(InterruptedException e){Thread.currentThread().interrupt();throw new ProviderFailure("GATEWAY_TOKEN_UNAVAILABLE");}
    catch(Exception e){throw new ProviderFailure("GATEWAY_TOKEN_UNAVAILABLE");}
  }
  private void validate() {
    if(cfg==null || !cfg.enabled())throw new ProviderFailure("GATEWAY_AUTH_REQUIRED");
    URI u=cfg.tokenEndpoint();
    boolean fixture=u!=null && loopbackFixture && "http".equalsIgnoreCase(u.getScheme())
        && Set.of("127.0.0.1","localhost").contains(u.getHost());
    if(u==null || u.getHost()==null || (!"https".equalsIgnoreCase(u.getScheme()) && !fixture)
        || u.getUserInfo()!=null || u.getQuery()!=null || u.getFragment()!=null
        || u.getPath()==null || u.getPath().isEmpty() || u.getPath().equals("/")
        || cfg.clientId()==null || cfg.clientId().isBlank() || cfg.clientId().length()>256
        || cfg.clientId().chars().anyMatch(Character::isISOControl)
        || cfg.clientSecretFile()==null || cfg.scope()==null
        || !cfg.scope().matches("[A-Za-z0-9._:-]+( [A-Za-z0-9._:-]+)*")
        || cfg.requestTimeout()==null || cfg.requestTimeout().isNegative() || cfg.requestTimeout().isZero()
        || cfg.requestTimeout().compareTo(Duration.ofSeconds(30))>0
        || cfg.refreshSkew()==null || cfg.refreshSkew().isNegative()
        || cfg.refreshSkew().compareTo(Duration.ofSeconds(60))>0
        || cfg.maxResponseBytes()<1 || cfg.maxResponseBytes()>65536)
      throw new ProviderFailure("GATEWAY_AUTH_CONFIGURATION_INVALID");
  }
  private String secret() throws Exception {
    Path file=cfg.clientSecretFile();
    if(!Files.isRegularFile(file,LinkOption.NOFOLLOW_LINKS))throw new ProviderFailure("GATEWAY_CREDENTIAL_FILE_INVALID");
    try {
      Set<PosixFilePermission> permissions=Files.getPosixFilePermissions(file,LinkOption.NOFOLLOW_LINKS);
      if(permissions.stream().anyMatch(p->p.name().startsWith("GROUP_") || p.name().startsWith("OTHERS_")))
        throw new ProviderFailure("GATEWAY_CREDENTIAL_FILE_INVALID");
    }catch(UnsupportedOperationException ignored){ /* Non-POSIX deployment ACLs remain an installation check. */ }
    byte[] bytes;
    try(var in=Files.newInputStream(file,LinkOption.NOFOLLOW_LINKS)){bytes=in.readNBytes(4097);}
    if(bytes.length>4096)throw new ProviderFailure("GATEWAY_CREDENTIAL_FILE_INVALID");
    String value=new String(bytes,StandardCharsets.UTF_8).strip();
    if(value.isEmpty() || value.chars().anyMatch(Character::isISOControl))
      throw new ProviderFailure("GATEWAY_CREDENTIAL_FILE_INVALID");
    return value;
  }
  private static String enc(String s){return URLEncoder.encode(s,StandardCharsets.UTF_8);}
}
