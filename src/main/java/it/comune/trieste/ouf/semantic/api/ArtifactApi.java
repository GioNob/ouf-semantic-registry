package it.comune.trieste.ouf.semantic.api;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import java.net.URI;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import it.comune.trieste.ouf.semantic.application.ArtifactService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpHeaders;

@RestController
@RequestMapping("/api/semantic/v1")
public class ArtifactApi {
  private final ArtifactService service;private final TrustedActorResolver actors;
  public ArtifactApi(ArtifactService service,TrustedActorResolver actors) { this.service = service;this.actors=actors; }

  public record CreateArtifact(@NotBlank String semanticId,
      @Pattern(regexp="CLASS|PROPERTY|RELATIONSHIP|VOCABULARY|CONCEPT|ONTOLOGY") String artifactType,
      @NotBlank String namespace, @NotBlank String localName, @NotBlank String ownerRef,
      @NotBlank String authorityRef, @NotBlank String semanticVersion,
      Map<String,Object> labels, Map<String,Object> definition) {}
  public record PatchRevision(Map<String,Object> labels, Map<String,Object> definition) {}

  @SemanticCapability("ouf.semantic.propose") @PostMapping("/artifacts")
  ResponseEntity<Map<String,Object>> create(@Valid @RequestBody CreateArtifact command,HttpServletRequest request,@RequestHeader HttpHeaders headers) {
    var actor=actors.actor(request);var result=service.create(command,actor.subject(),actor.type(),correlation(headers));
    return ResponseEntity.created(URI.create("/api/semantic/v1/artifacts/"+result.get("artifactId"))).eTag(result.get("etag").toString()).body(result);
  }
  @SemanticCapability("ouf.semantic.read") @GetMapping("/artifacts/{id}") Map<String,Object> get(@PathVariable UUID id,HttpServletRequest request) {var result=service.get(id);if(!"ACTIVE".equals(result.get("status")))requireDraftRead(request);return result;}
  @SemanticCapability("ouf.semantic.search") @GetMapping("/search") List<Map<String,Object>> search(@RequestParam String q,@RequestParam(defaultValue="ACTIVE") String status,@RequestParam(defaultValue="20") int limit,HttpServletRequest request) {if(!"ACTIVE".equals(status))requireDraftRead(request);return service.search(q,status,limit);}
  @SemanticCapability("ouf.semantic.propose") @PatchMapping("/revisions/{id}") ResponseEntity<Map<String,Object>> patch(@PathVariable UUID id,@RequestHeader("If-Match") String etag,@Valid @RequestBody PatchRevision patch,HttpServletRequest request,@RequestHeader HttpHeaders headers) {
    var actor=actors.actor(request);var result=service.patch(id,etag,patch,actor.subject(),actor.type(),correlation(headers)); return ResponseEntity.ok().eTag(result.get("etag").toString()).body(result);
  }
  private void requireDraftRead(HttpServletRequest request){var actor=actors.actor(request);if(!actor.capabilities().contains("ouf.semantic.propose")&&!actor.capabilities().contains("ouf.semantic.review"))throw new it.comune.trieste.ouf.semantic.application.GovernanceService.Forbidden("SEM_DRAFT_READ_REQUIRED");}
  private static String correlation(HttpHeaders h){return java.util.Optional.ofNullable(h.getFirst("X-Correlation-Id")).filter(x->!x.isBlank()).orElseGet(()->UUID.randomUUID().toString());}
}
