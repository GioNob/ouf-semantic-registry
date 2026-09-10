package it.comune.trieste.ouf.semantic.api;

import it.comune.trieste.ouf.semantic.application.InterchangeService;
import java.util.*;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

@RestController @RequestMapping("/api/semantic/v1")
public class InterchangeApi {
  private final InterchangeService service;public InterchangeApi(InterchangeService service){this.service=service;}
  @PostMapping(value="/imports",consumes={"text/turtle","application/ld+json","application/rdf+xml","application/n-triples"})
  Map<String,Object> importRdf(@RequestParam String semanticId,@RequestParam String artifactType,@RequestParam String namespace,@RequestParam String localName,@RequestParam String ownerRef,@RequestParam String authorityRef,@RequestParam String semanticVersion,@RequestHeader(HttpHeaders.CONTENT_TYPE) String mediaType,@RequestHeader("X-OUF-Subject") String actor,@RequestBody byte[] body){return service.importDraft(semanticId,artifactType,namespace,localName,ownerRef,authorityRef,semanticVersion,baseType(mediaType),body,actor);}
  @GetMapping("/publication-sets/{setId}/artifacts/{artifactId}") ResponseEntity<byte[]> export(@PathVariable UUID setId,@PathVariable UUID artifactId,@RequestHeader(value=HttpHeaders.ACCEPT,defaultValue="application/ld+json") String accept){String selected=select(accept);var out=service.export(setId,artifactId,selected);return ResponseEntity.ok().contentType(MediaType.parseMediaType(out.mediaType())).body(out.body());}
  private static String baseType(String value){return value.split(";",2)[0].trim().toLowerCase(Locale.ROOT);}
  private static String select(String accept){if(accept.contains("*/*"))return "application/json";for(String candidate:List.of("application/json","application/ld+json","text/turtle","application/rdf+xml","application/n-triples","text/csv"))if(accept.contains(candidate))return candidate;throw new IllegalArgumentException("SEMANTIC_REPRESENTATION_NOT_ACCEPTABLE");}
}
