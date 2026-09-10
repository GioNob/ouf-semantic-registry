package it.comune.trieste.ouf.semantic.api;

import it.comune.trieste.ouf.semantic.application.ValidationService;
import java.util.*;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController @RequestMapping("/api/semantic/v1")
public class ValidationApi {
  private final ValidationService service;public ValidationApi(ValidationService service){this.service=service;}
  public record ImpactRequest(UUID fromRevisionId,UUID toRevisionId){}
  public record ConsumerReference(String consumerType,String consumerId,String semanticId,UUID revisionId,UUID publicationSetId){}
  @PostMapping("/revisions/{id}:validate") Map<String,Object> validate(@PathVariable UUID id,@RequestHeader("X-OUF-Subject") String actor){return service.validate(id,actor);}
  @GetMapping("/validation-runs/{id}") Map<String,Object> validation(@PathVariable UUID id){return service.validation(id);}
  @PostMapping("/impact-reports") Map<String,Object> impact(@RequestBody ImpactRequest r,@RequestHeader("X-OUF-Subject") String actor){return service.impact(r.fromRevisionId(),r.toRevisionId(),actor);}
  @GetMapping("/impact-reports/{id}") Map<String,Object> impact(@PathVariable UUID id){return service.impact(id);}
  @GetMapping("/references:resolve") Map<String,Object> resolve(@RequestParam String semanticId,@RequestParam UUID revisionId,@RequestParam UUID publicationSetId){return service.resolve(semanticId,revisionId,publicationSetId);}
  @PutMapping("/consumer-references") ResponseEntity<Void> consumer(@RequestBody ConsumerReference r){service.registerConsumer(r.consumerType(),r.consumerId(),r.semanticId(),r.revisionId(),r.publicationSetId());return ResponseEntity.noContent().build();}
}
