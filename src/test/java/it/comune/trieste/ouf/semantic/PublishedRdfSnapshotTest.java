package it.comune.trieste.ouf.semantic;

import static org.assertj.core.api.Assertions.*;
import it.comune.trieste.ouf.semantic.application.PublishedRdfSnapshot;
import it.comune.trieste.ouf.semantic.domain.SafeRdfParser;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.junit.jupiter.api.Test;

class PublishedRdfSnapshotTest {
  private final PublishedRdfSnapshot projection=new PublishedRdfSnapshot();
  private Map<String,Object> read(String rdf,String mediaType) {
    byte[] bytes=rdf.getBytes(StandardCharsets.UTF_8);
    var parsed=new SafeRdfParser().parse(bytes,mediaType);
    return projection.project(bytes,mediaType,parsed.contentHash(),parsed.statementCount());
  }
  @Test void preservesLabelsInheritanceDomainRangeAndBlankNodeRestrictionsWithoutInference() {
    var out=read("""
      @prefix ex: <https://example.org/> .
      @prefix owl: <http://www.w3.org/2002/07/owl#> .
      @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
      @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
      ex:Teatro a owl:Class ; rdfs:label "Teatro"@it ;
        rdfs:subClassOf ex:LuogoCulturale, [ a owl:Restriction ; owl:onProperty ex:nome ;
          owl:minCardinality "1"^^xsd:nonNegativeInteger ] .
      ex:nome a owl:DatatypeProperty ; rdfs:domain ex:Teatro ; rdfs:range xsd:string .
      ""","text/turtle");
    assertThat(out.get("partial")).isEqualTo(false);
    assertThat(out.get("statement_count")).isEqualTo(10L);
    assertThat(out.get("interpretation")).isEqualTo("ASSERTED_RDF_NO_INFERENCE");
    var triples=(List<Map<String,Object>>)out.get("statements");
    assertThat(triples).anySatisfy(t->{
      assertThat(t.get("predicate")).isEqualTo("http://www.w3.org/2000/01/rdf-schema#label");
      assertThat((Map<String,Object>)t.get("object")).containsEntry("value","Teatro").containsEntry("language","it");
    });
    assertThat(triples).anySatisfy(t->assertThat(t.get("predicate")).isEqualTo("http://www.w3.org/2002/07/owl#minCardinality"));
    assertThat(triples).anySatisfy(t->assertThat((Map<String,Object>)t.get("subject")).containsEntry("kind","BLANK_NODE"));
    assertThat(triples).noneSatisfy(t->{
      assertThat((Map<String,Object>)t.get("subject")).containsEntry("value","https://example.org/LuogoCulturale");
      assertThat(t.get("predicate")).isEqualTo("http://www.w3.org/1999/02/22-rdf-syntax-ns#type");
    });
  }
  @Test void capsStatementsAndReportsPartialInsteadOfClaimingCompleteOntology() {
    var rdf=new StringBuilder();
    for(int i=0;i<1001;i++)rdf.append("<urn:s:").append(i).append("> <urn:p> <urn:o> .\n");
    var out=read(rdf.toString(),"application/n-triples");
    assertThat((List<?>)out.get("statements")).hasSize(1000);
    assertThat(out).containsEntry("partial",true).containsEntry("statement_count",1001L);
    assertThat(read(rdf.toString(),"application/n-triples").get("statements")).isEqualTo(out.get("statements"));
  }
  @Test void checksStoredHashAndCountBeforeReturningAnyEvidence() {
    byte[] bytes="<urn:s> <urn:p> <urn:o> .".getBytes(StandardCharsets.UTF_8);
    var parsed=new SafeRdfParser().parse(bytes,"text/turtle");
    assertThatThrownBy(()->projection.project(bytes,"text/turtle","0".repeat(64),1))
      .hasMessage("SEM_READ_RDF_SNAPSHOT_MISMATCH");
    assertThatThrownBy(()->projection.project(bytes,"text/turtle",parsed.contentHash(),2))
      .hasMessage("SEM_READ_RDF_SNAPSHOT_MISMATCH");
  }
  @Test void rejectsRemoteJsonLdContextsBeforeParserCanFetchThemAndAcceptsLocalContexts() {
    for(String payload:List.of("{\"@context\":\"https://example.invalid/context\"}",
        "{\"@context\":[{},\"https://example.invalid/context\"]}",
        "{\"@context\":{\"@import\":\"https://example.invalid/context\"}}"))
      assertThatThrownBy(()->projection.project(payload.getBytes(StandardCharsets.UTF_8),
        "application/ld+json","0".repeat(64),0)).hasMessage("SEM_READ_RDF_REMOTE_CONTEXT_FORBIDDEN");
    assertThat(read("{\"@context\":{\"label\":\"http://www.w3.org/2000/01/rdf-schema#label\"},\"@id\":\"urn:s\",\"label\":\"Teatro\"}",
      "application/ld+json")).containsEntry("statement_count",1L).containsEntry("partial",false);
  }
  @Test void preservesRdfXmlAndRejectsExternalEntities() {
    assertThat(read("""
      <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
        <rdf:Description rdf:about="urn:s"><rdfs:label xml:lang="it">Teatro</rdfs:label></rdf:Description>
      </rdf:RDF>
      ""","application/rdf+xml")).containsEntry("statement_count",1L);
    assertThatThrownBy(()->projection.project("<!DOCTYPE x SYSTEM 'https://example.invalid/x'>".getBytes(StandardCharsets.UTF_8),
      "application/rdf+xml","0".repeat(64),0)).hasMessage("RDF_EXTERNAL_ENTITY_FORBIDDEN");
  }
}
