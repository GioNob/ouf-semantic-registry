package it.comune.trieste.ouf.semantic.api;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.databind.JsonNode;
import it.comune.trieste.ouf.authorization.OwnerAuthorization;
import it.comune.trieste.ouf.semantic.application.ProposalCommandService;
import it.comune.trieste.ouf.semantic.application.ProposalObservation;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;

@RestController @RequestMapping("/api/semantic/v1/proposal-commands")
public class ProposalCommandApi {
  private final ProposalCommandService service;
  private final TrustedActorResolver actors;
  private final ProposalObservation observations;
  public ProposalCommandApi(ProposalCommandService service,TrustedActorResolver actors,ProposalObservation observations){
    this.service=service;this.actors=actors;this.observations=observations;
  }
  public record Create(@NotBlank String semanticId,
      @NotNull @Pattern(regexp="CLASS|PROPERTY|RELATIONSHIP|VOCABULARY|CONCEPT|ONTOLOGY|DATATYPE|VALUE_MAP") String artifactType,
      @NotBlank String namespace,@NotBlank String localName,@NotBlank String ownerRef,
      @NotBlank String authorityRef,@NotBlank String semanticVersion,Map<String,Object> labels,
      Object definition,@Size(max=49152) String rdfTurtle,String mediaType,JsonNode rationale) {
    @SuppressWarnings("unchecked")
    public ArtifactApi.CreateArtifact artifact(){
      if ("VALUE_MAP".equals(artifactType)) {
        if (!(definition instanceof Map<?,?>) || rdfTurtle!=null || mediaType!=null)
          throw new IllegalArgumentException("SEMANTIC_VALUE_MAP_INVALID");
      } else if (definition!=null && !(definition instanceof Map<?,?>)) {
        throw new IllegalArgumentException("SEM_REQUEST_INVALID");
      }
      return new ArtifactApi.CreateArtifact(semanticId,artifactType,namespace,localName,ownerRef,authorityRef,
          semanticVersion,labels,(Map<String,Object>)definition);
    }
    SourceColumn sourceColumn(){
      if(rationale==null) return null;
      if(!"VALUE_MAP".equals(artifactType)) throw new IllegalArgumentException("SEM_REQUEST_INVALID");
      if(!rationale.isObject()) throw invalidValueMap();
      if(rationale.isEmpty()) return null;
      JsonNode column=rationale.get("sourceColumn");
      if(rationale.size()!=1 || column==null || !column.isObject()) throw invalidValueMap();
      String fieldName=column.path("fieldName").textValue();
      JsonNode source=column.get("sourceId");
      if(!validText(fieldName) || fieldName.isEmpty() || fieldName.codePointCount(0,fieldName.length())>256
          || column.size()!=(source==null?1:2) || (source!=null && !validText(source.textValue())))
        throw invalidValueMap();
      return new SourceColumn(fieldName,source==null?null:source.textValue());
    }
    private static boolean validText(String value){
      return value!=null && value.indexOf(0)<0 && StandardCharsets.UTF_8.newEncoder().canEncode(value);
    }
    private static IllegalArgumentException invalidValueMap(){
      return new IllegalArgumentException("SEMANTIC_VALUE_MAP_INVALID");
    }
  }
  @JsonInclude(JsonInclude.Include.NON_NULL)
  public record SourceColumn(String fieldName,String sourceId){}
  public record Adopt(@NotNull UUID requestId,@NotNull UUID candidateId){}
  @SemanticCapability("ouf.semantic.discovery.adopt") @PostMapping("/adopt")
  public Map<String,Object> adopt(@Valid @RequestBody Adopt body,
      @RequestHeader("Idempotency-Key") String key,HttpServletRequest request){
    if(!(request.getAttribute(SemanticProposalReceiptFilter.VERIFIED) instanceof SemanticProposalReceiptVerifier.Verified))
      throw new it.comune.trieste.ouf.semantic.application.GovernanceService.Forbidden("SEM_PROPOSAL_RECEIPT_INVALID");
    return service.adopt(OwnerAuthorization.bind(request).principal(),key,body.requestId(),body.candidateId());
  }
  public record Validate(@NotNull UUID revisionId,@NotNull @Min(0) Long expectedRowVersion){}
  public record Review(@NotNull UUID revisionId,@NotNull @Min(0) Long expectedRowVersion,@NotNull UUID validationRunId){}
  public record Read(@NotBlank @Pattern(regexp="[A-Za-z0-9_:.-]{1,128}") String commandKey,
      @Pattern(regexp="[a-f0-9]{64}") String expectedVersion){}
  @SemanticCapability("ouf.semantic.propose") @PostMapping("/create")
  public Map<String,Object> create(@Valid @RequestBody Create body,
      @RequestHeader("Idempotency-Key") String key,HttpServletRequest request,@RequestHeader HttpHeaders headers){
    var actor=actors.actor(request);
    var artifact=body.artifact();
    var sourceColumn=body.sourceColumn();
    if(body.rdfTurtle()!=null||body.mediaType()!=null)
      return withObservation(service.createImported(tenant(request),actor.subject(),actor.type(),key,artifact,body.rdfTurtle(),body.mediaType(),correlation(headers)));
    return withObservation(service.create(tenant(request),actor.subject(),actor.type(),key,artifact,sourceColumn,correlation(headers)));
  }
  @SemanticCapability("ouf.semantic.review.prepare") @PostMapping("/validate")
  public Map<String,Object> validate(@Valid @RequestBody Validate body,
      @RequestHeader("Idempotency-Key") String key,HttpServletRequest request){
    var actor=actors.actor(request);
    return withObservation(service.validate(tenant(request),actor.subject(),key,body.revisionId(),body.expectedRowVersion()));
  }
  @SemanticCapability("ouf.semantic.approval.request") @PostMapping("/review")
  public Map<String,Object> review(@Valid @RequestBody Review body,
      @RequestHeader("Idempotency-Key") String key,HttpServletRequest request,@RequestHeader HttpHeaders headers){
    var actor=actors.actor(request);actors.require(actor,"ouf.semantic.review.prepare");
    var response=withObservation(service.review(tenant(request),actor.subject(),actor.type(),key,body.revisionId(),
        body.expectedRowVersion(),body.validationRunId(),correlation(headers)));
    response.put("expiresAt",response.get("expires_at"));
    return response;
  }
  @SemanticCapability("ouf.semantic.proposal.read") @PostMapping("/read")
  public Map<String,Object> read(@Valid @RequestBody Read body,HttpServletRequest request){
    var actor=actors.actor(request);
    if(!"HUMAN".equals(actor.type()))throw new it.comune.trieste.ouf.semantic.application.GovernanceService.Forbidden("SEM_HUMAN_REQUIRED");
    String tenant=tenant(request);
    var receipt=service.receiptIdentity(tenant,actor.subject(),body.commandKey());
    actors.require(actor,switch(receipt.operation()){case "ADOPT"->"ouf.semantic.discovery.adopt";case "VALIDATE"->"ouf.semantic.review.prepare";case "REVIEW"->"ouf.semantic.approval.request";default->"ouf.semantic.propose";});
    var current=observations.current(receipt.revisionId());
    if(current.get("version").equals(body.expectedVersion())) {
      var unchanged=new LinkedHashMap<String,Object>();
      for(String field:List.of("version","state","allowedActions","pollAfterSeconds"))
        if(current.containsKey(field))unchanged.put(field,current.get(field));
      unchanged.put("changed",false);
      return unchanged;
    }
    var result=new LinkedHashMap<>(service.receipt(tenant,actor.subject(),body.commandKey()));
    result.putAll(current);
    result.put("changed",true);
    return result;
  }
  private Map<String,Object> withObservation(Map<String,Object> receipt) {
    var revision=ProposalCommandService.receiptRevision(receipt.getOrDefault("revisionId",receipt.get("revision_id")));
    var result=new LinkedHashMap<>(receipt);
    result.putAll(observations.current(revision));
    return result;
  }
  private static String tenant(HttpServletRequest request){return OwnerAuthorization.bind(request).principal().tenantId();}
  private static String correlation(HttpHeaders h){return Optional.ofNullable(h.getFirst("X-Correlation-ID")).filter(x->!x.isBlank()).orElseGet(()->UUID.randomUUID().toString());}
}
