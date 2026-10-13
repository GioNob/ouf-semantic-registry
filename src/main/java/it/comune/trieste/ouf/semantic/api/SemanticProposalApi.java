package it.comune.trieste.ouf.semantic.api;

import com.fasterxml.jackson.databind.*;
import it.comune.trieste.ouf.authorization.*;
import it.comune.trieste.ouf.semantic.application.NativeProposalService;
import jakarta.servlet.http.HttpServletRequest;
import java.util.*;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/** Gateway receipt plus fresh local owner policy; no THS decisions here. */
@RestController
@RequestMapping("/api/internal/v1/semantic/proposals")
public class SemanticProposalApi {
  private final SemanticProposalDelegation receipts;
  private final NativeProposalService service;
  private final ObjectMapper json;
  public SemanticProposalApi(SemanticProposalDelegation receipts,NativeProposalService service,ObjectMapper json) {
    this.receipts=receipts;this.service=service;
    this.json=json.copy().enable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)
      .enable(com.fasterxml.jackson.core.JsonParser.Feature.STRICT_DUPLICATE_DETECTION);
  }
  public record Create(String proposalKey,List<ArtifactApi.CreateArtifact> commands){}
  private record Call(JsonNode args,PrincipalContext principal,String correlation){}
  private Call authorize(byte[] raw,HttpServletRequest request,String capability,String operation,Set<String> fields) {
    var principal=receipts.verify(request.getHeader("X-OUF-Semantic-Proposal-Receipt"),request.getRequestURI(),capability,raw);
    request.setAttribute(ServletAuthorization.TRUSTED_PRINCIPAL,new TrustedPrincipal(principal));
    String permission="ouf.semantic.proposal.read".equals(capability)?"ouf.semantic.propose":capability;
    OwnerAuthorization.bind(request).require(permission,new ResourceContext("semantic.artifact",null,principal.tenantId(),null,Map.of("module","SEMANTIC")));
    try {
      var e=json.readTree(raw);var a=e.required("Arguments");
      if(!e.required("CapabilityID").asText().equals(capability)||!e.required("GatewayBindingRef").asText().equals("capability://"+capability)
          ||!e.required("Owner").asText().equals("semantic")||!e.required("OperationClass").asText().equals(operation)||!a.isObject())throw new IllegalArgumentException();
      for(var it=a.fieldNames();it.hasNext();)if(!fields.contains(it.next()))throw new IllegalArgumentException();
      String key=text(a,"proposalKey");if(!key.matches("[A-Za-z0-9][A-Za-z0-9._:-]{0,127}"))throw new IllegalArgumentException();
      if(!e.required("Identity").required("PrincipalID").asText().equals(principal.subjectId())
          ||!e.required("Identity").required("TenantID").asText().equals(principal.tenantId()))throw new IllegalArgumentException();
      return new Call(a,principal,text(e,"CorrelationID"));
    }catch(Exception e){throw new IllegalArgumentException("SEM_PROPOSAL_ARGUMENTS_INVALID");}
  }
  @PostMapping("/create") public Object create(@RequestBody byte[] raw,HttpServletRequest request) {
    var c=authorize(raw,request,"ouf.semantic.propose","COMMAND",Set.of("proposalKey","commands"));
    final Create input;try{input=json.treeToValue(c.args(),Create.class);}catch(Exception e){throw new IllegalArgumentException("SEM_NATIVE_COMMAND_INVALID");}
    return service.create(c.principal().tenantId(),c.principal().subjectId(),c.principal().actorType().name(),input.proposalKey(),input.commands(),c.correlation());
  }
  @PostMapping("/validate") public Object validate(@RequestBody byte[] raw,HttpServletRequest request) {
    var c=authorize(raw,request,"ouf.semantic.review.prepare","COMMAND",Set.of("proposalKey","expectedVersion"));
    return service.validate(c.principal().tenantId(),c.principal().subjectId(),text(c.args(),"proposalKey"),version(c.args()));
  }
  @PostMapping("/request") public Object review(@RequestBody byte[] raw,HttpServletRequest request) {
    var c=authorize(raw,request,"ouf.semantic.approval.request","COMMAND",Set.of("proposalKey","expectedVersion"));
    return service.requestReview(c.principal().tenantId(),c.principal().subjectId(),c.principal().actorType().name(),text(c.args(),"proposalKey"),version(c.args()),c.correlation());
  }
  @PostMapping("/read") public Object read(@RequestBody byte[] raw,HttpServletRequest request) {
    var c=authorize(raw,request,"ouf.semantic.proposal.read","READ",Set.of("proposalKey"));
    return service.read(c.principal().tenantId(),c.principal().subjectId(),text(c.args(),"proposalKey"));
  }
  private static String text(JsonNode n,String key){if(!n.hasNonNull(key)||!n.get(key).isTextual()||n.get(key).asText().isBlank())throw new IllegalArgumentException("SEM_PROPOSAL_ARGUMENTS_INVALID");return n.get(key).textValue();}
  private static long version(JsonNode a){var v=a.get("expectedVersion");if(v==null||!v.isIntegralNumber()||!v.canConvertToLong()||v.longValue()<0)throw new IllegalArgumentException("SEM_PROPOSAL_VERSION_INVALID");return v.longValue();}
  @ExceptionHandler(SecurityException.class) ResponseEntity<?> denied(){return ResponseEntity.status(403).body(Map.of("code","SEM_PROPOSAL_RECEIPT_OR_POLICY_DENIED"));}
}
