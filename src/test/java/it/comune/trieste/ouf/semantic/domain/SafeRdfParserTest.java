package it.comune.trieste.ouf.semantic.domain;

import static org.assertj.core.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.Map;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.rdf.model.RDFNode;
import org.apache.jena.riot.Lang;
import org.apache.jena.riot.RDFDataMgr;
import org.junit.jupiter.api.Test;

class SafeRdfParserTest {
  private final SafeRdfParser parser=new SafeRdfParser();
  @Test void parsesFiveSubjectOnlyOntopiaFetchesIncludingPublicServiceLiteral() throws IOException {
    var ontology=ModelFactory.createDefaultModel();
    try(var in=getClass().getResourceAsStream("/discovery/ontopia/POI-AP_IT.ttl")){
      RDFDataMgr.read(ontology,in,Lang.TURTLE);
      var counts=Map.of("MultiplePointOfInterest",10,"POINameInTime",13,"POIState",11,
          "PointOfInterest",20,"PointOfInterestCategory",10);
      for(var entry:counts.entrySet()){
        var description=ModelFactory.createDefaultModel();
        try{
          var subject=ontology.getResource("https://w3id.org/italia/onto/POI/"+entry.getKey());
          description.add(ontology.listStatements(subject,null,(RDFNode)null));
          assertThat(description.size()).as(entry.getKey()).isEqualTo(entry.getValue().longValue());
          var bytes=new ByteArrayOutputStream();
          RDFDataMgr.write(bytes,description,Lang.TURTLE);
          if(entry.getKey().equals("PointOfInterestCategory")){
            assertThat(bytes.toString(StandardCharsets.UTF_8)).contains("public service");
          }
          assertThat(parser.parse(bytes.toByteArray(),"text/turtle").statementCount())
              .as(entry.getKey()).isEqualTo(description.size());
        }finally{description.close();}
      }
    }finally{ontology.close();}
  }
  @Test void parsesLocalTurtleAndReturnsDeterministicHash(){byte[] b="@prefix ex: <https://example.test/> . ex:a ex:p ex:b .".getBytes(StandardCharsets.UTF_8);var a=parser.parse(b,"text/turtle");var c=parser.parse(b,"text/turtle");assertThat(a.statementCount()).isEqualTo(1);assertThat(a.contentHash()).isEqualTo(c.contentHash()).hasSize(64);}
  @Test void owlImportsIsDataAndIsNotDereferenced(){byte[] b="@prefix owl: <http://www.w3.org/2002/07/owl#> . <urn:a> owl:imports <http://127.0.0.1:9/never> .".getBytes(StandardCharsets.UTF_8);assertThat(parser.parse(b,"text/turtle").statementCount()).isEqualTo(1);}
  @Test void rejectsDoctypeAndExternalEntityBeforeJena(){for(String x:new String[]{"<!DOCTYPE rdf:RDF []>","<!ENTITY xxe SYSTEM 'file:///etc/passwd'>"})assertThatThrownBy(()->parser.parse(x.getBytes(StandardCharsets.UTF_8),"application/rdf+xml")).isInstanceOf(SafeRdfParser.UnsafeRdf.class).hasMessage("RDF_EXTERNAL_ENTITY_FORBIDDEN");}
  @Test void xmlLiteralCanDescribeAPublicService(){
    String rdf="""
        <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
          <rdf:Description rdf:about="https://example.test/category"><rdfs:comment>public service</rdfs:comment></rdf:Description>
        </rdf:RDF>
        """;
    assertThat(parser.parse(rdf.getBytes(StandardCharsets.UTF_8),"application/rdf+xml").statementCount()).isOne();
  }
  @Test void leadingPaddingCannotHideDoctype(){String x=" ".repeat(5000)+"<!DOCTYPE rdf:RDF []>";assertThatThrownBy(()->parser.parse(x.getBytes(StandardCharsets.UTF_8),"application/rdf+xml")).hasMessage("RDF_EXTERNAL_ENTITY_FORBIDDEN");}
  @Test void rejectsUnsupportedMediaType(){assertThatThrownBy(()->parser.parse("x".getBytes(),"text/html")).hasMessage("RDF_MEDIA_TYPE_UNSUPPORTED");}
  @Test void rejectsOversizeBeforeAllocationToModel(){assertThatThrownBy(()->parser.parse(new byte[SafeRdfParser.MAX_BYTES+1],"text/turtle")).hasMessage("RDF_SIZE_LIMIT");}
}
