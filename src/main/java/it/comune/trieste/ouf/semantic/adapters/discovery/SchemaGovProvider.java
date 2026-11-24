package it.comune.trieste.ouf.semantic.adapters.discovery;

import com.fasterxml.jackson.databind.*;
import it.comune.trieste.ouf.semantic.domain.SafeRdfParser;
import it.comune.trieste.ouf.semantic.ports.SemanticDiscoveryProvider;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@EnableConfigurationProperties({SchemaGovProperties.class,GatewayOAuthProperties.class})
public class SchemaGovProvider implements SemanticDiscoveryProvider {
  private static final Set<String> JSON=Set.of("application/json","application/sparql-results+json");
  private static final Set<String> RDF=Set.of("text/turtle","application/ld+json","application/rdf+xml");
  // During a required GET these statuses can describe the supplied resource or URI.
  private static final Set<String> RESOURCE_DENIALS=Set.of("PROVIDER_HTTP_400","PROVIDER_HTTP_404",
      "PROVIDER_HTTP_406","PROVIDER_HTTP_409","PROVIDER_HTTP_410","PROVIDER_HTTP_414","PROVIDER_HTTP_422","PROVIDER_HTTP_451");
  // A denied URI does not use a candidate slot; total fetch attempts stay bounded.
  private static final int MAX_ATTEMPT_FACTOR=3;
  private final SchemaGovProperties cfg;private final BoundedGatewayClient client;private final ObjectMapper json;private final Clock clock;
  @Autowired
  public SchemaGovProvider(SchemaGovProperties cfg,ObjectMapper json,GatewayOAuthProperties auth){this(cfg,new BoundedGatewayClient(cfg.connectTimeout(),new ClientCredentialsTokenSource(auth,json)),json,Clock.systemUTC());}
  // Existing package-local HTTP fixtures cannot become a production anonymous provider.
  SchemaGovProvider(SchemaGovProperties cfg,ObjectMapper json){this(cfg,fixtureClient(cfg),json,Clock.systemUTC());}
  private static BoundedGatewayClient fixtureClient(SchemaGovProperties cfg){
    URI base=cfg.gatewayBaseUrl();
    if(base==null || !Set.of("127.0.0.1","localhost").contains(base.getHost()))throw new BoundedGatewayClient.ProviderFailure("GATEWAY_AUTH_REQUIRED");
    return new BoundedGatewayClient(cfg.connectTimeout());
  }
  SchemaGovProvider(SchemaGovProperties cfg,BoundedGatewayClient client,ObjectMapper json,Clock clock){this.cfg=cfg;this.client=client;this.json=json;this.clock=clock;}
  public String providerId(){return "SCHEMA_GOV_IT";}
  @Override public boolean enabled(){return cfg.enabled();}
  public List<Candidate> search(Query q){
    return searchWithExclusions(q).candidates();
  }
  @Override public SearchResult searchWithExclusions(Query q){
    if(!cfg.enabled())return new SearchResult(List.of(),0);
    URI endpoint=underGateway(cfg.searchPath());
    String form="query="+enc(query(q))+"&format="+enc("application/sparql-results+json");
    var response=client.postForm(cfg.gatewayBaseUrl(),endpoint,form,timeout(q.deadline()),cfg.maxResponseBytes(),JSON);
    JsonNode root;
    try {root=json.readTree(response.body());}
    catch(java.io.IOException e){throw new BoundedGatewayClient.ProviderFailure("SCHEMA_GOV_SPARQL_RESULT_INVALID",e);}
    if(root==null || !root.path("results").path("bindings").isArray())
      throw new BoundedGatewayClient.ProviderFailure("SCHEMA_GOV_SPARQL_RESULT_INVALID");
    JsonNode rows=root.path("results").path("bindings");
    // Fetch required descriptions first so optional metadata cannot starve a later candidate.
    record Fetched(SchemaGovRanking.Match match,BoundedGatewayClient.Response body,OntologyProvenance.Description description){}
    var descriptions=new ArrayList<Fetched>();
    var evidence=new OntologyProvenance(Math.min(cfg.maxResponseBytes(),65536));
    var attempted=new HashSet<String>();
    int denied=0,invalid=0,bound=0;
    for(var match:SchemaGovRanking.rank(rows,q)){
      if(descriptions.size()>=cfg.maxCandidates() || attempted.size()>=cfg.maxCandidates()*MAX_ATTEMPT_FACTOR)break;
      String uri=match.uri();
      if(!attempted.add(uri))continue;
      try {
        var body=fetch(uri,q.deadline());
        descriptions.add(new Fetched(match,body,evidence.inspect(uri,body)));
      } catch(SafeRdfParser.UnsafeRdf rejected){
        if("RDF_SIZE_LIMIT".equals(rejected.getMessage()))bound++;
        else invalid++;
      } catch(BoundedGatewayClient.ProviderFailure failure){
        // Installation namespace policy and absent resources describe this URI only.
        if(!RESOURCE_DENIALS.contains(failure.decision().code()))throw failure;
        denied++;
      }
    }
    var candidates=new ArrayList<Candidate>();
    // Reserve time for local parsing and the final publication fence.
    var cutoff=q.deadline().minusSeconds(1);
    for(var entry:descriptions){
      var match=entry.match();
      var body=entry.body();
      if(Thread.currentThread().isInterrupted())throw new BoundedGatewayClient.ProviderFailure("PROVIDER_INTERRUPTED");
      var metadata=clock.instant().isBefore(cutoff)?evidence.read(entry.description(),link->fetch(link,cutoff)):
          new OntologyProvenance.Evidence(null,entry.description().labels(),List.of("ONTOLOGY_PROVENANCE_UNAVAILABLE"));
      candidates.add(new Candidate(match.uri(),match.uri(),q.artifactType(),"HIGH",match.score(),match.reasons(),metadata.gaps(),
          body.body(),body.mediaType(),metadata.triples(),metadata.labels()));
    }
    return new SearchResult(candidates,denied,invalid,bound);
  }
  private BoundedGatewayClient.Response fetch(String resource,Instant deadline){
    return client.get(cfg.gatewayBaseUrl(),underGateway(cfg.fetchPath()+"?uri="+enc(resource)),
        timeout(deadline),cfg.maxResponseBytes(),RDF);
  }
  private Duration timeout(Instant deadline){
    if(Thread.currentThread().isInterrupted())throw new BoundedGatewayClient.ProviderFailure("PROVIDER_INTERRUPTED");
    var remaining=Duration.between(clock.instant(),deadline);
    if(remaining.toMillis()<1)throw new BoundedGatewayClient.ProviderFailure("PROVIDER_TIMEOUT");
    return remaining.compareTo(cfg.requestTimeout())<0?remaining:cfg.requestTimeout();
  }
  static String query(Query q){String pattern=switch(q.artifactType()){case "CLASS"->"?resource a owl:Class .";case "PROPERTY"->"VALUES ?kind { owl:ObjectProperty owl:DatatypeProperty } ?resource a ?kind .";case "RELATIONSHIP"->"?resource a owl:ObjectProperty .";case "CONCEPT"->"?resource a skos:Concept .";case "VOCABULARY"->"?resource a skos:ConceptScheme .";case "ONTOLOGY"->"?resource a owl:Ontology .";default->throw new IllegalArgumentException("unsupported artifact type");};String literal=q.intent().replace("\\","\\\\").replace("\"","\\\"").replace("\n"," ").replace("\r"," ");return "PREFIX owl: <http://www.w3.org/2002/07/owl#>\nPREFIX skos: <http://www.w3.org/2004/02/skos/core#>\nPREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\nSELECT DISTINCT ?resource ?label WHERE { "+pattern+" OPTIONAL { ?resource rdfs:label|skos:prefLabel ?label } FILTER(CONTAINS(LCASE(STR(COALESCE(?label,?resource))),LCASE(\""+literal+"\"))) } ORDER BY ?resource LIMIT 50";}
  private URI underGateway(String path){URI u=cfg.gatewayBaseUrl().resolve(path);BoundedGatewayClient.requireSameOrigin(cfg.gatewayBaseUrl(),u);return u;}
  private static String enc(String v){return URLEncoder.encode(v,StandardCharsets.UTF_8);}
}
