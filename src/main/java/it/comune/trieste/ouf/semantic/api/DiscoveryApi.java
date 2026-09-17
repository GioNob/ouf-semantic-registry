package it.comune.trieste.ouf.semantic.api;

import it.comune.trieste.ouf.semantic.application.DiscoveryService;
import it.comune.trieste.ouf.semantic.adapters.discovery.SchemaGovProvider;
import java.util.*;
import org.springframework.web.bind.annotation.*;
import jakarta.servlet.http.HttpServletRequest;

@RestController @RequestMapping("/api/semantic/v1/discovery-requests")
public class DiscoveryApi {
  private final DiscoveryService service;private final SchemaGovProvider schemaGov;private final TrustedActorResolver actors;public DiscoveryApi(DiscoveryService service,SchemaGovProvider schemaGov,TrustedActorResolver actors){this.service=service;this.schemaGov=schemaGov;this.actors=actors;}
  public record Request(String requestedArtifactType,String intent,List<String> preferredLanguages){}
  public record Adoption(String semanticId,String namespace,String localName,String ownerRef,String authorityRef){}
  @SemanticCapability("ouf.semantic.discovery") @PostMapping Map<String,Object> create(@RequestBody Request r,HttpServletRequest request){UUID id=service.request(r.requestedArtifactType(),r.intent(),r.preferredLanguages()==null?List.of():r.preferredLanguages(),actors.actor(request).subject());return Map.of("requestId",id,"state","PENDING");}
  @SemanticCapability("ouf.semantic.read") @GetMapping("/{id}/candidates") List<Map<String,Object>> candidates(@PathVariable UUID id){return service.candidates(id);}
  @SemanticCapability("ouf.semantic.propose") @PostMapping("/{requestId}/candidates/{candidateId}:adopt") Map<String,Object> adopt(@PathVariable UUID requestId,@PathVariable UUID candidateId,@RequestBody Adoption r,HttpServletRequest request){UUID artifact=service.adopt(candidateId,r.semanticId(),r.namespace(),r.localName(),r.ownerRef(),r.authorityRef(),actors.actor(request).subject());return Map.of("artifactId",artifact,"status","DRAFT");}
  @SemanticCapability("ouf.semantic.read") @GetMapping("/providers") Map<String,Object> providers(){return Map.of("providers",List.of(schemaGov.status()));}
}
