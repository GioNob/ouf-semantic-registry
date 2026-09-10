package it.comune.trieste.ouf.semantic.adapters.discovery;

import com.fasterxml.jackson.databind.*;
import it.comune.trieste.ouf.semantic.ports.SemanticDiscoveryProvider;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@EnableConfigurationProperties(SchemaGovProperties.class)
public class SchemaGovProvider implements SemanticDiscoveryProvider {
  private static final Set<String> JSON=Set.of("application/json","application/sparql-results+json");
  private static final Set<String> RDF=Set.of("text/turtle","application/ld+json","application/rdf+xml");
  private final SchemaGovProperties cfg;private final BoundedGatewayClient client;private final ObjectMapper json;private final Clock clock;
  private final AtomicInteger consecutiveFailures=new AtomicInteger();private final AtomicReference<Instant> openUntil=new AtomicReference<>();
  @Autowired
  public SchemaGovProvider(SchemaGovProperties cfg,ObjectMapper json){this(cfg,new BoundedGatewayClient(cfg.connectTimeout()),json,Clock.systemUTC());}
  SchemaGovProvider(SchemaGovProperties cfg,BoundedGatewayClient client,ObjectMapper json,Clock clock){this.cfg=cfg;this.client=client;this.json=json;this.clock=clock;}
  public String providerId(){return "SCHEMA_GOV_IT";}
  public List<Candidate> search(Query q){
    if(!cfg.enabled())return List.of();
    Instant blockedUntil=openUntil.get();if(blockedUntil!=null&&clock.instant().isBefore(blockedUntil))throw new BoundedGatewayClient.ProviderFailure("SCHEMA_GOV_CIRCUIT_OPEN");
    URI endpoint=underGateway(cfg.searchPath());String sparql=query(q);
    try{JsonNode root=json.readTree(withRetry(()->client.postForm(cfg.gatewayBaseUrl(),endpoint,"query="+enc(sparql)+"&format="+enc("application/sparql-results+json"),cfg.requestTimeout(),cfg.maxResponseBytes(),JSON)).body());JsonNode rows=root.path("results").path("bindings");if(!rows.isArray())throw new BoundedGatewayClient.ProviderFailure("SCHEMA_GOV_SPARQL_RESULT_INVALID");List<Candidate> out=new ArrayList<>();Set<String> seen=new HashSet<>();for(JsonNode n:rows){if(out.size()>=cfg.maxCandidates())break;String canonical=binding(n,"resource");if(canonical==null||!seen.add(canonical))continue;URI fetch=underGateway(cfg.fetchPath()+"?uri="+enc(canonical));var body=withRetry(()->client.get(cfg.gatewayBaseUrl(),fetch,cfg.requestTimeout(),cfg.maxResponseBytes(),RDF));String label=binding(n,"label");String language=n.path("label").path("xml:lang").asText(null);List<String> reasons=label==null?List.of("schema.gov.it SPARQL match"):List.of("label: "+label+(language==null?"":" ["+language+"]"));out.add(new Candidate(canonical,canonical,q.artifactType(),"HIGH",.85,reasons,List.of(),body.body(),body.mediaType()));}consecutiveFailures.set(0);openUntil.set(null);return List.copyOf(out);}catch(BoundedGatewayClient.ProviderFailure e){recordFailure();throw e;}catch(Exception e){recordFailure();throw new BoundedGatewayClient.ProviderFailure("SCHEMA_GOV_SPARQL_RESULT_INVALID",e);}
  }
  static String query(Query q){String pattern=switch(q.artifactType()){case "CLASS"->"?resource a owl:Class .";case "PROPERTY"->"VALUES ?kind { owl:ObjectProperty owl:DatatypeProperty } ?resource a ?kind .";case "RELATIONSHIP"->"?resource a owl:ObjectProperty .";case "CONCEPT"->"?resource a skos:Concept .";case "VOCABULARY"->"?resource a skos:ConceptScheme .";case "ONTOLOGY"->"?resource a owl:Ontology .";default->throw new IllegalArgumentException("unsupported artifact type");};String literal=q.intent().replace("\\","\\\\").replace("\"","\\\"").replace("\n"," ").replace("\r"," ");return "PREFIX owl: <http://www.w3.org/2002/07/owl#>\nPREFIX skos: <http://www.w3.org/2004/02/skos/core#>\nPREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\nSELECT DISTINCT ?resource ?label WHERE { "+pattern+" OPTIONAL { ?resource rdfs:label|skos:prefLabel ?label } FILTER(CONTAINS(LCASE(STR(COALESCE(?label,?resource))),LCASE(\""+literal+"\"))) } ORDER BY ?resource LIMIT 50";}
  public ProviderStatus status(){Instant until=openUntil.get();return new ProviderStatus(providerId(),cfg.enabled(),until!=null&&clock.instant().isBefore(until),consecutiveFailures.get(),until);}
  private BoundedGatewayClient.Response withRetry(java.util.function.Supplier<BoundedGatewayClient.Response> call){BoundedGatewayClient.ProviderFailure last=null;for(int attempt=1;attempt<=Math.max(1,cfg.maxAttempts());attempt++){try{return call.get();}catch(BoundedGatewayClient.ProviderFailure e){last=e;if(!retryable(e)||attempt>=cfg.maxAttempts())break;try{Thread.sleep(Math.max(0,cfg.retryBackoff().toMillis()));}catch(InterruptedException interrupted){Thread.currentThread().interrupt();throw new BoundedGatewayClient.ProviderFailure("PROVIDER_INTERRUPTED",interrupted);}}}throw last;}
  private boolean retryable(BoundedGatewayClient.ProviderFailure e){return e.getMessage().equals("PROVIDER_UNAVAILABLE")||e.getMessage().equals("PROVIDER_HTTP_429")||e.getMessage().startsWith("PROVIDER_HTTP_5");}
  private void recordFailure(){if(consecutiveFailures.incrementAndGet()>=Math.max(1,cfg.circuitFailureThreshold()))openUntil.set(clock.instant().plus(cfg.circuitOpenDuration()));}
  public record ProviderStatus(String providerId,boolean enabled,boolean circuitOpen,int consecutiveFailures,Instant openUntil){}
  private URI underGateway(String path){URI u=cfg.gatewayBaseUrl().resolve(path);BoundedGatewayClient.requireSameOrigin(cfg.gatewayBaseUrl(),u);return u;}
  private static String enc(String v){return URLEncoder.encode(v,StandardCharsets.UTF_8);}
  private static String binding(JsonNode n,String name){String v=n.path(name).path("value").asText(null);return v==null||v.isBlank()?null:v;}
}
