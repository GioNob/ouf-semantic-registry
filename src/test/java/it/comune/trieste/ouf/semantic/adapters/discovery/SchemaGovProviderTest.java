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

  @Test void filtersDistinctUrisBeforeFetchAndPreservesScoresOrderAndProvenance(){
    var rows=new ObjectMapper().createArrayNode();
    String other=TEST_NAMESPACE+"other";
    String ontology=TEST_NAMESPACE+"ontology";
    String external="https://external.example.test/ontology";
    label(rows,DENIED,"latitudine","it");
    label(rows,DENIED,"latitudine","en");
    label(rows,other,"latitudine stimata","it");
    label(rows,VALID,"latitudine","it");
    var gateway=new SchemaGovFetchFixture(2,rows);
    for(String uri:List.of(VALID,other))
      gateway.describe(uri,"<"+uri+"> <http://www.w3.org/2000/01/rdf-schema#isDefinedBy> <"+external+">,<"+ontology+"> .");
    gateway.describe(ontology,"<"+ontology+"> <http://purl.org/dc/terms/license> <urn:license> .");

    var result=gateway.provider.searchWithNamespaceFilter(property);
    assertThat(result.namespaceExcluded()).isEqualTo(2); // One description and one shared ontology.
    assertThat(result.fetched().fetchDenied()).isZero();
    var candidates=result.fetched().candidates();
    assertThat(candidates).extracting(Candidate::canonicalUri).containsExactly(VALID,other);
    assertThat(candidates).extracting(Candidate::score).containsExactly(1.0,.85);
    assertThat(candidates).allSatisfy(c->{
      assertThat(c.gaps()).containsExactly("ONTOLOGY_PROVENANCE_UNAVAILABLE");
      assertThat(new String(c.ontologyProvenance(),UTF_8)).contains("<urn:license>");
    });
    gateway.verifyFetches(DENIED,0);
    gateway.verifyFetches(external,0);
    for(String uri:List.of(VALID,other,ontology))gateway.verifyFetches(uri,1);
  }

  @Test void localExclusionsDoNotConsumeTheRequiredFetchAttemptBudget(){
    var rows=new ObjectMapper().createArrayNode();
    for(int i=0;i<4;i++)label(rows,DENIED+i,"latitudine","it");
    label(rows,VALID,"latitudine stimata","it");
    var gateway=new SchemaGovFetchFixture(1,rows);
    gateway.describe(VALID,"<urn:s> <urn:p> <urn:o> .");
    var result=gateway.provider.searchWithNamespaceFilter(property);
    assertThat(result.namespaceExcluded()).isEqualTo(4);
    assertThat(result.fetched().candidates()).extracting(Candidate::canonicalUri).containsExactly(VALID);
    for(int i=0;i<4;i++)gateway.verifyFetches(DENIED+i,0);
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
    label(rows,TEST_NAMESPACE+"z","id campo","it");
    label(rows,TEST_NAMESPACE+"x","codice-id-valido","it");
    label(rows,TEST_NAMESPACE+"b","id","en");
    label(rows,TEST_NAMESPACE+"a","id","en");
    label(rows,TEST_NAMESPACE+"d","id","it");
    label(rows,TEST_NAMESPACE+"c","valido","it");
    var gateway=new SchemaGovFetchFixture(6,rows);
    for(String name:List.of("a","b","c","d","x","z"))
      gateway.describe(TEST_NAMESPACE+name,"<urn:a> <urn:b> <urn:c> .");
    var matches=gateway.provider.search(new Query("PROPERTY","id",List.of("it","en")));
    assertThat(matches).extracting(Candidate::canonicalUri).containsExactly(TEST_NAMESPACE+"d",TEST_NAMESPACE+"a",TEST_NAMESPACE+"b",TEST_NAMESPACE+"z",TEST_NAMESPACE+"x",TEST_NAMESPACE+"c");
    assertThat(matches).extracting(Candidate::score).containsExactly(1.0,.99,.99,.85,.70,.55);
  }

  @Test void invalidRdfAndDeniedFetchLeaveRoomForAValidDescription(){
    var gateway=new SchemaGovFetchFixture(1,TEST_NAMESPACE+"a",TEST_NAMESPACE+"b",TEST_NAMESPACE+"c");
    gateway.describe(TEST_NAMESPACE+"a","broken");
    gateway.reject(TEST_NAMESPACE+"b","PROVIDER_HTTP_404");
    gateway.describe(TEST_NAMESPACE+"c","<urn:c> <urn:p> <urn:o> .");
    var result=gateway.provider.searchWithExclusions(property);
    assertThat(result.candidates()).extracting(Candidate::canonicalUri).containsExactly(TEST_NAMESPACE+"c");
    assertThat(result.fetchDenied()).isOne();
    assertThat(result.rdfInvalid()).isOne();
  }

  @ParameterizedTest @ValueSource(ints={400,404,406,409,410,414,422,451})
  void individualDenialCountsOnceAndDoesNotConsumeACandidateSlot(int status){
    var gateway=new SchemaGovFetchFixture(1,REMOTE_DENIAL,REMOTE_DENIAL,VALID);
    gateway.reject(REMOTE_DENIAL,"PROVIDER_HTTP_"+status);
    gateway.describe(VALID,"<"+VALID+"> <http://www.w3.org/2000/01/rdf-schema#label> \"valid\" .");
    var result=gateway.provider.searchWithExclusions(property);
    assertThat(result.candidates()).hasSize(1);
    assertThat(result.fetchDenied()).isOne();
    gateway.verifyFetches(REMOTE_DENIAL,1);
    gateway.verifyFetches(VALID,1);
  }

  @Test void remoteDenialsNeverBlockTheProviderAndAttemptsStayBounded(){
    var three=new SchemaGovFetchFixture(3,TEST_NAMESPACE+"a",TEST_NAMESPACE+"a",TEST_NAMESPACE+"b",TEST_NAMESPACE+"c");
    for(String uri:List.of(TEST_NAMESPACE+"a",TEST_NAMESPACE+"b",TEST_NAMESPACE+"c"))three.reject(uri,"PROVIDER_HTTP_400");
    var all=three.provider.searchWithExclusions(property);
    assertThat(all.candidates()).isEmpty();
    assertThat(all.fetchDenied()).isEqualTo(3);
    three.verifyFetches(TEST_NAMESPACE+"a",1);
    var bounded=new SchemaGovFetchFixture(1,TEST_NAMESPACE+"a",TEST_NAMESPACE+"b",TEST_NAMESPACE+"c",TEST_NAMESPACE+"d");
    for(String uri:List.of(TEST_NAMESPACE+"a",TEST_NAMESPACE+"b",TEST_NAMESPACE+"c",TEST_NAMESPACE+"d"))bounded.reject(uri,"PROVIDER_HTTP_400");
    assertThat(bounded.provider.searchWithExclusions(property).fetchDenied()).isEqualTo(3);
    bounded.verifyFetches(TEST_NAMESPACE+"d",0);
  }

  @Test void laterSuccessPreventsEscalationAndUnavailableOntologyOnlyAddsAGap(){
    var gateway=new SchemaGovFetchFixture(4,TEST_NAMESPACE+"a",TEST_NAMESPACE+"b",TEST_NAMESPACE+"c",VALID);
    for(String uri:List.of(TEST_NAMESPACE+"a",TEST_NAMESPACE+"b",TEST_NAMESPACE+"c"))gateway.reject(uri,"PROVIDER_HTTP_404");
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
    var reader=new OntologyProvenance(4096,uri->true);
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
    var reversed=new OntologyProvenance(4096,uri->true).read(poi,id->turtle(
        "<"+id+"> <http://purl.org/dc/terms/license> <urn:license> ; <http://purl.org/dc/terms/publisher> <urn:agid> ."));
    assertThat(reversed.triples()).isEqualTo(evidence.triples());
  }
  @Test void discardsMalformedOrOversizedProjectionAndPropagatesCancellation(){
    var description=turtle("<urn:poi> <http://www.w3.org/2000/01/rdf-schema#isDefinedBy> <urn:ontology> .");
    var poi=new OntologyProvenance(4096,uri->true).inspect("urn:poi",description);
    for(var response:List.of(turtle("broken"),turtle("<urn:ontology> <http://purl.org/dc/terms/publisher> <urn:agid> ."),
        new BoundedGatewayClient.Response("{\"@context\":\"https://context.invalid/\"}".getBytes(UTF_8),"application/ld+json"))){
      var metadata=new OntologyProvenance(16,uri->true).read(poi,id->response);
      assertThat(metadata.triples()).isNull();
      assertThat(metadata.gaps()).containsExactly("ONTOLOGY_PROVENANCE_UNAVAILABLE");
    }
    assertThatThrownBy(()->new OntologyProvenance(4096,uri->true).read(poi,id->{
      throw new BoundedGatewayClient.ProviderFailure("PROVIDER_INTERRUPTED");
    })).hasMessage("PROVIDER_INTERRUPTED");
  }
  @Test void ontologyRequestUsesOnlyRemainingLeaseTimeAndSkipsAnExpiredOptionalFetch(){
    var base=URI.create("https://gateway.invalid");
    var clock=Clock.fixed(Instant.parse("2026-11-21T12:00:00Z"),ZoneOffset.UTC);
    var transport=mock(BoundedGatewayClient.class);
    var cfg=new SchemaGovProperties(true,base,"/search","/fetch",Duration.ofSeconds(1),Duration.ofSeconds(5),
        4096,1,1,Duration.ofSeconds(1),1,Duration.ofSeconds(30),List.of(TEST_NAMESPACE));
    String rows="{\"results\":{\"bindings\":[{\"resource\":{\"value\":\"https://terms.example.test/poi\"}}]}}";
    when(transport.postForm(eq(base),eq(base.resolve("/search")),anyString(),any(Duration.class),eq(4096),anySet()))
        .thenReturn(new BoundedGatewayClient.Response(rows.getBytes(UTF_8),"application/json"));
    var poi=base.resolve("/fetch?uri=https%3A%2F%2Fterms.example.test%2Fpoi");
    var ontology=base.resolve("/fetch?uri=https%3A%2F%2Fterms.example.test%2Fontology");
    when(transport.get(eq(base),eq(poi),any(Duration.class),eq(4096),anySet()))
        .thenReturn(turtle("<https://terms.example.test/poi> <http://www.w3.org/2000/01/rdf-schema#isDefinedBy> <https://terms.example.test/ontology> ."));
    when(transport.get(eq(base),eq(ontology),eq(Duration.ofMillis(500)),eq(4096),anySet()))
        .thenReturn(turtle("<https://terms.example.test/ontology> <http://purl.org/dc/terms/publisher> <urn:agid> ."));
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
