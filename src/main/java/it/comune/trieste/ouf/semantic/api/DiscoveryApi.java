package it.comune.trieste.ouf.semantic.api;

import it.comune.trieste.ouf.semantic.application.DiscoveryService;
import it.comune.trieste.ouf.semantic.adapters.discovery.SchemaGovProvider;
import java.util.*;
import org.springframework.web.bind.annotation.*;

@RestController @RequestMapping("/api/semantic/v1/discovery-requests")
public class DiscoveryApi {
  private final DiscoveryService service;private final SchemaGovProvider schemaGov;public DiscoveryApi(DiscoveryService service,SchemaGovProvider schemaGov){this.service=service;this.schemaGov=schemaGov;}
  public record Request(String requestedArtifactType,String intent,List<String> preferredLanguages){}
  public record Adoption(String semanticId,String namespace,String localName,String ownerRef,String authorityRef){}
  @PostMapping Map<String,Object> create(@RequestBody Request r,@RequestHeader("X-OUF-Subject") String actor){UUID id=service.request(r.requestedArtifactType(),r.intent(),r.preferredLanguages()==null?List.of():r.preferredLanguages(),actor);return Map.of("requestId",id,"state","PENDING");}
  @GetMapping("/{id}/candidates") List<Map<String,Object>> candidates(@PathVariable UUID id){return service.candidates(id);}
  @PostMapping("/{requestId}/candidates/{candidateId}:adopt") Map<String,Object> adopt(@PathVariable UUID requestId,@PathVariable UUID candidateId,@RequestBody Adoption r,@RequestHeader("X-OUF-Subject") String actor){UUID artifact=service.adopt(candidateId,r.semanticId(),r.namespace(),r.localName(),r.ownerRef(),r.authorityRef(),actor);return Map.of("artifactId",artifact,"status","DRAFT");}
  @GetMapping("/providers") Map<String,Object> providers(){return Map.of("providers",List.of(schemaGov.status()));}
}
