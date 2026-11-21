package it.comune.trieste.ouf.semantic.adapters.discovery;

import static org.assertj.core.api.Assertions.*;
import static java.nio.charset.StandardCharsets.UTF_8;
import static org.mockito.Mockito.*;
import static it.comune.trieste.ouf.semantic.adapters.discovery.SchemaGovFetchFixture.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import it.comune.trieste.ouf.semantic.ports.SemanticDiscoveryProvider.Candidate;
import it.comune.trieste.ouf.semantic.ports.SemanticDiscoveryProvider.Query;
import java.net.URI;
import java.time.*;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

class SchemaGovProviderTest {
  private final Query property=new Query("PROPERTY","latitudine",List.of("it"));

  private static void label(ArrayNode rows,String uri,String text,String language){
    var row=rows.addObject();
    row.putObject("resource").put("type","uri").put("value",uri);
    row.putObject("label").put("value",text).put("xml:lang",language);
  }

  @Test void exactIdentifierBeyondTheUriCutoffIsFetchedOnceUsingItsBestLabel(){
    var rows=new ObjectMapper().createArrayNode();
    String ns="https://w3id.org/italia/onto/";
    var earlier=List.of("CLV","COV","CPSV","HER","IoT","L2","MU","PARK","POI","RO","SM");
    for(String name:earlier)label(rows,ns+name+"/id","identificativo locale","it");
    String identifier=ns+"l0/identifier";
    label(rows,identifier,"codice identificativo","it");
    label(rows,identifier,"  IDENTIFICATIVO  ","IT");
    var gateway=new SchemaGovFetchFixture(10,rows);
    for(String name:earlier)gateway.describe(ns+name+"/id","<urn:a> <urn:b> <urn:c> .");
    gateway.describe(identifier,"<"+identifier+"> a <http://www.w3.org/2002/07/owl#DatatypeProperty> .");
    var candidates=gateway.provider.search(new Query("PROPERTY","identificativo",List.of("it")));
    assertThat(candidates).hasSize(10);
    assertThat(candidates.getFirst().canonicalUri()).isEqualTo(identifier);
    assertThat(candidates.getFirst().score()).isEqualTo(1.0);
    assertThat(candidates.getFirst().reasons()).contains("exact label, preferred language it (score 1.0)");
    gateway.verifyFetches(identifier,1);
    gateway.verifyFetches(ns+"RO/id",0);
    gateway.verifyFetches(ns+"SM/id",0);
  }

  @Test void tiersPrecedeLanguageAndEqualScoresUseUriOrder(){
    var rows=new ObjectMapper().createArrayNode();
    label(rows,"urn:z","id campo","it");
    label(rows,"urn:x","codice-id-valido","it");
    label(rows,"urn:b","id","en");
    label(rows,"urn:a","id","en");
    label(rows,"urn:d","id","it");
    label(rows,"urn:c","valido","it");
    var gateway=new SchemaGovFetchFixture(6,rows);
    for(String name:List.of("a","b","c","d","x","z"))
      gateway.describe("urn:"+name,"<urn:a> <urn:b> <urn:c> .");
    var matches=gateway.provider.search(new Query("PROPERTY","id",List.of("it","en")));
    assertThat(matches).extracting(Candidate::canonicalUri).containsExactly("urn:d","urn:a","urn:b","urn:z","urn:x","urn:c");
    assertThat(matches).extracting(Candidate::score).containsExactly(1.0,.99,.99,.85,.70,.55);
  }

  @Test void invalidRdfAndDeniedFetchLeaveRoomForAValidDescription(){
    var gateway=new SchemaGovFetchFixture(1,"urn:a","urn:b","urn:c");
    gateway.describe("urn:a","broken");
    gateway.reject("urn:b","PROVIDER_HTTP_404");
    gateway.describe("urn:c","<urn:c> <urn:p> <urn:o> .");
    var result=gateway.provider.searchWithExclusions(property);
    assertThat(result.candidates()).extracting(Candidate::canonicalUri).containsExactly("urn:c");
    assertThat(result.fetchDenied()).isOne();
    assertThat(result.rdfInvalid()).isOne();
  }

  @ParameterizedTest @ValueSource(ints={400,404,406,409,410,414,422,451})
  void individualDenialCountsOnceAndDoesNotConsumeACandidateSlot(int status){
    var gateway=new SchemaGovFetchFixture(1,DENIED,DENIED,VALID);
    gateway.reject(DENIED,"PROVIDER_HTTP_"+status);
    gateway.describe(VALID,"<"+VALID+"> <http://www.w3.org/2000/01/rdf-schema#label> \"valid\" .");
    var result=gateway.provider.searchWithExclusions(property);
    assertThat(result.candidates()).hasSize(1);
    assertThat(result.fetchDenied()).isOne();
    gateway.verifyFetches(DENIED,1);
    gateway.verifyFetches(VALID,1);
  }

  @Test void namespaceDenialsNeverBlockTheProviderAndAttemptsStayBounded(){
    // Out-of-namespace results sort before admitted ones (ORDER BY ?resource).
    var three=new SchemaGovFetchFixture(3,"urn:a","urn:a","urn:b","urn:c");
    for(String uri:List.of("urn:a","urn:b","urn:c"))three.reject(uri,"PROVIDER_HTTP_400");
    var all=three.provider.searchWithExclusions(property);
    assertThat(all.candidates()).isEmpty();
    assertThat(all.fetchDenied()).isEqualTo(3);
    three.verifyFetches("urn:a",1);
    var bounded=new SchemaGovFetchFixture(1,"urn:a","urn:b","urn:c","urn:d");
    for(String uri:List.of("urn:a","urn:b","urn:c","urn:d"))bounded.reject(uri,"PROVIDER_HTTP_400");
    assertThat(bounded.provider.searchWithExclusions(property).fetchDenied()).isEqualTo(3);
    bounded.verifyFetches("urn:d",0);
  }

  @Test void laterSuccessPreventsEscalationAndUnavailableOntologyOnlyAddsAGap(){
    var gateway=new SchemaGovFetchFixture(4,"urn:a","urn:b","urn:c",VALID);
    for(String uri:List.of("urn:a","urn:b","urn:c"))gateway.reject(uri,"PROVIDER_HTTP_404");
    String ontology="https://w3id.org/italia/onto/CLV/";
    gateway.describe(VALID,"<"+VALID+"> <http://www.w3.org/2000/01/rdf-schema#isDefinedBy> <"+ontology+"> .");
    gateway.reject(ontology,"PROVIDER_HTTP_400");
    var result=gateway.provider.searchWithExclusions(property);
    assertThat(result.fetchDenied()).isEqualTo(3);
    assertThat(result.candidates()).singleElement().satisfies(c->{
      assertThat(c.canonicalUri()).isEqualTo(VALID);
      assertThat(c.ontologyProvenance()).isNull();
      assertThat(c.gaps()).containsExactly("ONTOLOGY_PROVENANCE_UNAVAILABLE");
    });
  }

  @Test void searchDenialRemainsAProviderFailure(){
    var gateway=new SchemaGovFetchFixture(1,VALID);
    gateway.rejectSearch("PROVIDER_HTTP_400");
    assertThatThrownBy(()->gateway.provider.searchWithExclusions(property))
        .isInstanceOf(BoundedGatewayClient.ProviderFailure.class).hasMessage("PROVIDER_HTTP_400");
    gateway.verifyFetches(VALID,0);
  }

  @ParameterizedTest @ValueSource(strings={"PROVIDER_HTTP_401","PROVIDER_HTTP_403","PROVIDER_HTTP_405","PROVIDER_HTTP_408",
      "PROVIDER_HTTP_429","PROVIDER_HTTP_503","PROVIDER_TIMEOUT","GATEWAY_TOKEN_REJECTED",
      "PROVIDER_MEDIA_TYPE_REJECTED","PROVIDER_RESPONSE_TOO_LARGE"})
  void requiredFetchPreservesChannelFailures(String code){
    var gateway=new SchemaGovFetchFixture(1,VALID);
    gateway.reject(VALID,code);
    assertThatThrownBy(()->gateway.provider.searchWithExclusions(property))
        .isInstanceOf(BoundedGatewayClient.ProviderFailure.class).hasMessage(code);
  }
  private static BoundedGatewayClient.Response turtle(String content){
    return new BoundedGatewayClient.Response(content.getBytes(UTF_8),"text/turtle");
  }
  @Test void followsOnlyTwoDistinctDefinitionsOfTheCandidateAndPreservesTermsDeterministically(){
    var description=turtle("""
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        <urn:poi> rdfs:isDefinedBy <urn:c>,<urn:b>,<urn:a>,[] .
        <urn:other> rdfs:isDefinedBy <urn:unrelated> .
        """);
    var calls=new java.util.ArrayList<String>();
    var reader=new OntologyProvenance(4096);
    var poi=reader.inspect("urn:poi",description);
    var evidence=reader.read(poi,id->{
      calls.add(id);
      return turtle("""
          @prefix dct: <http://purl.org/dc/terms/> .
          <%s> dct:publisher <urn:agid> ; dct:license <urn:license> ; dct:title "omit" .
          <urn:other> dct:publisher <urn:unrelated> .
          """.formatted(id));
    });
    assertThat(calls).containsExactly("urn:a","urn:b");
    String triples=new String(evidence.triples(),UTF_8);
    assertThat(triples.lines().toList()).hasSize(4).isSorted();
    assertThat(triples).contains("<urn:license>","<urn:agid>").doesNotContain("omit","unrelated","urn:c");
    assertThat(evidence.gaps()).containsExactly("ONTOLOGY_PROVENANCE_UNAVAILABLE");
    var reversed=new OntologyProvenance(4096).read(poi,id->turtle(
        "<"+id+"> <http://purl.org/dc/terms/license> <urn:license> ; <http://purl.org/dc/terms/publisher> <urn:agid> ."));
    assertThat(reversed.triples()).isEqualTo(evidence.triples());
  }
  @Test void discardsMalformedOrOversizedProjectionAndPropagatesCancellation(){
    var description=turtle("<urn:poi> <http://www.w3.org/2000/01/rdf-schema#isDefinedBy> <urn:ontology> .");
    var poi=new OntologyProvenance(4096).inspect("urn:poi",description);
    for(var response:List.of(turtle("broken"),turtle("<urn:ontology> <http://purl.org/dc/terms/publisher> <urn:agid> ."),
        new BoundedGatewayClient.Response("{\"@context\":\"https://context.invalid/\"}".getBytes(UTF_8),"application/ld+json"))){
      var metadata=new OntologyProvenance(16).read(poi,id->response);
      assertThat(metadata.triples()).isNull();
      assertThat(metadata.gaps()).containsExactly("ONTOLOGY_PROVENANCE_UNAVAILABLE");
    }
    assertThatThrownBy(()->new OntologyProvenance(4096).read(poi,id->{
      throw new BoundedGatewayClient.ProviderFailure("PROVIDER_INTERRUPTED");
    })).hasMessage("PROVIDER_INTERRUPTED");
  }
  @Test void ontologyRequestUsesOnlyRemainingLeaseTimeAndSkipsAnExpiredOptionalFetch(){
    var base=URI.create("https://gateway.invalid");
    var clock=Clock.fixed(Instant.parse("2026-11-21T12:00:00Z"),ZoneOffset.UTC);
    var transport=mock(BoundedGatewayClient.class);
    var cfg=new SchemaGovProperties(true,base,"/search","/fetch",Duration.ofSeconds(1),Duration.ofSeconds(5),
        4096,1,1,Duration.ofSeconds(1),1,Duration.ofSeconds(30));
    String rows="{\"results\":{\"bindings\":[{\"resource\":{\"value\":\"urn:poi\"}}]}}";
    when(transport.postForm(eq(base),eq(base.resolve("/search")),anyString(),any(Duration.class),eq(4096),anySet()))
        .thenReturn(new BoundedGatewayClient.Response(rows.getBytes(UTF_8),"application/json"));
    var poi=base.resolve("/fetch?uri=urn%3Apoi");
    var ontology=base.resolve("/fetch?uri=urn%3Aontology");
    when(transport.get(eq(base),eq(poi),any(Duration.class),eq(4096),anySet()))
        .thenReturn(turtle("<urn:poi> <http://www.w3.org/2000/01/rdf-schema#isDefinedBy> <urn:ontology> ."));
    when(transport.get(eq(base),eq(ontology),eq(Duration.ofMillis(500)),eq(4096),anySet()))
        .thenReturn(turtle("<urn:ontology> <http://purl.org/dc/terms/publisher> <urn:agid> ."));
    var provider=new SchemaGovProvider(cfg,transport,new ObjectMapper(),clock);
    var allowed=provider.search(new Query("CLASS","poi",List.of(),clock.instant().plusMillis(1500)));
    assertThat(allowed.getFirst().ontologyProvenance()).isNotEmpty();
    var skipped=provider.search(new Query("CLASS","poi",List.of(),clock.instant().plusMillis(800)));
    assertThat(skipped.getFirst().ontologyProvenance()).isNull();
    verify(transport,times(1)).get(eq(base),eq(ontology),any(Duration.class),eq(4096),anySet());
  }
  @Test void queryIsBoundedAndSelectsOfficialSemanticKinds(){for(var type:List.of("CLASS","PROPERTY","RELATIONSHIP","CONCEPT","VOCABULARY","ONTOLOGY")){String q=SchemaGovProvider.query(new Query(type,"luogo",List.of("it")));assertThat(q).contains("LIMIT 50").contains("SELECT DISTINCT ?resource ?label");}}
  @Test void propertyIncludesObjectAndDatatypeProperties(){assertThat(SchemaGovProvider.query(new Query("PROPERTY","nome",List.of("it")))).contains("owl:ObjectProperty owl:DatatypeProperty");}
  @Test void literalCannotBreakOutOfQuery(){String q=SchemaGovProvider.query(new Query("CLASS","x\") } UNION { ?evil ?p ?o } #",List.of()));assertThat(q).contains("LCASE(\"x\\\") } UNION { ?evil ?p ?o } #\")");assertThat(q).endsWith("LIMIT 50");}
}
