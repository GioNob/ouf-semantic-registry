package it.comune.trieste.ouf.semantic.domain;

import static org.assertj.core.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;

class SafeRdfParserTest {
  private final SafeRdfParser parser=new SafeRdfParser();
  @Test void parsesLocalTurtleAndReturnsDeterministicHash(){byte[] b="@prefix ex: <https://example.test/> . ex:a ex:p ex:b .".getBytes(StandardCharsets.UTF_8);var a=parser.parse(b,"text/turtle");var c=parser.parse(b,"text/turtle");assertThat(a.statementCount()).isEqualTo(1);assertThat(a.contentHash()).isEqualTo(c.contentHash()).hasSize(64);}
  @Test void owlImportsIsDataAndIsNotDereferenced(){byte[] b="@prefix owl: <http://www.w3.org/2002/07/owl#> . <urn:a> owl:imports <http://127.0.0.1:9/never> .".getBytes(StandardCharsets.UTF_8);assertThat(parser.parse(b,"text/turtle").statementCount()).isEqualTo(1);}
  @Test void rejectsDoctypeAndExternalEntityBeforeJena(){for(String x:new String[]{"<!DOCTYPE rdf:RDF []>","<!ENTITY xxe SYSTEM 'file:///etc/passwd'>"})assertThatThrownBy(()->parser.parse(x.getBytes(StandardCharsets.UTF_8),"application/rdf+xml")).isInstanceOf(SafeRdfParser.UnsafeRdf.class).hasMessage("RDF_EXTERNAL_ENTITY_FORBIDDEN");}
  @Test void leadingPaddingCannotHideDoctype(){String x=" ".repeat(5000)+"<!DOCTYPE rdf:RDF []>";assertThatThrownBy(()->parser.parse(x.getBytes(StandardCharsets.UTF_8),"application/rdf+xml")).hasMessage("RDF_EXTERNAL_ENTITY_FORBIDDEN");}
  @Test void rejectsUnsupportedMediaType(){assertThatThrownBy(()->parser.parse("x".getBytes(),"text/html")).hasMessage("RDF_MEDIA_TYPE_UNSUPPORTED");}
  @Test void rejectsOversizeBeforeAllocationToModel(){assertThatThrownBy(()->parser.parse(new byte[SafeRdfParser.MAX_BYTES+1],"text/turtle")).hasMessage("RDF_SIZE_LIMIT");}
}
