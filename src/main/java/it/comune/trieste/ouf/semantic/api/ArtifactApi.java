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

@RestController
@RequestMapping("/api/semantic/v1")
public class ArtifactApi {
  private final ArtifactService service;
  public ArtifactApi(ArtifactService service) { this.service = service; }

  public record CreateArtifact(@NotBlank String semanticId,
      @Pattern(regexp="CLASS|PROPERTY|RELATIONSHIP|VOCABULARY|CONCEPT|ONTOLOGY") String artifactType,
      @NotBlank String namespace, @NotBlank String localName, @NotBlank String ownerRef,
      @NotBlank String authorityRef, Map<String,Object> labels, Map<String,Object> definition) {}
  public record PatchRevision(Map<String,Object> labels, Map<String,Object> definition) {}

  @PostMapping("/artifacts")
  ResponseEntity<Map<String,Object>> create(@Valid @RequestBody CreateArtifact command) {
    var result=service.create(command);
    return ResponseEntity.created(URI.create("/api/semantic/v1/artifacts/"+result.get("artifactId"))).eTag(result.get("etag").toString()).body(result);
  }
  @GetMapping("/artifacts/{id}") Map<String,Object> get(@PathVariable UUID id) { return service.get(id); }
  @GetMapping("/search") List<Map<String,Object>> search(@RequestParam String q,@RequestParam(defaultValue="ACTIVE") String status,@RequestParam(defaultValue="20") int limit) { return service.search(q,status,limit); }
  @PatchMapping("/revisions/{id}") ResponseEntity<Map<String,Object>> patch(@PathVariable UUID id,@RequestHeader("If-Match") String etag,@Valid @RequestBody PatchRevision patch) {
    var result=service.patch(id,etag,patch); return ResponseEntity.ok().eTag(result.get("etag").toString()).body(result);
  }
}
