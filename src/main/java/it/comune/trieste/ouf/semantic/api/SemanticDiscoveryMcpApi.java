package it.comune.trieste.ouf.semantic.api;

import com.fasterxml.jackson.databind.*;
import it.comune.trieste.ouf.authorization.*;
import it.comune.trieste.ouf.semantic.application.DiscoveryJobService;
import jakarta.servlet.http.HttpServletRequest;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/** Delegated discovery jobs only. Adoption and publication retain their native HUMAN boundaries. */
@RestController
@RequestMapping("/api/internal/v1/semantic/discovery")
public class SemanticDiscoveryMcpApi {
  private final SemanticDiscoveryDelegation receipts;
  private final DiscoveryJobService jobs;
  private final ObjectMapper json;
  public SemanticDiscoveryMcpApi(SemanticDiscoveryDelegation receipts,DiscoveryJobService jobs,ObjectMapper json) {
    this.receipts=receipts;this.jobs=jobs;
    this.json=json.copy().enable(com.fasterxml.jackson.core.JsonParser.Feature.STRICT_DUPLICATE_DETECTION);
  }
  private record Input(JsonNode arguments,String actor) {}
  private Input input(byte[] raw,HttpServletRequest request,String capability,String operation,Set<String> keys) {
    var principal=receipts.verify(request.getHeader("X-OUF-Semantic-Discovery-Receipt"),request.getRequestURI(),capability,raw);
    request.setAttribute(ServletAuthorization.TRUSTED_PRINCIPAL,new TrustedPrincipal(principal));
    OwnerAuthorization.bind(request).require(capability,new ResourceContext("semantic.DiscoveryApi",null,principal.tenantId(),null,Map.of("module","SEMANTIC")));
    try {
      var e=json.readTree(raw);var a=e.required("Arguments");
      if(!capability.equals(e.required("CapabilityID").asText())||!("capability://"+capability).equals(e.required("GatewayBindingRef").asText())
          ||!"semantic".equals(e.required("Owner").asText())||!operation.equals(e.required("OperationClass").asText())||!a.isObject())throw new IllegalArgumentException();
      for(var fields=a.fieldNames();fields.hasNext();)if(!keys.contains(fields.next()))throw new IllegalArgumentException();
      // Namespace delegated jobs by trusted issuer, tenant and subject, never caller-supplied identity.
      // Native subject-only job history is preserved and cannot alias this bridge's namespace.
      String actor="mcp-discovery-v1:"+HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(
          json.writeValueAsBytes(List.of(principal.issuer(),principal.tenantId(),principal.subjectId()))));
      return new Input(a,actor);
    }catch(Exception e){throw new IllegalArgumentException("SEM_DISCOVERY_ARGUMENTS_INVALID");}
  }
  @PostMapping("/request") public Object create(@RequestBody byte[] raw,HttpServletRequest request) {
    var in=input(raw,request,"ouf.semantic.discovery","COMMAND",Set.of("requestedArtifactType","intent","preferredLanguages","idempotencyKey"));
    var a=in.arguments();var langs=a.required("preferredLanguages");
    if(!langs.isArray()||langs.size()>5)throw invalid();
    var languages=new ArrayList<String>();
    for(var language:langs){if(!language.isTextual())throw invalid();languages.add(language.textValue());}
    return jobs.request(text(a,"requestedArtifactType"),text(a,"intent"),languages,in.actor(),text(a,"idempotencyKey"));
  }
  @PostMapping("/status") public Object status(@RequestBody byte[] raw,HttpServletRequest request) {
    var in=input(raw,request,"ouf.semantic.discovery.status","READ",Set.of("requestId"));
    return jobs.status(id(in.arguments()),in.actor());
  }
  @PostMapping("/candidates") public Object candidates(@RequestBody byte[] raw,HttpServletRequest request) {
    var in=input(raw,request,"ouf.semantic.discovery.candidates","READ",Set.of("requestId"));
    return jobs.candidates(id(in.arguments()),in.actor());
  }
  private static UUID id(JsonNode a){String value=text(a,"requestId");if(!value.matches("[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"))throw invalid();return UUID.fromString(value);}
  private static String text(JsonNode a,String key){if(!a.hasNonNull(key)||!a.get(key).isTextual())throw invalid();return a.get(key).textValue();}
  private static IllegalArgumentException invalid(){return new IllegalArgumentException("SEM_DISCOVERY_ARGUMENTS_INVALID");}
  @ExceptionHandler(SecurityException.class) ResponseEntity<?> denied(){return ResponseEntity.status(403).body(Map.of("code","SEM_DISCOVERY_RECEIPT_OR_POLICY_DENIED"));}
}
