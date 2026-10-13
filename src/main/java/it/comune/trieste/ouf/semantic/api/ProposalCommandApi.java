package it.comune.trieste.ouf.semantic.api;

import it.comune.trieste.ouf.authorization.OwnerAuthorization;
import it.comune.trieste.ouf.semantic.application.ProposalCommandService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import java.util.*;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;

@RestController @RequestMapping("/api/semantic/v1/proposal-commands")
public class ProposalCommandApi {
  private final ProposalCommandService service;
  private final TrustedActorResolver actors;
  public ProposalCommandApi(ProposalCommandService service,TrustedActorResolver actors){this.service=service;this.actors=actors;}
  public record Validate(@NotNull UUID revisionId,@NotNull @Min(0) Long expectedRowVersion){}
  public record Review(@NotNull UUID revisionId,@NotNull @Min(0) Long expectedRowVersion,@NotNull UUID validationRunId){}
  public record Read(@NotBlank @Pattern(regexp="[A-Za-z0-9_:.-]{1,128}") String commandKey){}
  @SemanticCapability("ouf.semantic.propose") @PostMapping("/create")
  public Map<String,Object> create(@Valid @RequestBody ArtifactApi.CreateArtifact body,
      @RequestHeader("Idempotency-Key") String key,HttpServletRequest request,@RequestHeader HttpHeaders headers){
    var actor=actors.actor(request);
    return service.create(tenant(request),actor.subject(),actor.type(),key,body,correlation(headers));
  }
  @SemanticCapability("ouf.semantic.review.prepare") @PostMapping("/validate")
  public Map<String,Object> validate(@Valid @RequestBody Validate body,
      @RequestHeader("Idempotency-Key") String key,HttpServletRequest request){
    var actor=actors.actor(request);
    return service.validate(tenant(request),actor.subject(),key,body.revisionId(),body.expectedRowVersion());
  }
  @SemanticCapability("ouf.semantic.approval.request") @PostMapping("/review")
  public Map<String,Object> review(@Valid @RequestBody Review body,
      @RequestHeader("Idempotency-Key") String key,HttpServletRequest request,@RequestHeader HttpHeaders headers){
    var actor=actors.actor(request);actors.require(actor,"ouf.semantic.review.prepare");
    return service.review(tenant(request),actor.subject(),actor.type(),key,body.revisionId(),
        body.expectedRowVersion(),body.validationRunId(),correlation(headers));
  }
  @SemanticCapability("ouf.semantic.read") @PostMapping("/read")
  public Map<String,Object> read(@Valid @RequestBody Read body,HttpServletRequest request){
    var actor=actors.actor(request);var result=service.receipt(tenant(request),actor.subject(),body.commandKey());
    String op=String.valueOf(result.get("operation"));
    actors.require(actor,switch(op){case "VALIDATE"->"ouf.semantic.review.prepare";case "REVIEW"->"ouf.semantic.approval.request";default->"ouf.semantic.propose";});
    return result;
  }
  private static String tenant(HttpServletRequest request){return OwnerAuthorization.bind(request).principal().tenantId();}
  private static String correlation(HttpHeaders h){return Optional.ofNullable(h.getFirst("X-Correlation-ID")).filter(x->!x.isBlank()).orElseGet(()->UUID.randomUUID().toString());}
}
