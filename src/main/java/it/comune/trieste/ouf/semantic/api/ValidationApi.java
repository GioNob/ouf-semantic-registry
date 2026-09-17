package it.comune.trieste.ouf.semantic.api;

import it.comune.trieste.ouf.semantic.application.ValidationService;
import java.util.*;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import jakarta.servlet.http.HttpServletRequest;

@RestController @RequestMapping("/api/semantic/v1")
public class ValidationApi {
  private final ValidationService service;private final TrustedActorResolver actors;public ValidationApi(ValidationService service,TrustedActorResolver actors){this.service=service;this.actors=actors;}
  public record ImpactRequest(UUID fromRevisionId,UUID toRevisionId){}
  public record ConsumerReference(String consumerType,String consumerId,String semanticId,UUID revisionId,UUID publicationSetId){}
  @SemanticCapability("ouf.semantic.propose") @PostMapping("/revisions/{id}:validate") Map<String,Object> validate(@PathVariable UUID id,HttpServletRequest request){return service.validate(id,actors.actor(request).subject());}
  @SemanticCapability("ouf.semantic.read") @GetMapping("/validation-runs/{id}") Map<String,Object> validation(@PathVariable UUID id){return service.validation(id);}
  @SemanticCapability("ouf.semantic.propose") @PostMapping("/impact-reports") Map<String,Object> impact(@RequestBody ImpactRequest r,HttpServletRequest request){return service.impact(r.fromRevisionId(),r.toRevisionId(),actors.actor(request).subject());}
  @SemanticCapability("ouf.semantic.read") @GetMapping("/impact-reports/{id}") Map<String,Object> impact(@PathVariable UUID id){return service.impact(id);}
  @SemanticCapability("ouf.semantic.read") @GetMapping("/references:resolve") Map<String,Object> resolve(@RequestParam String semanticId,@RequestParam UUID revisionId,@RequestParam UUID publicationSetId){return service.resolve(semanticId,revisionId,publicationSetId);}
  @SemanticCapability("ouf.semantic.consumer-reference.write") @PutMapping("/consumer-references") ResponseEntity<Void> consumer(@RequestBody ConsumerReference r,HttpServletRequest request){var actor=actors.actor(request);actors.require(actor,"ouf.semantic.consumer-reference.write");service.registerConsumer(r.consumerType(),r.consumerId(),r.semanticId(),r.revisionId(),r.publicationSetId());return ResponseEntity.noContent().build();}
}
