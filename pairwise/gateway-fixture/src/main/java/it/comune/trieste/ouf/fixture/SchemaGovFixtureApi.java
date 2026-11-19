package it.comune.trieste.ouf.fixture;

import jakarta.servlet.http.HttpServletRequest;
import java.util.UUID;
import java.util.Map;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

@RestController
public class SchemaGovFixtureApi {
  private static final String CORRELATION="X-Correlation-Id";
  @Value("${OUF_PAIRWISE_PROVIDER_SECRET:}") private String providerSecret;
  @Value("${OUF_PAIRWISE_PROVIDER_TOKEN:}") private String providerToken;
  private final SchemaGovProxy proxy;
  SchemaGovFixtureApi(SchemaGovProxy proxy){this.proxy=proxy;}

  @PostMapping(path="/semantic-providers/schema-gov/sparql",consumes=MediaType.APPLICATION_FORM_URLENCODED_VALUE)
  ResponseEntity<byte[]> sparql(@RequestBody byte[] body,HttpServletRequest request){authenticate(request);return response(proxy.sparql(body,correlation(request)));}

  @GetMapping("/semantic-providers/schema-gov/fetch")
  ResponseEntity<byte[]> fetch(@RequestParam("uri") String uri,HttpServletRequest request){authenticate(request);return response(proxy.fetch(uri,correlation(request)));}

  // Ephemeral fixture issuer only: this is not production IAM or JWT admission.
  @PostMapping(path="/fixture/oauth/token",consumes=MediaType.APPLICATION_FORM_URLENCODED_VALUE)
  Map<String,Object> token(@RequestParam("grant_type") String grant,@RequestParam("client_id") String client,
      @RequestParam("client_secret") String secret,@RequestParam("scope") String scope){
    if(!"client_credentials".equals(grant) || !"fixture-semantic".equals(client)
        || !"fixture.gateway.invoke".equals(scope) || providerSecret.isEmpty()
        || !equal(providerSecret,secret) || providerToken.isEmpty())
      throw new ResponseStatusException(HttpStatus.UNAUTHORIZED);
    return Map.of("access_token",providerToken,"token_type","Bearer","expires_in",300,"scope",scope);
  }
  private void authenticate(HttpServletRequest request){
    String header=request.getHeader("Authorization");
    if(providerToken.isEmpty() || header==null || !equal("Bearer "+providerToken,header))
      throw new ResponseStatusException(HttpStatus.UNAUTHORIZED);
  }
  private boolean equal(String a,String b){return MessageDigest.isEqual(a.getBytes(StandardCharsets.UTF_8),b.getBytes(StandardCharsets.UTF_8));}
  private ResponseEntity<byte[]> response(SchemaGovProxy.ProxyResponse result){return ResponseEntity.ok().contentType(MediaType.parseMediaType(result.mediaType())).body(result.body());}
  private String correlation(HttpServletRequest request){String value=request.getHeader(CORRELATION);return value!=null&&value.matches("[A-Za-z0-9._:-]{1,128}")?value:UUID.randomUUID().toString();}

  @ExceptionHandler(SchemaGovProxy.GatewayFailure.class)
  ResponseEntity<ProblemDetail> failure(SchemaGovProxy.GatewayFailure e){var p=ProblemDetail.forStatusAndDetail(HttpStatusCode.valueOf(e.status),e.getMessage());p.setTitle("Semantic provider gateway rejection");return ResponseEntity.status(e.status).body(p);}
}
