package it.comune.trieste.ouf.semantic.adapters.discovery;

import static org.assertj.core.api.Assertions.*;
import static java.nio.charset.StandardCharsets.UTF_8;
import static org.mockito.Mockito.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import it.comune.trieste.ouf.semantic.ports.SemanticDiscoveryProvider.Query;
import java.net.URI;
import java.time.*;
import java.util.List;
import org.junit.jupiter.api.Test;

class SchemaGovProviderTest {
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
    var evidence=new OntologyProvenance(4096).read("urn:poi",description,id->{
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
    var reversed=new OntologyProvenance(4096).read("urn:poi",description,id->turtle(
        "<"+id+"> <http://purl.org/dc/terms/license> <urn:license> ; <http://purl.org/dc/terms/publisher> <urn:agid> ."));
    assertThat(reversed.triples()).isEqualTo(evidence.triples());
  }
  @Test void discardsMalformedOrOversizedProjectionAndPropagatesCancellation(){
    var description=turtle("<urn:poi> <http://www.w3.org/2000/01/rdf-schema#isDefinedBy> <urn:ontology> .");
    for(var response:List.of(turtle("broken"),turtle("<urn:ontology> <http://purl.org/dc/terms/publisher> <urn:agid> ."),
        new BoundedGatewayClient.Response("{\"@context\":\"https://context.invalid/\"}".getBytes(UTF_8),"application/ld+json"))){
      var metadata=new OntologyProvenance(16).read("urn:poi",description,id->response);
      assertThat(metadata.triples()).isNull();
      assertThat(metadata.gaps()).containsExactly("ONTOLOGY_PROVENANCE_UNAVAILABLE");
    }
    assertThatThrownBy(()->new OntologyProvenance(4096).read("urn:poi",description,id->{
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
